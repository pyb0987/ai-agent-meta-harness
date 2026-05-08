#!/usr/bin/env python3
"""Check or refresh deterministic governance fixture bindings."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET_KEY = "AcceptancePacket"
REVIEW_IMPORT_KEY = "AcceptancePacketReviewImport"
MULTI_REVIEW_KEY = "MultiReviewResult"
PROBE_TRANSCRIPT_KEY = "ProbeTranscript"


def load_checker_module() -> Any:
    script = REPO_ROOT / "scripts" / "check-governance-acceptance.py"
    spec = importlib.util.spec_from_file_location("check_governance_acceptance_for_fixtures", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load checker module: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_benchmark_module() -> Any:
    script = REPO_ROOT / "benchmarks" / "multi-review" / "check-fixtures.py"
    spec = importlib.util.spec_from_file_location("multi_review_benchmark_for_fixtures", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark module: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker_module()
BENCHMARK = load_benchmark_module()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_structured(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def dump_structured(path: Path, value: Any) -> bytes:
    if path.suffix == ".json":
        return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=False).encode("utf-8")


def normalize(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def sorted_string_values(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(item for item in values if isinstance(item, str) and item)


def ref_to_file_path(root: Path, ref: str, *, source: str) -> Path:
    if not isinstance(ref, str) or not ref.startswith("file:"):
        raise ValueError(f"{source}: expected file: ref, got {ref!r}")
    rel = ref.removeprefix("file:")
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{source}: ref escapes repository root: {ref}")
    candidate = (root / path).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"{source}: ref escapes repository root: {ref}")
    rel_candidate = candidate.relative_to(root_resolved)
    if not rel_candidate.as_posix().startswith("backlog/fixtures/"):
        raise ValueError(f"{source}: fixture helper file refs must stay under backlog/fixtures/: {ref}")
    return candidate


@dataclass
class CommandLogSection:
    start: int
    end: int
    fields: dict[str, str]
    field_lines: dict[str, int]
    duplicate_fields: set[str]


@dataclass
class PacketInfo:
    path: Path
    ref: str
    packet: dict[str, Any]
    packet_sha256: str
    changed: bool


class FixtureUpdater:
    def __init__(self, root: Path, *, write: bool) -> None:
        self.root = root.resolve()
        self.write = write
        self.drift: list[str] = []
        self.errors: list[str] = []
        self.pending_writes: dict[Path, bytes] = {}
        self.transcript_bindings: dict[Path, tuple[dict[str, Any], str]] = {}

    def run(self) -> int:
        packet_infos = self.process_acceptance_packets()
        for info in packet_infos:
            self.process_command_logs(info)
        self.process_standalone_multi_review_results()
        self.process_benchmark_scenarios()
        if self.write and not self.errors:
            for path, content in sorted(self.pending_writes.items()):
                if path.exists() and path.read_bytes() == content:
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                print(f"updated: {relative_path(self.root, path)}")
        for item in self.errors:
            print(f"ERROR: {item}", file=sys.stderr)
        for item in self.drift:
            print(f"DRIFT: {item}", file=sys.stderr)
        if self.errors or (self.drift and not self.write):
            return 1
        if self.drift and self.write:
            print(f"governance fixture update: wrote {len(self.pending_writes)} file(s)")
        else:
            print("governance fixture update: OK")
        return 0

    def process_acceptance_packets(self) -> list[PacketInfo]:
        packet_root = self.root / "backlog" / "fixtures" / "acceptance-packets"
        infos: list[PacketInfo] = []
        for packet_path in sorted(packet_root.glob("*.yml")):
            try:
                info = self.process_acceptance_packet(packet_path)
            except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
                self.errors.append(f"{relative_path(self.root, packet_path)}: {exc}")
                continue
            infos.append(info)
        return infos

    def process_acceptance_packet(self, packet_path: Path) -> PacketInfo:
        packet_doc = load_structured(packet_path)
        if not isinstance(packet_doc, dict) or PACKET_KEY not in packet_doc:
            raise ValueError(f"missing {PACKET_KEY}")
        packet_doc = copy.deepcopy(packet_doc)
        packet = packet_doc[PACKET_KEY]
        packet_ref = relative_path(self.root, packet_path)
        packet_changed = False
        wrapper_tasks: list[tuple[dict[str, Any], str, str]] = []

        evidence = packet.get("result", {}).get("evidence", {})
        imports = evidence.get("review_imports", [])
        if isinstance(imports, list):
            for index, import_record in enumerate(imports):
                if not isinstance(import_record, dict):
                    continue
                source = f"{packet_ref}:result.evidence.review_imports[{index}]"
                source_ref = import_record.get("source_ref")
                if not isinstance(source_ref, str):
                    self.errors.append(f"{source}: source_ref is required")
                    continue
                try:
                    wrapper_path = ref_to_file_path(self.root, source_ref, source=source)
                    wrapper_doc = load_structured(wrapper_path)
                except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
                    self.errors.append(f"{source}: cannot load review import: {exc}")
                    continue
                if not isinstance(wrapper_doc, dict) or REVIEW_IMPORT_KEY not in wrapper_doc:
                    self.errors.append(f"{source}: missing {REVIEW_IMPORT_KEY}")
                    continue
                wrapper_doc = copy.deepcopy(wrapper_doc)
                wrapper = wrapper_doc[REVIEW_IMPORT_KEY]
                binding = CHECKER.review_target_binding(packet, root=self.root, packet_ref=packet_ref)
                wrapper_changed = self.set_value(
                    wrapper,
                    "target_binding",
                    binding,
                    f"{relative_path(self.root, wrapper_path)}:target_binding",
                )
                packet_changed |= self.set_value(
                    import_record,
                    "target_binding",
                    binding,
                    f"{source}.target_binding",
                )
                wrapper_bytes = (
                    dump_structured(wrapper_path, wrapper_doc)
                    if wrapper_changed
                    else wrapper_path.read_bytes()
                )
                wrapper_digest = sha256_bytes(wrapper_bytes)
                packet_changed |= self.set_value(
                    import_record,
                    "source_digest",
                    wrapper_digest,
                    f"{source}.source_digest",
                )
                if wrapper_changed:
                    self.pending_writes[wrapper_path] = wrapper_bytes
                multi_review = wrapper.get(MULTI_REVIEW_KEY)
                if isinstance(multi_review, dict):
                    wrapper_tasks.append((multi_review, source_ref, wrapper_digest))

        packet_bytes = dump_structured(packet_path, packet_doc) if packet_changed else packet_path.read_bytes()
        packet_sha = sha256_bytes(packet_bytes)
        if packet_changed:
            self.pending_writes[packet_path] = packet_bytes

        for multi_review, result_ref, result_digest in wrapper_tasks:
            self.process_probe_transcripts(
                multi_review,
                result_ref=result_ref,
                result_digest=result_digest,
                packet_ref=packet_ref,
                packet_sha256=packet_sha,
            )
        return PacketInfo(packet_path, packet_ref, packet, packet_sha, packet_changed)

    def process_standalone_multi_review_results(self) -> None:
        fixture_root = self.root / "backlog" / "fixtures" / "multi-review"
        for path in sorted(fixture_root.iterdir() if fixture_root.exists() else []):
            if path.is_dir() or path.suffix not in {".yml", ".yaml", ".json"}:
                continue
            try:
                doc = load_structured(path)
            except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
                self.errors.append(f"{relative_path(self.root, path)}: cannot load result: {exc}")
                continue
            if not isinstance(doc, dict) or MULTI_REVIEW_KEY not in doc:
                continue
            self.process_probe_transcripts(
                doc[MULTI_REVIEW_KEY],
                result_ref=relative_path(self.root, path),
                result_digest=sha256_bytes(path.read_bytes()),
                packet_ref=None,
                packet_sha256=None,
            )

    def process_benchmark_scenarios(self) -> None:
        scenarios_root = self.root / "benchmarks" / "multi-review" / "scenarios"
        if not scenarios_root.exists():
            return
        for scenario_path in sorted(scenarios_root.glob("**/scenario.yml")):
            try:
                original_root = BENCHMARK.ROOT
                BENCHMARK.ROOT = self.root
                try:
                    scenario = BENCHMARK.load_scenario(scenario_path)
                    if not scenario.get("replay_probe_commands"):
                        continue
                    result = BENCHMARK.scenario_result(scenario)
                    result_ref, result_digest = BENCHMARK.scenario_result_binding(scenario_path, scenario, result)
                finally:
                    BENCHMARK.ROOT = original_root
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
                self.errors.append(f"{relative_path(self.root, scenario_path)}: cannot load benchmark scenario: {exc}")
                continue
            self.process_probe_transcripts(
                result,
                result_ref=result_ref,
                result_digest=result_digest,
                packet_ref=None,
                packet_sha256=None,
            )

    def process_probe_transcripts(
        self,
        result: dict[str, Any],
        *,
        result_ref: str,
        result_digest: str,
        packet_ref: str | None,
        packet_sha256: str | None,
    ) -> None:
        critics = result.get("critics", [])
        if not isinstance(critics, list):
            return
        for critic_index, critic in enumerate(critics):
            if not isinstance(critic, dict):
                continue
            refs = critic.get("probe_evidence_refs", [])
            if not isinstance(refs, list):
                continue
            for ref_index, ref in enumerate(refs):
                source = f"{result_ref}:critics[{critic_index}].probe_evidence_refs[{ref_index}]"
                try:
                    transcript_path = ref_to_file_path(self.root, ref, source=source)
                    transcript_doc = load_structured(transcript_path)
                except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
                    self.errors.append(f"{source}: cannot load transcript: {exc}")
                    continue
                if not isinstance(transcript_doc, dict) or PROBE_TRANSCRIPT_KEY not in transcript_doc:
                    self.errors.append(f"{source}: missing {PROBE_TRANSCRIPT_KEY}")
                    continue
                transcript_doc = copy.deepcopy(transcript_doc)
                transcript = transcript_doc[PROBE_TRANSCRIPT_KEY]
                if not isinstance(transcript, dict):
                    self.errors.append(f"{source}: {PROBE_TRANSCRIPT_KEY} must be a mapping")
                    continue
                original_checker_root = BENCHMARK.checker.ROOT
                BENCHMARK.checker.ROOT = self.root
                try:
                    transcript_shape_errors = BENCHMARK.checker.probe_transcript_shape_errors(transcript)
                finally:
                    BENCHMARK.checker.ROOT = original_checker_root
                if transcript_shape_errors:
                    self.errors.append(
                        f"{relative_path(self.root, transcript_path)}: transcript schema drift requires explicit regeneration, not --write: "
                        f"{'; '.join(transcript_shape_errors)}"
                    )
                    continue
                stdout = transcript.get("stdout")
                stderr = transcript.get("stderr")
                if not isinstance(stdout, str) or not isinstance(stderr, str):
                    self.errors.append(f"{source}: transcript stdout/stderr must be strings")
                    continue
                expected_command = critic.get("probe_command")
                expected_exit_code = critic.get("probe_exit_code")
                if not isinstance(expected_command, str) or not expected_command:
                    self.errors.append(f"{source}: probe_command must be a non-empty string")
                    continue
                if not isinstance(expected_exit_code, int) or isinstance(expected_exit_code, bool):
                    self.errors.append(f"{source}: probe_exit_code must be an integer")
                    continue
                transcript_path_display = relative_path(self.root, transcript_path)
                changed = False
                expectations = {
                    "probe_command": expected_command,
                    "probe_exit_code": expected_exit_code,
                    "result_ref": result_ref,
                    "result_digest": result_digest,
                    "packet_ref": packet_ref,
                    "packet_sha256": packet_sha256,
                }
                raw_source_refs = critic.get("source_refs")
                if (
                    not isinstance(raw_source_refs, list)
                    or not raw_source_refs
                    or any(not isinstance(ref, str) or not ref for ref in raw_source_refs)
                ):
                    self.errors.append(f"{source}: source_refs must be a non-empty list of strings")
                    continue
                expected_source_refs = sorted(raw_source_refs)
                previous_binding = self.transcript_bindings.get(transcript_path)
                binding_identity = copy.deepcopy(expectations)
                binding_identity["source_refs"] = expected_source_refs
                if previous_binding is not None and previous_binding[0] != binding_identity:
                    self.errors.append(
                        f"{transcript_path_display}: conflicting transcript binding owners: "
                        f"{previous_binding[1]} and {source}"
                    )
                    continue
                self.transcript_bindings[transcript_path] = (binding_identity, source)
                if transcript.get("probe_command") != expected_command:
                    self.errors.append(
                        f"{transcript_path_display}:probe_command: probe command drift requires explicit replay, not --write"
                    )
                    continue
                if transcript.get("probe_exit_code") != expected_exit_code:
                    self.errors.append(
                        f"{transcript_path_display}:probe_exit_code: probe exit-code drift requires explicit replay, not --write"
                    )
                    continue
                if transcript.get("source_refs") != expected_source_refs:
                    self.errors.append(
                        f"{transcript_path_display}:source_refs: source-ref drift requires explicit replay, not --write"
                    )
                    continue
                for field, expected in expectations.items():
                    changed |= self.set_value(
                        transcript,
                        field,
                        expected,
                        f"{relative_path(self.root, transcript_path)}:{field}",
                    )
                if changed:
                    self.pending_writes[transcript_path] = dump_structured(transcript_path, transcript_doc)

    def process_command_logs(self, info: PacketInfo) -> None:
        command_results = (
            info.packet.get("result", {})
            .get("evidence", {})
            .get("command_results", [])
        )
        if not isinstance(command_results, list):
            return
        packet_id = info.packet.get("meta", {}).get("packet_id")
        if not isinstance(packet_id, str):
            return
        for index, command_result in enumerate(command_results):
            if not isinstance(command_result, dict):
                continue
            source = f"{info.ref}:result.evidence.command_results[{index}]"
            command = command_result.get("command")
            status = command_result.get("status")
            artifact_ref = command_result.get("artifact_ref")
            if not all(isinstance(value, str) and value for value in (command, status, artifact_ref)):
                self.errors.append(f"{source}: command, status, and artifact_ref are required")
                continue
            if not artifact_ref.startswith("file:"):
                continue
            try:
                artifact_path = ref_to_file_path(self.root, artifact_ref, source=source)
            except ValueError as exc:
                self.errors.append(str(exc))
                continue
            expected = {
                "packet_id": packet_id,
                "packet_ref": info.ref,
                "packet_sha256": info.packet_sha256,
                "command": command,
                "status": status,
            }
            try:
                self.process_command_log_section(artifact_path, expected, source=source)
            except OSError as exc:
                self.errors.append(f"{source}: cannot read artifact: {exc}")

    def process_command_log_section(self, path: Path, expected: dict[str, str], *, source: str) -> None:
        if path in self.pending_writes:
            text = self.pending_writes[path].decode("utf-8")
        else:
            text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        sections = parse_command_log_sections(lines)
        if not sections:
            self.errors.append(f"{source}: command artifact has no # Command Evidence section")
            return
        matching = [
            section for section in sections
            if section.fields.get("packet_id") == expected["packet_id"]
            and section.fields.get("command") == expected["command"]
        ]
        section = matching[0] if len(matching) == 1 else None
        if section is None:
            self.errors.append(
                f"{source}: command artifact lacks an unambiguous section for "
                f"{expected['packet_id']} / {expected['command']}"
            )
            return
        if section.duplicate_fields:
            duplicates = ", ".join(sorted(section.duplicate_fields))
            self.errors.append(
                f"{relative_path(self.root, path)}: command artifact has duplicate fields: {duplicates}"
            )
            return
        changed = False
        observed_fields = {"packet_id", "command", "status"}
        for field in observed_fields:
            current_value = section.fields.get(field)
            if current_value != expected[field]:
                self.errors.append(
                    f"{relative_path(self.root, path)}:{field}: observed command evidence drift requires explicit replay, not --write"
                )
                return
        for field in ("packet_ref", "packet_sha256"):
            expected_value = expected[field]
            current_value = section.fields.get(field)
            label = f"{relative_path(self.root, path)}:{field}"
            if current_value != expected_value:
                self.drift.append(f"{label}: expected {expected_value!r}, found {current_value!r}")
                changed = True
                if field in section.field_lines:
                    lines[section.field_lines[field]] = f"{field}: {expected_value}"
                else:
                    lines.insert(section.end, f"{field}: {expected_value}")
        if changed:
            content = ("\n".join(lines) + ("\n" if text.endswith("\n") else "")).encode("utf-8")
            self.pending_writes[path] = content

    def set_value(self, container: dict[str, Any], field: str, expected: Any, label: str) -> bool:
        current = container.get(field)
        if normalize(current) == normalize(expected):
            return False
        self.drift.append(f"{label}: expected {expected!r}, found {current!r}")
        container[field] = copy.deepcopy(expected)
        return True


def parse_command_log_sections(lines: list[str]) -> list[CommandLogSection]:
    sections: list[CommandLogSection] = []
    for start, end in CHECKER.command_evidence_section_bounds(lines):
        fields = CHECKER.command_evidence_section_fields(lines, start, end)
        duplicate_fields = CHECKER.command_evidence_section_duplicate_fields(lines, start, end)
        field_lines: dict[str, int] = {}
        for index in range(start + 1, end):
            match = CHECKER.COMMAND_EVIDENCE_FIELD_RE.match(lines[index])
            if not match:
                continue
            field = match.group(1).casefold().replace("-", "_")
            field_lines[field] = index
        sections.append(
            CommandLogSection(
                start=start,
                end=end,
                fields=fields,
                field_lines=field_lines,
                duplicate_fields=duplicate_fields,
            )
        )
    return sections


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail when deterministic fixture fields drift")
    mode.add_argument("--write", action="store_true", help="rewrite deterministic fixture fields")
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root containing backlog/fixtures (default: this repository)",
    )
    args = parser.parse_args(argv)

    updater = FixtureUpdater(args.root, write=args.write)
    return updater.run()


if __name__ == "__main__":
    raise SystemExit(main())
