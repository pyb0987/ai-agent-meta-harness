#!/usr/bin/env python3
"""Create and validate v2 AcceptancePacket skeletons."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
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
LIFECYCLES = {"start", "finalized", "blocked"}
MODES = {"staged", "base-ref", "worktree"}
PROTECTED_PREFIXES = (
    ".githooks/",
    "adapters/",
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
    if kind:
        errors.append(f"{source}: kind is only valid for downgrade records")
    if not target_allowed(field, value, required_evidence, required_review):
        errors.append(f"{source}: exception target is not required: {value}")
    return errors


def validate_packet(packet: dict, *, require_stable: bool = False) -> list[str]:
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
    required_evidence, required_review = required_targets(packet)

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

    accepted = decision.get("accepted")
    stable = decision.get("stable_handoff_eligible")
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
        if review.get("veto") is True and stable:
            errors.append("stable-handoff packet cannot include VETO review")
        score = review.get("score")
        if stable and (not isinstance(score, (int, float)) or score < 9):
            errors.append("stable-handoff packet cannot include review score below 9")
        if stable:
            errors.extend(validate_review_record(review, source="result.judgment.reviews"))
        if isinstance(score, (int, float)) and score == 9:
            if not review.get("why_not_10") or not review.get("disposition"):
                errors.append("score 9 review requires why_not_10 and disposition")

    if stable:
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
        waived_evidence = {item.get("evidence") for item in judgment.get("waivers", []) if item.get("evidence")}
        downgraded_evidence = {
            item.get("from")
            for item in judgment.get("downgrades", [])
            if item.get("kind") == "evidence" and item.get("from")
        }
        missing_evidence = required_evidence - passed_evidence - waived_evidence - downgraded_evidence
        if missing_evidence:
            errors.append(f"stable packet missing required evidence: {sorted(missing_evidence)}")

        passing_reviews = {
            item.get("critic")
            for item in reviews
            if item.get("score", 0) >= 9 and item.get("veto") is False and item.get("critic")
        }
        waived_reviews = {item.get("review") for item in judgment.get("waivers", []) if item.get("review")}
        downgraded_reviews = {
            item.get("from")
            for item in judgment.get("downgrades", [])
            if item.get("kind") == "review" and item.get("from")
        }
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


def is_protected(path: str) -> bool:
    return path in PROTECTED_PATHS or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def requires_review_for_path(path: str) -> bool:
    return is_protected(path)


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
    required_review = ["checker correctness"] if protected else []
    diff_check = git(root, diff_command[1:])
    diff_status = "pass" if diff_check.returncode == 0 else "fail"

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
            "required_review": required_review,
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
            "stable_handoff_eligible": diff_status == "pass" and not protected and mode != "worktree",
            "reason": "Skeleton finalization computed from local command status only.",
            "next_action": "Run check before stable handoff.",
        },
    }
    if protected:
        packet["result"]["decision"]["reason"] = (
            "Plan 03 cannot accept protected changes yet; review import and protected-change stable promotion are out of scope."
        )
        packet["result"]["decision"]["next_action"] = "Use a later review-import plan before protected stable handoff."
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
    errors = validate_packet(packet)
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
    errors = validate_packet(packet)
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
    errors = validate_packet(packet, require_stable=args.require_stable)
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
