#!/usr/bin/env python3
"""Check a user's installed Claude profile against a small governance manifest.

This checker is for the user-global Claude layer, not this repository's v2
governance archive. It verifies only the files explicitly named by the manifest:
canonical rule mirrors, settings hook contracts, and stale model identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_VERSION = "claude-profile-governance/v1"
DEFAULT_MANIFEST = Path("harness/profile-governance.json")
IGNORED_NAMES = {".DS_Store"}


class ProfileDriftError(ValueError):
    pass


def default_claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_HOME", "~/.claude")).expanduser()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProfileDriftError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileDriftError(f"invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ProfileDriftError(f"cannot read {path}: {exc}") from exc


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProfileDriftError(f"{label} must be a JSON object")
    return value


def string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileDriftError(f"{label} must be a list of strings")
    return value


def mapping_list(value: Any, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ProfileDriftError(f"{label} must be a list of objects")
    return value


def resolve_profile_path(claude_home: Path, raw: str, label: str) -> Path:
    if not raw.strip():
        raise ProfileDriftError(f"{label} path is empty")
    path = Path(raw).expanduser()
    candidate = path if path.is_absolute() else claude_home / path
    resolved_home = claude_home.resolve()
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_home)
    except ValueError as exc:
        raise ProfileDriftError(
            f"{label}: path {raw!r} must stay under Claude home {resolved_home}"
        ) from exc
    return resolved_candidate


def resolve_source_path(claude_home: Path, source_root: Path, raw: str, label: str) -> Path:
    if not raw.strip():
        raise ProfileDriftError(f"{label} canonical_source is empty")
    if raw.startswith("repo:"):
        relative = raw[len("repo:") :]
        if not relative:
            raise ProfileDriftError(f"{label} repo: canonical_source is empty")
        resolved_root = source_root.resolve()
        resolved_candidate = (source_root / relative).resolve(strict=False)
        try:
            resolved_candidate.relative_to(resolved_root)
        except ValueError as exc:
            raise ProfileDriftError(
                f"{label}: repo: canonical_source {raw!r} must stay under {resolved_root}"
            ) from exc
        return resolved_candidate
    return resolve_profile_path(claude_home, raw, label)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise ProfileDriftError(f"{label}: missing file {path}") from exc
    except OSError as exc:
        raise ProfileDriftError(f"{label}: cannot read {path}: {exc}") from exc


def validate_rule_mirrors(
    manifest: dict[str, Any],
    *,
    claude_home: Path,
    source_root: Path,
) -> list[str]:
    errors: list[str] = []
    entries: list[tuple[str, dict[str, Any]]] = []
    entries.extend(
        (f"mirrors[{index}]", mirror)
        for index, mirror in enumerate(mapping_list(manifest.get("mirrors"), "mirrors"), start=1)
    )
    entries.extend(
        (f"rules[{index}]", rule)
        for index, rule in enumerate(mapping_list(manifest.get("rules"), "rules"), start=1)
    )
    for label, rule in entries:
        path_value = rule.get("path")
        if not isinstance(path_value, str):
            errors.append(f"{label}: missing string path")
            continue
        try:
            rule_path = resolve_profile_path(claude_home, path_value, label)
        except ProfileDriftError as exc:
            errors.append(str(exc))
            continue
        try:
            rule_bytes = read_bytes(rule_path, label)
        except ProfileDriftError as exc:
            errors.append(str(exc))
            continue
        expected_hash = rule.get("sha256")
        if expected_hash is not None:
            if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                errors.append(f"{label}: sha256 must be a 64-character hex string")
            elif sha256_bytes(rule_bytes) != expected_hash:
                errors.append(f"{label}: {path_value} does not match declared sha256")
        canonical_value = rule.get("canonical_source")
        if canonical_value is not None:
            if not isinstance(canonical_value, str):
                errors.append(f"{label}: canonical_source must be a string")
                continue
            try:
                canonical_path = resolve_source_path(
                    claude_home,
                    source_root,
                    canonical_value,
                    label,
                )
            except ProfileDriftError as exc:
                errors.append(str(exc))
                continue
            try:
                canonical_bytes = read_bytes(canonical_path, f"{label}.canonical_source")
            except ProfileDriftError as exc:
                errors.append(str(exc))
                continue
            if rule_bytes != canonical_bytes:
                errors.append(
                    f"{label}: {path_value} drifted from canonical_source {canonical_value}"
                )
    return errors


def existing_settings(
    manifest: dict[str, Any],
    *,
    claude_home: Path,
) -> dict[str, tuple[Path, dict[str, Any]]]:
    settings: dict[str, tuple[Path, dict[str, Any]]] = {}
    for raw in string_list(manifest.get("settings_paths", ["settings.json"]), "settings_paths"):
        path = resolve_profile_path(claude_home, raw, "settings_paths")
        if not path.exists():
            continue
        loaded = load_json(path)
        if not isinstance(loaded, dict):
            raise ProfileDriftError(f"{raw}: settings file must be a JSON object")
        settings[raw] = (path, loaded)
    return settings


def collect_hook_commands(value: Any) -> list[str]:
    """Return commands from Claude hook entries only.

    Expected shape is an event list of matcher records, each optionally carrying
    a `hooks` list whose entries include `{ "type": "command", "command": ... }`.
    Other nested `command` keys are metadata, not runnable hooks.
    """

    commands: list[str] = []
    if not isinstance(value, list):
        return commands
    for matcher_record in value:
        if not isinstance(matcher_record, dict):
            continue
        hook_entries = matcher_record.get("hooks")
        if not isinstance(hook_entries, list):
            continue
        for hook_entry in hook_entries:
            if not isinstance(hook_entry, dict):
                continue
            if hook_entry.get("type") != "command":
                continue
            command = hook_entry.get("command")
            if isinstance(command, str):
                commands.append(command)
    return commands


def hook_commands(settings: dict[str, Any], event: str) -> list[str] | None:
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return None
    if event not in hooks:
        return None
    return collect_hook_commands(hooks[event])


def validate_hook_contracts(
    manifest: dict[str, Any],
    *,
    claude_home: Path,
    settings_by_path: dict[str, tuple[Path, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    for index, contract in enumerate(
        mapping_list(manifest.get("hook_contracts"), "hook_contracts"),
        start=1,
    ):
        label = f"hook_contracts[{index}]"
        event = contract.get("event")
        if not isinstance(event, str) or not event.strip():
            errors.append(f"{label}: missing string event")
            continue
        required_fragments = string_list(contract.get("command_contains"), f"{label}.command_contains")
        if not required_fragments:
            errors.append(f"{label}: command_contains must contain at least one string")
            continue
        if any(not fragment.strip() for fragment in required_fragments):
            errors.append(f"{label}: command_contains entries must be non-empty strings")
            continue
        setting_names = string_list(contract.get("settings_paths"), f"{label}.settings_paths")
        if not setting_names:
            setting_names = list(settings_by_path)
        matched_commands: list[str] = []
        for setting_name in setting_names:
            if setting_name not in settings_by_path:
                continue
            _path, settings = settings_by_path[setting_name]
            commands = hook_commands(settings, event)
            if commands is not None:
                matched_commands.extend(commands)
        if not matched_commands:
            errors.append(f"{label}: hook event {event!r} is not present in configured settings")
        for fragment in required_fragments:
            if not any(fragment in command for command in matched_commands):
                errors.append(
                    f"{label}: hook event {event!r} has no command containing {fragment!r}"
                )
        declared_in = contract.get("declared_in")
        if declared_in is not None:
            if not isinstance(declared_in, str):
                errors.append(f"{label}: declared_in must be a string")
                continue
            doc_path = resolve_profile_path(claude_home, declared_in, label)
            try:
                doc_text = read_bytes(doc_path, f"{label}.declared_in").decode(
                    "utf-8",
                    errors="replace",
                )
            except ProfileDriftError as exc:
                errors.append(str(exc))
                continue
            if event not in doc_text:
                errors.append(f"{label}: {declared_in} does not mention hook event {event!r}")
            for fragment in required_fragments:
                if fragment not in doc_text:
                    errors.append(f"{label}: {declared_in} does not mention {fragment!r}")
    return errors


def iter_scan_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    files: list[Path] = []
    for child in sorted(path.rglob("*")):
        if child.is_file() and child.name not in IGNORED_NAMES:
            files.append(child)
    return files


def validate_blocked_model_ids(
    manifest: dict[str, Any],
    *,
    claude_home: Path,
) -> list[str]:
    blocked = string_list(manifest.get("blocked_model_ids"), "blocked_model_ids")
    if not blocked:
        return []
    scan_paths = string_list(manifest.get("scan_paths"), "scan_paths")
    if not scan_paths:
        scan_paths = ["settings.json", "settings.local.json", "rules", "docs", "commands", "skills"]
    errors: list[str] = []
    for raw in scan_paths:
        try:
            base = resolve_profile_path(claude_home, raw, "scan_paths")
        except ProfileDriftError as exc:
            errors.append(str(exc))
            continue
        for path in iter_scan_files(base):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                errors.append(f"blocked_model_ids: cannot read {path}: {exc}")
                continue
            for model_id in blocked:
                if model_id in text:
                    try:
                        rel = path.relative_to(claude_home).as_posix()
                    except ValueError:
                        rel = path.as_posix()
                    errors.append(f"blocked_model_ids: {rel} contains stale model id {model_id!r}")
    return errors


def validate_manifest(
    manifest: dict[str, Any],
    *,
    claude_home: Path,
    source_root: Path,
) -> list[str]:
    errors: list[str] = []
    schema = manifest.get("schema_version")
    if schema != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    try:
        settings_by_path = existing_settings(manifest, claude_home=claude_home)
    except ProfileDriftError as exc:
        settings_by_path = {}
        errors.append(str(exc))
    errors.extend(
        validate_rule_mirrors(
            manifest,
            claude_home=claude_home,
            source_root=source_root,
        )
    )
    errors.extend(
        validate_hook_contracts(
            manifest,
            claude_home=claude_home,
            settings_by_path=settings_by_path,
        )
    )
    errors.extend(validate_blocked_model_ids(manifest, claude_home=claude_home))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--claude-home",
        type=Path,
        default=default_claude_home(),
        help="Claude home directory, default: $CLAUDE_HOME or ~/.claude",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="manifest path, default: <claude-home>/harness/profile-governance.json",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT,
        help="repo source root used by repo: canonical_source entries",
    )
    parser.add_argument("--json", action="store_true", help="print JSON result")
    args = parser.parse_args(argv)

    claude_home = args.claude_home.expanduser().resolve()
    manifest_path = (
        args.manifest.expanduser().resolve(strict=False)
        if args.manifest
        else claude_home / DEFAULT_MANIFEST
    )
    source_root = args.source_root.expanduser().resolve()

    try:
        manifest = require_mapping(load_json(manifest_path), "manifest")
        errors = validate_manifest(manifest, claude_home=claude_home, source_root=source_root)
    except ProfileDriftError as exc:
        errors = [str(exc)]

    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "claude_home": claude_home.as_posix(),
                    "manifest": manifest_path.as_posix(),
                    "status": "pass" if not errors else "fail",
                    "errors": errors,
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif errors:
        for error in errors:
            print(error, file=sys.stderr)
    else:
        print("Claude profile drift check passed.")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
