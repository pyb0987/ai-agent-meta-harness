from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "adapters" / "claude" / "skills" / "multi-review" / "SKILL.md"
MIRROR = ROOT / "skills" / "multi-review" / "SKILL.md"


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def section_between(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def has_substantive_false_green_coverage(prompt_shape: str, convergence: str) -> bool:
    prompt = " ".join(prompt_shape.split())
    combined = f"{prompt} {' '.join(convergence.split())}".lower()
    contradictory_markers = (
        "generic answers count as adversarial coverage",
        "null, empty, or generic answers count as adversarial coverage",
        "unverified false-green values may pass",
        "unverified false-green values count",
    )
    if any(marker in combined for marker in contradictory_markers):
        return False
    return all(
        marker in prompt
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
    ) and "Treat null, empty, or generic" in convergence and "listed no-coverage values" in convergence and "contradictory wording" in convergence


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

class ClaudeMultiReviewSkillTests(unittest.TestCase):
    def test_repository_governance_mode_uses_local_score_threshold(self) -> None:
        text = normalized(CANONICAL)

        for marker in (
            "Repository Governance Mode",
            "project-local governance mode",
            "When reviewing this repository's maintenance work, harness-affecting changes, "
            "release gates, hook semantics, core methodology boundaries, or durable adapter contracts",
            "provides `scripts/check-multi-review-result.py`",
            "any reviewer or Critic score below 9 is a **VETO**",
            "fixed and the affected Critic reruns to at least 9",
            "A score of 9 is acceptable only when the final report records why it was not 10",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_global_skill_does_not_require_project_local_validator(self) -> None:
        text = normalized(CANONICAL)

        for marker in (
            "This skill is globally usable for advisory multi-review",
            "Do not require a cwd-relative validator just because the skill is installed globally",
            "Project-local governance mode is active only when the current repository declares meta-harness governance",
            "has the repository-local validator at `scripts/check-multi-review-result.py`",
            "If the repository declares meta-harness governance but the validator is missing, report governance setup incomplete",
            "do not convert unrelated advisory reviews in other projects into VETO",
            "In projects without a local governance declaration and local validator, run advisory or non-governance multi-review",
            "A missing validator means incomplete governance setup, not a global skill failure",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_generic_threshold_is_not_repository_governance_threshold(self) -> None:
        text = normalized(CANONICAL)

        self.assertIn("The generic 7/10 threshold below applies only to non-governance qualitative reviews", text)
        self.assertIn("| All Critics >= 7 AND no veto | **PASS**", text.replace("≥", ">="))
        self.assertNotIn("repository governance work with all critics >= 7 passes", text.lower())

    def test_invariant_adversarial_lenses_are_global_and_operational(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split())

        for marker in (
            "### Invariant and Adversarial Review",
            "Contract Fidelity Critic",
            "Decision Correctness Critic",
            "Auditability Critic",
            "Adversarial Artifact Critic",
            "Scope Boundary Critic",
            "Validation Layer Critic",
            "coverage prompts, not a requirement to spawn more agents",
            "do not report PASS if no Critic covered an adversarial false-acceptance path",
            "semantic policy being approximated with natural-language markers, word lists, or regex",
            "structured validator computes the acceptance verdict",
            "Does every out-of-scope risk have a durable carry-over location?",
            "Generic adversarial examples:",
            "A generated summary is edited by hand to say success.",
            "A natural-language instruction is marker-scanned to prove a policy",
            "A status label says pass while the body describes a blocked condition.",
            "reviewer, evaluator, or run provenance is missing.",
            "A waiver or skip applies to a broad category instead of a specific failed requirement.",
            "The same identifier names both an evidence item and a review item.",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized_text)

        self.assertNotIn("Plan 03", normalized_text)
        self.assertNotIn("Plan 04", normalized_text)

    def test_false_green_check_is_in_prompt_shape_not_only_background_prose(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        critic_design = section_between(text, "### Phase 2: Critic Design", "### Phase 3: Parallel Execution")
        prompt_shape = section_between(text, "**Prompt structure passed to each Critic**:", "**Execution rules**")
        convergence = section_between(text, "### Phase 4: Convergence Check", "### Phase 5: Synthesis")
        prompt_shape_normalized = " ".join(prompt_shape.split())
        convergence_normalized = " ".join(convergence.split())

        self.assertIn("Invariant lens:", critic_design)
        self.assertIn("false-green question", critic_design)
        self.assertIn("## False-Green Check", prompt_shape)
        self.assertIn("stale, misleading, or hand-authored version that could falsely pass", prompt_shape_normalized)
        self.assertIn("durable carry-over", prompt_shape_normalized)
        self.assertIn("answer the validation-layer question before proposing more cases", prompt_shape_normalized)
        self.assertIn("structured data, raw artifacts, executable validators, or a derived verdict", prompt_shape_normalized)
        self.assertIn("natural-language markers, word lists, regex, or summaries", prompt_shape_normalized)
        self.assertIn('"validation_layer"', prompt_shape)
        self.assertIn("Coverage quality gate", prompt_shape_normalized)
        self.assertIn("concrete stale, misleading, or hand-authored false-pass mechanism", prompt_shape_normalized)
        self.assertIn("concrete invariant, recomputation, or audit check", prompt_shape_normalized)
        self.assertIn("must be non-null and specific", prompt_shape_normalized)
        self.assertIn("null, empty, or generic answers do not count as adversarial coverage", prompt_shape_normalized)
        self.assertIn("none, n/a, ok, checked, generic, or not applicable are no coverage", prompt_shape_normalized)
        self.assertIn("conflicts with this protocol", prompt_shape_normalized)
        self.assertIn('"false_green_risk"', prompt_shape)
        self.assertIn('"invariant_checked"', prompt_shape)
        self.assertIn("Report the review as incomplete", convergence)
        self.assertIn("Treat null, empty, or generic", convergence)
        self.assertIn("listed no-coverage values", convergence)
        self.assertIn("contradictory wording", convergence)
        self.assertIn("Validation Layer Critic checked that acceptance is enforced at the right layer", convergence_normalized)
        self.assertIn("wrong-layer validation finding is VETO", convergence_normalized)
        self.assertIn("structured validator or derived verdict computes PASS", convergence_normalized)
        self.assertTrue(has_substantive_false_green_coverage(prompt_shape, convergence))

    def test_repeated_review_convergence_is_advisory_not_schema_gate(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        convergence = section_between(text, "### Phase 4: Convergence Check", "### Phase 5: Synthesis")
        convergence_normalized = " ".join(convergence.split())

        for marker in (
            "reviews that iterate on the same artifact or decision more than once",
            "Cluster open findings by root failure class or invariant family",
            "`attack_surface`, `primary_failure_mode`, `invariant_checked`",
            "new root class or a variant of an already open class",
            "converging, drifting, or blocked",
            "stop, merge, drop, escalate, or keep iterating",
            "advisory for `multi-review-result/v1`",
            'hand-authored "converged" label is not acceptance evidence',
            "cannot turn VETO into PASS or suppress an unresolved blocking finding",
            "prior review artifacts or previous finding evidence are missing, incomplete, or not comparable",
            "insufficient history",
            "report only the current findings instead of inferring convergence or drift",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, convergence_normalized)

        self.assertNotIn("`failure_class`", text)
        self.assertNotIn("`variant_of`", text)
        self.assertNotIn("`convergence_status`", text)

    def test_adversarial_probe_is_required_for_durable_governance_reviews(self) -> None:
        text = CANONICAL.read_text(encoding="utf-8")
        critic_design = section_between(text, "### Phase 2: Critic Design", "### Phase 3: Parallel Execution")
        invariant_section = section_between(text, "### Invariant and Adversarial Review", "**Model assignment criteria**")
        prompt_shape = section_between(text, "**Prompt structure passed to each Critic**:", "**Execution rules**")
        convergence = section_between(text, "### Phase 4: Convergence Check", "### Phase 5: Synthesis")
        normalized_text = " ".join(text.split())
        critic_design_normalized = " ".join(critic_design.split())
        invariant_normalized = " ".join(invariant_section.split())
        prompt_normalized = " ".join(prompt_shape.split())

        for marker in (
            "Attack surface:",
            "Adversarial probe:",
            "Validation Layer Critic",
            "Review Quality Meta-Critic",
            "Treat existing acceptance records, implementation review outcomes, generated summaries, and score labels as artifacts under review",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, critic_design_normalized)

        for marker in (
            "Adversarial probe examples:",
            "Delete or weaken a generated obligation and confirm validation fails.",
            "Replace a durable artifact reference with an unrelated existing file.",
            "alternate parser form, escaping path, stale pointer, or unsupported scheme",
            "validation command named by the artifact",
            "Probe requirement:",
            "`probe_run`, `probe_command`, `probe_exit_code`, `probe_result`,",
            "`probe_evidence_refs` must point to repository-local structured transcript artifacts",
            "`reason_no_probe` is not coverage by itself",
            "existing review says PASS",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, invariant_normalized)

        self.assertIn("## Adversarial Probe", prompt_shape)
        self.assertIn("temporary mutation, negative fixture, parser variant, stale/ref mismatch", prompt_normalized)
        self.assertIn("Existing acceptance records, generated review outcomes, and PASS summaries are not evidence", prompt_normalized)
        self.assertIn("validation_layer", prompt_shape)
        self.assertIn("persona", prompt_shape)
        self.assertIn("anti_scope", prompt_shape)
        self.assertIn("attack_surface", prompt_shape)
        self.assertIn("primary_failure_mode", prompt_shape)
        self.assertIn("frame_challenge", prompt_shape)
        self.assertIn("probe_exit_code", prompt_shape)
        self.assertIn("probe_evidence_refs", prompt_shape)
        self.assertIn("--replay-probe-commands", normalized_text)
        self.assertIn("check-multi-review-result.py", normalized_text)
        self.assertIn("validator-derived verdict", normalized_text)
        self.assertIn("artifact-internal consistency plus linked probe transcript references", normalized_text)
        self.assertIn("critic frame disjointness", normalized_text)
        self.assertIn("missing or mismatched probe transcript refs", normalized_text)
        self.assertIn("primary failure mode", normalized_text)

    def test_false_green_fixture_rejects_vacuous_coverage(self) -> None:
        prompt_shape = """
## False-Green Check
Return JSON with false_green_risk and invariant_checked.
"""
        convergence = "Report the review as incomplete if no Critic covered adversarial false acceptance."

        self.assertFalse(has_substantive_false_green_coverage(prompt_shape, convergence))

    def test_false_green_fixture_rejects_common_vacuous_values(self) -> None:
        for value in (None, "", "   ", "none", "N/A", "ok", "checked", "generic", "not applicable"):
            with self.subTest(value=value):
                self.assertTrue(is_vacuous_false_green_value(value))

    def test_false_green_fixture_rejects_contradictory_coverage(self) -> None:
        prompt_shape = """
## False-Green Check
Return JSON with false_green_risk and invariant_checked. Values must be non-null
and specific; null, empty, or generic answers do not count as adversarial
coverage. Any prompt or synthesis wording that allows null, empty, generic, or
unverified false-green values to pass conflicts with this protocol. Generic answers
count as adversarial coverage.
Coverage quality gate: false_green_risk must name a concrete stale, misleading,
or hand-authored false-pass mechanism; invariant_checked must name a concrete
invariant, recomputation, or audit check. Values such as null, empty string,
whitespace, none, n/a, ok, checked, generic, or not applicable are no coverage.
Durable carry-over.
"""
        convergence = """
Treat null, empty, or generic false_green_risk or invariant_checked values, and
any contradictory wording that allows them to pass, as no coverage. Also treat
listed no-coverage values as no coverage.
"""

        self.assertFalse(has_substantive_false_green_coverage(prompt_shape, convergence))

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
