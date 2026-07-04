from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-governance-acceptance.py"
FIXTURE_ROOT = ROOT / "backlog" / "fixtures" / "acceptance-packets"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_fixture(name: str) -> dict:
    return yaml.safe_load((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def load_checker():
    spec = importlib.util.spec_from_file_location("check_governance_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8").strip()


class GovernanceEvidenceRefsTests(unittest.TestCase):
    def assert_rejected(self, packet: dict, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "packet.yml"
            path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            result = run_cli("check", "--packet", str(path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(expected, result.stderr)

    def test_stable_terminal_artifact_without_durable_ref_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["command_results"][0]["artifact_ref"] = "terminal:git-diff-check"

        self.assert_rejected(packet, "terminal placeholder cannot satisfy stable evidence")

    def test_stable_source_ref_without_resolved_ref_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"] = [
            record
            for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]
            if record["relation"] != "source"
        ]

        self.assert_rejected(packet, "source_ref lacks resolved source relation")

    def test_stable_input_source_ref_missing_from_evidence_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        packet["AcceptancePacket"]["input"]["source_refs"].append("backlog/plans/04-evidence-capture-and-source-refs.md")

        self.assert_rejected(packet, "input source_ref missing from evidence.source_refs")

    def test_stable_input_source_ref_must_be_input_origin_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]:
            if record["relation"] == "source":
                record["origin"] = "generated"

        self.assert_rejected(packet, "input source_ref lacks resolved input source relation")

    def test_stable_git_source_ref_cannot_hide_protected_path(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        commit = git("rev-parse", "HEAD")
        ref = f"git:{commit}:scripts/check-governance-acceptance.py"
        evidence["source_refs"].append(ref)
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "source",
                "ref": ref,
                "status": "resolved",
                "target": f"{commit}:scripts/check-governance-acceptance.py",
            }
        )

        self.assert_rejected(packet, "source_ref points to protected path outside changed_paths")

    def test_stable_git_source_ref_must_not_be_opaque_blob(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        blob_sha = git("rev-parse", "HEAD:scripts/check-governance-acceptance.py")
        ref = f"git:{blob_sha}"
        evidence["source_refs"].append(ref)
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "source",
                "ref": ref,
                "status": "resolved",
                "target": blob_sha,
            }
        )

        self.assert_rejected(packet, "git source refs must use git:<full-commit-sha>:<repo-path> form")

    def test_stable_git_source_ref_must_be_commit_pinned(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        ref = "git:HEAD:backlog/fixtures/acceptance-packets/README.md"
        evidence["source_refs"].append(ref)
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "source",
                "ref": ref,
                "status": "resolved",
                "target": "HEAD:backlog/fixtures/acceptance-packets/README.md",
            }
        )

        self.assert_rejected(packet, "git source refs must use git:<full-commit-sha>:<repo-path> form")

    def test_stable_source_ref_protects_directory_roots(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        ref = "file:scripts"
        evidence["source_refs"].append(ref)
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "source",
                "ref": ref,
                "status": "resolved",
                "target": "scripts",
            }
        )

        self.assert_rejected(packet, "source_ref points to protected path outside changed_paths")

    def test_stable_local_colon_path_does_not_satisfy_changed_path_source(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        result["inference"]["changed_paths"] = ["scripts/check-governance-acceptance.py"]
        result["inference"]["change_class"] = "harness-affecting"
        result["inference"]["impact"] = "high"
        result["inference"]["protected_boundary_changed"] = True

        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            source_file = Path(tmpdir) / "tmp:scripts" / "check-governance-acceptance.py"
            source_file.parent.mkdir(parents=True)
            source_file.write_text("# unrelated local file\n", encoding="utf-8")
            rel_source = source_file.relative_to(ROOT).as_posix()
            ref = f"file:{rel_source}"
            packet["AcceptancePacket"]["input"]["source_refs"].append(ref)
            evidence["source_refs"].append(ref)
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": rel_source,
                }
            )

            self.assert_rejected(packet, "changed_paths lack resolved source refs")

    def test_stable_unlisted_resolved_source_cannot_close_changed_path(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        changed_path = result["inference"]["changed_paths"][0]
        packet["AcceptancePacket"]["input"]["source_refs"] = ["README.md"]
        evidence["source_refs"] = ["README.md"]
        evidence["resolved_refs"] = [
            record for record in evidence["resolved_refs"] if record.get("relation") != "source"
        ]
        evidence["resolved_refs"].extend(
            [
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "README.md",
                    "status": "resolved",
                    "target": "README.md",
                },
                {
                    "origin": "generated",
                    "relation": "source",
                    "ref": changed_path,
                    "status": "resolved",
                    "target": changed_path,
                },
            ]
        )

        self.assert_rejected(packet, "changed_paths lack resolved source refs")

    def test_stable_file_ref_fragment_is_literal_source_path(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]

        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            visible_path = Path(tmpdir) / "changed-source.txt"
            shadow_path = Path(f"{visible_path}#shadow")
            shadow_path.write_text("shadow source\n", encoding="utf-8")
            visible_rel = visible_path.relative_to(ROOT).as_posix()
            shadow_rel = shadow_path.relative_to(ROOT).as_posix()
            ref = f"file:{shadow_rel}"
            result["inference"]["changed_paths"] = [visible_rel]
            packet["AcceptancePacket"]["input"]["source_refs"] = [ref]
            evidence["source_refs"] = [ref]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": shadow_rel,
                }
            )

            self.assert_rejected(packet, "changed_paths lack resolved source refs")

    def test_stable_trace_refs_require_anchors(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        trace_ref = "trace:.harness/traces/evolution/001-repository-self-application-root.md"
        packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]["evolution"] = [trace_ref]

        self.assert_rejected(packet, "trace_refs.evolution entries must include an anchor")

    def test_stable_trace_source_refs_require_anchors(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        trace_ref = "trace:.harness/traces/evolution/001-repository-self-application-root.md"
        changed_path = result["inference"]["changed_paths"][0]
        packet["AcceptancePacket"]["input"]["source_refs"] = [trace_ref]
        evidence["source_refs"] = [trace_ref]
        evidence["resolved_refs"] = [
            record for record in evidence["resolved_refs"] if record.get("relation") != "source"
        ]
        evidence["resolved_refs"].append(
            {
                "origin": "input",
                "relation": "source",
                "ref": trace_ref,
                "status": "resolved",
                "target": changed_path,
            }
        )

        self.assert_rejected(packet, "trace source refs must include an anchor")

    def test_stable_missing_artifact_file_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        artifact_ref = "file:backlog/fixtures/acceptance-packets/artifacts/missing.log"
        packet["AcceptancePacket"]["result"]["evidence"]["command_results"][0]["artifact_ref"] = artifact_ref
        packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "artifact",
                "ref": artifact_ref,
                "status": "resolved",
                "target": "backlog/fixtures/acceptance-packets/artifacts/missing.log",
            }
        )

        self.assert_rejected(packet, "resolved ref does not resolve")

    def test_stable_protected_packet_missing_search_set_ref_fails(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]["search_set_before"] = None
        packet["AcceptancePacket"]["result"]["evidence"]["skipped"] = [
            item
            for item in packet["AcceptancePacket"]["result"]["evidence"]["skipped"]
            if item.get("evidence") != "search_set_before"
        ]

        self.assert_rejected(packet, "stable protected packet missing search_set_before")

    def test_stable_protected_packet_cannot_both_trace_and_skip_search_set(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["skipped"].append(
            {
                "evidence": "search_set_after",
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "conflicting search-set closure",
                "source_ref": "file:backlog/plans/02-acceptance-packet-schema-and-fixtures.md",
            }
        )

        self.assert_rejected(
            packet,
            "stable protected packet search_set_after cannot have both trace evidence and skipped evidence",
        )

    def test_stable_protected_packet_search_set_refs_must_use_search_set_trace(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        bad_ref = "trace:README.md#ai-agent-meta-harness"
        evidence["trace_refs"]["search_set_before"] = bad_ref
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": bad_ref,
                "status": "resolved",
                "target": "README.md#ai-agent-meta-harness",
            }
        )

        self.assert_rejected(packet, "stable trace_refs.search_set_before must point to backlog/repository-search-set.md")

    def test_stable_protected_packet_search_set_refs_must_use_allowed_anchor(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        bad_ref = "trace:backlog/repository-search-set.md#harness-search-set"
        evidence["trace_refs"]["search_set_after"] = bad_ref
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": bad_ref,
                "status": "resolved",
                "target": "backlog/repository-search-set.md#harness-search-set",
            }
        )

        self.assert_rejected(packet, "stable trace_refs.search_set_after must point to backlog/repository-search-set.md")

    def test_stable_search_set_before_after_must_use_capture_anchor(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        evidence["trace_refs"]["search_set_before"] = "trace:backlog/repository-search-set.md#active"

        self.assert_rejected(packet, "search-set capture ref must use search-set-before-* anchor")

    def test_stable_protected_packet_search_set_refs_must_be_canonical(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        bad_ref = "trace:backlog//repository-search-set.md#active"
        evidence["trace_refs"]["search_set_after"] = bad_ref
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": bad_ref,
                "status": "resolved",
                "target": "backlog//repository-search-set.md#active",
            }
        )

        self.assert_rejected(packet, "stable trace_refs.search_set_after must point to backlog/repository-search-set.md")

    def test_stable_protected_packet_search_set_distinctness_uses_normalized_ref(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        before_ref = "trace:backlog/./repository-search-set.md#active"
        after_ref = "trace:backlog/repository-search-set.md#active"
        evidence["trace_refs"]["search_set_before"] = before_ref
        evidence["trace_refs"]["search_set_after"] = after_ref
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": before_ref,
                "status": "resolved",
                "target": "backlog/./repository-search-set.md#active",
            }
        )

        self.assert_rejected(packet, "search_set_before and search_set_after must be distinct")

    def test_stable_recorded_search_set_refs_are_distinct_even_for_routine_packets(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        trace_ref = "trace:backlog/repository-search-set.md#active"
        evidence["trace_refs"]["search_set_before"] = trace_ref
        evidence["trace_refs"]["search_set_after"] = trace_ref
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": trace_ref,
                "status": "resolved",
                "target": "backlog/repository-search-set.md#active",
            }
        )

        self.assert_rejected(packet, "search_set_before and search_set_after must be distinct")

    def test_stable_evolution_and_failure_traces_must_use_bucket_paths(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        bad_ref = "trace:README.md#ai-agent-meta-harness"
        evidence["trace_refs"]["evolution"] = [bad_ref]
        evidence["trace_refs"]["failures"] = [bad_ref]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": bad_ref,
                "status": "resolved",
                "target": "README.md#ai-agent-meta-harness",
            }
        )

        self.assert_rejected(packet, "stable trace_refs.evolution entries must point to .harness/traces/evolution/ evidence")
        self.assert_rejected(packet, "stable trace_refs.failures entries must point to .harness/traces/failures/ evidence")

    def test_stable_bucket_trace_refs_must_be_canonical(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        bad_ref = (
            "trace:.harness/traces/./evolution/"
            "001-repository-self-application-root.md#iteration-001-repository-self-application-trace-root"
        )
        evidence["trace_refs"]["evolution"] = [bad_ref]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "trace",
                "ref": bad_ref,
                "status": "resolved",
                "target": (
                    ".harness/traces/./evolution/"
                    "001-repository-self-application-root.md#iteration-001-repository-self-application-trace-root"
                ),
            }
        )

        self.assert_rejected(packet, "stable trace_refs.evolution entries must point to .harness/traces/evolution/ evidence")

    def test_stable_command_base_ref_must_match_boundary_refs(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["comparison_ref"] = "HEAD"

        self.assert_rejected(packet, "required_evidence must match checker-derived required evidence")

    def test_stable_boundary_refs_are_required(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        del packet["AcceptancePacket"]["result"]["evidence"]["baseline_ref"]
        del packet["AcceptancePacket"]["result"]["evidence"]["comparison_ref"]

        self.assert_rejected(packet, "stable packet baseline_ref is required")

    def test_stable_boundary_refs_must_be_commits(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        evidence["baseline_ref"] = "HEAD:README.md"
        evidence["comparison_ref"] = "HEAD:README.md"

        self.assert_rejected(packet, "baseline_ref must resolve to a git commit")

    def test_staged_stable_boundary_refs_must_match_head(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        stale_ref = "HEAD~1"
        evidence["baseline_ref"] = stale_ref
        evidence["comparison_ref"] = stale_ref

        self.assert_rejected(packet, "staged stable packet baseline_ref must match HEAD")

    def test_archive_v1_path_cannot_be_inferred_routine(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        inference = packet["AcceptancePacket"]["result"]["inference"]
        inference["changed_paths"] = ["archive/v1/README.md"]

        self.assert_rejected(packet, "protected changed paths require protected_boundary_changed")

    def test_stable_proof_like_docs_claim_without_raw_evidence_fails(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        inference = packet["AcceptancePacket"]["result"]["inference"]
        inference["changed_paths"] = ["docs/reference.md"]

        self.assert_rejected(packet, "proof-like changed docs")

    def test_stable_proof_like_docs_require_high_impact(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        result["inference"]["changed_paths"] = ["docs/reference.md"]
        packet["AcceptancePacket"]["input"]["source_refs"] = ["docs/reference.md"]
        evidence["source_refs"] = ["docs/reference.md"]
        evidence["claims"] = [
            {
                "raw_evidence_refs": [
                    "file:backlog/fixtures/multi-review/probe-transcripts/governance-pass-schema-contract.txt"
                ]
            }
        ]
        evidence["resolved_refs"] = [
            record for record in evidence["resolved_refs"] if record.get("relation") not in {"source", "claim-evidence"}
        ]
        evidence["resolved_refs"].extend(
            [
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/reference.md",
                    "status": "resolved",
                    "target": "docs/reference.md",
                },
                {
                    "origin": "generated",
                    "relation": "claim-evidence",
                    "ref": "file:backlog/fixtures/multi-review/probe-transcripts/governance-pass-schema-contract.txt",
                    "status": "resolved",
                    "target": "backlog/fixtures/multi-review/probe-transcripts/governance-pass-schema-contract.txt",
                },
            ]
        )

        self.assert_rejected(packet, "proof-like changed docs require impact: high")

    def test_stable_claim_evidence_requires_raw_artifact_file_scheme(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        evidence["claims"] = [{"raw_evidence_refs": ["README.md"]}]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "claim-evidence",
                "ref": "README.md",
                "status": "resolved",
                "target": "README.md",
            }
        )

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_trace_ref_requires_anchor(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        raw_ref = "trace:.harness/traces/evolution/001-repository-self-application-root.md"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "claim-evidence",
                "ref": raw_ref,
                "status": "resolved",
                "target": ".harness/traces/evolution/001-repository-self-application-root.md",
            }
        )

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_trace_ref_must_use_harness_trace(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        raw_ref = "trace:README.md#ai-agent-meta-harness"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "claim-evidence",
                "ref": raw_ref,
                "status": "resolved",
                "target": "README.md#ai-agent-meta-harness",
            }
        )

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_trace_ref_must_not_use_search_set_index(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        raw_ref = "trace:backlog/repository-search-set.md#active"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_rejects_any_search_set_file_anchor(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        raw_ref = "trace:backlog/repository-search-set.md#harness-search-set"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "claim-evidence",
                "ref": raw_ref,
                "status": "resolved",
                "target": "backlog/repository-search-set.md#harness-search-set",
            }
        )

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_normalizes_search_set_trace_path(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        raw_ref = "trace:backlog/./repository-search-set.md#active"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]
        evidence["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "claim-evidence",
                "ref": raw_ref,
                "status": "resolved",
                "target": "backlog/./repository-search-set.md#active",
            }
        )

        self.assert_rejected(packet, "claim evidence ref must use file: scheme")

    def test_stable_claim_evidence_rejects_source_file_as_raw_evidence(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        result["inference"]["changed_paths"] = ["docs/reference.md"]
        result["inference"]["required_review"] = ["claim evidence"]
        evidence["claims"] = [{"raw_evidence_refs": ["file:README.md"]}]
        evidence["resolved_refs"].extend(
            [
                {
                    "origin": "generated",
                    "relation": "claim-evidence",
                    "ref": "file:README.md",
                    "status": "resolved",
                    "target": "README.md",
                },
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:backlog/plans/04-evidence-capture-and-source-refs.md",
                    "status": "resolved",
                    "target": "backlog/plans/04-evidence-capture-and-source-refs.md",
                },
            ]
        )
        result["judgment"]["waivers"].append(
            {
                "kind": "review",
                "review": "claim evidence",
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "test isolates raw claim evidence classification",
                "source_ref": "file:backlog/plans/04-evidence-capture-and-source-refs.md",
            }
        )

        self.assert_rejected(packet, "claim evidence file ref must point to raw artifact/log/screenshot/report evidence")

    def test_stable_claim_evidence_file_ref_must_be_archive_local(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        evidence = result["evidence"]
        result["inference"]["changed_paths"] = ["docs/reference.md"]
        result["inference"]["required_review"] = ["claim evidence"]
        raw_ref = "file:backlog/fixtures/acceptance-packets/artifacts/verify-release-list-base-ref.log"
        evidence["claims"] = [{"raw_evidence_refs": [raw_ref]}]
        evidence["resolved_refs"].extend(
            [
                {
                    "origin": "generated",
                    "relation": "claim-evidence",
                    "ref": raw_ref,
                    "status": "resolved",
                    "target": raw_ref.removeprefix("file:"),
                },
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:backlog/plans/04-evidence-capture-and-source-refs.md",
                    "status": "resolved",
                    "target": "backlog/plans/04-evidence-capture-and-source-refs.md",
                },
            ]
        )
        result["judgment"]["waivers"].append(
            {
                "kind": "review",
                "review": "claim evidence",
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "test isolates archive-local raw claim evidence",
                "source_ref": "file:backlog/plans/04-evidence-capture-and-source-refs.md",
            }
        )

        self.assert_rejected(packet, "claim evidence file ref must point to raw artifact/log/screenshot/report evidence")

    def test_raw_claim_file_refs_must_be_under_archive_artifacts(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw_path = root / "archive" / "v2" / "raw.log"
            artifact_path = root / "archive" / "v2" / "artifacts" / "raw.log"
            raw_path.parent.mkdir(parents=True)
            artifact_path.parent.mkdir(parents=True)
            raw_path.write_text("raw\n", encoding="utf-8")
            artifact_path.write_text("raw\n", encoding="utf-8")

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/raw.log"))
            self.assertTrue(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/raw.log"))
            alias = root / "evidence" / "raw.log"
            alias.parent.mkdir()
            alias.symlink_to("../archive/v2/artifacts/raw.log")
            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:evidence/raw.log"))

    def test_raw_claim_file_refs_reject_diagnostic_strategy_search_yaml(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact_path = root / "archive" / "v2" / "artifacts" / "strategy-search-selection.yml"
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "strategy-search-adoption-selection/v1",
                        "evidence_status": "diagnostic_only",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            self.assertFalse(
                checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/strategy-search-selection.yml")
            )

    def test_raw_claim_file_refs_reject_strategy_search_diagnostic_logs(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact_dir = root / "archive" / "v2" / "artifacts"
            artifact_dir.mkdir(parents=True)
            stdout_path = artifact_dir / "stdout.log"
            named_path = artifact_dir / "strategy-search-stdout.log"
            stdout_path.write_text("score: 0.97\ncase: fresh-empty-repo: pass\n", encoding="utf-8")
            named_path.write_text("score: 0.97\ncase: fresh-empty-repo: pass\n", encoding="utf-8")

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/stdout.log"))
            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/strategy-search-stdout.log"))

    def test_raw_claim_file_refs_reject_hard_linked_strategy_search_logs(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "stdout.log"
            artifact = root / "archive" / "v2" / "artifacts" / "raw.log"
            source.parent.mkdir(parents=True)
            artifact.parent.mkdir(parents=True)
            source.write_text("score: 0.97\ncase: fresh-empty-repo: pass\n", encoding="utf-8")
            os.link(source, artifact)

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/raw.log"))

    def test_raw_claim_file_refs_reject_renamed_strategy_search_logs(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact = root / "archive" / "v2" / "artifacts" / "raw.log"
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                f"{'x' * 70000}\nSCORE = 0.97\ncase = fresh-empty-repo pass\n",
                encoding="utf-8",
            )

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/raw.log"))

    def test_raw_claim_file_refs_reject_strategy_search_namespace_logs(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact = root / "archive" / "v2" / "artifacts" / "strategy-search" / "raw.log"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("opaque diagnostic output\n", encoding="utf-8")

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/strategy-search/raw.log"))

    def test_raw_claim_file_refs_reject_strategy_search_jsonl_sidecars(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scores = root / "archive" / "v2" / "artifacts" / "scores.jsonl"
            proposals = root / "archive" / "v2" / "artifacts" / "proposals.jsonl"
            scores.parent.mkdir(parents=True)
            scores.write_text('{"schema_version":"strategy-search-candidate/v1"}\n', encoding="utf-8")
            proposals.write_text('{"schema_version":"strategy-search-proposal-ledger/v1"}\n', encoding="utf-8")

            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/scores.jsonl"))
            self.assertFalse(checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/proposals.jsonl"))

    def test_stable_generated_provenance_refs_require_file_scheme(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "waiver-provenance",
                "ref": "tests/test_governance_evidence_refs.py",
                "status": "resolved",
                "target": "tests/test_governance_evidence_refs.py",
            }
        )

        self.assert_rejected(packet, "generated waiver-provenance refs must use file: scheme")

    def test_stable_broad_skipped_evidence_fails(self) -> None:
        packet = load_fixture("finalized-waiver-downgrade.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["skipped"].append(
            {
                "evidence": "all search-set evidence",
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "broad skip",
                "source_ref": "file:backlog/plans/04-evidence-capture-and-source-refs.md",
            }
        )

        self.assert_rejected(packet, "skipped evidence is not required")

    def test_stable_skipped_provenance_source_ref_must_resolve(self) -> None:
        packet = load_fixture("finalized-waiver-downgrade.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"] = [
            record
            for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]
            if record["relation"] != "waiver-provenance"
        ]

        self.assert_rejected(packet, "source_ref lacks resolved waiver-provenance relation")

    def test_stable_review_provenance_source_ref_must_resolve(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0]["source_ref"] = "terminal:lost-review"

        self.assert_rejected(packet, "source_ref lacks resolved review-provenance relation")


if __name__ == "__main__":
    unittest.main()
