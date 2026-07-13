#!/usr/bin/env python3
"""Validate the repository-local Codex plugin marketplace contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "adapters" / "codex" / "plugin-scope.md"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_MANIFEST_PATH = ROOT / "plugins" / "ai-agent-meta-harness" / ".codex-plugin" / "plugin.json"
PLUGIN_NAME = "ai-agent-meta-harness"
PLUGIN_SOURCE_PATH = "./plugins/ai-agent-meta-harness"

REQUIRED_POLICY_MARKERS = (
    "Marketplace publication ready: yes",
    "Official marketplace schema:",
    "Official marketplace taxonomy:",
    "Generated metadata source:",
    "python3 scripts/check-codex-marketplace-metadata.py --worktree",
)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _inside_git_worktree() -> bool:
    result = _git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path, *, use_index: bool) -> tuple[str, list[str]]:
    if use_index:
        relative = _relative(path)
        result = _git(["show", f":{relative}"])
        if result.returncode != 0:
            return "", [f"MISSING STAGED FILE: {relative}"]
        return result.stdout, []
    try:
        return path.read_text(encoding="utf-8"), []
    except OSError as exc:
        return "", [f"UNREADABLE FILE: {_relative(path)}: {exc}"]


def read_json_object(path: Path, *, use_index: bool) -> tuple[dict[str, Any] | None, list[str]]:
    text, errors = read_text(path, use_index=use_index)
    if errors:
        return None, errors
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"INVALID JSON: {_relative(path)}: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"INVALID JSON ROOT: {_relative(path)} must contain an object"]
    return payload, []


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in markers if marker not in normalized]


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_marketplace(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _non_empty_string(payload.get("name")):
        errors.append("marketplace name must be a non-empty string")

    interface = payload.get("interface")
    if not isinstance(interface, dict) or not _non_empty_string(interface.get("displayName")):
        errors.append("marketplace interface.displayName must be a non-empty string")

    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        return errors + ["marketplace plugins must be an array"]
    if len(plugins) != 1:
        return errors + ["marketplace plugins must contain exactly one entry"]

    matches = [entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME]
    if len(matches) != 1:
        return errors + [f"marketplace must contain exactly one {PLUGIN_NAME} entry"]

    entry = matches[0]
    source = entry.get("source")
    if not isinstance(source, dict):
        errors.append("plugin source must be an object")
    else:
        if source.get("source") != "local":
            errors.append("plugin source.source must be local")
        if source.get("path") != PLUGIN_SOURCE_PATH:
            errors.append(f"plugin source.path must be {PLUGIN_SOURCE_PATH}")

    policy = entry.get("policy")
    if not isinstance(policy, dict):
        errors.append("plugin policy must be an object")
    else:
        if policy.get("installation") != "AVAILABLE":
            errors.append("plugin policy.installation must be AVAILABLE")
        if policy.get("authentication") != "ON_INSTALL":
            errors.append("plugin policy.authentication must be ON_INSTALL")

    if entry.get("category") != "Productivity":
        errors.append("plugin category must be Productivity")
    return errors


def validate(*, use_index: bool = False) -> list[str]:
    errors: list[str] = []

    policy_text, policy_errors = read_text(POLICY_PATH, use_index=use_index)
    errors.extend(policy_errors)
    if not policy_errors:
        errors.extend(f"MISSING POLICY MARKER: {marker}" for marker in missing_markers(policy_text, REQUIRED_POLICY_MARKERS))

    marketplace, marketplace_errors = read_json_object(MARKETPLACE_PATH, use_index=use_index)
    errors.extend(marketplace_errors)
    if marketplace is not None:
        errors.extend(validate_marketplace(marketplace))

    plugin_manifest, plugin_errors = read_json_object(PLUGIN_MANIFEST_PATH, use_index=use_index)
    errors.extend(plugin_errors)
    if plugin_manifest is not None and plugin_manifest.get("name") != PLUGIN_NAME:
        errors.append(f"plugin manifest name must be {PLUGIN_NAME}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worktree",
        action="store_true",
        help="validate worktree files instead of the staged index",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    use_index = _inside_git_worktree() and not args.worktree
    errors = validate(use_index=use_index)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    mode = "worktree" if not use_index else "staged index"
    print(f"Codex marketplace metadata is valid ({mode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
