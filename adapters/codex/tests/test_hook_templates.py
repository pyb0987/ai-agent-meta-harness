#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[3]
HOOKS = ROOT / "adapters" / "codex" / "templates" / "hooks"
AUTORESEARCH_SKILL = ROOT / "adapters" / "codex" / "skills" / "autoresearch" / "SKILL.md"


class HookTemplateTests(unittest.TestCase):
    def test_codex_hooks_template_uses_shared_checker(self):
        template = json.loads((HOOKS / "codex-hooks.json.template").read_text(encoding="utf-8"))
        hooks = template["hooks"]
        self.assertEqual(set(hooks), {"PreToolUse", "PermissionRequest"})
        pre_tool = hooks["PreToolUse"][0]["hooks"][0]
        permission = hooks["PermissionRequest"][0]["hooks"][0]
        self.assertEqual(pre_tool["type"], "command")
        self.assertEqual(permission["type"], "command")
        self.assertEqual(pre_tool["timeout"], 5)
        self.assertEqual(permission["timeout"], 5)
        self.assertIn("check-autoresearch-protected.py", pre_tool["command"])
        self.assertIn("--codex-pre-tool-use", pre_tool["command"])
        self.assertIn("check-autoresearch-protected.py", permission["command"])
        self.assertIn("--codex-permission-request", permission["command"])

    def test_codex_hooks_template_pins_short_checker_timeouts(self):
        template = json.loads((HOOKS / "codex-hooks.json.template").read_text(encoding="utf-8"))

        for hook_name in ("PreToolUse", "PermissionRequest"):
            with self.subTest(hook_name=hook_name):
                command_hook = template["hooks"][hook_name][0]["hooks"][0]
                self.assertIn("timeout", command_hook)
                self.assertIsInstance(command_hook["timeout"], int)
                self.assertGreaterEqual(command_hook["timeout"], 3)
                self.assertLessEqual(command_hook["timeout"], 10)

    def test_autoresearch_skill_embedded_hooks_example_pins_short_checker_timeouts(self):
        text = AUTORESEARCH_SKILL.read_text(encoding="utf-8")
        for command in ("--codex-pre-tool-use", "--codex-permission-request"):
            marker = (
                f'"command": "python3 \\"$(git rev-parse --show-toplevel)/scripts/'
                f'check-autoresearch-protected.py\\" {command}",\n'
                '            "timeout": 5,'
            )
            with self.subTest(command=command):
                self.assertIn(marker, text)

    def test_codex_hooks_template_is_template_only(self):
        template_text = (HOOKS / "codex-hooks.json.template").read_text(encoding="utf-8")
        self.assertNotIn('"hooks": "./hooks', template_text)
        self.assertIn("PreToolUse", template_text)
        self.assertIn("PermissionRequest", template_text)

    def test_pre_commit_template_uses_pre_commit_mode(self):
        text = (HOOKS / "pre-commit-autoresearch-protected.sh").read_text(encoding="utf-8")
        self.assertIn("check-autoresearch-protected.py --pre-commit", text)
        self.assertIn("set -eu", text)

    def test_github_actions_template_uses_ci_mode_and_fetch_depth_zero(self):
        text = (HOOKS / "github-actions-autoresearch-protected.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("pull_request", text)
        self.assertNotIn("push:", text)
        self.assertIn("BASE_REF", text)
        self.assertIn("github.base_ref", text)
        self.assertIn("check-autoresearch-protected.py --ci", text)

    def test_agents_snippet_names_protection_command(self):
        text = (HOOKS / "agents-autoresearch-protection.md").read_text(encoding="utf-8")
        self.assertIn(".harness/autoresearch-protected.txt", text)
        self.assertIn("check-autoresearch-protected.py --pre-commit", text)
        self.assertIn("best_score.txt", text)

    def run_smoke_with_fake_checker(self, checker_source: str):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            scripts = cwd / "scripts"
            protected_dir = cwd / ".harness"
            scripts.mkdir()
            protected_dir.mkdir()
            checker = scripts / "fake-checker.py"
            checker.write_text(textwrap.dedent(checker_source), encoding="utf-8")
            protected = protected_dir / "autoresearch-protected.txt"
            protected.write_text("evaluate.py\n", encoding="utf-8")
            return subprocess.run(
                [
                    "python3",
                    str(ROOT / "adapters" / "codex" / "scripts" / "smoke-autoresearch-hooks.py"),
                    "--checker",
                    str(checker),
                    "--protected-file",
                    str(protected),
                ],
                cwd=cwd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_smoke_script_rejects_legacy_top_level_decision(self):
        result = self.run_smoke_with_fake_checker(
            'import json\nprint(json.dumps({"decision": "block"}))\n'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("legacy top-level decision", result.stderr)

    def test_smoke_script_rejects_invalid_json(self):
        result = self.run_smoke_with_fake_checker('print("not json")\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)

    def test_smoke_script_rejects_missing_output(self):
        result = self.run_smoke_with_fake_checker('')
        self.assertEqual(result.returncode, 1)
        self.assertIn("produced no blocking JSON", result.stderr)

    def test_smoke_script_rejects_malformed_hook_specific_keys(self):
        result = self.run_smoke_with_fake_checker(
            'import json\nprint(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny"}}))\n'
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("hookSpecificOutput keys differ", result.stderr)

    def test_plugin_manifest_does_not_expose_runtime_hooks(self):
        manifest = json.loads((ROOT / "adapters" / "codex" / "plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("hooks", manifest)
        self.assertEqual(manifest["skills"], "./skills/")

    def test_plugin_scope_gates_runtime_hooks_on_tool_event_delivery(self):
        text = (ROOT / "adapters" / "codex" / "plugin-scope.md").read_text(encoding="utf-8")
        for marker in (
            "Only after isolated local activation and Codex plugin tool-event delivery smoke tests pass",
            "smoke-tested through both the isolated local plugin activation path and a Codex\nplugin tool-event delivery path",
            "Template-only files under `templates/hooks/`\nshould not be advertised as active runtime hooks",
        ):
            self.assertIn(marker, text)

    def test_plugin_scope_lists_activation_smoke_generated_surface(self):
        canonical = (ROOT / "adapters" / "codex" / "plugin-scope.md").read_text(encoding="utf-8")
        generated = (ROOT / "plugins" / "ai-agent-meta-harness" / "plugin-scope.md").read_text(encoding="utf-8")

        for text in (canonical, generated):
            with self.subTest(path="plugin-scope"):
                self.assertIn("- `scripts/smoke-local-plugin-activation.py`", text)
                self.assertIn("- `scripts/check-codex-cli-surface.py`", text)
                self.assertIn("- `scripts/smoke-init-codex-project-fixtures.py`", text)
                self.assertIn(
                    "| Local plugin activation smoke test | `adapters/codex/scripts/smoke-local-plugin-activation.py` | `scripts/smoke-local-plugin-activation.py` |",
                    text,
                )
                self.assertIn(
                    "| Optional Codex CLI surface probe | `adapters/codex/scripts/check-codex-cli-surface.py` | `scripts/check-codex-cli-surface.py` |",
                    text,
                )
                self.assertIn(
                    "| Init project fixture smoke test | `adapters/codex/scripts/smoke-init-codex-project-fixtures.py` | `scripts/smoke-init-codex-project-fixtures.py` |",
                    text,
                )
                self.assertIn("Deterministic artifact/adoption check that runs generated Active search-set verifiers in fixture projects", text)
                self.assertIn("does not prove live Codex model dogfooding", text)
                self.assertIn("does not prove Desktop model-visible skill surfacing or plugin tool-event delivery", text)
        self.assertEqual(canonical, generated)

    def test_plugin_scope_lists_init_skill_bundled_agents_asset(self):
        canonical = (ROOT / "adapters" / "codex" / "plugin-scope.md").read_text(encoding="utf-8")
        generated = (ROOT / "plugins" / "ai-agent-meta-harness" / "plugin-scope.md").read_text(encoding="utf-8")

        for text in (canonical, generated):
            with self.subTest(path="plugin-scope"):
                self.assertIn("- `skills/init-codex-harness/assets/AGENTS.md.template`", text)
                self.assertIn(
                    "| Init skill project template asset | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` | `skills/init-codex-harness/assets/AGENTS.md.template` |",
                    text,
                )
                self.assertIn(
                    "Skill-local project template used by the init skill; top-level `templates/AGENTS.md.template` remains a compatibility/bootstrap template",
                    text,
                )
        self.assertEqual(canonical, generated)

    def test_v1_protection_scope_names_current_limit(self):
        readme = (ROOT / "adapters" / "codex" / "README.md").read_text(encoding="utf-8")
        generated_readme = (ROOT / "plugins" / "ai-agent-meta-harness" / "README.md").read_text(encoding="utf-8")
        scope = (ROOT / "adapters" / "codex" / "plugin-scope.md").read_text(encoding="utf-8")
        generated_scope = (ROOT / "plugins" / "ai-agent-meta-harness" / "plugin-scope.md").read_text(encoding="utf-8")

        expected_row = (
            "| v1 protection | Checker, hook smoke assertions, protected-path template, "
            "AGENTS reminder snippet, Codex hook template, pre-commit template, CI "
            "template, target-project install docs, and local smoke commands | "
            "Implemented for copied target-project guardrails; runtime plugin hook "
            "delivery remains deferred until a product-supported smoke or reviewed "
            "manual gate exists |"
        )
        for label, text in (
            ("README", readme),
            ("generated README", generated_readme),
            ("plugin-scope", scope),
            ("generated plugin-scope", generated_scope),
        ):
            with self.subTest(path=label):
                self.assertIn(expected_row, text)
                self.assertEqual(text.count("| v1 protection |"), 1)
                self.assertEqual(text.count(expected_row), 1)
                self.assertNotIn("install docs planned", text)
                self.assertNotIn("| Partial |", text)
        self.assertEqual(readme, generated_readme)
        self.assertEqual(scope, generated_scope)

    def test_runtime_delivery_evidence_status_is_deferred_with_surface_evidence(self):
        readme = (ROOT / "adapters" / "codex" / "README.md").read_text(encoding="utf-8")
        scope = (ROOT / "adapters" / "codex" / "plugin-scope.md").read_text(encoding="utf-8")
        generated_readme = (ROOT / "plugins" / "ai-agent-meta-harness" / "README.md").read_text(encoding="utf-8")
        generated_scope = (ROOT / "plugins" / "ai-agent-meta-harness" / "plugin-scope.md").read_text(encoding="utf-8")

        for text in (readme, generated_readme):
            normalized_readme = " ".join(text.split())
            with self.subTest(path="README"):
                self.assertIn("Runtime delivery has three evidence levels", text)
                self.assertIn("Generated artifact integrity", text)
                self.assertIn("Isolated CLI activation/config", text)
                self.assertIn("Runtime model-visible skill surfacing or plugin hook delivery", text)
                self.assertIn("no stable noninteractive smoke exists in this repo yet", text)
                self.assertIn("codex plugin marketplace add|upgrade|remove", text)
                self.assertIn("experimental app-server protocol tooling", text)
                self.assertIn("check-codex-cli-surface.py", text)
                self.assertIn("skips when it is absent", text)
                self.assertIn("This probe does not assert that a running Desktop session surfaced plugin skills", text)
                self.assertIn("Keep runtime hook manifest fields disabled", text)
                self.assertIn("Reviewed Manual Runtime Delivery Gate", text)
                self.assertIn("Minimum manual evidence packet", text)
                self.assertIn("Codex app or runtime version, surface name, OS", text)
                self.assertIn("showing the running Codex surface loaded `ai-agent-meta-harness`", normalized_readme)
                self.assertIn("For manifest `hooks` enablement only", text)
                self.assertIn("CLI help probes and isolated activation smokes remain prerequisites, not substitutes", normalized_readme)
        for text in (scope, generated_scope):
            normalized = " ".join(text.split())
            with self.subTest(path="plugin-scope"):
                self.assertIn("Runtime delivery evidence is deliberately deferred as of the 2026-05-04 maintenance pass", normalized)
                self.assertIn("generated artifact integrity and isolated CLI activation/config shape", normalized)
                self.assertIn("optional CLI surface probe can mechanically confirm those help markers", normalized)
                self.assertIn("That probe is not runtime delivery evidence and does not prove Desktop model-visible skill surfacing or plugin hook event delivery", normalized)
                self.assertIn("Runtime hook manifest fields must remain absent", normalized)
                self.assertIn("An explicitly reviewed manual gate may substitute for an automated runtime delivery smoke only when it records a concrete evidence packet", normalized)
                self.assertIn("Codex app or runtime version, surface name, OS, plugin source path", normalized)
                self.assertIn("fresh session transcript, screenshot, or exported runtime trace showing the generated `ai-agent-meta-harness` plugin surfaced the expected skills", normalized)
                self.assertIn("Manifest `hooks` fields still require separate evidence that a plugin hook received a real tool event", normalized)
                self.assertIn("CLI help probes and isolated activation smokes are prerequisites, not substitutes", normalized)
        self.assertEqual(readme, generated_readme)
        self.assertEqual(scope, generated_scope)


if __name__ == "__main__":
    unittest.main()
