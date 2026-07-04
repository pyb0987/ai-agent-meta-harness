from __future__ import annotations

from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
import io
import importlib.util
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-search-set-evidence.py"

spec = importlib.util.spec_from_file_location("check_search_set_evidence", SCRIPT)
assert spec and spec.loader
check_search_set_evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_search_set_evidence)


def run_main_silently(args: list[str]) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return check_search_set_evidence.main(args)


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def evidence_record(status: str = "진행중") -> str:
    return f"""
### 57. Current item
Status: {status}
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`
  - AFTER: PASS `python3 scripts/run-search-set.py`
- Multi-review required: yes
"""


class SearchSetEvidenceCheckerTests(unittest.TestCase):
    def test_harness_affecting_paths_require_recorded_evidence(self) -> None:
        errors = check_search_set_evidence.validate(["core/methodology.md"])

        self.assertTrue(errors)
        self.assertIn("Harness-affecting changes lack recorded search-set", errors[0])

    def test_before_after_evidence_satisfies_harness_affecting_change(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
### 43. Example
Status: 리뷰대기

Completion Gate:
- Search-set verification:
  - BEFORE: PASS `python3 scripts/check-maintenance-review.py`
  - AFTER: PASS `python3 scripts/check-maintenance-review.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["core/methodology.md", "backlog/core.md"],
            read_text=read_text,
        )

        self.assertEqual(errors, [])

    def test_skipped_reason_satisfies_non_applicable_change(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
### 43. Example
Status: 리뷰대기

Completion Gate:
- Search-set verification:
  - SKIPPED: not harness-affecting cleanup.
- Multi-review required: no
"""

        errors = check_search_set_evidence.validate(
            ["MAINTENANCE.md", "backlog/core.md"],
            read_text=read_text,
        )

        self.assertEqual(errors, [])

    def test_not_skipped_keyword_does_not_satisfy_gate(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification: not skipped, still TODO before and after.
- Multi-review required: yes
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_prose_before_after_without_status_does_not_satisfy_gate(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification: before and after commands will be run during review.
- Multi-review required: yes
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_structured_pass_without_command_does_not_satisfy_gate(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification:
  - BEFORE: PASS reviewed locally
  - AFTER: PASS will rerun later
- Multi-review required: yes
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_legacy_no_colon_shape_does_not_satisfy_gate(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification:
  - BEFORE PASS: `cmd`
  - AFTER PASS: `cmd`
- Multi-review required: yes
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_todo_inside_structured_evidence_does_not_satisfy_gate(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification:
  - BEFORE: PASS `cmd`
  - AFTER: PASS TODO rerun
- Multi-review required: yes
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_evidence_commands_extracts_before_after_backticks(self) -> None:
        text = """
### 43. Example
Status: 진행중

Completion Gate:
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`
  - AFTER: FAIL `python3 scripts/check-maintenance-review.py`
- Multi-review required: yes
"""

        self.assertEqual(
            check_search_set_evidence.evidence_commands(text),
            [
                "python3 scripts/run-search-set.py",
                "python3 scripts/check-maintenance-review.py",
            ],
        )

    def test_active_search_set_commands_extracts_active_verify_lines(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
## Active

### SS-001: Active case
- **verify**: `python3 scripts/check-maintenance-review.py`

## Archived

### SS-000: Old case
- **verify**: `python3 old.py`
"""

        commands = check_search_set_evidence.active_search_set_commands(
            read_text=read_text,
            search_set_path=ROOT / "backlog/repository-search-set.md",
        )

        self.assertEqual(commands, {"python3 scripts/check-maintenance-review.py"})

    def test_require_active_run_accepts_aggregate_runner(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return evidence_record()

        errors = check_search_set_evidence.validate(
            ["core/methodology.md", "backlog/core.md"],
            read_text=read_text,
            require_active_run=True,
        )

        self.assertEqual(errors, [])

    def test_require_active_run_accepts_current_active_verify_command(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            if path.relative_to(ROOT).as_posix() == "backlog/repository-search-set.md":
                return """
## Active

### SS-001: Active case
- **verify**: `python3 scripts/check-maintenance-review.py`

## Archived
"""
            return """
### 57. Current item
Status: 진행중
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/check-maintenance-review.py`
  - AFTER: PASS `python3 scripts/check-maintenance-review.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["core/methodology.md", "backlog/core.md"],
            read_text=read_text,
            require_active_run=True,
        )

        self.assertEqual(errors, [])

    def test_require_active_run_rejects_non_active_command(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
### 57. Current item
Status: 진행중
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/not-active.py`
  - AFTER: PASS `python3 scripts/not-active.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["core/methodology.md", "backlog/core.md"],
            read_text=read_text,
            require_active_run=True,
        )

        self.assertTrue(errors)
        self.assertIn("active search-set run attestation", errors[0])
        self.assertIn("Allowed commands:", errors)

    def test_require_active_run_ignores_unrelated_historical_in_progress_sections(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            if path.relative_to(ROOT).as_posix() == "backlog/repository-search-set.md":
                return """
## Active

### SS-001: Active case
- **verify**: `python3 scripts/run-search-set.py`

## Archived
"""
            return """
### 12. Historical archived item
Status: 진행중
Completion Gate:
- Search-set verification:
  - BEFORE: PASS `python3 scripts/not-active.py`
  - AFTER: PASS `python3 scripts/not-active.py`

### 76. Current completed item
Status: 완료
Completion Gate:
- Changed files: `scripts/check-search-set-evidence.py`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`
  - AFTER: PASS `python3 scripts/run-search-set.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["scripts/check-search-set-evidence.py", "backlog/core.md"],
            read_text=read_text,
            require_active_run=True,
        )

        self.assertEqual(errors, [])

    def test_backlog_only_cleanup_is_not_harness_affecting(self) -> None:
        errors = check_search_set_evidence.validate(["backlog/core.md"])

        self.assertEqual(errors, [])

    def test_checker_itself_is_harness_affecting(self) -> None:
        self.assertTrue(check_search_set_evidence.is_harness_affecting("scripts/check-search-set-evidence.py"))

    def test_stale_completed_record_does_not_satisfy_active_item(self) -> None:
        text = """
### 42. Old item
Status: 완료
Completion Gate:
- Search-set verification:
  - BEFORE PASS: `cmd`
  - AFTER PASS: `cmd`

### 43. Current item
Status: 진행중
Completion Gate:
- Verification results:
  - PASS: `cmd`
"""

        self.assertFalse(check_search_set_evidence.has_current_record_evidence(text))

    def test_completed_current_record_satisfies_completed_handoff(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
### 42. Current completed item
Status: 완료
Completion Gate:
- Changed files: `adapters/codex/README.md`, `backlog/codex-adapter.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py --list`
  - AFTER: PASS `python3 scripts/run-search-set.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["adapters/codex/README.md", "backlog/codex-adapter.md"],
            read_text=read_text,
        )

        self.assertEqual(errors, [])

    def test_unrelated_completed_record_does_not_satisfy_completed_handoff(self) -> None:
        def read_text(path: Path, *, encoding: str) -> str:
            return """
### 41. New completed item
Status: 완료
Completion Gate:
- Changed files: `adapters/codex/README.md`, `backlog/codex-adapter.md`.
- Verification results: PASS `cmd`

### 40. Old completed item
Status: 완료
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py --list`
  - AFTER: PASS `python3 scripts/run-search-set.py`
- Multi-review required: yes
"""

        errors = check_search_set_evidence.validate(
            ["adapters/codex/README.md", "backlog/codex-adapter.md"],
            read_text=read_text,
        )

        self.assertTrue(errors)

    def test_unrelated_review_pending_record_does_not_satisfy_in_progress_item(self) -> None:
        records = {
            "backlog/core.md": """
### 43. Current item
Status: 진행중
Completion Gate:
- Verification results:
  - PASS: `cmd`
""",
            "backlog/codex-adapter.md": """
### 37. Other item
Status: 리뷰대기
Completion Gate:
- Search-set verification:
  - BEFORE PASS: `cmd`
  - AFTER PASS: `cmd`
""",
        }

        def read_text(path: Path, *, encoding: str) -> str:
            return records[path.relative_to(ROOT).as_posix()]

        errors = check_search_set_evidence.validate(
            ["MAINTENANCE.md", "backlog/core.md", "backlog/codex-adapter.md"],
            read_text=read_text,
        )

        self.assertTrue(errors)

    def test_completed_record_does_not_satisfy_review_pending_item(self) -> None:
        records = {
            "backlog/codex-adapter.md": """
### 43. Review-pending item
Status: 리뷰대기
Completion Gate:
- Verification results:
  - PASS: `cmd`

### 42. Completed item
Status: 완료
Completion Gate:
- Changed files: `adapters/codex/README.md`, `backlog/codex-adapter.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py --list`
  - AFTER: PASS `python3 scripts/run-search-set.py`
""",
        }

        def read_text(path: Path, *, encoding: str) -> str:
            return records[path.relative_to(ROOT).as_posix()]

        errors = check_search_set_evidence.validate(
            ["adapters/codex/README.md", "backlog/codex-adapter.md"],
            read_text=read_text,
        )

        self.assertTrue(errors)

    def test_standard_verification_documents_checker(self) -> None:
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
        lower = text.lower()
        normalized = " ".join(text.split())

        self.assertIn("python3 scripts/check-search-set-evidence.py", text)
        self.assertIn("python3 scripts/check-search-set-evidence.py --staged", text)
        self.assertIn("python3 scripts/check-search-set-evidence.py --base-ref origin/main", text)
        self.assertIn("search-set evidence compliance", lower)
        self.assertIn("git index", lower)
        self.assertIn("ref...head", lower)
        self.assertIn("shape-only", lower)
        self.assertIn("parses `backlog/repository-search-set.md`", text)
        self.assertIn("requires recorded BEFORE/AFTER commands to match", normalized)
        self.assertIn("prove that `python3 scripts/run-search-set.py` actually\nran", text)
        self.assertIn("Active-case execution is enforced by the separate verification policy", text)
        self.assertIn("optional strict mode", lower)
        self.assertIn("python3 scripts/check-search-set-evidence.py --staged --require-active-run", text)

    def test_staged_mode_uses_index_paths_and_records(self) -> None:
        original_staged_paths = check_search_set_evidence.git_staged_paths
        original_read_index_text = check_search_set_evidence.read_index_text
        try:
            check_search_set_evidence.git_staged_paths = lambda: [
                "core/methodology.md",
                "backlog/core.md",
            ]

            def read_index_text(path: Path, *, encoding: str) -> str:
                self.assertEqual(path.relative_to(ROOT).as_posix(), "backlog/core.md")
                return """
### 57. Current item
Status: 진행중
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`
  - AFTER: PASS `python3 scripts/run-search-set.py`
- Multi-review required: yes
"""

            check_search_set_evidence.read_index_text = read_index_text

            self.assertEqual(run_main_silently(["--staged"]), 0)
        finally:
            check_search_set_evidence.git_staged_paths = original_staged_paths
            check_search_set_evidence.read_index_text = original_read_index_text

    def test_staged_mode_fails_when_staged_record_lacks_evidence(self) -> None:
        original_staged_paths = check_search_set_evidence.git_staged_paths
        original_read_index_text = check_search_set_evidence.read_index_text
        try:
            check_search_set_evidence.git_staged_paths = lambda: [
                "core/methodology.md",
                "backlog/core.md",
            ]
            check_search_set_evidence.read_index_text = lambda path, *, encoding: """
### 57. Current item
Status: 진행중
Completion Gate:
- Verification results: PASS `cmd`
"""

            self.assertEqual(run_main_silently(["--staged"]), 1)
        finally:
            check_search_set_evidence.git_staged_paths = original_staged_paths
            check_search_set_evidence.read_index_text = original_read_index_text

    def test_base_ref_mode_uses_range_paths(self) -> None:
        original_base_paths = check_search_set_evidence.git_base_paths
        original_validate = check_search_set_evidence.validate
        calls: list[tuple[list[str], object]] = []
        try:
            check_search_set_evidence.git_base_paths = lambda base_ref: [
                f"BASE={base_ref}",
                "scripts/check-search-set-evidence.py",
                "backlog/core.md",
            ]

            def validate(
                changed_paths: list[str],
                *,
                read_text=Path.read_text,
                require_active_run: bool = False,
            ) -> list[str]:
                calls.append((changed_paths, read_text))
                self.assertFalse(require_active_run)
                return []

            check_search_set_evidence.validate = validate

            self.assertEqual(run_main_silently(["--base-ref", "origin/main"]), 0)
            self.assertEqual(
                calls,
                [
                    (
                        [
                            "BASE=origin/main",
                            "scripts/check-search-set-evidence.py",
                            "backlog/core.md",
                        ],
                        check_search_set_evidence.read_head_text,
                    )
                ],
            )
        finally:
            check_search_set_evidence.git_base_paths = original_base_paths
            check_search_set_evidence.validate = original_validate

    def test_explicit_paths_cannot_combine_with_staged_mode(self) -> None:
        with self.assertRaises(SystemExit):
            run_main_silently(["--staged", "core/methodology.md"])

    def test_staged_mode_exercises_real_git_index(self) -> None:
        original_root = check_search_set_evidence.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run_git(repo, "init")
            run_git(repo, "config", "user.email", "test@example.com")
            run_git(repo, "config", "user.name", "Test User")
            write(repo / "core/methodology.md", "baseline\n")
            write(repo / "backlog/core.md", "# Backlog\n")
            run_git(repo, "add", ".")
            run_git(repo, "commit", "-m", "baseline")

            write(repo / "core/methodology.md", "changed\n")
            write(repo / "backlog/core.md", evidence_record())
            run_git(repo, "add", "core/methodology.md", "backlog/core.md")
            write(repo / "backlog/core.md", "# unstaged worktree drift should not satisfy staged mode\n")

            try:
                check_search_set_evidence.ROOT = repo
                self.assertEqual(run_main_silently(["--staged"]), 0)
            finally:
                check_search_set_evidence.ROOT = original_root

    def test_staged_strict_mode_uses_index_search_set_allowlist(self) -> None:
        original_root = check_search_set_evidence.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run_git(repo, "init")
            run_git(repo, "config", "user.email", "test@example.com")
            run_git(repo, "config", "user.name", "Test User")
            write(repo / "core/methodology.md", "baseline\n")
            write(repo / "backlog/repository-search-set.md", """
# Search Set

## Active

### SS-001: Active staged command
- **verify**: `python3 scripts/index-active.py`

## Archived
""")
            write(repo / "backlog/core.md", "# Backlog\n")
            run_git(repo, "add", ".")
            run_git(repo, "commit", "-m", "baseline")

            write(repo / "core/methodology.md", "changed\n")
            write(repo / "backlog/core.md", """
### 57. Current item
Status: 진행중
Completion Gate:
- Changed files: `core/methodology.md`, `backlog/core.md`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/index-active.py`
  - AFTER: PASS `python3 scripts/index-active.py`
- Multi-review required: yes
""")
            write(repo / "backlog/repository-search-set.md", """
# Search Set

## Active

### SS-001: Active staged command
- **verify**: `python3 scripts/index-active.py`

## Archived
""")
            run_git(repo, "add", "core/methodology.md", "backlog/core.md", "backlog/repository-search-set.md")
            write(repo / "backlog/repository-search-set.md", """
# Search Set

## Active

### SS-001: Dirty worktree command
- **verify**: `python3 scripts/worktree-only.py`

## Archived
""")

            try:
                check_search_set_evidence.ROOT = repo
                self.assertEqual(run_main_silently(["--staged", "--require-active-run"]), 0)
            finally:
                check_search_set_evidence.ROOT = original_root

    def test_base_ref_mode_exercises_real_committed_range(self) -> None:
        original_root = check_search_set_evidence.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run_git(repo, "init")
            run_git(repo, "config", "user.email", "test@example.com")
            run_git(repo, "config", "user.name", "Test User")
            write(repo / "core/methodology.md", "baseline\n")
            write(repo / "backlog/core.md", "# Backlog\n")
            run_git(repo, "add", ".")
            run_git(repo, "commit", "-m", "baseline")
            base = run_git(repo, "rev-parse", "HEAD")

            write(repo / "core/methodology.md", "changed\n")
            write(repo / "backlog/core.md", evidence_record(status="완료"))
            run_git(repo, "add", "core/methodology.md", "backlog/core.md")
            run_git(repo, "commit", "-m", "record evidence")
            write(repo / "backlog/core.md", "# dirty worktree drift should not satisfy base-ref mode\n")

            try:
                check_search_set_evidence.ROOT = repo
                self.assertEqual(run_main_silently(["--base-ref", base]), 0)
            finally:
                check_search_set_evidence.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
