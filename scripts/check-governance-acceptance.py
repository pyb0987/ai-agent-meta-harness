#!/usr/bin/env python3
"""Create and validate v2 AcceptancePacket skeletons."""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import uuid

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "v2.0-draft"
INFERENCE_RULE_VERSION = "v2.0-draft"
PACKET_KEY = "AcceptancePacket"
POINTER_KEY = "AcceptancePacketPointer"
POINTER_SCHEMA_VERSION = "acceptance-packet-pointer/v1"
COMMAND_EVIDENCE_HEADING = "# Command Evidence"
COMMAND_EVIDENCE_FIELD_RE = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$")
CHECKER_REF = "scripts/check-governance-acceptance.py"
COMMAND_ARCHIVE_REPLAY_METADATA_VALUES = {"pointer-bound"}
COMMAND_ARCHIVE_REPLAY_METADATA_FIELDS = (
    "replay_metadata",
    "replay_recorded_by",
    "replay_recorded_at",
    "replay_checker_ref",
)
LEGACY_COMMAND_ARCHIVE_PROVENANCE_FIELDS = ("archive_provenance", "generated_by", "generated_at", "runner_ref")
COMMAND_ARCHIVE_REPLAY_FIELDS = ("exit_code", "stdout_sha256", "stderr_sha256")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
FULL_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
PUBLIC_SECTIONS = ("meta", "input", "result")
ARCHIVE_PACKET_PREFIX = "archive/v2/packets/"
ARCHIVE_ARTIFACT_PREFIX = "archive/v2/artifacts/"
DEFAULT_POINTER_PREFIX = "archive/v2/pointers/"
ARCHIVE_COMMIT_AUTHOR_NAME = "Acceptance Archive"
ARCHIVE_COMMIT_AUTHOR_EMAIL = "acceptance-archive@example.invalid"
ARCHIVE_COMMIT_DATE = "2000-01-01T00:00:00+0000"
TRUSTED_REPLAY_PATH_ENTRIES = tuple(
    dict.fromkeys(
        [
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
        ]
    )
)
TRUSTED_REPLAY_PATH = os.pathsep.join(TRUSTED_REPLAY_PATH_ENTRIES)
POINTER_FIELDS = {
    "schema_version",
    "packet_id",
    "packet_ref",
    "packet_sha256",
    "checker_version",
    "inference_rule_version",
    "baseline_ref",
    "comparison_ref",
    "head_commit",
    "archive_commit",
    "stable_target",
    "decision_status",
    "command_artifacts",
    "claim_artifacts",
    "review_import_artifacts",
    "probe_transcripts",
}
LEGACY_POINTER_FIELDS = POINTER_FIELDS - {"claim_artifacts"}
POINTER_COMMAND_ARTIFACT_FIELDS = {"artifact_ref", "artifact_sha256", "command"}
POINTER_CLAIM_ARTIFACT_FIELDS = {"source_ref", "source_sha256"}
POINTER_REVIEW_IMPORT_ARTIFACT_FIELDS = {"source_ref", "source_sha256", "review_target_digest", "review_ids"}
POINTER_PROBE_TRANSCRIPT_FIELDS = {
    "source_ref",
    "transcript_sha256",
    "result_ref",
    "result_digest",
    "packet_ref",
    "packet_sha256",
}
CANONICAL_ACCEPTANCE_PACKET_FIXTURES = {
    "backlog/fixtures/acceptance-packets/blocked.yml",
    "backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml",
    "backlog/fixtures/acceptance-packets/finalized-routine.yml",
    "backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml",
    "backlog/fixtures/acceptance-packets/start.yml",
    "backlog/fixtures/acceptance-packets/worktree-nonstable.yml",
}
FIXTURE_MATERIALIZATION_MARKER = ".fixture-materialization"
FIXTURE_MATERIALIZATION_ENV = "AI_META_HARNESS_TEST_FIXTURE_MATERIALIZATION"
META_FIELDS = ("packet_id", "schema_version", "lifecycle", "mode", "created_at", "finalized_at")
INPUT_FIELDS = ("intent", "actor", "source_refs", "user_judgment")
RESULT_GROUPS = ("inference", "evidence", "judgment", "decision")
FINALIZED_INFERENCE_FIELDS = (
    "change_class",
    "impact",
    "changed_paths",
    "intended_scope",
    "actual_scope",
    "deviations",
    "isolation",
    "protected_boundary_changed",
    "required_evidence",
    "required_review",
)
PROVENANCE_FIELDS = ("actor", "role", "date", "reason", "source_ref")
REVIEW_PROVENANCE_FIELDS = ("actor", "role", "date", "source_ref")
REVIEW_IMPORT_KEY = "AcceptancePacketReviewImport"
REVIEW_IMPORT_SCHEMA_VERSION = "acceptance-packet-review-import/v1"
REVIEW_IMPORT_FIELDS = {"schema_version", "target_binding", "MultiReviewResult", "review_lineage"}
PROBE_TRANSCRIPT_KEY = "ProbeTranscript"
REVIEW_IMPORT_RECORD_FIELDS = {"source_ref", "format", "source_digest", "status", "review_ids", "target_binding"}
TARGET_BINDING_FIELDS = {
    "packet_id",
    "packet_ref",
    "review_target_digest",
    "baseline_ref",
    "comparison_ref",
    "source_refs",
    "changed_paths",
    "required_review",
}
REVIEW_LINEAGE_FIELDS = {
    "review_id",
    "critic",
    "scope",
    "anti_scope",
    "score",
    "veto",
    "actor",
    "role",
    "date",
    "source_ref",
    "false_green_risk",
    "invariant_checked",
    "evidence",
    "source_refs",
    "blocking_findings",
    "why_not_10",
    "disposition",
    "rerun_of",
    "fixed_finding_ids",
}
REVIEW_MIRROR_FIELDS = REVIEW_LINEAGE_FIELDS
VACUOUS_REVIEW_VALUES = {
    "",
    "none",
    "na",
    "ok",
    "pass",
    "checked",
    "generic",
    "notapplicable",
    "selfattested",
    "readtheplan",
}
TARGET_FIELDS = ("evidence", "review", "from")
LIFECYCLES = {"start", "finalized", "blocked"}
MODES = {"staged", "base-ref", "worktree"}
PROTECTED_PREFIXES = (
    ".githooks/",
    "adapters/",
    "archive/v1/",
    "commands/",
    "core/",
    "plugins/",
    "scripts/",
    "skills/",
)
PROTECTED_PATHS = {
    ".harness/traces/search-set.md",
    "MAINTENANCE.md",
    "README.md",
}
REQUIRED_RESOLVED_REF_FIELDS = ("origin", "relation", "ref", "status", "target")
RESOLVED_REF_ORIGINS = {"input", "generated"}
RESOLVED_REF_RELATIONS = {
    "source",
    "artifact",
    "trace",
    "claim-evidence",
    "review-provenance",
    "waiver-provenance",
    "observation",
}
ANCHOR_RE = re.compile(r"[^a-z0-9]+")
PROOF_LIKE_RE = re.compile(
    r"\b(verified|guaranteed|proves?|runtime|public API|release-ready|production-ready)\b",
    re.IGNORECASE,
)
SEARCH_SET_TRACE_ANCHORS = {"active"}
SEARCH_SET_CAPTURE_ANCHOR_RE = re.compile(r"^search-set-(before|after)-[0-9a-z-]+$")
SEARCH_SET_CAPTURE_COMMAND = "python3 scripts/run-search-set.py"
SEARCH_SET_CAPTURE_SYNTAX_RE = re.compile(r"[|&;<>()[\]{}$`\\*?\n]")
SEARCH_SET_CAPTURE_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEARCH_SET_CAPTURE_FIELD_RE = re.compile(r"^- \*\*([A-Za-z0-9_]+)\*\*: ?(.*)$")
SEARCH_SET_CAPTURE_REQUIRED_FIELDS = (
    "phase",
    "status",
    "command",
    "exit_code",
    "stdout_sha256",
    "stderr_sha256",
    "head_ref",
    "captured_at",
)
RAW_CLAIM_EVIDENCE_PATH_PARTS = {
    ".harness",
    "artifact",
    "artifacts",
    "log",
    "logs",
    "probe-transcripts",
    "reports",
    "screenshots",
    "trace",
    "traces",
    "transcripts",
}
RAW_CLAIM_EVIDENCE_DIRECT_SUFFIXES = {
    ".csv",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".jsonl",
    ".log",
    ".pdf",
    ".png",
    ".tsv",
    ".webp",
}
RAW_CLAIM_EVIDENCE_CONTEXTUAL_SUFFIXES = {".json", ".txt", ".xml", ".yaml", ".yml"}
STRATEGY_SEARCH_DIAGNOSTIC_BASENAMES = {
    "patch.diff",
    "proposals.jsonl",
    "run.yml",
    "score.yml",
    "scores.jsonl",
    "stderr.log",
    "stdout.log",
    "trace.md",
    "trace.yaml",
    "trace.yml",
}
POINTER_SUFFIXES = (".yml", ".yaml")
GIT_ENV_PREFIX = "GIT_"

class PacketError(ValueError):
    pass


