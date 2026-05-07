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
        return tmp, tmp_root

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


if __name__ == "__main__":
    unittest.main()
