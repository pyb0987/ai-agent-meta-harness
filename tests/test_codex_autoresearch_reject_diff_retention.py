from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTORESEARCH = ROOT / "adapters" / "codex" / "skills" / "autoresearch" / "SKILL.md"
AUTORESEARCH_PLUGIN = ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "autoresearch" / "SKILL.md"
HARNESS_ENGINEER = ROOT / "adapters" / "codex" / "skills" / "harness-engineer" / "SKILL.md"
HARNESS_ENGINEER_PLUGIN = ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "harness-engineer" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class CodexAutoresearchRejectDiffRetentionTests(unittest.TestCase):
    def test_autoresearch_records_rejected_diff_for_every_non_adopted_attempt(self) -> None:
        canonical = read(AUTORESEARCH)
        plugin = read(AUTORESEARCH_PLUGIN)

        markers = (
            "For every `REJECT_GUARD`, `REJECT_THRESHOLD`, or `ERROR`, capture the rejected genome diff",
            ".harness/traces/experiments/rejected-diffs/NNN-{verdict}-{slug}.patch",
            "preserve the raw JSON stdout outside the rejected candidate commit before any revert or cleanup",
            "revert the genome commit according to the current Codex permission policy only after steps 7-9 have preserved",
            "Append or update the full evaluator result in `experiments.jsonl` for every verdict from the preserved evaluator JSON.",
            '"rejected_diff":null',
            "For non-adopted verdicts, set `rejected_diff` to the compact rejected-diff trail path.",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, canonical)
                self.assertIn(marker, plugin)
                self.assertEqual(canonical.count(marker), plugin.count(marker))

        self.assertNotIn(
            "preserve the genome diff and evaluator JSON when recording triggers apply",
            canonical,
        )
        self.assertNotIn(
            "preserve the genome diff and evaluator JSON in the rejected-diff trail",
            canonical,
        )

    def test_harness_engineer_uses_every_reject_diff_trail_with_triggered_failures(self) -> None:
        canonical = read(HARNESS_ENGINEER)
        plugin = read(HARNESS_ENGINEER_PLUGIN)

        markers = (
            "For every autoresearch REJECT or ERROR, capture the genome diff before reverting",
            "compact rejected-diff trail referenced by `experiments.jsonl`",
            "For a REJECT that meets failure recording triggers, also capture the evaluator JSON in the richer failure diagnosis.",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, canonical)
                self.assertIn(marker, plugin)
                self.assertEqual(canonical.count(marker), plugin.count(marker))


if __name__ == "__main__":
    unittest.main()
