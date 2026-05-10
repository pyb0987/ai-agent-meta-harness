#!/usr/bin/env python3
"""Create and validate v2 AcceptancePacket skeletons."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import re
import shlex
import subprocess
import sys
import uuid

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "v2.0-draft"
PACKET_KEY = "AcceptancePacket"
COMMAND_EVIDENCE_HEADING = "# Command Evidence"
COMMAND_EVIDENCE_FIELD_RE = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
PUBLIC_SECTIONS = ("meta", "input", "result")
CANONICAL_ACCEPTANCE_PACKET_FIXTURES = {
    "backlog/fixtures/acceptance-packets/blocked.yml",
    "backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml",
    "backlog/fixtures/acceptance-packets/finalized-routine.yml",
    "backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml",
    "backlog/fixtures/acceptance-packets/start.yml",
    "backlog/fixtures/acceptance-packets/worktree-nonstable.yml",
}
FIXTURE_MATERIALIZATION_MARKER = ".fixture-materialization"
FIXTURE_MATERIALIZATION_ENV = "AI_META_HARNESS_TEST_FIXTURE_MATERIALIZATION"
META_FIELDS = ("packet_id", "schema_version", "lifecycle", "mode", "created_at", "finalized_at")
INPUT_FIELDS = ("intent", "actor", "source_refs", "user_judgment")
RESULT_GROUPS = ("inference", "evidence", "judgment", "decision")
FINALIZED_INFERENCE_FIELDS = (
    "change_class",
    "impact",
    "changed_paths",
    "intended_scope",
    "actual_scope",
    "deviations",
    "isolation",
    "protected_boundary_changed",
    "required_evidence",
    "required_review",
)
PROVENANCE_FIELDS = ("actor", "role", "date", "reason", "source_ref")
REVIEW_PROVENANCE_FIELDS = ("actor", "role", "date", "source_ref")
REVIEW_IMPORT_KEY = "AcceptancePacketReviewImport"
REVIEW_IMPORT_SCHEMA_VERSION = "acceptance-packet-review-import/v1"
REVIEW_IMPORT_FIELDS = {"schema_version", "target_binding", "MultiReviewResult", "review_lineage"}
REVIEW_IMPORT_RECORD_FIELDS = {"source_ref", "format", "source_digest", "status", "review_ids", "target_binding"}
TARGET_BINDING_FIELDS = {
    "packet_id",
    "packet_ref",
    "review_target_digest",
    "baseline_ref",
    "comparison_ref",
    "source_refs",
    "changed_paths",
    "required_review",
}
REVIEW_LINEAGE_FIELDS = {
    "review_id",
    "critic",
    "scope",
    "anti_scope",
    "score",
    "veto",
    "actor",
    "role",
    "date",
    "source_ref",
    "false_green_risk",
    "invariant_checked",
    "evidence",
    "source_refs",
    "blocking_findings",
    "why_not_10",
    "disposition",
    "rerun_of",
    "fixed_finding_ids",
}
REVIEW_MIRROR_FIELDS = REVIEW_LINEAGE_FIELDS
VACUOUS_REVIEW_VALUES = {
    "",
    "none",
    "na",
    "ok",
    "pass",
    "checked",
    "generic",
    "notapplicable",
    "selfattested",
    "readtheplan",
}
TARGET_FIELDS = ("evidence", "review", "from")
LIFECYCLES = {"start", "finalized", "blocked"}
MODES = {"staged", "base-ref", "worktree"}
PROTECTED_PREFIXES = (
    ".githooks/",
    "adapters/",
    "archive/v1/",
    "commands/",
    "core/",
    "plugins/",
    "scripts/",
    "skills/",
)
PROTECTED_PATHS = {
    ".harness/traces/search-set.md",
    "MAINTENANCE.md",
    "README.md",
}
REQUIRED_RESOLVED_REF_FIELDS = ("origin", "relation", "ref", "status", "target")
RESOLVED_REF_ORIGINS = {"input", "generated"}
RESOLVED_REF_RELATIONS = {
    "source",
    "artifact",
    "trace",
    "claim-evidence",
    "review-provenance",
    "waiver-provenance",
    "observation",
}
ANCHOR_RE = re.compile(r"[^a-z0-9]+")
PROOF_LIKE_RE = re.compile(
    r"\b(verified|guaranteed|proves?|runtime|public API|release-ready|production-ready)\b",
    re.IGNORECASE,
)
SEARCH_SET_TRACE_ANCHORS = {"active"}
RAW_CLAIM_EVIDENCE_PATH_PARTS = {
    ".harness",
    "artifact",
    "artifacts",
    "log",
    "logs",
    "probe-transcripts",
    "reports",
    "screenshots",
    "trace",
    "traces",
    "transcripts",
}
RAW_CLAIM_EVIDENCE_DIRECT_SUFFIXES = {
    ".csv",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".jsonl",
    ".log",
    ".pdf",
    ".png",
    ".tsv",
    ".webp",
}
RAW_CLAIM_EVIDENCE_CONTEXTUAL_SUFFIXES = {".json", ".txt", ".xml", ".yaml", ".yml"}

class PacketError(ValueError):
    pass


def git(root: Path, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def today() -> dt.date:
    return dt.date.today()


def packet_id() -> str:
    return f"pkt-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def load_packet(path: Path) -> dict:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PacketError(f"{path}: cannot read packet: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PacketError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict) or PACKET_KEY not in loaded:
        raise PacketError(f"{path}: missing {PACKET_KEY}")
    packet = loaded[PACKET_KEY]
    if not isinstance(packet, dict):
        raise PacketError(f"{path}: {PACKET_KEY} must be a mapping")
    return packet


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_anchor(text: str) -> str:
    return ANCHOR_RE.sub("-", text.strip().lower()).strip("-")


def has_markdown_anchor(path: Path, anchor: str) -> bool:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") and markdown_anchor(line.lstrip("#").strip()) == anchor:
                return True
    except OSError:
        return False
    return False


def resolve_repo_path(root: Path, ref_path: str) -> str | None:
    path = Path(ref_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (root / path).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    if not candidate.exists():
        return None
    return candidate.relative_to(root_resolved).as_posix()


def resolve_ref(root: Path, ref: str) -> str | None:
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("terminal:"):
        return None
    if ref.startswith("file:"):
        rel = ref.removeprefix("file:")
        return resolve_repo_path(root, rel)
    if ref.startswith("trace:"):
        body = ref.removeprefix("trace:")
        rel, sep, anchor = body.partition("#")
        resolved = resolve_repo_path(root, rel)
        if resolved is None:
            return None
        path = root / resolved
        if sep and not has_markdown_anchor(path, anchor):
            return None
        return body
    if ref.startswith("git:"):
        spec = ref.removeprefix("git:")
        result = git(root, ["rev-parse", "--verify", spec])
        if result.returncode == 0:
            return spec
        result = git(root, ["cat-file", "-e", spec])
        return spec if result.returncode == 0 else None
    if "://" in ref:
        return None
    return resolve_repo_path(root, ref)


def trace_ref_has_anchor(ref: str) -> bool:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return False
    body = ref.removeprefix("trace:")
    rel, sep, anchor = body.partition("#")
    return bool(rel and sep and anchor)


def trace_ref_path(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return None
    body = ref.removeprefix("trace:")
    rel, _sep, _anchor = body.partition("#")
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        return None
    normalized = posixpath.normpath(rel)
    return None if normalized == "." else normalized


def trace_ref_anchor(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return None
    body = ref.removeprefix("trace:")
    _rel, sep, anchor = body.partition("#")
    return anchor if sep and anchor else None


def canonical_trace_ref(ref: str) -> str | None:
    path = trace_ref_path(ref)
    anchor = trace_ref_anchor(ref)
    if not path or not anchor:
        return None
    return f"trace:{path}#{anchor}"


def is_search_set_trace_ref(ref: str) -> bool:
    return (
        trace_ref_has_anchor(ref)
        and trace_ref_path(ref) == ".harness/traces/search-set.md"
        and trace_ref_anchor(ref) in SEARCH_SET_TRACE_ANCHORS
    )


def is_search_set_trace_path_ref(ref: str) -> bool:
    return trace_ref_path(ref) == ".harness/traces/search-set.md"


def is_harness_trace_ref(ref: str) -> bool:
    path = trace_ref_path(ref)
    return bool(trace_ref_has_anchor(ref) and path and path.startswith(".harness/traces/"))


def is_claim_evidence_trace_ref(ref: str) -> bool:
    return is_harness_trace_ref(ref) and not is_search_set_trace_path_ref(ref)


def is_bucket_trace_ref(ref: str, bucket_name: str) -> bool:
    path = trace_ref_path(ref)
    return bool(
        trace_ref_has_anchor(ref)
        and path
        and path.startswith(f".harness/traces/{bucket_name}/")
    )


def is_raw_claim_file_ref(root: Path, ref: str) -> bool:
    resolved = resolve_ref(root, ref)
    if resolved is None:
        return False
    path = resolved.split("#", 1)[0]
    parts = {part.casefold() for part in Path(path).parts}
    suffix = Path(path).suffix.casefold()
    if suffix in RAW_CLAIM_EVIDENCE_DIRECT_SUFFIXES:
        return True
    if parts & RAW_CLAIM_EVIDENCE_PATH_PARTS and suffix in RAW_CLAIM_EVIDENCE_CONTEXTUAL_SUFFIXES:
        return True
    return False


def write_packet(path: Path, packet: dict, *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise PacketError(f"{path}: already exists; refusing to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump({PACKET_KEY: packet}, sort_keys=False, allow_unicode=False)
    path.write_text(text, encoding="utf-8")


def date_like(value: object, *, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none
    parsed = parsed_date(value)
    return parsed is not None and parsed <= dt.date.today()


def parsed_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def canonical_vacuous_value(value: str) -> str:
    normalized = " ".join(value.strip().strip("\"'").casefold().split())
    return re.sub(r"[^a-z0-9]+", "", normalized)


def required_targets(packet: dict) -> tuple[set[str], set[str]]:
    inference = packet["result"]["inference"]
    required_evidence = inference.get("required_evidence", [])
    required_review = inference.get("required_review", [])
    if not isinstance(required_evidence, list):
        required_evidence = []
    if not isinstance(required_review, list):
        required_review = []
    return (
        {item for item in required_evidence if isinstance(item, str)},
        {item for item in required_review if isinstance(item, str)},
    )


def checker_required_evidence(packet: dict) -> set[str]:
    meta = packet["meta"]
    inference = packet["result"]["inference"]
    evidence = packet["result"]["evidence"]
    mode = meta.get("mode")
    comparison_ref = evidence.get("comparison_ref")
    changed_paths = string_list_values(inference.get("changed_paths", []))
    changed = set(changed_paths)

    archive_changed = any(path.startswith("archive/v1/") for path in changed)
    release_gate_changed = bool({"scripts/verify-release.py", "scripts/check-v1-archive-boundary.py"} & changed)

    if release_gate_changed and mode == "base-ref" and comparison_ref:
        return {
            f"python3 scripts/verify-release.py --list --base-ref {comparison_ref} --skip-clean-worktree",
            f"python3 scripts/check-v1-archive-boundary.py --base-ref {comparison_ref}",
            "python3 -m unittest tests/test_v1_archive_boundary.py tests/test_verify_release.py",
        }

    required: set[str] = set()
    if archive_changed:
        if mode == "staged":
            required.add("python3 scripts/check-v1-archive-boundary.py --staged")
        elif mode == "base-ref" and comparison_ref:
            required.add(f"python3 scripts/check-v1-archive-boundary.py --base-ref {comparison_ref}")
        required.add("python3 scripts/verify-release.py")

    if mode == "staged":
        required.add("git diff --cached --check")
    elif mode == "base-ref" and comparison_ref and not required:
        required.add(f"git diff --check {comparison_ref}...HEAD")
    elif mode == "worktree":
        required.add("git diff --check")
    return required


def stable_required_evidence(packet: dict) -> tuple[set[str], list[str]]:
    evidence = packet["result"]["evidence"]
    required = checker_required_evidence(packet)
    boundary = evidence.get("evaluator_boundary")
    errors: list[str] = []
    if not isinstance(boundary, dict):
        return required, ["result.evidence.evaluator_boundary must be a mapping for stable packets"]
    commands = boundary.get("commands")
    if not isinstance(commands, list):
        return required, ["result.evidence.evaluator_boundary.commands must be a list for stable packets"]
    invalid_commands = [command for command in commands if not isinstance(command, str) or not command]
    boundary_required = {command for command in commands if isinstance(command, str) and command}
    if invalid_commands:
        errors.append("result.evidence.evaluator_boundary.commands must contain only non-empty strings")
    if boundary_required != required:
        errors.append(
            "result.evidence.evaluator_boundary.commands must match checker-derived required evidence: "
            f"{sorted(required)}"
        )
    return required, errors


def text_mentions_scope_boundary(path: str, text: str) -> bool:
    lowered_path = path.casefold()
    if path.startswith("archive/v1/"):
        return False
    if "multi-review" in lowered_path or "review" in lowered_path:
        return True
    if any(marker in lowered_path for marker in ("waiver", "downgrade", "not-required", "not_required")):
        return True
    if not path.endswith(".md"):
        return False
    text = text.casefold()
    return any(
        phrase in text
        for phrase in (
            "waiver",
            "downgrade",
            "not required",
            "deferred",
            "out of scope",
            "review-governance",
            "review governance",
        )
    )


def path_mentions_scope_boundary(root: Path, path: str) -> bool:
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return False
    return text_mentions_scope_boundary(path, text)


def path_mentions_scope_boundary_at_commit(root: Path, commit_ref: str, path: str) -> bool:
    text = git_text(root, commit_ref, path)
    return bool(text and text_mentions_scope_boundary(path, text))


def base_ref_content_refs(packet: dict) -> list[str] | None:
    meta = packet.get("meta", {})
    result = packet.get("result", {})
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    comparison_ref = evidence.get("comparison_ref")
    if isinstance(meta, dict) and meta.get("mode") == "base-ref" and isinstance(comparison_ref, str):
        return [comparison_ref, "HEAD"]
    return None


def path_mentions_scope_boundary_for_packet(root: Path, packet: dict, path: str) -> bool:
    content_refs = base_ref_content_refs(packet)
    if content_refs:
        return any(path_mentions_scope_boundary_at_commit(root, ref, path) for ref in content_refs)
    return path_mentions_scope_boundary(root, path)


def path_has_proof_like_claim_for_packet(root: Path, packet: dict, path: str) -> bool:
    content_refs = base_ref_content_refs(packet)
    if content_refs:
        return any(path_has_proof_like_claim_at_commit(root, ref, path) for ref in content_refs)
    return path_has_proof_like_claim(root, path)


def checker_required_review(packet: dict, *, root: Path = ROOT) -> set[str]:
    meta = packet.get("meta", {}) if isinstance(packet.get("meta"), dict) else {}
    result = packet.get("result", {})
    inference = result.get("inference", {}) if isinstance(result, dict) else {}
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    changed_paths = string_list_values(inference.get("changed_paths", []))
    required: set[str] = set()

    def scope_boundary_changed(path: str) -> bool:
        return path_mentions_scope_boundary_for_packet(root, packet, path)

    def proof_like_changed(path: str) -> bool:
        return path_has_proof_like_claim_for_packet(root, packet, path)

    archive_paths = [path for path in changed_paths if path.startswith("archive/v1/")]
    if archive_paths:
        required.update({"archive boundary", "full v1 archive fidelity"})
    protected_paths = [path for path in changed_paths if requires_review_for_path(path) and not path.startswith("archive/v1/")]
    if protected_paths:
        required.add("checker correctness")
    if inference.get("protected_boundary_changed") is True and not archive_paths:
        required.add("checker correctness")
    if inference.get("impact") == "high" and not required:
        required.add("checker correctness")

    if any(
        path.startswith(".githooks/")
        or path in {"scripts/verify-release.py", "scripts/check-v1-archive-boundary.py"}
        or "pre-commit" in path
        or "release" in path
        or "archive-boundary" in path
        or "stable" in path
        for path in changed_paths
    ):
        required.add("release integration")

    if any(
        path in {"MAINTENANCE.md", "README.md", "backlog/v2-roadmap.md"}
        or path == "scripts/check-v1-archive-boundary.py"
        or path.startswith("backlog/plans/")
        or path.startswith("core/")
        for path in changed_paths
    ):
        required.add("methodology fidelity")

    evidence_surfaces = (
        "source_ref",
        "source_refs",
        "artifact_ref",
        "artifact_refs",
        "trace_ref",
        "trace_refs",
        "review-provenance",
        "waiver-provenance",
        "acceptance-packets",
        "check-governance-acceptance",
        "governance_evidence",
    )
    if any(
        any(surface in path for surface in evidence_surfaces)
        and path != "backlog/fixtures/acceptance-packets/README.md"
        for path in changed_paths
    ):
        required.add("evidence auditability")

    if any(scope_boundary_changed(path) for path in changed_paths):
        required.add("scope boundary")

    if any(path.endswith(".md") and proof_like_changed(path) for path in changed_paths):
        required.add("claim evidence")

    evaluator_boundary = evidence.get("evaluator_boundary", {})
    if isinstance(evaluator_boundary, dict):
        status = evaluator_boundary.get("status")
        if status is not None and status != "unchanged":
            required.add("evaluator boundary")

    return required


def sorted_key_names(keys: object) -> list[str]:
    return sorted(str(key) for key in keys)


def schema_field_errors(record: dict, expected_fields: set[str], *, source: str, label: str) -> list[str]:
    string_keys = {key for key in record if isinstance(key, str)}
    errors: list[str] = []
    missing = sorted(expected_fields - string_keys)
    extra = sorted_key_names(key for key in record if not isinstance(key, str) or key not in expected_fields)
    if missing:
        errors.append(f"{source}: {label} missing fields: {missing}")
    if extra:
        errors.append(f"{source}: {label} extra fields: {extra}")
    return errors


def target_entries(record: dict, fields: tuple[str, ...], *, source: str, errors: list[str]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for field in fields:
        if field not in record:
            continue
        value = record.get(field)
        if review_value_is_substantive_string(value):
            targets.append((field, value))
        else:
            errors.append(f"{source}: target field {field} must be a substantive string")
    return targets


def exception_target(record: dict, *, source: str, errors: list[str]) -> tuple[str, str] | None:
    targets = target_entries(record, TARGET_FIELDS, source=source, errors=errors)
    if len(targets) != 1:
        return None
    return targets[0]


def target_allowed(
    field: str,
    target: str,
    required_evidence: set[str],
    required_review: set[str],
    *,
    kind: str | None = None,
) -> bool:
    if field == "evidence":
        return target in required_evidence
    if field == "review":
        return target in required_review
    if kind == "evidence":
        return target in required_evidence
    if kind == "review":
        return target in required_review
    return target in required_evidence or target in required_review


def validate_provenance_record(record: dict, *, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: judgment record must be a mapping"]
    for field in ("actor", "role", "reason", "source_ref"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} is required")
    if not record.get("date"):
        errors.append(f"{source}: date is required")
    elif not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    return errors


def residual_risk_target(record: dict, *, source: str, errors: list[str]) -> tuple[str, str] | None:
    targets = target_entries(record, ("evidence", "review"), source=source, errors=errors)
    if len(targets) != 1:
        return None
    return targets[0]


def validate_residual_risk_record(
    record: dict,
    *,
    required_evidence: set[str],
    required_review: set[str],
    source: str,
) -> list[str]:
    errors = validate_provenance_record(record, source=source)
    if errors and not isinstance(record, dict):
        return errors
    for forbidden in ("from", "to"):
        if forbidden in record:
            errors.append(f"{source}: residual risk cannot include {forbidden}")
    target = residual_risk_target(record, source=source, errors=errors)
    if target is None:
        errors.append(f"{source}: residual risk must target exactly one required evidence/review item")
        return errors
    field, value = target
    required = required_evidence if field == "evidence" else required_review
    if value not in required:
        errors.append(f"{source}: residual risk target is not required: {value}")
    return errors


def mapping_records(value: object, *, source: str, errors: list[str]) -> list[dict]:
    if not isinstance(value, list):
        errors.append(f"{source} must be a list")
        return []
    records: list[dict] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{source}[{index}] must be a mapping")
            continue
        records.append(item)
    return records


def validate_review_record(record: dict, *, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: review record must be a mapping"]
    for field in REVIEW_PROVENANCE_FIELDS:
        if not record.get(field):
            errors.append(f"{source}: {field} is required")
    if record.get("date") and not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    if not record.get("critic"):
        errors.append(f"{source}: critic is required")
    return errors


def validate_exception_record(
    record: dict,
    *,
    required_evidence: set[str],
    required_review: set[str],
    source: str,
    record_type: str = "exception",
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_provenance_record(record, source=source))
    if errors and not isinstance(record, dict):
        return errors
    target = exception_target(record, source=source, errors=errors)
    if target is None:
        errors.append(f"{source}: exception must target exactly one required evidence/review item")
        return errors
    field, value = target
    kind = record.get("kind")
    if kind is not None and not isinstance(kind, str):
        errors.append(f"{source}: exception kind must be evidence or review")
        return errors
    if record_type == "waiver":
        for forbidden in ("from", "to"):
            if forbidden in record:
                errors.append(f"{source}: waiver cannot include {forbidden}")
    if record_type == "downgrade" and field != "from":
        errors.append(f"{source}: downgrade must target from")
        return errors
    if record_type == "waiver" and field == "from":
        errors.append(f"{source}: waiver must target evidence or review")
        return errors
    if field == "from":
        if kind not in {"evidence", "review"}:
            errors.append(f"{source}: downgrade kind must be evidence or review")
        elif not target_allowed(field, value, required_evidence, required_review, kind=kind):
            errors.append(f"{source}: {kind} downgrade target is not required: {value}")
        replacement = record.get("to")
        if not review_value_is_substantive_string(replacement):
            errors.append(f"{source}: downgrade to is required")
        elif replacement == value:
            errors.append(f"{source}: downgrade to must differ from from")
        return errors
    if field == "review":
        if kind != "review":
            errors.append(f"{source}: review waiver kind must be review")
    elif kind and kind != "evidence":
        errors.append(f"{source}: evidence waiver kind must be evidence")
    if not target_allowed(field, value, required_evidence, required_review):
        errors.append(f"{source}: exception target is not required: {value}")
    return errors


def validate_resolved_ref_record(record: dict, *, root: Path, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: resolved ref record must be a mapping"]
    for field in REQUIRED_RESOLVED_REF_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{source}: {field} is required")
    if errors:
        return errors
    if record["origin"] not in RESOLVED_REF_ORIGINS:
        errors.append(f"{source}: origin must be input or generated")
    if record["relation"] not in RESOLVED_REF_RELATIONS:
        errors.append(f"{source}: relation is invalid: {record['relation']}")
    if record["relation"] == "artifact" and not str(record["ref"]).startswith("file:"):
        errors.append(f"{source}: artifact refs must use file: scheme")
    if record["relation"] == "trace":
        if not str(record["ref"]).startswith("trace:"):
            errors.append(f"{source}: trace refs must use trace: scheme")
        elif not trace_ref_has_anchor(record["ref"]):
            errors.append(f"{source}: trace refs must include an anchor")
    if record["relation"] == "source" and str(record["ref"]).startswith("trace:"):
        if not trace_ref_has_anchor(record["ref"]):
            errors.append(f"{source}: trace source refs must include an anchor")
    if record["relation"] == "source" and str(record["ref"]).startswith("git:"):
        source_path = git_source_ref_path(root, record["ref"])
        if source_path is None:
            errors.append(f"{source}: git source refs must use git:<full-commit-sha>:<repo-path> form")
        elif git_resolved_target_path(record["target"]) != source_path:
            errors.append(f"{source}: git source target must expose repo path: {record['ref']}")
    if (
        record["origin"] == "generated"
        and record["relation"] == "claim-evidence"
        and not str(record["ref"]).startswith(("file:", "trace:"))
    ):
        errors.append(f"{source}: generated claim-evidence refs must use file: or trace: scheme")
    if (
        record["origin"] == "generated"
        and record["relation"] in {"review-provenance", "waiver-provenance"}
        and not str(record["ref"]).startswith("file:")
    ):
        errors.append(f"{source}: generated {record['relation']} refs must use file: scheme")
    resolved = resolve_ref(root, record["ref"])
    if record["status"] == "resolved":
        if resolved is None:
            errors.append(f"{source}: resolved ref does not resolve: {record['ref']}")
        elif record["target"] != resolved:
            errors.append(f"{source}: target does not match resolved ref: {record['ref']}")
    elif record["status"] == "local-placeholder":
        if not str(record["ref"]).startswith("terminal:") or record["relation"] != "observation":
            errors.append(f"{source}: local-placeholder is only valid for terminal observation refs")
    else:
        errors.append(f"{source}: status must be resolved or local-placeholder")
    return errors


def resolved_ref_index(records: list[dict]) -> dict[tuple[str, str], list[dict]]:
    index: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        if (
            isinstance(record, dict)
            and isinstance(record.get("relation"), str)
            and isinstance(record.get("ref"), str)
        ):
            index.setdefault((record.get("relation"), record.get("ref")), []).append(record)
    return index


def has_resolved_relation(
    index: dict[tuple[str, str], list[dict]],
    *,
    relation: str,
    ref: str,
    origin: str | None = None,
) -> bool:
    if not isinstance(ref, str):
        return False
    return any(
        record.get("status") == "resolved" and (origin is None or record.get("origin") == origin)
        for record in index.get((relation, ref), [])
    )


def command_base_ref(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    if "--base-ref" in parts:
        index = parts.index("--base-ref")
        if index + 1 < len(parts):
            return parts[index + 1]
    for part in parts:
        if part.startswith("--base-ref="):
            return part.split("=", 1)[1]
        if "...HEAD" in part:
            return part.split("...HEAD", 1)[0]
    return None


def artifact_text(root: Path, artifact_ref: str) -> str | None:
    if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
        return None
    resolved = resolve_ref(root, artifact_ref)
    if resolved is None:
        return None
    try:
        return (root / resolved).read_text(encoding="utf-8")
    except OSError:
        return None


def artifact_has_field(text: str, field: str, value: str) -> bool:
    return any(line.strip() == f"{field}: {value}" for line in text.splitlines())


def field_section_records_values(text: str, expected: dict[str, str]) -> bool:
    normalized_expected = {
        field: normalize_review_field(value) for field, value in expected.items()
    }
    return any(
        all(section.get(field) == value for field, value in normalized_expected.items())
        for section in markdown_field_sections(text)
    )


def command_evidence_sections_exact(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    return [
        command_evidence_section_fields(lines, start, end)
        for start, end in command_evidence_section_bounds(lines)
        if not command_evidence_section_duplicate_fields(lines, start, end)
    ]


def command_evidence_section_bounds(lines: list[str]) -> list[tuple[int, int]]:
    starts = [index for index, line in enumerate(lines) if line.strip() == COMMAND_EVIDENCE_HEADING]
    headings = [index for index, line in enumerate(lines) if line.lstrip().startswith("#")]
    bounds: list[tuple[int, int]] = []
    for start in starts:
        end = next((heading for heading in headings if heading > start), len(lines))
        bounds.append((start, end))
    return bounds


def command_evidence_section_fields(lines: list[str], start: int, end: int) -> dict[str, str]:
    fields: dict[str, str] = {}
    for index in range(start + 1, end):
        match = COMMAND_EVIDENCE_FIELD_RE.match(lines[index])
        if match:
            key = match.group(1).casefold().replace("-", "_")
            fields[key] = match.group(2)
    return fields


def command_evidence_section_duplicate_fields(lines: list[str], start: int, end: int) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for index in range(start + 1, end):
        match = COMMAND_EVIDENCE_FIELD_RE.match(lines[index])
        if not match:
            continue
        key = match.group(1).casefold().replace("-", "_")
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return duplicates


def command_evidence_record_error(
    text: str,
    *,
    identity: dict[str, str],
    status: str,
) -> str | None:
    lines = text.splitlines()
    matching_sections: list[dict[str, str]] = []
    duplicate_matches: list[set[str]] = []
    for start, end in command_evidence_section_bounds(lines):
        section = command_evidence_section_fields(lines, start, end)
        if not all(section.get(field) == value for field, value in identity.items()):
            continue
        duplicates = command_evidence_section_duplicate_fields(lines, start, end)
        if duplicates:
            duplicate_matches.append(duplicates)
            continue
        matching_sections.append(section)
    if duplicate_matches:
        duplicate_fields = sorted({field for fields in duplicate_matches for field in fields})
        return f"duplicate fields in matching # Command Evidence section: {duplicate_fields}"
    if not matching_sections:
        return "missing matching # Command Evidence section"
    if len(matching_sections) > 1:
        return "ambiguous # Command Evidence sections for packet/ref/command identity"
    recorded_status = matching_sections[0].get("status")
    if recorded_status != status:
        return f"# Command Evidence status mismatch: expected {status}, got {recorded_status}"
    return None


def artifact_command_evidence_error(
    root: Path,
    artifact_ref: str,
    command: str,
    status: str,
    *,
    packet_id: str,
    packet_ref: str,
    packet_sha256: str,
) -> str | None:
    text = artifact_text(root, artifact_ref)
    if text is None:
        return "command evidence artifact could not be read"
    return command_evidence_record_error(
        text,
        identity={
            "packet_id": packet_id,
            "packet_ref": packet_ref,
            "packet_sha256": packet_sha256,
            "command": command,
        },
        status=status,
    )


def multiple_required_closure_errors(
    required_targets: set[str],
    closures: list[tuple[str, list[str] | set[str]]],
    *,
    kind: str,
) -> list[str]:
    errors: list[str] = []
    for target in sorted(required_targets):
        labels = [
            label
            for label, targets in closures
            for value in targets
            if value == target
        ]
        if len(labels) > 1:
            errors.append(
                f"stable packet required {kind} has multiple closures: {target} via {', '.join(labels)}"
            )
    return errors


def ref_text(root: Path, ref: str) -> str | None:
    resolved = resolve_ref(root, ref)
    if resolved is None or ref.startswith("git:"):
        return None
    if "#" in resolved:
        resolved = resolved.split("#", 1)[0]
    try:
        return (root / resolved).read_text(encoding="utf-8")
    except OSError:
        return None


def ref_is_acceptance_packet(root: Path, ref: str) -> bool:
    text = ref_text(root, ref)
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        return False
    return isinstance(loaded, dict) and PACKET_KEY in loaded


def normalize_review_field(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dt.date):
        return value.isoformat()
    return canonical_vacuous_value(str(value))


def review_value_is_substantive(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return normalize_review_field(value) not in VACUOUS_REVIEW_VALUES
    if isinstance(value, dt.date):
        return True
    if isinstance(value, list):
        return any(review_value_is_substantive(item) for item in value)
    if isinstance(value, dict):
        return any(review_value_is_substantive(item) for item in value.values())
    return True


def review_value_is_substantive_string(value: object) -> bool:
    return isinstance(value, str) and review_value_is_substantive(value)


def sorted_string_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if isinstance(value, str) and value})


def string_list_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str)]


def canonical_json_bytes(value: object) -> bytes:
    def normalize(item: object) -> object:
        if isinstance(item, dt.datetime):
            return item.date().isoformat()
        if isinstance(item, dt.date):
            return item.isoformat()
        if isinstance(item, dict):
            return {str(key): normalize(item[key]) for key in sorted(item, key=lambda key: repr(key))}
        if isinstance(item, list):
            return [normalize(element) for element in item]
        return item

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def review_target_context(packet: dict, *, root: Path, packet_ref: str | None) -> dict:
    meta = packet["meta"]
    input_data = packet["input"]
    result = packet["result"]
    inference = result["inference"]
    evidence = result["evidence"]
    evaluator_boundary = evidence.get("evaluator_boundary", {})
    commands = evaluator_boundary.get("commands") if isinstance(evaluator_boundary, dict) else []
    return {
        "packet_id": meta.get("packet_id"),
        "schema_version": meta.get("schema_version"),
        "lifecycle": meta.get("lifecycle"),
        "mode": meta.get("mode"),
        "packet_ref": packet_ref or "",
        "input": {
            "intent": input_data.get("intent"),
            "actor": input_data.get("actor"),
            "source_refs": sorted_string_values(input_data.get("source_refs")),
        },
        "inference": {
            "change_class": inference.get("change_class"),
            "impact": inference.get("impact"),
            "changed_paths": sorted_string_values(inference.get("changed_paths")),
            "intended_scope": inference.get("intended_scope"),
            "actual_scope": inference.get("actual_scope"),
            "deviations": sorted_string_values(inference.get("deviations")),
            "isolation": inference.get("isolation"),
            "protected_boundary_changed": inference.get("protected_boundary_changed"),
            "required_evidence": sorted_string_values(inference.get("required_evidence")),
            "required_review": sorted(checker_required_review(packet, root=root)),
        },
        "evidence": {
            "baseline_ref": evidence.get("baseline_ref"),
            "comparison_ref": evidence.get("comparison_ref"),
            "evaluator_boundary_commands": sorted_string_values(commands),
            "source_refs": sorted_string_values(evidence.get("source_refs")),
        },
    }


def review_target_digest(packet: dict, *, root: Path, packet_ref: str | None) -> str:
    return hashlib.sha256(canonical_json_bytes(review_target_context(packet, root=root, packet_ref=packet_ref))).hexdigest()


def review_lineage_digest(lineage: list[dict]) -> str:
    return hashlib.sha256(canonical_json_bytes(lineage)).hexdigest()


def passing_required_critic_evidence(multi_review: dict) -> set[str]:
    evidence: set[str] = set()
    critics = multi_review.get("critics", [])
    if not isinstance(critics, list):
        return evidence
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        if critic.get("required") is not True:
            continue
        if critic.get("verdict") != "pass" or critic.get("veto") is not False:
            continue
        score = critic.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 9:
            continue
        for item in critic.get("evidence", []):
            if isinstance(item, str):
                evidence.add(item)
    return evidence


def review_target_binding(packet: dict, *, root: Path, packet_ref: str | None) -> dict:
    result = packet["result"]
    evidence = result["evidence"]
    inference = result["inference"]
    return {
        "packet_id": packet["meta"].get("packet_id"),
        "packet_ref": packet_ref or "",
        "review_target_digest": review_target_digest(packet, root=root, packet_ref=packet_ref),
        "baseline_ref": evidence.get("baseline_ref"),
        "comparison_ref": evidence.get("comparison_ref"),
        "source_refs": sorted_string_values(packet["input"].get("source_refs")),
        "changed_paths": sorted_string_values(inference.get("changed_paths")),
        "required_review": sorted(checker_required_review(packet, root=root)),
    }


def multi_review_target_matches_binding(multi_review: dict, binding: dict) -> list[str]:
    errors: list[str] = []
    target = multi_review.get("target")
    if not isinstance(target, dict):
        return ["imported MultiReviewResult target must be a mapping"]
    source_refs = target.get("source_refs")
    if not isinstance(source_refs, list) or any(not isinstance(ref, str) for ref in source_refs):
        return ["imported MultiReviewResult target.source_refs must be a list of strings"]
    required_refs = [binding.get("packet_ref")]
    missing_refs = sorted(ref for ref in required_refs if isinstance(ref, str) and ref and ref not in source_refs)
    if missing_refs:
        errors.append(f"imported MultiReviewResult target.source_refs must include current packet ref: {missing_refs}")
    return errors


def markdown_field_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    field_re = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$")
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                sections.append(current)
            current = {}
            continue
        if current is None:
            continue
        match = field_re.match(line)
        if match:
            key = match.group(1).casefold().replace("-", "_")
            current[key] = normalize_review_field(match.group(2))
    if current:
        sections.append(current)
    return sections


def review_source_ref_records_review(root: Path, ref: str, review: dict, *, packet_id: str) -> bool:
    text = ref_text(root, ref)
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        loaded = None
    if isinstance(loaded, dict) and REVIEW_IMPORT_KEY in loaded:
        wrapper = loaded.get(REVIEW_IMPORT_KEY)
        if not isinstance(wrapper, dict):
            return False
        binding = wrapper.get("target_binding") if isinstance(wrapper.get("target_binding"), dict) else {}
        if normalize_review_field(binding.get("packet_id", "")) != normalize_review_field(packet_id):
            return False
        lineage = wrapper.get("review_lineage", [])
        if not isinstance(lineage, list):
            return False
        for record in lineage:
            if not isinstance(record, dict):
                continue
            if review.get("review_id") and record.get("review_id") != review.get("review_id"):
                continue
            expected = {
                "critic": normalize_review_field(review.get("critic", "")),
                "actor": normalize_review_field(review.get("actor", "")),
                "role": normalize_review_field(review.get("role", "")),
                "date": normalize_review_field(review.get("date", "")),
                "score": normalize_review_field(review.get("score", "")),
                "veto": normalize_review_field(review.get("veto", "")),
            }
            if any(not value for value in expected.values()):
                return False
            if all(normalize_review_field(record.get(field, "")) == value for field, value in expected.items()):
                return True
        return False
    expected = {
        "record_type": "governance-review",
        "packet_id": normalize_review_field(packet_id),
        "critic": normalize_review_field(review.get("critic", "")),
        "actor": normalize_review_field(review.get("actor", "")),
        "role": normalize_review_field(review.get("role", "")),
        "date": normalize_review_field(review.get("date", "")),
        "score": normalize_review_field(review.get("score", "")),
        "veto": normalize_review_field(review.get("veto", "")),
    }
    if any(not value for value in expected.values()):
        return False
    for field in ("why_not_10", "disposition"):
        if review.get(field):
            expected[field] = normalize_review_field(review[field])
    return any(all(section.get(field) == value for field, value in expected.items()) for section in markdown_field_sections(text))


def local_ref_path(root: Path, ref: str) -> Path | None:
    resolved = resolve_ref(root, ref)
    if resolved is None or ref.startswith("git:"):
        return None
    if "#" in resolved:
        resolved = resolved.split("#", 1)[0]
    path = (root / resolved).resolve()
    root_resolved = root.resolve()
    if path != root_resolved and root_resolved not in path.parents:
        return None
    return path if path.is_file() else None


def load_review_import_wrapper(root: Path, source_ref: str) -> tuple[dict | None, list[str]]:
    path = local_ref_path(root, source_ref)
    if path is None:
        return None, [f"review import source_ref does not resolve to a local file: {source_ref}"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"cannot read review import source_ref {source_ref}: {exc}"]
    try:
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        return None, [f"invalid review import artifact syntax: {source_ref}: {exc}"]
    if not isinstance(loaded, dict) or REVIEW_IMPORT_KEY not in loaded:
        return None, [f"review import artifact missing {REVIEW_IMPORT_KEY}: {source_ref}"]
    wrapper = loaded[REVIEW_IMPORT_KEY]
    if not isinstance(wrapper, dict):
        return None, [f"{REVIEW_IMPORT_KEY} must be a mapping: {source_ref}"]
    return wrapper, []


def derive_multi_review_result(
    root: Path,
    result: dict,
    *,
    result_ref: str | None = None,
    result_digest: str | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> tuple[str, list[str]]:
    script = ROOT / "scripts" / "check-multi-review-result.py"
    spec = importlib.util.spec_from_file_location("check_multi_review_result_for_acceptance", script)
    if spec is None or spec.loader is None:
        return "VETO", [f"cannot load multi-review validator: {script}"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_root = getattr(module, "ROOT", None)
    module.ROOT = root
    try:
        return module.derive_verdict(
            result,
            result_ref=result_ref,
            result_digest=result_digest,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
        )
    finally:
        if original_root is not None:
            module.ROOT = original_root


def review_lineage_ids(lineage: list[dict]) -> list[str]:
    return [str(record.get("review_id")) for record in lineage if isinstance(record, dict) and record.get("review_id")]


def finding_ids(record: dict) -> set[str]:
    ids: set[str] = set()
    findings = record.get("blocking_findings", [])
    if not isinstance(findings, list):
        return ids
    for finding in findings:
        if isinstance(finding, dict) and review_value_is_substantive(finding.get("finding_id")):
            ids.add(str(finding["finding_id"]))
        elif isinstance(finding, str) and review_value_is_substantive(finding):
            ids.add(markdown_anchor(finding))
    return ids


def review_is_blocking(record: dict) -> bool:
    score = record.get("score")
    return record.get("veto") is True or not isinstance(score, (int, float)) or score < 9 or bool(record.get("blocking_findings"))


def review_is_open_passing(record: dict, closed_blocking_ids: set[str]) -> bool:
    if record.get("review_id") in closed_blocking_ids:
        return False
    score = record.get("score")
    return isinstance(score, (int, float)) and score >= 9 and record.get("veto") is False and not record.get("blocking_findings")


def normalize_for_mirror(value: object) -> object:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize_for_mirror(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_for_mirror(value[key]) for key in sorted(value, key=lambda item: repr(item))}
    return value


def validate_review_lineage_record(record: object, *, source: str, import_source_ref: str, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: review lineage record must be a mapping"]
    errors.extend(schema_field_errors(record, REVIEW_LINEAGE_FIELDS, source=source, label="review lineage"))
    for field in ("review_id", "critic", "scope", "anti_scope", "actor", "role", "source_ref"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} is required")
    if record.get("source_ref") != import_source_ref:
        errors.append(f"{source}: source_ref must match review import source_ref: {import_source_ref}")
    if not date_like(record.get("date")):
        errors.append(f"{source}: date must be an ISO date")
    score = record.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 10:
        errors.append(f"{source}: score must be an integer from 1 to 10")
    if not isinstance(record.get("veto"), bool):
        errors.append(f"{source}: veto must be a boolean")
    for field in ("false_green_risk", "invariant_checked"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} must be substantive")
    evidence_items = record.get("evidence")
    if not isinstance(evidence_items, list) or not evidence_items:
        errors.append(f"{source}: evidence must be a non-empty substantive list")
    else:
        for index, item in enumerate(evidence_items):
            if not review_value_is_substantive_string(item):
                errors.append(f"{source}: evidence[{index}] must be a substantive string")
    source_refs = record.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append(f"{source}: source_refs must be a non-empty list")
    else:
        for index, ref in enumerate(source_refs):
            if not isinstance(ref, str) or not review_value_is_substantive(ref):
                errors.append(f"{source}: source_refs[{index}] must be a non-empty string")
            elif ref.startswith("trace:") and not trace_ref_has_anchor(ref):
                errors.append(f"{source}: source_refs[{index}] trace refs must include an anchor")
            elif resolve_ref(root, ref) is None:
                errors.append(f"{source}: source_refs[{index}] does not resolve: {ref}")
    if not isinstance(record.get("blocking_findings"), list):
        errors.append(f"{source}: blocking_findings must be a list")
    else:
        seen_finding_ids: set[str] = set()
        for index, finding in enumerate(record["blocking_findings"]):
            if not isinstance(finding, dict):
                errors.append(f"{source}: blocking_findings[{index}] must be a mapping with finding_id and summary")
                continue
            finding_id = finding.get("finding_id")
            if not review_value_is_substantive_string(finding_id):
                errors.append(f"{source}: blocking_findings[{index}].finding_id is required")
            elif finding_id in seen_finding_ids:
                errors.append(f"{source}: duplicate blocking finding_id: {finding_id}")
            else:
                seen_finding_ids.add(finding_id)
            if not review_value_is_substantive_string(finding.get("summary")):
                errors.append(f"{source}: blocking_findings[{index}].summary is required")
    if review_is_blocking(record) and not finding_ids(record):
        errors.append(f"{source}: blocking review requires blocking_findings with stable finding_id values")
    if score == 9:
        if not review_value_is_substantive_string(record.get("why_not_10")):
            errors.append(f"{source}: score 9 requires why_not_10")
        if not review_value_is_substantive_string(record.get("disposition")):
            errors.append(f"{source}: score 9 requires disposition")
    fixed = record.get("fixed_finding_ids")
    if not isinstance(fixed, list):
        errors.append(f"{source}: fixed_finding_ids must be a list")
    elif any(not isinstance(item, str) or not review_value_is_substantive(item) for item in fixed):
        errors.append(f"{source}: fixed_finding_ids must contain only substantive string ids")
    elif len(fixed) != len(set(fixed)):
        errors.append(f"{source}: fixed_finding_ids must not contain duplicates")
    rerun_of = record.get("rerun_of")
    if rerun_of is not None:
        if not review_value_is_substantive_string(rerun_of):
            errors.append(f"{source}: rerun_of must be a review_id string")
        if not fixed:
            errors.append(f"{source}: rerun requires fixed_finding_ids")
    elif fixed:
        errors.append(f"{source}: fixed_finding_ids require rerun_of")
    return errors


def validate_review_lineage_closure(lineage: list[dict], *, source: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    by_id: dict[str, dict] = {}
    index_by_id: dict[str, int] = {}
    for index, record in enumerate(lineage):
        review_id = record.get("review_id") if isinstance(record, dict) else None
        if not isinstance(review_id, str) or not review_id:
            continue
        if review_id in by_id:
            errors.append(f"{source}: duplicate review_id: {review_id}")
        by_id[review_id] = record
        index_by_id[review_id] = index

    closed_blocking_ids: set[str] = set()
    for index, record in enumerate(lineage):
        if not isinstance(record, dict) or not record.get("rerun_of"):
            continue
        rerun_id = record.get("review_id")
        target_id = record.get("rerun_of")
        if not isinstance(rerun_id, str) or not isinstance(target_id, str):
            continue
        target = by_id.get(target_id)
        if target is None:
            errors.append(f"{source}: rerun {rerun_id} references missing review_id: {target_id}")
            continue
        if index_by_id.get(target_id, len(lineage)) >= index:
            errors.append(f"{source}: rerun {rerun_id} must appear after rerun_of review: {target_id}")
            continue
        if not review_is_blocking(target):
            errors.append(f"{source}: rerun {rerun_id} references nonblocking review: {target_id}")
            continue
        if record.get("critic") != target.get("critic"):
            errors.append(f"{source}: rerun {rerun_id} must use same critic as {target_id}")
        if not review_is_open_passing(record, set()):
            errors.append(f"{source}: rerun {rerun_id} must be score >= 9, veto false, and nonblocking")
            continue
        target_findings = finding_ids(target)
        fixed_values = record.get("fixed_finding_ids", [])
        if not isinstance(fixed_values, list) or any(not isinstance(item, str) for item in fixed_values):
            continue
        fixed = set(fixed_values)
        if not target_findings:
            errors.append(f"{source}: rerun target {target_id} has no stable finding ids")
            continue
        if fixed != target_findings:
            errors.append(f"{source}: rerun {rerun_id} fixed_finding_ids must exactly cover {target_id}: {sorted(target_findings)}")
            continue
        rerun_date = parsed_date(record.get("date"))
        target_date = parsed_date(target.get("date"))
        if rerun_date is not None and target_date is not None and rerun_date < target_date:
            errors.append(f"{source}: rerun {rerun_id} date must not precede rerun_of review date: {target_id}")
            continue
        if target_id in closed_blocking_ids:
            errors.append(f"{source}: multiple reruns close review_id: {target_id}")
            continue
        closed_blocking_ids.add(target_id)

    for record in lineage:
        if not isinstance(record, dict):
            continue
        review_id = record.get("review_id")
        if review_is_blocking(record) and review_id not in closed_blocking_ids:
            errors.append(f"{source}: unclosed blocking review: {review_id}")

    open_passing = [
        record["critic"]
        for record in lineage
        if isinstance(record, dict)
        and isinstance(record.get("critic"), str)
        and review_is_open_passing(record, closed_blocking_ids)
    ]
    return open_passing, errors


def validate_review_imports(
    packet: dict,
    *,
    root: Path,
    packet_ref: str | None,
    packet_sha256: str | None,
    ref_index: dict[tuple[str, str], list[dict]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    evidence = packet["result"]["evidence"]
    packet_reviews_raw = packet["result"]["judgment"].get("reviews", [])
    packet_reviews = packet_reviews_raw if isinstance(packet_reviews_raw, list) else []
    imports = evidence.get("review_imports", [])
    if not isinstance(imports, list):
        return [], ["result.evidence.review_imports must be a list"]
    if packet_reviews and not imports:
        return [], ["stable packet reviews require result.evidence.review_imports"]

    expected_binding = review_target_binding(packet, root=root, packet_ref=packet_ref)
    imported_source_refs: set[str] = set()
    imported_lineage_by_id: dict[str, dict] = {}
    open_passing_reviews: list[str] = []
    for import_index, import_record in enumerate(imports):
        source = f"result.evidence.review_imports[{import_index}]"
        if not isinstance(import_record, dict):
            errors.append(f"{source}: review import must be a mapping")
            continue
        errors.extend(schema_field_errors(import_record, REVIEW_IMPORT_RECORD_FIELDS, source=source, label="review import"))
        source_ref = import_record.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref:
            errors.append(f"{source}: source_ref is required")
            continue
        imported_source_refs.add(source_ref)
        if import_record.get("format") != REVIEW_IMPORT_SCHEMA_VERSION:
            errors.append(f"{source}: format must be {REVIEW_IMPORT_SCHEMA_VERSION}")
        if import_record.get("status") != "imported":
            errors.append(f"{source}: status must be imported")
        if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref, origin="generated"):
            errors.append(f"{source}: source_ref lacks resolved review-provenance relation with generated origin: {source_ref}")
        if ref_is_acceptance_packet(root, source_ref):
            errors.append(f"{source}: review import source_ref cannot be an acceptance packet: {source_ref}")
        path = local_ref_path(root, source_ref)
        if path is None:
            errors.append(f"{source}: source_ref does not resolve to a local file: {source_ref}")
            continue
        digest = file_sha256(path)
        if import_record.get("source_digest") != digest:
            errors.append(f"{source}: source_digest does not match current artifact bytes: {source_ref}")

        binding = import_record.get("target_binding")
        if not isinstance(binding, dict) or set(binding) != TARGET_BINDING_FIELDS:
            errors.append(f"{source}: target_binding fields must be exactly {sorted(TARGET_BINDING_FIELDS)}")
        elif normalize_for_mirror(binding) != normalize_for_mirror(expected_binding):
            errors.append(f"{source}: target_binding does not match current packet review target")

        wrapper, wrapper_errors = load_review_import_wrapper(root, source_ref)
        errors.extend(f"{source}: {item}" for item in wrapper_errors)
        if wrapper is None:
            continue
        errors.extend(schema_field_errors(wrapper, REVIEW_IMPORT_FIELDS, source=source, label="wrapper"))
        if wrapper.get("schema_version") != REVIEW_IMPORT_SCHEMA_VERSION:
            errors.append(f"{source}: wrapper schema_version must be {REVIEW_IMPORT_SCHEMA_VERSION}")
        wrapper_binding = wrapper.get("target_binding")
        if not isinstance(wrapper_binding, dict) or set(wrapper_binding) != TARGET_BINDING_FIELDS:
            errors.append(f"{source}: wrapper target_binding fields must be exactly {sorted(TARGET_BINDING_FIELDS)}")
        elif normalize_for_mirror(wrapper_binding) != normalize_for_mirror(expected_binding):
            errors.append(f"{source}: wrapper target_binding does not match current packet review target")
        if isinstance(binding, dict) and isinstance(wrapper_binding, dict) and normalize_for_mirror(binding) != normalize_for_mirror(wrapper_binding):
            errors.append(f"{source}: packet import target_binding must match wrapper target_binding")

        multi_review = wrapper.get("MultiReviewResult")
        if not isinstance(multi_review, dict):
            errors.append(f"{source}: wrapper MultiReviewResult must be a mapping")
        else:
            expected_packet_ref = wrapper_binding.get("packet_ref") if isinstance(wrapper_binding, dict) else packet_ref
            target_binding = wrapper_binding if isinstance(wrapper_binding, dict) else expected_binding
            for item in multi_review_target_matches_binding(multi_review, target_binding):
                errors.append(f"{source}: {item}")
            derived, derived_errors = derive_multi_review_result(
                root,
                multi_review,
                result_ref=source_ref,
                result_digest=digest,
                packet_ref=expected_packet_ref,
                packet_sha256=packet_sha256,
            )
            if derived != "PASS":
                errors.append(f"{source}: imported MultiReviewResult must freshly derive governance PASS: {derived}")
            for item in derived_errors:
                errors.append(f"{source}: imported MultiReviewResult error: {item}")

        lineage = wrapper.get("review_lineage")
        if not isinstance(lineage, list) or not lineage:
            errors.append(f"{source}: review_lineage must be a non-empty list")
            continue
        for index, record in enumerate(lineage):
            errors.extend(
                validate_review_lineage_record(
                    record,
                    source=f"{source}.review_lineage[{index}]",
                    import_source_ref=source_ref,
                    root=root,
                )
            )
        ids = review_lineage_ids(lineage)
        if len(ids) != len(set(ids)):
            errors.append(f"{source}: review_lineage contains duplicate review_id values")
        review_ids = import_record.get("review_ids")
        if not isinstance(review_ids, list):
            errors.append(f"{source}: review_ids must match imported review_lineage ids")
        elif any(not isinstance(review_id, str) for review_id in review_ids):
            errors.append(f"{source}: review_ids must contain only strings")
        elif sorted(review_ids) != sorted(ids):
            errors.append(f"{source}: review_ids must match imported review_lineage ids")
        lineage_digest_marker = f"review_lineage_sha256:{review_lineage_digest(lineage)}"
        if not isinstance(multi_review, dict) or lineage_digest_marker not in passing_required_critic_evidence(multi_review):
            errors.append(
                f"{source}: review_lineage digest must be represented by a passing required MultiReviewResult critic: {lineage_digest_marker}"
            )
        for record in lineage:
            if isinstance(record, dict) and isinstance(record.get("review_id"), str):
                review_id = record["review_id"]
                if review_id in imported_lineage_by_id:
                    errors.append(f"{source}: duplicate imported review_id across imports: {review_id}")
                imported_lineage_by_id[review_id] = record
        passing, closure_errors = validate_review_lineage_closure(lineage, source=source)
        open_passing_reviews.extend(passing)
        errors.extend(closure_errors)

    packet_reviews_by_id: dict[str, dict] = {}
    for index, review in enumerate(packet_reviews):
        source = f"result.judgment.reviews[{index}]"
        if not isinstance(review, dict):
            errors.append(f"{source}: review record must be a mapping")
            continue
        review_id = review.get("review_id")
        if not isinstance(review_id, str) or not review_id:
            errors.append(f"{source}: review_id is required")
            continue
        if review_id in packet_reviews_by_id:
            errors.append(f"{source}: duplicate review_id: {review_id}")
        packet_reviews_by_id[review_id] = review
        source_ref = review.get("source_ref")
        if not isinstance(source_ref, str) or source_ref not in imported_source_refs:
            errors.append(f"{source}: source_ref must point to an imported structured review artifact")
        imported = imported_lineage_by_id.get(review_id)
        if imported is None:
            errors.append(f"{source}: imported source_ref review is missing from review_lineage: {review_id}")
            continue
        for field in REVIEW_MIRROR_FIELDS:
            if normalize_for_mirror(review.get(field)) != normalize_for_mirror(imported.get(field)):
                errors.append(f"{source}: field does not mirror imported review_lineage[{review_id}]: {field}")

    missing_from_packet = sorted(set(imported_lineage_by_id) - set(packet_reviews_by_id))
    if missing_from_packet:
        errors.append(f"result.judgment.reviews missing imported review_lineage records: {missing_from_packet}")

    return open_passing_reviews, errors


def resolved_targets(records: list[dict], *, relation: str) -> set[str]:
    return {
        record["target"]
        for record in records
        if isinstance(record, dict)
        and record.get("relation") == relation
        and record.get("status") == "resolved"
        and isinstance(record.get("target"), str)
    }


def source_target_path(ref: str, target: str) -> str:
    if ref.startswith("trace:"):
        return target.split("#", 1)[0]
    return target


def git_resolved_target_path(target: str) -> str | None:
    if ":" not in target:
        return None
    commit, path = target.split(":", 1)
    if not FULL_COMMIT_RE.fullmatch(commit) or not path:
        return None
    return path


def resolved_source_paths(root: Path, records: list[dict], *, listed_refs: set[str]) -> set[str]:
    paths: set[str] = set()
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("relation") != "source"
            or record.get("status") != "resolved"
            or not isinstance(record.get("target"), str)
        ):
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        if isinstance(ref, str) and ref.startswith("git:"):
            source_path = git_source_ref_path(root, ref)
            if source_path:
                paths.add(source_path)
            continue
        paths.add(source_target_path(ref, record["target"]))
    return paths


def current_staged_changed_paths(root: Path) -> list[str]:
    return changed_paths(root, mode="staged", base_ref=None)


def current_base_ref_changed_paths(root: Path, base_ref: str) -> list[str]:
    return changed_paths(root, mode="base-ref", base_ref=base_ref)


def current_base_ref_deleted_paths(root: Path, base_ref: str) -> list[str]:
    result = git(root, ["diff", "--name-status", f"{base_ref}...HEAD"])
    if result.returncode != 0:
        raise PacketError(result.stderr.strip() or "failed to read git deleted paths")
    deleted: list[str] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0].startswith("D"):
            deleted.append(fields[1])
    return sorted(set(deleted))


def git_text(root: Path, commit_ref: str, path: str) -> str | None:
    result = git(root, ["show", f"{commit_ref}:{path}"])
    return result.stdout if result.returncode == 0 else None


def path_has_proof_like_claim_at_commit(root: Path, commit_ref: str, path: str) -> bool:
    text = git_text(root, commit_ref, path)
    return bool(text and PROOF_LIKE_RE.search(text))


def commit_pinned_source_paths(
    root: Path,
    records: list[dict],
    *,
    listed_refs: set[str],
    commit_ref: str,
) -> set[str]:
    commit = git_ref_commit(root, commit_ref)
    if commit is None:
        return set()
    paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or record.get("relation") != "source" or record.get("status") != "resolved":
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        parts = git_source_ref_parts(root, ref)
        if parts and parts[0] == commit:
                paths.add(parts[1])
    return paths


def active_source_ref_violations(
    root: Path,
    records: list[dict],
    *,
    listed_refs: set[str],
    declared_changed_paths: set[str],
    deleted_paths: set[str],
    comparison_ref: str | None,
) -> list[str]:
    errors: list[str] = []
    head_commit = git_ref_commit(root, "HEAD")
    comparison_commit = git_ref_commit(root, comparison_ref) if comparison_ref else None
    extra_paths: set[str] = set()
    mutable_refs: list[str] = []
    wrong_commit_refs: list[str] = []
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("relation") != "source"
            or record.get("status") != "resolved"
            or not isinstance(record.get("target"), str)
        ):
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        parts = git_source_ref_parts(root, ref)
        if parts is None:
            mutable_refs.append(ref)
            target = source_target_path(ref, record["target"])
            if target not in declared_changed_paths:
                extra_paths.add(target)
            continue
        commit, path = parts
        if path not in declared_changed_paths:
            extra_paths.add(path)
            continue
        expected_commit = comparison_commit if path in deleted_paths else head_commit
        if expected_commit is None or commit != expected_commit:
            wrong_commit_refs.append(ref)
    if extra_paths:
        errors.append(
            "active base-ref stable packet source_refs must only cover changed_paths: "
            f"{sorted(extra_paths)}"
        )
    if mutable_refs:
        errors.append(
            "active base-ref stable packet source_refs must use commit-pinned git refs only: "
            f"{sorted(mutable_refs)}"
        )
    if wrong_commit_refs:
        errors.append(
            "active base-ref stable packet source_refs use the wrong boundary commit: "
            f"{sorted(wrong_commit_refs)}"
        )
    return errors


def git_source_ref_path(root: Path, ref: str) -> str | None:
    parts = git_source_ref_parts(root, ref)
    return parts[1] if parts else None


def git_source_ref_parts(root: Path, ref: str) -> tuple[str, str] | None:
    if not isinstance(ref, str) or not ref.startswith("git:"):
        return None
    spec = ref.removeprefix("git:")
    if ":" not in spec:
        return None
    commit, path = spec.split(":", 1)
    if not FULL_COMMIT_RE.fullmatch(commit):
        return None
    result = git(root, ["cat-file", "-t", commit])
    if result.returncode != 0 or result.stdout.strip() != "commit":
        return None
    if not path or path.startswith("/") or ".." in Path(path).parts:
        return None
    return commit, path.split("#", 1)[0]


def git_ref_commit(root: Path, ref: str) -> str | None:
    result = git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    return result.stdout.strip() if result.returncode == 0 else None


def git_ref_is_commit(root: Path, ref: object) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    result = git(root, ["cat-file", "-t", ref])
    return result.returncode == 0 and result.stdout.strip() == "commit"


def same_git_boundary(root: Path, left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    left_commit = git_ref_commit(root, left)
    right_commit = git_ref_commit(root, right)
    return left_commit is not None and left_commit == right_commit


def provenance_source_refs(packet: dict) -> list[tuple[str, str]]:
    input_data = packet["input"]
    result = packet["result"]
    refs: list[tuple[str, str]] = []
    user_judgment = input_data.get("user_judgment", {})
    if isinstance(user_judgment, dict):
        for key, record in user_judgment.items():
            if (
                isinstance(key, str)
                and isinstance(record, dict)
                and isinstance(record.get("source_ref"), str)
                and record.get("source_ref")
            ):
                refs.append((f"input.user_judgment.{key}", record["source_ref"]))
    for source, records in (
        ("result.evidence.skipped", result["evidence"].get("skipped", [])),
        ("result.judgment.waivers", result["judgment"].get("waivers", [])),
        ("result.judgment.downgrades", result["judgment"].get("downgrades", [])),
        ("result.judgment.residual_risk", result["judgment"].get("residual_risk", [])),
    ):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if isinstance(record, dict) and isinstance(record.get("source_ref"), str) and record.get("source_ref"):
                refs.append((f"{source}[{index}]", record["source_ref"]))
    return refs


def review_source_refs(packet: dict) -> list[tuple[str, str, dict]]:
    refs: list[tuple[str, str, dict]] = []
    records = packet["result"]["judgment"].get("reviews", [])
    if not isinstance(records, list):
        return refs
    for index, record in enumerate(records):
        if isinstance(record, dict) and isinstance(record.get("source_ref"), str) and record.get("source_ref"):
            refs.append((f"result.judgment.reviews[{index}]", record["source_ref"], record))
    return refs


def validate_packet(
    packet: dict,
    *,
    require_stable: bool = False,
    root: Path = ROOT,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if set(packet) != set(PUBLIC_SECTIONS):
        errors.append(f"packet public sections must be exactly {', '.join(PUBLIC_SECTIONS)}")
        return errors

    meta = packet.get("meta")
    input_data = packet.get("input")
    result = packet.get("result")
    if not isinstance(meta, dict) or not isinstance(input_data, dict) or not isinstance(result, dict):
        return ["meta, input, and result must be mappings"]

    if set(meta) != set(META_FIELDS):
        errors.append(f"meta fields must be exactly {', '.join(META_FIELDS)}")
    if set(input_data) != set(INPUT_FIELDS):
        errors.append(f"input fields must be exactly {', '.join(INPUT_FIELDS)}")
    if any(field not in meta for field in META_FIELDS) or any(field not in input_data for field in INPUT_FIELDS):
        return errors
    if set(result) != set(RESULT_GROUPS):
        errors.append(f"result groups must be exactly {', '.join(RESULT_GROUPS)}")
        return errors
    for group in RESULT_GROUPS:
        if not isinstance(result[group], dict):
            errors.append(f"result.{group} must be a mapping")

    if errors:
        return errors

    lifecycle = meta["lifecycle"]
    mode = meta["mode"]
    if not isinstance(lifecycle, str) or lifecycle not in LIFECYCLES:
        errors.append(f"meta.lifecycle is invalid: {lifecycle}")
    if not isinstance(mode, str) or mode not in MODES:
        errors.append(f"meta.mode is invalid: {mode}")
    if not date_like(meta["created_at"]):
        errors.append("meta.created_at must be an ISO date")
    if not date_like(meta["finalized_at"], allow_none=lifecycle == "start"):
        errors.append("meta.finalized_at must be an ISO date, or null for start packets")
    if lifecycle == "start" and meta["finalized_at"] is not None:
        errors.append("start packet finalized_at must be null")
    if lifecycle != "start" and meta["finalized_at"] is None:
        errors.append("finalized or blocked packet finalized_at is required")

    if not isinstance(input_data["intent"], str) or not input_data["intent"]:
        errors.append("input.intent must be a non-empty string")
    if not isinstance(input_data["actor"], str) or not input_data["actor"]:
        errors.append("input.actor must be a non-empty string")
    if not isinstance(input_data["source_refs"], list):
        errors.append("input.source_refs must be a list")
    if not isinstance(input_data["user_judgment"], dict):
        errors.append("input.user_judgment must be a mapping")

    inference = result["inference"]
    evidence = result["evidence"]
    judgment = result["judgment"]
    decision = result["decision"]
    command_result_records = mapping_records(
        evidence.get("command_results", []),
        source="result.evidence.command_results",
        errors=errors,
    )
    skipped_records = mapping_records(
        evidence.get("skipped", []),
        source="result.evidence.skipped",
        errors=errors,
    )
    waiver_records = mapping_records(
        judgment.get("waivers", []),
        source="result.judgment.waivers",
        errors=errors,
    )
    downgrade_records = mapping_records(
        judgment.get("downgrades", []),
        source="result.judgment.downgrades",
        errors=errors,
    )
    review_records = mapping_records(
        judgment.get("reviews", []),
        source="result.judgment.reviews",
        errors=errors,
    )
    residual_risk_records = mapping_records(
        judgment.get("residual_risk", []),
        source="result.judgment.residual_risk",
        errors=errors,
    )
    evaluator_boundary = evidence.get("evaluator_boundary")
    if isinstance(evaluator_boundary, dict):
        status = evaluator_boundary.get("status")
        if status is not None and not isinstance(status, str):
            errors.append("result.evidence.evaluator_boundary.status must be null or a string")
    accepted = decision.get("accepted")
    stable = decision.get("stable_handoff_eligible")
    declared_required_evidence, declared_required_review = required_targets(packet)
    required_review = declared_required_review
    required_evidence = declared_required_evidence
    stable_required_evidence_errors: list[str] = []
    stable_required_review_errors: list[str] = []
    if stable:
        required_evidence, stable_required_evidence_errors = stable_required_evidence(packet)
        required_review = checker_required_review(packet, root=root)
        if declared_required_review != required_review:
            stable_required_review_errors.append(
                "stable packet required_review must match checker-derived required reviews: "
                f"{sorted(required_review)}"
            )

    if lifecycle != "start":
        for field in FINALIZED_INFERENCE_FIELDS:
            if field not in inference:
                errors.append(f"result.inference.{field} is required for {lifecycle} packets")
        changed_path_values = inference.get("changed_paths", [])
        if not isinstance(changed_path_values, list):
            errors.append("result.inference.changed_paths must be a list")
            changed_path_values = []
        elif any(not isinstance(path, str) for path in changed_path_values):
            errors.append("result.inference.changed_paths must contain only strings")
        if not isinstance(inference.get("deviations"), list):
            errors.append("result.inference.deviations must be a list")
        if not isinstance(inference.get("required_evidence"), list):
            errors.append("result.inference.required_evidence must be a list")
        elif any(not isinstance(item, str) for item in inference.get("required_evidence", [])):
            errors.append("result.inference.required_evidence must contain only strings")
        if not isinstance(inference.get("required_review"), list):
            errors.append("result.inference.required_review must be a list")
        elif any(not isinstance(item, str) for item in inference.get("required_review", [])):
            errors.append("result.inference.required_review must contain only strings")
        if not isinstance(inference.get("protected_boundary_changed"), bool):
            errors.append("result.inference.protected_boundary_changed must be a boolean")
        protected_paths = [path for path in changed_path_values if isinstance(path, str) and requires_review_for_path(path)]
        if protected_paths:
            if inference.get("protected_boundary_changed") is not True:
                errors.append("protected changed paths require protected_boundary_changed: true")
            if inference.get("change_class") != "harness-affecting":
                errors.append("protected changed paths require change_class: harness-affecting")
            if inference.get("impact") != "high":
                errors.append("protected changed paths require impact: high")

    user_judgment = input_data.get("user_judgment")
    if not isinstance(user_judgment, dict):
        user_judgment = {}
    for key, request in user_judgment.items():
        if not isinstance(key, str):
            errors.append(f"input.user_judgment key must be a string: {key}")
            continue
        if "waiver" in key or "downgrade" in key:
            errors.extend(
                validate_exception_record(
                    request,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"input.user_judgment.{key}",
                    record_type="downgrade" if "downgrade" in key else "waiver",
                )
            )
        elif "skipped" in key:
            errors.extend(validate_provenance_record(request, source=f"input.user_judgment.{key}"))
            if isinstance(request, dict):
                evidence_target = request.get("evidence")
                if not evidence_target:
                    errors.append(f"input.user_judgment.{key}: evidence is required")
                elif not isinstance(evidence_target, str):
                    errors.append(f"input.user_judgment.{key}: evidence must be a string")
                elif evidence_target not in required_evidence:
                    errors.append(f"input.user_judgment.{key}: skipped evidence is not required: {evidence_target}")
        elif "residual" in key:
            errors.extend(
                validate_residual_risk_record(
                    request,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"input.user_judgment.{key}",
                )
            )
        else:
            errors.append(
                f"input.user_judgment.{key}: key must declare waiver, downgrade, skipped, or residual"
            )

    for waiver in waiver_records:
        errors.extend(
            validate_exception_record(
                waiver,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.waivers",
                record_type="waiver",
            )
        )
    for downgrade in downgrade_records:
        errors.extend(
            validate_exception_record(
                downgrade,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.downgrades",
                record_type="downgrade",
            )
        )

    if lifecycle == "start":
        if accepted is not None:
            errors.append("start packet decision.accepted must be null")
        if stable is not False:
            errors.append("start packet cannot be stable-handoff eligible")
    if lifecycle == "blocked":
        if accepted is not False:
            errors.append("blocked packet decision.accepted must be false")
        if stable is not False:
            errors.append("blocked packet cannot be stable-handoff eligible")
    if mode == "worktree" and stable is not False:
        errors.append("worktree packets cannot be stable-handoff eligible")
    if stable and accepted is not True:
        errors.append("stable-handoff packet must be accepted")

    for review in review_records:
        score = review.get("score")
        if stable and not review.get("review_id"):
            errors.append("stable review requires review_id")
        if stable and not review.get("rerun_of"):
            errors.extend(validate_review_record(review, source="result.judgment.reviews"))
        if isinstance(score, (int, float)) and score == 9:
            if not review.get("why_not_10") or not review.get("disposition"):
                errors.append("score 9 review requires why_not_10 and disposition")

    if stable:
        active_stable_handoff = packet_is_active_handoff(packet, packet_ref, root=root)
        if active_stable_handoff and mode != "base-ref":
            errors.append("active stable handoff requires base-ref mode; staged packets are preflight-only")
        errors.extend(stable_required_evidence_errors)
        errors.extend(stable_required_review_errors)
        if not required_evidence:
            errors.append("stable packet must declare checker-derived required evidence")
        if declared_required_evidence != required_evidence:
            errors.append(
                "stable packet required_evidence must match checker-derived required evidence: "
                f"{sorted(required_evidence)}"
            )

        resolved_refs = evidence.get("resolved_refs", [])
        if not isinstance(resolved_refs, list):
            errors.append("stable packet evidence.resolved_refs must be a list")
            resolved_refs = []
        for record in resolved_refs:
            errors.extend(validate_resolved_ref_record(record, root=root, source="result.evidence.resolved_refs"))
        ref_index = resolved_ref_index(resolved_refs)
        open_passing_review_targets, review_import_errors = validate_review_imports(
            packet,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
            ref_index=ref_index,
        )
        errors.extend(review_import_errors)

        evidence_source_refs = evidence.get("source_refs", [])
        if not isinstance(evidence_source_refs, list):
            errors.append("stable packet evidence.source_refs must be a list")
            evidence_source_refs = []
        input_source_refs = input_data.get("source_refs", [])
        if not isinstance(input_source_refs, list):
            input_source_refs = []
        for ref in input_source_refs:
            if not isinstance(ref, str):
                errors.append(f"stable packet input source_ref must be a string: {ref}")
                continue
            if ref not in evidence_source_refs:
                errors.append(f"stable packet input source_ref missing from evidence.source_refs: {ref}")
            if not has_resolved_relation(ref_index, relation="source", ref=ref, origin="input"):
                errors.append(f"stable packet input source_ref lacks resolved input source relation: {ref}")
        for ref in evidence_source_refs:
            if not isinstance(ref, str):
                errors.append(f"stable packet evidence source_ref must be a string: {ref}")
                continue
            if not has_resolved_relation(ref_index, relation="source", ref=ref):
                errors.append(f"stable packet source_ref lacks resolved source relation: {ref}")
        source_paths = resolved_source_paths(
            root,
            resolved_refs,
            listed_refs={ref for ref in evidence_source_refs if isinstance(ref, str)},
        )
        declared_changed_paths = set(string_list_values(inference.get("changed_paths", [])))
        missing_changed_sources = sorted(path for path in declared_changed_paths if path not in source_paths)
        if missing_changed_sources:
            errors.append(f"stable packet changed_paths lack resolved source refs: {missing_changed_sources}")
        protected_source_targets = sorted(
            target for target in source_paths if requires_review_for_path(target) and target not in declared_changed_paths
        )
        if protected_source_targets:
            errors.append(
                f"stable packet source_ref points to protected path outside changed_paths: {protected_source_targets}"
            )
        if active_stable_handoff and mode == "base-ref":
            deleted_paths: set[str] = set()
            comparison_ref = evidence.get("comparison_ref")
            if isinstance(comparison_ref, str) and git_ref_is_commit(root, comparison_ref):
                deleted_paths = set(current_base_ref_deleted_paths(root, comparison_ref))
            source_ref_set = {ref for ref in evidence_source_refs if isinstance(ref, str)}
            errors.extend(
                active_source_ref_violations(
                    root,
                    resolved_refs,
                    listed_refs=source_ref_set,
                    declared_changed_paths=declared_changed_paths,
                    deleted_paths=deleted_paths,
                    comparison_ref=comparison_ref if isinstance(comparison_ref, str) else None,
                )
            )
            head_pinned_paths = commit_pinned_source_paths(
                root,
                resolved_refs,
                listed_refs=source_ref_set,
                commit_ref="HEAD",
            )
            missing_head_sources = sorted(
                path for path in declared_changed_paths - deleted_paths if path not in head_pinned_paths
            )
            if missing_head_sources:
                errors.append(
                    "active base-ref stable packet changed_paths require HEAD-pinned git source refs: "
                    f"{missing_head_sources}"
                )
            if deleted_paths:
                base_pinned_paths = commit_pinned_source_paths(
                    root,
                    resolved_refs,
                    listed_refs=source_ref_set,
                    commit_ref=comparison_ref,
                )
                missing_deleted_sources = sorted(
                    path for path in declared_changed_paths & deleted_paths if path not in base_pinned_paths
                )
                if missing_deleted_sources:
                    errors.append(
                        "active base-ref stable packet deleted changed_paths require comparison-ref-pinned git source refs: "
                        f"{missing_deleted_sources}"
                    )
        if mode == "staged" and packet_ref_is_repo_local(packet_ref) and active_stable_handoff:
            staged_paths = set(current_staged_changed_paths(root))
            if staged_paths != declared_changed_paths:
                errors.append(
                    "staged stable packet changed_paths must match current staged diff: "
                    f"declared={sorted(declared_changed_paths)} staged={sorted(staged_paths)}"
                )

        for boundary_ref_name in ("baseline_ref", "comparison_ref"):
            boundary_ref = evidence.get(boundary_ref_name)
            if not boundary_ref:
                errors.append(f"stable packet {boundary_ref_name} is required")
            elif not git_ref_is_commit(root, boundary_ref):
                errors.append(f"stable packet {boundary_ref_name} must resolve to a git commit: {boundary_ref}")
            elif mode == "staged" and not same_git_boundary(root, boundary_ref, "HEAD"):
                errors.append(f"staged stable packet {boundary_ref_name} must match HEAD: {boundary_ref}")
        comparison_ref = evidence.get("comparison_ref")
        baseline_ref = evidence.get("baseline_ref")
        if (
            active_stable_handoff
            and mode == "base-ref"
            and isinstance(baseline_ref, str)
            and isinstance(comparison_ref, str)
            and git_ref_is_commit(root, baseline_ref)
            and git_ref_is_commit(root, comparison_ref)
            and not same_git_boundary(root, baseline_ref, comparison_ref)
        ):
            errors.append("active base-ref stable packet baseline_ref must match comparison_ref")
        if (
            active_stable_handoff
            and mode == "base-ref"
            and isinstance(comparison_ref, str)
            and git_ref_is_commit(root, comparison_ref)
        ):
            base_ref_paths = set(current_base_ref_changed_paths(root, comparison_ref))
            if base_ref_paths != declared_changed_paths:
                errors.append(
                    "base-ref stable packet changed_paths must match git diff boundary: "
                    f"declared={sorted(declared_changed_paths)} base_ref={comparison_ref} "
                    f"actual={sorted(base_ref_paths)}"
                )

        for source, source_ref in provenance_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="waiver-provenance", ref=source_ref, origin="generated"):
                errors.append(f"{source}: source_ref lacks resolved waiver-provenance relation with generated origin: {source_ref}")
            elif ref_is_acceptance_packet(root, source_ref):
                errors.append(f"{source}: waiver-provenance source_ref cannot be an acceptance packet: {source_ref}")
        for index, record in enumerate(residual_risk_records):
            errors.extend(
                validate_residual_risk_record(
                    record,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"result.judgment.residual_risk[{index}]",
                )
            )
        for source, source_ref, review in review_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref, origin="generated"):
                errors.append(f"{source}: source_ref lacks resolved review-provenance relation with generated origin: {source_ref}")
            elif ref_is_acceptance_packet(root, source_ref):
                errors.append(f"{source}: review-provenance source_ref cannot be an acceptance packet: {source_ref}")
            elif not review_source_ref_records_review(root, source_ref, review, packet_id=meta["packet_id"]):
                errors.append(f"{source}: review-provenance source_ref lacks matching review record: {source_ref}")

        protected_review_required = (
            inference.get("protected_boundary_changed") is True
            or inference.get("change_class") == "harness-affecting"
            or inference.get("impact") == "high"
            or any(requires_review_for_path(path) for path in string_list_values(inference.get("changed_paths", [])))
        )
        if protected_review_required and not required_review:
            errors.append("stable protected or high-impact packet must infer required review")

        passed_evidence: set[str] = set()
        for index, item in enumerate(command_result_records):
            status = item.get("status")
            if not isinstance(status, str) or not status:
                errors.append(f"result.evidence.command_results[{index}].status must be a non-empty string")
                continue
            command = item.get("command")
            if not isinstance(command, str) or not command:
                errors.append(f"result.evidence.command_results[{index}].command must be a non-empty string")
                continue
            if status == "pass":
                passed_evidence.add(command)
            base_ref = command_base_ref(command)
            if base_ref:
                for boundary_ref_name in ("baseline_ref", "comparison_ref"):
                    if not same_git_boundary(root, evidence.get(boundary_ref_name), base_ref):
                        errors.append(
                            f"stable command base-ref {base_ref} must match evidence.{boundary_ref_name}: "
                            f"{evidence.get(boundary_ref_name)}"
                        )
            artifact_ref = item.get("artifact_ref")
            if not artifact_ref:
                errors.append(f"stable command evidence lacks artifact_ref: {command}")
            elif str(artifact_ref).startswith("terminal:"):
                errors.append(f"terminal placeholder cannot satisfy stable evidence: {artifact_ref}")
            elif not str(artifact_ref).startswith("file:"):
                errors.append(f"stable command artifact_ref must use file: scheme: {artifact_ref}")
            elif not has_resolved_relation(ref_index, relation="artifact", ref=artifact_ref, origin="generated"):
                errors.append(f"stable command artifact lacks resolved generated artifact relation: {artifact_ref}")
            else:
                artifact_error = artifact_command_evidence_error(
                    root,
                    artifact_ref,
                    command,
                    status,
                    packet_id=meta["packet_id"],
                    packet_ref=packet_ref or "",
                    packet_sha256=packet_sha256 or "",
                )
                if artifact_error:
                    errors.append(f"stable command artifact does not record command evidence: {artifact_ref}: {artifact_error}")

        trace_refs = evidence.get("trace_refs", {})
        if not isinstance(trace_refs, dict):
            errors.append("stable packet evidence.trace_refs must be a mapping")
            trace_refs = {}
        for trace_name in ("search_set_before", "search_set_after"):
            trace_ref = trace_refs.get(trace_name)
            if trace_ref is None:
                continue
            if not isinstance(trace_ref, str) or not trace_ref.startswith("trace:"):
                errors.append(f"stable trace_refs.{trace_name} must use trace: scheme: {trace_ref}")
            elif not trace_ref_has_anchor(trace_ref):
                errors.append(f"stable trace_refs.{trace_name} must include an anchor: {trace_ref}")
            elif not is_search_set_trace_ref(trace_ref):
                errors.append(f"stable trace_refs.{trace_name} must point to .harness/traces/search-set.md: {trace_ref}")
            elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                errors.append(f"stable trace_refs.{trace_name} lacks resolved generated trace relation: {trace_ref}")
        if isinstance(trace_refs, dict):
            search_set_before = trace_refs.get("search_set_before")
            search_set_after = trace_refs.get("search_set_after")
            canonical_before = canonical_trace_ref(search_set_before) if isinstance(search_set_before, str) else None
            canonical_after = canonical_trace_ref(search_set_after) if isinstance(search_set_after, str) else None
            if canonical_before and canonical_before == canonical_after:
                errors.append("stable packet search_set_before and search_set_after must be distinct when both are recorded")
        for bucket_name in ("evolution", "failures"):
            bucket_refs = trace_refs.get(bucket_name, [])
            if not isinstance(bucket_refs, list):
                errors.append(f"stable trace_refs.{bucket_name} must be a list")
                continue
            for trace_ref in bucket_refs:
                if not isinstance(trace_ref, str) or not trace_ref.startswith("trace:"):
                    errors.append(f"stable trace_refs.{bucket_name} entries must use trace: scheme: {trace_ref}")
                elif not trace_ref_has_anchor(trace_ref):
                    errors.append(f"stable trace_refs.{bucket_name} entries must include an anchor: {trace_ref}")
                elif not is_bucket_trace_ref(trace_ref, bucket_name):
                    errors.append(
                        f"stable trace_refs.{bucket_name} entries must point to .harness/traces/{bucket_name}/ evidence: {trace_ref}"
                    )
                elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                    errors.append(f"stable trace_refs.{bucket_name} lacks resolved generated trace relation: {trace_ref}")

        if protected_review_required:
            for trace_name in ("search_set_before", "search_set_after"):
                trace_ref = trace_refs.get(trace_name) if isinstance(trace_refs, dict) else None
                skipped_targets = {
                    item.get("evidence")
                    for item in skipped_records
                    if isinstance(item, dict)
                    and isinstance(item.get("evidence"), str)
                    and item.get("evidence")
                }
                if trace_ref and trace_name in skipped_targets:
                    errors.append(
                        f"stable protected packet {trace_name} cannot have both trace evidence and skipped evidence"
                    )
                    continue
                if not trace_ref and trace_name in skipped_targets:
                    continue
                if not trace_ref:
                    errors.append(f"stable protected packet missing {trace_name}")
                elif not is_search_set_trace_ref(trace_ref):
                    errors.append(f"stable protected packet {trace_name} must point to .harness/traces/search-set.md: {trace_ref}")
                elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                    errors.append(f"stable protected packet {trace_name} lacks resolved generated trace relation: {trace_ref}")

        for skipped in skipped_records:
            errors.extend(validate_provenance_record(skipped, source="result.evidence.skipped"))
            evidence_target = skipped.get("evidence") if isinstance(skipped, dict) else None
            allowed_skips = required_evidence | {"search_set_before", "search_set_after"}
            if not evidence_target:
                errors.append("result.evidence.skipped: evidence is required")
            elif not isinstance(evidence_target, str):
                errors.append("result.evidence.skipped: evidence must be a string")
            elif evidence_target not in allowed_skips:
                errors.append(f"result.evidence.skipped: skipped evidence is not required: {evidence_target}")

        proof_like_paths = [
            path
            for path in string_list_values(inference.get("changed_paths", []))
            if path.endswith(".md") and path_has_proof_like_claim_for_packet(root, packet, path)
        ]
        claims = evidence.get("claims", [])
        if proof_like_paths and not claims:
            errors.append(f"stable packet has proof-like changed docs without claim evidence: {proof_like_paths}")
        if proof_like_paths and inference.get("impact") != "high":
            errors.append("proof-like changed docs require impact: high")
        if proof_like_paths and "claim evidence" not in required_review:
            errors.append("proof-like changed docs require claim evidence review")
        if claims and not isinstance(claims, list):
            errors.append("result.evidence.claims must be a list")
            claims = []
        for claim in claims:
            if not isinstance(claim, dict):
                errors.append("result.evidence.claims: claim must be a mapping")
                continue
            raw_refs = claim.get("raw_evidence_refs")
            if not isinstance(raw_refs, list) or not raw_refs:
                errors.append("result.evidence.claims: raw_evidence_refs is required")
                continue
            for raw_ref in raw_refs:
                if not isinstance(raw_ref, str) or not raw_ref.startswith(("file:", "trace:")):
                    errors.append(f"claim evidence ref must use file: or trace: scheme: {raw_ref}")
                elif raw_ref.startswith("trace:") and not trace_ref_has_anchor(raw_ref):
                    errors.append(f"claim evidence trace ref must include an anchor: {raw_ref}")
                elif raw_ref.startswith("trace:") and not is_claim_evidence_trace_ref(raw_ref):
                    errors.append(f"claim evidence trace ref must point to .harness/traces/ evidence and not search-set index: {raw_ref}")
                elif not has_resolved_relation(ref_index, relation="claim-evidence", ref=raw_ref, origin="generated"):
                    errors.append(f"claim evidence ref lacks resolved generated claim-evidence relation: {raw_ref}")
                elif raw_ref.startswith("file:") and not is_raw_claim_file_ref(root, raw_ref):
                    errors.append(
                        "claim evidence file ref must point to raw artifact/log/screenshot/report evidence: "
                        f"{raw_ref}"
                    )

        passed_evidence_records = [
            item.get("command")
            for item in command_result_records
            if item.get("status") == "pass" and isinstance(item.get("command"), str) and item.get("command")
        ]
        waived_evidence_records = [
            item.get("evidence")
            for item in waiver_records
            if isinstance(item.get("evidence"), str) and item.get("evidence")
        ]
        skipped_evidence_records = [
            item.get("evidence")
            for item in skipped_records
            if isinstance(item, dict) and isinstance(item.get("evidence"), str) and item.get("evidence") in required_evidence
        ]
        closed_evidence_replacements = (
            set(passed_evidence_records) | set(waived_evidence_records) | set(skipped_evidence_records)
        )
        downgraded_evidence_records: list[str] = []
        for item in downgrade_records:
            if item.get("kind") != "evidence":
                continue
            source_target = item.get("from")
            replacement = item.get("to")
            if not isinstance(source_target, str) or not source_target:
                continue
            if not isinstance(replacement, str) or not replacement:
                continue
            if replacement not in closed_evidence_replacements:
                errors.append(
                    "stable evidence downgrade replacement is not closed by durable evidence, waiver, or skip: "
                    f"{source_target} -> {replacement}"
                )
                continue
            downgraded_evidence_records.append(source_target)
        errors.extend(
            multiple_required_closure_errors(
                required_evidence,
                [
                    ("command pass", passed_evidence_records),
                    ("waiver", waived_evidence_records),
                    ("downgrade", downgraded_evidence_records),
                    ("skipped", skipped_evidence_records),
                ],
                kind="evidence",
            )
        )
        passed_evidence = set(passed_evidence_records)
        waived_evidence = set(waived_evidence_records)
        downgraded_evidence = set(downgraded_evidence_records)
        skipped_evidence = set(skipped_evidence_records)
        missing_evidence = required_evidence - passed_evidence - waived_evidence - downgraded_evidence - skipped_evidence
        if missing_evidence:
            errors.append(f"stable packet missing required evidence: {sorted(missing_evidence)}")

        open_passing_review_records = list(open_passing_review_targets)
        waived_review_records = [
            item.get("review")
            for item in waiver_records
            if isinstance(item.get("review"), str) and item.get("review")
        ]
        closed_review_replacements = set(open_passing_review_records) | set(waived_review_records)
        downgraded_review_records: list[str] = []
        for item in downgrade_records:
            if item.get("kind") != "review":
                continue
            source_target = item.get("from")
            replacement = item.get("to")
            if not isinstance(source_target, str) or not source_target:
                continue
            if not isinstance(replacement, str) or not replacement:
                continue
            if replacement not in closed_review_replacements:
                errors.append(
                    "stable review downgrade replacement is not closed by durable review or waiver: "
                    f"{source_target} -> {replacement}"
                )
                continue
            downgraded_review_records.append(source_target)
        errors.extend(
            multiple_required_closure_errors(
                required_review,
                [
                    ("review pass", open_passing_review_records),
                    ("waiver", waived_review_records),
                    ("downgrade", downgraded_review_records),
                ],
                kind="review",
            )
        )
        waived_reviews = set(waived_review_records)
        downgraded_reviews = set(downgraded_review_records)
        passing_reviews = set(open_passing_review_records)
        missing_reviews = required_review - passing_reviews - waived_reviews - downgraded_reviews
        if missing_reviews:
            errors.append(f"stable packet missing required review: {sorted(missing_reviews)}")

    if require_stable and stable is not True:
        errors.append("packet is valid but not stable-handoff eligible")

    return errors


def mode_from_args(args: argparse.Namespace) -> tuple[str, str | None]:
    selected = [name for name in ("staged", "worktree", "base_ref") if getattr(args, name, None)]
    if len(selected) != 1:
        raise PacketError("select exactly one mode: --staged, --worktree, or --base-ref <ref>")
    if selected[0] == "base_ref":
        return "base-ref", args.base_ref
    return selected[0], None


def changed_paths(root: Path, *, mode: str, base_ref: str | None) -> list[str]:
    if mode == "staged":
        result = git(root, ["diff", "--cached", "--name-only"])
    elif mode == "base-ref":
        result = git(root, ["diff", "--name-only", f"{base_ref}...HEAD"])
    else:
        result = git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
        if result.returncode == 0:
            paths: list[str] = []
            for line in result.stdout.splitlines():
                path = line[3:] if len(line) > 3 else ""
                if " -> " in path:
                    path = path.split(" -> ", 1)[1]
                if path:
                    paths.append(path)
            return sorted(set(paths))
    if result.returncode != 0:
        raise PacketError(result.stderr.strip() or "failed to read git changes")
    return sorted(path for path in result.stdout.splitlines() if path)


def packet_ref_is_repo_local(packet_ref: str | None) -> bool:
    return bool(packet_ref) and not Path(str(packet_ref)).is_absolute()


def packet_ref_is_fixture(packet_ref: str | None) -> bool:
    if not packet_ref:
        return False
    path = Path(str(packet_ref))
    return not path.is_absolute() and path.as_posix() in CANONICAL_ACCEPTANCE_PACKET_FIXTURES


def packet_ref_is_fixture_materialization(root: Path, packet_ref: str | None) -> bool:
    if os.environ.get(FIXTURE_MATERIALIZATION_ENV) != "1" or not packet_ref:
        return False
    path = Path(str(packet_ref))
    fixture_root = Path("backlog/fixtures/acceptance-packets")
    if path.is_absolute() or fixture_root not in (path, *path.parents):
        return False
    marker = root / path.parent / FIXTURE_MATERIALIZATION_MARKER
    try:
        return marker.read_text(encoding="utf-8").strip() == "acceptance-packet-fixture-materialization/v1"
    except OSError:
        return False


def packet_has_fixture_binding(packet: dict) -> bool:
    review_imports = packet.get("result", {}).get("evidence", {}).get("review_imports", [])
    if not isinstance(review_imports, list):
        return False
    for item in review_imports:
        if not isinstance(item, dict):
            continue
        binding = item.get("target_binding")
        if isinstance(binding, dict) and packet_ref_is_fixture(binding.get("packet_ref")):
            return True
    return False


def packet_has_materialized_fixture_binding(packet: dict, packet_ref: str | None, *, root: Path) -> bool:
    if not packet_ref_is_fixture_materialization(root, packet_ref):
        return False
    path = Path(str(packet_ref))
    packet_rel = path.as_posix()
    materialization_dir = path.parent.as_posix()
    review_imports = packet.get("result", {}).get("evidence", {}).get("review_imports", [])
    if not isinstance(review_imports, list):
        return False
    for item in review_imports:
        if not isinstance(item, dict):
            continue
        binding = item.get("target_binding")
        source_ref = item.get("source_ref")
        if not isinstance(binding, dict) or binding.get("packet_ref") != packet_rel:
            continue
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            continue
        source_path = source_ref.removeprefix("file:")
        if source_path == materialization_dir or source_path.startswith(f"{materialization_dir}/"):
            return True
    return False


def packet_is_active_handoff(packet: dict, packet_ref: str | None, *, root: Path) -> bool:
    return (
        not packet_ref_is_fixture(packet_ref)
        and not packet_has_materialized_fixture_binding(packet, packet_ref, root=root)
        and not packet_has_fixture_binding(packet)
    )



def is_protected(path: str) -> bool:
    return path in PROTECTED_PATHS or any(
        path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def requires_review_for_path(path: str) -> bool:
    return is_protected(path)


def path_has_proof_like_claim(root: Path, path: str) -> bool:
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(PROOF_LIKE_RE.search(text))


def infer_packet_result(root: Path, packet: dict, *, mode: str, base_ref: str | None) -> dict:
    paths = changed_paths(root, mode=mode, base_ref=base_ref)
    baseline_ref = packet["result"].get("evidence", {}).get("baseline_ref")
    comparison_ref = base_ref if mode == "base-ref" else baseline_ref
    protected = any(is_protected(path) for path in paths)
    if mode == "base-ref":
        proof_like = any(
            path.endswith(".md")
            and (
                path_has_proof_like_claim_at_commit(root, str(base_ref), path)
                or path_has_proof_like_claim_at_commit(root, "HEAD", path)
            )
            for path in paths
        )
    else:
        proof_like = any(path.endswith(".md") and path_has_proof_like_claim(root, path) for path in paths)
    high_risk = protected or proof_like
    change_class = "harness-affecting" if protected else "routine"
    if mode == "staged":
        diff_command = ["git", "diff", "--cached", "--check"]
        evidence_command = "git diff --cached --check"
    elif mode == "base-ref":
        diff_command = ["git", "diff", "--check", f"{base_ref}...HEAD"]
        evidence_command = f"git diff --check {base_ref}...HEAD"
    else:
        diff_command = ["git", "diff", "--check"]
        evidence_command = "git diff --check"
    required_evidence = [evidence_command]
    diff_check = git(root, diff_command[1:])
    diff_status = "pass" if diff_check.returncode == 0 else "fail"
    resolved_refs = []
    for ref in packet["input"].get("source_refs", []):
        resolved = resolve_ref(root, ref)
        if resolved:
            resolved_refs.append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": resolved,
                }
            )
    resolved_refs.append(
        {
            "origin": "generated",
            "relation": "observation",
            "ref": "terminal:git-diff-check",
            "status": "local-placeholder",
            "target": "terminal:git-diff-check",
        }
    )
    skipped_evidence: list[dict] = []
    if protected:
        skip_source_ref = "file:backlog/plans/04-evidence-capture-and-source-refs.md"
        resolved_refs.append(
            {
                "origin": "generated",
                "relation": "waiver-provenance",
                "ref": skip_source_ref,
                "status": "resolved",
                "target": "backlog/plans/04-evidence-capture-and-source-refs.md",
            }
        )
        for evidence_name in ("search_set_before", "search_set_after"):
            skipped_evidence.append(
                {
                    "evidence": evidence_name,
                    "actor": packet["input"].get("actor", "codex"),
                    "role": "operator",
                    "date": today(),
                    "reason": f"Finalize did not capture {evidence_name}; stable handoff must add trace evidence or keep this targeted skip.",
                    "source_ref": skip_source_ref,
                }
            )

    packet["meta"]["lifecycle"] = "finalized"
    packet["meta"]["finalized_at"] = today()
    packet["result"] = {
        "inference": {
            "change_class": change_class,
            "impact": "high" if high_risk else "low",
            "changed_paths": paths,
            "intended_scope": packet["input"]["intent"],
            "actual_scope": ", ".join(paths) if paths else "No changed paths detected.",
            "deviations": [],
            "isolation": "isolated" if paths else "no-op",
            "protected_boundary_changed": protected,
            "required_evidence": required_evidence,
            "required_review": [],
        },
        "evidence": {
            "baseline_ref": baseline_ref,
            "comparison_ref": comparison_ref,
            "evaluator_boundary": {
                "status": "unchanged",
                "commands": [evidence_command],
            },
            "command_results": [
                {
                    "command": evidence_command,
                    "status": diff_status,
                    "artifact_ref": "terminal:git-diff-check",
                }
            ],
            "source_refs": list(packet["input"].get("source_refs", [])),
            "resolved_refs": resolved_refs,
            "trace_refs": {
                "search_set_before": None,
                "search_set_after": None,
                "evolution": [],
                "failures": [],
                "disposition": "Trace capture is deferred to Plan 04.",
            },
            "skipped": skipped_evidence,
        },
        "judgment": packet["result"].get(
            "judgment",
            {"reviews": [], "waivers": [], "downgrades": [], "residual_risk": []},
        ),
        "decision": {
            "accepted": diff_status == "pass" and not high_risk,
            "stable_handoff_eligible": False,
            "reason": "Plan 04 requires durable artifact refs before stable handoff.",
            "next_action": "Add durable evidence refs and run check --require-stable.",
        },
    }
    if protected:
        packet["result"]["decision"]["reason"] = (
            "Plan 03 cannot accept protected changes yet; review import and protected-change stable promotion are out of scope."
        )
        packet["result"]["decision"]["next_action"] = "Use a later review-import plan before protected stable handoff."
    elif proof_like:
        packet["result"]["decision"]["reason"] = (
            "Plan 04 cannot accept proof-like/public claim changes without durable claim evidence and review."
        )
        packet["result"]["decision"]["next_action"] = "Add raw claim evidence and claim-evidence review before stable handoff."
    packet["result"]["inference"]["required_review"] = sorted(checker_required_review(packet, root=root))
    if mode == "worktree":
        packet["result"]["decision"]["stable_handoff_eligible"] = False
        packet["result"]["decision"]["next_action"] = "Finalize with --staged or --base-ref before stable handoff."
    return packet


def start_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    mode, base_ref = mode_from_args(args)
    output = Path(args.output)
    packet = {
        "meta": {
            "packet_id": packet_id(),
            "schema_version": SCHEMA_VERSION,
            "lifecycle": "start",
            "mode": mode,
            "created_at": today(),
            "finalized_at": None,
        },
        "input": {
            "intent": args.intent,
            "actor": args.actor,
            "source_refs": args.source_ref or [],
            "user_judgment": {},
        },
        "result": {
            "inference": {
                "status": "pending-finalize",
                "changed_paths": [],
                "intended_scope": args.intent,
                "actual_scope": "Not computed until finalize.",
                "deviations": [],
                "isolation": "pending-finalize",
                "required_evidence": [],
                "required_review": [],
            },
            "evidence": {
                "baseline_ref": base_ref if mode == "base-ref" else "HEAD",
                "before_refs": [],
                "after_refs": [],
                "skipped": [],
            },
            "judgment": {
                "reviews": [],
                "waivers": [],
                "downgrades": [],
                "residual_risk": [],
            },
            "decision": {
                "accepted": None,
                "stable_handoff_eligible": False,
                "reason": "Start packet only; finalization has not run.",
                "next_action": "Run finalize before stable handoff.",
            },
        },
    }
    errors = validate_packet(packet, root=root)
    if errors:
        raise PacketError("; ".join(errors))
    write_packet(root / output if not output.is_absolute() else output, packet)
    print(f"wrote start packet: {output}")
    return 0


def finalize_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    mode, base_ref = mode_from_args(args)
    path = Path(args.packet)
    packet_path = root / path if not path.is_absolute() else path
    packet = load_packet(packet_path)
    if packet["meta"].get("lifecycle") != "start":
        raise PacketError(f"{packet_path}: finalize requires lifecycle start")
    if packet["meta"].get("mode") != mode:
        raise PacketError(f"{packet_path}: finalize mode must match packet mode")
    if mode == "base-ref":
        packet_base_ref = packet["result"].get("evidence", {}).get("baseline_ref")
        if packet_base_ref != base_ref:
            raise PacketError(f"{packet_path}: finalize base-ref must match start baseline_ref: {packet_base_ref}")
    packet = infer_packet_result(root, packet, mode=mode, base_ref=base_ref)
    errors = validate_packet(packet, root=root)
    if errors:
        raise PacketError("; ".join(errors))
    write_packet(packet_path, packet, overwrite=True)
    print(f"finalized packet: {path}")
    return 0


def check_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = Path(args.packet)
    packet_path = root / path if not path.is_absolute() else path
    packet = load_packet(packet_path)
    try:
        packet_ref = packet_path.resolve().relative_to(root).as_posix()
    except ValueError:
        packet_ref = packet_path.resolve().as_posix()
    errors = validate_packet(
        packet,
        require_stable=args.require_stable,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=file_sha256(packet_path),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    stable = packet["result"]["decision"].get("stable_handoff_eligible") is True
    status = "STABLE" if stable else "VALID: not stable-handoff eligible"
    print(f"{status}: {packet_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--output", required=True)
    start.add_argument("--intent", required=True)
    start.add_argument("--actor", default="codex")
    start.add_argument("--source-ref", action="append")
    start.add_argument("--staged", action="store_true")
    start.add_argument("--worktree", action="store_true")
    start.add_argument("--base-ref")
    start.set_defaults(func=start_packet)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--packet", required=True)
    finalize.add_argument("--staged", action="store_true")
    finalize.add_argument("--worktree", action="store_true")
    finalize.add_argument("--base-ref")
    finalize.set_defaults(func=finalize_packet)

    check = subparsers.add_parser("check")
    check.add_argument("--packet", required=True)
    check.add_argument("--require-stable", action="store_true")
    check.set_defaults(func=check_packet)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
