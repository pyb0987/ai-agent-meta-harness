from __future__ import annotations

import copy
import hashlib
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
IMPORT_REF = "file:backlog/fixtures/acceptance-packets/artifacts/harness-affecting-review-import.yml"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AI_META_HARNESS_TEST_FIXTURE_MATERIALIZATION"] = "1"
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_checker():
    spec = importlib.util.spec_from_file_location("check_governance_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def probe_transcript(
    command: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    *,
    result_ref: str = "file:backlog/fixtures/acceptance-packets/artifacts/harness-affecting-review-import.yml",
    result_digest: str = "0" * 64,
    packet_ref: str | None = "backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml",
    packet_sha256: str | None = "0" * 64,
    source_refs: list[str] | None = None,
) -> dict:
    if source_refs is None:
        source_refs = ["scripts/check-governance-acceptance.py"]
    return {
        "ProbeTranscript": {
            "schema_version": "probe-transcript/v1",
            "probe_command": command,
            "probe_exit_code": exit_code,
            "result_ref": result_ref,
            "result_digest": result_digest,
            "packet_ref": packet_ref,
            "packet_sha256": packet_sha256,
            "source_refs": source_refs,
            "cwd": ".",
            "generated_by": "test",
            "date": "2026-05-06",
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        }
    }


class GovernanceReviewImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = load_checker()
        self.tmp = tempfile.TemporaryDirectory(dir=FIXTURE_ROOT)
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        (self.tmp_path / ".fixture-materialization").write_text(
            "acceptance-packet-fixture-materialization/v1\n",
            encoding="utf-8",
        )
        self.rel_dir = self.tmp_path.relative_to(ROOT).as_posix()

    def materialize_packet(
        self,
        *,
        mutate_packet=None,
        mutate_wrapper=None,
        mutate_after_digest=None,
    ) -> Path:
        packet_doc = load_yaml(FIXTURE_ROOT / "finalized-harness-affecting.yml")
        packet = packet_doc["AcceptancePacket"]
        wrapper_doc = load_yaml(FIXTURE_ROOT / "artifacts" / "harness-affecting-review-import.yml")
        wrapper = wrapper_doc["AcceptancePacketReviewImport"]
        packet_ref = f"{self.rel_dir}/packet.yml"
        import_ref = f"file:{self.rel_dir}/review-import.yml"

        artifact_refs = [
            f"file:{self.rel_dir}/cmd-verify-release-list.log",
            f"file:{self.rel_dir}/cmd-v1-archive-boundary.log",
            f"file:{self.rel_dir}/cmd-release-tests.log",
        ]
        artifact_targets = [ref.removeprefix("file:") for ref in artifact_refs]
        for command_result, artifact_ref in zip(packet["result"]["evidence"]["command_results"], artifact_refs):
            command_result["artifact_ref"] = artifact_ref
        resolved_refs = [
            record
            for record in packet["result"]["evidence"]["resolved_refs"]
            if record["relation"] not in {"artifact", "review-provenance"}
        ]
        for artifact_ref, target in zip(artifact_refs, artifact_targets):
            resolved_refs.append(
                {
                    "origin": "generated",
                    "relation": "artifact",
                    "ref": artifact_ref,
                    "status": "resolved",
                    "target": target,
                }
            )
        resolved_refs.append(
            {
                "origin": "generated",
                "relation": "review-provenance",
                "ref": import_ref,
                "status": "resolved",
                "target": import_ref.removeprefix("file:"),
            }
        )
        packet["result"]["evidence"]["resolved_refs"] = resolved_refs
        binding = self.checker.review_target_binding(packet, root=ROOT, packet_ref=packet_ref)
        wrapper["target_binding"] = copy.deepcopy(binding)
        target_refs = wrapper["MultiReviewResult"]["target"]["source_refs"]
        if packet_ref not in target_refs:
            target_refs.append(packet_ref)
        for review in wrapper["review_lineage"]:
            review["source_ref"] = import_ref
        if mutate_wrapper:
            mutate_wrapper(wrapper)
        for index, critic in enumerate(wrapper["MultiReviewResult"]["critics"]):
            critic_id = str(critic.get("critic_id", f"critic-{index}")).replace("/", "-")
            critic["probe_evidence_refs"] = [f"file:{self.rel_dir}/probe-{critic_id}.yml"]
        packet["result"]["judgment"]["reviews"] = copy.deepcopy(wrapper["review_lineage"])
        packet["result"]["evidence"]["review_imports"] = [
            {
                "source_ref": import_ref,
                "format": "acceptance-packet-review-import/v1",
                "source_digest": "",
                "status": "imported",
                "review_ids": [review["review_id"] for review in wrapper["review_lineage"]],
                "target_binding": copy.deepcopy(binding),
            }
        ]
        if mutate_packet:
            mutate_packet(packet)

        wrapper_path = self.tmp_path / "review-import.yml"
        wrapper_path.write_text(yaml.safe_dump({"AcceptancePacketReviewImport": wrapper}, sort_keys=False), encoding="utf-8")
        digest = hashlib.sha256(wrapper_path.read_bytes()).hexdigest()
        if packet["result"]["evidence"].get("review_imports"):
            packet["result"]["evidence"]["review_imports"][0]["source_digest"] = digest
        if mutate_after_digest:
            mutate_after_digest(packet, wrapper_path)
        packet_path = self.tmp_path / "packet.yml"
        packet_path.write_text(yaml.safe_dump({"AcceptancePacket": packet}, sort_keys=False), encoding="utf-8")
        packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        wrapper_digest = hashlib.sha256(wrapper_path.read_bytes()).hexdigest()
        for critic in wrapper["MultiReviewResult"]["critics"]:
            probe_ref = critic["probe_evidence_refs"][0]
            (ROOT / probe_ref.removeprefix("file:")).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        critic["probe_command"],
                        critic["probe_exit_code"],
                        result_ref=import_ref,
                        result_digest=wrapper_digest,
                        packet_ref=packet_ref,
                        packet_sha256=packet_sha,
                        source_refs=critic["source_refs"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
        for command_result, artifact_ref in zip(packet["result"]["evidence"]["command_results"], artifact_refs):
            artifact_path = ROOT / artifact_ref.removeprefix("file:")
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        f"packet_id: {packet['meta']['packet_id']}",
                        f"packet_ref: {packet_ref}",
                        f"packet_sha256: {packet_sha}",
                        f"command: {command_result['command']}",
                        f"status: {command_result['status']}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        return packet_path

    def assert_rejected(self, packet_path: Path, expected: str) -> None:
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def test_accepts_target_bound_review_import_fixture(self) -> None:
        packet_path = self.materialize_packet()
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_review_target_digest_is_order_insensitive_but_target_sensitive(self) -> None:
        packet_doc = load_yaml(FIXTURE_ROOT / "finalized-harness-affecting.yml")
        packet = packet_doc["AcceptancePacket"]
        packet_ref = "backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml"
        baseline = self.checker.review_target_digest(packet, root=ROOT, packet_ref=packet_ref)
        reordered = copy.deepcopy(packet)
        reordered["input"]["source_refs"] = list(reversed(reordered["input"]["source_refs"]))
        reordered["result"]["inference"]["changed_paths"] = list(reversed(reordered["result"]["inference"]["changed_paths"]))
        changed = copy.deepcopy(packet)
        changed["result"]["inference"]["changed_paths"].append("scripts/new-review-surface.py")

        self.assertEqual(baseline, self.checker.review_target_digest(reordered, root=ROOT, packet_ref=packet_ref))
        self.assertNotEqual(baseline, self.checker.review_target_digest(changed, root=ROOT, packet_ref=packet_ref))

    def test_rejects_required_review_erasure_or_misdirection(self) -> None:
        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["inference"].__setitem__("required_review", ["unrelated"])
        )

        self.assert_rejected(packet_path, "required_review must match checker-derived required reviews")

        def add_extra_required_review(packet: dict) -> None:
            packet["result"]["inference"]["required_review"].append("unrelated authored review")

        packet_path = self.materialize_packet(mutate_packet=add_extra_required_review)
        self.assert_rejected(packet_path, "required_review must match checker-derived required reviews")

    def test_rejects_wrong_packet_or_stale_target_binding(self) -> None:
        def mutate_wrapper(wrapper: dict) -> None:
            wrapper["target_binding"]["packet_id"] = "pkt-other"

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)

        self.assert_rejected(packet_path, "wrapper target_binding does not match current packet review target")

    def test_rejects_multi_review_target_not_bound_to_packet(self) -> None:
        def mutate_wrapper(wrapper: dict) -> None:
            wrapper["MultiReviewResult"]["target"]["source_refs"] = ["scripts/check-governance-acceptance.py"]

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)

        self.assert_rejected(packet_path, "target.source_refs must include current packet ref")

    def test_rejects_malformed_target_binding_without_traceback(self) -> None:
        def mutate_packet(packet: dict) -> None:
            packet["input"]["intent"] = {1: "bad", "x": "bad"}

        packet_path = self.materialize_packet(mutate_packet=mutate_packet)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.intent must be a non-empty string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_mixed_type_target_binding_keys_without_traceback(self) -> None:
        def mutate_packet(packet: dict) -> None:
            binding = dict(packet["result"]["evidence"]["review_imports"][0]["target_binding"])
            binding[1] = "malformed"
            packet["result"]["evidence"]["review_imports"][0]["target_binding"] = binding

        packet_path = self.materialize_packet(mutate_packet=mutate_packet)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target_binding fields must be exactly", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_mixed_type_review_import_keys_without_traceback(self) -> None:
        def mutate_packet(packet: dict) -> None:
            packet["result"]["evidence"]["review_imports"][0][1] = "malformed"

        packet_path = self.materialize_packet(mutate_packet=mutate_packet)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review import extra fields", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_vacuous_review_lineage_fields(self) -> None:
        def mutate_wrapper(wrapper: dict) -> None:
            wrapper["review_lineage"][0]["false_green_risk"] = "pass"
            wrapper["review_lineage"][0]["invariant_checked"] = "pass"

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)

        self.assert_rejected(packet_path, "false_green_risk must be substantive")

    def test_rejects_boolean_review_lineage_evidence(self) -> None:
        def mutate_wrapper(wrapper: dict) -> None:
            wrapper["review_lineage"][0]["evidence"] = [True]

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)

        self.assert_rejected(packet_path, "evidence[0] must be a substantive string")

    def test_rejects_non_list_review_lineage_without_traceback(self) -> None:
        def mutate_after_digest(packet: dict, wrapper_path: Path) -> None:
            wrapper_doc = load_yaml(wrapper_path)
            wrapper_doc["AcceptancePacketReviewImport"]["review_lineage"] = 1
            wrapper_path.write_text(yaml.safe_dump(wrapper_doc, sort_keys=False), encoding="utf-8")
            packet["result"]["evidence"]["review_imports"][0]["source_digest"] = hashlib.sha256(
                wrapper_path.read_bytes()
            ).hexdigest()

        packet_path = self.materialize_packet(mutate_after_digest=mutate_after_digest)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_lineage must be a non-empty list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_source_digest_drift(self) -> None:
        def mutate_after_digest(packet: dict, wrapper_path: Path) -> None:
            text = wrapper_path.read_text(encoding="utf-8")
            wrapper_path.write_text(text.replace("Fixture is illustrative", "Fixture drifted"), encoding="utf-8")

        packet_path = self.materialize_packet(mutate_after_digest=mutate_after_digest)

        self.assert_rejected(packet_path, "source_digest does not match current artifact bytes")

    def test_rejects_advisory_multi_review_import(self) -> None:
        def mutate_wrapper(wrapper: dict) -> None:
            wrapper["MultiReviewResult"]["review_mode"] = "advisory"

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)

        self.assert_rejected(packet_path, "must freshly derive governance PASS")

    def test_stable_check_does_not_replay_imported_probe_command(self) -> None:
        sentinel = self.tmp_path / "probe-ran.txt"
        rel_sentinel = sentinel.relative_to(ROOT).as_posix()
        rel_transcript = (self.tmp_path / "malicious-probe-transcript.yml").relative_to(ROOT).as_posix()
        command = f"python3 -c \"from pathlib import Path; Path('{rel_sentinel}').write_text('ran')\""
        (ROOT / rel_transcript).write_text(
            yaml.safe_dump(probe_transcript(command, 0), sort_keys=False),
            encoding="utf-8",
        )

        def mutate_wrapper(wrapper: dict) -> None:
            critic = wrapper["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = command
            critic["probe_result"] = "Command is represented as durable replay evidence only."
            critic["probe_interpretation"] = "Stable check must not execute imported probe commands."
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]

        packet_path = self.materialize_packet(mutate_wrapper=mutate_wrapper)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())

    def test_rejects_partial_mirror_in_both_directions(self) -> None:
        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["judgment"]["reviews"].pop()
        )
        self.assert_rejected(packet_path, "missing imported review_lineage records")

        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["judgment"]["reviews"][0].__setitem__(
                "false_green_risk", "packet-only edit"
            )
        )
        self.assert_rejected(packet_path, "field does not mirror imported review_lineage")

    def test_rejects_review_ids_mismatch_and_duplicate_ids(self) -> None:
        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["evidence"]["review_imports"][0].__setitem__(
                "review_ids", ["review-harness-checker-correctness"]
            )
        )
        self.assert_rejected(packet_path, "review_ids must match imported review_lineage ids")

        def duplicate(wrapper: dict) -> None:
            wrapper["review_lineage"][1]["review_id"] = wrapper["review_lineage"][0]["review_id"]

        packet_path = self.materialize_packet(mutate_wrapper=duplicate)
        self.assert_rejected(packet_path, "duplicate review_id")

    def test_rejects_duplicate_passing_review_closure_for_same_target(self) -> None:
        def duplicate_passing_checker_review(wrapper: dict) -> None:
            duplicate = copy.deepcopy(wrapper["review_lineage"][0])
            duplicate["review_id"] = "review-harness-checker-correctness-duplicate"
            wrapper["review_lineage"].insert(1, duplicate)

        packet_path = self.materialize_packet(mutate_wrapper=duplicate_passing_checker_review)

        self.assert_rejected(packet_path, "required review has multiple closures")

    def test_rejects_invalid_format_status_or_markdown_only_provenance(self) -> None:
        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["evidence"]["review_imports"][0].__setitem__(
                "format", "multi-review-json-v1"
            )
        )
        self.assert_rejected(packet_path, "format must be acceptance-packet-review-import/v1")

        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["evidence"]["review_imports"][0].__setitem__(
                "status", "claimed"
            )
        )
        self.assert_rejected(packet_path, "status must be imported")

        def markdown_only(packet: dict) -> None:
            packet["result"]["evidence"].pop("review_imports")
            for review in packet["result"]["judgment"]["reviews"]:
                review["source_ref"] = IMPORT_REF

        packet_path = self.materialize_packet(mutate_packet=markdown_only)
        self.assert_rejected(packet_path, "stable packet reviews require result.evidence.review_imports")

    def test_rejects_non_string_packet_review_source_ref_without_traceback(self) -> None:
        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["judgment"]["reviews"][0].__setitem__(
                "source_ref", ["file:review-import.yml"]
            )
        )
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_ref must point to an imported structured review artifact", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_unclosed_veto_and_wrong_critic_rerun(self) -> None:
        def add_unclosed_veto(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            wrapper["review_lineage"].insert(0, failed)

        packet_path = self.materialize_packet(mutate_wrapper=add_unclosed_veto)
        self.assert_rejected(packet_path, "unclosed blocking review")

        def wrong_critic_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][1])
            rerun.update({"review_id": "review-harness-wrong-rerun", "rerun_of": failed["review_id"], "fixed_finding_ids": ["F1"]})
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=wrong_critic_rerun)
        self.assert_rejected(packet_path, "must use same critic")

    def test_accepts_failed_review_with_exact_same_critic_rerun_closure(self) -> None:
        def add_closed_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "scope": "Rerun checker correctness after adding target binding replay coverage.",
                    "score": 9,
                    "veto": False,
                    "blocking_findings": [],
                    "why_not_10": "The fixture still does not represent an archived packet.",
                    "disposition": "Accepted because the blocking finding is fixed by targeted tests.",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_closed_rerun)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_rerun_without_date_provenance(self) -> None:
        def add_rerun_without_date(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "score": 9,
                    "veto": False,
                    "blocking_findings": [],
                    "why_not_10": "Rerun covers the blocking finding.",
                    "disposition": "Accepted.",
                    "date": None,
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_rerun_without_date)

        self.assert_rejected(packet_path, "date must be an ISO date")

    def test_rejects_future_dated_rerun_provenance(self) -> None:
        def add_future_dated_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "score": 9,
                    "veto": False,
                    "blocking_findings": [],
                    "why_not_10": "Rerun covers the blocking finding.",
                    "disposition": "Accepted.",
                    "date": "2099-01-01",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_future_dated_rerun)

        self.assert_rejected(packet_path, "date must be an ISO date")

    def test_rejects_rerun_dated_before_blocking_review(self) -> None:
        def add_backdated_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "date": "2026-05-07",
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "score": 9,
                    "veto": False,
                    "date": "2026-05-06",
                    "blocking_findings": [],
                    "why_not_10": "Rerun claims to cover the blocking finding.",
                    "disposition": "Accepted.",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_backdated_rerun)

        self.assert_rejected(packet_path, "date must not precede rerun_of review date")

    def test_rejects_duplicate_blocking_finding_ids(self) -> None:
        def add_duplicate_finding_ids(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [
                        {"finding_id": "F1", "summary": "First finding."},
                        {"finding_id": "F1", "summary": "Different finding with same id."},
                    ],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "score": 9,
                    "veto": False,
                    "blocking_findings": [],
                    "why_not_10": "Rerun claims to close duplicate finding ids.",
                    "disposition": "Accepted.",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_duplicate_finding_ids)

        self.assert_rejected(packet_path, "duplicate blocking finding_id: F1")

    def test_rejects_malformed_rerun_fields_without_traceback(self) -> None:
        def add_malformed_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "rerun_of": [failed["review_id"]],
                    "fixed_finding_ids": [{"id": "F1"}],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_malformed_rerun)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rerun_of must be a review_id string", result.stderr)
        self.assertIn("fixed_finding_ids must contain only substantive string ids", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_empty_rerun_container_without_traceback(self) -> None:
        def add_empty_rerun_container(wrapper: dict) -> None:
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update({"review_id": "review-empty-rerun", "rerun_of": [], "fixed_finding_ids": []})
            wrapper["review_lineage"] = [rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_empty_rerun_container)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rerun_of must be a review_id string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_rejects_duplicate_fixed_finding_ids(self) -> None:
        def add_duplicate_fixed_ids(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1", "F1"],
                }
            )
            wrapper["review_lineage"] = [failed, rerun, *wrapper["review_lineage"][1:]]

        packet_path = self.materialize_packet(mutate_wrapper=add_duplicate_fixed_ids)
        result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed_finding_ids must not contain duplicates", result.stderr)

    def test_rejects_rerun_that_precedes_failed_review(self) -> None:
        def add_reversed_rerun(wrapper: dict) -> None:
            failed = copy.deepcopy(wrapper["review_lineage"][0])
            failed.update(
                {
                    "review_id": "review-harness-checker-failed",
                    "score": 8,
                    "veto": True,
                    "blocking_findings": [{"finding_id": "F1", "summary": "Missing target binding replay test."}],
                    "why_not_10": None,
                    "disposition": None,
                }
            )
            rerun = copy.deepcopy(wrapper["review_lineage"][0])
            rerun.update(
                {
                    "review_id": "review-harness-checker-rerun",
                    "scope": "Rerun checker correctness before the failed record appears.",
                    "rerun_of": failed["review_id"],
                    "fixed_finding_ids": ["F1"],
                }
            )
            wrapper["review_lineage"] = [rerun, failed, *wrapper["review_lineage"]]

        packet_path = self.materialize_packet(mutate_wrapper=add_reversed_rerun)

        self.assert_rejected(packet_path, "must appear after rerun_of review")

    def test_rejects_generic_false_green_and_broad_not_required_bypass(self) -> None:
        packet_path = self.materialize_packet(
            mutate_wrapper=lambda wrapper: wrapper["review_lineage"][0].__setitem__("false_green_risk", "generic")
        )
        self.assert_rejected(packet_path, "false_green_risk must be substantive")

        packet_path = self.materialize_packet(
            mutate_wrapper=lambda wrapper: wrapper["review_lineage"][0].update(
                {"false_green_risk": "none.", "invariant_checked": "checked."}
            )
        )
        self.assert_rejected(packet_path, "false_green_risk must be substantive")

        packet_path = self.materialize_packet(
            mutate_wrapper=lambda wrapper: wrapper["review_lineage"][0].update(
                {"false_green_risk": "N.A.", "invariant_checked": "N.A."}
            )
        )
        self.assert_rejected(packet_path, "false_green_risk must be substantive")

        packet_path = self.materialize_packet(
            mutate_wrapper=lambda wrapper: wrapper["review_lineage"][0].__setitem__(
                "false_green_risk", ["list wrapped risk"]
            )
        )
        self.assert_rejected(packet_path, "false_green_risk must be substantive")

        packet_path = self.materialize_packet(
            mutate_packet=lambda packet: packet["result"]["judgment"]["waivers"].append(
                {
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "review": "not required",
                    "reason": "broad bypass",
                    "source_ref": "file:backlog/plans/02-acceptance-packet-schema-and-fixtures.md",
                }
            )
        )
        self.assert_rejected(packet_path, "exception target is not required")


if __name__ == "__main__":
    unittest.main()
