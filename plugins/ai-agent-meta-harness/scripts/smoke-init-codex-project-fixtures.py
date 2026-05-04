#!/usr/bin/env python3
"""Smoke-test init-codex-harness contracts on representative project fixtures.

This does not run a live Codex model. It mechanically validates the project
artifacts that `init-codex-harness` is expected to produce or preserve for
TypeScript, Python, and migrated Claude-history projects.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


FIXTURES = ("typescript-app", "python-research", "migrated-claude-history")
VERIFY_RE = re.compile(r"^- \*\*verify\*\*: `([^`]+)`\s*$", re.MULTILINE)
VERIFY_TIMEOUT_SECONDS = 20


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def search_set(command: str, source: str) -> str:
    return f"""
    # Harness Search Set

    ## Active

    ### SS-001: initial project verification

    - **Source**: {source}
    - **Failure mode**: Project initialization loses the primary local verifier.
    - **verify**: `{command}`

    ## Archived
    """


def evolution_trace(project_type: str, trace_root: str, command: str) -> str:
    return f"""
    ---
    title: initial-codex-harness
    project_type: {project_type}
    trace_root: {trace_root}
    ---

    ## Trigger

    Initialize Codex harness instructions for the representative project fixture.

    ## Diagnosis

    The project needs a trace root, an Active search-set verifier, and concise
    AGENTS.md guidance before harness work can be repeated safely.

    ## Change

    Created `{trace_root}/search-set.md` with `{command}` as the first Active
    verifier and wrote project-local AGENTS.md harness guidance.

    ## Result

    Fixture validation passed.

    ## Lesson

    Codex init behavior should preserve the most specific local verifier found
    during project inspection.
    """


def agents(trace_root: str, command: str, *, migrated: bool = False) -> str:
    migration_note = ""
    if migrated:
        migration_note = """
        This project temporarily reuses `.claude/traces/` because it already
        contains meaningful history. Propose a reviewed migration before moving
        history into `.harness/traces/`.
        """
    return f"""
    # Project Instructions

    ## Build

    - Primary verifier: `{command}`

    ## Harness

    Use `{trace_root}` for harness history. Before and after harness changes,
    run Active verify commands from `{trace_root}/search-set.md` when practical
    and record PASS/FAIL in the related evolution trace.
    {migration_note}

    ## Codex Notes

    Do not add Claude Code hook configuration for Codex-only initialization.
    """


def create_typescript_fixture(root: Path) -> Path:
    project = root / "typescript-app"
    write(
        project / "package.json",
        """
        {
          "scripts": {
            "typecheck": "node ./scripts/typecheck.js",
            "test": "vitest run",
            "lint": "eslint .",
            "build": "vite build"
          }
        }
        """,
    )
    write(
        project / "scripts/typecheck.js",
        """
        console.log("fixture typecheck passed");
        """,
    )
    trace_root = ".harness/traces"
    command = "npm run typecheck"
    write(project / f"{trace_root}/search-set.md", search_set(command, "package.json scripts"))
    write(project / f"{trace_root}/evolution/001-initial-codex-harness.md", evolution_trace("typescript", trace_root, command))
    (project / f"{trace_root}/failures").mkdir(parents=True)
    (project / f"{trace_root}/experiments").mkdir(parents=True)
    write(project / "AGENTS.md", agents(trace_root, command))
    return project


def create_python_fixture(root: Path) -> Path:
    project = root / "python-research"
    write(
        project / "pyproject.toml",
        """
        [project]
        name = "python-research"

        [tool.pytest.ini_options]
        testpaths = ["tests"]
        """,
    )
    write(project / "pytest.py", "print('fixture pytest passed')\n")
    trace_root = ".harness/traces"
    command = "python3 -m pytest"
    write(project / f"{trace_root}/search-set.md", search_set(command, "pyproject.toml pytest config"))
    write(project / f"{trace_root}/evolution/001-initial-codex-harness.md", evolution_trace("python", trace_root, command))
    (project / f"{trace_root}/failures").mkdir(parents=True)
    (project / f"{trace_root}/experiments").mkdir(parents=True)
    write(project / "AGENTS.md", agents(trace_root, command))
    return project


def create_migrated_fixture(root: Path) -> Path:
    project = root / "migrated-claude-history"
    write(project / "package.json", '{"scripts":{"test":"node ./test-runner.js"}}\n')
    write(project / "test-runner.js", "console.log('fixture migrated npm test passed')\n")
    trace_root = ".claude/traces"
    command = "npm test -- --runInBand"
    write(project / f"{trace_root}/search-set.md", search_set(command, "existing Claude Active case"))
    write(project / f"{trace_root}/failures/001-existing-regression.md", "resolved: false\n\nExisting meaningful failure trace.\n")
    write(project / f"{trace_root}/evolution/001-initial-codex-harness.md", evolution_trace("migrated", trace_root, command))
    (project / f"{trace_root}/experiments").mkdir(parents=True)
    write(project / "AGENTS.md", agents(trace_root, command, migrated=True))
    return project


def create_fixtures(root: Path) -> list[Path]:
    return [
        create_typescript_fixture(root),
        create_python_fixture(root),
        create_migrated_fixture(root),
    ]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rel(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def active_verify_commands(search_set_text: str) -> list[str]:
    active = search_set_text.split("## Archived", 1)[0]
    return [match.group(1).strip() for match in VERIFY_RE.finditer(active)]


def command_masks_exit_status(command: str) -> bool:
    return any(marker in command for marker in ("| tail", "|| true", "; echo $?", "&& echo $?"))


def run_verify_command(project: Path, command: str) -> str | None:
    try:
        result = subprocess.run(
            command,
            cwd=project,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=VERIFY_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"{project.name}: VERIFY COMMAND TIMED OUT: {command}"
    if result.returncode != 0:
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        if len(output) > 500:
            output = output[:500] + "...<truncated>"
        detail = f": {output}" if output else ""
        return f"{project.name}: VERIFY COMMAND FAILED ({result.returncode}): {command}{detail}"
    return None


def validate_trace_root(project: Path, trace_root: str, command: str, *, migrated: bool) -> list[str]:
    errors: list[str] = []
    root = project / trace_root
    for directory in ("evolution", "failures", "experiments"):
        path = root / directory
        if not path.is_dir():
            errors.append(f"{project.name}: MISSING TRACE DIR: {rel(project, path)}")
    search_path = root / "search-set.md"
    if not search_path.is_file():
        errors.append(f"{project.name}: MISSING SEARCH SET: {rel(project, search_path)}")
    else:
        text = read(search_path)
        for marker in ("## Active", "### SS-001:", "- **verify**: `"):
            if marker not in text:
                errors.append(f"{project.name}: SEARCH SET MISSING MARKER: {marker}")
        if f"- **verify**: `{command}`" not in text:
            errors.append(f"{project.name}: SEARCH SET DOES NOT USE EXPECTED VERIFY: {command}")
        commands = active_verify_commands(text)
        if not commands:
            errors.append(f"{project.name}: SEARCH SET HAS NO ACTIVE VERIFY COMMANDS")
        for verify_command in commands:
            if command_masks_exit_status(verify_command):
                errors.append(f"{project.name}: SEARCH SET VERIFY MUST NOT MASK EXIT STATUS")
                continue
            failure = run_verify_command(project, verify_command)
            if failure:
                errors.append(failure)
    evolution = root / "evolution" / "001-initial-codex-harness.md"
    if not evolution.is_file():
        errors.append(f"{project.name}: MISSING INITIAL EVOLUTION TRACE: {rel(project, evolution)}")
    else:
        text = read(evolution)
        for marker in ("---", "## Trigger", "## Diagnosis", "## Change", "## Result", "## Lesson"):
            if marker not in text:
                errors.append(f"{project.name}: EVOLUTION TRACE MISSING MARKER: {marker}")
    harness_root = project / ".harness" / "traces"
    if migrated and harness_root.exists():
        errors.append(f"{project.name}: MIGRATED PROJECT MUST NOT SPLIT HISTORY INTO .harness/traces")
    if not migrated and (project / ".claude" / "traces").exists():
        errors.append(f"{project.name}: NEW PROJECT MUST NOT CREATE .claude/traces")
    return errors


def validate_agents(project: Path, trace_root: str, command: str, *, migrated: bool) -> list[str]:
    path = project / "AGENTS.md"
    if not path.is_file():
        return [f"{project.name}: MISSING AGENTS.md"]
    text = read(path)
    errors: list[str] = []
    for marker in (trace_root, f"{trace_root}/search-set.md", command, "Active verify commands"):
        if marker not in text:
            errors.append(f"{project.name}: AGENTS.md MISSING MARKER: {marker}")
    if migrated:
        for marker in ("temporarily reuses `.claude/traces/`", "reviewed migration"):
            if marker not in text:
                errors.append(f"{project.name}: MIGRATED AGENTS.md MISSING MARKER: {marker}")
    if ".codex/hooks.json" in text or "PostToolUse" in text:
        errors.append(f"{project.name}: AGENTS.md MUST NOT ADD CLAUDE-ONLY HOOK ASSUMPTIONS")
    return errors


def validate_project(project: Path) -> list[str]:
    expectations = {
        "typescript-app": (".harness/traces", "npm run typecheck", False),
        "python-research": (".harness/traces", "python3 -m pytest", False),
        "migrated-claude-history": (".claude/traces", "npm test -- --runInBand", True),
    }
    try:
        trace_root, command, migrated = expectations[project.name]
    except KeyError:
        return [f"UNKNOWN FIXTURE: {project.name}"]
    errors = validate_trace_root(project, trace_root, command, migrated=migrated)
    errors.extend(validate_agents(project, trace_root, command, migrated=migrated))
    return errors


def smoke(fixtures_root: Path | None = None, *, keep_fixtures: bool = False) -> list[str]:
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if fixtures_root is None:
        if keep_fixtures:
            fixtures_root = Path(tempfile.mkdtemp(prefix="codex-init-fixtures."))
        else:
            temp_dir = tempfile.TemporaryDirectory(prefix="codex-init-fixtures.")
            fixtures_root = Path(temp_dir.name)
    else:
        fixtures_root.mkdir(parents=True, exist_ok=True)
        for name in FIXTURES:
            path = fixtures_root / name
            if path.exists():
                shutil.rmtree(path)

    try:
        projects = create_fixtures(fixtures_root)
        errors: list[str] = []
        for project in projects:
            errors.extend(validate_project(project))
        return errors
    finally:
        if keep_fixtures:
            print(f"Kept fixtures at: {fixtures_root}")
        if temp_dir is not None:
            temp_dir.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-root", type=Path, help="optional directory for generated fixtures")
    parser.add_argument("--keep-fixtures", action="store_true", help="keep temporary fixtures for inspection")
    args = parser.parse_args(argv)

    errors = smoke(args.fixtures_root, keep_fixtures=args.keep_fixtures)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Codex init project fixture smoke passed: TypeScript, Python, migrated Claude history")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
