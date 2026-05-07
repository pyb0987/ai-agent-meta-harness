from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-multi-review-result.py"
FIXTURE_ROOT = ROOT / "backlog" / "fixtures" / "multi-review"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_yaml_fixture(name: str) -> dict:
    return yaml.safe_load((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class MultiReviewResultCliTests(unittest.TestCase):
    def write_result(self, result: dict) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "multi-review.yml"
        path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
        return path

    def assert_rejected(self, result: dict, expected: str) -> None:
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn(expected, completed.stderr)

    def test_accepts_governance_pass_yaml(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "governance-pass.yml"),
            "--require-governance-pass",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DERIVED: PASS", result.stdout)
        self.assertIn("linked probe transcripts", result.stdout)
        self.assertIn("stable handoff evidence", result.stdout)

    def test_replays_probe_commands_when_requested(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "governance-pass.yml"),
            "--require-governance-pass",
            "--verify-probe-commands",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("replayed probe commands", result.stdout)

    def test_accepts_advisory_pass_json_but_not_as_governance(self) -> None:
        result = run_cli("--result", str(FIXTURE_ROOT / "advisory-pass.json"))
        strict = run_cli(
            "--result",
            str(FIXTURE_ROOT / "advisory-pass.json"),
            "--require-governance-pass",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DERIVED: ADVISORY_PASS", result.stdout)
        self.assertNotEqual(strict.returncode, 0)
        self.assertIn("not governance PASS", strict.stderr)

    def test_rejects_hand_authored_pass_when_typed_veto_exists(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "hand-authored-pass-with-veto.yml"),
            "--require-governance-pass",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("veto must be false", result.stderr)
        self.assertIn("DERIVED: VETO", result.stderr)

    def test_rejects_score_below_governance_threshold(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][2]["score"] = 8

        self.assert_rejected(result, "score below 9")

    def test_rejects_stored_derived_verdict_mismatch_and_errors(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["derived_verdict"] = "VETO"

        self.assert_rejected(result, "derived_verdict")
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["derivation_errors"] = ["stale previous error"]
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("derivation_errors: must be empty", completed.stderr)

    def test_rejects_non_required_veto_or_low_score_critic(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        extra = dict(result["MultiReviewResult"]["critics"][0])
        extra.update(
            {
                "critic_id": "extra-veto",
                "required": False,
                "score": 8,
                "verdict": "veto",
                "veto": True,
                "blocking_findings": ["Optional-looking veto must not be hidden."],
            }
        )
        result["MultiReviewResult"]["critics"].append(extra)

        self.assert_rejected(result, "veto must be false")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("score below 9", completed.stderr)
        self.assertIn("blocking_findings must be empty", completed.stderr)

    def test_rejects_spoofed_required_critic_id(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["required_critics"][0] = "validation"

        self.assert_rejected(result, "missing required critics")

    def test_rejects_generic_false_green_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["false_green_risk"] = "checked"
        result["MultiReviewResult"]["critics"][0]["invariant_checked"] = "ok"

        self.assert_rejected(result, "false_green_risk must be substantive")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("invariant_checked must be substantive", completed.stderr)

    def test_rejects_probe_run_false_and_vacuous_probe_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_run"] = False
        critic["probe_command"] = "existing review says PASS"
        critic["probe_result"] = "pass"
        critic["probe_interpretation"] = "generic"
        critic["reason_no_probe"] = "network unavailable"

        self.assert_rejected(result, "probe_run must be true")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("probe_command must be substantive", completed.stderr)
        self.assertIn("probe_result must be substantive", completed.stderr)
        self.assertIn("probe_interpretation must be substantive", completed.stderr)

    def test_rejects_probe_exit_failure_for_acceptance(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["probe_exit_code"] = 1

        self.assert_rejected(result, "probe_exit_code must be 0")

    def test_rejects_probe_without_matching_transcript(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = "python3 missing-probe.py --claim-pass"
        critic["probe_result"] = "Plausible hand-authored success text."

        self.assert_rejected(result, "probe_evidence_refs must include a transcript matching probe_command")

    def test_rejects_fabricated_transcript_when_replayed(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = "python3 missing-probe.py --claim-pass"
        critic["probe_result"] = "Plausible hand-authored success text."
        critic["probe_evidence_refs"] = ["backlog/fixtures/multi-review/probe-transcripts/fabricated-command.txt"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass", "--verify-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command exit mismatch", completed.stderr)

    def test_rejects_known_no_coverage_probe_values(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = "read the plan"
        critic["probe_result"] = "no probe run"
        critic["probe_interpretation"] = "self-attested"

        self.assert_rejected(result, "probe_command must be substantive")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("probe_result must be substantive", completed.stderr)
        self.assertIn("probe_interpretation must be substantive", completed.stderr)

    def test_rejects_non_required_no_coverage_probe_values(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        extra = dict(result["MultiReviewResult"]["critics"][0])
        extra.update(
            {
                "critic_id": "extra-no-probe",
                "required": False,
                "probe_command": "read the plan",
                "probe_result": "not run",
                "probe_interpretation": "generic",
            }
        )
        result["MultiReviewResult"]["critics"].append(extra)

        self.assert_rejected(result, "probe_command must be substantive")

    def test_rejects_wrong_layer_validation(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["validation_layer"] = "wrong-layer"

        self.assert_rejected(result, "validation_layer wrong-layer")

    def test_rejects_malformed_or_empty_target(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["target"] = {"summary": ""}

        self.assert_rejected(result, "MultiReviewResult.target")

    def test_rejects_repo_escape_or_missing_target_refs(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["target"]["source_refs"] = ["file:/etc/hosts"]

        self.assert_rejected(result, "must resolve to an existing repository-local file")
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["target"]["source_refs"] = ["missing/nope.yml"]
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing/nope.yml", completed.stderr)

    def test_rejects_empty_required_critic_evidence_or_source_refs(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["evidence"] = []
        critic["source_refs"] = []

        self.assert_rejected(result, "evidence must be a non-empty list")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("source_refs", completed.stderr)

    def test_rejects_invalid_or_future_critic_date(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["date"] = "not-a-date"

        self.assert_rejected(result, "date must be an ISO date")
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["date"] = "3026-01-01"
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("date must be an ISO date", completed.stderr)

    def test_rejects_prose_smoke_without_primary_validation_layer(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        for critic in result["MultiReviewResult"]["critics"]:
            critic["validation_layer"] = "prose-smoke"

        self.assert_rejected(result, "prose-smoke requires another structured/raw/derived validation layer")

    def test_rejects_missing_meta_critics(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["critic_type"] = "domain"
        result["MultiReviewResult"]["critics"][1]["critic_type"] = "domain"

        self.assert_rejected(result, "missing required Validation Layer Critic")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("missing required Review Quality Meta-Critic", completed.stderr)

    def test_rejects_fallback_nonindependent_for_governance_pass(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["independence"] = "fallback_nonindependent"

        self.assert_rejected(result, "fallback_nonindependent cannot derive governance PASS")

    def test_rejects_missing_frame_challenge_for_governance_pass(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        for critic in result["MultiReviewResult"]["critics"]:
            critic["frame_challenge"] = False

        self.assert_rejected(result, "missing required frame_challenge critic")

    def test_rejects_redundant_required_critic_frames(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][1]["scope"] = result["MultiReviewResult"]["critics"][0]["scope"]

        self.assert_rejected(result, "required critics must have distinct scope values")

    def test_rejects_list_wrapped_frame_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][1]["scope"] = [
            result["MultiReviewResult"]["critics"][0]["scope"]
        ]

        self.assert_rejected(result, "scope must be a non-empty string")

    def test_rejects_redundant_primary_failure_modes(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][1]["primary_failure_mode"] = result["MultiReviewResult"]["critics"][0]["primary_failure_mode"]

        self.assert_rejected(result, "required critics must have distinct primary_failure_mode values")

    def test_rejects_score_9_without_disposition(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["why_not_10"] = ""
        result["MultiReviewResult"]["critics"][0]["residual_risk_disposition"] = "ok"

        self.assert_rejected(result, "score 9 requires why_not_10")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("score 9 requires residual_risk_disposition", completed.stderr)

    def test_rejects_empty_or_malformed_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = Path(tmpdir) / "empty.yml"
            malformed = Path(tmpdir) / "malformed.yml"
            empty.write_text("", encoding="utf-8")
            malformed.write_text("MultiReviewResult: [", encoding="utf-8")

            empty_result = run_cli("--result", str(empty), "--require-governance-pass")
            malformed_result = run_cli("--result", str(malformed), "--require-governance-pass")

        self.assertNotEqual(empty_result.returncode, 0)
        self.assertIn("missing MultiReviewResult", empty_result.stderr)
        self.assertNotEqual(malformed_result.returncode, 0)
        self.assertIn("invalid result syntax", malformed_result.stderr)


if __name__ == "__main__":
    unittest.main()
