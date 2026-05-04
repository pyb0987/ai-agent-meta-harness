from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "adapters" / "claude" / "skills" / "multi-review" / "SKILL.md"
MIRROR = ROOT / "skills" / "multi-review" / "SKILL.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class ClaudeMultiReviewSkillTests(unittest.TestCase):
    def test_repository_governance_mode_uses_local_score_threshold(self) -> None:
        text = normalized(CANONICAL)

        for marker in (
            "Repository Governance Mode",
            "When reviewing this repository's maintenance work, harness-affecting changes, "
            "release gates, hook semantics, core methodology boundaries, or durable adapter contracts",
            "any reviewer or Critic score below 9 is a **VETO**",
            "fixed and the affected Critic reruns to at least 9",
            "A score of 9 is acceptable only when the final report records why it was not 10",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_generic_threshold_is_not_repository_governance_threshold(self) -> None:
        text = normalized(CANONICAL)

        self.assertIn("The generic 7/10 threshold below applies only to non-governance qualitative reviews", text)
        self.assertIn("| All Critics >= 7 AND no veto | **PASS**", text.replace("≥", ">="))
        self.assertNotIn("repository governance work with all critics >= 7 passes", text.lower())

    def test_root_mirror_matches_canonical_content(self) -> None:
        canonical = CANONICAL.read_text(encoding="utf-8")
        mirror = MIRROR.read_text(encoding="utf-8")
        mirror_without_header = mirror.replace(
            "<!-- Compatibility mirror of `adapters/claude/skills/multi-review/SKILL.md`. Edit the canonical source, not this file. -->\n\n",
            "",
        )

        self.assertEqual(canonical, mirror_without_header)


if __name__ == "__main__":
    unittest.main()
