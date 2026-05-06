#!/usr/bin/env python3
"""Validate MultiReviewResult artifact-internal consistency and derive verdicts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RESULT_KEY = "MultiReviewResult"
SCHEMA_VERSION = "multi-review-result/v1"

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
    "scope",
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
    "probe_result",
    "probe_interpretation",
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
TARGET_FIELDS = {"summary", "source_refs"}
VACUOUS_VALUES = {
    "",
    "none",
    "n/a",
    "na",
    "ok",
    "checked",
    "generic",
    "not applicable",
    "pass",
    "read the plan",
    "read plan",
    "not run",
    "not executed",
    "did not run",
    "no probe run",
    "self-attested",
    "self attested",
    "definitely-not-a-real-command --should-fail",
    "existing review says pass",
    "existing acceptance says pass",
}


class MultiReviewError(ValueError):
    pass


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


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


def date_like(value: Any) -> bool:
    if isinstance(value, dt.datetime):
        value = value.date()
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


def validate_top_level(result: dict[str, Any], errors: list[str]) -> None:
    if set(result) != TOP_LEVEL_FIELDS:
        missing = sorted(TOP_LEVEL_FIELDS - set(result))
        extra = sorted(set(result) - TOP_LEVEL_FIELDS)
        if missing:
            error(errors, "MultiReviewResult", f"missing fields: {missing}")
        if extra:
            error(errors, "MultiReviewResult", f"extra fields: {extra}")
    if result.get("schema_version") != SCHEMA_VERSION:
        error(errors, "MultiReviewResult.schema_version", f"must be {SCHEMA_VERSION}")
    if result.get("lifecycle") not in LIFECYCLES:
        error(errors, "MultiReviewResult.lifecycle", "must be draft or finalized")
    if result.get("review_mode") not in REVIEW_MODES:
        error(errors, "MultiReviewResult.review_mode", "must be governance or advisory")
    if result.get("independence") not in INDEPENDENCE_MODES:
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
    if stored_verdict is not None and stored_verdict not in DERIVED_VERDICTS:
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


def validate_target(target: Any, errors: list[str]) -> None:
    if not isinstance(target, dict):
        error(errors, "MultiReviewResult.target", "must be a mapping")
        return
    if set(target) != TARGET_FIELDS:
        missing = sorted(TARGET_FIELDS - set(target))
        extra = sorted(set(target) - TARGET_FIELDS)
        if missing:
            error(errors, "MultiReviewResult.target", f"missing fields: {missing}")
        if extra:
            error(errors, "MultiReviewResult.target", f"extra fields: {extra}")
    if not is_substantive(target.get("summary")):
        error(errors, "MultiReviewResult.target.summary", "must be substantive")
    validate_source_refs(target.get("source_refs"), source="MultiReviewResult.target.source_refs", errors=errors)


def critic_source(critic: dict[str, Any], index: int) -> str:
    critic_id = critic.get("critic_id")
    return f"critics[{index}:{critic_id}]" if critic_id else f"critics[{index}]"


def validate_critic_shape(critic: Any, *, index: int, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(critic, dict):
        error(errors, f"critics[{index}]", "critic result must be a mapping")
        return None
    source = critic_source(critic, index)
    if set(critic) != CRITIC_FIELDS:
        missing = sorted(CRITIC_FIELDS - set(critic))
        extra = sorted(set(critic) - CRITIC_FIELDS)
        if missing:
            error(errors, source, f"missing fields: {missing}")
        if extra:
            error(errors, source, f"extra fields: {extra}")
    for field in ("critic_id", "name", "critic_type", "scope", "actor", "date"):
        if not is_substantive(critic.get(field)):
            error(errors, source, f"{field} is required")
    if is_substantive(critic.get("date")) and not date_like(critic.get("date")):
        error(errors, source, "date must be an ISO date on or before today")
    if critic.get("critic_type") not in CRITIC_TYPES:
        error(errors, source, f"critic_type is invalid: {critic.get('critic_type')}")
    if not isinstance(critic.get("required"), bool):
        error(errors, source, "required must be a boolean")
    score = critic.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 10:
        error(errors, source, "score must be an integer from 1 to 10")
    if critic.get("verdict") not in CRITIC_VERDICTS:
        error(errors, source, f"verdict is invalid: {critic.get('verdict')}")
    if not isinstance(critic.get("veto"), bool):
        error(errors, source, "veto must be a boolean")
    if not isinstance(critic.get("blocking_findings"), list):
        error(errors, source, "blocking_findings must be a list")
    if critic.get("validation_layer") not in VALIDATION_LAYERS:
        error(errors, source, f"validation_layer is invalid: {critic.get('validation_layer')}")
    if not isinstance(critic.get("probe_run"), bool):
        error(errors, source, "probe_run must be a boolean")
    validate_source_refs(critic.get("source_refs"), source=f"{source}.source_refs", errors=errors)
    if not isinstance(critic.get("evidence"), list) or not critic.get("evidence"):
        error(errors, source, "evidence must be a non-empty list")
    elif not any(is_substantive(item) for item in critic.get("evidence", [])):
        error(errors, source, "evidence must include substantive entries")
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
        if not is_substantive(critic.get(field)):
            error(errors, source, f"{field} must be substantive")
    if critic.get("validation_layer") == "wrong-layer":
        error(errors, source, "validation_layer wrong-layer blocks derived acceptance")
    if critic.get("probe_run") is not True:
        error(errors, source, "probe_run must be true for derived acceptance")
    for field in ("probe_command", "probe_result", "probe_interpretation"):
        if not is_substantive(critic.get(field)):
            error(errors, source, f"{field} must be substantive")
    if score == 9:
        for field in ("why_not_10", "residual_risk_disposition"):
            if not is_substantive(critic.get(field)):
                error(errors, source, f"score 9 requires {field}")


def derive_verdict(result: dict[str, Any]) -> tuple[str, list[str]]:
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
        if critic_id in critic_ids:
            error(errors, source, f"duplicate critic_id: {critic_id}")
        if isinstance(critic_id, str):
            critic_ids.add(critic_id)
        critics.append(critic)

    required_critics = result.get("required_critics")
    required_ids = set(required_critics) if isinstance(required_critics, list) else set()
    if len(required_ids) != len(required_critics or []):
        error(errors, "MultiReviewResult.required_critics", "must not contain duplicate ids")
    missing_required = sorted(required_ids - critic_ids)
    if missing_required:
        error(errors, "MultiReviewResult.required_critics", f"missing required critics: {missing_required}")

    required_results = [critic for critic in critics if critic.get("critic_id") in required_ids]
    for critic in required_results:
        if critic.get("required") is not True:
            error(errors, critic_source(critic, critics.index(critic)), "required critic must set required: true")
    if review_mode == "governance":
        if not any(critic.get("critic_type") == "validation_layer" for critic in required_results):
            error(errors, "MultiReviewResult.required_critics", "missing required Validation Layer Critic")
        if not any(critic.get("critic_type") == "review_quality" for critic in required_results):
            error(errors, "MultiReviewResult.required_critics", "missing required Review Quality Meta-Critic")

    has_primary_validation_layer = any(
        critic.get("critic_id") in required_ids and critic.get("validation_layer") in PRIMARY_VALIDATION_LAYERS
        for critic in critics
    )
    for index, critic in enumerate(critics):
        if review_mode in REVIEW_MODES:
            validate_listed_critic_for_acceptance(
                critic,
                source=critic_source(critic, index),
                review_mode=str(review_mode),
                errors=errors,
            )
        if critic.get("critic_id") in required_ids:
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


def check_result(path: Path, *, require_governance_pass: bool = False) -> int:
    try:
        result = load_result(path)
    except MultiReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    derived_verdict, errors = derive_verdict(result)
    if errors:
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
    if require_governance_pass and derived_verdict != "PASS":
        print(f"ERROR: derived verdict is not governance PASS: {derived_verdict}", file=sys.stderr)
    success = derived_verdict in {"PASS", "ADVISORY_PASS"} and (
        not require_governance_pass or derived_verdict == "PASS"
    )
    stream = sys.stdout if success else sys.stderr
    boundary = "artifact-internal consistency only; not probe execution or stable evidence"
    print(f"DERIVED: {derived_verdict} ({boundary}): {path}", file=stream)
    return 0 if success else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, help="Path to a MultiReviewResult JSON/YAML artifact")
    parser.add_argument("--require-governance-pass", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.result)
    result_path = ROOT / path if not path.is_absolute() else path
    return check_result(result_path, require_governance_pass=args.require_governance_pass)


if __name__ == "__main__":
    raise SystemExit(main())
