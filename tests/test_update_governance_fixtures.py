from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "update-governance-fixtures.py"


def run_helper(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class UpdateGovernanceFixturesTests(unittest.TestCase):
    def make_fixture_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory(dir=ROOT)
        tmp_root = Path(tmp.name)
        source_root = ROOT / "backlog" / "fixtures"
        target_root = tmp_root / "backlog" / "fixtures"
        shutil.copytree(source_root / "acceptance-packets", target_root / "acceptance-packets")
        shutil.copytree(source_root / "multi-review", target_root / "multi-review")
        self.copy_benchmark_source_ref_placeholders(tmp_root)
        for rel in (
            "MAINTENANCE.md",
            "README.md",
            "benchmarks/multi-review/check-fixtures.py",
            "scripts/check-multi-review-result.py",
            "scripts/check-governance-acceptance.py",
            "scripts/verify-release.py",
            "tests/test_governance_acceptance_cli.py",
            "tests/test_governance_review_import.py",
            "tests/test_maintenance_policy_boundaries.py",
            "tests/test_multi_review_benchmark_cli.py",
            "tests/test_multi_review_result_cli.py",
            "tests/test_pre_commit_hook.py",
            "tests/test_verify_release.py",
        ):
            target = tmp_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)
        return tmp, tmp_root

    def copy_benchmark_scenarios(self, tmp_root: Path) -> None:
        source_root = ROOT / "benchmarks" / "multi-review" / "scenarios"
        target_root = tmp_root / "benchmarks" / "multi-review" / "scenarios"
        shutil.copytree(source_root, target_root, dirs_exist_ok=True)

    def copy_benchmark_source_ref_placeholders(self, tmp_root: Path) -> None:
        source_root = ROOT / "benchmarks" / "multi-review" / "scenarios"
        target_root = tmp_root / "benchmarks" / "multi-review" / "scenarios"
        for source in sorted(source_root.glob("**/scenario.yml")):
            scenario = yaml.safe_load(source.read_text(encoding="utf-8"))
            scenario["replay_probe_commands"] = False
            target = target_root / source.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(yaml.safe_dump(scenario, sort_keys=False), encoding="utf-8")

    def test_check_accepts_current_fixtures(self) -> None:
        completed = run_helper("--check")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("governance fixture update: OK", completed.stdout)

    def test_check_rejects_and_write_repairs_probe_transcript_drift(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "governance-pass-validation-layer.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["result_digest"] = "0" * 64
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        check = run_helper("--root", str(tmp_root), "--check")
        self.assertNotEqual(check.returncode, 0)
        self.assertIn("result_digest", check.stderr)

        write = run_helper("--root", str(tmp_root), "--write")
        self.assertEqual(write.returncode, 0, write.stderr)
        self.assertIn("updated:", write.stdout)

        repaired = run_helper("--root", str(tmp_root), "--check")
        self.assertEqual(repaired.returncode, 0, repaired.stderr)

    def test_check_rejects_command_log_packet_hash_drift(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        log_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "git-diff-check.log"
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        packet_sha_index = next(index for index, line in enumerate(lines) if line.startswith("packet_sha256:"))
        lines[packet_sha_index] = "packet_sha256: " + ("0" * 64)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--check")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("packet_sha256", completed.stderr)

    def test_check_rejects_duplicate_command_log_fields(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        log_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "git-diff-check.log"
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        status_index = next(index for index, line in enumerate(lines) if line == "status: pass")
        lines.insert(status_index, "status: fail")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--check")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("command artifact has duplicate fields", completed.stderr)

    def test_write_repairs_multiple_sections_in_shared_command_log(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        log_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "git-diff-check.log"
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        packet_sha_lines = [index for index, line in enumerate(lines) if line.startswith("packet_sha256:")]
        self.assertGreaterEqual(len(packet_sha_lines), 2)
        lines[packet_sha_lines[0]] = "packet_sha256: " + ("1" * 64)
        lines[packet_sha_lines[1]] = "packet_sha256: " + ("2" * 64)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        write = run_helper("--root", str(tmp_root), "--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        repaired = run_helper("--root", str(tmp_root), "--check")
        self.assertEqual(repaired.returncode, 0, repaired.stderr)

    def test_write_rejects_observed_command_status_drift(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        log_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "git-diff-check.log"
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        status_index = next(index for index, line in enumerate(lines) if line == "status: pass")
        lines[status_index] = "status: fail"
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("observed command evidence drift requires explicit replay", completed.stderr)

    def test_write_rejects_command_log_rebinding_by_packet_only(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        log_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "git-diff-check.log"
        )
        lines = log_path.read_text(encoding="utf-8").splitlines()
        command_index = next(index for index, line in enumerate(lines) if line.startswith("command: git diff"))
        lines[command_index] = "command: changed command that was not observed"
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("command artifact lacks an unambiguous section", completed.stderr)

    def test_helper_does_not_execute_probe_commands(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        sentinel = tmp_root / "SHOULD_NOT_EXIST"
        wrapper_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "harness-affecting-review-import.yml"
        )
        wrapper = yaml.safe_load(wrapper_path.read_text(encoding="utf-8"))
        critic = wrapper["AcceptancePacketReviewImport"]["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = (
            "python3 -c \"from pathlib import Path; "
            "Path('SHOULD_NOT_EXIST').write_text('executed')\""
        )
        wrapper_path.write_text(yaml.safe_dump(wrapper, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--check")

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(sentinel.exists())

    def test_write_rejects_probe_command_drift_without_replay(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        wrapper_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "acceptance-packets"
            / "artifacts"
            / "harness-affecting-review-import.yml"
        )
        wrapper = yaml.safe_load(wrapper_path.read_text(encoding="utf-8"))
        critic = wrapper["AcceptancePacketReviewImport"]["MultiReviewResult"]["critics"][0]
        critic["probe_command"] = "python3 -c \"print('changed command')\""
        wrapper_path.write_text(yaml.safe_dump(wrapper, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe command drift requires explicit replay", completed.stderr)

    def test_write_rejects_probe_output_hash_drift_without_replay(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "governance-pass-validation-layer.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["stdout"] = "tampered output\n"
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("transcript schema drift requires explicit regeneration", completed.stderr)
        self.assertIn("stdout_sha256 must match stdout", completed.stderr)

    def test_write_rejects_probe_schema_drift_without_regeneration(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "governance-pass-validation-layer.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["schema_version"] = "probe-transcript/legacy"
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("transcript schema drift requires explicit regeneration", completed.stderr)

        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"].pop("cwd")
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("transcript schema drift requires explicit regeneration", completed.stderr)
        self.assertIn("missing fields", completed.stderr)

    def test_write_rejects_invalid_probe_transcript_shape_without_regeneration(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "governance-pass-validation-layer.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["cwd"] = "/tmp"
        doc["ProbeTranscript"]["result_digest"] = "0" * 64
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("transcript schema drift requires explicit regeneration", completed.stderr)
        self.assertIn("cwd must identify the repository root", completed.stderr)

    def test_check_resolves_transcript_source_refs_against_requested_root(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        source_ref = "scripts/tmp-only-source.py"
        (tmp_root / source_ref).write_text("# tmp-only fixture source\n", encoding="utf-8")
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        result["MultiReviewResult"]["critics"][0]["source_refs"] = [source_ref]
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "governance-pass-validation-layer.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["source_refs"] = [source_ref]
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("source_refs must resolve", completed.stderr)

    def test_write_rejects_transcript_source_ref_drift(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        result["MultiReviewResult"]["critics"][0]["source_refs"] = ["README.md"]
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
        (tmp_root / "README.md").write_text("# temporary source\n", encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("source-ref drift requires explicit replay", completed.stderr)

    def test_write_rejects_boolean_probe_exit_owner_shape(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        result["MultiReviewResult"]["critics"][0]["probe_exit_code"] = False
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("probe_exit_code must be an integer", completed.stderr)

    def test_write_rejects_malformed_owner_source_refs(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        result["MultiReviewResult"]["critics"][0]["source_refs"].append(123)
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("source_refs must be a non-empty list of strings", completed.stderr)

    def test_check_rejects_conflicting_transcript_binding_owners(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        shared_ref = result["MultiReviewResult"]["critics"][0]["probe_evidence_refs"][0]
        result["MultiReviewResult"]["critics"][1]["probe_evidence_refs"] = [shared_ref]
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--check")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("conflicting transcript binding owners", completed.stderr)

    def test_write_rejects_fixture_refs_outside_fixture_roots(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        (tmp_root / "README.md").write_text("not a fixture transcript\n", encoding="utf-8")
        result_path = tmp_root / "backlog" / "fixtures" / "multi-review" / "governance-pass.yml"
        result = yaml.safe_load(result_path.read_text(encoding="utf-8"))
        result["MultiReviewResult"]["critics"][0]["probe_evidence_refs"] = ["file:README.md"]
        result_path.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")

        completed = run_helper("--root", str(tmp_root), "--write")

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must stay under backlog/fixtures", completed.stderr)

    def test_check_rejects_and_write_repairs_benchmark_probe_transcript_binding(self) -> None:
        tmp, tmp_root = self.make_fixture_root()
        self.addCleanup(tmp.cleanup)
        self.copy_benchmark_scenarios(tmp_root)
        transcript_path = (
            tmp_root
            / "backlog"
            / "fixtures"
            / "multi-review"
            / "probe-transcripts"
            / "fabricated-command.txt"
        )
        doc = yaml.safe_load(transcript_path.read_text(encoding="utf-8"))
        doc["ProbeTranscript"]["result_digest"] = "0" * 64
        transcript_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

        check = run_helper("--root", str(tmp_root), "--check")
        self.assertNotEqual(check.returncode, 0)
        self.assertIn("fabricated-command.txt:result_digest", check.stderr)

        write = run_helper("--root", str(tmp_root), "--write")
        self.assertEqual(write.returncode, 0, write.stderr)

        repaired = run_helper("--root", str(tmp_root), "--check")
        self.assertEqual(repaired.returncode, 0, repaired.stderr)


if __name__ == "__main__":
    unittest.main()
