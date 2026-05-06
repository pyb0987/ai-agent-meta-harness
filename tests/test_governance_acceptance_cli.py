from __future__ import annotations

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

    def test_check_rejects_stable_protected_packet_without_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_review"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must infer required review", result.stderr)

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

    def test_check_rejects_stable_packet_with_subthreshold_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0]["score"] = 8
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review score below 9", result.stderr)

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
