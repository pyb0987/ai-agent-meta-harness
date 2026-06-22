#!/usr/bin/env python3
"""Generate and verify the repo-local Codex plugin bundle.

The editable Codex adapter source lives under adapters/codex/. The plugin under
plugins/ai-agent-meta-harness/ is generated output so Codex can consume the
adapter as a local plugin without creating a second manually edited copy.
"""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "adapters" / "codex"
PLUGIN_ROOT = ROOT / "plugins" / "ai-agent-meta-harness"
IGNORED_FILE_NAMES = {".DS_Store"}
REQUIRED_SKILL_FILES = (
    "autoresearch/SKILL.md",
    "harness-engineer/SKILL.md",
    "init-codex-harness/SKILL.md",
    "multi-review/SKILL.md",
)
REQUIRED_TEMPLATE_FILES = (
    "AGENTS.md.template",
    "autoresearch-protected.txt",
    "hooks/codex-hooks.json.template",
    "hooks/pre-commit-autoresearch-protected.sh",
    "hooks/github-actions-autoresearch-protected.yml",
    "hooks/agents-autoresearch-protection.md",
)
REQUIRED_SCRIPT_FILES = (
    "check-autoresearch-protected.py",
    "check-codex-cli-surface.py",
    "check-codex-hook-schema-drift.py",
    "install-autoresearch-protection.py",
    "smoke-init-codex-project-fixtures.py",
    "smoke-local-plugin-activation.py",
    "smoke-autoresearch-hooks.py",
    "smoke-local-plugin.py",
)
REQUIRED_EXAMPLE_FILES = (
    "AGENTS.md.example",
)
REQUIRED_HOOK_FILES = (
    "experimental/harness_orientation.py",
    "experimental/harness-orientation-hooks.json.example",
)


@dataclass(frozen=True)
class Mapping:
    source: Path
    dest: Path


@dataclass(frozen=True)
class FileState:
    content: bytes
    mode: int


class TreeReader:
    def exists(self, path: Path) -> bool:
        raise NotImplementedError

    def is_dir(self, path: Path) -> bool:
        raise NotImplementedError

    def read_bytes(self, path: Path) -> bytes:
        raise NotImplementedError

    def mode(self, path: Path) -> int:
        raise NotImplementedError

    def iter_files(self, base: Path):
        raise NotImplementedError


class FilesystemReader(TreeReader):
    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def read_bytes(self, path: Path) -> bytes:
        return path.read_bytes()

    def mode(self, path: Path) -> int:
        return stat.S_IMODE(path.stat().st_mode)

    def iter_files(self, base: Path):
        return _iter_files(base)


class IndexReader(TreeReader):
    def __init__(self) -> None:
        self.files = _read_git_index()
        self.dirs = {parent for path in self.files for parent in path.parents}

    def _relative(self, path: Path) -> Path:
        return path.relative_to(ROOT)

    def exists(self, path: Path) -> bool:
        rel = self._relative(path)
        return rel in self.files or rel in self.dirs

    def is_dir(self, path: Path) -> bool:
        return self._relative(path) in self.dirs

    def read_bytes(self, path: Path) -> bytes:
        return self.files[self._relative(path)].content

    def mode(self, path: Path) -> int:
        return self.files[self._relative(path)].mode

    def iter_files(self, base: Path):
        base_rel = self._relative(base)
        for rel in sorted(self.files):
            if rel.name in IGNORED_FILE_NAMES:
                continue
            try:
                rel.relative_to(base_rel)
            except ValueError:
                continue
            yield ROOT / rel


def _iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.name not in IGNORED_FILE_NAMES:
            yield path