def git_env(*, keep_index: bool = False) -> dict[str, str]:
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
    env["PATH"] = TRUSTED_REPLAY_PATH
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def git(root: Path, args: list[str], *, check: bool = False, keep_index: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        env=git_env(keep_index=keep_index),
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_bytes(root: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        env=git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_with_env(root: Path, args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        env=env,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_objects_dir(root: Path) -> Path | None:
    result = git(root, ["rev-parse", "--git-path", "objects"])
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else root / path


def today() -> dt.date:
    return dt.date.today()


def packet_id() -> str:
    return f"pkt-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def load_packet(path: Path) -> dict:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PacketError(f"{path}: cannot read packet: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PacketError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict) or PACKET_KEY not in loaded:
        raise PacketError(f"{path}: missing {PACKET_KEY}")
    packet = loaded[PACKET_KEY]
    if not isinstance(packet, dict):
        raise PacketError(f"{path}: {PACKET_KEY} must be a mapping")
    return packet


def load_pointer(path: Path) -> dict:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PacketError(f"{path}: cannot read pointer: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PacketError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(loaded, dict) or POINTER_KEY not in loaded:
        raise PacketError(f"{path}: missing {POINTER_KEY}")
    pointer = loaded[POINTER_KEY]
    if not isinstance(pointer, dict):
        raise PacketError(f"{path}: {POINTER_KEY} must be a mapping")
    return pointer


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_anchor(text: str) -> str:
    return ANCHOR_RE.sub("-", text.strip().lower()).strip("-")


def has_markdown_anchor(path: Path, anchor: str) -> bool:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") and markdown_anchor(line.lstrip("#").strip()) == anchor:
                return True
    except OSError:
        return False
    return False


def resolve_repo_path(root: Path, ref_path: str) -> str | None:
    path = Path(ref_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    candidate = (root / path).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        return None
    if not candidate.exists():
        return None
    return candidate.relative_to(root_resolved).as_posix()


def repo_path_has_symlink(root: Path, path: Path) -> bool:
    root_abs = Path(os.path.abspath(os.path.normpath(root)))
    candidate_abs = Path(os.path.abspath(os.path.normpath(path)))
    try:
        rel = candidate_abs.relative_to(root_abs)
    except ValueError:
        return path.is_symlink()
    current = root_abs
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def resolve_archive_file_ref_path(root: Path, ref_path: str) -> str | None:
    path = Path(ref_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    rel = path.as_posix()
    if not rel.startswith("archive/v2/"):
        return None
    candidate = root / rel
    if repo_path_has_symlink(root, candidate) or not candidate.is_file():
        return None
    return rel


def resolve_ref(root: Path, ref: str) -> str | None:
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("terminal:"):
        return None
    if ref.startswith("file:"):
        rel = ref.removeprefix("file:")
        if rel.startswith("archive/v2/"):
            return resolve_archive_file_ref_path(root, rel)
        return resolve_repo_path(root, rel)
    if ref.startswith("trace:"):
        body = ref.removeprefix("trace:")
        rel, sep, anchor = body.partition("#")
        resolved = resolve_repo_path(root, rel)
        if resolved is None:
            return None
        path = root / resolved
        if sep and not has_markdown_anchor(path, anchor):
            return None
        return body
    if ref.startswith("git:"):
        spec = ref.removeprefix("git:")
        result = git(root, ["rev-parse", "--verify", spec])
        if result.returncode == 0:
            return spec
        result = git(root, ["cat-file", "-e", spec])
        return spec if result.returncode == 0 else None
    if "://" in ref:
        return None
    return resolve_repo_path(root, ref)


def markdown_section_lines(path: Path, anchor: str) -> list[str] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    in_section = False
    section: list[str] = []
    for line in lines:
        if line.startswith("#"):
            line_anchor = markdown_anchor(line.lstrip("#").strip())
            if in_section:
                break
            if line_anchor == anchor:
                in_section = True
                continue
        if in_section:
            section.append(line)
    return section if in_section else None


def unbacktick(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1].strip()
    return stripped


def search_set_capture_fields(root: Path, ref: str) -> tuple[dict[str, str], str | None]:
    path_ref = trace_ref_path(ref)
    anchor = trace_ref_anchor(ref)
    if not path_ref or not anchor:
        return {}, f"search-set capture ref is not canonical: {ref}"
    path = root / path_ref
    section = markdown_section_lines(path, anchor)
    if section is None:
        return {}, f"search-set capture section does not resolve: {ref}"
    fields: dict[str, str] = {}
    for line in section:
        match = SEARCH_SET_CAPTURE_FIELD_RE.fullmatch(line.strip())
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields, None


def search_set_capture_record_error(
    root: Path,
    ref: str,
    *,
    expected_phase: str | None = None,
    expected_packet_ref: str | None = None,
    expected_head_ref: str | None = None,
) -> str | None:
    anchor = trace_ref_anchor(ref)
    if not isinstance(anchor, str) or not SEARCH_SET_CAPTURE_ANCHOR_RE.fullmatch(anchor):
        if expected_phase:
            return f"search-set capture ref must use search-set-{expected_phase}-* anchor: {ref}"
        return None
    fields, section_error = search_set_capture_fields(root, ref)
    if section_error:
        return section_error
    missing = [name for name in SEARCH_SET_CAPTURE_REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        return f"search-set capture record is missing required fields {missing}: {ref}"
    phase = fields["phase"]
    if phase not in {"before", "after"}:
        return f"search-set capture record phase must be before or after: {ref}"
    if expected_phase and phase != expected_phase:
        return f"search-set capture record phase must be {expected_phase}: {ref}"
    anchor_phase = SEARCH_SET_CAPTURE_ANCHOR_RE.fullmatch(anchor).group(1)
    if phase != anchor_phase:
        return f"search-set capture record phase must match anchor phase {anchor_phase}: {ref}"
    if fields["status"] != "PASS":
        return f"search-set capture record status must be PASS: {ref}"
    if fields["exit_code"] != "0":
        return f"search-set capture record exit_code must be 0: {ref}"
    for stream_field in ("stdout_sha256", "stderr_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", fields[stream_field]):
            return f"search-set capture record {stream_field} must be a sha256 hex digest: {ref}"
    command = unbacktick(fields["command"])
    if command != SEARCH_SET_CAPTURE_COMMAND:
        return f"search-set capture record command must be {SEARCH_SET_CAPTURE_COMMAND!r}: {ref}"
    head_ref = unbacktick(fields["head_ref"])
    if not FULL_COMMIT_RE.fullmatch(head_ref):
        return f"search-set capture record head_ref must be a full commit SHA: {ref}"
    if git_ref_commit(root, head_ref) != head_ref:
        return f"search-set capture record head_ref must resolve to a commit: {ref}"
    if expected_head_ref is not None and head_ref != expected_head_ref:
        return f"search-set capture record head_ref must match packet boundary {expected_head_ref}: {ref}"
    if expected_packet_ref is not None and fields.get("packet_ref") != f"`{expected_packet_ref}`":
        return f"search-set capture record packet_ref must match packet ref {expected_packet_ref}: {ref}"
    if not date_like(fields["captured_at"]):
        return f"search-set capture record captured_at must be an ISO date not in the future: {ref}"
    return None


def search_set_trace_ref_error(
    root: Path,
    ref: object,
    *,
    field: str,
    expected_phase: str | None = None,
) -> str | None:
    if not isinstance(ref, str) or not ref:
        return f"{field} must be a non-empty trace ref"
    if not ref.startswith("trace:"):
        return f"{field} must use trace: scheme: {ref}"
    if not trace_ref_has_anchor(ref):
        return f"{field} must include an anchor: {ref}"
    if not is_search_set_trace_ref(ref):
        return f"{field} must point to .harness/traces/search-set.md with an allowed search-set anchor: {ref}"
    if resolve_ref(root, ref) is None:
        return f"{field} does not resolve: {ref}"
    if error := search_set_capture_record_error(root, ref, expected_phase=expected_phase):
        return f"{field}: {error}"
    return None


def search_set_capture_argv(command: str) -> tuple[list[str] | None, str | None]:
    if SEARCH_SET_CAPTURE_SYNTAX_RE.search(command):
        return None, (
            "search-set capture command contains shell syntax; use a plain argv "
            "command without pipes, redirects, chaining, command substitution, or globs"
        )
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, f"search-set capture command cannot be parsed as argv: {exc}"
    if not argv:
        return None, "search-set capture command is empty"
    if SEARCH_SET_CAPTURE_ENV_ASSIGNMENT_RE.match(argv[0]):
        return None, "search-set capture command uses an environment assignment prefix"
    return argv, None


def search_set_capture_heading(phase: str, *, packet_ref: str | None = None) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix_source = packet_ref or uuid.uuid4().hex
    suffix = safe_artifact_stem(suffix_source)[-12:] or uuid.uuid4().hex[:12]
    return f"Search-set {phase} {stamp} {suffix} {uuid.uuid4().hex[:8]}"


def search_set_capture_stream_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def search_set_capture_record(
    *,
    heading: str,
    phase: str,
    command: str,
    completed: subprocess.CompletedProcess[str],
    head_ref: str,
    packet_ref: str | None,
    note: str | None,
) -> str:
    status = "PASS" if completed.returncode == 0 else "FAIL"
    stdout_text = search_set_capture_stream_text(completed.stdout)
    stderr_text = search_set_capture_stream_text(completed.stderr)
    stdout_sha = hashlib.sha256(stdout_text.encode("utf-8")).hexdigest()
    stderr_sha = hashlib.sha256(stderr_text.encode("utf-8")).hexdigest()
    lines = [
        f"### {heading}",
        f"- **phase**: {phase}",
        f"- **status**: {status}",
        f"- **command**: `{command}`",
        f"- **exit_code**: {completed.returncode}",
        f"- **stdout_sha256**: {stdout_sha}",
        f"- **stderr_sha256**: {stderr_sha}",
        f"- **head_ref**: `{head_ref}`",
        f"- **captured_at**: {today().isoformat()}",
    ]
    if packet_ref:
        lines.append(f"- **packet_ref**: `{packet_ref}`")
    if note:
        lines.append(f"- **note**: {note}")
    return "\n".join(lines) + "\n"


def append_search_set_capture(root: Path, record: str) -> None:
    path = root / ".harness/traces/search-set.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PacketError(f"cannot read {path.relative_to(root).as_posix()}: {exc}") from exc
    if "\n## Search-set Evidence Captures\n" not in text:
        text = text.rstrip() + "\n\n## Search-set Evidence Captures\n\n"
    else:
        text = text.rstrip() + "\n\n"
    write_text_atomic(path, text + record)


def trace_ref_has_anchor(ref: str) -> bool:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return False
    body = ref.removeprefix("trace:")
    rel, sep, anchor = body.partition("#")
    return bool(rel and sep and anchor)


def trace_ref_path(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return None
    body = ref.removeprefix("trace:")
    rel, _sep, _anchor = body.partition("#")
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        return None
    normalized = posixpath.normpath(rel)
    return None if normalized == "." else normalized


def trace_ref_anchor(ref: str) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("trace:"):
        return None
    body = ref.removeprefix("trace:")
    _rel, sep, anchor = body.partition("#")
    return anchor if sep and anchor else None


def canonical_trace_ref(ref: str) -> str | None:
    path = trace_ref_path(ref)
    anchor = trace_ref_anchor(ref)
    if not path or not anchor:
        return None
    return f"trace:{path}#{anchor}"


def is_search_set_trace_ref(ref: str) -> bool:
    canonical = canonical_trace_ref(ref)
    anchor = trace_ref_anchor(ref)
    return (
        canonical == ref
        and trace_ref_path(ref) == ".harness/traces/search-set.md"
        and (
            anchor in SEARCH_SET_TRACE_ANCHORS
            or (isinstance(anchor, str) and SEARCH_SET_CAPTURE_ANCHOR_RE.fullmatch(anchor))
        )
    )


def is_search_set_trace_path_ref(ref: str) -> bool:
    return trace_ref_path(ref) == ".harness/traces/search-set.md"


def is_harness_trace_ref(ref: str) -> bool:
    canonical = canonical_trace_ref(ref)
    path = trace_ref_path(ref)
    return bool(canonical == ref and path and path.startswith(".harness/traces/"))


def is_claim_evidence_trace_ref(ref: str) -> bool:
    return is_harness_trace_ref(ref) and not is_search_set_trace_path_ref(ref)


def is_bucket_trace_ref(ref: str, bucket_name: str) -> bool:
    canonical = canonical_trace_ref(ref)
    path = trace_ref_path(ref)
    return bool(
        canonical == ref
        and path
        and path.startswith(f".harness/traces/{bucket_name}/")
    )


def is_strategy_search_diagnostic_claim_artifact(root: Path, path: str) -> bool:
    local_path = root / path
    name = Path(path).name.casefold()
    if name in STRATEGY_SEARCH_DIAGNOSTIC_BASENAMES:
        return True
    if "strategy-search" in path.casefold():
        return True
    if local_path.exists() and local_path.is_file():
        try:
            if local_path.stat().st_nlink > 1:
                return True
        except OSError:
            return True
        suffix = Path(path).suffix.casefold()
        if suffix in RAW_CLAIM_EVIDENCE_DIRECT_SUFFIXES | RAW_CLAIM_EVIDENCE_CONTEXTUAL_SUFFIXES:
            try:
                sample = local_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return True
            if "schema_version" in sample and "strategy-search-" in sample:
                return True
            if "evidence_status" in sample and "diagnostic_only" in sample:
                return True
            if "strategy-search invalid candidate:" in sample:
                return True
            nonempty_lines = [line.strip() for line in sample.splitlines() if line.strip()]
            if re.search(r"(?im)^\s*score\s*[:=]\s*\d+(?:\.\d+)?\s*$", sample) and re.search(
                r"(?im)^\s*case\s*[:=]\s*[A-Za-z0-9._-]+\s*[:= ]\s*(pass|fail|skip|xfail)\s*$",
                sample,
            ):
                return True
            if nonempty_lines and all(
                re.match(r"(?i)^(?:score|case)\s*[:=]\s+", line)
                or re.match(r"(?i)^(?:candidate_id|verdict|score_path)\s*[:=]\s+", line)
                for line in nonempty_lines
            ):
                return True
    return False


def is_raw_claim_file_ref(root: Path, ref: str) -> bool:
    if not isinstance(ref, str) or not ref.startswith("file:"):
        return False
    path = ref.removeprefix("file:").split("#", 1)[0]
    if not path.startswith(ARCHIVE_ARTIFACT_PREFIX):
        return False
    resolved = resolve_archive_file_ref_path(root, path)
    if resolved is None or resolved != path:
        return False
    if is_strategy_search_diagnostic_claim_artifact(root, path):
        return False
    parts = {part.casefold() for part in Path(path).parts}
    suffix = Path(path).suffix.casefold()
    local_path = root / path
    if suffix in {".yml", ".yaml"} and local_path.is_file():
        try:
            loaded = yaml.safe_load(local_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            loaded = None
        if isinstance(loaded, dict):
            schema = loaded.get("schema_version")
            if loaded.get("evidence_status") == "diagnostic_only":
                return False
            if isinstance(schema, str) and schema.startswith("strategy-search-"):
                return False
    if suffix in RAW_CLAIM_EVIDENCE_DIRECT_SUFFIXES:
        return True
    if parts & RAW_CLAIM_EVIDENCE_PATH_PARTS and suffix in RAW_CLAIM_EVIDENCE_CONTEXTUAL_SUFFIXES:
        return True
    return False


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, path)
    except OSError:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def packet_document_text(packet: dict) -> str:
    return yaml.safe_dump({PACKET_KEY: packet}, sort_keys=False, allow_unicode=False)


def write_packet(path: Path, packet: dict, *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise PacketError(f"{path}: already exists; refusing to overwrite")
    write_text_atomic(path, packet_document_text(packet))


def date_like(value: object, *, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none
    parsed = parsed_date(value)
    return parsed is not None and parsed <= dt.date.today()


def parsed_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def canonical_vacuous_value(value: str) -> str:
    normalized = " ".join(value.strip().strip("\"'").casefold().split())
    return re.sub(r"[^a-z0-9]+", "", normalized)


def required_targets(packet: dict) -> tuple[set[str], set[str]]:
    inference = packet["result"]["inference"]
    required_evidence = inference.get("required_evidence", [])
    required_review = inference.get("required_review", [])
    if not isinstance(required_evidence, list):
        required_evidence = []
    if not isinstance(required_review, list):
        required_review = []
    return (
        {item for item in required_evidence if isinstance(item, str)},
        {item for item in required_review if isinstance(item, str)},
    )


def checker_required_evidence(packet: dict) -> set[str]:
    meta = packet["meta"]
    inference = packet["result"]["inference"]
    evidence = packet["result"]["evidence"]
    mode = meta.get("mode")
    comparison_ref = evidence.get("comparison_ref")
    accepted_head_commit = evidence.get("accepted_head_commit")
    head_ref = accepted_head_commit if isinstance(accepted_head_commit, str) and accepted_head_commit else "HEAD"
    changed_paths = string_list_values(inference.get("changed_paths", []))
    changed = set(changed_paths)

    archive_changed = any(path.startswith("archive/v1/") for path in changed)
    legacy_release_gate_changed = bool({"scripts/verify-release.py", "scripts/check-v1-archive-boundary.py"} & changed)
    active_release_gate_changed = "scripts/check-active-packet-gate.py" in changed
    pre_commit_gate_changed = ".githooks/pre-commit" in changed
    release_gate_changed = legacy_release_gate_changed or active_release_gate_changed or pre_commit_gate_changed

    required: set[str] = set()

    if release_gate_changed and mode == "base-ref" and comparison_ref:
        required.add(f"python3 scripts/verify-release.py --list --base-ref {comparison_ref} --skip-clean-worktree")
        if legacy_release_gate_changed:
            required.update(
                {
                    f"python3 scripts/check-v1-archive-boundary.py --base-ref {comparison_ref}",
                    "python3 -m unittest tests/test_v1_archive_boundary.py tests/test_verify_release.py",
                }
            )
        if active_release_gate_changed:
            required.add("python3 -m unittest tests/test_active_packet_gate.py tests/test_verify_release.py")
        if pre_commit_gate_changed:
            required.update(
                {
                    "sh .githooks/pre-commit",
                    "python3 -m unittest tests/test_pre_commit_hook.py tests/test_active_packet_gate.py",
                }
            )

    if archive_changed:
        if mode == "staged":
            required.add("python3 scripts/check-v1-archive-boundary.py --staged")
            required.add("python3 scripts/verify-release.py")
        elif mode == "base-ref" and comparison_ref:
            required.add(f"python3 scripts/check-v1-archive-boundary.py --base-ref {comparison_ref}")
            required.add(f"python3 scripts/verify-release.py --list --base-ref {comparison_ref} --skip-clean-worktree")
        else:
            required.add("python3 scripts/verify-release.py")

    if mode == "staged":
        required.add("git diff --cached --check")
    elif mode == "base-ref" and comparison_ref and not required:
        required.add(f"git diff --check {comparison_ref}...{head_ref}")
    elif mode == "worktree":
        required.add("git diff --check")
    return required


def stable_required_evidence(packet: dict) -> tuple[set[str], list[str]]:
    evidence = packet["result"]["evidence"]
    required = checker_required_evidence(packet)
    boundary = evidence.get("evaluator_boundary")
    errors: list[str] = []
    if not isinstance(boundary, dict):
        return required, ["result.evidence.evaluator_boundary must be a mapping for stable packets"]
    commands = boundary.get("commands")
    if not isinstance(commands, list):
        return required, ["result.evidence.evaluator_boundary.commands must be a list for stable packets"]
    invalid_commands = [command for command in commands if not isinstance(command, str) or not command]
    boundary_required = {command for command in commands if isinstance(command, str) and command}
    if invalid_commands:
        errors.append("result.evidence.evaluator_boundary.commands must contain only non-empty strings")
    if boundary_required != required:
        errors.append(
            "result.evidence.evaluator_boundary.commands must match checker-derived required evidence: "
            f"{sorted(required)}"
        )
    return required, errors


def text_mentions_scope_boundary(path: str, text: str) -> bool:
    lowered_path = path.casefold()
    if path.startswith("archive/v1/"):
        return False
    if "multi-review" in lowered_path or "review" in lowered_path:
        return True
    if any(marker in lowered_path for marker in ("waiver", "downgrade", "not-required", "not_required")):
        return True
    if not path.endswith(".md"):
        return False
    text = text.casefold()
    return any(
        phrase in text
        for phrase in (
            "waiver",
            "downgrade",
            "not required",
            "deferred",
            "out of scope",
            "review-governance",
            "review governance",
        )
    )


def path_mentions_scope_boundary(root: Path, path: str) -> bool:
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return False
    return text_mentions_scope_boundary(path, text)


def path_mentions_scope_boundary_at_commit(root: Path, commit_ref: str, path: str) -> bool:
    text = git_text(root, commit_ref, path)
    return bool(text and text_mentions_scope_boundary(path, text))


def base_ref_content_refs(packet: dict) -> list[str] | None:
    meta = packet.get("meta", {})
    result = packet.get("result", {})
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    comparison_ref = evidence.get("comparison_ref")
    accepted_head = evidence.get("accepted_head_commit")
    if isinstance(meta, dict) and meta.get("mode") == "base-ref" and isinstance(comparison_ref, str):
        head_ref = accepted_head if isinstance(accepted_head, str) and accepted_head else "HEAD"
        return list(dict.fromkeys([comparison_ref, head_ref]))
    return None


def path_mentions_scope_boundary_for_packet(root: Path, packet: dict, path: str) -> bool:
    content_refs = base_ref_content_refs(packet)
    if content_refs:
        return any(path_mentions_scope_boundary_at_commit(root, ref, path) for ref in content_refs)
    return path_mentions_scope_boundary(root, path)


def path_has_proof_like_claim_for_packet(root: Path, packet: dict, path: str) -> bool:
    content_refs = base_ref_content_refs(packet)
    if content_refs:
        return any(path_has_proof_like_claim_at_commit(root, ref, path) for ref in content_refs)
    return path_has_proof_like_claim(root, path)


def checker_required_review(packet: dict, *, root: Path = ROOT) -> set[str]:
    meta = packet.get("meta", {}) if isinstance(packet.get("meta"), dict) else {}
    result = packet.get("result", {})
    inference = result.get("inference", {}) if isinstance(result, dict) else {}
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    changed_paths = string_list_values(inference.get("changed_paths", []))
    required: set[str] = set()

    def scope_boundary_changed(path: str) -> bool:
        return path_mentions_scope_boundary_for_packet(root, packet, path)

    def proof_like_changed(path: str) -> bool:
        return path_has_proof_like_claim_for_packet(root, packet, path)

    archive_paths = [path for path in changed_paths if path.startswith("archive/v1/")]
    if archive_paths:
        required.update({"archive boundary", "full v1 archive fidelity"})
    protected_paths = [path for path in changed_paths if requires_review_for_path(path) and not path.startswith("archive/v1/")]
    if protected_paths:
        required.add("checker correctness")
    if inference.get("protected_boundary_changed") is True and not archive_paths:
        required.add("checker correctness")
    if inference.get("impact") == "high" and not required:
        required.add("checker correctness")

    if any(
        path.startswith(".githooks/")
        or path
        in {
            "scripts/verify-release.py",
            "scripts/check-v1-archive-boundary.py",
            "scripts/check-active-packet-gate.py",
        }
        or "pre-commit" in path
        or "release" in path
        or "archive-boundary" in path
        or "stable" in path
        for path in changed_paths
    ):
        required.add("release integration")

    if any(
        path in {"MAINTENANCE.md", "README.md", "backlog/v2-roadmap.md"}
        or path == "scripts/check-v1-archive-boundary.py"
        or path.startswith("backlog/plans/")
        or path.startswith("core/")
        for path in changed_paths
    ):
        required.add("methodology fidelity")

    evidence_surfaces = (
        "source_ref",
        "source_refs",
        "artifact_ref",
        "artifact_refs",
        "trace_ref",
        "trace_refs",
        "review-provenance",
        "waiver-provenance",
        "acceptance-packets",
        "check-governance-acceptance",
        "governance_evidence",
    )
    if any(
        any(surface in path for surface in evidence_surfaces)
        and path != "backlog/fixtures/acceptance-packets/README.md"
        for path in changed_paths
    ):
        required.add("evidence auditability")

    if any(scope_boundary_changed(path) for path in changed_paths):
        required.add("scope boundary")

    if any(path.endswith(".md") and proof_like_changed(path) for path in changed_paths):
        required.add("claim evidence")

    evaluator_boundary = evidence.get("evaluator_boundary", {})
    if isinstance(evaluator_boundary, dict):
        status = evaluator_boundary.get("status")
        if status is not None and status != "unchanged":
            required.add("evaluator boundary")

    return required


def sorted_key_names(keys: object) -> list[str]:
    return sorted(str(key) for key in keys)


def schema_field_errors(record: dict, expected_fields: set[str], *, source: str, label: str) -> list[str]:
    string_keys = {key for key in record if isinstance(key, str)}
    errors: list[str] = []
    missing = sorted(expected_fields - string_keys)
    extra = sorted_key_names(key for key in record if not isinstance(key, str) or key not in expected_fields)
    if missing:
        errors.append(f"{source}: {label} missing fields: {missing}")
    if extra:
        errors.append(f"{source}: {label} extra fields: {extra}")
    return errors


def target_entries(record: dict, fields: tuple[str, ...], *, source: str, errors: list[str]) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for field in fields:
        if field not in record:
            continue
        value = record.get(field)
        if review_value_is_substantive_string(value):
            targets.append((field, value))
        else:
            errors.append(f"{source}: target field {field} must be a substantive string")
    return targets


def exception_target(record: dict, *, source: str, errors: list[str]) -> tuple[str, str] | None:
    targets = target_entries(record, TARGET_FIELDS, source=source, errors=errors)
    if len(targets) != 1:
        return None
    return targets[0]


def target_allowed(
    field: str,
    target: str,
    required_evidence: set[str],
    required_review: set[str],
    *,
    kind: str | None = None,
) -> bool:
    if field == "evidence":
        return target in required_evidence
    if field == "review":
        return target in required_review
    if kind == "evidence":
        return target in required_evidence
    if kind == "review":
        return target in required_review
    return target in required_evidence or target in required_review


def validate_provenance_record(record: dict, *, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: judgment record must be a mapping"]
    for field in ("actor", "role", "reason", "source_ref"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} is required")
    if not record.get("date"):
        errors.append(f"{source}: date is required")
    elif not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    return errors


def residual_risk_target(record: dict, *, source: str, errors: list[str]) -> tuple[str, str] | None:
    targets = target_entries(record, ("evidence", "review"), source=source, errors=errors)
    if len(targets) != 1:
        return None
    return targets[0]


def validate_residual_risk_record(
    record: dict,
    *,
    required_evidence: set[str],
    required_review: set[str],
    source: str,
) -> list[str]:
    errors = validate_provenance_record(record, source=source)
    if errors and not isinstance(record, dict):
        return errors
    for forbidden in ("from", "to"):
        if forbidden in record:
            errors.append(f"{source}: residual risk cannot include {forbidden}")
    target = residual_risk_target(record, source=source, errors=errors)
    if target is None:
        errors.append(f"{source}: residual risk must target exactly one required evidence/review item")
        return errors
    field, value = target
    required = required_evidence if field == "evidence" else required_review
    if value not in required:
        errors.append(f"{source}: residual risk target is not required: {value}")
    return errors


def mapping_records(value: object, *, source: str, errors: list[str]) -> list[dict]:
    if not isinstance(value, list):
        errors.append(f"{source} must be a list")
        return []
    records: list[dict] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{source}[{index}] must be a mapping")
            continue
        records.append(item)
    return records


def validate_review_record(record: dict, *, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: review record must be a mapping"]
    for field in REVIEW_PROVENANCE_FIELDS:
        if not record.get(field):
            errors.append(f"{source}: {field} is required")
    if record.get("date") and not date_like(record["date"]):
        errors.append(f"{source}: date must be an ISO date")
    if not record.get("critic"):
        errors.append(f"{source}: critic is required")
    return errors


def validate_exception_record(
    record: dict,
    *,
    required_evidence: set[str],
    required_review: set[str],
    source: str,
    record_type: str = "exception",
) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_provenance_record(record, source=source))
    if errors and not isinstance(record, dict):
        return errors
    target = exception_target(record, source=source, errors=errors)
    if target is None:
        errors.append(f"{source}: exception must target exactly one required evidence/review item")
        return errors
    field, value = target
    kind = record.get("kind")
    if kind is not None and not isinstance(kind, str):
        errors.append(f"{source}: exception kind must be evidence or review")
        return errors
    if record_type == "waiver":
        for forbidden in ("from", "to"):
            if forbidden in record:
                errors.append(f"{source}: waiver cannot include {forbidden}")
    if record_type == "downgrade" and field != "from":
        errors.append(f"{source}: downgrade must target from")
        return errors
    if record_type == "waiver" and field == "from":
        errors.append(f"{source}: waiver must target evidence or review")
        return errors
    if field == "from":
        if kind not in {"evidence", "review"}:
            errors.append(f"{source}: downgrade kind must be evidence or review")
        elif not target_allowed(field, value, required_evidence, required_review, kind=kind):
            errors.append(f"{source}: {kind} downgrade target is not required: {value}")
        replacement = record.get("to")
        if not review_value_is_substantive_string(replacement):
            errors.append(f"{source}: downgrade to is required")
        elif replacement == value:
            errors.append(f"{source}: downgrade to must differ from from")
        return errors
    if field == "review":
        if kind != "review":
            errors.append(f"{source}: review waiver kind must be review")
    elif kind and kind != "evidence":
        errors.append(f"{source}: evidence waiver kind must be evidence")
    if not target_allowed(field, value, required_evidence, required_review):
        errors.append(f"{source}: exception target is not required: {value}")
    return errors


def validate_resolved_ref_record(record: dict, *, root: Path, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: resolved ref record must be a mapping"]
    for field in REQUIRED_RESOLVED_REF_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"{source}: {field} is required")
    if errors:
        return errors
    if record["origin"] not in RESOLVED_REF_ORIGINS:
        errors.append(f"{source}: origin must be input or generated")
    if record["relation"] not in RESOLVED_REF_RELATIONS:
        errors.append(f"{source}: relation is invalid: {record['relation']}")
    if record["relation"] == "artifact" and not str(record["ref"]).startswith("file:"):
        errors.append(f"{source}: artifact refs must use file: scheme")
    if record["relation"] == "trace":
        if not str(record["ref"]).startswith("trace:"):
            errors.append(f"{source}: trace refs must use trace: scheme")
        elif not trace_ref_has_anchor(record["ref"]):
            errors.append(f"{source}: trace refs must include an anchor")
    if record["relation"] == "source" and str(record["ref"]).startswith("trace:"):
        if not trace_ref_has_anchor(record["ref"]):
            errors.append(f"{source}: trace source refs must include an anchor")
    if record["relation"] == "source" and str(record["ref"]).startswith("git:"):
        source_path = git_source_ref_path(root, record["ref"])
        if source_path is None:
            errors.append(f"{source}: git source refs must use git:<full-commit-sha>:<repo-path> form")
        elif git_resolved_target_path(record["target"]) != source_path:
            errors.append(f"{source}: git source target must expose repo path: {record['ref']}")
    if (
        record["origin"] == "generated"
        and record["relation"] == "claim-evidence"
        and not str(record["ref"]).startswith("file:")
    ):
        errors.append(f"{source}: generated claim-evidence refs must use file: scheme")
    if (
        record["origin"] == "generated"
        and record["relation"] in {"review-provenance", "waiver-provenance"}
        and not str(record["ref"]).startswith("file:")
    ):
        errors.append(f"{source}: generated {record['relation']} refs must use file: scheme")
    resolved = resolve_ref(root, record["ref"])
    if record["status"] == "resolved":
        if resolved is None:
            errors.append(f"{source}: resolved ref does not resolve: {record['ref']}")
        elif record["target"] != resolved:
            errors.append(f"{source}: target does not match resolved ref: {record['ref']}")
    elif record["status"] == "local-placeholder":
        if not str(record["ref"]).startswith("terminal:") or record["relation"] != "observation":
            errors.append(f"{source}: local-placeholder is only valid for terminal observation refs")
    else:
        errors.append(f"{source}: status must be resolved or local-placeholder")
    return errors


def resolved_ref_index(records: list[dict]) -> dict[tuple[str, str], list[dict]]:
    index: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        if (
            isinstance(record, dict)
            and isinstance(record.get("relation"), str)
            and isinstance(record.get("ref"), str)
        ):
            index.setdefault((record.get("relation"), record.get("ref")), []).append(record)
    return index


def has_resolved_relation(
    index: dict[tuple[str, str], list[dict]],
    *,
    relation: str,
    ref: str,
    origin: str | None = None,
) -> bool:
    if not isinstance(ref, str):
        return False
    return any(
        record.get("status") == "resolved" and (origin is None or record.get("origin") == origin)
        for record in index.get((relation, ref), [])
    )


def command_base_ref(command: str) -> str | None:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    if "--base-ref" in parts:
        index = parts.index("--base-ref")
        if index + 1 < len(parts):
            return parts[index + 1]
    for part in parts:
        if part.startswith("--base-ref="):
            return part.split("=", 1)[1]
        if "...HEAD" in part:
            return part.split("...HEAD", 1)[0]
    return None


def artifact_text(root: Path, artifact_ref: str) -> str | None:
    if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
        return None
    resolved = resolve_ref(root, artifact_ref)
    if resolved is None:
        return None
    try:
        return (root / resolved).read_text(encoding="utf-8")
    except OSError:
        return None


def artifact_has_field(text: str, field: str, value: str) -> bool:
    return any(line.strip() == f"{field}: {value}" for line in text.splitlines())


def field_section_records_values(text: str, expected: dict[str, str]) -> bool:
    normalized_expected = {
        field: normalize_review_field(value) for field, value in expected.items()
    }
    return any(
        all(section.get(field) == value for field, value in normalized_expected.items())
        for section in markdown_field_sections(text)
    )


def command_evidence_sections_exact(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    return [
        command_evidence_section_fields(lines, start, end)
        for start, end in command_evidence_section_bounds(lines)
        if not command_evidence_section_duplicate_fields(lines, start, end)
    ]


def command_evidence_section_bounds(lines: list[str]) -> list[tuple[int, int]]:
    starts = [index for index, line in enumerate(lines) if line.strip() == COMMAND_EVIDENCE_HEADING]
    headings = [index for index, line in enumerate(lines) if line.lstrip().startswith("#")]
    bounds: list[tuple[int, int]] = []
    for start in starts:
        end = next((heading for heading in headings if heading > start), len(lines))
        bounds.append((start, end))
    return bounds


def command_evidence_section_fields(lines: list[str], start: int, end: int) -> dict[str, str]:
    fields: dict[str, str] = {}
    for index in range(start + 1, end):
        match = COMMAND_EVIDENCE_FIELD_RE.match(lines[index])
        if match:
            key = match.group(1).casefold().replace("-", "_")
            fields[key] = match.group(2)
    return fields


def command_evidence_section_duplicate_fields(lines: list[str], start: int, end: int) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for index in range(start + 1, end):
        match = COMMAND_EVIDENCE_FIELD_RE.match(lines[index])
        if not match:
            continue
        key = match.group(1).casefold().replace("-", "_")
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    return duplicates


def archive_replay_command_policy_error(command: object) -> str | None:
    if not isinstance(command, str) or not command:
        return "archive command replay requires command field"
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return f"archive command replay command is not shell-parseable: {exc}"
    if release_gate_archive_replay_argv_allowed(argv):
        return None
    if len(argv) != 4 or argv[:3] != ["git", "diff", "--check"]:
        return (
            "archive command replay is limited to: git diff --check <full-sha>...<full-sha> "
            "or fixed release/pre-commit gate evidence commands"
        )
    if "..." not in argv[3]:
        return "archive command replay diff range must use <full-sha>...<full-sha>"
    left, right = argv[3].split("...", 1)
    if not FULL_COMMIT_RE.fullmatch(left) or not FULL_COMMIT_RE.fullmatch(right):
        return "archive command replay diff range must use full commit SHAs"
    return None


def release_gate_archive_replay_argv_allowed(argv: list[str]) -> bool:
    if release_gate_unittest_replay_argv_allowed(argv):
        return True
    if argv == ["sh", ".githooks/pre-commit"]:
        return True
    if len(argv) == 6 and argv[:4] == ["python3", "scripts/verify-release.py", "--list", "--base-ref"]:
        return FULL_COMMIT_RE.fullmatch(argv[4]) is not None and argv[5] == "--skip-clean-worktree"
    if len(argv) == 4 and argv[:3] == ["python3", "scripts/check-v1-archive-boundary.py", "--base-ref"]:
        return FULL_COMMIT_RE.fullmatch(argv[3]) is not None
    return False


def release_gate_unittest_replay_argv_allowed(argv: list[str]) -> bool:
    return argv in (
        [
            "python3",
            "-m",
            "unittest",
            "tests/test_v1_archive_boundary.py",
            "tests/test_verify_release.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "tests/test_active_packet_gate.py",
            "tests/test_verify_release.py",
        ],
        [
            "python3",
            "-m",
            "unittest",
            "tests/test_pre_commit_hook.py",
            "tests/test_active_packet_gate.py",
        ],
    )


def archive_replay_normalized_streams(command: object) -> set[str]:
    if not isinstance(command, str) or not command:
        return set()
    try:
        argv = shlex.split(command)
    except ValueError:
        return set()
    if (
        len(argv) == 4
        and argv[:3] == ["git", "diff", "--check"]
        and "..." in argv[3]
        and all(FULL_COMMIT_RE.fullmatch(part) for part in argv[3].split("...", 1))
    ):
        return {"stdout", "stderr"}
    if release_gate_unittest_replay_argv_allowed(argv):
        return {"stderr"}
    return set()


def archive_replay_requires_empty_pass_hashes(command: object) -> bool:
    return bool(archive_replay_normalized_streams(command))


def archive_replay_empty_pass_hash_error(section: dict[str, str]) -> str | None:
    if section.get("status") != "pass":
        return None
    if section.get("exit_code") != "0":
        return "pass archive command evidence must record exit_code 0"
    for stream in sorted(archive_replay_normalized_streams(section.get("command"))):
        field = f"{stream}_sha256"
        if section.get(field) != EMPTY_SHA256:
            return f"pass archive command evidence must record empty {stream} hash"
    return None


def command_archive_replay_metadata_error(section: dict[str, str], *, root: Path) -> str | None:
    legacy_fields = sorted(field for field in LEGACY_COMMAND_ARCHIVE_PROVENANCE_FIELDS if field in section)
    if legacy_fields:
        return f"archive command evidence legacy provenance fields are not allowed with replay metadata: {legacy_fields}"
    for field in COMMAND_ARCHIVE_REPLAY_METADATA_FIELDS:
        if not review_value_is_substantive_string(section.get(field)):
            return f"archive command evidence missing replay metadata field: {field}"
    for field in COMMAND_ARCHIVE_REPLAY_FIELDS:
        if not review_value_is_substantive_string(section.get(field)):
            return f"archive command evidence missing replay field: {field}"
    metadata = section["replay_metadata"]
    if metadata not in COMMAND_ARCHIVE_REPLAY_METADATA_VALUES:
        return f"replay_metadata must be one of {sorted(COMMAND_ARCHIVE_REPLAY_METADATA_VALUES)}"
    if section["replay_recorded_by"] != CHECKER_REF:
        return f"replay_recorded_by must be {CHECKER_REF}"
    if not date_like(section["replay_recorded_at"]):
        return "replay_recorded_at must be an ISO date"
    if section["replay_checker_ref"] != CHECKER_REF:
        return f"replay_checker_ref must be {CHECKER_REF}"
    if resolve_ref(root, section["replay_checker_ref"]) is None:
        return f"replay_checker_ref does not resolve: {section['replay_checker_ref']}"
    exit_code = section["exit_code"]
    if not exit_code.isdecimal():
        return "exit_code must be a non-negative integer"
    if section.get("status") == "pass" and exit_code != "0":
        return "pass archive command evidence must record exit_code 0"
    for field in ("stdout_sha256", "stderr_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", section[field]):
            return f"{field} must be a SHA-256 hex digest"
    return None


def run_archive_command(command: str, *, root: Path) -> tuple[subprocess.CompletedProcess[bytes] | None, str | None]:
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return None, f"command is not shell-parseable: {exc}"
    if not argv:
        return None, "command replay requires non-empty argv"
    argv, executable_error = trusted_replay_argv(argv)
    if executable_error:
        return None, executable_error
    with trusted_replay_tool_dir() as (tool_dir, tool_error):
        if tool_error:
            return None, tool_error
        try:
            return subprocess.run(
                argv,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=archive_replay_env(tool_dir=tool_dir),
                timeout=120,
            ), None
        except FileNotFoundError:
            return None, f"command executable not found: {argv[0]}"
        except OSError as exc:
            return None, f"command replay failed: {exc}"
        except subprocess.TimeoutExpired:
            return None, "command replay timed out after 120s"


def trusted_replay_argv(argv: list[str]) -> tuple[list[str], str | None]:
    executable = argv[0]
    if executable == "python3":
        return [sys.executable, *argv[1:]], None
    if executable not in {"git", "sh"}:
        return argv, None
    trusted, error = trusted_replay_executable(executable)
    if error:
        return argv, error
    return [trusted, *argv[1:]], None


def trusted_replay_executable(executable: str) -> tuple[str, str | None]:
    if executable == "python3":
        return str(Path(sys.executable).resolve()), None
    trusted = shutil.which(executable, path=TRUSTED_REPLAY_PATH)
    if trusted is None:
        return executable, f"trusted replay executable not found: {executable}"
    return trusted, None


@contextmanager
def trusted_replay_tool_dir():
    targets: dict[str, str] = {}
    for executable in ("python3", "git", "sh"):
        target, error = trusted_replay_executable(executable)
        if error:
            yield None, error
            return
        targets[executable] = target
    with tempfile.TemporaryDirectory(prefix="acceptance-replay-tools.") as tmpdir:
        tool_dir = Path(tmpdir)
        for name, target in targets.items():
            wrapper = tool_dir / name
            wrapper.write_text(f"#!/bin/sh\nexec {shlex.quote(target)} \"$@\"\n", encoding="utf-8")
            wrapper.chmod(0o755)
        yield tool_dir, None


def archive_replay_env(*, tool_dir: Path | None = None) -> dict[str, str]:
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
    path_entries = [str(tool_dir)] if tool_dir is not None else []
    path_entries.append(TRUSTED_REPLAY_PATH)
    env["PATH"] = os.pathsep.join(path_entries)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    return env


def archive_replay_stream_sha256(command: str, completed: subprocess.CompletedProcess[bytes], stream: str) -> str:
    data = completed.stdout if stream == "stdout" else completed.stderr
    if completed.returncode == 0 and stream in archive_replay_normalized_streams(command):
        data = b""
    return hashlib.sha256(data).hexdigest()


def command_archive_replay_error(section: dict[str, str], *, root: Path) -> str | None:
    command = section.get("command")
    if not isinstance(command, str) or not command:
        return "command replay requires command field"
    policy_error = archive_replay_command_policy_error(command)
    if policy_error:
        return policy_error
    completed, error = run_archive_command(command, root=root)
    if error:
        return error
    assert completed is not None
    expected_exit = int(section["exit_code"])
    if completed.returncode != expected_exit:
        return f"command replay exit mismatch: expected {expected_exit}, got {completed.returncode}"
    stdout_sha = archive_replay_stream_sha256(command, completed, "stdout")
    stderr_sha = archive_replay_stream_sha256(command, completed, "stderr")
    if section["stdout_sha256"] != stdout_sha:
        return "command replay stdout hash mismatch"
    if section["stderr_sha256"] != stderr_sha:
        return "command replay stderr hash mismatch"
    return None


def command_evidence_refreshable_packet_sha(
    lines: list[str],
    *,
    identity: dict[str, str],
    status: str,
) -> bool:
    relaxed_identity = {key: value for key, value in identity.items() if key != "packet_sha256"}
    matches: list[dict[str, str]] = []
    for start, end in command_evidence_section_bounds(lines):
        section = command_evidence_section_fields(lines, start, end)
        if not all(section.get(field) == value for field, value in relaxed_identity.items()):
            continue
        if command_evidence_section_duplicate_fields(lines, start, end):
            return False
        matches.append(section)
    return len(matches) == 1 and matches[0].get("status") == status


def command_evidence_record_error(
    text: str,
    *,
    root: Path,
    identity: dict[str, str],
    status: str,
    require_archive_replay_metadata: bool = False,
    require_safe_archive_replay_command: bool = False,
    require_empty_pass_replay_hashes: bool = False,
    replay_archive_command: bool = False,
    replay_root: Path | None = None,
    allow_stale_packet_sha: bool = False,
) -> str | None:
    lines = text.splitlines()
    matching_sections: list[dict[str, str]] = []
    duplicate_matches: list[set[str]] = []
    for start, end in command_evidence_section_bounds(lines):
        section = command_evidence_section_fields(lines, start, end)
        if not all(section.get(field) == value for field, value in identity.items()):
            continue
        duplicates = command_evidence_section_duplicate_fields(lines, start, end)
        if duplicates:
            duplicate_matches.append(duplicates)
            continue
        matching_sections.append(section)
    if duplicate_matches:
        duplicate_fields = sorted({field for fields in duplicate_matches for field in fields})
        return f"duplicate fields in matching # Command Evidence section: {duplicate_fields}"
    if not matching_sections:
        if (
            allow_stale_packet_sha
            and not require_archive_replay_metadata
            and not require_safe_archive_replay_command
            and not require_empty_pass_replay_hashes
            and not replay_archive_command
            and command_evidence_refreshable_packet_sha(lines, identity=identity, status=status)
        ):
            return None
        return "missing matching # Command Evidence section"
    if len(matching_sections) > 1:
        return "ambiguous # Command Evidence sections for packet/ref/command identity"
    recorded_status = matching_sections[0].get("status")
    if recorded_status != status:
        return f"# Command Evidence status mismatch: expected {status}, got {recorded_status}"
    if require_archive_replay_metadata:
        metadata_error = command_archive_replay_metadata_error(matching_sections[0], root=root)
        if metadata_error:
            return metadata_error
    if require_safe_archive_replay_command:
        policy_error = archive_replay_command_policy_error(matching_sections[0].get("command"))
        if policy_error:
            return policy_error
    if require_empty_pass_replay_hashes:
        digest_error = archive_replay_empty_pass_hash_error(matching_sections[0])
        if digest_error:
            return digest_error
    if replay_archive_command:
        return command_archive_replay_error(matching_sections[0], root=replay_root or root)
    return None


def artifact_command_evidence_error(
    root: Path,
    artifact_ref: str,
    command: str,
    status: str,
    *,
    packet_id: str,
    packet_ref: str,
    packet_sha256: str,
    require_archive_replay_metadata: bool = False,
    require_safe_archive_replay_command: bool = False,
    require_empty_pass_replay_hashes: bool = False,
    replay_archive_command: bool = False,
    replay_root: Path | None = None,
    allow_stale_packet_sha: bool = False,
) -> str | None:
    text = artifact_text(root, artifact_ref)
    if text is None:
        return "command evidence artifact could not be read"
    return command_evidence_record_error(
        text,
        root=root,
        identity={
            "packet_id": packet_id,
            "packet_ref": packet_ref,
            "packet_sha256": packet_sha256,
            "command": command,
        },
        status=status,
        require_archive_replay_metadata=require_archive_replay_metadata,
        require_safe_archive_replay_command=require_safe_archive_replay_command,
        require_empty_pass_replay_hashes=require_empty_pass_replay_hashes,
        replay_archive_command=replay_archive_command,
        replay_root=replay_root,
        allow_stale_packet_sha=allow_stale_packet_sha,
    )


def apply_text_updates_with_rollback(updates: dict[Path, str]) -> tuple[str | None, dict[Path, str | None]]:
    originals: dict[Path, str | None] = {}
    written: list[Path] = []
    try:
        for path, text in updates.items():
            originals[path] = path.read_text(encoding="utf-8") if path.exists() else None
            write_text_atomic(path, text)
            written.append(path)
    except OSError as exc:
        rollback_text_updates({path: originals[path] for path in written})
        return str(exc), originals
    return None, originals


def rollback_text_updates(originals: dict[Path, str | None]) -> None:
    for path, text in reversed(list(originals.items())):
        try:
            if text is None:
                if path.exists():
                    path.unlink()
            else:
                write_text_atomic(path, text)
        except OSError:
            pass


def init_archive_replay_snapshot(root: Path, snapshot: Path, commit_ref: str) -> list[str]:
    init = git(snapshot, ["init"])
    if init.returncode != 0:
        return [init.stderr.strip() or "failed to initialize archive replay snapshot"]
    source_objects = git_objects_dir(root)
    if source_objects is None:
        return ["archive replay snapshot could not locate source git object directory"]
    alternates = snapshot / ".git" / "objects" / "info" / "alternates"
    alternates.parent.mkdir(parents=True, exist_ok=True)
    alternates.write_text(f"{source_objects.resolve()}\n", encoding="utf-8")
    git(snapshot, ["config", "user.name", "Acceptance Replay"])
    git(snapshot, ["config", "user.email", "acceptance-replay@example.invalid"])
    update = git(snapshot, ["update-ref", "refs/heads/main", commit_ref])
    if update.returncode != 0:
        return [update.stderr.strip() or "failed to set archive replay snapshot HEAD"]
    symbolic = git(snapshot, ["symbolic-ref", "HEAD", "refs/heads/main"])
    if symbolic.returncode != 0:
        return [symbolic.stderr.strip() or "failed to set archive replay snapshot symbolic HEAD"]
    checkout = git(snapshot, ["checkout", "-f", "main"])
    if checkout.returncode != 0:
        return [checkout.stderr.strip() or "failed to checkout archive replay snapshot"]
    return []


@contextmanager
def archive_command_replay_root(root: Path, packet: dict):
    evidence = packet.get("result", {}).get("evidence", {}) if isinstance(packet.get("result"), dict) else {}
    accepted_head = evidence.get("accepted_head_commit") if isinstance(evidence, dict) else None
    if not isinstance(accepted_head, str) or not FULL_COMMIT_RE.fullmatch(accepted_head):
        yield root, []
        return
    with tempfile.TemporaryDirectory(prefix="acceptance-replay-snapshot.") as tmpdir:
        snapshot = Path(tmpdir)
        errors = init_archive_replay_snapshot(root, snapshot, accepted_head)
        yield snapshot, errors


def planned_archive_command_evidence_updates(
    packet: dict,
    *,
    root: Path,
    packet_ref: str,
    packet_sha256: str,
    replay_root: Path | None = None,
    allow_existing_replay_metadata: bool = False,
) -> tuple[dict[Path, str], list[str]]:
    evidence = packet.get("result", {}).get("evidence", {})
    command_results = evidence.get("command_results", []) if isinstance(evidence, dict) else []
    if not isinstance(command_results, list):
        return {}, []
    packet_id = packet.get("meta", {}).get("packet_id")
    errors: list[str] = []
    updates: dict[Path, str] = {}
    for index, item in enumerate(command_results):
        if not isinstance(item, dict):
            continue
        command = item.get("command")
        status = item.get("status")
        artifact_ref = item.get("artifact_ref")
        if not isinstance(command, str) or not command:
            continue
        if not isinstance(status, str) or not status:
            continue
        if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
            continue
        path = local_ref_path(root, artifact_ref)
        if path is None:
            errors.append(
                f"result.evidence.command_results[{index}].artifact_ref: {artifact_ref}: "
                "command evidence artifact could not be read"
            )
            continue
        updated_text, error = archive_command_artifact_updated_text(
            root,
            artifact_ref,
            identity={
                "packet_id": str(packet_id),
                "packet_ref": packet_ref,
                "packet_sha256": packet_sha256,
                "command": command,
            },
            status=status,
            current_text=updates.get(path),
            replay_root=replay_root,
            allow_existing_replay_metadata=allow_existing_replay_metadata,
        )
        if error:
            errors.append(f"result.evidence.command_results[{index}].artifact_ref: {artifact_ref}: {error}")
            continue
        assert updated_text is not None
        updates[path] = updated_text
    return updates, errors


def archive_command_artifact_updated_text(
    root: Path,
    artifact_ref: str,
    *,
    identity: dict[str, str],
    status: str,
    current_text: str | None = None,
    replay_root: Path | None = None,
    allow_existing_replay_metadata: bool = False,
) -> tuple[str | None, str | None]:
    path = local_ref_path(root, artifact_ref)
    if path is None:
        return None, "command evidence artifact could not be read"
    if current_text is None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None, "command evidence artifact could not be read"
    else:
        text = current_text
    lines = text.splitlines()
    matches: list[tuple[int, int, dict[str, str]]] = []
    stale_packet_sha_matches: list[tuple[int, int, dict[str, str]]] = []
    duplicate_matches: list[set[str]] = []
    relaxed_identity = {key: value for key, value in identity.items() if key != "packet_sha256"}
    for start, end in command_evidence_section_bounds(lines):
        section = command_evidence_section_fields(lines, start, end)
        strict_match = all(section.get(field) == value for field, value in identity.items())
        relaxed_match = all(section.get(field) == value for field, value in relaxed_identity.items())
        if not strict_match and not relaxed_match:
            continue
        duplicates = command_evidence_section_duplicate_fields(lines, start, end)
        if duplicates:
            duplicate_matches.append(duplicates)
            continue
        if strict_match:
            matches.append((start, end, section))
        else:
            stale_packet_sha_matches.append((start, end, section))
    if duplicate_matches:
        duplicate_fields = sorted({field for fields in duplicate_matches for field in fields})
        return None, f"duplicate fields in matching # Command Evidence section: {duplicate_fields}"
    if not matches:
        matches = stale_packet_sha_matches
    if not matches:
        return None, "missing matching # Command Evidence section"
    if len(matches) > 1:
        return None, "ambiguous # Command Evidence sections for packet/ref/command identity"
    start, end, section = matches[0]
    recorded_status = section.get("status")
    if recorded_status != status:
        return None, f"# Command Evidence status mismatch: expected {status}, got {recorded_status}"
    preexisting_legacy_fields = [
        field
        for field in LEGACY_COMMAND_ARCHIVE_PROVENANCE_FIELDS
        if field in section
    ]
    if preexisting_legacy_fields:
        return None, (
            "archive command evidence legacy provenance fields are not allowed; "
            f"remove preexisting fields: {sorted(preexisting_legacy_fields)}"
        )
    preexisting_replay_fields = [
        field
        for field in (
            *COMMAND_ARCHIVE_REPLAY_METADATA_FIELDS,
            *COMMAND_ARCHIVE_REPLAY_FIELDS,
        )
        if field in section
    ]
    if preexisting_replay_fields and not allow_existing_replay_metadata:
        return None, (
            "archive command evidence replay metadata must be materialized by write-pointer; "
            f"remove preexisting fields: {sorted(preexisting_replay_fields)}"
        )
    command = identity["command"]
    policy_error = archive_replay_command_policy_error(command)
    if policy_error:
        return None, policy_error
    completed, error = run_archive_command(command, root=replay_root or root)
    if error:
        return None, error
    assert completed is not None
    if status == "pass" and completed.returncode != 0:
        return None, f"command replay exit mismatch: expected 0 for pass status, got {completed.returncode}"
    replay_fields = [
        "replay_metadata: pointer-bound",
        f"replay_recorded_by: {CHECKER_REF}",
        f"replay_recorded_at: {today().isoformat()}",
        f"replay_checker_ref: {CHECKER_REF}",
        f"exit_code: {completed.returncode}",
        f"stdout_sha256: {archive_replay_stream_sha256(command, completed, 'stdout')}",
        f"stderr_sha256: {archive_replay_stream_sha256(command, completed, 'stderr')}",
    ]
    replay_field_names = set(COMMAND_ARCHIVE_REPLAY_METADATA_FIELDS) | set(COMMAND_ARCHIVE_REPLAY_FIELDS)
    section_lines: list[str] = []
    for line in lines[start:end]:
        match = COMMAND_EVIDENCE_FIELD_RE.match(line)
        field_name = match.group(1).casefold().replace("-", "_") if match else None
        if field_name in replay_field_names:
            continue
        if field_name == "packet_sha256":
            section_lines.append(f"packet_sha256: {identity['packet_sha256']}")
        else:
            section_lines.append(line)
    lines = [*lines[:start], *section_lines, *lines[end:]]
    end = start + len(section_lines)
    lines[end:end] = replay_fields
    return "\n".join(lines) + "\n", None


def multiple_required_closure_errors(
    required_targets: set[str],
    closures: list[tuple[str, list[str] | set[str]]],
    *,
    kind: str,
) -> list[str]:
    errors: list[str] = []
    for target in sorted(required_targets):
        labels = [
            label
            for label, targets in closures
            for value in targets
            if value == target
        ]
        if len(labels) > 1:
            errors.append(
                f"stable packet required {kind} has multiple closures: {target} via {', '.join(labels)}"
            )
    return errors


def ref_text(root: Path, ref: str) -> str | None:
    resolved = resolve_ref(root, ref)
    if resolved is None or ref.startswith("git:"):
        return None
    if "#" in resolved:
        resolved = resolved.split("#", 1)[0]
    try:
        return (root / resolved).read_text(encoding="utf-8")
    except OSError:
        return None


def ref_is_acceptance_packet(root: Path, ref: str) -> bool:
    text = ref_text(root, ref)
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        return False
    return isinstance(loaded, dict) and PACKET_KEY in loaded


def normalize_review_field(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dt.date):
        return value.isoformat()
    return canonical_vacuous_value(str(value))


def review_value_is_substantive(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return normalize_review_field(value) not in VACUOUS_REVIEW_VALUES
    if isinstance(value, dt.date):
        return True
    if isinstance(value, list):
        return any(review_value_is_substantive(item) for item in value)
    if isinstance(value, dict):
        return any(review_value_is_substantive(item) for item in value.values())
    return True


def review_value_is_substantive_string(value: object) -> bool:
    return isinstance(value, str) and review_value_is_substantive(value)


def sorted_string_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if isinstance(value, str) and value})


def string_list_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str)]


def canonical_json_bytes(value: object) -> bytes:
    def normalize(item: object) -> object:
        if isinstance(item, dt.datetime):
            return item.date().isoformat()
        if isinstance(item, dt.date):
            return item.isoformat()
        if isinstance(item, dict):
            return {str(key): normalize(item[key]) for key in sorted(item, key=lambda key: repr(key))}
        if isinstance(item, list):
            return [normalize(element) for element in item]
        return item

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def review_target_context(packet: dict, *, root: Path, packet_ref: str | None) -> dict:
    meta = packet["meta"]
    input_data = packet["input"]
    result = packet["result"]
    inference = result["inference"]
    evidence = result["evidence"]
    evaluator_boundary = evidence.get("evaluator_boundary", {})
    commands = evaluator_boundary.get("commands") if isinstance(evaluator_boundary, dict) else []
    return {
        "packet_id": meta.get("packet_id"),
        "schema_version": meta.get("schema_version"),
        "lifecycle": meta.get("lifecycle"),
        "mode": meta.get("mode"),
        "packet_ref": packet_ref or "",
        "input": {
            "intent": input_data.get("intent"),
            "actor": input_data.get("actor"),
            "source_refs": sorted_string_values(input_data.get("source_refs")),
        },
        "inference": {
            "change_class": inference.get("change_class"),
            "impact": inference.get("impact"),
            "changed_paths": sorted_string_values(inference.get("changed_paths")),
            "intended_scope": inference.get("intended_scope"),
            "actual_scope": inference.get("actual_scope"),
            "deviations": sorted_string_values(inference.get("deviations")),
            "isolation": inference.get("isolation"),
            "protected_boundary_changed": inference.get("protected_boundary_changed"),
            "required_evidence": sorted_string_values(inference.get("required_evidence")),
            "required_review": sorted(checker_required_review(packet, root=root)),
        },
        "evidence": {
            "baseline_ref": evidence.get("baseline_ref"),
            "comparison_ref": evidence.get("comparison_ref"),
            "evaluator_boundary_commands": sorted_string_values(commands),
            "source_refs": sorted_string_values(evidence.get("source_refs")),
        },
    }


def review_target_digest(packet: dict, *, root: Path, packet_ref: str | None) -> str:
    return hashlib.sha256(canonical_json_bytes(review_target_context(packet, root=root, packet_ref=packet_ref))).hexdigest()


def review_lineage_digest(lineage: list[dict]) -> str:
    return hashlib.sha256(canonical_json_bytes(lineage)).hexdigest()


def passing_required_critic_evidence(multi_review: dict, required_ids: set[str]) -> set[str]:
    evidence: set[str] = set()
    critics = multi_review.get("critics", [])
    if not isinstance(critics, list):
        return evidence
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        critic_id = critic.get("critic_id")
        if not isinstance(critic_id, str) or critic_id not in required_ids:
            continue
        if critic.get("required") is not True:
            continue
        if critic.get("verdict") != "pass" or critic.get("veto") is not False:
            continue
        score = critic.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 9:
            continue
        for item in critic.get("evidence", []):
            if isinstance(item, str):
                evidence.add(item)
    return evidence


def review_target_binding(packet: dict, *, root: Path, packet_ref: str | None) -> dict:
    result = packet["result"]
    evidence = result["evidence"]
    inference = result["inference"]
    return {
        "packet_id": packet["meta"].get("packet_id"),
        "packet_ref": packet_ref or "",
        "review_target_digest": review_target_digest(packet, root=root, packet_ref=packet_ref),
        "baseline_ref": evidence.get("baseline_ref"),
        "comparison_ref": evidence.get("comparison_ref"),
        "source_refs": sorted_string_values(packet["input"].get("source_refs")),
        "changed_paths": sorted_string_values(inference.get("changed_paths")),
        "required_review": sorted(checker_required_review(packet, root=root)),
    }


def multi_review_target_matches_binding(multi_review: dict, binding: dict) -> list[str]:
    errors: list[str] = []
    target = multi_review.get("target")
    if not isinstance(target, dict):
        return ["imported MultiReviewResult target must be a mapping"]
    source_refs = target.get("source_refs")
    if not isinstance(source_refs, list) or any(not isinstance(ref, str) for ref in source_refs):
        return ["imported MultiReviewResult target.source_refs must be a list of strings"]
    required_refs = [binding.get("packet_ref")]
    missing_refs = sorted(ref for ref in required_refs if isinstance(ref, str) and ref and ref not in source_refs)
    if missing_refs:
        errors.append(f"imported MultiReviewResult target.source_refs must include current packet ref: {missing_refs}")
    return errors


def markdown_field_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    field_re = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(.*?)\s*$")
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                sections.append(current)
            current = {}
            continue
        if current is None:
            continue
        match = field_re.match(line)
        if match:
            key = match.group(1).casefold().replace("-", "_")
            current[key] = normalize_review_field(match.group(2))
    if current:
        sections.append(current)
    return sections


def review_source_ref_records_review(root: Path, ref: str, review: dict, *, packet_id: str) -> bool:
    text = ref_text(root, ref)
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        loaded = None
    if isinstance(loaded, dict) and REVIEW_IMPORT_KEY in loaded:
        wrapper = loaded.get(REVIEW_IMPORT_KEY)
        if not isinstance(wrapper, dict):
            return False
        binding = wrapper.get("target_binding") if isinstance(wrapper.get("target_binding"), dict) else {}
        if normalize_review_field(binding.get("packet_id", "")) != normalize_review_field(packet_id):
            return False
        lineage = wrapper.get("review_lineage", [])
        if not isinstance(lineage, list):
            return False
        for record in lineage:
            if not isinstance(record, dict):
                continue
            if review.get("review_id") and record.get("review_id") != review.get("review_id"):
                continue
            expected = {
                "critic": normalize_review_field(review.get("critic", "")),
                "actor": normalize_review_field(review.get("actor", "")),
                "role": normalize_review_field(review.get("role", "")),
                "date": normalize_review_field(review.get("date", "")),
                "score": normalize_review_field(review.get("score", "")),
                "veto": normalize_review_field(review.get("veto", "")),
            }
            if any(not value for value in expected.values()):
                return False
            if all(normalize_review_field(record.get(field, "")) == value for field, value in expected.items()):
                return True
        return False
    expected = {
        "record_type": "governance-review",
        "packet_id": normalize_review_field(packet_id),
        "critic": normalize_review_field(review.get("critic", "")),
        "actor": normalize_review_field(review.get("actor", "")),
        "role": normalize_review_field(review.get("role", "")),
        "date": normalize_review_field(review.get("date", "")),
        "score": normalize_review_field(review.get("score", "")),
        "veto": normalize_review_field(review.get("veto", "")),
    }
    if any(not value for value in expected.values()):
        return False
    for field in ("why_not_10", "disposition"):
        if review.get(field):
            expected[field] = normalize_review_field(review[field])
    return any(all(section.get(field) == value for field, value in expected.items()) for section in markdown_field_sections(text))


def local_ref_path(root: Path, ref: str) -> Path | None:
    resolved = resolve_ref(root, ref)
    if resolved is None or ref.startswith("git:"):
        return None
    if "#" in resolved:
        resolved = resolved.split("#", 1)[0]
    path = (root / resolved).resolve()
    root_resolved = root.resolve()
    if path != root_resolved and root_resolved not in path.parents:
        return None
    return path if path.is_file() else None


def load_review_import_wrapper(root: Path, source_ref: str) -> tuple[dict | None, list[str]]:
    path = local_ref_path(root, source_ref)
    if path is None:
        return None, [f"review import source_ref does not resolve to a local file: {source_ref}"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"cannot read review import source_ref {source_ref}: {exc}"]
    try:
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        return None, [f"invalid review import artifact syntax: {source_ref}: {exc}"]
    if not isinstance(loaded, dict) or REVIEW_IMPORT_KEY not in loaded:
        return None, [f"review import artifact missing {REVIEW_IMPORT_KEY}: {source_ref}"]
    wrapper = loaded[REVIEW_IMPORT_KEY]
    if not isinstance(wrapper, dict):
        return None, [f"{REVIEW_IMPORT_KEY} must be a mapping: {source_ref}"]
    return wrapper, []


def load_probe_transcript(root: Path, source_ref: str) -> dict | None:
    path = local_ref_path(root, source_ref)
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        loaded = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return None
    if not isinstance(loaded, dict):
        return None
    transcript = loaded.get("ProbeTranscript")
    return transcript if isinstance(transcript, dict) else None


def derive_multi_review_result(
    root: Path,
    result: dict,
    *,
    result_ref: str | None = None,
    result_digest: str | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> tuple[str, list[str]]:
    script = ROOT / "scripts" / "check-multi-review-result.py"
    spec = importlib.util.spec_from_file_location("check_multi_review_result_for_acceptance", script)
    if spec is None or spec.loader is None:
        return "VETO", [f"cannot load multi-review validator: {script}"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_root = getattr(module, "ROOT", None)
    module.ROOT = root
    try:
        return module.derive_verdict(
            result,
            result_ref=result_ref,
            result_digest=result_digest,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
        )
    finally:
        if original_root is not None:
            module.ROOT = original_root


def review_lineage_ids(lineage: list[dict]) -> list[str]:
    return [
        record["review_id"]
        for record in lineage
        if isinstance(record, dict)
        and isinstance(record.get("review_id"), str)
        and record["review_id"]
    ]


def finding_ids(record: dict) -> set[str]:
    ids: set[str] = set()
    findings = record.get("blocking_findings", [])
    if not isinstance(findings, list):
        return ids
    for finding in findings:
        if isinstance(finding, dict) and review_value_is_substantive(finding.get("finding_id")):
            ids.add(str(finding["finding_id"]))
        elif isinstance(finding, str) and review_value_is_substantive(finding):
            ids.add(markdown_anchor(finding))
    return ids


def review_is_blocking(record: dict) -> bool:
    score = record.get("score")
    return record.get("veto") is True or not isinstance(score, (int, float)) or score < 9 or bool(record.get("blocking_findings"))


def review_is_open_passing(record: dict, closed_blocking_ids: set[str]) -> bool:
    review_id = record.get("review_id")
    if not isinstance(review_id, str) or not review_id:
        return False
    if review_id in closed_blocking_ids:
        return False
    score = record.get("score")
    return isinstance(score, (int, float)) and score >= 9 and record.get("veto") is False and not record.get("blocking_findings")


def normalize_for_mirror(value: object) -> object:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize_for_mirror(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_for_mirror(value[key]) for key in sorted(value, key=lambda item: repr(item))}
    return value


def validate_review_lineage_record(record: object, *, source: str, import_source_ref: str, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{source}: review lineage record must be a mapping"]
    errors.extend(schema_field_errors(record, REVIEW_LINEAGE_FIELDS, source=source, label="review lineage"))
    for field in ("review_id", "critic", "scope", "anti_scope", "actor", "role", "source_ref"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} is required")
    if record.get("source_ref") != import_source_ref:
        errors.append(f"{source}: source_ref must match review import source_ref: {import_source_ref}")
    if not date_like(record.get("date")):
        errors.append(f"{source}: date must be an ISO date")
    score = record.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 1 or score > 10:
        errors.append(f"{source}: score must be an integer from 1 to 10")
    if not isinstance(record.get("veto"), bool):
        errors.append(f"{source}: veto must be a boolean")
    for field in ("false_green_risk", "invariant_checked"):
        if not review_value_is_substantive_string(record.get(field)):
            errors.append(f"{source}: {field} must be substantive")
    evidence_items = record.get("evidence")
    if not isinstance(evidence_items, list) or not evidence_items:
        errors.append(f"{source}: evidence must be a non-empty substantive list")
    else:
        for index, item in enumerate(evidence_items):
            if not review_value_is_substantive_string(item):
                errors.append(f"{source}: evidence[{index}] must be a substantive string")
    source_refs = record.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append(f"{source}: source_refs must be a non-empty list")
    else:
        for index, ref in enumerate(source_refs):
            if not isinstance(ref, str) or not review_value_is_substantive(ref):
                errors.append(f"{source}: source_refs[{index}] must be a non-empty string")
            elif ref.startswith("trace:") and not trace_ref_has_anchor(ref):
                errors.append(f"{source}: source_refs[{index}] trace refs must include an anchor")
            elif ref.startswith("trace:") and canonical_trace_ref(ref) != ref:
                errors.append(f"{source}: source_refs[{index}] trace refs must be canonical: {ref}")
            elif resolve_ref(root, ref) is None:
                errors.append(f"{source}: source_refs[{index}] does not resolve: {ref}")
    if not isinstance(record.get("blocking_findings"), list):
        errors.append(f"{source}: blocking_findings must be a list")
    else:
        seen_finding_ids: set[str] = set()
        for index, finding in enumerate(record["blocking_findings"]):
            if not isinstance(finding, dict):
                errors.append(f"{source}: blocking_findings[{index}] must be a mapping with finding_id and summary")
                continue
            finding_id = finding.get("finding_id")
            if not review_value_is_substantive_string(finding_id):
                errors.append(f"{source}: blocking_findings[{index}].finding_id is required")
            elif finding_id in seen_finding_ids:
                errors.append(f"{source}: duplicate blocking finding_id: {finding_id}")
            else:
                seen_finding_ids.add(finding_id)
            if not review_value_is_substantive_string(finding.get("summary")):
                errors.append(f"{source}: blocking_findings[{index}].summary is required")
    if review_is_blocking(record) and not finding_ids(record):
        errors.append(f"{source}: blocking review requires blocking_findings with stable finding_id values")
    if score == 9:
        if not review_value_is_substantive_string(record.get("why_not_10")):
            errors.append(f"{source}: score 9 requires why_not_10")
        if not review_value_is_substantive_string(record.get("disposition")):
            errors.append(f"{source}: score 9 requires disposition")
    fixed = record.get("fixed_finding_ids")
    if not isinstance(fixed, list):
        errors.append(f"{source}: fixed_finding_ids must be a list")
    elif any(not isinstance(item, str) or not review_value_is_substantive(item) for item in fixed):
        errors.append(f"{source}: fixed_finding_ids must contain only substantive string ids")
    elif len(fixed) != len(set(fixed)):
        errors.append(f"{source}: fixed_finding_ids must not contain duplicates")
    rerun_of = record.get("rerun_of")
    if rerun_of is not None:
        if not review_value_is_substantive_string(rerun_of):
            errors.append(f"{source}: rerun_of must be a review_id string")
        if not fixed:
            errors.append(f"{source}: rerun requires fixed_finding_ids")
    elif fixed:
        errors.append(f"{source}: fixed_finding_ids require rerun_of")
    return errors


def validate_review_lineage_closure(lineage: list[dict], *, source: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    by_id: dict[str, dict] = {}
    index_by_id: dict[str, int] = {}
    for index, record in enumerate(lineage):
        review_id = record.get("review_id") if isinstance(record, dict) else None
        if not isinstance(review_id, str) or not review_id:
            continue
        if review_id in by_id:
            errors.append(f"{source}: duplicate review_id: {review_id}")
        by_id[review_id] = record
        index_by_id[review_id] = index

    closed_blocking_ids: set[str] = set()
    for index, record in enumerate(lineage):
        if not isinstance(record, dict) or not record.get("rerun_of"):
            continue
        rerun_id = record.get("review_id")
        target_id = record.get("rerun_of")
        if not isinstance(rerun_id, str) or not isinstance(target_id, str):
            continue
        target = by_id.get(target_id)
        if target is None:
            errors.append(f"{source}: rerun {rerun_id} references missing review_id: {target_id}")
            continue
        if index_by_id.get(target_id, len(lineage)) >= index:
            errors.append(f"{source}: rerun {rerun_id} must appear after rerun_of review: {target_id}")
            continue
        if not review_is_blocking(target):
            errors.append(f"{source}: rerun {rerun_id} references nonblocking review: {target_id}")
            continue
        if record.get("critic") != target.get("critic"):
            errors.append(f"{source}: rerun {rerun_id} must use same critic as {target_id}")
        if not review_is_open_passing(record, set()):
            errors.append(f"{source}: rerun {rerun_id} must be score >= 9, veto false, and nonblocking")
            continue
        target_findings = finding_ids(target)
        fixed_values = record.get("fixed_finding_ids", [])
        if not isinstance(fixed_values, list) or any(not isinstance(item, str) for item in fixed_values):
            continue
        fixed = set(fixed_values)
        if not target_findings:
            errors.append(f"{source}: rerun target {target_id} has no stable finding ids")
            continue
        if fixed != target_findings:
            errors.append(f"{source}: rerun {rerun_id} fixed_finding_ids must exactly cover {target_id}: {sorted(target_findings)}")
            continue
        rerun_date = parsed_date(record.get("date"))
        target_date = parsed_date(target.get("date"))
        if rerun_date is not None and target_date is not None and rerun_date < target_date:
            errors.append(f"{source}: rerun {rerun_id} date must not precede rerun_of review date: {target_id}")
            continue
        if target_id in closed_blocking_ids:
            errors.append(f"{source}: multiple reruns close review_id: {target_id}")
            continue
        closed_blocking_ids.add(target_id)

    for record in lineage:
        if not isinstance(record, dict):
            continue
        review_id = record.get("review_id")
        if not isinstance(review_id, str) or not review_id:
            continue
        if review_is_blocking(record) and review_id not in closed_blocking_ids:
            errors.append(f"{source}: unclosed blocking review: {review_id}")

    open_passing = [
        record["critic"]
        for record in lineage
        if isinstance(record, dict)
        and isinstance(record.get("critic"), str)
        and review_is_open_passing(record, closed_blocking_ids)
    ]
    return open_passing, errors


def validate_review_imports(
    packet: dict,
    *,
    root: Path,
    packet_ref: str | None,
    packet_sha256: str | None,
    ref_index: dict[tuple[str, str], list[dict]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    evidence = packet["result"]["evidence"]
    packet_reviews_raw = packet["result"]["judgment"].get("reviews", [])
    packet_reviews = packet_reviews_raw if isinstance(packet_reviews_raw, list) else []
    imports = evidence.get("review_imports", [])
    if not isinstance(imports, list):
        return [], ["result.evidence.review_imports must be a list"]
    if packet_reviews and not imports:
        return [], ["stable packet reviews require result.evidence.review_imports"]

    expected_binding = review_target_binding(packet, root=root, packet_ref=packet_ref)
    imported_source_refs: set[str] = set()
    imported_lineage_by_id: dict[str, dict] = {}
    open_passing_reviews: list[str] = []
    for import_index, import_record in enumerate(imports):
        source = f"result.evidence.review_imports[{import_index}]"
        if not isinstance(import_record, dict):
            errors.append(f"{source}: review import must be a mapping")
            continue
        errors.extend(schema_field_errors(import_record, REVIEW_IMPORT_RECORD_FIELDS, source=source, label="review import"))
        source_ref = import_record.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref:
            errors.append(f"{source}: source_ref is required")
            continue
        imported_source_refs.add(source_ref)
        if import_record.get("format") != REVIEW_IMPORT_SCHEMA_VERSION:
            errors.append(f"{source}: format must be {REVIEW_IMPORT_SCHEMA_VERSION}")
        if import_record.get("status") != "imported":
            errors.append(f"{source}: status must be imported")
        if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref, origin="generated"):
            errors.append(f"{source}: source_ref lacks resolved review-provenance relation with generated origin: {source_ref}")
        if ref_is_acceptance_packet(root, source_ref):
            errors.append(f"{source}: review import source_ref cannot be an acceptance packet: {source_ref}")
        path = local_ref_path(root, source_ref)
        if path is None:
            errors.append(f"{source}: source_ref does not resolve to a local file: {source_ref}")
            continue
        digest = file_sha256(path)
        if import_record.get("source_digest") != digest:
            errors.append(f"{source}: source_digest does not match current artifact bytes: {source_ref}")

        binding = import_record.get("target_binding")
        if not isinstance(binding, dict) or set(binding) != TARGET_BINDING_FIELDS:
            errors.append(f"{source}: target_binding fields must be exactly {sorted(TARGET_BINDING_FIELDS)}")
        elif normalize_for_mirror(binding) != normalize_for_mirror(expected_binding):
            errors.append(f"{source}: target_binding does not match current packet review target")

        wrapper, wrapper_errors = load_review_import_wrapper(root, source_ref)
        errors.extend(f"{source}: {item}" for item in wrapper_errors)
        if wrapper is None:
            continue
        errors.extend(schema_field_errors(wrapper, REVIEW_IMPORT_FIELDS, source=source, label="wrapper"))
        if wrapper.get("schema_version") != REVIEW_IMPORT_SCHEMA_VERSION:
            errors.append(f"{source}: wrapper schema_version must be {REVIEW_IMPORT_SCHEMA_VERSION}")
        wrapper_binding = wrapper.get("target_binding")
        if not isinstance(wrapper_binding, dict) or set(wrapper_binding) != TARGET_BINDING_FIELDS:
            errors.append(f"{source}: wrapper target_binding fields must be exactly {sorted(TARGET_BINDING_FIELDS)}")
        elif normalize_for_mirror(wrapper_binding) != normalize_for_mirror(expected_binding):
            errors.append(f"{source}: wrapper target_binding does not match current packet review target")
        if isinstance(binding, dict) and isinstance(wrapper_binding, dict) and normalize_for_mirror(binding) != normalize_for_mirror(wrapper_binding):
            errors.append(f"{source}: packet import target_binding must match wrapper target_binding")

        multi_review = wrapper.get("MultiReviewResult")
        if not isinstance(multi_review, dict):
            errors.append(f"{source}: wrapper MultiReviewResult must be a mapping")
        else:
            expected_packet_ref = wrapper_binding.get("packet_ref") if isinstance(wrapper_binding, dict) else packet_ref
            target_binding = wrapper_binding if isinstance(wrapper_binding, dict) else expected_binding
            for item in multi_review_target_matches_binding(multi_review, target_binding):
                errors.append(f"{source}: {item}")
            derived, derived_errors = derive_multi_review_result(
                root,
                multi_review,
                result_ref=source_ref,
                result_digest=digest,
                packet_ref=expected_packet_ref,
                packet_sha256=packet_sha256,
            )
            if derived != "PASS":
                errors.append(f"{source}: imported MultiReviewResult must freshly derive governance PASS: {derived}")
            for item in derived_errors:
                errors.append(f"{source}: imported MultiReviewResult error: {item}")

        lineage = wrapper.get("review_lineage")
        if not isinstance(lineage, list) or not lineage:
            errors.append(f"{source}: review_lineage must be a non-empty list")
            continue
        for index, record in enumerate(lineage):
            errors.extend(
                validate_review_lineage_record(
                    record,
                    source=f"{source}.review_lineage[{index}]",
                    import_source_ref=source_ref,
                    root=root,
                )
            )
        ids = review_lineage_ids(lineage)
        if len(ids) != len(set(ids)):
            errors.append(f"{source}: review_lineage contains duplicate review_id values")
        review_ids = import_record.get("review_ids")
        if not isinstance(review_ids, list):
            errors.append(f"{source}: review_ids must match imported review_lineage ids")
        elif any(not isinstance(review_id, str) for review_id in review_ids):
            errors.append(f"{source}: review_ids must contain only strings")
        elif sorted(review_ids) != sorted(ids):
            errors.append(f"{source}: review_ids must match imported review_lineage ids")
        required_critics = multi_review.get("required_critics") if isinstance(multi_review, dict) else None
        required_ids = {
            critic_id
            for critic_id in required_critics
            if isinstance(critic_id, str)
        } if isinstance(required_critics, list) else set()
        lineage_digest_marker = f"review_lineage_sha256:{review_lineage_digest(lineage)}"
        if not isinstance(multi_review, dict) or lineage_digest_marker not in passing_required_critic_evidence(multi_review, required_ids):
            errors.append(
                f"{source}: review_lineage digest must be represented by a passing required MultiReviewResult critic: {lineage_digest_marker}"
            )
        for record in lineage:
            if isinstance(record, dict) and isinstance(record.get("review_id"), str):
                review_id = record["review_id"]
                if review_id in imported_lineage_by_id:
                    errors.append(f"{source}: duplicate imported review_id across imports: {review_id}")
                imported_lineage_by_id[review_id] = record
        passing, closure_errors = validate_review_lineage_closure(lineage, source=source)
        open_passing_reviews.extend(passing)
        errors.extend(closure_errors)

    packet_reviews_by_id: dict[str, dict] = {}
    for index, review in enumerate(packet_reviews):
        source = f"result.judgment.reviews[{index}]"
        if not isinstance(review, dict):
            errors.append(f"{source}: review record must be a mapping")
            continue
        review_id = review.get("review_id")
        if not isinstance(review_id, str) or not review_id:
            errors.append(f"{source}: review_id is required")
            continue
        if review_id in packet_reviews_by_id:
            errors.append(f"{source}: duplicate review_id: {review_id}")
        packet_reviews_by_id[review_id] = review
        source_ref = review.get("source_ref")
        if not isinstance(source_ref, str) or source_ref not in imported_source_refs:
            errors.append(f"{source}: source_ref must point to an imported structured review artifact")
        imported = imported_lineage_by_id.get(review_id)
        if imported is None:
            errors.append(f"{source}: imported source_ref review is missing from review_lineage: {review_id}")
            continue
        for field in REVIEW_MIRROR_FIELDS:
            if normalize_for_mirror(review.get(field)) != normalize_for_mirror(imported.get(field)):
                errors.append(f"{source}: field does not mirror imported review_lineage[{review_id}]: {field}")

    missing_from_packet = sorted(set(imported_lineage_by_id) - set(packet_reviews_by_id))
    if missing_from_packet:
        errors.append(f"result.judgment.reviews missing imported review_lineage records: {missing_from_packet}")

    return open_passing_reviews, errors


def load_review_import_wrapper_text(text: str, *, source: str) -> tuple[dict | None, list[str]]:
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [f"invalid review import artifact syntax: {source}: {exc}"]
    if not isinstance(loaded, dict) or REVIEW_IMPORT_KEY not in loaded:
        return None, [f"review import artifact missing {REVIEW_IMPORT_KEY}: {source}"]
    wrapper = loaded[REVIEW_IMPORT_KEY]
    if not isinstance(wrapper, dict):
        return None, [f"{REVIEW_IMPORT_KEY} must be a mapping: {source}"]
    return wrapper, []


def review_import_source_from_arg(root: Path, value: str) -> tuple[dict | None, str | None, Path | None, list[str]]:
    if value == "-":
        wrapper, errors = load_review_import_wrapper_text(sys.stdin.read(), source="stdin")
        return wrapper, None, None, errors
    if value.startswith("file:"):
        source_ref = value
    else:
        path = Path(value)
        source_ref = f"file:{repo_relative_path(root, root / path if not path.is_absolute() else path)}"
    if "#" in source_ref:
        raise PacketError("import-review source_ref must name a whole local file, not an anchored ref")
    source_path = local_ref_path(root, source_ref)
    if source_path is None:
        raise PacketError(f"review import source_ref does not resolve to a local file: {source_ref}")
    if repo_path_has_symlink(root, source_path):
        raise PacketError(f"review import artifact must be a regular file, not a symlink: {source_ref}")
    wrapper, errors = load_review_import_wrapper(root, source_ref)
    return wrapper, source_ref, source_path, errors


def review_import_output_ref_from_arg(
    root: Path,
    packet: dict,
    *,
    source_ref: str | None,
    source_path: Path | None,
    output: str | None,
    overwrite: bool,
) -> tuple[str, Path]:
    if output:
        output_value = output.removeprefix("file:")
        output_path = Path(output_value)
        output_path = root / output_path if not output_path.is_absolute() else output_path
    elif source_ref and source_ref.startswith(f"file:{ARCHIVE_ARTIFACT_PREFIX}") and source_path is not None:
        output_path = source_path
    else:
        packet_id = packet.get("meta", {}).get("packet_id", "packet")
        output_path = root / ARCHIVE_ARTIFACT_PREFIX / f"{safe_artifact_stem(packet_id)}-review-import.yml"
    output_ref = f"file:{repo_relative_path(root, output_path)}"
    output_rel = output_ref.removeprefix("file:")
    if not output_rel.startswith(ARCHIVE_ARTIFACT_PREFIX):
        raise PacketError("import-review output must be under archive/v2/artifacts/")
    if Path(output_rel).suffix not in {".yml", ".yaml"}:
        raise PacketError("import-review output must be a .yml or .yaml file")
    if repo_path_has_symlink(root, output_path):
        raise PacketError(f"review import output must be a regular file, not a symlink: {output_ref}")
    same_source = source_path is not None and output_path.resolve() == source_path.resolve()
    if output_path.exists() and not overwrite and not same_source:
        raise PacketError(f"{output_path}: already exists; use --overwrite to replace")
    return output_ref, output_path


def review_template_scratch_output_ref_from_arg(root: Path, output: str) -> tuple[str, Path]:
    output_value = output.removeprefix("file:")
    output_path = Path(output_value)
    output_path = root / output_path if not output_path.is_absolute() else output_path
    if output_path.suffix not in {".yml", ".yaml"}:
        raise PacketError("review-template scratch output must be a .yml or .yaml file")
    if repo_path_has_symlink(root, output_path):
        raise PacketError(f"review-template scratch output must be a regular file, not a symlink: {output_path}")
    try:
        output_ref = f"file:{repo_relative_path(root, output_path)}"
    except PacketError:
        output_ref = f"file:{output_path.resolve().as_posix()}"
    return output_ref, output_path


def review_template_probe_transcript(
    *,
    command: str,
    source_ref: str,
    packet_ref: str,
    source_refs: list[str],
) -> dict:
    empty_sha = hashlib.sha256(b"").hexdigest()
    return {
        "schema_version": "probe-transcript/v1",
        "probe_command": command,
        "probe_exit_code": 1,
        "result_ref": source_ref,
        "result_digest": "0" * 64,
        "packet_ref": packet_ref,
        "packet_sha256": "0" * 64,
        "source_refs": source_refs,
        "cwd": ".",
        "generated_by": "governance review-template",
        "date": today().isoformat(),
        "stdout": "",
        "stderr": "",
        "stdout_sha256": empty_sha,
        "stderr_sha256": empty_sha,
    }


def review_template_wrapper(
    packet: dict,
    *,
    root: Path,
    packet_ref: str,
    source_ref: str,
) -> tuple[dict, dict[Path, str]]:
    packet_id_value = safe_artifact_stem(packet.get("meta", {}).get("packet_id", "packet"))
    binding = review_target_binding(packet, root=root, packet_ref=packet_ref)
    required_reviews = list(binding.get("required_review", []))
    target_source_refs = [packet_ref]
    source_refs = [packet_ref]
    critics: list[dict] = []
    lineage: list[dict] = []
    probe_updates: dict[Path, str] = {}
    source_rel = source_ref.removeprefix("file:")
    probe_dir = posixpath.dirname(source_rel) or ARCHIVE_ARTIFACT_PREFIX.rstrip("/")
    for review_name in required_reviews:
        critic_id = markdown_anchor(review_name) or "review"
        probe_ref = f"file:{posixpath.join(probe_dir, f'{packet_id_value}-{critic_id}-probe.yml')}"
        probe_path = root / probe_ref.removeprefix("file:")
        probe_command = f"TODO replace with replayable probe command for {review_name}"
        blocking_findings = [
            {
                "finding_id": "template-incomplete",
                "summary": "Review template must be completed before import.",
            }
        ]
        critics.append(
            {
                "critic_id": critic_id,
                "name": f"{review_name.title()} Critic",
                "critic_type": "other",
                "persona": f"TODO reviewer persona for {review_name}.",
                "scope": f"TODO review scope for {review_name}.",
                "anti_scope": "TODO review anti-scope.",
                "attack_surface": "TODO false-green surface this review checks.",
                "primary_failure_mode": "TODO primary failure mode.",
                "frame_challenge": False,
                "required": True,
                "actor": "TODO-reviewer",
                "date": today().isoformat(),
                "score": 1,
                "verdict": "veto",
                "veto": True,
                "blocking_findings": copy.deepcopy(blocking_findings),
                "false_green_risk": "TODO substantive false-green risk.",
                "invariant_checked": "TODO substantive invariant checked.",
                "validation_layer": "structured-validator",
                "probe_run": False,
                "probe_command": probe_command,
                "probe_exit_code": 1,
                "probe_result": "TODO probe result.",
                "probe_interpretation": "TODO probe interpretation.",
                "probe_evidence_refs": [probe_ref],
                "reason_no_probe": "TODO run and record probe before import.",
                "evidence": ["TODO replace with substantive review evidence."],
                "source_refs": source_refs,
                "why_not_10": "Template is incomplete and must not be imported as acceptance evidence.",
                "residual_risk_disposition": "Complete the review, rerun probes, and clear blocking findings before import.",
            }
        )
        lineage.append(
            {
                "review_id": f"review-{packet_id_value}-{critic_id}",
                "critic": review_name,
                "scope": f"TODO review scope for {review_name}.",
                "anti_scope": "TODO review anti-scope.",
                "score": 1,
                "veto": True,
                "actor": "TODO-reviewer",
                "role": "reviewer",
                "date": today().isoformat(),
                "source_ref": source_ref,
                "false_green_risk": "TODO substantive false-green risk.",
                "invariant_checked": "TODO substantive invariant checked.",
                "evidence": ["TODO replace with substantive review evidence."],
                "source_refs": source_refs,
                "blocking_findings": copy.deepcopy(blocking_findings),
                "why_not_10": "Template is incomplete and must not be imported as acceptance evidence.",
                "disposition": "Complete the review, rerun probes, and clear blocking findings before import.",
                "rerun_of": None,
                "fixed_finding_ids": [],
            }
        )
        probe_updates[probe_path] = probe_transcript_document_text(
            review_template_probe_transcript(
                command=probe_command,
                source_ref=source_ref,
                packet_ref=packet_ref,
                source_refs=source_refs,
            )
        )
    wrapper = {
        "schema_version": REVIEW_IMPORT_SCHEMA_VERSION,
        "target_binding": binding,
        "MultiReviewResult": {
            "schema_version": "multi-review-result/v1",
            "review_id": f"mr-{packet_id_value}-template",
            "lifecycle": "draft",
            "review_mode": "governance",
            "independence": "independent",
            "target": {
                "summary": f"TODO review summary for {packet_id_value}.",
                "source_refs": target_source_refs,
            },
            "required_critics": [critic["critic_id"] for critic in critics],
            "critics": critics,
            "reported_final_verdict": "INCOMPLETE",
            "derived_verdict": None,
            "derivation_errors": [],
        },
        "review_lineage": lineage,
    }
    return wrapper, probe_updates


def refresh_review_lineage_marker(wrapper: dict) -> None:
    lineage = wrapper.get("review_lineage")
    multi_review = wrapper.get("MultiReviewResult")
    if not isinstance(lineage, list) or not isinstance(multi_review, dict):
        return
    marker = f"review_lineage_sha256:{review_lineage_digest(lineage)}"
    critics = multi_review.get("critics", [])
    if not isinstance(critics, list):
        return
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        evidence = critic.get("evidence")
        if isinstance(evidence, list):
            critic["evidence"] = [
                item
                for item in evidence
                if not (isinstance(item, str) and item.startswith("review_lineage_sha256:"))
            ]
    required_ids = set(string_list_values(multi_review.get("required_critics", [])))
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        score = critic.get("score")
        if (
            critic.get("critic_id") in required_ids
            and critic.get("required") is True
            and critic.get("verdict") == "pass"
            and critic.get("veto") is False
            and isinstance(score, int)
            and not isinstance(score, bool)
            and score >= 9
        ):
            evidence = critic.get("evidence")
            if not isinstance(evidence, list):
                evidence = []
                critic["evidence"] = evidence
            evidence.append(marker)
            return


def review_import_target_errors(wrapper: dict, *, target_binding: dict, packet_ref: str) -> list[str]:
    errors: list[str] = []
    wrapper_binding = wrapper.get("target_binding")
    if not isinstance(wrapper_binding, dict) or set(wrapper_binding) != TARGET_BINDING_FIELDS:
        errors.append(f"wrapper target_binding fields must be exactly {sorted(TARGET_BINDING_FIELDS)}")
    elif normalize_for_mirror(wrapper_binding) != normalize_for_mirror(target_binding):
        errors.append("wrapper target_binding does not match current packet review target")
    multi_review = wrapper.get("MultiReviewResult")
    if not isinstance(multi_review, dict):
        errors.append("wrapper MultiReviewResult must be a mapping")
    else:
        target_errors = multi_review_target_matches_binding(
            multi_review,
            wrapper_binding if isinstance(wrapper_binding, dict) else target_binding,
        )
        errors.extend(target_errors)
        target = multi_review.get("target")
        source_refs = target.get("source_refs") if isinstance(target, dict) else []
        if isinstance(source_refs, list) and packet_ref not in source_refs:
            errors.append(f"imported MultiReviewResult target.source_refs must include current packet ref: {packet_ref}")
    return errors


def materialized_review_import_wrapper(wrapper: dict, *, source_ref: str) -> dict:
    updated = copy.deepcopy(wrapper)
    lineage = updated.get("review_lineage")
    if isinstance(lineage, list):
        for record in lineage:
            if isinstance(record, dict):
                record["source_ref"] = source_ref
    refresh_review_lineage_marker(updated)
    return updated


def add_multi_review_evidence_markers(wrapper: dict, markers: list[str]) -> None:
    if not markers:
        return
    multi_review = wrapper.get("MultiReviewResult")
    if not isinstance(multi_review, dict):
        return
    critics = multi_review.get("critics", [])
    if not isinstance(critics, list):
        return
    required_ids = set(string_list_values(multi_review.get("required_critics", [])))
    selected: dict | None = None
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        score = critic.get("score")
        if (
            critic.get("critic_id") in required_ids
            and critic.get("required") is True
            and critic.get("verdict") == "pass"
            and critic.get("veto") is False
            and isinstance(score, int)
            and not isinstance(score, bool)
            and score >= 9
        ):
            selected = critic
            break
    if selected is None:
        return
    evidence = selected.get("evidence")
    if not isinstance(evidence, list):
        evidence = []
        selected["evidence"] = evidence
    existing = {item for item in evidence if isinstance(item, str)}
    for marker in markers:
        if marker not in existing:
            evidence.append(marker)


def bind_skipped_provenance_to_review_import(packet: dict, wrapper: dict, *, source_ref: str) -> None:
    result = packet.get("result", {}) if isinstance(packet.get("result"), dict) else {}
    evidence = result.get("evidence", {}) if isinstance(result.get("evidence"), dict) else {}
    skipped = evidence.get("skipped", [])
    if not isinstance(skipped, list):
        return
    markers: list[str] = []
    changed = False
    for record in skipped:
        if not isinstance(record, dict):
            continue
        record["source_ref"] = source_ref
        markers.append(f"provenance_record_sha256:{provenance_record_digest(record)}")
        changed = True
    if not changed:
        return
    resolved_refs = evidence.get("resolved_refs", [])
    if not isinstance(resolved_refs, list):
        resolved_refs = []
    evidence["resolved_refs"] = [
        item
        for item in resolved_refs
        if not (
            isinstance(item, dict)
            and item.get("relation") == "waiver-provenance"
            and item.get("ref") == source_ref
        )
    ]
    evidence["resolved_refs"].append(
        {
            "origin": "generated",
            "relation": "waiver-provenance",
            "ref": source_ref,
            "status": "resolved",
            "target": source_ref.removeprefix("file:"),
        }
    )
    add_multi_review_evidence_markers(wrapper, markers)


def promote_imported_review_decision(
    packet: dict,
    wrapper: dict,
    *,
    source_ref: str,
    root: Path,
    packet_ref: str | None,
) -> None:
    if pointer_packet_ref_error(packet_ref) is not None:
        return
    if packet.get("meta", {}).get("lifecycle") != "finalized" or packet.get("meta", {}).get("mode") != "base-ref":
        return
    result = packet.get("result", {}) if isinstance(packet.get("result"), dict) else {}
    inference = result.get("inference", {}) if isinstance(result.get("inference"), dict) else {}
    decision = result.get("decision", {}) if isinstance(result.get("decision"), dict) else {}
    protected_review_required = (
        inference.get("protected_boundary_changed") is True
        or inference.get("change_class") == "harness-affecting"
        or inference.get("impact") == "high"
        or any(requires_review_for_path(path) for path in string_list_values(inference.get("changed_paths", [])))
    )
    if not protected_review_required:
        return
    inference["required_review"] = sorted(checker_required_review(packet, root=root))
    bind_skipped_provenance_to_review_import(packet, wrapper, source_ref=source_ref)
    decision["accepted"] = True
    decision["stable_handoff_eligible"] = True
    decision["reason"] = "Required durable evidence and imported multi-review passed."
    decision["next_action"] = "Publish active archive pointer."


def review_import_document_text(wrapper: dict) -> str:
    return yaml.safe_dump({REVIEW_IMPORT_KEY: wrapper}, sort_keys=False, allow_unicode=False)


def probe_transcript_document_text(transcript: dict) -> str:
    return yaml.safe_dump({PROBE_TRANSCRIPT_KEY: transcript}, sort_keys=False, allow_unicode=False)


def local_file_ref_for_path(root: Path, path: Path) -> str:
    try:
        return f"file:{repo_relative_path(root, path)}"
    except PacketError:
        return f"file:{path.resolve().as_posix()}"


def review_import_probe_transcript_updates(
    root: Path,
    wrapper: dict,
    *,
    source_ref: str,
    source_digest: str,
    packet_ref: str,
    packet_sha256: str,
) -> tuple[dict[Path, str], list[str]]:
    updates: dict[Path, str] = {}
    errors: list[str] = []
    multi_review = wrapper.get("MultiReviewResult")
    critics = multi_review.get("critics", []) if isinstance(multi_review, dict) else []
    if not isinstance(critics, list):
        return updates, errors
    for critic_index, critic in enumerate(critics):
        if not isinstance(critic, dict):
            continue
        refs = critic.get("probe_evidence_refs", [])
        if not isinstance(refs, list):
            continue
        for ref_index, ref in enumerate(refs):
            source = f"MultiReviewResult.critics[{critic_index}].probe_evidence_refs[{ref_index}]"
            if not isinstance(ref, str) or not ref.startswith("file:"):
                continue
            path = local_ref_path(root, ref)
            if path is None:
                errors.append(f"{source}: probe transcript ref does not resolve to a local file: {ref}")
                continue
            if repo_path_has_symlink(root, path):
                errors.append(f"{source}: probe transcript must be a regular file, not a symlink: {ref}")
                continue
            transcript = load_probe_transcript(root, ref)
            if transcript is None:
                errors.append(f"{source}: probe transcript must be a structured {PROBE_TRANSCRIPT_KEY} artifact: {ref}")
                continue
            updated = copy.deepcopy(transcript)
            updated["result_ref"] = source_ref
            updated["result_digest"] = source_digest
            updated["packet_ref"] = packet_ref
            updated["packet_sha256"] = packet_sha256
            updates[path] = probe_transcript_document_text(updated)
    return updates, errors


def review_import_record(
    *,
    source_ref: str,
    source_digest: str,
    wrapper: dict,
    target_binding: dict,
) -> dict:
    lineage = wrapper.get("review_lineage", [])
    return {
        "source_ref": source_ref,
        "format": REVIEW_IMPORT_SCHEMA_VERSION,
        "source_digest": source_digest,
        "status": "imported",
        "review_ids": review_lineage_ids(lineage if isinstance(lineage, list) else []),
        "target_binding": copy.deepcopy(target_binding),
    }


def apply_review_import_to_packet(
    packet: dict,
    *,
    source_ref: str,
    source_digest: str,
    wrapper: dict,
    target_binding: dict,
) -> dict:
    updated = copy.deepcopy(packet)
    result = updated["result"]
    evidence = result["evidence"]
    judgment = result["judgment"]
    lineage = wrapper.get("review_lineage")
    imported_reviews = copy.deepcopy(lineage if isinstance(lineage, list) else [])
    imported_ids = {
        review["review_id"]
        for review in imported_reviews
        if isinstance(review, dict) and isinstance(review.get("review_id"), str)
    }

    existing_imports = evidence.get("review_imports", [])
    if not isinstance(existing_imports, list):
        existing_imports = []
    evidence["review_imports"] = [
        item
        for item in existing_imports
        if not (
            isinstance(item, dict)
            and (
                item.get("source_ref") == source_ref
                or bool(imported_ids & set(string_list_values(item.get("review_ids", []))))
            )
        )
    ]
    evidence["review_imports"].append(
        review_import_record(
            source_ref=source_ref,
            source_digest=source_digest,
            wrapper=wrapper,
            target_binding=target_binding,
        )
    )

    resolved_refs = evidence.get("resolved_refs", [])
    if not isinstance(resolved_refs, list):
        resolved_refs = []
    evidence["resolved_refs"] = [
        item
        for item in resolved_refs
        if not (
            isinstance(item, dict)
            and item.get("relation") == "review-provenance"
            and item.get("ref") == source_ref
        )
    ]
    evidence["resolved_refs"].append(
        {
            "origin": "generated",
            "relation": "review-provenance",
            "ref": source_ref,
            "status": "resolved",
            "target": source_ref.removeprefix("file:"),
        }
    )

    existing_reviews = judgment.get("reviews", [])
    if not isinstance(existing_reviews, list):
        existing_reviews = []
    judgment["reviews"] = [
        review
        for review in existing_reviews
        if not (
            isinstance(review, dict)
            and isinstance(review.get("review_id"), str)
            and review["review_id"] in imported_ids
        )
    ]
    judgment["reviews"].extend(imported_reviews)
    return updated


def resolved_targets(records: list[dict], *, relation: str) -> set[str]:
    return {
        record["target"]
        for record in records
        if isinstance(record, dict)
        and record.get("relation") == relation
        and record.get("status") == "resolved"
        and isinstance(record.get("target"), str)
    }


def source_target_path(ref: str, target: str) -> str:
    if ref.startswith("trace:"):
        return target.split("#", 1)[0]
    return target


def git_resolved_target_path(target: str) -> str | None:
    if ":" not in target:
        return None
    commit, path = target.split(":", 1)
    if not FULL_COMMIT_RE.fullmatch(commit) or not path:
        return None
    return path


def resolved_source_paths(root: Path, records: list[dict], *, listed_refs: set[str]) -> set[str]:
    paths: set[str] = set()
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("relation") != "source"
            or record.get("status") != "resolved"
            or not isinstance(record.get("target"), str)
        ):
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        if isinstance(ref, str) and ref.startswith("git:"):
            source_path = git_source_ref_path(root, ref)
            if source_path:
                paths.add(source_path)
            continue
        paths.add(source_target_path(ref, record["target"]))
    return paths


def current_staged_changed_paths(root: Path) -> list[str]:
    return changed_paths(root, mode="staged", base_ref=None)


def current_base_ref_changed_paths(
    root: Path,
    base_ref: str,
    *,
    head_ref: str = "HEAD",
    exclude_archive_v2: bool = False,
) -> list[str]:
    result = git(root, ["diff", "--name-status", f"{base_ref}...{head_ref}"])
    if result.returncode != 0:
        raise PacketError(result.stderr.strip() or "failed to read git changed paths")
    paths = name_status_changed_paths(result.stdout)
    if exclude_archive_v2:
        paths = [path for path in paths if not path.startswith("archive/v2/")]
    return paths


def current_base_ref_deleted_paths(root: Path, base_ref: str, *, head_ref: str = "HEAD") -> list[str]:
    result = git(root, ["diff", "--name-status", f"{base_ref}...{head_ref}"])
    if result.returncode != 0:
        raise PacketError(result.stderr.strip() or "failed to read git deleted paths")
    deleted: list[str] = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0].startswith("D"):
            deleted.append(fields[1])
        elif len(fields) >= 3 and fields[0].startswith("R"):
            deleted.append(fields[1])
    return sorted(set(deleted))


def generated_base_ref_source_refs(
    root: Path,
    paths: list[str],
    base_ref: str | None,
    *,
    head_ref: str = "HEAD",
) -> list[tuple[str, str]]:
    if base_ref is None:
        return []
    head_commit = git_ref_commit(root, head_ref)
    comparison_commit = git_ref_commit(root, base_ref)
    if head_commit is None or comparison_commit is None:
        return []
    deleted_paths = set(current_base_ref_deleted_paths(root, base_ref, head_ref=head_ref))
    refs: list[tuple[str, str]] = []
    for path in paths:
        commit = comparison_commit if path in deleted_paths else head_commit
        ref = f"git:{commit}:{path}"
        resolved = resolve_ref(root, ref)
        if resolved is not None:
            refs.append((ref, resolved))
    return refs


def name_status_changed_paths(output: str) -> list[str]:
    return sorted({path for _status, paths in name_status_records(output) for path in paths})


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


def porcelain_status_paths(output: str) -> list[str]:
    paths: set[str] = set()
    for line in output.splitlines():
        path = line[3:] if len(line) > 3 else ""
        if not path:
            continue
        if " -> " in path:
            before, after = path.split(" -> ", 1)
            paths.update([before, after])
        else:
            paths.add(path)
    return sorted(paths)


def porcelain_status_records(output: str) -> list[tuple[str, list[str]]]:
    records: list[tuple[str, list[str]]] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if not path:
            continue
        if " -> " in path:
            before, after = path.split(" -> ", 1)
            records.append((status, [before, after]))
        else:
            records.append((status, [path]))
    return records


def git_text(root: Path, commit_ref: str, path: str) -> str | None:
    result = git(root, ["show", f"{commit_ref}:{path}"])
    return result.stdout if result.returncode == 0 else None


def path_has_proof_like_claim_at_commit(root: Path, commit_ref: str, path: str) -> bool:
    text = git_text(root, commit_ref, path)
    return bool(text and PROOF_LIKE_RE.search(text))


def commit_pinned_source_paths(
    root: Path,
    records: list[dict],
    *,
    listed_refs: set[str],
    commit_ref: str,
) -> set[str]:
    commit = git_ref_commit(root, commit_ref)
    if commit is None:
        return set()
    paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict) or record.get("relation") != "source" or record.get("status") != "resolved":
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        parts = git_source_ref_parts(root, ref)
        if parts and parts[0] == commit:
                paths.add(parts[1])
    return paths


def active_source_ref_violations(
    root: Path,
    records: list[dict],
    *,
    listed_refs: set[str],
    declared_changed_paths: set[str],
    deleted_paths: set[str],
    comparison_ref: str | None,
    accepted_head_commit: str | None,
) -> list[str]:
    errors: list[str] = []
    head_commit = git_ref_commit(root, accepted_head_commit) if accepted_head_commit else None
    comparison_commit = git_ref_commit(root, comparison_ref) if comparison_ref else None
    extra_paths: set[str] = set()
    mutable_refs: list[str] = []
    wrong_commit_refs: list[str] = []
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("relation") != "source"
            or record.get("status") != "resolved"
            or not isinstance(record.get("target"), str)
        ):
            continue
        ref = record.get("ref")
        if not isinstance(ref, str) or ref not in listed_refs:
            continue
        parts = git_source_ref_parts(root, ref)
        if parts is None:
            mutable_refs.append(ref)
            target = source_target_path(ref, record["target"])
            if target not in declared_changed_paths:
                extra_paths.add(target)
            continue
        commit, path = parts
        if path not in declared_changed_paths:
            extra_paths.add(path)
            continue
        expected_commit = comparison_commit if path in deleted_paths else head_commit
        if expected_commit is None or commit != expected_commit:
            wrong_commit_refs.append(ref)
    if extra_paths:
        errors.append(
            "active base-ref stable packet source_refs must only cover changed_paths: "
            f"{sorted(extra_paths)}"
        )
    if mutable_refs:
        errors.append(
            "active base-ref stable packet source_refs must use commit-pinned git refs only: "
            f"{sorted(mutable_refs)}"
        )
    if wrong_commit_refs:
        errors.append(
            "active base-ref stable packet source_refs use the wrong boundary commit: "
            f"{sorted(wrong_commit_refs)}"
        )
    return errors


def git_source_ref_path(root: Path, ref: str) -> str | None:
    parts = git_source_ref_parts(root, ref)
    return parts[1] if parts else None


def git_source_ref_parts(root: Path, ref: str) -> tuple[str, str] | None:
    if not isinstance(ref, str) or not ref.startswith("git:"):
        return None
    spec = ref.removeprefix("git:")
    if ":" not in spec:
        return None
    commit, path = spec.split(":", 1)
    if not FULL_COMMIT_RE.fullmatch(commit):
        return None
    result = git(root, ["cat-file", "-t", commit])
    if result.returncode != 0 or result.stdout.strip() != "commit":
        return None
    if not path or path.startswith("/") or ".." in Path(path).parts:
        return None
    return commit, path.split("#", 1)[0]


def git_ref_commit(root: Path, ref: str) -> str | None:
    result = git(root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    return result.stdout.strip() if result.returncode == 0 else None


def git_ref_is_commit(root: Path, ref: object) -> bool:
    if not isinstance(ref, str) or not ref:
        return False
    result = git(root, ["cat-file", "-t", ref])
    return result.returncode == 0 and result.stdout.strip() == "commit"


def git_ref_is_full_commit(root: Path, ref: object) -> bool:
    return isinstance(ref, str) and FULL_COMMIT_RE.fullmatch(ref) is not None and git_ref_is_commit(root, ref)


def git_blob_bytes(root: Path, commit_ref: str, path: str) -> bytes | None:
    result = git_bytes(root, ["cat-file", "blob", f"{commit_ref}:{path}"])
    return result.stdout if result.returncode == 0 else None


def git_file_sha256(root: Path, commit_ref: str, path: str) -> str | None:
    data = git_blob_bytes(root, commit_ref, path)
    return hashlib.sha256(data).hexdigest() if data is not None else None


def git_diff_name_only(root: Path, left_ref: str, right_ref: str) -> list[str] | None:
    result = git(root, ["diff", "--name-only", left_ref, right_ref])
    if result.returncode != 0:
        return None
    return sorted(path for path in result.stdout.splitlines() if path)


def git_diff_changed_paths(root: Path, left_ref: str, right_ref: str) -> list[str] | None:
    result = git(root, ["diff", "--name-status", left_ref, right_ref])
    if result.returncode != 0:
        return None
    return name_status_changed_paths(result.stdout)


def git_diff_name_status_records(root: Path, left_ref: str, right_ref: str) -> list[tuple[str, list[str]]] | None:
    result = git(root, ["diff", "--name-status", left_ref, right_ref])
    if result.returncode != 0:
        return None
    return name_status_records(result.stdout)


def git_diff_name_status_records_for_spec(root: Path, diff_spec: str) -> list[tuple[str, list[str]]] | None:
    result = git(root, ["diff", "--name-status", diff_spec])
    if result.returncode != 0:
        return None
    return name_status_records(result.stdout)


def git_tree_paths(root: Path, commit_ref: str, pathspec: str) -> list[str] | None:
    result = git(root, ["ls-tree", "-r", "--name-only", commit_ref, "--", pathspec])
    if result.returncode != 0:
        return None
    return sorted(path for path in result.stdout.splitlines() if path)


def git_commit_count_between(root: Path, left_ref: str, right_ref: str) -> int | None:
    result = git(root, ["rev-list", "--count", f"{left_ref}..{right_ref}"])
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def git_rev_list_between(root: Path, left_ref: str, right_ref: str) -> list[str] | None:
    result = git(root, ["rev-list", "--reverse", "--ancestry-path", f"{left_ref}..{right_ref}"])
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


def git_commit_parents(root: Path, commit_ref: str) -> list[str] | None:
    result = git(root, ["show", "-s", "--format=%P", commit_ref])
    if result.returncode != 0:
        return None
    return [parent for parent in result.stdout.strip().split() if parent]


def git_is_ancestor(root: Path, ancestor_ref: str, descendant_ref: str) -> bool:
    return git(root, ["merge-base", "--is-ancestor", ancestor_ref, descendant_ref]).returncode == 0


def same_git_boundary(root: Path, left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    left_commit = git_ref_commit(root, left)
    right_commit = git_ref_commit(root, right)
    return left_commit is not None and left_commit == right_commit


def provenance_source_refs(packet: dict) -> list[tuple[str, dict, str]]:
    input_data = packet["input"]
    result = packet["result"]
    refs: list[tuple[str, dict, str]] = []
    user_judgment = input_data.get("user_judgment", {})
    if isinstance(user_judgment, dict):
        for key, record in user_judgment.items():
            if (
                isinstance(key, str)
                and isinstance(record, dict)
                and isinstance(record.get("source_ref"), str)
                and record.get("source_ref")
            ):
                refs.append((f"input.user_judgment.{key}", record, record["source_ref"]))
    for source, records in (
        ("result.evidence.skipped", result["evidence"].get("skipped", [])),
        ("result.judgment.waivers", result["judgment"].get("waivers", [])),
        ("result.judgment.downgrades", result["judgment"].get("downgrades", [])),
        ("result.judgment.residual_risk", result["judgment"].get("residual_risk", [])),
    ):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if isinstance(record, dict) and isinstance(record.get("source_ref"), str) and record.get("source_ref"):
                refs.append((f"{source}[{index}]", record, record["source_ref"]))
    return refs


def provenance_record_digest(record: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def provenance_source_ref_binds_record(root: Path, source_ref: str, record: dict) -> bool:
    text = ref_text(root, source_ref)
    if text is None:
        return False
    return f"provenance_record_sha256:{provenance_record_digest(record)}" in text


def review_source_refs(packet: dict) -> list[tuple[str, str, dict]]:
    refs: list[tuple[str, str, dict]] = []
    records = packet["result"]["judgment"].get("reviews", [])
    if not isinstance(records, list):
        return refs
    for index, record in enumerate(records):
        if isinstance(record, dict) and isinstance(record.get("source_ref"), str) and record.get("source_ref"):
            refs.append((f"result.judgment.reviews[{index}]", record["source_ref"], record))
    return refs


def validate_packet(
    packet: dict,
    *,
    require_stable: bool = False,
    require_archive_command_replay_metadata: bool = False,
    replay_archive_command_evidence: bool = False,
    allow_stale_archive_command_artifacts: bool = False,
    root: Path = ROOT,
    replay_root: Path | None = None,
    packet_ref: str | None = None,
    packet_sha256: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if set(packet) != set(PUBLIC_SECTIONS):
        errors.append(f"packet public sections must be exactly {', '.join(PUBLIC_SECTIONS)}")
        return errors

    meta = packet.get("meta")
    input_data = packet.get("input")
    result = packet.get("result")
    if not isinstance(meta, dict) or not isinstance(input_data, dict) or not isinstance(result, dict):
        return ["meta, input, and result must be mappings"]

    if set(meta) != set(META_FIELDS):
        errors.append(f"meta fields must be exactly {', '.join(META_FIELDS)}")
    if set(input_data) != set(INPUT_FIELDS):
        errors.append(f"input fields must be exactly {', '.join(INPUT_FIELDS)}")
    if any(field not in meta for field in META_FIELDS) or any(field not in input_data for field in INPUT_FIELDS):
        return errors
    if set(result) != set(RESULT_GROUPS):
        errors.append(f"result groups must be exactly {', '.join(RESULT_GROUPS)}")
        return errors
    for group in RESULT_GROUPS:
        if not isinstance(result[group], dict):
            errors.append(f"result.{group} must be a mapping")

    if errors:
        return errors

    lifecycle = meta["lifecycle"]
    mode = meta["mode"]
    if not isinstance(lifecycle, str) or lifecycle not in LIFECYCLES:
        errors.append(f"meta.lifecycle is invalid: {lifecycle}")
    if not isinstance(mode, str) or mode not in MODES:
        errors.append(f"meta.mode is invalid: {mode}")
    if not date_like(meta["created_at"]):
        errors.append("meta.created_at must be an ISO date")
    if not date_like(meta["finalized_at"], allow_none=lifecycle == "start"):
        errors.append("meta.finalized_at must be an ISO date, or null for start packets")
    if lifecycle == "start" and meta["finalized_at"] is not None:
        errors.append("start packet finalized_at must be null")
    if lifecycle != "start" and meta["finalized_at"] is None:
        errors.append("finalized or blocked packet finalized_at is required")

    if not isinstance(input_data["intent"], str) or not input_data["intent"]:
        errors.append("input.intent must be a non-empty string")
    if not isinstance(input_data["actor"], str) or not input_data["actor"]:
        errors.append("input.actor must be a non-empty string")
    if not isinstance(input_data["source_refs"], list):
        errors.append("input.source_refs must be a list")
    if not isinstance(input_data["user_judgment"], dict):
        errors.append("input.user_judgment must be a mapping")

    inference = result["inference"]
    evidence = result["evidence"]
    judgment = result["judgment"]
    decision = result["decision"]
    command_result_records = mapping_records(
        evidence.get("command_results", []),
        source="result.evidence.command_results",
        errors=errors,
    )
    skipped_records = mapping_records(
        evidence.get("skipped", []),
        source="result.evidence.skipped",
        errors=errors,
    )
    waiver_records = mapping_records(
        judgment.get("waivers", []),
        source="result.judgment.waivers",
        errors=errors,
    )
    downgrade_records = mapping_records(
        judgment.get("downgrades", []),
        source="result.judgment.downgrades",
        errors=errors,
    )
    review_records = mapping_records(
        judgment.get("reviews", []),
        source="result.judgment.reviews",
        errors=errors,
    )
    residual_risk_records = mapping_records(
        judgment.get("residual_risk", []),
        source="result.judgment.residual_risk",
        errors=errors,
    )
    evaluator_boundary = evidence.get("evaluator_boundary")
    if isinstance(evaluator_boundary, dict):
        status = evaluator_boundary.get("status")
        if status is not None and not isinstance(status, str):
            errors.append("result.evidence.evaluator_boundary.status must be null or a string")
    accepted = decision.get("accepted")
    stable = decision.get("stable_handoff_eligible")
    declared_required_evidence, declared_required_review = required_targets(packet)
    required_review = declared_required_review
    required_evidence = declared_required_evidence
    stable_required_evidence_errors: list[str] = []
    stable_required_review_errors: list[str] = []
    if stable:
        required_evidence, stable_required_evidence_errors = stable_required_evidence(packet)
        required_review = checker_required_review(packet, root=root)
        if declared_required_review != required_review:
            stable_required_review_errors.append(
                "stable packet required_review must match checker-derived required reviews: "
                f"{sorted(required_review)}"
            )

    if lifecycle != "start":
        for field in FINALIZED_INFERENCE_FIELDS:
            if field not in inference:
                errors.append(f"result.inference.{field} is required for {lifecycle} packets")
        changed_path_values = inference.get("changed_paths", [])
        if not isinstance(changed_path_values, list):
            errors.append("result.inference.changed_paths must be a list")
            changed_path_values = []
        elif any(not isinstance(path, str) for path in changed_path_values):
            errors.append("result.inference.changed_paths must contain only strings")
        if not isinstance(inference.get("deviations"), list):
            errors.append("result.inference.deviations must be a list")
        if not isinstance(inference.get("required_evidence"), list):
            errors.append("result.inference.required_evidence must be a list")
        elif any(not isinstance(item, str) for item in inference.get("required_evidence", [])):
            errors.append("result.inference.required_evidence must contain only strings")
        if not isinstance(inference.get("required_review"), list):
            errors.append("result.inference.required_review must be a list")
        elif any(not isinstance(item, str) for item in inference.get("required_review", [])):
            errors.append("result.inference.required_review must contain only strings")
        if not isinstance(inference.get("protected_boundary_changed"), bool):
            errors.append("result.inference.protected_boundary_changed must be a boolean")
        protected_paths = [path for path in changed_path_values if isinstance(path, str) and requires_review_for_path(path)]
        if protected_paths:
            if inference.get("protected_boundary_changed") is not True:
                errors.append("protected changed paths require protected_boundary_changed: true")
            if inference.get("change_class") != "harness-affecting":
                errors.append("protected changed paths require change_class: harness-affecting")
            if inference.get("impact") != "high":
                errors.append("protected changed paths require impact: high")

    user_judgment = input_data.get("user_judgment")
    if not isinstance(user_judgment, dict):
        user_judgment = {}
    for key, request in user_judgment.items():
        if not isinstance(key, str):
            errors.append(f"input.user_judgment key must be a string: {key}")
            continue
        if "waiver" in key or "downgrade" in key:
            errors.extend(
                validate_exception_record(
                    request,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"input.user_judgment.{key}",
                    record_type="downgrade" if "downgrade" in key else "waiver",
                )
            )
        elif "skipped" in key:
            errors.extend(validate_provenance_record(request, source=f"input.user_judgment.{key}"))
            if isinstance(request, dict):
                evidence_target = request.get("evidence")
                if not evidence_target:
                    errors.append(f"input.user_judgment.{key}: evidence is required")
                elif not isinstance(evidence_target, str):
                    errors.append(f"input.user_judgment.{key}: evidence must be a string")
                elif evidence_target not in required_evidence:
                    errors.append(f"input.user_judgment.{key}: skipped evidence is not required: {evidence_target}")
        elif "residual" in key:
            errors.extend(
                validate_residual_risk_record(
                    request,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"input.user_judgment.{key}",
                )
            )
        else:
            errors.append(
                f"input.user_judgment.{key}: key must declare waiver, downgrade, skipped, or residual"
            )

    for waiver in waiver_records:
        errors.extend(
            validate_exception_record(
                waiver,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.waivers",
                record_type="waiver",
            )
        )
    for downgrade in downgrade_records:
        errors.extend(
            validate_exception_record(
                downgrade,
                required_evidence=required_evidence,
                required_review=required_review,
                source="result.judgment.downgrades",
                record_type="downgrade",
            )
        )

    if lifecycle == "start":
        if accepted is not None:
            errors.append("start packet decision.accepted must be null")
        if stable is not False:
            errors.append("start packet cannot be stable-handoff eligible")
    if lifecycle == "blocked":
        if accepted is not False:
            errors.append("blocked packet decision.accepted must be false")
        if stable is not False:
            errors.append("blocked packet cannot be stable-handoff eligible")
    if mode == "worktree" and stable is not False:
        errors.append("worktree packets cannot be stable-handoff eligible")
    if stable and accepted is not True:
        errors.append("stable-handoff packet must be accepted")
    if lifecycle == "finalized" and mode == "base-ref" and packet_is_active_handoff(packet, packet_ref, root=root):
        comparison_ref = evidence.get("comparison_ref")
        accepted_head_commit = evidence.get("accepted_head_commit")
        accepted_head_ref = (
            accepted_head_commit
            if isinstance(accepted_head_commit, str) and git_ref_is_commit(root, accepted_head_commit)
            else "HEAD"
        )
        if isinstance(comparison_ref, str) and git_ref_is_commit(root, comparison_ref) and isinstance(packet_ref, str):
            errors.extend(
                accepted_head_archive_scope_errors(
                    root,
                    packet,
                    packet_ref=packet_ref,
                    comparison_ref=comparison_ref,
                    accepted_head=accepted_head_ref,
                )
            )

    for review in review_records:
        score = review.get("score")
        if stable and not review.get("review_id"):
            errors.append("stable review requires review_id")
        if stable and not review.get("rerun_of"):
            errors.extend(validate_review_record(review, source="result.judgment.reviews"))
        if isinstance(score, (int, float)) and score == 9:
            if not review.get("why_not_10") or not review.get("disposition"):
                errors.append("score 9 review requires why_not_10 and disposition")

    if stable:
        active_stable_handoff = packet_is_active_handoff(packet, packet_ref, root=root)
        if active_stable_handoff and mode != "base-ref":
            errors.append("active stable handoff requires base-ref mode; staged packets are preflight-only")
        errors.extend(stable_required_evidence_errors)
        errors.extend(stable_required_review_errors)
        if not required_evidence:
            errors.append("stable packet must declare checker-derived required evidence")
        if declared_required_evidence != required_evidence:
            errors.append(
                "stable packet required_evidence must match checker-derived required evidence: "
                f"{sorted(required_evidence)}"
            )

        resolved_refs = evidence.get("resolved_refs", [])
        if not isinstance(resolved_refs, list):
            errors.append("stable packet evidence.resolved_refs must be a list")
            resolved_refs = []
        for record in resolved_refs:
            errors.extend(validate_resolved_ref_record(record, root=root, source="result.evidence.resolved_refs"))
        ref_index = resolved_ref_index(resolved_refs)
        open_passing_review_targets, review_import_errors = validate_review_imports(
            packet,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
            ref_index=ref_index,
        )
        errors.extend(review_import_errors)

        evidence_source_refs = evidence.get("source_refs", [])
        if not isinstance(evidence_source_refs, list):
            errors.append("stable packet evidence.source_refs must be a list")
            evidence_source_refs = []
        input_source_refs = input_data.get("source_refs", [])
        if not isinstance(input_source_refs, list):
            input_source_refs = []
        for ref in input_source_refs:
            if not isinstance(ref, str):
                errors.append(f"stable packet input source_ref must be a string: {ref}")
                continue
            if ref not in evidence_source_refs:
                errors.append(f"stable packet input source_ref missing from evidence.source_refs: {ref}")
            if not has_resolved_relation(ref_index, relation="source", ref=ref, origin="input"):
                errors.append(f"stable packet input source_ref lacks resolved input source relation: {ref}")
        for ref in evidence_source_refs:
            if not isinstance(ref, str):
                errors.append(f"stable packet evidence source_ref must be a string: {ref}")
                continue
            if not has_resolved_relation(ref_index, relation="source", ref=ref):
                errors.append(f"stable packet source_ref lacks resolved source relation: {ref}")
        source_paths = resolved_source_paths(
            root,
            resolved_refs,
            listed_refs={ref for ref in evidence_source_refs if isinstance(ref, str)},
        )
        declared_changed_paths = set(string_list_values(inference.get("changed_paths", [])))
        accepted_head_commit = evidence.get("accepted_head_commit")
        if active_stable_handoff and mode == "base-ref":
            if not accepted_head_commit:
                errors.append("active base-ref stable packet accepted_head_commit is required")
            elif not git_ref_is_full_commit(root, accepted_head_commit):
                errors.append(
                    f"active base-ref stable packet accepted_head_commit must be a full commit SHA: {accepted_head_commit}"
                )
        missing_changed_sources = sorted(path for path in declared_changed_paths if path not in source_paths)
        if missing_changed_sources:
            errors.append(f"stable packet changed_paths lack resolved source refs: {missing_changed_sources}")
        protected_source_targets = sorted(
            target for target in source_paths if requires_review_for_path(target) and target not in declared_changed_paths
        )
        if protected_source_targets:
            errors.append(
                f"stable packet source_ref points to protected path outside changed_paths: {protected_source_targets}"
            )
        if active_stable_handoff and mode == "base-ref":
            deleted_paths: set[str] = set()
            comparison_ref = evidence.get("comparison_ref")
            accepted_head_ref = (
                accepted_head_commit
                if isinstance(accepted_head_commit, str) and git_ref_is_commit(root, accepted_head_commit)
                else "HEAD"
            )
            if isinstance(comparison_ref, str) and git_ref_is_commit(root, comparison_ref):
                deleted_paths = set(current_base_ref_deleted_paths(root, comparison_ref, head_ref=accepted_head_ref))
            source_ref_set = {ref for ref in evidence_source_refs if isinstance(ref, str)}
            errors.extend(
                active_source_ref_violations(
                    root,
                    resolved_refs,
                    listed_refs=source_ref_set,
                    declared_changed_paths=declared_changed_paths,
                    deleted_paths=deleted_paths,
                    comparison_ref=comparison_ref if isinstance(comparison_ref, str) else None,
                    accepted_head_commit=accepted_head_ref,
                )
            )
            head_pinned_paths = commit_pinned_source_paths(
                root,
                resolved_refs,
                listed_refs=source_ref_set,
                commit_ref=accepted_head_ref,
            )
            missing_head_sources = sorted(
                path for path in declared_changed_paths - deleted_paths if path not in head_pinned_paths
            )
            if missing_head_sources:
                errors.append(
                    "active base-ref stable packet changed_paths require HEAD-pinned git source refs: "
                    f"{missing_head_sources}"
                )
            if deleted_paths:
                base_pinned_paths = commit_pinned_source_paths(
                    root,
                    resolved_refs,
                    listed_refs=source_ref_set,
                    commit_ref=comparison_ref,
                )
                missing_deleted_sources = sorted(
                    path for path in declared_changed_paths & deleted_paths if path not in base_pinned_paths
                )
                if missing_deleted_sources:
                    errors.append(
                        "active base-ref stable packet deleted or renamed-preimage changed_paths require comparison-ref-pinned git source refs: "
                        f"{missing_deleted_sources}"
                    )
        if mode == "staged" and packet_ref_is_repo_local(packet_ref) and active_stable_handoff:
            staged_paths = set(current_staged_changed_paths(root))
            if staged_paths != declared_changed_paths:
                errors.append(
                    "staged stable packet changed_paths must match current staged diff: "
                    f"declared={sorted(declared_changed_paths)} staged={sorted(staged_paths)}"
                )

        for boundary_ref_name in ("baseline_ref", "comparison_ref"):
            boundary_ref = evidence.get(boundary_ref_name)
            if not boundary_ref:
                errors.append(f"stable packet {boundary_ref_name} is required")
            elif not git_ref_is_commit(root, boundary_ref):
                errors.append(f"stable packet {boundary_ref_name} must resolve to a git commit: {boundary_ref}")
            elif active_stable_handoff and mode == "base-ref" and not git_ref_is_full_commit(root, boundary_ref):
                errors.append(
                    f"active base-ref stable packet {boundary_ref_name} must be a full commit SHA: {boundary_ref}"
                )
            elif mode == "staged" and not same_git_boundary(root, boundary_ref, "HEAD"):
                errors.append(f"staged stable packet {boundary_ref_name} must match HEAD: {boundary_ref}")
        comparison_ref = evidence.get("comparison_ref")
        baseline_ref = evidence.get("baseline_ref")
        if (
            active_stable_handoff
            and mode == "base-ref"
            and isinstance(baseline_ref, str)
            and isinstance(comparison_ref, str)
            and git_ref_is_commit(root, baseline_ref)
            and git_ref_is_commit(root, comparison_ref)
            and not same_git_boundary(root, baseline_ref, comparison_ref)
        ):
            errors.append("active base-ref stable packet baseline_ref must match comparison_ref")
        if (
            active_stable_handoff
            and mode == "base-ref"
            and isinstance(comparison_ref, str)
            and git_ref_is_commit(root, comparison_ref)
        ):
            accepted_head_ref = (
                accepted_head_commit
                if isinstance(accepted_head_commit, str) and git_ref_is_commit(root, accepted_head_commit)
                else "HEAD"
            )
            base_ref_paths = set(
                current_base_ref_changed_paths(
                    root,
                    comparison_ref,
                    head_ref=accepted_head_ref,
                    exclude_archive_v2=True,
                )
            )
            if base_ref_paths != declared_changed_paths:
                errors.append(
                    "base-ref stable packet changed_paths must match git diff boundary: "
                    f"declared={sorted(declared_changed_paths)} base_ref={comparison_ref} "
                    f"accepted_head={accepted_head_ref} "
                    f"actual={sorted(base_ref_paths)}"
                )

        for source, record, source_ref in provenance_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="waiver-provenance", ref=source_ref, origin="generated"):
                errors.append(f"{source}: source_ref lacks resolved waiver-provenance relation with generated origin: {source_ref}")
            elif ref_is_acceptance_packet(root, source_ref):
                errors.append(f"{source}: waiver-provenance source_ref cannot be an acceptance packet: {source_ref}")
            elif active_stable_handoff and not provenance_source_ref_binds_record(root, source_ref, record):
                errors.append(
                    f"{source}: waiver-provenance source_ref must contain provenance_record_sha256 marker: {source_ref}"
                )
        for index, record in enumerate(residual_risk_records):
            errors.extend(
                validate_residual_risk_record(
                    record,
                    required_evidence=required_evidence,
                    required_review=required_review,
                    source=f"result.judgment.residual_risk[{index}]",
                )
            )
        for source, source_ref, review in review_source_refs(packet):
            if not has_resolved_relation(ref_index, relation="review-provenance", ref=source_ref, origin="generated"):
                errors.append(f"{source}: source_ref lacks resolved review-provenance relation with generated origin: {source_ref}")
            elif ref_is_acceptance_packet(root, source_ref):
                errors.append(f"{source}: review-provenance source_ref cannot be an acceptance packet: {source_ref}")
            elif not review_source_ref_records_review(root, source_ref, review, packet_id=meta["packet_id"]):
                errors.append(f"{source}: review-provenance source_ref lacks matching review record: {source_ref}")

        protected_review_required = (
            inference.get("protected_boundary_changed") is True
            or inference.get("change_class") == "harness-affecting"
            or inference.get("impact") == "high"
            or any(requires_review_for_path(path) for path in string_list_values(inference.get("changed_paths", [])))
        )
        if protected_review_required and not required_review:
            errors.append("stable protected or high-impact packet must infer required review")

        passed_evidence: set[str] = set()
        for index, item in enumerate(command_result_records):
            status = item.get("status")
            if not isinstance(status, str) or not status:
                errors.append(f"result.evidence.command_results[{index}].status must be a non-empty string")
                continue
            command = item.get("command")
            if not isinstance(command, str) or not command:
                errors.append(f"result.evidence.command_results[{index}].command must be a non-empty string")
                continue
            if status == "pass":
                passed_evidence.add(command)
            base_ref = command_base_ref(command)
            if base_ref:
                for boundary_ref_name in ("baseline_ref", "comparison_ref"):
                    if not same_git_boundary(root, evidence.get(boundary_ref_name), base_ref):
                        errors.append(
                            f"stable command base-ref {base_ref} must match evidence.{boundary_ref_name}: "
                            f"{evidence.get(boundary_ref_name)}"
                        )
            artifact_ref = item.get("artifact_ref")
            if not artifact_ref:
                errors.append(f"stable command evidence lacks artifact_ref: {command}")
            elif str(artifact_ref).startswith("terminal:"):
                errors.append(f"terminal placeholder cannot satisfy stable evidence: {artifact_ref}")
            elif not str(artifact_ref).startswith("file:"):
                errors.append(f"stable command artifact_ref must use file: scheme: {artifact_ref}")
            elif active_stable_handoff and mode == "base-ref" and not str(artifact_ref).startswith(f"file:{ARCHIVE_ARTIFACT_PREFIX}"):
                errors.append(
                    "active stable command artifact_ref must be under "
                    f"{ARCHIVE_ARTIFACT_PREFIX}: {artifact_ref}"
                )
            elif not has_resolved_relation(ref_index, relation="artifact", ref=artifact_ref, origin="generated"):
                errors.append(f"stable command artifact lacks resolved generated artifact relation: {artifact_ref}")
            else:
                artifact_error = artifact_command_evidence_error(
                    root,
                    artifact_ref,
                    command,
                    status,
                    packet_id=meta["packet_id"],
                    packet_ref=packet_ref or "",
                    packet_sha256=packet_sha256 or "",
                    require_archive_replay_metadata=require_archive_command_replay_metadata,
                    require_safe_archive_replay_command=require_archive_command_replay_metadata,
                    require_empty_pass_replay_hashes=require_archive_command_replay_metadata,
                    replay_archive_command=replay_archive_command_evidence,
                    replay_root=replay_root,
                    allow_stale_packet_sha=allow_stale_archive_command_artifacts,
                )
                if artifact_error:
                    errors.append(f"stable command artifact does not record command evidence: {artifact_ref}: {artifact_error}")

        trace_refs = evidence.get("trace_refs", {})
        if not isinstance(trace_refs, dict):
            errors.append("stable packet evidence.trace_refs must be a mapping")
            trace_refs = {}
        expected_search_set_packet_ref = (
            None if packet_has_materialized_fixture_binding(packet, packet_ref, root=root) else packet_ref
        )
        accepted_head_ref = evidence.get("accepted_head_commit")
        comparison_head_ref = evidence.get("comparison_ref") or evidence.get("baseline_ref")
        expected_search_set_heads = {
            "search_set_before": comparison_head_ref if isinstance(comparison_head_ref, str) and FULL_COMMIT_RE.fullmatch(comparison_head_ref) else None,
            "search_set_after": accepted_head_ref if isinstance(accepted_head_ref, str) and FULL_COMMIT_RE.fullmatch(accepted_head_ref) else None,
        }
        for trace_name in ("search_set_before", "search_set_after"):
            trace_ref = trace_refs.get(trace_name)
            if trace_ref is None:
                continue
            expected_phase = "before" if trace_name == "search_set_before" else "after"
            if not isinstance(trace_ref, str) or not trace_ref.startswith("trace:"):
                errors.append(f"stable trace_refs.{trace_name} must use trace: scheme: {trace_ref}")
            elif not trace_ref_has_anchor(trace_ref):
                errors.append(f"stable trace_refs.{trace_name} must include an anchor: {trace_ref}")
            elif not is_search_set_trace_ref(trace_ref):
                errors.append(f"stable trace_refs.{trace_name} must point to .harness/traces/search-set.md: {trace_ref}")
            elif error := search_set_capture_record_error(
                root,
                trace_ref,
                expected_phase=expected_phase,
                expected_packet_ref=expected_search_set_packet_ref,
                expected_head_ref=expected_search_set_heads[trace_name],
            ):
                errors.append(f"stable trace_refs.{trace_name}: {error}")
            elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                errors.append(f"stable trace_refs.{trace_name} lacks resolved generated trace relation: {trace_ref}")
        if isinstance(trace_refs, dict):
            search_set_before = trace_refs.get("search_set_before")
            search_set_after = trace_refs.get("search_set_after")
            canonical_before = canonical_trace_ref(search_set_before) if isinstance(search_set_before, str) else None
            canonical_after = canonical_trace_ref(search_set_after) if isinstance(search_set_after, str) else None
            if canonical_before and canonical_before == canonical_after:
                errors.append("stable packet search_set_before and search_set_after must be distinct when both are recorded")
        for bucket_name in ("evolution", "failures"):
            bucket_refs = trace_refs.get(bucket_name, [])
            if not isinstance(bucket_refs, list):
                errors.append(f"stable trace_refs.{bucket_name} must be a list")
                continue
            for trace_ref in bucket_refs:
                if not isinstance(trace_ref, str) or not trace_ref.startswith("trace:"):
                    errors.append(f"stable trace_refs.{bucket_name} entries must use trace: scheme: {trace_ref}")
                elif not trace_ref_has_anchor(trace_ref):
                    errors.append(f"stable trace_refs.{bucket_name} entries must include an anchor: {trace_ref}")
                elif not is_bucket_trace_ref(trace_ref, bucket_name):
                    errors.append(
                        f"stable trace_refs.{bucket_name} entries must point to .harness/traces/{bucket_name}/ evidence: {trace_ref}"
                    )
                elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                    errors.append(f"stable trace_refs.{bucket_name} lacks resolved generated trace relation: {trace_ref}")

        if protected_review_required:
            for trace_name in ("search_set_before", "search_set_after"):
                trace_ref = trace_refs.get(trace_name) if isinstance(trace_refs, dict) else None
                skipped_targets = {
                    item.get("evidence")
                    for item in skipped_records
                    if isinstance(item, dict)
                    and isinstance(item.get("evidence"), str)
                    and item.get("evidence")
                }
                if trace_ref and trace_name in skipped_targets:
                    errors.append(
                        f"stable protected packet {trace_name} cannot have both trace evidence and skipped evidence"
                    )
                    continue
                if not trace_ref and trace_name in skipped_targets:
                    continue
                if not trace_ref:
                    errors.append(f"stable protected packet missing {trace_name}")
                elif not is_search_set_trace_ref(trace_ref):
                    errors.append(f"stable protected packet {trace_name} must point to .harness/traces/search-set.md: {trace_ref}")
                elif error := search_set_capture_record_error(
                    root,
                    trace_ref,
                    expected_phase="before" if trace_name == "search_set_before" else "after",
                    expected_packet_ref=expected_search_set_packet_ref,
                    expected_head_ref=expected_search_set_heads[trace_name],
                ):
                    errors.append(f"stable protected packet {trace_name}: {error}")
                elif not has_resolved_relation(ref_index, relation="trace", ref=trace_ref, origin="generated"):
                    errors.append(f"stable protected packet {trace_name} lacks resolved generated trace relation: {trace_ref}")

        for skipped in skipped_records:
            errors.extend(validate_provenance_record(skipped, source="result.evidence.skipped"))
            evidence_target = skipped.get("evidence") if isinstance(skipped, dict) else None
            allowed_skips = required_evidence | {"search_set_before", "search_set_after"}
            if not evidence_target:
                errors.append("result.evidence.skipped: evidence is required")
            elif not isinstance(evidence_target, str):
                errors.append("result.evidence.skipped: evidence must be a string")
            elif evidence_target not in allowed_skips:
                errors.append(f"result.evidence.skipped: skipped evidence is not required: {evidence_target}")

        proof_like_paths = [
            path
            for path in string_list_values(inference.get("changed_paths", []))
            if path.endswith(".md") and path_has_proof_like_claim_for_packet(root, packet, path)
        ]
        claims = evidence.get("claims", [])
        if proof_like_paths and not claims:
            errors.append(f"stable packet has proof-like changed docs without claim evidence: {proof_like_paths}")
        if proof_like_paths and inference.get("impact") != "high":
            errors.append("proof-like changed docs require impact: high")
        if proof_like_paths and "claim evidence" not in required_review:
            errors.append("proof-like changed docs require claim evidence review")
        if claims and not isinstance(claims, list):
            errors.append("result.evidence.claims must be a list")
            claims = []
        for claim in claims:
            if not isinstance(claim, dict):
                errors.append("result.evidence.claims: claim must be a mapping")
                continue
            raw_refs = claim.get("raw_evidence_refs")
            if not isinstance(raw_refs, list) or not raw_refs:
                errors.append("result.evidence.claims: raw_evidence_refs is required")
                continue
            for raw_ref in raw_refs:
                if not isinstance(raw_ref, str) or not raw_ref.startswith("file:"):
                    errors.append(f"claim evidence ref must use file: scheme: {raw_ref}")
                elif not has_resolved_relation(ref_index, relation="claim-evidence", ref=raw_ref, origin="generated"):
                    errors.append(f"claim evidence ref lacks resolved generated claim-evidence relation: {raw_ref}")
                elif not is_raw_claim_file_ref(root, raw_ref):
                    errors.append(
                        "claim evidence file ref must point to raw artifact/log/screenshot/report evidence: "
                        f"{raw_ref}"
                    )

        passed_evidence_records = [
            item.get("command")
            for item in command_result_records
            if item.get("status") == "pass" and isinstance(item.get("command"), str) and item.get("command")
        ]
        waived_evidence_records = [
            item.get("evidence")
            for item in waiver_records
            if isinstance(item.get("evidence"), str) and item.get("evidence")
        ]
        skipped_evidence_records = [
            item.get("evidence")
            for item in skipped_records
            if isinstance(item, dict) and isinstance(item.get("evidence"), str) and item.get("evidence") in required_evidence
        ]
        closed_evidence_replacements = (
            set(passed_evidence_records) | set(waived_evidence_records) | set(skipped_evidence_records)
        )
        downgraded_evidence_records: list[str] = []
        for item in downgrade_records:
            if item.get("kind") != "evidence":
                continue
            source_target = item.get("from")
            replacement = item.get("to")
            if not isinstance(source_target, str) or not source_target:
                continue
            if not isinstance(replacement, str) or not replacement:
                continue
            if replacement not in closed_evidence_replacements:
                errors.append(
                    "stable evidence downgrade replacement is not closed by durable evidence, waiver, or skip: "
                    f"{source_target} -> {replacement}"
                )
                continue
            downgraded_evidence_records.append(source_target)
        errors.extend(
            multiple_required_closure_errors(
                required_evidence,
                [
                    ("command pass", passed_evidence_records),
                    ("waiver", waived_evidence_records),
                    ("downgrade", downgraded_evidence_records),
                    ("skipped", skipped_evidence_records),
                ],
                kind="evidence",
            )
        )
        passed_evidence = set(passed_evidence_records)
        waived_evidence = set(waived_evidence_records)
        downgraded_evidence = set(downgraded_evidence_records)
        skipped_evidence = set(skipped_evidence_records)
        missing_evidence = required_evidence - passed_evidence - waived_evidence - downgraded_evidence - skipped_evidence
        if missing_evidence:
            errors.append(f"stable packet missing required evidence: {sorted(missing_evidence)}")

        open_passing_review_records = list(open_passing_review_targets)
        waived_review_records = [
            item.get("review")
            for item in waiver_records
            if isinstance(item.get("review"), str) and item.get("review")
        ]
        closed_review_replacements = set(open_passing_review_records) | set(waived_review_records)
        downgraded_review_records: list[str] = []
        for item in downgrade_records:
            if item.get("kind") != "review":
                continue
            source_target = item.get("from")
            replacement = item.get("to")
            if not isinstance(source_target, str) or not source_target:
                continue
            if not isinstance(replacement, str) or not replacement:
                continue
            if replacement not in closed_review_replacements:
                errors.append(
                    "stable review downgrade replacement is not closed by durable review or waiver: "
                    f"{source_target} -> {replacement}"
                )
                continue
            downgraded_review_records.append(source_target)
        errors.extend(
            multiple_required_closure_errors(
                required_review,
                [
                    ("review pass", open_passing_review_records),
                    ("waiver", waived_review_records),
                    ("downgrade", downgraded_review_records),
                ],
                kind="review",
            )
        )
        waived_reviews = set(waived_review_records)
        downgraded_reviews = set(downgraded_review_records)
        passing_reviews = set(open_passing_review_records)
        missing_reviews = required_review - passing_reviews - waived_reviews - downgraded_reviews
        if missing_reviews:
            errors.append(f"stable packet missing required review: {sorted(missing_reviews)}")

    if require_stable and stable is not True:
        errors.append("packet is valid but not stable-handoff eligible")

    return errors


def stable_target_for_packet(packet: dict) -> str:
    meta = packet.get("meta", {}) if isinstance(packet.get("meta"), dict) else {}
    result = packet.get("result", {})
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    target = f"{meta.get('mode')}:{evidence.get('baseline_ref')}...{evidence.get('comparison_ref')}"
    accepted_head = evidence.get("accepted_head_commit")
    return f"{target}@{accepted_head}" if accepted_head else target


def decision_status_for_packet(packet: dict) -> str:
    result = packet.get("result", {}) if isinstance(packet.get("result"), dict) else {}
    decision = result.get("decision", {}) if isinstance(result, dict) else {}
    if not isinstance(decision, dict):
        return "unknown"
    if decision.get("accepted") is True and decision.get("stable_handoff_eligible") is True:
        return "accepted"
    if decision.get("accepted") is False:
        return "blocked"
    return "pending"


def safe_artifact_stem(value: object) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip(".-")
    return stem or "packet"


def default_archive_packet_output(packet_id_value: str) -> Path:
    return Path(ARCHIVE_PACKET_PREFIX) / f"{safe_artifact_stem(packet_id_value)}.yml"


def repo_relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PacketError(f"{path}: path must be inside repository root") from exc


def pointer_packet_ref_error(packet_ref: object) -> str | None:
    if not isinstance(packet_ref, str) or not packet_ref:
        return "packet_ref must be a non-empty string"
    path = Path(packet_ref)
    if path.is_absolute() or ".." in path.parts:
        return "packet_ref must be a repository-local path"
    normalized = path.as_posix()
    if not normalized.startswith(ARCHIVE_PACKET_PREFIX):
        return f"packet_ref must start with {ARCHIVE_PACKET_PREFIX}"
    if not normalized.endswith((".yml", ".yaml", ".json")):
        return "packet_ref must point to a packet artifact file"
    return None


def archive_command_artifact_rel(packet: dict, *, index: int) -> str:
    packet_id = safe_artifact_stem(packet.get("meta", {}).get("packet_id", "packet"))
    suffix = "git-diff-check" if index == 0 else f"git-diff-check-{index + 1}"
    return f"{ARCHIVE_ARTIFACT_PREFIX}{packet_id}-{suffix}.log"


def command_evidence_artifact_text(
    packet: dict,
    *,
    packet_ref: str,
    packet_sha256: str,
    command: str,
    status: str,
) -> str:
    packet_id = str(packet.get("meta", {}).get("packet_id", ""))
    return "\n".join(
        [
            COMMAND_EVIDENCE_HEADING,
            f"packet_id: {packet_id}",
            f"packet_ref: {packet_ref}",
            f"packet_sha256: {packet_sha256}",
            f"command: {command}",
            f"status: {status}",
            "summary: finalized base-ref command evidence",
            "",
        ]
    )


def promote_archive_command_artifacts(packet: dict, *, packet_ref: str) -> dict[str, tuple[str, str]]:
    if pointer_packet_ref_error(packet_ref):
        return {}
    if packet.get("meta", {}).get("lifecycle") != "finalized" or packet.get("meta", {}).get("mode") != "base-ref":
        return {}
    result = packet.get("result", {}) if isinstance(packet.get("result"), dict) else {}
    decision = result.get("decision", {}) if isinstance(result, dict) else {}
    accepted = decision.get("accepted") is True
    evidence = result.get("evidence", {}) if isinstance(result.get("evidence"), dict) else {}
    command_results = evidence.get("command_results", [])
    if not isinstance(command_results, list):
        return {}

    updates: dict[str, tuple[str, str]] = {}
    resolved_refs = evidence.get("resolved_refs", [])
    if not isinstance(resolved_refs, list):
        resolved_refs = []
    terminal_refs: set[str] = set()
    for index, item in enumerate(command_results):
        if not isinstance(item, dict):
            continue
        artifact_ref = item.get("artifact_ref")
        command = item.get("command")
        status = item.get("status")
        if not isinstance(command, str) or not command:
            continue
        if not isinstance(status, str) or not status:
            continue
        if archive_replay_command_policy_error(command):
            continue
        if isinstance(artifact_ref, str) and artifact_ref.startswith("file:"):
            continue
        if not isinstance(artifact_ref, str) or not artifact_ref.startswith("terminal:"):
            continue
        artifact_rel = archive_command_artifact_rel(packet, index=index)
        generated_ref = f"file:{artifact_rel}"
        item["artifact_ref"] = generated_ref
        terminal_refs.add(artifact_ref)
        updates[artifact_rel] = (command, status)
        resolved_refs.append(
            {
                "origin": "generated",
                "relation": "artifact",
                "ref": generated_ref,
                "status": "resolved",
                "target": artifact_rel,
            }
        )
    if not updates:
        return {}
    evidence["resolved_refs"] = [
        record
        for record in resolved_refs
        if not (
            isinstance(record, dict)
            and record.get("relation") == "observation"
            and record.get("ref") in terminal_refs
        )
    ]
    if accepted:
        decision["stable_handoff_eligible"] = True
        decision["reason"] = "Required routine archive evidence passed."
        decision["next_action"] = "Publish active archive pointer."
    return updates


def file_ref_repo_path(root: Path, ref: object) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("file:"):
        return None
    rel = ref.removeprefix("file:").split("#", 1)[0]
    resolved = resolve_repo_path(root, rel)
    if resolved is None or not (root / resolved).is_file():
        return None
    return resolved


def review_import_probe_refs(root: Path, source_ref: str) -> list[str]:
    wrapper, _wrapper_errors = load_review_import_wrapper(root, source_ref)
    if wrapper is None:
        return []
    multi_review = wrapper.get("MultiReviewResult")
    critics = multi_review.get("critics", []) if isinstance(multi_review, dict) else []
    refs: list[str] = []
    if not isinstance(critics, list):
        return refs
    for critic in critics:
        if not isinstance(critic, dict):
            continue
        probe_refs = critic.get("probe_evidence_refs", [])
        if isinstance(probe_refs, list):
            refs.extend(ref for ref in probe_refs if isinstance(ref, str))
    return refs


def archive_artifact_paths(packet: dict, *, root: Path) -> list[str]:
    evidence = packet.get("result", {}).get("evidence", {})
    command_results = evidence.get("command_results", []) if isinstance(evidence, dict) else []
    paths: list[str] = []
    if isinstance(command_results, list):
        for item in command_results:
            if not isinstance(item, dict):
                continue
            artifact_path = file_ref_repo_path(root, item.get("artifact_ref"))
            if artifact_path is not None:
                paths.append(artifact_path)
    review_imports = evidence.get("review_imports", []) if isinstance(evidence, dict) else []
    if isinstance(review_imports, list):
        for item in review_imports:
            if not isinstance(item, dict):
                continue
            source_ref = item.get("source_ref")
            source_path = file_ref_repo_path(root, source_ref)
            if source_path is not None:
                paths.append(source_path)
            if isinstance(source_ref, str):
                for probe_ref in review_import_probe_refs(root, source_ref):
                    probe_path = file_ref_repo_path(root, probe_ref)
                    if probe_path is not None:
                        paths.append(probe_path)
    claims = evidence.get("claims", []) if isinstance(evidence, dict) else []
    if isinstance(claims, list):
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            raw_refs = claim.get("raw_evidence_refs", [])
            if not isinstance(raw_refs, list):
                continue
            for raw_ref in raw_refs:
                claim_path = file_ref_repo_path(root, raw_ref)
                if claim_path is not None and is_raw_claim_file_ref(root, raw_ref):
                    paths.append(claim_path)
    return sorted(set(paths))


def archive_commit_env(
    root: Path,
    *,
    index_path: Path | None = None,
    object_dir: Path | None = None,
) -> dict[str, str]:
    env = git_env()
    if index_path is not None:
        env["GIT_INDEX_FILE"] = str(index_path)
    if object_dir is not None:
        object_dir.mkdir(parents=True, exist_ok=True)
        env["GIT_OBJECT_DIRECTORY"] = str(object_dir)
        alternates: list[str] = []
        repo_objects = git_objects_dir(root)
        if repo_objects is not None:
            alternates.append(str(repo_objects.resolve()))
        if env.get("GIT_ALTERNATE_OBJECT_DIRECTORIES"):
            alternates.append(env["GIT_ALTERNATE_OBJECT_DIRECTORIES"])
        if alternates:
            env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = os.pathsep.join(alternates)
    env.update(
        {
            "GIT_AUTHOR_NAME": ARCHIVE_COMMIT_AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": ARCHIVE_COMMIT_AUTHOR_EMAIL,
            "GIT_AUTHOR_DATE": ARCHIVE_COMMIT_DATE,
            "GIT_COMMITTER_NAME": ARCHIVE_COMMIT_AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": ARCHIVE_COMMIT_AUTHOR_EMAIL,
            "GIT_COMMITTER_DATE": ARCHIVE_COMMIT_DATE,
        }
    )
    return env


def archive_parent_ref(packet: dict) -> str:
    accepted_head = packet.get("result", {}).get("evidence", {}).get("accepted_head_commit")
    return accepted_head if isinstance(accepted_head, str) and accepted_head else "HEAD"


def create_archive_commit(
    root: Path,
    packet: dict,
    *,
    packet_ref: str,
    parent_ref: str | None = None,
    materialize: bool = False,
) -> tuple[str | None, str | None]:
    parent_commit = git_ref_commit(root, parent_ref or archive_parent_ref(packet))
    if parent_commit is None:
        return None, "archive commit parent does not resolve to a commit"
    paths = [packet_ref, *archive_artifact_paths(packet, root=root)]
    if not paths:
        return None, "archive commit requires at least the packet path"
    with tempfile.TemporaryDirectory(prefix="acceptance-archive-objects.") as tmpdir:
        tmp_path = Path(tmpdir)
        object_dir = None if materialize else tmp_path / "objects"
        env = archive_commit_env(root, index_path=tmp_path / "index", object_dir=object_dir)
        read_tree = git_with_env(root, ["read-tree", parent_commit], env=env)
        if read_tree.returncode != 0:
            return None, read_tree.stderr.strip() or "failed to prepare archive commit index"
        for rel_path in paths:
            if Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
                return None, f"archive path must be repository-local: {rel_path}"
            path = root / rel_path
            if not path.is_file():
                return None, f"archive path does not exist: {rel_path}"
            blob = git_with_env(root, ["hash-object", "-w", rel_path], env=env)
            if blob.returncode != 0:
                return None, blob.stderr.strip() or f"failed to hash archive path: {rel_path}"
            update = git_with_env(root, ["update-index", "--add", "--cacheinfo", "100644", blob.stdout.strip(), rel_path], env=env)
            if update.returncode != 0:
                return None, update.stderr.strip() or f"failed to stage archive path in synthetic commit: {rel_path}"
        tree = git_with_env(root, ["write-tree"], env=env)
        if tree.returncode != 0:
            return None, tree.stderr.strip() or "failed to write archive commit tree"
        commit = git_with_env(
            root,
            [
                "commit-tree",
                tree.stdout.strip(),
                "-p",
                parent_commit,
                "-m",
                f"archive acceptance packet {packet.get('meta', {}).get('packet_id', '')}",
            ],
            env=env,
        )
        if commit.returncode != 0:
            return None, commit.stderr.strip() or "failed to create archive commit"
        return commit.stdout.strip(), None


def pointer_command_artifacts(packet: dict, *, root: Path) -> list[dict]:
    evidence = packet.get("result", {}).get("evidence", {})
    command_results = evidence.get("command_results", []) if isinstance(evidence, dict) else []
    artifacts: list[dict] = []
    if not isinstance(command_results, list):
        return artifacts
    for item in command_results:
        if not isinstance(item, dict):
            continue
        artifact_ref = item.get("artifact_ref")
        command = item.get("command")
        if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
            continue
        if not isinstance(command, str) or not command:
            continue
        path = local_ref_path(root, artifact_ref)
        artifacts.append(
            {
                "artifact_ref": artifact_ref,
                "artifact_sha256": file_sha256(path) if path else "",
                "command": command,
            }
        )
    return sorted(artifacts, key=lambda item: (item["artifact_ref"], item["command"]))


def pointer_claim_artifacts(packet: dict, *, root: Path) -> list[dict]:
    evidence = packet.get("result", {}).get("evidence", {})
    claims = evidence.get("claims", []) if isinstance(evidence, dict) else []
    artifacts: list[dict] = []
    if not isinstance(claims, list):
        return artifacts
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        raw_refs = claim.get("raw_evidence_refs", [])
        if not isinstance(raw_refs, list):
            continue
        for raw_ref in raw_refs:
            if not isinstance(raw_ref, str) or not raw_ref.startswith("file:"):
                continue
            if not is_raw_claim_file_ref(root, raw_ref):
                continue
            path = local_ref_path(root, raw_ref)
            artifacts.append(
                {
                    "source_ref": raw_ref,
                    "source_sha256": file_sha256(path) if path else "",
                }
            )
    return sorted(artifacts, key=lambda item: item["source_ref"])


def pointer_review_import_artifacts(packet: dict, *, root: Path) -> list[dict]:
    evidence = packet.get("result", {}).get("evidence", {})
    review_imports = evidence.get("review_imports", []) if isinstance(evidence, dict) else []
    artifacts: list[dict] = []
    if not isinstance(review_imports, list):
        return artifacts
    for item in review_imports:
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            continue
        path = local_ref_path(root, source_ref)
        binding = item.get("target_binding")
        review_ids = item.get("review_ids")
        artifacts.append(
            {
                "source_ref": source_ref,
                "source_sha256": file_sha256(path) if path else "",
                "review_target_digest": binding.get("review_target_digest", "") if isinstance(binding, dict) else "",
                "review_ids": sorted_string_values(review_ids),
            }
        )
    return sorted(artifacts, key=lambda item: item["source_ref"])


def pointer_probe_transcripts(packet: dict, *, root: Path) -> list[dict]:
    evidence = packet.get("result", {}).get("evidence", {})
    review_imports = evidence.get("review_imports", []) if isinstance(evidence, dict) else []
    transcripts: list[dict] = []
    if not isinstance(review_imports, list):
        return transcripts
    for import_record in review_imports:
        if not isinstance(import_record, dict):
            continue
        source_ref = import_record.get("source_ref")
        if not isinstance(source_ref, str):
            continue
        wrapper, _wrapper_errors = load_review_import_wrapper(root, source_ref)
        if wrapper is None:
            continue
        multi_review = wrapper.get("MultiReviewResult")
        critics = multi_review.get("critics", []) if isinstance(multi_review, dict) else []
        if not isinstance(critics, list):
            continue
        for critic in critics:
            if not isinstance(critic, dict):
                continue
            refs = critic.get("probe_evidence_refs", [])
            if not isinstance(refs, list):
                continue
            for probe_ref in refs:
                if not isinstance(probe_ref, str) or not probe_ref.startswith("file:"):
                    continue
                path = local_ref_path(root, probe_ref)
                transcript = load_probe_transcript(root, probe_ref) or {}
                transcripts.append(
                    {
                        "source_ref": probe_ref,
                        "transcript_sha256": file_sha256(path) if path else "",
                        "result_ref": transcript.get("result_ref", ""),
                        "result_digest": transcript.get("result_digest", ""),
                        "packet_ref": transcript.get("packet_ref", ""),
                        "packet_sha256": transcript.get("packet_sha256", ""),
                    }
                )
    return sorted(transcripts, key=lambda item: item["source_ref"])


def archive_tree_errors(
    pointer: dict,
    *,
    root: Path,
    packet_ref: str,
    commit_ref: object,
    label: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(commit_ref, str) or not FULL_COMMIT_RE.fullmatch(commit_ref):
        return [f"{label} must be the full commit SHA containing archived packet artifacts"]
    if not git_ref_is_commit(root, commit_ref):
        return [f"{label} must resolve to a git commit: {commit_ref}"]

    packet_sha = git_file_sha256(root, commit_ref, packet_ref)
    if packet_sha is None:
        errors.append(f"{label} does not contain packet_ref: {packet_ref}")
    elif packet_sha != pointer.get("packet_sha256"):
        errors.append(f"{label} packet bytes do not match pointer packet_sha256")

    command_artifacts = pointer.get("command_artifacts", [])
    if not isinstance(command_artifacts, list):
        command_artifacts = []
    for index, item in enumerate(command_artifacts):
        if not isinstance(item, dict):
            continue
        artifact_ref = item.get("artifact_ref")
        if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
            continue
        artifact_path = artifact_ref.removeprefix("file:")
        artifact_sha = git_file_sha256(root, commit_ref, artifact_path)
        if artifact_sha is None:
            errors.append(f"{label} does not contain command_artifacts[{index}].artifact_ref: {artifact_ref}")
        elif artifact_sha != item.get("artifact_sha256"):
            errors.append(f"{label} command_artifacts[{index}] bytes do not match artifact_sha256")

    claim_artifacts = pointer.get("claim_artifacts", [])
    if not isinstance(claim_artifacts, list):
        claim_artifacts = []
    for index, item in enumerate(claim_artifacts):
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        source_path = file_ref_repo_path(root, source_ref)
        if source_path is None:
            continue
        source_sha = git_file_sha256(root, commit_ref, source_path)
        if source_sha is None:
            errors.append(f"{label} does not contain claim_artifacts[{index}].source_ref: {source_ref}")
        elif source_sha != item.get("source_sha256"):
            errors.append(f"{label} claim_artifacts[{index}] bytes do not match source_sha256")

    review_import_artifacts = pointer.get("review_import_artifacts", [])
    if not isinstance(review_import_artifacts, list):
        review_import_artifacts = []
    for index, item in enumerate(review_import_artifacts):
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        source_path = file_ref_repo_path(root, source_ref)
        if source_path is None:
            continue
        source_sha = git_file_sha256(root, commit_ref, source_path)
        if source_sha is None:
            errors.append(f"{label} does not contain review_import_artifacts[{index}].source_ref: {source_ref}")
        elif source_sha != item.get("source_sha256"):
            errors.append(f"{label} review_import_artifacts[{index}] bytes do not match source_sha256")

    probe_transcripts = pointer.get("probe_transcripts", [])
    if not isinstance(probe_transcripts, list):
        probe_transcripts = []
    for index, item in enumerate(probe_transcripts):
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        source_path = file_ref_repo_path(root, source_ref)
        if source_path is None:
            continue
        transcript_sha = git_file_sha256(root, commit_ref, source_path)
        if transcript_sha is None:
            errors.append(f"{label} does not contain probe_transcripts[{index}].source_ref: {source_ref}")
        elif transcript_sha != item.get("transcript_sha256"):
            errors.append(f"{label} probe_transcripts[{index}] bytes do not match transcript_sha256")
    return errors


def archive_commit_tree_errors(
    pointer: dict,
    *,
    root: Path,
    packet_ref: str,
) -> list[str]:
    return archive_tree_errors(
        pointer,
        root=root,
        packet_ref=packet_ref,
        commit_ref=pointer.get("archive_commit"),
        label="archive_commit",
    )


def archive_file_ref_path(ref: object) -> str | None:
    if not isinstance(ref, str) or not ref.startswith("file:"):
        return None
    path = ref.removeprefix("file:").split("#", 1)[0]
    return path if path.startswith("archive/v2/") else None


def pointer_bound_archive_paths(pointer: dict) -> set[str]:
    paths: set[str] = set()

    def add_path(path: object) -> None:
        if isinstance(path, str) and path.startswith("archive/v2/"):
            paths.add(path)

    add_path(pointer.get("packet_ref"))
    for item in pointer.get("command_artifacts", []) if isinstance(pointer.get("command_artifacts"), list) else []:
        if isinstance(item, dict):
            add_path(archive_file_ref_path(item.get("artifact_ref")))
    for item in pointer.get("claim_artifacts", []) if isinstance(pointer.get("claim_artifacts"), list) else []:
        if isinstance(item, dict):
            add_path(archive_file_ref_path(item.get("source_ref")))
    for item in (
        pointer.get("review_import_artifacts", [])
        if isinstance(pointer.get("review_import_artifacts"), list)
        else []
    ):
        if isinstance(item, dict):
            add_path(archive_file_ref_path(item.get("source_ref")))
    for item in pointer.get("probe_transcripts", []) if isinstance(pointer.get("probe_transcripts"), list) else []:
        if isinstance(item, dict):
            add_path(archive_file_ref_path(item.get("source_ref")))
    return paths


def pointer_publication_paths(pointer: dict, *, pointer_ref: str | None) -> set[str]:
    paths = pointer_bound_archive_paths(pointer)
    if isinstance(pointer_ref, str) and pointer_ref.startswith("archive/v2/"):
        paths.add(pointer_ref)
    return paths


def packet_bound_archive_paths(packet: dict, *, root: Path, packet_ref: str) -> set[str]:
    return {packet_ref, *archive_artifact_paths(packet, root=root)}


def archive_pointer_ref_error(pointer_ref: object) -> str | None:
    if not isinstance(pointer_ref, str) or not pointer_ref:
        return "active pointer path must be repository-local under archive/v2/pointers/"
    if not pointer_ref.startswith(DEFAULT_POINTER_PREFIX):
        return f"active pointer path must be under {DEFAULT_POINTER_PREFIX}"
    if not pointer_ref.endswith(POINTER_SUFFIXES):
        return "active pointer path must end with .yml or .yaml"
    return None


def archive_pointer_output_error(output_ref: str, *, packet_ref: str, bound_paths: set[str]) -> str | None:
    if output_ref == packet_ref or output_ref.startswith(ARCHIVE_PACKET_PREFIX) or output_ref.startswith(ARCHIVE_ARTIFACT_PREFIX):
        return "write-pointer output must not overwrite archived packet or artifact paths"
    if output_ref in bound_paths:
        return "write-pointer output must not overwrite pointer-bound packet or artifact paths"
    return archive_pointer_ref_error(output_ref)


def archive_commit_scope_errors(pointer: dict, packet: dict, *, root: Path) -> list[str]:
    archive_commit = pointer.get("archive_commit")
    accepted_head = packet.get("result", {}).get("evidence", {}).get("accepted_head_commit")
    if not isinstance(archive_commit, str) or not isinstance(accepted_head, str):
        return []
    if not git_ref_is_commit(root, archive_commit) or not git_ref_is_commit(root, accepted_head):
        return []
    errors: list[str] = []
    if not git_is_ancestor(root, accepted_head, archive_commit):
        errors.append("archive_commit must be at or after accepted_head_commit")
    parents = git_commit_parents(root, archive_commit)
    if parents is None:
        errors.append("archive_commit parents could not be checked")
    elif parents != [accepted_head]:
        errors.append("archive_commit must have accepted_head_commit as its only parent")
    records = git_diff_name_status_records(root, accepted_head, archive_commit)
    if records is None:
        errors.append("archive_commit scope could not be compared to accepted_head_commit")
        return errors
    errors.extend(
        archive_v2_diff_errors(
            records,
            expected_paths=pointer_bound_archive_paths(pointer),
            label="archive_commit",
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
    return errors


def active_pointer_dirty_worktree_errors(
    root: Path,
    *,
    allowed_archive_paths: set[str],
    allowed_modified_start_packet: tuple[Path, str, str, dict] | None = None,
    ignore_non_archive_dirty: bool = False,
) -> list[str]:
    result = git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if result.returncode != 0:
        return ["active pointer worktree status could not be checked"]
    non_publication_paths: set[str] = set()
    invalid_publication_records: list[str] = []
    for status, paths in porcelain_status_records(result.stdout):
        unexpected_archive_paths = [
            path for path in paths if path.startswith("archive/v2/") and path not in allowed_archive_paths
        ]
        if unexpected_archive_paths:
            non_publication_paths.update(unexpected_archive_paths)
            continue
        if any(not path.startswith("archive/v2/") for path in paths):
            if not ignore_non_archive_dirty:
                non_publication_paths.update(paths)
            continue
        if status in {"??", "A "}:
            continue
        if allowed_modified_start_packet is not None:
            draft_root, accepted_head, packet_ref, packet = allowed_modified_start_packet
            if (
                "M" in status
                and paths == [packet_ref]
                and accepted_archive_packet_is_start_draft(draft_root, accepted_head, packet_ref, packet)
            ):
                continue
        invalid_publication_records.append(f"{status} {paths}")
    errors: list[str] = []
    if non_publication_paths:
        errors.append(f"active pointer worktree includes non-publication changes: {sorted(non_publication_paths)}")
    if invalid_publication_records:
        errors.append(
            "active pointer worktree may only add publication paths or modify the current start-draft packet: "
            f"{invalid_publication_records}"
        )
    return errors


def accepted_archive_packet_is_start_draft(root: Path, accepted_head: str, packet_ref: str, packet: dict) -> bool:
    text = git_text(root, accepted_head, packet_ref)
    if text is None:
        return False
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        return False
    draft = loaded.get(PACKET_KEY) if isinstance(loaded, dict) else None
    if not isinstance(draft, dict):
        return False
    draft_meta = draft.get("meta", {}) if isinstance(draft.get("meta"), dict) else {}
    packet_meta = packet.get("meta", {}) if isinstance(packet.get("meta"), dict) else {}
    draft_evidence = draft.get("result", {}).get("evidence", {}) if isinstance(draft.get("result"), dict) else {}
    packet_evidence = packet.get("result", {}).get("evidence", {}) if isinstance(packet.get("result"), dict) else {}
    return (
        draft_meta.get("packet_id") == packet_meta.get("packet_id")
        and draft_meta.get("schema_version") == packet_meta.get("schema_version")
        and draft_meta.get("lifecycle") == "start"
        and packet_meta.get("lifecycle") == "finalized"
        and draft_meta.get("mode") == packet_meta.get("mode")
        and draft_evidence.get("baseline_ref") == packet_evidence.get("baseline_ref")
    )


def archive_v2_diff_errors(
    records: list[tuple[str, list[str]]],
    *,
    expected_paths: set[str],
    label: str,
    allowed_modified_start_packet: tuple[Path, str, str, dict] | None = None,
) -> list[str]:
    errors: list[str] = []
    changed_paths = {path for _status, paths in records for path in paths}
    non_archive_paths = sorted(path for path in changed_paths if not path.startswith("archive/v2/"))
    if non_archive_paths:
        errors.append(f"{label} includes non-archive changes: {non_archive_paths}")
    unexpected_archive_paths = sorted(
        path for path in changed_paths if path.startswith("archive/v2/") and path not in expected_paths
    )
    if unexpected_archive_paths:
        errors.append(f"{label} includes unexpected archive/v2 paths: {unexpected_archive_paths}")
    for status, paths in records:
        if not any(path.startswith("archive/v2/") for path in paths):
            continue
        if status == "A":
            continue
        if allowed_modified_start_packet is not None:
            root, accepted_head, packet_ref, packet = allowed_modified_start_packet
            if (
                status == "M"
                and paths == [packet_ref]
                and accepted_archive_packet_is_start_draft(root, accepted_head, packet_ref, packet)
            ):
                continue
        errors.append(f"{label} may only add expected archive/v2 paths: {status} {paths}")
    return errors


def accepted_head_archive_scope_errors(
    root: Path,
    packet: dict,
    *,
    packet_ref: str | None,
    comparison_ref: str,
    accepted_head: str,
) -> list[str]:
    if not isinstance(packet_ref, str):
        return []
    errors: list[str] = []
    records = git_diff_name_status_records_for_spec(root, f"{comparison_ref}...{accepted_head}")
    if records is None:
        errors.append("active base-ref accepted_head archive scope could not be compared to comparison_ref")
        return errors
    archive_records = [
        (status, paths)
        for status, paths in records
        if any(path.startswith("archive/v2/") for path in paths)
    ]
    if not archive_records:
        return errors
    expected_paths = (
        {packet_ref}
        if accepted_archive_packet_is_start_draft(root, accepted_head, packet_ref, packet)
        else set()
    )
    changed_paths = {path for _status, paths in archive_records for path in paths}
    unexpected_archive_paths = sorted(path for path in changed_paths if path not in expected_paths)
    if unexpected_archive_paths:
        errors.append(f"active base-ref accepted_head includes unexpected archive/v2 paths: {unexpected_archive_paths}")
    for status, paths in archive_records:
        if status in {"A", "M"} and paths == [packet_ref] and packet_ref in expected_paths:
            continue
        errors.append(f"active base-ref accepted_head may only carry the current start-draft packet: {status} {paths}")
    return errors


def publication_commit_errors(
    root: Path,
    accepted_head: str,
    publication_commit: str,
    *,
    pointer: dict,
    packet: dict,
    pointer_ref: str | None,
    label: str,
) -> list[str]:
    parents = git_commit_parents(root, publication_commit)
    if parents is None:
        return [f"{label} parents could not be read: {publication_commit}"]
    baseline = parents[0] if parents else accepted_head
    records = git_diff_name_status_records(root, baseline, publication_commit)
    if records is None:
        return [f"{label} scope could not be compared to its parent"]
    if not records:
        return ["head_commit does not match current HEAD or first archive/v2 publication commit"]
    expected_paths = pointer_publication_paths(pointer, pointer_ref=pointer_ref)
    errors = archive_v2_diff_errors(
        records,
        expected_paths=expected_paths,
        label=label,
        allowed_modified_start_packet=(
            root,
            accepted_head,
            pointer["packet_ref"],
            packet,
        )
        if isinstance(pointer.get("packet_ref"), str)
        else None,
    )
    changed_paths = {path for _status, paths in records for path in paths}
    if pointer_ref is None:
        errors.append(f"{label} requires a repository-local pointer path")
    elif pointer_ref not in changed_paths:
        errors.append(f"{label} must add the active pointer path: {pointer_ref}")
    packet_ref = pointer.get("packet_ref")
    if isinstance(packet_ref, str):
        errors.extend(
            archive_tree_errors(
                pointer,
                root=root,
                packet_ref=packet_ref,
                commit_ref=publication_commit,
                label=label,
            )
        )
    return errors


def commit_archive_v2_paths(root: Path, commit: str) -> list[str] | None:
    parents = git_commit_parents(root, commit)
    if parents is None:
        return None
    baseline = parents[0] if parents else f"{commit}^"
    records = git_diff_name_status_records(root, baseline, commit)
    if records is None:
        return None
    return sorted(
        {
            path
            for _status, paths in records
            for path in paths
            if path.startswith("archive/v2/")
        }
    )


def post_publication_archive_history_errors(
    root: Path,
    publication_commit: str,
    current_head: str,
    *,
    protected_paths: set[str],
) -> list[str]:
    commits = git_rev_list_between(root, publication_commit, current_head)
    if commits is None:
        return ["current HEAD post-publication history could not be compared to active pointer publication"]
    errors: list[str] = []
    for commit in commits:
        parents = git_commit_parents(root, commit)
        if parents is None:
            errors.append(f"post-publication commit parents could not be read: {commit}")
            continue
        baseline = parents[0] if parents else f"{commit}^"
        records = git_diff_name_status_records(root, baseline, commit)
        if records is None:
            errors.append(f"post-publication commit scope could not be compared: {commit}")
            continue
        touched_protected_paths = sorted(
            {
                path
                for _status, paths in records
                for path in paths
                if path in protected_paths
            }
        )
        if touched_protected_paths:
            errors.append(
                "current HEAD history includes archive/v2 changes after active pointer publication "
                f"to pointer-bound bytes: {commit} {touched_protected_paths}"
            )
    return errors


def current_head_publication_errors(
    root: Path,
    accepted_head: str,
    *,
    pointer: dict,
    packet: dict,
    pointer_ref: str | None,
    ignore_non_archive_dirty: bool = False,
) -> list[str]:
    current_head = git_ref_commit(root, "HEAD")
    if current_head is None:
        return ["head_commit cannot be checked because HEAD does not resolve"]
    if current_head == accepted_head:
        return active_pointer_dirty_worktree_errors(
            root,
            allowed_archive_paths=pointer_publication_paths(pointer, pointer_ref=pointer_ref),
            ignore_non_archive_dirty=ignore_non_archive_dirty,
            allowed_modified_start_packet=(
                root,
                accepted_head,
                pointer["packet_ref"],
                packet,
            )
            if isinstance(pointer.get("packet_ref"), str)
            else None,
        )
    if not git_is_ancestor(root, accepted_head, current_head):
        return ["head_commit does not match current HEAD or first archive/v2 publication commit"]
    commits = git_rev_list_between(root, accepted_head, current_head)
    if commits is None:
        return ["current HEAD history could not be compared to accepted_head_commit"]
    if not commits:
        return ["head_commit does not match current HEAD or first archive/v2 publication commit"]
    publication_commit: str | None = None
    for commit in commits:
        archive_paths = commit_archive_v2_paths(root, commit)
        if archive_paths is None:
            return [f"current HEAD commit scope could not be compared: {commit}"]
        if archive_paths:
            publication_commit = commit
            break
    if publication_commit is None:
        return ["head_commit does not match current HEAD or first archive/v2 publication commit"]
    label = "current HEAD publication" if publication_commit == current_head else "historical pointer publication"
    errors = publication_commit_errors(
        root,
        accepted_head,
        publication_commit,
        pointer=pointer,
        packet=packet,
        pointer_ref=pointer_ref,
        label=label,
    )
    if errors:
        return errors
    errors.extend(
        post_publication_archive_history_errors(
            root,
            publication_commit,
            current_head,
            protected_paths=pointer_publication_paths(pointer, pointer_ref=pointer_ref),
        )
    )
    errors.extend(
        active_pointer_dirty_worktree_errors(
            root,
            allowed_archive_paths=set(),
            ignore_non_archive_dirty=True,
        )
    )
    return errors


def pointer_for_packet(
    packet: dict,
    *,
    root: Path,
    packet_ref: str,
    packet_sha256: str,
    archive_commit: str,
) -> dict:
    evidence = packet["result"]["evidence"]
    head_commit = evidence.get("accepted_head_commit") or git_ref_commit(root, "HEAD") or ""
    return {
        "schema_version": POINTER_SCHEMA_VERSION,
        "packet_id": packet["meta"]["packet_id"],
        "packet_ref": packet_ref,
        "packet_sha256": packet_sha256,
        "checker_version": SCHEMA_VERSION,
        "inference_rule_version": INFERENCE_RULE_VERSION,
        "baseline_ref": evidence.get("baseline_ref"),
        "comparison_ref": evidence.get("comparison_ref"),
        "head_commit": head_commit,
        "archive_commit": archive_commit,
        "stable_target": stable_target_for_packet(packet),
        "decision_status": decision_status_for_packet(packet),
        "command_artifacts": pointer_command_artifacts(packet, root=root),
        "claim_artifacts": pointer_claim_artifacts(packet, root=root),
        "review_import_artifacts": pointer_review_import_artifacts(packet, root=root),
        "probe_transcripts": pointer_probe_transcripts(packet, root=root),
    }


def validate_pointer_claim_artifacts(
    pointer: dict,
    packet: dict,
    *,
    root: Path,
    errors: list[str],
) -> None:
    claim_artifacts = pointer.get("claim_artifacts", [])
    expected = pointer_claim_artifacts(packet, root=root)
    if "claim_artifacts" not in pointer:
        if expected:
            errors.append("claim_artifacts must mirror archived packet claim evidence artifact bytes")
        return
    if not isinstance(claim_artifacts, list):
        errors.append("claim_artifacts must be a list")
        return
    for index, item in enumerate(claim_artifacts):
        source = f"claim_artifacts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{source} must be a mapping")
            continue
        errors.extend(schema_field_errors(item, POINTER_CLAIM_ARTIFACT_FIELDS, source=source, label="claim artifact"))
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            errors.append(f"{source}.source_ref must use file: scheme")
        elif file_ref_repo_path(root, source_ref) is None:
            errors.append(f"{source}.source_ref does not resolve to an archive path: {source_ref}")
        source_sha256 = item.get("source_sha256")
        if not isinstance(source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            errors.append(f"{source}.source_sha256 must be a SHA-256 hex digest")
    if normalize_for_mirror(claim_artifacts) != normalize_for_mirror(expected):
        errors.append("claim_artifacts do not match archived packet claim evidence artifact bytes")


def validate_pointer_review_import_artifacts(
    pointer: dict,
    packet: dict,
    *,
    root: Path,
    errors: list[str],
) -> None:
    review_import_artifacts = pointer.get("review_import_artifacts")
    if not isinstance(review_import_artifacts, list):
        errors.append("review_import_artifacts must be a list")
        return
    for index, item in enumerate(review_import_artifacts):
        source = f"review_import_artifacts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{source} must be a mapping")
            continue
        errors.extend(
            schema_field_errors(
                item,
                POINTER_REVIEW_IMPORT_ARTIFACT_FIELDS,
                source=source,
                label="review import artifact",
            )
        )
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            errors.append(f"{source}.source_ref must use file: scheme")
        elif local_ref_path(root, source_ref) is None:
            errors.append(f"{source}.source_ref does not resolve: {source_ref}")
        source_sha256 = item.get("source_sha256")
        if not isinstance(source_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            errors.append(f"{source}.source_sha256 must be a SHA-256 hex digest")
        review_target_digest = item.get("review_target_digest")
        if not isinstance(review_target_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", review_target_digest):
            errors.append(f"{source}.review_target_digest must be a SHA-256 hex digest")
        if not isinstance(item.get("review_ids"), list) or any(not isinstance(review_id, str) for review_id in item.get("review_ids", [])):
            errors.append(f"{source}.review_ids must be a list of strings")
    expected = pointer_review_import_artifacts(packet, root=root)
    if normalize_for_mirror(review_import_artifacts) != normalize_for_mirror(expected):
        errors.append("review_import_artifacts do not match archived packet review import artifact bytes")


def validate_pointer_probe_transcripts(
    pointer: dict,
    packet: dict,
    *,
    root: Path,
    errors: list[str],
) -> None:
    probe_transcripts = pointer.get("probe_transcripts")
    if not isinstance(probe_transcripts, list):
        errors.append("probe_transcripts must be a list")
        return
    pointer_packet_ref = pointer.get("packet_ref")
    pointer_packet_sha256 = pointer.get("packet_sha256")
    for index, item in enumerate(probe_transcripts):
        source = f"probe_transcripts[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{source} must be a mapping")
            continue
        errors.extend(
            schema_field_errors(
                item,
                POINTER_PROBE_TRANSCRIPT_FIELDS,
                source=source,
                label="probe transcript",
            )
        )
        source_ref = item.get("source_ref")
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            errors.append(f"{source}.source_ref must use file: scheme")
        elif local_ref_path(root, source_ref) is None:
            errors.append(f"{source}.source_ref does not resolve: {source_ref}")
        transcript_sha256 = item.get("transcript_sha256")
        if not isinstance(transcript_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", transcript_sha256):
            errors.append(f"{source}.transcript_sha256 must be a SHA-256 hex digest")
        result_ref = item.get("result_ref")
        if not review_value_is_substantive_string(result_ref):
            errors.append(f"{source}.result_ref must be a substantive string")
        result_digest = item.get("result_digest")
        if not isinstance(result_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", result_digest):
            errors.append(f"{source}.result_digest must be a SHA-256 hex digest")
        if item.get("packet_ref") != pointer_packet_ref:
            errors.append(f"{source}.packet_ref must match active pointer packet_ref")
        if item.get("packet_sha256") != pointer_packet_sha256:
            errors.append(f"{source}.packet_sha256 must match active pointer packet_sha256")
    expected = pointer_probe_transcripts(packet, root=root)
    if normalize_for_mirror(probe_transcripts) != normalize_for_mirror(expected):
        errors.append("probe_transcripts do not match archived packet probe transcript bytes")


def validate_pointer(
    pointer: dict,
    *,
    root: Path,
    pointer_ref: str | None = None,
    replay_archive_command_evidence: bool = False,
    check_publication_scope: bool = True,
    ignore_non_archive_dirty: bool = False,
) -> list[str]:
    errors: list[str] = []
    pointer_fields = set(pointer)
    if pointer_fields != POINTER_FIELDS and pointer_fields != LEGACY_POINTER_FIELDS:
        errors.append(f"{POINTER_KEY} fields must be exactly {sorted(POINTER_FIELDS)}")
        return errors
    pointer_path_error = archive_pointer_ref_error(pointer_ref)
    if pointer_path_error:
        errors.append(pointer_path_error)
    if pointer.get("schema_version") != POINTER_SCHEMA_VERSION:
        errors.append(f"schema_version must be {POINTER_SCHEMA_VERSION}")
    packet_ref_error = pointer_packet_ref_error(pointer.get("packet_ref"))
    if packet_ref_error:
        errors.append(packet_ref_error)
        return errors
    packet_ref = pointer["packet_ref"]
    packet_rel = resolve_repo_path(root, packet_ref)
    if packet_rel is None:
        errors.append(f"packet_ref does not resolve to an archived packet: {packet_ref}")
        return errors
    packet_path = root / packet_rel
    actual_sha256 = file_sha256(packet_path)
    if pointer.get("packet_sha256") != actual_sha256:
        errors.append("packet_sha256 does not match archived packet bytes")
    try:
        packet = load_packet(packet_path)
    except PacketError as exc:
        errors.append(str(exc))
        return errors

    if pointer.get("packet_id") != packet.get("meta", {}).get("packet_id"):
        errors.append("packet_id does not match archived packet meta.packet_id")
    if pointer.get("checker_version") != SCHEMA_VERSION:
        errors.append(f"checker_version must be {SCHEMA_VERSION}")
    if pointer.get("inference_rule_version") != INFERENCE_RULE_VERSION:
        errors.append(f"inference_rule_version must be {INFERENCE_RULE_VERSION}")

    result = packet.get("result", {}) if isinstance(packet.get("result"), dict) else {}
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    if pointer.get("baseline_ref") != evidence.get("baseline_ref"):
        errors.append("baseline_ref does not match archived packet evidence.baseline_ref")
    if pointer.get("comparison_ref") != evidence.get("comparison_ref"):
        errors.append("comparison_ref does not match archived packet evidence.comparison_ref")
    head_commit = pointer.get("head_commit")
    accepted_head_commit = evidence.get("accepted_head_commit")
    publication_commit: str | None = None
    if not isinstance(head_commit, str) or not FULL_COMMIT_RE.fullmatch(head_commit):
        errors.append("head_commit must be the full accepted_head_commit SHA")
    else:
        if not isinstance(accepted_head_commit, str) or not FULL_COMMIT_RE.fullmatch(accepted_head_commit):
            errors.append("archived packet accepted_head_commit must be a full commit SHA")
        elif head_commit != accepted_head_commit:
            errors.append("head_commit does not match archived packet accepted_head_commit")
        elif check_publication_scope:
            publication_errors = current_head_publication_errors(
                root,
                accepted_head_commit,
                pointer=pointer,
                packet=packet,
                pointer_ref=pointer_ref,
                ignore_non_archive_dirty=ignore_non_archive_dirty,
            )
            errors.extend(publication_errors)
            current_head = git_ref_commit(root, "HEAD")
            commit_count = (
                git_commit_count_between(root, accepted_head_commit, current_head)
                if not publication_errors and isinstance(current_head, str) and current_head != accepted_head_commit
                else None
            )
            if commit_count == 1:
                publication_commit = current_head
    archive_commit = pointer.get("archive_commit")
    if not isinstance(archive_commit, str) or not FULL_COMMIT_RE.fullmatch(archive_commit):
        errors.append("archive_commit must be the full commit SHA containing archived packet artifacts")
    else:
        expected_archive_commit, archive_commit_error = create_archive_commit(
            root,
            packet,
            packet_ref=packet_ref,
            parent_ref=accepted_head_commit if isinstance(accepted_head_commit, str) else None,
        )
        if archive_commit_error:
            errors.append(f"archive_commit could not be reproduced from pointer-bound bytes: {archive_commit_error}")
        elif archive_commit != expected_archive_commit:
            errors.append("archive_commit does not match reproducible pointer-bound archive bytes")
        if publication_commit is not None:
            errors.extend(
                archive_tree_errors(
                    pointer,
                    root=root,
                    packet_ref=packet_ref,
                    commit_ref=publication_commit,
                    label="publication commit",
                )
            )
        elif git_ref_is_commit(root, archive_commit):
            errors.extend(archive_commit_tree_errors(pointer, root=root, packet_ref=packet_ref))
            errors.extend(archive_commit_scope_errors(pointer, packet, root=root))
    expected_stable_target = stable_target_for_packet(packet)
    if pointer.get("stable_target") != expected_stable_target:
        errors.append(f"stable_target must be {expected_stable_target}")
    expected_decision_status = decision_status_for_packet(packet)
    if pointer.get("decision_status") != expected_decision_status:
        errors.append(f"decision_status must match archived packet decision status: {expected_decision_status}")
    if pointer.get("decision_status") != "accepted":
        errors.append("active pointer decision_status must be accepted")
    if packet.get("meta", {}).get("lifecycle") != "finalized":
        errors.append("active pointer packet must have finalized lifecycle")
    if packet.get("meta", {}).get("mode") != "base-ref":
        errors.append("active pointer packet must use base-ref mode")
    command_artifacts = pointer.get("command_artifacts")
    if not isinstance(command_artifacts, list):
        errors.append("command_artifacts must be a list")
    else:
        for index, item in enumerate(command_artifacts):
            source = f"command_artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{source} must be a mapping")
                continue
            errors.extend(schema_field_errors(item, POINTER_COMMAND_ARTIFACT_FIELDS, source=source, label="command artifact"))
            artifact_ref = item.get("artifact_ref")
            artifact_sha256 = item.get("artifact_sha256")
            if not isinstance(artifact_ref, str) or not artifact_ref.startswith("file:"):
                errors.append(f"{source}.artifact_ref must use file: scheme")
            elif local_ref_path(root, artifact_ref) is None:
                errors.append(f"{source}.artifact_ref does not resolve: {artifact_ref}")
            if not isinstance(artifact_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
                errors.append(f"{source}.artifact_sha256 must be a SHA-256 hex digest")
            if not review_value_is_substantive_string(item.get("command")):
                errors.append(f"{source}.command must be a substantive string")
        expected_artifacts = pointer_command_artifacts(packet, root=root)
        if normalize_for_mirror(command_artifacts) != normalize_for_mirror(expected_artifacts):
            errors.append("command_artifacts do not match archived packet command artifact bytes")
    validate_pointer_claim_artifacts(pointer, packet, root=root, errors=errors)
    validate_pointer_review_import_artifacts(pointer, packet, root=root, errors=errors)
    validate_pointer_probe_transcripts(pointer, packet, root=root, errors=errors)

    pointer_sha = pointer.get("packet_sha256")
    packet_errors = validate_packet(
        packet,
        require_stable=True,
        require_archive_command_replay_metadata=True,
        replay_archive_command_evidence=False,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=pointer_sha if isinstance(pointer_sha, str) else None,
    )
    errors.extend(f"archived packet: {error}" for error in packet_errors)
    if errors:
        return errors
    if replay_archive_command_evidence:
        with archive_command_replay_root(root, packet) as (replay_root, replay_root_errors):
            replay_errors = list(replay_root_errors)
            if not replay_errors:
                replay_errors = validate_packet(
                    packet,
                    require_stable=True,
                    require_archive_command_replay_metadata=True,
                    replay_archive_command_evidence=True,
                    root=root,
                    replay_root=replay_root,
                    packet_ref=packet_ref,
                    packet_sha256=pointer_sha if isinstance(pointer_sha, str) else None,
                )
        errors.extend(f"archived packet: {error}" for error in replay_errors)
    return errors


def mode_from_args(args: argparse.Namespace) -> tuple[str, str | None]:
    selected = [name for name in ("staged", "worktree", "base_ref") if getattr(args, name, None)]
    if len(selected) != 1:
        raise PacketError("select exactly one mode: --staged, --worktree, or --base-ref <ref>")
    if selected[0] == "base_ref":
        return "base-ref", args.base_ref
    return selected[0], None


def normalize_base_ref(root: Path, base_ref: str | None) -> str | None:
    if base_ref is None:
        return None
    commit = git_ref_commit(root, base_ref)
    if commit is None:
        raise PacketError(f"base-ref must resolve to a git commit: {base_ref}")
    return commit


def changed_paths(root: Path, *, mode: str, base_ref: str | None) -> list[str]:
    if mode == "staged":
        result = git(root, ["diff", "--cached", "--name-status"], keep_index=True)
    elif mode == "base-ref":
        result = git(root, ["diff", "--name-status", f"{base_ref}...HEAD"])
    else:
        result = git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
        if result.returncode == 0:
            return porcelain_status_paths(result.stdout)
    if result.returncode != 0:
        raise PacketError(result.stderr.strip() or "failed to read git changes")
    paths = name_status_changed_paths(result.stdout)
    if mode == "base-ref":
        paths = [path for path in paths if not path.startswith("archive/v2/")]
    return paths


def packet_ref_is_repo_local(packet_ref: str | None) -> bool:
    return bool(packet_ref) and not Path(str(packet_ref)).is_absolute()


def packet_ref_is_fixture(packet_ref: str | None) -> bool:
    if not packet_ref:
        return False
    path = Path(str(packet_ref))
    return not path.is_absolute() and path.as_posix() in CANONICAL_ACCEPTANCE_PACKET_FIXTURES


def packet_ref_is_fixture_materialization(root: Path, packet_ref: str | None) -> bool:
    if os.environ.get(FIXTURE_MATERIALIZATION_ENV) != "1" or not packet_ref:
        return False
    path = Path(str(packet_ref))
    fixture_root = Path("backlog/fixtures/acceptance-packets")
    if path.is_absolute() or fixture_root not in (path, *path.parents):
        return False
    marker = root / path.parent / FIXTURE_MATERIALIZATION_MARKER
    try:
        return marker.read_text(encoding="utf-8").strip() == "acceptance-packet-fixture-materialization/v1"
    except OSError:
        return False


def packet_has_fixture_binding(packet: dict) -> bool:
    review_imports = packet.get("result", {}).get("evidence", {}).get("review_imports", [])
    if not isinstance(review_imports, list):
        return False
    for item in review_imports:
        if not isinstance(item, dict):
            continue
        binding = item.get("target_binding")
        if isinstance(binding, dict) and packet_ref_is_fixture(binding.get("packet_ref")):
            return True
    return False


def packet_has_materialized_fixture_binding(packet: dict, packet_ref: str | None, *, root: Path) -> bool:
    if not packet_ref_is_fixture_materialization(root, packet_ref):
        return False
    path = Path(str(packet_ref))
    packet_rel = path.as_posix()
    materialization_dir = path.parent.as_posix()
    review_imports = packet.get("result", {}).get("evidence", {}).get("review_imports", [])
    if not isinstance(review_imports, list):
        return False
    for item in review_imports:
        if not isinstance(item, dict):
            continue
        binding = item.get("target_binding")
        source_ref = item.get("source_ref")
        if not isinstance(binding, dict) or binding.get("packet_ref") != packet_rel:
            continue
        if not isinstance(source_ref, str) or not source_ref.startswith("file:"):
            continue
        source_path = source_ref.removeprefix("file:")
        if source_path == materialization_dir or source_path.startswith(f"{materialization_dir}/"):
            return True
    return False


def packet_is_active_handoff(packet: dict, packet_ref: str | None, *, root: Path) -> bool:
    return (
        not packet_ref_is_fixture(packet_ref)
        and not packet_has_materialized_fixture_binding(packet, packet_ref, root=root)
        and not packet_has_fixture_binding(packet)
    )



def is_protected(path: str) -> bool:
    return path in PROTECTED_PATHS or any(
        path == prefix.rstrip("/") or path.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def requires_review_for_path(path: str) -> bool:
    return is_protected(path)


def path_has_proof_like_claim(root: Path, path: str) -> bool:
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(PROOF_LIKE_RE.search(text))


def terminal_ref_for_command(command: str, *, index: int) -> str:
    if command.startswith("git diff"):
        return "terminal:git-diff-check"
    return f"terminal:required-evidence-{index + 1}"


def command_result_status_for_finalize(
    root: Path,
    command: str,
    *,
    cached_statuses: dict[str, str],
    replay_root_errors: list[str],
) -> str:
    if command in cached_statuses:
        return cached_statuses[command]
    if replay_root_errors:
        return "fail"
    policy_error = archive_replay_command_policy_error(command)
    if policy_error:
        return "fail"
    completed, error = run_archive_command(command, root=root)
    if error:
        return "fail"
    assert completed is not None
    return "pass" if completed.returncode == 0 else "fail"


def finalize_required_evidence_commands(
    root: Path,
    packet: dict,
    *,
    cached_statuses: dict[str, str],
) -> None:
    required = sorted(checker_required_evidence(packet))
    packet["result"]["inference"]["required_evidence"] = required
    evaluator_boundary = packet["result"]["evidence"].setdefault("evaluator_boundary", {})
    if isinstance(evaluator_boundary, dict):
        evaluator_boundary["commands"] = required
    command_results: list[dict[str, str]] = []
    resolved_refs = packet["result"]["evidence"].setdefault("resolved_refs", [])
    if not isinstance(resolved_refs, list):
        resolved_refs = []
        packet["result"]["evidence"]["resolved_refs"] = resolved_refs
    with archive_command_replay_root(root, packet) as (replay_root, replay_root_errors):
        for index, command in enumerate(required):
            terminal_ref = terminal_ref_for_command(command, index=index)
            command_results.append(
                {
                    "command": command,
                    "status": command_result_status_for_finalize(
                        replay_root,
                        command,
                        cached_statuses=cached_statuses,
                        replay_root_errors=replay_root_errors,
                    ),
                    "artifact_ref": terminal_ref,
                }
            )
            resolved_refs.append(
                {
                    "origin": "generated",
                    "relation": "observation",
                    "ref": terminal_ref,
                    "status": "local-placeholder",
                    "target": terminal_ref,
                }
            )
    packet["result"]["evidence"]["command_results"] = command_results


def infer_packet_result(
    root: Path,
    packet: dict,
    *,
    mode: str,
    base_ref: str | None,
    search_set_before: str | None = None,
    search_set_after: str | None = None,
) -> dict:
    paths = changed_paths(root, mode=mode, base_ref=base_ref)
    baseline_ref = base_ref if mode == "base-ref" else packet["result"].get("evidence", {}).get("baseline_ref")
    comparison_ref = base_ref if mode == "base-ref" else baseline_ref
    accepted_head_commit = git_ref_commit(root, "HEAD") if mode == "base-ref" else None
    protected = any(is_protected(path) for path in paths)
    if mode == "base-ref":
        proof_like = any(
            path.endswith(".md")
            and (
                path_has_proof_like_claim_at_commit(root, str(base_ref), path)
                or path_has_proof_like_claim_at_commit(root, str(accepted_head_commit or "HEAD"), path)
            )
            for path in paths
        )
    else:
        proof_like = any(path.endswith(".md") and path_has_proof_like_claim(root, path) for path in paths)
    high_risk = protected or proof_like
    change_class = "harness-affecting" if protected else "routine"
    if mode == "staged":
        diff_command = ["git", "diff", "--cached", "--check"]
        evidence_command = "git diff --cached --check"
    elif mode == "base-ref":
        diff_command = ["git", "diff", "--check", f"{base_ref}...{accepted_head_commit or 'HEAD'}"]
        evidence_command = f"git diff --check {base_ref}...{accepted_head_commit or 'HEAD'}"
    else:
        diff_command = ["git", "diff", "--check"]
        evidence_command = "git diff --check"
    diff_check = git(root, diff_command[1:], keep_index=(mode == "staged"))
    diff_status = "pass" if diff_check.returncode == 0 else "fail"
    resolved_refs = []
    input_source_refs = list(packet["input"].get("source_refs", []))
    if mode == "base-ref" and not high_risk:
        packet["input"]["source_refs"] = []
        input_source_refs = []
    source_refs = list(input_source_refs)
    generated_source_refs = (
        generated_base_ref_source_refs(root, paths, base_ref, head_ref=accepted_head_commit or "HEAD")
        if mode == "base-ref"
        else []
    )
    for ref, resolved in generated_source_refs:
        if ref not in source_refs:
            source_refs.append(ref)
            resolved_refs.append(
                {
                    "origin": "generated",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": resolved,
                }
            )
    for ref in input_source_refs:
        resolved = resolve_ref(root, ref)
        if resolved:
            resolved_refs.append(
                {
                    "origin": "input",
                    "relation": "source",
                    "ref": ref,
                    "status": "resolved",
                    "target": resolved,
                }
            )
    cached_statuses = {evidence_command: diff_status}
    search_set_trace_refs = {
        "search_set_before": search_set_before,
        "search_set_after": search_set_after,
    }
    for trace_name, trace_ref in search_set_trace_refs.items():
        if not trace_ref:
            continue
        resolved = resolve_ref(root, trace_ref)
        if resolved:
            resolved_refs.append(
                {
                    "origin": "generated",
                    "relation": "trace",
                    "ref": trace_ref,
                    "status": "resolved",
                    "target": resolved,
                }
            )

    skipped_evidence: list[dict] = []
    if protected:
        skip_source_ref = "file:backlog/plans/04-evidence-capture-and-source-refs.md"
        if not all(search_set_trace_refs.values()):
            resolved_refs.append(
                {
                    "origin": "generated",
                    "relation": "waiver-provenance",
                    "ref": skip_source_ref,
                    "status": "resolved",
                    "target": "backlog/plans/04-evidence-capture-and-source-refs.md",
                }
            )
        for evidence_name in ("search_set_before", "search_set_after"):
            if search_set_trace_refs.get(evidence_name):
                continue
            skipped_evidence.append(
                {
                    "evidence": evidence_name,
                    "actor": packet["input"].get("actor", "codex"),
                    "role": "operator",
                    "date": today(),
                    "reason": f"Finalize did not capture {evidence_name}; stable handoff must add trace evidence or keep this targeted skip.",
                    "source_ref": skip_source_ref,
                }
            )

    packet["meta"]["lifecycle"] = "finalized"
    packet["meta"]["finalized_at"] = today()
    packet["result"] = {
        "inference": {
            "change_class": change_class,
            "impact": "high" if high_risk else "low",
            "changed_paths": paths,
            "intended_scope": packet["input"]["intent"],
            "actual_scope": ", ".join(paths) if paths else "No changed paths detected.",
            "deviations": [],
            "isolation": "isolated" if paths else "no-op",
            "protected_boundary_changed": protected,
            "required_evidence": [],
            "required_review": [],
        },
        "evidence": {
            "baseline_ref": baseline_ref,
            "comparison_ref": comparison_ref,
            "accepted_head_commit": accepted_head_commit,
            "evaluator_boundary": {
                "status": "unchanged",
                "commands": [],
            },
            "command_results": [],
            "source_refs": source_refs,
            "resolved_refs": resolved_refs,
            "trace_refs": {
                "search_set_before": search_set_before,
                "search_set_after": search_set_after,
                "evolution": [],
                "failures": [],
                "disposition": (
                    "Search-set before/after trace refs are captured when supplied; "
                    "missing refs remain explicit targeted skips."
                ),
            },
            "skipped": skipped_evidence,
        },
        "judgment": packet["result"].get(
            "judgment",
            {"reviews": [], "waivers": [], "downgrades": [], "residual_risk": []},
        ),
        "decision": {
            "accepted": diff_status == "pass" and not high_risk,
            "stable_handoff_eligible": False,
            "reason": "Plan 04 requires durable artifact refs before stable handoff.",
            "next_action": "Add durable evidence refs and run check --require-stable.",
        },
    }
    finalize_required_evidence_commands(root, packet, cached_statuses=cached_statuses)
    required_evidence = set(packet["result"]["inference"]["required_evidence"])
    command_results = packet["result"]["evidence"].get("command_results", [])
    required_evidence_passed = (
        isinstance(command_results, list)
        and all(
            isinstance(item, dict)
            and item.get("status") == "pass"
            and item.get("command") in required_evidence
            for item in command_results
        )
        and {item.get("command") for item in command_results if isinstance(item, dict)} == required_evidence
    )
    packet["result"]["decision"]["accepted"] = required_evidence_passed and not high_risk
    if protected:
        packet["result"]["decision"]["reason"] = (
            "Protected changes require imported review judgment before stable handoff."
        )
        packet["result"]["decision"]["next_action"] = (
            "Run governance review-template --packet <packet>, complete the review artifact, "
            "then run governance import-review --packet <packet> --from <artifact>."
        )
    elif proof_like:
        packet["result"]["decision"]["reason"] = (
            "Proof-like or public claims require durable claim evidence and imported review judgment before stable handoff."
        )
        packet["result"]["decision"]["next_action"] = (
            "Add raw claim evidence, run governance review-template --packet <packet>, "
            "complete the claim-evidence review, then run governance import-review --packet <packet> --from <artifact>."
        )
    packet["result"]["inference"]["required_review"] = sorted(checker_required_review(packet, root=root))
    if mode == "worktree":
        packet["result"]["decision"]["stable_handoff_eligible"] = False
        packet["result"]["decision"]["next_action"] = "Finalize with --staged or --base-ref before stable handoff."
    return packet


def start_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    mode, base_ref = mode_from_args(args)
    if mode == "base-ref":
        base_ref = normalize_base_ref(root, base_ref)
    new_packet_id = packet_id()
    if args.output:
        output = Path(args.output)
    elif mode == "base-ref":
        output = default_archive_packet_output(new_packet_id)
    else:
        raise PacketError("start --staged and start --worktree require --output; archive defaults are base-ref only")
    output_path = root / output if not output.is_absolute() else output
    try:
        output_ref = repo_relative_path(root, output_path)
    except PacketError as exc:
        raise PacketError(str(exc)) from exc
    if mode == "base-ref":
        output_error = pointer_packet_ref_error(output_ref)
        if output_error:
            raise PacketError(
                "active base-ref start output must be an archived packet path; "
                f"{output_error}; omit --output to use the default archive path"
            )
    packet = {
        "meta": {
            "packet_id": new_packet_id,
            "schema_version": SCHEMA_VERSION,
            "lifecycle": "start",
            "mode": mode,
            "created_at": today(),
            "finalized_at": None,
        },
        "input": {
            "intent": args.intent,
            "actor": args.actor,
            "source_refs": args.source_ref or [],
            "user_judgment": {},
        },
        "result": {
            "inference": {
                "status": "pending-finalize",
                "changed_paths": [],
                "intended_scope": args.intent,
                "actual_scope": "Not computed until finalize.",
                "deviations": [],
                "isolation": "pending-finalize",
                "required_evidence": [],
                "required_review": [],
            },
            "evidence": {
                "baseline_ref": base_ref if mode == "base-ref" else "HEAD",
                "before_refs": [],
                "after_refs": [],
                "skipped": [],
            },
            "judgment": {
                "reviews": [],
                "waivers": [],
                "downgrades": [],
                "residual_risk": [],
            },
            "decision": {
                "accepted": None,
                "stable_handoff_eligible": False,
                "reason": "Start packet only; finalization has not run.",
                "next_action": "Run finalize before stable handoff.",
            },
        },
    }
    errors = validate_packet(packet, root=root)
    if errors:
        raise PacketError("; ".join(errors))
    write_packet(output_path, packet)
    print(f"wrote start packet: {output_ref}")
    return 0


def finalize_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    mode, base_ref = mode_from_args(args)
    if mode == "base-ref":
        base_ref = normalize_base_ref(root, base_ref)
    path = Path(args.packet)
    packet_path = root / path if not path.is_absolute() else path
    packet = load_packet(packet_path)
    if packet["meta"].get("lifecycle") != "start":
        raise PacketError(f"{packet_path}: finalize requires lifecycle start")
    if packet["meta"].get("mode") != mode:
        raise PacketError(f"{packet_path}: finalize mode must match packet mode")
    if mode == "base-ref":
        packet_base_ref = packet["result"].get("evidence", {}).get("baseline_ref")
        if not same_git_boundary(root, packet_base_ref, base_ref):
            raise PacketError(f"{packet_path}: finalize base-ref must match start baseline_ref: {packet_base_ref}")
    search_set_refs = {
        "search_set_before": args.search_set_before,
        "search_set_after": args.search_set_after,
    }
    if (
        args.search_set_before
        and args.search_set_after
        and canonical_trace_ref(args.search_set_before) == canonical_trace_ref(args.search_set_after)
    ):
        raise PacketError("finalize search-set before and after refs must be distinct")
    for field, ref in search_set_refs.items():
        if not ref:
            continue
        expected_phase = "before" if field == "search_set_before" else "after"
        error = search_set_trace_ref_error(
            root,
            ref,
            field=f"finalize --{field.replace('_', '-')}",
            expected_phase=expected_phase,
        )
        if error:
            raise PacketError(error)
    packet = infer_packet_result(
        root,
        packet,
        mode=mode,
        base_ref=base_ref,
        search_set_before=args.search_set_before,
        search_set_after=args.search_set_after,
    )
    packet_ref = repo_relative_path(root, packet_path)
    artifact_plan = promote_archive_command_artifacts(packet, packet_ref=packet_ref)
    if artifact_plan:
        packet_text = packet_document_text(packet)
        packet_sha256 = hashlib.sha256(packet_text.encode("utf-8")).hexdigest()
        artifact_updates = {
            root / artifact_rel: command_evidence_artifact_text(
                packet,
                packet_ref=packet_ref,
                packet_sha256=packet_sha256,
                command=command,
                status=status,
            )
            for artifact_rel, (command, status) in artifact_plan.items()
        }
        write_error, originals = apply_text_updates_with_rollback(artifact_updates)
        if write_error:
            raise PacketError(write_error)
        errors = validate_packet(
            packet,
            require_stable=packet["result"]["decision"].get("stable_handoff_eligible") is True,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
        )
        if errors:
            rollback_text_updates(originals)
            raise PacketError("; ".join(errors))
        try:
            write_text_atomic(packet_path, packet_text)
        except OSError as exc:
            rollback_text_updates(originals)
            raise PacketError(str(exc)) from exc
    else:
        errors = validate_packet(packet, root=root)
        if errors:
            raise PacketError("; ".join(errors))
        write_packet(packet_path, packet, overwrite=True)
    print(f"finalized packet: {path}")
    return 0


def capture_search_set(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    command = args.command or SEARCH_SET_CAPTURE_COMMAND
    if command != SEARCH_SET_CAPTURE_COMMAND:
        raise PacketError(
            "stable search-set capture command must be "
            f"{SEARCH_SET_CAPTURE_COMMAND!r}; custom commands are diagnostic-only and are not captured here"
        )
    argv, argv_error = search_set_capture_argv(command)
    if argv_error:
        raise PacketError(argv_error)
    assert argv is not None
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            env=git_env(),
            encoding="utf-8",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(
            argv,
            124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nsearch-set capture timed out after {args.timeout}s",
        )
    heading = search_set_capture_heading(args.phase, packet_ref=args.packet)
    head_ref = git_ref_commit(root, "HEAD") or "HEAD"
    record = search_set_capture_record(
        heading=heading,
        phase=args.phase,
        command=command,
        completed=completed,
        head_ref=head_ref,
        packet_ref=args.packet,
        note=args.note,
    )
    append_search_set_capture(root, record)
    trace_ref = f"trace:.harness/traces/search-set.md#{markdown_anchor(heading)}"
    print(f"captured search-set {args.phase} trace: {trace_ref}")
    if completed.returncode != 0:
        print(f"search-set capture command failed with exit code {completed.returncode}", file=sys.stderr)
    return completed.returncode


def check_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = Path(args.packet)
    packet_path = root / path if not path.is_absolute() else path
    packet = load_packet(packet_path)
    try:
        packet_ref = packet_path.resolve().relative_to(root).as_posix()
    except ValueError:
        packet_ref = packet_path.resolve().as_posix()
    errors = validate_packet(
        packet,
        require_stable=args.require_stable,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=file_sha256(packet_path),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    stable = packet["result"]["decision"].get("stable_handoff_eligible") is True
    status = "STABLE" if stable else "VALID: not stable-handoff eligible"
    print(f"{status}: {packet_path}")
    return 0


def import_review(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    packet_arg = Path(args.packet)
    packet_path = root / packet_arg if not packet_arg.is_absolute() else packet_arg
    if repo_path_has_symlink(root, packet_path):
        print(f"ERROR: archived packet must be a regular file, not a symlink: {args.packet}", file=sys.stderr)
        return 1
    packet = load_packet(packet_path)
    try:
        packet_ref = repo_relative_path(root, packet_path)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    try:
        wrapper, input_source_ref, input_source_path, wrapper_errors = review_import_source_from_arg(root, args.source)
        target_binding = review_target_binding(packet, root=root, packet_ref=packet_ref)
        source_ref, source_path = review_import_output_ref_from_arg(
            root,
            packet,
            source_ref=input_source_ref,
            source_path=input_source_path,
            output=args.output,
            overwrite=args.overwrite,
        )
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if wrapper_errors or wrapper is None:
        for error in wrapper_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    target_errors = review_import_target_errors(wrapper, target_binding=target_binding, packet_ref=packet_ref)
    if target_errors:
        for error in target_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    wrapper = materialized_review_import_wrapper(wrapper, source_ref=source_ref)
    updated = apply_review_import_to_packet(
        packet,
        source_ref=source_ref,
        source_digest="",
        wrapper=wrapper,
        target_binding=target_binding,
    )
    promote_imported_review_decision(updated, wrapper, source_ref=source_ref, root=root, packet_ref=packet_ref)
    wrapper_text = review_import_document_text(wrapper)
    source_digest = hashlib.sha256(wrapper_text.encode("utf-8")).hexdigest()
    for import_record in updated["result"]["evidence"].get("review_imports", []):
        if isinstance(import_record, dict) and import_record.get("source_ref") == source_ref:
            import_record["source_digest"] = source_digest
    packet_text = packet_document_text(updated)
    packet_sha256 = hashlib.sha256(packet_text.encode("utf-8")).hexdigest()
    probe_updates, probe_errors = review_import_probe_transcript_updates(
        root,
        wrapper,
        source_ref=source_ref,
        source_digest=source_digest,
        packet_ref=packet_ref,
        packet_sha256=packet_sha256,
    )
    if probe_errors:
        for error in probe_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    protected_update_paths = {source_path.resolve(), packet_path.resolve()}
    conflicting_probe_paths = sorted(
        path.as_posix()
        for path in probe_updates
        if path.resolve() in protected_update_paths
    )
    if conflicting_probe_paths:
        print(
            "ERROR: review import probe transcript refs must not point at the packet or review-import output: "
            f"{conflicting_probe_paths}",
            file=sys.stderr,
        )
        return 1
    updates = {source_path: wrapper_text, **probe_updates, packet_path: packet_text}
    write_error, originals = apply_text_updates_with_rollback(updates)
    if write_error:
        print(f"ERROR: {write_error}", file=sys.stderr)
        return 1
    evidence = updated["result"]["evidence"]
    resolved_refs = evidence.get("resolved_refs", [])
    ref_index = resolved_ref_index(resolved_refs if isinstance(resolved_refs, list) else [])
    _open_reviews, import_errors = validate_review_imports(
        updated,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=packet_sha256,
        ref_index=ref_index,
    )
    if import_errors:
        rollback_text_updates(originals)
        for error in import_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    packet_errors = (
        validate_packet(
            updated,
            require_stable=updated["result"]["decision"].get("stable_handoff_eligible") is True,
            allow_stale_archive_command_artifacts=True,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
        )
        if pointer_packet_ref_error(packet_ref) is None
        else []
    )
    if packet_errors:
        rollback_text_updates(originals)
        for error in packet_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"imported review artifact: {source_ref}")
    return 0


def review_template(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if args.output and args.scratch_output:
        print("ERROR: review-template accepts only one of --output or --scratch-output", file=sys.stderr)
        return 1
    packet_arg = Path(args.packet)
    packet_path = root / packet_arg if not packet_arg.is_absolute() else packet_arg
    if repo_path_has_symlink(root, packet_path):
        print(f"ERROR: archived packet must be a regular file, not a symlink: {args.packet}", file=sys.stderr)
        return 1
    packet = load_packet(packet_path)
    try:
        packet_ref = repo_relative_path(root, packet_path)
        if args.scratch_output:
            source_ref, source_path = review_template_scratch_output_ref_from_arg(root, args.scratch_output)
        else:
            source_ref, source_path = review_import_output_ref_from_arg(
                root,
                packet,
                source_ref=None,
                source_path=None,
                output=args.output,
                overwrite=args.overwrite,
            )
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    required_reviews = sorted(checker_required_review(packet, root=root))
    if not required_reviews:
        print("ERROR: packet does not require imported review judgment", file=sys.stderr)
        return 1
    wrapper, probe_updates = review_template_wrapper(
        packet,
        root=root,
        packet_ref=packet_ref,
        source_ref=source_ref,
    )
    updates = {source_path: review_import_document_text(wrapper), **probe_updates}
    for path in updates:
        if repo_path_has_symlink(root, path):
            print(f"ERROR: review template output must be a regular file, not a symlink: {path}", file=sys.stderr)
            return 1
        if path.exists() and not args.overwrite:
            print(f"ERROR: {path}: already exists; use --overwrite to replace", file=sys.stderr)
            return 1
    write_error, _originals = apply_text_updates_with_rollback(updates)
    if write_error:
        print(f"ERROR: {write_error}", file=sys.stderr)
        return 1
    if args.scratch_output:
        print(f"wrote scratch review template: {source_ref}")
        print(
            "scratch review templates are draft-only workspace files and are not accepted directly by import-review; "
            "complete the review, then materialize durable evidence with --output under archive/v2/artifacts/ "
            "or import-review --from - --output file:archive/v2/artifacts/<name>.yml"
        )
    else:
        print(f"wrote review template: {source_ref}")
    for probe_path in sorted(probe_updates, key=lambda item: item.as_posix()):
        probe_ref = local_file_ref_for_path(root, probe_path)
        if args.scratch_output:
            print(f"wrote scratch probe template: {probe_ref}")
        else:
            print(f"wrote probe template: {probe_ref}")
    return 0


def write_pointer(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    packet_arg = Path(args.packet)
    packet_path = root / packet_arg if not packet_arg.is_absolute() else packet_arg
    if repo_path_has_symlink(root, packet_path):
        print(f"ERROR: archived packet must be a regular file, not a symlink: {args.packet}", file=sys.stderr)
        return 1
    packet = load_packet(packet_path)
    try:
        packet_ref = packet_path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PacketError(f"{packet_path}: archived packet must be inside repository root") from exc
    packet_sha256 = file_sha256(packet_path)
    packet_ref_error = pointer_packet_ref_error(packet_ref)
    if packet_ref_error:
        print(f"ERROR: {packet_ref_error}", file=sys.stderr)
        return 1
    preflight_errors = validate_packet(
        packet,
        require_stable=True,
        require_archive_command_replay_metadata=False,
        allow_stale_archive_command_artifacts=True,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=packet_sha256,
    )
    if preflight_errors:
        for error in preflight_errors:
            print(f"ERROR: archived packet: {error}", file=sys.stderr)
        return 1
    output = Path(args.output) if args.output else Path(DEFAULT_POINTER_PREFIX) / f"{packet['meta']['packet_id']}.yml"
    output_path = root / output if not output.is_absolute() else output
    try:
        output_ref = repo_relative_path(root, output_path)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    output_error = archive_pointer_output_error(
        output_ref,
        packet_ref=packet_ref,
        bound_paths=packet_bound_archive_paths(packet, root=root, packet_ref=packet_ref),
    )
    if output_error:
        print(f"ERROR: {output_error}", file=sys.stderr)
        return 1
    if output_path.exists() and not args.overwrite:
        raise PacketError(f"{output_path}: already exists; use --overwrite to replace")
    with archive_command_replay_root(root, packet) as (replay_root, replay_root_errors):
        if replay_root_errors:
            for error in replay_root_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        updates, materialize_errors = planned_archive_command_evidence_updates(
            packet,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
            replay_root=replay_root,
            allow_existing_replay_metadata=args.overwrite,
        )
    if materialize_errors:
        for error in materialize_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    materialize_error, originals = apply_text_updates_with_rollback(updates)
    if materialize_error:
        print(f"ERROR: {materialize_error}", file=sys.stderr)
        return 1
    try:
        archive_commit, archive_commit_error = create_archive_commit(root, packet, packet_ref=packet_ref)
        if archive_commit_error:
            rollback_text_updates(originals)
            print(f"ERROR: {archive_commit_error}", file=sys.stderr)
            return 1
        assert archive_commit is not None
        pointer = pointer_for_packet(
            packet,
            root=root,
            packet_ref=packet_ref,
            packet_sha256=packet_sha256,
            archive_commit=archive_commit,
        )
        errors = validate_pointer(pointer, root=root, pointer_ref=output_ref, ignore_non_archive_dirty=True)
        if errors:
            rollback_text_updates(originals)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

        pointer_text = yaml.safe_dump({POINTER_KEY: pointer}, sort_keys=False, allow_unicode=False)
        write_text_atomic(output_path, pointer_text)
    except OSError as exc:
        rollback_text_updates(originals)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except PacketError:
        rollback_text_updates(originals)
        raise
    print(f"wrote active pointer: {output}")
    return 0


def git_name_only(root: Path, args: list[str]) -> list[str] | None:
    result = git(root, args)
    if result.returncode != 0:
        return None
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def dirty_worktree_paths(root: Path) -> list[str]:
    result = git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    return porcelain_status_paths(result.stdout) if result.returncode == 0 else []


def run_active_packet_gate(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check-active-packet-gate.py"),
            "--root",
            str(root),
            *args,
        ],
        cwd=root,
        env=git_env(keep_index=True),
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def publish_packet(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    packet_arg = Path(args.packet)
    packet_path = root / packet_arg if not packet_arg.is_absolute() else packet_arg
    if repo_path_has_symlink(root, packet_path):
        print(f"ERROR: archived packet must be a regular file, not a symlink: {args.packet}", file=sys.stderr)
        return 1
    packet = load_packet(packet_path)
    try:
        packet_ref = repo_relative_path(root, packet_path)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    packet_ref_error = pointer_packet_ref_error(packet_ref)
    if packet_ref_error:
        print(f"ERROR: {packet_ref_error}", file=sys.stderr)
        return 1
    evidence = packet.get("result", {}).get("evidence", {})
    accepted_head = evidence.get("accepted_head_commit") if isinstance(evidence, dict) else None
    comparison_ref = evidence.get("comparison_ref") if isinstance(evidence, dict) else None
    current_head = git_ref_commit(root, "HEAD")
    if not isinstance(accepted_head, str) or not FULL_COMMIT_RE.fullmatch(accepted_head):
        print("ERROR: publish requires packet evidence.accepted_head_commit to be a full commit SHA", file=sys.stderr)
        return 1
    if current_head != accepted_head:
        print(
            "ERROR: publish requires content commits first: current HEAD must equal packet accepted_head_commit",
            file=sys.stderr,
        )
        return 1
    staged_before = git_name_only(root, ["diff", "--cached", "--name-only"])
    if staged_before is None:
        print("ERROR: publish could not inspect staged changes", file=sys.stderr)
        return 1
    if staged_before:
        print(
            "ERROR: publish requires an empty index before generating the archive publication; "
            f"staged paths: {staged_before}",
            file=sys.stderr,
        )
        return 1
    preflight_errors = validate_packet(
        packet,
        require_stable=True,
        require_archive_command_replay_metadata=False,
        allow_stale_archive_command_artifacts=True,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=file_sha256(packet_path),
    )
    if preflight_errors:
        for error in preflight_errors:
            print(f"ERROR: archived packet: {error}", file=sys.stderr)
        return 1
    allowed_pre_dirty = packet_bound_archive_paths(packet, root=root, packet_ref=packet_ref)
    unexpected_pre_dirty = sorted(path for path in dirty_worktree_paths(root) if path not in allowed_pre_dirty)
    if unexpected_pre_dirty:
        print(
            "ERROR: publish requires content commits first and only pointer-bound archive files dirty; "
            f"unexpected dirty paths: {unexpected_pre_dirty}",
            file=sys.stderr,
        )
        return 1
    pointer_arg = args.pointer
    pointer_output = pointer_arg or str(Path(DEFAULT_POINTER_PREFIX) / f"{packet['meta']['packet_id']}.yml")
    write_args = argparse.Namespace(
        root=str(root),
        packet=packet_ref,
        output=pointer_output,
        overwrite=args.overwrite,
    )
    write_result = write_pointer(write_args)
    if write_result != 0:
        return write_result
    pointer_path = root / pointer_output if not Path(pointer_output).is_absolute() else Path(pointer_output)
    try:
        pointer_ref = repo_relative_path(root, pointer_path)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    pointer = load_pointer(pointer_path)
    publication_paths = pointer_publication_paths(pointer, pointer_ref=pointer_ref)
    unexpected_dirty = sorted(path for path in dirty_worktree_paths(root) if path not in publication_paths)
    if unexpected_dirty:
        print(
            "ERROR: publish generated pointer-bound archive files but found unexpected dirty paths; "
            f"refusing archive commit: {unexpected_dirty}",
            file=sys.stderr,
        )
        return 1
    add_result = git(root, ["add", "--", *sorted(publication_paths)])
    if add_result.returncode != 0:
        print(f"ERROR: publish could not stage archive publication: {add_result.stderr.strip()}", file=sys.stderr)
        return 1
    staged_after = git_name_only(root, ["diff", "--cached", "--name-only"])
    if staged_after is None:
        print("ERROR: publish could not inspect staged archive publication", file=sys.stderr)
        return 1
    unexpected_staged = sorted(path for path in staged_after if path not in publication_paths)
    if unexpected_staged:
        print(f"ERROR: publish staged unexpected paths: {unexpected_staged}", file=sys.stderr)
        return 1
    staged_gate = run_active_packet_gate(root, ["--staged", "--pointer", pointer_ref])
    if staged_gate.returncode != 0:
        print(staged_gate.stdout, end="")
        print(staged_gate.stderr, end="", file=sys.stderr)
        return staged_gate.returncode
    commit_result = git(root, ["commit", "-m", args.message])
    if commit_result.returncode != 0:
        print(commit_result.stdout, end="")
        print(commit_result.stderr, end="", file=sys.stderr)
        return commit_result.returncode
    if not isinstance(comparison_ref, str) or not comparison_ref:
        print("ERROR: publish cannot run release gate because packet comparison_ref is missing", file=sys.stderr)
        return 1
    release_gate = run_active_packet_gate(root, ["--base-ref", comparison_ref, "--pointer", pointer_ref])
    if release_gate.returncode != 0:
        print(release_gate.stdout, end="")
        print(release_gate.stderr, end="", file=sys.stderr)
        return release_gate.returncode
    print(commit_result.stdout, end="")
    print(staged_gate.stdout, end="")
    print(release_gate.stdout, end="")
    print(f"published active pointer: {pointer_ref}")
    return 0


def check_pointer(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = Path(args.pointer)
    pointer_path = root / path if not path.is_absolute() else path
    pointer = load_pointer(pointer_path)
    try:
        pointer_ref = repo_relative_path(root, pointer_path)
    except PacketError:
        pointer_ref = None
    errors = validate_pointer(
        pointer,
        root=root,
        pointer_ref=pointer_ref,
        replay_archive_command_evidence=args.replay_command_evidence,
        ignore_non_archive_dirty=True,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"POINTER: STABLE: {pointer_path} -> {pointer['packet_ref']}")
    return 0


def status_archive_refs(root: Path, prefix: str, suffixes: tuple[str, ...]) -> list[str]:
    directory = root / prefix
    if not directory.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.name.endswith(suffixes)
    )


def status_base_ref_matches(root: Path, record: dict, base_commit: str | None) -> bool:
    if base_commit is None:
        return True
    for key in ("comparison_ref", "baseline_ref"):
        value = record.get(key)
        if isinstance(value, str) and same_git_boundary(root, value, base_commit):
            return True
    evidence = record.get("result", {}).get("evidence", {}) if isinstance(record.get("result"), dict) else {}
    for key in ("comparison_ref", "baseline_ref"):
        value = evidence.get(key) if isinstance(evidence, dict) else None
        if isinstance(value, str) and same_git_boundary(root, value, base_commit):
            return True
    return False


def status_packet_for_pointer(root: Path, pointer: dict) -> tuple[dict | None, str | None]:
    packet_ref = pointer.get("packet_ref")
    if not isinstance(packet_ref, str):
        return None, None
    packet_rel = resolve_repo_path(root, packet_ref)
    if packet_rel is None:
        return None, packet_ref
    try:
        return load_packet(root / packet_rel), packet_rel
    except PacketError:
        return None, packet_rel


def status_publication_commit(root: Path, pointer: dict, packet: dict | None) -> str:
    if packet is None:
        return "unknown"
    result = packet.get("result", {})
    evidence = result.get("evidence", {}) if isinstance(result, dict) else {}
    accepted_head = evidence.get("accepted_head_commit") if isinstance(evidence, dict) else None
    current_head = git_ref_commit(root, "HEAD")
    if not isinstance(accepted_head, str) or current_head is None:
        return "unknown"
    if current_head == accepted_head:
        return "prepublication"
    if not git_is_ancestor(root, accepted_head, current_head):
        return "unknown"
    commits = git_rev_list_between(root, accepted_head, current_head)
    if commits is None:
        return "unknown"
    for commit in commits:
        archive_paths = commit_archive_v2_paths(root, commit)
        if archive_paths:
            return commit
    return "unpublished"


def status_issue_buckets(errors: list[str]) -> tuple[list[str], list[str], list[str]]:
    human_markers = (
        "required review",
        "missing required review",
        "review",
        "waiver",
        "downgrade",
        "skipped",
        "residual",
        "human",
        "provenance",
        "claim evidence",
    )
    generated_markers = (
        "command artifact",
        "command evidence",
        "artifact",
        "archive_commit",
        "packet_sha256",
        "source_digest",
        "replay metadata",
        "probe transcript",
        "resolved generated",
        "generated artifact",
        "terminal placeholder",
    )
    human: list[str] = []
    generated: list[str] = []
    other: list[str] = []
    for error in errors:
        lowered = error.lower()
        if any(marker in lowered for marker in human_markers):
            human.append(error)
        elif any(marker in lowered for marker in generated_markers):
            generated.append(error)
        else:
            other.append(error)
    return human, generated, other


def status_print_issue_summary(errors: list[str], *, indent: str = "  ") -> None:
    human, generated, other = status_issue_buckets(errors)
    print(f"{indent}human_decisions: {len(human)}")
    print(f"{indent}generated_refreshes: {len(generated)}")
    print(f"{indent}other_issues: {len(other)}")
    if errors:
        print(f"{indent}issues:")
        for error in errors[:8]:
            print(f"{indent}  - {error}")
        if len(errors) > 8:
            print(f"{indent}  - ... {len(errors) - 8} more")


def status_packet_errors(root: Path, packet_ref: str, packet: dict) -> list[str]:
    return validate_packet(
        packet,
        require_stable=True,
        require_archive_command_replay_metadata=False,
        allow_stale_archive_command_artifacts=True,
        root=root,
        packet_ref=packet_ref,
        packet_sha256=file_sha256(root / packet_ref),
    )


def status_command(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    base_commit = git_ref_commit(root, args.base_ref) if args.base_ref else None
    if args.base_ref and base_commit is None:
        print(f"ERROR: base-ref does not resolve to a commit: {args.base_ref}", file=sys.stderr)
        return 1

    print("governance status")
    print(f"base_ref: {base_commit or '(none)'}")

    pointer_refs = status_archive_refs(root, DEFAULT_POINTER_PREFIX, POINTER_SUFFIXES)
    pointer_summaries: list[tuple[str, dict | None, str | None, dict | None, list[str]]] = []
    referenced_packets: set[str] = set()
    for pointer_ref in pointer_refs:
        pointer_path = root / pointer_ref
        try:
            pointer = load_pointer(pointer_path)
        except PacketError as exc:
            pointer_summaries.append((pointer_ref, None, None, None, [str(exc)]))
            continue
        if not status_base_ref_matches(root, pointer, base_commit):
            continue
        packet, packet_ref = status_packet_for_pointer(root, pointer)
        if packet_ref:
            referenced_packets.add(packet_ref)
        errors = validate_pointer(
            pointer,
            root=root,
            pointer_ref=pointer_ref,
            replay_archive_command_evidence=False,
            ignore_non_archive_dirty=True,
        )
        pointer_summaries.append((pointer_ref, pointer, packet_ref, packet, errors))

    print(f"pointers: {len(pointer_summaries)}")
    for pointer_ref, pointer, packet_ref, packet, errors in pointer_summaries:
        print(f"- pointer: {pointer_ref}")
        print(f"  packet: {packet_ref or 'unknown'}")
        packet_id_value = (
            pointer.get("packet_id")
            if isinstance(pointer, dict)
            else None
        )
        print(f"  packet_id: {packet_id_value or 'unknown'}")
        decision = packet.get("result", {}).get("decision", {}) if isinstance(packet, dict) else {}
        stable = decision.get("stable_handoff_eligible") if isinstance(decision, dict) else None
        decision_status = pointer.get("decision_status") if isinstance(pointer, dict) else None
        print(f"  stable_handoff: {stable if stable is not None else 'unknown'}")
        print(f"  decision: {decision_status or 'unknown'}")
        print(f"  publication: {status_publication_commit(root, pointer, packet) if isinstance(pointer, dict) else 'unknown'}")
        print(f"  audit: {'PASS' if not errors else 'FAIL'}")
        status_print_issue_summary(errors)

    packet_refs = status_archive_refs(root, ARCHIVE_PACKET_PREFIX, (".yml", ".yaml", ".json"))
    pending_summaries: list[tuple[str, dict | None, list[str]]] = []
    for packet_ref in packet_refs:
        if packet_ref in referenced_packets:
            continue
        try:
            packet = load_packet(root / packet_ref)
        except PacketError as exc:
            pending_summaries.append((packet_ref, None, [str(exc)]))
            continue
        if not status_base_ref_matches(root, packet, base_commit):
            continue
        pending_summaries.append((packet_ref, packet, status_packet_errors(root, packet_ref, packet)))

    print(f"pending_packets: {len(pending_summaries)}")
    for packet_ref, packet, errors in pending_summaries:
        print(f"- packet: {packet_ref}")
        meta = packet.get("meta", {}) if isinstance(packet, dict) else {}
        result = packet.get("result", {}) if isinstance(packet, dict) else {}
        decision = result.get("decision", {}) if isinstance(result, dict) else {}
        print(f"  packet_id: {meta.get('packet_id') if isinstance(meta, dict) else 'unknown'}")
        print(f"  stable_handoff: {decision.get('stable_handoff_eligible') if isinstance(decision, dict) else 'unknown'}")
        print(f"  status: {'READY' if not errors else 'BLOCKED'}")
        status_print_issue_summary(errors)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--output")
    start.add_argument("--intent", required=True)
    start.add_argument("--actor", default="codex")
    start.add_argument("--source-ref", action="append")
    start.add_argument("--staged", action="store_true")
    start.add_argument("--worktree", action="store_true")
    start.add_argument("--base-ref")
    start.set_defaults(func=start_packet)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--packet", required=True)
    finalize.add_argument("--staged", action="store_true")
    finalize.add_argument("--worktree", action="store_true")
    finalize.add_argument("--base-ref")
    finalize.add_argument("--search-set-before", help="trace:.harness/traces/search-set.md#... ref captured before the change")
    finalize.add_argument("--search-set-after", help="trace:.harness/traces/search-set.md#... ref captured after the change")
    finalize.set_defaults(func=finalize_packet)

    capture_search = subparsers.add_parser("capture-search-set")
    capture_search.add_argument("--phase", choices=("before", "after"), required=True)
    capture_search.add_argument("--packet", help="packet ref this capture is intended to support")
    capture_search.add_argument("--command", default=SEARCH_SET_CAPTURE_COMMAND)
    capture_search.add_argument("--timeout", type=int, default=300)
    capture_search.add_argument("--note")
    capture_search.set_defaults(func=capture_search_set)

    check = subparsers.add_parser("check")
    check.add_argument("--packet", required=True)
    check.add_argument("--require-stable", action="store_true")
    check.set_defaults(func=check_packet)

    import_review_parser = subparsers.add_parser("import-review")
    import_review_parser.add_argument("--packet", required=True)
    import_review_parser.add_argument("--from", dest="source", required=True)
    import_review_parser.add_argument("--output")
    import_review_parser.add_argument("--overwrite", action="store_true")
    import_review_parser.set_defaults(func=import_review)

    review_template_parser = subparsers.add_parser("review-template")
    review_template_parser.add_argument("--packet", required=True)
    review_template_parser.add_argument("--output")
    review_template_parser.add_argument("--scratch-output")
    review_template_parser.add_argument("--overwrite", action="store_true")
    review_template_parser.set_defaults(func=review_template)

    write_pointer_parser = subparsers.add_parser("write-pointer")
    write_pointer_parser.add_argument("--packet", required=True)
    write_pointer_parser.add_argument("--output")
    write_pointer_parser.add_argument("--overwrite", action="store_true")
    write_pointer_parser.set_defaults(func=write_pointer)

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("--packet", required=True)
    publish_parser.add_argument("--pointer")
    publish_parser.add_argument("--message", default="Publish active packet pointer")
    publish_parser.add_argument("--overwrite", action="store_true")
    publish_parser.set_defaults(func=publish_packet)

    check_pointer_parser = subparsers.add_parser("check-pointer")
    check_pointer_parser.add_argument("--pointer", required=True)
    check_pointer_parser.add_argument("--replay-command-evidence", action="store_true")
    check_pointer_parser.set_defaults(func=check_pointer)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--base-ref")
    status_parser.set_defaults(func=status_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PacketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
