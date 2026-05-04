#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "smoke-init-codex-project-fixtures.py"

spec = importlib.util.spec_from_file_location("smoke_init_codex_project_fixtures", SCRIPT)
assert spec and spec.loader
fixtures = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fixtures
spec.loader.exec_module(fixtures)


class InitCodexProjectFixtureSmokeTests(unittest.TestCase):
    def test_generated_representative_fixtures_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(fixtures.smoke(root), [])
            self.assertTrue((root / "typescript-app" / ".harness" / "traces" / "search-set.md").is_file())
            self.assertTrue((root / "python-research" / ".harness" / "traces" / "search-set.md").is_file())
            self.assertTrue((root / "migrated-claude-history" / ".claude" / "traces" / "search-set.md").is_file())

    def test_typescript_fixture_prefers_typecheck(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_typescript_fixture(Path(tmp))

            errors = fixtures.validate_project(project)

            self.assertEqual(errors, [])
            search_set = (project / ".harness" / "traces" / "search-set.md").read_text(encoding="utf-8")
            self.assertIn("- **verify**: `npm run typecheck`", search_set)
            self.assertNotIn("| tail", search_set)

    def test_python_fixture_prefers_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_python_fixture(Path(tmp))

            errors = fixtures.validate_project(project)

            self.assertEqual(errors, [])
            search_set = (project / ".harness" / "traces" / "search-set.md").read_text(encoding="utf-8")
            self.assertIn("- **verify**: `python3 -m pytest`", search_set)

    def test_migrated_fixture_reuses_claude_history_without_split_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_migrated_fixture(Path(tmp))

            errors = fixtures.validate_project(project)

            self.assertEqual(errors, [])
            self.assertFalse((project / ".harness" / "traces").exists())
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("temporarily reuses `.claude/traces/`", agents)
            self.assertIn("reviewed migration", agents)

    def test_rejects_missing_active_verify_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_typescript_fixture(Path(tmp))
            search_set = project / ".harness" / "traces" / "search-set.md"
            text = search_set.read_text(encoding="utf-8")
            search_set.write_text(text.replace("- **verify**: `npm run typecheck`", "- **verify**: `echo ok`"), encoding="utf-8")

            errors = fixtures.validate_project(project)

            self.assertTrue(any("EXPECTED VERIFY" in error for error in errors), errors)

    def test_rejects_masked_exit_status_in_search_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_python_fixture(Path(tmp))
            search_set = project / ".harness" / "traces" / "search-set.md"
            text = search_set.read_text(encoding="utf-8")
            search_set.write_text(text.replace("python3 -m pytest", "python3 -m pytest | tail -n 20"), encoding="utf-8")

            errors = fixtures.validate_project(project)

            self.assertTrue(any("MUST NOT MASK EXIT STATUS" in error for error in errors), errors)

    def test_rejects_verify_command_that_fails_in_fixture_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_typescript_fixture(Path(tmp))
            (project / "scripts" / "typecheck.js").unlink()

            errors = fixtures.validate_project(project)

            self.assertTrue(any("VERIFY COMMAND FAILED" in error for error in errors), errors)

    def test_rejects_missing_active_verify_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_python_fixture(Path(tmp))
            search_set = project / ".harness" / "traces" / "search-set.md"
            text = search_set.read_text(encoding="utf-8")
            search_set.write_text(text.replace("- **verify**: `python3 -m pytest`", ""), encoding="utf-8")

            errors = fixtures.validate_project(project)

            self.assertTrue(any("NO ACTIVE VERIFY COMMANDS" in error for error in errors), errors)

    def test_rejects_split_trace_root_for_migrated_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_migrated_fixture(Path(tmp))
            (project / ".harness" / "traces" / "evolution").mkdir(parents=True)

            errors = fixtures.validate_project(project)

            self.assertTrue(any("MUST NOT SPLIT HISTORY" in error for error in errors), errors)

    def test_smoke_replaces_existing_fixture_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = root / "typescript-app"
            stale.mkdir()
            (stale / "stale.txt").write_text("old\n", encoding="utf-8")

            errors = fixtures.smoke(root)

            self.assertEqual(errors, [])
            self.assertFalse((root / "typescript-app" / "stale.txt").exists())

    def test_rejects_missing_migrated_history_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = fixtures.create_migrated_fixture(Path(tmp))
            agents = project / "AGENTS.md"
            text = agents.read_text(encoding="utf-8")
            agents.write_text(text.replace("temporarily reuses `.claude/traces/`", "uses `.claude/traces/`"), encoding="utf-8")

            errors = fixtures.validate_project(project)

            self.assertTrue(any("MIGRATED AGENTS.md MISSING MARKER" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
