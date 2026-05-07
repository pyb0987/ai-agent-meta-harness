#!/usr/bin/env python3
"""Create and validate v2 AcceptancePacket skeletons."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "v2.0-draft"
PACKET_KEY = "AcceptancePacket"
PUBLIC_SECTIONS = ("meta", "input", "result")
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
    "n/a",
    "na",
    "ok",
    "checked",
    "generic",
    "not applicable",
    "self-attested",
    "self attested",
    "read the plan",
}
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
    if isinstance(value, dt.date):
        return True
    if isinstance(value, str):
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            return False
        return True
    return False


def required_targets(packet: dict) -> tuple[set[str], set[str]]:
    inference = packet["result"]["inference"]
    return set(inference.get("required_evidence", [])), set(inference.get("required_review", []))


def checker_required_evidence(packet: dict) -> set[str]:
    meta = packet["meta"]
    inference = packet["result"]["inference"]
    evidence = packet["result"]["evidence"]
    mode = meta.get("mode")
    comparison_ref = evidence.get("comparison_ref")
    changed_paths = [path for path in inference.get("changed_paths", []) if isinstance(path, str)]
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


def path_mentions_scope_boundary(root: Path, path: str) -> bool:
    lowered_path = path.casefold()
    if path.startswith("archive/v1/"):
        return False
    if "multi-review" in lowered_path or "review" in lowered_path:
        return True
    if any(marker in lowered_path for marker in ("waiver", "downgrade", "not-required", "not_required")):
        return True
    if not path.endswith(".md"):
        return False
    try:
        text = (root / path).read_text(encoding="utf-8").casefold()
    except OSError:
        return False
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


def checker_required_review(packet: dict, *, root: Path = ROOT) -> set[str]:
    result = packet.get("result", {})
    inference = result.get("inference", {}) if isinstance(result, dict) else {}
    changed_paths = [path for path in inference.get("changed_paths", []) if isinstance(path, str)]
    required: set[str] = set()

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

    if any(path_mentions_scope_boundary(root, path) for path in changed_paths):
        required.add("scope boundary")

    if any(path.endswith(".md") and path_has_proof_like_claim(root, path) for path in changed_paths):
        required.add("claim evidence")

    return required


def exception_target(record: dict) -> tuple[str, str] | None:
    targets = [(field, record[field]) for field in ("evidence", "review", "from") if record.get(field)]
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
    for field in PROVENANCE_FIELDS:
        if not record.get(field):
            errors.append(f"{source}: {field} is required")
    if record.get("date") and not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    return errors


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
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_provenance_record(record, source=source))
    if errors and not isinstance(record, dict):
        return errors
    target = exception_target(record)
    if target is None:
        errors.append(f"{source}: exception must target exactly one required evidence/review item")
        return errors
    field, value = target
    kind = record.get("kind")
    if field == "from":
        if kind not in {"evidence", "review"}:
            errors.append(f"{source}: downgrade kind must be evidence or review")
        elif not target_allowed(field, value, required_evidence, required_review, kind=kind):
            errors.append(f"{source}: {kind} downgrade target is not required: {value}")
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
        if not record.get(field):
            errors.append(f"{source}: {field} is required")
    if errors:
        return errors
    if record["origin"] not in RESOLVED_REF_ORIGINS:
        errors.append(f"{source}: origin must be input or generated")
    if record["relation"] not in RESOLVED_REF_RELATIONS:
        errors.append(f"{source}: relation is invalid: {record['relation']}")
    if record["relation"] == "artifact" and not str(record["ref"]).startswith("file:"):
        errors.append(f"{source}: artifact refs must use file: scheme")
    if record["relation"] == "trace" and not str(record["ref"]).startswith("trace:"):
        errors.append(f"{source}: trace refs must use trace: scheme")
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
        if isinstance(record, dict):
            index.setdefault((record.get("relation"), record.get("ref")), []).append(record)
    return index


def has_resolved_relation(
    index: dict[tuple[str, str], list[dict]],
    *,
    relation: str,
    ref: str,
    origin: str | None = None,
) -> bool:
    return any(
        record.get("status") == "resolved" and (origin is None or record.get("origin") == origin)
        for record in index.get((relation, ref), [])
    )


def command_base_ref(command: str) -> str | None:
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


def artifact_records_command(
    root: Path,
    artifact_ref: str,
    command: str,
    status: str,
    *,
    packet_id: str,
    packet_ref: str,
    packet_sha256: str,
) -> bool:
    text = artifact_text(root, artifact_ref)
    if text is None:
        return False
    return field_section_records_values(
        text,
        {
            "packet_id": packet_id,
            "packet_ref": packet_ref,
            "packet_sha256": packet_sha256,
            "command": command,
            "status": status,
        },
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
    normalized = " ".join(str(value).strip().strip("\"'").casefold().split())
    return normalized


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


def sorted_string_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if isinstance(value, str) and value})


def canonical_json_bytes(value: object) -> bytes:
    def normalize(item: object) -> object:
        if isinstance(item, dt.datetime):
            return item.date().isoformat()
        if isinstance(item, dt.date):
            return item.isoformat()
        if isinstance(item, dict):
            return {str(key): normalize(item[key]) for key in sorted(item)}
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
        for record in wrapper.get("review_lineage", []):
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
        return {key: normalize_for_mirror(value[key]) for key in sorted(value)}
    return value


def validate_review_lineage_record(record: object, *, source: str, import_source_ref: str, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: review lineage record must be a mapping"]
    if set(record) != REVIEW_LINEAGE_FIELDS:
        missing = sorted(REVIEW_LINEAGE_FIELDS - set(record))
        extra = sorted(set(record) - REVIEW_LINEAGE_FIELDS)
        if missing:
            errors.append(f"{source}: missing fields: {missing}")
        if extra:
            errors.append(f"{source}: extra fields: {extra}")
    for field in ("review_id", "critic", "scope", "anti_scope", "actor", "role", "source_ref"):
        if not review_value_is_substantive(record.get(field)):
            errors.append(f"{source}: {field} is required")
    if record.get("source_ref") != import_source_ref:
        errors.append(f"{source}: source_ref must match review import source_ref: {import_source_ref}")
    if record.get("date") and not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    score = record.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 10:
        errors.append(f"{source}: score must be an integer from 1 to 10")
    if not isinstance(record.get("veto"), bool):
        errors.append(f"{source}: veto must be a boolean")
    for field in ("false_green_risk", "invariant_checked"):
        if not review_value_is_substantive(record.get(field)):
            errors.append(f"{source}: {field} must be substantive")
    if not isinstance(record.get("evidence"), list) or not review_value_is_substantive(record.get("evidence")):
        errors.append(f"{source}: evidence must be a non-empty substantive list")
    source_refs = record.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append(f"{source}: source_refs must be a non-empty list")
    else:
        for index, ref in enumerate(source_refs):
            if not isinstance(ref, str) or not review_value_is_substantive(ref):
                errors.append(f"{source}: source_refs[{index}] must be a non-empty string")
            elif resolve_ref(root, ref) is None:
                errors.append(f"{source}: source_refs[{index}] does not resolve: {ref}")
    if not isinstance(record.get("blocking_findings"), list):
        errors.append(f"{source}: blocking_findings must be a list")
    else:
        for index, finding in enumerate(record["blocking_findings"]):
            if not isinstance(finding, dict):
                errors.append(f"{source}: blocking_findings[{index}] must be a mapping with finding_id and summary")
                continue
            if not review_value_is_substantive(finding.get("finding_id")):
                errors.append(f"{source}: blocking_findings[{index}].finding_id is required")
            if not review_value_is_substantive(finding.get("summary")):
                errors.append(f"{source}: blocking_findings[{index}].summary is required")
    if review_is_blocking(record) and not finding_ids(record):
        errors.append(f"{source}: blocking review requires blocking_findings with stable finding_id values")
    if score == 9:
        if not review_value_is_substantive(record.get("why_not_10")):
            errors.append(f"{source}: score 9 requires why_not_10")
        if not review_value_is_substantive(record.get("disposition")):
            errors.append(f"{source}: score 9 requires disposition")
    fixed = record.get("fixed_finding_ids")
    if not isinstance(fixed, list):
        errors.append(f"{source}: fixed_finding_ids must be a list")
    elif any(not isinstance(item, str) or not review_value_is_substantive(item) for item in fixed):
        errors.append(f"{source}: fixed_finding_ids must contain only substantive string ids")
    if record.get("rerun_of"):
        if not isinstance(record.get("rerun_of"), str):
            errors.append(f"{source}: rerun_of must be a review_id string")
        if not fixed:
            errors.append(f"{source}: rerun requires fixed_finding_ids")
    elif fixed:
        errors.append(f"{source}: fixed_finding_ids require rerun_of")
    return errors


def validate_review_lineage_closure(lineage: list[dict], *, source: str) -> tuple[set[str], list[str]]:
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
        fixed = set(record.get("fixed_finding_ids", []))
        if not target_findings:
            errors.append(f"{source}: rerun target {target_id} has no stable finding ids")
            continue
        if fixed != target_findings:
            errors.append(f"{source}: rerun {rerun_id} fixed_finding_ids must exactly cover {target_id}: {sorted(target_findings)}")
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

    open_passing = {
        record["critic"]
        for record in lineage
        if isinstance(record, dict)
        and isinstance(record.get("critic"), str)
        and review_is_open_passing(record, closed_blocking_ids)
    }
    return open_passing, errors


def validate_review_imports(
    packet: dict,
    *,
    root: Path,
    packet_ref: str | None,
    packet_sha256: str | None,
    ref_index: dict[tuple[str, str], list[dict]],
) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    evidence = packet["result"]["evidence"]
    packet_reviews = packet["result"]["judgment"].get("reviews", [])
    imports = evidence.get("review_imports", [])
    if not isinstance(imports, list):
        return set(), ["result.evidence.review_imports must be a list"]
    if packet_reviews and not imports:
        return set(), ["stable packet reviews require result.evidence.review_imports"]

    expected_binding = review_target_binding(packet, root=root, packet_ref=packet_ref)
    imported_source_refs: set[str] = set()
    imported_lineage_by_id: dict[str, dict] = {}
    open_passing_reviews: set[str] = set()
    for import_index, import_record in enumerate(imports):
        source = f"result.evidence.review_imports[{import_index}]"
        if not isinstance(import_record, dict):
            errors.append(f"{source}: review import must be a mapping")
            continue
        if set(import_record) != REVIEW_IMPORT_RECORD_FIELDS:
            missing = sorted(REVIEW_IMPORT_RECORD_FIELDS - set(import_record))
            extra = sorted(set(import_record) - REVIEW_IMPORT_RECORD_FIELDS)
            if missing:
                errors.append(f"{source}: missing fields: {missing}")
            if extra:
                errors.append(f"{source}: extra fields: {extra}")
        source_ref = import_record.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref:
            errors.append(f"{source}: source_ref is required")
            continue
        imported_source_refs.add(source_ref)
        if import_record.get("format") != REVIEW_IMPORT_SCHEMA_VERSION:
            errors.append(f"{source}: format must be {REVIEW_IMPORT_SCHEMA_VERSION}")
        if import_record.get("status") != "imported":
            errors.append(f"{source}: status must be imported")
        if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref):
            errors.append(f"{source}: source_ref lacks resolved review-provenance relation: {source_ref}")
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
        if set(wrapper) != REVIEW_IMPORT_FIELDS:
            missing = sorted(REVIEW_IMPORT_FIELDS - set(wrapper))
            extra = sorted(set(wrapper) - REVIEW_IMPORT_FIELDS)
            if missing:
                errors.append(f"{source}: wrapper missing fields: {missing}")
            if extra:
                errors.append(f"{source}: wrapper extra fields: {extra}")
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
        if not isinstance(review_ids, list) or sorted(review_ids) != sorted(ids):
            errors.append(f"{source}: review_ids must match imported review_lineage ids")
        for record in lineage:
            if isinstance(record, dict) and isinstance(record.get("review_id"), str):
                review_id = record["review_id"]
                if review_id in imported_lineage_by_id:
                    errors.append(f"{source}: duplicate imported review_id across imports: {review_id}")
                imported_lineage_by_id[review_id] = record
        passing, closure_errors = validate_review_lineage_closure(lineage, source=source)
        open_passing_reviews |= passing
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
        if review.get("source_ref") not in imported_source_refs:
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


def git_ref_commit(root: Path, ref: str) -> str | None:
    result = git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    return result.stdout.strip() if result.returncode == 0 else None


def same_git_boundary(root: Path, left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    left_commit = git_ref_commit(root, left)
    right_commit = git_ref_commit(root, right)
    return left_commit is not None and left_commit == right_commit


def provenance_source_refs(packet: dict) -> list[tuple[str, str]]:
    result = packet["result"]
    refs: list[tuple[str, str]] = []
    for source, records in (
        ("result.evidence.skipped", result["evidence"].get("skipped", [])),
        ("result.judgment.waivers", result["judgment"].get("waivers", [])),
        ("result.judgment.downgrades", result["judgment"].get("downgrades", [])),
        ("result.judgment.residual_risk", result["judgment"].get("residual_risk", [])),
    ):
        for index, record in enumerate(records):
            if isinstance(record, dict) and record.get("source_ref"):
                refs.append((f"{source}[{index}]", record["source_ref"]))
    return refs


def review_source_refs(packet: dict) -> list[tuple[str, str, dict]]:
    refs: list[tuple[str, str, dict]] = []
    for index, record in enumerate(packet["result"]["judgment"].get("reviews", [])):
        if isinstance(record, dict) and record.get("source_ref"):
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
    if lifecycle not in LIFECYCLES:
        errors.append(f"meta.lifecycle is invalid: {lifecycle}")
    if mode not in MODES:
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
        if not isinstance(inference.get("changed_paths"), list):
            errors.append("result.inference.changed_paths must be a list")
        if not isinstance(inference.get("deviations"), list):
            errors.append("result.inference.deviations must be a list")
        if not isinstance(inference.get("required_evidence"), list):
            errors.append("result.inference.required_evidence must be a list")
        if not isinstance(inference.get("required_review"), list):
            errors.append("result.inference.required_review must be a list")
        if not isinstance(inference.get("protected_boundary_changed"), bool):
            errors.append("result.inference.protected_boundary_changed must be a boolean")
        protected_paths = [path for path in inference.get("changed_paths", []) if requires_review_for_path(path)]
        if protected_paths:
            if inference.get("protected_boundary_changed") is not True:
                errors.append("protected changed paths require protected_boundary_changed: true")
            if inference.get("change_class") != "harness-affecting":
                errors.append("protected changed paths require change_class: harness-affecting")
            if inference.get("impact") != "high":
                errors.append("protected changed paths require impact: high")

    for key, request in input_data["user_judgment"].items():
        if "waiver" in key or "downgrade" in key:
            errors.extend(
                validate_exception_record(
                    request,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"input.user_judgment.{key}",
                )
            )
        elif "skipped" in key:
            errors.extend(validate_provenance_record(request, source=f"input.user_judgment.{key}"))
            if isinstance(request, dict):
                evidence_target = request.get("evidence")
                if not evidence_target:
                    errors.append(f"input.user_judgment.{key}: evidence is required")
                elif evidence_target not in required_evidence:
                    errors.append(f"input.user_judgment.{key}: skipped evidence is not required: {evidence_target}")
        elif "residual" in key:
            errors.extend(validate_provenance_record(request, source=f"input.user_judgment.{key}"))

    for waiver in judgment.get("waivers", []):
        errors.extend(
            validate_exception_record(
                waiver,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.waivers",
            )
        )
    for downgrade in judgment.get("downgrades", []):
        errors.extend(
            validate_exception_record(
                downgrade,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.downgrades",
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

    reviews = judgment.get("reviews", [])
    for review in reviews:
        score = review.get("score")
        if stable and not review.get("review_id"):
            errors.append("stable review requires review_id")
        if stable and not review.get("rerun_of"):
            errors.extend(validate_review_record(review, source="result.judgment.reviews"))
        if isinstance(score, (int, float)) and score == 9:
            if not review.get("why_not_10") or not review.get("disposition"):
                errors.append("score 9 review requires why_not_10 and disposition")

    if stable:
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
            if ref not in evidence_source_refs:
                errors.append(f"stable packet input source_ref missing from evidence.source_refs: {ref}")
            if not has_resolved_relation(ref_index, relation="source", ref=ref, origin="input"):
                errors.append(f"stable packet input source_ref lacks resolved input source relation: {ref}")
        for ref in evidence_source_refs:
            if not has_resolved_relation(ref_index, relation="source", ref=ref):
                errors.append(f"stable packet source_ref lacks resolved source relation: {ref}")
        source_targets = resolved_targets(resolved_refs, relation="source")
        changed_paths = {
            path for path in inference.get("changed_paths", []) if isinstance(path, str)
        }
        missing_changed_sources = sorted(path for path in changed_paths if path not in source_targets)
        if missing_changed_sources:
            errors.append(f"stable packet changed_paths lack resolved source refs: {missing_changed_sources}")
        protected_source_targets = sorted(
            target for target in source_targets if requires_review_for_path(target) and target not in changed_paths
        )
        if protected_source_targets:
            errors.append(
                f"stable packet source_ref points to protected path outside changed_paths: {protected_source_targets}"
            )

        for boundary_ref_name in ("baseline_ref", "comparison_ref"):
            boundary_ref = evidence.get(boundary_ref_name)
            if not boundary_ref:
                errors.append(f"stable packet {boundary_ref_name} is required")
            elif resolve_ref(root, f"git:{boundary_ref}") is None:
                errors.append(f"stable packet {boundary_ref_name} does not resolve: {boundary_ref}")

        for source, source_ref in provenance_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="waiver-provenance", ref=source_ref):
                errors.append(f"{source}: source_ref lacks resolved waiver-provenance relation: {source_ref}")
        for source, source_ref, review in review_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref):
                errors.append(f"{source}: source_ref lacks resolved review-provenance relation: {source_ref}")
            elif ref_is_acceptance_packet(root, source_ref):
                errors.append(f"{source}: review-provenance source_ref cannot be an acceptance packet: {source_ref}")
            elif not review_source_ref_records_review(root, source_ref, review, packet_id=meta["packet_id"]):
                errors.append(f"{source}: review-provenance source_ref lacks matching review record: {source_ref}")

        protected_review_required = (
            inference.get("protected_boundary_changed") is True
            or inference.get("change_class") == "harness-affecting"
            or inference.get("impact") == "high"
            or any(requires_review_for_path(path) for path in inference.get("changed_paths", []))
        )
        if protected_review_required and not required_review:
            errors.append("stable protected or high-impact packet must infer required review")

        passed_evidence = {
            item.get("command")
            for item in evidence.get("command_results", [])
            if item.get("status") == "pass" and item.get("command")
        }
        for item in evidence.get("command_results", []):
            if item.get("status") != "pass":
                continue
            base_ref = command_base_ref(item.get("command", ""))
            if base_ref:
                for boundary_ref_name in ("baseline_ref", "comparison_ref"):
                    if not same_git_boundary(root, evidence.get(boundary_ref_name), base_ref):
                        errors.append(
                            f"stable command base-ref {base_ref} must match evidence.{boundary_ref_name}: "
                            f"{evidence.get(boundary_ref_name)}"
                        )
            artifact_ref = item.get("artifact_ref")
            if not artifact_ref:
                errors.append(f"stable command evidence lacks artifact_ref: {item.get('command')}")
            elif str(artifact_ref).startswith("terminal:"):
                errors.append(f"terminal placeholder cannot satisfy stable evidence: {artifact_ref}")
            elif not str(artifact_ref).startswith("file:"):
                errors.append(f"stable command artifact_ref must use file: scheme: {artifact_ref}")
            elif not has_resolved_relation(ref_index, relation="artifact", ref=artifact_ref):
                errors.append(f"stable command artifact lacks resolved artifact relation: {artifact_ref}")
            elif not artifact_records_command(
                root,
                artifact_ref,
                item.get("command", ""),
                item.get("status", ""),
                packet_id=meta["packet_id"],
                packet_ref=packet_ref or "",
                packet_sha256=packet_sha256 or "",
            ):
                errors.append(f"stable command artifact does not record command evidence: {artifact_ref}")

        if protected_review_required:
            trace_refs = evidence.get("trace_refs", {})
            if isinstance(trace_refs, dict):
                search_set_before = trace_refs.get("search_set_before")
                search_set_after = trace_refs.get("search_set_after")
                if search_set_before and search_set_before == search_set_after:
                    errors.append(
                        "stable protected packet search_set_before and search_set_after must be distinct or explicitly skipped"
                    )
            for trace_name in ("search_set_before", "search_set_after"):
                trace_ref = trace_refs.get(trace_name) if isinstance(trace_refs, dict) else None
                skipped_targets = {
                    item.get("evidence")
                    for item in evidence.get("skipped", [])
                    if isinstance(item, dict) and item.get("evidence")
                }
                if not trace_ref and trace_name in skipped_targets:
                    continue
                if not trace_ref:
                    errors.append(f"stable protected packet missing {trace_name}")
                elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref):
                    errors.append(f"stable protected packet {trace_name} lacks resolved trace relation: {trace_ref}")

        for skipped in evidence.get("skipped", []):
            errors.extend(validate_provenance_record(skipped, source="result.evidence.skipped"))
            evidence_target = skipped.get("evidence") if isinstance(skipped, dict) else None
            allowed_skips = required_evidence | {"search_set_before", "search_set_after"}
            if not evidence_target:
                errors.append("result.evidence.skipped: evidence is required")
            elif evidence_target not in allowed_skips:
                errors.append(f"result.evidence.skipped: skipped evidence is not required: {evidence_target}")

        proof_like_paths = [
            path
            for path in inference.get("changed_paths", [])
            if path.endswith(".md") and path_has_proof_like_claim(root, path)
        ]
        claims = evidence.get("claims", [])
        if proof_like_paths and not claims:
            errors.append(f"stable packet has proof-like changed docs without claim evidence: {proof_like_paths}")
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
                elif not has_resolved_relation(ref_index, relation="claim-evidence", ref=raw_ref):
                    errors.append(f"claim evidence ref lacks resolved claim-evidence relation: {raw_ref}")
                elif raw_ref.startswith("file:") and not is_raw_claim_file_ref(root, raw_ref):
                    errors.append(
                        "claim evidence file ref must point to raw artifact/log/screenshot/report evidence: "
                        f"{raw_ref}"
                    )

        passed_evidence_records = [
            item.get("command")
            for item in evidence.get("command_results", [])
            if item.get("status") == "pass" and item.get("command")
        ]
        waived_evidence_records = [item.get("evidence") for item in judgment.get("waivers", []) if item.get("evidence")]
        downgraded_evidence_records = [
            item.get("from")
            for item in judgment.get("downgrades", [])
            if item.get("kind") == "evidence" and item.get("from")
        ]
        skipped_evidence_records = [
            item.get("evidence")
            for item in evidence.get("skipped", [])
            if isinstance(item, dict) and item.get("evidence") in required_evidence
        ]
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
        waived_review_records = [item.get("review") for item in judgment.get("waivers", []) if item.get("review")]
        downgraded_review_records = [
            item.get("from")
            for item in judgment.get("downgrades", [])
            if item.get("kind") == "review" and item.get("from")
        ]
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
        missing_reviews = required_review - open_passing_review_targets - waived_reviews - downgraded_reviews
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


def is_protected(path: str) -> bool:
    return path in PROTECTED_PATHS or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


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

    packet["meta"]["lifecycle"] = "finalized"
    packet["meta"]["finalized_at"] = today()
    packet["result"] = {
        "inference": {
            "change_class": change_class,
            "impact": "high" if protected else "low",
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
            "skipped": [],
        },
        "judgment": packet["result"].get(
            "judgment",
            {"reviews": [], "waivers": [], "downgrades": [], "residual_risk": []},
        ),
        "decision": {
            "accepted": diff_status == "pass" and not protected,
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
