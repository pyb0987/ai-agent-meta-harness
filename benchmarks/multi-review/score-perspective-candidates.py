#!/usr/bin/env python3
"""Score perspective-eval candidate reviews against sealed rubric contracts."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS_ROOT = ROOT / "benchmarks" / "multi-review" / "perspective-eval" / "scenarios"
SCENARIO_VERSION = "multi-review-perspective-scenario/v1"
CANDIDATE_VERSION = "multi-review-perspective-candidate/v1"
GENERIC_RE = re.compile(r"\b(pass|acceptable|safe|valid|wrong|issue|quality|unrelated things?)\b", re.IGNORECASE)
GENERIC_TOKENS = {
    "acceptable",
    "accepting",
    "agree",
    "all",
    "be",
    "check",
    "does",
    "final",
    "invalid",
    "is",
    "might",
    "not",
    "pass",
    "reported",
    "result",
    "safe",
    "says",
    "that",
    "the",
    "things",
    "unrelated",
    "valid",
    "whether",
    "wrong",
}


class PerspectiveScoreError(ValueError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PerspectiveScoreError(f"{path}: cannot read file: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PerspectiveScoreError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PerspectiveScoreError(f"{path}: must be a mapping")
    return loaded


def text_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def normalize_text(value: object) -> str:
    text = text_value(value).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def substantive(value: object) -> bool:
    text = normalize_text(value)
    tokens = [token for token in text.split() if token not in GENERIC_TOKENS and len(token) > 2]
    return len(text) >= 12 and len(set(tokens)) >= 2 and not GENERIC_RE.fullmatch(text)


def candidate_critics(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    critics = candidate.get("critics")
    return [item for item in critics if isinstance(item, dict)] if isinstance(critics, list) else []


def final_synthesis(candidate: dict[str, Any]) -> dict[str, Any]:
    synthesis = candidate.get("final_synthesis")
    return synthesis if isinstance(synthesis, dict) else {}


def unique_substantive_values(critics: list[dict[str, Any]], field: str) -> set[str]:
    return {
        normalize_text(critic.get(field))
        for critic in critics
        if substantive(critic.get(field))
    }


def has_clean_pass_synthesis(candidate: dict[str, Any]) -> bool:
    verdict = normalize_text(final_synthesis(candidate).get("verdict"))
    summary = normalize_text(final_synthesis(candidate).get("summary"))
    preserved = final_synthesis(candidate).get("preserved_disagreement")
    return verdict == "pass" and "residual" not in summary and not preserved


def score_frame_diversity(candidate: dict[str, Any]) -> int:
    critics = candidate_critics(candidate)
    scopes = unique_substantive_values(critics, "scope")
    attacks = unique_substantive_values(critics, "attack_surface")
    if len(scopes) >= 3 and len(attacks) >= 3:
        return 5
    if len(scopes) >= 2 and len(attacks) >= 2:
        return 3
    return 0


def score_failure_mode_diversity(candidate: dict[str, Any]) -> int:
    modes = unique_substantive_values(candidate_critics(candidate), "primary_failure_mode")
    if len(modes) >= 3:
        return 5
    if len(modes) == 2:
        return 3
    return 0


def score_anti_scope_clarity(candidate: dict[str, Any]) -> int:
    critics = candidate_critics(candidate)
    anti_scopes = [
        normalize_text(critic.get("anti_scope"))
        for critic in critics
        if substantive(critic.get("anti_scope")) and "unrelated" not in normalize_text(critic.get("anti_scope"))
    ]
    if len(anti_scopes) >= 3 and len(set(anti_scopes)) >= 3:
        return 5
    if len(anti_scopes) >= 2 and len(set(anti_scopes)) >= 2:
        return 3
    return 0


def score_presupposition_challenge(candidate: dict[str, Any]) -> int:
    critics = candidate_critics(candidate)
    has_challenge = any(critic.get("frame_challenge") is True for critic in critics)
    synthesis = final_synthesis(candidate)
    preserved = synthesis.get("preserved_disagreement")
    summary = normalize_text(synthesis.get("summary"))
    if has_challenge and (preserved or "residual" in summary or "veto" in summary):
        return 5
    return 3 if has_challenge else 0


def source_refs(candidate: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for critic in candidate_critics(candidate):
        values = critic.get("source_refs")
        if isinstance(values, list):
            refs.extend(ref for ref in values if isinstance(ref, str) and ref.strip())
    return refs


def score_evidence_diversity(candidate: dict[str, Any]) -> int:
    refs = source_refs(candidate)
    unique_refs = set(refs)
    if len(unique_refs) >= max(3, len(candidate_critics(candidate))):
        return 5
    if len(unique_refs) >= 2:
        return 3
    return 0


def score_evidence_binding(candidate: dict[str, Any]) -> int:
    critics = candidate_critics(candidate)
    bound = 0
    for critic in critics:
        evidence = " ".join(item for item in critic.get("evidence", []) if isinstance(item, str))
        refs = critic.get("source_refs", [])
        if not isinstance(refs, list) or not refs:
            continue
        if substantive(evidence) and not evidence.lower().startswith("the readme exists"):
            bound += 1
    if bound >= len(critics) and score_evidence_diversity(candidate) >= 3:
        return 5
    if bound >= 2:
        return 3
    if bound == 1:
        return 1
    return 0


def has_open_disagreement(candidate: dict[str, Any]) -> bool:
    for critic in candidate_critics(candidate):
        verdict = normalize_text(critic.get("verdict"))
        findings = critic.get("blocking_findings")
        if verdict in {"veto", "concern", "fail"} or (isinstance(findings, list) and findings):
            return True
    return False


def score_disagreement_preservation(candidate: dict[str, Any]) -> int:
    if not has_open_disagreement(candidate):
        return 5 if not has_clean_pass_synthesis(candidate) else 2
    synthesis = final_synthesis(candidate)
    preserved = synthesis.get("preserved_disagreement")
    summary = normalize_text(synthesis.get("summary"))
    verdict = normalize_text(synthesis.get("verdict"))
    if verdict == "veto" and isinstance(preserved, list) and preserved:
        return 5
    if "veto" in summary or "residual" in summary or (isinstance(preserved, list) and preserved):
        return 3
    return 0


def score_final_synthesis_fidelity(candidate: dict[str, Any]) -> int:
    synthesis = final_synthesis(candidate)
    summary = normalize_text(synthesis.get("summary"))
    verdict = normalize_text(synthesis.get("verdict"))
    if has_open_disagreement(candidate):
        if verdict == "veto" and ("veto" in summary or "blocking" in summary):
            return 5
        if "residual" in summary and not has_clean_pass_synthesis(candidate):
            return 3
        return 0
    if "residual" in summary or score_evidence_diversity(candidate) >= 3:
        return 5
    return 0


CRITERIA = {
    "frame_diversity": score_frame_diversity,
    "failure_mode_diversity": score_failure_mode_diversity,
    "anti_scope_clarity": score_anti_scope_clarity,
    "presupposition_challenge": score_presupposition_challenge,
    "evidence_binding": score_evidence_binding,
    "evidence_diversity": score_evidence_diversity,
    "final_synthesis_fidelity": score_final_synthesis_fidelity,
    "disagreement_preservation": score_disagreement_preservation,
}


def public_source_ref_errors(candidate: dict[str, Any], *, candidate_path: Path) -> list[str]:
    errors: list[str] = []
    for ref in source_refs(candidate):
        ref_path = Path(ref)
        if ref_path.is_absolute() or ".." in ref_path.parts:
            errors.append(f"{candidate_path}: source_ref must be repository-local: {ref}")
            continue
        if "sealed-rubric" in ref_path.name or "sealed" in ref_path.parts:
            errors.append(f"{candidate_path}: source_ref must not point to sealed oracle material: {ref}")
            continue
        if not (ROOT / ref_path).exists():
            errors.append(f"{candidate_path}: source_ref does not resolve: {ref}")
    return errors


def score_candidate(candidate: dict[str, Any], rubric: dict[str, Any]) -> tuple[int, dict[str, int], list[str]]:
    errors: list[str] = []
    if candidate.get("schema_version") != CANDIDATE_VERSION:
        errors.append(f"candidate schema_version must be {CANDIDATE_VERSION}")
    if rubric.get("schema_version") != SCENARIO_VERSION:
        errors.append(f"rubric schema_version must be {SCENARIO_VERSION}")
    expectations = rubric.get("rubric_expectations")
    criteria = expectations.get("high_signal_criteria", []) if isinstance(expectations, dict) else []
    if not isinstance(criteria, list) or not criteria:
        errors.append("rubric_expectations.high_signal_criteria must be a non-empty list")
        criteria = []
    scores: dict[str, int] = {}
    for criterion in criteria:
        if not isinstance(criterion, str) or criterion not in CRITERIA:
            errors.append(f"unsupported high-signal criterion: {criterion}")
            continue
        scores[criterion] = CRITERIA[criterion](candidate)
    return sum(scores.values()), scores, errors


def scenario_dirs(root: Path) -> list[Path]:
    if not root.exists():
        raise PerspectiveScoreError(f"{root}: corpus root does not exist")
    return sorted(path for path in root.iterdir() if path.is_dir())


def score_scenario(scenario: Path) -> tuple[list[str], list[str]]:
    rubric = load_yaml(scenario / "sealed-rubric.yml")
    expectations = rubric.get("rubric_expectations", {})
    strong_min = expectations.get("strong_min_total") if isinstance(expectations, dict) else None
    weak_max = expectations.get("weak_max_total") if isinstance(expectations, dict) else None
    lines: list[str] = []
    errors: list[str] = []
    for name in ("candidate-strong.yml", "candidate-weak.yml"):
        candidate_path = scenario / name
        candidate = load_yaml(candidate_path)
        total, criteria, score_errors = score_candidate(candidate, rubric)
        errors.extend(f"{candidate_path}: {error}" for error in score_errors)
        errors.extend(public_source_ref_errors(candidate, candidate_path=candidate_path))
        quality = candidate.get("intended_quality")
        if quality == "strong" and isinstance(strong_min, int) and total < strong_min:
            errors.append(f"{candidate_path}: strong candidate scored {total}, expected at least {strong_min}")
        if quality == "weak" and isinstance(weak_max, int) and total > weak_max:
            errors.append(f"{candidate_path}: weak candidate scored {total}, expected at most {weak_max}")
        criteria_text = ", ".join(f"{key}={value}" for key, value in sorted(criteria.items()))
        lines.append(f"{scenario.name}/{name}: score {total} ({criteria_text})")
    return lines, errors


def emit_agent_prompt(scenario: Path, output: Path) -> None:
    public_input = scenario / "public-input.md"
    text = public_input.read_text(encoding="utf-8")
    prompt = f"""# Multi-Review Agent Evaluation Prompt

