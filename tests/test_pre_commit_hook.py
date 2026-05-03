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

    def test_hook_runs_codex_marketplace_metadata_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-codex-marketplace-metadata.py", text)

    def test_readme_pre_commit_docs_name_marketplace_metadata_checker(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-codex-marketplace-metadata.py", text)
        self.assertIn("marketplace metadata readiness", text)

    def test_standard_verification_runs_codex_activation_smoke(self):
        text = (ROOT / "MAINTENANCE.md").read_text(encoding="utf-8")

        self.assertIn("python3 adapters/codex/scripts/smoke-local-plugin-activation.py", text)
        self.assertIn("heavier Codex local\nplugin activation smoke", text)

    def test_root_readme_says_codex_activation_smoke_is_implemented(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 adapters/codex/scripts/smoke-local-plugin-activation.py", text)
        self.assertIn("The activation smoke creates an isolated `CODEX_HOME`", text)
        self.assertIn("does not prove a running Codex Desktop session has surfaced those skills", text)
        self.assertIn("part of Standard verification rather than pre-commit", text)
        self.assertNotIn("pending an activation smoke test", text)


if __name__ == "__main__":
    unittest.main()
