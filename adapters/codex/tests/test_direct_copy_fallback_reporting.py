#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
CANONICAL_SKILL = ROOT / "adapters" / "codex" / "skills" / "autoresearch" / "SKILL.md"
PLUGIN_SKILL = ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "autoresearch" / "SKILL.md"
README = ROOT / "adapters" / "codex" / "README.md"
PLUGIN_README = ROOT / "plugins" / "ai-agent-meta-harness" / "README.md"


REQUIRED_ASSETS = (
    "scripts/check-autoresearch-protected.py",
    "scripts/smoke-autoresearch-hooks.py",
    "templates/autoresearch-protected.txt",
    "templates/hooks/codex-hooks.json.template",
    "templates/hooks/pre-commit-autoresearch-protected.sh",
    "templates/hooks/github-actions-autoresearch-protected.yml",
    "templates/hooks/agents-autoresearch-protection.md",
)


class DirectCopyFallbackReportingTests(unittest.TestCase):
    def assert_skill_contract(self, text: str) -> None:
        for marker in (
            "Direct-copy fallback reporting",
            "DEGRADED_DIRECT_COPY_PROTECTION",
            "Missing assets:",
            "Protection level: incomplete",
            "Do not claim hook, checker, pre-commit, or CI protection",
            "skill-only copy",
            "not a valid protection install path by itself",
        ):
            self.assertIn(marker, text)
        for asset in REQUIRED_ASSETS:
            self.assertIn(asset, text)

    def assert_readme_contract(self, text: str) -> None:
        for marker in (
            "DEGRADED_DIRECT_COPY_PROTECTION",
            "Protection level: incomplete",
            "skill-only direct-copy install",
            "must not claim Codex hooks, checker scripts",
            "generated plugin bundle and smoke-tested",
        ):
            self.assertIn(marker, text)

    def test_autoresearch_skill_defines_direct_copy_degraded_report(self) -> None:
        self.assert_skill_contract(CANONICAL_SKILL.read_text(encoding="utf-8"))

    def test_generated_plugin_skill_matches_direct_copy_degraded_report(self) -> None:
        self.assertEqual(
            CANONICAL_SKILL.read_text(encoding="utf-8"),
            PLUGIN_SKILL.read_text(encoding="utf-8"),
        )
        self.assert_skill_contract(PLUGIN_SKILL.read_text(encoding="utf-8"))

    def test_readme_documents_direct_copy_degraded_report(self) -> None:
        self.assert_readme_contract(README.read_text(encoding="utf-8"))

    def test_generated_plugin_readme_matches_direct_copy_degraded_report(self) -> None:
        self.assertEqual(
            README.read_text(encoding="utf-8"),
            PLUGIN_README.read_text(encoding="utf-8"),
        )
        self.assert_readme_contract(PLUGIN_README.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
