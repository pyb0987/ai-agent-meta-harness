#!/usr/bin/env python3
"""Smoke-test local Codex plugin marketplace activation.

This exercises the Codex CLI marketplace registration path in an isolated
CODEX_HOME. It does not enable runtime hook manifest fields; those remain gated
on separate tool-event coverage.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PLUGIN_NAME = "ai-agent-meta-harness"
MARKETPLACE_NAME = "local-ai-agent-meta-harness"
EXPECTED_SKILLS = (
    "autoresearch",
    "harness-engineer",
    "init-codex-harness",
    "multi-review",
)


def default_plugin_root() -> Path:
    script = Path(__file__).resolve()
    parts = script.parts
    if "plugins" in parts and "ai-agent-meta-harness" in parts:
        plugin_index = parts.index("plugins")
        return Path(*parts[: plugin_index + 2])
    return script.parents[3] / "plugins" / PLUGIN_NAME


def write_marketplace(marketplace_root: Path, plugin_root: Path) -> Path:
    plugins_dir = marketplace_root / "plugins"
    plugin_dest = plugins_dir / PLUGIN_NAME
    metadata_dir = marketplace_root / ".agents" / "plugins"
    metadata_dir.mkdir(parents=True)
    plugins_dir.mkdir(parents=True)
    shutil.copytree(plugin_root, plugin_dest)
    marketplace = {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "Local AI Agent Meta Harness"},
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Engineering",
            }
        ],
    }
    manifest = metadata_dir / "marketplace.json"
    manifest.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")
    return plugin_dest


def run_codex_marketplace_add(codex_bin: str, codex_home: Path, marketplace_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return subprocess.run(
        [codex_bin, "plugin", "marketplace", "add", str(marketplace_root)],
        cwd=marketplace_root,
        env=env,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def append_enabled_plugin(codex_home: Path) -> None:
    config = codex_home / "config.toml"
    with config.open("a", encoding="utf-8") as handle:
        handle.write(f'\n[plugins."{PLUGIN_NAME}@{MARKETPLACE_NAME}"]\n')
        handle.write("enabled = true\n")


def validate_plugin_files(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    manifest = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest.is_file():
        return [f"MISSING PLUGIN MANIFEST: {manifest}"]
    try:
        parsed = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"INVALID PLUGIN MANIFEST JSON: {manifest}: {exc}"]
    if parsed.get("name") != PLUGIN_NAME:
        errors.append(f"plugin.json name must be {PLUGIN_NAME}")
    if parsed.get("skills") != "./skills/":
        errors.append("plugin.json skills must point to ./skills/")
    for skill in EXPECTED_SKILLS:
        skill_path = plugin_root / "skills" / skill / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"MISSING ACTIVATED SKILL: {skill_path}")
    return errors


def validate_activation(codex_home: Path, marketplace_root: Path, activated_plugin_root: Path) -> list[str]:
    errors: list[str] = []
    config = codex_home / "config.toml"
    try:
        config_text = config.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"UNREADABLE CODEX CONFIG: {config}: {exc}"]
    required_config_markers = (
        f"[marketplaces.{MARKETPLACE_NAME}]",
        "source_type = \"local\"",
        f"source = \"{marketplace_root}\"",
        f"[plugins.\"{PLUGIN_NAME}@{MARKETPLACE_NAME}\"]",
        "enabled = true",
    )
    for marker in required_config_markers:
        if marker not in config_text:
            errors.append(f"MISSING ACTIVATION CONFIG MARKER: {marker}")
    marketplace_manifest = marketplace_root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_manifest.is_file():
        errors.append(f"MISSING MARKETPLACE MANIFEST: {marketplace_manifest}")
    errors.extend(validate_plugin_files(activated_plugin_root))
    return errors


def smoke(codex_bin: str, plugin_root: Path) -> list[str]:
    if not plugin_root.is_dir():
        return [f"MISSING PLUGIN ROOT: {plugin_root}"]
    with tempfile.TemporaryDirectory(prefix="codex-plugin-activation.") as temp_dir:
        temp = Path(temp_dir)
        codex_home = temp / "codex-home"
        marketplace_root = (temp / "marketplace").resolve()
        codex_home.mkdir()
        activated_plugin_root = write_marketplace(marketplace_root, plugin_root)
        result = run_codex_marketplace_add(codex_bin, codex_home, marketplace_root)
        if result.returncode != 0:
            return [
                "CODEX MARKETPLACE ADD FAILED",
                f"stdout: {result.stdout.strip()}",
                f"stderr: {result.stderr.strip()}",
            ]
        append_enabled_plugin(codex_home)
        return validate_activation(codex_home, marketplace_root, activated_plugin_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable")
    parser.add_argument("--plugin-root", type=Path, default=default_plugin_root(), help="local plugin root")
    args = parser.parse_args(argv)

    errors = smoke(args.codex_bin, args.plugin_root.resolve())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Local Codex plugin activation smoke passed: {args.plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
