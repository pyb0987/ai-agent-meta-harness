from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-governance-acceptance.py"
FIXTURE_ROOT = ROOT / "backlog" / "fixtures" / "acceptance-packets"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def run_cli(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


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


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.com")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("initial\n", encoding="utf-8")
    (root / "scripts").mkdir()
    (root / "scripts" / "check-governance-acceptance.py").write_text(
        "# archive pointer fixture runner ref\n",
        encoding="utf-8",
    )
    git(root, "add", "-A")
    git(root, "commit", "-m", "initial")


def load_checker():
    spec = importlib.util.spec_from_file_location("check_governance_acceptance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def provenance_marker(record: dict) -> str:
    checker = load_checker()
    return f"provenance_record_sha256:{checker.provenance_record_digest(record)}"


def write_archived_base_ref_packet(
    root: Path,
    *,
    packet_id: str = "pkt-archived-pointer-test",
    artifact_rel: str | None = None,
    artifact_packet_ref: str | None = None,
    replay_metadata: bool = False,
    replay_metadata_value: str = "pointer-bound",
    mutable_boundary_refs: bool = False,
) -> tuple[str, str, str]:
    packet_rel = f"archive/v2/packets/{packet_id}.yml"
    artifact_rel = artifact_rel or f"archive/v2/artifacts/{packet_id}-diff-check.log"
    accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()
    boundary_ref = "HEAD" if mutable_boundary_refs else accepted_head
    command = f"git diff --check {boundary_ref}...{accepted_head}"
    packet_path = root / packet_rel
    artifact_path = root / artifact_rel
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    runner_path = root / "scripts" / "check-governance-acceptance.py"
    runner_path.parent.mkdir(parents=True, exist_ok=True)
    runner_path.write_text("# archive pointer fixture runner ref\n", encoding="utf-8")
    packet = {
        "AcceptancePacket": {
            "meta": {
                "packet_id": packet_id,
                "schema_version": "v2.0-draft",
                "lifecycle": "finalized",
                "mode": "base-ref",
                "created_at": "2026-05-06",
                "finalized_at": "2026-05-06",
            },
            "input": {
                "intent": "Archive a stable no-op packet.",
                "actor": "codex",
                "source_refs": [],
                "user_judgment": {},
            },
            "result": {
                "inference": {
                    "change_class": "routine",
                    "impact": "low",
                    "changed_paths": [],
                    "intended_scope": "Archive pointer validation fixture.",
                    "actual_scope": "No repository changes.",
                    "deviations": [],
                    "isolation": "isolated",
                    "protected_boundary_changed": False,
                    "required_evidence": [command],
                    "required_review": [],
                },
                "evidence": {
                    "baseline_ref": boundary_ref,
                    "comparison_ref": boundary_ref,
                    "accepted_head_commit": accepted_head,
                    "evaluator_boundary": {
                        "status": "unchanged",
                        "commands": [command],
                    },
                    "command_results": [
                        {
                            "command": command,
                            "status": "pass",
                            "artifact_ref": f"file:{artifact_rel}",
                        }
                    ],
                    "source_refs": [],
                    "resolved_refs": [
                        {
                            "origin": "generated",
                            "relation": "artifact",
                            "ref": f"file:{artifact_rel}",
                            "status": "resolved",
                            "target": artifact_rel,
                        }
                    ],
                    "trace_refs": {
                        "search_set_before": None,
                        "search_set_after": None,
                        "evolution": [],
                        "failures": [],
                        "disposition": "No trace evidence required for no-op pointer fixture.",
                    },
                    "skipped": [],
                },
                "judgment": {
                    "reviews": [],
                    "waivers": [],
                    "downgrades": [],
                    "residual_risk": [],
                },
                "decision": {
                    "accepted": True,
                    "stable_handoff_eligible": True,
                    "reason": "Required routine evidence passed.",
                    "next_action": "Publish active archive pointer.",
                },
            },
        }
    }
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    artifact_lines = [
        "# Command Evidence",
        f"packet_id: {packet_id}",
        f"packet_ref: {artifact_packet_ref or packet_rel}",
        f"packet_sha256: {packet_sha}",
        f"command: {command}",
        "status: pass",
        "summary: archived pointer fixture command evidence",
    ]
    if replay_metadata:
        artifact_lines.extend(
            [
                f"replay_metadata: {replay_metadata_value}",
                "replay_recorded_by: scripts/check-governance-acceptance.py",
                "replay_recorded_at: 2026-05-06",
                "replay_checker_ref: scripts/check-governance-acceptance.py",
                "exit_code: 0",
                "stdout_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ]
        )
    artifact_path.write_text("\n".join([*artifact_lines, ""]), encoding="utf-8")
    return packet_rel, artifact_rel, packet_sha


def rewrite_archived_packet_and_artifact_sha(root: Path, packet_rel: str, artifact_rel: str, packet: dict) -> str:
    packet_path = root / packet_rel
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    artifact_path = root / artifact_rel
    lines = artifact_path.read_text(encoding="utf-8").splitlines()
    packet_sha_index = next(index for index, line in enumerate(lines) if line.startswith("packet_sha256:"))
    lines[packet_sha_index] = f"packet_sha256: {packet_sha}"
    artifact_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return packet_sha


def synthetic_archive_commit(root: Path, packet_rel: str) -> str:
    checker = load_checker()
    packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
    commit, error = checker.create_archive_commit(root, packet, packet_ref=packet_rel, materialize=True)
    if error:
        raise AssertionError(error)
    return commit


def git_loose_object_count(root: Path) -> int:
    output = git(root, "count-objects", "-v").stdout
    for line in output.splitlines():
        if line.startswith("count: "):
            return int(line.split(":", 1)[1].strip())
    raise AssertionError(f"missing count-objects count line: {output}")


def synthetic_archive_commit_with_extra_path(root: Path, packet_rel: str, extra_rel: str) -> str:
    checker = load_checker()
    packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
    accepted_head = packet["result"]["evidence"]["accepted_head_commit"]
    extra_path = root / extra_rel
    extra_path.parent.mkdir(parents=True, exist_ok=True)
    extra_path.write_text("unexpected archive bytes\n", encoding="utf-8")
    archive_paths = [packet_rel, *checker.archive_artifact_paths(packet, root=root), extra_rel]
    git(root, "add", *archive_paths)
    tree = git(root, "write-tree").stdout.strip()
    return git(root, "commit-tree", tree, "-p", accepted_head, "-m", "archive with unexpected bytes").stdout.strip()


class GovernanceAcceptanceCliTests(unittest.TestCase):
    def test_archive_artifact_paths_include_archive_claim_evidence_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            archive_claim = root / "archive" / "v2" / "artifacts" / "raw-claim.log"
            archive_claim.parent.mkdir(parents=True)
            archive_claim.write_text("selection\n", encoding="utf-8")
            non_archive_claim = root / "evidence" / "raw.log"
            non_archive_claim.parent.mkdir()
            non_archive_claim.write_text("raw\n", encoding="utf-8")
            checker = load_checker()
            packet = {
                "result": {
                    "evidence": {
                        "claims": [
                            {
                                "raw_evidence_refs": [
                                    "file:archive/v2/artifacts/raw-claim.log",
                                    "file:evidence/raw.log",
                                ]
                            }
                        ]
                    }
                }
            }

            self.assertEqual(
                checker.archive_artifact_paths(packet, root=root),
                ["archive/v2/artifacts/raw-claim.log"],
            )

    def test_pointer_claim_artifacts_mirror_archive_claim_evidence_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            archive_claim = root / "archive" / "v2" / "artifacts" / "raw-claim.log"
            archive_claim.parent.mkdir(parents=True)
            archive_claim.write_text("selection\n", encoding="utf-8")
            checker = load_checker()
            packet = {
                "result": {
                    "evidence": {
                        "claims": [
                            {
                                "raw_evidence_refs": [
                                    "file:archive/v2/artifacts/raw-claim.log",
                                    "trace:.harness/traces/evidence.md#claim-capture",
                                ]
                            }
                        ]
                    }
                }
            }

            self.assertEqual(
                checker.pointer_claim_artifacts(packet, root=root),
                [
                    {
                        "source_ref": "file:archive/v2/artifacts/raw-claim.log",
                        "source_sha256": hashlib.sha256(archive_claim.read_bytes()).hexdigest(),
                    }
                ],
            )

    def test_pointer_claim_artifacts_use_raw_claim_classifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            archive_claim = root / "archive" / "v2" / "artifacts" / "strategy-search-selection.yml"
            archive_claim.parent.mkdir(parents=True)
            archive_claim.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "strategy-search-adoption-selection/v1",
                        "evidence_status": "diagnostic_only",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            checker = load_checker()
            packet = {
                "result": {
                    "evidence": {
                        "claims": [
                            {
                                "raw_evidence_refs": [
                                    "file:archive/v2/artifacts/strategy-search-selection.yml",
                                ]
                            }
                        ]
                    }
                }
            }

            self.assertFalse(
                checker.is_raw_claim_file_ref(root, "file:archive/v2/artifacts/strategy-search-selection.yml")
            )
            self.assertEqual(checker.archive_artifact_paths(packet, root=root), [])
            self.assertEqual(checker.pointer_claim_artifacts(packet, root=root), [])

    def test_git_blob_bytes_preserves_raw_blob_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            raw_rel = "archive/v2/artifacts/raw-bytes.bin"
            raw_bytes = b"line\r\n\xff\x00tail\n"
            raw_path = root / raw_rel
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(raw_bytes)
            git(root, "add", raw_rel)
            git(root, "commit", "-m", "add raw archive bytes")
            checker = load_checker()

            blob_bytes = checker.git_blob_bytes(root, "HEAD", raw_rel)
            blob_sha = checker.git_file_sha256(root, "HEAD", raw_rel)

        self.assertEqual(blob_bytes, raw_bytes)
        self.assertEqual(blob_sha, hashlib.sha256(raw_bytes).hexdigest())

    def test_archive_replay_ignores_caller_git_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            other = Path(tmpdir) / "other"
            root.mkdir()
            other.mkdir()
            init_repo(root)
            init_repo(other)
            checker = load_checker()
            env = {
                "GIT_DIR": str(other / ".git"),
                "GIT_WORK_TREE": str(other),
                "GIT_INDEX_FILE": str(other / ".git" / "index"),
                "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
            }

            with mock.patch.dict(os.environ, env, clear=False):
                completed, error = checker.run_archive_command("git rev-parse --show-toplevel", root=root)

        self.assertIsNone(error)
        assert completed is not None
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(Path(completed.stdout.decode("utf-8").strip()).resolve(), root.resolve())

    def test_archive_replay_does_not_trust_caller_path(self) -> None:
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
            checker = load_checker()
            env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}

            with mock.patch.dict(os.environ, env, clear=False):
                completed, error = checker.run_archive_command("git rev-parse --show-toplevel", root=root)
            fake_called = (root / "fake-git-called").exists()

        self.assertIsNone(error)
        assert completed is not None
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(Path(completed.stdout.decode("utf-8").strip()).resolve(), root.resolve())
        self.assertFalse(fake_called)

    def test_archive_replay_hook_child_python_uses_checker_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            hook = root / ".githooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("python3 -c 'import sys; print(sys.executable)'\n", encoding="utf-8")
            checker = load_checker()

            completed, error = checker.run_archive_command("sh .githooks/pre-commit", root=root)

        self.assertIsNone(error)
        assert completed is not None
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        replay_python = Path(completed.stdout.decode("utf-8").strip()).resolve()
        self.assertEqual(replay_python, Path(sys.executable).resolve())

    def test_governance_git_helper_does_not_trust_caller_path(self) -> None:
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
            checker = load_checker()
            env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}

            with mock.patch.dict(os.environ, env, clear=False):
                result = checker.git(root, ["rev-parse", "--show-toplevel"])
            fake_called = (root / "fake-git-called").exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), root.resolve())
        self.assertFalse(fake_called)

    def test_governance_git_env_ignores_global_config_locations(self) -> None:
        checker = load_checker()
        with mock.patch.dict(
            os.environ,
            {
                "HOME": "/tmp/fake-home",
                "XDG_CONFIG_HOME": "/tmp/fake-xdg",
                "GIT_CONFIG_GLOBAL": "/tmp/fake-gitconfig",
            },
            clear=False,
        ):
            env = checker.git_env()

        self.assertNotIn("HOME", env)
        self.assertNotIn("XDG_CONFIG_HOME", env)
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], os.devnull)
        self.assertNotIn(str(Path(sys.executable).resolve().parent), checker.TRUSTED_REPLAY_PATH_ENTRIES)

    def test_check_pointer_replay_snapshot_ignores_caller_git_environment(self) -> None:
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
            env = os.environ.copy()
            env.update(
                {
                    "GIT_DIR": str(other / ".git"),
                    "GIT_WORK_TREE": str(other),
                    "GIT_INDEX_FILE": str(other / ".git" / "index"),
                    "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
                }
            )

            check_pointer = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
                env=env,
            )

        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(check_pointer.returncode, 0, check_pointer.stderr)

    def test_write_pointer_rejects_symlinked_archive_artifact_ref_without_target_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            artifact_path = root / artifact_rel
            target_path = root / "docs" / "note.md"
            target_before = target_path.read_text(encoding="utf-8")
            artifact_path.unlink()
            artifact_path.symlink_to(target_path)

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)
            target_after = target_path.read_text(encoding="utf-8")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command evidence artifact could not be read", result.stderr)
        self.assertEqual(target_after, target_before)

    def test_publish_commits_pointer_bound_archive_bytes_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"

            publish = run_cli(
                "--root",
                str(root),
                "publish",
                "--packet",
                packet_rel,
                "--pointer",
                pointer_rel,
                "--message",
                "publish via wrapper",
            )
            committed = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout.splitlines()
            check_pointer = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )
            status = git(root, "status", "--short").stdout

        self.assertEqual(publish.returncode, 0, publish.stderr)
        self.assertIn(f"published active pointer: {pointer_rel}", publish.stdout)
        self.assertEqual(sorted(committed), sorted([packet_rel, artifact_rel, pointer_rel]))
        self.assertEqual(check_pointer.returncode, 0, check_pointer.stderr)
        self.assertEqual(status, "")

    def test_publish_rejects_uncommitted_content_dirt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            (root / "docs" / "note.md").write_text("initial\nuncommitted\n", encoding="utf-8")

            publish = run_cli(
                "--root",
                str(root),
                "publish",
                "--packet",
                packet_rel,
                "--pointer",
                "archive/v2/pointers/pkt-archived-pointer-test.yml",
                "--message",
                "publish via wrapper",
            )

        self.assertNotEqual(publish.returncode, 0)
        self.assertIn("content commits first", publish.stderr)
        self.assertIn("docs/note.md", publish.stderr)

    def test_write_pointer_rejects_symlinked_packet_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            alias_rel = "archive/v2/packets/pkt-alias.yml"
            (root / alias_rel).symlink_to(Path(packet_rel).name)

            result = run_cli("--root", str(root), "write-pointer", "--packet", alias_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archived packet must be a regular file, not a symlink", result.stderr)

    def test_write_pointer_rejects_pointer_output_without_yaml_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)

            result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                "archive/v2/pointers/pkt-noext",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active pointer path must end with .yml or .yaml", result.stderr)

    def test_check_accepts_plan_02_fixtures(self) -> None:
        for path in sorted(FIXTURE_ROOT.glob("*.yml")):
            with self.subTest(path=path.name):
                result = run_cli("check", "--packet", str(path))

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_output_separates_valid_from_stable(self) -> None:
        nonstable = run_cli("check", "--packet", str(FIXTURE_ROOT / "worktree-nonstable.yml"))
        stable = run_cli("check", "--packet", str(FIXTURE_ROOT / "finalized-routine.yml"), "--require-stable")

        self.assertEqual(nonstable.returncode, 0, nonstable.stderr)
        self.assertIn("VALID: not stable-handoff eligible", nonstable.stdout)
        self.assertNotIn("PASS", nonstable.stdout)
        self.assertEqual(stable.returncode, 0, stable.stderr)
        self.assertIn("STABLE:", stable.stdout)

    def test_require_stable_rejects_valid_nonstable_packet(self) -> None:
        result = run_cli(
            "check",
            "--packet",
            str(FIXTURE_ROOT / "worktree-nonstable.yml"),
            "--require-stable",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not stable-handoff eligible", result.stderr)

    def test_write_and_check_pointer_accept_archive_bound_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"

            write_result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
            )
            check_result = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )

            self.assertEqual(write_result.returncode, 0, write_result.stderr)
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            pointer = yaml.safe_load((root / pointer_rel).read_text(encoding="utf-8"))["AcceptancePacketPointer"]
            self.assertEqual(pointer["packet_id"], "pkt-archived-pointer-test")
            self.assertEqual(pointer["packet_ref"], packet_rel)
            self.assertEqual(pointer["packet_sha256"], packet_sha)
            self.assertEqual(pointer["checker_version"], "v2.0-draft")
            self.assertEqual(pointer["inference_rule_version"], "v2.0-draft")
            boundary_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            command = f"git diff --check {boundary_ref}...{boundary_ref}"
            self.assertEqual(pointer["head_commit"], boundary_ref)
            self.assertRegex(pointer["archive_commit"], r"^[0-9a-f]{40}$")
            self.assertEqual(pointer["stable_target"], f"base-ref:{boundary_ref}...{boundary_ref}@{boundary_ref}")
            self.assertEqual(pointer["decision_status"], "accepted")
            self.assertEqual(pointer["claim_artifacts"], [])
            self.assertEqual(pointer["review_import_artifacts"], [])
            self.assertEqual(pointer["probe_transcripts"], [])
            self.assertEqual(
                pointer["command_artifacts"],
                [
                    {
                        "artifact_ref": f"file:{artifact_rel}",
                        "artifact_sha256": hashlib.sha256((root / artifact_rel).read_bytes()).hexdigest(),
                        "command": command,
                    }
                ],
            )

    def test_check_pointer_rejects_checker_or_inference_version_drift(self) -> None:
        for field in ("checker_version", "inference_rule_version"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                init_repo(root)
                packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
                pointer_rel = "archive/v2/pointers/pkt-version-boundary.yml"
                write_result = run_cli(
                    "--root",
                    str(root),
                    "write-pointer",
                    "--packet",
                    packet_rel,
                    "--output",
                    pointer_rel,
                )
                pointer_path = root / pointer_rel
                pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
                pointer_doc["AcceptancePacketPointer"][field] = "v2.0-legacy"
                pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")

                result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

            self.assertEqual(write_result.returncode, 0, write_result.stderr)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"{field} must be v2.0-draft", result.stderr)

    def test_write_pointer_overwrite_regenerates_existing_replay_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            first_write = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
            )

            second_write = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
                "--overwrite",
            )
            check_result = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )
            artifact_text = (root / artifact_rel).read_text(encoding="utf-8")

        self.assertEqual(first_write.returncode, 0, first_write.stderr)
        self.assertEqual(second_write.returncode, 0, second_write.stderr)
        self.assertEqual(check_result.returncode, 0, check_result.stderr)
        self.assertEqual(artifact_text.count("replay_metadata: pointer-bound"), 1)
        self.assertEqual(artifact_text.count("stdout_sha256:"), 1)

    def test_write_pointer_refreshes_stale_command_artifact_packet_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _old_packet_sha = write_archived_base_ref_packet(root)
            packet_path = root / packet_rel
            packet_doc = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            packet_doc["AcceptancePacket"]["result"]["decision"]["reason"] = "Accepted after imported review."
            packet_path.write_text(yaml.safe_dump(packet_doc, sort_keys=False), encoding="utf-8")
            refreshed_packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"

            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            artifact_text = (root / artifact_rel).read_text(encoding="utf-8")
            check_result = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertIn(f"packet_sha256: {refreshed_packet_sha}", artifact_text)
        self.assertEqual(check_result.returncode, 0, check_result.stderr)

    def test_write_pointer_rejects_archived_mutable_boundary_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(
                root,
                mutable_boundary_refs=True,
            )
            artifact_before = (root / artifact_rel).read_text(encoding="utf-8")

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)
            artifact_after = (root / artifact_rel).read_text(encoding="utf-8")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active base-ref stable packet baseline_ref must be a full commit SHA", result.stderr)
        self.assertEqual(artifact_after, artifact_before)

    def test_finalize_archive_base_ref_materializes_stable_artifact_for_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "second")
            base_commit = git(root, "rev-parse", "HEAD~1").stdout.strip()
            packet_rel = "archive/v2/packets/pkt-finalize-pointer.yml"
            pointer_rel = "archive/v2/pointers/pkt-finalize-pointer.yml"
            runner_path = root / "scripts" / "check-governance-acceptance.py"
            runner_path.parent.mkdir(parents=True, exist_ok=True)
            runner_path.write_text("# archive pointer fixture runner ref\n", encoding="utf-8")

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--base-ref",
                "HEAD~1",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")
            stable = run_cli("--root", str(root), "check", "--packet", packet_rel, "--require-stable")
            write_pointer_result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
            )
            check_pointer_result = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            artifact_ref = packet["result"]["evidence"]["command_results"][0]["artifact_ref"]
            artifact_rel = artifact_ref.removeprefix("file:")
            artifact_text = (root / artifact_rel).read_text(encoding="utf-8")
            accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()

            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertEqual(finalize.returncode, 0, finalize.stderr)
            self.assertEqual(stable.returncode, 0, stable.stderr)
            self.assertEqual(write_pointer_result.returncode, 0, write_pointer_result.stderr)
            self.assertEqual(check_pointer_result.returncode, 0, check_pointer_result.stderr)
            self.assertTrue(packet["result"]["decision"]["stable_handoff_eligible"])
            self.assertEqual(packet["input"]["source_refs"], [])
            self.assertEqual(packet["result"]["evidence"]["accepted_head_commit"], accepted_head)
            self.assertTrue(artifact_rel.startswith("archive/v2/artifacts/"))
            self.assertIn(f"packet_ref: {packet_rel}", artifact_text)
            self.assertIn(f"command: git diff --check {base_commit}...{accepted_head}", artifact_text)
            self.assertIn("replay_metadata: pointer-bound", artifact_text)

    def test_start_base_ref_defaults_to_archive_packet_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )
            packet_ref = start.stdout.strip().removeprefix("wrote start packet: ")

            self.assertEqual(start.returncode, 0, start.stderr)
            self.assertTrue(packet_ref.startswith("archive/v2/packets/"))
            self.assertTrue(packet_ref.endswith(".yml"))
            self.assertTrue((root / packet_ref).is_file())

    def test_start_base_ref_rejects_non_archive_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                "packet.yml",
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )

        self.assertNotEqual(start.returncode, 0)
        self.assertIn("active base-ref start output must be an archived packet path", start.stderr)
        self.assertIn("omit --output to use the default archive path", start.stderr)

    def test_start_non_base_ref_modes_require_explicit_output(self) -> None:
        for args in (("--staged",), ("--worktree",)):
            with self.subTest(args=args), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                init_repo(root)

                start = run_cli(
                    "--root",
                    str(root),
                    "start",
                    "--intent",
                    "Update local docs.",
                    *args,
                )

                self.assertNotEqual(start.returncode, 0)
                self.assertIn("start --staged and start --worktree require --output", start.stderr)
                self.assertIn("archive defaults are base-ref only", start.stderr)

    def test_worktree_packet_cannot_satisfy_stable_handoff_or_pointer_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("dirty local worktree update\n", encoding="utf-8")
            packet_rel = "archive/v2/packets/pkt-worktree-nonstable.yml"
            pointer_rel = "archive/v2/pointers/pkt-worktree-nonstable.yml"

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Inspect dirty worktree.",
                "--worktree",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--worktree")
            valid = run_cli("--root", str(root), "check", "--packet", packet_rel)
            stable = run_cli("--root", str(root), "check", "--packet", packet_rel, "--require-stable")
            write_pointer = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
            )

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertIn("VALID: not stable-handoff eligible", valid.stdout)
        self.assertNotEqual(stable.returncode, 0)
        self.assertIn("not stable-handoff eligible", stable.stderr)
        self.assertNotEqual(write_pointer.returncode, 0)
        self.assertIn("not stable-handoff eligible", write_pointer.stderr)

    def test_active_gate_changes_require_non_circular_release_evidence(self) -> None:
        checker = load_checker()
        packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))[
            "AcceptancePacket"
        ]
        packet["result"]["inference"]["changed_paths"] = ["scripts/check-active-packet-gate.py"]

        required = checker.checker_required_evidence(packet)

        self.assertIn("python3 scripts/verify-release.py --list --base-ref origin/main --skip-clean-worktree", required)
        self.assertIn("python3 -m unittest tests/test_active_packet_gate.py tests/test_verify_release.py", required)
        self.assertNotIn("python3 scripts/check-active-packet-gate.py --base-ref origin/main", required)

    def test_bundled_release_gate_and_archive_changes_accumulate_evidence(self) -> None:
        checker = load_checker()
        packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))[
            "AcceptancePacket"
        ]
        packet["result"]["inference"]["changed_paths"] = [
            "scripts/check-active-packet-gate.py",
            "archive/v1/example.yml",
        ]

        required = checker.checker_required_evidence(packet)

        self.assertIn("python3 scripts/verify-release.py --list --base-ref origin/main --skip-clean-worktree", required)
        self.assertIn("python3 -m unittest tests/test_active_packet_gate.py tests/test_verify_release.py", required)
        self.assertIn("python3 scripts/check-v1-archive-boundary.py --base-ref origin/main", required)
        self.assertNotIn("python3 scripts/verify-release.py", required)

    def test_pre_commit_hook_changes_require_hook_evidence(self) -> None:
        checker = load_checker()
        packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))[
            "AcceptancePacket"
        ]
        packet["result"]["inference"]["changed_paths"] = [".githooks/pre-commit"]

        required = checker.checker_required_evidence(packet)

        self.assertIn("python3 scripts/verify-release.py --list --base-ref origin/main --skip-clean-worktree", required)
        self.assertIn("sh .githooks/pre-commit", required)
        self.assertIn("python3 -m unittest tests/test_pre_commit_hook.py tests/test_active_packet_gate.py", required)
        self.assertNotIn("python3 scripts/check-active-packet-gate.py --base-ref origin/main", required)

    def test_active_gate_changes_require_release_integration_review(self) -> None:
        checker = load_checker()
        packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))[
            "AcceptancePacket"
        ]
        packet["result"]["inference"]["changed_paths"] = ["scripts/check-active-packet-gate.py"]

        required = checker.checker_required_review(packet, root=ROOT)

        self.assertIn("checker correctness", required)
        self.assertIn("release integration", required)

    def test_finalize_base_ref_materializes_plan08_required_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts" / "verify-release.py").write_text(
                "import sys\nprint('release list ok')\n",
                encoding="utf-8",
            )
            (root / "scripts" / "check-active-packet-gate.py").write_text("print('old gate')\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_active_packet_gate.py").write_text(
                "import unittest\n\nclass ActiveGateEvidenceTest(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_verify_release.py").write_text(
                "import unittest\n\nclass VerifyReleaseEvidenceTest(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            git(root, "add", "-A")
            git(root, "commit", "-m", "add release gate fixtures")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "check-active-packet-gate.py").write_text("print('new gate')\n", encoding="utf-8")
            git(root, "add", "scripts/check-active-packet-gate.py")
            git(root, "commit", "-m", "change active gate")

            start = run_cli("--root", str(root), "start", "--intent", "Update active gate.", "--base-ref", base_ref)
            packet_ref = start.stdout.strip().removeprefix("wrote start packet: ")
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_ref, "--base-ref", base_ref)
            packet = yaml.safe_load((root / packet_ref).read_text(encoding="utf-8"))["AcceptancePacket"]
            artifact_refs = [
                item["artifact_ref"]
                for item in packet["result"]["evidence"]["command_results"]
                if isinstance(item, dict)
            ]
            artifact_paths_exist = [
                (root / artifact_ref.removeprefix("file:")).is_file()
                for artifact_ref in artifact_refs
                if artifact_ref.startswith("file:")
            ]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        expected = {
            f"python3 scripts/verify-release.py --list --base-ref {base_ref} --skip-clean-worktree",
            "python3 -m unittest tests/test_active_packet_gate.py tests/test_verify_release.py",
        }
        self.assertEqual(set(packet["result"]["inference"]["required_evidence"]), expected)
        self.assertEqual(set(packet["result"]["evidence"]["evaluator_boundary"]["commands"]), expected)
        self.assertEqual(
            {item["command"] for item in packet["result"]["evidence"]["command_results"]},
            expected,
        )
        self.assertFalse(packet["result"]["decision"]["stable_handoff_eligible"])
        for item in packet["result"]["evidence"]["command_results"]:
            self.assertEqual(item["status"], "pass")
            self.assertTrue(item["artifact_ref"].startswith("file:archive/v2/artifacts/"))
        self.assertEqual(artifact_paths_exist, [True, True])

    def test_archive_replay_materializes_fixed_release_gate_evidence(self) -> None:
        checker = load_checker()
        head = git(ROOT, "rev-parse", "HEAD").stdout.strip()
        command = f"python3 scripts/verify-release.py --list --base-ref {head} --skip-clean-worktree"
        with tempfile.TemporaryDirectory(dir=FIXTURE_ROOT) as tmpdir:
            artifact_path = Path(tmpdir) / "release-gate-evidence.log"
            artifact_ref = f"file:{artifact_path.relative_to(ROOT).as_posix()}"
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-release-gate-evidence",
                        "packet_ref: archive/v2/packets/pkt-release-gate-evidence.yml",
                        f"packet_sha256: {'0' * 64}",
                        f"command: {command}",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            updated, error = checker.archive_command_artifact_updated_text(
                ROOT,
                artifact_ref,
                identity={
                    "packet_id": "pkt-release-gate-evidence",
                    "packet_ref": "archive/v2/packets/pkt-release-gate-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
            )

        self.assertIsNone(error)
        assert updated is not None
        self.assertIn("replay_metadata: pointer-bound", updated)
        self.assertIn("exit_code: 0", updated)
        stdout_line = next(line for line in updated.splitlines() if line.startswith("stdout_sha256:"))
        self.assertNotEqual(stdout_line, "stdout_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertIsNone(
            checker.command_evidence_record_error(
                updated,
                root=ROOT,
                identity={
                    "packet_id": "pkt-release-gate-evidence",
                    "packet_ref": "archive/v2/packets/pkt-release-gate-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
                require_archive_replay_metadata=True,
                require_safe_archive_replay_command=True,
                require_empty_pass_replay_hashes=True,
            )
        )
        forged_empty_stdout = "\n".join(
            "stdout_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            if line.startswith("stdout_sha256:")
            else line
            for line in updated.splitlines()
        ) + "\n"
        self.assertEqual(
            checker.command_evidence_record_error(
                forged_empty_stdout,
                root=ROOT,
                identity={
                    "packet_id": "pkt-release-gate-evidence",
                    "packet_ref": "archive/v2/packets/pkt-release-gate-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
                require_archive_replay_metadata=True,
                require_safe_archive_replay_command=True,
                replay_archive_command=True,
            ),
            "command replay stdout hash mismatch",
        )

    def test_archive_replay_normalizes_unittest_output_hashes(self) -> None:
        checker = load_checker()
        command = "python3 -m unittest tests/test_active_packet_gate.py tests/test_verify_release.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "scripts").mkdir()
            (root / "scripts" / "check-governance-acceptance.py").write_text("# checker\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_active_packet_gate.py").write_text(
                "import unittest\n\nclass ActiveGateEvidenceTest(unittest.TestCase):\n"
                "    def test_ok(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_verify_release.py").write_text(
                "import unittest\n\nclass VerifyReleaseEvidenceTest(unittest.TestCase):\n"
                "    def test_ok(self):\n        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            artifact_rel = "archive/v2/artifacts/unittest-evidence.log"
            artifact_path = root / artifact_rel
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-unittest-evidence",
                        "packet_ref: archive/v2/packets/pkt-unittest-evidence.yml",
                        f"packet_sha256: {'0' * 64}",
                        f"command: {command}",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            updated, error = checker.archive_command_artifact_updated_text(
                root,
                f"file:{artifact_rel}",
                identity={
                    "packet_id": "pkt-unittest-evidence",
                    "packet_ref": "archive/v2/packets/pkt-unittest-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
            )
            assert updated is not None
            replay_error = checker.command_evidence_record_error(
                updated,
                root=root,
                identity={
                    "packet_id": "pkt-unittest-evidence",
                    "packet_ref": "archive/v2/packets/pkt-unittest-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
                require_archive_replay_metadata=True,
                require_safe_archive_replay_command=True,
                replay_archive_command=True,
            )
            forged_stderr = "\n".join(
                "stderr_sha256: " + ("1" * 64) if line.startswith("stderr_sha256:") else line
                for line in updated.splitlines()
            ) + "\n"
            empty_hash_error = checker.command_evidence_record_error(
                forged_stderr,
                root=root,
                identity={
                    "packet_id": "pkt-unittest-evidence",
                    "packet_ref": "archive/v2/packets/pkt-unittest-evidence.yml",
                    "packet_sha256": "0" * 64,
                    "command": command,
                },
                status="pass",
                require_archive_replay_metadata=True,
                require_safe_archive_replay_command=True,
                require_empty_pass_replay_hashes=True,
            )

        self.assertIsNone(error)
        self.assertIn("stdout_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", updated)
        self.assertIn("stderr_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", updated)
        self.assertIsNone(replay_error)
        self.assertEqual(empty_hash_error, "pass archive command evidence must record empty stderr hash")

    def test_finalize_base_ref_ignores_committed_archive_draft_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel = "archive/v2/packets/pkt-draft-in-work-commit.yml"
            pointer_rel = "archive/v2/pointers/pkt-draft-in-work-commit.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with draft packet")
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")
            stable = run_cli("--root", str(root), "check", "--packet", packet_rel, "--require-stable")
            write_pointer_result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
            )
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            check_pointer_result = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(stable.returncode, 0, stable.stderr)
        self.assertEqual(write_pointer_result.returncode, 0, write_pointer_result.stderr)
        self.assertEqual(check_pointer_result.returncode, 0, check_pointer_result.stderr)
        self.assertEqual(packet["result"]["inference"]["changed_paths"], ["docs/note.md"])
        self.assertNotIn(packet_rel, packet["result"]["inference"]["changed_paths"])

    def test_finalize_base_ref_rejects_committed_unexpected_archive_dirt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel = "archive/v2/packets/pkt-draft-with-hidden-archive-dirt.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            unexpected = root / "archive/v2/artifacts/preexisting-unexpected.txt"
            unexpected.parent.mkdir(parents=True, exist_ok=True)
            unexpected.write_text("hidden accepted archive dirt\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with hidden archive dirt")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("active base-ref accepted_head includes unexpected archive/v2 paths", finalize.stderr)
        self.assertIn("archive/v2/artifacts/preexisting-unexpected.txt", finalize.stderr)

    def test_finalize_base_ref_rejects_unexpected_archive_dirt_before_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel = "archive/v2/packets/pkt-nonstable-with-hidden-archive-dirt.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update protected checker code.",
                "--base-ref",
                "HEAD",
            )
            (root / "scripts" / "check-governance-acceptance.py").write_text(
                "# protected checker change\n",
                encoding="utf-8",
            )
            unexpected = root / "archive/v2/artifacts/nonstable-unexpected.txt"
            unexpected.parent.mkdir(parents=True, exist_ok=True)
            unexpected.write_text("hidden accepted archive dirt\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "protected work with hidden archive dirt")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("active base-ref accepted_head includes unexpected archive/v2 paths", finalize.stderr)
        self.assertIn("archive/v2/artifacts/nonstable-unexpected.txt", finalize.stderr)

    def test_finalize_replays_required_hook_evidence_in_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel = "archive/v2/packets/pkt-hook-replay-snapshot.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update pre-commit hook.",
                "--base-ref",
                "HEAD",
            )
            hook = root / ".githooks" / "pre-commit"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("printf touched > finalize-hook-side-effect.txt\nexit 0\n", encoding="utf-8")
            git(root, "add", ".githooks/pre-commit")
            git(root, "commit", "-m", "update pre-commit hook")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")
            side_effect_exists = (root / "finalize-hook-side-effect.txt").exists()

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertFalse(side_effect_exists)

    def test_finalize_base_ref_allows_preexisting_archive_namespace_before_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            preexisting = root / "archive/v2/artifacts/preexisting-before-base.txt"
            preexisting.parent.mkdir(parents=True, exist_ok=True)
            preexisting.write_text("preexisting archive dirt\n", encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "preexisting archive dirt")
            packet_rel = "archive/v2/packets/pkt-draft-with-preexisting-archive-dirt.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with preexisting archive dirt")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)

    def test_finalize_base_ref_does_not_validate_preexisting_archive_pointer_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            preexisting = root / "archive/v2/artifacts/preexisting-whitelisted.txt"
            preexisting.parent.mkdir(parents=True, exist_ok=True)
            preexisting.write_text("preexisting archive dirt\n", encoding="utf-8")
            bogus_pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "bogus-preexisting-pointer",
                    "packet_ref": "archive/v2/packets/missing.yml",
                    "packet_sha256": "0" * 64,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": "0" * 40,
                    "comparison_ref": "0" * 40,
                    "head_commit": "0" * 40,
                    "archive_commit": "0" * 40,
                    "stable_target": "0" * 40,
                    "decision_status": "accepted",
                    "command_artifacts": [
                        {
                            "artifact_ref": "file:archive/v2/artifacts/preexisting-whitelisted.txt",
                            "artifact_sha256": hashlib.sha256(preexisting.read_bytes()).hexdigest(),
                            "command": "git diff --check HEAD...HEAD",
                        }
                    ],
                    "review_import_artifacts": [],
                    "probe_transcripts": [],
                }
            }
            pointer = root / "archive/v2/pointers/bogus-preexisting-pointer.yml"
            pointer.parent.mkdir(parents=True, exist_ok=True)
            pointer.write_text(yaml.safe_dump(bogus_pointer, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "bogus preexisting archive pointer")
            packet_rel = "archive/v2/packets/pkt-draft-with-invalid-preexisting-pointer.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with invalid preexisting pointer")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)

    def test_finalize_base_ref_does_not_execute_historical_pointer_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            side_effect_rel = "historical-finalize-side-effect.txt"
            artifact = root / "archive/v2/artifacts/historical-command.log"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            command = (
                "python3 -c \"from pathlib import Path; "
                f"Path('{side_effect_rel}').write_text('historical replay ran')\""
            )
            artifact.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: forged-historical-pointer",
                        "packet_ref: archive/v2/packets/missing.yml",
                        f"packet_sha256: {'0' * 64}",
                        f"command: {command}",
                        "status: pass",
                        "replay_metadata: pointer-bound",
                        "replay_recorded_by: scripts/check-governance-acceptance.py",
                        "replay_recorded_at: 2026-05-06",
                        "replay_checker_ref: scripts/check-governance-acceptance.py",
                        "exit_code: 0",
                        f"stdout_sha256: {'0' * 64}",
                        f"stderr_sha256: {'0' * 64}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            bogus_pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "forged-historical-pointer",
                    "packet_ref": "archive/v2/packets/missing.yml",
                    "packet_sha256": "0" * 64,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": "0" * 40,
                    "comparison_ref": "0" * 40,
                    "head_commit": "0" * 40,
                    "archive_commit": "0" * 40,
                    "stable_target": "base-ref:historical",
                    "decision_status": "accepted",
                    "command_artifacts": [
                        {
                            "artifact_ref": "file:archive/v2/artifacts/historical-command.log",
                            "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                            "command": command,
                        }
                    ],
                    "review_import_artifacts": [],
                    "probe_transcripts": [],
                }
            }
            pointer = root / "archive/v2/pointers/forged-historical-pointer.yml"
            pointer.parent.mkdir(parents=True, exist_ok=True)
            pointer.write_text(yaml.safe_dump(bogus_pointer, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "forged historical pointer")
            packet_rel = "archive/v2/packets/pkt-after-forged-historical-pointer.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs after forged historical pointer.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work after forged historical pointer")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")
            side_effect_exists = (root / side_effect_rel).exists()

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertFalse(side_effect_exists)

    def test_historical_pointer_cannot_whitelist_new_archive_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            future_rel = "archive/v2/artifacts/unexpected-after-base.txt"
            bogus_pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "historical-whitelist-attempt",
                    "packet_ref": "archive/v2/packets/missing.yml",
                    "packet_sha256": "0" * 64,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": "0" * 40,
                    "comparison_ref": "0" * 40,
                    "head_commit": "0" * 40,
                    "archive_commit": "0" * 40,
                    "stable_target": "base-ref:historical",
                    "decision_status": "accepted",
                    "command_artifacts": [
                        {
                            "artifact_ref": f"file:{future_rel}",
                            "artifact_sha256": "0" * 64,
                            "command": "git diff --check HEAD...HEAD",
                        }
                    ],
                    "review_import_artifacts": [],
                    "probe_transcripts": [],
                }
            }
            pointer = root / "archive/v2/pointers/historical-whitelist-attempt.yml"
            pointer.parent.mkdir(parents=True, exist_ok=True)
            pointer.write_text(yaml.safe_dump(bogus_pointer, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "historical pointer whitelist attempt")
            packet_rel = "archive/v2/packets/pkt-after-historical-whitelist-attempt.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs after a historical whitelist attempt.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            future_path = root / future_rel
            future_path.parent.mkdir(parents=True, exist_ok=True)
            future_path.write_text("unexpected new archive bytes\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with unexpected archive bytes")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("active base-ref accepted_head includes unexpected archive/v2 paths", finalize.stderr)
        self.assertIn(future_rel, finalize.stderr)

    def test_historical_pointer_fake_review_import_cannot_whitelist_new_archive_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            future_rel = "archive/v2/artifacts/fake-review-import-after-base.yml"
            bogus_pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "historical-fake-review-import",
                    "packet_ref": "archive/v2/packets/missing.yml",
                    "packet_sha256": "0" * 64,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": "0" * 40,
                    "comparison_ref": "0" * 40,
                    "head_commit": "0" * 40,
                    "archive_commit": "0" * 40,
                    "stable_target": "base-ref:historical",
                    "decision_status": "accepted",
                    "command_artifacts": [],
                    "review_import_artifacts": [
                        {
                            "source_ref": f"file:{future_rel}",
                            "source_sha256": "0" * 64,
                            "review_target_digest": "0" * 64,
                            "review_ids": ["fake-review"],
                        }
                    ],
                    "probe_transcripts": [],
                }
            }
            pointer = root / "archive/v2/pointers/historical-fake-review-import.yml"
            pointer.parent.mkdir(parents=True, exist_ok=True)
            pointer.write_text(yaml.safe_dump(bogus_pointer, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "historical fake review import pointer")
            packet_rel = "archive/v2/packets/pkt-after-historical-fake-review-import.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs after a fake historical review import.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            future_path = root / future_rel
            future_path.parent.mkdir(parents=True, exist_ok=True)
            future_path.write_text("not a review import wrapper\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work with fake review import bytes")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("active base-ref accepted_head includes unexpected archive/v2 paths", finalize.stderr)
        self.assertIn(future_rel, finalize.stderr)

    def test_finalize_base_ref_allows_prior_archive_publication_before_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            prior_packet_rel, _prior_artifact_rel, _prior_packet_sha = write_archived_base_ref_packet(root)
            prior_pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_prior = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                prior_packet_rel,
                "--output",
                prior_pointer_rel,
            )
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish prior archive pointer")
            packet_rel = "archive/v2/packets/pkt-draft-after-prior-pointer.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs after a prior archive publication.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work after prior archive pointer")

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")

        self.assertEqual(write_prior.returncode, 0, write_prior.stderr)
        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)

    def test_finalize_base_ref_with_prior_archive_publication_does_not_write_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            prior_packet_rel, _prior_artifact_rel, _prior_packet_sha = write_archived_base_ref_packet(root)
            prior_pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_prior = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                prior_packet_rel,
                "--output",
                prior_pointer_rel,
            )
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish prior archive pointer")
            packet_rel = "archive/v2/packets/pkt-draft-after-prior-pointer.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update local docs after a prior archive publication.",
                "--base-ref",
                "HEAD",
            )
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "work after prior archive pointer")
            before_objects = git_loose_object_count(root)

            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", "HEAD~1")
            after_objects = git_loose_object_count(root)

        self.assertEqual(write_prior.returncode, 0, write_prior.stderr)
        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(after_objects, before_objects)

    def test_check_pointer_accepts_committed_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_status_reports_published_active_pointer_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            publication = git(root, "rev-parse", "HEAD").stdout.strip()

            result = run_cli("--root", str(root), "status", "--base-ref", base_ref)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pointers: 1", result.stdout)
        self.assertIn(f"- pointer: {pointer_rel}", result.stdout)
        self.assertIn("packet_id: pkt-archived-pointer-test", result.stdout)
        self.assertIn(f"publication: {publication}", result.stdout)
        self.assertIn("audit: PASS", result.stdout)
        self.assertIn("pending_packets: 0", result.stdout)

    def test_status_reports_invalid_pointer_without_failing_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            pointer_path = root / pointer_rel
            pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer["AcceptancePacketPointer"]["packet_sha256"] = "0" * 64
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "status", "--base-ref", base_ref)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("audit: FAIL", result.stdout)
        self.assertIn("packet_sha256 does not match archived packet bytes", result.stdout)

    def test_status_reports_pending_stable_packet_before_pointer_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)

            result = run_cli("--root", str(root), "status", "--base-ref", base_ref)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pointers: 0", result.stdout)
        self.assertIn("pending_packets: 1", result.stdout)
        self.assertIn(f"- packet: {packet_rel}", result.stdout)
        self.assertIn("status: READY", result.stdout)

    def test_check_pointer_accepts_historical_publication_after_later_content_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            (root / "docs" / "note.md").write_text("initial\nlater content\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "later content after publication")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_pointer_accepts_historical_publication_after_later_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            first_packet, _first_artifact, _first_packet_sha = write_archived_base_ref_packet(
                root,
                packet_id="pkt-first-publication",
            )
            first_pointer = "archive/v2/pointers/pkt-first-publication.yml"
            write_first = run_cli("--root", str(root), "write-pointer", "--packet", first_packet, "--output", first_pointer)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish first archive pointer")
            second_packet, _second_artifact, _second_packet_sha = write_archived_base_ref_packet(
                root,
                packet_id="pkt-second-publication",
            )
            second_pointer = "archive/v2/pointers/pkt-second-publication.yml"
            write_second = run_cli("--root", str(root), "write-pointer", "--packet", second_packet, "--output", second_pointer)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish second archive pointer")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", first_pointer, "--replay-command-evidence")

        self.assertEqual(write_first.returncode, 0, write_first.stderr)
        self.assertEqual(write_second.returncode, 0, write_second.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_pointer_uses_accepted_head_not_later_head_for_archived_review_recomputation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel = "archive/v2/packets/pkt-ambient-head-proof.yml"
            pointer_rel = "archive/v2/pointers/pkt-ambient-head-proof.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Update docs without proof-like claims.",
                "--base-ref",
                base_ref,
            )
            (root / "docs" / "note.md").write_text("initial\nplain docs update\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "plain docs update")
            finalize = run_cli("--root", str(root), "finalize", "--packet", packet_rel, "--base-ref", base_ref)
            write_pointer = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish plain docs pointer")
            (root / "docs" / "note.md").write_text(
                "initial\nplain docs update\nlater release-ready claim\n",
                encoding="utf-8",
            )
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "later proof-like docs content")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertEqual(write_pointer.returncode, 0, write_pointer.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_pointer_finds_publication_after_intermediate_content_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            (root / "docs" / "note.md").write_text("initial\nintermediate content\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "content before archive publication")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_pointer_rejects_reverted_archive_rewrite_after_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            artifact_path = root / artifact_rel
            pointer_path = root / pointer_rel
            original_artifact = artifact_path.read_text(encoding="utf-8")
            original_pointer = pointer_path.read_text(encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
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

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("current HEAD history includes archive/v2 changes after active pointer publication", result.stderr)
        self.assertIn("pointer-bound bytes", result.stderr)
        self.assertIn(artifact_rel, result.stderr)

    def test_check_pointer_rejects_invalid_pointer_before_replay_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root, replay_metadata=True)
            side_effect_rel = "check-pointer-side-effect.txt"
            command = (
                "python3 -c \"from pathlib import Path; "
                f"Path('{side_effect_rel}').write_text('replay ran')\""
            )
            packet_path = root / packet_rel
            packet_doc = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            packet["result"]["inference"]["required_evidence"] = [command]
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["command_results"][0]["command"] = command
            packet_sha = rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)
            artifact_path = root / artifact_rel
            artifact_lines = artifact_path.read_text(encoding="utf-8").splitlines()
            command_index = next(index for index, line in enumerate(artifact_lines) if line.startswith("command:"))
            artifact_lines[command_index] = f"command: {command}"
            artifact_path.write_text("\n".join(artifact_lines) + "\n", encoding="utf-8")
            checker = load_checker()
            archive_commit, archive_commit_error = checker.create_archive_commit(root, packet, packet_ref=packet_rel)
            self.assertIsNone(archive_commit_error)
            pointer = checker.pointer_for_packet(
                packet,
                root=root,
                packet_ref=packet_rel,
                packet_sha256=packet_sha,
                archive_commit=archive_commit,
            )
            pointer["archive_commit"] = "0" * 40
            pointer_rel = "archive/v2/pointers/pkt-invalid-before-replay.yml"
            (root / pointer_rel).parent.mkdir(parents=True, exist_ok=True)
            (root / pointer_rel).write_text(
                yaml.safe_dump({"AcceptancePacketPointer": pointer}, sort_keys=False),
                encoding="utf-8",
            )

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")
            side_effect_exists = (root / side_effect_rel).exists()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive_commit does not match reproducible pointer-bound archive bytes", result.stderr)
        self.assertFalse(side_effect_exists)

    def test_check_pointer_accepts_committed_archive_publication_after_no_local_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            parent = Path(tmpdir)
            root = parent / "source"
            root.mkdir()
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            pointer = yaml.safe_load((root / pointer_rel).read_text(encoding="utf-8"))["AcceptancePacketPointer"]
            archive_commit = pointer["archive_commit"]
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            clone = parent / "clone"
            git(parent, "clone", "--no-local", str(root), str(clone))
            archive_commit_type = subprocess.run(
                ["git", "cat-file", "-t", archive_commit],
                cwd=clone,
                encoding="utf-8",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            before_objects = git_loose_object_count(clone)

            result = run_cli("--root", str(clone), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")
            after_objects = git_loose_object_count(clone)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(archive_commit_type.returncode, 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(after_objects, before_objects)

    def test_check_pointer_rejects_published_pointer_archive_commit_relabel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer_doc["AcceptancePacketPointer"]["archive_commit"] = "0" * 40
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish relabeled archive pointer")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive_commit does not match reproducible pointer-bound archive bytes", result.stderr)

    def test_check_pointer_rejects_relabel_after_archive_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            artifact_path = root / artifact_rel
            artifact_path.write_text(
                artifact_path.read_text(encoding="utf-8").replace(
                    "summary: archived pointer fixture command evidence",
                    "summary: relabeled pointer fixture command evidence",
                ),
                encoding="utf-8",
            )
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer = pointer_doc["AcceptancePacketPointer"]
            pointer["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            archive_commit = synthetic_archive_commit(root, packet_rel)
            pointer["archive_commit"] = archive_commit
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "relabel archive pointer")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("historical pointer publication command_artifacts[0] bytes do not match artifact_sha256", result.stderr)

    def test_check_pointer_rejects_unexpected_archive_commit_only_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer_doc["AcceptancePacketPointer"]["archive_commit"] = synthetic_archive_commit_with_extra_path(
                root,
                packet_rel,
                "archive/v2/artifacts/unexpected-in-archive-commit-only.txt",
            )
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive_commit includes unexpected archive/v2 paths", result.stderr)

    def test_check_pointer_rejects_stale_active_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "commit", "--allow-empty", "-m", "advance head")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("head_commit does not match current HEAD or first archive/v2 publication commit", result.stderr)

    def test_check_pointer_accepts_dirty_non_archive_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            (root / "docs" / "note.md").write_text("dirty after pointer\n", encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_write_pointer_ignores_unrelated_untracked_worktree_dirt(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            (root / "local-scratch.txt").write_text("local scratch\n", encoding="utf-8")

            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)

    def test_check_pointer_rejects_unexpected_prepublication_archive_dirty_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            unexpected = root / "archive/v2/artifacts/unexpected-local.txt"
            unexpected.write_text("unexpected local archive dirt\n", encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active pointer worktree includes non-publication changes", result.stderr)
        self.assertIn("archive/v2/artifacts/unexpected-local.txt", result.stderr)

    def test_write_pointer_rejects_prepublication_archive_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            first_write = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "add", "archive/v2")
            git(root, "commit", "-m", "publish archive pointer")
            write_archived_base_ref_packet(
                root,
                packet_id="pkt-archived-pointer-test",
                artifact_rel=artifact_rel,
            )

            second_write = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
                "--overwrite",
            )

        self.assertEqual(first_write.returncode, 0, first_write.stderr)
        self.assertNotEqual(second_write.returncode, 0)
        self.assertIn("active pointer worktree may only add publication paths", second_write.stderr)
        self.assertIn(packet_rel, second_write.stderr)
        self.assertIn(artifact_rel, second_write.stderr)

    def test_check_pointer_rejects_non_archive_head_after_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            (root / "docs" / "note.md").write_text("changed after acceptance\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "change docs after acceptance")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("head_commit does not match current HEAD or first archive/v2 publication commit", result.stderr)

    def test_check_pointer_rejects_pointer_only_head_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            git(root, "commit", "--allow-empty", "-m", "advance head")
            current_head = git(root, "rev-parse", "HEAD").stdout.strip()
            pointer_path = root / pointer_rel
            pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer["AcceptancePacketPointer"]["head_commit"] = current_head
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel, "--replay-command-evidence")

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("head_commit does not match archived packet accepted_head_commit", result.stderr)

    def test_check_pointer_requires_archive_commit_packet_and_artifact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            pointer_path = root / pointer_rel
            pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer["AcceptancePacketPointer"]["archive_commit"] = pointer["AcceptancePacketPointer"]["head_commit"]
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive_commit does not contain packet_ref", result.stderr)

    def test_archive_commit_binds_review_import_and_probe_transcript_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            review_rel = "archive/v2/artifacts/pkt-review-import.yml"
            probe_rel = "archive/v2/artifacts/pkt-review-probe.yml"
            review_path = root / review_rel
            probe_path = root / probe_rel
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                yaml.safe_dump(
                    {
                        "AcceptancePacketReviewImport": {
                            "schema_version": "acceptance-packet-review-import/v1",
                            "target_binding": {},
                            "MultiReviewResult": {
                                "critics": [
                                    {
                                        "critic_id": "archive-byte-binding",
                                        "probe_evidence_refs": [f"file:{probe_rel}"],
                                    }
                                ]
                            },
                            "review_lineage": [],
                        }
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            probe_path.write_text(
                yaml.safe_dump(
                    {
                        "ProbeTranscript": {
                            "result_ref": f"file:{review_rel}",
                            "result_digest": "1" * 64,
                            "packet_ref": packet_rel,
                            "packet_sha256": "2" * 64,
                        }
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            evidence = packet_doc["AcceptancePacket"]["result"]["evidence"]
            evidence["review_imports"] = [
                {
                    "source_ref": f"file:{review_rel}",
                    "format": "acceptance-packet-review-import/v1",
                    "source_digest": hashlib.sha256(review_path.read_bytes()).hexdigest(),
                    "status": "imported",
                    "review_ids": ["review-archive-byte-binding"],
                    "target_binding": {"review_target_digest": "3" * 64},
                }
            ]
            packet_sha = rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)
            checker = load_checker()
            packet = packet_doc["AcceptancePacket"]
            archive_commit = synthetic_archive_commit(root, packet_rel)
            pointer = checker.pointer_for_packet(
                packet,
                root=root,
                packet_ref=packet_rel,
                packet_sha256=packet_sha,
                archive_commit=archive_commit,
            )

            clean_errors = checker.archive_commit_tree_errors(pointer, root=root, packet_ref=packet_rel)
            review_path.write_text(review_path.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
            review_drift_pointer = yaml.safe_load(yaml.safe_dump(pointer, sort_keys=False))
            review_drift_pointer["review_import_artifacts"][0]["source_sha256"] = hashlib.sha256(
                review_path.read_bytes()
            ).hexdigest()
            review_errors = checker.archive_commit_tree_errors(review_drift_pointer, root=root, packet_ref=packet_rel)
            probe_path.write_text(probe_path.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
            probe_drift_pointer = yaml.safe_load(yaml.safe_dump(pointer, sort_keys=False))
            probe_drift_pointer["probe_transcripts"][0]["transcript_sha256"] = hashlib.sha256(
                probe_path.read_bytes()
            ).hexdigest()
            probe_errors = checker.archive_commit_tree_errors(probe_drift_pointer, root=root, packet_ref=packet_rel)

        self.assertEqual(clean_errors, [])
        self.assertIn("archive_commit review_import_artifacts[0] bytes do not match source_sha256", review_errors)
        self.assertIn("archive_commit probe_transcripts[0] bytes do not match transcript_sha256", probe_errors)

    def test_finalize_base_ref_generates_head_pinned_source_refs_for_changed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_commit = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "docs" / "note.md").write_text("updated\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "update note")
            head_commit = git(root, "rev-parse", "HEAD").stdout.strip()
            packet_rel = "archive/v2/packets/source-ref-changed.yml"

            start_result = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Test generated source refs.",
                "--base-ref",
                base_commit,
            )
            finalize_result = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                packet_rel,
                "--base-ref",
                base_commit,
            )

            self.assertEqual(start_result.returncode, 0, start_result.stderr)
            self.assertEqual(finalize_result.returncode, 0, finalize_result.stderr)
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            expected_ref = f"git:{head_commit}:docs/note.md"
            evidence = packet["result"]["evidence"]
            self.assertEqual(packet["input"]["source_refs"], [])
            self.assertIn(expected_ref, evidence["source_refs"])
            self.assertIn(
                {
                    "origin": "generated",
                    "relation": "source",
                    "ref": expected_ref,
                    "status": "resolved",
                    "target": f"{head_commit}:docs/note.md",
                },
                evidence["resolved_refs"],
            )

    def test_finalize_base_ref_generates_comparison_pinned_source_refs_for_deleted_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            base_commit = git(root, "rev-parse", "HEAD").stdout.strip()
            git(root, "rm", "docs/note.md")
            git(root, "commit", "-m", "delete note")
            packet_rel = "archive/v2/packets/source-ref-deleted.yml"

            start_result = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                packet_rel,
                "--intent",
                "Test deleted source refs.",
                "--base-ref",
                base_commit,
            )
            finalize_result = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                packet_rel,
                "--base-ref",
                base_commit,
            )

            self.assertEqual(start_result.returncode, 0, start_result.stderr)
            self.assertEqual(finalize_result.returncode, 0, finalize_result.stderr)
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            expected_ref = f"git:{base_commit}:docs/note.md"
            evidence = packet["result"]["evidence"]
            self.assertEqual(packet["input"]["source_refs"], [])
            self.assertIn(expected_ref, evidence["source_refs"])
            self.assertIn(
                {
                    "origin": "generated",
                    "relation": "source",
                    "ref": expected_ref,
                    "status": "resolved",
                    "target": f"{base_commit}:docs/note.md",
                },
                evidence["resolved_refs"],
            )

    def test_check_pointer_rejects_archived_packet_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            self.assertEqual(
                run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel).returncode,
                0,
            )
            with (root / packet_rel).open("a", encoding="utf-8") as handle:
                handle.write("\n")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packet_sha256 does not match archived packet bytes", result.stderr)

    def test_check_pointer_rejects_command_artifact_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            self.assertEqual(
                run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel).returncode,
                0,
            )
            with (root / artifact_rel).open("a", encoding="utf-8") as handle:
                handle.write("post-pointer drift\n")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command_artifacts do not match archived packet command artifact bytes", result.stderr)

    def test_check_pointer_replay_rejects_forged_command_output_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            self.assertEqual(write_result.returncode, 0, write_result.stderr)
            artifact_path = root / artifact_rel
            lines = artifact_path.read_text(encoding="utf-8").splitlines()
            stdout_index = next(index for index, line in enumerate(lines) if line.startswith("stdout_sha256:"))
            lines[stdout_index] = "stdout_sha256: " + ("0" * 64)
            artifact_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            pointer_path = root / pointer_rel
            pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer["AcceptancePacketPointer"]["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(
                artifact_path.read_bytes()
            ).hexdigest()
            pointer["AcceptancePacketPointer"]["archive_commit"] = synthetic_archive_commit(root, packet_rel)
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            no_replay = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)
            replayed = run_cli(
                "--root",
                str(root),
                "check-pointer",
                "--pointer",
                pointer_rel,
                "--replay-command-evidence",
            )

        self.assertNotEqual(no_replay.returncode, 0)
        self.assertIn("pass archive command evidence must record empty stdout hash", no_replay.stderr)
        self.assertNotEqual(replayed.returncode, 0)
        self.assertIn("pass archive command evidence must record empty stdout hash", replayed.stderr)

    def test_write_pointer_rejects_non_archive_packet_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            non_archive = "packets/pkt-archived-pointer-test.yml"
            (root / non_archive).parent.mkdir(parents=True, exist_ok=True)
            (root / non_archive).write_text((root / packet_rel).read_text(encoding="utf-8"), encoding="utf-8")

            result = run_cli("--root", str(root), "write-pointer", "--packet", non_archive)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packet_ref must start with archive/v2/packets/", result.stderr)

    def test_check_pointer_rejects_hand_authored_command_evidence_without_replay_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, packet_sha = write_archived_base_ref_packet(root)
            artifact_sha = hashlib.sha256((root / artifact_rel).read_bytes()).hexdigest()
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            archive_commit = synthetic_archive_commit(root, packet_rel)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "pkt-archived-pointer-test",
                    "packet_ref": packet_rel,
                    "packet_sha256": packet_sha,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": evidence["baseline_ref"],
                    "comparison_ref": evidence["comparison_ref"],
                    "head_commit": evidence["accepted_head_commit"],
                    "archive_commit": archive_commit,
                    "stable_target": f"base-ref:{evidence['baseline_ref']}...{evidence['comparison_ref']}@{evidence['accepted_head_commit']}",
                    "decision_status": "accepted",
                    "command_artifacts": [
                        {
                            "artifact_ref": f"file:{artifact_rel}",
                            "artifact_sha256": artifact_sha,
                            "command": evidence["command_results"][0]["command"],
                        }
                    ],
                    "review_import_artifacts": [],
                    "probe_transcripts": [],
                }
            }
            pointer_path = root / pointer_rel
            pointer_path.parent.mkdir(parents=True, exist_ok=True)
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive command evidence missing replay metadata field", result.stderr)

    def test_check_pointer_rejects_unauthenticated_replay_metadata_labels(self) -> None:
        for label in ("trusted-runner", "generated-artifact"):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    init_repo(root)
                    packet_rel, artifact_rel, packet_sha = write_archived_base_ref_packet(
                        root,
                        replay_metadata=True,
                        replay_metadata_value=label,
                    )
                    artifact_sha = hashlib.sha256((root / artifact_rel).read_bytes()).hexdigest()
                    packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
                    evidence = packet["result"]["evidence"]
                    archive_commit = synthetic_archive_commit(root, packet_rel)
                    pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
                    pointer = {
                        "AcceptancePacketPointer": {
                            "schema_version": "acceptance-packet-pointer/v1",
                            "packet_id": "pkt-archived-pointer-test",
                            "packet_ref": packet_rel,
                            "packet_sha256": packet_sha,
                            "checker_version": "v2.0-draft",
                            "inference_rule_version": "v2.0-draft",
                            "baseline_ref": evidence["baseline_ref"],
                            "comparison_ref": evidence["comparison_ref"],
                            "head_commit": evidence["accepted_head_commit"],
                            "archive_commit": archive_commit,
                            "stable_target": f"base-ref:{evidence['baseline_ref']}...{evidence['comparison_ref']}@{evidence['accepted_head_commit']}",
                            "decision_status": "accepted",
                            "command_artifacts": [
                                {
                                    "artifact_ref": f"file:{artifact_rel}",
                                    "artifact_sha256": artifact_sha,
                                    "command": evidence["command_results"][0]["command"],
                                }
                            ],
                            "review_import_artifacts": [],
                            "probe_transcripts": [],
                        }
                    }
                    pointer_path = root / pointer_rel
                    pointer_path.parent.mkdir(parents=True, exist_ok=True)
                    pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

                    result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("replay_metadata must be one of ['pointer-bound']", result.stderr)

    def test_check_pointer_rejects_arbitrary_replay_metadata_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            artifact_path = root / artifact_rel
            artifact_text = artifact_path.read_text(encoding="utf-8")
            artifact_text = artifact_text.replace(
                "replay_recorded_by: scripts/check-governance-acceptance.py",
                "replay_recorded_by: trusted-runner",
            )
            artifact_text = artifact_text.replace(
                "replay_checker_ref: scripts/check-governance-acceptance.py",
                "replay_checker_ref: docs/note.md",
            )
            artifact_path.write_text(artifact_text, encoding="utf-8")
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer = pointer_doc["AcceptancePacketPointer"]
            pointer["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            pointer["archive_commit"] = synthetic_archive_commit(root, packet_rel)
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("replay_recorded_by must be scripts/check-governance-acceptance.py", result.stderr)

    def test_check_pointer_rejects_legacy_provenance_with_replay_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            write_result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel, "--output", pointer_rel)
            artifact_path = root / artifact_rel
            artifact_text = artifact_path.read_text(encoding="utf-8")
            artifact_text = artifact_text.replace(
                "replay_metadata: pointer-bound",
                "replay_metadata: pointer-bound\narchive_provenance: legacy-runner",
            )
            artifact_path.write_text(artifact_text, encoding="utf-8")
            pointer_path = root / pointer_rel
            pointer_doc = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
            pointer = pointer_doc["AcceptancePacketPointer"]
            pointer["command_artifacts"][0]["artifact_sha256"] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            pointer["archive_commit"] = synthetic_archive_commit(root, packet_rel)
            pointer_path.write_text(yaml.safe_dump(pointer_doc, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertEqual(write_result.returncode, 0, write_result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive command evidence legacy provenance fields are not allowed", result.stderr)

    def test_write_pointer_rejects_pre_authored_replay_metadata_even_with_matching_replay_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, _artifact_rel, _packet_sha = write_archived_base_ref_packet(
                root,
                replay_metadata=True,
            )

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive command evidence replay metadata must be materialized by write-pointer", result.stderr)

    def test_write_pointer_preflight_failure_does_not_materialize_command_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            packet["input"]["source_refs"] = ["docs/note.md"]
            evidence["source_refs"] = ["docs/note.md"]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/note.md",
                    "status": "resolved",
                    "target": "docs/note.md",
                }
            )
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)
            artifact_before = (root / artifact_rel).read_text(encoding="utf-8")

            rejected = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("active base-ref stable packet source_refs must use commit-pinned git refs only", rejected.stderr)
            self.assertEqual((root / artifact_rel).read_text(encoding="utf-8"), artifact_before)

            packet["input"]["source_refs"] = []
            evidence["source_refs"] = []
            evidence["resolved_refs"] = [
                record for record in evidence["resolved_refs"] if record.get("ref") != "docs/note.md"
            ]
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)
            retried = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertEqual(retried.returncode, 0, retried.stderr)

    def test_write_pointer_output_failure_rolls_back_command_artifact_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            pointer_path = root / pointer_rel
            pointer_path.mkdir(parents=True)
            artifact_before = (root / artifact_rel).read_text(encoding="utf-8")

            failed = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                pointer_rel,
                "--overwrite",
            )
            artifact_after = (root / artifact_rel).read_text(encoding="utf-8")
            pointer_path.rmdir()
            retried = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
            )

        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(artifact_after, artifact_before)
        self.assertEqual(retried.returncode, 0, retried.stderr)

    def test_write_pointer_rejects_packet_and_artifact_output_paths(self) -> None:
        for output_kind in ("packet", "artifact"):
            with self.subTest(output_kind=output_kind):
                with tempfile.TemporaryDirectory() as tmpdir:
                    root = Path(tmpdir)
                    init_repo(root)
                    packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
                    output_rel = packet_rel if output_kind == "packet" else artifact_rel
                    output_path = root / output_rel
                    before = output_path.read_text(encoding="utf-8")

                    result = run_cli(
                        "--root",
                        str(root),
                        "write-pointer",
                        "--packet",
                        packet_rel,
                        "--output",
                        output_rel,
                        "--overwrite",
                    )
                    after = output_path.read_text(encoding="utf-8")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("write-pointer output must not overwrite archived packet or artifact paths", result.stderr)
                self.assertEqual(after, before)

    def test_write_pointer_rejects_pointer_namespaced_command_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            artifact_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(
                root,
                artifact_rel=artifact_rel,
            )
            artifact_before = (root / artifact_rel).read_text(encoding="utf-8")

            result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                artifact_rel,
                "--overwrite",
            )
            artifact_after = (root / artifact_rel).read_text(encoding="utf-8")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active stable command artifact_ref must be under archive/v2/artifacts/", result.stderr)
        self.assertEqual(artifact_after, artifact_before)

    def test_write_pointer_rejects_output_outside_pointer_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            artifact_before = (root / artifact_rel).read_text(encoding="utf-8")

            result = run_cli(
                "--root",
                str(root),
                "write-pointer",
                "--packet",
                packet_rel,
                "--output",
                "archive/v2/pointer.yml",
            )
            artifact_after = (root / artifact_rel).read_text(encoding="utf-8")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active pointer path must be under archive/v2/pointers/", result.stderr)
        self.assertEqual(artifact_after, artifact_before)

    def test_check_pointer_rejects_artifact_bound_to_pre_archive_packet_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, packet_sha = write_archived_base_ref_packet(
                root,
                artifact_packet_ref="backlog/fixtures/acceptance-packets/finalized-routine.yml",
            )
            artifact_sha = hashlib.sha256((root / artifact_rel).read_bytes()).hexdigest()
            packet = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            archive_commit = synthetic_archive_commit(root, packet_rel)
            pointer_rel = "archive/v2/pointers/pkt-archived-pointer-test.yml"
            pointer = {
                "AcceptancePacketPointer": {
                    "schema_version": "acceptance-packet-pointer/v1",
                    "packet_id": "pkt-archived-pointer-test",
                    "packet_ref": packet_rel,
                    "packet_sha256": packet_sha,
                    "checker_version": "v2.0-draft",
                    "inference_rule_version": "v2.0-draft",
                    "baseline_ref": evidence["baseline_ref"],
                    "comparison_ref": evidence["comparison_ref"],
                    "head_commit": evidence["accepted_head_commit"],
                    "archive_commit": archive_commit,
                    "stable_target": f"base-ref:{evidence['baseline_ref']}...{evidence['comparison_ref']}@{evidence['accepted_head_commit']}",
                    "decision_status": "accepted",
                    "command_artifacts": [
                        {
                            "artifact_ref": f"file:{artifact_rel}",
                            "artifact_sha256": artifact_sha,
                            "command": evidence["command_results"][0]["command"],
                        }
                    ],
                    "review_import_artifacts": [],
                    "probe_transcripts": [],
                }
            }
            pointer_path = root / pointer_rel
            pointer_path.parent.mkdir(parents=True, exist_ok=True)
            pointer_path.write_text(yaml.safe_dump(pointer, sort_keys=False), encoding="utf-8")

            result = run_cli("--root", str(root), "check-pointer", "--pointer", pointer_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archived packet: stable command artifact does not record command evidence", result.stderr)

    def test_write_pointer_rejects_archived_bare_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            packet["input"]["source_refs"] = ["docs/note.md"]
            evidence["source_refs"] = ["docs/note.md"]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": "docs/note.md",
                    "status": "resolved",
                    "target": "docs/note.md",
                }
            )
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active base-ref stable packet source_refs must use commit-pinned git refs only", result.stderr)

    def test_write_pointer_rejects_archived_mutable_git_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            ref = "git:HEAD:docs/note.md"
            packet["input"]["source_refs"] = [ref]
            evidence["source_refs"] = [ref]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": "HEAD:docs/note.md",
                }
            )
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git source refs must use git:<full-commit-sha>:<repo-path> form", result.stderr)

    def test_write_pointer_rejects_archived_opaque_git_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            blob_sha = git(root, "rev-parse", "HEAD:docs/note.md").stdout.strip()
            ref = f"git:{blob_sha}"
            packet["input"]["source_refs"] = [ref]
            evidence["source_refs"] = [ref]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": blob_sha,
                }
            )
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git source refs must use git:<full-commit-sha>:<repo-path> form", result.stderr)

    def test_write_pointer_rejects_archived_protected_directory_root_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet_rel, artifact_rel, _packet_sha = write_archived_base_ref_packet(root)
            packet_doc = yaml.safe_load((root / packet_rel).read_text(encoding="utf-8"))
            packet = packet_doc["AcceptancePacket"]
            evidence = packet["result"]["evidence"]
            ref = "file:scripts"
            packet["input"]["source_refs"] = [ref]
            evidence["source_refs"] = [ref]
            evidence["resolved_refs"].append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": "scripts",
                }
            )
            rewrite_archived_packet_and_artifact_sha(root, packet_rel, artifact_rel, packet_doc)

            result = run_cli("--root", str(root), "write-pointer", "--packet", packet_rel)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source_ref points to protected path outside changed_paths", result.stderr)

    def test_check_rejects_untargeted_input_exception_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["review_downgrade_request"].pop("from")
            packet["AcceptancePacket"]["input"]["user_judgment"]["review_downgrade_request"].pop("to")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.review_downgrade_request", result.stderr)

    def test_check_rejects_input_exception_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["waiver_request"].pop("actor")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("actor is required", result.stderr)

    def test_check_rejects_residual_input_judgment_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["residual_risk_request"] = {
                "reason": "accept a small residual risk"
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.residual_risk_request: actor is required", result.stderr)

    def test_check_rejects_untargeted_residual_input_judgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["residual_risk_request"] = {
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "accept a small residual risk",
                "source_ref": "file:tests/test_governance_acceptance_cli.py",
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.residual_risk_request: residual risk must target", result.stderr)

    def test_check_rejects_extra_meta_or_input_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["change_class"] = "routine"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input fields must be exactly", result.stderr)

    def test_check_rejects_stable_packet_without_generated_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"] = {}
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.change_class is required", result.stderr)

    def test_check_rejects_container_required_targets_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_review"] = [["checker correctness"]]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_evidence"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_evidence must be a list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_non_mapping_stable_records_without_traceback(self) -> None:
        cases = [
            ("result.evidence.command_results", "command_results", "result.evidence.command_results[0] must be a mapping"),
            ("result.evidence.skipped", "skipped", "result.evidence.skipped[0] must be a mapping"),
            ("result.judgment.reviews", "reviews", "result.judgment.reviews[0] must be a mapping"),
            ("result.judgment.waivers", "waivers", "result.judgment.waivers[0] must be a mapping"),
            ("result.judgment.downgrades", "downgrades", "result.judgment.downgrades[0] must be a mapping"),
            ("result.judgment.residual_risk", "residual_risk", "result.judgment.residual_risk[0] must be a mapping"),
        ]
        for path, field, expected in cases:
            with self.subTest(field=path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = ["not-a-mapping"]
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = ["not-a-mapping"]
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

        for path, field, expected in cases:
            with self.subTest(field=f"{path}-scalar"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = 1
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = 1
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"{path} must be a list", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_null_stable_record_buckets(self) -> None:
        cases = [
            ("result.evidence.command_results", "command_results"),
            ("result.evidence.skipped", "skipped"),
            ("result.judgment.reviews", "reviews"),
            ("result.judgment.waivers", "waivers"),
            ("result.judgment.downgrades", "downgrades"),
            ("result.judgment.residual_risk", "residual_risk"),
        ]
        for path, field in cases:
            with self.subTest(field=path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    packet_path = Path(tmpdir) / "packet.yml"
                    packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
                    if path.startswith("result.evidence"):
                        packet["AcceptancePacket"]["result"]["evidence"][field] = None
                    else:
                        packet["AcceptancePacket"]["result"]["judgment"][field] = None
                    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

                    result = run_cli("check", "--packet", str(packet_path), "--require-stable")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"{path} must be a list", result.stderr)

    def test_check_rejects_container_command_result_value_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"][0]["command"] = [
                "git diff --cached --check"
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("command must be a non-empty string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_protected_packet_without_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["required_review"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must match checker-derived required reviews", result.stderr)

    def test_check_rejects_evaluator_boundary_change_without_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            result_data = packet["AcceptancePacket"]["result"]
            result_data["evidence"]["evaluator_boundary"]["status"] = "changed"
            result_data["inference"]["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_review must match checker-derived required reviews", result.stderr)
        self.assertIn("evaluator boundary", result.stderr)

    def test_check_rejects_malformed_evaluator_boundary_status_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["evaluator_boundary"]["status"] = ["changed"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.evaluator_boundary.status must be null or a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_changed_paths_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["changed_paths"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.changed_paths must be a list", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_container_wrapped_changed_path_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["inference"]["changed_paths"] = [
                {"path": "scripts/check-governance-acceptance.py"}
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.inference.changed_paths must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_scalar_user_judgment_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"] = 1
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment must be a mapping", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_non_string_user_judgment_key_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"] = {
                1: {
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "non-string key regression",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment key must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_resolved_ref_fields_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            resolved_ref = packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"][1]
            resolved_ref["origin"] = ["generated"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.resolved_refs: origin is required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_review_ids_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["review_imports"][0]["review_ids"] = [{}, "x"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review_ids must contain only strings", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_malformed_meta_enums_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["meta"]["lifecycle"] = ["finalized"]
            packet["AcceptancePacket"]["meta"]["mode"] = ["staged"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("meta.lifecycle is invalid", result.stderr)
        self.assertIn("meta.mode is invalid", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_protected_path_with_falsified_low_risk_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["changed_paths"] = ["scripts/tool.py"]
            inference["change_class"] = "routine"
            inference["impact"] = "low"
            inference["protected_boundary_changed"] = False
            inference["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected_boundary_changed: true", result.stderr)
        self.assertIn("change_class: harness-affecting", result.stderr)
        self.assertIn("impact: high", result.stderr)

    def test_check_rejects_container_skipped_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["skipped"][0]["evidence"] = ["search_set_before"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.evidence.skipped: evidence must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_container_user_judgment_skipped_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["input"]["user_judgment"]["skipped_request"] = {
                "evidence": ["git diff --cached --check"],
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "regression for malformed skipped request target",
                "source_ref": "file:tests/test_governance_acceptance_cli.py",
            }
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("input.user_judgment.skipped_request: evidence must be a string", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_stable_root_protected_path_with_falsified_low_risk_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["changed_paths"] = ["README.md"]
            inference["change_class"] = "routine"
            inference["impact"] = "low"
            inference["protected_boundary_changed"] = False
            inference["required_review"] = []
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected_boundary_changed: true", result.stderr)
        self.assertIn("change_class: harness-affecting", result.stderr)
        self.assertIn("impact: high", result.stderr)

    def test_check_rejects_downgrade_without_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0].pop("kind")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade kind must be evidence or review", result.stderr)

    def test_check_rejects_downgrade_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0].pop("to")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade to is required", result.stderr)

    def test_check_rejects_evidence_downgrade_to_unclosed_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "from": "git diff --cached --check",
                    "to": "not required by maintainer",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for arbitrary downgrade closure",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable evidence downgrade replacement is not closed", result.stderr)

    def test_check_rejects_exception_malformed_sibling_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = [
                {
                    "kind": "evidence",
                    "evidence": "git diff --cached --check",
                    "review": ["not a valid sibling target"],
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for malformed sibling target",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target field review must be a substantive string", result.stderr)

    def test_check_rejects_waiver_with_downgrade_to_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = [
                {
                    "kind": "evidence",
                    "evidence": "git diff --cached --check",
                    "to": "not a valid waiver target",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for forbidden waiver to field",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("waiver cannot include to", result.stderr)

    def test_check_rejects_review_downgrade_to_unclosed_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["review_imports"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "review",
                    "from": "validation layer",
                    "to": "not required by maintainer",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for arbitrary review downgrade closure",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable review downgrade replacement is not closed", result.stderr)

    def test_check_rejects_residual_risk_malformed_sibling_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "review": ["not a valid sibling target"],
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for malformed residual risk sibling",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target field review must be a substantive string", result.stderr)

    def test_check_rejects_residual_risk_with_from_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "from": "not a valid residual-risk target",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "regression for forbidden residual from field",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual risk cannot include from", result.stderr)

    def test_check_rejects_waiver_shaped_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "evidence": "python3 scripts/check-v1-archive-boundary.py --staged",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "waiver-shaped downgrade regression",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("downgrade must target from", result.stderr)

    def test_check_rejects_container_exception_target_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0]["review"] = ["archive boundary"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception must target exactly one required evidence/review item", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"][0]["kind"] = ["evidence"]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception kind must be evidence or review", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_review_waiver_without_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0].pop("kind", None)
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review waiver kind must be review", result.stderr)

    def test_check_does_not_apply_evidence_downgrade_to_required_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            inference = packet["AcceptancePacket"]["result"]["inference"]
            inference["required_evidence"] = ["shared target"]
            inference["required_review"] = ["shared target"]
            packet["AcceptancePacket"]["input"]["user_judgment"] = {}
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"] = []
            packet["AcceptancePacket"]["result"]["judgment"]["downgrades"] = [
                {
                    "kind": "evidence",
                    "from": "shared target",
                    "to": "narrow evidence check",
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "test kind isolation",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable packet missing required review", result.stderr)

    def test_check_rejects_required_evidence_double_closure(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "verify-release-double-closure.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"].append(
                {
                    "command": "python3 scripts/verify-release.py",
                    "status": "pass",
                    "artifact_ref": f"file:{rel_artifact}",
                }
            )
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "artifact",
                    "ref": f"file:{rel_artifact}",
                    "status": "resolved",
                    "target": rel_artifact,
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-waiver-downgrade-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: python3 scripts/verify-release.py",
                        "status: pass",
                        "summary: double closure regression fixture",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required evidence has multiple closures", result.stderr)

    def test_check_validates_non_pass_command_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["command_results"].append(
                {
                    "command": "python3 -c 'raise SystemExit(1)'",
                    "status": "fail",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command evidence lacks artifact_ref", result.stderr)

    def test_check_rejects_duplicate_review_waiver_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            waiver = dict(packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0])
            waiver["reason"] = "duplicate closure regression"
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"].append(waiver)
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required review has multiple closures", result.stderr)

    def test_check_accepts_targeted_skipped_required_evidence_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory(dir=ROOT) as repo_tmp:
            packet_path = Path(tmpdir) / "packet.yml"
            provenance_path = Path(repo_tmp) / "skip-provenance.md"
            provenance_ref = f"file:{provenance_path.relative_to(ROOT).as_posix()}"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            boundary_ref = git(ROOT, "rev-parse", "HEAD").stdout.strip()
            command = f"git diff --check {boundary_ref}...{boundary_ref}"
            packet["AcceptancePacket"]["meta"]["mode"] = "base-ref"
            packet["AcceptancePacket"]["input"]["source_refs"] = []
            packet["AcceptancePacket"]["result"]["inference"]["changed_paths"] = []
            packet["AcceptancePacket"]["result"]["inference"]["required_evidence"] = [command]
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["baseline_ref"] = boundary_ref
            evidence["comparison_ref"] = boundary_ref
            evidence["accepted_head_commit"] = boundary_ref
            evidence["evaluator_boundary"]["commands"] = [command]
            evidence["source_refs"] = []
            evidence["command_results"] = []
            skipped_record = {
                "evidence": command,
                "actor": "maintainer",
                "role": "maintainer",
                "date": "2026-05-06",
                "reason": "targeted skip regression",
                "source_ref": provenance_ref,
            }
            provenance_path.write_text(f"{provenance_marker(skipped_record)}\n", encoding="utf-8")
            evidence["skipped"] = [skipped_record]
            evidence["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": provenance_ref,
                    "status": "resolved",
                    "target": provenance_path.relative_to(ROOT).as_posix(),
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_rejects_broad_review_waiver_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["waivers"][0]["review"] = "not required"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exception target is not required: not required", result.stderr)

    def test_check_rejects_broad_stable_residual_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "actor": "maintainer",
                    "role": "maintainer",
                    "date": "2026-05-06",
                    "reason": "broad residual risk acceptance",
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual risk must target exactly one required evidence/review item", result.stderr)

    def test_check_rejects_container_residual_risk_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["residual_risk"] = [
                {
                    "evidence": "git diff --cached --check",
                    "actor": ["maintainer"],
                    "role": {"name": "maintainer"},
                    "date": "2026-05-06",
                    "reason": ["container wrapped reason"],
                    "source_ref": "file:tests/test_governance_acceptance_cli.py",
                }
            ]
            packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"].append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": "file:tests/test_governance_acceptance_cli.py",
                    "status": "resolved",
                    "target": "tests/test_governance_acceptance_cli.py",
                }
            )
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("residual_risk[0]: actor is required", result.stderr)
        self.assertIn("residual_risk[0]: role is required", result.stderr)
        self.assertIn("residual_risk[0]: reason is required", result.stderr)

    def test_check_rejects_same_search_set_before_after_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            trace_refs = packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]
            trace_refs["search_set_before"] = "trace:backlog/repository-search-set.md#active"
            trace_refs["search_set_after"] = "trace:backlog/repository-search-set.md#active"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("search_set_before and search_set_after must be distinct", result.stderr)

    def test_check_rejects_unbound_command_artifact_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "mixed-command-record.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Packet Record",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "# Command Record",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_non_command_evidence_heading(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "not-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Not Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_duplicate_command_evidence_fields(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "duplicate-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: git diff --cached --check",
                        "status: fail",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_duplicate_command_evidence_even_with_valid_neighbor(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "duplicate-plus-valid-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            common = [
                "packet_id: pkt-finalized-routine-example",
                f"packet_ref: {rel_packet}",
                f"packet_sha256: {packet_sha}",
                "command: git diff --cached --check",
            ]
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        *common,
                        "status: pass",
                        "",
                        "# Command Evidence",
                        *common,
                        "status: fail",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate fields in matching # Command Evidence section", result.stderr)

    def test_check_rejects_ambiguous_command_evidence_sections(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "ambiguous-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            common = [
                "packet_id: pkt-finalized-routine-example",
                f"packet_ref: {rel_packet}",
                f"packet_sha256: {packet_sha}",
                "command: git diff --cached --check",
            ]
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        *common,
                        "status: fail",
                        "",
                        "# Command Evidence",
                        *common,
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ambiguous # Command Evidence sections", result.stderr)

    def test_check_stops_command_evidence_at_next_heading(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "split-command-evidence.log.yml"
            artifact_path = tmp_path / "split-command-evidence.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "# Observational Evidence",
                        "command: git diff --cached --check",
                        "status: pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_case_changed_command_artifact_record(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            tmp_path = Path(tmpdir)
            packet_path = tmp_path / "packet.yml"
            artifact_path = tmp_path / "case-changed-command-record.log"
            rel_packet = packet_path.relative_to(ROOT).as_posix()
            rel_artifact = artifact_path.relative_to(ROOT).as_posix()
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            evidence["command_results"][0]["artifact_ref"] = f"file:{rel_artifact}"
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = f"file:{rel_artifact}"
                    record["target"] = rel_artifact
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
            packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
            artifact_path.write_text(
                "\n".join(
                    [
                        "# Command Evidence",
                        "packet_id: pkt-finalized-routine-example",
                        f"packet_ref: {rel_packet}",
                        f"packet_sha256: {packet_sha}",
                        "command: Git Diff --Cached --Check",
                        "status: Pass",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_cli("check", "--packet", rel_packet, "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact does not record command evidence", result.stderr)

    def test_check_rejects_bare_command_artifact_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            evidence = packet["AcceptancePacket"]["result"]["evidence"]
            artifact_ref = evidence["command_results"][0]["artifact_ref"].removeprefix("file:")
            evidence["command_results"][0]["artifact_ref"] = artifact_ref
            for record in evidence["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["ref"] = artifact_ref
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable command artifact_ref must use file: scheme", result.stderr)

    def test_check_rejects_generated_closure_ref_relabelled_as_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-routine.yml").read_text(encoding="utf-8"))
            for record in packet["AcceptancePacket"]["result"]["evidence"]["resolved_refs"]:
                if record.get("relation") == "artifact":
                    record["origin"] = "input"
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lacks resolved generated artifact relation", result.stderr)

    def test_check_rejects_bare_stable_trace_bucket_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["evidence"]["trace_refs"]["evolution"] = [
                ".harness/traces/evolution/001-repository-self-application-root.md"
            ]
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trace_refs.evolution entries must use trace: scheme", result.stderr)

    def test_check_rejects_stable_packet_with_subthreshold_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0]["score"] = 8
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("field does not mirror imported review_lineage", result.stderr)

    def test_check_rejects_stable_review_without_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            packet_path = Path(tmpdir) / "packet.yml"
            packet = yaml.safe_load((FIXTURE_ROOT / "finalized-harness-affecting.yml").read_text(encoding="utf-8"))
            packet["AcceptancePacket"]["result"]["judgment"]["reviews"][0].pop("actor")
            packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")

            result = run_cli("check", "--packet", str(packet_path), "--require-stable")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("result.judgment.reviews: actor is required", result.stderr)

    def test_start_writes_valid_neutral_packet_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet = root / "archive/v2/packets/baseline-match.yml"

            result = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--staged",
            )
            second = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--staged",
            )
            check = run_cli("check", "--packet", str(packet))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("refusing to overwrite", second.stderr)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_finalize_staged_routine_packet_remains_nonstable_without_durable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            packet = root / "archive/v2/packets/normalize-boundaries.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--staged",
            )
            (root / "docs" / "note.md").write_text("initial\nupdated\n", encoding="utf-8")
            git(root, "add", "docs/note.md")

            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--staged")
            stable = run_cli("check", "--packet", str(packet), "--require-stable")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertNotEqual(stable.returncode, 0)
        self.assertEqual(packet_data["meta"]["lifecycle"], "finalized")
        self.assertEqual(packet_data["result"]["inference"]["change_class"], "routine")
        self.assertFalse(packet_data["result"]["decision"]["stable_handoff_eligible"])
        self.assertIn("durable artifact refs", packet_data["result"]["decision"]["reason"])

    def test_finalize_base_ref_must_match_start_baseline_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "second")
            base_commit = git(root, "rev-parse", "HEAD~1").stdout.strip()
            packet = root / "archive/v2/packets/baseline-match.yml"

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--base-ref",
                "HEAD~1",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--base-ref", "HEAD")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("finalize base-ref must match start baseline_ref:", finalize.stderr)
        self.assertIn(base_commit, finalize.stderr)
        self.assertEqual(packet_data["result"]["evidence"]["baseline_ref"], base_commit)

    def test_start_and_finalize_base_ref_normalize_boundary_refs_for_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "docs" / "note.md").write_text("initial\nsecond\n", encoding="utf-8")
            git(root, "add", "docs/note.md")
            git(root, "commit", "-m", "second")
            base_commit = git(root, "rev-parse", "HEAD~1").stdout.strip()
            packet = root / "archive/v2/packets/normalize-boundaries.yml"

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update local docs.",
                "--source-ref",
                "docs/note.md",
                "--base-ref",
                "HEAD~1",
            )
            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--base-ref", "HEAD~1")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]
            accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        expected_command = f"git diff --check {base_commit}...{accepted_head}"
        self.assertEqual(packet_data["input"]["source_refs"], [])
        self.assertEqual(packet_data["result"]["evidence"]["baseline_ref"], base_commit)
        self.assertEqual(packet_data["result"]["evidence"]["comparison_ref"], base_commit)
        self.assertEqual(packet_data["result"]["evidence"]["accepted_head_commit"], accepted_head)
        self.assertEqual(packet_data["result"]["inference"]["required_evidence"], [expected_command])
        self.assertEqual(packet_data["result"]["evidence"]["evaluator_boundary"]["commands"], [expected_command])
        self.assertEqual(packet_data["result"]["evidence"]["command_results"][0]["command"], expected_command)

    def test_finalize_protected_packet_remains_nonstable_without_review_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            (root / "scripts").mkdir(exist_ok=True)
            (root / "scripts" / "tool.py").write_text("print('old')\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "add script")
            packet = root / "packet.yml"
            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update checker script.",
                "--source-ref",
                "scripts/tool.py",
                "--staged",
            )
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")

            finalize = run_cli("--root", str(root), "finalize", "--packet", str(packet), "--staged")
            stable = run_cli("check", "--packet", str(packet), "--require-stable")
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        self.assertNotEqual(stable.returncode, 0)
        self.assertEqual(packet_data["result"]["inference"]["required_review"], ["checker correctness"])
        self.assertFalse(packet_data["result"]["decision"]["stable_handoff_eligible"])
        self.assertIn("Protected changes require imported review judgment", packet_data["result"]["decision"]["reason"])
        self.assertIn("governance review-template --packet <packet>", packet_data["result"]["decision"]["next_action"])

    def test_capture_search_set_writes_resolvable_phase_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text(
                """# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived
""",
                encoding="utf-8",
            )
            (root / "scripts" / "run-search-set.py").write_text("", encoding="utf-8")

            result = run_cli(
                "--root",
                str(root),
                "capture-search-set",
                "--phase",
                "before",
                "--packet",
                "archive/v2/packets/pkt-search-set.yml",
            )
            text = search_set.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("captured search-set before trace: trace:backlog/repository-search-set.md#", result.stdout)
        self.assertIn("## Search-set Evidence Captures", text)
        self.assertIn("### Search-set before ", text)
        self.assertIn("- **status**: PASS", text)
        self.assertIn("- **command**: `python3 scripts/run-search-set.py`", text)
        self.assertIn("- **packet_ref**: `archive/v2/packets/pkt-search-set.yml`", text)

    def test_capture_search_set_rejects_custom_stable_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            result = run_cli(
                "--root",
                str(root),
                "capture-search-set",
                "--phase",
                "before",
                "--command",
                "true",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stable search-set capture command must be", result.stderr)

    def test_finalize_base_ref_accepts_captured_search_set_trace_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text(
                """# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived
""",
                encoding="utf-8",
            )
            git(root, "add", "-A")
            git(root, "commit", "-m", "add search set")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()
            packet = root / "archive/v2/packets/pkt-search-set-traces.yml"
            search_set.write_text(
                f"""# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived

## Search-set Evidence Captures

### Search-set before fixture
- **phase**: before
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `{base_ref}`
- **captured_at**: 2026-05-18
- **packet_ref**: `archive/v2/packets/pkt-search-set-traces.yml`

### Search-set after fixture
- **phase**: after
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `{accepted_head}`
- **captured_at**: 2026-05-18
- **packet_ref**: `archive/v2/packets/pkt-search-set-traces.yml`
""",
                encoding="utf-8",
            )

            start = run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update protected script with captured search-set traces.",
                "--base-ref",
                base_ref,
            )
            finalize = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                str(packet),
                "--base-ref",
                base_ref,
                "--search-set-before",
                "trace:backlog/repository-search-set.md#search-set-before-fixture",
                "--search-set-after",
                "trace:backlog/repository-search-set.md#search-set-after-fixture",
            )
            packet_data = yaml.safe_load(packet.read_text(encoding="utf-8"))["AcceptancePacket"]

        self.assertEqual(start.returncode, 0, start.stderr)
        self.assertEqual(finalize.returncode, 0, finalize.stderr)
        evidence = packet_data["result"]["evidence"]
        self.assertEqual(
            evidence["trace_refs"]["search_set_before"],
            "trace:backlog/repository-search-set.md#search-set-before-fixture",
        )
        self.assertEqual(
            evidence["trace_refs"]["search_set_after"],
            "trace:backlog/repository-search-set.md#search-set-after-fixture",
        )
        skipped_targets = {item["evidence"] for item in evidence["skipped"]}
        self.assertNotIn("search_set_before", skipped_targets)
        self.assertNotIn("search_set_after", skipped_targets)
        trace_refs = {
            item["ref"]
            for item in evidence["resolved_refs"]
            if item.get("relation") == "trace" and item.get("origin") == "generated"
        }
        self.assertIn("trace:backlog/repository-search-set.md#search-set-before-fixture", trace_refs)
        self.assertIn("trace:backlog/repository-search-set.md#search-set-after-fixture", trace_refs)

    def test_finalize_rejects_incomplete_captured_search_set_trace_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text(
                """# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived

## Search-set Evidence Captures

### Search-set before fixture
- **phase**: before
- **status**: PASS
""",
                encoding="utf-8",
            )
            git(root, "add", "-A")
            git(root, "commit", "-m", "add search set")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            packet = root / "archive/v2/packets/pkt-search-set-incomplete.yml"
            run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update script.",
                "--base-ref",
                base_ref,
            )

            finalize = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                str(packet),
                "--base-ref",
                base_ref,
                "--search-set-before",
                "trace:backlog/repository-search-set.md#search-set-before-fixture",
            )

        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("search-set capture record is missing required fields", finalize.stderr)

    def test_finalize_rejects_noop_captured_search_set_trace_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            git(root, "commit", "--allow-empty", "-m", "base")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            packet = root / "archive/v2/packets/pkt-search-set-noop.yml"
            search_set.write_text(
                f"""# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived

## Search-set Evidence Captures

### Search-set after fixture
- **phase**: after
- **status**: PASS
- **command**: `true`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `{base_ref}`
- **captured_at**: 2026-05-18
- **packet_ref**: `archive/v2/packets/pkt-search-set-noop.yml`
""",
                encoding="utf-8",
            )
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update script.",
                "--base-ref",
                base_ref,
            )

            finalize = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                str(packet),
                "--base-ref",
                base_ref,
                "--search-set-after",
                "trace:backlog/repository-search-set.md#search-set-after-fixture",
            )

        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("search-set capture record command must be", finalize.stderr)

    def test_finalize_rejects_search_set_head_ref_boundary_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text("# Harness Search Set\n\n## Active\n\n## Archived\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-m", "add search set")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            accepted_head = git(root, "rev-parse", "HEAD").stdout.strip()
            search_set.write_text(
                f"""# Harness Search Set

## Active

## Archived

## Search-set Evidence Captures

### Search-set after fixture
- **phase**: after
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `{base_ref}`
- **captured_at**: 2026-05-18
- **packet_ref**: `archive/v2/packets/pkt-search-set-boundary.yml`
""",
                encoding="utf-8",
            )
            error = load_checker().search_set_capture_record_error(
                root,
                "trace:backlog/repository-search-set.md#search-set-after-fixture",
                expected_phase="after",
                expected_head_ref=accepted_head,
            )

        self.assertIn("search-set capture record head_ref must match packet boundary", error)

    def test_finalize_rejects_wrong_phase_captured_search_set_trace_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text(
                f"""# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived

## Search-set Evidence Captures

### Search-set after fixture
- **phase**: after
- **status**: PASS
- **command**: `true`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `HEAD`
- **captured_at**: 2026-05-18
""",
                encoding="utf-8",
            )
            git(root, "add", "-A")
            git(root, "commit", "-m", "add search set")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            packet = root / "archive/v2/packets/pkt-search-set-wrong-phase.yml"
            run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update script.",
                "--base-ref",
                base_ref,
            )

            finalize = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                str(packet),
                "--base-ref",
                base_ref,
                "--search-set-before",
                "trace:backlog/repository-search-set.md#search-set-after-fixture",
            )

        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("search-set capture record phase must be before", finalize.stderr)

    def test_finalize_rejects_same_captured_search_set_trace_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            init_repo(root)
            search_set = root / "backlog/repository-search-set.md"
            search_set.parent.mkdir(parents=True)
            search_set.write_text(
                f"""# Harness Search Set

## Active

### SS-001: fixture
- **verify**: `true`

## Archived

## Search-set Evidence Captures

### Search-set before fixture
- **phase**: before
- **status**: PASS
- **command**: `true`
- **exit_code**: 0
- **stdout_sha256**: {EMPTY_SHA256}
- **stderr_sha256**: {EMPTY_SHA256}
- **head_ref**: `HEAD`
- **captured_at**: 2026-05-18
""",
                encoding="utf-8",
            )
            git(root, "add", "-A")
            git(root, "commit", "-m", "add search set")
            base_ref = git(root, "rev-parse", "HEAD").stdout.strip()
            (root / "scripts" / "tool.py").write_text("print('new')\n", encoding="utf-8")
            git(root, "add", "scripts/tool.py")
            git(root, "commit", "-m", "update script")
            packet = root / "archive/v2/packets/pkt-search-set-same.yml"
            run_cli(
                "--root",
                str(root),
                "start",
                "--output",
                str(packet),
                "--intent",
                "Update script.",
                "--base-ref",
                base_ref,
            )

            finalize = run_cli(
                "--root",
                str(root),
                "finalize",
                "--packet",
                str(packet),
                "--base-ref",
                base_ref,
                "--search-set-before",
                "trace:backlog/repository-search-set.md#search-set-before-fixture",
                "--search-set-after",
                "trace:backlog/repository-search-set.md#search-set-before-fixture",
            )

        self.assertNotEqual(finalize.returncode, 0)
        self.assertIn("finalize search-set before and after refs must be distinct", finalize.stderr)


if __name__ == "__main__":
    unittest.main()
