#!/usr/bin/env python3
"""Validate MultiReviewResult artifact-internal consistency and derive verdicts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RESULT_KEY = "MultiReviewResult"
SCHEMA_VERSION = "multi-review-result/v1"
PROBE_TRANSCRIPT_KEY = "ProbeTranscript"
PROBE_TRANSCRIPT_SCHEMA_VERSION = "probe-transcript/v1"

TOP_LEVEL_FIELDS = {
    "schema_version",
    "review_id",
    "lifecycle",
    "review_mode",
    "independence",
    "target",
    "required_critics",
    "critics",
    "reported_final_verdict",
    "derived_verdict",
    "derivation_errors",
}
CRITIC_FIELDS = {
    "critic_id",
    "name",
    "critic_type",
    "persona",
    "scope",
    "anti_scope",
    "attack_surface",
    "primary_failure_mode",
    "frame_challenge",
    "required",
    "actor",
    "date",
    "score",
    "verdict",
    "veto",
    "blocking_findings",
    "false_green_risk",
    "invariant_checked",
    "validation_layer",
    "probe_run",
    "probe_command",
    "probe_exit_code",
    "probe_result",
    "probe_interpretation",
    "probe_evidence_refs",
    "reason_no_probe",
    "evidence",
    "source_refs",
    "why_not_10",
    "residual_risk_disposition",
}
LIFECYCLES = {"draft", "finalized"}
REVIEW_MODES = {"governance", "advisory"}
INDEPENDENCE_MODES = {"independent", "fallback_nonindependent"}
CRITIC_TYPES = {"validation_layer", "review_quality", "domain", "other"}
CRITIC_VERDICTS = {"pass", "concern", "veto"}
VALIDATION_LAYERS = {
    "structured-validator",
    "raw-artifact",
    "derived-verdict",
    "prose-smoke",
    "wrong-layer",
}
PRIMARY_VALIDATION_LAYERS = {"structured-validator", "raw-artifact", "derived-verdict"}
DERIVED_VERDICTS = {"PASS", "ADVISORY_PASS", "VETO", "INCOMPLETE", "FALLBACK_NONINDEPENDENT"}
REPORTED_ACCEPTANCE_VERDICTS = {"PASS", "ADVISORY_PASS"}
REPORTED_DRAFT_VERDICTS = {"DRAFT", "INCOMPLETE"}
TARGET_FIELDS = {"summary", "source_refs"}
PROBE_TRANSCRIPT_FIELDS = {
    "schema_version",
    "probe_command",
    "probe_exit_code",
    "result_ref",
    "result_digest",
    "packet_ref",
    "packet_sha256",
    "source_refs",
    "cwd",
    "generated_by",
    "date",
    "stdout",
    "stderr",
    "stdout_sha256",
    "stderr_sha256",
}
VACUOUS_VALUES = {
    "",
    "none",
    "na",
    "ok",
    "checked",
    "generic",
    "notapplicable",
    "pass",
    "readtheplan",
    "readplan",
    "notrun",
    "notexecuted",
    "didnotrun",
    "noproberun",
    "selfattested",
    "definitelynotarealcommandshouldfail",
    "existingreviewsayspass",
    "existingacceptancesayspass",
}


class MultiReviewError(ValueError):
    pass


def sorted_key_names(keys: Any) -> list[str]:
    return sorted(str(key) for key in keys)


def validate_exact_fields(
    mapping: dict[Any, Any],
    *,
    expected: set[str],
    source: str,
    errors: list[str],
) -> None:
    string_keys = {key for key in mapping if isinstance(key, str)}
    missing = sorted(expected - string_keys)
    extra = sorted_key_names(key for key in mapping if not isinstance(key, str) or key not in expected)
    if missing:
        error(errors, source, f"missing fields: {missing}")
    if extra:
        error(errors, source, f"extra fields: {extra}")


def normalize_text(value: str) -> str:
    normalized = " ".join(value.strip().strip("\"'").casefold().split())
    return re.sub(r"[^a-z0-9]+", "", normalized)


def is_substantive(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return normalize_text(value) not in VACUOUS_VALUES
    if isinstance(value, dt.date):
        return True
    if isinstance(value, list):
        return any(is_substantive(item) for item in value)
    if isinstance(value, dict):
        return any(is_substantive(item) for item in value.values())
    return False


def is_substantive_string(value: Any) -> bool:
    return isinstance(value, str) and is_substantive(value)


def date_like(value: Any) -> bool:
    if isinstance(value, dt.datetime):
        return False
    if isinstance(value, dt.date):
        return value <= dt.date.today()
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        return False
    return parsed <= dt.date.today()


def resolve_repo_path(root: Path, ref_path: str) -> str | None:
    path = Path(ref_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (root / path).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    if not candidate.is_file():
        return None
    return candidate.relative_to(root_resolved).as_posix()


def resolve_source_ref(root: Path, ref: str) -> str | None:
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("file:"):
        return resolve_repo_path(root, ref.removeprefix("file:"))
    if "://" in ref or ":" in ref:
        return None
    return resolve_repo_path(root, ref)


def resolve_probe_transcript_ref(root: Path, ref: str) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("file:"):
        return None
    return resolve_repo_path(root, ref.removeprefix("file:"))


def load_result(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MultiReviewError(f"{path}: cannot read result: {exc}") from exc
    try:
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise MultiReviewError(f"{path}: invalid result syntax: {exc}") from exc
    if not isinstance(loaded, dict) or RESULT_KEY not in loaded:
        raise MultiReviewError(f"{path}: missing {RESULT_KEY}")
    result = loaded[RESULT_KEY]
    if not isinstance(result, dict):
        raise MultiReviewError(f"{path}: {RESULT_KEY} must be a mapping")
    return result


def error(errors: list[str], source: str, message: str) -> None:
    errors.append(f"{source}: {message}")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def validate_top_level(result: dict[str, Any], errors: list[str]) -> None:
    validate_exact_fields(result, expected=TOP_LEVEL_FIELDS, source="MultiReviewResult", errors=errors)
    if result.get("schema_version") != SCHEMA_VERSION:
        error(errors, "MultiReviewResult.schema_version", f"must be {SCHEMA_VERSION}")
    if not isinstance(result.get("review_id"), str) or not is_substantive(result.get("review_id")):
        error(errors, "MultiReviewResult.review_id", "must be a substantive string")
    reported_final_verdict = result.get("reported_final_verdict")
    reported_verdict = (
        reported_final_verdict.strip().upper().replace("-", "_").replace(" ", "_")
        if isinstance(reported_final_verdict, str)
        else None
    )
    lifecycle = result.get("lifecycle")
    review_mode = result.get("review_mode")
    if not isinstance(reported_final_verdict, str) or not reported_final_verdict.strip():
        error(errors, "MultiReviewResult.reported_final_verdict", "must be a non-empty string")
    elif lifecycle == "draft":
        if reported_verdict not in REPORTED_DRAFT_VERDICTS:
            error(
                errors,
                "MultiReviewResult.reported_final_verdict",
                f"must be a draft verdict for draft lifecycle: {sorted(REPORTED_DRAFT_VERDICTS)}",
            )
    elif reported_verdict not in REPORTED_ACCEPTANCE_VERDICTS:
        error(
            errors,
            "MultiReviewResult.reported_final_verdict",
            f"must be an acceptance verdict: {sorted(REPORTED_ACCEPTANCE_VERDICTS)}",
        )
    elif review_mode == "governance" and reported_verdict != "PASS":
        error(errors, "MultiReviewResult.reported_final_verdict", "must be PASS for governance review_mode")
    elif review_mode == "advisory" and reported_verdict != "ADVISORY_PASS":
        error(errors, "MultiReviewResult.reported_final_verdict", "must be ADVISORY_PASS for advisory review_mode")
    if not isinstance(result.get("lifecycle"), str) or result.get("lifecycle") not in LIFECYCLES:
        error(errors, "MultiReviewResult.lifecycle", "must be draft or finalized")
    if not isinstance(result.get("review_mode"), str) or result.get("review_mode") not in REVIEW_MODES:
        error(errors, "MultiReviewResult.review_mode", "must be governance or advisory")
    if not isinstance(result.get("independence"), str) or result.get("independence") not in INDEPENDENCE_MODES:
        error(errors, "MultiReviewResult.independence", "must be independent or fallback_nonindependent")
    if not isinstance(result.get("required_critics"), list) or not result.get("required_critics"):
        error(errors, "MultiReviewResult.required_critics", "must be a non-empty list")
    elif not all(isinstance(critic_id, str) and is_substantive(critic_id) for critic_id in result["required_critics"]):
        error(errors, "MultiReviewResult.required_critics", "must contain only non-empty string ids")
    if not isinstance(result.get("critics"), list) or not result.get("critics"):
        error(errors, "MultiReviewResult.critics", "must be a non-empty list")
    if not isinstance(result.get("derivation_errors"), list):
        error(errors, "MultiReviewResult.derivation_errors", "must be a list")
    elif result.get("derivation_errors"):
        error(errors, "MultiReviewResult.derivation_errors", "must be empty for derived acceptance")
    stored_verdict = result.get("derived_verdict")
    if stored_verdict is not None and (
        not isinstance(stored_verdict, str) or stored_verdict not in DERIVED_VERDICTS
    ):
        error(errors, "MultiReviewResult.derived_verdict", f"must be null or one of {sorted(DERIVED_VERDICTS)}")


def validate_source_refs(refs: Any, *, source: str, errors: list[str]) -> None:
    if not isinstance(refs, list) or not refs:
        error(errors, source, "must be a non-empty list")
        return
    for index, ref in enumerate(refs):
        item_source = f"{source}[{index}]"
        if not isinstance(ref, str) or not is_substantive(ref):
            error(errors, item_source, "must be a non-empty string ref")
        elif resolve_source_ref(ROOT, ref) is None:
            error(errors, item_source, f"must resolve to an existing repository-local file: {ref}")


def validate_probe_evidence_refs(refs: Any, *, source: str, errors: list[str]) -> None:
    if not isinstance(refs, list) or not refs:
        error(errors, source, "must be a non-empty list")
        return
    for index, ref in enumerate(refs):
        item_source = f"{source}[{index}]"
        if not isinstance(ref, str) or not is_substantive(ref):
            error(errors, item_source, "must be a non-empty string ref")
        elif not ref.startswith("file:"):
            error(errors, item_source, f"must use file: scheme for probe transcript artifact refs: {ref}")
        elif resolve_probe_transcript_ref(ROOT, ref) is None:
            error(errors, item_source, f"must resolve to an existing repository-local file: {ref}")
        else:
            transcript = load_probe_transcript(ref)
            if transcript is None:
                error(errors, item_source, f"must be a structured {PROBE_TRANSCRIPT_KEY} artifact: {ref}")
                continue
            for message in probe_transcript_shape_errors(transcript):
                error(errors, item_source, f"invalid probe transcript: {message}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def transcript_cwd_is_repo_root(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value.strip())
    if path.is_absolute():
        return False
    if ".." in path.parts:
        return False
    return (ROOT / path).resolve() == ROOT.resolve()


def load_probe_transcript(ref: str) -> dict[str, Any] | None:
    resolved = resolve_probe_transcript_ref(ROOT, ref)
    if resolved is None:
        return None
    path = ROOT / resolved
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None
    if not isinstance(loaded, dict) or PROBE_TRANSCRIPT_KEY not in loaded:
        return None
    transcript = loaded[PROBE_TRANSCRIPT_KEY]
    return transcript if isinstance(transcript, dict) else None


def probe_transcript_shape_errors(transcript: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(transcript) != PROBE_TRANSCRIPT_FIELDS:
        string_keys = {key for key in transcript if isinstance(key, str)}
        missing = sorted(PROBE_TRANSCRIPT_FIELDS - string_keys)
        extra = sorted_key_names(key for key in transcript if not isinstance(key, str) or key not in PROBE_TRANSCRIPT_FIELDS)
        if missing:
            errors.append(f"missing fields: {missing}")
        if extra:
            errors.append(f"extra fields: {extra}")
        return errors
    if transcript.get("schema_version") != PROBE_TRANSCRIPT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {PROBE_TRANSCRIPT_SCHEMA_VERSION}")
    if not isinstance(transcript.get("probe_command"), str) or not is_substantive(transcript.get("probe_command")):
        errors.append("probe_command must be a substantive string")
    if not isinstance(transcript.get("probe_exit_code"), int) or isinstance(transcript.get("probe_exit_code"), bool):
        errors.append("probe_exit_code must be an integer")
    if not isinstance(transcript.get("result_ref"), str) or not is_substantive(transcript.get("result_ref")):
        errors.append("result_ref must be a substantive string")
    if not is_sha256(transcript.get("result_digest")):
        errors.append("result_digest must be a sha256 hex digest")
    for field in ("packet_ref", "packet_sha256"):
        value = transcript.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{field} must be null or a string")
    if transcript.get("packet_sha256") is not None and not is_sha256(transcript.get("packet_sha256")):
        errors.append("packet_sha256 must be null or a sha256 hex digest")
    if not source_refs_resolve(transcript.get("source_refs")):
        errors.append("source_refs must resolve to repository-local files")
    if not transcript_cwd_is_repo_root(transcript.get("cwd")):
        errors.append("cwd must identify the repository root")
    if not isinstance(transcript.get("generated_by"), str) or not is_substantive(transcript.get("generated_by")):
        errors.append("generated_by must be a substantive string")
    if not date_like(transcript.get("date")):
        errors.append("date must be an ISO date on or before today")
    stdout = transcript.get("stdout")
    stderr = transcript.get("stderr")
    if not isinstance(stdout, str):
        errors.append("stdout must be a string")
    if not isinstance(stderr, str):
        errors.append("stderr must be a string")
    if not is_sha256(transcript.get("stdout_sha256")):
        errors.append("stdout_sha256 must be a sha256 hex digest")
    if not is_sha256(transcript.get("stderr_sha256")):
        errors.append("stderr_sha256 must be a sha256 hex digest")
    if isinstance(stdout, str) and is_sha256(transcript.get("stdout_sha256")):
        if transcript["stdout_sha256"] != sha256_text(stdout):
            errors.append("stdout_sha256 must match stdout")
    if isinstance(stderr, str) and is_sha256(transcript.get("stderr_sha256")):
        if transcript["stderr_sha256"] != sha256_text(stderr):
            errors.append("stderr_sha256 must match stderr")
    return errors


def sorted_string_values(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(item for item in values if isinstance(item, str) and is_substantive(item))


def source_refs_resolve(refs: Any) -> bool:
    if not isinstance(refs, list) or not refs:
        return False
    return all(isinstance(ref, str) and resolve_source_ref(ROOT, ref) is not None for ref in refs)


def transcript_matches_probe(
    transcript: dict[str, Any],
    *,
    command: str,
    exit_code: int,
    result_ref: str | None,
    result_digest: str | None,
    packet_ref: str | None,
    packet_sha256: str | None,
    source_refs: list[str],
) -> bool:
    if probe_transcript_shape_errors(transcript):
        return False
    if transcript.get("probe_command") != command:
        return False
    if transcript.get("probe_exit_code") != exit_code:
        return False
    if result_ref is not None and transcript.get("result_ref") != result_ref:
        return False
    if result_digest is not None and transcript.get("result_digest") != result_digest:
        return False
    if result_digest is None and not is_sha256(transcript.get("result_digest")):
        return False
    if packet_ref is not None:
        if transcript.get("packet_ref") != packet_ref:
            return False
    elif transcript.get("packet_ref") is not None:
        return False
    if packet_sha256 is not None:
        if transcript.get("packet_sha256") != packet_sha256:
            return False
    elif transcript.get("packet_sha256") is not None:
        return False
    transcript_source_refs = transcript.get("source_refs")
    if not source_refs_resolve(transcript_source_refs):
        return False
    if source_refs and sorted_string_values(transcript_source_refs) != source_refs:
        return False
    if not transcript_cwd_is_repo_root(transcript.get("cwd")) or not is_substantive(transcript.get("generated_by")):
        return False
    if not date_like(transcript.get("date")):
        return False
    stdout = transcript.get("stdout")
    stderr = transcript.get("stderr")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        return False
    if not is_sha256(transcript.get("stdout_sha256")) or not is_sha256(transcript.get("stderr_sha256")):
        return False
    return transcript["stdout_sha256"] == sha256_text(stdout) and transcript["stderr_sha256"] == sha256_text(stderr)


def validate_target(target: Any, errors: list[str]) -> None:
    if not isinstance(target, dict):
        error(errors, "MultiReviewResult.target", "must be a mapping")
        return
    validate_exact_fields(target, expected=TARGET_FIELDS, source="MultiReviewResult.target", errors=errors)
    if not is_substantive_string(target.get("summary")):
        error(errors, "MultiReviewResult.target.summary", "must be a substantive string")
    validate_source_refs(target.get("source_refs"), source="MultiReviewResult.target.source_refs", errors=errors)


def critic_source(critic: dict[str, Any], index: int) -> str:
    critic_id = critic.get("critic_id")
    return f"critics[{index}:{critic_id}]" if critic_id else f"critics[{index}]"


def validate_critic_shape(critic: Any, *, index: int, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(critic, dict):
        error(errors, f"critics[{index}]", "critic result must be a mapping")
        return None
    source = critic_source(critic, index)
    validate_exact_fields(critic, expected=CRITIC_FIELDS, source=source, errors=errors)
    string_fields = (
        "critic_id",
        "name",
        "critic_type",
        "persona",
        "scope",
        "anti_scope",
        "attack_surface",
        "primary_failure_mode",
        "actor",
    )
    for field in string_fields:
        if not is_substantive_string(critic.get(field)):
            error(errors, source, f"{field} must be a non-empty string")
    text_fields = (
        "false_green_risk",
        "invariant_checked",
        "probe_command",
        "probe_result",
        "probe_interpretation",
        "why_not_10",
        "residual_risk_disposition",
    )
    for field in text_fields:
        value = critic.get(field)
        if value is not None and not isinstance(value, str):
            error(errors, source, f"{field} must be a string")
    reason_no_probe = critic.get("reason_no_probe")
    if reason_no_probe is not None and not isinstance(reason_no_probe, str):
        error(errors, source, "reason_no_probe must be null or a string")
    if critic.get("probe_run") is True and reason_no_probe is not None:
        error(errors, source, "reason_no_probe must be null when probe_run is true")
    if not is_substantive(critic.get("date")):
        error(errors, source, "date is required")
    if not isinstance(critic.get("frame_challenge"), bool):
        error(errors, source, "frame_challenge must be a boolean")
    if is_substantive(critic.get("date")) and not date_like(critic.get("date")):
        error(errors, source, "date must be an ISO date on or before today")
    critic_type = critic.get("critic_type")
    if not isinstance(critic_type, str) or critic_type not in CRITIC_TYPES:
        error(errors, source, f"critic_type is invalid: {critic.get('critic_type')}")
    if not isinstance(critic.get("required"), bool):
        error(errors, source, "required must be a boolean")
    score = critic.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 10:
        error(errors, source, "score must be an integer from 1 to 10")
    verdict = critic.get("verdict")
    if not isinstance(verdict, str) or verdict not in CRITIC_VERDICTS:
        error(errors, source, f"verdict is invalid: {critic.get('verdict')}")
    if not isinstance(critic.get("veto"), bool):
        error(errors, source, "veto must be a boolean")
    if not isinstance(critic.get("blocking_findings"), list):
        error(errors, source, "blocking_findings must be a list")
    validation_layer = critic.get("validation_layer")
    if not isinstance(validation_layer, str) or validation_layer not in VALIDATION_LAYERS:
        error(errors, source, f"validation_layer is invalid: {critic.get('validation_layer')}")
    if not isinstance(critic.get("probe_run"), bool):
        error(errors, source, "probe_run must be a boolean")
    if not isinstance(critic.get("probe_exit_code"), int) or isinstance(critic.get("probe_exit_code"), bool):
        error(errors, source, "probe_exit_code must be an integer")
    validate_source_refs(critic.get("source_refs"), source=f"{source}.source_refs", errors=errors)
    validate_probe_evidence_refs(critic.get("probe_evidence_refs"), source=f"{source}.probe_evidence_refs", errors=errors)
    if not isinstance(critic.get("evidence"), list) or not critic.get("evidence"):
        error(errors, source, "evidence must be a non-empty list")
    else:
        for index, item in enumerate(critic.get("evidence", [])):
            if not is_substantive_string(item):
                error(errors, source, f"evidence[{index}] must be a substantive string")
    return critic


def validate_required_critic(
    critic: dict[str, Any],
    *,
    source: str,
    review_mode: str,
    has_primary_validation_layer: bool,
    errors: list[str],
) -> None:
    validation_layer = critic.get("validation_layer")
    if validation_layer == "prose-smoke" and not has_primary_validation_layer:
        error(errors, source, "prose-smoke requires another structured/raw/derived validation layer")


def validate_listed_critic_for_acceptance(
    critic: dict[str, Any],
    *,
    source: str,
    review_mode: str,
    replay_probe_commands: bool,
    result_ref: str | None,
    result_digest: str | None,
    packet_ref: str | None,
    packet_sha256: str | None,
    errors: list[str],
) -> None:
    score = critic.get("score")
    threshold = 9 if review_mode == "governance" else 7
    if isinstance(score, int) and not isinstance(score, bool) and score < threshold:
        error(errors, source, f"score below {threshold}: {score}")
    if critic.get("veto") is True:
        error(errors, source, "veto must be false for derived acceptance")
    if critic.get("verdict") == "veto":
        error(errors, source, "verdict veto blocks derived acceptance")
    if critic.get("blocking_findings"):
        error(errors, source, "blocking_findings must be empty for derived acceptance")
    for field in ("false_green_risk", "invariant_checked"):
        if not is_substantive_string(critic.get(field)):
            error(errors, source, f"{field} must be substantive")
    if critic.get("validation_layer") == "wrong-layer":
        error(errors, source, "validation_layer wrong-layer blocks derived acceptance")
    if critic.get("probe_run") is not True:
        error(errors, source, "probe_run must be true for derived acceptance")
    for field in ("probe_command", "probe_result", "probe_interpretation"):
        if not is_substantive_string(critic.get(field)):
            error(errors, source, f"{field} must be substantive")
    if critic.get("probe_exit_code") != 0:
        error(errors, source, "probe_exit_code must be 0 for derived acceptance")
    transcripts = matching_probe_transcripts(
        critic,
        result_ref=result_ref,
        result_digest=result_digest,
        packet_ref=packet_ref,
        packet_sha256=packet_sha256,
    )
    if transcripts is None:
        error(errors, source, "probe_evidence_refs must include a structured transcript matching probe_command and probe_exit_code")
    if replay_probe_commands:
        for transcript in transcripts or [None]:
            replay_probe_command(critic, source=source, transcript=transcript, errors=errors)
    if score == 9:
        for field in ("why_not_10", "residual_risk_disposition"):
            if not is_substantive_string(critic.get(field)):
                error(errors, source, f"score 9 requires {field}")


def matching_probe_transcripts(
    critic: dict[str, Any],
    *,
    result_ref: str | None = None,
    result_digest: str | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> dict[str, Any] | None:
    command = critic.get("probe_command")
    exit_code = critic.get("probe_exit_code")
    refs = critic.get("probe_evidence_refs")
    if not isinstance(command, str) or not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return None
    if not isinstance(refs, list) or not refs:
        return None
    matching: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, str):
            return None
        transcript = load_probe_transcript(ref)
        if transcript is None:
            return None
        if not transcript_matches_probe(
            transcript,
            command=command,
            exit_code=exit_code,
            result_ref=result_ref,
            result_digest=result_digest,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
            source_refs=sorted_string_values(critic.get("source_refs")),
        ):
            return None
        matching.append(transcript)
    if not matching:
        return None
    return matching


def matching_probe_transcript(
    critic: dict[str, Any],
    *,
    result_ref: str | None = None,
    result_digest: str | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> dict[str, Any] | None:
    transcripts = matching_probe_transcripts(
        critic,
        result_ref=result_ref,
        result_digest=result_digest,
        packet_ref=packet_ref,
        packet_sha256=packet_sha256,
    )
    if not transcripts:
        return None
    return transcripts[0]


def probe_has_matching_transcript(critic: dict[str, Any]) -> bool:
    return matching_probe_transcript(critic) is not None


def replay_probe_command(
    critic: dict[str, Any],
    *,
    source: str,
    transcript: dict[str, Any] | None,
    errors: list[str],
) -> None:
    command = critic.get("probe_command")
    expected_exit = critic.get("probe_exit_code")
    if not isinstance(command, str) or not isinstance(expected_exit, int) or isinstance(expected_exit, bool):
        return
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        error(errors, source, f"probe_command is not shell-parseable: {exc}")
        return
    if not argv:
        error(errors, source, "probe_command must not be empty")
        return
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
    except FileNotFoundError:
        error(errors, source, f"probe_command executable not found: {argv[0]}")
        return
    except OSError as exc:
        error(errors, source, f"probe_command launch failed: {exc}")
        return
    except subprocess.TimeoutExpired:
        error(errors, source, "probe_command timed out after 120s")
        return
    if completed.returncode != expected_exit:
        error(errors, source, f"probe_command exit mismatch: expected {expected_exit}, got {completed.returncode}")
        return
    if transcript is None:
        return
    stdout_hash = sha256_bytes(completed.stdout)
    stderr_hash = sha256_bytes(completed.stderr)
    try:
        stdout_text = completed.stdout.decode("utf-8")
    except UnicodeDecodeError:
        error(errors, source, "probe_command stdout was not valid UTF-8")
        stdout_text = None
    try:
        stderr_text = completed.stderr.decode("utf-8")
    except UnicodeDecodeError:
        error(errors, source, "probe_command stderr was not valid UTF-8")
        stderr_text = None
    if transcript.get("stdout_sha256") != stdout_hash:
        error(errors, source, "probe_command stdout hash mismatch against linked transcript")
    if transcript.get("stderr_sha256") != stderr_hash:
        error(errors, source, "probe_command stderr hash mismatch against linked transcript")
    if stdout_text is not None and transcript.get("stdout") != stdout_text:
        error(errors, source, "probe_command stdout text mismatch against linked transcript")
    if stderr_text is not None and transcript.get("stderr") != stderr_text:
        error(errors, source, "probe_command stderr text mismatch against linked transcript")


def validate_governance_frame_disjointness(
    required_results: list[dict[str, Any]],
    errors: list[str],
) -> None:
    if not any(critic.get("frame_challenge") is True for critic in required_results):
        error(errors, "MultiReviewResult.required_critics", "missing required frame_challenge critic")
    for field in ("persona", "scope", "anti_scope", "attack_surface", "primary_failure_mode"):
        values = [
            normalize_text(value)
            for value in (critic.get(field) for critic in required_results)
            if isinstance(value, str) and is_substantive(value)
        ]
        if len(values) != len(required_results):
            continue
        if len(set(values)) != len(values):
            error(errors, "MultiReviewResult.required_critics", f"required critics must have distinct {field} values")


def derive_verdict(
    result: dict[str, Any],
    *,
    replay_probe_commands: bool = False,
    result_ref: str | None = None,
    result_digest: str | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    validate_top_level(result, errors)
    validate_target(result.get("target"), errors)
    review_mode = result.get("review_mode")
    critics_raw = result.get("critics") if isinstance(result.get("critics"), list) else []
    critics: list[dict[str, Any]] = []
    critic_ids: set[str] = set()
    for index, critic_raw in enumerate(critics_raw):
        critic = validate_critic_shape(critic_raw, index=index, errors=errors)
        if critic is None:
            continue
        source = critic_source(critic, index)
        critic_id = critic.get("critic_id")
        if isinstance(critic_id, str):
            if critic_id in critic_ids:
                error(errors, source, f"duplicate critic_id: {critic_id}")
            critic_ids.add(critic_id)
        critics.append(critic)

    required_critics = result.get("required_critics")
    required_ids = {
        critic_id
        for critic_id in required_critics
        if isinstance(critic_id, str)
    } if isinstance(required_critics, list) else set()
    if isinstance(required_critics, list) and len(required_ids) != len(required_critics):
        error(errors, "MultiReviewResult.required_critics", "must not contain duplicate ids")
    missing_required = sorted(required_ids - critic_ids)
    if missing_required:
        error(errors, "MultiReviewResult.required_critics", f"missing required critics: {missing_required}")

    required_results = [
        critic
        for critic in critics
        if isinstance(critic.get("critic_id"), str) and critic.get("critic_id") in required_ids
    ]
    for critic in required_results:
        if critic.get("required") is not True:
            error(errors, critic_source(critic, critics.index(critic)), "required critic must set required: true")
    if review_mode == "governance":
        if not any(critic.get("critic_type") == "validation_layer" for critic in required_results):
            error(errors, "MultiReviewResult.required_critics", "missing required Validation Layer Critic")
        if not any(critic.get("critic_type") == "review_quality" for critic in required_results):
            error(errors, "MultiReviewResult.required_critics", "missing required Review Quality Meta-Critic")
        validate_governance_frame_disjointness(required_results, errors)

    has_primary_validation_layer = any(
        isinstance(critic.get("critic_id"), str)
        and critic.get("critic_id") in required_ids
        and isinstance(critic.get("validation_layer"), str)
        and critic.get("validation_layer") in PRIMARY_VALIDATION_LAYERS
        for critic in critics
    )
    for index, critic in enumerate(critics):
        if isinstance(review_mode, str) and review_mode in REVIEW_MODES:
            validate_listed_critic_for_acceptance(
                critic,
                source=critic_source(critic, index),
                review_mode=str(review_mode),
                replay_probe_commands=replay_probe_commands,
                result_ref=result_ref,
                result_digest=result_digest,
                packet_ref=packet_ref,
                packet_sha256=packet_sha256,
                errors=errors,
            )
        if isinstance(critic.get("critic_id"), str) and critic.get("critic_id") in required_ids:
            validate_required_critic(
                critic,
                source=critic_source(critic, index),
                review_mode=str(review_mode),
                has_primary_validation_layer=has_primary_validation_layer,
                errors=errors,
            )

    if result.get("lifecycle") != "finalized":
        error(errors, "MultiReviewResult.lifecycle", "draft results are incomplete")
    if result.get("independence") == "fallback_nonindependent":
        error(errors, "MultiReviewResult.independence", "fallback_nonindependent cannot derive governance PASS")

    stored_verdict = result.get("derived_verdict")
    provisional_errors = list(errors)
    if result.get("lifecycle") != "finalized":
        derived = "INCOMPLETE"
    elif result.get("independence") == "fallback_nonindependent":
        derived = "FALLBACK_NONINDEPENDENT"
    elif provisional_errors:
        derived = "VETO" if review_mode == "governance" else "INCOMPLETE"
    else:
        derived = "PASS" if review_mode == "governance" else "ADVISORY_PASS"
    if stored_verdict is not None and stored_verdict != derived:
        error(errors, "MultiReviewResult.derived_verdict", f"must be null or match fresh derived verdict: {derived}")
        derived = "VETO" if review_mode == "governance" else "INCOMPLETE"
    return derived, [] if derived in {"PASS", "ADVISORY_PASS"} and not errors else errors


def check_result(
    path: Path,
    *,
    require_governance_pass: bool = False,
    replay_probe_commands: bool = False,
) -> int:
    try:
        result = load_result(path)
    except MultiReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    path_resolved = path.resolve()
    root_resolved = ROOT.resolve()
    derived_verdict, errors = derive_verdict(
        result,
        replay_probe_commands=replay_probe_commands,
        result_ref=display_path(path),
        result_digest=file_sha256(path),
    )
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
    if require_governance_pass and derived_verdict != "PASS":
        print(f"ERROR: derived verdict is not governance PASS: {derived_verdict}", file=sys.stderr)
    if require_governance_pass and not replay_probe_commands:
        print("ERROR: governance PASS acceptance requires explicit --replay-probe-commands", file=sys.stderr)
    success = derived_verdict in {"PASS", "ADVISORY_PASS"} and (
        not require_governance_pass or (derived_verdict == "PASS" and replay_probe_commands)
    )
    stream = sys.stdout if success else sys.stderr
    boundary = (
        "artifact-internal consistency with linked probe transcripts and replayed probe commands; "
        "not stable handoff evidence"
        if replay_probe_commands
        else "artifact-internal consistency with linked probe transcripts; not command replay or stable handoff evidence"
    )
    label = (
        "VALID"
        if require_governance_pass and not replay_probe_commands and derived_verdict == "PASS"
        else "DERIVED"
    )
    print(f"{label}: {derived_verdict} ({boundary}): {display_path(path)}", file=stream)
    return 0 if success else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, help="Path to a MultiReviewResult JSON/YAML artifact")
    parser.add_argument("--require-governance-pass", action="store_true")
    parser.add_argument(
        "--replay-probe-commands",
        action="store_true",
        help="Actively replay probe_command values and compare exit codes plus raw stdout/stderr hashes",
    )
    args = parser.parse_args(argv)
    path = Path(args.result)
    result_path = ROOT / path if not path.is_absolute() else path
    return check_result(
        result_path,
        require_governance_pass=args.require_governance_pass,
        replay_probe_commands=args.replay_probe_commands,
    )


if __name__ == "__main__":
    raise SystemExit(main())
