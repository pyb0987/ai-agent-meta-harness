from __future__ import annotations

from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "adapters" / "claude" / "skills" / "autoresearch" / "SKILL.md"
MIRROR_SKILL = ROOT / "skills" / "autoresearch" / "SKILL.md"


def skill_text(path: Path = SKILL) -> str:
    return path.read_text(encoding="utf-8")


def hard_layer_script(text: str) -> str:
    marker = "# protect-autoresearch-evaluator-diff.sh"
    marker_index = text.find(marker)
    if marker_index == -1:
        raise AssertionError("missing hard-layer script marker")
    fence_start = text.rfind("```bash", 0, marker_index)
    if fence_start == -1:
        raise AssertionError("missing hard-layer bash fence")
    body_start = text.index("\n", fence_start) + 1
    body_end = text.index("```", body_start)
    return text[body_start:body_end]


def run(command: list[str], cwd: Path, **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )


class ClaudeAutoresearchHardLayerGuidanceTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        repo = Path(tempdir.name)
        (repo / ".claude").mkdir()
        (repo / ".githooks").mkdir()
        (repo / "evaluate.py").write_text("print('baseline')\n", encoding="utf-8")
        (repo / "genome.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / ".claude/autoresearch-protected.txt").write_text("evaluate.py\n", encoding="utf-8")

        script = repo / ".githooks/protect-autoresearch-evaluator.sh"
        script.write_text(hard_layer_script(skill_text()), encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)

        for command in (
            ["git", "init"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "config", "user.name", "Test User"],
            ["git", "add", "."],
            ["git", "commit", "-m", "initial"],
        ):
            result = run(command, repo)
            self.assertEqual(result.returncode, 0, result)

        return tempdir, repo, script

    def test_hard_layer_script_blocks_staged_protected_evaluator_edit(self) -> None:
        _, repo, script = self.make_repo()
        (repo / "evaluate.py").write_text("print('tampered')\n", encoding="utf-8")
        self.assertEqual(run(["git", "add", "evaluate.py"], repo).returncode, 0)

        result = run(["sh", str(script)], repo)

        self.assertEqual(result.returncode, 1, result)
        self.assertIn("BLOCKED: protected evaluator files changed:", result.stderr)
        self.assertIn("evaluate.py", result.stderr)

    def test_hard_layer_script_allows_staged_mutable_genome_edit(self) -> None:
        _, repo, script = self.make_repo()
        (repo / "genome.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.assertEqual(run(["git", "add", "genome.py"], repo).returncode, 0)

        result = run(["sh", str(script)], repo)

        self.assertEqual(result.returncode, 0, result)
        self.assertEqual(result.stderr, "")

    def test_guidance_names_hard_layer_install_and_smoke_expectations(self) -> None:
        text = skill_text()

        for marker in (
            "Hard-layer diff protection (pre-commit/CI)",
            "Claude tool hooks are a fast local warning/blocking layer",
            "project-local Git diff check as the\nhard protection layer",
            ".claude/autoresearch-protected.txt",
            ".githooks/protect-autoresearch-evaluator.sh",
            "CI wiring should set `BASE_REF`",
            "do not treat\nthe heuristic Claude hooks as sufficient hard protection",
            "The protected evaluator edit must exit 1",
            "mutable genome edit not listed",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_setup_completion_requires_hard_layer_install_and_smoke(self) -> None:
        for path in (SKILL, MIRROR_SKILL):
            text = skill_text(path)
            for marker in (
                "Hard-layer diff protection (pre-commit/CI) installed, or an explicit skipped reason recorded",
                "Hard-layer smoke result recorded",
                "protected evaluator edit fails with `BLOCKED`",
                "staged mutable genome edit not listed in `.claude/autoresearch-protected.txt` passes",
                "fast local protection, not a replacement for the hard pre-commit/CI layer",
            ):
                with self.subTest(path=path, marker=marker):
                    self.assertIn(marker, text)

    def test_compatibility_mirror_has_same_hard_layer_guidance(self) -> None:
        canonical = skill_text(SKILL)
        mirror = skill_text(MIRROR_SKILL)

        for marker in (
            "Hard-layer diff protection (pre-commit/CI)",
            "# protect-autoresearch-evaluator-diff.sh",
            ".claude/autoresearch-protected.txt",
            "CI wiring should set `BASE_REF`",
            "The protected evaluator edit must exit 1",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))


if __name__ == "__main__":
    unittest.main()
