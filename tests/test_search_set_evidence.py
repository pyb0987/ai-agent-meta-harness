from __future__ import annotations

from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-search-set-evidence.py"

spec = importlib.util.spec_from_file_location("check_search_set_evidence", SCRIPT)
assert spec and spec.loader
check_search_set_evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_search_set_evidence)


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
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
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
- Search-set verification: SKIPPED; not harness-affecting cleanup.
- Multi-review required: no
"""

        errors = check_search_set_evidence.validate(
            ["scripts/check-clean-worktree.py", "backlog/core.md"],
            read_text=read_text,
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

    def test_standard_verification_documents_checker(self) -> None:
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
        lower = text.lower()

        self.assertIn("python3 scripts/check-search-set-evidence.py", text)
        self.assertIn("search-set evidence compliance", lower)


if __name__ == "__main__":
    unittest.main()
