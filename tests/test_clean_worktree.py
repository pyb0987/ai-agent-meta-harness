#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-clean-worktree.py"


def run_checker(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class CleanWorktreeCheckerTests(unittest.TestCase):
    def test_clean_git_worktree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            result = run_checker(repo)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Clean worktree verified.", result.stdout)

    def test_dirty_git_worktree_fails_and_lists_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (repo / "backlog.md").write_text("dirty\n", encoding="utf-8")

            result = run_checker(repo)

        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("DIRTY WORKTREE", result.stdout)
        self.assertIn("backlog.md", result.stdout)

    def test_non_git_directory_fails_as_unverifiable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_checker(Path(tmp))

        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertIn("not a git repository", result.stderr.lower())

    def test_release_check_is_documented_but_not_pre_commit(self) -> None:
        maintenance = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-clean-worktree.py", maintenance)
        self.assertIn("stable handoff", maintenance)
        self.assertIn("not part of pre-commit", maintenance)
        self.assertNotIn("scripts/check-clean-worktree.py", hook)


if __name__ == "__main__":
    unittest.main()
