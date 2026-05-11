#!/usr/bin/env python3
"""Run deterministic multi-review fixture scenarios against the validator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


CANONICAL_ROOT = Path(__file__).resolve().parents[2]
ROOT = CANONICAL_ROOT
SCENARIO_VERSION = "multi-review-benchmark-scenario/v1"
DEFAULT_SCENARIOS_ROOT = ROOT / "benchmarks" / "multi-review" / "scenarios"
CHECKER_PATH = ROOT / "scripts" / "check-multi-review-result.py"
PUBLIC_INPUT_FIELDS = {"neutral_id", "title", "summary", "input_artifacts"}
ORACLE_TYPES = {"structural", "semantic", "probe-replay"}
SCORING_MODES = {"validator-only", "contract-only"}
ASSERTION_SEVERITIES = {"acceptance", "advisory", "blocking", "warning"}
VACUOUS_SEMANTIC_VALUES = {"", "none", "na", "ok", "checked", "generic", "notapplicable", "pass"}
SEALED_ORACLE_FIELDS = {
    "expected_derived_verdict",
    "expected_errors",
    "false_green_target",
    "forbidden_errors",
    "oracle_assertions",
    "oracle_type",
    "primary_invariant",
    "scoring_mode",
    "semantic_oracle",
}
ORACLE_ASSERTION_FIELDS = {
    "acceptable_disposition",
    "forbidden_shortcuts",
    "id",
    "invariant_id",
    "kind",
    "required_evidence_refs",
    "severity",
    "target_path",
}
SEMANTIC_ORACLE_FIELDS = {
    "accepted_disposition",
    "expected_false_premise",
    "facts_refuting_premise",
    "forbidden_oracle_terms",
    "irrelevant_source_refs",
    "leakage_policy",
    "relevant_source_refs",
    "semantic_equivalence_group",
    "source_contract",
    "unsupported_claim",
}
SEMANTIC_ORACLE_ANCHOR_FIELDS = {
    "expected_false_premise",
    "leakage_policy",
    "semantic_equivalence_group",
    "source_contract",
    "unsupported_claim",
}
SEMANTIC_ORACLE_SOURCE_REF_FIELDS = {"irrelevant_source_refs", "relevant_source_refs"}
SEALED_ORACLE_LABELS = {
    "acceptable_disposition",
    "expected_derived_verdict",
    "expected_errors",
    "false_green_target",
    "forbidden_errors",
    "forbidden_oracle_terms",
    "oracle_assertions",
    "primary_invariant",
    "scoring_mode",
    "sealed_oracle",
    "semantic_oracle",
}
EMBEDDED_REPO_REF_RE = re.compile(
    r"(?:file:)?(?:benchmarks/multi-review/[A-Za-z0-9._/#-]+|backlog/fixtures/[A-Za-z0-9._/#-]+)"
)
EMBEDDED_GENERATED_REF_RE = re.compile(r"benchmark-generated:[A-Za-z0-9._/#-]+")


spec = importlib.util.spec_from_file_location("multi_review_result_checker", CHECKER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load checker module: {CHECKER_PATH}")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ScenarioError(ValueError):
    pass


def sorted_key_names(keys: Any) -> list[str]:
    return sorted(str(key) for key in keys)


def normalize_text(value: str) -> str:
    normalized = " ".join(value.strip().strip("\"'").casefold().split())
    return re.sub(r"[^a-z0-9]+", "", normalized)


def canonical_public_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def is_substantive_semantic_text(value: str) -> bool:
    return normalize_text(value) not in VACUOUS_SEMANTIC_VALUES


def recursive_strings(value: Any, source: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(source, value)]
    if isinstance(value, list):
        strings: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            strings.extend(recursive_strings(item, f"{source}[{index}]"))
        return strings
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            if isinstance(key, str):
                strings.append((f"{source}.<key>", key))
            strings.extend(recursive_strings(item, f"{source}.{key}"))
        return strings
    return []


def is_public_repo_ref_text(value: str) -> bool:
    rel_path = repo_relative_file(value)
    return rel_path is not None and sealed_benchmark_file_error(value, source="public ref") is None


def sealed_oracle_public_terms(oracle: dict[str, Any]) -> tuple[set[str], set[str]]:
    generic_tokens = {
        canonical_public_token(value)
        for value in (
            set(checker.DERIVED_VERDICTS)
            | ORACLE_TYPES
            | SCORING_MODES
            | ASSERTION_SEVERITIES
        )
    }
    substring_terms = {canonical_public_token(label) for label in SEALED_ORACLE_LABELS}
    exact_terms: set[str] = set()
    prose_sources = (
        "sealed_oracle.expected_errors",
        "sealed_oracle.forbidden_errors",
        "sealed_oracle.false_green_target",
        "sealed_oracle.primary_invariant",
        "sealed_oracle.oracle_assertions",
        "sealed_oracle.semantic_oracle",
    )
    prose_leaf_fields = {
        "expected_errors",
        "forbidden_errors",
        "false_green_target",
        "primary_invariant",
        "forbidden_oracle_terms",
        "forbidden_shortcuts",
        *SEMANTIC_ORACLE_ANCHOR_FIELDS,
    }
    for source, value in recursive_strings(oracle, "sealed_oracle"):
        leaf = source.rsplit(".", 1)[-1].split("[", 1)[0]
        if is_public_repo_ref_text(value):
            token = canonical_public_token(value)
            if token and token not in generic_tokens:
                exact_terms.add(token)
            continue
        token = canonical_public_token(value)
        if not token or token in generic_tokens:
            continue
        if source.startswith(prose_sources) and leaf in prose_leaf_fields:
            substring_terms.add(token)
        else:
            exact_terms.add(token)
    return substring_terms, exact_terms


def sealed_oracle_forbidden_terms(oracle: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for source, value in recursive_strings(oracle, "sealed_oracle"):
        leaf = source.rsplit(".", 1)[-1].split("[", 1)[0]
        if leaf != "forbidden_oracle_terms":
            continue
        token = canonical_public_token(value)
        if token:
            terms.add(token)
    return terms


def public_string_leakage_errors(
    scenario_path: Path,
    value: str,
    *,
    source: str,
    forbidden_substrings: set[str],
    forbidden_exact: set[str],
    expected_generated_ref: str | None = None,
) -> list[str]:
    failures: list[str] = []
    normalized_value = canonical_public_token(value)
    for term in forbidden_substrings:
        if term and term in normalized_value:
            failures.append(f"{scenario_path}: {source} must not contain sealed oracle term: {term}")
    for term in forbidden_exact:
        if term and term == normalized_value:
            failures.append(f"{scenario_path}: {source} must not copy sealed oracle value: {term}")
    for embedded_error in embedded_repo_ref_errors(value, source=source):
        failures.append(f"{scenario_path}: {embedded_error}")
    for generated_error in embedded_generated_ref_errors(
        value,
        source=source,
        expected_result_ref=expected_generated_ref,
    ):
        failures.append(f"{scenario_path}: {generated_error}")
    return failures


def public_text_leakage_errors(scenario_path: Path, public_input: dict[str, Any], oracle: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden_substrings, forbidden_exact = sealed_oracle_public_terms(oracle)
    for field in ("neutral_id", "title", "summary"):
        value = public_input.get(field)
        if not isinstance(value, str):
            continue
        failures.extend(
            public_string_leakage_errors(
                scenario_path,
                value,
                source=f"public_input.{field}",
                forbidden_substrings=forbidden_substrings,
                forbidden_exact=forbidden_exact,
                expected_generated_ref=None,
            )
        )
    return failures


def repo_relative_file(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref:
        return None
    ref = ref.split("#", 1)[0]
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
    try:
        is_file = candidate.is_file()
    except OSError:
        return None
    if not is_file:
        return None
    return candidate.relative_to(root_resolved).as_posix()


def is_tracked_repo_file(rel_path: str) -> bool:
    if ROOT.resolve() != CANONICAL_ROOT.resolve():
        return (ROOT / rel_path).is_file()
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


def sealed_benchmark_file_error(ref: str, *, source: str) -> str | None:
    rel_path = repo_relative_file(ref)
    if (
        rel_path is not None
        and rel_path.startswith("benchmarks/multi-review/scenarios/")
        and rel_path.endswith("/scenario.yml")
    ):
        return f"{source} cannot point to scenario files with sealed_oracle data: {ref}"
    if rel_path is not None and rel_path.startswith("benchmarks/multi-review/"):
        if any(part.startswith("sealed") for part in Path(rel_path).parts):
            return f"{source} cannot point to sealed benchmark/oracle files: {ref}"
    return None


def embedded_repo_ref_errors(text: str, *, source: str) -> list[str]:
    errors: list[str] = []
    for match in EMBEDDED_REPO_REF_RE.finditer(text):
        token = match.group(0).rstrip(".,;:)")
        sealed_error = sealed_benchmark_file_error(token, source=source)
        if sealed_error and sealed_error not in errors:
            errors.append(sealed_error)
    return errors


def embedded_generated_ref_errors(
    text: str,
    *,
    source: str,
    expected_result_ref: str | None,
) -> list[str]:
    errors: list[str] = []
    for match in EMBEDDED_GENERATED_REF_RE.finditer(text):
        token = match.group(0).rstrip(".,;:)")
        if expected_result_ref is None:
            errors.append(f"{source} must not expose benchmark-generated refs: {token}")
            continue
        if token != expected_result_ref:
            errors.append(
                f"{source} benchmark-generated ref must match {expected_result_ref}: {token}"
            )
    return errors


def public_fixture_ref_errors(ref: str, *, source: str) -> list[str]:
    errors: list[str] = []
    tracked_error = tracked_file_error(ref, source=source)
    if tracked_error:
        errors.append(tracked_error)
        return errors
    sealed_error = sealed_benchmark_file_error(ref, source=source)
    if sealed_error:
        errors.append(sealed_error)
    return errors


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
    base_result_error = tracked_file_error(loaded["base_result"], source="base_result")
    if base_result_error:
        raise ScenarioError(f"{path}: {base_result_error}")
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


def pointer_exists(document: Any, pointer: str) -> bool:
    if pointer == "/":
        return True
    try:
        tokens = pointer_tokens(pointer)
    except ScenarioError:
        return False

    def walk(current: Any, remaining: list[str]) -> bool:
        if not remaining:
            return True
        token, rest = remaining[0], remaining[1:]
        if token == "*":
            if isinstance(current, list):
                return any(walk(item, rest) for item in current)
            if isinstance(current, dict):
                return any(walk(item, rest) for item in current.values())
            return False
        if isinstance(current, dict):
            return token in current and walk(current[token], rest)
        if isinstance(current, list):
            try:
                index = int(token)
            except ValueError:
                return False
            return 0 <= index < len(current) and walk(current[index], rest)
        return False

    return walk(document, tokens)


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
    result_bytes = yaml.safe_dump(result, sort_keys=True).encode("utf-8")
    return f"benchmark-generated:{scenario['scenario_id']}#mutated-result", hashlib.sha256(result_bytes).hexdigest()


def semantic_pending_reasons(scenario: dict[str, Any], derived_verdict: str) -> list[str]:
    oracle = scenario["sealed_oracle"]
    if oracle.get("scoring_mode") != "contract-only" or oracle.get("oracle_type") != "semantic":
        return []
    oracle_assertions = oracle.get("oracle_assertions", [])
    if not isinstance(oracle_assertions, list):
        return []
    reasons: list[str] = []
    semantic_oracle = oracle.get("semantic_oracle", {})
    if isinstance(semantic_oracle, dict):
        accepted = semantic_oracle.get("accepted_disposition")
        accepted_values = [accepted] if isinstance(accepted, str) else accepted
        if isinstance(accepted_values, list) and accepted_values and derived_verdict not in accepted_values:
            reasons.append(
                f"semantic_oracle.accepted_disposition requires one of {accepted_values}, "
                f"structural validator derived {derived_verdict}"
            )
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


def validate_oracle_shape(
    scenario_path: Path,
    scenario: dict[str, Any],
    *,
    result: dict[str, Any] | None = None,
    expected_result_ref: str | None = None,
    expected_result_digest: str | None = None,
) -> list[str]:
    failures: list[str] = []
    public_input = scenario["public_input"]
    oracle = scenario["sealed_oracle"]
    extra_oracle_fields = sorted_key_names(
        key for key in oracle if not isinstance(key, str) or key not in SEALED_ORACLE_FIELDS
    )
    if extra_oracle_fields:
        failures.append(f"{scenario_path}: sealed_oracle extra fields are not allowed: {extra_oracle_fields}")
    extra_public_fields = sorted_key_names(
        key for key in public_input if not isinstance(key, str) or key not in PUBLIC_INPUT_FIELDS
    )
    if extra_public_fields:
        failures.append(f"{scenario_path}: public_input extra fields are not allowed: {extra_public_fields}")
    for field in sorted(PUBLIC_INPUT_FIELDS):
        if field not in public_input:
            failures.append(f"{scenario_path}: public_input missing {field}")
    for field in ("neutral_id", "title", "summary"):
        value = public_input.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f"{scenario_path}: public_input.{field} must be a non-empty string")
    failures.extend(public_text_leakage_errors(scenario_path, public_input, oracle))
    if "input_artifacts" in public_input and not isinstance(public_input["input_artifacts"], list):
        failures.append(f"{scenario_path}: public_input.input_artifacts must be a list")
    elif "input_artifacts" in public_input:
        for index, artifact in enumerate(public_input["input_artifacts"]):
            if not isinstance(artifact, str) or not artifact.strip():
                failures.append(f"{scenario_path}: public_input.input_artifacts[{index}] must be a non-empty string")
                continue
            for ref_error in public_fixture_ref_errors(artifact, source=f"public_input.input_artifacts[{index}]"):
                failures.append(f"{scenario_path}: {ref_error}")
            failures.extend(
                validate_probe_transcript_public_metadata(
                    scenario_path,
                    artifact,
                    source=f"public_input.input_artifacts[{index}]",
                    oracle=oracle,
                    expected_result_ref=expected_result_ref,
                    expected_result_digest=expected_result_digest,
                )
            )

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
        extra_assertion_fields = sorted_key_names(
            key for key in assertion if not isinstance(key, str) or key not in ORACLE_ASSERTION_FIELDS
        )
        if extra_assertion_fields:
            failures.append(
                f"{scenario_path}: oracle_assertions[{index}] extra fields are not allowed: {extra_assertion_fields}"
            )
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
        if "target_path" in assertion and isinstance(assertion.get("target_path"), str) and not assertion["target_path"].startswith("/"):
            failures.append(f"{scenario_path}: oracle_assertions[{index}].target_path must be a JSON pointer")
        elif result is not None and isinstance(assertion.get("target_path"), str) and not pointer_exists(result, assertion["target_path"]):
            failures.append(f"{scenario_path}: oracle_assertions[{index}].target_path must resolve against the mutated result")
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
                    if field == "acceptable_disposition" and item not in checker.DERIVED_VERDICTS:
                        failures.append(
                            f"{scenario_path}: oracle_assertions[{index}].acceptable_disposition[{item_index}] "
                            f"must be one of {sorted(checker.DERIVED_VERDICTS)}"
                        )
                    if field == "required_evidence_refs":
                        for evidence_error in public_fixture_ref_errors(
                            item,
                            source=f"oracle_assertions[{index}].required_evidence_refs[{item_index}]",
                        ):
                            failures.append(f"{scenario_path}: {evidence_error}")
    semantic_oracle_present = "semantic_oracle" in oracle
    if semantic_oracle_present and oracle_type != "semantic":
        failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle requires oracle_type: semantic")
    if oracle_type == "semantic" or oracle.get("scoring_mode") == "contract-only":
        if "semantic_oracle" not in oracle:
            failures.append(f"{scenario_path}: semantic oracle must include semantic_oracle")
        elif not isinstance(oracle.get("semantic_oracle"), dict) or not oracle.get("semantic_oracle"):
            failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle must be a non-empty mapping")
        else:
            failures.extend(validate_semantic_oracle(scenario_path, oracle["semantic_oracle"]))
    elif semantic_oracle_present:
        if not isinstance(oracle.get("semantic_oracle"), dict) or not oracle.get("semantic_oracle"):
            failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle must be a non-empty mapping")
        else:
            failures.extend(validate_semantic_oracle(scenario_path, oracle["semantic_oracle"]))
    return failures


def validate_semantic_oracle(scenario_path: Path, semantic_oracle: dict[Any, Any]) -> list[str]:
    failures: list[str] = []
    extra_fields = sorted_key_names(
        key for key in semantic_oracle if not isinstance(key, str) or key not in SEMANTIC_ORACLE_FIELDS
    )
    if extra_fields:
        failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle extra fields are not allowed: {extra_fields}")
    if not any(field in semantic_oracle for field in SEMANTIC_ORACLE_ANCHOR_FIELDS):
        failures.append(
            f"{scenario_path}: sealed_oracle.semantic_oracle must include one of "
            f"{sorted(SEMANTIC_ORACLE_ANCHOR_FIELDS)}"
        )
    for field, value in semantic_oracle.items():
        if not isinstance(field, str) or field not in SEMANTIC_ORACLE_FIELDS:
            continue
        if field in SEMANTIC_ORACLE_SOURCE_REF_FIELDS:
            if not isinstance(value, list) or not value:
                failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle.{field} must be a non-empty source-ref list")
                continue
            for item_index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    failures.append(
                        f"{scenario_path}: sealed_oracle.semantic_oracle.{field}[{item_index}] must be a non-empty string"
                    )
                    continue
                for ref_error in public_fixture_ref_errors(item, source=f"semantic_oracle.{field}[{item_index}]"):
                    failures.append(f"{scenario_path}: {ref_error}")
            continue
        if field == "accepted_disposition":
            values = [value] if isinstance(value, str) else value
            if not isinstance(values, list) or not values:
                failures.append(
                    f"{scenario_path}: sealed_oracle.semantic_oracle.accepted_disposition "
                    "must be a non-empty string or list"
                )
                continue
            for item_index, item in enumerate(values):
                if not isinstance(item, str) or item not in checker.DERIVED_VERDICTS:
                    failures.append(
                        f"{scenario_path}: sealed_oracle.semantic_oracle.accepted_disposition[{item_index}] "
                        f"must be one of {sorted(checker.DERIVED_VERDICTS)}"
                    )
            continue
        if isinstance(value, str):
            if not value.strip() or not is_substantive_semantic_text(value):
                failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle.{field} must be substantive")
            continue
        if isinstance(value, list) and value:
            if not all(isinstance(item, str) and item.strip() and is_substantive_semantic_text(item) for item in value):
                failures.append(
                    f"{scenario_path}: sealed_oracle.semantic_oracle.{field} must contain only substantive strings"
                )
            continue
        failures.append(f"{scenario_path}: sealed_oracle.semantic_oracle.{field} must be a non-empty string or list")
    return failures


def validate_result_fixture_refs(
    scenario_path: Path,
    scenario: dict[str, Any],
    result: dict[str, Any],
    *,
    expected_result_ref: str,
    expected_result_digest: str,
) -> list[str]:
    failures: list[str] = []
    target = result.get("target", {})
    if isinstance(target, dict):
        target_refs = target.get("source_refs", [])
        if isinstance(target_refs, list):
            for ref_index, ref in enumerate(target_refs):
                if not isinstance(ref, str):
                    continue
                for ref_error in public_fixture_ref_errors(ref, source=f"target.source_refs[{ref_index}]"):
                    failures.append(f"{scenario_path}: {ref_error}")
    critics = result.get("critics", [])
    if not isinstance(critics, list):
        return failures
    for critic_index, critic in enumerate(critics):
        if not isinstance(critic, dict):
            continue
        for field in ("source_refs", "probe_evidence_refs"):
            refs = critic.get(field, [])
            if not isinstance(refs, list):
                continue
            for ref_index, ref in enumerate(refs):
                if not isinstance(ref, str):
                    continue
                for ref_error in public_fixture_ref_errors(ref, source=f"critics[{critic_index}].{field}[{ref_index}]"):
                    failures.append(f"{scenario_path}: {ref_error}")
                if field == "probe_evidence_refs":
                    failures.extend(
                        validate_probe_transcript_public_metadata(
                            scenario_path,
                            ref,
                            source=f"critics[{critic_index}].probe_evidence_refs[{ref_index}]",
                            oracle=scenario["sealed_oracle"],
                            expected_result_ref=expected_result_ref,
                            expected_result_digest=expected_result_digest,
                        )
                    )
    return failures


def validate_probe_transcript_public_metadata(
    scenario_path: Path,
    ref: str,
    *,
    source: str,
    oracle: dict[str, Any] | None = None,
    expected_result_ref: str | None = None,
    expected_result_digest: str | None = None,
) -> list[str]:
    failures: list[str] = []
    rel_path = repo_relative_file(ref)
    if rel_path is None:
        return failures
    artifact_forbidden_terms = sealed_oracle_forbidden_terms(oracle or {})
    try:
        raw_text = (ROOT / rel_path).read_text(encoding="utf-8")
    except OSError:
        return failures
    failures.extend(
        public_string_leakage_errors(
            scenario_path,
            raw_text,
            source=source,
            forbidden_substrings=artifact_forbidden_terms,
            forbidden_exact=set(),
            expected_generated_ref=expected_result_ref,
        )
    )
    try:
        loaded = yaml.safe_load(raw_text)
    except yaml.YAMLError:
        return failures
    forbidden_terms = sealed_oracle_forbidden_terms(oracle or {})
    if not isinstance(loaded, dict) or "ProbeTranscript" not in loaded:
        return failures
    for nested_source, text in recursive_strings(loaded, source):
        for generated_error in embedded_generated_ref_errors(
            text,
            source=nested_source,
            expected_result_ref=expected_result_ref,
        ):
            failures.append(f"{scenario_path}: {generated_error}")
        sealed_error = sealed_benchmark_file_error(text, source=nested_source)
        if sealed_error:
            failures.append(f"{scenario_path}: {sealed_error}")
        for embedded_error in embedded_repo_ref_errors(text, source=nested_source):
            failures.append(f"{scenario_path}: {embedded_error}")
        for term in forbidden_terms:
            if term and term in canonical_public_token(text):
                failures.append(f"{scenario_path}: {nested_source} must not contain sealed oracle term: {term}")
        if ".source_refs[" in nested_source:
            for ref_error in public_fixture_ref_errors(text, source=nested_source):
                failures.append(f"{scenario_path}: {ref_error}")
    transcript = loaded["ProbeTranscript"]
    if not isinstance(transcript, dict):
        return failures
    failures.extend(
        validate_probe_transcript_public_fields(
            scenario_path,
            transcript,
            source=f"{source}.ProbeTranscript",
            oracle=oracle,
            expected_result_ref=expected_result_ref,
            expected_result_digest=expected_result_digest,
        )
    )
    return failures


def validate_probe_transcript_public_fields(
    scenario_path: Path,
    fields: Any,
    *,
    source: str,
    oracle: dict[str, Any] | None = None,
    expected_result_ref: str | None = None,
    expected_result_digest: str | None = None,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(fields, dict):
        return failures
    forbidden_terms = sealed_oracle_forbidden_terms(oracle or {})
    for nested_source, text in recursive_strings(fields, source):
        for generated_error in embedded_generated_ref_errors(
            text,
            source=nested_source,
            expected_result_ref=expected_result_ref,
        ):
            failures.append(f"{scenario_path}: {generated_error}")
        sealed_error = sealed_benchmark_file_error(text, source=nested_source)
        if sealed_error:
            failures.append(f"{scenario_path}: {sealed_error}")
        for embedded_error in embedded_repo_ref_errors(text, source=nested_source):
            failures.append(f"{scenario_path}: {embedded_error}")
        for term in forbidden_terms:
            if term and term in canonical_public_token(text):
                failures.append(f"{scenario_path}: {nested_source} must not contain sealed oracle term: {term}")
        if ".source_refs[" in nested_source:
            for ref_error in public_fixture_ref_errors(text, source=nested_source):
                failures.append(f"{scenario_path}: {ref_error}")
    result_ref = fields.get("result_ref")
    result_digest = fields.get("result_digest")
    if expected_result_ref is not None:
        if not isinstance(result_ref, str):
            failures.append(
                f"{scenario_path}: {source}.result_ref must match current scenario result binding: {result_ref}"
            )
        elif result_ref != expected_result_ref:
            failures.append(
                f"{scenario_path}: {source}.result_ref must match current scenario result binding: {result_ref}"
            )
        elif result_digest != expected_result_digest:
            failures.append(
                f"{scenario_path}: {source}.result_digest must match current scenario result digest: {result_digest}"
            )
    if isinstance(result_ref, str) and not result_ref.startswith("benchmark-generated:"):
        sealed_error = sealed_benchmark_file_error(
            result_ref,
            source=f"{source}.result_ref",
        )
        if sealed_error:
            failures.append(f"{scenario_path}: {sealed_error}")
    packet_ref = fields.get("packet_ref")
    if isinstance(packet_ref, str):
        sealed_error = sealed_benchmark_file_error(
            packet_ref,
            source=f"{source}.packet_ref",
        )
        if sealed_error:
            failures.append(f"{scenario_path}: {sealed_error}")
    return failures


def check_scenario(path: Path, *, replay_probe_commands: bool = False) -> tuple[str, str, list[str], list[str]]:
    scenario = load_scenario(path)
    scenario_id = scenario["scenario_id"]
    result = scenario_result(scenario)
    result_ref, result_digest = scenario_result_binding(path, scenario, result)
    failures = validate_oracle_shape(
        path,
        scenario,
        result=result,
        expected_result_ref=result_ref,
        expected_result_digest=result_digest,
    )
    failures.extend(
        validate_result_fixture_refs(
            path,
            scenario,
            result,
            expected_result_ref=result_ref,
            expected_result_digest=result_digest,
        )
    )
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
