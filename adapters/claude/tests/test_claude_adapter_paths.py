#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check-claude-adapter-paths.py"


spec = importlib.util.spec_from_file_location("claude_adapter_paths", SCRIPT)
assert spec and spec.loader
claude_adapter_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claude_adapter_paths)


class ClaudeAdapterPathTests(unittest.TestCase):
    def make_temp_git_repo(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        subprocess.run(
            ["git", "init"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (root / "adapters/claude/commands").mkdir(parents=True)
        return root

    def run_checker_with_root(self, root: Path) -> tuple[int, str, str]:
        original_root = claude_adapter_paths.ROOT
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            claude_adapter_paths.ROOT = root
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = claude_adapter_paths.main()
        finally:
            claude_adapter_paths.ROOT = original_root
        return returncode, stdout.getvalue(), stderr.getvalue()

    def test_repo_claude_adapter_paths_pass(self):
        result = subprocess.run(
            ["python3", str(SCRIPT)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Claude adapter lexical path docs are consistent", result.stdout)

    def test_flags_bare_trace_paths(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/commands/init-harness.md",
            "Write traces/evolution/001-initial-harness.md\n",
        )
        self.assertTrue(any("bare trace path" in error for error in errors))

    def test_flags_generic_bare_trace_root(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/skills/harness-engineer/SKILL.md",
            'Prior similar cases: {traces/ reference or "none"}\n',
        )
        self.assertTrue(any("bare trace path" in error for error in errors))

    def test_flags_generic_bare_failures_root(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/skills/autoresearch/SKILL.md",
            "Episodes are a different layer from failures/.\n",
        )
        self.assertTrue(any("bare trace path" in error for error in errors))

    def test_flags_bare_settings_path(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/commands/init-harness.md",
            "Write hooks into settings.local.json\n",
        )
        self.assertTrue(any("bare settings.local.json" in error for error in errors))

    def test_flags_bare_hooks_path(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/commands/init-harness.md",
            "Place scripts under hooks/tsc-check.sh\n",
        )
        self.assertTrue(any("bare hooks path" in error for error in errors))

    def test_flags_generic_bare_hooks_root(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/commands/init-harness.md",
            "Place scripts under hooks/.\n",
        )
        self.assertTrue(any("bare hooks path" in error for error in errors))

    def test_allows_explicit_claude_trace_paths(self):
        errors = claude_adapter_paths.validate_text(
            "adapters/claude/skills/harness-engineer/SKILL.md",
            "Read `.claude/traces/failures/` before diagnosis.\n",
        )
        self.assertEqual(errors, [])

    def test_readme_core_section_allows_runtime_neutral_trace_examples(self):
        text = "## Core Principles\nUse traces/evolution/.\n## Claude Code Adapter\nUse .claude/traces/evolution/.\n## Codex Adapter\n"
        self.assertEqual(claude_adapter_paths.validate_text("README.md", text), [])

    def test_readme_reports_real_line_numbers(self):
        text = "\n".join([
            "# Title",
            "## Core Principles",
            "Use traces/evolution/.",
            "## Claude Code Adapter",
            "Use traces/evolution/.",
            "## Codex Adapter",
        ])
        errors = claude_adapter_paths.validate_text("README.md", text)
        self.assertTrue(any(error.startswith("README.md:5:") for error in errors))

    def test_discovers_current_claude_markdown_surfaces(self):
        files = claude_adapter_paths.discover_checked_files()
        self.assertIn("adapters/claude/skills/multi-review/SKILL.md", files)
        self.assertIn("adapters/claude/commands/init-harness.md", files)

    def test_discovers_staged_added_claude_markdown_surfaces(self):
        files = claude_adapter_paths.discover_checked_files({
            "adapters/claude/skills/new-skill/SKILL.md",
        })
        self.assertIn("adapters/claude/skills/new-skill/SKILL.md", files)

    def test_deleted_index_path_is_not_discovered(self):
        files = claude_adapter_paths.discover_checked_files({"README.md"})
        self.assertNotIn("adapters/claude/skills/deleted/SKILL.md", files)

    def test_index_content_is_validated(self):
        original_reader = claude_adapter_paths.read_index_text
        try:
            claude_adapter_paths.read_index_text = lambda path: "Write traces/evolution/001.md\n"
            text = claude_adapter_paths.read_index_text(
                "adapters/claude/commands/init-harness.md"
            )
        finally:
            claude_adapter_paths.read_index_text = original_reader
        errors = claude_adapter_paths.validate_text("adapters/claude/commands/init-harness.md", text)
        self.assertTrue(any("bare trace path" in error for error in errors))

    def test_index_added_content_is_validated(self):
        indexed_path = "adapters/claude/skills/new-skill/SKILL.md"
        indexed = {indexed_path}
        files = claude_adapter_paths.discover_checked_files(indexed)

        original_reader = claude_adapter_paths.read_index_text
        try:
            claude_adapter_paths.read_index_text = lambda path: "Write hooks/check.sh\n"
            self.assertIn(indexed_path, files)
            text = claude_adapter_paths.read_index_text(indexed_path)
        finally:
            claude_adapter_paths.read_index_text = original_reader

        errors = claude_adapter_paths.validate_text(indexed_path, text)
        self.assertTrue(any("bare hooks path" in error for error in errors))

    def test_temp_git_checks_staged_content_not_unstaged_worktree(self):
        root = self.make_temp_git_repo()
        path = root / "adapters/claude/commands/init-harness.md"
        path.write_text("Write .claude/traces/evolution/001.md\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", path.relative_to(root).as_posix()],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        path.write_text("Write traces/evolution/001.md\n", encoding="utf-8")

        returncode, stdout, stderr = self.run_checker_with_root(root)

        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Claude adapter lexical path docs are consistent", stdout)

    def test_temp_git_flags_staged_added_bare_path(self):
        root = self.make_temp_git_repo()
        path = root / "adapters/claude/commands/init-harness.md"
        path.write_text("Write hooks/tsc-check.sh\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", path.relative_to(root).as_posix()],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        returncode, _stdout, stderr = self.run_checker_with_root(root)

        self.assertEqual(returncode, 1)
        self.assertIn("bare hooks path", stderr)

    def test_temp_git_ignores_index_deleted_path(self):
        root = self.make_temp_git_repo()
        path = root / "adapters/claude/commands/init-harness.md"
        relative = path.relative_to(root).as_posix()
        path.write_text("Write .claude/hooks/tsc-check.sh\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", relative],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        path.unlink()
        subprocess.run(
            ["git", "rm", "--cached", relative],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        returncode, stdout, stderr = self.run_checker_with_root(root)

        self.assertEqual(returncode, 0, stderr)
        self.assertIn("Claude adapter lexical path docs are consistent", stdout)


if __name__ == "__main__":
    unittest.main()
