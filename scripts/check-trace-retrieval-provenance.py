#!/usr/bin/env python3
"""Validate trace retrieval provenance blocks.

This checker enforces the Plan 16 structural boundary: raw trace evidence must
cite byte-matching quotes from raw trace files. It does not judge semantic
relevance or retrieval completeness.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import sys
from collections.abc import Callable

import yaml


ROOT = Path(__file__).resolve().parents[1]
TRACE_RECORD_PARTS = {"evolution", "failures"}
VALID_MODES = {"selective", "full_scan", "not_needed"}
CATALOG_NAMES = {"trace-catalog.jsonl", "trace-catalog.yml", "trace-catalog.yaml"}


class ProvenanceError(ValueError):
    pass


def git_staged_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ProvenanceError(result.stderr.strip() or "git diff --cached failed")
    return [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_index_bytes(path: Path) -> bytes:
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "show", f":{rel}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode == 0:
        return result.stdout
    raise FileNotFoundError(f"{rel} is not staged in the git index")


def worktree_bytes(path: Path) -> bytes:
    return path.read_bytes()


def markdown_frontmatter(data: bytes, source: Path) -> dict:
    if not data.startswith(b"---\n"):
        raise ProvenanceError(f"{source}: missing YAML frontmatter")
    end = data.find(b"\n---\n", 4)
    if end == -1:
        raise ProvenanceError(f"{source}: unterminated YAML frontmatter")
    raw = data[4:end]
    try:
        loaded = yaml.safe_load(raw.decode("utf-8")) or {}
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ProvenanceError(f"{source}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ProvenanceError(f"{source}: YAML frontmatter must be a mapping")
    return loaded


def trace_root_for(path: Path) -> Path | None:
    parts = path.parts
    for index, part in enumerate(parts):
        if part == "traces" and index > 0:
            return Path(*parts[: index + 1])
    return None


def is_trace_record(path: Path) -> bool:
    if path.suffix != ".md":
        return False
    parts = set(path.parts)
    return "traces" in parts and bool(parts & TRACE_RECORD_PARTS)


def resolve_repo_path(repo_root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def require_under(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ProvenanceError(f"{label}: {path} is outside trace root {root}") from exc


def parse_lines(value: object, source: str) -> tuple[int, int]:
    if isinstance(value, int):
        start = end = value
    elif isinstance(value, str):
        text = value.strip()
        if "-" in text:
            left, right = text.split("-", 1)
            if not left.strip().isdigit() or not right.strip().isdigit():
                raise ProvenanceError(f"{source}: invalid lines value {value!r}")
            start = int(left)
            end = int(right)
        elif text.isdigit():
            start = end = int(text)
        else:
            raise ProvenanceError(f"{source}: invalid lines value {value!r}")
    elif (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) for item in value)
    ):
        start, end = value
    else:
        raise ProvenanceError(f"{source}: invalid lines value {value!r}")
    if start < 1 or end < start:
        raise ProvenanceError(f"{source}: line range must be positive and ordered")
    return start, end


def line_span(data: bytes, start: int, end: int, source: str) -> bytes:
    lines = data.splitlines(keepends=True)
    if end > len(lines):
        raise ProvenanceError(f"{source}: line range {start}-{end} exceeds file length {len(lines)}")
    return b"".join(lines[start - 1 : end])


def validate_raw_trace_ref(
    ref: object,
    *,
    repo_root: Path,
    trace_root: Path,
    read_bytes: Callable[[Path], bytes],
    source: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(ref, dict):
        return [f"{source}: raw_trace_refs entries must be mappings"]
    file_value = ref.get("file")
    if not isinstance(file_value, str) or not file_value.strip():
        return [f"{source}: raw_trace_refs entry missing file"]
    ref_path = resolve_repo_path(repo_root, file_value)
    try:
        require_under(ref_path, trace_root, source)
    except ProvenanceError as exc:
        errors.append(str(exc))
    if ref_path.name in CATALOG_NAMES:
        errors.append(f"{source}: catalog files cannot be raw_trace_refs: {file_value}")
    try:
        raw = read_bytes(ref_path)
    except OSError as exc:
        errors.append(f"{source}: cannot read raw trace ref {file_value}: {exc}")
        return errors
    quote = ref.get("quote")
    if not isinstance(quote, str) or not quote:
        errors.append(f"{source}: raw trace ref missing non-empty quote")
        return errors
    try:
        start, end = parse_lines(ref.get("lines"), source)
    except ProvenanceError as exc:
        errors.append(str(exc))
        return errors
    try:
        span = line_span(raw, start, end, source)
    except ProvenanceError as exc:
        errors.append(str(exc))
        return errors
    quote_bytes = quote.encode("utf-8")
    if quote_bytes not in span:
        errors.append(f"{source}: quote bytes do not match cited lines in {file_value}:{start}-{end}")
    return errors


def validate_retrieval(
    frontmatter: dict,
    *,
    path: Path,
    repo_root: Path,
    read_bytes: Callable[[Path], bytes],
) -> list[str]:
    errors: list[str] = []
    if "retrieval_mode" in frontmatter:
        errors.append(f"{path}: use retrieval.mode, not top-level retrieval_mode")
    retrieval = frontmatter.get("retrieval")
    if not isinstance(retrieval, dict):
        return [f"{path}: missing retrieval mapping"]
    mode = retrieval.get("mode")
    if mode not in VALID_MODES:
        errors.append(f"{path}: retrieval.mode must be one of {sorted(VALID_MODES)}")
        return errors
    reason = retrieval.get("reason")
    if mode in {"full_scan", "not_needed"} and (
        not isinstance(reason, str) or not reason.strip()
    ):
        errors.append(f"{path}: retrieval.mode {mode} requires a non-empty reason")
    trace_root = trace_root_for(path)
    if trace_root is None:
        errors.append(f"{path}: cannot infer trace root")
        return errors
    refs = retrieval.get("raw_trace_refs")
    if mode in {"selective", "full_scan"}:
        if not isinstance(refs, list) or not refs:
            errors.append(f"{path}: retrieval.mode {mode} requires raw_trace_refs")
            return errors
        for index, ref in enumerate(refs, start=1):
            errors.extend(
                validate_raw_trace_ref(
                    ref,
                    repo_root=repo_root,
                    trace_root=trace_root,
                    read_bytes=read_bytes,
                    source=f"{path}: raw_trace_refs[{index}]",
                )
            )
    elif refs:
        errors.append(f"{path}: retrieval.mode not_needed must not include raw_trace_refs")
    return errors


def validate_file(
    path: Path,
    *,
    repo_root: Path = ROOT,
    require_retrieval: bool = True,
    read_bytes: Callable[[Path], bytes] = worktree_bytes,
) -> list[str]:
    try:
        data = read_bytes(path)
    except OSError as exc:
        return [f"{path}: cannot read file: {exc}"]
    try:
        frontmatter = markdown_frontmatter(data, path)
    except ProvenanceError as exc:
        return [str(exc)]
    if "retrieval" not in frontmatter and "retrieval_mode" not in frontmatter:
        if require_retrieval:
            return [f"{path}: missing retrieval block"]
        return []
    return validate_retrieval(
        frontmatter,
        path=path.resolve(),
        repo_root=repo_root.resolve(),
        read_bytes=read_bytes,
    )


def validate_paths(
    paths: list[Path],
    *,
    repo_root: Path = ROOT,
    require_retrieval: bool = True,
    read_bytes: Callable[[Path], bytes] = worktree_bytes,
) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not is_trace_record(path):
            continue
        errors.extend(
            validate_file(
                path,
                repo_root=repo_root,
                require_retrieval=require_retrieval,
                read_bytes=read_bytes,
            )
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="trace files to validate")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="validate staged evolution/failure trace records",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="validate retrieval blocks when present but do not require them",
    )
    args = parser.parse_args(argv)

    try:
        if args.staged:
            paths = git_staged_paths()
            read_bytes = git_index_bytes
        else:
            paths = [Path(path) for path in args.paths]
            read_bytes = worktree_bytes
        errors = validate_paths(
            [(ROOT / path).resolve() if not path.is_absolute() else path.resolve() for path in paths],
            repo_root=ROOT,
            require_retrieval=not args.allow_missing,
            read_bytes=read_bytes,
        )
    except ProvenanceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Trace retrieval provenance is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
