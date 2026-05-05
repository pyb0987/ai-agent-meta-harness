from __future__ import annotations

from pathlib import Path
import importlib.util
import io
import subprocess
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-release.py"

spec = importlib.util.spec_from_file_location("verify_release", SCRIPT)
assert spec and spec.loader
verify_release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify_release
spec.loader.exec_module(verify_release)


def subprocess_result(returncode: int) -> subprocess.CompletedProcess[tuple[str, ...]]:
    return subprocess.CompletedProcess(args=("python3",), returncode=returncode)


def maintenance_standard_commands() -> list[str]:
    text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
    marker = "Standard verification:\n\n```bash\n"
    start = text.index(marker) + len(marker)
    end = text.index("\n```", start)
    return [line.strip() for line in text[start:end].splitlines() if line.strip()]


class VerifyReleaseTests(unittest.TestCase):
    def test_release_commands_include_stable_handoff_gates(self) -> None:
        commands = [command.command for command in verify_release.RELEASE_COMMANDS]

        for expected in maintenance_standard_commands():
            with self.subTest(expected=expected):
                self.assertIn(expected, commands)
        for expected in (
            "python3 scripts/run-search-set.py",
            "python3 scripts/check-clean-worktree.py",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, commands)

    def test_release_commands_are_stored_as_argv(self) -> None:
        for command in verify_release.RELEASE_COMMANDS:
            with self.subTest(command=command.name):
                self.assertIsInstance(command.argv, tuple)
                self.assertGreater(len(command.argv), 1)
                self.assertTrue(all(isinstance(part, str) and part for part in command.argv))

    def test_release_command_rejects_shell_c_argv(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not use shell -c"):
            verify_release.ReleaseCommand("unsafe", ("sh", "-c", "python3 scripts/check-compat-mirrors.py"))

    def test_release_commands_do_not_use_plain_root_unittest_discovery(self) -> None:
        commands = [command.command for command in verify_release.RELEASE_COMMANDS]

        self.assertNotIn("python3 -m unittest discover", commands)

    def test_release_script_is_executable(self) -> None:
        self.assertTrue(SCRIPT.stat().st_mode & 0o111)

    def test_skip_clean_worktree_only_removes_clean_gate(self) -> None:
        all_commands = verify_release.RELEASE_COMMANDS
        selected = verify_release.selected_commands(skip_clean_worktree=True)

        self.assertEqual(len(all_commands) - len(selected), 1)
        self.assertFalse(any(command.clean_worktree for command in selected))

    def test_ci_mode_omits_clean_gate_and_local_codex_activation_smoke(self) -> None:
        selected = verify_release.selected_commands(skip_clean_worktree=True, ci=True)
        commands = {command.name: command.command for command in selected}

        self.assertNotIn("clean worktree", commands)
        self.assertNotIn("codex local plugin activation smoke", commands)
        self.assertIn("codex local plugin smoke", commands)

    def test_base_ref_rewrites_only_search_set_evidence_command(self) -> None:
        selected = verify_release.selected_commands(skip_clean_worktree=True, base_ref="origin/main")
        commands = {command.name: command.command for command in selected}

        self.assertEqual(
            commands["search-set evidence records (base-ref: origin/main)"],
            "python3 scripts/check-search-set-evidence.py --base-ref origin/main",
        )
        self.assertIn("python3 scripts/run-search-set.py", commands.values())
        self.assertNotIn("python3 scripts/check-clean-worktree.py", commands.values())

    def test_base_ref_wrapper_preserves_command_flags(self) -> None:
        command = verify_release.ReleaseCommand(
            "local evidence",
            ("python3", "scripts/check-search-set-evidence.py"),
            search_set_evidence=True,
            ci_local_only=True,
        )

        rewritten = verify_release.with_search_set_evidence_mode(command, base_ref="origin/main")

        self.assertTrue(rewritten.search_set_evidence)
        self.assertTrue(rewritten.ci_local_only)
        self.assertEqual(rewritten.argv, (*command.argv, "--base-ref", "origin/main"))


    def test_base_ref_is_shell_quoted_in_search_set_evidence_command(self) -> None:
        selected = verify_release.selected_commands(skip_clean_worktree=True, base_ref="feature/ref with space")
        commands = {command.name: command.command for command in selected}
        argv = {command.name: command.argv for command in selected}

        self.assertEqual(
            commands["search-set evidence records (base-ref: feature/ref with space)"],
            "python3 scripts/check-search-set-evidence.py --base-ref 'feature/ref with space'",
        )
        self.assertEqual(
            argv["search-set evidence records (base-ref: feature/ref with space)"],
            ("python3", "scripts/check-search-set-evidence.py", "--base-ref", "feature/ref with space"),
        )

    def test_run_command_executes_argv_without_shell(self) -> None:
        command = verify_release.ReleaseCommand("example", ("python3", "-c", "print('ok')"))
        completed = subprocess_result(returncode=0)

        with mock.patch.object(verify_release.subprocess, "run", return_value=completed) as run:
            status = verify_release.run_command(command, timeout=5)

        self.assertEqual(status, 0)
        run.assert_called_once_with(
            command.argv,
            cwd=verify_release.ROOT,
            text=True,
            timeout=5,
            check=False,
        )

    def test_list_mode_prints_commands_without_running(self) -> None:
        output = io.StringIO()

        with mock.patch("sys.stdout", output):
            status = verify_release.main(["--list"])

        self.assertEqual(status, 0)
        text = output.getvalue()
        self.assertIn("python3 scripts/check-compat-mirrors.py", text)
        self.assertIn("python3 scripts/check-clean-worktree.py", text)
        self.assertIn("search-set evidence mode: worktree status", text)

    def test_list_mode_prints_base_ref_search_set_evidence_command(self) -> None:
        output = io.StringIO()

        with mock.patch("sys.stdout", output):
            status = verify_release.main(["--list", "--ci", "--skip-clean-worktree", "--base-ref", "origin/main"])

        self.assertEqual(status, 0)
        text = output.getvalue()
        self.assertIn("release-gate mode: ci deterministic subset", text)
        self.assertIn("search-set evidence mode: base-ref diff (origin/main)", text)
        self.assertIn("python3 scripts/check-search-set-evidence.py --base-ref origin/main", text)
        self.assertNotIn("smoke-local-plugin-activation.py", text)

    def test_maintenance_documents_verify_release(self) -> None:
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/verify-release.py", text)
        self.assertIn("python3 scripts/verify-release.py --base-ref origin/main", text)
        self.assertIn("preferred stable-handoff command", text)


if __name__ == "__main__":
    unittest.main()
