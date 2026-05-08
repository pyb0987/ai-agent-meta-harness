from __future__ import annotations

import importlib.util
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


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, encoding="utf-8", text=True, check=True, stdout=subprocess.PIPE)


class GovernanceEvidenceFalseGreenTests(unittest.TestCase):
    def assert_rejected(self, packet: dict, expected: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "packet.yml"
            path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            result = run_cli("check", "--packet", str(path), "--require-stable")

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def test_stable_required_evidence_cannot_be_erased(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        result["inference"]["required_evidence"] = []
        result["evidence"]["command_results"] = []

        self.assert_rejected(packet, "required_evidence must match checker-derived required evidence")

    def test_stable_required_evidence_cannot_be_spoofed(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        result["inference"]["required_evidence"] = ["python3 scripts/not-the-checker.py"]
        result["evidence"]["command_results"][0]["command"] = "python3 scripts/not-the-checker.py"

        self.assert_rejected(packet, "required_evidence must match checker-derived required evidence")

    def test_stable_evaluator_boundary_commands_are_required(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        result["evidence"]["evaluator_boundary"]["commands"] = []

        self.assert_rejected(packet, "evaluator_boundary.commands must match checker-derived required evidence")

    def test_stable_evidence_obligations_cannot_move_with_packet_authored_boundary(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        result = packet["AcceptancePacket"]["result"]
        command = "python3 scripts/verify-release.py"
        result["inference"]["required_evidence"] = [command]
        result["evidence"]["evaluator_boundary"]["commands"] = [command]
        result["evidence"]["command_results"][0]["command"] = command
        result["evidence"]["command_results"][0]["artifact_ref"] = (
            "file:backlog/fixtures/acceptance-packets/artifacts/verify-release.log"
        )
        result["evidence"]["resolved_refs"][-1] = {
            "origin": "generated",
            "relation": "artifact",
            "ref": "file:backlog/fixtures/acceptance-packets/artifacts/verify-release.log",
            "status": "resolved",
            "target": "backlog/fixtures/acceptance-packets/artifacts/verify-release.log",
        }

        self.assert_rejected(packet, "required_evidence must match checker-derived required evidence")

    def test_stable_packet_cannot_reuse_command_artifact_from_another_packet(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        acceptance_packet = packet["AcceptancePacket"]
        acceptance_packet["meta"]["packet_id"] = "pkt-finalized-routine-example"
        acceptance_packet["meta"]["mode"] = "staged"
        acceptance_packet["input"]["source_refs"] = ["backlog/fixtures/acceptance-packets/README.md"]
        result = acceptance_packet["result"]
        result["inference"].update(
            {
                "change_class": "routine",
                "impact": "low",
                "changed_paths": ["backlog/fixtures/acceptance-packets/README.md"],
                "protected_boundary_changed": False,
                "required_evidence": ["git diff --cached --check"],
                "required_review": [],
            }
        )
        evidence = result["evidence"]
        evidence["baseline_ref"] = "HEAD"
        evidence["comparison_ref"] = "HEAD"
        evidence["evaluator_boundary"] = {"status": "unchanged", "commands": ["git diff --cached --check"]}
        evidence["command_results"] = [
            {
                "command": "git diff --cached --check",
                "status": "pass",
                "artifact_ref": "file:backlog/fixtures/acceptance-packets/artifacts/git-diff-check.log",
            }
        ]
        evidence["source_refs"] = ["backlog/fixtures/acceptance-packets/README.md"]
        evidence["resolved_refs"] = [
            {
                "origin": "input",
                "relation": "source",
                "ref": "backlog/fixtures/acceptance-packets/README.md",
                "status": "resolved",
                "target": "backlog/fixtures/acceptance-packets/README.md",
            },
            {
                "origin": "generated",
                "relation": "artifact",
                "ref": "file:backlog/fixtures/acceptance-packets/artifacts/git-diff-check.log",
                "status": "resolved",
                "target": "backlog/fixtures/acceptance-packets/artifacts/git-diff-check.log",
            },
        ]
        result["judgment"]["reviews"] = []
        result["judgment"]["residual_risk"] = []

        self.assert_rejected(packet, "stable command artifact does not record command evidence")

    def test_stable_command_artifact_packet_ref_match_is_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text("note\n", encoding="utf-8")
            (root / "artifacts").mkdir()
            (root / "artifacts" / "git-diff-check.log").write_text(
                "\n".join(
                    [
                        "packet_id: pkt-prefix-probe",
                        "packet_ref: packets/pkt.yml",
                        "command: git diff --cached --check",
                        "status: pass",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            git(root, "init")
            git(root, "config", "user.name", "Test")
            git(root, "config", "user.email", "test@example.com")
            git(root, "add", "-A")
            git(root, "commit", "-m", "initial")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["packet_id"] = "pkt-prefix-probe"
            acceptance_packet["input"]["source_refs"] = ["docs/note.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/note.md"]
            result["evidence"]["source_refs"] = ["docs/note.md"]
            result["evidence"]["command_results"][0]["artifact_ref"] = "file:artifacts/git-diff-check.log"
            result["evidence"]["resolved_refs"] = [
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/note.md",
                    "status": "resolved",
                    "target": "docs/note.md",
                },
                {
                    "origin": "generated",
                    "relation": "artifact",
                    "ref": "file:artifacts/git-diff-check.log",
                    "status": "resolved",
                    "target": "artifacts/git-diff-check.log",
                },
            ]
            packet_path = root / "packets" / "pkt"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_stable_file_ref_cannot_escape_repository_root(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        acceptance_packet = packet["AcceptancePacket"]
        acceptance_packet["input"]["source_refs"] = ["file:/etc/hosts"]
        evidence = acceptance_packet["result"]["evidence"]
        evidence["source_refs"] = ["file:/etc/hosts"]
        evidence["resolved_refs"][0] = {
            "origin": "input",
            "relation": "source",
            "ref": "file:/etc/hosts",
            "status": "resolved",
            "target": "/etc/hosts",
        }

        self.assert_rejected(packet, "resolved ref does not resolve: file:/etc/hosts")

    def test_stable_bare_ref_cannot_escape_repository_root(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        acceptance_packet = packet["AcceptancePacket"]
        acceptance_packet["input"]["source_refs"] = ["/etc/hosts"]
        evidence = acceptance_packet["result"]["evidence"]
        evidence["source_refs"] = ["/etc/hosts"]
        evidence["resolved_refs"][0] = {
            "origin": "input",
            "relation": "source",
            "ref": "/etc/hosts",
            "status": "resolved",
            "target": "/etc/hosts",
        }

        self.assert_rejected(packet, "resolved ref does not resolve: /etc/hosts")

    def test_stable_parent_traversal_file_ref_cannot_escape_repository_root(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        acceptance_packet = packet["AcceptancePacket"]
        escape_ref = "file:../README.md"
        acceptance_packet["input"]["source_refs"] = [escape_ref]
        evidence = acceptance_packet["result"]["evidence"]
        evidence["source_refs"] = [escape_ref]
        evidence["resolved_refs"][0] = {
            "origin": "input",
            "relation": "source",
            "ref": escape_ref,
            "status": "resolved",
            "target": "../README.md",
        }

        self.assert_rejected(packet, f"resolved ref does not resolve: {escape_ref}")

    def test_stable_base_ref_equals_form_must_match_boundary_refs(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        result = packet["AcceptancePacket"]["result"]
        commands = [
            "python3 scripts/verify-release.py --list --base-ref=origin/main --skip-clean-worktree",
            "python3 scripts/check-v1-archive-boundary.py --base-ref=origin/main",
        ]
        result["inference"]["required_evidence"][0] = commands[0]
        result["inference"]["required_evidence"][1] = commands[1]
        result["evidence"]["command_results"][0]["command"] = commands[0]
        result["evidence"]["command_results"][1]["command"] = commands[1]
        result["evidence"]["baseline_ref"] = "HEAD"
        result["evidence"]["comparison_ref"] = "HEAD"

        self.assert_rejected(packet, "required_evidence must match checker-derived required evidence")

    def test_command_base_ref_parses_equals_form(self) -> None:
        checker = load_checker()

        self.assertEqual(
            checker.command_base_ref("python3 scripts/check-v1-archive-boundary.py --base-ref=origin/main"),
            "origin/main",
        )

    def test_stable_command_artifact_cannot_be_unrelated_file(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        evidence = packet["AcceptancePacket"]["result"]["evidence"]
        evidence["command_results"][0]["artifact_ref"] = "file:README.md"
        evidence["resolved_refs"][-1] = {
            "origin": "generated",
            "relation": "artifact",
            "ref": "file:README.md",
            "status": "resolved",
            "target": "README.md",
        }

        self.assert_rejected(packet, "stable command artifact does not record command evidence")

    def test_stable_protected_source_ref_cannot_hide_behind_routine_changed_path(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        acceptance_packet = packet["AcceptancePacket"]
        protected_ref = "scripts/check-governance-acceptance.py"
        acceptance_packet["input"]["source_refs"].append(protected_ref)
        evidence = acceptance_packet["result"]["evidence"]
        evidence["source_refs"].append(protected_ref)
        evidence["resolved_refs"].append(
            {
                "origin": "input",
                "relation": "source",
                "ref": protected_ref,
                "status": "resolved",
                "target": protected_ref,
            }
        )

        self.assert_rejected(packet, "stable packet source_ref points to protected path outside changed_paths")

    def test_stable_review_provenance_must_match_review_record(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        result = packet["AcceptancePacket"]["result"]
        for review in result["judgment"]["reviews"]:
            review["source_ref"] = "file:README.md"
        result["evidence"]["resolved_refs"] = [
            record
            for record in result["evidence"]["resolved_refs"]
            if record["relation"] != "review-provenance"
        ]
        result["evidence"]["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "review-provenance",
                "ref": "file:README.md",
                "status": "resolved",
                "target": "README.md",
            }
        )

        self.assert_rejected(packet, "review-provenance source_ref lacks matching review record")

    def test_stable_review_provenance_cannot_be_self_attested_packet(self) -> None:
        packet = load_fixture("finalized-harness-affecting.yml")
        result = packet["AcceptancePacket"]["result"]
        source_ref = "file:backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml"
        for review in result["judgment"]["reviews"]:
            review["source_ref"] = source_ref
        result["evidence"]["resolved_refs"] = [
            record
            for record in result["evidence"]["resolved_refs"]
            if record["relation"] != "review-provenance"
        ]
        result["evidence"]["resolved_refs"].append(
            {
                "origin": "generated",
                "relation": "review-provenance",
                "ref": source_ref,
                "status": "resolved",
                "target": "backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml",
            }
        )

        self.assert_rejected(packet, "review-provenance source_ref cannot be an acceptance packet")


if __name__ == "__main__":
    unittest.main()
