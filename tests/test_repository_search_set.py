#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import re
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TRACE_ROOT = ROOT / ".harness" / "traces"
SEARCH_SET = ROOT / ".harness" / "traces" / "search-set.md"
MAINTENANCE = ROOT / "MAINTENANCE.md"
RUN_SEARCH_SET = ROOT / "scripts" / "run-search-set.py"
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.S)
REQUIRED_EVOLUTION_FIELDS = (
    "iteration",
    "date",
    "type",
    "verdict",
    "files_changed",
    "refs",
)
REQUIRED_FAILURE_FIELDS = (
    "date",
    "escalated_to",
    "search_set_id",
    "resolved",
)


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


def frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


class RepositorySearchSetTests(unittest.TestCase):
    def test_repository_trace_root_has_minimum_surfaces(self) -> None:
        for relative in (
            "search-set.md",
            "evolution/001-repository-self-application-root.md",
            "evolution/002-self-application-evidence-review.md",
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

    def test_repository_evolution_records_follow_schema(self) -> None:
        for path in sorted((TRACE_ROOT / "evolution").glob("*.md")):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                fields = frontmatter(text)
                self.assertEqual([field for field in REQUIRED_EVOLUTION_FIELDS if field not in fields], [])
                self.assertRegex(fields["iteration"], r"^\d+$")
                self.assertIn(fields["type"], {"additive", "subtractive", "structural"})
                self.assertIn(fields["verdict"], {"improved", "regressed", "neutral"})
                self.assertTrue(fields["files_changed"].startswith("["))
                self.assertTrue(fields["refs"].startswith("["))
                iteration = int(fields["iteration"])
                self.assertIn(f"## Iteration {iteration:03d}:", text)
                for heading in ("### Diagnosis", "### Change", "### Result", "### Lesson"):
                    self.assertIn(heading, text)
                self.assertRegex(text, r"- Before: .+")
                self.assertRegex(text, r"- After: .+")

    def test_repository_failure_records_follow_schema(self) -> None:
        for path in sorted((TRACE_ROOT / "failures").glob("*.md")):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                fields = frontmatter(text)
                self.assertEqual([field for field in REQUIRED_FAILURE_FIELDS if field not in fields], [])
                self.assertIn(fields["resolved"], {"true", "false"})
                self.assertIn(fields["escalated_to"], {"instructions", "docs", "skill", "hook", "tool", "none"})
                self.assertIn("## Failure:", text)
                for heading in ("### Observation", "### Root Cause", "### Fix", "### Prevention"):
                    self.assertIn(heading, text)

    def test_evolution_review_trace_records_self_application_evidence_boundary(self) -> None:
        text = (TRACE_ROOT / "evolution/002-self-application-evidence-review.md").read_text(encoding="utf-8")

        for marker in (
            "iteration: 2",
            "verdict: improved",
            "thin tracked\nself-application evidence",
            "does not copy that\nhistory blindly",
            "avoids overclaiming richer local\n  self-application evidence",
            "not synthetic failures",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
