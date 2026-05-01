#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIRROR_SCRIPT = ROOT / "scripts" / "check-compat-mirrors.py"


spec = importlib.util.spec_from_file_location("check_compat_mirrors", MIRROR_SCRIPT)
assert spec and spec.loader
check_compat_mirrors = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_compat_mirrors
spec.loader.exec_module(check_compat_mirrors)


class ClaudeCompatInstallSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_home = self.root / "old-home"
        self.canonical_home = self.root / "canonical-home"

    def tearDown(self):
        self.tmp.cleanup()

    def install_old_mirrors(self, home: Path) -> None:
        claude = home / ".claude"
        (claude / "rules/common").mkdir(parents=True)
        (claude / "docs").mkdir(parents=True)
        (claude / "commands").mkdir(parents=True)
        (claude / "skills").mkdir(parents=True)

        shutil.copy2(ROOT / "docs/methodology.md", claude / "rules/common/harness-methodology.md")
        shutil.copy2(ROOT / "docs/reference.md", claude / "docs/harness-reference.md")
        shutil.copy2(ROOT / "commands/init-harness.md", claude / "commands/init-harness.md")
        for source in (ROOT / "skills").iterdir():
            if source.is_dir():
                shutil.copytree(source, claude / "skills" / source.name)

    def install_canonical_claude(self, home: Path) -> None:
        claude = home / ".claude"
        (claude / "rules/common").mkdir(parents=True)
        (claude / "docs").mkdir(parents=True)
        (claude / "commands").mkdir(parents=True)
        (claude / "skills").mkdir(parents=True)

        shutil.copy2(ROOT / "core/methodology.md", claude / "rules/common/harness-methodology.md")
        shutil.copy2(ROOT / "core/reference.md", claude / "docs/harness-reference.md")
        shutil.copy2(
            ROOT / "adapters/claude/commands/init-harness.md",
            claude / "commands/init-harness.md",
        )
        for source in (ROOT / "adapters/claude/skills").iterdir():
            if source.is_dir():
                shutil.copytree(source, claude / "skills" / source.name)

    def read_installed(self, home: Path, relative: str) -> str:
        return (home / ".claude" / relative).read_text(encoding="utf-8")

    def assert_normalized_doc_matches(
        self,
        *,
        canonical_source: str,
        mirror_source: str,
        installed_relative: str,
    ) -> None:
        canonical = self.read_installed(self.canonical_home, installed_relative)
        mirror = self.read_installed(self.old_home, installed_relative)
        canonical_norm, mirror_norm = check_compat_mirrors.normalize_pair(
            canonical_source,
            mirror_source,
            canonical,
            mirror,
        )
        self.assertEqual(canonical_norm, mirror_norm)

    def test_old_mirror_install_matches_canonical_claude_install(self):
        self.install_old_mirrors(self.old_home)
        self.install_canonical_claude(self.canonical_home)

        expected_files = (
            "rules/common/harness-methodology.md",
            "docs/harness-reference.md",
            "commands/init-harness.md",
            "skills/autoresearch/SKILL.md",
            "skills/harness-engineer/SKILL.md",
            "skills/multi-review/SKILL.md",
        )
        for relative in expected_files:
            self.assertTrue((self.old_home / ".claude" / relative).is_file(), relative)
            self.assertTrue((self.canonical_home / ".claude" / relative).is_file(), relative)

        self.assert_normalized_doc_matches(
            canonical_source="core/methodology.md",
            mirror_source="docs/methodology.md",
            installed_relative="rules/common/harness-methodology.md",
        )
        self.assert_normalized_doc_matches(
            canonical_source="core/reference.md",
            mirror_source="docs/reference.md",
            installed_relative="docs/harness-reference.md",
        )

        normalized_match_files = (
            (
                "adapters/claude/commands/init-harness.md",
                "commands/init-harness.md",
                "commands/init-harness.md",
            ),
            (
                "adapters/claude/skills/autoresearch/SKILL.md",
                "skills/autoresearch/SKILL.md",
                "skills/autoresearch/SKILL.md",
            ),
            (
                "adapters/claude/skills/harness-engineer/SKILL.md",
                "skills/harness-engineer/SKILL.md",
                "skills/harness-engineer/SKILL.md",
            ),
            (
                "adapters/claude/skills/multi-review/SKILL.md",
                "skills/multi-review/SKILL.md",
                "skills/multi-review/SKILL.md",
            ),
        )
        for canonical_source, mirror_source, relative in normalized_match_files:
            canonical_norm, mirror_norm = check_compat_mirrors.normalize_pair(
                canonical_source,
                mirror_source,
                self.read_installed(self.canonical_home, relative),
                self.read_installed(self.old_home, relative),
            )
            self.assertEqual(canonical_norm, mirror_norm, relative)


if __name__ == "__main__":
    unittest.main()
