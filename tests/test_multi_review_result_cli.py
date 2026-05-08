from __future__ import annotations

from pathlib import Path
import hashlib
import json
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


def probe_transcript(
    command: str,
    exit_code: int,
    stdout: str = "",
    stderr: str = "",
    cwd: str = ".",
    result_ref: str = "backlog/fixtures/multi-review/governance-pass.yml",
    result_digest: str = "0" * 64,
    source_refs: list[str] | None = None,
) -> dict:
    if source_refs is None:
        source_refs = ["scripts/check-multi-review-result.py"]
    return {
        "ProbeTranscript": {
            "schema_version": "probe-transcript/v1",
            "probe_command": command,
            "probe_exit_code": exit_code,
            "result_ref": result_ref,
            "result_digest": result_digest,
            "packet_ref": None,
            "packet_sha256": None,
            "source_refs": source_refs,
            "cwd": cwd,
            "generated_by": "test",
            "date": "2026-05-06",
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        }
    }


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

    def test_rejects_container_stored_verdict_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["derived_verdict"] = ["PASS"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("MultiReviewResult.derived_verdict: must be null or one of", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_container_top_level_enums_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["lifecycle"] = ["finalized"]
        result["MultiReviewResult"]["review_mode"] = ["governance"]
        result["MultiReviewResult"]["independence"] = ["independent"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("MultiReviewResult.lifecycle: must be draft or finalized", completed.stderr)
        self.assertIn("MultiReviewResult.review_mode: must be governance or advisory", completed.stderr)
        self.assertIn("MultiReviewResult.independence: must be independent or fallback_nonindependent", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_container_identity_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["review_id"] = ["mr-governance-pass-fixture"]
        result["MultiReviewResult"]["reported_final_verdict"] = {"verdict": "PASS"}

        self.assert_rejected(result, "MultiReviewResult.review_id: must be a substantive string")
        self.assert_rejected(result, "MultiReviewResult.reported_final_verdict: must be a non-empty string")

    def test_rejects_mixed_mapping_keys_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"][1] = "extra"
        result["MultiReviewResult"]["target"][1] = "extra"
        result["MultiReviewResult"]["critics"][0][1] = "extra"
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("MultiReviewResult: extra fields", completed.stderr)
        self.assertIn("MultiReviewResult.target: extra fields", completed.stderr)
        self.assertIn("extra fields", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_container_critic_enums_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["critic_type"] = ["validation_layer"]
        critic["verdict"] = ["pass"]
        critic["validation_layer"] = ["structured-validator"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("critic_type must be a non-empty string", completed.stderr)
        self.assertIn("verdict is invalid", completed.stderr)
        self.assertIn("validation_layer is invalid", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_reports_governance_pass_transcript_consistency_without_replay(self) -> None:
        result = run_cli("--result", str(FIXTURE_ROOT / "governance-pass.yml"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DERIVED: PASS", result.stdout)
        self.assertIn("linked probe transcripts", result.stdout)
        self.assertIn("not command replay", result.stdout)

    def test_require_governance_pass_requires_explicit_replay(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "governance-pass.yml"),
            "--require-governance-pass",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("governance PASS acceptance requires explicit --replay-probe-commands", result.stderr)
        self.assertIn("VALID: PASS", result.stderr)
        self.assertNotIn("DERIVED: PASS", result.stderr)

    def test_replays_probe_commands_when_requested(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "governance-pass.yml"),
            "--require-governance-pass",
            "--replay-probe-commands",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("replayed probe commands", result.stdout)

    def test_rejects_deprecated_verify_probe_alias(self) -> None:
        result = run_cli(
            "--result",
            str(FIXTURE_ROOT / "governance-pass.yml"),
            "--require-governance-pass",
            "--verify-probe-commands",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --verify-probe-commands", result.stderr)

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
        result["MultiReviewResult"]["derived_verdict"] = "ADVISORY_PASS"

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

    def test_rejects_malformed_required_critics_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["required_critics"] = 1
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("required_critics: must be a non-empty list", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["required_critics"] = [["validation-layer"]]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("required_critics: must contain only non-empty string ids", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["critic_id"] = ["validation-layer"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("critic_id must be a non-empty string", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_generic_false_green_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["false_green_risk"] = "checked"
        result["MultiReviewResult"]["critics"][0]["invariant_checked"] = "ok"

        self.assert_rejected(result, "false_green_risk must be substantive")
        path = self.write_result(result)
        completed = run_cli("--result", str(path), "--require-governance-pass")
        self.assertIn("invariant_checked must be substantive", completed.stderr)

    def test_rejects_container_values_in_scalar_acceptance_fields(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["false_green_risk"] = ["list wrapped risk"]
        critic["invariant_checked"] = {"claim": "dict wrapped invariant"}
        critic["probe_result"] = ["list wrapped probe result"]
        critic["probe_interpretation"] = {"claim": "dict wrapped interpretation"}
        critic["why_not_10"] = ["list wrapped why"]
        critic["residual_risk_disposition"] = {"claim": "dict wrapped disposition"}
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("false_green_risk must be a string", completed.stderr)
        self.assertIn("invariant_checked must be a string", completed.stderr)
        self.assertIn("probe_result must be a string", completed.stderr)
        self.assertIn("probe_interpretation must be a string", completed.stderr)
        self.assertIn("why_not_10 must be a string", completed.stderr)
        self.assertIn("residual_risk_disposition must be a string", completed.stderr)

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

        self.assert_rejected(result, "probe_evidence_refs must include a structured transcript matching probe_command")

    def test_rejects_bare_probe_transcript_artifact_refs(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_evidence_refs"] = [
            critic["probe_evidence_refs"][0].removeprefix("file:")
        ]

        self.assert_rejected(result, "must use file: scheme for probe transcript artifact refs")

    def test_rejects_extra_non_transcript_probe_evidence_ref(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["critics"][0]["probe_evidence_refs"].append("file:README.md")

        self.assert_rejected(result, "must be a structured ProbeTranscript artifact")

    def test_rejects_extra_malformed_transcript_probe_evidence_ref(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "missing-cwd-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            transcript = probe_transcript(
                critic["probe_command"],
                critic["probe_exit_code"],
                source_refs=critic["source_refs"],
            )
            transcript["ProbeTranscript"].pop("cwd")
            (ROOT / rel_transcript).write_text(yaml.safe_dump(transcript, sort_keys=False), encoding="utf-8")
            critic["probe_evidence_refs"].append(f"file:{rel_transcript}")
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid probe transcript: missing fields", completed.stderr)

    def test_rejects_mixed_key_transcript_shape_without_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "mixed-key-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            transcript = probe_transcript(
                critic["probe_command"],
                critic["probe_exit_code"],
                source_refs=critic["source_refs"],
            )
            transcript["ProbeTranscript"][1] = "extra"
            transcript["ProbeTranscript"]["extra"] = "extra"
            (ROOT / rel_transcript).write_text(yaml.safe_dump(transcript, sort_keys=False), encoding="utf-8")
            critic["probe_evidence_refs"].append(f"file:{rel_transcript}")
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid probe transcript: extra fields", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rejects_container_generated_by_in_probe_transcript(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "container-generated-by-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            transcript = probe_transcript(
                critic["probe_command"],
                critic["probe_exit_code"],
                source_refs=critic["source_refs"],
            )
            transcript["ProbeTranscript"]["generated_by"] = ["codex"]
            (ROOT / rel_transcript).write_text(yaml.safe_dump(transcript, sort_keys=False), encoding="utf-8")
            critic["probe_evidence_refs"].append(f"file:{rel_transcript}")
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid probe transcript: generated_by must be a substantive string", completed.stderr)

    def test_rejects_marker_only_transcript_even_when_markers_match(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "marker-only.txt").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            (ROOT / rel_transcript).write_text(
                f"COMMAND: {critic['probe_command']}\nEXIT_CODE: {critic['probe_exit_code']}\n",
                encoding="utf-8",
            )
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_structured_transcript_from_non_repo_cwd(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "foreign-cwd-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        critic["probe_command"],
                        critic["probe_exit_code"],
                        cwd="/tmp/other-checkout",
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_structured_transcript_from_absolute_repo_cwd(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_transcript = (Path(tmpdir) / "absolute-cwd-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        critic["probe_command"],
                        critic["probe_exit_code"],
                        cwd=str(ROOT),
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_transcript_bound_to_different_result_ref(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "wrong-result-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        critic["probe_command"],
                        critic["probe_exit_code"],
                        result_ref="backlog/fixtures/multi-review/governance-pass.yml",
                        source_refs=critic["source_refs"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            completed = run_cli("--result", rel_result, "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_external_result_copy_bound_to_original_transcripts(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["target"]["summary"] = "External copied result should not reuse fixture transcripts."
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "governance-pass-copy.yml"
            path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_transcript_without_critic_source_refs(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "wrong-source-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        critic["probe_command"],
                        critic["probe_exit_code"],
                        result_ref=rel_result,
                        result_digest=result_digest,
                        source_refs=["README.md"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            completed = run_cli("--result", rel_result, "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_rejects_extra_stale_transcript_ref_even_when_one_ref_matches(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            for index, critic in enumerate(result["MultiReviewResult"]["critics"]):
                rel_transcript = (tmp_path / f"critic-{index}-transcript.yml").relative_to(ROOT).as_posix()
                critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            stale_ref = (tmp_path / "stale-extra-transcript.yml").relative_to(ROOT).as_posix()
            result["MultiReviewResult"]["critics"][0]["probe_evidence_refs"].append(f"file:{stale_ref}")
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            for index, critic in enumerate(result["MultiReviewResult"]["critics"]):
                rel_transcript = critic["probe_evidence_refs"][0].removeprefix("file:")
                (ROOT / rel_transcript).write_text(
                    yaml.safe_dump(
                        probe_transcript(
                            critic["probe_command"],
                            critic["probe_exit_code"],
                            result_ref=rel_result,
                            result_digest=result_digest,
                            source_refs=critic["source_refs"],
                        ),
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )
            stale_critic = result["MultiReviewResult"]["critics"][0]
            (ROOT / stale_ref).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        stale_critic["probe_command"],
                        stale_critic["probe_exit_code"],
                        result_ref=rel_result,
                        result_digest="1" * 64,
                        source_refs=stale_critic["source_refs"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            completed = run_cli("--result", rel_result)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)

    def test_replay_checks_every_matching_transcript_ref(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            command = "python3 -c \"print('fresh')\""
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = command
            critic["probe_evidence_refs"] = [
                f"file:{(tmp_path / 'fresh-transcript.yml').relative_to(ROOT).as_posix()}",
                f"file:{(tmp_path / 'stale-transcript.yml').relative_to(ROOT).as_posix()}",
            ]
            for index, other in enumerate(result["MultiReviewResult"]["critics"][1:], start=1):
                other["probe_command"] = "python3 -c \"\""
                other["probe_evidence_refs"] = [
                    f"file:{(tmp_path / f'critic-{index}-transcript.yml').relative_to(ROOT).as_posix()}"
                ]
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            for item in result["MultiReviewResult"]["critics"]:
                for ref in item["probe_evidence_refs"]:
                    rel_transcript = ref.removeprefix("file:")
                    stdout = ""
                    if item is critic and "fresh-transcript" in rel_transcript:
                        stdout = "fresh\n"
                    if item is critic and "stale-transcript" in rel_transcript:
                        stdout = "stale\n"
                    (ROOT / rel_transcript).write_text(
                        yaml.safe_dump(
                            probe_transcript(
                                item["probe_command"],
                                item["probe_exit_code"],
                                stdout=stdout,
                                result_ref=rel_result,
                                result_digest=result_digest,
                                source_refs=item["source_refs"],
                            ),
                            sort_keys=False,
                        ),
                        encoding="utf-8",
                    )

            completed = run_cli("--result", rel_result, "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command stdout hash mismatch against linked transcript", completed.stderr)

    def test_rejects_fabricated_transcript_when_replayed(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        critic = result["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = "python3 missing-probe.py --claim-pass"
        critic["probe_result"] = "Plausible hand-authored success text."
        critic["probe_evidence_refs"] = ["file:backlog/fixtures/multi-review/probe-transcripts/fabricated-command.txt"]
        path = self.write_result(result)

        completed = run_cli("--result", str(path), "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command exit mismatch", completed.stderr)

    def test_probe_replay_launch_errors_become_validator_errors(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_command = (tmp_path / "not-executable-probe").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "non-exec-transcript.txt").relative_to(ROOT).as_posix()
            (ROOT / rel_command).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(probe_transcript(rel_command, 0, stdout="not actually executable\n"), sort_keys=False),
                encoding="utf-8",
            )
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = rel_command
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command launch failed", completed.stderr)
        self.assertIn("DERIVED: VETO", completed.stderr)

    def test_non_utf8_probe_transcript_ref_becomes_veto_not_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            rel_binary = (Path(tmpdir) / "binary-transcript.bin").relative_to(ROOT).as_posix()
            (ROOT / rel_binary).write_bytes(b"\xff\xfe\x00not utf8")
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_evidence_refs"] = [f"file:{rel_binary}"]
            path = self.write_result(result)
            completed = run_cli("--result", str(path), "--require-governance-pass")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_evidence_refs must include a structured transcript matching probe_command", completed.stderr)
        self.assertIn("DERIVED: VETO", completed.stderr)

    def test_probe_replay_non_utf8_output_does_not_traceback(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            command = "python3 -c \"import sys; sys.stdout.buffer.write(bytes([255]))\""
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "invalid-output-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = command
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        command,
                        0,
                        stdout="not replayed output\n",
                        result_ref=rel_result,
                        result_digest=result_digest,
                        source_refs=critic["source_refs"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            completed = run_cli("--result", rel_result, "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command stdout was not valid UTF-8", completed.stderr)
        self.assertIn("DERIVED: VETO", completed.stderr)

    def test_probe_replay_hashes_raw_bytes_not_replacement_text(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            command = "python3 -c \"import sys; sys.stdout.buffer.write(bytes([255]))\""
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "replacement-output-transcript.yml").relative_to(ROOT).as_posix()
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = command
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            (ROOT / rel_transcript).write_text(
                yaml.safe_dump(
                    probe_transcript(
                        command,
                        0,
                        stdout="\ufffd",
                        result_ref=rel_result,
                        result_digest=result_digest,
                        source_refs=critic["source_refs"],
                    ),
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            completed = run_cli("--result", rel_result, "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command stdout was not valid UTF-8", completed.stderr)
        self.assertIn("DERIVED: VETO", completed.stderr)

    def test_probe_replay_compares_against_pre_replay_transcript(self) -> None:
        result = load_yaml_fixture("governance-pass.yml")
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            rel_result = (tmp_path / "multi-review.yml").relative_to(ROOT).as_posix()
            rel_transcript = (tmp_path / "self-mutating-transcript.json").relative_to(ROOT).as_posix()
            code = (
                "from pathlib import Path; import hashlib, json; "
                f"p=Path({rel_transcript!r}); "
                "d=json.loads(p.read_text()); "
                "out='mutated\\n'; "
                "d['ProbeTranscript']['stdout']=out; "
                "d['ProbeTranscript']['stdout_sha256']=hashlib.sha256(out.encode()).hexdigest(); "
                "p.write_text(json.dumps(d)); "
                "print('mutated')"
            )
            command = f"python3 -c {code!r}"
            critic = result["MultiReviewResult"]["critics"][0]
            critic["probe_command"] = command
            critic["probe_evidence_refs"] = [f"file:{rel_transcript}"]
            (ROOT / rel_result).write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
            result_digest = hashlib.sha256((ROOT / rel_result).read_bytes()).hexdigest()
            (ROOT / rel_transcript).write_text(
                json.dumps(
                    probe_transcript(
                        command,
                        0,
                        stdout="original\n",
                        result_ref=rel_result,
                        result_digest=result_digest,
                        source_refs=critic["source_refs"],
                    )
                ),
                encoding="utf-8",
            )
            completed = run_cli("--result", rel_result, "--require-governance-pass", "--replay-probe-commands")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_command stdout hash mismatch against linked transcript", completed.stderr)
        self.assertIn("DERIVED: VETO", completed.stderr)

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

        result = load_yaml_fixture("governance-pass.yml")
        result["MultiReviewResult"]["target"]["summary"] = ["list wrapped summary"]

        self.assert_rejected(result, "target.summary: must be a substantive string")

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
