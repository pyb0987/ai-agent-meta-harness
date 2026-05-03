#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "adapters" / "claude" / "skills" / "autoresearch" / "SKILL.md"
MIRROR = ROOT / "skills" / "autoresearch" / "SKILL.md"


def read(path: Path = CANONICAL) -> str:
    return path.read_text(encoding="utf-8")


class ClaudeAutoresearchRejectEvidenceTests(unittest.TestCase):
    def test_reject_path_preserves_raw_evidence_before_revert(self) -> None:
        text = read()

        for marker in (
            "On every REJECT, capture the candidate diff and raw evaluator JSON into\n"
            "  temporary evidence outside the rejected commit before any reset/revert.",
            "REJECT → preserve raw evaluator JSON + capture candidate diff (`git diff HEAD~1`)",
            "store that evidence outside the rejected commit before cleanup",
            "reset/revert the rejected genome commit",
            "append full evaluator result and rejection metadata to experiments.jsonl from the preserved evidence",
            "write `{trace_root}` episode/failure evidence from the preserved evidence when recording triggers apply",
            "Never run `git reset --hard HEAD~1` or another revert before preserving the\n"
            "candidate diff and full evaluator JSON for a REJECT.",
            "Do not rely on\npre-revert appends to tracked files such as `experiments.jsonl`",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_reject_protocol_orders_capture_before_revert(self) -> None:
        text = read()
        reject_step = text.split(
            "REJECT → preserve raw evaluator JSON + capture candidate diff (`git diff HEAD~1`)",
            1,
        )[1].split("8. Repeat from 3", 1)[0]

        preserve_index = reject_step.index("store that evidence outside the rejected commit")
        revert_index = reject_step.index("reset/revert the rejected genome commit")
        append_index = reject_step.index("append full evaluator result")
        evidence_index = reject_step.index("write `{trace_root}` episode/failure evidence")

        self.assertLess(preserve_index, revert_index)
        self.assertLess(revert_index, append_index)
        self.assertLess(revert_index, evidence_index)

    def test_reject_path_no_longer_collapses_to_reset_then_log(self) -> None:
        text = read()

        self.assertNotIn("REJECT → git reset --hard HEAD~1 + log", text)

    def test_compatibility_mirror_matches_canonical_reject_evidence_contract(self) -> None:
        canonical = read(CANONICAL)
        mirror = read(MIRROR)

        self.assertEqual(canonical, mirror)
        self.assertIn("Never run `git reset --hard HEAD~1`", mirror)


if __name__ == "__main__":
    unittest.main()
