from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "adapters" / "claude" / "skills" / "autoresearch" / "SKILL.md"
MIRROR_SKILL = ROOT / "skills" / "autoresearch" / "SKILL.md"


def skill_text(path: Path = SKILL) -> str:
    return path.read_text(encoding="utf-8")


def write_verbs_pattern(text: str) -> str:
    match = re.search(r'^WRITE_VERBS="(.+)"$', text, re.MULTILINE)
    if not match:
        raise AssertionError("missing WRITE_VERBS double-quoted pattern")
    return match.group(1)


def grep_matches(pattern: str, command: str) -> bool:
    result = subprocess.run(
        ["grep", "-Eq", pattern],
        input=command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise AssertionError(result.stderr)
    return result.returncode == 0


class ClaudeAutoresearchHookGuidanceTests(unittest.TestCase):
    def test_bash_write_heuristic_covers_representative_bypass_patterns(self) -> None:
        pattern = write_verbs_pattern(skill_text())
        blocked = (
            'echo "x" > evaluate.py',
            'python -c "open(\'evaluate.py\', \'w\').write(\'x\')"',
            'python -c "open(file=\'evaluate.py\', mode=\'w\').write(\'x\')"',
            'python -c "from pathlib import Path; Path(\'evaluate.py\').open(\'r+\').write(\'x\')"',
            'python -c "from pathlib import Path; Path(\'evaluate.py\').write_text(\'x\')"',
        )

        for command in blocked:
            with self.subTest(command=command):
                self.assertTrue(grep_matches(pattern, command))

    def test_bash_write_heuristic_does_not_match_read_only_open(self) -> None:
        pattern = write_verbs_pattern(skill_text())

        self.assertFalse(grep_matches(pattern, 'python -c "open(\'evaluate.py\', mode=\'r\').read()"'))

    def test_guidance_names_heuristic_boundary_and_smoke_expectations(self) -> None:
        text = skill_text()

        for marker in (
            "common Python open/pathlib writes",
            "This is a heuristic",
            "pre-commit/CI diff protection as the hard layer",
            "Path('\\''evaluate.py'\\'').open('\\''r+'\\'')",
            "open(file='\\''evaluate.py'\\'', mode='\\''w'\\'')",
            "Each command must exit 1",
            "mode='r').read()",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_compatibility_mirror_has_same_hook_guidance(self) -> None:
        canonical = skill_text(SKILL)
        mirror = skill_text(MIRROR_SKILL)

        for marker in (
            "WRITE_VERBS=",
            "common Python open/pathlib writes",
            "pre-commit/CI diff protection as the hard layer",
            "Each command must exit 1",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))


if __name__ == "__main__":
    unittest.main()
