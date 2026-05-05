from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "MAINTENANCE.md"


def maintenance_text() -> str:
    return MAINTENANCE.read_text(encoding="utf-8")


def normalized_text() -> str:
    return " ".join(maintenance_text().split())


class MaintenancePolicyBoundaryTests(unittest.TestCase):
    def test_review_score_thresholds_are_labeled_local_governance(self) -> None:
        text = normalized_text()

        for marker in (
            "local release discipline for review scores",
            "Under the same local governance rule",
            "repository governance and release discipline",
            "stricter than the Meta-Harness paper's methodological claims",
            "this repository chooses numeric review gates",
            "As local release policy, reviewer or critic scores below 9 are VETO",
            "local governance requires recording why",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_paper_claims_are_separated_from_numeric_review_gates(self) -> None:
        text = normalized_text()
        lower = text.lower()

        self.assertIn(
            "the paper motivates evaluator boundaries, trace reuse, and harness design",
            text,
        )
        self.assertIn(
            "Meta-Harness paper for the harness-sensitivity lesson, including the introduction's cited prior evidence that changing only the harness can produce a 6x performance gap on the same benchmark",
            text,
        )
        self.assertNotIn("harness design can dominate model choice", lower)
        self.assertNotIn("paper requires reviewer scores below 9", lower)
        self.assertNotIn("paper requires score 9", lower)

    def test_backlog_policy_multi_review_trigger_matches_durable_contracts(self) -> None:
        text = normalized_text()

        self.assertIn(
            "Use multi-review for adapter behavior, release gates, hook semantics, "
            "core methodology boundaries, or durable contracts named in `Multi-Review Use`",
            text,
        )
        self.assertIn(
            "Routine backlog/status/doc cleanup can use focused checks without mandatory "
            "multi-review when it does not change those contracts",
            text,
        )
        self.assertNotIn(
            "anything that can steer future work in the wrong direction",
            text,
        )

    def test_required_multi_review_is_not_single_reviewer_gate(self) -> None:
        text = normalized_text()

        for marker in (
            "If multi-review is required, run the multi-review skill or an explicitly "
            "documented equivalent with multiple reviewers/critics before acceptance",
            "A single isolated reviewer does not satisfy required multi-review",
            "If multi-review is not required but the item will be committed as a stable "
            "handoff, ask a single isolated reviewer",
            "Required multi-review means multiple distinct reviewers or critics",
            "When a committed stable-handoff item does not require multi-review, the "
            "Reviewed Commit Loop uses a single isolated reviewer as the required "
            "handoff hygiene check",
            "that check must still not be recorded as satisfying required multi-review",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn(
            "ask an isolated reviewer to review the item-specific diff before acceptance "
            "when multi-review is required",
            text,
        )
        self.assertNotIn(
            "when multi-review is required or when the item will be committed as a "
            "stable handoff",
            text,
        )

    def test_raw_evidence_expectations_for_review_records_are_bounded(self) -> None:
        text = normalized_text()

        for marker in (
            "Distilled reviewer findings are acceptable for routine maintenance records",
            "reviewed files, commands, scores, blocking findings, and residual risk",
            "Preserve or link stronger raw evidence when a review is used to support a "
            "core methodology boundary, evaluator-boundary change, runtime delivery proof, "
            "release gate, or public evidence claim",
            "transcript excerpt, command output, screenshot, exported trace, or reviewed "
            "evidence packet",
            "record the skipped reason when the runtime cannot export it",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_accepted_completed_items_are_marked_complete(self) -> None:
        text = normalized_text()

        for marker in (
            "`리뷰대기`: implementation is ready but still waiting for external review, "
            "merge coordination, or maintainer acceptance",
            "`완료`: accepted and completed in the current maintenance flow or merged",
            "Complete the Completion Gate, mark an accepted completed item `완료`",
            "Use `리뷰대기` only when the implementation is ready but still awaiting "
            "external review, merge coordination, or maintainer acceptance",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn(
            "Complete the Completion Gate, mark the item `리뷰대기`",
            text,
        )


if __name__ == "__main__":
    unittest.main()
