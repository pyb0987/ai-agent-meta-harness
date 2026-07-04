#!/usr/bin/env python3
"""Check that harness-affecting changes record search-set evidence."""

from __future__ import annotations

from pathlib import Path
import argparse
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

HARNESS_AFFECTING_PREFIXES = (
    ".githooks/",
    "adapters/",
    "backlog/repository-search-set.md",
    "commands/",
    "core/",
    "docs/",
    "plugins/",
    "scripts/",
    "skills/",
)
HARNESS_AFFECTING_FILES = {
    "MAINTENANCE.md",
    "README.md",
}
NON_HARNESS_SCRIPT_PREFIXES = (
    "scripts/check-clean-worktree.py",
)
RECORD_PATH_PREFIXES = (
    ".harness/traces/",
    "backlog/",
)
SEARCH_SET_PATH = Path("backlog/repository-search-set.md")
AGGREGATE_SEARCH_SET_COMMANDS = {
    "python3 scripts/run-search-set.py",
}
BACKLOG_SECTION_RE = re.compile(r"^### \d+\. .+?(?=^### \d+\. |\Z)", re.MULTILINE | re.DOTALL)
EVIDENCE_LINE_RE = re.compile(
    r"^\s*(?:-\s*)?(BEFORE|AFTER):\s+(PASS|FAIL|SKIPPED)\b(.+)",
    re.IGNORECASE,
)
VERIFY_LINE_RE = re.compile(r"^\s*-\s+\*\*verify\*\*:\s+`([^`]+)`\s*$", re.MULTILINE)
SKIPPED_LINE_RE = re.compile(r"^\s*(?:-\s*)?SKIPPED\s*:\s+\S.+", re.IGNORECASE)
AMBIGUOUS_EVIDENCE_RE = re.compile(
    r"\bnot\s+skipped\b|\bTODO\b|\bTBD\b|\bunchecked\b",
    re.IGNORECASE,
)


def git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        paths.append(line[3:].strip())
    return sorted(set(paths))


def git_staged_paths() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTD"],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff --cached failed")
    return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})


def git_base_paths(base_ref: str) -> list[str]:
    commands = (
        ["git", "diff", "--name-only", "--diff-filter=ACMRTD", f"{base_ref}...HEAD"],
        ["git", "diff", "--name-only", "--diff-filter=ACMRTD", f"{base_ref}..HEAD"],
    )
    errors: list[str] = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            encoding="utf-8",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
        errors.append(result.stderr.strip())
    raise RuntimeError(errors[-1] or f"git diff against {base_ref} failed")


def read_index_text(path: Path, *, encoding: str) -> str:
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f":{relative}"],
        cwd=ROOT,
        encoding=encoding,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise FileNotFoundError(result.stderr.strip() or f"missing staged file: {relative}")
    return result.stdout


def read_head_text(path: Path, *, encoding: str) -> str:
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative}"],
        cwd=ROOT,
        encoding=encoding,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise FileNotFoundError(result.stderr.strip() or f"missing HEAD file: {relative}")
    return result.stdout


def is_harness_affecting(path: str) -> bool:
    if path in HARNESS_AFFECTING_FILES:
        return True
    if path.startswith(NON_HARNESS_SCRIPT_PREFIXES):
        return False
    return path.startswith(HARNESS_AFFECTING_PREFIXES)


def record_paths(changed_paths: list[str]) -> list[Path]:
    return [
        ROOT / path
        for path in changed_paths
        if path.startswith(RECORD_PATH_PREFIXES) and (ROOT / path).is_file()
    ]


def has_search_set_evidence(text: str) -> bool:
    if "Search-set verification:" not in text:
        return False
    section = text.rsplit("Search-set verification:", 1)[1]
    stop = section.find("\n- Multi-review")
    if stop != -1:
        section = section[:stop]
    if AMBIGUOUS_EVIDENCE_RE.search(section):
        return False
    has_before = False
    has_after = False
    for line in section.splitlines():
        if SKIPPED_LINE_RE.match(line):
            return True
        match = EVIDENCE_LINE_RE.match(line)
        if not match:
            continue
        status = match.group(2).lower()
        detail = match.group(3)
        if status in {"pass", "fail"} and "`" not in detail:
            continue
        if status == "skipped" and not detail.strip():
            continue
        label = match.group(1).lower()
        has_before = has_before or label == "before"
        has_after = has_after or label == "after"
    if has_before and has_after:
        return True
    return False


def evidence_commands(text: str) -> list[str]:
    if "Search-set verification:" not in text:
        return []
    section = text.rsplit("Search-set verification:", 1)[1]
    stop = section.find("\n- Multi-review")
    if stop != -1:
        section = section[:stop]
    commands: list[str] = []
    for line in section.splitlines():
        match = EVIDENCE_LINE_RE.match(line)
        if not match:
            continue
        status = match.group(2).lower()
        if status not in {"pass", "fail"}:
            continue
        detail = match.group(3)
        commands.extend(re.findall(r"`([^`]+)`", detail))
    return commands


def active_search_set_commands(
    *,
    read_text=Path.read_text,
    search_set_path: Path | None = None,
) -> set[str]:
    path = search_set_path or ROOT / SEARCH_SET_PATH
    try:
        text = read_text(path, encoding="utf-8")
    except OSError:
        return set()
    active = text.split("\n## Active", 1)
    if len(active) != 2:
        return set()
    active_text = active[1].split("\n## Archived", 1)[0]
    return set(VERIFY_LINE_RE.findall(active_text))


