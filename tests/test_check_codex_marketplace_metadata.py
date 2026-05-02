from __future__ import annotations

import importlib.util
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

## Marketplace Metadata Policy

Marketplace metadata is a release surface, not part of the local-only dogfood
path.

Official source check (2026-05-03): no public schema has been adopted.

Run the checker before publication prep. In the current deferred state, it
passes only when no publication manifest exists.
"""


READY_POLICY_TEXT = POLICY_TEXT + """
Marketplace publication ready: yes
Official marketplace schema: https://example.invalid/schema
Official marketplace taxonomy: https://example.invalid/taxonomy
Generated metadata source: adapters/codex/plugin-scope.md
"""


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
        self.original_root = check_marketplace.ROOT
        self.original_policy = check_marketplace.POLICY_PATH
        self.original_manifests = check_marketplace.PUBLICATION_MANIFESTS
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        root = Path(self.tempdir.name)
        policy = root / "adapters/codex/plugin-scope.md"
        policy.parent.mkdir(parents=True)
        policy.write_text(POLICY_TEXT, encoding="utf-8")

        check_marketplace.ROOT = root
        check_marketplace.POLICY_PATH = policy
        check_marketplace.PUBLICATION_MANIFESTS = (root / ".agents/plugins/marketplace.json",)
        self.addCleanup(setattr, check_marketplace, "ROOT", self.original_root)
        self.addCleanup(setattr, check_marketplace, "POLICY_PATH", self.original_policy)
        self.addCleanup(setattr, check_marketplace, "PUBLICATION_MANIFESTS", self.original_manifests)

    def test_accepts_deferred_state_without_publication_manifest(self) -> None:
        self.assertEqual(check_marketplace.validate(), [])

    def test_rejects_publication_manifest_before_ready_policy(self) -> None:
        manifest = check_marketplace.PUBLICATION_MANIFESTS[0]
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")

        errors = check_marketplace.validate()

        self.assertTrue(any("MARKETPLACE METADATA NOT READY" in error for error in errors))

    def test_accepts_publication_manifest_when_ready_policy_markers_exist(self) -> None:
        check_marketplace.POLICY_PATH.write_text(READY_POLICY_TEXT, encoding="utf-8")
        manifest = check_marketplace.PUBLICATION_MANIFESTS[0]
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")

        self.assertEqual(check_marketplace.validate(), [])

    def test_requires_deferred_policy_markers(self) -> None:
        check_marketplace.POLICY_PATH.write_text("# Missing policy\n", encoding="utf-8")

        errors = check_marketplace.validate()

        self.assertTrue(any("MISSING POLICY MARKER" in error for error in errors))

    def test_index_validation_rejects_staged_manifest_hidden_by_worktree(self) -> None:
        root = check_marketplace.ROOT
        git(root, "init")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test User")
        git(root, "add", "adapters/codex/plugin-scope.md")
        git(root, "commit", "-m", "initial")

        manifest = check_marketplace.PUBLICATION_MANIFESTS[0]
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}", encoding="utf-8")
        git(root, "add", ".agents/plugins/marketplace.json")
        manifest.unlink()

        worktree_errors = check_marketplace.validate()
        index_errors = check_marketplace.validate(use_index=True)

        self.assertEqual(worktree_errors, [])
        self.assertTrue(any("MARKETPLACE METADATA NOT READY" in error for error in index_errors))


if __name__ == "__main__":
    unittest.main()
