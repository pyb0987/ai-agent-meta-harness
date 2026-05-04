#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import contextlib
import io
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-maintenance-review.py"

spec = importlib.util.spec_from_file_location("check_maintenance_review", SCRIPT)
assert spec and spec.loader
check_maintenance_review = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_maintenance_review
spec.loader.exec_module(check_maintenance_review)


def summary(multi_review: str) -> str:
    return f"""# Review

## Follow-Up Iteration: Example

Multi-review:
{multi_review}
"""


def fallback_threshold_review(*, disposition: str | None = None) -> str:
    disposition_line = f"- Fallback-threshold disposition: {disposition}\n" if disposition else ""
    return "\n".join(
        summary(
            f"""- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT for this durable-contract check. Follow-up/residual risk: accepted.
{disposition_line}- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
        )
        for _ in range(check_maintenance_review.FALLBACK_ACTION_SECTION_THRESHOLD)
    )


VALID_REVIEW = summary(
    """- Test scope critic: score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is intentionally narrow. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
)

INVALID_LOW_SCORE_REVIEW = summary(
    """- Test scope critic: score 8, PASS. Blocking findings: none. No VETO triggered.
- Score handling: all critic scores were treated as accepted.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none recorded.
- Final acceptance: accepted for this follow-up iteration.
"""
)


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


class CheckMaintenanceReviewTests(unittest.TestCase):
    def test_accepts_score_9_review_summary(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is intentionally narrow. Follow-up/residual risk: accepted for this test-only review.
- Release-gate critic: score 9, PASS. Blocking findings: none. Why not 10: no release-like diff was present. No backlog item added because this is test fixture scope.
- Score handling: all required critics scored at least 9, so no VETO iteration was needed. Every score 9 records why not 10 and either backlog follow-up or residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_rejects_score_8_pass_without_veto_handling(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, PASS. Blocking findings: none.
- Score handling: all critic scores were treated as accepted.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none recorded.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score below 9" in error for error in errors))

    def test_rejects_score_8_pass_with_negated_veto_language(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, PASS. Blocking findings: none. No VETO triggered.
- Score handling: all critic scores were treated as accepted.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none recorded.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score below 9" in error for error in errors))

    def test_rejects_score_8_veto_without_rerun_or_not_accepted(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, VETO triggered. Blocking findings: missing checker coverage.
- Score handling: score 8 triggered VETO recovery.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none recorded.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score below 9" in error for error in errors))

    def test_accepts_score_8_veto_with_successful_rerun(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, VETO triggered. Blocking findings: missing checker coverage.
- Re-review: test scope critic score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is intentionally narrow. Follow-up/residual risk: accepted.
- Score handling: score 8 triggered VETO recovery; affected critic rerun reached score 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: affected critic rerun after fixes; final score 9.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_rejects_score_8_veto_with_only_unrelated_successful_rerun(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, VETO triggered. Blocking findings: missing checker coverage.
- Re-review: release-gate critic score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is intentionally narrow. Follow-up/residual risk: accepted.
- Score handling: score 8 triggered VETO recovery; a different critic rerun reached score 9.
- Rerun status: release-gate critic rerun after fixes; final score 9.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score below 9" in error for error in errors))

    def test_accepts_score_8_not_accepted_without_rerun(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 8, VETO. Blocking findings: missing checker coverage. Not accepted.
- Score handling: score 8 triggered VETO; work is not accepted.
- Rerun status: no rerun was performed because the item is not accepted.
- Follow-up/residual risk: blocking finding remains.
- Final acceptance: not accepted.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_rejects_pending_review_status(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: pending critic rerun after fixes.
- Follow-up/residual risk: rerun is still pending.
- Final acceptance: accepted after rerun.
"""
            )
        )

        self.assertTrue(any("unresolved review status" in error for error in errors))

    def test_rejects_missing_required_fields(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("follow-up/residual risk" in error for error in errors))
        self.assertTrue(any("rerun status" in error for error in errors))

    def test_rejects_required_words_outside_review_block(self):
        text = """# Review

## Follow-Up Iteration: Example

Change:

- Added prose that says score 9, score 8, VETO, Blocking findings: none,
  Score handling:, Rerun status:, Follow-up/residual risk:, and Final acceptance:.

Multi-review:

- Test scope critic: score 9, PASS.
"""

        errors = check_maintenance_review.validate_text(text)

        self.assertTrue(any("score record lacks blocking findings" in error for error in errors))
        self.assertTrue(any("follow-up/residual risk" in error for error in errors))

    def test_rejects_score_record_without_scope(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("critic scope" in error for error in errors))

    def test_rejects_score_record_without_blocking_findings(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS.
- Release-gate critic: score 9, PASS. Blocking findings: none. Why not 10: fixture scope only. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score record lacks blocking findings" in error for error in errors))

    def test_rejects_score_9_without_why_not_10(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score 9 lacks why-not-10 handling" in error for error in errors))

    def test_rejects_score_9_without_disposition(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none. Why not 10: fixture coverage is narrow.
- Score handling: all required critics scored at least 9.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: none.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertTrue(any("score 9 lacks backlog/residual-risk disposition" in error for error in errors))

    def test_accepts_section_level_score_9_handling(self):
        errors = check_maintenance_review.validate_text(
            summary(
                """- Test scope critic: score 9, PASS. Blocking findings: none.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10; the only score 9 produced no backlog item and is accepted as residual risk.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
        )

        self.assertEqual(errors, [])

    def test_ignores_inline_review_outcome_text(self):
        text = """# Backlog

## Candidate

Potential improvement:

- Fix existing embedded `Review outcome:` sections when this item is selected.
"""

        self.assertEqual(check_maintenance_review.validate_text(text), [])

    def test_default_paths_include_backlog_ownership_files(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backlog = root / "backlog"
            backlog.mkdir()
            review = backlog / "review-example.md"
            core = backlog / "core.md"
            claude = backlog / "claude-adapter.md"
            codex = backlog / "codex-adapter.md"
            archive = backlog / "archive"
            archive.mkdir()
            archive_core = archive / "core.md"
            archive_claude = archive / "claude-adapter.md"
            archive_codex = archive / "codex-adapter.md"
            for path in (review, core, claude, codex, archive_core, archive_claude, archive_codex):
                path.write_text("", encoding="utf-8")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)

            paths = {path.relative_to(root).as_posix() for path in check_maintenance_review.default_paths()}

        self.assertEqual(
            paths,
            {
                "backlog/review-example.md",
                "backlog/core.md",
                "backlog/claude-adapter.md",
                "backlog/codex-adapter.md",
                "backlog/archive/core.md",
                "backlog/archive/claude-adapter.md",
                "backlog/archive/codex-adapter.md",
            },
        )

    def test_default_git_validation_reads_staged_content(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            backlog = root / "backlog"
            backlog.mkdir()
            core = backlog / "core.md"
            claude = backlog / "claude-adapter.md"
            codex = backlog / "codex-adapter.md"
            archive = backlog / "archive"
            archive.mkdir()
            archive_core = archive / "core.md"
            archive_claude = archive / "claude-adapter.md"
            archive_codex = archive / "codex-adapter.md"
            core.write_text(INVALID_LOW_SCORE_REVIEW, encoding="utf-8")
            claude.write_text("", encoding="utf-8")
            codex.write_text("", encoding="utf-8")
            archive_core.write_text(VALID_REVIEW, encoding="utf-8")
            archive_claude.write_text("", encoding="utf-8")
            archive_codex.write_text("", encoding="utf-8")
            git(
                root,
                "add",
                "backlog/core.md",
                "backlog/claude-adapter.md",
                "backlog/codex-adapter.md",
                "backlog/archive/core.md",
                "backlog/archive/claude-adapter.md",
                "backlog/archive/codex-adapter.md",
            )
            core.write_text(VALID_REVIEW, encoding="utf-8")
            archive_core.write_text("", encoding="utf-8")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)

            index_errors = check_maintenance_review.validate_default_paths(use_index=True)
            worktree_errors = check_maintenance_review.validate_paths([core, archive_core])

        self.assertTrue(any("score below 9" in error for error in index_errors))
        self.assertEqual(worktree_errors, [])

    def test_index_default_paths_include_staged_archive_files(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            archive = root / "backlog" / "archive"
            archive.mkdir(parents=True)
            archive_core = archive / "core.md"
            archive_core.write_text(VALID_REVIEW, encoding="utf-8")
            git(root, "add", "backlog/archive/core.md")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)

            paths = {
                path.relative_to(root).as_posix()
                for path in check_maintenance_review.default_paths(use_index=True)
            }
            errors = check_maintenance_review.validate_default_paths(use_index=True)

        self.assertEqual(paths, {"backlog/archive/core.md"})
        self.assertEqual(errors, [])

    def test_index_default_paths_include_staged_review_files(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            review = root / "backlog" / "review-example.md"
            review.parent.mkdir()
            review.write_text("", encoding="utf-8")
            git(root, "add", "backlog/review-example.md")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)

            paths = {path.relative_to(root).as_posix() for path in check_maintenance_review.default_paths(use_index=True)}

        self.assertEqual(paths, {"backlog/review-example.md"})

    def test_default_git_mode_ignores_historical_threshold_disposition(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test User")
            archive = root / "backlog" / "archive"
            archive.mkdir(parents=True)
            archive_core = archive / "core.md"
            archive_core.write_text(
                fallback_threshold_review(
                    disposition="accepted residual risk because this is a historical record"
                ),
                encoding="utf-8",
            )
            git(root, "add", "backlog/archive/core.md")
            git(root, "commit", "-m", "historical disposition")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("Record maintainer disposition", stdout.getvalue())
        self.assertNotIn("disposition recorded", stdout.getvalue())

    def test_default_git_mode_counts_clean_handoff_disposition(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test User")
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            for path in (
                backlog / "core.md",
                backlog / "claude-adapter.md",
                backlog / "codex-adapter.md",
                archive / "claude-adapter.md",
                archive / "codex-adapter.md",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            (archive / "core.md").write_text(fallback_threshold_review(), encoding="utf-8")
            (root / "MAINTENANCE.md").write_text(
                "- Fallback-threshold disposition: accepted residual risk because "
                "this clean handoff has independent review discipline.\n",
                encoding="utf-8",
            )
            git(root, "add", "MAINTENANCE.md", "backlog")
            git(root, "commit", "-m", "clean handoff disposition")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("disposition recorded", stdout.getvalue())
        self.assertNotIn("Record maintainer disposition", stdout.getvalue())

    def test_default_git_mode_does_not_use_clean_handoff_disposition_for_staged_work(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test User")
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            for path in (
                backlog / "core.md",
                backlog / "claude-adapter.md",
                backlog / "codex-adapter.md",
                archive / "claude-adapter.md",
                archive / "codex-adapter.md",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            (archive / "core.md").write_text(fallback_threshold_review(), encoding="utf-8")
            (root / "MAINTENANCE.md").write_text(
                "- Fallback-threshold disposition: accepted residual risk because "
                "this clean handoff has independent review discipline.\n",
                encoding="utf-8",
            )
            script = root / "scripts" / "example.py"
            script.parent.mkdir()
            script.write_text("print('old')\n", encoding="utf-8")
            git(root, "add", "MAINTENANCE.md", "backlog", "scripts/example.py")
            git(root, "commit", "-m", "clean handoff disposition")
            script.write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/example.py")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("Record maintainer disposition", stdout.getvalue())
        self.assertNotIn("disposition recorded", stdout.getvalue())

    def test_default_git_mode_counts_staged_threshold_disposition(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            git(root, "config", "user.email", "test@example.com")
            git(root, "config", "user.name", "Test User")
            backlog = root / "backlog"
            archive = backlog / "archive"
            archive.mkdir(parents=True)
            core = backlog / "core.md"
            archive_core = archive / "core.md"
            core.write_text("", encoding="utf-8")
            archive_core.write_text(fallback_threshold_review(), encoding="utf-8")
            git(root, "add", "backlog/core.md", "backlog/archive/core.md")
            git(root, "commit", "-m", "historical fallback")
            core.write_text(
                "- Fallback-threshold disposition: independent re-review because affected critics were rerun independently.\n",
                encoding="utf-8",
            )
            git(root, "add", "backlog/core.md")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("disposition recorded", stdout.getvalue())
        self.assertNotIn("Record maintainer disposition", stdout.getvalue())

    def test_quality_signal_flags_nonindependent_fallback_without_validation_error(self):
        text = summary(
            """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: review used documented sequential fallback rather than independent sub-agent critics. Follow-up/residual risk: accepted as session-surface residual risk.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
        )

        errors = check_maintenance_review.validate_text(text)
        signals = check_maintenance_review.review_quality_signals(text, source="backlog/core.md")

        self.assertEqual(errors, [])
        self.assertEqual(len(signals), 1)
        self.assertIn("sequential fallback", signals[0].fallback_records[0])

    def test_main_prints_fallback_quality_signal_without_failing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            review = Path(tmpdir) / "review.md"
            review.write_text(
                summary(
                    """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT because sub-agents were unavailable. Follow-up/residual risk: accepted as a one-off fallback.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([review.as_posix()])

        self.assertEqual(result, 0)
        self.assertIn("Maintenance review summaries are valid.", stdout.getvalue())
        self.assertIn("Review-quality signal:", stdout.getvalue())
        self.assertIn("not a validation failure", stdout.getvalue())

    def test_main_prints_recorded_threshold_disposition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            review = Path(tmpdir) / "review.md"
            review.write_text(
                "\n".join(
                    summary(
                        """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT for this durable-contract check. Follow-up/residual risk: accepted.
- Fallback-threshold disposition: accepted residual risk because current item used independent critics.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
                    )
                    for _ in range(check_maintenance_review.FALLBACK_ACTION_SECTION_THRESHOLD)
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([review.as_posix()])

        self.assertEqual(result, 0)
        self.assertIn("disposition recorded", stdout.getvalue())
        self.assertNotIn("Record maintainer disposition", stdout.getvalue())

    def test_quality_signal_summary_marks_action_threshold_without_failing(self):
        text = "\n".join(
            summary(
                """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT for this durable-contract check. Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
            )
            for _ in range(check_maintenance_review.FALLBACK_ACTION_SECTION_THRESHOLD)
        )

        errors = check_maintenance_review.validate_text(text)
        signals = check_maintenance_review.review_quality_signals(text, source="backlog/core.md")
        summary_lines = check_maintenance_review.quality_signal_summary(signals)

        self.assertEqual(errors, [])
        self.assertTrue(any("fallback action threshold met" in line for line in summary_lines))

    def test_quality_signal_summary_reports_recorded_threshold_disposition(self):
        for disposition in (
            "accepted residual risk because current item used independent critics",
            "independent re-review because affected critics were rerun independently",
            "follow-up backlog item because repeated fallback needs systemic cleanup",
        ):
            with self.subTest(disposition=disposition):
                text = "\n".join(
                    summary(
                        f"""- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT for this durable-contract check. Follow-up/residual risk: accepted.
- Fallback-threshold disposition: {disposition}
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
                    )
                    for _ in range(check_maintenance_review.FALLBACK_ACTION_SECTION_THRESHOLD)
                )

                signals = check_maintenance_review.review_quality_signals(text, source="backlog/core.md")
                dispositions = check_maintenance_review.fallback_threshold_dispositions(
                    text,
                    source="backlog/core.md",
                )
                summary_lines = check_maintenance_review.quality_signal_summary(
                    signals,
                    dispositions=dispositions,
                )

                self.assertEqual(len(dispositions), check_maintenance_review.FALLBACK_ACTION_SECTION_THRESHOLD)
                self.assertTrue(any("disposition recorded" in line for line in summary_lines))
                self.assertFalse(any("Record maintainer disposition" in line for line in summary_lines))

    def test_empty_threshold_disposition_detail_is_not_counted(self):
        text = summary(
            """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT for this durable-contract check. Follow-up/residual risk: accepted.
- Fallback-threshold disposition: accepted residual risk
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
        )

        dispositions = check_maintenance_review.fallback_threshold_dispositions(text)

        self.assertEqual(dispositions, [])

    def test_quality_signal_summary_keeps_one_off_below_action_threshold(self):
        text = summary(
            """- Governance critic: score 9, PASS. Blocking findings: none. Why not 10: multi-review used FALLBACK_NONINDEPENDENT because sub-agents were unavailable. Follow-up/residual risk: accepted as a one-off fallback.
- Score handling: all required critics scored at least 9. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: no fixes were needed, so no rerun was required.
- Follow-up/residual risk: accepted for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.
"""
        )

        signals = check_maintenance_review.review_quality_signals(text, source="backlog/core.md")
        summary_lines = check_maintenance_review.quality_signal_summary(signals)

        self.assertFalse(any("fallback action threshold met" in line for line in summary_lines))

    def test_missing_multi_review_signal_flags_high_impact_paths(self):
        signal = check_maintenance_review.missing_multi_review_signal(
            ["scripts/check-maintenance-review.py"],
            ["# Core Backlog\n\n### 1. Example\n\nStatus: 진행중\n"],
        )

        self.assertIsNotNone(signal)
        self.assertTrue(
            any(
                "lack a recorded Multi-review" in line
                for line in check_maintenance_review.missing_multi_review_summary(signal)
            )
        )

    def test_missing_multi_review_signal_accepts_not_required_reason(self):
        signal = check_maintenance_review.missing_multi_review_signal(
            ["scripts/check-maintenance-review.py"],
            ["# Core Backlog\n\nMulti-review not required: generated typo-only cleanup.\n"],
        )

        self.assertIsNone(signal)

    def test_missing_multi_review_signal_ignores_low_impact_backlog_only_paths(self):
        signal = check_maintenance_review.missing_multi_review_signal(
            ["backlog/core.md"],
            ["# Core Backlog\n\n### 1. Example\n\nStatus: 진행중\n"],
        )

        self.assertIsNone(signal)

    def test_main_prints_missing_multi_review_signal_for_staged_high_impact_change(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            scripts = root / "scripts"
            backlog = root / "backlog"
            archive = backlog / "archive"
            scripts.mkdir()
            archive.mkdir(parents=True)
            (scripts / "example.py").write_text("print('hi')\n", encoding="utf-8")
            (backlog / "core.md").write_text(
                "# Core Backlog\n\n### 1. Example\n\nStatus: 진행중\n",
                encoding="utf-8",
            )
            for name in ("claude-adapter.md", "codex-adapter.md"):
                (backlog / name).write_text(f"# {name}\n", encoding="utf-8")
                (archive / name).write_text(f"# {name} Archive\n", encoding="utf-8")
            (archive / "core.md").write_text("# Core Backlog Archive\n", encoding="utf-8")
            git(root, "add", "scripts/example.py", "backlog")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("high-impact changed path", stdout.getvalue())

    def test_staged_missing_multi_review_signal_ignores_historical_archive_markers(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            scripts = root / "scripts"
            backlog = root / "backlog"
            archive = backlog / "archive"
            scripts.mkdir()
            archive.mkdir(parents=True)
            (scripts / "example.py").write_text("print('hi')\n", encoding="utf-8")
            (backlog / "core.md").write_text(
                "# Core Backlog\n",
                encoding="utf-8",
            )
            for name in ("claude-adapter.md", "codex-adapter.md"):
                (backlog / name).write_text(f"# {name}\n", encoding="utf-8")
                (archive / name).write_text(f"# {name} Archive\n", encoding="utf-8")
            (archive / "core.md").write_text(VALID_REVIEW, encoding="utf-8")
            git(root, "add", "scripts/example.py", "backlog")
            git(root, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "initial")
            (scripts / "example.py").write_text("print('changed')\n", encoding="utf-8")
            (backlog / "core.md").write_text(
                "# Core Backlog\n\n### 1. Example\n\nStatus: 진행중\n",
                encoding="utf-8",
            )
            git(root, "add", "scripts/example.py", "backlog/core.md")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertIn("high-impact changed path", stdout.getvalue())

    def test_staged_missing_multi_review_signal_accepts_changed_not_required_record(self):
        original_root = check_maintenance_review.ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init")
            scripts = root / "scripts"
            backlog = root / "backlog"
            archive = backlog / "archive"
            scripts.mkdir()
            archive.mkdir(parents=True)
            (scripts / "example.py").write_text("print('hi')\n", encoding="utf-8")
            (backlog / "core.md").write_text(
                "# Core Backlog\n",
                encoding="utf-8",
            )
            for name in ("claude-adapter.md", "codex-adapter.md"):
                (backlog / name).write_text(f"# {name}\n", encoding="utf-8")
                (archive / name).write_text(f"# {name} Archive\n", encoding="utf-8")
            (archive / "core.md").write_text(VALID_REVIEW, encoding="utf-8")
            git(root, "add", "scripts/example.py", "backlog")
            git(root, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "initial")
            (scripts / "example.py").write_text("print('changed')\n", encoding="utf-8")
            (backlog / "core.md").write_text(
                "# Core Backlog\n\nMulti-review not required: script comment-only cleanup.\n",
                encoding="utf-8",
            )
            git(root, "add", "scripts/example.py", "backlog/core.md")

            check_maintenance_review.ROOT = root
            self.addCleanup(setattr, check_maintenance_review, "ROOT", original_root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = check_maintenance_review.main([])

        self.assertEqual(result, 0)
        self.assertNotIn("high-impact changed path", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
