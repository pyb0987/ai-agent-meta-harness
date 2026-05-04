from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-backlog-archive-lifecycle.py"

spec = importlib.util.spec_from_file_location("check_backlog_archive_lifecycle", SCRIPT)
assert spec and spec.loader
check_backlog_archive_lifecycle = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_backlog_archive_lifecycle
spec.loader.exec_module(check_backlog_archive_lifecycle)


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


class BacklogArchiveLifecycleTests(unittest.TestCase):
    def test_current_backlogs_follow_archive_lifecycle(self) -> None:
        self.assertEqual(check_backlog_archive_lifecycle.validate_root(ROOT), [])

    def test_completed_active_record_with_completion_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료

Completion Gate:

- Accepted: yes
""",
                encoding="utf-8",
            )
            (archive / "core.md").write_text("# Core Backlog Archive\n", encoding="utf-8")

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertTrue(any("still contains Completion Gate" in error for error in errors))
        self.assertTrue(any("lacks Archived pointer" in error for error in errors))

    def test_archived_pointer_must_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료
Archived: `backlog/archive/core.md#1-example`
""",
                encoding="utf-8",
            )
            (archive / "core.md").write_text(
                """# Core Backlog Archive

### 2. Other

Status: 완료
""",
                encoding="utf-8",
            )

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertTrue(any("Archived pointer target not found" in error for error in errors))

    def test_archived_completed_target_must_keep_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료
Archived: `backlog/archive/core.md#1-example`
""",
                encoding="utf-8",
            )
            (archive / "core.md").write_text(
                """# Core Backlog Archive

### 1. Example

Status: 완료
""",
                encoding="utf-8",
            )

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertTrue(any("lacks Completion Gate or review evidence" in error for error in errors))

    def test_legacy_archive_exception_counts_as_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료
Archived: `backlog/archive/core.md#1-example`
""",
                encoding="utf-8",
            )
            (archive / "core.md").write_text(
                """# Core Backlog Archive

### 1. Example

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration.
""",
                encoding="utf-8",
            )

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertEqual(errors, [])

    def test_archived_target_must_be_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료
Archived: `backlog/archive/core.md#1-example`
""",
                encoding="utf-8",
            )
            (archive / "core.md").write_text(
                """# Core Backlog Archive

### 1. Example

Completion Gate:

- Accepted: yes
""",
                encoding="utf-8",
            )

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertTrue(any("lacks completed status" in error for error in errors))

    def test_current_archived_pointers_resolve_after_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copytree(ROOT / "backlog", root / "backlog")

            errors = check_backlog_archive_lifecycle.validate_root(root)

        self.assertEqual(errors, [])

    def test_staged_reader_ignores_unstaged_invalid_backlog_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료
Archived: `backlog/archive/core.md#1-example`
""",
                encoding="utf-8",
            )
            for name in ("claude-adapter.md", "codex-adapter.md"):
                (backlog / name).write_text(f"# {name}\n", encoding="utf-8")
            (archive / "core.md").write_text(
                """# Core Backlog Archive

### 1. Example

Status: 완료

Completion Gate:

- Accepted: yes
""",
                encoding="utf-8",
            )
            for name in ("claude-adapter.md", "codex-adapter.md"):
                (archive / name).write_text(f"# {name} Archive\n", encoding="utf-8")
            git(root, "add", "backlog")
            (backlog / "core.md").write_text(
                """# Core Backlog

### 1. Example

Status: 완료

Completion Gate:

- Accepted: yes
""",
                encoding="utf-8",
            )

            errors = check_backlog_archive_lifecycle.validate_root(
                root,
                read_text=lambda path, encoding="utf-8": check_backlog_archive_lifecycle.read_index_text(
                    path,
                    encoding=encoding,
                    root=root,
                ),
            )

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
