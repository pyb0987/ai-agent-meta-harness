from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-v1-archive-boundary.py"

spec = importlib.util.spec_from_file_location("check_v1_archive_boundary", SCRIPT)
assert spec and spec.loader
check_v1_archive_boundary = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_v1_archive_boundary
spec.loader.exec_module(check_v1_archive_boundary)


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


def commit_all(cwd: Path, message: str = "snapshot") -> None:
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", message)


class V1ArchiveBoundaryTests(unittest.TestCase):
    def test_current_repository_reports_boundary(self) -> None:
        messages, errors = check_v1_archive_boundary.validate(ROOT)

        self.assertEqual(errors, [])
        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("legacy v1 compatibility gates do not actively revalidate" in message for message in messages))

    def test_initial_archive_import_is_allowed_before_archive_exists_in_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            backlog.mkdir()
            (backlog / "core.md").write_text("# v1 core\n", encoding="utf-8")
            commit_all(root, "initial")
            archive = root / "archive" / "v1" / "backlog"
            archive.mkdir(parents=True)
            (archive / "core.md").write_text("# v1 core\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(root)

        self.assertEqual(errors, [])
        self.assertTrue(any("initial archive/v1 import detected" in message for message in messages))

    def test_initial_archive_import_rejects_mismatched_source_without_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            backlog.mkdir()
            (backlog / "core.md").write_text("# v1 core\n", encoding="utf-8")
            commit_all(root, "initial")
            archive = root / "archive" / "v1" / "backlog"
            archive.mkdir(parents=True)
            (archive / "core.md").write_text("# changed\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(root)

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("not a faithful or manifested relocation" in error for error in errors))

    def test_initial_archive_import_accepts_manifested_local_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            backlog.mkdir()
            (backlog / "core.md").write_text("# v1 core\n", encoding="utf-8")
            commit_all(root, "initial")
            archive = root / "archive" / "v1" / "backlog"
            archive.mkdir(parents=True)
            snapshot = "# changed\n"
            (archive / "core.md").write_text(snapshot, encoding="utf-8")
            digest = check_v1_archive_boundary.sha256_text(snapshot)
            (root / "archive" / "v1" / "IMPORT.md").write_text(
                f"""# Import

| Archive path | SHA256 | Source note |
|--------------|--------|-------------|
| `archive/v1/backlog/core.md` | `{digest}` | local pre-v2 worktree snapshot |
""",
                encoding="utf-8",
            )

            messages, errors = check_v1_archive_boundary.validate(root)

        self.assertEqual(errors, [])
        self.assertTrue(any("manifest covers local pre-v2 snapshot divergence" in message for message in messages))

    def test_archive_change_fails_after_archive_exists_in_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\nchanged\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(root)

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("changes require --allow-v1-archive-changes" in error for error in errors))

    def test_archive_change_can_be_waived_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason=(
                    "actor=TestMaintainer role=maintainer date=2026-05-06 "
                    "reason=approved-typo-correction source=git:HEAD"
                ),
            )

        self.assertEqual(errors, [])
        self.assertTrue(any("waiver accepted" in message for message in messages))

    def test_archive_change_waiver_requires_judgment_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason="typo",
            )

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("actor=<name>" in error for error in errors))

    def test_archive_change_waiver_rejects_empty_provenance_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason="actor= role= date= reason= source=",
            )

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("actor=<name>" in error for error in errors))

    def test_archive_change_waiver_rejects_invalid_role_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason="actor=Test role=observer date=today reason=typo source=test",
            )

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("actor=<name>" in error for error in errors))

    def test_archive_change_waiver_rejects_impossible_calendar_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason=(
                    "actor=Test role=maintainer date=2026-99-99 "
                    "reason=typo source=file:tests/test_v1_archive_boundary.py"
                ),
            )

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("real calendar date" in error for error in errors))

    def test_archive_change_waiver_rejects_unresolved_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\ncorrect typo\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(
                root,
                allow_v1_archive_changes=True,
                reason=(
                    "actor=Test role=maintainer date=2026-05-06 "
                    "reason=typo source=file:missing.md"
                ),
            )

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("source file does not exist" in error for error in errors))

    def test_staged_mode_ignores_unstaged_archive_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\nunstaged\n", encoding="utf-8")

            messages, errors = check_v1_archive_boundary.validate(root, staged=True)

        self.assertEqual(errors, [])
        self.assertTrue(any("no archive/v1 changes detected" in message for message in messages))

    def test_staged_archive_change_fails_after_archive_exists_in_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (archive / "README.md").write_text("# v1\n\nstaged\n", encoding="utf-8")
            git(root, "add", "archive/v1/README.md")

            messages, errors = check_v1_archive_boundary.validate(root, staged=True)

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("archive/v1 changed paths" in error for error in errors))

    def test_staged_rename_out_of_archive_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            (root / "elsewhere.md").write_text((archive / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
            git(root, "rm", "archive/v1/README.md")
            git(root, "add", "elsewhere.md")

            messages, errors = check_v1_archive_boundary.validate(root, staged=True)

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("archive/v1 changed paths" in error for error in errors))

    def test_staged_initial_import_accepts_rename_detected_archive_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog_archive = root / "backlog" / "archive"
            backlog_archive.mkdir(parents=True)
            (backlog_archive / "core.md").write_text("# archived core\n", encoding="utf-8")
            commit_all(root, "v1 archive")
            target = root / "archive" / "v1" / "backlog" / "archive"
            target.mkdir(parents=True)
            (target / "core.md").write_text((backlog_archive / "core.md").read_text(encoding="utf-8"), encoding="utf-8")
            git(root, "rm", "backlog/archive/core.md")
            git(root, "add", "archive/v1/backlog/archive/core.md")

            messages, errors = check_v1_archive_boundary.validate(root, staged=True)

        self.assertEqual(errors, [])
        self.assertTrue(any("initial archive/v1 import detected" in message for message in messages))

    def test_base_ref_archive_change_fails_for_committed_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "archive" / "v1"
            archive.mkdir(parents=True)
            (archive / "README.md").write_text("# v1\n", encoding="utf-8")
            commit_all(root, "archive import")
            git(root, "branch", "base")
            (archive / "README.md").write_text("# v1\n\nchanged\n", encoding="utf-8")
            commit_all(root, "change archive")

            messages, errors = check_v1_archive_boundary.validate(root, base_ref="base")

        self.assertTrue(any("frozen historical evidence" in message for message in messages))
        self.assertTrue(any("archive/v1 changed paths" in error for error in errors))

    def test_base_ref_initial_import_uses_merge_base_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            backlog.mkdir()
            (backlog / "core.md").write_text("# v1 at fork\n", encoding="utf-8")
            commit_all(root, "fork point")
            git(root, "branch", "feature")
            git(root, "branch", "base")
            (backlog / "core.md").write_text("# v1 after base advanced\n", encoding="utf-8")
            commit_all(root, "advance base")
            git(root, "switch", "feature")
            archive = root / "archive" / "v1" / "backlog"
            archive.mkdir(parents=True)
            (archive / "core.md").write_text("# v1 at fork\n", encoding="utf-8")
            commit_all(root, "import archive")

            messages, errors = check_v1_archive_boundary.validate(root, base_ref="base")

        self.assertEqual(errors, [])
        self.assertTrue(any("initial archive/v1 import detected" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
