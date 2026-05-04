from __future__ import annotations

from pathlib import Path
import importlib.util
import io
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

    def test_list_mode_prints_commands_without_running(self) -> None:
        output = io.StringIO()

        with mock.patch("sys.stdout", output):
            status = verify_release.main(["--list"])

        self.assertEqual(status, 0)
        text = output.getvalue()
        self.assertIn("python3 scripts/check-compat-mirrors.py", text)
        self.assertIn("python3 scripts/check-clean-worktree.py", text)

    def test_maintenance_documents_verify_release(self) -> None:
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/verify-release.py", text)
        self.assertIn("preferred stable-handoff command", text)


if __name__ == "__main__":
    unittest.main()
