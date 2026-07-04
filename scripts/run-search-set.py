#!/usr/bin/env python3
"""Run Active verify commands from a harness search-set file."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEARCH_SET = ROOT / "backlog" / "repository-search-set.md"
CASE_RE = re.compile(r"^###\s+([A-Za-z0-9_-]+):\s*(.+?)\s*$", re.MULTILINE)
VERIFY_RE = re.compile(r"^- \*\*verify\*\*: `([^`]+)`\s*$", re.MULTILINE)
ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELL_SYNTAX_RE = re.compile(r"[|&;<>()[\]{}$`\\*?\n]")


@dataclass(frozen=True)
class SearchSetCase:
    case_id: str
    title: str
    verify: str


class UnsafeVerifyCommand(ValueError):
    """Raised when a markdown-authored verify command needs shell evaluation."""


def active_block(text: str) -> str:
    marker = re.search(r"^## Active\s*$", text, flags=re.MULTILINE)
    if not marker:
        raise ValueError("search-set is missing '## Active'")
    archived = re.search(r"^## Archived\s*$", text[marker.end() :], flags=re.MULTILINE)
    end = marker.end() + archived.start() if archived else len(text)
    return text[marker.end() : end]


def parse_active_cases(text: str) -> list[SearchSetCase]:
    block = active_block(text)
    matches = list(CASE_RE.finditer(block))
    if not matches:
        raise ValueError("search-set has no Active cases")

    cases: list[SearchSetCase] = []
    for index, match in enumerate(matches):
        case_text_start = match.end()
        case_text_end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        case_text = block[case_text_start:case_text_end]
        verify_matches = VERIFY_RE.findall(case_text)
        case_id = match.group(1)
        title = match.group(2)
        if len(verify_matches) != 1:
            raise ValueError(f"{case_id}: expected exactly one '- **verify**: `...`' line")
        verify = verify_matches[0].strip()
        if not verify:
            raise ValueError(f"{case_id}: verify command is empty")
        cases.append(SearchSetCase(case_id, title, verify))
    return cases


def selected_cases(cases: list[SearchSetCase], selected: list[str]) -> list[SearchSetCase]:
    if not selected:
        return cases
    by_id = {case.case_id: case for case in cases}
    missing = [case_id for case_id in selected if case_id not in by_id]
    if missing:
        raise ValueError(f"unknown Active case id(s): {', '.join(missing)}")
    return [by_id[case_id] for case_id in selected]


def verify_argv(command: str) -> list[str]:
    if SHELL_SYNTAX_RE.search(command):
        raise UnsafeVerifyCommand(
            "verify command contains shell syntax; use a plain argv command without pipes, redirects, chaining, command substitution, or globs"
        )
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise UnsafeVerifyCommand(f"verify command cannot be parsed as argv: {exc}") from exc
    if not argv:
        raise UnsafeVerifyCommand("verify command is empty")
    if ENV_ASSIGNMENT_RE.match(argv[0]):
        raise UnsafeVerifyCommand("verify command uses an environment assignment prefix; wrap it in a checked script instead")
    return argv


def run_case(case: SearchSetCase, *, cwd: Path, timeout: int) -> int:
    print(f"==> {case.case_id}: {case.title}")
    print(f"$ {case.verify}")
    try:
        argv = verify_argv(case.verify)
    except UnsafeVerifyCommand as exc:
        print(f"{case.case_id}: unsafe verify command: {exc}", file=sys.stderr)
        return 2
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"{case.case_id}: timed out after {timeout}s", file=sys.stderr)
        return 124
    if result.returncode == 0:
        print(f"{case.case_id}: PASS")
    else:
        print(f"{case.case_id}: FAIL ({result.returncode})", file=sys.stderr)
    return result.returncode


def load_cases(path: Path) -> list[SearchSetCase]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read search-set {path}: {exc}") from exc
    return parse_active_cases(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-set", type=Path, default=DEFAULT_SEARCH_SET, help="search-set.md path")
    parser.add_argument("--case", action="append", default=[], help="Active case id to run; repeatable")
    parser.add_argument("--list", action="store_true", help="list selected Active cases without running commands")
    parser.add_argument("--cwd", type=Path, default=ROOT, help="working directory for verify commands")
    parser.add_argument("--timeout", type=int, default=300, help="timeout per verify command in seconds")
    args = parser.parse_args(argv)

    try:
        cases = selected_cases(load_cases(args.search_set), args.case)
    except ValueError as exc:
        print(f"run-search-set: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for case in cases:
            print(f"{case.case_id}\t{case.verify}\t{case.title}")
        return 0

    failures: list[tuple[str, int]] = []
    for case in cases:
        status = run_case(case, cwd=args.cwd, timeout=args.timeout)
        if status != 0:
            failures.append((case.case_id, status))

    if failures:
        summary = ", ".join(f"{case_id}={status}" for case_id, status in failures)
        print(f"run-search-set: failing Active case(s): {summary}", file=sys.stderr)
        return 1
    print(f"run-search-set: PASS ({len(cases)} Active case(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