You are producing a candidate multi-review from public task input only.
Do not assume access to hidden rubrics or expected answers.

Return a YAML document using schema_version: {CANDIDATE_VERSION}.
Include at least three critics with distinct persona, scope, anti_scope,
attack_surface, primary_failure_mode, evidence, source_refs, and final_synthesis.

## Public Input

{text.rstrip()}
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prompt, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--scenario-dir", help="score one scenario directory")
    parser.add_argument("--candidate", help="score one candidate against --scenario-dir")
    parser.add_argument("--emit-agent-prompt", metavar="SCENARIO_DIR")
    parser.add_argument("--output", help="prompt output path for --emit-agent-prompt")
    args = parser.parse_args(argv)

    if args.emit_agent_prompt:
        if not args.output:
            print("ERROR: --emit-agent-prompt requires --output", file=sys.stderr)
            return 1
        scenario = Path(args.emit_agent_prompt)
        scenario = scenario if scenario.is_absolute() else ROOT / scenario
        output = Path(args.output)
        output = output if output.is_absolute() else ROOT / output
        try:
            emit_agent_prompt(scenario, output)
        except (OSError, PerspectiveScoreError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"wrote agent prompt: {output}")
        return 0

    errors: list[str] = []
    lines: list[str] = []
    try:
        if args.candidate:
            if not args.scenario_dir:
                print("ERROR: --candidate requires --scenario-dir", file=sys.stderr)
                return 1
            scenario = Path(args.scenario_dir)
            scenario = scenario if scenario.is_absolute() else ROOT / scenario
            candidate_path = Path(args.candidate)
            candidate_path = candidate_path if candidate_path.is_absolute() else ROOT / candidate_path
            rubric = load_yaml(scenario / "sealed-rubric.yml")
            candidate = load_yaml(candidate_path)
            total, criteria, score_errors = score_candidate(candidate, rubric)
            errors.extend(f"{candidate_path}: {error}" for error in score_errors)
            errors.extend(public_source_ref_errors(candidate, candidate_path=candidate_path))
            criteria_text = ", ".join(f"{key}={value}" for key, value in sorted(criteria.items()))
            lines.append(f"{candidate_path}: score {total} ({criteria_text})")
        else:
            root = Path(args.corpus_root)
            root = root if root.is_absolute() else ROOT / root
            for scenario in scenario_dirs(root):
                scenario_lines, scenario_errors = score_scenario(scenario)
                lines.extend(scenario_lines)
                errors.extend(scenario_errors)
    except PerspectiveScoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Perspective candidate scoring: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
