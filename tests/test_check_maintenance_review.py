#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-maintenance-review.py"

spec = importlib.util.spec_from_file_location("check_maintenance_review", SCRIPT)
assert spec and spec.loader
check_maintenance_review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_maintenance_review
spec.loader.exec_module(check_maintenance_review)


def summary(multi_review: str) -> str:
    return f"""# Review

## Follow-Up Iteration: Example

Multi-review:
{multi_review}
"""


class CheckMaintenanceReviewTests(unittest.TestCase):
    def test_accepts_score_9_review_summary(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is intentionally narrow. Follow-up/residual risk: accepted for this test-only review.
- Release-gate critic: score 9, PASS. Blocking findings: none. Why not 10: no release-like diff was present. No backlog item added because this is test fixture scope.
- Score handling: all required critics scored at least 9, so no VETO iteration was needed. Every score 9 records why not 10 and either backlog follow-up or residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_rejects_score_8_pass_without_veto_handling(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, PASS. Blocking findings: none.
- Score handling: all critic scores were treated as accepted.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none recorded.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score below 9" in error for error in errors))

    def test_rejects_pending_review_status(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: pending critic rerun after fixes.
- Follow-up/residual risk: rerun is still pending.
- Final acceptance: accepted after rerun.
"""
            )
        )

        self.assertTrue(any("unresolved review status" in error for error in errors))

    def test_rejects_missing_required_fields(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("follow-up/residual risk" in error for error in errors))
        self.assertTrue(any("rerun status" in error for error in errors))

    def test_rejects_required_words_outside_review_block(self):
        text = """# Review

## Follow-Up Iteration: Example

Change:

- Added prose that says score 9, score 8, VETO, Blocking findings: none,
  Score handling:, Rerun status:, Follow-up/residual risk:, and Final acceptance:.

Multi-review:

- Test scope critic: score 9, PASS.
"""

        errors = check_maintenance_review.validate_text(text)

        self.assertTrue(any("score record lacks blocking findings" in error for error in errors))
        self.assertTrue(any("follow-up/residual risk" in error for error in errors))

    def test_rejects_score_record_without_scope(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("critic scope" in error for error in errors))

    def test_rejects_score_record_without_blocking_findings(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS.
- Release-gate critic: score 9, PASS. Blocking findings: none. Why not 10: fixture scope only. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score record lacks blocking findings" in error for error in errors))

    def test_rejects_score_9_without_why_not_10(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score 9 lacks why-not-10 handling" in error for error in errors))

    def test_rejects_score_9_without_disposition(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is narrow.
- Score handling: all required critics scored at least 9.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score 9 lacks backlog/residual-risk disposition" in error for error in errors))

    def test_accepts_section_level_score_9_handling(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10; the only score 9 produced no backlog item and is accepted as residual risk.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_ignores_inline_review_outcome_text(self):
        text = """# Backlog

## Candidate

Potential improvement:

- Fix existing embedded `Review outcome:` sections when this item is selected.
"""

        self.assertEqual(check_maintenance_review.validate_text(text), [])


if __name__ == "__main__":
    unittest.main()
