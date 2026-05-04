#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
INSTALLER = ROOT / "adapters" / "codex" / "scripts" / "install-autoresearch-protection.py"
SOURCE_ROOT = ROOT / "adapters" / "codex"


class InstallAutoresearchProtectionTests(unittest.TestCase):
    def run_installer(self, target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(INSTALLER),
                "--source-root",
                str(SOURCE_ROOT),
                "--target",
                str(target),
                *extra,
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_installs_new_project_bundle_and_smoke_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["git", "init"], cwd=target, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = self.run_installer(target, "--run-smoke")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Protection level: local-only", result.stdout)
            self.assertIn("Autoresearch hook smoke assertions passed.", result.stdout)
            for relative in (
                "scripts/check-autoresearch-protected.py",
                "scripts/smoke-autoresearch-hooks.py",
                ".harness/autoresearch-protected.txt",
                ".codex/hooks.json",
                ".githooks/pre-commit-autoresearch-protected.sh",
                ".githooks/pre-commit",
                ".github/workflows/autoresearch-protected.yml",
                "AGENTS.md",
            ):
                self.assertTrue((target / relative).is_file(), relative)
            self.assertIn("evaluate.py", (target / ".harness/autoresearch-protected.txt").read_text(encoding="utf-8"))
            self.assertIn(
                "pre-commit-autoresearch-protected.sh",
                (target / ".githooks/pre-commit").read_text(encoding="utf-8"),
            )
            hooks_path = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=target,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(hooks_path.stdout.strip(), ".githooks")

    def test_existing_project_files_are_not_silently_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / ".codex").mkdir()
            (target / ".codex/hooks.json").write_text('{"hooks": {}}\n', encoding="utf-8")
            (target / ".github/workflows").mkdir(parents=True)
            workflow = target / ".github/workflows/autoresearch-protected.yml"
            workflow.write_text("name: existing\n", encoding="utf-8")
            (target / ".githooks").mkdir()
            pre_commit = target / ".githooks/pre-commit"
            pre_commit.write_text("#!/bin/sh\necho existing\n", encoding="utf-8")
            agents = target / "AGENTS.md"
            agents.write_text("# Existing\n", encoding="utf-8")
            (target / ".harness").mkdir()
            protected = target / ".harness/autoresearch-protected.txt"
            protected.write_text("custom-evaluator.py\n", encoding="utf-8")

            result = self.run_installer(target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("merge-required: .codex/hooks.json", result.stdout)
            self.assertIn("merge-required: .github/workflows/autoresearch-protected.yml", result.stdout)
            self.assertIn("Protection level: incomplete", result.stdout)
            self.assertEqual('{"hooks": {}}\n', (target / ".codex/hooks.json").read_text(encoding="utf-8"))
            self.assertEqual("name: existing\n", workflow.read_text(encoding="utf-8"))
            self.assertEqual("custom-evaluator.py\n", protected.read_text(encoding="utf-8"))
            self.assertIn("echo existing", pre_commit.read_text(encoding="utf-8"))
            self.assertIn("pre-commit-autoresearch-protected.sh", pre_commit.read_text(encoding="utf-8"))
            self.assertIn("## Autoresearch Protection", agents.read_text(encoding="utf-8"))
            self.assertNotIn("Protection level: template-installed", result.stdout)

    def test_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = self.run_installer(target, "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Smoke commands:", result.stdout)
            self.assertFalse((target / "scripts/check-autoresearch-protected.py").exists())

    def test_non_git_project_reports_manual_hook_activation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = self.run_installer(target, "--run-smoke")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("manual-step: .githooks/pre-commit", result.stdout)
            self.assertIn("Protection level: incomplete", result.stdout)
            self.assertNotIn("Protection level: local-only", result.stdout)

    def test_existing_hooks_path_requires_reviewed_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            subprocess.run(["git", "init"], cwd=target, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(
                ["git", "config", "core.hooksPath", ".custom-hooks"],
                cwd=target,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = self.run_installer(target)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("merge-required: .githooks/pre-commit", result.stdout)
            hooks_path = subprocess.run(
                ["git", "config", "--get", "core.hooksPath"],
                cwd=target,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(hooks_path.stdout.strip(), ".custom-hooks")


if __name__ == "__main__":
    unittest.main()
