#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "adapters" / "claude" / "scripts" / "check-claude-profile-drift.py"


spec = importlib.util.spec_from_file_location("check_claude_profile_drift", SCRIPT)
assert spec and spec.loader
check_claude_profile_drift = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_claude_profile_drift
spec.loader.exec_module(check_claude_profile_drift)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ClaudeProfileDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.claude_home = self.root / ".claude"
        self.write_profile(
            settings={
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit|Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "bash .claude/hooks/typecheck.sh",
                                }
                            ],
                        }
                    ]
                }
            },
            hook_contracts=[
                {
                    "event": "PostToolUse",
                    "command_contains": [".claude/hooks/typecheck.sh"],
                    "declared_in": "rules/common/hooks.md",
                }
            ],
            blocked_model_ids=["claude-3-opus"],
        )

    def manifest(self, **overrides) -> dict:
        data = {
            "schema_version": "claude-profile-governance/v1",
            "settings_paths": ["settings.json"],
            "rules": [
                {
                    "path": "rules/common/harness-methodology.md",
                    "canonical_source": "harness/canonical/harness-methodology.md",
                }
            ],
            "hook_contracts": [],
            "blocked_model_ids": [],
            "scan_paths": ["settings.json", "rules"],
        }
        data.update(overrides)
        return data

    def write_profile(
        self,
        *,
        settings: dict | None = None,
        hook_contracts: list[dict] | None = None,
        blocked_model_ids: list[str] | None = None,
    ) -> None:
        canonical = "# Harness Methodology\n\nUse trace-backed changes.\n"
        write(self.claude_home / "harness/canonical/harness-methodology.md", canonical)
        write(self.claude_home / "rules/common/harness-methodology.md", canonical)
        write(
            self.claude_home / "rules/common/hooks.md",
            "PostToolUse runs bash .claude/hooks/typecheck.sh after edits.\n",
        )
        if settings is not None:
            write(self.claude_home / "settings.json", json.dumps(settings, indent=2))
        manifest = self.manifest(
            hook_contracts=hook_contracts or [],
            blocked_model_ids=blocked_model_ids or [],
        )
        write(self.claude_home / "harness/profile-governance.json", json.dumps(manifest, indent=2))

    def validate(self) -> list[str]:
        manifest = check_claude_profile_drift.load_json(
            self.claude_home / "harness/profile-governance.json"
        )
        return check_claude_profile_drift.validate_manifest(
            manifest,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

    def test_valid_profile_passes(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_detects_canonical_rule_drift(self) -> None:
        write(self.claude_home / "rules/common/harness-methodology.md", "edited by hand\n")

        errors = self.validate()

        self.assertTrue(any("drifted from canonical_source" in error for error in errors))

    def test_detects_missing_hook_command(self) -> None:
        write(
            self.claude_home / "settings.json",
            json.dumps({"hooks": {"PostToolUse": [{"hooks": []}]}}, indent=2),
        )

        errors = self.validate()

        self.assertTrue(any("has no command containing" in error for error in errors))

    def test_detects_documented_hook_without_settings_event(self) -> None:
        write(self.claude_home / "settings.json", json.dumps({"hooks": {}}, indent=2))

        errors = self.validate()

        self.assertTrue(any("is not present in configured settings" in error for error in errors))

    def test_detects_stale_model_id_in_governed_profile_files(self) -> None:
        write(
            self.claude_home / "rules/common/testing.md",
            "Use claude-3-opus for hard review.\n",
        )

        errors = self.validate()

        self.assertTrue(any("contains stale model id" in error for error in errors))

    def test_default_template_matches_installed_canonical_layout(self) -> None:
        template = json.loads(
            (ROOT / "adapters/claude/templates/profile-governance.json").read_text(
                encoding="utf-8"
            )
        )
        reference = "# Reference\n"
        write(self.claude_home / "docs/harness-reference.md", reference)
        write(self.claude_home / "harness/canonical/harness-reference.md", reference)
        command = "# Init Harness\n"
        write(self.claude_home / "commands/init-harness.md", command)
        write(self.claude_home / "harness/canonical/commands/init-harness.md", command)
        for skill in ("autoresearch", "harness-engineer", "multi-review"):
            text = f"---\nname: {skill}\n---\n"
            write(self.claude_home / f"skills/{skill}/SKILL.md", text)
            write(self.claude_home / f"harness/canonical/skills/{skill}/SKILL.md", text)

        errors = check_claude_profile_drift.validate_manifest(
            template,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertEqual(errors, [])

    def test_default_template_detects_installed_skill_drift(self) -> None:
        template = json.loads(
            (ROOT / "adapters/claude/templates/profile-governance.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (
            "docs/harness-reference.md",
            "harness/canonical/harness-reference.md",
            "commands/init-harness.md",
            "harness/canonical/commands/init-harness.md",
        ):
            write(self.claude_home / path, "same\n")
        for skill in ("autoresearch", "harness-engineer", "multi-review"):
            write(self.claude_home / f"skills/{skill}/SKILL.md", "same\n")
            write(self.claude_home / f"harness/canonical/skills/{skill}/SKILL.md", "same\n")
        write(self.claude_home / "skills/harness-engineer/SKILL.md", "stale\n")

        errors = check_claude_profile_drift.validate_manifest(
            template,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertTrue(any("skills/harness-engineer/SKILL.md" in error for error in errors))

    def test_rejects_manifest_paths_outside_claude_home(self) -> None:
        manifest = self.manifest(
            settings_paths=["../outside-settings.json"],
            hook_contracts=[
                {
                    "event": "PostToolUse",
                    "command_contains": [".claude/hooks/typecheck.sh"],
                }
            ],
        )

        errors = check_claude_profile_drift.validate_manifest(
            manifest,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertTrue(any("must stay under Claude home" in error for error in errors))

    def test_rejects_repo_canonical_sources_outside_source_root(self) -> None:
        manifest = self.manifest(
            rules=[
                {
                    "path": "rules/common/harness-methodology.md",
                    "canonical_source": "repo:../outside.md",
                }
            ]
        )

        errors = check_claude_profile_drift.validate_manifest(
            manifest,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertTrue(any("must stay under" in error for error in errors))

    def test_hook_contract_requires_command_fragment(self) -> None:
        manifest = self.manifest(hook_contracts=[{"event": "PostToolUse"}])

        errors = check_claude_profile_drift.validate_manifest(
            manifest,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertTrue(any("command_contains must contain" in error for error in errors))

    def test_hook_contract_rejects_empty_command_fragment(self) -> None:
        manifest = self.manifest(
            hook_contracts=[{"event": "PostToolUse", "command_contains": [""]}]
        )

        errors = check_claude_profile_drift.validate_manifest(
            manifest,
            claude_home=self.claude_home,
            source_root=ROOT,
        )

        self.assertTrue(any("entries must be non-empty" in error for error in errors))

    def test_hook_contract_ignores_non_hook_command_metadata(self) -> None:
        write(
            self.claude_home / "settings.json",
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "metadata": {
                                    "command": "bash .claude/hooks/typecheck.sh"
                                },
                                "hooks": [],
                            }
                        ]
                    }
                },
                indent=2,
            ),
        )

        errors = self.validate()

        self.assertTrue(any("is not present in configured settings" in error for error in errors))
        self.assertTrue(any("has no command containing" in error for error in errors))

    def test_cli_reports_json_failures(self) -> None:
        write(self.claude_home / "rules/common/harness-methodology.md", "edited\n")

        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--claude-home",
                str(self.claude_home),
                "--json",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 1)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["status"], "fail")
        self.assertTrue(parsed["errors"])

    def test_cli_relative_manifest_path_is_relative_to_cwd(self) -> None:
        manifest = self.root / "custom-profile-governance.json"
        manifest.write_text(
            json.dumps(
                self.manifest(
                    rules=[
                        {
                            "path": "rules/common/harness-methodology.md",
                            "canonical_source": "harness/canonical/harness-methodology.md",
                        }
                    ]
                )
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--claude-home",
                str(self.claude_home),
                "--manifest",
                manifest.name,
            ],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
