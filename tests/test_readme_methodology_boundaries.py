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


if __name__ == "__main__":
    unittest.main()
