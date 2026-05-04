from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-gate.yml"


class ReleaseCiWorkflowTests(unittest.TestCase):
    def test_release_gate_workflow_exists(self) -> None:
        self.assertTrue(WORKFLOW.is_file())

    def test_workflow_runs_verify_release_with_ci_safe_flags(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("python3 scripts/verify-release.py --ci --skip-clean-worktree --base-ref \"$BASE_REF\"", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("BASE_REF=\"origin/${{ github.base_ref }}\"", text)
        self.assertIn("BASE_REF=\"${{ github.event.before }}\"", text)

    def test_workflow_uses_explicit_release_gate_not_plain_unittest(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertNotIn("python3 -m unittest discover\n", text)
        self.assertNotIn("python3 -m unittest discover ", text)
        self.assertIn("verify-release.py", text)

    def test_workflow_documents_read_only_permissions(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("permissions:", text)
        self.assertIn("contents: read", text)


if __name__ == "__main__":
    unittest.main()
