from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "multi-review" / "check-perspective-corpus.py"
CORPUS_ROOT = ROOT / "benchmarks" / "multi-review" / "perspective-eval" / "scenarios"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class MultiReviewPerspectiveCorpusTests(unittest.TestCase):
    def test_accepts_seed_perspective_corpus(self) -> None:
        completed = run_cli()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Perspective corpus scenarios valid: 3", completed.stdout)

    def test_rejects_candidate_quality_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "scenarios"
            scenario = root / "bad-scenario"
            scenario.mkdir(parents=True)
            source = CORPUS_ROOT / "semantic-duplicate-frames"
            for name in ("public-input.md", "sealed-rubric.yml", "candidate-strong.yml", "candidate-weak.yml"):
                (scenario / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
            weak = yaml.safe_load((scenario / "candidate-weak.yml").read_text(encoding="utf-8"))
            weak["intended_quality"] = "strong"
            (scenario / "candidate-weak.yml").write_text(yaml.safe_dump(weak, sort_keys=False), encoding="utf-8")

            completed = run_cli("--corpus-root", str(root))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("intended_quality must be weak", completed.stderr)


if __name__ == "__main__":
    unittest.main()
