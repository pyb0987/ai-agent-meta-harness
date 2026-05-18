from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

from tests.test_governance_acceptance_cli import git, init_repo, load_checker, run_cli, write_archived_base_ref_packet


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-active-packet-gate.py"


def run_gate(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_gate_module():
    spec = importlib.util.spec_from_file_location("active_packet_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def loose_object_count(root: Path) -> int:
    output = git(root, "count-objects", "-v").stdout
    for line in output.splitlines():
        if line.startswith("count:"):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError(f"count-objects output missing count: {output}")


class ActivePacketGateTests(unittest.TestCase):
    def test_bare_gate_requires_mode(self) -> None:
        result = run_gate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("select an active packet gate scope", result.stderr)

    def test_pointer_only_gate_is_rejected(self) -> None:
        result = run_gate("--pointer", "archive/v2/pointers/pkt.yml")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--pointer requires --base-ref or --staged", result.stderr)
        self.assertIn("check-governance-acceptance.py check-pointer", result.stderr)

    def test_staged_explicit_pointer_requires_staged_pointer_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")

            no_staged_archive = run_gate("--root", str(root), "--staged", "--pointer", pointer_rel)
            (root / "docs" / "note.md").write_text("initial\nunrelated staged change\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            unrelated_staged = run_gate("--root", str(root), "--staged", "--pointer", pointer_rel)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(no_staged_archive.returncode, 0)
        self.assertIn("explicit active packet pointer must be staged with archive evidence", no_staged_archive.stderr)
        self.assertNotEqual(unrelated_staged.returncode, 0)
        self.assertIn("explicit active packet pointer must be staged with archive evidence", unrelated_staged.stderr)

    def test_pointer_candidates_use_rename_destination_only(self) -> None:
        module = load_gate_module()

        self.assertEqual(
            module.pointer_candidates(
                [
                    (
                        "R100",
                        [
                            "archive/v2/pointers/old.yml",
                            "archive/v2/pointers/new.yml",
                        ],
                    )
                ]
            ),
            ["archive/v2/pointers/new.yml"],
        )
        self.assertEqual(
            module.pointer_candidates(
                [
                    (
                        "R100",
                        [
                            "archive/v2/pointers/old.yml",
                            "docs/old-pointer.yml",
                        ],
                    )
                ]
            ),
            [],
        )

    def test_git_helper_ignores_repo_local_git_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            other = Path(tmpdir) / "other"
            root.mkdir()
            other.mkdir()
            init_repo(root)
            init_repo(other)
            module = load_gate_module()
            env = {
                "GIT_DIR": str(other / ".git"),
                "GIT_WORK_TREE": str(other),
                "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
            }

            with mock.patch.dict(os.environ, env, clear=False):
                result = module.git(root, ["rev-parse", "--show-toplevel"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), root.resolve())

    def test_git_helper_does_not_trust_caller_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            fake_bin = Path(tmpdir) / "bin"
            root.mkdir()
            fake_bin.mkdir()
            init_repo(root)
            fake_git = fake_bin / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                "touch \"$PWD/fake-git-called\"\n"
                "printf '/fake/path\\n'\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            module = load_gate_module()
            env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}

            with mock.patch.dict(os.environ, env, clear=False):
                result = module.git(root, ["rev-parse", "--show-toplevel"])
            fake_called = (root / "fake-git-called").exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), root.resolve())
        self.assertFalse(fake_called)

    def test_git_env_ignores_global_config_locations(self) -> None:
        module = load_gate_module()
        with mock.patch.dict(
            os.environ,
            {
                "HOME": "/tmp/fake-home",
                "XDG_CONFIG_HOME": "/tmp/fake-xdg",
                "GIT_CONFIG_GLOBAL": "/tmp/fake-gitconfig",
            },
            clear=False,
        ):
            env = module.git_env()

        self.assertNotIn("HOME", env)
        self.assertNotIn("XDG_CONFIG_HOME", env)
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], os.devnull)
        self.assertNotIn(str(Path(sys.executable).resolve().parent), module.TRUSTED_GIT_PATH_ENTRIES)

    def test_load_checker_prefers_snapshot_checker_when_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = Path(tmpdir)
            module = load_gate_module()
            checker_path = snapshot / "scripts" / "check-governance-acceptance.py"
            checker_path.parent.mkdir(parents=True)
            lines = [
                "SENTINEL = 'snapshot-checker'",
                "SCHEMA_VERSION = 'v2.0-draft'",
                "POINTER_SCHEMA_VERSION = 'acceptance-packet-pointer/v1'",
            ]
            lines.extend(f"def {name}(*args, **kwargs):\n    return []" for name in module.CHECKER_REQUIRED_API)
            checker_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            checker = module.load_checker(snapshot)

        self.assertEqual(checker.SENTINEL, "snapshot-checker")

    def test_load_checker_skips_partial_snapshot_checker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot = Path(tmpdir)
            checker_path = snapshot / "scripts" / "check-governance-acceptance.py"
            checker_path.parent.mkdir(parents=True)
            checker_path.write_text(
                "SENTINEL = 'partial-snapshot-checker'\n"
                "def load_pointer(path):\n"
                "    return {}\n"
                "def validate_pointer(*args, **kwargs):\n"
                "    return []\n",
                encoding="utf-8",
            )
            module = load_gate_module()

            checker = module.load_checker(snapshot)

        self.assertNotEqual(getattr(checker, "SENTINEL", None), "partial-snapshot-checker")
        self.assertTrue(hasattr(checker, "git_ref_commit"))

    def test_base_ref_gate_scrubs_checker_git_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            other = Path(tmpdir) / "other"
            root.mkdir()
            other.mkdir()
            init_repo(root)
            init_repo(other)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")
            env = os.environ.copy()
            env.update(
                {
                    "GIT_DIR": str(other / ".git"),
                    "GIT_WORK_TREE": str(other),
                    "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
                }
            )

            result = run_gate("--root", str(root), "--base-ref", "HEAD~1", env=env)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)

    def test_base_ref_gate_discovers_and_accepts_active_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")

            result = run_gate("--root", str(root), "--base-ref", "HEAD~1")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)

    def test_base_ref_gate_replays_archived_command_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "docs" / "note.md").write_text("bad whitespace   \n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "content with diff-check failure")
            accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_path = root / packet_rel
            artifact_path = root / artifact_rel
            packet_doc = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            command = f"git diff --check {base_ref}...{accepted_head}"
            packet["result"]["inference"]["required_evidence"] = [command]
            packet["result"]["inference"]["changed_paths"] = ["docs/note.md"]
            packet["result"]["inference"]["actual_scope"] = "docs/note.md"
            packet["result"]["evidence"]["baseline_ref"] = base_ref
            packet["result"]["evidence"]["comparison_ref"] = base_ref
            packet["result"]["evidence"]["evaluator_boundary"]["commands"] = [command]
            packet["result"]["evidence"]["command_results"][0]["command"] = command
            source_ref = f"git:{accepted_head}:docs/note.md"
            packet["result"]["evidence"]["source_refs"] = [source_ref]
            packet["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "source",
                    "ref": source_ref,
                    "status": "resolved",
                    "target": f"{accepted_head}:docs/note.md",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet_doc, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        f"packet_id: {packet['meta']['packet_id']}",
                        f"packet_ref: {packet_rel}",
                        f"packet_sha256: {packet_sha}",
                        f"command: {command}",
                        "status: pass",
                        "summary: forged pass command evidence",
                        "replay_metadata: pointer-bound",
                        "replay_recorded_by: scripts/check-governance-acceptance.py",
                        "replay_recorded_at: 2026-05-06",
                        "replay_checker_ref: scripts/check-governance-acceptance.py",
                        "exit_code: 0",
                        "stdout_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            checker = load_checker()
            archive_commit, archive_error = checker.create_archive_commit(root, packet, packet_ref=packet_rel)
            self.assertIsNone(archive_error)
            pointer = checker.pointer_for_packet(
                packet,
                root=root,
                packet_ref=packet_rel,
                packet_sha256=packet_sha,
                archive_commit=archive_commit,
            )
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            pointer_path = root / pointer_rel
            pointer_path.parent.mkdir(parents=True, exist_ok=True)
            pointer_path.write_text(
                yaml.safe_dump({"AcceptancePacketPointer": pointer}, sort_keys=False),
                encoding="utf-8",
            )
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish forged active pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref, "--pointer", pointer_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)
        self.assertIn("command replay exit mismatch", result.stderr)

    def test_base_ref_gate_allows_noop_before_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "commit", "--allow-empty", "-m", "metadata-only before publication")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)

    def test_base_ref_gate_rejects_content_before_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            (root / "docs" / "note.md").write_text("late content before publication\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "late content before publication")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content-changing commits before the selected active pointer publication", result.stderr)

    def test_base_ref_gate_rejects_merge_side_content_before_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            git(root, "switch", "-c", "side-content")
            (root / "docs" / "note.md").write_text("side content before publication\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "side content before publication")
            git(root, "switch", base_branch)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "merge", "--no-ff", "side-content", "-m", "merge side content before publication")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content-changing commits before the selected active pointer publication", result.stderr)

    def test_base_ref_gate_requires_active_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("changed\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "change docs without pointer")

            result = run_gate("--root", str(root), "--base-ref", "HEAD~1")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("base-ref release gate requires an active packet pointer", result.stderr)

    def test_base_ref_explicit_pointer_must_be_published_in_release_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)

            result = run_gate("--root", str(root), "--base-ref", base_ref, "--pointer", pointer_rel)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit active packet pointer must be published in release diff", result.stderr)

    def test_base_ref_gate_rejects_pointer_not_bound_to_release_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("changed before packet\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "uncovered work before packet")
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish late no-op pointer")

            result = run_gate("--root", str(root), "--base-ref", "HEAD~2")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("comparison_ref must match release base-ref", result.stderr)

    def test_active_gate_rejects_symlinked_pointer_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outer = Path(tmpdir)
            root = outer / "repo"
            root.mkdir()
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            pointer_path = root / pointer_rel
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            external_pointer = outer / "external-pointer.yml"
            external_pointer.write_text(pointer_path.read_text(encoding="utf-8"), encoding="utf-8")
            pointer_path.unlink()
            pointer_path.symlink_to(external_pointer)
            git(root, "add", "archive/v2")
            staged = run_gate("--root", str(root), "--staged")
            git(root, "commit", "-m", "publish symlinked pointer")
            release = run_gate("--root", str(root), "--base-ref", "HEAD~1")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(staged.returncode, 0)
        self.assertIn("active packet pointer must be a regular file, not a symlink", staged.stderr)
        self.assertNotEqual(release.returncode, 0)
        self.assertIn("active packet pointer must be a regular file, not a symlink", release.stderr)

    def test_base_ref_explicit_pointer_does_not_follow_symlink_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            pointer_dir = root / "archive" / "v2" / "pointers"
            pointer_dir.mkdir(parents=True)
            (pointer_dir / "alias.yml").symlink_to("pkt-archived-pointer-test.yml")
            git(root, "add", "archive/v2/pointers/alias.yml")
            git(root, "commit", "-m", "add pointer alias")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref, "--pointer", "archive/v2/pointers/alias.yml")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit active packet pointer must be published in release diff", result.stderr)

    def test_base_ref_gate_accepts_no_ff_merge_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            git(root, "switch", "-c", "feature")
            (root / "docs" / "note.md").write_text("feature work\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "feature work")
            packet_rel = "archive/v2/packets/merge-publication.yml"
            pointer_rel = "archive/v2/pointers/merge-publication.yml"
            start = run_cli("--root", str(root), "start", "--output", packet_rel, "--intent", "Feature work.", "--base-ref", base_ref)
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", base_ref)
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")
            git(root, "switch", base_branch)
            git(root, "merge", "--no-ff", "feature", "-m", "merge feature")

            result = run_gate("--root", str(root), "--base-ref", base_ref)

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)

    def test_base_ref_gate_rejects_archive_rewrite_after_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")
            artifact_path = root / artifact_rel
            artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + "note: rewritten\n", encoding="utf-8")
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer = pointer_doc["AcceptancePacketPointer"]
            pointer["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            checker = load_checker()
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            archive_commit, archive_error = checker.create_archive_commit(root, packet, packet_ref=packet_rel)
            self.assertIsNone(archive_error)
            pointer["archive_commit"] = archive_commit
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "rewrite archive pointer")

            result = run_gate("--root", str(root), "--base-ref", base_ref, "--pointer", pointer_rel)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("was not published by a valid first archive/v2 publication commit", result.stderr)

    def test_base_ref_gate_rejects_archive_rewrite_even_after_revert(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            artifact_path = root / artifact_rel
            pointer_path = root / pointer_rel
            original_artifact = artifact_path.read_text(encoding="utf-8")
            original_pointer = pointer_path.read_text(encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")
            artifact_path.write_text(original_artifact + "note: rewritten\n", encoding="utf-8")
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer = pointer_doc["AcceptancePacketPointer"]
            pointer["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            checker = load_checker()
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            archive_commit, archive_error = checker.create_archive_commit(root, packet, packet_ref=packet_rel)
            self.assertIsNone(archive_error)
            pointer["archive_commit"] = archive_commit
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "rewrite archive pointer")
            artifact_path.write_text(original_artifact, encoding="utf-8")
            pointer_path.write_text(original_pointer, encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "revert archive rewrite")

            result = run_gate("--root", str(root), "--base-ref", base_ref, "--pointer", pointer_rel)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content-changing commits", result.stderr)

    def test_base_ref_gate_rejects_merge_side_content_after_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish active pointer")
            git(root, "switch", "-c", "side-content-after-publication")
            (root / "docs" / "note.md").write_text("side content after publication\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "side content after publication")
            git(root, "switch", base_branch)
            git(root, "merge", "--no-ff", "side-content-after-publication", "-m", "merge side content after publication")

            result = run_gate("--root", str(root), "--base-ref", base_ref)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("content-changing commits", result.stderr)

    def test_base_ref_gate_rejects_multiple_pointer_candidates_without_recovery_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            pointer_dir = root / "archive" / "v2" / "pointers"
            pointer_dir.mkdir(parents=True)
            (pointer_dir / "pkt-one.yml").write_text("AcceptancePacketPointer: {}\n", encoding="utf-8")
            (pointer_dir / "pkt-two.yml").write_text("AcceptancePacketPointer: {}\n", encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish two active pointers")

            result = run_gate("--root", str(root), "--base-ref", "HEAD~1")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("publish one active pointer per release diff", result.stderr)
        self.assertNotIn("pass --pointer explicitly", result.stderr)

    def test_staged_gate_requires_pointer_for_staged_archive_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            write_archived_base_ref_packet(root)
            git(root, "add", "archive/v2")

            result = run_gate("--root", str(root), "--staged")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("staged archive gate requires an active packet pointer", result.stderr)

    def test_staged_gate_ignores_non_archive_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("changed\n", encoding="utf-8")
            git(root, "add", "docs/note.md")

            result = run_gate("--root", str(root), "--staged")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no packet pointer required", result.stdout)

    def test_staged_gate_rejects_non_base_ref_pointed_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            packet_path = root / packet_rel
            packet_text = packet_path.read_text(encoding="utf-8").replace("mode: base-ref", "mode: staged")
            packet_path.write_text(packet_text, encoding="utf-8")
            git(root, "add", "archive/v2")

            result = run_gate("--root", str(root), "--staged")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pointed acceptance packet must use base-ref mode", result.stderr)

    def test_staged_gate_validates_index_not_untracked_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", packet_rel, pointer_rel)

            result = run_gate("--root", str(root), "--staged")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact_ref does not resolve", result.stderr)

    def test_staged_gate_preserves_ignored_staged_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / ".gitignore").write_text("archive/v2/artifacts/*.log\n", encoding="utf-8")
            git(root, "add", ".gitignore")
            git(root, "commit", "-m", "ignore archive logs")
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "-f", "archive/v2")

            result = run_gate("--root", str(root), "--staged")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)

    def test_staged_gate_does_not_write_live_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            before_objects = loose_object_count(root)

            result = run_gate("--root", str(root), "--staged")
            after_objects = loose_object_count(root)

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(after_objects, before_objects)

    def test_staged_gate_ignores_unstaged_worktree_dirt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            (root / "docs" / "note.md").write_text("unstaged worktree dirt\n", encoding="utf-8")
            (root / "local-untracked.txt").write_text("untracked dirt\n", encoding="utf-8")

            result = run_gate("--root", str(root), "--staged")

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"active packet gate: PASS {pointer_rel}", result.stdout)


if __name__ == "__main__":
    unittest.main()
