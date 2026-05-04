#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PreCommitHookTests(unittest.TestCase):
    def test_standard_verification_runs_codex_marketplace_metadata_checker(self):
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-codex-marketplace-metadata.py", text)
        self.assertIn("Codex marketplace metadata readiness check passes", text)

    def test_hook_runs_maintenance_review_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-maintenance-review.py", text)

    def test_hook_runs_staged_search_set_evidence_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-search-set-evidence.py --staged", text)

    def test_hook_runs_staged_backlog_archive_lifecycle_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-backlog-archive-lifecycle.py --staged", text)

    def test_hook_runs_codex_marketplace_metadata_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-codex-marketplace-metadata.py", text)

    def test_readme_pre_commit_docs_name_marketplace_metadata_checker(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-codex-marketplace-metadata.py", text)
        self.assertIn("marketplace metadata readiness", text)

    def test_readme_pre_commit_docs_name_staged_archive_lifecycle_checker(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-backlog-archive-lifecycle.py --staged", text)
        self.assertIn("completed backlog archive pointers", text)

    def test_standard_verification_runs_codex_activation_smoke(self):
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("python3 adapters/codex/scripts/smoke-local-plugin-activation.py", text)
        self.assertIn("heavier Codex local plugin activation smoke", normalized)
        self.assertIn("Codex local plugin activation smoke test passes", text)
        self.assertIn("isolated CLI\n  marketplace registration and enabled-plugin config shape", text)
        self.assertIn("not running Codex\n  Desktop skill surfacing or plugin tool-event delivery", text)

    def test_root_readme_says_codex_activation_smoke_is_implemented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 adapters/codex/scripts/smoke-local-plugin-activation.py", text)
        self.assertIn("The activation smoke creates an isolated `CODEX_HOME`", text)
        self.assertIn("does not prove a running Codex Desktop session has surfaced those skills", text)
        self.assertIn("part of Standard verification rather than pre-commit", text)
        self.assertNotIn("pending an activation smoke test", text)

    def test_root_readme_distinguishes_quick_hook_from_release_gate(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())

        self.assertIn("quick pre-commit-adjacent check", normalized)
        self.assertIn("sh .githooks/pre-commit", text)
        self.assertIn("stable handoff or release-like local verification", normalized)
        self.assertIn("python3 scripts/verify-release.py", text)
        self.assertIn("python3 scripts/verify-release.py --skip-clean-worktree", text)
        self.assertIn("runs the Standard verification set plus this repository's Active search-set", normalized)
        self.assertIn("clean-worktree gate", normalized)
        self.assertIn("During an in-progress maintenance diff", normalized)


if __name__ == "__main__":
    unittest.main()
