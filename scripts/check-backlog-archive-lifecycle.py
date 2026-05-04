#!/usr/bin/env python3
"""Validate that active backlog files keep completed records archived."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_BACKLOG_FILES = (
    Path("backlog/core.md"),
    Path("backlog/claude-adapter.md"),
    Path("backlog/codex-adapter.md"),
)

SECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
STATUS_DONE_RE = re.compile(r"^Status:\s*완료\s*$", re.MULTILINE)
COMPLETION_GATE_RE = re.compile(r"^Completion Gate:\s*$", re.MULTILINE)
ARCHIVED_RE = re.compile(r"^Archived:\s*`([^`#]+)#([^`]+)`\s*$", re.MULTILINE)
ARCHIVE_EVIDENCE_RE = re.compile(
    r"^(?:Completion Gate|Review outcome|Multi-review|Legacy archive exception):\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Section:
    path: Path
    heading: str
    start_line: int
    text: str


def anchor_for_heading(heading: str) -> str:
    anchor = heading.strip().lower()
    anchor = re.sub(r"[`'\"“”‘’]", "", anchor)
    anchor = re.sub(r"[^0-9a-z가-힣]+", " ", anchor)
    anchor = re.sub(r"\s+", "-", anchor)
    anchor = re.sub(r"-+", "-", anchor)
    return anchor.strip("-")


def sections(path: Path, *, read_text=Path.read_text) -> list[Section]:
    text = read_text(path, encoding="utf-8")
    matches = list(SECTION_RE.finditer(text))
    parsed: list[Section] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        parsed.append(
            Section(
                path=path,
                heading=match.group(1).strip(),
                start_line=text.count("\n", 0, match.start()) + 1,
                text=text[match.start():end],
            )
        )
    return parsed


def archive_sections(root: Path, *, read_text=Path.read_text) -> dict[str, dict[str, Section]]:
    archives: dict[str, dict[str, Section]] = {}
    for active in ACTIVE_BACKLOG_FILES:
        archive = root / active.parent / "archive" / active.name
        try:
            parsed = sections(archive, read_text=read_text)
        except OSError:
            continue
        relative = archive.relative_to(root).as_posix()
        archives[relative] = {anchor_for_heading(section.heading): section for section in parsed}
    return archives


def validate_root(root: Path = ROOT, *, read_text=Path.read_text) -> list[str]:
    errors: list[str] = []
    known_archives = archive_sections(root, read_text=read_text)
    for relative in ACTIVE_BACKLOG_FILES:
        path = root / relative
        try:
            parsed = sections(path, read_text=read_text)
        except OSError:
            continue
        for section in parsed:
            if not STATUS_DONE_RE.search(section.text):
                continue
            label = f"{relative.as_posix()}:{section.start_line} ({section.heading})"
            archived = ARCHIVED_RE.search(section.text)
            if COMPLETION_GATE_RE.search(section.text):
                errors.append(f"{label}: completed active record still contains Completion Gate; move it to archive")
            if not archived:
                errors.append(f"{label}: completed active record lacks Archived pointer")
                continue
            archive_path, anchor = archived.groups()
            target = known_archives.get(archive_path, {}).get(anchor)
            if target is None:
                errors.append(f"{label}: Archived pointer target not found: {archive_path}#{anchor}")
            elif not STATUS_DONE_RE.search(target.text):
                errors.append(f"{label}: Archived pointer target lacks completed status: {archive_path}#{anchor}")
            elif not ARCHIVE_EVIDENCE_RE.search(target.text):
                errors.append(
                    f"{label}: Archived pointer target lacks Completion Gate or review evidence: "
                    f"{archive_path}#{anchor}"
                )
    return errors


def read_index_text(path: Path, *, encoding: str = "utf-8", root: Path = ROOT) -> str:
    relative = path.relative_to(root).as_posix()
    result = subprocess.run(
        ["git", "show", f":{relative}"],
        cwd=root,
        encoding=encoding,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise FileNotFoundError(result.stderr.strip() or f"missing staged file: {relative}")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--staged",
        action="store_true",
        help="validate backlog archive lifecycle using Git index contents",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    read_text = read_index_text if args.staged else Path.read_text
    errors = validate_root(read_text=read_text)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    mode = "staged " if args.staged else ""
    print(f"Backlog archive lifecycle is valid for {mode}content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
