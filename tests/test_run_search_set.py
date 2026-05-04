from __future__ import annotations

import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-search-set.py"

spec = importlib.util.spec_from_file_location("run_search_set", SCRIPT)
assert spec and spec.loader
run_search_set = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run_search_set
spec.loader.exec_module(run_search_set)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


class RunSearchSetTests(unittest.TestCase):
    def test_parses_active_cases_and_ignores_archived(self) -> None:
        cases = run_search_set.parse_active_cases(
            """# Harness Search Set

## Active

### SS-001: first case
- **verify**: `python3 -c "print('one')"`

### SS-002: second case
- **verify**: `python3 -c "print('two')"`

## Archived

### SS-999: old case
- **verify**: `false`
"""
        )

        self.assertEqual([case.case_id for case in cases], ["SS-001", "SS-002"])
        self.assertEqual(cases[1].verify, 'python3 -c "print(\'two\')"')

    def test_rejects_active_case_without_verify(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected exactly one"):
            run_search_set.parse_active_cases(
                """# Harness Search Set

## Active

### SS-001: missing verifier
- **Source**: test

## Archived
"""
            )

    def test_selects_requested_case_ids(self) -> None:
        cases = [
            run_search_set.SearchSetCase("SS-001", "one", "true"),
            run_search_set.SearchSetCase("SS-002", "two", "false"),
        ]

        selected = run_search_set.selected_cases(cases, ["SS-002"])

        self.assertEqual(selected, [cases[1]])

    def test_rejects_unknown_requested_case_id(self) -> None:
        cases = [run_search_set.SearchSetCase("SS-001", "one", "true")]

        with self.assertRaisesRegex(ValueError, "unknown Active case"):
            run_search_set.selected_cases(cases, ["SS-404"])

    def test_main_returns_nonzero_when_verify_command_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            search_set = Path(tmp) / "search-set.md"
            write(
                search_set,
                """# Harness Search Set

## Active

### SS-001: failing verifier
- **verify**: `python3 -c "raise SystemExit(7)"`

## Archived
""",
            )

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = run_search_set.main(["--search-set", str(search_set), "--cwd", tmp])

            self.assertEqual(status, 1)

    def test_list_mode_does_not_run_verify_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "marker"
            search_set = Path(tmp) / "search-set.md"
            write(
                search_set,
                f"""# Harness Search Set

## Active

### SS-001: list only
- **verify**: `python3 -c "from pathlib import Path; Path('{marker}').write_text('ran')"`

## Archived
""",
            )

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = run_search_set.main(["--search-set", str(search_set), "--list"])

            self.assertEqual(status, 0)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
