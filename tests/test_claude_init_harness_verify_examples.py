from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INIT_HARNESS = ROOT / "adapters" / "claude" / "commands" / "init-harness.md"
MIRROR_INIT_HARNESS = ROOT / "commands" / "init-harness.md"


def seed_verify_examples(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    examples: dict[str, str] = {}
    for name in ("TypeScript", "Python", "Godot"):
        match = re.search(rf"^- {name}: `(.+)`$", text, re.MULTILINE)
        if not match:
            raise AssertionError(f"missing {name} verify example in {path}")
        examples[name] = match.group(1)
    return examples


class ClaudeInitHarnessVerifyExamplesTest(unittest.TestCase):
    def test_seed_verify_examples_preserve_failing_exit_status(self) -> None:
        examples = seed_verify_examples(INIT_HARNESS)
        executable_by_name = {
            "TypeScript": "tsc",
            "Python": "pytest",
            "Godot": "godot",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            for executable in executable_by_name.values():
                tool = bin_dir / executable
                tool.write_text(
                    "#!/bin/sh\n"
                    "printf '%s\\n' line1 line2 line3 line4 line5 line6\n"
                    "exit 42\n",
                    encoding="utf-8",
                )
                tool.chmod(tool.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TMPDIR"] = str(temp_path)

            for name, command in examples.items():
                with self.subTest(name=name):
                    result = subprocess.run(
                        command,
                        cwd=temp_path,
                        env=env,
                        shell=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    self.assertEqual(result.returncode, 42, result)
                    self.assertIn("EXIT: 42", result.stdout)
                    self.assertIn("line6", result.stdout)

    def test_compatibility_mirror_has_same_seed_verify_examples(self) -> None:
        self.assertEqual(
            seed_verify_examples(INIT_HARNESS),
            seed_verify_examples(MIRROR_INIT_HARNESS),
        )


if __name__ == "__main__":
    unittest.main()
