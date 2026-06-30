from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-harness-dogfood.py"

spec = importlib.util.spec_from_file_location("check_harness_dogfood", SCRIPT)
assert spec and spec.loader
dogfood = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dogfood)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class HarnessDogfoodTests(unittest.TestCase):
    def test_sparse_trace_root_alone_is_not_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / ".harness/traces/search-set.md",
                """---
description: "test"
---
# Harness Search Set

## Active

## Archived
""",
            )

            report = dogfood.build_report(root, changed_paths=[])

            self.assertEqual(report["schema_version"], "harness-dogfood-report/v1")
            self.assertEqual(report["evidence_status"], "diagnostic_only")
            self.assertEqual(report["evidence_role"], "pointer_only")
            self.assertEqual(report["adoption_boundary"], "not_adoption_evidence")
            self.assertEqual(report["maintenance_note_kind"], "quiet_post_task_diagnostic_candidate")
            self.assertIsNone(report["maintenance_note"])
            self.assertEqual(report["candidate_count"], 0)

    def test_trace_gap_requires_trigger_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            without_evidence = dogfood.build_report(root, changed_paths=["docs/meta-harness-system.md"])
            with_evidence = dogfood.build_report(
                root,
                changed_paths=[
                    "docs/meta-harness-system.md",
                    "backlog/review-2026-06-29-bounded-loop.md",
                ],
            )

            self.assertEqual(without_evidence["candidate_count"], 0)
            self.assertEqual(with_evidence["candidate_count"], 1)
            candidate = with_evidence["candidates"][0]
            self.assertEqual(candidate["candidate_kind"], "trace_candidate")
            self.assertEqual(candidate["status"], "candidate")
            self.assertEqual(candidate["evidence_status"], "diagnostic_only")
            self.assertEqual(candidate["evidence_role"], "pointer_only")
            self.assertEqual(candidate["adoption_boundary"], "not_adoption_evidence")
            self.assertEqual(candidate["trigger_evidence_role"], "pointer_only")
            self.assertIn("reusable_future_value", candidate)
            self.assertIn("backlog/review-2026-06-29-bounded-loop.md", candidate["trigger_evidence"])
            self.assertIsNotNone(with_evidence["maintenance_note"])
            self.assertEqual(with_evidence["maintenance_note"]["candidate_kind"], "trace_candidate")

    def test_changed_evolution_trace_closes_trace_gap_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            report = dogfood.build_report(
                root,
                changed_paths=[
                    "docs/meta-harness-system.md",
                    "backlog/review-2026-06-29-bounded-loop.md",
                    ".harness/traces/evolution/005-bounded-loop.md",
                ],
            )

            self.assertEqual(report["candidate_count"], 0)
            self.assertIsNone(report["maintenance_note"])

    def test_missing_search_set_verify_is_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / ".harness/traces/search-set.md",
                """# Harness Search Set

## Active

### SS-001: Missing verify
- **Source**: test

## Archived
""",
            )

            report = dogfood.build_report(root, changed_paths=[])

            self.assertFalse(dogfood.has_malformed(report))
            self.assertEqual(report["candidate_count"], 0)
            self.assertEqual(report["internal_candidate_count"], 1)
            self.assertEqual(report["suppressed_candidate_count"], 1)
            self.assertIsNone(report["maintenance_note"])

            explicit_report = dogfood.build_report(
                root,
                changed_paths=[],
                surface_mode=dogfood.EXPLICIT_SURFACE,
            )
            self.assertTrue(dogfood.has_malformed(explicit_report))
            self.assertEqual(explicit_report["candidate_count"], 1)
            self.assertEqual(explicit_report["candidates"][0]["candidate_kind"], "search_set_candidate")
            self.assertEqual(explicit_report["candidates"][0]["status"], "malformed")
            self.assertIsNone(explicit_report["maintenance_note"])

    def test_cli_malformed_explicit_report_has_no_maintenance_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(root, "init")
            write(
                root / ".harness/traces/search-set.md",
                """# Harness Search Set

## Active

### SS-001: Missing verify
- **Source**: test

## Archived
""",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(root),
                    "--surface-mode",
                    dogfood.EXPLICIT_SURFACE,
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["candidate_count"], 1)
            self.assertIsNone(report["maintenance_note"])

    def test_stale_search_set_command_is_diagnostic_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / ".harness/traces/search-set.md",
                """# Harness Search Set

## Active

### SS-001: Stale command
- **Source**: test
- **verify**: `python3 scripts/missing-check.py`

## Archived
""",
            )

            report = dogfood.build_report(root, changed_paths=[])

            self.assertFalse(dogfood.has_malformed(report))
            self.assertEqual(report["candidate_count"], 0)
            self.assertEqual(report["internal_candidate_count"], 1)
            self.assertEqual(report["suppressed_candidate_count"], 1)
            self.assertIsNone(report["maintenance_note"])

            explicit_report = dogfood.build_report(
                root,
                changed_paths=[],
                surface_mode=dogfood.EXPLICIT_SURFACE,
            )
            self.assertEqual(explicit_report["candidate_count"], 1)
            self.assertIn("missing path", explicit_report["candidates"][0]["reason"])
            self.assertIsNotNone(explicit_report["maintenance_note"])
            self.assertEqual(explicit_report["maintenance_note"]["candidate_kind"], "search_set_candidate")

    def test_strategy_selection_reports_diagnostic_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            report = dogfood.build_report(
                root,
                changed_paths=[".harness/search-runs/run-001/selections/cand-001-selection.yml"],
            )

            self.assertEqual(report["candidate_count"], 1)
            candidate = report["candidates"][0]
            self.assertEqual(candidate["candidate_kind"], "strategy_search_candidate")
            self.assertIn("diagnostic pointers", candidate["reason"])
            self.assertEqual(candidate["evidence_role"], "pointer_only")
            self.assertIn("reusable_future_value", candidate)

    def test_multiple_internal_candidates_surface_only_one_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            report = dogfood.build_report(
                root,
                changed_paths=[
                    "docs/meta-harness-system.md",
                    "backlog/review-2026-06-29-bounded-loop.md",
                    "experiments/run-001/output.json",
                ],
            )

            self.assertEqual(report["candidate_count"], 2)
            self.assertIsNotNone(report["maintenance_note"])
            self.assertEqual(report["maintenance_note"]["kind"], "quiet_post_task_diagnostic_candidate")
            self.assertEqual(report["maintenance_note"]["candidate_kind"], "trace_candidate")
            self.assertEqual(report["maintenance_note"]["source_candidate_index"], 0)
            self.assertLessEqual(len(report["maintenance_note"]["rendered_note"]), 240)

    def test_candidate_like_signal_without_evidence_has_no_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            report = dogfood.build_report(
                root,
                changed_paths=[
                    "skills/harness-engineer/SKILL.md",
                    "docs/meta-harness-system.md",
                ],
            )

            self.assertEqual(report["candidate_count"], 0)
            self.assertIsNone(report["maintenance_note"])

    def test_report_does_not_use_adoption_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".harness/traces/search-set.md", "# Harness Search Set\n\n## Active\n\n## Archived\n")

            report = dogfood.build_report(
                root,
                changed_paths=[
                    "scripts/check-harness-dogfood.py",
                    "backlog/review-2026-06-29-bounded-loop.md",
                ],
            )
            encoded = str(report).lower()

            for forbidden in (
                "pass",
                "adopted",
                "required",
                "gate",
                "blocked",
                "learned",
                "fixed the harness",
                "recorded",
                "promoted",
                "search-set updated",
            ):
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, encoded)
            self.assertIn("diagnostic_only", encoded)
            self.assertIn("pointer_only", encoded)

    def test_rendered_notes_do_not_use_stable_claim_words(self) -> None:
        forbidden = (
            "pass",
            "adopted",
            "required",
            "gate",
            "blocked",
            "learned",
            "fixed the harness",
            "recorded",
            "promoted",
            "search-set updated",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / ".harness/traces/search-set.md",
                """# Harness Search Set

## Active

### SS-001: Stale command
- **Source**: test
- **verify**: `python3 scripts/missing-check.py`

## Archived
""",
            )
            scenarios = [
                dogfood.build_report(
                    root,
                    changed_paths=[
                        "docs/meta-harness-system.md",
                        ".harness/traces/failures/001-example.md",
                    ],
                ),
                dogfood.build_report(
                    root,
                    changed_paths=["experiments/run-001/output.json"],
                ),
                dogfood.build_report(
                    root,
                    changed_paths=[".harness/search-runs/run-001/selections/cand-001-selection.yml"],
                ),
                dogfood.build_report(
                    root,
                    changed_paths=[],
                    surface_mode=dogfood.EXPLICIT_SURFACE,
                ),
            ]

            for report in scenarios:
                note = report["maintenance_note"]
                self.assertIsNotNone(note)
                rendered = note["rendered_note"].lower()
                for word in forbidden:
                    with self.subTest(candidate=note["candidate_kind"], forbidden=word):
                        self.assertNotIn(word, rendered)

    def test_git_changed_paths_parses_rename_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(root, "init")
            run_git(root, "config", "user.email", "test@example.com")
            run_git(root, "config", "user.name", "Test User")
            write(root / "plain.txt", "plain\n")
            run_git(root, "add", "plain.txt")
            run_git(root, "commit", "-m", "initial")
            (root / "docs").mkdir()
            run_git(root, "mv", "plain.txt", "docs/meta-harness-system.md")

            paths = dogfood.git_changed_paths(root)

            self.assertIn("docs/meta-harness-system.md", paths)
            self.assertNotIn("plain.txt -> docs/meta-harness-system.md", paths)

    def test_git_changed_paths_parses_rename_out_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_git(root, "init")
            run_git(root, "config", "user.email", "test@example.com")
            run_git(root, "config", "user.name", "Test User")
            write(root / "docs/meta-harness-system.md", "doc\n")
            run_git(root, "add", "docs/meta-harness-system.md")
            run_git(root, "commit", "-m", "initial")
            run_git(root, "mv", "docs/meta-harness-system.md", "plain.txt")

            paths = dogfood.git_changed_paths(root)

            self.assertIn("plain.txt", paths)
            self.assertNotIn("docs/meta-harness-system.md -> plain.txt", paths)

    def test_porcelain_parser_keeps_copy_and_rename_destinations(self) -> None:
        paths = dogfood.parse_porcelain_changed_paths(
            b"C  docs/copied.md\0README.md\0R  docs/renamed.md\0old.md\0"
        )

        self.assertEqual(paths, ["docs/copied.md", "docs/renamed.md"])


if __name__ == "__main__":
    unittest.main()
