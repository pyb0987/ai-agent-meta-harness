from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "multi-review" / "check-fixtures.py"
SCENARIOS_ROOT = ROOT / "benchmarks" / "multi-review" / "scenarios"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class MultiReviewBenchmarkCliTests(unittest.TestCase):
    def test_accepts_seed_benchmark_scenarios(self) -> None:
        completed = run_cli()

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("PENDING aa-valid-governance-pass derived=PASS", completed.stdout)
        self.assertIn("PENDING pp-fabricated-transcript derived=PASS", completed.stdout)
        self.assertIn("PASS er-existing-unrelated-file derived=VETO", completed.stdout)
        self.assertIn("Fixture scenarios checked: 10 passed, 2 pending explicit checks", completed.stdout)
        self.assertIn("pending scenarios require --allow-pending", completed.stderr)

    def test_allows_pending_with_explicit_flag(self) -> None:
        completed = run_cli("--allow-pending")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Fixture scenarios checked: 10 passed, 2 pending explicit checks", completed.stdout)

    def test_replays_probe_scenarios_only_with_explicit_flag(self) -> None:
        completed = run_cli("--replay-probe-commands")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS aa-valid-governance-pass derived=PASS", completed.stdout)
        self.assertIn("PASS pp-fabricated-transcript derived=VETO", completed.stdout)
        self.assertIn("PASS er-existing-unrelated-file derived=VETO", completed.stdout)
        self.assertIn("Fixture scenarios checked: 12 passed, 0 pending explicit checks", completed.stdout)

    def test_replays_and_allows_semantic_pending_with_explicit_flags(self) -> None:
        completed = run_cli("--replay-probe-commands", "--allow-pending")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Fixture scenarios checked: 12 passed, 0 pending explicit checks", completed.stdout)

    def test_accepts_single_scenario_path(self) -> None:
        scenario = (
            SCENARIOS_ROOT
            / "typed_artifact_integrity"
            / "ta-list-wrapped-frame"
            / "scenario.yml"
        )

        completed = run_cli("--scenario", str(scenario))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS ta-list-wrapped-frame derived=VETO", completed.stdout)
        self.assertIn("Fixture scenarios checked: 1 passed, 0 pending explicit checks", completed.stdout)

    def test_rejects_oracle_mismatch(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_derived_verdict"] = "VETO"
        scenario["replay_probe_commands"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("expected derived verdict VETO, got PASS", completed.stderr)

    def test_rejects_scenario_review_mode_drift(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["mutations"] = [
            {"op": "set", "path": "/review_mode", "value": "advisory"},
        ]
        scenario["sealed_oracle"]["expected_derived_verdict"] = "ADVISORY_PASS"
        scenario["replay_probe_commands"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "scenario review_mode governance does not match result review_mode advisory",
            completed.stderr,
        )

    def test_rejects_old_verify_probe_scenario_key(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario.pop("replay_probe_commands")
        scenario["verify_probe_commands"] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("use replay_probe_commands instead of verify_probe_commands", completed.stderr)

    def test_rejects_missing_expected_error(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "probe_failure_or_partial_success"
            / "pf-exit-1-hidden"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = ["not a real validator error"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing expected error substring", completed.stderr)


if __name__ == "__main__":
    unittest.main()
