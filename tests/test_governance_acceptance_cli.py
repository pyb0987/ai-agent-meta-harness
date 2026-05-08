from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-governance-acceptance.py"
FIXTURE_ROOT = ROOT / "backlog" / "fixtures" / "acceptance-packets"


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("initial\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-m", "initial")


class GovernanceAcceptanceCliTests(unittest.TestCase):
    def test_check_accepts_plan_02_fixtures(self) -> None:
        for path in sorted(FIXTURE_ROOT.glob("*.yml")):
            with self.subTest(path=path.name):
                result = run_cli("check", "--packet", str(path))

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_output_separates_valid_from_stable(self) -> None:
        nonstable = run_cli("check", "--packet", str(FIXTURE_ROOT / "worktree-nonstable.yml"))
        stable = run_cli("check", "--packet", str(FIXTURE_ROOT / "finalized-routine.yml"), "--require-stable")

        self.assertEqual(nonstable.returncode, 0, nonstable.stderr)
        self.assertIn("VALID: not stable-handoff eligible", nonstable.stdout)
        self.assertNotIn("PASS", nonstable.stdout)
        self.assertEqual(stable.returncode, 0, stable.stderr)
        self.assertIn("STABLE:", stable.stdout)

    def test_require_stable_rejects_valid_nonstable_packet(self) -> None:
        result = run_cli(
            "check",
            "--packet",
            str(FIXTURE_ROOT / "worktree-nonstable.yml"),
            "--require-stable",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not stable-handoff eligible", result.stderr)

    def test_check_rejects_untargeted_input_exception_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["review_downgrade_request"].pop("from")
            packet["AcceptancePacket"]["input"]["user_judgment"]["review_downgrade_request"].pop("to")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.review_downgrade_request", result.stderr)

    def test_check_rejects_input_exception_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["waiver_request"].pop("actor")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("actor is required", result.stderr)

    def test_check_rejects_residual_input_judgment_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["residual_risk_request"] = {
                "reason": "accept a small residual risk"
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.residual_risk_request: actor is required", result.stderr)

    def test_check_rejects_untargeted_residual_input_judgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["residual_risk_request"] = {
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "accept a small residual risk",
                "source_ref": "file:tests/test_governance_acceptance_cli.py",
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.residual_risk_request: residual risk must target", result.stderr)

    def test_check_rejects_extra_meta_or_input_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["change_class"] = "routine"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input fields must be exactly", result.stderr)

    def test_check_rejects_stable_packet_without_generated_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"] = {}
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.change_class is required", result.stderr)

    def test_check_rejects_container_required_targets_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_review"] = [["checker correctness"]]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_evidence"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_evidence must be a list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_non_mapping_stable_records_without_traceback(self) -> None:
        cases = [
            ("result.evidence.command_results", "command_results", "result.evidence.command_results[0] must be a mapping"),
            ("result.evidence.skipped", "skipped", "result.evidence.skipped[0] must be a mapping"),
            ("result.judgment.reviews", "reviews", "result.judgment.reviews[0] must be a mapping"),
            ("result.judgment.waivers", "waivers", "result.judgment.waivers[0] must be a mapping"),
            ("result.judgment.downgrades", "downgrades", "result.judgment.downgrades[0] must be a mapping"),
            ("result.judgment.residual_risk", "residual_risk", "result.judgment.residual_risk[0] must be a mapping"),
        ]
        for path, field, expected in cases:
            with self.subTest(field=path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = ["not-a-mapping"]
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = ["not-a-mapping"]
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

        for path, field, expected in cases:
            with self.subTest(field=f"{path}-scalar"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = 1
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = 1
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"{path} must be a list", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_null_stable_record_buckets(self) -> None:
        cases = [
            ("result.evidence.command_results", "command_results"),
            ("result.evidence.skipped", "skipped"),
            ("result.judgment.reviews", "reviews"),
            ("result.judgment.waivers", "waivers"),
            ("result.judgment.downgrades", "downgrades"),
            ("result.judgment.residual_risk", "residual_risk"),
        ]
        for path, field in cases:
            with self.subTest(field=path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = None
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = None
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"{path} must be a list", result.stderr)

    def test_check_rejects_container_command_result_value_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"][0]["command"] = [
                "git diff --cached --check"
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command must be a non-empty string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_protected_packet_without_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_review"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must match checker-derived required reviews", result.stderr)

    def test_check_rejects_evaluator_boundary_change_without_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            result_data = packet["AcceptancePacket"]["result"]
            result_data["evidence"]["evaluator_boundary"]["status"] = "changed"
            result_data["inference"]["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must match checker-derived required reviews", result.stderr)
        self.assertIn("evaluator boundary", result.stderr)

    def test_check_rejects_malformed_evaluator_boundary_status_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["evaluator_boundary"]["status"] = ["changed"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.evaluator_boundary.status must be null or a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_changed_paths_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["changed_paths"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.changed_paths must be a list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_container_wrapped_changed_path_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["changed_paths"] = [
                {"path": "scripts/check-governance-acceptance.py"}
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.changed_paths must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_scalar_user_judgment_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment must be a mapping", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_non_string_user_judgment_key_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"] = {
                1: {
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "non-string key regression",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment key must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_resolved_ref_fields_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            resolved_ref = packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"][1]
            resolved_ref["origin"] = ["generated"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.resolved_refs: origin is required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_review_ids_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["review_imports"][0]["review_ids"] = [{}, "x"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_ids must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_meta_enums_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["meta"]["lifecycle"] = ["finalized"]
            packet["AcceptancePacket"]["meta"]["mode"] = ["staged"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("meta.lifecycle is invalid", result.stderr)
        self.assertIn("meta.mode is invalid", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_protected_path_with_falsified_low_risk_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["changed_paths"] = ["scripts/tool.py"]
            inference["change_class"] = "routine"
            inference["impact"] = "low"
            inference["protected_boundary_changed"] = False
            inference["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected_boundary_changed: true", result.stderr)
        self.assertIn("change_class: harness-affecting", result.stderr)
        self.assertIn("impact: high", result.stderr)

    def test_check_rejects_container_skipped_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["skipped"][0]["evidence"] = ["search_set_before"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.skipped: evidence must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_container_user_judgment_skipped_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["skipped_request"] = {
                "evidence": ["git diff --cached --check"],
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "regression for malformed skipped request target",
                "source_ref": "file:tests/test_governance_acceptance_cli.py",
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.skipped_request: evidence must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_root_protected_path_with_falsified_low_risk_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["changed_paths"] = ["README.md"]
            inference["change_class"] = "routine"
            inference["impact"] = "low"
            inference["protected_boundary_changed"] = False
            inference["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected_boundary_changed: true", result.stderr)
        self.assertIn("change_class: harness-affecting", result.stderr)
        self.assertIn("impact: high", result.stderr)

    def test_check_rejects_downgrade_without_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0].pop("kind")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade kind must be evidence or review", result.stderr)

    def test_check_rejects_downgrade_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0].pop("to")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade to is required", result.stderr)

    def test_check_rejects_evidence_downgrade_to_unclosed_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "from": "git diff --cached --check",
                    "to": "not required by maintainer",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for arbitrary downgrade closure",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable evidence downgrade replacement is not closed", result.stderr)

    def test_check_rejects_exception_malformed_sibling_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = [
                {
                    "kind": "evidence",
                    "evidence": "git diff --cached --check",
                    "review": ["not a valid sibling target"],
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for malformed sibling target",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target field review must be a substantive string", result.stderr)

    def test_check_rejects_waiver_with_downgrade_to_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = [
                {
                    "kind": "evidence",
                    "evidence": "git diff --cached --check",
                    "to": "not a valid waiver target",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for forbidden waiver to field",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("waiver cannot include to", result.stderr)

    def test_check_rejects_review_downgrade_to_unclosed_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["review_imports"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "review",
                    "from": "validation layer",
                    "to": "not required by maintainer",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for arbitrary review downgrade closure",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable review downgrade replacement is not closed", result.stderr)

    def test_check_rejects_residual_risk_malformed_sibling_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "review": ["not a valid sibling target"],
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for malformed residual risk sibling",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target field review must be a substantive string", result.stderr)

    def test_check_rejects_residual_risk_with_from_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "from": "not a valid residual-risk target",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for forbidden residual from field",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual risk cannot include from", result.stderr)

    def test_check_rejects_waiver_shaped_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "evidence": "python3 scripts/check-v1-archive-boundary.py --staged",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "waiver-shaped downgrade regression",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade must target from", result.stderr)

    def test_check_rejects_container_exception_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0]["review"] = ["archive boundary"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception must target exactly one required evidence/review item", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0]["kind"] = ["evidence"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception kind must be evidence or review", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_review_waiver_without_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0].pop("kind", None)
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review waiver kind must be review", result.stderr)

    def test_check_does_not_apply_evidence_downgrade_to_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["required_evidence"] = ["shared target"]
            inference["required_review"] = ["shared target"]
            packet["AcceptancePacket"]["input"]["user_judgment"] = {}
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "from": "shared target",
                    "to": "narrow evidence check",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "test kind isolation",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable packet missing required review", result.stderr)

    def test_check_rejects_required_evidence_double_closure(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "verify-release-double-closure.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"].append(
                {
                    "command": "python3 scripts/verify-release.py",
                    "status": "pass",
                    "artifact_ref": f"file:{rel_artifact}",
                }
            )
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "artifact",
                    "ref": f"file:{rel_artifact}",
                    "status": "resolved",
                    "target": rel_artifact,
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-waiver-downgrade-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: python3 scripts/verify-release.py",
                        "status: pass",
                        "summary: double closure regression fixture",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required evidence has multiple closures", result.stderr)

    def test_check_validates_non_pass_command_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"].append(
                {
                    "command": "python3 -c 'raise SystemExit(1)'",
                    "status": "fail",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command evidence lacks artifact_ref", result.stderr)

    def test_check_rejects_duplicate_review_waiver_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            waiver = dict(packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0])
            waiver["reason"] = "duplicate closure regression"
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"].append(waiver)
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required review has multiple closures", result.stderr)

    def test_check_accepts_targeted_skipped_required_evidence_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"] = []
            evidence["skipped"] = [
                {
                    "evidence": "git diff --cached --check",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "targeted skip regression",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_rejects_broad_review_waiver_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0]["review"] = "not required"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception target is not required: not required", result.stderr)

    def test_check_rejects_broad_stable_residual_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "broad residual risk acceptance",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual risk must target exactly one required evidence/review item", result.stderr)

    def test_check_rejects_container_residual_risk_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "actor": ["maintainer"],
                    "role": {"name": "maintainer"},
                    "date": "2026-05-06",
                    "reason": ["container wrapped reason"],
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual_risk[0]: actor is required", result.stderr)
        self.assertIn("residual_risk[0]: role is required", result.stderr)
        self.assertIn("residual_risk[0]: reason is required", result.stderr)

    def test_check_rejects_same_search_set_before_after_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            trace_refs = packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]
            trace_refs["search_set_before"] = "trace:.harness/traces/search-set.md#active"
            trace_refs["search_set_after"] = "trace:.harness/traces/search-set.md#active"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("search_set_before and search_set_after must be distinct", result.stderr)

    def test_check_rejects_unbound_command_artifact_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "mixed-command-record.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Packet Record",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "# Command Record",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_non_command_evidence_heading(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "not-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Not Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_duplicate_command_evidence_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "duplicate-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: git diff --cached --check",
                        "status: fail",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_duplicate_command_evidence_even_with_valid_neighbor(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "duplicate-plus-valid-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            common = [
                "packet_id: pkt-finalized-routine-example",
                f"packet_ref: {rel_packet}",
                f"packet_sha256: {packet_sha}",
                "command: git diff --cached --check",
            ]
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        *common,
                        "status: pass",
                        "",
                        "# Command Evidence",
                        *common,
                        "status: fail",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate fields in matching # Command Evidence section", result.stderr)

    def test_check_rejects_ambiguous_command_evidence_sections(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "ambiguous-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            common = [
                "packet_id: pkt-finalized-routine-example",
                f"packet_ref: {rel_packet}",
                f"packet_sha256: {packet_sha}",
                "command: git diff --cached --check",
            ]
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        *common,
                        "status: fail",
                        "",
                        "# Command Evidence",
                        *common,
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ambiguous # Command Evidence sections", result.stderr)

    def test_check_stops_command_evidence_at_next_heading(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "split-command-evidence.log.yml"
            artifact_path = tmp_path / "split-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "# Observational Evidence",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_case_changed_command_artifact_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "case-changed-command-record.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: Git Diff --Cached --Check",
                        "status: Pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_bare_command_artifact_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            artifact_ref = evidence["command_results"][0]["artifact_ref"].removeprefix("file:")
            evidence["command_results"][0]["artifact_ref"] = artifact_ref
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = artifact_ref
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact_ref must use file: scheme", result.stderr)

    def test_check_rejects_generated_closure_ref_relabelled_as_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["origin"] = "input"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lacks resolved generated artifact relation", result.stderr)

    def test_check_rejects_bare_stable_trace_bucket_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]["evolution"] = [
                ".harness/traces/evolution/001-repository-self-application-root.md"
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trace_refs.evolution entries must use trace: scheme", result.stderr)

    def test_check_rejects_stable_packet_with_subthreshold_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0]["score"] = 8
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("field does not mirror imported review_lineage", result.stderr)

    def test_check_rejects_stable_review_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0].pop("actor")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.judgment.reviews: actor is required", result.stderr)

    def test_start_writes_valid_neutral_packet_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet = root / "packet.yml"

            result = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--staged",
            )
            second = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--staged",
            )
            check = run_cli("check", "--packet", str(packet))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("refusing to overwrite", second.stderr)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_finalize_staged_routine_packet_remains_nonstable_without_durable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet = root / "packet.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--staged",
            )
            (root / "docs" / "note.md").write_text("initial\nupdated\n", encoding="utf-8")
            git(root, "add", "docs/note.md")

            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--staged")
            stable = run_cli("check", "--packet", str(packet), "--require-stable")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertNotEqual(stable.returncode, 0)
        self.assertEqual(packet_data["meta"]["lifecycle"], "finalized")
        self.assertEqual(packet_data["result"]["inference"]["change_class"], "routine")
        self.assertFalse(packet_data["result"]["decision"]["stable_handoff_eligible"])
        self.assertIn("durable artifact refs", packet_data["result"]["decision"]["reason"])

    def test_finalize_base_ref_must_match_start_baseline_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "second")
            packet = root / "packet.yml"

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--base-ref",
                "HEAD~1",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--base-ref", "HEAD")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("finalize base-ref must match start baseline_ref: HEAD~1", finalize.stderr)
        self.assertEqual(packet_data["result"]["evidence"]["baseline_ref"], "HEAD~1")

    def test_finalize_base_ref_preserves_comparison_ref_for_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "second")
            packet = root / "packet.yml"

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--base-ref",
                "HEAD~1",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--base-ref", "HEAD~1")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(packet_data["result"]["evidence"]["baseline_ref"], "HEAD~1")
        self.assertEqual(packet_data["result"]["evidence"]["comparison_ref"], "HEAD~1")

    def test_finalize_protected_packet_remains_nonstable_without_review_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts").mkdir()
            (root / "scripts" / "tool.py").write_text("print('old')\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "add script")
            packet = root / "packet.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update checker script.",
                "--source-ref",
                "scripts/tool.py",
                "--staged",
            )
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")

            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--staged")
            stable = run_cli("check", "--packet", str(packet), "--require-stable")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertNotEqual(stable.returncode, 0)
        self.assertEqual(packet_data["result"]["inference"]["required_review"], ["checker correctness"])
        self.assertFalse(packet_data["result"]["decision"]["stable_handoff_eligible"])
        self.assertIn("Plan 03 cannot accept protected changes yet", packet_data["result"]["decision"]["reason"])


if __name__ == "__main__":
    unittest.main()
