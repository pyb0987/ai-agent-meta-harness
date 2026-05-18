from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "multi-review" / "score-perspective-candidates.py"
SCENARIO = ROOT / "benchmarks/multi-review/perspective-eval/scenarios/semantic-duplicate-frames"


def run_scorer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class MultiReviewPerspectiveScorerTests(unittest.TestCase):
    def test_scores_calibration_corpus(self) -> None:
        result = run_scorer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Perspective candidate scoring: PASS", result.stdout)
        self.assertIn("semantic-duplicate-frames/candidate-strong.yml", result.stdout)
        self.assertIn("synthesis-drops-veto/candidate-weak.yml", result.stdout)

    def test_emit_agent_prompt_excludes_sealed_rubric(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "prompt.md"

            result = run_scorer("--emit-agent-prompt", str(SCENARIO), "--output", str(output))
            prompt = output.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Public Input", prompt)
        self.assertIn("multi-review-perspective-candidate/v1", prompt)
        self.assertNotIn("anchored_risks", prompt)
        self.assertNotIn("expected_detection", prompt)

    def test_rejects_candidate_that_cites_sealed_rubric(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_path = Path(tmpdir) / "candidate.yml"
            candidate = yaml.safe_load((SCENARIO / "candidate-strong.yml").read_text(encoding="utf-8"))
            candidate["critics"][0]["source_refs"] = [
                "benchmarks/multi-review/perspective-eval/scenarios/semantic-duplicate-frames/sealed-rubric.yml"
            ]
            candidate_path.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")

            result = run_scorer("--scenario-dir", str(SCENARIO), "--candidate", str(candidate_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_ref must not point to sealed oracle material", result.stderr)


if __name__ == "__main__":
    unittest.main()
