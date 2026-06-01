#!/usr/bin/env python3
"""Build and query raw-trace retrieval catalogs.

Catalogs are retrieval pointers, not evidence. They intentionally contain
frontmatter metadata and file hashes, but no narrative summaries.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CATALOG_NAME = "trace-catalog.jsonl"
TRACE_KIND_BY_DIR = {
    "evolution": "evolution",
    "failures": "failure",
    "experiments": "experiment",
}
EXPERIMENT_REQUIRED_FIELDS = {
    "kind",
    "date",
    "objective",
    "metric",
    "verdict",
    "tags",
    "evaluator",
}


class TraceQueryError(ValueError):
    pass


def repo_relative(path: Path, repo_root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_frontmatter(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data.startswith(b"---\n"):
        return {}
    end = data.find(b"\n---\n", 4)
    if end == -1:
        return {}
    try:
        loaded = yaml.safe_load(data[4:end].decode("utf-8")) or {}
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise TraceQueryError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(loaded, dict):
        return {}
    return loaded


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def search_set_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs = normalize_string_list(frontmatter.get("search_set_refs"))
    search_set_id = frontmatter.get("search_set_id")
    if isinstance(search_set_id, str) and search_set_id and search_set_id not in refs:
        refs.append(search_set_id)
    return sorted(set(refs))


def touched_files(frontmatter: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for key in ("files", "files_changed", "changed_files", "touched_files"):
        files.extend(normalize_string_list(frontmatter.get(key)))
    return sorted(set(files))


def status_for(kind: str, frontmatter: dict[str, Any]) -> str:
    if kind == "failure":
        resolved = frontmatter.get("resolved")
        if resolved is True:
            return "resolved"
        if resolved is False:
            return "unresolved"
    verdict = frontmatter.get("verdict")
    if isinstance(verdict, str) and verdict.strip():
        return verdict.strip()
    status = frontmatter.get("status")
    if isinstance(status, str) and status.strip():
        return status.strip()
    return "unknown"


def date_value(frontmatter: dict[str, Any]) -> str | None:
    value = frontmatter.get("date")
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def trace_files(trace_root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in TRACE_KIND_BY_DIR:
        root = trace_root / directory
        if root.is_dir():
            files.extend(path for path in root.rglob("*.md") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(trace_root).as_posix())


def catalog_record(path: Path, trace_root: Path) -> dict[str, Any]:
    kind_dir = path.relative_to(trace_root).parts[0]
    kind = TRACE_KIND_BY_DIR[kind_dir]
    frontmatter = markdown_frontmatter(path)
    return {
        "catalog_schema": "trace-catalog-v1",
        "trace": repo_relative(path),
        "kind": kind,
        "status": status_for(kind, frontmatter),
        "date": date_value(frontmatter),
        "tags": sorted(set(normalize_string_list(frontmatter.get("tags")))),
        "files": touched_files(frontmatter),
        "search_set_refs": search_set_refs(frontmatter),
        "source_sha256": file_sha256(path),
    }


def build_catalog(trace_root: Path) -> list[dict[str, Any]]:
    if not trace_root.is_dir():
        raise TraceQueryError(f"trace root does not exist: {trace_root}")
    return [catalog_record(path, trace_root) for path in trace_files(trace_root)]


def write_catalog(trace_root: Path, records: list[dict[str, Any]]) -> Path:
    path = trace_root / CATALOG_NAME
    text = "".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in records)
    path.write_text(text, encoding="utf-8")
    return path


def read_catalog(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TraceQueryError(f"cannot read catalog {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceQueryError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(record, dict):
            raise TraceQueryError(f"{path}:{line_number}: catalog row must be an object")
        records.append(record)
    return records


def stale_catalog_errors(trace_root: Path, stored_records: list[dict[str, Any]]) -> list[str]:
    current = {record["trace"]: record for record in build_catalog(trace_root)}
    stored: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    duplicate_traces: set[str] = set()
    for record in stored_records:
        trace = record.get("trace")
        if not isinstance(trace, str):
            errors.append("catalog row missing string trace")
            continue
        if trace in stored:
            duplicate_traces.add(trace)
        stored[trace] = record
    missing = sorted(set(current) - set(stored))
    extra = sorted(set(stored) - set(current))
    changed = sorted(path for path in set(current) & set(stored) if current[path] != stored[path])
    if duplicate_traces:
        errors.append(f"catalog has duplicate traces: {', '.join(sorted(duplicate_traces))}")
    if missing:
        errors.append(f"catalog missing traces: {', '.join(missing)}")
    if extra:
        errors.append(f"catalog has removed traces: {', '.join(extra)}")
    if changed:
        errors.append(f"catalog stale for traces: {', '.join(changed)}")
    return errors


def searchable_text(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("trace", "kind", "status", "date"):
        value = record.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ("tags", "files", "search_set_refs"):
        values.extend(normalize_string_list(record.get(key)))
    return "\n".join(values).lower()


def query_records(records: list[dict[str, Any]], query: str, *, limit: int) -> list[dict[str, Any]]:
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return records[:limit]
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for record in records:
        haystack = searchable_text(record)
        if all(term in haystack for term in terms):
            score = sum(haystack.count(term) for term in terms)
            trace = record.get("trace") if isinstance(record.get("trace"), str) else ""
            scored.append((score, trace, record))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [record for _, _, record in scored[:limit]]


def experiment_metadata_warnings(trace_root: Path) -> list[str]:
    warnings: list[str] = []
    experiments = trace_root / "experiments"
    if not experiments.is_dir():
        return warnings
    for path in sorted(experiments.rglob("*.md")):
        frontmatter = markdown_frontmatter(path)
        missing = sorted(field for field in EXPERIMENT_REQUIRED_FIELDS if field not in frontmatter)
        if missing:
            warnings.append(f"{repo_relative(path)}: missing experiment metadata: {', '.join(missing)}")
            continue
        kind = frontmatter.get("kind")
        if kind != "experiment":
            warnings.append(f"{repo_relative(path)}: experiment kind must be 'experiment'")
        date = frontmatter.get("date")
        if not ((isinstance(date, str) and date.strip()) or hasattr(date, "isoformat")):
            warnings.append(f"{repo_relative(path)}: experiment date must be a non-empty date or string")
        for field in ("objective", "metric", "verdict", "evaluator"):
            value = frontmatter.get(field)
            if not isinstance(value, str) or not value.strip():
                warnings.append(f"{repo_relative(path)}: experiment {field} must be a non-empty string")
        tags = frontmatter.get("tags")
        if not (
            isinstance(tags, list)
            and tags
            and all(isinstance(item, str) and item.strip() for item in tags)
        ):
            warnings.append(f"{repo_relative(path)}: experiment tags must be a non-empty list of strings")
    return warnings


def command_catalog(args: argparse.Namespace) -> int:
    records = build_catalog(args.trace_root)
    if args.write:
        path = write_catalog(args.trace_root, records)
        print(f"Wrote {len(records)} trace catalog records to {repo_relative(path)}")
    else:
        for record in records:
            print(json.dumps(record, sort_keys=True, ensure_ascii=False))
    return 0


def command_query(args: argparse.Namespace) -> int:
    if args.use_stored:
        catalog_path = args.trace_root / CATALOG_NAME
        records = read_catalog(catalog_path)
        errors = stale_catalog_errors(args.trace_root, records)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
    else:
        records = build_catalog(args.trace_root)
    for record in query_records(records, args.query, limit=args.limit):
        print(record["trace"])
    return 0


def command_check_experiments(args: argparse.Namespace) -> int:
    warnings = experiment_metadata_warnings(args.trace_root)
    for warning in warnings:
        print(warning, file=sys.stderr)
    if warnings and args.strict:
        return 1
    if not warnings:
        print("Experiment trace metadata is valid.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog = subparsers.add_parser("catalog", help="build a trace catalog")
    catalog.add_argument("--trace-root", type=Path, required=True)
    catalog.add_argument("--write", action="store_true", help=f"write {CATALOG_NAME} under trace root")
    catalog.set_defaults(func=command_catalog)

    query = subparsers.add_parser("query", help="query trace catalog metadata")
    query.add_argument("--trace-root", type=Path, required=True)
    query.add_argument("--query", required=True)
    query.add_argument("--limit", type=int, default=20)
    query.add_argument("--use-stored", action="store_true", help="use stored catalog and fail if stale")
    query.set_defaults(func=command_query)

    check_experiments = subparsers.add_parser(
        "check-experiments",
        help="warn about missing experiment frontmatter metadata",
    )
    check_experiments.add_argument("--trace-root", type=Path, required=True)
    check_experiments.add_argument("--strict", action="store_true", help="exit nonzero on warnings")
    check_experiments.set_defaults(func=command_check_experiments)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TraceQueryError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
