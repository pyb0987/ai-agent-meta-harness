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
    ".harness/traces/search-set.md",
    ".githooks/",
    "adapters/",
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
BACKLOG_SECTION_RE = re.compile(r"^### \d+\. .+?(?=^### \d+\. |\Z)", re.MULTILINE | re.DOTALL)
EVIDENCE_LINE_RE = re.compile(
    r"^\s*(?:-\s*)?(BEFORE|AFTER):\s+(PASS|FAIL|SKIPPED)\b(.+)",
    re.IGNORECASE,
)
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


def validate(changed_paths: list[str], *, read_text=Path.read_text) -> list[str]:
    affected = [path for path in changed_paths if is_harness_affecting(path)]
    if not affected:
        return []
    progressing_records: list[str] = []
    review_records: list[str] = []
    completed_records: list[str] = []
    record_texts: list[str] = []
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
    if progressing_records:
        if any(has_current_record_evidence(text, status="진행중") for text in progressing_records):
            return []
    elif review_records:
        if any(has_current_record_evidence(text, status="리뷰대기") for text in review_records):
            return []
    elif completed_records:
        if any(has_completed_record_evidence_for_paths(text, affected) for text in completed_records):
            return []
    elif any(has_search_set_evidence(text) for text in record_texts):
        return []
    return [
        "Harness-affecting changes lack recorded search-set before/after evidence "
        "or an explicit skipped reason.",
        "Harness-affecting paths:",
        *[f"- {path}" for path in affected],
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional changed paths to validate instead of reading git status.",
    )
    args = parser.parse_args()

    try:
        changed_paths = args.paths or git_changed_paths()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors = validate(changed_paths)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Search-set evidence compliance is recorded or not required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
