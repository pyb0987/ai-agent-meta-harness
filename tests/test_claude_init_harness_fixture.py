#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def smoke_validate_init_harness_output(project: Path) -> list[str]:
    errors: list[str] = []
    required_dirs = (
        ".claude/traces/evolution",
        ".claude/traces/failures",
        ".claude/traces/experiments",
        ".claude/hooks",
    )
    for relative in required_dirs:
        if not (project / relative).is_dir():
            errors.append(f"MISSING DIR: {relative}")

    if (project / ".claude/agents").exists():
        errors.append("FORBIDDEN DIR: .claude/agents")

    search_set = project / ".claude/traces/search-set.md"
    if not search_set.is_file():
        errors.append("MISSING FILE: .claude/traces/search-set.md")
    else:
        text = search_set.read_text(encoding="utf-8")
        for marker in ("## Active", "### SS-001:", "- **verify**: `"):
            if marker not in text:
                errors.append(f"SEARCH SET MISSING: {marker}")

    if not (project / ".claude/traces/evolution/001-initial-harness.md").is_file():
        errors.append("MISSING FILE: .claude/traces/evolution/001-initial-harness.md")

    claude_md = project / "CLAUDE.md"
    if not claude_md.is_file():
        errors.append("MISSING FILE: CLAUDE.md")
    else:
        text = claude_md.read_text(encoding="utf-8")
        if len(text.splitlines()) > 100:
            errors.append("CLAUDE.md exceeds 100 lines")
        for marker in (
            "## Harness",
            ".claude/hooks",
            ".claude/traces",
            "Change Strategy",
            "Sub-agent",
        ):
            if marker not in text:
                errors.append(f"CLAUDE.md MISSING: {marker}")

    settings = project / ".claude/settings.local.json"
    if not settings.is_file():
        errors.append("MISSING FILE: .claude/settings.local.json")
    else:
        try:
            parsed = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"INVALID JSON: .claude/settings.local.json: {exc}")
        else:
            if not isinstance(parsed.get("hooks"), dict):
                errors.append("SETTINGS MISSING: hooks object")

    return errors


class ClaudeInitHarnessFixtureSmokeTests(unittest.TestCase):
    def make_project(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        project = Path(tempdir.name)
        write(
            project / ".claude/traces/search-set.md",
            """# Harness Search Set

## Active
### SS-001: Typecheck before handoff
- **Symptom**: Type errors can slip into commits.
- **verify**: `npm run typecheck`
- **ref**: none

## Archived
(Resolved cases with low regression risk)
""",
        )
        write(
            project / ".claude/traces/evolution/001-initial-harness.md",
            """---
iteration: 1
type: additive
verdict: neutral
---

# Initial Harness
""",
        )
        for relative in (
            ".claude/traces/failures/.keep",
            ".claude/traces/experiments/.keep",
            ".claude/hooks/typecheck.sh",
        ):
            write(project / relative, "")
        write(
            project / ".claude/settings.local.json",
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "matcher": "Edit|Write",
                                "hooks": [{"type": "command", "command": "bash .claude/hooks/typecheck.sh"}],
                            }
                        ]
                    }
                },
                indent=2,
            ),
        )
        write(
            project / "CLAUDE.md",
            """# Project Instructions

## Harness

### Hooks (`.claude/settings.local.json`)
- `.claude/hooks/typecheck.sh` blocks typecheck failures.

### Traces
- `.claude/traces/evolution/`
- `.claude/traces/failures/`
- `.claude/traces/search-set.md`

### Change Strategy
Additive first -> Subtractive -> Structural.

### Sub-agent triggers
Use multi-review for qualitative judgment and evaluator isolation for fixed evaluators.
""",
        )
        return project

    def test_minimal_project_fixture_satisfies_init_harness_output_contract(self):
        project = self.make_project()

        self.assertEqual(smoke_validate_init_harness_output(project), [])

    def test_fixture_rejects_forbidden_agent_directory(self):
        project = self.make_project()
        (project / ".claude/agents").mkdir()

        self.assertIn("FORBIDDEN DIR: .claude/agents", smoke_validate_init_harness_output(project))

    def test_fixture_rejects_missing_active_search_set_case(self):
        project = self.make_project()
        write(project / ".claude/traces/search-set.md", "# Harness Search Set\n\n## Active\n")

        errors = smoke_validate_init_harness_output(project)

        self.assertTrue(any("SEARCH SET MISSING: ### SS-001:" == error for error in errors))


if __name__ == "__main__":
    unittest.main()
