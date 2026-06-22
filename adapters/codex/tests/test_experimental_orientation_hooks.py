#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import os
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "adapters" / "codex" / "hooks" / "experimental" / "harness_orientation.py"


class ExperimentalOrientationHookTests(unittest.TestCase):
    def run_hook(
        self,
        *args: str,
        cwd: Path,
        state_dir: Path,
        stdin: str = "",
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["AI_AGENT_META_HARNESS_STATE_DIR"] = str(state_dir)
        return subprocess.run(
            ["python3", str(HOOK), *args],
            cwd=cwd,
            input=stdin,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def make_project(self, root: Path) -> None:
        traces = root / ".harness" / "traces"
        (traces / "failures").mkdir(parents=True)
        (traces / "search-set.md").write_text(
            textwrap.dedent(
                """\
                ---
                description: "fixture"
                ---
                # Harness Search Set

                ## Active

                ### SS-001: Fixture verifier
                - **verify**: `python3 -m unittest`

                ### SS-002: Second verifier
                - **verify**: `python3 scripts/check.py`

                ## Archived
                """
            ),
            encoding="utf-8",
        )
        (traces / "failures" / "001-open.md").write_text(
            "---\nresolved: false\n---\n# open\n",
            encoding="utf-8",
        )

    def test_session_start_outputs_orientation_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()
            self.make_project(project)

            result = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["systemMessage"], "AI_AGENT_META_HARNESS:NORMAL")
        hook_output = output["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "SessionStart")
        context = hook_output["additionalContext"]
        self.assertIn("orientation only, not evidence and not enforcement", context)
        self.assertIn("detected_trace_root: .harness/traces", context)
        self.assertIn("active_search_set_cases: 2", context)
        self.assertIn("python3 -m unittest", context)
        self.assertIn("unresolved_failures: 1", context)
        self.assertIn("plugin manifest hooks remain disabled", context)

    def test_session_start_handles_missing_trace_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()

            result = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("detected_trace_root: not_detected", context)
        self.assertIn("active_search_set_cases: 0", context)

    def test_mode_tracker_persists_exact_commands_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()
            self.make_project(project)

            change = self.run_hook(
                "--user-prompt-submit",
                cwd=project,
                state_dir=state,
                stdin=json.dumps({"prompt": "/harness evolve"}),
            )
            session = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(change.returncode, 0, change.stderr)
        self.assertEqual(json.loads(change.stdout)["systemMessage"], "AI_AGENT_META_HARNESS:HARNESS-EVOLUTION")
        context = json.loads(session.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mode: harness-evolution", context)

    def test_incidental_text_does_not_switch_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()
            self.make_project(project)

            first = self.run_hook(
                "--user-prompt-submit",
                cwd=project,
                state_dir=state,
                stdin=json.dumps({"prompt": "/harness multi-review"}),
            )
            incidental = self.run_hook(
                "--user-prompt-submit",
                cwd=project,
                state_dir=state,
                stdin=json.dumps({"prompt": "please add a /harness normal button"}),
            )
            session = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(incidental.returncode, 0, incidental.stderr)
        self.assertEqual(incidental.stdout, "")
        context = json.loads(session.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mode: multi-review", context)

    def test_off_mode_suppresses_orientation_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()
            self.make_project(project)

            off = self.run_hook(
                "--user-prompt-submit",
                cwd=project,
                state_dir=state,
                stdin=json.dumps({"prompt": "/harness off"}),
            )
            session = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(off.returncode, 0, off.stderr)
        self.assertEqual(json.loads(off.stdout)["systemMessage"], "AI_AGENT_META_HARNESS:OFF")
        output = json.loads(session.stdout)
        self.assertEqual(output["systemMessage"], "AI_AGENT_META_HARNESS:OFF")
        self.assertNotIn("hookSpecificOutput", output)

    def test_malformed_state_does_not_crash_or_preserve_bad_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            state = Path(tmp) / "state"
            project.mkdir()
            state.mkdir()
            self.make_project(project)
            (state / "harness-mode.txt").write_text("maybe\n", encoding="utf-8")

            result = self.run_hook("--session-start", cwd=project, state_dir=state)

        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mode: normal", context)
        self.assertIn("state_note: ignored invalid mode state", context)

    def test_example_hook_config_is_not_manifest_activation(self):
        config = json.loads(
            (ROOT / "adapters" / "codex" / "hooks" / "experimental" / "harness-orientation-hooks.json.example").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(config["hooks"]), {"SessionStart", "UserPromptSubmit"})
        self.assertIn("AI_AGENT_META_HARNESS_PLUGIN_ROOT", config["hooks"]["SessionStart"][0]["hooks"][0]["command"])
        manifest = json.loads(
            (ROOT / "adapters" / "codex" / "plugin" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("hooks", manifest)


if __name__ == "__main__":
    unittest.main()
