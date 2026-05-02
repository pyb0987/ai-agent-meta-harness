#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "adapters" / "claude" / "skills" / "autoresearch" / "SKILL.md"
MIRROR = ROOT / "skills" / "autoresearch" / "SKILL.md"


class ClaudeAutoresearchTraceRootTests(unittest.TestCase):
    def test_setup_mode_selects_active_trace_root_before_trace_writes(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")

        for marker in (
            "#### Step 5.5: Select Active Trace Root",
            "Select the active trace root before writing experiment episodes, failure\n"
            "diagnoses, or escalation records.",
            "Default Claude root: `.claude/traces/`.",
            "reuse `.harness/traces/` as `{trace_root}`",
            "Do not split future experiment or failure history across roots silently.",
            "Treat the selected root as `{trace_root}` for all steps below.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_trace_outputs_use_selected_trace_root(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")

        for marker in (
            "`{trace_root}/experiments/NNN-*.md`",
            "`{trace_root}/failures/` trace",
            "Ensure `{trace_root}/experiments/` exists",
            "Active `{trace_root}` selected by evidence",
            "record in `{trace_root}/failures/`",
            "Episode file: `{trace_root}/experiments/NNN-{name}.md`",
            "Numbering: next sequence number within `{trace_root}/experiments/`",
            "latest episode traces from `{trace_root}/experiments/`",
            "Record in `{trace_root}/failures/NNN-{name}.md`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_hardcoded_trace_writes_are_not_used_after_active_root_selection(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        active_root_section = text.split("#### Step 5.5: Select Active Trace Root", 1)[1]

        forbidden_patterns = (
            r"`\.claude/traces/experiments/",
            r"`\.claude/traces/failures/",
            r"in `\.claude/traces/failures/`",
            r"within `\.claude/traces/experiments/`",
            r"Record in `\.claude/traces/failures/",
        )
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, active_root_section))

    def test_compatibility_mirror_matches_canonical_trace_root_contract(self) -> None:
        canonical = CANONICAL.read_text(encoding="utf-8")
        mirror = MIRROR.read_text(encoding="utf-8")

        self.assertEqual(canonical, mirror)
        self.assertIn("Treat the selected root as `{trace_root}` for all steps below.", mirror)


if __name__ == "__main__":
    unittest.main()
