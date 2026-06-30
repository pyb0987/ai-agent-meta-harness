#!/usr/bin/env python3
"""Report bounded self-evolution candidates without adopting them.

This command is intentionally diagnostic. It may suggest trace, search-set,
instruction, or strategy-search follow-up, but it never edits files and its
default exit status stays zero for candidate suggestions.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import shlex
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "harness-dogfood-report/v1"
MAINTENANCE_NOTE_KIND = "quiet_post_task_diagnostic_candidate"
POST_TASK_SURFACE = "post_task"
EXPLICIT_SURFACE = "explicit_dogfood"
TRACE_ROOT = Path(".harness/traces")
SEARCH_SET_PATH = TRACE_ROOT / "search-set.md"
HARNESS_PREFIXES = (
    ".githooks/",
    ".harness/traces/search-set.md",
    "adapters/",
    "backlog/plans/",
    "core/",
    "docs/",
    "plugins/",
    "scripts/",
    "skills/",
)
HARNESS_FILES = {
    "MAINTENANCE.md",
    "README.md",
}
EVIDENCE_PREFIXES = (
    ".harness/traces/failures/",
    ".harness/traces/experiments/",
    ".harness/search-runs/",
    "backlog/review-",
)
EXPERIMENT_OUTPUT_PREFIXES = (
    ".harness/experiments/",
    "experiments/",
    "autoresearch/",
)


class DogfoodError(ValueError):
    pass


def repo_relative(path: str | Path, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            return candidate.as_posix()
    return candidate.as_posix()


def git_changed_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise DogfoodError(stderr or "git status failed")
    return parse_porcelain_changed_paths(result.stdout)


def parse_porcelain_changed_paths(output: bytes) -> list[str]:
    paths: list[str] = []
    entries = output.decode("utf-8", errors="surrogateescape").split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:] if len(entry) > 3 and entry[2] == " " else entry[2:].lstrip()
        if path:
            paths.append(path)
        if "R" in status or "C" in status:
            index += 1
    return sorted(set(paths))


def is_harness_affecting(path: str) -> bool:
    return path in HARNESS_FILES or path.startswith(HARNESS_PREFIXES)


def is_evolution_trace(path: str) -> bool:
    return path.startswith(".harness/traces/evolution/") and path.endswith(".md")


def is_experiment_trace(path: str) -> bool:
    return path.startswith(".harness/traces/experiments/") and path.endswith(".md")


def is_trigger_evidence(path: str) -> bool:
    return path.startswith(EVIDENCE_PREFIXES)


def is_experiment_output(path: str) -> bool:
    return path.startswith(EXPERIMENT_OUTPUT_PREFIXES) and not path.startswith(".harness/traces/")


def is_strategy_selection(path: str) -> bool:
    return (
        path.startswith(".harness/search-runs/")
        and "/selections/" in path
        and path.endswith("-selection.yml")
    )


def candidate(
    *,
    kind: str,
    trigger_evidence: list[str],
    affected_surface: list[str],
    proposed_action: str,
    reason: str,
    reusable_future_value: str,
    status: str = "candidate",
    surface_scope: str = POST_TASK_SURFACE,
    surfacing_priority: int = 50,
) -> dict[str, Any]:
    return {
        "candidate_kind": kind,
        "status": status,
        "evidence_status": "diagnostic_only",
        "evidence_role": "pointer_only",
        "adoption_boundary": "not_adoption_evidence",
        "trigger_evidence_role": "pointer_only",
        "trigger_evidence": sorted(set(trigger_evidence)),
        "affected_surface": sorted(set(affected_surface)),
        "reusable_future_value": reusable_future_value,
        "proposed_action": proposed_action,
        "reason": reason,
        "surface_scope": surface_scope,
        "surfacing_priority": surfacing_priority,
    }


def trace_gap_candidates(changed_paths: list[str]) -> list[dict[str, Any]]:
    harness_changes = [path for path in changed_paths if is_harness_affecting(path)]
    evidence = [path for path in changed_paths if is_trigger_evidence(path)]
    has_evolution_trace = any(is_evolution_trace(path) for path in changed_paths)
    if not harness_changes or has_evolution_trace or not evidence:
        return []
    return [
        candidate(
            kind="trace_candidate",
            trigger_evidence=evidence,
            affected_surface=harness_changes,
            proposed_action="Draft an evolution trace with Plan 16 retrieval provenance.",
            reusable_future_value=(
                "Future harness work can inspect the same usage or review evidence "
                "instead of rediscovering why these harness-affecting files changed."
            ),
            reason=(
                "Harness-affecting changes have concrete usage or review evidence "
                "but no changed evolution trace. This is a diagnostic suggestion, "
                "not proof that a trace must be written."
            ),
            surfacing_priority=90,
        )
    ]


def experiment_trace_candidates(changed_paths: list[str]) -> list[dict[str, Any]]:
    outputs = [path for path in changed_paths if is_experiment_output(path)]
    if not outputs or any(is_experiment_trace(path) for path in changed_paths):
        return []
    return [
        candidate(
            kind="trace_candidate",
            trigger_evidence=outputs,
            affected_surface=outputs,
            proposed_action="Consider an experiment trace if these outputs carry reusable method evidence.",
            reusable_future_value=(
                "Future experiment or evaluator work can reuse the outcome and "
                "avoid repeating an already explored method branch."
            ),
            reason=(
                "Experiment-like outputs changed without a matching experiment trace. "
                "Sparse trace history is not a failure; this is a prompt to decide "
                "whether the outputs deserve durable trace memory."
            ),
            surfacing_priority=70,
        )
    ]


def strategy_selection_candidates(changed_paths: list[str]) -> list[dict[str, Any]]:
    selections = [path for path in changed_paths if is_strategy_selection(path)]
    if not selections:
        return []
    return [
        candidate(
            kind="strategy_search_candidate",
            trigger_evidence=selections,
            affected_surface=selections,
            proposed_action=(
                "Keep the selection diagnostic until the patch is applied as a normal "
                "content change and verified through the adoption path."
            ),
            reusable_future_value=(
                "Future strategy-search adoption work can distinguish selected "
                "diagnostic pointers from content changes that have actually crossed "
                "the normal review path."
            ),
            reason="Strategy-search selections are diagnostic pointers, not stable evidence.",
            surfacing_priority=80,
        )
    ]


def active_search_set_text(search_set_path: Path) -> str:
    try:
        text = search_set_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    parts = text.split("\n## Active", 1)
    if len(parts) != 2:
        return ""
    return parts[1].split("\n## Archived", 1)[0]


def search_set_sections(active_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in active_text.splitlines():
        if line.startswith("### "):
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines)))
            current_title = line[4:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
    if current_title is not None:
        sections.append((current_title, "\n".join(current_lines)))
    return sections


def verify_command(section_body: str) -> str | None:
    for line in section_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **verify**:"):
            start = stripped.find("`")
            end = stripped.rfind("`")
            if start != -1 and end > start:
                return stripped[start + 1 : end].strip()
            return ""
    return None


def command_path_tokens(command: str) -> list[str]:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    paths: list[str] = []
    for token in tokens:
        if token in {"python", "python3", "sh", "bash", "-m"}:
            continue
        if token.startswith("-"):
            continue
        if "/" in token or token.endswith((".py", ".sh", ".md", ".yml", ".yaml")):
            paths.append(token)
    return paths


def stale_verify_reason(command: str, repo_root: Path) -> str | None:
    for token in command_path_tokens(command):
        if token.startswith(("http://", "https://")):
            continue
        if not (repo_root / token).exists():
            return f"verify command references missing path: {token}"
    return None


def search_set_candidates(repo_root: Path) -> list[dict[str, Any]]:
    search_set_path = repo_root / SEARCH_SET_PATH
    active_text = active_search_set_text(search_set_path)
    if not active_text:
        return []
    reports: list[dict[str, Any]] = []
    for title, body in search_set_sections(active_text):
        command = verify_command(body)
        if command is None or command == "":
            reports.append(
                candidate(
                    kind="search_set_candidate",
                    status="malformed",
                    trigger_evidence=[SEARCH_SET_PATH.as_posix()],
                    affected_surface=[SEARCH_SET_PATH.as_posix()],
                    proposed_action="Add a deterministic verify command or archive the Active entry.",
                    reusable_future_value=(
                        "Future harness checks need Active search-set entries to "
                        "carry executable commands before they can be reused as "
                        "regression probes."
                    ),
                    reason=f"Active search-set entry lacks a verify command: {title}",
                    surface_scope=EXPLICIT_SURFACE,
                    surfacing_priority=60,
                )
            )
            continue
        stale_reason = stale_verify_reason(command, repo_root)
        if stale_reason:
            reports.append(
                candidate(
                    kind="search_set_candidate",
                    trigger_evidence=[SEARCH_SET_PATH.as_posix()],
                    affected_surface=[SEARCH_SET_PATH.as_posix()],
                    proposed_action="Update the verify command, add the missing file, or archive the entry.",
                    reusable_future_value=(
                        "Future verification can avoid stale guard commands and "
                        "keep recurring-risk checks executable."
                    ),
                    reason=f"{title}: {stale_reason}",
                    surface_scope=EXPLICIT_SURFACE,
                    surfacing_priority=55,
                )
            )
    return reports


def note_eligible(candidate_record: dict[str, Any], surface_mode: str) -> bool:
    if candidate_record.get("status") != "candidate":
        return False
    if surface_mode == POST_TASK_SURFACE and candidate_record.get("surface_scope") != POST_TASK_SURFACE:
        return False
    return bool(
        candidate_record.get("trigger_evidence")
        and candidate_record.get("reusable_future_value")
        and candidate_record.get("proposed_action")
    )


def select_maintenance_note(candidates: list[dict[str, Any]], surface_mode: str) -> dict[str, Any] | None:
    eligible = [
        (index, candidate_record)
        for index, candidate_record in enumerate(candidates)
        if note_eligible(candidate_record, surface_mode)
    ]
    if not eligible:
        return None
    source_index, selected = sorted(
        eligible,
        key=lambda item: (
            -int(item[1].get("surfacing_priority", 0)),
            item[1].get("candidate_kind", ""),
            item[1].get("reason", ""),
            item[0],
        ),
    )[0]
    first_evidence = selected["trigger_evidence"][0]
    rendered_note = (
        f"Diagnostic maintenance note: {selected['candidate_kind']} from "
        f"{first_evidence}; next: {selected['proposed_action']}"
    )
    return {
        "kind": MAINTENANCE_NOTE_KIND,
        "surface_mode": surface_mode,
        "evidence_status": "diagnostic_only",
        "evidence_role": "pointer_only",
        "adoption_boundary": "not_adoption_evidence",
        "trigger_evidence_role": "pointer_only",
        "source_candidate_index": source_index,
        "candidate_kind": selected["candidate_kind"],
        "trigger_evidence": selected["trigger_evidence"],
        "affected_surface": selected["affected_surface"],
        "reusable_future_value": selected["reusable_future_value"],
        "proposed_action": selected["proposed_action"],
        "reason": selected["reason"],
        "rendered_note": rendered_note,
    }


def build_report(
    repo_root: Path = ROOT,
    changed_paths: list[str] | None = None,
    surface_mode: str = POST_TASK_SURFACE,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if surface_mode not in {POST_TASK_SURFACE, EXPLICIT_SURFACE}:
        raise DogfoodError(f"unsupported surface mode: {surface_mode}")
    paths = sorted(set(changed_paths if changed_paths is not None else git_changed_paths(repo_root)))
    internal_candidates: list[dict[str, Any]] = []
    internal_candidates.extend(trace_gap_candidates(paths))
    internal_candidates.extend(experiment_trace_candidates(paths))
    internal_candidates.extend(strategy_selection_candidates(paths))
    internal_candidates.extend(search_set_candidates(repo_root))
    if surface_mode == POST_TASK_SURFACE:
        candidates = [
            candidate_record
            for candidate_record in internal_candidates
            if candidate_record.get("surface_scope") == POST_TASK_SURFACE
        ]
    else:
        candidates = internal_candidates
    maintenance_note = select_maintenance_note(candidates, surface_mode)
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_status": "diagnostic_only",
        "evidence_role": "pointer_only",
        "adoption_boundary": "not_adoption_evidence",
        "maintenance_note_kind": MAINTENANCE_NOTE_KIND,
        "maintenance_note": maintenance_note,
        "surface_mode": surface_mode,
        "repo": repo_root.as_posix(),
        "changed_paths": paths,
        "internal_candidate_count": len(internal_candidates),
        "suppressed_candidate_count": len(internal_candidates) - len(candidates),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def has_malformed(report: dict[str, Any]) -> bool:
    return any(candidate.get("status") == "malformed" for candidate in report.get("candidates", []))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=ROOT.as_posix(), help="Repository root to inspect.")
    parser.add_argument(
        "--strict-candidates",
        action="store_true",
        help="Exit nonzero when diagnostic candidates are reported.",
    )
    parser.add_argument(
        "--surface-mode",
        choices=(POST_TASK_SURFACE, EXPLICIT_SURFACE),
        default=POST_TASK_SURFACE,
        help=(
            "post_task emits at most one current-work maintenance note; "
            "explicit_dogfood may surface one note from any diagnostic candidate."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        report = build_report(Path(args.repo), surface_mode=args.surface_mode)
    except DogfoodError as exc:
        print(f"check-harness-dogfood: error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if has_malformed(report):
        return 2
    if args.strict_candidates and report["candidate_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
