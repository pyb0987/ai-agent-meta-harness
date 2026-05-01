#!/usr/bin/env python3
"""Validate maintenance multi-review summaries.

The checker intentionally validates review-result structure, not prose style.
It looks for sections that contain either "Multi-review:" or "Review outcome:"
and enforces the fields required by MAINTENANCE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_GLOB = "backlog/review-*.md"
DEFAULT_BACKLOG_FILES = (
    "backlog/core.md",
    "backlog/claude-adapter.md",
    "backlog/codex-adapter.md",
)

SCORE_RE = re.compile(r"\b(?:normalized\s+)?score(?:d)?(?:\s*[:=]|\s+)(\d+(?:\.\d+)?)\b", re.IGNORECASE)
REVIEW_MARKER_RE = re.compile(r"^\s*(?:Multi-review|Review outcome):\s*$", re.MULTILINE)
WHY_NOT_10_RE = re.compile(r"\b(?:why\s+not\s+10|not\s+10)\b", re.IGNORECASE)
SCORE_9_DISPOSITION_RE = re.compile(
    r"\b(?:backlog|follow-up|residual risk|remaining follow-up|addressed|fixed|resolved|accepted)\b",
    re.IGNORECASE,
)

REQUIRED_FIELDS = {
    "verdict": re.compile(r"\b(?:PASS|VETO|MIXED|FAIL)\b"),
    "blocking findings": re.compile(r"\bBlocking findings?:", re.IGNORECASE),
    "follow-up/residual risk": re.compile(r"\bFollow-up/residual risk:", re.IGNORECASE),
    "score handling": re.compile(r"\bScore handling:", re.IGNORECASE),
    "rerun status": re.compile(r"\bRerun status:", re.IGNORECASE),
    "final acceptance": re.compile(r"\bFinal acceptance:", re.IGNORECASE),
}
SECTION_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
PENDING_RE = re.compile(r"\b(?:pending|active re-review|not accepted yet)\b", re.IGNORECASE)
HANDLED_LOW_SCORE_RE = re.compile(
    r"\b(?:VETO|MIXED|FAIL|not accepted|below .*threshold|restored policy)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReviewSection:
    heading: str
    start_line: int
    text: str


def normalize_score(raw: str) -> float:
    value = float(raw)
    if 0 <= value <= 1:
        return value * 10
    return value


def review_sections(text: str) -> list[ReviewSection]:
    matches = list(SECTION_RE.finditer(text))
    sections: list[ReviewSection] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end]
        if not REVIEW_MARKER_RE.search(body):
            continue
        sections.append(
            ReviewSection(
                heading=match.group(2).strip(),
                start_line=text.count("\n", 0, match.start()) + 1,
                text=body,
            )
        )
    return sections


def bullet_records(section_text: str) -> list[str]:
    records: list[str] = []
    current: list[str] = []
    for line in section_text.splitlines():
        if line.startswith("- "):
            if current:
                records.append(" ".join(part.strip() for part in current))
            current = [line]
        elif current and (line.startswith("  ") or not line.strip()):
            current.append(line)
    if current:
        records.append(" ".join(part.strip() for part in current))
    return records


def review_block(section_text: str) -> str:
    match = REVIEW_MARKER_RE.search(section_text)
    if not match:
        return ""
    return section_text[match.start():]


def has_score_scope(record: str) -> bool:
    if not record.startswith("- ") or ":" not in record:
        return False
    prefix = record[2:].split(":", 1)[0].strip().lower()
    return bool(prefix) and "score" not in prefix


def validate_text(text: str, *, source: str = "<text>") -> list[str]:
    errors: list[str] = []
    sections = review_sections(text)
    if not sections:
        return errors

    for section in sections:
        label = f"{source}:{section.start_line} ({section.heading})"
        block = review_block(section.text)
        for field, pattern in REQUIRED_FIELDS.items():
            if not pattern.search(block):
                errors.append(f"{label}: missing required review field: {field}")

        records = bullet_records(block)
        score_handling_records = [
            record
            for record in records
            if record.lower().startswith("- score handling:")
        ]
        score_9_handling_text = " ".join(score_handling_records)
        score_records = [
            record
            for record in records
            if not record.lower().startswith("- score handling:") and SCORE_RE.search(record)
        ]
        if not score_records:
            errors.append(f"{label}: missing required review field: score")
        if not any(has_score_scope(record) for record in score_records):
            errors.append(f"{label}: missing required review field: critic scope")
        for record in records:
            lower = record.lower()
            if (
                (lower.startswith("- rerun status:") or lower.startswith("- final acceptance:"))
                and PENDING_RE.search(record)
            ):
                errors.append(f"{label}: unresolved review status: {record}")

        for record in score_records:
            scores = [normalize_score(match.group(1)) for match in SCORE_RE.finditer(record)]
            if scores:
                if not has_score_scope(record):
                    errors.append(f"{label}: score record lacks critic scope: {record}")
                if not REQUIRED_FIELDS["verdict"].search(record):
                    errors.append(f"{label}: score record lacks verdict: {record}")
                if not REQUIRED_FIELDS["blocking findings"].search(record):
                    errors.append(f"{label}: score record lacks blocking findings: {record}")
            for score in scores:
                if 9 <= score < 10:
                    why_context = f"{record} {score_9_handling_text}"
                    if not WHY_NOT_10_RE.search(why_context):
                        errors.append(f"{label}: score 9 lacks why-not-10 handling: {record}")
                    if not SCORE_9_DISPOSITION_RE.search(why_context):
                        errors.append(f"{label}: score 9 lacks backlog/residual-risk disposition: {record}")
                if score >= 9:
                    continue
                if not HANDLED_LOW_SCORE_RE.search(record):
                    errors.append(f"{label}: score below 9 lacks VETO/not-accepted handling: {record}")
                if "PASS" in record and not HANDLED_LOW_SCORE_RE.search(record):
                    errors.append(f"{label}: score below 9 is marked PASS without VETO handling: {record}")

    return errors


def validate_paths(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{path}: unreadable review summary: {exc}")
            continue
        errors.extend(validate_text(text, source=path.as_posix()))
    return errors


def default_paths() -> list[Path]:
    paths = set(ROOT.glob(DEFAULT_REVIEW_GLOB))
    paths.update(path for relative in DEFAULT_BACKLOG_FILES if (path := ROOT / relative).exists())
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(arg) for arg in args] if args else default_paths()
    errors = validate_paths(paths)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Maintenance review summaries are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
