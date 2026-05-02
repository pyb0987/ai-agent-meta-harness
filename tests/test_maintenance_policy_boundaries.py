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


if __name__ == "__main__":
    unittest.main()