def _git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _inside_git_worktree() -> bool:
    result = _git(["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == b"true"


def _read_git_index() -> dict[Path, FileState]:
    result = _git(["ls-files", "-s", "-z"])
    files: dict[Path, FileState] = {}
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode_text, _object_id, stage_text = metadata.split()
        if stage_text != b"0":
            continue
        rel = Path(raw_path.decode("utf-8"))
        show = _git(["show", f":{rel.as_posix()}"])
        files[rel] = FileState(show.stdout, int(mode_text, 8) & 0o777)
    return files


def _check_reader() -> TreeReader:
    if _inside_git_worktree():
        return IndexReader()
    return FilesystemReader()


def validate_source_tree(reader: TreeReader | None = None) -> list[str]:
    reader = reader or FilesystemReader()
    errors: list[str] = []
    required = (
        ("skills", REQUIRED_SKILL_FILES),
        ("templates", REQUIRED_TEMPLATE_FILES),
        ("scripts", REQUIRED_SCRIPT_FILES),
        ("examples", REQUIRED_EXAMPLE_FILES),
        ("hooks", REQUIRED_HOOK_FILES),
    )
    for directory, files in required:
        base = SOURCE_ROOT / directory
        if not reader.is_dir(base):
            errors.append(f"MISSING SOURCE DIR: {base.relative_to(ROOT)}")
            continue
        discovered = [path for path in reader.iter_files(base)]
        if not discovered:
            errors.append(f"EMPTY SOURCE DIR: {base.relative_to(ROOT)}")
        for file_name in files:
            path = base / file_name
            if not reader.exists(path):
                errors.append(f"MISSING REQUIRED SOURCE: {path.relative_to(ROOT)}")
    return errors


def validate_all_owned(mappings: list[Mapping], reader: TreeReader | None = None) -> list[str]:
    reader = reader or FilesystemReader()
    mapped_sources = {mapping.source for mapping in mappings}
    errors: list[str] = []
    for directory in ("skills", "templates", "scripts", "examples", "hooks"):
        base = SOURCE_ROOT / directory
        if not reader.exists(base):
            continue
        for source in reader.iter_files(base):
            if source not in mapped_sources:
                errors.append(f"UNMAPPED SOURCE: {source.relative_to(ROOT)}")
    return errors


def build_mappings(reader: TreeReader | None = None) -> list[Mapping]:
    reader = reader or FilesystemReader()
    mappings = [
        Mapping(
            SOURCE_ROOT / "plugin" / ".codex-plugin" / "plugin.json",
            PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        ),
        Mapping(SOURCE_ROOT / "README.md", PLUGIN_ROOT / "README.md"),
        Mapping(SOURCE_ROOT / "hook-schema.md", PLUGIN_ROOT / "hook-schema.md"),
        Mapping(SOURCE_ROOT / "plugin-scope.md", PLUGIN_ROOT / "plugin-scope.md"),
    ]
    skills_root = SOURCE_ROOT / "skills"
    for source in reader.iter_files(skills_root):
        mappings.append(Mapping(source, PLUGIN_ROOT / "skills" / source.relative_to(skills_root)))

    templates_root = SOURCE_ROOT / "templates"
    for source in reader.iter_files(templates_root):
        mappings.append(Mapping(source, PLUGIN_ROOT / "templates" / source.relative_to(templates_root)))

    scripts_root = SOURCE_ROOT / "scripts"
    for source in reader.iter_files(scripts_root):
        mappings.append(Mapping(source, PLUGIN_ROOT / "scripts" / source.relative_to(scripts_root)))

    examples_root = SOURCE_ROOT / "examples"
    if reader.exists(examples_root):
        for source in reader.iter_files(examples_root):
            mappings.append(Mapping(source, PLUGIN_ROOT / "examples" / source.relative_to(examples_root)))

    hooks_root = SOURCE_ROOT / "hooks"
    for source in reader.iter_files(hooks_root):
        mappings.append(Mapping(source, PLUGIN_ROOT / "hooks" / source.relative_to(hooks_root)))
    return mappings


def validate_manifest(path: Path, reader: TreeReader | None = None) -> list[str]:
    reader = reader or FilesystemReader()
    errors: list[str] = []
    try:
        manifest = json.loads(reader.read_bytes(path).decode("utf-8"))
    except (FileNotFoundError, KeyError):
        return [f"MISSING MANIFEST: {path.relative_to(ROOT)}"]
    except OSError as exc:
        return [f"UNREADABLE MANIFEST: {path.relative_to(ROOT)}: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"INVALID JSON: {path.relative_to(ROOT)}: {exc}"]

    if manifest.get("name") != "ai-agent-meta-harness":
        errors.append("plugin.json name must be ai-agent-meta-harness")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin.json skills must point to ./skills/")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json interface must be an object")
    elif not interface.get("displayName"):
        errors.append("plugin.json interface.displayName is required")
    return errors


def render_diff(source_path: Path, dest_path: Path, source: bytes, dest: bytes) -> list[str]:
    try:
        source_text = source.decode("utf-8")
        dest_text = dest.decode("utf-8")
    except UnicodeDecodeError:
        return ["Binary files differ"]
    return list(
        difflib.unified_diff(
            source_text.splitlines(),
            dest_text.splitlines(),
            fromfile=str(source_path.relative_to(ROOT)),
            tofile=str(dest_path.relative_to(ROOT)),
            lineterm="",
        )
    )


def find_extra_files(expected: set[Path]) -> list[Path]:
    if not PLUGIN_ROOT.exists():
        return []
    return [path for path in _iter_files(PLUGIN_ROOT) if path not in expected]


def find_extra_files_in_reader(expected: set[Path], reader: TreeReader) -> list[Path]:
    if not reader.exists(PLUGIN_ROOT):
        return []
    return [path for path in reader.iter_files(PLUGIN_ROOT) if path not in expected]


def write_files(mappings: list[Mapping]) -> int:
    source_errors = validate_source_tree() + validate_all_owned(mappings)
    if source_errors:
        for error in source_errors:
            print(error, file=sys.stderr)
        return 1

    missing_sources = [m.source for m in mappings if not m.source.exists()]
    if missing_sources:
        for path in missing_sources:
            print(f"MISSING SOURCE: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    manifest_errors = validate_manifest(SOURCE_ROOT / "plugin" / ".codex-plugin" / "plugin.json")
    if manifest_errors:
        for error in manifest_errors:
            print(error, file=sys.stderr)
        return 1

    for mapping in mappings:
        mapping.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mapping.source, mapping.dest)

    extra = find_extra_files({m.dest for m in mappings})
    if extra:
        print("Generated plugin contains extra files not owned by the sync map:", file=sys.stderr)
        for path in extra:
            print(f"EXTRA: {path.relative_to(ROOT)}", file=sys.stderr)
        print("Remove or add these files to the sync map before --check can pass.", file=sys.stderr)
        return 1

    print(f"Synced {len(mappings)} files into {PLUGIN_ROOT.relative_to(ROOT)}.")
    return 0


def check_files(mappings: list[Mapping], reader: TreeReader | None = None) -> int:
    reader = reader or _check_reader()
    failed = False
    expected = {m.dest for m in mappings}

    for error in validate_source_tree(reader) + validate_all_owned(mappings, reader):
        print(error, file=sys.stderr)
        failed = True

    for mapping in mappings:
        if not reader.exists(mapping.source):
            print(f"MISSING SOURCE: {mapping.source.relative_to(ROOT)}", file=sys.stderr)
            failed = True
            continue
        if not reader.exists(mapping.dest):
            print(f"MISSING GENERATED: {mapping.dest.relative_to(ROOT)}", file=sys.stderr)
            failed = True
            continue
        source = reader.read_bytes(mapping.source)
        dest = reader.read_bytes(mapping.dest)
        if source != dest:
            failed = True
            print(
                f"OUT OF SYNC: {mapping.dest.relative_to(ROOT)} "
                f"(canonical: {mapping.source.relative_to(ROOT)})",
                file=sys.stderr,
            )
            for line in render_diff(mapping.source, mapping.dest, source, dest)[:80]:
                print(line, file=sys.stderr)
        source_mode = reader.mode(mapping.source)
        dest_mode = reader.mode(mapping.dest)
        if source_mode != dest_mode:
            failed = True
            print(
                f"MODE MISMATCH: {mapping.dest.relative_to(ROOT)} "
                f"{dest_mode:o} (canonical: {mapping.source.relative_to(ROOT)} {source_mode:o})",
                file=sys.stderr,
            )

    for path in find_extra_files_in_reader(expected, reader):
        print(f"EXTRA GENERATED: {path.relative_to(ROOT)}", file=sys.stderr)
        failed = True

    for error in validate_manifest(PLUGIN_ROOT / ".codex-plugin" / "plugin.json", reader):
        print(error, file=sys.stderr)
        failed = True

    if failed:
        return 1
    print("Codex plugin bundle is in sync.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="materialize generated plugin files")
    mode.add_argument("--check", action="store_true", help="verify generated plugin files without modifying them")
    args = parser.parse_args(argv)

    if args.write:
        mappings = build_mappings()
        return write_files(mappings)
    reader = _check_reader()
    mappings = build_mappings(reader)
    return check_files(mappings, reader)


if __name__ == "__main__":
    raise SystemExit(main())
