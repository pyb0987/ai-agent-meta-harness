#!/usr/bin/env python3
"""Validate maintenance multi-review summaries.

The checker intentionally validates review-result structure, not prose style.
It looks for sections that contain either "Multi-review:" or "Review outcome:"
and enforces the fields required by MAINTENANCE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_GLOB = "backlog/review-*.md"
DEFAULT_BACKLOG_FILES = (
    "backlog/core.md",
    "backlog/claude-adapter.md",
    "backlog/codex-adapter.md",
    "backlog/archive/core.md",
    "backlog/archive/claude-adapter.md",
    "backlog/archive/codex-adapter.md",
)
CLEAN_HANDOFF_DISPOSITION_FILES = (
    "MAINTENANCE.md",
)
HIGH_IMPACT_PATH_PREFIXES = (
    ".githooks/",
    "adapters/",
    "core/",
    "scripts/",
)
HIGH_IMPACT_PATHS = {
    "MAINTENANCE.md",
    "README.md",
}
HIGH_IMPACT_PATH_EXEMPT_PREFIXES = (
    "scripts/check-clean-worktree.py",
)

SCORE_RE = re.compile(r"\b(?:normalized\s+)?score(?:d)?(?:\s*[:=]|\s+)(\d+(?:\.\d+)?)\b", re.IGNORECASE)
REVIEW_MARKER_RE = re.compile(r"^\s*(?:Multi-review|Review outcome):\s*$", re.MULTILINE)
MULTI_REVIEW_NOT_REQUIRED_RE = re.compile(r"^\s*Multi-review not required:\s+\S.+", re.MULTILINE)
WHY_NOT_10_RE = re.compile(r"\b(?:why\s+not\s+10|not\s+10)\b", re.IGNORECASE)
SCORE_9_DISPOSITION_RE = re.compile(
    r"\b(?:backlog|follow-up|residual risk|remaining follow-up|addressed|fixed|resolved|accepted)\b",
    re.IGNORECASE,
)
NONINDEPENDENT_FALLBACK_RE = re.compile(
    r"\b(?:FALLBACK_NONINDEPENDENT|"
    r"nonindependent multi-review fallback|"
    r"documented sequential fallback|"
    r"sequential fallback rather than independent|"
    r"sequential fallback in the parent context|"
    r"fallback in the parent context)\b",
    re.IGNORECASE,
)
FALLBACK_THRESHOLD_DISPOSITION_RE = re.compile(
    r"^\s*-\s*Fallback-threshold disposition:\s*"
    r"(?P<disposition>accepted residual risk|independent re-review|follow-up backlog item)"
    r"\b(?P<detail>.*)$",
    re.IGNORECASE | re.MULTILINE,
)
FALLBACK_ACTION_RECORD_THRESHOLD = 5
FALLBACK_ACTION_SECTION_THRESHOLD = 3

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
NEGATED_VETO_RE = re.compile(r"\b(?:no|not|without)\s+VETO\b|\bVETO\s+(?:was\s+)?not\s+triggered\b", re.IGNORECASE)
LOW_SCORE_BLOCKING_RE = re.compile(
    r"\b(?:VETO|"
    r"(?:triggered|treated as|marked|is|are)\s+VETO|"
    r"MIXED/VETO|"
    r"FAIL|"
    r"below\s+\d+(?:\.\d+)?\s+(?:is|are)\s+VETO|"
    r"below .*threshold|"
    r"restored policy)\b",
    re.IGNORECASE,
)
NOT_ACCEPTED_RE = re.compile(r"\bnot accepted\b|\baccepted:\s*no\b", re.IGNORECASE)
RERUN_RECORD_RE = re.compile(r"\b(?:rerun|re-review)\b", re.IGNORECASE)
METADATA_RECORD_PREFIXES = (
    "- score handling:",
    "- rerun status:",
    "- follow-up/residual risk:",
    "- final acceptance:",
)
GENERIC_SCORE_SCOPES = {
    "initial review",
    "historical re-review",
    "re-review",
    "review",
}


@dataclass(frozen=True)
class ReviewSection:
    heading: str
    start_line: int
    text: str


@dataclass(frozen=True)
class ReviewQualitySignal:
    source: str
    heading: str
    start_line: int
    fallback_records: tuple[str, ...]


@dataclass(frozen=True)
class FallbackThresholdDisposition:
    source: str
    start_line: int
    record: str


@dataclass(frozen=True)
class MissingMultiReviewSignal:
    changed_paths: tuple[str, ...]


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


def score_scope(record: str) -> str:
    if not has_score_scope(record):
        return ""
    scope = record[2:].split(":", 1)[0].strip().lower()
    if scope in GENERIC_SCORE_SCOPES:
        return ""
    return scope


def record_scores(record: str) -> list[float]:
    return [normalize_score(match.group(1)) for match in SCORE_RE.finditer(record)]


def has_successful_rerun(records: list[str], low_score_record: str) -> bool:
    scope = score_scope(low_score_record)
    for record in records:
        if not RERUN_RECORD_RE.search(record):
            continue
        if scope and scope not in record.lower():
            continue
        if any(score >= 9 for score in record_scores(record)):
            return True
    return False


def is_metadata_record(record: str) -> bool:
    lower = record.lower()
    return lower.startswith(METADATA_RECORD_PREFIXES)


def low_score_has_blocking_disposition(record: str, *, rerun_reached_threshold: bool) -> bool:
    if NOT_ACCEPTED_RE.search(record):
        return True
    if NEGATED_VETO_RE.search(record):
        return False
    if LOW_SCORE_BLOCKING_RE.search(record):
        return rerun_reached_threshold
    return False


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
            if not is_metadata_record(record) and SCORE_RE.search(record)
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
                rerun_reached_threshold = has_successful_rerun(records, record)
                if not low_score_has_blocking_disposition(
                    record,
                    rerun_reached_threshold=rerun_reached_threshold,
                ):
                    errors.append(
                        f"{label}: score below 9 lacks concrete VETO/not-accepted/rerun handling: {record}"
                    )
                if "PASS" in record and not low_score_has_blocking_disposition(
                    record,
                    rerun_reached_threshold=rerun_reached_threshold,
                ):
                    errors.append(f"{label}: score below 9 is marked PASS without VETO handling: {record}")

    return errors


def review_quality_signals(text: str, *, source: str = "<text>") -> list[ReviewQualitySignal]:
    signals: list[ReviewQualitySignal] = []
    for section in review_sections(text):
        block = review_block(section.text)
        fallback_records = tuple(
            record for record in bullet_records(block) if NONINDEPENDENT_FALLBACK_RE.search(record)
        )
        if fallback_records:
            signals.append(
                ReviewQualitySignal(
                    source=source,
                    heading=section.heading,
                    start_line=section.start_line,
                    fallback_records=fallback_records,
                )
            )
    return signals


def fallback_threshold_dispositions(
    text: str,
    *,
    source: str = "<text>",
) -> list[FallbackThresholdDisposition]:
    dispositions: list[FallbackThresholdDisposition] = []
    for match in FALLBACK_THRESHOLD_DISPOSITION_RE.finditer(text):
        detail = match.group("detail").strip()
        record = match.group(0).strip()
        if not detail:
            continue
        dispositions.append(
            FallbackThresholdDisposition(
                source=source,
                start_line=text.count("\n", 0, match.start()) + 1,
                record=record,
            )
        )
    return dispositions


def is_high_impact_path(path: str) -> bool:
    if path in HIGH_IMPACT_PATHS:
        return True
    if path.startswith(HIGH_IMPACT_PATH_EXEMPT_PREFIXES):
        return False
    return path.startswith(HIGH_IMPACT_PATH_PREFIXES)


def has_multi_review_disposition(texts: list[str]) -> bool:
    return any(REVIEW_MARKER_RE.search(text) or MULTI_REVIEW_NOT_REQUIRED_RE.search(text) for text in texts)


def missing_multi_review_signal(changed_paths: list[str], record_texts: list[str]) -> MissingMultiReviewSignal | None:
    high_impact = tuple(path for path in changed_paths if is_high_impact_path(path))
    if not high_impact or has_multi_review_disposition(record_texts):
        return None
    return MissingMultiReviewSignal(changed_paths=high_impact)


def missing_multi_review_summary(signal: MissingMultiReviewSignal | None, *, limit: int = 5) -> list[str]:
    if signal is None:
        return []
    shown = signal.changed_paths[:limit]
    lines = [
        (
            "Review-quality signal: high-impact changed path(s) lack a recorded "
            "Multi-review section or explicit 'Multi-review not required:' reason."
        )
    ]
    lines.extend(f"Review-quality signal: high-impact path: {path}" for path in shown)
    remaining = len(signal.changed_paths) - len(shown)
    if remaining > 0:
        lines.append(f"Review-quality signal: ... {remaining} additional high-impact path(s) omitted.")
    return lines


def quality_signal_summary(
    signals: list[ReviewQualitySignal],
    *,
    dispositions: list[FallbackThresholdDisposition] | None = None,
    limit: int = 5,
) -> list[str]:
    total_records = sum(len(signal.fallback_records) for signal in signals)
    if total_records == 0:
        return []
    dispositions = dispositions or []

    intensity = "repeated" if total_records > 1 else "one-off"
    threshold_met = (
        total_records >= FALLBACK_ACTION_RECORD_THRESHOLD
        or len(signals) >= FALLBACK_ACTION_SECTION_THRESHOLD
    )
    lines = [
        (
            "Review-quality signal: "
            f"{total_records} {intensity} nonindependent multi-review fallback "
            f"record(s) found across {len(signals)} review section(s)."
        ),
        (
            "Review-quality signal: fallback is visible but not a validation "
            "failure; use MAINTENANCE.md to decide whether repeated durable-contract "
            "fallback needs follow-up."
        ),
    ]
    if threshold_met:
        if dispositions:
            disposition = dispositions[-1]
            excerpt = re.sub(r"\s+", " ", disposition.record).strip()
            if len(excerpt) > 180:
                excerpt = f"{excerpt[:177]}..."
            lines.append(
                "Review-quality signal: fallback action threshold met and "
                f"disposition recorded at {disposition.source}:{disposition.start_line}: {excerpt}"
            )
        else:
            lines.append(
                "Review-quality signal: fallback action threshold met "
                f"({total_records} record(s), {len(signals)} section(s); threshold is "
                f"{FALLBACK_ACTION_RECORD_THRESHOLD} record(s) or "
                f"{FALLBACK_ACTION_SECTION_THRESHOLD} section(s)). Record maintainer "
                "disposition as accepted residual risk, independent re-review, or a "
                "follow-up backlog item."
            )
    shown = 0
    for signal in signals:
        for record in signal.fallback_records:
            if shown >= limit:
                remaining = total_records - shown
                lines.append(f"Review-quality signal: ... {remaining} additional fallback record(s) omitted.")
                return lines
            excerpt = re.sub(r"\s+", " ", record).strip()
            if len(excerpt) > 180:
                excerpt = f"{excerpt[:177]}..."
            lines.append(
                f"Review-quality signal: {signal.source}:{signal.start_line} "
                f"({signal.heading}): {excerpt}"
            )
            shown += 1
    return lines


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


def quality_signals_paths(paths: list[Path]) -> list[ReviewQualitySignal]:
    signals: list[ReviewQualitySignal] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        signals.extend(review_quality_signals(text, source=path.as_posix()))
    return signals


def fallback_threshold_dispositions_paths(paths: list[Path]) -> list[FallbackThresholdDisposition]:
    dispositions: list[FallbackThresholdDisposition] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        dispositions.extend(fallback_threshold_dispositions(text, source=path.as_posix()))
    return dispositions


def _git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _staged_changed_paths() -> list[str]:
    result = _git(["diff", "--cached", "--name-only", "--diff-filter=ACMRTD"], check=False)
    if result.returncode != 0:
        return []
    return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})


def _has_staged_changes() -> bool:
    result = _git(["diff", "--cached", "--quiet"], check=False)
    return result.returncode == 1


def _inside_git_worktree() -> bool:
    result = _git(["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def _read_index_text(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    result = _git(["show", f":{relative}"], check=False)
    if result.returncode != 0:
        raise OSError(result.stderr.strip() or f"git show :{relative} failed")
    return result.stdout


def indexed_default_paths() -> list[Path]:
    result = _git(["ls-files", "-z", "--", "backlog"], check=False)
    if result.returncode != 0:
        return []
    indexed = [path for path in result.stdout.split("\0") if path]
    wanted = set(DEFAULT_BACKLOG_FILES)
    for path in indexed:
        if fnmatch.fnmatch(path, DEFAULT_REVIEW_GLOB):
            wanted.add(path)
    return sorted(ROOT / path for path in wanted if path in indexed)


def staged_record_paths(changed_paths: list[str]) -> list[Path]:
    return [
        ROOT / path
        for path in changed_paths
        if path in DEFAULT_BACKLOG_FILES or fnmatch.fnmatch(path, DEFAULT_REVIEW_GLOB)
    ]


def clean_handoff_disposition_paths() -> list[Path]:
    return [
        ROOT / path
        for path in CLEAN_HANDOFF_DISPOSITION_FILES
        if (ROOT / path).exists()
    ]


def validate_index_paths(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            text = _read_index_text(path)
        except OSError as exc:
            errors.append(f"{path}: unreadable staged review summary: {exc}")
            continue
        errors.extend(validate_text(text, source=path.as_posix()))
    return errors


def quality_signals_index_paths(paths: list[Path]) -> list[ReviewQualitySignal]:
    signals: list[ReviewQualitySignal] = []
    for path in paths:
        try:
            text = _read_index_text(path)
        except OSError:
            continue
        signals.extend(review_quality_signals(text, source=path.as_posix()))
    return signals


def fallback_threshold_dispositions_index_paths(paths: list[Path]) -> list[FallbackThresholdDisposition]:
    dispositions: list[FallbackThresholdDisposition] = []
    for path in paths:
        try:
            text = _read_index_text(path)
        except OSError:
            continue
        dispositions.extend(fallback_threshold_dispositions(text, source=path.as_posix()))
    return dispositions


def default_paths(*, use_index: bool = False) -> list[Path]:
    if use_index:
        return indexed_default_paths()
    paths = set(ROOT.glob(DEFAULT_REVIEW_GLOB))
    paths.update(path for relative in DEFAULT_BACKLOG_FILES if (path := ROOT / relative).exists())
    return sorted(paths)


def validate_default_paths(*, use_index: bool = False) -> list[str]:
    paths = default_paths(use_index=use_index)
    if use_index:
        return validate_index_paths(paths)
    return validate_paths(paths)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    use_index = False
    if args:
        paths = [Path(arg) for arg in args]
        errors = validate_paths(paths)
        quality_signals = quality_signals_paths(paths)
        fallback_dispositions = fallback_threshold_dispositions_paths(paths)
        missing_multi_review = None
    else:
        use_index = _inside_git_worktree()
        paths = default_paths(use_index=use_index)
        errors = validate_index_paths(paths) if use_index else validate_paths(paths)
        quality_signals = (
            quality_signals_index_paths(paths) if use_index else quality_signals_paths(paths)
        )
        changed_paths = _staged_changed_paths() if use_index else []
        if use_index:
            disposition_paths = staged_record_paths(changed_paths)
            if not disposition_paths and not _has_staged_changes():
                disposition_paths = clean_handoff_disposition_paths()
        else:
            disposition_paths = paths
        fallback_dispositions = (
            fallback_threshold_dispositions_index_paths(disposition_paths)
            if use_index
            else fallback_threshold_dispositions_paths(disposition_paths)
        )
        record_texts: list[str] = []
        for path in disposition_paths:
            try:
                record_texts.append(_read_index_text(path) if use_index else path.read_text(encoding="utf-8"))
            except OSError:
                continue
        missing_multi_review = missing_multi_review_signal(changed_paths, record_texts)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Maintenance review summaries are valid.")
    for line in quality_signal_summary(quality_signals, dispositions=fallback_dispositions):
        print(line)
    for line in missing_multi_review_summary(missing_multi_review):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
