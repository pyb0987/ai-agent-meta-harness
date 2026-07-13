#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-codex-plugin.py"

spec = importlib.util.spec_from_file_location("sync_codex_plugin", SCRIPT)
assert spec and spec.loader
sync_codex_plugin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sync_codex_plugin
spec.loader.exec_module(sync_codex_plugin)


def write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def call_silently(func, *args):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return func(*args)


def call_with_stderr(func, *args):
    stderr = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
        code = func(*args)
    return code, stderr.getvalue()


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class SyncCodexPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "adapters" / "codex"
        self.plugin = self.root / "plugins" / "ai-agent-meta-harness"

        write(
            self.source / "plugin" / ".codex-plugin" / "plugin.json",
            '{"name":"ai-agent-meta-harness","skills":"./skills/","interface":{"displayName":"Meta Harness"}}\n',
        )
        write(self.source / "README.md", "readme\n")
        write(self.source / "hook-schema.md", "schema\n")
        write(self.source / "plugin-scope.md", "scope\n")

        for skill in sync_codex_plugin.REQUIRED_SKILL_FILES:
            write(self.source / "skills" / skill, "---\nname: x\n---\n")
        for template in sync_codex_plugin.REQUIRED_TEMPLATE_FILES:
            mode = 0o755 if template.endswith("pre-commit-autoresearch-protected.sh") else 0o644
            write(self.source / "templates" / template, "template\n", mode=mode)
        for script in sync_codex_plugin.REQUIRED_SCRIPT_FILES:
            mode = 0o755 if script in {
                "check-autoresearch-protected.py",
                "check-multi-review-result.py",
                "smoke-autoresearch-hooks.py",
            } else 0o644
            write(self.source / "scripts" / script, "script\n", mode=mode)
        for example in sync_codex_plugin.REQUIRED_EXAMPLE_FILES:
            write(self.source / "examples" / example, "example\n")
        for hook in sync_codex_plugin.REQUIRED_HOOK_FILES:
            mode = 0o755 if hook.endswith("harness_orientation.py") else 0o644
            write(self.source / "hooks" / hook, "hook\n", mode=mode)
        write(self.source / "templates" / "future-template.txt", "future\n")
        write(self.source / "scripts" / "future-helper.py", "future\n")
        write(self.source / "examples" / "future-example.md", "future\n")
        write(self.source / "hooks" / "experimental" / "future-hook.py", "future\n")

        self.original = (
            sync_codex_plugin.ROOT,
            sync_codex_plugin.SOURCE_ROOT,
            sync_codex_plugin.PLUGIN_ROOT,
        )
        sync_codex_plugin.ROOT = self.root
        sync_codex_plugin.SOURCE_ROOT = self.source
        sync_codex_plugin.PLUGIN_ROOT = self.plugin

    def tearDown(self):
        sync_codex_plugin.ROOT, sync_codex_plugin.SOURCE_ROOT, sync_codex_plugin.PLUGIN_ROOT = self.original
        self.tmp.cleanup()

    def test_build_mappings_includes_new_templates_and_scripts(self):
        mappings = sync_codex_plugin.build_mappings()
        destinations = {mapping.dest.relative_to(self.plugin).as_posix() for mapping in mappings}

        self.assertIn("templates/future-template.txt", destinations)
        self.assertIn("scripts/future-helper.py", destinations)
        self.assertIn("examples/future-example.md", destinations)
        self.assertIn("hooks/experimental/future-hook.py", destinations)

    def test_write_files_preserves_executable_mode(self):
        mappings = sync_codex_plugin.build_mappings()

        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)

        source_mode = stat.S_IMODE((self.source / "templates" / "hooks" / "pre-commit-autoresearch-protected.sh").stat().st_mode)
        dest_mode = stat.S_IMODE((self.plugin / "templates" / "hooks" / "pre-commit-autoresearch-protected.sh").stat().st_mode)
        self.assertEqual(dest_mode, source_mode)
        self.assertTrue(os.access(self.plugin / "scripts" / "smoke-autoresearch-hooks.py", os.X_OK))
        self.assertTrue(os.access(self.plugin / "hooks" / "experimental" / "harness_orientation.py", os.X_OK))

    def test_check_files_rejects_missing_required_hook_source(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        (self.source / "hooks" / "experimental" / "harness_orientation.py").unlink()

        code, stderr = call_with_stderr(sync_codex_plugin.check_files, mappings)

        self.assertEqual(code, 1)
        self.assertIn("MISSING REQUIRED SOURCE: adapters/codex/hooks/experimental/harness_orientation.py", stderr)

    def test_check_files_detects_mode_mismatch(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        (self.plugin / "scripts" / "smoke-autoresearch-hooks.py").chmod(0o644)

        self.assertEqual(call_silently(sync_codex_plugin.check_files, mappings), 1)

    def test_check_files_rejects_missing_required_example_source(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        (self.source / "examples" / "AGENTS.md.example").unlink()

        code, stderr = call_with_stderr(sync_codex_plugin.check_files, mappings)

        self.assertEqual(code, 1)
        self.assertIn("MISSING REQUIRED SOURCE: adapters/codex/examples/AGENTS.md.example", stderr)

    def test_check_files_rejects_extra_generated_file(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        write(self.plugin / "examples" / "unexpected.md", "extra\n")

        code, stderr = call_with_stderr(sync_codex_plugin.check_files, mappings)

        self.assertEqual(code, 1)
        self.assertIn("EXTRA GENERATED: plugins/ai-agent-meta-harness/examples/unexpected.md", stderr)

    def test_check_files_rejects_invalid_generated_manifest(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        generated_manifest = self.plugin / ".codex-plugin" / "plugin.json"
        original_validate_manifest = sync_codex_plugin.validate_manifest
        calls = []

        def fake_validate_manifest(path: Path, reader=None):
            calls.append(path)
            if path == generated_manifest:
                return ["plugin.json skills must point to ./skills/"]
            return []

        sync_codex_plugin.validate_manifest = fake_validate_manifest
        try:
            code, stderr = call_with_stderr(sync_codex_plugin.check_files, mappings)
        finally:
            sync_codex_plugin.validate_manifest = original_validate_manifest

        self.assertEqual(code, 1)
        self.assertIn(generated_manifest, calls)
        self.assertIn("plugin.json skills must point to ./skills/", stderr)
        self.assertNotIn("OUT OF SYNC", stderr)

    def test_check_uses_staged_content_and_ignores_unstaged_generated_drift(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        write(self.plugin / "README.md", "unstaged generated drift\n")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 0, stderr)

    def test_worktree_check_rejects_unstaged_generated_drift(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        write(self.plugin / "README.md", "unstaged generated drift\n")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check", "--worktree"])

        self.assertEqual(code, 1)
        self.assertIn("OUT OF SYNC: plugins/ai-agent-meta-harness/README.md", stderr)

    def test_check_rejects_partially_staged_generated_content(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        write(self.source / "README.md", "staged source change\n")
        write(self.plugin / "README.md", "matching but unstaged generated change\n")
        git(self.root, "add", "adapters/codex/README.md")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 1)
        self.assertIn("OUT OF SYNC: plugins/ai-agent-meta-harness/README.md", stderr)

    def test_check_rejects_staged_added_source_without_generated_file(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        write(self.source / "templates" / "new-template.md", "new source\n")
        git(self.root, "add", "adapters/codex/templates/new-template.md")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 1)
        self.assertIn("MISSING GENERATED: plugins/ai-agent-meta-harness/templates/new-template.md", stderr)

    def test_check_rejects_staged_added_extra_generated_file(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        write(self.plugin / "templates" / "unexpected.md", "extra\n")
        git(self.root, "add", "plugins/ai-agent-meta-harness/templates/unexpected.md")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 1)
        self.assertIn("EXTRA GENERATED: plugins/ai-agent-meta-harness/templates/unexpected.md", stderr)

    def test_check_rejects_partially_staged_generated_mode(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        source_script = self.source / "scripts" / "future-helper.py"
        source_script.chmod(0o755)
        (self.plugin / "scripts" / "future-helper.py").chmod(0o755)
        git(self.root, "add", "adapters/codex/scripts/future-helper.py")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 1)
        self.assertIn("MODE MISMATCH: plugins/ai-agent-meta-harness/scripts/future-helper.py", stderr)

    def test_check_rejects_staged_deleted_generated_file(self):
        mappings = sync_codex_plugin.build_mappings()
        self.assertEqual(call_silently(sync_codex_plugin.write_files, mappings), 0)
        git(self.root, "init")
        git(self.root, "add", ".")
        git(self.root, "rm", "--cached", "plugins/ai-agent-meta-harness/README.md")

        code, stderr = call_with_stderr(sync_codex_plugin.main, ["--check"])

        self.assertEqual(code, 1)
        self.assertIn("MISSING GENERATED: plugins/ai-agent-meta-harness/README.md", stderr)


if __name__ == "__main__":
    unittest.main()
