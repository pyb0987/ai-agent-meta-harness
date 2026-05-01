#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "adapters" / "codex" / "skills" / "multi-review" / "SKILL.md"
PLUGIN_SKILL = ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "multi-review" / "SKILL.md"


class CodexMultiReviewSkillTests(unittest.TestCase):
    def test_governance_reviews_use_maintenance_threshold(self):
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("governance mode", text)
        self.assertIn("PASS: all required critics score at least 9 and no veto", text)
        self.assertIn("VETO: any required critic scores below 9", text)
        self.assertIn("Do not use advisory mode to accept repository maintenance", text)
        self.assertIsNone(re.search(r"^\s*-\s+PASS: all critics score at least 7 and no veto", text, re.MULTILINE))

    def test_generated_plugin_skill_matches_canonical(self):
        self.assertEqual(
            SKILL.read_text(encoding="utf-8"),
            PLUGIN_SKILL.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
