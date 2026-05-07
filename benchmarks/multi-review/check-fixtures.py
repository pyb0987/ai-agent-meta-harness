#!/usr/bin/env python3
"""Run deterministic multi-review fixture scenarios against the validator."""

from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCENARIO_VERSION = "multi-review-benchmark-scenario/v1"
DEFAULT_SCENARIOS_ROOT = ROOT / "benchmarks" / "multi-review" / "scenarios"
CHECKER_PATH = ROOT / "scripts" / "check-multi-review-result.py"


spec = importlib.util.spec_from_file_location("multi_review_result_checker", CHECKER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load checker module: {CHECKER_PATH}")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ScenarioError(ValueError):
    pass


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
    for field in ("scenario_id", "axis", "public_input", "base_result", "sealed_oracle"):
        if field not in loaded:
            raise ScenarioError(f"{path}: missing {field}")
    if not isinstance(loaded["scenario_id"], str) or not loaded["scenario_id"]:
        raise ScenarioError(f"{path}: scenario_id must be a non-empty string")
    if not isinstance(loaded["axis"], str) or not loaded["axis"]:
        raise ScenarioError(f"{path}: axis must be a non-empty string")
    if not isinstance(loaded["public_input"], dict):
        raise ScenarioError(f"{path}: public_input must be a mapping")
    if not isinstance(loaded["sealed_oracle"], dict):
        raise ScenarioError(f"{path}: sealed_oracle must be a mapping")
    if "expected_derived_verdict" not in loaded["sealed_oracle"]:
        raise ScenarioError(f"{path}: sealed_oracle missing expected_derived_verdict")
    if not isinstance(loaded.get("mutations", []), list):
        raise ScenarioError(f"{path}: mutations must be a list")
    if not isinstance(loaded.get("verify_probe_commands", False), bool):
        raise ScenarioError(f"{path}: verify_probe_commands must be a boolean")
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


def validate_oracle_shape(scenario_path: Path, scenario: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    public_input = scenario["public_input"]
    for field in ("neutral_id", "title", "summary", "input_artifacts"):
        if field not in public_input:
            failures.append(f"{scenario_path}: public_input missing {field}")
    if "input_artifacts" in public_input and not isinstance(public_input["input_artifacts"], list):
        failures.append(f"{scenario_path}: public_input.input_artifacts must be a list")

    oracle = scenario["sealed_oracle"]
    for field in ("oracle_type", "false_green_target", "primary_invariant", "oracle_assertions"):
        if field not in oracle:
            failures.append(f"{scenario_path}: sealed_oracle missing {field}")
    if not isinstance(oracle.get("oracle_assertions", []), list) or not oracle.get("oracle_assertions"):
        failures.append(f"{scenario_path}: sealed_oracle.oracle_assertions must be a non-empty list")
    if not isinstance(oracle.get("expected_errors", []), list):
        failures.append(f"{scenario_path}: sealed_oracle.expected_errors must be a list")
    if not isinstance(oracle.get("forbidden_errors", []), list):
        failures.append(f"{scenario_path}: sealed_oracle.forbidden_errors must be a list")
    for field in ("expected_errors", "forbidden_errors"):
        for index, item in enumerate(oracle.get(field, [])):
            if not isinstance(item, str):
                failures.append(f"{scenario_path}: sealed_oracle.{field}[{index}] must be a string")
    for index, assertion in enumerate(oracle.get("oracle_assertions", [])):
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
        for field in ("required_evidence_refs", "forbidden_shortcuts", "acceptable_disposition"):
            if field in assertion and not isinstance(assertion[field], list):
                failures.append(f"{scenario_path}: oracle_assertions[{index}].{field} must be a list")
    if oracle.get("scoring_mode") == "contract-only" and "semantic_oracle" not in oracle:
        failures.append(f"{scenario_path}: contract-only oracle must include semantic_oracle")
    return failures


def check_scenario(path: Path) -> tuple[str, str, list[str]]:
    scenario = load_scenario(path)
    failures = validate_oracle_shape(path, scenario)
    scenario_id = scenario["scenario_id"]
    result = scenario_result(scenario)
    derived_verdict, errors = checker.derive_verdict(
        result,
        verify_probe_commands=scenario.get("verify_probe_commands", False),
    )
    oracle = scenario["sealed_oracle"]
    expected_verdict = oracle["expected_derived_verdict"]
    if derived_verdict != expected_verdict:
        failures.append(
            f"{path}: expected derived verdict {expected_verdict}, got {derived_verdict}"
        )
    joined_errors = "\n".join(errors)
    for expected in oracle.get("expected_errors", []):
        if expected not in joined_errors:
            failures.append(f"{path}: missing expected error substring: {expected!r}")
    for forbidden in oracle.get("forbidden_errors", []):
        if forbidden in joined_errors:
            failures.append(f"{path}: found forbidden error substring: {forbidden!r}")
    if expected_verdict in {"PASS", "ADVISORY_PASS"} and errors:
        failures.append(f"{path}: expected acceptance but validator produced errors: {errors}")
    return scenario_id, derived_verdict, failures


def check_scenarios(paths: list[Path]) -> int:
    failures: list[str] = []
    for path in paths:
        try:
            scenario_id, derived_verdict, scenario_failures = check_scenario(path)
        except (ScenarioError, checker.MultiReviewError) as exc:
            failures.append(f"ERROR {path}: {exc}")
            continue
        if scenario_failures:
            failures.extend(scenario_failures)
            print(f"FAIL {scenario_id} derived={derived_verdict}", file=sys.stderr)
        else:
            print(f"PASS {scenario_id} derived={derived_verdict}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print(f"Fixture scenarios passed: {len(paths)}")
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
    args = parser.parse_args(argv)
    try:
        paths = scenario_paths(args.scenario, resolve_path(args.scenarios_root))
    except ScenarioError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not paths:
        print("ERROR: no scenarios found", file=sys.stderr)
        return 1
    return check_scenarios(paths)


if __name__ == "__main__":
    raise SystemExit(main())
