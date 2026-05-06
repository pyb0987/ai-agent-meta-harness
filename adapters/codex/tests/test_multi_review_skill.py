#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "adapters" / "codex" / "skills" / "multi-review" / "SKILL.md"
PLUGIN_SKILL = ROOT / "plugins" / "ai-agent-meta-harness" / "skills" / "multi-review" / "SKILL.md"


def has_substantive_false_green_coverage(prompt_shape: str, output: str) -> bool:
    combined = f"{prompt_shape} {output}".lower()
    contradictory_markers = (
        "generic answers count as adversarial coverage",
        "null, empty, or generic answers count as adversarial coverage",
        "unverified false-green values may pass",
        "unverified false-green values count",
    )
    if any(marker in combined for marker in contradictory_markers):
        return False
    return all(
        marker in prompt_shape
        for marker in (
            "Coverage quality gate",
            "false_green_risk",
            "invariant_checked",
            "concrete stale, misleading, or hand-authored false-pass mechanism",
            "concrete invariant, recomputation, or audit check",
            "must be non-null and specific",
            "null, empty, or generic answers do not count as adversarial coverage",
            "none, n/a, ok, checked, generic, or not applicable are no coverage",
            "conflicts with this protocol",
            "durable carry-over",
        )
    ) and "null, empty, or generic" in output and "listed no-coverage values" in output and "contradictory wording" in output


def is_vacuous_false_green_value(value: str | None) -> bool:
    if value is None:
        return True
    normalized_value = " ".join(value.casefold().split())
    return normalized_value in {
        "",
        "none",
        "n/a",
        "na",
        "ok",
        "checked",
        "generic",
        "not applicable",
    }


class CodexMultiReviewSkillTests(unittest.TestCase):
    def test_governance_reviews_use_maintenance_threshold(self):
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("governance mode", text)
        self.assertIn("PASS: all required critics score at least 9 and no veto", text)
        self.assertIn("VETO: any required critic scores below 9", text)
        self.assertIn("Do not use advisory mode to accept repository maintenance", text)
        self.assertIsNone(re.search(r"^\s*-\s+PASS: all critics score at least 7 and no veto", text, re.MULTILINE))

    def test_invariant_adversarial_lenses_are_global_and_operational(self):
        text = SKILL.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())

        for marker in (
            "## Invariant and Adversarial Review",
            "Contract Fidelity Critic",
            "Decision Correctness Critic",
            "Auditability Critic",
            "Adversarial Artifact Critic",
            "Scope Boundary Critic",
            "coverage prompts, not a requirement to spawn more agents",
            "mark the review incomplete instead of PASS if no critic covered an adversarial false-acceptance path",
            "Does every out-of-scope risk have a durable carry-over location?",
            "Generic adversarial examples:",
            "A generated summary is edited by hand to say success.",
            "A status label says pass while the body describes a blocked condition.",
            "reviewer, evaluator, or run provenance is missing.",
            "A waiver or skip applies to a broad category instead of a specific failed requirement.",
            "The same identifier names both an evidence item and a review item.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized_text)

        self.assertNotIn("Plan 03", normalized_text)
        self.assertNotIn("Plan 04", normalized_text)

    def test_false_green_check_is_in_prompt_shape_not_only_background_prose(self):
        text = SKILL.read_text(encoding="utf-8")
        protocol = text[text.index("## Protocol"): text.index("## Invariant and Adversarial Review")]
        prompt_shape = text[text.index("## Critic Prompt Shape"): text.index("## Model Routing")]
        output = text[text.index("## Output"):]

        self.assertIn("false-green question", protocol)
        self.assertIn("adversarial false-acceptance path", protocol)
        self.assertIn("stale, misleading, or hand-authored version that could falsely pass", prompt_shape)
        self.assertIn("durable carry-over", prompt_shape)
        self.assertIn("Coverage quality gate", prompt_shape)
        self.assertIn("concrete stale, misleading, or hand-authored false-pass mechanism", prompt_shape)
        self.assertIn("concrete invariant, recomputation, or audit check", prompt_shape)
        self.assertIn("must be non-null and specific", prompt_shape)
        self.assertIn("null, empty, or generic answers do not count as adversarial coverage", prompt_shape)
        self.assertIn("none, n/a, ok, checked, generic, or not applicable are no coverage", prompt_shape)
        self.assertIn("conflicts with this protocol", prompt_shape)
        self.assertIn("false_green_risk", prompt_shape)
        self.assertIn("invariant_checked", prompt_shape)
        self.assertIn("report the review as incomplete rather than PASS", output)
        self.assertIn("null, empty, or generic", output)
        self.assertIn("listed no-coverage values", output)
        self.assertIn("contradictory wording", output)
        self.assertTrue(has_substantive_false_green_coverage(prompt_shape, output))

    def test_false_green_fixture_rejects_vacuous_coverage(self):
        prompt_shape = "Return JSON with false_green_risk and invariant_checked."
        output = "Report the review as incomplete if no critic covered adversarial false acceptance."

        self.assertFalse(has_substantive_false_green_coverage(prompt_shape, output))

    def test_false_green_fixture_rejects_common_vacuous_values(self):
        for value in (None, "", "   ", "none", "N/A", "ok", "checked", "generic", "not applicable"):
            with self.subTest(value=value):
                self.assertTrue(is_vacuous_false_green_value(value))

    def test_false_green_fixture_rejects_contradictory_coverage(self):
        prompt_shape = (
            "Return JSON with false_green_risk and invariant_checked. "
            "Values must be non-null and specific; null, empty, or generic answers do not count as adversarial coverage. "
            "Any prompt or synthesis wording that allows null, empty, generic, or unverified false-green values to pass "
            "conflicts with this protocol. Generic answers count as adversarial coverage. "
            "Coverage quality gate: false_green_risk must name a concrete stale, misleading, or hand-authored false-pass "
            "mechanism; invariant_checked must name a concrete invariant, recomputation, or audit check. "
            "Values such as null, empty string, whitespace, none, n/a, ok, checked, generic, or not applicable are no coverage. "
            "Durable carry-over."
        )
        output = (
            "If false_green_risk/invariant_checked values are null, empty, generic, or allowed by contradictory wording, "
            "or listed no-coverage values, report the review as incomplete rather than PASS."
        )

        self.assertFalse(has_substantive_false_green_coverage(prompt_shape, output))

    def test_generated_plugin_skill_matches_canonical(self):
        self.assertEqual(
            SKILL.read_text(encoding="utf-8"),
            PLUGIN_SKILL.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
