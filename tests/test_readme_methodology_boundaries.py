from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def normalized_readme() -> str:
    return " ".join(readme_text().split())


class ReadmeMethodologyBoundaryTests(unittest.TestCase):
    def test_autoresearch_flow_labels_filenames_as_repository_examples(self) -> None:
        text = normalized_readme()

        for marker in (
            "Set up a direction file + immutable evaluator + mutable search surface",
            "this repository's examples usually call them program.md, evaluate.py, and genome",
            "`evaluate.py` is this repository's common filename convention, not a paper-level requirement",
            "Adapters choose the runtime-appropriate evaluator file, command, and enforcement mechanism",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_autoresearch_flow_preserves_fixed_evaluator_principle(self) -> None:
        text = normalized_readme()
        lower = text.lower()

        self.assertIn("if the agent can modify its own evaluator, it contaminates the feedback signal", lower)
        self.assertIn("mutable search surface", text)
        self.assertNotIn("paper requires program.md", lower)
        self.assertNotIn("paper requires evaluate.py", lower)
        self.assertNotIn("paper requires genome", lower)

    def test_readme_separates_paper_results_from_local_repository_evidence(self) -> None:
        text = normalized_readme()

        for marker in (
            "This project operationalizes Meta-Harness paper principles into a practical harness toolkit, runtime adapters, and verification gates",
            "does not claim a local reproduction of the paper's end-to-end benchmark gains",
            "Evidence categories used in this repository",
            "Paper results and benchmark claims",
            "Cited as paper context only; not local reproduction evidence",
            "Repository methodology and documentation correctness",
            "Adapter and generated-artifact operability",
            "Repository self-application evidence",
            ".harness/traces/search-set.md",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_precise_paper_numbers_remain_labeled_as_paper_context(self) -> None:
        text = normalized_readme()
        lower = text.lower()

        self.assertIn(
            "its introduction cites prior harness-sensitivity evidence that changing only the harness can produce a 6x performance gap on the same benchmark",
            text,
        )
        self.assertIn("6x performance gap on the same benchmark", text)
        self.assertIn("full trace access achieved 56.7% accuracy vs 38.7% with summaries (Table 3)", text)
        self.assertIn("Paper results and benchmark claims", text)
        self.assertNotIn("meta-harness demonstrated that", lower)
        self.assertNotIn("this repository reproduces", lower)
        self.assertNotIn("locally reproduced the paper", lower)

    def test_public_framing_avoids_reproduction_or_proof_overclaim(self) -> None:
        readme = normalized_readme()
        maintenance = " ".join((ROOT / "MAINTENANCE.md").read_text(encoding="utf-8").split())
        backlog = " ".join((ROOT / "backlog" / "README.md").read_text(encoding="utf-8").split())
        combined = f"{readme} {maintenance} {backlog}".lower()

        framing = "operationalizes meta-harness paper principles into a practical harness toolkit, runtime adapters, and verification gates"
        self.assertIn(framing, readme.lower())
        self.assertIn(framing, maintenance.lower())
        self.assertIn(framing, backlog.lower())
        for forbidden in (
            "paper reproduction package",
            "full meta-harness implementation",
            "empirical proof of the paper's performance claims",
            "demonstrated the paper's benchmark gains",
        ):
            with self.subTest(forbidden=forbidden):
                if forbidden == "paper reproduction package":
                    self.assertIn("not a paper reproduction package", combined)
                elif forbidden == "demonstrated the paper's benchmark gains":
                    self.assertIn("not a paper reproduction package or a claim that this local repo has demonstrated the paper's benchmark gains", combined)
                else:
                    self.assertNotIn(forbidden, combined)

    def test_readme_has_compact_paper_claim_traceability_map(self) -> None:
        text = normalized_readme()

        for marker in (
            "Paper claim traceability",
            "README Claim",
            "Paper Location",
            "Local Status",
            "Changing only the harness can produce a 6x performance gap on the same benchmark",
            "Paper Introduction, citing prior harness sensitivity evidence",
            "not locally reproduced here",
            "Meta-Harness improves online text classification by 7.7 points while using 4x fewer context tokens",
            "Paper Abstract and Section 4.1 comparison against ACE",
            "Full traces outperform summaries in the online text-classification ablation",
            "Paper Table 3: scores-only, scores-plus-summary, and full-interface comparison",
            "Paper result used to motivate this repo's trace discipline",
            "Meta-Harness searches over harness code with source, scores, and execution traces available through the filesystem",
            "Paper Abstract and system design description of the agentic proposer/filesystem interface",
            "Paper-backed design principle adapted into this repo's code-space search and trace-root conventions",
            "The outer loop proposes, evaluates, and logs candidates rather than adding persistent multi-agent orchestration",
            "Paper system design: agentic proposer plus evaluator plus filesystem trace history",
            "Repository-calibrated workflow rule",
            "Paper Appendix A/A.2 qualitative search trajectory and discussion",
            "Paper Appendix D practical implementation tips",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_code_space_and_outer_loop_claims_are_source_scoped(self) -> None:
        text = normalized_readme()

        for marker in (
            "**Code-space search** — Paper-backed by the Meta-Harness proposer/filesystem design",
            "Repository-calibrated rule: \"try harder\" is noise",
            "**Minimal outer loop** — Paper-backed by the system's propose -> evaluate -> log loop over candidate harnesses",
            "Repository-calibrated rule: avoid orchestration that makes the harness harder to verify",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

        self.assertNotIn("Code-space search — Paper-backed principle, repository-calibrated surfaces", text)
        self.assertNotIn("Minimal outer loop — Paper-backed principle", text)


if __name__ == "__main__":
    unittest.main()
