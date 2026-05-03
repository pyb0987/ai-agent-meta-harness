#!/usr/bin/env python3
"""Fail when a release or stable handoff is attempted from a dirty worktree."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def git_status(root: Path = Path.cwd()) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> int:
    result = git_status()
    if result.returncode != 0:
        print(result.stderr.strip() or "Unable to read git worktree status.", file=sys.stderr)
        return 2

    dirty = [line for line in result.stdout.splitlines() if line.strip()]
    if dirty:
        print("DIRTY WORKTREE: release or stable handoff requires explicit clean-tree verification.")
        print("Commit, stash, or intentionally record an exception for these paths:")
        for line in dirty:
            print(f"- {line}")
        return 1

    print("Clean worktree verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
