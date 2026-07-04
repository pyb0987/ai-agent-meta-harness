#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = ROOT / ".harness" / "traces"
SEARCH_SET = ROOT / "backlog" / "repository-search-set.md"
MAINTENANCE = ROOT / "MAINTENANCE.md"
RUN_SEARCH_SET = ROOT / "scripts" / "run-search-set.py"


def read_search_set() -> str:
    return SEARCH_SET.read_text(encoding="utf-8")


def load_run_search_set_module():
    spec = importlib.util.spec_from_file_location("run_search_set", RUN_SEARCH_SET)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def active_entries(text: str) -> list[str]:
    active = text.split("## Active", 1)[1].split("## Archived", 1)[0]
    return re.findall(r"^### SS-\d{3}: .+?(?=^### SS-\d{3}: |\Z)", active, flags=re.M | re.S)


class RepositorySearchSetTests(unittest.TestCase):
    def test_repository_search_set_is_product_manifest_not_trace(self) -> None:
        self.assertTrue(SEARCH_SET.is_file())
        self.assertFalse((TRACE_ROOT / "search-set.md").exists())

    def test_repository_search_set_exists_with_active_cases(self) -> None:
        text = read_search_set()
        entries = active_entries(text)

        self.assertIn('description: "Repository regression search-set', text)
        self.assertIn('last_updated: "2026-07-04"', text)
        self.assertGreaterEqual(len(entries), 7)

    def test_active_entries_have_executable_verify_commands(self) -> None:
        run_search_set = load_run_search_set_module()
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
                self.assertGreater(len(run_search_set.verify_argv(command)), 1)

    def test_search_set_runner_rejects_shell_syntax_before_execution(self) -> None:
        run_search_set = load_run_search_set_module()

        unsafe_commands = (
            "python3 scripts/check-maintenance-review.py | tail -20",
            "BASE_REF=main python3 scripts/check-search-set-evidence.py",
            "python3 scripts/check-maintenance-review.py && python3 scripts/check-search-set-evidence.py",
            "python3 scripts/check-maintenance-review.py > /tmp/out",
            "python3 $(pwd)/scripts/check-maintenance-review.py",
            "python3 scripts/*.py",
        )
        for command in unsafe_commands:
            with self.subTest(command=command):
                with self.assertRaises(run_search_set.UnsafeVerifyCommand):
                    run_search_set.verify_argv(command)

    def test_search_set_runner_rejects_unsafe_case_before_subprocess(self) -> None:
        run_search_set = load_run_search_set_module()
        case = run_search_set.SearchSetCase(
            case_id="SS-999",
            title="Unsafe syntax fixture",
            verify="python3 scripts/check-maintenance-review.py | tail -20",
        )

        stderr = io.StringIO()
        stdout = io.StringIO()
        with (
            mock.patch("subprocess.run") as subprocess_run,
            mock.patch("sys.stderr", stderr),
            mock.patch("sys.stdout", stdout),
        ):
            status = run_search_set.run_case(case, cwd=ROOT, timeout=1)

        self.assertEqual(status, 2)
        subprocess_run.assert_not_called()
        self.assertIn("==> SS-999: Unsafe syntax fixture", stdout.getvalue())
        self.assertIn("SS-999: unsafe verify command", stderr.getvalue())
        self.assertIn("without pipes, redirects, chaining", stderr.getvalue())

    def test_search_set_runner_preserves_case_filtering_with_safe_argv(self) -> None:
        run_search_set = load_run_search_set_module()
        cases = run_search_set.parse_active_cases(read_search_set())

        selected = run_search_set.selected_cases(cases, ["SS-006"])

        self.assertEqual([case.case_id for case in selected], ["SS-006"])
        self.assertEqual(
            run_search_set.verify_argv(selected[0].verify),
            ["python3", "-m", "unittest", "tests/test_repository_search_set.py"],
        )

    def test_active_cases_cover_current_recurring_regressions(self) -> None:
        text = read_search_set()

        for marker in (
            "Backlog review records keep enforceable gates",
            "Compatibility mirrors stay synchronized",
            "Pre-commit release gate remains wired",
            "Claude autoresearch preserves REJECT evidence",
            "Codex activation evidence stays aligned",
            "Repository search-set stays outside maintainer traces",
            "Claude worktrees keep one shared trace root",
            "python3 scripts/check-maintenance-review.py",
            "python3 scripts/check-compat-mirrors.py",
            "sh .githooks/pre-commit",
            "python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py",
            "python3 -m unittest tests/test_pre_commit_hook.py",
            "python3 -m unittest tests/test_repository_search_set.py",
            "python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_claude_init_harness_fixture.py tests/test_maintenance_policy_boundaries.py",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_active_search_set_names_provider_trace_boundary(self) -> None:
        entries = active_entries(read_search_set())
        matching = [
            entry for entry in entries
            if "Repository search-set stays outside maintainer traces" in entry
        ]

        self.assertEqual(len(matching), 1)
        entry = matching[0]
        self.assertIn("Trace is working memory; harness changes are the product", entry)
        self.assertIn("repository regression manifest is stored under `.harness/traces/`", entry)
        self.assertIn("maintainer working-memory traces with the shipped product surface", entry)
        self.assertIn("python3 -m unittest tests/test_repository_search_set.py", entry)

    def test_maintenance_points_repo_self_application_to_search_set(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("For this repository's own harness-maintenance loop", text)
        self.assertIn("`backlog/repository-search-set.md` as the tracked repository regression manifest", normalized)
        self.assertIn("Maintainer/user trace files are local working memory", normalized)
        self.assertIn("Active verify commands", text)
        self.assertIn("do not publish raw maintainer traces as product artifacts", normalized)

    def test_maintainer_trace_directories_are_ignored_working_memory(self) -> None:
        ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".harness/traces/", ignore_text)

    def test_raw_maintainer_trace_files_are_not_tracked(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", ".harness/traces"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
