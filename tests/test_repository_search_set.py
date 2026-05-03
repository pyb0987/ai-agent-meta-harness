#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = ROOT / ".harness" / "traces"
SEARCH_SET = ROOT / ".harness" / "traces" / "search-set.md"
MAINTENANCE = ROOT / "MAINTENANCE.md"


def read_search_set() -> str:
    return SEARCH_SET.read_text(encoding="utf-8")


def active_entries(text: str) -> list[str]:
    active = text.split("## Active", 1)[1].split("## Archived", 1)[0]
    return re.findall(r"^### SS-\d{3}: .+?(?=^### SS-\d{3}: |\Z)", active, flags=re.M | re.S)


class RepositorySearchSetTests(unittest.TestCase):
    def test_repository_trace_root_has_minimum_surfaces(self) -> None:
        for relative in (
            "search-set.md",
            "evolution/001-repository-self-application-root.md",
            "failures/.gitkeep",
            "experiments/.gitkeep",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((TRACE_ROOT / relative).exists())

    def test_repository_search_set_exists_with_active_cases(self) -> None:
        text = read_search_set()
        entries = active_entries(text)

        self.assertIn('description: "Repository self-application search-set', text)
        self.assertIn('last_updated: "2026-05-04"', text)
        self.assertGreaterEqual(len(entries), 6)

    def test_active_entries_have_executable_verify_commands(self) -> None:
        for entry in active_entries(read_search_set()):
            with self.subTest(entry=entry.splitlines()[0]):
                self.assertIn("- **Source**:", entry)
                self.assertIn("- **Symptom**:", entry)
                match = re.search(r"- \*\*verify\*\*: `([^`]+)`", entry)
                self.assertIsNotNone(match)
                command = match.group(1)
                self.assertRegex(command, r"^(python3|sh) ")
                self.assertNotIn("echo ", command)
                self.assertNotIn("|", command)

    def test_active_cases_cover_current_recurring_regressions(self) -> None:
        text = read_search_set()

        for marker in (
            "Backlog review records keep enforceable gates",
            "Compatibility mirrors stay synchronized",
            "Pre-commit release gate remains wired",
            "Claude autoresearch preserves REJECT evidence",
            "Codex activation evidence stays aligned",
            "Repository trace root keeps minimum self-application surface",
            "python3 scripts/check-maintenance-review.py",
            "python3 scripts/check-compat-mirrors.py",
            "sh .githooks/pre-commit",
            "python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py",
            "python3 -m unittest tests/test_pre_commit_hook.py",
            "python3 -m unittest tests/test_repository_search_set.py",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_active_search_set_names_trace_root_completeness_regression(self) -> None:
        entries = active_entries(read_search_set())
        matching = [
            entry for entry in entries
            if "Repository trace root keeps minimum self-application surface" in entry
        ]

        self.assertEqual(len(matching), 1)
        entry = matching[0]
        self.assertIn("backlog/core.md item 33", entry)
        self.assertIn("self-application trace-root multi-review VETO", entry)
        self.assertIn("missing sibling `evolution/`, `failures/`, or `experiments/`", entry)
        self.assertIn("python3 -m unittest tests/test_repository_search_set.py", entry)

    def test_maintenance_points_repo_self_application_to_search_set(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")

        self.assertIn("For this repository's own harness-maintenance loop", text)
        self.assertIn("`.harness/traces/` tree as the active repository self-application trace root", text)
        self.assertIn("`.harness/traces/search-set.md`", text)
        self.assertIn("Active verify commands", text)
        self.assertIn("Historical `.claude/traces/` files are legacy\nClaude-local context", text)
        self.assertIn("do not write new repository maintenance traces there", text)

    def test_evolution_record_documents_legacy_claude_trace_relationship(self) -> None:
        text = (TRACE_ROOT / "evolution/001-repository-self-application-root.md").read_text(encoding="utf-8")

        self.assertIn("minimum trace surface is present", text)
        self.assertIn("Legacy Claude-local history remains under `.claude/traces/`", text)
        self.assertIn("Future repository maintenance traces should be\nwritten under `.harness/traces/`", text)


if __name__ == "__main__":
    unittest.main()
