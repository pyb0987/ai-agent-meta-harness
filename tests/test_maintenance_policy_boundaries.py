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
            "As local release policy, reviewer scores below 9 are VETO",
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


if __name__ == "__main__":
    unittest.main()
