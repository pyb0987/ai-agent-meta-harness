from __future__ import annotations

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

        self.assert_rejected(packet, "stable protected packet missing search_set_before")

    def test_stable_command_base_ref_must_match_boundary_refs(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        packet["AcceptancePacket"]["result"]["evidence"]["comparison_ref"] = "HEAD"

        self.assert_rejected(packet, "stable command base-ref origin/main must match evidence.comparison_ref")

    def test_stable_boundary_refs_are_required(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        del packet["AcceptancePacket"]["result"]["evidence"]["baseline_ref"]
        del packet["AcceptancePacket"]["result"]["evidence"]["comparison_ref"]

        self.assert_rejected(packet, "stable packet baseline_ref is required")

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
