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
        self.assertIn("pending scenarios require --allow-pending", completed.stderr)
        self.assertIn("PASS er-existing-unrelated-file derived=VETO", completed.stdout)

    def test_allow_pending_does_not_allow_structural_failures(self) -> None:
        completed = run_cli("--allow-pending")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PENDING pp-fabricated-transcript derived=PASS", completed.stdout)

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

    def test_rejects_malformed_scenario_scalar_fields_without_traceback(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["review_mode"] = ["governance"]
        scenario["base_result"] = ["backlog/fixtures/multi-review/governance-pass.yml"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("review_mode must be one of", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_non_probe_scenarios_do_not_fail_from_binding_noise_only(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["mutations"] = [
            {"op": "set", "path": "/target/summary", "value": "Mutated result bytes."},
        ]
        scenario["replay_probe_commands"] = False
        scenario["sealed_oracle"]["expected_derived_verdict"] = "PASS"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertEqual(completed.returncode, 0, completed.stderr)

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
        self.assertIn("missing expected validator error", completed.stderr)

    def test_replay_rejects_unexpected_extra_validator_errors(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "probe_provenance_and_replay"
            / "pp-fabricated-transcript"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["mutations"].append(
            {
                "op": "set",
                "path": "/critics/1/probe_evidence_refs",
                "value": ["file:README.md"],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path), "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unexpected validator error", completed.stderr)

    def test_rejects_unexpected_extra_validator_errors_without_replay(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-reported-pass-typed-veto"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = [
            "critics[1:review-quality]: veto must be false for derived acceptance"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unexpected validator error", completed.stderr)

    def test_rejects_same_substring_extra_validator_errors(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "validation_layer_confusion"
            / "vl-prose-smoke-only"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = [
            "critics[0:validation-layer]: prose-smoke requires another structured/raw/derived validation layer",
            "critics[1:review-quality]: prose-smoke requires another structured/raw/derived validation layer",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unexpected validator error", completed.stderr)

    def test_source_ref_scenario_fails_if_focus_mutation_is_removed(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["mutations"] = [
            {"op": "set", "path": "/target/summary", "value": "Unrelated target summary mutation."}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("expected derived verdict VETO, got PASS", completed.stderr)

    def test_rejects_malformed_oracle_error_lists_without_traceback(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = [1]
        scenario["sealed_oracle"]["oracle_assertions"] = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.expected_errors[0] must be a non-empty string", completed.stderr)
        self.assertIn("sealed_oracle.oracle_assertions must be a non-empty list", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_replay_expected_veto_requires_expected_error_allowlist(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "probe_provenance_and_replay"
            / "pp-fabricated-transcript"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path), "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unexpected validator error", completed.stderr)

    def test_rejects_empty_expected_error_substring(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_errors"] = [" "]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("expected_errors[0] must be a non-empty string", completed.stderr)

    def test_rejects_malformed_expected_verdict_type_without_traceback(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["expected_derived_verdict"] = ["VETO"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.expected_derived_verdict must be one of", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_public_input_oracle_fields(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["expected_derived_verdict"] = "VETO"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public_input extra fields are not allowed", completed.stderr)

    def test_rejects_mixed_public_input_keys_without_traceback(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"][1] = "leak"
        scenario["public_input"]["extra"] = "leak"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public_input extra fields are not allowed", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_public_input_leaky_scalar_values(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["summary"] = {"expected_derived_verdict": "VETO"}
        scenario["public_input"]["input_artifacts"] = ["../sealed-oracle-leak.yml"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public_input.summary must be a non-empty string", completed.stderr)
        self.assertIn("input_artifacts[0] must point to an existing repo-local file", completed.stderr)

    def test_rejects_public_input_text_leaking_oracle_terms(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["summary"] = "This case expects expected_derived_verdict=VETO."

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public_input.summary must not contain sealed oracle term", completed.stderr)

    def test_rejects_public_input_artifact_pointing_to_scenario_oracle(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["input_artifacts"].append(
            "benchmarks/multi-review/scenarios/critic_independence_and_redundancy/ci-duplicate-scope/scenario.yml"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot point to scenario files with sealed_oracle data", completed.stderr)

    def test_rejects_public_input_artifact_pointing_to_sealed_rubric(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["input_artifacts"].append(
            "benchmarks/multi-review/perspective-eval/scenarios/synthesis-drops-veto/sealed-rubric.yml"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot point to sealed benchmark/oracle files", completed.stderr)

    def test_rejects_public_input_artifact_oracle_mapping(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["public_input"]["input_artifacts"].append({"expected_derived_verdict": "VETO"})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("public_input.input_artifacts", completed.stderr)

    def test_rejects_oracle_scalar_shape_drift(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = ["structural"]
        scenario["sealed_oracle"]["false_green_target"] = {"text": "hidden"}
        scenario["sealed_oracle"]["oracle_assertions"][0]["severity"] = ["blocking"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.oracle_type must be one of", completed.stderr)
        self.assertIn("sealed_oracle.false_green_target must be a non-empty string", completed.stderr)
        self.assertIn("oracle_assertions[0].severity must be one of", completed.stderr)

    def test_rejects_untracked_oracle_evidence_refs(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp, tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(repo_tmp) / "oracle-evidence.txt"
            evidence.write_text("local-only evidence\n", encoding="utf-8")
            scenario["sealed_oracle"]["oracle_assertions"][0]["required_evidence_refs"] = [
                evidence.relative_to(ROOT).as_posix()
            ]
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("required_evidence_refs[0] must point to a tracked fixture file", completed.stderr)

    def test_rejects_sealed_oracle_evidence_refs(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_assertions"][0]["required_evidence_refs"] = [
            "benchmarks/multi-review/perspective-eval/scenarios/synthesis-drops-veto/sealed-rubric.yml"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "required_evidence_refs[0] cannot point to sealed benchmark/oracle files",
            completed.stderr,
        )

    def test_rejects_invalid_oracle_acceptable_disposition(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_assertions"][0]["acceptable_disposition"] = ["NOT_A_VERDICT"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("acceptable_disposition[0] must be one of", completed.stderr)

    def test_rejects_oracle_target_path_that_is_not_json_pointer(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_assertions"][0]["target_path"] = "critics/0/scope"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("target_path must be a JSON pointer", completed.stderr)

    def test_rejects_untracked_base_result(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp, tempfile.TemporaryDirectory() as tmpdir:
            base_result = Path(repo_tmp) / "base-result.yml"
            base_result.write_text(
                (ROOT / "backlog/fixtures/multi-review/governance-pass.yml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            scenario["base_result"] = base_result.relative_to(ROOT).as_posix()
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("base_result must point to a tracked fixture file", completed.stderr)

    def test_rejects_semantic_oracle_assertion_shape_without_traceback(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_assertions"] = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.oracle_assertions must be a non-empty list", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_semantic_oracle_shape(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = ["not a mapping"]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.semantic_oracle must be a non-empty mapping", completed.stderr)

    def test_rejects_semantic_oracle_on_structural_oracle(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "structural"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {
            "unsupported_claim": "The structural scenario should not carry a semantic oracle contract.",
            "accepted_disposition": "VETO",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path), "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.semantic_oracle requires oracle_type: semantic", completed.stderr)

    def test_rejects_empty_semantic_oracle_shape(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.semantic_oracle must be a non-empty mapping", completed.stderr)

    def test_rejects_junk_semantic_oracle_contract(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {"junk": "still accepted"}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.semantic_oracle extra fields are not allowed", completed.stderr)
        self.assertIn("sealed_oracle.semantic_oracle must include one of", completed.stderr)

    def test_rejects_vacuous_semantic_oracle_anchor(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {"unsupported_claim": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("sealed_oracle.semantic_oracle.unsupported_claim must be substantive", completed.stderr)

    def test_rejects_untracked_semantic_oracle_source_ref(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"

        with tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp, tempfile.TemporaryDirectory() as tmpdir:
            semantic_ref = Path(repo_tmp) / "semantic-source.txt"
            semantic_ref.write_text("local semantic evidence\n", encoding="utf-8")
            scenario["sealed_oracle"]["semantic_oracle"] = {
                "unsupported_claim": "README evidence supports an unrelated semantic claim",
                "relevant_source_refs": [semantic_ref.relative_to(ROOT).as_posix()],
            }
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("semantic_oracle.relevant_source_refs[0] must point to a tracked fixture file", completed.stderr)

    def test_rejects_sealed_semantic_oracle_source_ref(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {
            "unsupported_claim": "Sealed rubric supports an unrelated semantic claim",
            "relevant_source_refs": [
                "benchmarks/multi-review/perspective-eval/scenarios/synthesis-drops-veto/sealed-rubric.yml"
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("semantic_oracle.relevant_source_refs[0] cannot point to sealed benchmark/oracle files", completed.stderr)

    def test_validates_semantic_oracle_refs_outside_contract_only(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "validator-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {
            "unsupported_claim": "Sealed rubric supports an unrelated semantic claim",
            "relevant_source_refs": [
                "benchmarks/multi-review/perspective-eval/scenarios/synthesis-drops-veto/sealed-rubric.yml"
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("semantic_oracle.relevant_source_refs[0] cannot point to sealed benchmark/oracle files", completed.stderr)

    def test_semantic_oracle_accepted_disposition_can_make_pass_pending(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "acceptance_authority_spoof"
            / "aa-valid-governance-pass"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {
            "unsupported_claim": "The valid governance-pass fixture should still be semantically rejected here.",
            "accepted_disposition": "VETO",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path), "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("semantic_oracle.accepted_disposition requires one of ['VETO']", completed.stdout)

    def test_accepts_named_semantic_oracle_contract(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "evidence_relevance_and_source_support"
            / "er-existing-unrelated-file"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
        scenario["sealed_oracle"]["oracle_type"] = "semantic"
        scenario["sealed_oracle"]["scoring_mode"] = "contract-only"
        scenario["sealed_oracle"]["semantic_oracle"] = {
            "unsupported_claim": "README.md supports the schema-contract probe",
            "relevant_source_refs": [
                "file:backlog/fixtures/multi-review/probe-transcripts/governance-pass-schema-contract.txt"
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS er-existing-unrelated-file derived=VETO", completed.stdout)

    def test_rejects_untracked_result_target_source_ref(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp, tempfile.TemporaryDirectory() as tmpdir:
            source_ref = Path(repo_tmp) / "target-source.txt"
            source_ref.write_text("local-only target source\n", encoding="utf-8")
            scenario["mutations"] = [
                {
                    "op": "set",
                    "path": "/target/source_refs",
                    "value": [source_ref.relative_to(ROOT).as_posix()],
                }
            ]
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("target.source_refs[0] must point to a tracked fixture file", completed.stderr)

    def test_rejects_untracked_result_critic_source_ref(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp, tempfile.TemporaryDirectory() as tmpdir:
            source_ref = Path(repo_tmp) / "critic-source.txt"
            source_ref.write_text("local-only critic source\n", encoding="utf-8")
            scenario["mutations"] = [
                {
                    "op": "set",
                    "path": "/critics/0/source_refs",
                    "value": [source_ref.relative_to(ROOT).as_posix()],
                }
            ]
            path = Path(tmpdir) / "scenario.yml"
            path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
            completed = run_cli("--scenario", str(path))

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("critics[0].source_refs[0] must point to a tracked fixture file", completed.stderr)

    def test_rejects_probe_transcript_metadata_pointing_to_sealed_scenario(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "probe_provenance_and_replay"
            / "pp-fabricated-transcript"
            / "scenario.yml"
        )
        transcript = ROOT / "backlog/fixtures/multi-review/probe-transcripts/fabricated-command.txt"
        original = transcript.read_text(encoding="utf-8")
        try:
            transcript.write_text(
                original.replace(
                    "result_ref: benchmark-generated:pp-fabricated-transcript#mutated-result",
                    (
                        "result_ref: benchmarks/multi-review/scenarios/probe_provenance_and_replay/"
                        "pp-fabricated-transcript/scenario.yml#mutated-result"
                    ),
                ),
                encoding="utf-8",
            )
            scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "scenario.yml"
                path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
                completed = run_cli("--scenario", str(path), "--replay-probe-commands")
        finally:
            transcript.write_text(original, encoding="utf-8")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ProbeTranscript.result_ref cannot point to scenario files with sealed_oracle data", completed.stderr)

    def test_rejects_public_input_transcript_metadata_pointing_to_sealed_scenario(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "critic_independence_and_redundancy"
            / "ci-duplicate-scope"
            / "scenario.yml"
        )
        transcript_ref = "backlog/fixtures/multi-review/probe-transcripts/fabricated-command.txt"
        transcript = ROOT / transcript_ref
        original = transcript.read_text(encoding="utf-8")
        try:
            transcript.write_text(
                original.replace(
                    "result_ref: benchmark-generated:pp-fabricated-transcript#mutated-result",
                    (
                        "result_ref: benchmarks/multi-review/scenarios/probe_provenance_and_replay/"
                        "pp-fabricated-transcript/scenario.yml#mutated-result"
                    ),
                ),
                encoding="utf-8",
            )
            scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
            scenario["public_input"]["input_artifacts"].append(transcript_ref)

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "scenario.yml"
                path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
                completed = run_cli("--scenario", str(path))
        finally:
            transcript.write_text(original, encoding="utf-8")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "public_input.input_artifacts[1].ProbeTranscript.result_ref cannot point to scenario files",
            completed.stderr,
        )

    def test_rejects_nested_probe_transcript_metadata_pointing_to_sealed_scenario(self) -> None:
        source = (
            SCENARIOS_ROOT
            / "probe_provenance_and_replay"
            / "pp-fabricated-transcript"
            / "scenario.yml"
        )
        transcript = ROOT / "backlog/fixtures/multi-review/probe-transcripts/fabricated-command.txt"
        original = transcript.read_text(encoding="utf-8")
        try:
            loaded = yaml.safe_load(original)
            loaded["ProbeTranscript"]["metadata"] = {
                "result_ref": (
                    "benchmarks/multi-review/scenarios/probe_provenance_and_replay/"
                    "pp-fabricated-transcript/scenario.yml#mutated-result"
                ),
                "packet_ref": (
                    "benchmarks/multi-review/scenarios/probe_provenance_and_replay/"
                    "pp-fabricated-transcript/scenario.yml"
                ),
                "source_refs": [
                    "benchmarks/multi-review/perspective-eval/scenarios/synthesis-drops-veto/sealed-rubric.yml"
                ],
            }
            transcript.write_text(yaml.safe_dump(loaded, sort_keys=False), encoding="utf-8")
            scenario = yaml.safe_load(source.read_text(encoding="utf-8"))

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "scenario.yml"
                path.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")
                completed = run_cli("--scenario", str(path), "--replay-probe-commands")
        finally:
            transcript.write_text(original, encoding="utf-8")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("ProbeTranscript.metadata.result_ref cannot point to scenario files", completed.stderr)
        self.assertIn("ProbeTranscript.metadata.source_refs[0] cannot point to sealed benchmark/oracle files", completed.stderr)


if __name__ == "__main__":
    unittest.main()
