from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core" / "methodology.md"
MIRROR = ROOT / "docs" / "methodology.md"


def text(path: Path = CORE) -> str:
    return path.read_text(encoding="utf-8")


class CoreMethodologyBoundaryTests(unittest.TestCase):
    def test_structural_hardening_is_framed_as_repository_practice(self) -> None:
        methodology = text()

        for marker in (
            "### Applied Repository Hardening",
            "paper core is the proposer/evaluator/trace loop",
            "repository's applied engineering discipline",
            "not a separate paper claim",
            "**Repository hardening ladder**",
            "**Repository Single Source + Generated Derivatives pattern**",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, methodology)

    def test_structural_hardening_avoids_overclaiming_impossibility(self) -> None:
        methodology = text()

        self.assertNotIn("### P5: Recurring failures are absorbed by structure, not rules", methodology)
        self.assertNotIn("Structural elimination check** (P5)", methodology)
        self.assertNotIn("P5 ladder level 3", methodology)
        self.assertNotIn("Drift itself is impossible", methodology)
        self.assertIn("Applied hardening check", methodology)
        self.assertIn("Drift is mechanically prevented or detected", methodology)

    def test_compatibility_mirror_has_same_boundary_language(self) -> None:
        canonical = text(CORE)
        mirror = text(MIRROR)

        for marker in (
            "### Applied Repository Hardening",
            "not a separate paper claim",
            "**Repository hardening ladder**",
            "Applied hardening check",
            "Drift is mechanically prevented or detected",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))


if __name__ == "__main__":
    unittest.main()
