#!/usr/bin/env python3
"""Run deterministic multi-review fixture scenarios against the validator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCENARIO_VERSION = "multi-review-benchmark-scenario/v1"
DEFAULT_SCENARIOS_ROOT = ROOT / "benchmarks" / "multi-review" / "scenarios"
CHECKER_PATH = ROOT / "scripts" / "check-multi-review-result.py"
PUBLIC_INPUT_FIELDS = {"neutral_id", "title", "summary", "input_artifacts"}
ORACLE_TYPES = {"structural", "semantic", "probe-replay"}
SCORING_MODES = {"validator-only", "contract-only"}
ASSERTION_SEVERITIES = {"acceptance", "advisory", "blocking", "warning"}


spec = importlib.util.spec_from_file_location("multi_review_result_checker", CHECKER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load checker module: {CHECKER_PATH}")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ScenarioError(ValueError):
    pass


def repo_relative_file(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref:
        return None
    body = ref.removeprefix("file:") if ref.startswith("file:") else ref
    if ":" in body or "://" in body:
        return None
    path = Path(body)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (ROOT / path).resolve()
    root_resolved = ROOT.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    if not candidate.is_file():
        return None
    return candidate.relative_to(root_resolved).as_posix()


def is_tracked_repo_file(rel_path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode == 0


def tracked_file_error(ref: str, *, source: str) -> str | None:
    rel_path = repo_relative_file(ref)
    if rel_path is None:
        return f"{source} must point to an existing repo-local file: {ref}"
    if not is_tracked_repo_file(rel_path):
        return f"{source} must point to a tracked fixture file: {ref}"
    return None


def sealed_scenario_file_error(ref: str, *, source: str) -> str | None:
    rel_path = repo_relative_file(ref)
    if (
        rel_path is not None
        and rel_path.startswith("benchmarks/multi-review/scenarios/")
        and rel_path.endswith("/scenario.yml")
    ):
        return f"{source} cannot point to scenario files with sealed_oracle data: {ref}"
    return None


def load_scenario(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScenarioError(f"{path}: cannot read scenario: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ScenarioError(f"{path}: invalid scenario syntax: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ScenarioError(f"{path}: scenario must be a mapping")
    if loaded.get("schema_version") != SCENARIO_VERSION:
        raise ScenarioError(f"{path}: schema_version must be {SCENARIO_VERSION}")
    for field in ("scenario_id", "axis", "review_mode", "public_input", "base_result", "sealed_oracle"):
        if field not in loaded:
            raise ScenarioError(f"{path}: missing {field}")
    if not isinstance(loaded["scenario_id"], str) or not loaded["scenario_id"]:
        raise ScenarioError(f"{path}: scenario_id must be a non-empty string")
    if not isinstance(loaded["axis"], str) or not loaded["axis"]:
        raise ScenarioError(f"{path}: axis must be a non-empty string")
    if not isinstance(loaded["review_mode"], str) or loaded["review_mode"] not in checker.REVIEW_MODES:
        raise ScenarioError(f"{path}: review_mode must be one of {sorted(checker.REVIEW_MODES)}")
    if not isinstance(loaded["base_result"], str) or not loaded["base_result"]:
        raise ScenarioError(f"{path}: base_result must be a non-empty string")
    if not isinstance(loaded["public_input"], dict):
        raise ScenarioError(f"{path}: public_input must be a mapping")
    if not isinstance(loaded["sealed_oracle"], dict):
        raise ScenarioError(f"{path}: sealed_oracle must be a mapping")
    if "expected_derived_verdict" not in loaded["sealed_oracle"]:
        raise ScenarioError(f"{path}: sealed_oracle missing expected_derived_verdict")
    expected_verdict = loaded["sealed_oracle"].get("expected_derived_verdict")
    if not isinstance(expected_verdict, str) or expected_verdict not in checker.DERIVED_VERDICTS:
        raise ScenarioError(
            f"{path}: sealed_oracle.expected_derived_verdict must be one of {sorted(checker.DERIVED_VERDICTS)}"
        )
    if not isinstance(loaded.get("mutations", []), list):
        raise ScenarioError(f"{path}: mutations must be a list")
    if "verify_probe_commands" in loaded:
        raise ScenarioError(f"{path}: use replay_probe_commands instead of verify_probe_commands")
    if not isinstance(loaded.get("replay_probe_commands", False), bool):
        raise ScenarioError(f"{path}: replay_probe_commands must be a boolean")
    return loaded


def scenario_paths(paths: list[str], scenarios_root: Path) -> list[Path]:
    if paths:
        return [resolve_path(path) for path in paths]
    if not scenarios_root.exists():
        raise ScenarioError(f"{scenarios_root}: scenarios root does not exist")
    return sorted(scenarios_root.glob("**/scenario.yml"))


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def pointer_tokens(pointer: str) -> list[str]:
    if pointer == "":
        return []
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ScenarioError(f"mutation path must be a JSON pointer: {pointer!r}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def get_child(container: Any, token: str, pointer: str) -> Any:
    if isinstance(container, dict):
        if token not in container:
            raise ScenarioError(f"mutation path does not exist at {pointer!r}: {token!r}")
        return container[token]
    if isinstance(container, list):
        try:
            index = int(token)
        except ValueError as exc:
            raise ScenarioError(f"list mutation path must use integer indexes at {pointer!r}") from exc
        if index < 0 or index >= len(container):
            raise ScenarioError(f"list mutation index out of range at {pointer!r}: {index}")
        return container[index]
    raise ScenarioError(f"mutation path cannot descend into {type(container).__name__} at {pointer!r}")


def get_pointer(document: Any, pointer: str) -> Any:
    current = document
    for token in pointer_tokens(pointer):
        current = get_child(current, token, pointer)
    return current


def parent_for(document: Any, pointer: str) -> tuple[Any, str]:
    tokens = pointer_tokens(pointer)
    if not tokens:
        raise ScenarioError("mutation path must not target the document root")
    parent = document
    for token in tokens[:-1]:
        parent = get_child(parent, token, pointer)
    return parent, tokens[-1]


def apply_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    if not isinstance(mutation, dict):
        raise ScenarioError("mutation must be a mapping")
    op = mutation.get("op")
    path = mutation.get("path")
    if op not in {"set", "delete", "append"}:
        raise ScenarioError(f"unsupported mutation op: {op!r}")
    if not isinstance(path, str):
        raise ScenarioError("mutation path must be a string")
    if op == "append":
        target = get_pointer(document, path)
        if not isinstance(target, list):
            raise ScenarioError(f"append target must be a list: {path}")
        target.append(copy.deepcopy(mutation.get("value")))
        return
    parent, token = parent_for(document, path)
    if isinstance(parent, dict):
        if op == "delete":
            if token not in parent:
                raise ScenarioError(f"delete target does not exist: {path}")
            del parent[token]
        else:
            parent[token] = copy.deepcopy(mutation.get("value"))
        return
    if isinstance(parent, list):
        try:
            index = int(token)
        except ValueError as exc:
            raise ScenarioError(f"list mutation path must use integer indexes: {path}") from exc
        if index < 0 or index >= len(parent):
            raise ScenarioError(f"list mutation index out of range: {path}")
        if op == "delete":
            del parent[index]
        else:
            parent[index] = copy.deepcopy(mutation.get("value"))
        return
    raise ScenarioError(f"mutation parent must be a mapping or list: {path}")


def scenario_result(scenario: dict[str, Any]) -> dict[str, Any]:
    base_path = resolve_path(scenario["base_result"])
    result = copy.deepcopy(checker.load_result(base_path))
    for mutation in scenario.get("mutations", []):
        apply_mutation(result, mutation)
    return result


def scenario_result_binding(scenario_path: Path, scenario: dict[str, Any], result: dict[str, Any]) -> tuple[str, str]:
    if not scenario.get("mutations") or not scenario.get("replay_probe_commands"):
        base_ref = str(scenario["base_result"])
        base_path = resolve_path(base_ref)
        return base_ref, hashlib.sha256(base_path.read_bytes()).hexdigest()
    try:
        scenario_ref = scenario_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        scenario_ref = str(scenario_path)
    result_bytes = yaml.safe_dump(result, sort_keys=True).encode("utf-8")
    return f"{scenario_ref}#mutated-result", hashlib.sha256(result_bytes).hexdigest()


def semantic_pending_reasons(scenario: dict[str, Any], derived_verdict: str) -> list[str]:
    oracle = scenario["sealed_oracle"]
    if oracle.get("scoring_mode") != "contract-only" or oracle.get("oracle_type") != "semantic":
        return []
    oracle_assertions = oracle.get("oracle_assertions", [])
    if not isinstance(oracle_assertions, list):
        return []
    reasons: list[str] = []
    for index, assertion in enumerate(oracle_assertions):
        if not isinstance(assertion, dict):
            continue
        acceptable = assertion.get("acceptable_disposition", [])
        if isinstance(acceptable, list) and derived_verdict not in acceptable:
            assertion_id = assertion.get("id", index)
            reasons.append(
                f"semantic assertion {assertion_id} requires one of {acceptable}, structural validator derived {derived_verdict}"
            )
    return reasons


def validate_oracle_shape(scenario_path: Path, scenario: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    public_input = scenario["public_input"]
    extra_public_fields = sorted(set(public_input) - PUBLIC_INPUT_FIELDS)
    if extra_public_fields:
        failures.append(f"{scenario_path}: public_input extra fields are not allowed: {extra_public_fields}")
    for field in sorted(PUBLIC_INPUT_FIELDS):
        if field not in public_input:
            failures.append(f"{scenario_path}: public_input missing {field}")
    for field in ("neutral_id", "title", "summary"):
        value = public_input.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{scenario_path}: public_input.{field} must be a non-empty string")
    if "input_artifacts" in public_input and not isinstance(public_input["input_artifacts"], list):
        failures.append(f"{scenario_path}: public_input.input_artifacts must be a list")
    elif "input_artifacts" in public_input:
        for index, artifact in enumerate(public_input["input_artifacts"]):
            if not isinstance(artifact, str) or not artifact.strip():
                failures.append(f"{scenario_path}: public_input.input_artifacts[{index}] must be a non-empty string")
                continue
            artifact_error = tracked_file_error(artifact, source=f"public_input.input_artifacts[{index}]")
            if artifact_error:
                failures.append(f"{scenario_path}: {artifact_error}")
                continue
            sealed_error = sealed_scenario_file_error(artifact, source=f"public_input.input_artifacts[{index}]")
            if sealed_error:
                failures.append(f"{scenario_path}: {sealed_error}")

    oracle = scenario["sealed_oracle"]
    for field in ("oracle_type", "false_green_target", "primary_invariant", "oracle_assertions"):
        if field not in oracle:
            failures.append(f"{scenario_path}: sealed_oracle missing {field}")
    oracle_type = oracle.get("oracle_type")
    if not isinstance(oracle_type, str) or oracle_type not in ORACLE_TYPES:
        failures.append(f"{scenario_path}: sealed_oracle.oracle_type must be one of {sorted(ORACLE_TYPES)}")
    scoring_mode = oracle.get("scoring_mode")
    if scoring_mode is not None and (not isinstance(scoring_mode, str) or scoring_mode not in SCORING_MODES):
        failures.append(f"{scenario_path}: sealed_oracle.scoring_mode must be one of {sorted(SCORING_MODES)}")
    for field in ("false_green_target", "primary_invariant"):
        value = oracle.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{scenario_path}: sealed_oracle.{field} must be a non-empty string")
    oracle_assertions = oracle.get("oracle_assertions", [])
    if not isinstance(oracle_assertions, list) or not oracle_assertions:
        failures.append(f"{scenario_path}: sealed_oracle.oracle_assertions must be a non-empty list")
        oracle_assertions = []
    expected_errors = oracle.get("expected_errors", [])
    forbidden_errors = oracle.get("forbidden_errors", [])
    if not isinstance(expected_errors, list):
        failures.append(f"{scenario_path}: sealed_oracle.expected_errors must be a list")
        expected_errors = []
    if not isinstance(forbidden_errors, list):
        failures.append(f"{scenario_path}: sealed_oracle.forbidden_errors must be a list")
        forbidden_errors = []
    for field, values in (("expected_errors", expected_errors), ("forbidden_errors", forbidden_errors)):
        for index, item in enumerate(values):
            if not isinstance(item, str) or not item.strip():
                failures.append(f"{scenario_path}: sealed_oracle.{field}[{index}] must be a non-empty string")
    for index, assertion in enumerate(oracle_assertions):
        if not isinstance(assertion, dict):
            failures.append(f"{scenario_path}: oracle_assertions[{index}] must be a mapping")
            continue
        for field in (
            "id",
            "kind",
            "severity",
            "target_path",
            "invariant_id",
            "required_evidence_refs",
            "forbidden_shortcuts",
            "acceptable_disposition",
        ):
            if field not in assertion:
                failures.append(f"{scenario_path}: oracle_assertions[{index}] missing {field}")
        for field in ("id", "kind", "target_path", "invariant_id"):
            if field in assertion and (not isinstance(assertion[field], str) or not assertion[field].strip()):
                failures.append(f"{scenario_path}: oracle_assertions[{index}].{field} must be a non-empty string")
        if "severity" in assertion and (
            not isinstance(assertion["severity"], str) or assertion["severity"] not in ASSERTION_SEVERITIES
        ):
            failures.append(
                f"{scenario_path}: oracle_assertions[{index}].severity must be one of {sorted(ASSERTION_SEVERITIES)}"
            )
        for field in ("required_evidence_refs", "forbidden_shortcuts", "acceptable_disposition"):
            if field in assertion and not isinstance(assertion[field], list):
                failures.append(f"{scenario_path}: oracle_assertions[{index}].{field} must be a list")
            elif field in assertion:
                for item_index, item in enumerate(assertion[field]):
                    if not isinstance(item, str) or not item.strip():
                        failures.append(
                            f"{scenario_path}: oracle_assertions[{index}].{field}[{item_index}] must be a non-empty string"
                        )
                        continue
                    if field == "required_evidence_refs":
                        evidence_error = tracked_file_error(
                            item,
                            source=f"oracle_assertions[{index}].required_evidence_refs[{item_index}]",
                        )
                        if evidence_error:
                            failures.append(f"{scenario_path}: {evidence_error}")
    if oracle.get("scoring_mode") == "contract-only":
        if "semantic_oracle" not in oracle:
            failures.append(f"{scenario_path}: contract-only oracle must include semantic_oracle")
        elif not isinstance(oracle.get("semantic_oracle"), dict) or not oracle.get("semantic_oracle"):
            failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle must be a non-empty mapping")
    return failures


def validate_result_fixture_refs(scenario_path: Path, result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    critics = result.get("critics", [])
    if not isinstance(critics, list):
        return failures
    for critic_index, critic in enumerate(critics):
        if not isinstance(critic, dict):
            continue
        refs = critic.get("probe_evidence_refs", [])
        if not isinstance(refs, list):
            continue
        for ref_index, ref in enumerate(refs):
            if not isinstance(ref, str):
                continue
            ref_error = tracked_file_error(
                ref,
                source=f"critics[{critic_index}].probe_evidence_refs[{ref_index}]",
            )
            if ref_error:
                failures.append(f"{scenario_path}: {ref_error}")
    return failures


def check_scenario(path: Path, *, replay_probe_commands: bool = False) -> tuple[str, str, list[str], list[str]]:
    scenario = load_scenario(path)
    failures = validate_oracle_shape(path, scenario)
    scenario_id = scenario["scenario_id"]
    result = scenario_result(scenario)
    failures.extend(validate_result_fixture_refs(path, result))
    result_ref, result_digest = scenario_result_binding(path, scenario, result)
    if result.get("review_mode") != scenario["review_mode"]:
        failures.append(
            f"{path}: scenario review_mode {scenario['review_mode']} does not match result review_mode {result.get('review_mode')}"
        )
    replay_required = scenario.get("replay_probe_commands", False)
    replay_missing = replay_required and not replay_probe_commands
    replay_enabled = replay_required and replay_probe_commands
    derived_verdict, errors = checker.derive_verdict(
        result,
        replay_probe_commands=replay_enabled,
        result_ref=result_ref,
        result_digest=result_digest,
    )
    pending = []
    if replay_missing:
        pending.append("active probe replay required; rerun with --replay-probe-commands")
    pending.extend(semantic_pending_reasons(scenario, derived_verdict))
    oracle = scenario["sealed_oracle"]
    expected_verdict = oracle["expected_derived_verdict"]
    if not replay_missing and derived_verdict != expected_verdict:
        failures.append(
            f"{path}: expected derived verdict {expected_verdict}, got {derived_verdict}"
        )
    if not replay_missing:
        expected_errors_raw = oracle.get("expected_errors", [])
        expected_errors = [
            item for item in expected_errors_raw if isinstance(item, str)
        ] if isinstance(expected_errors_raw, list) else []
        matched_error_indexes: set[int] = set()
        for expected in expected_errors:
            matches = [
                index
                for index, validator_error in enumerate(errors)
                if index not in matched_error_indexes and expected == validator_error
            ]
            if not matches:
                failures.append(f"{path}: missing expected validator error: {expected!r}")
            else:
                matched_error_indexes.add(matches[0])
        forbidden_errors_raw = oracle.get("forbidden_errors", [])
        forbidden_errors = [
            item for item in forbidden_errors_raw if isinstance(item, str)
        ] if isinstance(forbidden_errors_raw, list) else []
        for forbidden in forbidden_errors:
            if forbidden in errors:
                failures.append(f"{path}: found forbidden validator error: {forbidden!r}")
        if expected_verdict not in {"PASS", "ADVISORY_PASS"}:
            for index, validator_error in enumerate(errors):
                if index not in matched_error_indexes:
                    failures.append(f"{path}: unexpected validator error: {validator_error!r}")
    elif errors:
        failures.append(f"{path}: replay-required scenario has structural validator errors without replay: {errors}")
    if expected_verdict in {"PASS", "ADVISORY_PASS"} and errors:
        failures.append(f"{path}: expected acceptance but validator produced errors: {errors}")
    return scenario_id, derived_verdict, failures, pending


def check_scenarios(
    paths: list[Path],
    *,
    replay_probe_commands: bool = False,
    allow_pending: bool = False,
) -> int:
    failures: list[str] = []
    pending_count = 0
    pass_count = 0
    for path in paths:
        try:
            scenario_id, derived_verdict, scenario_failures, scenario_pending = check_scenario(
                path,
                replay_probe_commands=replay_probe_commands,
            )
        except (ScenarioError, checker.MultiReviewError) as exc:
            failures.append(f"ERROR {path}: {exc}")
            continue
        if scenario_failures:
            failures.extend(scenario_failures)
            print(f"FAIL {scenario_id} derived={derived_verdict}", file=sys.stderr)
        elif scenario_pending:
            pending_count += 1
            print(f"PENDING {scenario_id} derived={derived_verdict} pending={'; '.join(scenario_pending)}")
        else:
            pass_count += 1
            print(f"PASS {scenario_id} derived={derived_verdict}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"Fixture scenarios checked: {pass_count} passed, {pending_count} pending explicit checks")
    if pending_count and not allow_pending:
        print("ERROR: pending scenarios require --allow-pending for a zero exit status", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Run a single scenario.yml file. May be repeated.",
    )
    parser.add_argument(
        "--scenarios-root",
        default=str(DEFAULT_SCENARIOS_ROOT),
        help="Root containing **/scenario.yml files.",
    )
    parser.add_argument(
        "--replay-probe-commands",
        action="store_true",
        help="Actively replay probe commands for scenarios that require replay.",
    )
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="Return zero when only explicit pending semantic/replay checks remain.",
    )
    args = parser.parse_args(argv)
    try:
        paths = scenario_paths(args.scenario, resolve_path(args.scenarios_root))
    except ScenarioError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not paths:
        print("ERROR: no scenarios found", file=sys.stderr)
        return 1
    return check_scenarios(paths, replay_probe_commands=args.replay_probe_commands, allow_pending=args.allow_pending)


if __name__ == "__main__":
    raise SystemExit(main())