def sections_with_status(text: str, status: str) -> list[str]:
    return [section for section in BACKLOG_SECTION_RE.findall(text) if f"Status: {status}" in section]


def has_current_record_evidence(text: str, *, status: str | None = None) -> bool:
    if status is not None:
        return any(has_search_set_evidence(section) for section in sections_with_status(text, status))
    sections = [
        section for section in BACKLOG_SECTION_RE.findall(text)
        if "Status: 진행중" in section or "Status: 리뷰대기" in section
    ]
    if not sections:
        sections = [section for section in BACKLOG_SECTION_RE.findall(text) if "Status: 완료" in section]
    if not sections:
        return has_search_set_evidence(text)
    return any(has_search_set_evidence(section) for section in sections)


def has_completed_record_evidence_for_paths(text: str, affected_paths: list[str]) -> bool:
    for section in sections_with_status(text, "완료"):
        if not has_search_set_evidence(section):
            continue
        if any(path in section for path in affected_paths):
            return True
    return False


def current_record_sections(text: str) -> list[str]:
    sections = [
        section for section in BACKLOG_SECTION_RE.findall(text)
        if "Status: 진행중" in section or "Status: 리뷰대기" in section
    ]
    if not sections:
        sections = [section for section in BACKLOG_SECTION_RE.findall(text) if "Status: 완료" in section]
    return sections or [text]


def has_active_run_attestation(text: str, allowed_commands: set[str]) -> bool:
    allowed = allowed_commands | AGGREGATE_SEARCH_SET_COMMANDS
    if not allowed:
        return False
    for section in current_record_sections(text):
        if not has_search_set_evidence(section):
            continue
        commands = evidence_commands(section)
        if commands and all(command in allowed for command in commands):
            return True
    return False


def completed_sections_for_paths(text: str, affected_paths: list[str]) -> list[str]:
    return [
        section
        for section in sections_with_status(text, "완료")
        if any(path in section for path in affected_paths)
    ]


def validate(
    changed_paths: list[str],
    *,
    read_text=Path.read_text,
    require_active_run: bool = False,
) -> list[str]:
    affected = [path for path in changed_paths if is_harness_affecting(path)]
    if not affected:
        return []
    progressing_records: list[str] = []
    review_records: list[str] = []
    completed_records: list[str] = []
    record_texts: list[str] = []
    attestation_sections: list[str] = []
    for record in record_paths(changed_paths):
        try:
            text = read_text(record, encoding="utf-8")
        except OSError:
            continue
        record_texts.append(text)
        if sections_with_status(text, "진행중"):
            progressing_records.append(text)
        if sections_with_status(text, "리뷰대기"):
            review_records.append(text)
        if sections_with_status(text, "완료"):
            completed_records.append(text)
    satisfied = False
    if progressing_records:
        satisfied = any(has_current_record_evidence(text, status="진행중") for text in progressing_records)
        attestation_sections = [
            section
            for text in progressing_records
            for section in sections_with_status(text, "진행중")
        ] + [
            section
            for text in completed_records
            for section in completed_sections_for_paths(text, affected)
        ]
    elif review_records:
        satisfied = any(has_current_record_evidence(text, status="리뷰대기") for text in review_records)
        attestation_sections = [
            section
            for text in review_records
            for section in sections_with_status(text, "리뷰대기")
        ] + [
            section
            for text in completed_records
            for section in completed_sections_for_paths(text, affected)
        ]
    elif completed_records:
        satisfied = any(has_completed_record_evidence_for_paths(text, affected) for text in completed_records)
        attestation_sections = [
            section
            for text in completed_records
            for section in completed_sections_for_paths(text, affected)
        ]
    elif any(has_search_set_evidence(text) for text in record_texts):
        satisfied = True
        attestation_sections = record_texts
    if satisfied:
        if not require_active_run:
            return []
        allowed_commands = active_search_set_commands(read_text=read_text)
        if any(has_active_run_attestation(text, allowed_commands) for text in attestation_sections):
            return []
        return [
            "Harness-affecting changes lack active search-set run attestation.",
            "Expected BEFORE/AFTER commands to reference the aggregate runner "
            "or current Active search-set verify commands.",
            "Allowed commands:",
            *[f"- {command}" for command in sorted(allowed_commands | AGGREGATE_SEARCH_SET_COMMANDS)],
        ]
    return [
        "Harness-affecting changes lack recorded search-set before/after evidence "
        "or an explicit skipped reason.",
        "Harness-affecting paths:",
        *[f"- {path}" for path in affected],
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--staged",
        action="store_true",
        help="validate staged changed paths and staged backlog/trace records",
    )
    source.add_argument(
        "--base-ref",
        metavar="REF",
        help="validate changed paths in REF...HEAD for a clean release candidate",
    )
    parser.add_argument(
        "--require-active-run",
        action="store_true",
        help=(
            "in addition to shape-only evidence, require recorded BEFORE/AFTER "
            "commands to match the aggregate search-set runner or current Active "
            "verify commands"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional changed paths to validate instead of reading git status.",
    )
    args = parser.parse_args(argv)
    if args.paths and (args.staged or args.base_ref):
        parser.error("explicit paths cannot be combined with --staged or --base-ref")

    try:
        read_text = Path.read_text
        if args.paths:
            changed_paths = args.paths
        elif args.staged:
            changed_paths = git_staged_paths()
            read_text = read_index_text
        elif args.base_ref:
            changed_paths = git_base_paths(args.base_ref)
            read_text = read_head_text
        else:
            changed_paths = git_changed_paths()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors = validate(changed_paths, read_text=read_text, require_active_run=args.require_active_run)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Search-set evidence compliance is recorded or not required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
