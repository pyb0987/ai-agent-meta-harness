from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "governance"


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.com")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("hello\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-m", "initial")


def run_governance(*args: str, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GOVERNANCE), "--root", str(root), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class GovernanceWrapperTests(unittest.TestCase):
    def test_wrapper_delegates_base_ref_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "docs" / "note.md").write_text("hello\nworld\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "update docs")

            result = run_governance("start", "--base-ref", base_ref, "--intent", "Update docs.", root=root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wrote start packet: archive/v2/packets/", result.stdout)

    def test_wrapper_delegates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()

            result = run_governance("status", "--base-ref", base_ref, root=root)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("governance status", result.stdout)
        self.assertIn("pointers: 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
