#!/usr/bin/env python3
"""Validate and prepare strategy-search direction and candidate records."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import posixpath
from pathlib import Path
import re
import signal
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any
from urllib.parse import unquote
import uuid

import yaml


ROOT = Path(__file__).resolve().parents[1]
DIRECTION_SCHEMA_VERSION = "strategy-search-direction/v1"
CANDIDATE_SCHEMA_VERSION = "strategy-search-candidate/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

DIRECTION_FIELDS = {
    "schema_version",
    "direction_id",
    "objective",
    "base_ref",
    "search_surface",
    "protected_evaluator_paths",
    "evaluator",
    "success",
    "notes",
}
EVALUATOR_FIELDS = {
    "command",
    "timeout_seconds",
    "protected_paths",
    "oracle_paths",
    "score_parser_paths",
}
SUCCESS_FIELDS = {"min_score", "max_regressions"}
CANDIDATE_FIELDS = {
    "schema_version",
    "candidate_id",
    "run_id",
    "base_commit",
    "direction_digest",
    "search_surface_digest_before",
    "patch_sha256",
    "evaluator_command",
    "evaluator_digest",
    "evaluator_closure",
    "started_at",
    "finished_at",
    "exit_code",
    "score",
    "case_results",
    "stdout_sha256",
    "stderr_sha256",
    "trace_sha256",
    "verdict",
}
CLOSURE_GROUPS = ("protected_paths", "oracle_paths", "score_parser_paths")
CLOSURE_DIGEST_FIELDS = {"before_sha256", "after_sha256"}
VALID_VERDICTS = {"pass", "fail", "invalid"}
VALID_CASE_STATUSES = {"pass", "fail", "skip", "xfail"}
RUN_SCHEMA_VERSION = "strategy-search-run/v1"
TRACE_SCHEMA_VERSION = "strategy-search-trace/v1"
TRACE_FIELDS = {
    "schema_version",
    "run_id",
    "candidate_id",
    "base_commit",
    "direction_digest",
    "created_at",
    "evidence_status",
    "why",
    "changed_paths",
    "result",
    "patch_ref",
    "stdout_ref",
    "stderr_ref",
    "candidate_metadata_ref",
    "next_hypothesis",
    "notes",
}
TRACE_RESULT_FIELDS = {"verdict", "score", "exit_code", "timed_out", "case_results"}
TRACE_REF_FIELDS = {"ref", "sha256"}
SEARCH_SET_SCHEMA_VERSION = "strategy-search-set/v1"
SELECTED_SUMMARY_SCHEMA_VERSION = "strategy-search-selected-candidate-summary/v1"
PROPOSAL_SCHEMA_VERSION = "strategy-search-proposal/v1"
PROPOSAL_CONTEXT_SCHEMA_VERSION = "strategy-search-proposal-context/v1"
PROPOSAL_POLICY_SCHEMA_VERSION = "strategy-search-proposal-policy/v1"
PROPOSAL_FIELDS = {
    "schema_version",
    "run_id",
    "candidate_id",
    "base_commit",
    "direction_digest",
    "created_at",
    "evidence_status",
    "status",
    "prompt_ref",
    "policy_ref",
    "context_ref",
    "prompt_sha256",
    "policy_sha256",
    "context_sha256",
    "patch_ref",
    "patch_sha256",
    "why",
    "next_hypothesis",
    "validation_errors",
    "evaluation_command",
}
PROPOSAL_STATUSES = {"awaiting_patch", "ready_for_evaluation", "invalid"}
PROPOSAL_CONTEXT_FIELDS = {
    "schema_version",
    "run_id",
    "base_commit",
    "direction_digest",
    "evidence_status",
    "direction",
    "public_run_refs",
    "prior_candidates",
    "sealed_material_excluded",
    "notes",
}
PROPOSAL_CONTEXT_DIRECTION_FIELDS = {"direction_id", "objective", "search_surface", "success", "notes"}
PROPOSAL_CONTEXT_REFS_FIELDS = {"summary_ref", "search_set_ref"}
PROPOSAL_CONTEXT_CANDIDATE_FIELDS = {
    "candidate_id",
    "verdict",
    "score",
    "validation_error_count",
    "trace_summary",
}
PROPOSAL_CONTEXT_TRACE_SUMMARY_FIELDS = {"why", "changed_paths", "next_hypothesis", "evidence_status"}
PROPOSAL_POLICY_FIELDS = {
    "schema_version",
    "run_id",
    "candidate_id",
    "evidence_status",
    "allowed_write_paths",
    "rules",
    "evaluation",
}
PROPOSAL_POLICY_EVALUATION_FIELDS = {"runner", "uses_fixed_direction_evaluator"}
PROPOSAL_LEDGER_SCHEMA_VERSION = "strategy-search-proposal-ledger/v1"
PROPOSAL_EVALUATION_COMMAND = "python3 scripts/strategy-search.py eval --run <run> --proposal <proposal.yml> --overwrite"
ADOPTION_SCHEMA_VERSION = "strategy-search-adoption-selection/v1"
SEARCH_RUNS_PREFIX = ".harness/search-runs/"
ARCHIVE_ARTIFACT_PREFIX = "archive/v2/artifacts/"
SIDE_EFFECT_SETTLE_SECONDS = 0.25


class StrategySearchError(ValueError):
    pass


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StrategySearchError(f"{path}: cannot read file: {exc}") from exc
    except yaml.YAMLError as exc:
        raise StrategySearchError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise StrategySearchError(f"{path}: must be a mapping")
    return loaded


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_direction(direction: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(direction))


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def has_git_pathspec_magic(value: str) -> bool:
    return value.startswith(":")


def repo_relative_path(value: str, *, source: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{source} must be a non-empty repository-relative path")
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{source} must be repository-relative and must not contain '..': {value}")
        return None
    normalized = path.as_posix().rstrip("/")
    if has_git_pathspec_magic(normalized):
        errors.append(f"{source} must use a literal repository path, not git pathspec magic: {value}")
        return None
    if "?" in normalized:
        errors.append(f"{source} must use a literal repository path, not query-style decoration: {value}")
        return None
    if not normalized or normalized == ".":
        errors.append(f"{source} must not be the repository root")
        return None
    return normalized


def path_exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def path_has_symlink(root: Path, rel_path: str) -> bool:
    path = root / rel_path
    if path.is_symlink():
        return True
    if not path.is_dir():
        return False
    return any(item.is_symlink() for item in path.rglob("*"))


def path_is_dir_spec(root: Path, spec: str) -> bool:
    return spec.endswith("/") or (root / spec).is_dir()


def path_matches_spec(path: str, spec: str, *, root: Path) -> bool:
    spec_clean = spec.rstrip("/")
    if path == spec_clean:
        return True
    return path_is_dir_spec(root, spec) and path.startswith(f"{spec_clean}/")


def path_overlaps(a: str, b: str, *, root: Path) -> bool:
    return path_matches_spec(a, b, root=root) or path_matches_spec(b, a, root=root)


def iter_digest_files(root: Path, rel_path: str) -> list[Path]:
    path = root / rel_path
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*") if item.is_file() and ".git" not in item.parts)
    return []


def digest_paths(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(dict.fromkeys(paths)):
        files = iter_digest_files(root, rel_path)
        if not files:
            digest.update(f"missing\0{rel_path}\0".encode("utf-8"))
            continue
        for file_path in files:
            relative = file_path.resolve().relative_to(root.resolve()).as_posix()
            digest.update(f"file\0{relative}\0".encode("utf-8"))
            digest.update(file_path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def git_output(root: Path, args: list[str], *, text: bool = True) -> str | bytes | None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        encoding="utf-8" if text else None,
        text=text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout if result.returncode == 0 else None


def git_ref_commit(root: Path, ref: str) -> str | None:
    output = git_output(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    return output.strip() if isinstance(output, str) and output.strip() else None


def git_blob_bytes(root: Path, commit: str, rel_path: str) -> bytes | None:
    output = git_output(root, ["show", f"{commit}:{rel_path}"], text=False)
    return output if isinstance(output, bytes) else None


def git_tree_files(root: Path, commit: str, rel_path: str) -> list[str]:
    if has_git_pathspec_magic(rel_path):
        return []
    output = git_output(root, ["ls-tree", "-r", "-z", "--name-only", commit, "--", rel_path])
    if not isinstance(output, str):
        return []
    return sorted(path for path in output.split("\0") if path)


def git_tree_entries(root: Path, commit: str, rel_path: str) -> list[tuple[str, str]]:
    if has_git_pathspec_magic(rel_path):
        return []
    output = git_output(root, ["ls-tree", "-r", "-z", commit, "--", rel_path])
    if not isinstance(output, str):
        return []
    entries: list[tuple[str, str]] = []
    for entry in output.split("\0"):
        if not entry or "\t" not in entry:
            continue
        meta, path = entry.split("\t", 1)
        mode = meta.split(" ", 1)[0]
        entries.append((mode, path))
    return entries


def path_exists_at_commit(root: Path, commit: str, rel_path: str) -> bool:
    return bool(git_tree_files(root, commit, rel_path.rstrip("/")))


def path_is_file_at_commit(root: Path, commit: str, rel_path: str) -> bool:
    clean = rel_path.rstrip("/")
    return any(path == clean for _mode, path in git_tree_entries(root, commit, clean))


def path_is_dir_at_commit(root: Path, commit: str, rel_path: str) -> bool:
    clean = rel_path.rstrip("/")
    return any(path.startswith(f"{clean}/") for path in git_tree_files(root, commit, clean))


def path_has_symlink_at_commit(root: Path, commit: str, rel_path: str) -> bool:
    return any(mode == "120000" for mode, _path in git_tree_entries(root, commit, rel_path.rstrip("/")))


def digest_paths_at_commit(root: Path, commit: str, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for rel_path in sorted(dict.fromkeys(paths)):
        files = git_tree_files(root, commit, rel_path.rstrip("/"))
        if not files:
            digest.update(f"missing\0{rel_path}\0".encode("utf-8"))
            continue
        for file_rel in files:
            blob = git_blob_bytes(root, commit, file_rel)
            if blob is None:
                digest.update(f"missing\0{file_rel}\0".encode("utf-8"))
                continue
            digest.update(f"file\0{file_rel}\0".encode("utf-8"))
            digest.update(blob)
            digest.update(b"\0")
    return digest.hexdigest()


def validate_exact_fields(mapping: dict[str, Any], expected: set[str], *, source: str, errors: list[str]) -> None:
    missing = sorted(expected - set(mapping))
    extra = sorted(set(mapping) - expected)
    if missing:
        errors.append(f"{source} missing fields: {missing}")
    if extra:
        errors.append(f"{source} extra fields: {extra}")


def validate_path_list(
    root: Path,
    value: object,
    *,
    source: str,
    require_exists: bool,
    base_commit: str | None = None,
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{source} must be a non-empty list")
        return []
    paths: list[str] = []
    for index, item in enumerate(value):
        rel_path = repo_relative_path(item, source=f"{source}[{index}]", errors=errors)
        if rel_path is None:
            continue
        if rel_path.startswith("archive/v2/"):
            errors.append(f"{source}[{index}] must not target archive/v2 during strategy search: {rel_path}")
        if require_exists and base_commit and (root / ".git").exists():
            if not path_exists_at_commit(root, base_commit, rel_path):
                errors.append(f"{source}[{index}] does not exist at base_ref: {rel_path}")
            if path_has_symlink_at_commit(root, base_commit, rel_path):
                errors.append(f"{source}[{index}] must not be or contain a symlink at base_ref: {rel_path}")
            if path_is_dir_at_commit(root, base_commit, rel_path):
                rel_path = f"{rel_path.rstrip('/')}/"
        elif require_exists:
            if not path_exists(root, rel_path):
                errors.append(f"{source}[{index}] does not exist: {rel_path}")
            if path_has_symlink(root, rel_path):
                errors.append(f"{source}[{index}] must not be or contain a symlink: {rel_path}")
            if (root / rel_path).is_dir():
                rel_path = f"{rel_path.rstrip('/')}/"
        paths.append(rel_path)
    if len(paths) != len(set(paths)):
        errors.append(f"{source} must not contain duplicate paths")
    return paths


def evaluator_closure_paths(direction: dict[str, Any]) -> dict[str, list[str]]:
    evaluator = direction.get("evaluator", {})
    if not isinstance(evaluator, dict):
        return {group: [] for group in CLOSURE_GROUPS}
    return {group: string_list(evaluator.get(group, [])) for group in CLOSURE_GROUPS}


def evaluator_combined_closure(direction: dict[str, Any]) -> list[str]:
    paths = string_list(direction.get("protected_evaluator_paths", []))
    for values in evaluator_closure_paths(direction).values():
        paths.extend(values)
    return sorted(dict.fromkeys(paths))


def evaluator_digest(root: Path, direction: dict[str, Any], *, commit: str | None = None) -> str:
    paths = evaluator_combined_closure(direction)
    if commit:
        return digest_paths_at_commit(root, commit, paths)
    return digest_paths(root, paths)


EVALUATOR_PATH_SUFFIXES = (".py", ".sh", ".js", ".mjs", ".yml", ".yaml", ".json", ".txt", ".toml", ".ini", ".cfg", ".csv")
PYTHON_RUNTIME_RE = re.compile(r"^python3(?:\.\d+)*$")
SUPPORTED_EVALUATOR_RUNTIMES = {"node", "sh", "bash"}
PYTHON_FLAG_OPTIONS = {"-q", "--quiet"}
BLOCKED_EVALUATOR_ENV_KEYS = {
    "BASH_ENV",
    "DYLD_FALLBACK_LIBRARY_PATH",
    "DYLD_FRAMEWORK_PATH",
    "DYLD_INSERT_LIBRARIES",
    "DYLD_LIBRARY_PATH",
    "ENV",
    "LD_AUDIT",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "NODE_OPTIONS",
    "NODE_PATH",
    "PATH",
    "PYTHONHOME",
    "PYTHONPATH",
}


def command_repo_path_exists(root: Path | None, base_commit: str | None, value: str) -> bool:
    if root is None:
        return False
    return (
        path_exists_at_commit(root, base_commit, value)
        if base_commit and (root / ".git").exists()
        else path_exists(root, value)
    )


def command_repo_path_is_file(root: Path | None, base_commit: str | None, value: str) -> bool:
    if root is None:
        return False
    return (
        path_is_file_at_commit(root, base_commit, value)
        if base_commit and (root / ".git").exists()
        else (root / value).is_file()
    )


def command_token_looks_like_path(value: str) -> bool:
    return "/" in value or value.endswith(EVALUATOR_PATH_SUFFIXES)


def evaluator_command_target_index(argv: list[str], *, root: Path | None, base_commit: str | None) -> int | None:
    def repo_file(value: str) -> bool:
        return command_repo_path_is_file(root, base_commit, value)

    def runtime_name(value: str) -> str:
        return Path(value).name

    index = 0
    if argv and argv[0] == "env":
        index = 1
        while index < len(argv):
            token = argv[index]
            if token == "--":
                index += 1
                break
            if token == "-S" or token.startswith("-S") or token == "--split-string" or token.startswith("--split-string="):
                return None
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                index += 1
                continue
            if token.startswith("-"):
                return None
            break
    if index >= len(argv):
        return None

    if argv[index] != runtime_name(argv[index]):
        return None
    command_name = runtime_name(argv[index])
    if not (PYTHON_RUNTIME_RE.fullmatch(command_name) or command_name in SUPPORTED_EVALUATOR_RUNTIMES):
        return None

    runtime = "python" if PYTHON_RUNTIME_RE.fullmatch(command_name) else command_name
    index += 1
    after_runtime_terminator = False

    while index < len(argv):
        token = argv[index]
        if token == "--":
            if after_runtime_terminator:
                return None
            after_runtime_terminator = True
            index += 1
            continue
        if token.startswith("-") and not after_runtime_terminator:
            if token == "-":
                return None
            if token in {"-c", "-m", "-e", "--eval", "--execute", "--command"}:
                return None
            if runtime == "node" and (
                token == "-p" or token.startswith("-p") or token == "--print" or token.startswith("--print=")
            ):
                return None
            if runtime in {"sh", "bash"} and (token == "-s" or token.startswith("-s")):
                return None
            if runtime == "python" and token in PYTHON_FLAG_OPTIONS:
                index += 1
                continue
            return None
        if token == "-":
            return None
        if repo_file(token):
            return index
        if after_runtime_terminator:
            return None
        return None
    return None


def evaluator_command_paths(
    argv: list[str],
    *,
    root: Path | None = None,
    base_commit: str | None = None,
    errors: list[str],
) -> list[str]:
    paths: list[str] = []

    if argv and argv[0] == "env":
        for env_token in argv[1:]:
            if env_token == "--":
                break
            if env_token.startswith("-"):
                errors.append(f"evaluator.command env options are not supported: {env_token!r}")
                continue
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", env_token):
                break
            env_key = env_token.split("=", 1)[0]
            if env_key in BLOCKED_EVALUATOR_ENV_KEYS:
                errors.append(f"evaluator.command must not set runtime hook environment variable: {env_key}")

    def token_variants(value: str) -> list[str]:
        variants: set[str] = {value}
        pending = [value]
        while pending:
            current = pending.pop()
            for separator in ("?", "::", "#"):
                if separator in current:
                    stripped = current.split(separator, 1)[0]
                    if stripped and stripped not in variants:
                        variants.add(stripped)
                        pending.append(stripped)
            if ":" in current and not re.match(r"^[A-Za-z]:", current):
                stripped = current.split(":", 1)[0]
                if stripped and stripped not in variants:
                    variants.add(stripped)
                    pending.append(stripped)
        return sorted(variants, key=lambda item: (len(Path(item).parts), len(item), item))

    def repo_path_exists(value: str) -> bool:
        return command_repo_path_exists(root, base_commit, value)

    target_index = evaluator_command_target_index(argv, root=root, base_commit=base_commit)
    allow_dash_path_token = False
    after_option_terminator = False
    pending_path_option: str | None = None
    for index, token in enumerate(argv):
        after_target = target_index is not None and index > target_index
        if token == "--":
            if pending_path_option is not None and after_target:
                errors.append(
                    "evaluator.command separated path-valued options are not supported; "
                    f"use --name=value or pass positional paths after '--': {pending_path_option!r} {token!r}"
                )
                pending_path_option = None
                continue
            if after_target and after_option_terminator:
                errors.append("evaluator.command repeated option terminators are not supported after evaluator target: '--'")
                continue
            pending_path_option = None
            if target_index is not None and index < target_index:
                allow_dash_path_token = index + 1 == target_index
            elif target_index is not None and index > target_index:
                allow_dash_path_token = True
                after_option_terminator = True
            else:
                allow_dash_path_token = False
            continue
        if pending_path_option is not None and after_target and not after_option_terminator:
            if command_token_looks_like_path(token) or repo_path_exists(token):
                errors.append(
                    "evaluator.command separated path-valued options are not supported; "
                    f"use --name=value or pass positional paths after '--': {pending_path_option!r} {token!r}"
                )
                pending_path_option = None
                continue
            pending_path_option = None
        token_values = [token]
        before_env_target = argv and argv[0] == "env" and target_index is not None and 0 < index < target_index
        if before_env_target and not token.startswith("-") and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            assignment_value = token.split("=", 1)[1]
            token_values = [assignment_value, *[value for value in assignment_value.split(os.pathsep) if value]]
        explicit_dash_path = allow_dash_path_token and token.startswith("-") and repo_path_exists(token)
        allow_dash_path_token = False
        if not explicit_dash_path and token.startswith("-"):
            if not token.startswith("--"):
                if repo_path_exists(token):
                    errors.append(
                        "evaluator.command dash-leading paths must be passed after '--' "
                        f"or as an explicit relative path: {token!r}"
                    )
                    continue
                if len(token) > 2 or "=" in token:
                    errors.append(
                        "evaluator.command path-valued short options are not supported; "
                        f"use --name=value or pass dash-leading paths after '--': {token!r}"
                    )
                    continue
                if after_target and len(token) == 2:
                    pending_path_option = token
                continue
            if "=" in token:
                token_values = [token.split("=", 1)[1]]
            else:
                if repo_path_exists(token):
                    errors.append(
                        "evaluator.command dash-leading paths must be passed after '--' "
                        f"or as an explicit relative path: {token!r}"
                    )
                if after_target:
                    pending_path_option = token
                continue
            token_values = [value for value in token_values if value]
            if not token_values:
                continue
        for token_value in token_values:
            if "?" in token_value:
                errors.append(f"evaluator.command path must not use query-style decoration: {token!r}")
                continue
            if "#" in token_value:
                errors.append(f"evaluator.command path must not use fragment-style decoration: {token!r}")
                continue
            if "," in token_value:
                errors.append(f"evaluator.command path must not use comma-style decoration: {token!r}")
                continue
            if "@" in token_value:
                errors.append(f"evaluator.command path must not use at-style decoration: {token!r}")
                continue
            if "=" in token_value:
                errors.append(f"evaluator.command path must not use equals-style decoration: {token!r}")
                continue
            if ":" in token_value and not re.match(r"^[A-Za-z]:", token_value):
                errors.append(f"evaluator.command path must not use colon-style decoration: {token!r}")
                continue
            existing_match: str | None = None
            fallback_match: str | None = None
            for candidate_text in token_variants(token_value):
                looks_like_path = command_token_looks_like_path(candidate_text)
                candidate = Path(candidate_text)
                if has_git_pathspec_magic(candidate_text):
                    repo_relative_path(candidate_text, source=f"evaluator.command path {token!r}", errors=errors)
                    continue
                if candidate.is_absolute() or ".." in candidate.parts:
                    if looks_like_path:
                        repo_relative_path(candidate_text, source=f"evaluator.command path {token!r}", errors=errors)
                    continue
                normalized = candidate.as_posix().rstrip("/")
                exists_in_repo = repo_path_exists(normalized)
                if not looks_like_path and not exists_in_repo:
                    continue
                if exists_in_repo:
                    existing_match = candidate_text
                    break
                if fallback_match is None and looks_like_path:
                    fallback_match = candidate_text
            selected_match = existing_match or fallback_match
            if selected_match is not None:
                rel_path = repo_relative_path(selected_match, source=f"evaluator.command path {token!r}", errors=errors)
                if rel_path is not None:
                    paths.append(rel_path)
    return sorted(dict.fromkeys(paths))


def command_uses_governance_publication(argv: list[str]) -> bool:
    blocked_names = {
        "write-pointer",
        "check-pointer",
        "verify-release",
        "verify-release.py",
        "check-governance-acceptance.py",
        "check-active-packet-gate.py",
    }
    normalized = [Path(token).name for token in argv]
    if any(token in blocked_names for token in normalized):
        return True
    if "publish" in normalized and any(token in {"governance", "check-governance-acceptance.py"} for token in normalized):
        return True
    return any(normalized[index] == "governance" and normalized[index + 1] == "publish" for index in range(len(normalized) - 1))


def command_uses_inline_code(argv: list[str], *, root: Path | None = None, base_commit: str | None = None) -> bool:
    inline_flags = {"-c", "-m", "-e", "--eval", "--execute", "--command"}
    inline_prefixes = ("--eval=", "--execute=", "--command=")
    target_index = evaluator_command_target_index(argv, root=root, base_commit=base_commit)
    scan_limit = target_index if target_index is not None else len(argv)
    dash_path_after_terminator = False
    for index, token in enumerate(argv):
        if index >= scan_limit:
            break
        if token != "env":
            continue
        for option_index, option in enumerate(argv[index + 1 :], start=index + 1):
            if option_index >= scan_limit:
                break
            if option == "--":
                break
            if option == "-S" or option.startswith("-S") or option == "--split-string" or option.startswith("--split-string="):
                return True
    has_node = any(Path(token).name == "node" for token in argv[:scan_limit])
    for index, token in enumerate(argv):
        if index >= scan_limit:
            break
        if token == "--":
            dash_path_after_terminator = True
            continue
        if has_node and (token == "-p" or token.startswith("-p") or token == "--print" or token.startswith("--print=")):
            return True
        if token in inline_flags or token.startswith(inline_prefixes):
            return True
        if token.startswith(("-c", "-m", "-e")) and len(token) > 2:
            exists_as_path = False
            if dash_path_after_terminator and root is not None:
                exists_as_path = command_repo_path_exists(root, base_commit, token)
            if not exists_as_path:
                return True
        dash_path_after_terminator = False
    return False


def normalized_direction_specs(root: Path, direction: dict[str, Any], paths: list[str]) -> list[str]:
    base_commit = direction.get("base_ref") if isinstance(direction.get("base_ref"), str) else None
    normalized: list[str] = []
    for path in paths:
        clean = path.rstrip("/")
        if base_commit and (root / ".git").exists() and git_ref_commit(root, base_commit):
            normalized.append(f"{clean}/" if path_is_dir_at_commit(root, base_commit, clean) else clean)
        else:
            normalized.append(f"{clean}/" if (root / clean).is_dir() else clean)
    return sorted(dict.fromkeys(normalized))


def validate_direction(direction: dict[str, Any], *, root: Path) -> list[str]:
    errors: list[str] = []
    validate_exact_fields(direction, DIRECTION_FIELDS, source="direction", errors=errors)
    if direction.get("schema_version") != DIRECTION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {DIRECTION_SCHEMA_VERSION}")
    for field in ("direction_id", "objective", "base_ref"):
        if not isinstance(direction.get(field), str) or not direction[field].strip():
            errors.append(f"{field} must be a non-empty string")
    base_commit = direction.get("base_ref") if isinstance(direction.get("base_ref"), str) else None
    if isinstance(direction.get("base_ref"), str):
        if not FULL_COMMIT_RE.fullmatch(direction["base_ref"]):
            errors.append("base_ref must be a full commit SHA for reproducible strategy search")
            base_commit = None
        elif (root / ".git").exists() and git_ref_commit(root, direction["base_ref"]) is None:
            errors.append(f"base_ref must resolve to a commit: {direction['base_ref']}")
            base_commit = None

    search_surface = validate_path_list(
        root,
        direction.get("search_surface"),
        source="search_surface",
        require_exists=True,
        base_commit=base_commit,
        errors=errors,
    )
    protected_evaluator_paths = validate_path_list(
        root,
        direction.get("protected_evaluator_paths"),
        source="protected_evaluator_paths",
        require_exists=True,
        base_commit=base_commit,
        errors=errors,
    )
    if isinstance(direction.get("search_surface"), list):
        direction["search_surface"] = search_surface

    evaluator = direction.get("evaluator")
    if not isinstance(evaluator, dict):
        errors.append("evaluator must be a mapping")
        evaluator = {}
    else:
        validate_exact_fields(evaluator, EVALUATOR_FIELDS, source="evaluator", errors=errors)
    command = evaluator.get("command")
    command_paths: list[str] = []
    if not isinstance(command, str) or not command.strip():
        errors.append("evaluator.command must be a non-empty string")
    else:
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            errors.append(f"evaluator.command must be shell-parseable: {exc}")
        else:
            if not argv:
                errors.append("evaluator.command must not be empty")
            command_paths = evaluator_command_paths(argv, root=root, base_commit=base_commit, errors=errors)
            if command_uses_inline_code(argv, root=root, base_commit=base_commit):
                errors.append("evaluator.command must run repository-local evaluator files, not inline/module code")
            if evaluator_command_target_index(argv, root=root, base_commit=base_commit) is None:
                errors.append("evaluator.command must execute a repository-local evaluator file via a supported runtime")
            if not command_paths:
                errors.append("evaluator.command must name at least one repository-local evaluator file")
            if command_uses_governance_publication(argv):
                errors.append("evaluator.command must not run governance publication or release commands")
    timeout = evaluator.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        errors.append("evaluator.timeout_seconds must be a positive integer")

    closure: dict[str, list[str]] = {}
    for group in CLOSURE_GROUPS:
        closure[group] = validate_path_list(
            root,
            evaluator.get(group),
            source=f"evaluator.{group}",
            require_exists=True,
            base_commit=base_commit,
            errors=errors,
        )
    closure_union = sorted(dict.fromkeys([*protected_evaluator_paths, *sum(closure.values(), [])]))
    explicit_closure_paths = sorted(dict.fromkeys(sum(closure.values(), [])))
    for protected_path in protected_evaluator_paths:
        if not path_allowed(protected_path, explicit_closure_paths, root=root):
            errors.append(
                "protected_evaluator_paths must be represented in evaluator closure groups: "
                f"{protected_path}"
            )
    for command_path in command_paths:
        if not path_allowed(command_path, closure_union, root=root):
            errors.append(f"evaluator.command path must be represented in evaluator closure groups: {command_path}")
    for search_path in search_surface:
        for protected_path in closure_union:
            if path_overlaps(search_path, protected_path, root=root):
                errors.append(
                    "search_surface must not overlap evaluator closure: "
                    f"{search_path} overlaps {protected_path}"
                )

    success = direction.get("success")
    if not isinstance(success, dict):
        errors.append("success must be a mapping")
    else:
        validate_exact_fields(success, SUCCESS_FIELDS, source="success", errors=errors)
        min_score = success.get("min_score")
        if not isinstance(min_score, (int, float)) or isinstance(min_score, bool) or min_score < 0:
            errors.append("success.min_score must be a non-negative number")
        max_regressions = success.get("max_regressions")
        if not isinstance(max_regressions, int) or isinstance(max_regressions, bool) or max_regressions < 0:
            errors.append("success.max_regressions must be a non-negative integer")
    if not isinstance(direction.get("notes"), list):
        errors.append("notes must be a list")
    return errors


def strip_patch_prefix(raw_path: str) -> str | None:
    if raw_path == "/dev/null":
        return None
    if raw_path.startswith("a/") or raw_path.startswith("b/"):
        return raw_path[2:]
    return raw_path


def patch_header_path(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None
    if text == "/dev/null":
        return None
    if text.startswith('"'):
        try:
            parts = shlex.split(text)
        except ValueError:
            parts = []
        if parts:
            return strip_patch_prefix(parts[0])
    if text.startswith(("a/", "b/")):
        path = text[2:]
        if "\t" in path:
            path = path.split("\t", 1)[0]
        return path
    if "\t" in text:
        text = text.split("\t", 1)[0]
    return strip_patch_prefix(text)


def patch_touched_paths(patch_path: Path) -> tuple[set[str], list[str]]:
    paths: set[str] = set()
    errors: list[str] = []
    if not patch_path.is_file():
        return paths, errors
    diff_re = re.compile(r"^diff --git a/(.+?) b/(.+)$")
    for line in patch_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = diff_re.match(line)
        if match:
            for raw_path in match.groups():
                path = strip_patch_prefix(raw_path)
                if path is not None:
                    paths.add(path)
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            path = patch_header_path(line[4:].strip())
            if path is not None:
                paths.add(path)
    if patch_path.read_text(encoding="utf-8", errors="replace").strip() and not paths:
        errors.append("patch.diff contains no parseable file paths")
    return paths, errors


def path_allowed(path: str, allowed_specs: list[str], *, root: Path) -> bool:
    return any(path_matches_spec(path, spec, root=root) for spec in allowed_specs)


def patch_boundary_errors(root: Path, direction: dict[str, Any], patch_path: Path) -> list[str]:
    touched, errors = patch_touched_paths(patch_path)
    search_surface = normalized_direction_specs(root, direction, string_list(direction.get("search_surface", [])))
    closure_paths = normalized_direction_specs(root, direction, evaluator_combined_closure(direction))
    for touched_path in sorted(touched):
        normalized = repo_relative_path(touched_path, source=f"candidate patch path {touched_path!r}", errors=errors)
        if normalized is None:
            continue
        if normalized.startswith("archive/v2/"):
            errors.append(f"candidate patch must not touch archive/v2: {normalized}")
        if path_allowed(normalized, closure_paths, root=root):
            errors.append(f"candidate patch must not touch evaluator closure: {normalized}")
        if not path_allowed(normalized, search_surface, root=root):
            errors.append(f"candidate patch touches path outside search_surface: {normalized}")
    return errors


def closure_digest_record(
    root: Path,
    direction: dict[str, Any],
    *,
    commit: str | None = None,
) -> dict[str, dict[str, str]]:
    return {
        group: {
            "before_sha256": digest_paths_at_commit(root, commit, paths) if commit else digest_paths(root, paths),
            "after_sha256": digest_paths_at_commit(root, commit, paths) if commit else digest_paths(root, paths),
        }
        for group, paths in evaluator_closure_paths(direction).items()
    }


def validate_trace_ref(
    value: object,
    *,
    source: str,
    expected_ref: str,
    expected_path: Path,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{source} must be a mapping")
        return
    validate_exact_fields(value, TRACE_REF_FIELDS, source=source, errors=errors)
    if value.get("ref") != expected_ref:
        errors.append(f"{source}.ref must be {expected_ref!r}")
    if not expected_path.is_file():
        errors.append(f"{expected_path}: missing file for {source}")
        return
    if value.get("sha256") != file_sha256(expected_path):
        errors.append(f"{source}.sha256 must match {expected_ref}")


def validate_trace_record(
    trace: dict[str, Any],
    *,
    candidate: dict[str, Any],
    direction: dict[str, Any],
    candidate_path: Path,
    patch_path: Path,
    errors: list[str],
) -> None:
    validate_exact_fields(trace, TRACE_FIELDS, source="trace", errors=errors)
    if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
        errors.append(f"trace.schema_version must be {TRACE_SCHEMA_VERSION}")
    for field in ("run_id", "candidate_id", "base_commit", "direction_digest", "created_at", "why", "next_hypothesis"):
        if not isinstance(trace.get(field), str) or not trace[field].strip():
            errors.append(f"trace.{field} must be a non-empty string")
    for field in ("run_id", "candidate_id", "base_commit", "direction_digest"):
        if trace.get(field) != candidate.get(field):
            errors.append(f"trace.{field} must match candidate.{field}")
    if trace.get("evidence_status") != "diagnostic_only":
        errors.append("trace.evidence_status must be diagnostic_only")
    if trace.get("candidate_metadata_ref") != "score.yml":
        errors.append("trace.candidate_metadata_ref must be 'score.yml'")

    touched_paths, _patch_errors = patch_touched_paths(patch_path)
    expected_changed_paths = sorted(touched_paths)
    if trace.get("changed_paths") != expected_changed_paths:
        errors.append("trace.changed_paths must match patch.diff touched paths")

    candidate_dir = candidate_path.parent
    validate_trace_ref(
        trace.get("patch_ref"),
        source="trace.patch_ref",
        expected_ref="patch.diff",
        expected_path=patch_path,
        errors=errors,
    )
    validate_trace_ref(
        trace.get("stdout_ref"),
        source="trace.stdout_ref",
        expected_ref="stdout.log",
        expected_path=candidate_dir / "stdout.log",
        errors=errors,
    )
    validate_trace_ref(
        trace.get("stderr_ref"),
        source="trace.stderr_ref",
        expected_ref="stderr.log",
        expected_path=candidate_dir / "stderr.log",
        errors=errors,
    )

    result = trace.get("result")
    stderr_text = (candidate_dir / "stderr.log").read_text(encoding="utf-8", errors="replace") if (candidate_dir / "stderr.log").is_file() else ""
    if not isinstance(result, dict):
        errors.append("trace.result must be a mapping")
    else:
        validate_exact_fields(result, TRACE_RESULT_FIELDS, source="trace.result", errors=errors)
        for field in ("verdict", "score", "exit_code", "case_results"):
            if result.get(field) != candidate.get(field):
                errors.append(f"trace.result.{field} must match candidate.{field}")
        if not isinstance(result.get("timed_out"), bool):
            errors.append("trace.result.timed_out must be a boolean")
        elif result.get("timed_out") != timed_out_from_logs(candidate.get("exit_code"), stderr_text):
            errors.append("trace.result.timed_out must match stdout/stderr timeout evidence")
    if not isinstance(trace.get("notes"), list):
        errors.append("trace.notes must be a list")


def validate_candidate(
    candidate: dict[str, Any],
    *,
    direction: dict[str, Any],
    root: Path,
    candidate_path: Path,
    patch_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    validate_exact_fields(candidate, CANDIDATE_FIELDS, source="candidate", errors=errors)
    if candidate.get("schema_version") != CANDIDATE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CANDIDATE_SCHEMA_VERSION}")
    for field in ("candidate_id", "run_id", "evaluator_command", "started_at", "finished_at", "verdict"):
        if not isinstance(candidate.get(field), str) or not candidate[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if isinstance(candidate.get("candidate_id"), str):
        validate_run_id(candidate["candidate_id"], source="candidate_id", errors=errors)
        if candidate["candidate_id"] != candidate_path.parent.name:
            errors.append("candidate_id must match the candidate directory name")
    if isinstance(candidate.get("run_id"), str):
        validate_run_id(candidate["run_id"], source="run_id", errors=errors)
        if candidate_path.parent.parent.name == "candidates":
            expected_run_id = candidate_path.parent.parent.parent.name
            if candidate["run_id"] != expected_run_id:
                errors.append("run_id must match the containing search run directory")
    base_commit = candidate.get("base_commit")
    if not isinstance(base_commit, str) or not FULL_COMMIT_RE.fullmatch(base_commit):
        errors.append("base_commit must be a full commit SHA")
        base_commit = None
    elif git_ref_commit(root, base_commit) != base_commit:
        errors.append("base_commit must resolve in the repository")
    direction_base = direction.get("base_ref")
    resolved_base = git_ref_commit(root, direction_base) if isinstance(direction_base, str) else None
    if resolved_base != base_commit:
        errors.append("base_commit must match direction base_ref")
    digest_commit = base_commit if isinstance(base_commit, str) else None
    if candidate.get("direction_digest") != digest_direction(direction):
        errors.append("direction_digest must match the direction file")
    expected_search_digest = (
        digest_paths_at_commit(root, digest_commit, string_list(direction.get("search_surface", [])))
        if digest_commit
        else digest_paths(root, string_list(direction.get("search_surface", [])))
    )
    if candidate.get("search_surface_digest_before") != expected_search_digest:
        errors.append("search_surface_digest_before must match direction search_surface bytes")
    if candidate.get("evaluator_command") != direction.get("evaluator", {}).get("command"):
        errors.append("evaluator_command must match direction evaluator.command")
    actual_evaluator_digest = evaluator_digest(root, direction, commit=digest_commit)
    if candidate.get("evaluator_digest") != actual_evaluator_digest:
        errors.append("evaluator_digest must match evaluator closure bytes")
    if candidate.get("verdict") not in VALID_VERDICTS:
        errors.append(f"verdict must be one of {sorted(VALID_VERDICTS)}")

    candidate_dir = candidate_path.parent
    patch_path = patch_path or candidate_dir / "patch.diff"
    stdout_path = candidate_dir / "stdout.log"
    stderr_path = candidate_dir / "stderr.log"
    trace_path = candidate_dir / "trace.yml"
    sidecar_errors: list[str] = []
    for label, source_path in {
        "score": candidate_path,
        "patch": patch_path,
        "stdout": stdout_path,
        "stderr": stderr_path,
        "trace": trace_path,
    }.items():
        sidecar_errors.extend(source_path_symlink_errors(root, source_path, label=label))
        sidecar_errors.extend(mutable_run_file_errors(source_path, label=f"candidate {label}"))
    if sidecar_errors:
        errors.extend(sidecar_errors)
        return errors
    if not patch_path.is_file():
        errors.append(f"{patch_path}: missing patch.diff")
    elif candidate.get("patch_sha256") != file_sha256(patch_path):
        errors.append("patch_sha256 must match patch.diff")
    if not stdout_path.is_file():
        errors.append(f"{stdout_path}: missing stdout.log")
    elif candidate.get("stdout_sha256") != file_sha256(stdout_path):
        errors.append("stdout_sha256 must match stdout.log")
    if not stderr_path.is_file():
        errors.append(f"{stderr_path}: missing stderr.log")
    elif candidate.get("stderr_sha256") != file_sha256(stderr_path):
        errors.append("stderr_sha256 must match stderr.log")
    if not trace_path.is_file():
        errors.append(f"{trace_path}: missing trace.yml")
    else:
        if candidate.get("trace_sha256") != file_sha256(trace_path):
            errors.append("trace_sha256 must match trace.yml")
        try:
            trace = load_yaml_mapping(trace_path)
        except StrategySearchError as exc:
            errors.append(str(exc))
        else:
            validate_trace_record(
                trace,
                candidate=candidate,
                direction=direction,
                candidate_path=candidate_path,
                patch_path=patch_path,
                errors=errors,
            )

    for field in (
        "direction_digest",
        "patch_sha256",
        "stdout_sha256",
        "stderr_sha256",
        "trace_sha256",
        "evaluator_digest",
        "search_surface_digest_before",
    ):
        if not is_sha256(candidate.get(field)):
            errors.append(f"{field} must be a SHA-256 hex digest")
    if not isinstance(candidate.get("exit_code"), int) or isinstance(candidate.get("exit_code"), bool):
        errors.append("exit_code must be an integer")
    stderr_text_for_diagnostics = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    if has_timeout_diagnostic(stderr_text_for_diagnostics) and candidate.get("exit_code") != 124:
        errors.append("timeout diagnostics require exit_code 124")
    score = candidate.get("score")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        errors.append("score must be a number")
        score = None
    if not isinstance(candidate.get("case_results"), list):
        errors.append("case_results must be a list")
    else:
        for index, case_result in enumerate(candidate["case_results"]):
            if not isinstance(case_result, dict):
                errors.append(f"case_results[{index}] must be a mapping")
                continue
            if not isinstance(case_result.get("case_id"), str) or not case_result["case_id"].strip():
                errors.append(f"case_results[{index}].case_id must be a non-empty string")
            if case_result.get("status") not in VALID_CASE_STATUSES:
                errors.append(f"case_results[{index}].status must be one of {sorted(VALID_CASE_STATUSES)}")

    if candidate.get("verdict") in {"pass", "fail"} and isinstance(candidate.get("exit_code"), int):
        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.is_file() else ""
        stderr_text = stderr_text_for_diagnostics
        if has_invalid_runner_diagnostic(stderr_text):
            errors.append("verdict pass/fail must not include strategy-search invalid diagnostics in stderr")
        timed_out = has_timeout_diagnostic(stderr_text)
        if timed_out:
            if candidate.get("verdict") == "pass":
                errors.append("timeout diagnostics must not validate as verdict pass")
            if score != 0.0 or candidate.get("case_results") != [{"case_id": "evaluator-output", "status": "fail"}]:
                errors.append("timeout diagnostics must use the canonical fail score and evaluator-output case")
        if candidate.get("verdict") in {"pass", "fail"} and not timed_out:
            output_errors = evaluator_output_errors(stdout_text, stderr_text)
            errors.extend(output_errors)
        expected_score = parse_score(stdout_text, stderr_text, candidate["exit_code"])
        expected_case_results = parse_case_results(stdout_text, stderr_text, candidate["exit_code"])
        if score is not None and expected_score is not None and score != expected_score:
            errors.append("score must match parsed stdout/stderr evaluator output")
        if expected_case_results and candidate.get("case_results") != expected_case_results:
            errors.append("case_results must match parsed stdout/stderr evaluator output")
        if score is not None and isinstance(candidate.get("case_results"), list):
            expected_verdict = candidate_verdict(
                direction,
                exit_code=candidate["exit_code"],
                score=score,
                case_results=candidate["case_results"],
            )
            if candidate.get("verdict") != expected_verdict:
                errors.append("verdict must match evaluator output and success policy")

    if candidate.get("verdict") == "pass":
        if candidate.get("exit_code") != 0:
            errors.append("verdict pass requires exit_code 0")
        success = direction.get("success") if isinstance(direction.get("success"), dict) else {}
        min_score = success.get("min_score")
        if isinstance(min_score, (int, float)) and not isinstance(min_score, bool) and score is not None and score < min_score:
            errors.append("verdict pass requires score >= success.min_score")
        max_regressions = success.get("max_regressions")
        if isinstance(max_regressions, int) and not isinstance(max_regressions, bool):
            failures = sum(
                1
                for item in candidate.get("case_results", [])
                if isinstance(item, dict) and item.get("status") == "fail"
            )
            if failures > max_regressions:
                errors.append("verdict pass exceeds success.max_regressions")

    closure = candidate.get("evaluator_closure")
    expected_closure = closure_digest_record(root, direction, commit=digest_commit)
    if not isinstance(closure, dict):
        errors.append("evaluator_closure must be a mapping")
    else:
        validate_exact_fields(closure, set(CLOSURE_GROUPS), source="evaluator_closure", errors=errors)
        for group in CLOSURE_GROUPS:
            item = closure.get(group)
            if not isinstance(item, dict):
                errors.append(f"evaluator_closure.{group} must be a mapping")
                continue
            validate_exact_fields(item, CLOSURE_DIGEST_FIELDS, source=f"evaluator_closure.{group}", errors=errors)
            before = item.get("before_sha256")
            after = item.get("after_sha256")
            if not is_sha256(before) or not is_sha256(after):
                errors.append(f"evaluator_closure.{group} before/after values must be SHA-256 digests")
                continue
            if before != after:
                errors.append(f"evaluator_closure.{group} changed during candidate evaluation")
            if before != expected_closure[group]["before_sha256"]:
                errors.append(f"evaluator_closure.{group} digest must match direction evaluator closure")

    errors.extend(patch_boundary_errors(root, direction, patch_path))
    return errors


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return slug or "strategy-search"


def write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def write_yaml_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp_path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    os.replace(tmp_path, path)


def mutable_run_file_errors(path: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    if path.is_symlink():
        errors.append(f"{label} must not be a symlink: {path}")
        return errors
    if path.exists() and path.is_file():
        try:
            if path.stat().st_nlink > 1:
                errors.append(f"{label} must not be hard-linked: {path}")
        except OSError as exc:
            errors.append(f"{label} cannot be inspected: {exc}")
    return errors


def patch_source_errors(root: Path, source_patch: Path, *, label: str = "patch source") -> list[str]:
    errors: list[str] = []
    if ".." in source_patch.parts:
        errors.append(f"{label} path must not contain '..': {source_patch}")
        return errors
    try:
        source_patch.resolve(strict=False).relative_to(root.resolve())
    except (OSError, ValueError):
        errors.append(f"{label} must be inside repository root: {source_patch}")
        return errors
    if path_component_has_symlink(root, source_patch):
        errors.append(f"{label} path must not contain symlinks: {source_patch}")
    errors.extend(mutable_run_file_errors(source_patch, label=label))
    return errors


def run_git(root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and completed.returncode != 0:
        raise StrategySearchError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed


def run_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def run_store_parent_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for parent in (root / ".harness", root / SEARCH_RUNS_PREFIX):
        if parent.is_symlink():
            errors.append(f"run-store parent must not be a symlink: {parent}")
    return errors


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except (OSError, ValueError):
        return False
    return True


def path_component_has_symlink(root: Path, path: Path) -> bool:
    root_abs = root.resolve()
    path_abs = Path(os.path.abspath(os.path.normpath(path)))
    try:
        path_abs.resolve(strict=False).relative_to(root_abs)
    except (OSError, ValueError):
        return path_abs.is_symlink()
    current = path_abs
    while True:
        try:
            current.resolve(strict=False).relative_to(root_abs)
        except (OSError, ValueError):
            break
        if current.is_symlink():
            return True
        if current == current.parent:
            break
        current = current.parent
    return False


def filesystem_digest(
    root: Path,
    *,
    exclude_roots: list[Path] | None = None,
    skip_git: bool = True,
) -> str:
    exclude_roots = [path.resolve() for path in (exclude_roots or [])]
    root = root if root.is_symlink() else root.resolve()
    digest = hashlib.sha256()
    if not root.exists() and not root.is_symlink():
        digest.update(b"missing\0.\0")
        return digest.hexdigest()
    if root.is_symlink():
        digest.update(f"symlink\0{oct(root.lstat().st_mode & 0o777)}\0.\0{os.readlink(root)}\0".encode("utf-8"))
        return digest.hexdigest()
    if root.is_file():
        digest.update(f"file\0{root.stat().st_mode & 0o777:o}\0.\0".encode("utf-8"))
        digest.update(root.read_bytes())
        digest.update(b"\0")
        return digest.hexdigest()
    digest.update(f"dir\0{root.stat().st_mode & 0o777:o}\0.\0".encode("utf-8"))
    for item in sorted(root.rglob("*")):
        resolved = item.resolve() if not item.is_symlink() else item.parent.resolve() / item.name
        if any(is_relative_to(resolved, excluded) or resolved == excluded for excluded in exclude_roots):
            continue
        if skip_git and ".git" in item.relative_to(root).parts:
            continue
        rel_path = item.relative_to(root).as_posix()
        if item.is_dir() and not item.is_symlink():
            mode = item.stat().st_mode & 0o777
            digest.update(f"dir\0{mode:o}\0{rel_path}\0".encode("utf-8"))
            continue
        if item.is_symlink():
            mode = item.lstat().st_mode & 0o777
            digest.update(f"symlink\0{mode:o}\0{rel_path}\0{os.readlink(item)}\0".encode("utf-8"))
            continue
        if item.is_file():
            mode = item.stat().st_mode & 0o777
            digest.update(f"file\0{mode:o}\0{rel_path}\0".encode("utf-8"))
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


EXTERNAL_GIT_SNAPSHOT_PREFIX = "__git_external__/"


def gitfile_target(root: Path) -> Path | None:
    git_file = root / ".git"
    if not git_file.is_file() or git_file.is_symlink():
        return None
    try:
        text = git_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if not first_line.startswith("gitdir:"):
        return None
    raw_path = first_line.split(":", 1)[1].strip()
    if not raw_path:
        return None
    gitdir = Path(raw_path)
    if not gitdir.is_absolute():
        gitdir = root / gitdir
    return gitdir.resolve()


def commondir_target(gitdir: Path) -> Path | None:
    commondir = gitdir / "commondir"
    if not commondir.is_file():
        return None
    try:
        raw_path = commondir.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    if not raw_path:
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = gitdir / path
    return path.resolve()


def source_git_external_roots(root: Path) -> list[tuple[str, Path]]:
    git_root = root / ".git"
    candidates: list[tuple[str, Path]] = []
    if git_root.is_symlink():
        candidates.append(("git-symlink-target", git_root.resolve()))
    gitdir = gitfile_target(root)
    if gitdir is not None:
        candidates.append(("gitfile-target", gitdir))
    if git_root.is_dir() and not git_root.is_symlink():
        candidates.append(("gitdir", git_root.resolve()))

    roots: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for label, path in candidates:
        if path not in seen:
            roots.append((label, path))
            seen.add(path)
        common = commondir_target(path)
        if common is not None and common not in seen:
            roots.append((f"{label}-common", common))
            seen.add(common)
    return roots


def source_git_metadata_digest(root: Path) -> str:
    git_root = root / ".git"
    if not git_root.exists() and not git_root.is_symlink():
        return "missing"
    digest = hashlib.sha256()
    if git_root.is_symlink():
        digest.update(f"symlink\0.git\0{git_root.lstat().st_mode & 0o777:o}\0{os.readlink(git_root)}\0".encode("utf-8"))
    elif git_root.is_file():
        digest.update(f"file\0.git\0{git_root.stat().st_mode & 0o777:o}\0".encode("utf-8"))
        digest.update(git_root.read_bytes())
        digest.update(b"\0")
    else:
        digest.update(filesystem_digest(git_root, skip_git=False).encode("utf-8"))
        digest.update(b"\0")
    for label, path in source_git_external_roots(root):
        digest.update(f"external-git\0{label}\0{path}\0".encode("utf-8"))
        digest.update(filesystem_digest(path, skip_git=False).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def add_external_git_snapshots(
    snapshot: dict[str, tuple[str, int, bytes | str | None]],
    root: Path,
) -> None:
    for index, (label, path) in enumerate(source_git_external_roots(root)):
        prefix = f"{EXTERNAL_GIT_SNAPSHOT_PREFIX}{index}"
        snapshot[f"{prefix}/label"] = ("git_external_label", 0, label)
        snapshot[f"{prefix}/path"] = ("git_external_path", 0, str(path))
        for key, value in capture_filesystem_snapshot(path, skip_git=False).items():
            snapshot[f"{prefix}/snapshot/{key}"] = value


def restore_external_git_snapshots(snapshot: dict[str, tuple[str, int, bytes | str | None]]) -> None:
    prefixes = sorted(
        key.rsplit("/", 1)[0]
        for key in snapshot
        if key.startswith(EXTERNAL_GIT_SNAPSHOT_PREFIX) and key.endswith("/path")
    )
    for prefix in prefixes:
        path_record = snapshot.get(f"{prefix}/path")
        if path_record is None or not isinstance(path_record[2], str):
            continue
        snapshot_prefix = f"{prefix}/snapshot/"
        target_snapshot = {
            key[len(snapshot_prefix) :]: value
            for key, value in snapshot.items()
            if key.startswith(snapshot_prefix)
        }
        restore_filesystem_snapshot(Path(path_record[2]), target_snapshot, skip_git=False)


def capture_git_metadata_snapshot(root: Path) -> dict[str, tuple[str, int, bytes | str | None]]:
    git_root = root / ".git"
    snapshot: dict[str, tuple[str, int, bytes | str | None]]
    if git_root.is_symlink():
        snapshot = {"": ("symlink", git_root.lstat().st_mode & 0o777, os.readlink(git_root))}
    elif git_root.is_file():
        snapshot = {"": ("file", git_root.stat().st_mode & 0o777, git_root.read_bytes())}
    elif git_root.is_dir():
        snapshot = capture_filesystem_snapshot(git_root, skip_git=False)
        snapshot[""] = ("dir", git_root.stat().st_mode & 0o777, None)
    else:
        snapshot = {"": ("missing", 0, None)}
    add_external_git_snapshots(snapshot, root)
    return snapshot


def restore_git_metadata_snapshot(
    root: Path,
    snapshot: dict[str, tuple[str, int, bytes | str | None]],
) -> None:
    git_root = root / ".git"
    if not snapshot:
        return
    root_record = snapshot.get("")
    if root_record is None:
        return
    kind, mode, payload = root_record
    if kind == "missing":
        if git_root.is_dir() and not git_root.is_symlink():
            shutil.rmtree(git_root)
        elif git_root.exists() or git_root.is_symlink():
            git_root.unlink()
        restore_external_git_snapshots(snapshot)
        return
    if git_root.exists() or git_root.is_symlink():
        if git_root.is_dir() and not git_root.is_symlink():
            shutil.rmtree(git_root)
        else:
            git_root.unlink()
    if kind == "symlink":
        git_root.symlink_to(str(payload))
        restore_external_git_snapshots(snapshot)
        return
    if kind == "file":
        git_root.write_bytes(payload if isinstance(payload, bytes) else str(payload).encode("utf-8"))
        git_root.chmod(mode)
        restore_external_git_snapshots(snapshot)
        return
    git_root.mkdir(parents=True, exist_ok=True)
    git_root.chmod(mode)
    restore_filesystem_snapshot(
        git_root,
        {key: value for key, value in snapshot.items() if not key.startswith(EXTERNAL_GIT_SNAPSHOT_PREFIX)},
        skip_git=False,
    )
    restore_external_git_snapshots(snapshot)


def capture_filesystem_snapshot(
    root: Path,
    *,
    exclude_roots: list[Path] | None = None,
    skip_git: bool = True,
) -> dict[str, tuple[str, int, bytes | str | None]]:
    exclude_roots = [path.resolve() for path in (exclude_roots or [])]
    root = root if root.is_symlink() else root.resolve()
    snapshot: dict[str, tuple[str, int, bytes | str | None]] = {}
    if not root.exists() and not root.is_symlink():
        snapshot[""] = ("missing", 0, None)
        return snapshot
    if root.is_symlink():
        snapshot[""] = ("symlink", root.lstat().st_mode & 0o777, os.readlink(root))
        return snapshot
    if root.is_file():
        snapshot[""] = ("file", root.stat().st_mode & 0o777, root.read_bytes())
        return snapshot
    snapshot[""] = ("dir", root.stat().st_mode & 0o777, None)
    for item in sorted(root.rglob("*")):
        resolved = item.resolve() if not item.is_symlink() else item.parent.resolve() / item.name
        if any(is_relative_to(resolved, excluded) or resolved == excluded for excluded in exclude_roots):
            continue
        if skip_git and ".git" in item.relative_to(root).parts:
            continue
        rel_path = item.relative_to(root).as_posix()
        if item.is_dir() and not item.is_symlink():
            snapshot[rel_path] = ("dir", item.stat().st_mode & 0o777, None)
            continue
        if item.is_symlink():
            snapshot[rel_path] = ("symlink", item.lstat().st_mode & 0o777, os.readlink(item))
        elif item.is_file():
            snapshot[rel_path] = ("file", item.stat().st_mode & 0o777, item.read_bytes())
    return snapshot


def restore_filesystem_snapshot(
    root: Path,
    snapshot: dict[str, tuple[str, int, bytes | str | None]],
    *,
    exclude_roots: list[Path] | None = None,
    skip_git: bool = True,
) -> None:
    exclude_roots = [path.resolve() for path in (exclude_roots or [])]
    root = root if root.is_absolute() else Path.cwd() / root
    root_record = snapshot.get("", ("dir", 0o777, None))
    root_kind, root_mode, root_payload = root_record
    if root_kind == "missing":
        if root.is_dir() and not root.is_symlink():
            shutil.rmtree(root)
        elif root.exists() or root.is_symlink():
            root.unlink()
        return
    if root.exists() or root.is_symlink():
        if root_kind == "dir" and not (root.is_dir() and not root.is_symlink()):
            if root.is_dir() and not root.is_symlink():
                shutil.rmtree(root)
            else:
                root.unlink()
        elif root_kind in {"file", "symlink"}:
            if root.is_dir() and not root.is_symlink():
                shutil.rmtree(root)
            else:
                root.unlink()
    if root_kind == "symlink":
        root.parent.mkdir(parents=True, exist_ok=True)
        root.symlink_to(str(root_payload))
        return
    if root_kind == "file":
        root.parent.mkdir(parents=True, exist_ok=True)
        root.write_bytes(root_payload if isinstance(root_payload, bytes) else str(root_payload).encode("utf-8"))
        root.chmod(root_mode)
        return
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(root_mode)
    for item in sorted(root.rglob("*"), reverse=True):
        resolved = item.resolve() if not item.is_symlink() else item.parent.resolve() / item.name
        if any(is_relative_to(resolved, excluded) or resolved == excluded for excluded in exclude_roots):
            continue
        if skip_git and ".git" in item.relative_to(root).parts:
            continue
        rel_path = item.relative_to(root).as_posix()
        if item.is_dir() and not item.is_symlink():
            if rel_path not in snapshot:
                try:
                    item.rmdir()
                except OSError:
                    pass
            continue
        if rel_path not in snapshot:
            item.unlink(missing_ok=True)
    for rel_path, (kind, mode, payload) in snapshot.items():
        if not rel_path:
            continue
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if kind == "dir":
            if path.exists() or path.is_symlink():
                if not (path.is_dir() and not path.is_symlink()):
                    path.unlink()
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(mode)
            continue
        if path.exists() or path.is_symlink():
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        if kind == "symlink":
            path.symlink_to(str(payload))
        else:
            path.write_bytes(payload if isinstance(payload, bytes) else payload.encode("utf-8"))
            path.chmod(mode)


def symlink_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for item in sorted(root.rglob("*")):
        if ".git" in item.relative_to(root).parts:
            continue
        if item.is_symlink():
            paths.append(item.relative_to(root).as_posix())
    return paths


def next_candidate_id(run_dir: Path) -> str:
    candidates_dir = run_dir / "candidates"
    if candidates_dir.is_symlink() or not candidates_dir.is_dir():
        return "cand-001"
    max_index = 0
    for path in candidates_dir.iterdir():
        match = re.fullmatch(r"cand-(\d+)", path.name)
        if match:
            max_index = max(max_index, int(match.group(1)))
    return f"cand-{max_index + 1:03d}"


def validate_run_id(value: str, *, source: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        errors.append(f"{source} must contain only letters, digits, '.', '_', or '-' and must not be empty")
        return None
    return value


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    ledger_errors = mutable_run_file_errors(path, label="JSONL ledger")
    if ledger_errors:
        raise StrategySearchError("; ".join(ledger_errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ledger_errors = mutable_run_file_errors(path, label="JSONL ledger")
    if ledger_errors:
        raise StrategySearchError("; ".join(ledger_errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records)
    path.write_text(content, encoding="utf-8")


def export_commit_tree(root: Path, commit: str, target: Path) -> None:
    result = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise StrategySearchError(result.stderr.decode("utf-8", errors="replace").strip())
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        archive.extractall(target)


def init_workspace_repo(workspace: Path) -> None:
    run_git(workspace, ["init"])
    run_git(workspace, ["config", "user.name", "Strategy Search"])
    run_git(workspace, ["config", "user.email", "strategy-search@example.invalid"])
    run_git(workspace, ["add", "-A"])
    run_git(workspace, ["commit", "--allow-empty", "-m", "strategy-search base"])


def status_changed_paths(workspace: Path) -> list[str]:
    completed = run_git(workspace, ["status", "--porcelain=v1", "-z", "--untracked-files=all"], check=False)
    if completed.returncode != 0:
        return []
    entries = [entry for entry in completed.stdout.split("\0") if entry]
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        status = entry[:2]
        if len(entry) > 3:
            paths.append(entry[3:])
        index += 2 if status and any(letter in status for letter in ("R", "C")) else 1
    return sorted(dict.fromkeys(paths))


def workspace_boundary_errors(workspace: Path, direction: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    search_surface = normalized_direction_specs(workspace, direction, string_list(direction.get("search_surface", [])))
    closure_paths = normalized_direction_specs(workspace, direction, evaluator_combined_closure(direction))
    for changed_path in status_changed_paths(workspace):
        normalized = repo_relative_path(changed_path, source=f"candidate workspace path {changed_path!r}", errors=errors)
        if normalized is None:
            continue
        if normalized.startswith("archive/v2/"):
            errors.append(f"candidate workspace must not write archive/v2: {normalized}")
        if path_allowed(normalized, closure_paths, root=workspace):
            errors.append(f"candidate workspace must not dirty evaluator closure: {normalized}")
        if not path_allowed(normalized, search_surface, root=workspace):
            errors.append(f"candidate workspace dirty path outside search_surface: {normalized}")
    return errors


SCORE_RE = re.compile(r"(?im)^\s*score\s*[:=]\s*(\d+(?:\.\d+)?)\s*$")
CASE_RE = re.compile(r"(?im)^\s*case\s*[:=]\s*([A-Za-z0-9._-]+)\s*[:= ]\s*(pass|fail|skip|xfail)\s*$")
INVALID_RUNNER_MARKERS = (
    "strategy-search invalid candidate:",
    "candidate workspace must not",
    "candidate workspace changed after patch application",
    "candidate evaluation dirtied the source repository outside the run store",
    "candidate workspace dirty path outside search_surface",
    "evaluator_closure.",
)


def parse_score(stdout: str, stderr: str, exit_code: int) -> float | None:
    matches = list(SCORE_RE.finditer(f"{stdout}\n{stderr}"))
    if matches:
        return float(matches[0].group(1))
    return None


def parse_case_results(stdout: str, stderr: str, exit_code: int) -> list[dict[str, str]]:
    text = f"{stdout}\n{stderr}"
    return [{"case_id": match.group(1), "status": match.group(2)} for match in CASE_RE.finditer(text)]


def evaluator_output_errors(stdout: str, stderr: str) -> list[str]:
    errors: list[str] = []
    score_matches = list(SCORE_RE.finditer(f"{stdout}\n{stderr}"))
    if not score_matches:
        errors.append("evaluator output must include an explicit score line")
    elif len(score_matches) != 1:
        errors.append("evaluator output must include exactly one explicit score line")
    if not parse_case_results(stdout, stderr, 0):
        errors.append("evaluator output must include at least one explicit case line")
    case_ids: set[str] = set()
    duplicate_case_ids: set[str] = set()
    for case_result in parse_case_results(stdout, stderr, 0):
        case_id = case_result["case_id"]
        if case_id in case_ids:
            duplicate_case_ids.add(case_id)
        case_ids.add(case_id)
    for case_id in sorted(duplicate_case_ids):
        errors.append(f"evaluator output must not include duplicate case line: {case_id}")
    return errors


def has_timeout_diagnostic(stderr: str) -> bool:
    return "strategy-search evaluator timed out after" in stderr


def timed_out_from_logs(exit_code: object, stderr: str) -> bool:
    return has_timeout_diagnostic(stderr)


def has_invalid_runner_diagnostic(stderr: str) -> bool:
    return any(marker in stderr for marker in INVALID_RUNNER_MARKERS)


def candidate_verdict(direction: dict[str, Any], *, exit_code: int, score: float, case_results: list[dict[str, str]]) -> str:
    if exit_code != 0:
        return "fail"
    success = direction.get("success") if isinstance(direction.get("success"), dict) else {}
    min_score = success.get("min_score")
    if isinstance(min_score, (int, float)) and not isinstance(min_score, bool) and score < min_score:
        return "fail"
    max_regressions = success.get("max_regressions")
    if isinstance(max_regressions, int) and not isinstance(max_regressions, bool):
        failures = sum(1 for item in case_results if item.get("status") == "fail")
        if failures > max_regressions:
            return "fail"
    return "pass"


def default_next_hypothesis(verdict: str) -> str:
    if verdict == "pass":
        return "Compare this candidate against the next search attempt or prepare it for v2 adoption."
    if verdict == "invalid":
        return "Inspect boundary failures, then propose a candidate that stays inside the declared search surface."
    return "Inspect failed evaluator cases and propose a narrower candidate for the next attempt."


def candidate_trace_record(
    *,
    direction: dict[str, Any],
    run_id: str,
    candidate_id: str,
    base_commit: str,
    patch_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    verdict: str,
    score: float,
    exit_code: int,
    case_results: list[dict[str, str]],
    timed_out: bool,
    why: str,
    next_hypothesis: str,
    created_at: str,
) -> dict[str, Any]:
    changed_paths, _errors = patch_touched_paths(patch_path)
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "base_commit": base_commit,
        "direction_digest": digest_direction(direction),
        "created_at": created_at,
        "evidence_status": "diagnostic_only",
        "why": why,
        "changed_paths": sorted(changed_paths),
        "result": {
            "verdict": verdict,
            "score": score,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "case_results": case_results,
        },
        "patch_ref": {"ref": "patch.diff", "sha256": file_sha256(patch_path)},
        "stdout_ref": {"ref": "stdout.log", "sha256": file_sha256(stdout_path)},
        "stderr_ref": {"ref": "stderr.log", "sha256": file_sha256(stderr_path)},
        "candidate_metadata_ref": "score.yml",
        "next_hypothesis": next_hypothesis,
        "notes": [
            "This trace is diagnostic strategy-search output.",
            "It is not archive/v2 evidence; adopt by applying the patch in a content commit.",
        ],
    }


def write_candidate_trace(
    candidate_dir: Path,
    trace: dict[str, Any],
    *,
    keep_worktree: Path | None = None,
    workspace_errors: list[str] | None = None,
    apply_failed: bool = False,
) -> Path:
    trace_path = candidate_dir / "trace.yml"
    write_yaml(trace_path, trace)
    (candidate_dir / "trace.md").write_text(
        candidate_trace_markdown_text(
            trace,
            keep_worktree=keep_worktree,
            workspace_errors=workspace_errors,
            apply_failed=apply_failed,
        ),
        encoding="utf-8",
    )
    return trace_path


def candidate_trace_markdown_text(
    trace: dict[str, Any],
    *,
    keep_worktree: Path | None = None,
    workspace_errors: list[str] | None = None,
    apply_failed: bool = False,
) -> str:
    result = trace["result"]
    trace_lines = [
        "# Candidate Trace",
        "",
        f"candidate_id: {trace['candidate_id']}",
        f"why: {trace['why']}",
        f"verdict: {result['verdict']}",
        f"score: {result['score']}",
        f"exit_code: {result['exit_code']}",
        f"next_hypothesis: {trace['next_hypothesis']}",
        "",
        "Changed paths:",
        *[f"- {path}" for path in trace["changed_paths"]],
        "",
        "Raw evaluator output refs:",
        f"- stdout: {trace['stdout_ref']['ref']} ({trace['stdout_ref']['sha256']})",
        f"- stderr: {trace['stderr_ref']['ref']} ({trace['stderr_ref']['sha256']})",
        "",
        "Diagnostic only: not archive/v2 evidence; adopt by applying the patch in a content commit.",
    ]
    if keep_worktree is not None:
        trace_lines.extend(["", f"worktree: {keep_worktree}"])
    if workspace_errors:
        trace_lines.extend(["", "Invalid workspace effects:", *[f"- {error}" for error in workspace_errors]])
    if apply_failed:
        trace_lines.extend(["", "Patch apply failed."])
    return "\n".join(trace_lines) + "\n"


def evaluator_env(workspace: Path, *, source_root: Path | None = None) -> dict[str, str]:
    safe_keys = {
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USER",
    }
    env = {key: value for key, value in os.environ.items() if key in safe_keys}
    blocked_path_roots = [
        Path(os.path.abspath(os.path.normpath(workspace))),
        workspace.resolve(),
    ]
    if source_root is not None:
        blocked_path_roots.extend(
            [
                Path(os.path.abspath(os.path.normpath(source_root))),
                source_root.resolve(),
            ]
        )
    path_entries: list[str] = []
    for raw_entry in os.environ.get("PATH", os.defpath).split(os.pathsep):
        if not raw_entry:
            continue
        entry = Path(raw_entry)
        if not entry.is_absolute():
            continue
        normalized_entry = Path(os.path.abspath(os.path.normpath(entry)))
        if any(is_relative_to(normalized_entry, blocked_root) for blocked_root in blocked_path_roots):
            continue
        try:
            if any(entry.resolve().is_relative_to(blocked_root) for blocked_root in blocked_path_roots):
                continue
        except OSError:
            pass
        path_entries.append(raw_entry)
    env["PATH"] = os.pathsep.join(path_entries or [entry for entry in os.defpath.split(os.pathsep) if entry])
    env["PWD"] = str(workspace)
    env["STRATEGY_SEARCH_WORKSPACE"] = str(workspace)
    return env


def terminate_process_group(pid: int, sig: int = signal.SIGTERM) -> None:
    try:
        os.killpg(pid, sig)
    except OSError:
        pass


def cleanup_process_group(pid: int) -> None:
    terminate_process_group(pid, signal.SIGTERM)
    time.sleep(0.1)
    terminate_process_group(pid, signal.SIGKILL)
    time.sleep(0.05)


def settle_after_evaluator_exit() -> None:
    time.sleep(SIDE_EFFECT_SETTLE_SECONDS)


def run_evaluator_process(
    argv: list[str],
    *,
    cwd: Path,
    source_root: Path | None = None,
    timeout_seconds: int,
) -> tuple[str, str, int, bool]:
    def decode_stream(data: bytes | None) -> str:
        return (data or b"").decode("utf-8", errors="replace")

    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=evaluator_env(cwd, source_root=source_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        return "", f"strategy-search evaluator failed to start: {exc}\n", 127, False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        cleanup_process_group(process.pid)
        return decode_stream(stdout), decode_stream(stderr), process.returncode, False
    except subprocess.TimeoutExpired:
        terminate_process_group(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        stderr_text = decode_stream(stderr) + f"\nstrategy-search evaluator timed out after {timeout_seconds}s\n"
        return decode_stream(stdout), stderr_text, 124, True


def closure_digest_record_for_workspace(
    source_root: Path,
    workspace: Path,
    direction: dict[str, Any],
    *,
    base_commit: str,
) -> dict[str, dict[str, str]]:
    return {
        group: {
            "before_sha256": digest_paths_at_commit(source_root, base_commit, paths),
            "after_sha256": digest_paths(workspace, paths),
        }
        for group, paths in evaluator_closure_paths(direction).items()
    }


def candidate_record(
    *,
    root: Path,
    direction: dict[str, Any],
    candidate_id: str,
    run_id: str,
    base_commit: str,
    patch_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    trace_path: Path,
    started_at: str,
    finished_at: str,
    exit_code: int,
    score: float,
    case_results: list[dict[str, str]],
    verdict: str,
    closure: dict[str, dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "run_id": run_id,
        "base_commit": base_commit,
        "direction_digest": digest_direction(direction),
        "search_surface_digest_before": digest_paths_at_commit(
            root,
            base_commit,
            string_list(direction.get("search_surface", [])),
        ),
        "patch_sha256": file_sha256(patch_path),
        "evaluator_command": direction["evaluator"]["command"],
        "evaluator_digest": evaluator_digest(root, direction, commit=base_commit),
        "evaluator_closure": closure,
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": exit_code,
        "score": score,
        "case_results": case_results,
        "stdout_sha256": file_sha256(stdout_path),
        "stderr_sha256": file_sha256(stderr_path),
        "trace_sha256": file_sha256(trace_path),
        "verdict": verdict,
    }


def validate_direction_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = Path(args.direction)
    direction_path = root / path if not path.is_absolute() else path
    try:
        direction = load_yaml_mapping(direction_path)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID direction: {direction_path}")
    print(f"direction_digest: {digest_direction(direction)}")
    return 0


def validate_candidate_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    direction_path = Path(args.direction)
    direction_path = root / direction_path if not direction_path.is_absolute() else direction_path
    candidate_path = Path(args.candidate)
    candidate_path = root / candidate_path if not candidate_path.is_absolute() else candidate_path
    expected_patch_path = candidate_path.parent / "patch.diff"
    patch_path = Path(args.patch) if args.patch else None
    if patch_path is not None:
        patch_path = root / patch_path if not patch_path.is_absolute() else patch_path
        patch_arg_path = Path(os.path.abspath(os.path.normpath(patch_path)))
        expected_arg_path = Path(os.path.abspath(os.path.normpath(expected_patch_path)))
        if patch_arg_path != expected_arg_path:
            print("ERROR: --patch must match the candidate directory patch.diff", file=sys.stderr)
            return 1
    preflight_errors: list[str] = []
    for label, source_path in {
        "score": candidate_path,
        "patch": expected_patch_path,
        "stdout": candidate_path.parent / "stdout.log",
        "stderr": candidate_path.parent / "stderr.log",
        "trace": candidate_path.parent / "trace.yml",
    }.items():
        preflight_errors.extend(source_path_symlink_errors(root, source_path, label=label))
        preflight_errors.extend(mutable_run_file_errors(source_path, label=f"candidate {label}"))
    if preflight_errors:
        for error in preflight_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    try:
        direction = load_yaml_mapping(direction_path)
        candidate = load_yaml_mapping(candidate_path)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    errors.extend(
        validate_candidate(
            candidate,
            direction=direction,
            root=root,
            candidate_path=candidate_path,
            patch_path=patch_path,
        )
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID candidate metadata: {candidate_path}")
    return 0


def start_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    direction_path = run_path(root, args.direction)
    try:
        direction = load_yaml_mapping(direction_path)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    run_id = args.run_id or f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{safe_slug(direction.get('direction_id', 'run'))}"
    if validate_run_id(run_id, source="run_id", errors=errors) is None:
        run_id = "invalid"
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    run_dir = root / ".harness" / "search-runs" / run_id
    parent_errors = run_store_parent_errors(root)
    if parent_errors:
        for error in parent_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if run_dir.exists() and not args.overwrite:
        print(f"ERROR: run already exists: {run_dir}", file=sys.stderr)
        return 1
    if run_dir.exists() and args.overwrite:
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "candidates").mkdir(exist_ok=True)
    (run_dir / "proposals").mkdir(exist_ok=True)
    write_yaml(run_dir / "direction.yml", direction)
    write_yaml(
        run_dir / "run.yml",
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": run_id,
            "direction_path": str(direction_path.relative_to(root)) if direction_path.is_relative_to(root) else str(direction_path),
            "direction_digest": digest_direction(direction),
            "base_commit": direction["base_ref"],
            "created_at": utc_now(),
        },
    )
    (run_dir / "scores.jsonl").touch(exist_ok=True)
    (run_dir / "proposals.jsonl").touch(exist_ok=True)
    print(f"RUN {run_id}")
    print(f"run_dir: {run_dir}")
    return 0


def load_run(root: Path, run_arg: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(os.path.abspath(os.path.normpath(run_path(root, run_arg))))
    pre_errors: list[str] = []
    expected_parent = Path(os.path.abspath(os.path.normpath(root / SEARCH_RUNS_PREFIX)))
    pre_errors.extend(run_store_parent_errors(root))
    if run_dir.parent != expected_parent:
        pre_errors.append(
            "run directory must be the canonical diagnostic path "
            f"{SEARCH_RUNS_PREFIX}<run-id>"
        )
    if path_component_has_symlink(root, run_dir):
        pre_errors.append("run directory path must not contain symlinks")
    for metadata_name in ("run.yml", "direction.yml"):
        metadata_path = run_dir / metadata_name
        if path_component_has_symlink(root, metadata_path):
            pre_errors.append(f"run metadata file must not be a symlink: {metadata_name}")
        else:
            for error in mutable_run_file_errors(metadata_path, label=f"run metadata file {metadata_name}"):
                pre_errors.append(error)
    for ledger_name in ("scores.jsonl", "proposals.jsonl"):
        ledger_path = run_dir / ledger_name
        for error in mutable_run_file_errors(ledger_path, label=f"run ledger file {ledger_name}"):
            pre_errors.append(error)
    if pre_errors:
        raise StrategySearchError("; ".join(pre_errors))
    run_meta = load_yaml_mapping(run_dir / "run.yml")
    direction = load_yaml_mapping(run_dir / "direction.yml")
    errors: list[str] = []
    if run_meta.get("schema_version") != RUN_SCHEMA_VERSION:
        errors.append(f"run.yml schema_version must be {RUN_SCHEMA_VERSION}")
    if run_meta.get("direction_digest") != digest_direction(direction):
        errors.append("run.yml direction_digest does not match direction.yml")
    if run_meta.get("base_commit") != direction.get("base_ref"):
        errors.append("run.yml base_commit does not match direction base_ref")
    if not isinstance(run_meta.get("run_id"), str) or not run_meta["run_id"].strip():
        errors.append("run.yml run_id must be a non-empty string")
    elif run_meta["run_id"] != run_dir.name:
        errors.append("run.yml run_id must match the search run directory name")
    else:
        expected_run_dir = Path(os.path.abspath(os.path.normpath(root / SEARCH_RUNS_PREFIX / run_meta["run_id"])))
        if run_dir != expected_run_dir:
            errors.append(
                "run directory must be the canonical diagnostic path "
                f"{SEARCH_RUNS_PREFIX}<run-id>"
            )
    if errors:
        raise StrategySearchError("; ".join(errors))
    return run_dir, run_meta, direction


def run_relative_ref(run_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(run_dir.resolve()).as_posix()


def candidate_entries_for_context(root: Path, run_dir: Path, direction: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for candidate_dir in immediate_candidate_dirs(root, run_dir):
        if candidate_dir.is_symlink() or not candidate_dir.is_dir():
            continue
        if candidate_source_errors(root, candidate_dir):
            continue
        score_path = candidate_dir / "score.yml"
        try:
            record = load_yaml_mapping(score_path)
        except StrategySearchError:
            continue
        validation_errors = validate_candidate(record, direction=direction, root=root, candidate_path=score_path)
        if validation_errors or record.get("verdict") == "invalid":
            continue
        entries.append(
            {
                "candidate_id": record.get("candidate_id"),
                "verdict": record.get("verdict"),
                "score": record.get("score"),
                "validation_error_count": 0,
            }
        )
        trace_path = score_path.parent / "trace.yml"
        if path_component_has_symlink(root, trace_path) or mutable_run_file_errors(
            trace_path,
            label="prior candidate trace",
        ):
            continue
        if trace_path.is_file():
            try:
                trace = load_yaml_mapping(trace_path)
            except StrategySearchError:
                trace = {}
            if isinstance(trace, dict):
                entries[-1]["trace_summary"] = {
                    "why": sanitize_public_value(trace.get("why"), direction),
                    "changed_paths": sanitize_public_value(trace.get("changed_paths"), direction),
                    "next_hypothesis": sanitize_public_value(trace.get("next_hypothesis"), direction),
                    "evidence_status": sanitize_public_value(trace.get("evidence_status"), direction),
                }
    return entries


def proposer_public_context(root: Path, run_dir: Path, run_meta: dict[str, Any], direction: dict[str, Any]) -> dict[str, Any]:
    refs = {
        "summary_ref": None,
        "search_set_ref": None,
    }
    return {
        "schema_version": PROPOSAL_CONTEXT_SCHEMA_VERSION,
        "run_id": run_meta.get("run_id", run_dir.name),
        "base_commit": direction["base_ref"],
        "direction_digest": digest_direction(direction),
        "evidence_status": "diagnostic_only",
        "direction": {
            "direction_id": sanitize_public_value(direction.get("direction_id"), direction),
            "objective": sanitize_public_value(direction.get("objective"), direction),
            "search_surface": string_list(direction.get("search_surface", [])),
            "success": direction.get("success"),
            "notes": sanitize_public_value(direction.get("notes"), direction),
        },
        "public_run_refs": refs,
        "prior_candidates": candidate_entries_for_context(root, run_dir, direction),
        "sealed_material_excluded": [
            "evaluator.command",
            "evaluator.protected_paths contents",
            "evaluator.oracle_paths contents",
            "evaluator.score_parser_paths contents",
            "raw evaluator output contents",
            "raw trace refs that point at evaluator output logs",
            "run-level diagnostic summary refs that point at raw trace/log refs",
        ],
        "notes": [
            "This proposer context is diagnostic-only strategy-search input.",
            "It omits evaluator and oracle internals; the fixed evaluator is run only by eval.",
        ],
    }


def proposer_policy(direction: dict[str, Any], run_id: str, candidate_id: str) -> dict[str, Any]:
    return {
        "schema_version": PROPOSAL_POLICY_SCHEMA_VERSION,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "evidence_status": "diagnostic_only",
        "allowed_write_paths": string_list(direction.get("search_surface", [])),
        "rules": [
            "Generate a unified diff only.",
            "Modify only allowed_write_paths.",
            "Do not inspect, quote, or edit evaluator or oracle internals.",
            "Do not create archive/v2 content.",
            "Store the patch in this proposal bundle before evaluation.",
        ],
        "evaluation": {
            "runner": PROPOSAL_EVALUATION_COMMAND,
            "uses_fixed_direction_evaluator": True,
        },
    }


def proposer_prompt(context: dict[str, Any], policy: dict[str, Any]) -> str:
    direction = context["direction"]
    lines = [
        "# Strategy Search Proposer Prompt",
        "",
        "You are proposing one candidate patch for a fixed strategy-search direction.",
        "Use only the public context in this bundle and repository files under allowed_write_paths.",
        "Do not inspect or modify evaluator/oracle internals.",
        "",
        "## Objective",
        "",
        str(direction.get("objective", "")),
        "",
        "## Allowed Write Paths",
        "",
        *[f"- {path}" for path in policy["allowed_write_paths"]],
        "",
        "## Prior Candidate Evidence",
        "",
    ]
    prior = context.get("prior_candidates", [])
    if prior:
        for candidate in prior:
            trace_summary = candidate.get("trace_summary") if isinstance(candidate.get("trace_summary"), dict) else {}
            changed_paths = trace_summary.get("changed_paths") if isinstance(trace_summary.get("changed_paths"), list) else []
            lines.append(
                "- {candidate_id}: verdict={verdict} score={score} changed_paths={changed_paths} next={next_hypothesis}".format(
                    candidate_id=candidate.get("candidate_id"),
                    verdict=candidate.get("verdict"),
                    score=candidate.get("score"),
                    changed_paths=",".join(str(path) for path in changed_paths),
                    next_hypothesis=trace_summary.get("next_hypothesis"),
                )
            )
    else:
        lines.append("- No prior candidates recorded.")
    lines.extend(
        [
            "",
            "## Output",
            "",
            "Return a unified diff. The operator should save it as patch.diff in this proposal bundle,",
            "then evaluate it with the fixed runner command recorded in proposal.yml.",
        ]
    )
    return "\n".join(lines) + "\n"


def proposal_eval_command(root: Path, run_dir: Path, proposal_path: Path) -> str:
    return PROPOSAL_EVALUATION_COMMAND


def proposer_forbidden_tokens(direction: dict[str, Any]) -> list[str]:
    tokens: list[str] = ["trace_ref", "oracle_paths:", "score_parser_paths:", "protected_paths:"]
    evaluator = direction.get("evaluator") if isinstance(direction.get("evaluator"), dict) else {}
    command = evaluator.get("command")
    if isinstance(command, str) and command.strip():
        tokens.append(command)
    return sorted(token for token in dict.fromkeys(tokens) if token)


def proposer_forbidden_paths(direction: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    evaluator = direction.get("evaluator") if isinstance(direction.get("evaluator"), dict) else {}
    command = evaluator.get("command")
    if isinstance(command, str) and command.strip():
        try:
            paths.extend(evaluator_command_paths(shlex.split(command), base_commit=None, errors=[]))
        except ValueError:
            pass
    paths.extend(evaluator_combined_closure(direction))
    normalized = [canonical_public_path(path) for path in paths]
    return sorted(path for path in dict.fromkeys(normalized) if path)


def slash_flexible_pattern(token: str) -> str:
    parts = [re.escape(part).replace(r"\.", r"\\?\.") for part in token.split("/")]
    return r"/+(?:\./+)*".join(parts)


def public_text_variants(text: str) -> list[str]:
    variants: list[str] = []
    queue = [text]
    for _ in range(4):
        next_queue: list[str] = []
        for value in queue:
            normalized = value
            for _inner in range(4):
                updated = (
                    unquote(normalized)
                    .replace("\\\\/", "/")
                    .replace("\\/", "/")
                    .replace("\\\\.", ".")
                    .replace("\\.", ".")
                    .replace("\x00", "")
                )
                updated = re.sub(r"\s*/\s*", "/", updated)
                updated = re.sub(r"\s*\.\s*", ".", updated)
                updated = re.sub(r"\s*([@=])\s*", r"\1", updated)
                updated = re.sub(r"\s*:\s*(?=//)", ":", updated)
                if updated == normalized:
                    break
                normalized = updated
            if normalized not in variants:
                variants.append(normalized)
            if normalized != value:
                next_queue.append(normalized)
        if not next_queue:
            break
        queue = next_queue
    return variants or [text]


def public_scalar_variants(value: str | bytes) -> list[str]:
    if isinstance(value, str):
        variants: list[str] = []
        for text in public_text_variants(value):
            if text not in variants:
                variants.append(text)
        return variants
    variants: list[str] = []
    for encoding in ("utf-8", "utf-16-le", "utf-16-be"):
        try:
            decoded = value.decode(encoding)
        except UnicodeDecodeError:
            decoded = value.decode(encoding, errors="ignore")
        variants.extend(public_text_variants(decoded))
    variants.append(repr(value))
    return list(dict.fromkeys(variants))


PUBLIC_PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_./%\\:?#=(),@+-]+")
PUBLIC_RUN_ARTIFACT_RE = re.compile(
    r"(?:^|/)\.harness/search-runs/[^/]+/candidates/[^/]+/"
    r"(?:patch\.diff|score\.yml|stdout\.log|stderr\.log|trace\.ya?ml|trace\.md)(?:$|[:,/])"
    r"|^candidates/[^/]+/(?:patch\.diff|score\.yml|stdout\.log|stderr\.log|trace\.ya?ml|trace\.md)(?:$|[:,/])"
    r"|^proposals/[^/]+/(?:patch\.diff|proposal\.yml|prompt\.md|policy\.yml|public-context\.yml)(?:$|[:,/])"
)
PUBLIC_RUN_SUMMARY_RE = re.compile(
    r"(?:^|/)\.harness/search-runs/[^/]+/(?:summary\.yml|search-set\.yml)$"
)
PUBLIC_SIDECAR_BASENAMES = {
    "direction.yml",
    "proposals.jsonl",
    "run.yml",
    "score.yml",
    "search-set.yml",
    "scores.jsonl",
    "stderr.log",
    "stdout.log",
    "summary.yml",
    "trace.md",
    "trace.yaml",
    "trace.yml",
}
PUBLIC_PATH_WINDOW_LIMIT = 12


def canonical_public_path(value: str) -> str:
    text = public_text_variants(value)[-1].strip()
    text = text.strip("'\"`()[]{}<>,;")
    for prefix in (":raw/", ",raw/", "raw/"):
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
            break
    text = re.sub(r"[\)\]\}]+:L?\d+(?:-\d+)?$", "", text)
    text = re.sub(r":L?\d+(?:-\d+)?$", "", text)
    def strip_file_alias_prefix(path: str) -> str:
        for prefix in ("localhost/", "file://localhost/", "file:///", "file://", "file:/", "file/"):
            if path.startswith(prefix):
                return path.removeprefix(prefix).lstrip("/")
        return path

    for _ in range(4):
        scheme_authority_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://(.+)$", text)
        if scheme_authority_match and not re.match(r"^[A-Za-z]:", text):
            text = strip_file_alias_prefix(scheme_authority_match.group(2)).lstrip("/")
            continue
        scheme_match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):(.+)$", text)
        if (
            scheme_match
            and scheme_match.group(1).lower() in {"cursor", "file", "path", "vscode"}
            and not re.match(r"^[A-Za-z]:", text)
        ):
            text = strip_file_alias_prefix(scheme_match.group(2)).lstrip("/")
            continue
        break
    text = strip_file_alias_prefix(text)
    text = re.split(r"[?#]", text, 1)[0]
    text = text.rstrip("'\"`()[]{}<>,;")
    text = text.rstrip("()[]{}")
    text = re.sub(r"[\)\]\}]+:L?\d+(?:-\d+)?$", "", text)
    text = re.sub(r":L?\d+(?:-\d+)?$", "", text)
    while text.endswith("."):
        text = text[:-1]
    if not text:
        return ""
    text = text.replace("\\", "/")
    text = re.sub(r"/+", "/", text)
    normalized = posixpath.normpath(text)
    if normalized == ".":
        return ""
    return normalized.lstrip("/")


def path_is_within_public_source(path: str, direction: dict[str, Any]) -> bool:
    candidate = path.rstrip("/")
    for allowed in string_list(direction.get("search_surface", [])):
        allowed_path = canonical_public_path(allowed).rstrip("/")
        allowed_is_directory = allowed.strip().endswith("/")
        if not allowed_path:
            continue
        if candidate == allowed_path:
            return True
        if allowed_is_directory and candidate.startswith(f"{allowed_path}/"):
            return True
    return False


def public_source_file_child_alias(path: str, direction: dict[str, Any]) -> bool:
    candidate = path.rstrip("/")
    for allowed in string_list(direction.get("search_surface", [])):
        allowed_path = canonical_public_path(allowed).rstrip("/")
        if allowed.strip().endswith("/"):
            continue
        if not allowed_path:
            continue
        if candidate.startswith(f"{allowed_path}/") or candidate.startswith(f"{allowed_path}:") or candidate.startswith(f"{allowed_path},"):
            return True
    return False


def forbidden_public_path_reason(path: str, direction: dict[str, Any]) -> str | None:
    for variant in public_text_variants(path):
        stripped = variant.strip("'\"`()[]{}<>,;")
        if public_source_file_child_alias(stripped, direction):
            return canonical_public_path(stripped) or stripped
    candidate = canonical_public_path(path)
    if not candidate:
        return None
    traversal_candidate = re.sub(r"^(?:\.\./)+", "", candidate)
    if traversal_candidate and traversal_candidate != candidate:
        traversal_reason = forbidden_public_path_reason(traversal_candidate, direction)
        if traversal_reason is not None:
            return traversal_reason
    first_part = re.split(r"[:,/]", candidate, 1)[0]
    if first_part == "patch.diff" and (
        candidate != "patch.diff" or canonical_public_path(path) != path.strip("'\"`()[]{}<>,;")
    ):
        return candidate
    if ".harness/search-runs/" in candidate:
        return candidate
    if PUBLIC_RUN_ARTIFACT_RE.search(candidate):
        return candidate
    if PUBLIC_RUN_SUMMARY_RE.search(candidate):
        return candidate
    if public_source_file_child_alias(candidate, direction):
        return candidate
    if path_is_within_public_source(candidate, direction):
        return None
    decorated_prefixes = [
        candidate.split(separator, 1)[0]
        for separator in ("=", "@")
        if separator in candidate and candidate.split(separator, 1)[0]
    ]
    for decorated_prefix in decorated_prefixes:
        decorated_first = re.split(r"[:,/]", decorated_prefix, 1)[0]
        if (
            decorated_first == "patch.diff"
            or decorated_prefix == "patch.diff"
            or decorated_prefix.startswith("patch.diff/")
            or decorated_prefix.startswith("patch.diff:")
            or decorated_prefix.startswith("patch.diff,")
            or decorated_prefix.startswith("patch.diff=")
            or decorated_prefix.startswith("patch.diff@")
            or decorated_first in PUBLIC_SIDECAR_BASENAMES
            or ".harness/search-runs/" in decorated_prefix
            or PUBLIC_RUN_ARTIFACT_RE.search(decorated_prefix)
            or PUBLIC_RUN_SUMMARY_RE.search(decorated_prefix)
            or public_source_file_child_alias(decorated_prefix, direction)
        ):
            return decorated_prefix
        for forbidden in proposer_forbidden_paths(direction):
            forbidden = forbidden.rstrip("/")
            if decorated_prefix == forbidden or decorated_prefix.startswith(f"{forbidden}/"):
                return forbidden
    for forbidden in proposer_forbidden_paths(direction):
        forbidden = forbidden.rstrip("/")
        if not forbidden:
            continue
        padded = f"/{candidate}/"
        forbidden_padded = f"/{forbidden}/"
        if (
            candidate == forbidden
            or candidate.startswith(f"{forbidden}/")
            or candidate.startswith(f"{forbidden}:")
            or candidate.startswith(f"{forbidden},")
            or candidate.endswith(f"/{forbidden}")
            or forbidden_padded in padded
        ):
            return forbidden
    if first_part in PUBLIC_SIDECAR_BASENAMES:
        return candidate
    return None


def public_path_window_limit(direction: dict[str, Any]) -> int:
    width = 1
    for path in proposer_forbidden_paths(direction):
        width = max(width, len(path.split()))
    return min(max(width + 2, 4), PUBLIC_PATH_WINDOW_LIMIT)


def forbidden_public_path_spans(text: str, direction: dict[str, Any]) -> list[tuple[int, int, str]]:
    matches = list(PUBLIC_PATH_TOKEN_RE.finditer(text))
    spans: list[tuple[int, int, str]] = []
    window_limit = public_path_window_limit(direction)
    for start_index, start_match in enumerate(matches):
        for stop_index in range(start_index + 1, min(len(matches), start_index + window_limit) + 1):
            stop_match = matches[stop_index - 1]
            if any(
                not text[matches[index - 1].end() : matches[index].start()].isspace()
                for index in range(start_index + 1, stop_index)
            ):
                break
            fragment = text[start_match.start() : stop_match.end()]
            if stop_index - start_index > 1 and "/" not in fragment and "." not in fragment:
                continue
            reason = forbidden_public_path_reason(fragment, direction)
            if reason is not None:
                spans.append((start_match.start(), stop_match.end(), reason))
    selected: list[tuple[int, int, str]] = []
    for start, end, reason in sorted(spans, key=lambda item: (item[0], -(item[1] - item[0]))):
        if selected and start < selected[-1][1]:
            continue
        selected.append((start, end, reason))
    return selected


def forbidden_public_reasons(text: str, direction: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for variant in public_text_variants(text):
        for token in proposer_forbidden_tokens(direction):
            if token in variant or re.search(slash_flexible_pattern(token), variant):
                reasons.append(token)
        for _start, _end, reason in forbidden_public_path_spans(variant, direction):
            reasons.append(reason)
    return list(dict.fromkeys(reasons))


def validate_no_forbidden_public_tokens(text: str, *, source: str, direction: dict[str, Any], errors: list[str]) -> None:
    for reason in forbidden_public_reasons(text, direction):
        errors.append(f"{source} must not expose sealed evaluator/oracle material: {reason}")


def validate_no_forbidden_public_values(
    value: Any,
    *,
    source: str,
    direction: dict[str, Any],
    errors: list[str],
) -> None:
    if isinstance(value, (str, bytes)):
        if isinstance(value, bytes):
            errors.append(f"{source} must not contain binary YAML scalar")
        for text in public_scalar_variants(value):
            validate_no_forbidden_public_tokens(text, source=source, direction=direction, errors=errors)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_no_forbidden_public_values(
                item,
                source=f"{source}[{index}]",
                direction=direction,
                errors=errors,
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, (str, bytes)):
                if isinstance(key, bytes):
                    errors.append(f"{source} key must not be a binary YAML scalar")
                for text in public_scalar_variants(key):
                    validate_no_forbidden_public_tokens(
                        text,
                        source=f"{source} key",
                        direction=direction,
                        errors=errors,
                    )
            validate_no_forbidden_public_values(
                item,
                source=f"{source}.{key}",
                direction=direction,
                errors=errors,
            )


def sanitize_public_text(value: str, direction: dict[str, Any]) -> str:
    for variant in public_text_variants(value):
        if variant != value and forbidden_public_reasons(variant, direction):
            value = variant
            break
    spans = forbidden_public_path_spans(value, direction)
    if spans:
        parts: list[str] = []
        cursor = 0
        for start, end, _reason in spans:
            if start < cursor:
                continue
            parts.append(value[cursor:start])
            parts.append("[sealed]")
            cursor = end
        parts.append(value[cursor:])
        value = "".join(parts)
    for reason in forbidden_public_reasons(value, direction):
        if reason in value:
            value = value.replace(reason, "[sealed]")
    def replace_if_forbidden(match: re.Match[str]) -> str:
        token = match.group(0)
        return "[sealed]" if forbidden_public_path_reason(token, direction) is not None else token
    value = PUBLIC_PATH_TOKEN_RE.sub(replace_if_forbidden, value)
    for token in proposer_forbidden_tokens(direction):
        value = re.sub(slash_flexible_pattern(token), "[sealed]", value)
    return value


def sanitize_public_value(value: Any, direction: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return sanitize_public_text(value, direction)
    if isinstance(value, list):
        return [sanitize_public_value(item, direction) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_public_value(item, direction) for key, item in value.items()}
    return value


def validate_proposer_context(context: dict[str, Any], *, direction: dict[str, Any], errors: list[str]) -> None:
    validate_exact_fields(context, PROPOSAL_CONTEXT_FIELDS, source="public-context.yml", errors=errors)
    if context.get("schema_version") != PROPOSAL_CONTEXT_SCHEMA_VERSION:
        errors.append(f"public-context.yml schema_version must be {PROPOSAL_CONTEXT_SCHEMA_VERSION}")
    if context.get("evidence_status") != "diagnostic_only":
        errors.append("public-context.yml evidence_status must be diagnostic_only")
    if context.get("direction_digest") != digest_direction(direction):
        errors.append("public-context.yml direction_digest must match direction.yml")
    direction_context = context.get("direction")
    if not isinstance(direction_context, dict):
        errors.append("public-context.yml direction must be a mapping")
    else:
        validate_exact_fields(
            direction_context,
            PROPOSAL_CONTEXT_DIRECTION_FIELDS,
            source="public-context.yml direction",
            errors=errors,
        )
        if direction_context.get("search_surface") != string_list(direction.get("search_surface", [])):
            errors.append("public-context.yml direction.search_surface must match direction.yml")
    public_refs = context.get("public_run_refs")
    if not isinstance(public_refs, dict):
        errors.append("public-context.yml public_run_refs must be a mapping")
    else:
        validate_exact_fields(
            public_refs,
            PROPOSAL_CONTEXT_REFS_FIELDS,
            source="public-context.yml public_run_refs",
            errors=errors,
        )
        if public_refs.get("summary_ref") is not None:
            errors.append("public-context.yml public_run_refs.summary_ref must be null")
        if public_refs.get("search_set_ref") is not None:
            errors.append("public-context.yml public_run_refs.search_set_ref must be null")
    for candidate in context.get("prior_candidates", []):
        if not isinstance(candidate, dict):
            errors.append("public-context.yml prior_candidates entries must be mappings")
            continue
        validate_exact_fields(
            candidate,
            PROPOSAL_CONTEXT_CANDIDATE_FIELDS,
            source="public-context.yml prior_candidates[]",
            errors=errors,
        )
        if "trace_ref" in candidate:
            errors.append("public-context.yml must not expose raw trace_ref entries to proposer")
        trace_summary = candidate.get("trace_summary")
        if not isinstance(trace_summary, dict):
            errors.append("public-context.yml trace_summary must be a mapping")
        else:
            validate_exact_fields(
                trace_summary,
                PROPOSAL_CONTEXT_TRACE_SUMMARY_FIELDS,
                source="public-context.yml trace_summary",
                errors=errors,
            )
    if not isinstance(context.get("sealed_material_excluded"), list):
        errors.append("public-context.yml sealed_material_excluded must be a list")
    if not isinstance(context.get("notes"), list):
        errors.append("public-context.yml notes must be a list")


def validate_proposer_policy(policy: dict[str, Any], *, direction: dict[str, Any], errors: list[str]) -> None:
    validate_exact_fields(policy, PROPOSAL_POLICY_FIELDS, source="policy.yml", errors=errors)
    if policy.get("schema_version") != PROPOSAL_POLICY_SCHEMA_VERSION:
        errors.append(f"policy.yml schema_version must be {PROPOSAL_POLICY_SCHEMA_VERSION}")
    if policy.get("evidence_status") != "diagnostic_only":
        errors.append("policy.yml evidence_status must be diagnostic_only")
    if policy.get("allowed_write_paths") != string_list(direction.get("search_surface", [])):
        errors.append("policy.yml allowed_write_paths must match direction search_surface")
    if not isinstance(policy.get("rules"), list):
        errors.append("policy.yml rules must be a list")
    evaluation = policy.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation.get("uses_fixed_direction_evaluator") is not True:
        errors.append("policy.yml evaluation must require the fixed direction evaluator")
    elif isinstance(evaluation, dict):
        validate_exact_fields(
            evaluation,
            PROPOSAL_POLICY_EVALUATION_FIELDS,
            source="policy.yml evaluation",
            errors=errors,
        )
        if evaluation.get("runner") != PROPOSAL_EVALUATION_COMMAND:
            errors.append("policy.yml evaluation.runner must match the canonical eval --proposal command")


def proposal_ledger_ref(run_dir: Path, proposal_path: Path) -> str:
    return run_relative_ref(run_dir, proposal_path)


def proposal_ledger_record(
    *,
    run_id: str,
    direction: dict[str, Any],
    candidate_id: str,
    proposal_path: Path,
    run_dir: Path,
    status: str,
    prompt_path: Path,
    policy_path: Path,
    context_path: Path,
    patch_sha256: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": PROPOSAL_LEDGER_SCHEMA_VERSION,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "proposal_ref": proposal_ledger_ref(run_dir, proposal_path),
        "status": status,
        "base_commit": direction["base_ref"],
        "direction_digest": digest_direction(direction),
        "created_at": utc_now(),
        "prompt_sha256": file_sha256(prompt_path),
        "policy_sha256": file_sha256(policy_path),
        "context_sha256": file_sha256(context_path),
        "patch_sha256": patch_sha256,
        "proposal_sha256": file_sha256(proposal_path),
    }


def proposal_ledger_entries(run_dir: Path) -> list[dict[str, Any]]:
    ledger_path = run_dir / "proposals.jsonl"
    if not ledger_path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StrategySearchError(f"{ledger_path}: malformed JSONL row {line_number}: {exc.msg}") from exc
        if not isinstance(entry, dict):
            raise StrategySearchError(f"{ledger_path}: JSONL row {line_number} must be an object")
        entries.append(entry)
    return entries


def validate_proposal_ledger(
    proposal: dict[str, Any],
    *,
    run_dir: Path,
    proposal_path: Path,
    errors: list[str],
) -> None:
    try:
        proposal_ref = proposal_ledger_ref(run_dir, proposal_path)
    except ValueError:
        errors.append("proposal.yml must be inside the search run directory")
        return
    try:
        ledger_entries = proposal_ledger_entries(run_dir)
    except StrategySearchError as exc:
        errors.append(str(exc))
        return
    entries = [
        entry
        for entry in ledger_entries
        if entry.get("candidate_id") == proposal.get("candidate_id")
        and entry.get("proposal_ref") == proposal_ref
        and entry.get("status") == "ready_for_evaluation"
    ]
    if not entries:
        errors.append("proposal ledger must contain a ready_for_evaluation entry for this proposal")
        return
    if len(entries) != 1:
        errors.append("proposal ledger must contain exactly one ready_for_evaluation entry for this proposal")
        return
    entry = entries[0]
    expected = {
        "schema_version": PROPOSAL_LEDGER_SCHEMA_VERSION,
        "run_id": proposal.get("run_id"),
        "candidate_id": proposal.get("candidate_id"),
        "proposal_ref": proposal_ref,
        "status": proposal.get("status"),
        "base_commit": proposal.get("base_commit"),
        "direction_digest": proposal.get("direction_digest"),
        "prompt_sha256": proposal.get("prompt_sha256"),
        "policy_sha256": proposal.get("policy_sha256"),
        "context_sha256": proposal.get("context_sha256"),
        "patch_sha256": proposal.get("patch_sha256"),
        "proposal_sha256": file_sha256(proposal_path),
    }
    for field, expected_value in expected.items():
        if entry.get(field) != expected_value:
            errors.append(f"proposal ledger {field} must match proposal creation record")


def validate_awaiting_proposal_ledger(
    proposal: dict[str, Any],
    *,
    run_dir: Path,
    proposal_path: Path,
    errors: list[str],
) -> None:
    try:
        proposal_ref = proposal_ledger_ref(run_dir, proposal_path)
    except ValueError:
        errors.append("proposal.yml must be inside the search run directory")
        return
    try:
        ledger_entries = proposal_ledger_entries(run_dir)
    except StrategySearchError as exc:
        errors.append(str(exc))
        return
    entries = [
        entry
        for entry in ledger_entries
        if entry.get("candidate_id") == proposal.get("candidate_id")
        and entry.get("proposal_ref") == proposal_ref
        and entry.get("status") == "awaiting_patch"
    ]
    ready_entries = [
        entry
        for entry in ledger_entries
        if entry.get("candidate_id") == proposal.get("candidate_id")
        and entry.get("proposal_ref") == proposal_ref
        and entry.get("status") == "ready_for_evaluation"
    ]
    if ready_entries:
        errors.append("proposal ledger must not contain a ready_for_evaluation entry before sealing")
        return
    if not entries:
        errors.append("proposal ledger must contain an awaiting_patch entry before sealing")
        return
    if len(entries) != 1:
        errors.append("proposal ledger must contain exactly one awaiting_patch entry before sealing")
        return
    entry = entries[0]
    expected = {
        "schema_version": PROPOSAL_LEDGER_SCHEMA_VERSION,
        "run_id": proposal.get("run_id"),
        "candidate_id": proposal.get("candidate_id"),
        "proposal_ref": proposal_ref,
        "status": "awaiting_patch",
        "base_commit": proposal.get("base_commit"),
        "direction_digest": proposal.get("direction_digest"),
        "prompt_sha256": proposal.get("prompt_sha256"),
        "policy_sha256": proposal.get("policy_sha256"),
        "context_sha256": proposal.get("context_sha256"),
        "patch_sha256": None,
        "proposal_sha256": file_sha256(proposal_path),
    }
    for field, expected_value in expected.items():
        if entry.get(field) != expected_value:
            errors.append(f"awaiting proposal ledger {field} must match original proposal record")


def remove_proposal_ledger_entries(run_dir: Path, *, proposal_path: Path, candidate_id: str) -> None:
    ledger_path = run_dir / "proposals.jsonl"
    if not ledger_path.exists():
        return
    proposal_ref = proposal_ledger_ref(run_dir, proposal_path)
    entries = proposal_ledger_entries(run_dir)
    kept = [
        entry
        for entry in entries
        if not (entry.get("candidate_id") == candidate_id and entry.get("proposal_ref") == proposal_ref)
    ]
    write_jsonl(ledger_path, kept)


def validate_proposal_public_bundle(
    proposal: dict[str, Any],
    *,
    direction: dict[str, Any],
    proposal_dir: Path,
    errors: list[str],
) -> None:
    bundle_files = {
        "prompt_ref": ("prompt.md", "prompt_sha256"),
        "policy_ref": ("policy.yml", "policy_sha256"),
        "context_ref": ("public-context.yml", "context_sha256"),
    }
    valid_sidecars: dict[str, Path] = {}
    for field, (expected, sha_field) in bundle_files.items():
        if proposal.get(field) != expected:
            errors.append(f"proposal.{field} must be {expected!r}")
            continue
        bundle_path = proposal_dir / expected
        if not bundle_path.is_file():
            errors.append(f"proposal.{field} file is missing: {expected}")
            continue
        sidecar_errors = proposal_sidecar_errors(proposal_dir, bundle_path, label=expected)
        if sidecar_errors:
            errors.extend(sidecar_errors)
            continue
        if proposal.get(sha_field) != file_sha256(bundle_path):
            errors.append(f"proposal.{sha_field} must match {expected}")
            continue
        valid_sidecars[expected] = bundle_path
    context_path = proposal_dir / "public-context.yml"
    if "public-context.yml" in valid_sidecars:
        context_path = valid_sidecars["public-context.yml"]
        try:
            context = load_yaml_mapping(context_path)
        except StrategySearchError as exc:
            errors.append(str(exc))
        else:
            validate_proposer_context(context, direction=direction, errors=errors)
            validate_no_forbidden_public_values(
                context,
                source="public-context.yml",
                direction=direction,
                errors=errors,
            )
    policy_path = proposal_dir / "policy.yml"
    if "policy.yml" in valid_sidecars:
        policy_path = valid_sidecars["policy.yml"]
        try:
            policy = load_yaml_mapping(policy_path)
        except StrategySearchError as exc:
            errors.append(str(exc))
        else:
            validate_proposer_policy(policy, direction=direction, errors=errors)
            validate_no_forbidden_public_values(
                policy,
                source="policy.yml",
                direction=direction,
                errors=errors,
            )
    prompt_path = proposal_dir / "prompt.md"
    if "prompt.md" in valid_sidecars:
        prompt_path = valid_sidecars["prompt.md"]
        expected_prompt = None
        if "public-context.yml" in valid_sidecars and "policy.yml" in valid_sidecars:
            try:
                context_for_prompt = load_yaml_mapping(valid_sidecars["public-context.yml"])
                policy_for_prompt = load_yaml_mapping(valid_sidecars["policy.yml"])
            except StrategySearchError:
                context_for_prompt = {}
                policy_for_prompt = {}
            if (
                isinstance(context_for_prompt, dict)
                and isinstance(context_for_prompt.get("direction"), dict)
                and isinstance(policy_for_prompt, dict)
                and isinstance(policy_for_prompt.get("allowed_write_paths"), list)
            ):
                expected_prompt = proposer_prompt(context_for_prompt, policy_for_prompt)
        prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace")
        if expected_prompt is not None and prompt_text != expected_prompt:
            errors.append("prompt.md must match the canonical prompt for public-context.yml and policy.yml")
        validate_no_forbidden_public_tokens(prompt_text, source="prompt.md", direction=direction, errors=errors)


def validate_proposal_public_metadata(
    proposal: dict[str, Any],
    *,
    direction: dict[str, Any],
    errors: list[str],
) -> None:
    for field in ("why", "next_hypothesis", "evaluation_command"):
        value = proposal.get(field)
        if isinstance(value, str):
            validate_no_forbidden_public_tokens(value, source=f"proposal.{field}", direction=direction, errors=errors)
    if "validation_errors" in proposal:
        validate_no_forbidden_public_values(
            proposal["validation_errors"],
            source="proposal.validation_errors",
            direction=direction,
            errors=errors,
        )


def public_proposal_validation_errors(errors: list[str]) -> list[str]:
    public_errors: list[str] = []
    for error in errors:
        if error.startswith("candidate patch must not touch evaluator closure:"):
            public_errors.append("candidate patch must not touch evaluator closure")
        elif error.startswith("candidate patch touches path outside search_surface:"):
            public_errors.append("candidate patch touches path outside search_surface")
        elif error.startswith("candidate patch must not touch archive/v2:"):
            public_errors.append("candidate patch must not touch archive/v2")
        else:
            public_errors.append(error)
    return sorted(dict.fromkeys(public_errors))


def proposal_sidecar_errors(proposal_dir: Path, path: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    errors.extend(mutable_run_file_errors(path, label=f"proposal {label}"))
    try:
        path.resolve().relative_to(proposal_dir.resolve())
    except ValueError:
        errors.append(f"proposal {label} must resolve inside the proposal directory: {path}")
    return errors


def seal_awaiting_proposal_for_eval(
    proposal: dict[str, Any],
    *,
    root: Path,
    run_dir: Path,
    run_meta: dict[str, Any],
    direction: dict[str, Any],
    proposal_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    validate_exact_fields(proposal, PROPOSAL_FIELDS, source="proposal", errors=errors)
    if proposal.get("schema_version") != PROPOSAL_SCHEMA_VERSION:
        errors.append(f"proposal.schema_version must be {PROPOSAL_SCHEMA_VERSION}")
    if proposal.get("evidence_status") != "diagnostic_only":
        errors.append("proposal.evidence_status must be diagnostic_only")
    if proposal.get("status") != "awaiting_patch":
        return proposal, errors
    if proposal.get("run_id") != run_meta.get("run_id"):
        errors.append("proposal.run_id must match run.yml")
    if proposal.get("base_commit") != direction.get("base_ref"):
        errors.append("proposal.base_commit must match direction base_ref")
    if proposal.get("direction_digest") != digest_direction(direction):
        errors.append("proposal.direction_digest must match direction.yml")
    if not isinstance(proposal.get("candidate_id"), str):
        errors.append("proposal.candidate_id must be a string")
    else:
        validate_run_id(proposal["candidate_id"], source="proposal.candidate_id", errors=errors)
        if proposal["candidate_id"] != proposal_path.parent.name:
            errors.append("proposal.candidate_id must match the proposal directory name")
    if not is_relative_to(proposal_path.resolve(), run_dir.resolve()):
        errors.append("proposal.yml must be inside the search run directory")
    if proposal.get("patch_ref") is not None:
        errors.append("awaiting proposal.patch_ref must be null before sealing")
    if proposal.get("patch_sha256") is not None:
        errors.append("awaiting proposal.patch_sha256 must be null before sealing")
    if proposal.get("evaluation_command") != "":
        errors.append("awaiting proposal.evaluation_command must be empty before sealing")
    if proposal.get("validation_errors") != []:
        errors.append("awaiting proposal.validation_errors must be empty before sealing")
    for field in ("why", "next_hypothesis"):
        if not isinstance(proposal.get(field), str) or not proposal[field].strip():
            errors.append(f"proposal.{field} must be a non-empty string")

    proposal_dir = proposal_path.parent
    validate_awaiting_proposal_ledger(proposal, run_dir=run_dir, proposal_path=proposal_path, errors=errors)
    validate_proposal_public_metadata(proposal, direction=direction, errors=errors)
    validate_proposal_public_bundle(proposal, direction=direction, proposal_dir=proposal_dir, errors=errors)
    patch_path = proposal_dir / "patch.diff"
    if not patch_path.is_file():
        errors.append(f"proposal patch is missing: {patch_path}")
    else:
        patch_sidecar_errors = proposal_sidecar_errors(proposal_dir, patch_path, label="patch.diff")
        errors.extend(patch_sidecar_errors)
        if not patch_sidecar_errors:
            errors.extend(patch_boundary_errors(root, direction, patch_path))
    if errors:
        return proposal, errors

    for error in mutable_run_file_errors(proposal_path, label="proposal.yml"):
        errors.append(error)
    if errors:
        return proposal, errors

    sealed = dict(proposal)
    sealed["status"] = "ready_for_evaluation"
    sealed["patch_ref"] = "patch.diff"
    sealed["patch_sha256"] = file_sha256(patch_path)
    sealed["validation_errors"] = []
    sealed["evaluation_command"] = proposal_eval_command(root, run_dir, proposal_path)
    write_yaml(proposal_path, sealed)
    append_jsonl(
        run_dir / "proposals.jsonl",
        proposal_ledger_record(
            run_id=str(run_meta.get("run_id", run_dir.name)),
            direction=direction,
            candidate_id=str(sealed["candidate_id"]),
            proposal_path=proposal_path,
            run_dir=run_dir,
            status="ready_for_evaluation",
            prompt_path=proposal_dir / "prompt.md",
            policy_path=proposal_dir / "policy.yml",
            context_path=proposal_dir / "public-context.yml",
            patch_sha256=sealed["patch_sha256"],
        ),
    )
    return sealed, []


def validate_proposal_for_eval(
    proposal: dict[str, Any],
    *,
    root: Path,
    run_dir: Path,
    run_meta: dict[str, Any],
    direction: dict[str, Any],
    proposal_path: Path,
) -> list[str]:
    errors: list[str] = []
    validate_exact_fields(proposal, PROPOSAL_FIELDS, source="proposal", errors=errors)
    if proposal.get("schema_version") != PROPOSAL_SCHEMA_VERSION:
        errors.append(f"proposal.schema_version must be {PROPOSAL_SCHEMA_VERSION}")
    if proposal.get("evidence_status") != "diagnostic_only":
        errors.append("proposal.evidence_status must be diagnostic_only")
    if proposal.get("status") != "ready_for_evaluation":
        errors.append("proposal.status must be ready_for_evaluation")
    if proposal.get("run_id") != run_meta.get("run_id"):
        errors.append("proposal.run_id must match run.yml")
    if proposal.get("base_commit") != direction.get("base_ref"):
        errors.append("proposal.base_commit must match direction base_ref")
    if proposal.get("direction_digest") != digest_direction(direction):
        errors.append("proposal.direction_digest must match direction.yml")
    if not isinstance(proposal.get("candidate_id"), str):
        errors.append("proposal.candidate_id must be a string")
    else:
        validate_run_id(proposal["candidate_id"], source="proposal.candidate_id", errors=errors)
        if proposal["candidate_id"] != proposal_path.parent.name:
            errors.append("proposal.candidate_id must match the proposal directory name")
    if not is_relative_to(proposal_path.resolve(), run_dir.resolve()):
        errors.append("proposal.yml must be inside the search run directory")

    proposal_dir = proposal_path.parent
    validate_proposal_public_bundle(proposal, direction=direction, proposal_dir=proposal_dir, errors=errors)
    if proposal.get("patch_ref") != "patch.diff":
        errors.append("proposal.patch_ref must be 'patch.diff'")
        patch_path = proposal_dir / "patch.diff"
    else:
        patch_path = proposal_dir / "patch.diff"
    if not patch_path.is_file():
        errors.append(f"proposal patch is missing: {patch_path}")
    else:
        patch_sidecar_errors = proposal_sidecar_errors(proposal_dir, patch_path, label="patch.diff")
        errors.extend(patch_sidecar_errors)
        if not patch_sidecar_errors:
            if proposal.get("patch_sha256") != file_sha256(patch_path):
                errors.append("proposal.patch_sha256 must match patch.diff")
            errors.extend(patch_boundary_errors(root, direction, patch_path))
    if proposal.get("validation_errors") != []:
        errors.append("proposal.validation_errors must be empty for evaluation")
    for field in ("why", "next_hypothesis", "evaluation_command"):
        if not isinstance(proposal.get(field), str) or not proposal[field].strip():
            errors.append(f"proposal.{field} must be a non-empty string")
    validate_proposal_public_metadata(proposal, direction=direction, errors=errors)
    expected_command = proposal_eval_command(root, run_dir, proposal_path)
    if isinstance(proposal.get("evaluation_command"), str) and proposal.get("evaluation_command") != expected_command:
        errors.append("proposal.evaluation_command must match the canonical eval --proposal command")
    validate_proposal_ledger(proposal, run_dir=run_dir, proposal_path=proposal_path, errors=errors)
    return errors


def propose_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    try:
        run_dir, run_meta, direction = load_run(root, args.run)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    run_id = run_meta.get("run_id", run_dir.name)
    if not isinstance(run_id, str):
        errors.append("run.yml run_id must be a string")
        run_id = run_dir.name
    candidate_id = args.candidate_id or next_candidate_id(run_dir)
    validate_run_id(candidate_id, source="candidate_id", errors=errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    proposal_dir = run_dir / "proposals" / candidate_id
    if path_component_has_symlink(root, proposal_dir.parent):
        print("ERROR: proposal output path must not contain symlinks", file=sys.stderr)
        return 1
    if (proposal_dir.exists() or proposal_dir.is_symlink()) and not args.overwrite:
        print(f"ERROR: proposal already exists: {proposal_dir}", file=sys.stderr)
        return 1
    if proposal_dir.is_symlink() and args.overwrite:
        print("ERROR: proposal output path must not contain symlinks", file=sys.stderr)
        return 1
    if proposal_dir.exists() and args.overwrite:
        try:
            remove_proposal_ledger_entries(
                run_dir,
                proposal_path=proposal_dir / "proposal.yml",
                candidate_id=candidate_id,
            )
        except StrategySearchError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        shutil.rmtree(proposal_dir)
    proposal_dir.mkdir(parents=True, exist_ok=True)

    context = proposer_public_context(root, run_dir, run_meta, direction)
    policy = proposer_policy(direction, run_id, candidate_id)
    prompt_text = proposer_prompt(context, policy)
    bundle_errors: list[str] = []
    validate_proposer_context(context, direction=direction, errors=bundle_errors)
    validate_proposer_policy(policy, direction=direction, errors=bundle_errors)
    validate_no_forbidden_public_tokens(
        yaml.safe_dump(context, sort_keys=False),
        source="public-context.yml",
        direction=direction,
        errors=bundle_errors,
    )
    validate_no_forbidden_public_tokens(
        yaml.safe_dump(policy, sort_keys=False),
        source="policy.yml",
        direction=direction,
        errors=bundle_errors,
    )
    validate_no_forbidden_public_tokens(prompt_text, source="prompt.md", direction=direction, errors=bundle_errors)
    if bundle_errors:
        for error in bundle_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    write_yaml(proposal_dir / "public-context.yml", context)
    write_yaml(proposal_dir / "policy.yml", policy)
    (proposal_dir / "prompt.md").write_text(prompt_text, encoding="utf-8")
    context_path = proposal_dir / "public-context.yml"
    policy_path = proposal_dir / "policy.yml"
    prompt_path = proposal_dir / "prompt.md"

    patch_ref: str | None = None
    patch_sha: str | None = None
    validation_errors: list[str] = []
    status = "awaiting_patch"
    if args.patch:
        source_patch = run_path(root, args.patch)
        source_errors = patch_source_errors(root, source_patch)
        if source_errors:
            validation_errors = source_errors
            status = "invalid"
        elif source_patch.is_file():
            patch_path = proposal_dir / "patch.diff"
            shutil.copyfile(source_patch, patch_path)
            patch_ref = "patch.diff"
            patch_sha = file_sha256(patch_path)
            validation_errors = public_proposal_validation_errors(patch_boundary_errors(root, direction, patch_path))
            status = "invalid" if validation_errors else "ready_for_evaluation"
        else:
            validation_errors = [f"patch does not exist: {source_patch}"]
            status = "invalid"

    proposal_path = proposal_dir / "proposal.yml"
    proposal = {
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "base_commit": direction["base_ref"],
        "direction_digest": digest_direction(direction),
        "created_at": utc_now(),
        "evidence_status": "diagnostic_only",
        "status": status,
        "prompt_ref": "prompt.md",
        "policy_ref": "policy.yml",
        "context_ref": "public-context.yml",
        "prompt_sha256": file_sha256(prompt_path),
        "policy_sha256": file_sha256(policy_path),
        "context_sha256": file_sha256(context_path),
        "patch_ref": patch_ref,
        "patch_sha256": patch_sha,
        "why": args.why.strip() if isinstance(args.why, str) and args.why.strip() else "proposer-generated candidate patch",
        "next_hypothesis": (
            args.next_hypothesis.strip()
            if isinstance(args.next_hypothesis, str) and args.next_hypothesis.strip()
            else "Evaluate this stored proposal patch, then inspect the resulting diagnostic trace summary."
        ),
        "validation_errors": validation_errors,
        "evaluation_command": proposal_eval_command(root, run_dir, proposal_path)
        if status == "ready_for_evaluation"
        else "",
    }
    metadata_errors: list[str] = []
    validate_proposal_public_metadata(proposal, direction=direction, errors=metadata_errors)
    if metadata_errors:
        for error in metadata_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for error in mutable_run_file_errors(proposal_path, label="proposal.yml"):
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    write_yaml(proposal_path, proposal)
    append_jsonl(
        run_dir / "proposals.jsonl",
        proposal_ledger_record(
            run_id=run_id,
            direction=direction,
            candidate_id=candidate_id,
            proposal_path=proposal_path,
            run_dir=run_dir,
            status=status,
            prompt_path=prompt_path,
            policy_path=policy_path,
            context_path=context_path,
            patch_sha256=patch_sha,
        ),
    )
    print(f"proposal_path: {proposal_path}")
    print(f"status: {status}")
    if proposal["evaluation_command"]:
        print(f"evaluation_command: {proposal['evaluation_command']}")
    for error in validation_errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if validation_errors else 0


def invalid_candidate_output(
    *,
    root: Path,
    direction: dict[str, Any],
    run_id: str,
    candidate_id: str,
    candidate_dir: Path,
    patch_path: Path,
    errors: list[str],
    case_id: str,
    why: str,
    next_hypothesis: str,
) -> dict[str, Any]:
    stdout_path = candidate_dir / "stdout.log"
    stderr_path = candidate_dir / "stderr.log"
    stdout_path.write_text("", encoding="utf-8")
    stderr_path.write_text(
        "strategy-search invalid candidate: boundary validation failed\n"
        + "\n".join(errors)
        + ("\n" if errors else ""),
        encoding="utf-8",
    )
    started_at = utc_now()
    finished_at = started_at
    trace = candidate_trace_record(
        direction=direction,
        run_id=run_id,
        candidate_id=candidate_id,
        base_commit=direction["base_ref"],
        patch_path=patch_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        verdict="invalid",
        score=0.0,
        exit_code=-1,
        case_results=[{"case_id": case_id, "status": "fail"}],
        timed_out=False,
        why=why,
        next_hypothesis=next_hypothesis,
        created_at=finished_at,
    )
    trace_path = write_candidate_trace(candidate_dir, trace, workspace_errors=errors)
    return candidate_record(
        root=root,
        direction=direction,
        candidate_id=candidate_id,
        run_id=run_id,
        base_commit=direction["base_ref"],
        patch_path=patch_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        trace_path=trace_path,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=-1,
        score=0.0,
        case_results=[{"case_id": case_id, "status": "fail"}],
        verdict="invalid",
        closure=closure_digest_record(root, direction, commit=direction["base_ref"]),
    )


def evaluate_candidate(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    try:
        run_dir, run_meta, direction = load_run(root, args.run)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    run_id = run_meta.get("run_id", run_dir.name)
    if not isinstance(run_id, str):
        errors.append("run.yml run_id must be a string")
        run_id = run_dir.name
    proposal: dict[str, Any] | None = None
    proposal_path: Path | None = None
    if args.patch and args.proposal:
        errors.append("eval accepts either --patch or --proposal, not both")
    if not args.patch and not args.proposal:
        errors.append("eval requires --patch or --proposal")
    if args.proposal:
        proposal_path = Path(os.path.abspath(os.path.normpath(run_path(root, args.proposal))))
        try:
            proposal_path.resolve(strict=False).relative_to(run_dir.resolve(strict=False))
        except ValueError:
            errors.append("proposal.yml must be inside the search run directory")
        if path_component_has_symlink(root, proposal_path):
            errors.append("proposal path must not contain symlinks")
        for error in mutable_run_file_errors(proposal_path, label="proposal.yml"):
            errors.append(error)
        if not errors:
            try:
                proposal = load_yaml_mapping(proposal_path)
            except StrategySearchError as exc:
                errors.append(str(exc))
        if proposal is not None:
            if proposal.get("status") == "awaiting_patch":
                pending_candidate_id = args.candidate_id or proposal.get("candidate_id")
                if args.candidate_id and args.candidate_id != proposal.get("candidate_id"):
                    errors.append("candidate_id must match proposal.candidate_id when --proposal is used")
                if isinstance(pending_candidate_id, str) and validate_run_id(
                    pending_candidate_id,
                    source="candidate_id",
                    errors=[],
                ) is not None:
                    pending_candidate_dir = run_dir / "candidates" / pending_candidate_id
                    if (pending_candidate_dir.exists() or pending_candidate_dir.is_symlink()) and not args.overwrite:
                        errors.append(f"candidate already exists: {pending_candidate_dir}")
                    elif path_component_has_symlink(root, pending_candidate_dir.parent):
                        errors.append("candidate output path must not contain symlinks")
                    if args.keep_worktree:
                        pending_worktree = run_dir / "worktrees" / pending_candidate_id
                        if (pending_worktree.exists() or pending_worktree.is_symlink()) and not args.overwrite:
                            errors.append(f"kept worktree already exists: {pending_worktree}")
                        elif path_component_has_symlink(root, pending_worktree.parent):
                            errors.append("kept worktree path must not contain symlinks")
                if not errors:
                    proposal, seal_errors = seal_awaiting_proposal_for_eval(
                        proposal,
                        root=root,
                        run_dir=run_dir,
                        run_meta=run_meta,
                        direction=direction,
                        proposal_path=proposal_path,
                    )
                    errors.extend(seal_errors)
            if not errors:
                errors.extend(
                    validate_proposal_for_eval(
                        proposal,
                        root=root,
                        run_dir=run_dir,
                        run_meta=run_meta,
                        direction=direction,
                        proposal_path=proposal_path,
                    )
                )
    candidate_id = (
        args.candidate_id
        or (proposal.get("candidate_id") if isinstance(proposal, dict) else None)
        or next_candidate_id(run_dir)
    )
    validate_run_id(candidate_id, source="candidate_id", errors=errors)
    if proposal is not None and args.candidate_id and args.candidate_id != proposal.get("candidate_id"):
        errors.append("candidate_id must match proposal.candidate_id when --proposal is used")
    if proposal_path is not None:
        source_patch = proposal_path.parent / "patch.diff"
    elif args.patch:
        source_patch = run_path(root, args.patch)
    else:
        source_patch = root / ".harness" / "missing-patch.diff"
    if proposal_path is None:
        errors.extend(patch_source_errors(root, source_patch))
    if not source_patch.is_file():
        errors.append(f"patch does not exist: {source_patch}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.keep_worktree:
        pending_worktree = run_dir / "worktrees" / candidate_id
        if (pending_worktree.exists() or pending_worktree.is_symlink()) and not args.overwrite:
            print(f"ERROR: kept worktree already exists: {pending_worktree}", file=sys.stderr)
            return 1
        if path_component_has_symlink(root, pending_worktree.parent):
            print("ERROR: kept worktree path must not contain symlinks", file=sys.stderr)
            return 1

    candidate_dir = run_dir / "candidates" / candidate_id
    if (candidate_dir.exists() or candidate_dir.is_symlink()) and not args.overwrite:
        print(f"ERROR: candidate already exists: {candidate_dir}", file=sys.stderr)
        return 1
    if path_component_has_symlink(root, candidate_dir.parent):
        print("ERROR: candidate output path must not contain symlinks", file=sys.stderr)
        return 1
    if candidate_dir.is_symlink() and args.overwrite:
        candidate_dir.unlink()
    elif candidate_dir.exists() and args.overwrite:
        shutil.rmtree(candidate_dir)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    patch_path = candidate_dir / "patch.diff"
    shutil.copyfile(source_patch, patch_path)
    why = (
        args.why.strip()
        if isinstance(args.why, str) and args.why.strip()
        else (
            proposal.get("why")
            if isinstance(proposal, dict) and isinstance(proposal.get("why"), str) and proposal["why"].strip()
            else "manual candidate evaluation"
        )
    )

    boundary_errors = patch_boundary_errors(root, direction, patch_path)
    if boundary_errors:
        next_hypothesis = (
            args.next_hypothesis.strip()
            if isinstance(args.next_hypothesis, str) and args.next_hypothesis.strip()
            else (
                proposal.get("next_hypothesis")
                if isinstance(proposal, dict)
                and isinstance(proposal.get("next_hypothesis"), str)
                and proposal["next_hypothesis"].strip()
                else default_next_hypothesis("invalid")
            )
        )
        record = invalid_candidate_output(
            root=root,
            direction=direction,
            run_id=run_id,
            candidate_id=candidate_id,
            candidate_dir=candidate_dir,
            patch_path=patch_path,
            errors=boundary_errors,
            case_id="candidate-boundary",
            why=why,
            next_hypothesis=next_hypothesis,
        )
        write_yaml(candidate_dir / "score.yml", record)
        append_jsonl(run_dir / "scores.jsonl", record)
        for error in boundary_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    workspace_parent: tempfile.TemporaryDirectory[str] | None = None
    if args.keep_worktree:
        workspace = run_dir / "worktrees" / candidate_id
        if (workspace.exists() or workspace.is_symlink()) and not args.overwrite:
            print(f"ERROR: kept worktree already exists: {workspace}", file=sys.stderr)
            return 1
        if path_component_has_symlink(root, workspace.parent):
            print("ERROR: kept worktree path must not contain symlinks", file=sys.stderr)
            return 1
        if workspace.is_symlink() and args.overwrite:
            workspace.unlink()
        elif workspace.exists() and args.overwrite:
            shutil.rmtree(workspace)
    else:
        workspace_parent = tempfile.TemporaryDirectory(prefix="strategy-search-")
        workspace = Path(workspace_parent.name)

    stdout_text = ""
    stderr_text = ""
    exit_code = -1
    workspace_errors: list[str] = []
    apply_failed = False
    timed_out = False
    started_at = utc_now()
    try:
        export_commit_tree(root, direction["base_ref"], workspace)
        init_workspace_repo(workspace)
        apply_result = run_git(workspace, ["apply", str(patch_path)], check=False)
        if apply_result.returncode != 0:
            apply_failed = True
            stderr_text = "strategy-search invalid candidate: patch apply failed\n" + apply_result.stderr
            case_results = [{"case_id": "patch-apply", "status": "fail"}]
            score = 0.0
            verdict = "invalid"
        else:
            workspace_errors = workspace_boundary_errors(workspace, direction)
            for symlink_path in symlink_paths(workspace):
                workspace_errors.append(f"candidate workspace must not contain symlink: {symlink_path}")
            if workspace_errors:
                verdict = "invalid"
                stderr_text = (
                    "strategy-search invalid candidate: post-apply boundary failure\n"
                    + "\n".join(workspace_errors)
                    + "\n"
                )
                exit_code = -1
                score = 0.0
                case_results = [{"case_id": "post-apply-boundary", "status": "fail"}]
                closure = closure_digest_record_for_workspace(
                    root,
                    workspace,
                    direction,
                    base_commit=direction["base_ref"],
                )
            else:
                workspace_digest_before_eval = filesystem_digest(workspace, exclude_roots=[workspace / ".git"])
                source_excludes = [run_dir]
                root_digest_before_eval = filesystem_digest(root, exclude_roots=source_excludes, skip_git=False)
                source_git_metadata_before_eval = source_git_metadata_digest(root)
                run_store_digest_before_eval = filesystem_digest(run_dir, skip_git=False)
                root_snapshot_before_eval = capture_filesystem_snapshot(root, exclude_roots=source_excludes, skip_git=False)
                git_metadata_snapshot_before_eval = capture_git_metadata_snapshot(root)
                run_store_snapshot_before_eval = capture_filesystem_snapshot(run_dir, skip_git=False)
                evaluator = direction["evaluator"]
                argv = shlex.split(evaluator["command"])
                timeout_seconds = evaluator["timeout_seconds"]
                stdout_text, stderr_text, exit_code, timed_out = run_evaluator_process(
                    argv,
                    cwd=workspace,
                    source_root=root,
                    timeout_seconds=timeout_seconds,
                )
                settle_after_evaluator_exit()
                parsed_score = parse_score(stdout_text, stderr_text, exit_code)
                parsed_case_results = parse_case_results(stdout_text, stderr_text, exit_code)
                score = parsed_score if parsed_score is not None else 0.0
                case_results = parsed_case_results or [{"case_id": "evaluator-output", "status": "fail"}]
                workspace_errors = workspace_boundary_errors(workspace, direction)
                if not timed_out:
                    workspace_errors.extend(evaluator_output_errors(stdout_text, stderr_text))
                if filesystem_digest(workspace, exclude_roots=[workspace / ".git"]) != workspace_digest_before_eval:
                    workspace_errors.append("candidate workspace changed after patch application")
                source_git_metadata_changed = source_git_metadata_digest(root) != source_git_metadata_before_eval
                if filesystem_digest(root, exclude_roots=source_excludes, skip_git=False) != root_digest_before_eval:
                    restore_filesystem_snapshot(root, root_snapshot_before_eval, exclude_roots=source_excludes, skip_git=False)
                    workspace_errors.append("candidate evaluation dirtied the source repository outside the run store")
                if source_git_metadata_changed:
                    restore_git_metadata_snapshot(root, git_metadata_snapshot_before_eval)
                    workspace_errors.append("candidate evaluation dirtied source repository git metadata")
                if filesystem_digest(run_dir, skip_git=False) != run_store_digest_before_eval:
                    restore_filesystem_snapshot(run_dir, run_store_snapshot_before_eval, skip_git=False)
                    workspace_errors.append("candidate evaluation dirtied the search run store")
                for symlink_path in symlink_paths(workspace):
                    workspace_errors.append(f"candidate workspace must not contain symlink: {symlink_path}")
                closure = closure_digest_record_for_workspace(
                    root,
                    workspace,
                    direction,
                    base_commit=direction["base_ref"],
                )
                for group, item in closure.items():
                    if item["before_sha256"] != item["after_sha256"]:
                        workspace_errors.append(f"evaluator_closure.{group} changed during candidate evaluation")
                if workspace_errors:
                    verdict = "invalid"
                    stderr_text += (
                        "\nstrategy-search invalid candidate: evaluator boundary failure\n"
                        + "\n".join(workspace_errors)
                        + "\n"
                    )
                elif timed_out:
                    verdict = "fail"
                else:
                    verdict = candidate_verdict(direction, exit_code=exit_code, score=score, case_results=case_results)

        if apply_failed:
            closure = closure_digest_record(root, direction, commit=direction["base_ref"])
        finished_at = utc_now()
        stdout_path = candidate_dir / "stdout.log"
        stderr_path = candidate_dir / "stderr.log"
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        next_hypothesis = (
            args.next_hypothesis.strip()
            if isinstance(args.next_hypothesis, str) and args.next_hypothesis.strip()
            else (
                proposal.get("next_hypothesis")
                if isinstance(proposal, dict)
                and isinstance(proposal.get("next_hypothesis"), str)
                and proposal["next_hypothesis"].strip()
                else default_next_hypothesis(verdict)
            )
        )
        trace = candidate_trace_record(
            direction=direction,
            run_id=run_id,
            candidate_id=candidate_id,
            base_commit=direction["base_ref"],
            patch_path=patch_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            verdict=verdict,
            score=score,
            exit_code=exit_code,
            case_results=case_results,
            timed_out=timed_out,
            why=why,
            next_hypothesis=next_hypothesis,
            created_at=finished_at,
        )
        trace_path = write_candidate_trace(
            candidate_dir,
            trace,
            keep_worktree=workspace if args.keep_worktree else None,
            workspace_errors=workspace_errors,
            apply_failed=apply_failed,
        )
        record = candidate_record(
            root=root,
            direction=direction,
            candidate_id=candidate_id,
            run_id=run_id,
            base_commit=direction["base_ref"],
            patch_path=patch_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            trace_path=trace_path,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=exit_code,
            score=score,
            case_results=case_results,
            verdict=verdict,
            closure=closure,
        )
        write_yaml(candidate_dir / "score.yml", record)
        append_jsonl(run_dir / "scores.jsonl", record)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if workspace_parent is not None:
            workspace_parent.cleanup()

    print(f"candidate_id: {candidate_id}")
    print(f"score: {score}")
    print(f"verdict: {verdict}")
    print(f"score_path: {candidate_dir / 'score.yml'}")
    return 0 if verdict == "pass" else 1


def trace_ref_for_score(run_dir: Path, score_path: Path) -> str:
    return (score_path.parent / "trace.yml").relative_to(run_dir).as_posix()


def candidate_trace_ref(run_dir: Path, candidate_id: object) -> str | None:
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        return None
    return f"candidates/{candidate_id}/trace.yml"


def recurring_failure_entries(run_dir: Path, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("verdict") != "fail" or record.get("validation_errors"):
            continue
        for case_result in record.get("case_results", []):
            if not isinstance(case_result, dict) or case_result.get("status") != "fail":
                continue
            case_id = case_result.get("case_id")
            if not isinstance(case_id, str) or not case_id.strip():
                continue
            by_case.setdefault(case_id, []).append(record)

    entries: list[dict[str, Any]] = []
    for case_id, case_records in sorted(by_case.items()):
        unique_candidates = [
            candidate_id
            for candidate_id in dict.fromkeys(record.get("candidate_id") for record in case_records)
            if isinstance(candidate_id, str) and candidate_id.strip()
        ]
        if len(unique_candidates) < 2:
            continue
        trace_refs = [
            trace_ref
            for trace_ref in dict.fromkeys(record.get("_trace_ref") for record in case_records)
            if isinstance(trace_ref, str) and trace_ref.strip()
        ]
        entries.append(
            {
                "search_id": f"recurring-failure-{safe_slug(case_id)}",
                "kind": "recurring_candidate_failure",
                "case_id": case_id,
                "candidate_ids": unique_candidates,
                "trace_refs": trace_refs,
                "hypothesis": (
                    f"Candidate attempts repeatedly failed {case_id}; inspect trace refs "
                    "and propose a narrower next search attempt."
                ),
            }
        )
    return entries


def write_search_set(run_dir: Path, run_id: str, records: list[dict[str, Any]]) -> Path:
    search_set = {
        "schema_version": SEARCH_SET_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": utc_now(),
        "evidence_status": "diagnostic_only",
        "entries": recurring_failure_entries(run_dir, records),
        "notes": [
            "Generated from repeated candidate failures.",
            "This file is search guidance only, not archive/v2 evidence.",
        ],
    }
    path = run_dir / "search-set.yml"
    errors = mutable_run_file_errors(path, label="search-set.yml")
    if errors:
        raise StrategySearchError("; ".join(errors))
    write_yaml_atomic(path, search_set)
    return path


def repo_relative_ref(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def selection_output_prefix(root: Path, run_dir: Path, value: str | None, *, candidate_id: str) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    if value is None or not value.strip():
        prefix_path = run_dir / "selections" / safe_slug(candidate_id)
    else:
        if value.strip().endswith(("/", "\\")):
            errors.append("output_prefix must be a file prefix, not a directory")
        prefix = repo_relative_path(value, source="output_prefix", errors=errors)
        prefix_path = root / prefix if prefix else None
    if prefix_path is None:
        return None, errors
    if prefix_path.exists() and prefix_path.is_dir():
        errors.append("output_prefix must be a file prefix, not a directory")
    try:
        prefix_path.resolve().relative_to(run_dir.resolve())
    except ValueError:
        errors.append("output_prefix must stay inside the diagnostic search run directory")
    try:
        rel = repo_relative_ref(root, prefix_path)
    except ValueError:
        rel = str(prefix_path)
    if rel.startswith(ARCHIVE_ARTIFACT_PREFIX):
        errors.append("strategy-search select is diagnostic-only and must not write archive/v2 artifacts")
    if prefix_path.name in {"", "."} or str(prefix_path).endswith("/"):
        errors.append("output_prefix must be a file prefix, not a directory")
    return prefix_path, errors


def selection_artifact_targets(prefix: Path) -> dict[str, Path]:
    return {
        "selection": prefix.with_name(f"{prefix.name}-selection.yml"),
        "summary": prefix.with_name(f"{prefix.name}-summary.yml"),
    }


def output_target_errors(root: Path, run_dir: Path, targets: dict[str, Path], *, overwrite: bool) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    allowed_targets = set(targets.values())
    prefix = next(iter(targets.values())).with_name(next(iter(targets.values())).name.rsplit("-", 1)[0]) if targets else None
    if prefix is not None and prefix.parent.exists():
        if prefix.parent.is_symlink():
            errors.append(f"output parent must not be a symlink: {prefix.parent}")
        elif not prefix.parent.is_dir():
            errors.append(f"output parent must be a directory: {prefix.parent}")
        else:
            for sibling in prefix.parent.iterdir():
                if sibling.name.startswith(f"{prefix.name}-") and sibling not in allowed_targets:
                    errors.append(f"stale diagnostic selection sibling is not allowed for this prefix: {sibling}")
    for label, path in targets.items():
        try:
            rel_path = repo_relative_ref(root, path)
        except ValueError:
            errors.append(f"{label} output must be inside repository root: {path}")
            continue
        if rel_path in seen:
            errors.append(f"duplicate output target: {rel_path}")
        seen.add(rel_path)
        try:
            path.resolve().relative_to(run_dir.resolve())
        except ValueError:
            errors.append(f"{label} output must stay inside the diagnostic search run directory: {rel_path}")
        if rel_path.startswith(ARCHIVE_ARTIFACT_PREFIX):
            errors.append(f"{label} output must not be under archive/v2/artifacts/: {rel_path}")
        for parent in path.parents:
            if parent == root or parent == root.parent:
                break
            if parent.is_symlink():
                errors.append(f"{label} output parent must not be a symlink: {parent}")
        if path.is_symlink():
            errors.append(f"{label} output must not be a symlink: {path}")
        if path.is_dir():
            errors.append(f"{label} output must not be a directory: {path}")
        if path.exists() and not path.is_symlink() and path.is_file() and path.stat().st_nlink > 1:
            errors.append(f"{label} output must not be a hard link: {path}")
        if (path.exists() or path.is_symlink()) and not overwrite:
            errors.append(f"{label} output already exists; use --overwrite: {path}")
    return errors


def selection_source_files(candidate_dir: Path) -> dict[str, Path]:
    return {
        "score": candidate_dir / "score.yml",
        "patch": candidate_dir / "patch.diff",
        "stdout": candidate_dir / "stdout.log",
        "stderr": candidate_dir / "stderr.log",
        "trace": candidate_dir / "trace.yml",
    }


def candidate_source_errors(root: Path, candidate_dir: Path) -> list[str]:
    errors: list[str] = []
    for label, source_path in selection_source_files(candidate_dir).items():
        errors.extend(source_path_symlink_errors(root, source_path, label=label))
        errors.extend(mutable_run_file_errors(source_path, label=f"selected candidate {label}"))
        if not source_path.is_file():
            errors.append(f"selected candidate is missing {label}: {source_path}")
    return errors


def selection_trace_public_errors(trace: dict[str, Any], direction: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("why", "next_hypothesis"):
        value = trace.get(field)
        if isinstance(value, str):
            validate_no_forbidden_public_tokens(
                value,
                source=f"selected candidate trace.{field}",
                direction=direction,
                errors=errors,
            )
    return errors


def source_path_symlink_errors(root: Path, source_path: Path, *, label: str) -> list[str]:
    errors: list[str] = []
    if ".." in source_path.parts:
        errors.append(f"selected candidate {label} path must not contain '..': {source_path}")
        return errors
    try:
        source_path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        errors.append(f"selected candidate {label} must be inside repository root: {source_path}")
        return errors
    if path_component_has_symlink(root, source_path):
        errors.append(f"selected candidate {label} path must not contain a symlink: {source_path}")
    return errors


def immediate_candidate_dirs(root: Path, run_dir: Path) -> list[Path]:
    candidates_dir = run_dir / "candidates"
    if path_component_has_symlink(root, candidates_dir) or not candidates_dir.is_dir():
        return []
    return sorted(candidates_dir.iterdir(), key=lambda path: path.name)


def case_result_counts(candidate: dict[str, Any]) -> dict[str, int]:
    counts = {status: 0 for status in sorted(VALID_CASE_STATUSES)}
    case_results = candidate.get("case_results")
    if not isinstance(case_results, list):
        return counts
    for item in case_results:
        if isinstance(item, dict) and item.get("status") in counts:
            counts[item["status"]] += 1
    return counts


def selection_manifest(
    *,
    root: Path,
    run_dir: Path,
    run_meta: dict[str, Any],
    direction: dict[str, Any],
    candidate: dict[str, Any],
    trace: dict[str, Any],
    targets: dict[str, Path],
    allow_nonpass: bool,
    reason: str,
) -> dict[str, Any]:
    changed_paths = trace.get("changed_paths") if isinstance(trace.get("changed_paths"), list) else []
    diagnostic_outputs = [
        {
            "kind": kind,
            "ref": repo_relative_ref(root, targets[kind]),
            "sha256": file_sha256(targets[kind]),
        }
        for kind in ("summary",)
        if targets[kind].is_file()
    ]
    return {
        "schema_version": ADOPTION_SCHEMA_VERSION,
        "run_id": run_meta.get("run_id", run_dir.name),
        "candidate_id": candidate.get("candidate_id"),
        "selected_at": utc_now(),
        "evidence_status": "diagnostic_only",
        "diagnostic_source": "strategy-search run-store records are diagnostic-only and are not archive evidence",
        "direction": {
            "base_ref": direction.get("base_ref"),
            "direction_digest": digest_direction(direction),
        },
        "candidate": {
            "verdict": candidate.get("verdict"),
            "score": candidate.get("score"),
            "exit_code": candidate.get("exit_code"),
            "case_result_counts": case_result_counts(candidate),
            "changed_path_count": len(changed_paths),
            "why": trace.get("why"),
            "next_hypothesis": trace.get("next_hypothesis"),
            "nonpass_selected": allow_nonpass,
            "selection_reason": reason,
        },
        "governance": {
            "selected_for_adoption": True,
            "stable_handoff_eligible": False,
            "search_pass_is_not_governance_pass": True,
            "requires_content_commit": True,
            "requires_acceptance_packet": True,
            "requires_active_pointer_publication": True,
            "release_verification_remains_final_gate": True,
            "protected_or_high_risk_review": "determined by v2 governance inference after the content commit",
        },
        "diagnostic_outputs": diagnostic_outputs,
        "notes": [
            "This artifact records a selected strategy-search candidate for adoption.",
            "It is diagnostic run-store output, not archive/v2 evidence and not stable handoff.",
            "Raw score, stdout, stderr, trace, and patch files remain diagnostic run-store history.",
            "Apply the patch in a content commit, then use the v2 AcceptancePacket and active pointer flow.",
        ],
    }


def selected_candidate_summary(
    *,
    direction: dict[str, Any],
    candidate: dict[str, Any],
    trace: dict[str, Any],
    allow_nonpass: bool,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": SELECTED_SUMMARY_SCHEMA_VERSION,
        "candidate_id": candidate.get("candidate_id"),
        "direction_digest": digest_direction(direction),
        "evidence_status": "diagnostic_only",
        "verdict": candidate.get("verdict"),
        "score": candidate.get("score"),
        "exit_code": candidate.get("exit_code"),
        "changed_path_count": len(trace.get("changed_paths") if isinstance(trace.get("changed_paths"), list) else []),
        "why": trace.get("why"),
        "next_hypothesis": trace.get("next_hypothesis"),
        "case_result_counts": case_result_counts(candidate),
        "residual_risks": [
            "Search output is diagnostic only; stable handoff starts from the adopted content commit and v2 packet flow.",
            *(
                [f"Selected non-pass candidate: {reason}"]
                if allow_nonpass
                else []
            ),
        ],
    }


def select_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    try:
        run_dir, run_meta, direction = load_run(root, args.run)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    errors = validate_direction(direction, root=root)
    candidate_id = args.candidate
    if validate_run_id(candidate_id, source="candidate", errors=errors) is None:
        candidate_id = "invalid"
    if args.allow_nonpass and (not isinstance(args.reason, str) or not args.reason.strip()):
        errors.append("--allow-nonpass requires --reason")
    reason = args.reason.strip() if isinstance(args.reason, str) and args.reason.strip() else "candidate passed evaluator"
    validate_no_forbidden_public_tokens(
        reason,
        source="selection reason",
        direction=direction,
        errors=errors,
    )
    candidate_dir = run_dir / "candidates" / candidate_id
    score_path = candidate_dir / "score.yml"
    trace_path = candidate_dir / "trace.yml"
    errors.extend(candidate_source_errors(root, candidate_dir))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    try:
        candidate = load_yaml_mapping(score_path)
        trace = load_yaml_mapping(trace_path)
    except StrategySearchError as exc:
        errors.append(str(exc))
        candidate = {}
        trace = {}
    if candidate:
        errors.extend(validate_candidate(candidate, direction=direction, root=root, candidate_path=score_path))
        if candidate.get("verdict") == "invalid":
            errors.append("invalid candidates cannot be selected for adoption")
        elif candidate.get("verdict") != "pass" and not args.allow_nonpass:
            errors.append("candidate verdict must be pass for adoption selection unless --allow-nonpass --reason is used")
    if trace and candidate:
        trace_errors: list[str] = []
        validate_trace_record(
            trace,
            candidate=candidate,
            direction=direction,
            candidate_path=score_path,
            patch_path=candidate_dir / "patch.diff",
            errors=trace_errors,
        )
        errors.extend(trace_errors)
        errors.extend(selection_trace_public_errors(trace, direction))
    run_id = run_meta.get("run_id", run_dir.name)
    prefix, prefix_errors = selection_output_prefix(root, run_dir, args.output_prefix, candidate_id=candidate_id)
    errors.extend(prefix_errors)
    targets = selection_artifact_targets(prefix) if prefix else {}
    if targets:
        errors.extend(output_target_errors(root, run_dir, targets, overwrite=args.overwrite))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    targets["summary"].parent.mkdir(parents=True, exist_ok=True)
    write_yaml_atomic(
        targets["summary"],
        selected_candidate_summary(
            direction=direction,
            candidate=candidate,
            trace=trace,
            allow_nonpass=args.allow_nonpass,
            reason=reason,
        ),
    )
    manifest = selection_manifest(
        root=root,
        run_dir=run_dir,
        run_meta=run_meta,
        direction=direction,
        candidate=candidate,
        trace=trace,
        targets=targets,
        allow_nonpass=args.allow_nonpass,
        reason=reason,
    )
    write_yaml_atomic(targets["selection"], manifest)
    print(f"selection_path: {targets['selection']}")
    print(f"selection_ref: {repo_relative_ref(root, targets['selection'])}")
    for artifact in manifest["diagnostic_outputs"]:
        print(f"{artifact['kind']}_ref: {artifact['ref']}")
    print("stable_handoff_eligible: false")
    print("evidence_status: diagnostic_only")
    return 0


def summarize_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    try:
        run_dir, run_meta, _direction = load_run(root, args.run)
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    records: list[dict[str, Any]] = []
    for candidate_dir in immediate_candidate_dirs(root, run_dir):
        candidate_id = candidate_dir.name
        if candidate_dir.is_symlink():
            records.append(
                {
                    "candidate_id": candidate_id,
                    "verdict": "invalid",
                    "score": 0.0,
                    "exit_code": -1,
                    "trace_ref": candidate_trace_ref(run_dir, candidate_id),
                    "validation_errors": [f"candidate directory must not be a symlink: {candidate_dir}"],
                }
            )
            continue
        if not candidate_dir.is_dir():
            continue
        score_path = candidate_dir / "score.yml"
        source_errors = candidate_source_errors(root, candidate_dir)
        if source_errors:
            records.append(
                {
                    "candidate_id": candidate_id,
                    "verdict": "invalid",
                    "score": 0.0,
                    "exit_code": -1,
                    "trace_ref": candidate_trace_ref(run_dir, candidate_id),
                    "validation_errors": source_errors,
                }
            )
            continue
        try:
            record = load_yaml_mapping(score_path)
        except StrategySearchError:
            continue
        validation_errors = validate_candidate(record, direction=_direction, root=root, candidate_path=score_path)
        if validation_errors:
            record = {
                **record,
                "verdict": "invalid",
                "validation_errors": validation_errors,
            }
        record["_score_path"] = score_path
        record["_trace_ref"] = trace_ref_for_score(run_dir, score_path)
        records.append(record)
    def sort_score(item: dict[str, Any]) -> float:
        try:
            return float(item.get("score", 0.0))
        except (TypeError, ValueError):
            return float("-inf")

    records.sort(key=lambda item: (item.get("verdict") != "pass", -sort_score(item)))
    counts = {verdict: sum(1 for item in records if item.get("verdict") == verdict) for verdict in sorted(VALID_VERDICTS)}
    summary = {
        "schema_version": "strategy-search-summary/v1",
        "run_id": run_meta.get("run_id", run_dir.name),
        "generated_at": utc_now(),
        "evidence_status": "diagnostic_only",
        "counts": counts,
        "candidates": [
            {
                "candidate_id": item.get("candidate_id"),
                "verdict": item.get("verdict"),
                "score": item.get("score"),
                "exit_code": item.get("exit_code"),
                "trace_ref": (
                    item.get("_trace_ref")
                    if isinstance(item.get("_trace_ref"), str)
                    else candidate_trace_ref(run_dir, item.get("candidate_id"))
                ),
                "trace_sha256": item.get("trace_sha256"),
                **({"validation_errors": item["validation_errors"]} if "validation_errors" in item else {}),
            }
            for item in records
        ],
        "notes": [
            "This summary ranks strategy-search candidates only.",
            "It is not archive/v2 evidence; adopt by applying the patch in a content commit.",
        ],
    }
    for item in records:
        item.pop("_score_path", None)
    summary_path = run_dir / "summary.yml"
    output_errors = mutable_run_file_errors(summary_path, label="summary.yml")
    if args.write_search_set:
        output_errors.extend(mutable_run_file_errors(run_dir / "search-set.yml", label="search-set.yml"))
    if output_errors:
        for error in output_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    try:
        search_set_path = write_search_set(run_dir, summary["run_id"], records) if args.write_search_set else None
    except StrategySearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for item in records:
        item.pop("_trace_ref", None)
    write_yaml_atomic(summary_path, summary)
    print(f"run_id: {summary['run_id']}")
    for item in summary["candidates"]:
        print(
            f"{item['candidate_id']}: verdict={item['verdict']} score={item['score']} "
            f"exit_code={item['exit_code']} trace={item['trace_ref']}"
        )
    print(f"summary_path: {summary_path}")
    if search_set_path is not None:
        print(f"search_set_path: {search_set_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--direction", required=True)
    start_parser.add_argument("--run-id")
    start_parser.add_argument("--overwrite", action="store_true")
    start_parser.set_defaults(func=start_command)

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--run", required=True, help="Path to the .harness/search-runs/<run-id> directory.")
    eval_parser.add_argument("--patch", help="Evaluate a candidate patch file directly.")
    eval_parser.add_argument(
        "--proposal",
        help=(
            "Evaluate a stored proposal.yml bundle produced by propose. "
            "For awaiting_patch bundles, save the diff as patch.diff beside proposal.yml first; eval seals it."
        ),
    )
    eval_parser.add_argument("--candidate-id", help="Candidate id for direct --patch evaluation; defaults to the next cand-NNN.")
    eval_parser.add_argument("--why", help="Record why this candidate is being tried in trace.yml.")
    eval_parser.add_argument("--next-hypothesis", help="Record the next search hypothesis after this candidate.")
    eval_parser.add_argument("--keep-worktree", action="store_true", help="Keep the temporary candidate worktree for inspection.")
    eval_parser.add_argument("--overwrite", action="store_true", help="Replace an existing candidate directory.")
    eval_parser.set_defaults(func=evaluate_candidate)

    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("--run", required=True)
    summarize_parser.add_argument(
        "--write-search-set",
        action="store_true",
        help="Write diagnostic-only search-set.yml entries from recurring validated evaluator failures.",
    )
    summarize_parser.set_defaults(func=summarize_command)

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--run", required=True, help="Path to the .harness/search-runs/<run-id> directory.")
    select_parser.add_argument("--candidate", required=True, help="Candidate id to record as a diagnostic selection.")
    select_parser.add_argument(
        "--output-prefix",
        help=(
            "Repository-relative diagnostic output prefix inside the selected .harness/search-runs/<run-id>/ "
            "directory; defaults to .harness/search-runs/<run-id>/selections/<candidate>."
        ),
    )
    select_parser.add_argument(
        "--allow-nonpass",
        action="store_true",
        help="Record a non-pass candidate only when --reason explains why it is still worth considering.",
    )
    select_parser.add_argument("--reason", default="", help="Human selection reason for non-pass or risk-bearing choices.")
    select_parser.add_argument("--overwrite", action="store_true", help="Replace existing diagnostic selection files.")
    select_parser.set_defaults(func=select_command)

    propose_parser = subparsers.add_parser("propose")
    propose_parser.add_argument("--run", required=True, help="Path to the .harness/search-runs/<run-id> directory.")
    propose_parser.add_argument("--candidate-id", help="Proposal/candidate id; defaults to the next cand-NNN.")
    propose_parser.add_argument(
        "--patch",
        help=(
            "Store a generated candidate patch in the proposal bundle before eval. "
            "Without --patch, save the returned diff as proposals/<candidate-id>/patch.diff before eval --proposal."
        ),
    )
    propose_parser.add_argument("--why", help="Record why this proposer patch is being tried.")
    propose_parser.add_argument("--next-hypothesis", help="Record the next hypothesis to carry into candidate trace.yml.")
    propose_parser.add_argument("--overwrite", action="store_true", help="Replace an existing proposal bundle.")
    propose_parser.set_defaults(func=propose_command)

    direction_parser = subparsers.add_parser("validate-direction")
    direction_parser.add_argument("--direction", required=True)
    direction_parser.set_defaults(func=validate_direction_command)

    candidate_parser = subparsers.add_parser("validate-candidate")
    candidate_parser.add_argument("--direction", required=True)
    candidate_parser.add_argument("--candidate", required=True)
    candidate_parser.add_argument("--patch")
    candidate_parser.set_defaults(func=validate_candidate_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
