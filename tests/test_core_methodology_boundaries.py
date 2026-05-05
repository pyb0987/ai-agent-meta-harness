from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core" / "methodology.md"
MIRROR = ROOT / "docs" / "methodology.md"
REFERENCE = ROOT / "core" / "reference.md"
REFERENCE_MIRROR = ROOT / "docs" / "reference.md"


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

    def test_aphoristic_slogans_are_claim_boundary_framed(self) -> None:
        methodology = text()
        mirror = text(MIRROR)

        for document in (methodology, mirror):
            with self.subTest(document=document[:20]):
                normalized = " ".join(document.split())
                self.assertIn("repository shorthand inspired by paper-backed", normalized)
                self.assertIn("not local benchmark reproduction claims", normalized)
                self.assertIn(
                    "not local benchmark reproduction claims or universal claims about model capability",
                    normalized,
                )
                self.assertIn(
                    "In this repository, improve the environment before blaming model capability",
                    normalized,
                )
                self.assertIn("Prefer richer trace context when changing harnesses", normalized)
                self.assertIn("Repository hardening shorthand", document)
                self.assertIn("repeated trace evidence can be turned into mechanical guardrails", document)
                self.assertNotIn("The bottleneck is environment design, not model intelligence", document)
                self.assertNotIn("Richer diagnostic context produces better harnesses", document)
                self.assertNotIn('> "Don\'t do this" fails. "Can\'t do this" succeeds.', document)

    def test_compatibility_mirror_has_same_boundary_language(self) -> None:
        canonical = text(CORE)
        mirror = text(MIRROR)
        normalized_canonical = " ".join(canonical.split())
        normalized_mirror = " ".join(mirror.split())

        for marker in (
            "### Applied Repository Hardening",
            "not a separate paper claim",
            "not local benchmark reproduction claims",
            "not local benchmark reproduction claims or universal claims about model capability",
            "**Repository hardening ladder**",
            "Repository hardening shorthand",
            "Applied hardening check",
            "Drift is mechanically prevented or detected",
        ):
            with self.subTest(marker=marker):
                if "\n" in marker or len(marker.split()) > 3:
                    self.assertIn(marker, normalized_mirror)
                    self.assertEqual(normalized_canonical.count(marker), normalized_mirror.count(marker))
                else:
                    self.assertIn(marker, mirror)
                    self.assertEqual(canonical.count(marker), mirror.count(marker))

    def test_prompt_as_code_example_uses_runtime_neutral_instruction_file(self) -> None:
        canonical = text(CORE)
        mirror = text(MIRROR)

        for document in (canonical, mirror):
            with self.subTest(document=document[:20]):
                self.assertIn("edit a project instruction file or a prompt paragraph", document)
                self.assertNotIn("`AGENTS.md`", document)
                self.assertNotIn("`CLAUDE.md`", document)

    def test_sub_agent_guidance_is_subordinate_runtime_tactic(self) -> None:
        methodology = text()

        for marker in (
            "paper-core Meta-Harness loop is proposer -> evaluator -> trace reuse",
            "applied runtime tactics",
            "subordinate to the",
            "not an additional paper-core methodology",
            "Only two methodology-level triggers belong in the shared core",
            "**Adapter ownership**",
            "runtime tool policy",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, methodology)

    def test_sub_agent_guidance_leaves_routing_to_adapters(self) -> None:
        methodology = text()

        self.assertNotIn("### Model routing", methodology)
        self.assertNotIn("Trigger threshold", methodology)
        self.assertNotIn("prefer over-invoking", methodology)

    def test_compatibility_mirror_has_same_sub_agent_boundary_language(self) -> None:
        canonical = text(CORE)
        mirror = text(MIRROR)

        for marker in (
            "paper-core Meta-Harness loop is proposer -> evaluator -> trace reuse",
            "applied runtime tactics",
            "Only two methodology-level triggers belong in the shared core",
            "**Adapter ownership**",
            "runtime tool policy",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))

    def test_trace_schema_is_framed_as_repository_convention(self) -> None:
        methodology = text(CORE)
        reference = text(REFERENCE)

        for marker in (
            "The paper-backed requirement is to preserve raw prior-experience signals",
            "this repository's applied convention",
            "exact trace-root surface, YAML frontmatter, and search-set schema",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, methodology)

        for marker in (
            "contracts for projects adopting this harness",
            "paper-mandated",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, reference)

    def test_trace_schema_boundary_language_is_mirrored(self) -> None:
        methodology = text(CORE)
        methodology_mirror = text(MIRROR)
        reference = text(REFERENCE)
        reference_mirror = text(REFERENCE_MIRROR)

        for marker in (
            "The paper-backed requirement is to preserve raw prior-experience signals",
            "this repository's applied convention",
            "exact trace-root surface, YAML frontmatter, and search-set schema",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, methodology_mirror)
                self.assertEqual(methodology.count(marker), methodology_mirror.count(marker))

        for marker in (
            "contracts for projects adopting this harness",
            "paper-mandated",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, reference_mirror)
                self.assertEqual(reference.count(marker), reference_mirror.count(marker))

    def test_raw_trace_ablation_claim_is_scoped_and_mirrored(self) -> None:
        methodology = text(CORE)
        methodology_mirror = text(MIRROR)

        for document in (methodology, methodology_mirror):
            with self.subTest(document=document[:20]):
                self.assertIn("paper's online text-classification ablation motivates", document)
                self.assertIn("do not generalize", document)
                self.assertIn("universal claim about every LLM summary in every task", document)
                self.assertNotIn("proven by ablation: summary < raw trace", document)

        for marker in (
            "paper's online text-classification ablation motivates",
            "universal claim about every LLM summary in every task",
        ):
            with self.subTest(marker=marker):
                self.assertEqual(methodology.count(marker), methodology_mirror.count(marker))

    def test_rejected_candidate_diff_policy_is_explicit_and_mirrored(self) -> None:
        methodology = text(CORE)
        methodology_mirror = text(MIRROR)
        reference = text(REFERENCE)
        reference_mirror = text(REFERENCE_MIRROR)

        methodology_markers = (
            "Simple threshold misses (REJECT_THRESHOLD) don't need `failures/` diagnosis",
            "records, but their candidate diffs still belong in the fixed-evaluator\n  rejected-diff trail below.",
            "capture a compact candidate diff for every non-adopted",
            "Preserve raw evaluator output in `experiments.jsonl`",
            "write a richer `failures/` diagnosis only when the",
        )
        for marker in methodology_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, methodology)
                self.assertIn(marker, methodology_mirror)
                self.assertEqual(methodology.count(marker), methodology_mirror.count(marker))

        reference_markers = (
            "Rejected fixed-evaluator candidates have two recording levels",
            "`{trace_root}/experiments/rejected-diffs/NNN-{verdict}-{name}.patch`",
            "including simple\n  threshold misses that do not justify a full failure diagnosis",
            "append or update the experiment log with the evaluator result and rejected-diff\nreference",
        )
        for marker in reference_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, reference)
                self.assertIn(marker, reference_mirror)
                self.assertEqual(reference.count(marker), reference_mirror.count(marker))


if __name__ == "__main__":
    unittest.main()
