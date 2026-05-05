#!/usr/bin/env python3
"""Run the repository stable-handoff verification gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ReleaseCommand:
    name: str
    argv: tuple[str, ...]
    clean_worktree: bool = False
    search_set_evidence: bool = False
    ci_local_only: bool = False

    def __post_init__(self) -> None:
        if not self.argv:
            raise ValueError(f"{self.name}: argv must not be empty")
        if self.argv[0] in {"sh", "bash", "zsh"} and len(self.argv) > 1 and self.argv[1] == "-c":
            raise ValueError(f"{self.name}: release commands must not use shell -c")

    @property
    def command(self) -> str:
        return shlex.join(self.argv)


RELEASE_COMMANDS = (
    ReleaseCommand("compat mirrors", ("python3", "scripts/check-compat-mirrors.py")),
    ReleaseCommand("claude adapter paths", ("python3", "scripts/check-claude-adapter-paths.py")),
    ReleaseCommand("codex plugin sync", ("python3", "scripts/sync-codex-plugin.py", "--check")),
    ReleaseCommand("codex hook schema drift", ("python3", "adapters/codex/scripts/check-codex-hook-schema-drift.py")),
    ReleaseCommand(
        "codex autoresearch hook smoke",
        (
            "python3",
            "adapters/codex/scripts/smoke-autoresearch-hooks.py",
            "--checker",
            "adapters/codex/scripts/check-autoresearch-protected.py",
            "--protected-file",
            "adapters/codex/templates/autoresearch-protected.txt",
        ),
    ),
    ReleaseCommand("codex local plugin smoke", ("python3", "adapters/codex/scripts/smoke-local-plugin.py")),
    ReleaseCommand(
        "codex local plugin activation smoke",
        ("python3", "adapters/codex/scripts/smoke-local-plugin-activation.py"),
        ci_local_only=True,
    ),
    ReleaseCommand("codex marketplace metadata", ("python3", "scripts/check-codex-marketplace-metadata.py")),
    ReleaseCommand("maintenance review records", ("python3", "scripts/check-maintenance-review.py")),
    ReleaseCommand(
        "search-set evidence records",
        ("python3", "scripts/check-search-set-evidence.py"),
        search_set_evidence=True,
    ),
    ReleaseCommand("backlog archive lifecycle", ("python3", "scripts/check-backlog-archive-lifecycle.py")),
    ReleaseCommand("repository search-set", ("python3", "scripts/run-search-set.py")),
    ReleaseCommand("repository tests", ("python3", "-m", "unittest", "discover", "-s", "tests")),
    ReleaseCommand("claude adapter tests", ("python3", "-m", "unittest", "discover", "-s", "adapters/claude/tests")),
    ReleaseCommand("codex adapter tests", ("python3", "-m", "unittest", "discover", "-s", "adapters/codex/tests")),
    ReleaseCommand("clean worktree", ("python3", "scripts/check-clean-worktree.py"), clean_worktree=True),
)


def with_search_set_evidence_mode(command: ReleaseCommand, *, base_ref: str | None) -> ReleaseCommand:
    if not command.search_set_evidence or base_ref is None:
        return command
    return ReleaseCommand(
        name=f"{command.name} (base-ref: {base_ref})",
        argv=(*command.argv, "--base-ref", base_ref),
        clean_worktree=command.clean_worktree,
        search_set_evidence=command.search_set_evidence,
        ci_local_only=command.ci_local_only,
    )


def selected_commands(
    *,
    skip_clean_worktree: bool,
    base_ref: str | None = None,
    ci: bool = False,
) -> tuple[ReleaseCommand, ...]:
    if not skip_clean_worktree:
        commands = RELEASE_COMMANDS
    else:
        commands = tuple(command for command in RELEASE_COMMANDS if not command.clean_worktree)
    if ci:
        commands = tuple(command for command in commands if not command.ci_local_only)
    return tuple(with_search_set_evidence_mode(command, base_ref=base_ref) for command in commands)


def print_command_list(commands: tuple[ReleaseCommand, ...]) -> None:
    for index, command in enumerate(commands, start=1):
        print(f"{index:02d}\t{command.command}\t{command.name}")


def run_command(command: ReleaseCommand, *, timeout: int) -> int:
    print(f"==> {command.name}")
    print(f"$ {command.command}")
    try:
        result = subprocess.run(
            command.argv,
            cwd=ROOT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"{command.name}: timed out after {timeout}s", file=sys.stderr)
        return 124
    if result.returncode == 0:
        print(f"{command.name}: PASS")
    else:
        print(f"{command.name}: FAIL ({result.returncode})", file=sys.stderr)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list release commands without running them")
    parser.add_argument(
        "--skip-clean-worktree",
        action="store_true",
        help="omit the clean-worktree gate when validating an in-progress diff",
    )
    parser.add_argument(
        "--base-ref",
        help=(
            "run search-set evidence validation against REF...HEAD for a clean "
            "release candidate or branch handoff"
        ),
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help=(
            "run the deterministic CI subset; excludes local-only checks such "
            "as the Codex CLI activation smoke and should be combined with "
            "--skip-clean-worktree"
        ),
    )
    parser.add_argument("--timeout", type=int, default=300, help="timeout per command in seconds")
    args = parser.parse_args(argv)

    commands = selected_commands(skip_clean_worktree=args.skip_clean_worktree, base_ref=args.base_ref, ci=args.ci)
    evidence_mode = f"base-ref diff ({args.base_ref})" if args.base_ref else "worktree status"
    if args.ci:
        print("release-gate mode: ci deterministic subset")
    print(f"search-set evidence mode: {evidence_mode}")
    if args.list:
        print_command_list(commands)
        return 0

    failures: list[tuple[str, int]] = []
    for command in commands:
        status = run_command(command, timeout=args.timeout)
        if status != 0:
            failures.append((command.name, status))

    if failures:
        summary = ", ".join(f"{name}={status}" for name, status in failures)
        print(f"verify-release: failing command(s): {summary}", file=sys.stderr)
        return 1
    print(f"verify-release: PASS ({len(commands)} command(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
