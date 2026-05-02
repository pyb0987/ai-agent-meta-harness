from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INIT_CODEX = ROOT / "adapters" / "codex" / "skills" / "init-codex-harness" / "SKILL.md"
PLUGIN_INIT_CODEX = (
    ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "init-codex-harness" / "SKILL.md"
)


def skill_text(path: Path = INIT_CODEX) -> str:
    return path.read_text(encoding="utf-8")


class CodexInitTraceRootSelectionTests(unittest.TestCase):
    def test_init_codex_compares_meaningful_history_before_path_preference(self) -> None:
        text = skill_text()

        for marker in (
            "Prefer `.harness/traces/` for runtime-neutral projects when history evidence is\nabsent or equivalent",
            "Choose by meaningful history before path preference",
            "Inspect both `.harness/traces/` and `.claude/traces/` when either exists",
            "Use `.claude/traces/` temporarily when it has meaningful history and\n   `.harness/traces/` is missing, empty, or template-only",
            "If both roots have meaningful but divergent history, stop and propose a\n   migration/merge plan",
            "If neither root exists, or neither existing root has meaningful history,\n   initialize `.harness/traces/`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_empty_harness_root_does_not_outrank_meaningful_claude_history(self) -> None:
        text = skill_text()

        for marker in (
            "Empty directories, `.keep` files, and\nuntouched `search-set.md` templates are not meaningful history",
            "must not\noutrank real history in the other root",
            "`search-set.md` has Active cases",
            "`failures/` has\ndiagnoses",
            "`evolution/` has prior harness changes",
            "`experiments/` has\nepisodes relevant to current work",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

        self.assertNotIn("1. Existing `.harness/traces/`", text)

    def test_generated_plugin_has_same_trace_root_selection_contract(self) -> None:
        canonical = skill_text(INIT_CODEX)
        plugin = skill_text(PLUGIN_INIT_CODEX)

        for marker in (
            "Choose by meaningful history before path preference",
            "Use `.claude/traces/` temporarily when it has meaningful history",
            "empty, or template-only",
            "Empty directories, `.keep` files",
            "untouched `search-set.md` templates are not meaningful history",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, plugin)
                self.assertEqual(canonical.count(marker), plugin.count(marker))


if __name__ == "__main__":
    unittest.main()
