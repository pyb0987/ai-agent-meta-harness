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


def git_stdout(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, encoding="utf-8").strip()


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    (root / "docs").mkdir()
    (root / "docs" / "old.md").write_text("stable docs\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "check-governance-acceptance.py").write_text("print('old')\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-m", "initial")


def add_skip_for_command(packet: dict, command: str) -> None:
    evidence = packet["AcceptancePacket"]["result"]["evidence"]
    evidence["command_results"] = []
    evidence["skipped"] = [
        {
            "evidence": command,
            "actor": "maintainer",
            "role": "maintainer",
            "date": "2026-05-06",
            "reason": "targeted skip for focused stable false-green test",
            "source_ref": "file:docs/old.md",
        }
    ]
    evidence["resolved_refs"].append(
        {
            "origin": "generated",
            "relation": "waiver-provenance",
            "ref": "file:docs/old.md",
            "status": "resolved",
            "target": "docs/old.md",
        }
    )


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

    def test_staged_stable_changed_paths_must_match_current_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts" / "check-governance-acceptance.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/check-governance-acceptance.py")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["packet_id"] = "pkt-staged-stale"
            acceptance_packet["input"]["source_refs"] = ["docs/old.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            evidence = result["evidence"]
            evidence["source_refs"] = ["docs/old.md"]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/old.md",
                    "status": "resolved",
                    "target": "docs/old.md",
                }
            )
            packet_path = root / "packets" / "stale.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("staged stable packet changed_paths must match current staged diff", result.stderr)

    def test_external_staged_stable_packet_is_preflight_only(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as packet_tmp:
            root = Path(repo_tmp)
            init_repo(root)
            (root / "scripts" / "check-governance-acceptance.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/check-governance-acceptance.py")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["input"]["source_refs"] = ["docs/old.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            evidence = result["evidence"]
            evidence["source_refs"] = ["docs/old.md"]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/old.md",
                    "status": "resolved",
                    "target": "docs/old.md",
                }
            )
            packet_path = Path(packet_tmp) / "external-staged.yml"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active stable handoff requires base-ref mode", result.stderr)

    def test_tmp_prefixed_repo_packet_is_active_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts" / "check-governance-acceptance.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/check-governance-acceptance.py")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["input"]["source_refs"] = ["docs/old.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            evidence = result["evidence"]
            evidence["source_refs"] = ["docs/old.md"]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/old.md",
                    "status": "resolved",
                    "target": "docs/old.md",
                }
            )
            packet_path = root / "tmp-prod" / "packet.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active stable handoff requires base-ref mode", result.stderr)

    def test_fixture_materialization_marker_does_not_disable_active_handoff_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts" / "check-governance-acceptance.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/check-governance-acceptance.py")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["input"]["source_refs"] = ["docs/old.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            evidence = result["evidence"]
            evidence["source_refs"] = ["docs/old.md"]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/old.md",
                    "status": "resolved",
                    "target": "docs/old.md",
                }
            )
            packet_path = root / "backlog" / "fixtures" / "acceptance-packets" / "tmp-prod" / "packet.yml"
            packet_path.parent.mkdir(parents=True)
            (packet_path.parent / ".fixture-materialization").write_text(
                "acceptance-packet-fixture-materialization/v1\n",
                encoding="utf-8",
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active stable handoff requires base-ref mode", result.stderr)

    def test_base_ref_stable_changed_paths_must_match_git_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts" / "check-governance-acceptance.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/check-governance-acceptance.py")
            git(root, "commit", "-m", "change script")

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            acceptance_packet["input"]["source_refs"] = ["docs/old.md"]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = ["git diff --check HEAD~1...HEAD"]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = ["git diff --check HEAD~1...HEAD"]
            evidence["command_results"][0]["command"] = "git diff --check HEAD~1...HEAD"
            evidence["source_refs"] = ["docs/old.md"]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/old.md",
                    "status": "resolved",
                    "target": "docs/old.md",
                }
            )
            packet_path = root / "packets" / "stale-base-ref.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("base-ref stable packet changed_paths must match git diff boundary", result.stderr)

    def test_base_ref_stable_changed_paths_require_head_pinned_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "old.md").write_text("stable docs\nfirst accepted bytes\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "first docs change")
            old_head = git_stdout(root, "rev-parse", "HEAD")
            (root / "docs" / "old.md").write_text("stable docs\nsecond accepted bytes\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "second docs change")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{old_head}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{old_head}:docs/old.md",
                }
            )
            add_skip_for_command(packet, command)
            packet_path = root / "packets" / "content-drift.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active base-ref stable packet changed_paths require HEAD-pinned git source refs", result.stderr)

    def test_base_ref_stable_deleted_paths_accept_comparison_pinned_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "provenance.md").write_text("targeted evidence skip rationale\n", encoding="utf-8")
            git(root, "add", "docs/provenance.md")
            git(root, "commit", "-m", "add provenance note")
            base = git_stdout(root, "rev-parse", "HEAD")
            (root / "docs" / "old.md").unlink()
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "delete old docs")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{base}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["command_results"] = []
            evidence["skipped"] = [
                {
                    "evidence": command,
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "deletion-only handoff uses comparison-side source bytes.",
                    "source_ref": "file:docs/provenance.md",
                }
            ]
            evidence["resolved_refs"] = [
                record
                for record in evidence["resolved_refs"]
                if record.get("relation") not in {"source", "artifact", "waiver-provenance"}
            ]
            evidence["resolved_refs"].extend(
                [
                    {
                        "origin": "input",
                        "relation": "source",
                        "ref": source_ref,
                        "status": "resolved",
                        "target": f"{base}:docs/old.md",
                    },
                    {
                        "origin": "generated",
                        "relation": "waiver-provenance",
                        "ref": "file:docs/provenance.md",
                        "status": "resolved",
                        "target": "docs/provenance.md",
                    },
                ]
            )
            packet_path = root / "packets" / "deleted-docs.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_base_ref_stable_baseline_must_match_comparison_even_when_evidence_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "old.md").write_text("stable docs\nchanged\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "docs change")
            head = git_stdout(root, "rev-parse", "HEAD")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{head}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{head}:docs/old.md",
                }
            )
            add_skip_for_command(packet, command)
            packet_path = root / "packets" / "baseline-drift.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active base-ref stable packet baseline_ref must match comparison_ref", result.stderr)

    def test_base_ref_proof_like_detection_reads_head_not_dirty_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "old.md").write_text("This verified claim is in HEAD.\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "add proof-like docs")
            head = git_stdout(root, "rev-parse", "HEAD")
            (root / "docs" / "old.md").write_text("This local edit removes the trigger.\n", encoding="utf-8")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{head}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{head}:docs/old.md",
                }
            )
            add_skip_for_command(packet, command)
            packet_path = root / "packets" / "proof-like.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable packet has proof-like changed docs without claim evidence", result.stderr)

    def test_base_ref_scope_review_detection_reads_head_not_dirty_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "old.md").write_text("This deferred scope note is in HEAD.\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "add scope boundary docs")
            head = git_stdout(root, "rev-parse", "HEAD")
            (root / "docs" / "old.md").write_text("This local edit removes the trigger.\n", encoding="utf-8")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{head}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            result["inference"]["required_review"] = []
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("relation") != "source"
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{head}:docs/old.md",
                }
            )
            add_skip_for_command(packet, command)
            packet_path = root / "packets" / "scope-boundary.yml"
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable packet required_review must match checker-derived required reviews", result.stderr)

    def test_skip_provenance_cannot_self_attest_acceptance_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "old.md").write_text("stable docs\nchanged\n", encoding="utf-8")
            git(root, "add", "docs/old.md")
            git(root, "commit", "-m", "docs change")
            head = git_stdout(root, "rev-parse", "HEAD")
            command = "git diff --check HEAD~1...HEAD"

            packet = load_fixture("finalized-routine.yml")
            acceptance_packet = packet["AcceptancePacket"]
            acceptance_packet["meta"]["mode"] = "base-ref"
            source_ref = f"git:{head}:docs/old.md"
            acceptance_packet["input"]["source_refs"] = [source_ref]
            result = acceptance_packet["result"]
            result["inference"]["changed_paths"] = ["docs/old.md"]
            result["inference"]["required_evidence"] = [command]
            evidence = result["evidence"]
            evidence["baseline_ref"] = "HEAD~1"
            evidence["comparison_ref"] = "HEAD~1"
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = [source_ref]
            evidence["resolved_refs"] = [
                record
                for record in evidence["resolved_refs"]
                if record.get("relation") not in {"source", "waiver-provenance"}
            ]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{head}:docs/old.md",
                }
            )
            add_skip_for_command(packet, command)
            packet_path = root / "packets" / "selfskip.yml"
            packet["AcceptancePacket"]["result"]["evidence"]["skipped"][0]["source_ref"] = "file:packets/selfskip.yml"
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"] = [
                record
                for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]
                if record.get("relation") != "waiver-provenance"
            ]
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:packets/selfskip.yml",
                    "status": "resolved",
                    "target": "packets/selfskip.yml",
                }
            )
            packet_path.parent.mkdir()
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("waiver-provenance source_ref cannot be an acceptance packet", result.stderr)

    def test_command_base_ref_parses_equals_form(self) -> None:
        checker = load_checker()

        self.assertEqual(
            checker.command_base_ref("python3 scripts/check-v1-archive-boundary.py --base-ref=origin/main"),
            "origin/main",
        )

    def test_yaml_timestamp_is_not_date_only(self) -> None:
        packet = load_fixture("finalized-routine.yml")
        packet["AcceptancePacket"]["meta"]["created_at"] = "2026-05-08 10:30:00"

        self.assert_rejected(packet, "meta.created_at must be an ISO date")

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
