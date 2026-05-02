#!/usr/bin/env python3
"""Validate Codex marketplace metadata readiness.

Marketplace publication is intentionally deferred. This check protects the
current release state: no publication manifest should appear until the adapter
policy records a ready state with official schema/taxonomy evidence.
"""

from __future__ import annotations

from pathlib import Path
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


def read_policy() -> tuple[str, list[str]]:
    try:
        return POLICY_PATH.read_text(encoding="utf-8"), []
    except OSError as exc:
        return "", [f"UNREADABLE POLICY: {POLICY_PATH.relative_to(ROOT)}: {exc}"]


def missing_markers(text: str, markers: tuple[str, ...]) -> list[str]:
    normalized = " ".join(text.split())
    return [marker for marker in markers if marker not in normalized]


def existing_publication_manifests() -> list[Path]:
    return [path for path in PUBLICATION_MANIFESTS if path.exists()]


def validate() -> list[str]:
    text, errors = read_policy()
    if errors:
        return errors

    for marker in missing_markers(text, REQUIRED_DEFERRED_POLICY_MARKERS):
        errors.append(f"MISSING POLICY MARKER: {marker}")

    manifests = existing_publication_manifests()
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
    errors = validate()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    if existing_publication_manifests():
        print("Codex marketplace metadata publication markers are present.")
    else:
        print("Codex marketplace metadata validation deferred: no publication manifest exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
