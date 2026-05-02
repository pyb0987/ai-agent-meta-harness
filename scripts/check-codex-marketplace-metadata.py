#!/usr/bin/env python3
"""Validate Codex marketplace metadata readiness.

Marketplace publication is intentionally deferred. This check protects the
current release state: no publication manifest should appear until the adapter
policy records a ready state with official schema/taxonomy evidence.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "adapters" / "codex" / "plugin-scope.md"
PUBLICATION_MANIFESTS = (
    ROOT / ".agents" / "plugins" / "marketplace.json",
)

REQUIRED_DEFERRED_POLICY_MARKERS = (
    "Marketplace metadata is a release surface",
    "not part of the local-only dogfood path",
    "Official source check (2026-05-03)",
    "no publication manifest exists",
)

READY_POLICY_MARKERS = (
    "Marketplace publication ready: yes",
    "Official marketplace schema:",
    "Official marketplace taxonomy:",
    "Generated metadata source:",
)


def _git(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _inside_git_worktree() -> bool:
    result = _git(["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_index_text(path: Path) -> tuple[str, list[str]]:
    relative = _relative(path)
    result = _git(["show", f":{relative}"])
    if result.returncode != 0:
        return "", [f"UNREADABLE STAGED POLICY: {relative}: {result.stderr.strip()}"]
    return result.stdout, []


def _index_contains(path: Path) -> bool:
    result = _git(["ls-files", "--error-unmatch", "--", _relative(path)])
    return result.returncode == 0


def read_policy(*, use_index: bool = False) -> tuple[str, list[str]]:
    if use_index:
        return _read_index_text(POLICY_PATH)
    try:
        return POLICY_PATH.read_text(encoding="utf-8"), []
    except OSError as exc:
        return "", [f"UNREADABLE POLICY: {POLICY_PATH.relative_to(ROOT)}: {exc}"]


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in markers if marker not in normalized]


def existing_publication_manifests(*, use_index: bool = False) -> list[Path]:
    manifests = {path for path in PUBLICATION_MANIFESTS if path.exists()}
    if use_index:
        manifests.update(path for path in PUBLICATION_MANIFESTS if _index_contains(path))
    return sorted(manifests)


def validate(*, use_index: bool = False) -> list[str]:
    text, errors = read_policy(use_index=use_index)
    if errors:
        return errors

    for marker in missing_markers(text, REQUIRED_DEFERRED_POLICY_MARKERS):
        errors.append(f"MISSING POLICY MARKER: {marker}")

    manifests = existing_publication_manifests(use_index=use_index)
    if not manifests:
        return errors

    missing_ready = missing_markers(text, READY_POLICY_MARKERS)
    for path in manifests:
        rel = path.relative_to(ROOT)
        if missing_ready:
            errors.append(
                f"MARKETPLACE METADATA NOT READY: {rel} exists before policy records "
                "official schema/taxonomy evidence and generated metadata source"
            )
        elif path.is_dir():
            errors.append(f"INVALID MARKETPLACE MANIFEST: {rel} is a directory")
        elif not path.is_file():
            errors.append(f"INVALID MARKETPLACE MANIFEST: {rel} is not a regular file")
    return errors


def main() -> int:
    use_index = _inside_git_worktree()
    errors = validate(use_index=use_index)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if existing_publication_manifests(use_index=use_index):
        print("Codex marketplace metadata publication markers are present.")
    else:
        print("Codex marketplace metadata validation deferred: no publication manifest exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
