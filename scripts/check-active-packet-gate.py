#!/usr/bin/env python3
"""Validate the active packet pointer gate for release and pre-commit flows."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check-governance-acceptance.py"
ARCHIVE_PACKET_PREFIX = "archive/v2/packets/"
ARCHIVE_ARTIFACT_PREFIX = "archive/v2/artifacts/"
ARCHIVE_POINTER_PREFIX = "archive/v2/pointers/"
POINTER_SUFFIXES = (".yml", ".yaml")
GIT_ENV_PREFIX = "GIT_"
TRUSTED_GIT_PATH_ENTRIES = tuple(
    dict.fromkeys(
        [
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
        ]
    )
)
TRUSTED_GIT_PATH = os.pathsep.join(TRUSTED_GIT_PATH_ENTRIES)
CHECKER_REQUIRED_API = (
    "archive_tree_errors",
    "archive_v2_diff_errors",
    "file_sha256",
    "git_blob_bytes",
    "git_commit_parents",
    "git_diff_name_status_records",
    "git_is_ancestor",
    "git_ref_commit",
    "load_packet",
    "load_pointer",
    "pointer_publication_paths",
    "validate_packet",
    "validate_pointer",
)
CHECKER_REQUIRED_VALUES = {
    "SCHEMA_VERSION": "v2.0-draft",
    "POINTER_SCHEMA_VERSION": "acceptance-packet-pointer/v1",
}


def git_env(
    *,
    keep_index: bool = False,
    object_dir: Path | None = None,
    alternates: list[Path] | None = None,
) -> dict[str, str]:
    safe_names = (
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TMPDIR",
        "TMP",
        "TEMP",
        "SYSTEMROOT",
        "COMSPEC",
        "PATHEXT",
    )
    env = {name: value for name in safe_names if (value := os.environ.get(name))}
    if keep_index and (index_path := os.environ.get("GIT_INDEX_FILE")):
        env["GIT_INDEX_FILE"] = index_path
    if object_dir is not None:
        object_dir.mkdir(parents=True, exist_ok=True)
        env["GIT_OBJECT_DIRECTORY"] = str(object_dir)
    if alternates:
        env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.pathsep.join(str(path) for path in alternates)
    env["PATH"] = TRUSTED_GIT_PATH
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def git(
    root: Path,
    args: list[str],
    *,
    keep_index: bool = False,
    object_dir: Path | None = None,
    alternates: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        encoding="utf-8",
        env=git_env(keep_index=keep_index, object_dir=object_dir, alternates=alternates),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_check(root: Path, args: list[str], *, keep_index: bool = False) -> str:
    result = git(root, args, keep_index=keep_index)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def load_checker(root: Path = ROOT) -> ModuleType:
    root_checker = root / "scripts" / "check-governance-acceptance.py"
    candidates = [root_checker]
    if root_checker.resolve() != CHECKER_PATH.resolve():
        candidates.append(CHECKER_PATH)
    last_error: str | None = None
    for checker_path in candidates:
        spec = importlib.util.spec_from_file_location("check_governance_acceptance_for_packet_gate", checker_path)
        if spec is None or spec.loader is None:
            last_error = f"{checker_path}: could not load governance checker"
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        missing_api = [name for name in CHECKER_REQUIRED_API if not hasattr(module, name)]
        mismatched_values = [
            name
            for name, expected in CHECKER_REQUIRED_VALUES.items()
            if getattr(module, name, None) != expected
        ]
        if not missing_api and not mismatched_values:
            return module
        details = []
        if missing_api:
            details.append(f"missing API {missing_api}")
        if mismatched_values:
            details.append(f"mismatched values {mismatched_values}")
        last_error = f"{checker_path}: not a complete governance checker ({'; '.join(details)})"
    raise RuntimeError(last_error or f"{CHECKER_PATH}: could not load governance checker")


def name_status_records(output: str) -> list[tuple[str, list[str]]]:
    records: list[tuple[str, list[str]]] = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        status = fields[0]
        if status.startswith(("R", "C")) and len(fields) >= 3:
            records.append((status, [fields[1], fields[2]]))
        else:
            records.append((status, [fields[1]]))
    return records


def changed_records(root: Path, *, base_ref: str | None, staged: bool) -> tuple[list[tuple[str, list[str]]] | None, str | None]:
    if staged:
        result = git(root, ["diff", "--cached", "--name-status"], keep_index=True)
    elif base_ref:
        result = git(root, ["diff", "--name-status", f"{base_ref}...HEAD"])
    else:
        return [], None
    if result.returncode != 0:
        return None, result.stderr.strip() or "failed to read active packet gate diff"
    return name_status_records(result.stdout), None


def repo_relative(root: Path, path: str) -> str | None:
    raw = Path(path)
    candidate = raw if raw.is_absolute() else root / raw
    root_abs = Path(os.path.abspath(os.path.normpath(root)))
    candidate_abs = Path(os.path.abspath(os.path.normpath(candidate)))
    try:
        return candidate_abs.relative_to(root_abs).as_posix()
    except ValueError:
        return None


def is_archive_evidence_path(path: str) -> bool:
    return path.startswith((ARCHIVE_PACKET_PREFIX, ARCHIVE_ARTIFACT_PREFIX, ARCHIVE_POINTER_PREFIX))


def pointer_candidates(records: list[tuple[str, list[str]]]) -> list[str]:
    candidates: set[str] = set()
    for status, paths in records:
        if status.startswith("D"):
            continue
        candidate_paths = paths[1:] if status.startswith(("R", "C")) and len(paths) > 1 else paths
        for path in candidate_paths:
            if path.startswith(ARCHIVE_POINTER_PREFIX) and path.endswith(POINTER_SUFFIXES):
                candidates.add(path)
    return sorted(candidates)


def gate_required(records: list[tuple[str, list[str]]], *, base_ref: str | None, staged: bool) -> bool:
    if base_ref and not staged:
        return True
    return any(is_archive_evidence_path(path) for _status, paths in records for path in paths)


def selected_pointer(
    root: Path,
    *,
    explicit_pointer: str | None,
    records: list[tuple[str, list[str]]],
    base_ref: str | None,
    staged: bool,
) -> tuple[str | None, list[str]]:
    if explicit_pointer:
        pointer_ref = repo_relative(root, explicit_pointer)
        if pointer_ref is None:
            return None, [f"active packet pointer must be inside repository root: {explicit_pointer}"]
        candidates = pointer_candidates(records)
        if base_ref and pointer_ref not in candidates:
            return None, [f"explicit active packet pointer must be published in release diff: {pointer_ref}"]
        if staged and pointer_ref not in candidates:
            return None, [f"explicit active packet pointer must be staged with archive evidence: {pointer_ref}"]
        return pointer_ref, []
    if not gate_required(records, base_ref=base_ref, staged=staged):
        return None, []
    candidates = pointer_candidates(records)
    if not candidates:
        label = "base-ref release" if base_ref and not staged else "staged archive"
        return None, [f"{label} gate requires an active packet pointer under {ARCHIVE_POINTER_PREFIX}"]
    if len(candidates) > 1:
        return None, [
            "active packet gate found multiple pointer candidates; "
            f"publish one active pointer per release diff: {candidates}"
        ]
    return candidates[0], []


def regular_file_error(path: Path, *, label: str, ref: str) -> str | None:
    if path.is_symlink():
        return f"{label} must be a regular file, not a symlink: {ref}"
    if not path.is_file():
        return f"{label} does not exist: {ref}"
    return None


def validate_pointer_gate(
    root: Path,
    pointer_ref: str,
    *,
    base_ref: str | None = None,
    replay_command_evidence: bool = False,
) -> list[str]:
    checker = load_checker(root)
    pointer_path = root / pointer_ref
    pointer_file_error = regular_file_error(pointer_path, label="active packet pointer", ref=pointer_ref)
    if pointer_file_error:
        return [pointer_file_error]
    try:
        pointer = checker.load_pointer(pointer_path)
    except Exception as exc:  # pragma: no cover - exact checker exception shape is not part of this gate.
        return [f"active packet pointer could not be read: {exc}"]
    errors = [
        f"active packet pointer: {error}"
        for error in checker.validate_pointer(
            pointer,
            root=root,
            pointer_ref=pointer_ref,
            replay_archive_command_evidence=replay_command_evidence,
        )
    ]
    packet_ref = pointer.get("packet_ref") if isinstance(pointer, dict) else None
    if not isinstance(packet_ref, str):
        return [*errors, "active packet pointer missing packet_ref"]
    packet_path = root / packet_ref
    packet_file_error = regular_file_error(packet_path, label="active packet pointer packet_ref", ref=packet_ref)
    if packet_file_error:
        return [*errors, packet_file_error]
    try:
        packet = checker.load_packet(packet_path)
    except Exception as exc:  # pragma: no cover - exact checker exception shape is not part of this gate.
        return [*errors, f"pointed acceptance packet could not be read: {exc}"]
    meta = packet.get("meta", {}) if isinstance(packet.get("meta"), dict) else {}
    decision = packet.get("result", {}).get("decision", {}) if isinstance(packet.get("result"), dict) else {}
    if meta.get("lifecycle") != "finalized":
        errors.append("pointed acceptance packet must be finalized")
    if meta.get("mode") != "base-ref":
        errors.append("pointed acceptance packet must use base-ref mode")
    if decision.get("stable_handoff_eligible") is not True:
        errors.append("pointed acceptance packet must be stable-handoff eligible")
    packet_errors = checker.validate_packet(
        packet,
        require_stable=True,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=checker.file_sha256(packet_path),
    )
    errors.extend(f"pointed acceptance packet: {error}" for error in packet_errors)
    if base_ref is not None:
        errors.extend(release_scope_errors(checker, root, pointer, packet, base_ref=base_ref))
    return errors


def release_scope_errors(checker: ModuleType, root: Path, pointer: dict, packet: dict, *, base_ref: str) -> list[str]:
    errors: list[str] = []
    release_base = checker.git_ref_commit(root, base_ref)
    if release_base is None:
        return [f"release base-ref must resolve to a commit: {base_ref}"]
    comparison_ref = packet.get("result", {}).get("evidence", {}).get("comparison_ref")
    if comparison_ref != release_base:
        errors.append(
            "active packet comparison_ref must match release base-ref: "
            f"{comparison_ref} != {release_base}"
        )
    head_commit = pointer.get("head_commit")
    current_head = checker.git_ref_commit(root, "HEAD")
    if not isinstance(head_commit, str) or current_head is None:
        return errors
    if not checker.git_is_ancestor(root, release_base, head_commit):
        errors.append("active packet accepted head must be reachable from release base-ref")
    if not checker.git_is_ancestor(root, head_commit, current_head):
        errors.append("release HEAD must include the active packet accepted head")
    return errors


def original_object_dir(root: Path) -> str:
    path = Path(git_check(root, ["rev-parse", "--git-path", "objects"]))
    return (path if path.is_absolute() else root / path).resolve().as_posix()


def init_snapshot_repo(snapshot: Path, source_root: Path, *, extra_alternates: list[Path] | None = None) -> list[str]:
    init = git(snapshot, ["init"])
    if init.returncode != 0:
        return [init.stderr.strip() or "failed to initialize snapshot repository"]
    try:
        source_objects = original_object_dir(source_root)
    except RuntimeError as exc:
        return [str(exc)]
    alternates = snapshot / ".git" / "objects" / "info" / "alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternate_paths = [source_objects, *(path.resolve().as_posix() for path in extra_alternates or [])]
    alternates.write_text("".join(f"{path}\n" for path in alternate_paths), encoding="utf-8")
    git(snapshot, ["config", "user.name", "Active Packet Gate"])
    git(snapshot, ["config", "user.email", "active-packet-gate@example.invalid"])
    return []


def checkout_snapshot_commit(snapshot: Path, commit_ref: str) -> list[str]:
    update = git(snapshot, ["update-ref", "refs/heads/main", commit_ref])
    if update.returncode != 0:
        return [update.stderr.strip() or "failed to set snapshot HEAD"]
    symbolic = git(snapshot, ["symbolic-ref", "HEAD", "refs/heads/main"])
    if symbolic.returncode != 0:
        return [symbolic.stderr.strip() or "failed to set snapshot symbolic HEAD"]
    checkout = git(snapshot, ["checkout", "-f", "main"])
    if checkout.returncode != 0:
        return [checkout.stderr.strip() or "failed to checkout snapshot HEAD"]
    return []


def synthetic_commit_from_tree(snapshot: Path, *, tree_ref: str, parent_ref: str, message: str) -> tuple[str | None, list[str]]:
    commit = git(snapshot, ["commit-tree", tree_ref, "-p", parent_ref, "-m", message])
    if commit.returncode != 0:
        return None, [commit.stderr.strip() or "failed to create snapshot commit"]
    return commit.stdout.strip(), []


def load_pointer_and_packet(checker: ModuleType, root: Path, pointer_ref: str) -> tuple[dict | None, dict | None, list[str]]:
    pointer_path = root / pointer_ref
    pointer_file_error = regular_file_error(pointer_path, label="active packet pointer", ref=pointer_ref)
    if pointer_file_error:
        return None, None, [pointer_file_error]
    try:
        pointer = checker.load_pointer(pointer_path)
    except Exception as exc:  # pragma: no cover - exact checker exception shape is not part of this gate.
        return None, None, [f"active packet pointer could not be read: {exc}"]
    packet_ref = pointer.get("packet_ref") if isinstance(pointer, dict) else None
    if not isinstance(packet_ref, str):
        return pointer, None, ["active packet pointer missing packet_ref"]
    packet_path = root / packet_ref
    packet_file_error = regular_file_error(packet_path, label="active packet pointer packet_ref", ref=packet_ref)
    if packet_file_error:
        return pointer, None, [packet_file_error]
    try:
        packet = checker.load_packet(packet_path)
    except Exception as exc:  # pragma: no cover - exact checker exception shape is not part of this gate.
        return pointer, None, [f"pointed acceptance packet could not be read: {exc}"]
    return pointer, packet, []


def validate_release_pointer_gate(root: Path, pointer_ref: str, *, base_ref: str) -> list[str]:
    checker = load_checker(root)
    release_base = checker.git_ref_commit(root, base_ref)
    if release_base is None:
        return [f"release base-ref must resolve to a commit: {base_ref}"]
    current_head = checker.git_ref_commit(root, "HEAD")
    if current_head is None:
        return ["release HEAD must resolve to a commit"]
    with tempfile.TemporaryDirectory(prefix="active-packet-release-snapshot.") as tmpdir:
        snapshot = Path(tmpdir)
        setup_errors = init_snapshot_repo(snapshot, root)
        if setup_errors:
            return setup_errors
        checkout_errors = checkout_snapshot_commit(snapshot, current_head)
        if checkout_errors:
            return checkout_errors
        pointer, packet, load_errors = load_pointer_and_packet(checker, snapshot, pointer_ref)
        if load_errors:
            return load_errors
        assert pointer is not None and packet is not None
        scope_errors = release_scope_errors_for_base(checker, root, pointer, packet, base_commit=release_base)
        if scope_errors:
            return scope_errors
        accepted_head = packet.get("result", {}).get("evidence", {}).get("accepted_head_commit")
        if not isinstance(accepted_head, str):
            return ["pointed acceptance packet missing accepted_head_commit"]
        publication_commit, publication_errors = find_publication_commit(
            checker,
            root,
            pointer=pointer,
            packet=packet,
            pointer_ref=pointer_ref,
            accepted_head=accepted_head,
            current_head=current_head,
        )
        if publication_errors:
            return publication_errors
        assert publication_commit is not None
        checkout_errors = checkout_snapshot_commit(snapshot, publication_commit)
        if checkout_errors:
            return checkout_errors
        return validate_pointer_gate(snapshot, pointer_ref, replay_command_evidence=True)


def release_scope_errors_for_base(
    checker: ModuleType,
    root: Path,
    pointer: dict,
    packet: dict,
    *,
    base_commit: str,
) -> list[str]:
    errors: list[str] = []
    comparison_ref = packet.get("result", {}).get("evidence", {}).get("comparison_ref")
    if comparison_ref != base_commit:
        errors.append(
            "active packet comparison_ref must match release base-ref: "
            f"{comparison_ref} != {base_commit}"
        )
    head_commit = pointer.get("head_commit")
    current_head = checker.git_ref_commit(root, "HEAD")
    if not isinstance(head_commit, str) or current_head is None:
        return errors
    if not checker.git_is_ancestor(root, base_commit, head_commit):
        errors.append("active packet accepted head must be reachable from release base-ref")
    if not checker.git_is_ancestor(root, head_commit, current_head):
        errors.append("release HEAD must include the active packet accepted head")
    return errors


def rev_list(root: Path, args: list[str]) -> tuple[list[str] | None, str | None]:
    result = git(root, ["rev-list", *args])
    if result.returncode != 0:
        return None, result.stderr.strip() or "git rev-list failed"
    return [line for line in result.stdout.splitlines() if line], None


def find_publication_commit(
    checker: ModuleType,
    root: Path,
    *,
    pointer: dict,
    packet: dict,
    pointer_ref: str,
    accepted_head: str,
    current_head: str,
) -> tuple[str | None, list[str]]:
    commits, error = rev_list(root, ["--reverse", "--ancestry-path", f"{accepted_head}..{current_head}"])
    if error:
        return None, [f"active pointer publication history could not be read: {error}"]
    assert commits is not None
    candidate_notes: list[str] = []
    for commit in commits:
        archive_paths, archive_error = commit_archive_v2_paths(checker, root, commit)
        if archive_error:
            return None, [archive_error]
        assert archive_paths is not None
        if not archive_paths:
            content_error = pre_publication_commit_error(checker, root, commit)
            if content_error:
                return None, [content_error]
            continue
        candidate_errors = publication_commit_candidate_errors(
            checker,
            root,
            pointer=pointer,
            packet=packet,
            pointer_ref=pointer_ref,
            accepted_head=accepted_head,
            publication_commit=commit,
            current_head=current_head,
        )
        if not candidate_errors:
            followup_errors = post_publication_change_errors(checker, root, publication_commit=commit, current_head=current_head)
            if followup_errors:
                return None, followup_errors
            return commit, []
        if any("active pointer path" in error or "pointer bytes" in error for error in candidate_errors):
            candidate_notes.append(f"{commit}: {candidate_errors[0]}")
    detail = f": {candidate_notes[:3]}" if candidate_notes else ""
    return None, [f"selected active pointer was not published by a valid first archive/v2 publication commit{detail}"]


def commit_archive_v2_paths(checker: ModuleType, root: Path, commit: str) -> tuple[list[str] | None, str | None]:
    parents = checker.git_commit_parents(root, commit)
    if parents is None:
        return None, f"commit parents could not be read while locating active pointer publication: {commit}"
    baseline = parents[0] if parents else f"{commit}^"
    records = checker.git_diff_name_status_records(root, baseline, commit)
    if records is None:
        return None, f"commit scope could not be read while locating active pointer publication: {commit}"
    paths = sorted(
        {
            path
            for _status, changed_paths in records
            for path in changed_paths
            if path.startswith("archive/v2/")
        }
    )
    return paths, None


def pre_publication_commit_error(checker: ModuleType, root: Path, commit: str) -> str | None:
    parents = checker.git_commit_parents(root, commit)
    if parents is None:
        return f"pre-publication commit parents could not be read: {commit}"
    commit_tree = commit_tree_ref(root, commit)
    if commit_tree is None:
        return f"pre-publication commit tree could not be read: {commit}"
    first_parent_tree = commit_tree_ref(root, parents[0]) if parents else None
    if first_parent_tree is not None and commit_tree == first_parent_tree:
        return None
    baseline = parents[0] if parents else f"{commit}^"
    records = checker.git_diff_name_status_records(root, baseline, commit)
    changed_paths = sorted({path for _status, paths in records for path in paths}) if records is not None else []
    return (
        "release history includes content-changing commits before the selected active pointer publication; "
        f"publish the pointer from the final accepted head before later content: {commit} {changed_paths}"
    )


def publication_commit_candidate_errors(
    checker: ModuleType,
    root: Path,
    *,
    pointer: dict,
    packet: dict,
    pointer_ref: str,
    accepted_head: str,
    publication_commit: str,
    current_head: str,
) -> list[str]:
    errors: list[str] = []
    parents = checker.git_commit_parents(root, publication_commit)
    if parents is None:
        errors.append("publication commit parents could not be read")
        return errors
    baseline = parents[0] if parents else accepted_head
    records = checker.git_diff_name_status_records(root, baseline, publication_commit)
    if records is None:
        errors.append("publication commit scope could not be compared to its first parent")
        return errors
    if not records:
        errors.append("publication commit has no changes after accepted_head_commit")
        return errors
    expected_paths = checker.pointer_publication_paths(pointer, pointer_ref=pointer_ref)
    errors.extend(
        checker.archive_v2_diff_errors(
            records,
            expected_paths=expected_paths,
            label="publication commit",
            allowed_modified_start_packet=(
                root,
                accepted_head,
                pointer["packet_ref"],
                packet,
            )
            if isinstance(pointer.get("packet_ref"), str)
            else None,
        )
    )
    changed_paths = {path for _status, paths in records for path in paths}
    if pointer_ref not in changed_paths:
        errors.append(f"publication commit must add the active pointer path: {pointer_ref}")
    errors.extend(
        checker.archive_tree_errors(
            pointer,
            root=root,
            packet_ref=pointer["packet_ref"],
            commit_ref=publication_commit,
            label="publication commit",
        )
        if isinstance(pointer.get("packet_ref"), str)
        else ["active packet pointer missing packet_ref"]
    )
    publication_pointer_bytes = checker.git_blob_bytes(root, publication_commit, pointer_ref)
    current_pointer_bytes = checker.git_blob_bytes(root, current_head, pointer_ref)
    if publication_pointer_bytes is None:
        errors.append(f"publication commit does not contain active pointer path: {pointer_ref}")
    elif current_pointer_bytes is None:
        errors.append(f"release HEAD does not contain active pointer path: {pointer_ref}")
    elif publication_pointer_bytes != current_pointer_bytes:
        errors.append("publication commit pointer bytes do not match release HEAD pointer bytes")
    return errors


def post_publication_change_errors(
    checker: ModuleType,
    root: Path,
    *,
    publication_commit: str,
    current_head: str,
) -> list[str]:
    commits, error = rev_list(root, ["--reverse", f"{publication_commit}..{current_head}"])
    if error:
        return [f"release history after selected active pointer publication could not be read: {error}"]
    assert commits is not None
    publication_tree = commit_tree_ref(root, publication_commit)
    if publication_tree is None:
        return [f"selected active pointer publication tree could not be read: {publication_commit}"]
    for commit in commits:
        parents = checker.git_commit_parents(root, commit)
        if parents is None:
            return [f"post-publication commit parents could not be read: {commit}"]
        commit_tree = commit_tree_ref(root, commit)
        if commit_tree is None:
            return [f"post-publication commit tree could not be read: {commit}"]
        first_parent_tree = commit_tree_ref(root, parents[0]) if parents else None
        if first_parent_tree is not None and commit_tree == first_parent_tree:
            continue
        if len(parents) > 1 and commit_tree == publication_tree:
            continue
        baseline = parents[0] if parents else f"{commit}^"
        records = checker.git_diff_name_status_records(root, baseline, commit)
        changed_paths = sorted({path for _status, paths in records for path in paths}) if records is not None else []
        return [
            "release history includes content-changing commits after the selected active pointer publication; "
            f"publish the pointer after final release content: {commit} {changed_paths}"
        ]
    return []


def commit_tree_ref(root: Path, commit_ref: str) -> str | None:
    result = git(root, ["rev-parse", "--verify", f"{commit_ref}^{{tree}}"])
    return result.stdout.strip() if result.returncode == 0 else None


def validate_staged_pointer_gate(root: Path, pointer_ref: str) -> list[str]:
    try:
        parent_commit = git_check(root, ["rev-parse", "--verify", "HEAD^{commit}"])
        source_objects = Path(original_object_dir(root))
    except RuntimeError as exc:
        return [str(exc)]
    with tempfile.TemporaryDirectory(prefix="active-packet-staged-index.") as tmpdir:
        tmp_path = Path(tmpdir)
        staged_object_dir = tmp_path / "staged-objects"
        tree = git(
            root,
            ["write-tree"],
            keep_index=True,
            object_dir=staged_object_dir,
            alternates=[source_objects],
        )
        if tree.returncode != 0:
            return [tree.stderr.strip() or "failed to write staged snapshot tree"]
        tree_ref = tree.stdout.strip()
        snapshot = tmp_path / "snapshot"
        snapshot.mkdir()
        setup_errors = init_snapshot_repo(snapshot, root, extra_alternates=[staged_object_dir])
        if setup_errors:
            return setup_errors
        commit, commit_errors = synthetic_commit_from_tree(
            snapshot,
            tree_ref=tree_ref,
            parent_ref=parent_commit,
            message="active packet staged snapshot",
        )
        if commit_errors:
            return commit_errors
        assert commit is not None
        checkout_errors = checkout_snapshot_commit(snapshot, commit)
        if checkout_errors:
            return checkout_errors
        return validate_pointer_gate(snapshot, pointer_ref)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--base-ref", help="require and discover an active pointer from REF...HEAD")
    parser.add_argument("--staged", action="store_true", help="preflight staged archive/v2 changes")
    parser.add_argument("--pointer", help="explicit active pointer path")
    args = parser.parse_args(argv)

    if args.base_ref and args.staged:
        print("ERROR: select only one active packet gate mode: --base-ref or --staged", file=sys.stderr)
        return 1
    if args.pointer and not (args.base_ref or args.staged):
        print(
            "ERROR: --pointer requires --base-ref or --staged; "
            "use check-governance-acceptance.py check-pointer for pointer-only validation",
            file=sys.stderr,
        )
        return 1
    if not (args.base_ref or args.staged):
        print("ERROR: select an active packet gate scope: --base-ref <ref> or --staged", file=sys.stderr)
        return 1
    root = Path(args.root).resolve()
    records, diff_error = changed_records(root, base_ref=args.base_ref, staged=args.staged)
    if diff_error:
        print(f"ERROR: {diff_error}", file=sys.stderr)
        return 1
    assert records is not None
    pointer_ref, selection_errors = selected_pointer(
        root,
        explicit_pointer=args.pointer,
        records=records,
        base_ref=args.base_ref,
        staged=args.staged,
    )
    if selection_errors:
        for error in selection_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if pointer_ref is None:
        print("active packet gate: no packet pointer required for this preflight")
        return 0
    errors = (
        validate_staged_pointer_gate(root, pointer_ref)
        if args.staged
        else validate_release_pointer_gate(root, pointer_ref, base_ref=args.base_ref)
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"active packet gate: PASS {pointer_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
