#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INIT_HARNESS = ROOT / "adapters" / "claude" / "commands" / "init-harness.md"
MIRROR_INIT_HARNESS = ROOT / "commands" / "init-harness.md"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def smoke_validate_init_harness_output(project: Path, trace_root: str = ".claude/traces") -> list[str]:
    errors: list[str] = []
    required_dirs = (
        f"{trace_root}/evolution",
        f"{trace_root}/failures",
        f"{trace_root}/experiments",
        ".claude/hooks",
    )
    for relative in required_dirs:
        if not (project / relative).is_dir():
            errors.append(f"MISSING DIR: {relative}")

    if (project / ".claude/agents").exists():
        errors.append("FORBIDDEN DIR: .claude/agents")

    search_set = project / trace_root / "search-set.md"
    if not search_set.is_file():
        errors.append(f"MISSING FILE: {trace_root}/search-set.md")
    else:
        text = search_set.read_text(encoding="utf-8")
        for marker in ("## Active", "### SS-001:", "- **verify**: `"):
            if marker not in text:
                errors.append(f"SEARCH SET MISSING: {marker}")

    if not (project / trace_root / "evolution/001-initial-harness.md").is_file():
        errors.append(f"MISSING FILE: {trace_root}/evolution/001-initial-harness.md")

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
            trace_root,
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

    def test_migrated_harness_trace_root_satisfies_init_harness_output_contract(self):
        project = self.make_project()
        trace_root = ".harness/traces"
        shutil.rmtree(project / ".claude/traces")
        write(
            project / f"{trace_root}/search-set.md",
            """# Harness Search Set

## Active
### SS-001: Preserve migrated shared history
- **Symptom**: Migrated projects can split trace history across roots.
- **verify**: `npm run typecheck`
- **ref**: none
""",
        )
        write(
            project / f"{trace_root}/evolution/001-initial-harness.md",
            """---
iteration: 1
type: additive
verdict: neutral
---

# Initial Harness
""",
        )
        for relative in (
            f"{trace_root}/failures/.keep",
            f"{trace_root}/experiments/.keep",
        ):
            write(project / relative, "")
        write(
            project / "CLAUDE.md",
            """# Project Instructions

## Harness

### Hooks (`.claude/settings.local.json`)
- `.claude/hooks/typecheck.sh` blocks typecheck failures.

### Traces
- Active trace root: `.harness/traces`
- Reusing meaningful migrated history; do not create a second trace root.

### Change Strategy
Additive first -> Subtractive -> Structural.

### Sub-agent triggers
Use multi-review for qualitative judgment and evaluator isolation for fixed evaluators.
""",
        )

        self.assertEqual(smoke_validate_init_harness_output(project, trace_root), [])
        self.assertFalse((project / ".claude/traces").exists())

    def test_fixture_rejects_forbidden_agent_directory(self):
        project = self.make_project()
        (project / ".claude/agents").mkdir()

        self.assertIn("FORBIDDEN DIR: .claude/agents", smoke_validate_init_harness_output(project))

    def test_fixture_rejects_missing_active_search_set_case(self):
        project = self.make_project()
        write(project / ".claude/traces/search-set.md", "# Harness Search Set\n\n## Active\n")

        errors = smoke_validate_init_harness_output(project)

        self.assertTrue(any("SEARCH SET MISSING: ### SS-001:" == error for error in errors))

    def test_init_harness_documents_migrated_trace_root_selection(self):
        text = INIT_HARNESS.read_text(encoding="utf-8")

        for marker in (
            "Select the active trace root before writing new trace files",
            ".harness/traces/",
            "Meaningful history includes `search-set.md` with Active cases",
            "migrate/copy it into `.claude/traces/`",
            "Do not split future trace history silently",
            "Active trace root selected by evidence",
            "`{trace_root}/search-set.md` template or reused Active search-set exists",
            "`{trace_root}/evolution/001-initial-harness.md` written",
            "CLAUDE.md includes Harness section (.claude/hooks/, selected trace root",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_compatibility_mirror_has_migrated_trace_root_selection(self):
        canonical = INIT_HARNESS.read_text(encoding="utf-8")
        mirror = MIRROR_INIT_HARNESS.read_text(encoding="utf-8")

        for marker in (
            "Select the active trace root before writing new trace files",
            "migrate/copy it into `.claude/traces/`",
            "Active trace root selected by evidence",
            "`{trace_root}/search-set.md` template or reused Active search-set exists",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))

    def test_init_harness_sub_agent_boundary_matches_core_policy(self):
        text = INIT_HARNESS.read_text(encoding="utf-8")

        for marker in (
            "two repo-specific triggers (multi-review for qualitative judgment, Fixed Evaluator for evaluator independence)",
            "Generic sub-agent uses (parallel Explore, context firewall) are Claude Code runtime tactics, not harness methodology",
            "use them only when they materially preserve independence or unblock bounded parallel work",
            "Temporary subagents are allowed only as bounded Claude Code runtime tactics for the two core isolation triggers",
            "extra runtime routing when it materially preserves independence or unblocks bounded parallel work",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("Prefer over-invoking to under-invoking", text)
        self.assertNotIn("three trigger categories", text)

    def test_compatibility_mirror_has_sub_agent_boundary_wording(self):
        canonical = INIT_HARNESS.read_text(encoding="utf-8")
        mirror = MIRROR_INIT_HARNESS.read_text(encoding="utf-8")

        for marker in (
            "Claude Code runtime tactics, not harness methodology",
            "Temporary subagents are allowed only as bounded Claude Code runtime tactics for the two core isolation triggers",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, mirror)
                self.assertEqual(canonical.count(marker), mirror.count(marker))
        self.assertNotIn("Prefer over-invoking to under-invoking", mirror)
        self.assertNotIn("three trigger categories", mirror)


if __name__ == "__main__":
    unittest.main()
