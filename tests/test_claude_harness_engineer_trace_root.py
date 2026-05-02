from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS_ENGINEER = ROOT / "adapters" / "claude" / "skills" / "harness-engineer" / "SKILL.md"
MIRROR_HARNESS_ENGINEER = ROOT / "skills" / "harness-engineer" / "SKILL.md"


def skill_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ClaudeHarnessEngineerTraceRootTests(unittest.TestCase):
    def test_harness_engineer_selects_active_trace_root_before_trace_use(self) -> None:
        text = skill_text(HARNESS_ENGINEER)

        for marker in (
            "Select active trace root first",
            "default to `.claude/traces/` for normal",
            "evidence-selected\n  `.harness/traces/` root in migrated projects",
            "Treat the selected root as\n  `{trace_root}`",
            "Active trace root evidence includes",
            "If both `.claude/traces/` and `.harness/traces/` have divergent meaningful\n  history",
            "Do not split future trace history silently",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_procedural_trace_reads_and_writes_use_selected_root(self) -> None:
        text = skill_text(HARNESS_ENGINEER)

        for marker in (
            "`ls {trace_root}/failures/`",
            "`{trace_root}/experiments/` episodes",
            "`{trace_root}/evolution/` records regression",
            "`{trace_root}/search-set.md`",
            "`grep -l 'resolved: false' {trace_root}/failures/`",
            "`{trace_root}/evolution/NNN-{name}.md`",
            "`{trace_root}/failures/NNN-{name}.md`",
            "`{trace_root}/...` reference",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

        for legacy in (
            "`ls .claude/traces/failures/`",
            "`.claude/traces/experiments/` episodes",
            "`.claude/traces/evolution/` records regression",
            "`.claude/traces/search-set.md`",
            "`grep -l 'resolved: false' .claude/traces/failures/`",
            "`.claude/traces/evolution/NNN-{name}.md`",
            "`.claude/traces/failures/NNN-{name}.md`",
        ):
            with self.subTest(legacy=legacy):
                self.assertNotIn(legacy, text)

    def test_compatibility_mirror_has_same_trace_root_contract(self) -> None:
        canonical = skill_text(HARNESS_ENGINEER)
        mirror = skill_text(MIRROR_HARNESS_ENGINEER)

        for marker in (
            "Select active trace root first",
            "Active trace root evidence includes",
            "`ls {trace_root}/failures/`",
            "`{trace_root}/search-set.md`",
            "`{trace_root}/evolution/NNN-{name}.md`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))


if __name__ == "__main__":
    unittest.main()
