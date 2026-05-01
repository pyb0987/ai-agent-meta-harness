#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PreCommitHookTests(unittest.TestCase):
    def test_hook_runs_maintenance_review_checker(self):
        text = (ROOT / ".githooks/pre-commit").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/check-maintenance-review.py", text)


if __name__ == "__main__":
    unittest.main()
