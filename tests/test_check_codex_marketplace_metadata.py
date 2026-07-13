from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-codex-marketplace-metadata.py"

spec = importlib.util.spec_from_file_location("check_codex_marketplace_metadata", SCRIPT)
assert spec and spec.loader
check_marketplace = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_marketplace
spec.loader.exec_module(check_marketplace)


POLICY_TEXT = """# Codex Plugin Bundle Scope

Marketplace publication ready: yes
Official marketplace schema: https://learn.chatgpt.com/docs/build-plugins
Official marketplace taxonomy: Productivity
Generated metadata source: .agents/plugins/marketplace.json
Run python3 scripts/check-codex-marketplace-metadata.py --worktree during development.
"""


def marketplace_payload() -> dict:
    return {
        "name": "personal",
        "interface": {"displayName": "Personal"},
        "plugins": [
            {
                "name": "ai-agent-meta-harness",
                "source": {"source": "local", "path": "./plugins/ai-agent-meta-harness"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


class CodexMarketplaceMetadataCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.originals = (
            check_marketplace.ROOT,
            check_marketplace.POLICY_PATH,
            check_marketplace.MARKETPLACE_PATH,
            check_marketplace.PLUGIN_MANIFEST_PATH,
        )
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        root = Path(self.tempdir.name)
        check_marketplace.ROOT = root
        check_marketplace.POLICY_PATH = root / "adapters/codex/plugin-scope.md"
        check_marketplace.MARKETPLACE_PATH = root / ".agents/plugins/marketplace.json"
        check_marketplace.PLUGIN_MANIFEST_PATH = root / "plugins/ai-agent-meta-harness/.codex-plugin/plugin.json"
        check_marketplace.POLICY_PATH.parent.mkdir(parents=True)
        check_marketplace.POLICY_PATH.write_text(POLICY_TEXT, encoding="utf-8")
        write_json(check_marketplace.MARKETPLACE_PATH, marketplace_payload())
        write_json(check_marketplace.PLUGIN_MANIFEST_PATH, {"name": "ai-agent-meta-harness"})
        self.addCleanup(self.restore_paths)

    def restore_paths(self) -> None:
        (
            check_marketplace.ROOT,
            check_marketplace.POLICY_PATH,
            check_marketplace.MARKETPLACE_PATH,
            check_marketplace.PLUGIN_MANIFEST_PATH,
        ) = self.originals

    def test_accepts_valid_worktree_contract(self) -> None:
        self.assertEqual(check_marketplace.validate(), [])

    def test_rejects_missing_marketplace(self) -> None:
        check_marketplace.MARKETPLACE_PATH.unlink()
        errors = check_marketplace.validate()
        self.assertTrue(any("UNREADABLE FILE" in error for error in errors))

    def test_rejects_wrong_source_path(self) -> None:
        payload = marketplace_payload()
        payload["plugins"][0]["source"]["path"] = "../wrong"
        write_json(check_marketplace.MARKETPLACE_PATH, payload)
        errors = check_marketplace.validate()
        self.assertIn("plugin source.path must be ./plugins/ai-agent-meta-harness", errors)

    def test_rejects_incomplete_policy(self) -> None:
        payload = marketplace_payload()
        payload["plugins"][0]["policy"].pop("authentication")
        write_json(check_marketplace.MARKETPLACE_PATH, payload)
        errors = check_marketplace.validate()
        self.assertIn("plugin policy.authentication must be ON_INSTALL", errors)

    def test_rejects_malformed_additional_entry(self) -> None:
        payload = marketplace_payload()
        payload["plugins"].append({"name": "broken"})
        write_json(check_marketplace.MARKETPLACE_PATH, payload)

        errors = check_marketplace.validate()

        self.assertIn("marketplace plugins must contain exactly one entry", errors)

    def test_rejects_plugin_manifest_identity_drift(self) -> None:
        write_json(check_marketplace.PLUGIN_MANIFEST_PATH, {"name": "wrong"})
        errors = check_marketplace.validate()
        self.assertIn("plugin manifest name must be ai-agent-meta-harness", errors)

    def test_requires_ready_policy_markers(self) -> None:
        check_marketplace.POLICY_PATH.write_text("# Missing policy\n", encoding="utf-8")
        errors = check_marketplace.validate()
        self.assertTrue(any("MISSING POLICY MARKER" in error for error in errors))

    def test_index_validation_reads_staged_marketplace(self) -> None:
        root = check_marketplace.ROOT
        git(root, "init")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test User")
        git(root, "add", ".")
        git(root, "commit", "-m", "initial")

        payload = marketplace_payload()
        payload["plugins"][0]["source"]["path"] = "../wrong"
        write_json(check_marketplace.MARKETPLACE_PATH, payload)
        git(root, "add", ".agents/plugins/marketplace.json")
        write_json(check_marketplace.MARKETPLACE_PATH, marketplace_payload())

        self.assertEqual(check_marketplace.validate(), [])
        index_errors = check_marketplace.validate(use_index=True)
        self.assertIn("plugin source.path must be ./plugins/ai-agent-meta-harness", index_errors)


if __name__ == "__main__":
    unittest.main()
