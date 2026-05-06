#!/usr/bin/env python3
"""Report and guard the frozen v1 archive boundary."""

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PREFIX = "archive/v1/"
IMPORT_MANIFEST = "archive/v1/IMPORT.md"
REQUIRED_WAIVER_FIELDS = ("actor=", "role=", "date=", "reason=", "source=")
ALLOWED_WAIVER_ROLES = {"maintainer", "reviewer"}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class ChangedPath:
    status: str
    paths: tuple[str, ...]

    @property
    def display(self) -> str:
        return f"{self.status} {' -> '.join(self.paths)}"


def git(root: Path, args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def has_head(root: Path) -> bool:
    return git(root, ["rev-parse", "--verify", "HEAD"]).returncode == 0


def tree_has_v1_archive(root: Path, ref: str = "HEAD") -> bool:
    if ref == "HEAD" and not has_head(root):
        return False
    result = git(root, ["ls-tree", "-r", "--name-only", ref, "--", "archive/v1"])
    return result.returncode == 0 and bool(result.stdout.strip())


def merge_base(root: Path, base_ref: str) -> str:
    result = git(root, ["merge-base", base_ref, "HEAD"])
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or f"failed to resolve merge-base for {base_ref}...HEAD")
    return result.stdout.strip()


def changed_v1_paths(root: Path, *, staged: bool, base_ref: str | None = None) -> list[ChangedPath]:
    if base_ref is not None:
        result = git(root, ["diff", "--name-status", f"{base_ref}...HEAD"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "failed to read base-ref archive/v1 changes")
        return parse_name_status(result.stdout)

    if staged:
        result = git(root, ["diff", "--cached", "--name-status"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "failed to read staged archive/v1 changes")
        return parse_name_status(result.stdout)

    result = git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "failed to read archive/v1 status")
    return parse_porcelain_status(result.stdout)


def parse_name_status(text: str) -> list[ChangedPath]:
    changes: list[ChangedPath] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        status, *paths = line.split("\t")
        relevant_paths = tuple(path for path in paths if is_v1_archive_path(path))
        if relevant_paths:
            changes.append(ChangedPath(status=status, paths=tuple(paths)))
    return changes


def parse_porcelain_status(text: str) -> list[ChangedPath]:
    changes: list[ChangedPath] = []
    for line in text.splitlines():
        if len(line) < 4:
            continue
        status = line[:2].strip() or line[:2]
        path = line[3:]
        if " -> " in path:
            paths = tuple(part.strip() for part in path.split(" -> ", 1))
        else:
            paths = (path,)
        if any(is_v1_archive_path(part) for part in paths):
            changes.append(ChangedPath(status=status, paths=paths))
    return changes


def is_v1_archive_path(path: str) -> bool:
    return path == "archive/v1" or path.startswith(ARCHIVE_PREFIX)


def source_for_archive_path(path: str) -> str | None:
    if path == "archive/v1/MAINTENANCE.md":
        return "MAINTENANCE.md"
    if path.startswith("archive/v1/backlog/"):
        return path.removeprefix("archive/v1/")
    return None


def archive_import_paths(root: Path, *, staged: bool, base_ref: str | None) -> list[str]:
    if base_ref is not None:
        result = git(root, ["ls-tree", "-r", "--name-only", "HEAD", "--", "archive/v1"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "failed to list HEAD archive/v1")
        return sorted(path for path in result.stdout.splitlines() if is_v1_archive_path(path))
    if staged:
        result = git(root, ["diff", "--cached", "--name-status"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "failed to list staged archive/v1 import")
        paths: set[str] = set()
        for change in parse_name_status(result.stdout):
            paths.update(path for path in change.paths if is_v1_archive_path(path))
        return sorted(paths)
    return sorted(
        path.relative_to(root).as_posix()
        for path in (root / "archive" / "v1").rglob("*")
        if path.is_file()
    )


def read_git_text(root: Path, ref: str, path: str) -> str | None:
    result = git(root, ["show", f"{ref}:{path}"])
    if result.returncode != 0:
        return None
    return result.stdout


def read_archive_text(root: Path, path: str, *, staged: bool, base_ref: str | None) -> str | None:
    if base_ref is not None:
        return read_git_text(root, "HEAD", path)
    if staged:
        result = git(root, ["show", f":{path}"])
        if result.returncode != 0:
            return None
        return result.stdout
    try:
        return (root / path).read_text(encoding="utf-8")
    except OSError:
        return None


def archive_import_manifest(root: Path, *, staged: bool, base_ref: str | None) -> dict[str, str]:
    text = read_archive_text(root, IMPORT_MANIFEST, staged=staged, base_ref=base_ref)
    if text is None:
        return {}
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("| `archive/v1/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        path = cells[0].strip("`")
        digest = cells[1].strip("`")
        if len(digest) == 64:
            entries[path] = digest
    return entries


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def initial_import_result(root: Path, *, staged: bool, base_ref: str | None) -> tuple[list[str], list[str]]:
    source_ref = merge_base(root, base_ref) if base_ref is not None else "HEAD"
    errors: list[str] = []
    manifested: list[str] = []
    manifest = archive_import_manifest(root, staged=staged, base_ref=base_ref)
    paths = archive_import_paths(root, staged=staged, base_ref=base_ref)
    if not paths:
        return ["initial archive/v1 import has no comparable v1 source files"], []
    for archive_path in paths:
        if archive_path == IMPORT_MANIFEST:
            if not manifest:
                errors.append(f"{archive_path}: import manifest has no hash entries")
            continue
        source_path = source_for_archive_path(archive_path)
        archive_text = read_archive_text(root, archive_path, staged=staged, base_ref=base_ref)
        manifest_digest = manifest.get(archive_path)
        archive_digest = sha256_text(archive_text) if archive_text is not None else None
        if source_path is None:
            if archive_digest and manifest_digest == archive_digest:
                manifested.append(f"{archive_path}: no comparable v1 source; manifest hash matches")
            else:
                errors.append(f"{archive_path}: no comparable v1 source and manifest hash is absent")
            continue
        source_text = read_git_text(root, source_ref, source_path)
        if source_text is None:
            if archive_digest and manifest_digest == archive_digest:
                manifested.append(f"{archive_path}: source {source_ref}:{source_path} missing; manifest hash matches")
            else:
                errors.append(f"{archive_path}: source {source_ref}:{source_path} is missing and manifest hash is absent")
        elif archive_text is None:
            errors.append(f"{archive_path}: archive content is unreadable")
        elif archive_text != source_text:
            if manifest_digest == archive_digest:
                manifested.append(f"{archive_path}: differs from {source_ref}:{source_path}; manifest hash matches")
            else:
                errors.append(
                    f"{archive_path}: does not match source {source_ref}:{source_path} "
                    "and manifest hash is absent"
                )
    return errors, manifested


def valid_waiver_reason(reason: str | None) -> bool:
    return waiver_reason_errors(reason) == []


def waiver_reason_errors(reason: str | None, root: Path = ROOT) -> list[str]:
    if not reason or not reason.strip():
        return ["waiver reason is empty"]
    fields: dict[str, str] = {}
    for token in reason.split():
        if "=" not in token:
            return [f"waiver token lacks key=value form: {token}"]
        key, value = token.split("=", 1)
        if not key:
            return ["waiver field has empty key"]
        if key in fields:
            return [f"waiver field is duplicated: {key}"]
        fields[key] = value
    required = {field.rstrip("=") for field in REQUIRED_WAIVER_FIELDS}
    if not required.issubset(fields):
        missing = ", ".join(sorted(required - set(fields)))
        return [f"waiver field(s) missing: {missing}"]
    if any(not fields[key].strip() for key in required):
        return ["waiver field values must be non-empty"]
    if fields["role"] not in ALLOWED_WAIVER_ROLES:
        return [f"waiver role must be one of: {', '.join(sorted(ALLOWED_WAIVER_ROLES))}"]
    if not ISO_DATE_RE.match(fields["date"]):
        return ["waiver date must use YYYY-MM-DD"]
    try:
        dt.date.fromisoformat(fields["date"])
    except ValueError:
        return ["waiver date must be a real calendar date"]
    source = fields["source"]
    if source.startswith("file:"):
        path = root / source.removeprefix("file:")
        if not path.exists():
            return [f"waiver source file does not exist: {source}"]
    elif source.startswith("git:"):
        ref = source.removeprefix("git:")
        result = git(root, ["rev-parse", "--verify", ref])
        if result.returncode != 0:
            return [f"waiver source git ref does not resolve: {source}"]
    else:
        return ["waiver source must use file:<path> or git:<ref>"]
    return []


def validate(
    root: Path = ROOT,
    *,
    staged: bool = False,
    base_ref: str | None = None,
    allow_v1_archive_changes: bool = False,
    reason: str | None = None,
) -> tuple[list[str], list[str]]:
    if staged and base_ref is not None:
        return [], ["--staged and --base-ref are mutually exclusive"]
    messages = [
        "v1 archive boundary: archive/v1 is frozen historical evidence; "
        "legacy v1 compatibility gates do not actively revalidate those records."
    ]
    changes = changed_v1_paths(root, staged=staged, base_ref=base_ref)
    if not changes:
        messages.append("v1 archive boundary: no archive/v1 changes detected.")
        return messages, []

    changed_list = ", ".join(change.display for change in changes)
    baseline_ref = merge_base(root, base_ref) if base_ref is not None else "HEAD"
    baseline_has_archive = tree_has_v1_archive(root, baseline_ref)
    if not baseline_has_archive:
        import_errors, manifested = initial_import_result(root, staged=staged, base_ref=base_ref)
        if import_errors:
            return messages, [
                "initial archive/v1 import is not a faithful or manifested relocation of v1 evidence:",
                *import_errors,
            ]
        messages.append(
            "v1 archive boundary: initial archive/v1 import detected; "
            "comparable v1 source files match or are manifest-pinned; "
            "future archive changes require an explicit waiver."
        )
        if manifested:
            messages.append(
                "v1 archive boundary: manifest covers local pre-v2 snapshot divergence for "
                f"{len(manifested)} file(s)."
            )
        messages.append(f"v1 archive boundary: changed paths: {changed_list}")
        return messages, []

    waiver_errors = waiver_reason_errors(reason, root=root)
    if allow_v1_archive_changes and not waiver_errors:
        messages.append(f"v1 archive boundary: archive/v1 change waiver accepted: {reason.strip()}")
        messages.append(f"v1 archive boundary: changed paths: {changed_list}")
        return messages, []

    errors = [
        "archive/v1 is frozen; changes require --allow-v1-archive-changes "
        "--reason 'actor=<name> role=<maintainer|reviewer> date=<YYYY-MM-DD> "
        "reason=<why> source=<file:path|git:ref>'.",
        f"archive/v1 changed paths: {changed_list}",
    ]
    if allow_v1_archive_changes:
        errors.extend(f"invalid archive/v1 waiver: {error}" for error in waiver_errors)
    return messages, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true", help="check staged archive/v1 changes")
    parser.add_argument("--base-ref", help="check archive/v1 changes in REF...HEAD")
    parser.add_argument(
        "--allow-v1-archive-changes",
        action="store_true",
        help="permit archive/v1 changes only with an explicit reason",
    )
    parser.add_argument("--reason", help="maintainer/reviewer reason for a v1 archive change waiver")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        messages, errors = validate(
            args.root,
            staged=args.staged,
            base_ref=args.base_ref,
            allow_v1_archive_changes=args.allow_v1_archive_changes,
            reason=args.reason,
        )
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 2

    for message in messages:
        print(message)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
