#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "smoke-local-plugin-activation.py"

spec = importlib.util.spec_from_file_location("smoke_local_plugin_activation", SCRIPT)
assert spec and spec.loader
activation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = activation
spec.loader.exec_module(activation)


def write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def write_minimal_plugin(root: Path) -> None:
    write(
        root / ".codex-plugin" / "plugin.json",
        json.dumps(
            {
                "name": activation.PLUGIN_NAME,
                "skills": "./skills/",
                "interface": {"displayName": "AI Agent Meta Harness"},
            }
        )
        + "\n",
    )
    for skill in activation.EXPECTED_SKILLS:
        write(root / "skills" / skill / "SKILL.md", f"---\nname: {skill}\n---\n")


def write_fake_codex(path: Path, return_code: int = 0) -> None:
    body = f"""#!/bin/sh
set -eu
if [ "$#" -ne 4 ] || [ "$1" != "plugin" ] || [ "$2" != "marketplace" ] || [ "$3" != "add" ]; then
  echo "unexpected args: $*" >&2
  exit 64
fi
if [ {return_code} -ne 0 ]; then
  echo "forced fake codex failure" >&2
  exit {return_code}
fi
mkdir -p "$CODEX_HOME"
cat > "$CODEX_HOME/config.toml" <<EOF
[marketplaces.{activation.MARKETPLACE_NAME}]
source_type = "local"
source = "$4"
EOF
"""
    write(path, body, mode=0o755)


class LocalPluginActivationSmokeTests(unittest.TestCase):
    def test_write_marketplace_copies_plugin_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugin"
            marketplace_root = root / "marketplace"
            write_minimal_plugin(plugin_root)

            activated = activation.write_marketplace(marketplace_root, plugin_root)

            self.assertEqual(activated, marketplace_root / "plugins" / activation.PLUGIN_NAME)
            manifest = json.loads(
                (marketplace_root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["name"], activation.MARKETPLACE_NAME)
            self.assertEqual(manifest["plugins"][0]["name"], activation.PLUGIN_NAME)
            self.assertEqual(manifest["plugins"][0]["source"]["path"], f"./plugins/{activation.PLUGIN_NAME}")
            self.assertTrue((activated / ".codex-plugin" / "plugin.json").is_file())
            self.assertTrue((activated / "skills" / "autoresearch" / "SKILL.md").is_file())

    def test_validate_activation_rejects_missing_enabled_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "codex-home"
            marketplace_root = root / "marketplace"
            plugin_root = marketplace_root / "plugins" / activation.PLUGIN_NAME
            codex_home.mkdir()
            write_minimal_plugin(plugin_root)
            write(
                codex_home / "config.toml",
                textwrap.dedent(
                    f"""\
                    [marketplaces.{activation.MARKETPLACE_NAME}]
                    source_type = "local"
                    source = "{marketplace_root}"
                    """
                ),
            )

            errors = activation.validate_activation(codex_home, marketplace_root, plugin_root)

            self.assertIn(
                f'MISSING ACTIVATION CONFIG MARKER: [plugins."{activation.PLUGIN_NAME}@{activation.MARKETPLACE_NAME}"]',
                errors,
            )

    def test_validate_activation_rejects_missing_activated_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "codex-home"
            marketplace_root = root / "marketplace"
            plugin_root = marketplace_root / "plugins" / activation.PLUGIN_NAME
            codex_home.mkdir()
            write_minimal_plugin(plugin_root)
            shutil.rmtree(plugin_root / "skills" / "multi-review")
            write(
                codex_home / "config.toml",
                textwrap.dedent(
                    f"""\
                    [marketplaces.{activation.MARKETPLACE_NAME}]
                    source_type = "local"
                    source = "{marketplace_root}"

                    [plugins."{activation.PLUGIN_NAME}@{activation.MARKETPLACE_NAME}"]
                    enabled = true
                    """
                ),
            )

            errors = activation.validate_activation(codex_home, marketplace_root, plugin_root)

            self.assertTrue(any("MISSING ACTIVATED SKILL" in error for error in errors), errors)

    def test_smoke_exercises_codex_marketplace_add_and_enablement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugin"
            fake_codex = root / "codex"
            write_minimal_plugin(plugin_root)
            write_fake_codex(fake_codex)

            self.assertEqual(activation.smoke(str(fake_codex), plugin_root), [])

    def test_smoke_reports_codex_cli_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugin"
            fake_codex = root / "codex"
            write_minimal_plugin(plugin_root)
            write_fake_codex(fake_codex, return_code=17)

            errors = activation.smoke(str(fake_codex), plugin_root)

            self.assertIn("CODEX MARKETPLACE ADD FAILED", errors)
            self.assertTrue(any("forced fake codex failure" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
