#!/usr/bin/env python3
"""Validate multi-review perspective-eval corpus structure, not semantics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_ROOT = ROOT / "benchmarks" / "multi-review" / "perspective-eval" / "scenarios"
SCENARIO_VERSION = "multi-review-perspective-scenario/v1"
CANDIDATE_VERSION = "multi-review-perspective-candidate/v1"

REQUIRED_SCENARIO_FILES = {
    "public-input.md",
    "sealed-rubric.yml",
    "candidate-strong.yml",
    "candidate-weak.yml",
}
REQUIRED_RUBRIC_FIELDS = {
    "schema_version",
    "scenario_id",
    "scenario_type",
    "surface_success_path",
    "anchored_risks",
    "rubric_expectations",
    "judge_instructions",
}
REQUIRED_CANDIDATE_FIELDS = {
    "schema_version",
    "candidate_id",
    "intended_quality",
    "reported_verdict",
    "critics",
    "final_synthesis",
}
REQUIRED_CRITIC_FIELDS = {
    "critic_id",
    "persona",
    "scope",
    "anti_scope",
    "attack_surface",
    "primary_failure_mode",
    "frame_challenge",
    "verdict",
    "evidence",
    "source_refs",
}


class CorpusError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CorpusError(f"{path}: cannot read file: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CorpusError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise CorpusError(f"{path}: must be a mapping")
    return loaded


def require_fields(path: Path, data: dict[str, Any], fields: set[str]) -> list[str]:
    missing = sorted(fields - set(data))
    return [f"{path}: missing fields: {missing}"] if missing else []


def require_non_empty_list(path: Path, data: dict[str, Any], field: str) -> list[str]:
    if not isinstance(data.get(field), list) or not data[field]:
        return [f"{path}: {field} must be a non-empty list"]
    return []


def validate_rubric(path: Path) -> list[str]:
    data = load_yaml(path)
    errors = require_fields(path, data, REQUIRED_RUBRIC_FIELDS)
    if data.get("schema_version") != SCENARIO_VERSION:
        errors.append(f"{path}: schema_version must be {SCENARIO_VERSION}")
    for field in ("surface_success_path", "anchored_risks", "judge_instructions"):
        errors.extend(require_non_empty_list(path, data, field))
    expectations = data.get("rubric_expectations")
    if not isinstance(expectations, dict):
        errors.append(f"{path}: rubric_expectations must be a mapping")
    else:
        for field in ("strong_min_total", "weak_max_total", "high_signal_criteria"):
            if field not in expectations:
                errors.append(f"{path}: rubric_expectations missing {field}")
        if not isinstance(expectations.get("high_signal_criteria", []), list):
            errors.append(f"{path}: rubric_expectations.high_signal_criteria must be a list")
    return errors


def validate_candidate(path: Path, expected_quality: str) -> list[str]:
    data = load_yaml(path)
    errors = require_fields(path, data, REQUIRED_CANDIDATE_FIELDS)
    if data.get("schema_version") != CANDIDATE_VERSION:
        errors.append(f"{path}: schema_version must be {CANDIDATE_VERSION}")
    if data.get("intended_quality") != expected_quality:
        errors.append(f"{path}: intended_quality must be {expected_quality}")
    critics = data.get("critics")
    if not isinstance(critics, list) or len(critics) < 3:
        errors.append(f"{path}: critics must contain at least three entries")
    else:
        for index, critic in enumerate(critics):
            if not isinstance(critic, dict):
                errors.append(f"{path}: critics[{index}] must be a mapping")
                continue
            errors.extend(require_fields(path, critic, REQUIRED_CRITIC_FIELDS))
            for field in ("evidence", "source_refs"):
                if field in critic and (not isinstance(critic[field], list) or not critic[field]):
                    errors.append(f"{path}: critics[{index}].{field} must be a non-empty list")
    synthesis = data.get("final_synthesis")
    if not isinstance(synthesis, dict):
        errors.append(f"{path}: final_synthesis must be a mapping")
    else:
        for field in ("verdict", "summary", "preserved_disagreement"):
            if field not in synthesis:
                errors.append(f"{path}: final_synthesis missing {field}")
        if "preserved_disagreement" in synthesis and not isinstance(synthesis["preserved_disagreement"], list):
            errors.append(f"{path}: final_synthesis.preserved_disagreement must be a list")
    return errors


def validate_scenario(path: Path) -> list[str]:
    errors: list[str] = []
    present = {item.name for item in path.iterdir() if item.is_file()}
    missing = sorted(REQUIRED_SCENARIO_FILES - present)
    if missing:
        errors.append(f"{path}: missing files: {missing}")
        return errors
    public_input = path / "public-input.md"
    if not public_input.read_text(encoding="utf-8").strip():
        errors.append(f"{public_input}: must not be empty")
    errors.extend(validate_rubric(path / "sealed-rubric.yml"))
    errors.extend(validate_candidate(path / "candidate-strong.yml", "strong"))
    errors.extend(validate_candidate(path / "candidate-weak.yml", "weak"))
    return errors


def scenario_dirs(root: Path) -> list[Path]:
    if not root.exists():
        raise CorpusError(f"{root}: corpus root does not exist")
    return sorted(path for path in root.iterdir() if path.is_dir())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    args = parser.parse_args(argv)
    root = Path(args.corpus_root)
    root = root if root.is_absolute() else ROOT / root
    try:
        scenarios = scenario_dirs(root)
    except CorpusError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    for scenario in scenarios:
        errors.extend(validate_scenario(scenario))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Perspective corpus scenarios valid: {len(scenarios)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
