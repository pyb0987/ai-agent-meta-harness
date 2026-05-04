#!/usr/bin/env python3
"""Optionally inspect local Codex CLI surface used by runtime-delivery docs.

This check proves only local CLI help-shape evidence. It does not prove that a
running Codex Desktop session surfaced plugin skills to the model or delivered
plugin runtime hook events.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys


MARKETPLACE_COMMANDS = ("add", "upgrade", "remove")
APP_SERVER_MARKERS = ("[experimental]", "generate-ts", "generate-json-schema")


@dataclass(frozen=True)
class ProbeResult:
    errors: tuple[str, ...]
    skipped: bool = False


def run_help(codex_bin: str, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [codex_bin, *args, "--help"],
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def require_markers(label: str, output: str, markers: tuple[str, ...]) -> list[str]:
    return [f"MISSING {label} HELP MARKER: {marker}" for marker in markers if marker not in output]


def probe(codex_bin: str, *, require_installed: bool = False) -> ProbeResult:
    resolved = shutil.which(codex_bin) if not Path(codex_bin).is_file() else codex_bin
    if not resolved:
        if require_installed:
            return ProbeResult((f"MISSING CODEX CLI: {codex_bin}",), skipped=False)
        message = f"SKIPPED: Codex CLI not found: {codex_bin}"
        return ProbeResult((message,), skipped=True)

    errors: list[str] = []
    marketplace = run_help(resolved, ("plugin", "marketplace"))
    if marketplace.returncode != 0:
        errors.append(f"CODEX PLUGIN MARKETPLACE HELP FAILED: {marketplace.returncode}")
        errors.append(combined_output(marketplace).strip())
    else:
        marketplace_help = combined_output(marketplace)
        errors.extend(require_markers("PLUGIN MARKETPLACE", marketplace_help, MARKETPLACE_COMMANDS))

    app_server = run_help(resolved, ("app-server",))
    if app_server.returncode != 0:
        errors.append(f"CODEX APP-SERVER HELP FAILED: {app_server.returncode}")
        errors.append(combined_output(app_server).strip())
    else:
        app_server_help = combined_output(app_server)
        errors.extend(require_markers("APP-SERVER", app_server_help, APP_SERVER_MARKERS))

    return ProbeResult(tuple(error for error in errors if error), skipped=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI executable")
    parser.add_argument(
        "--require-installed",
        action="store_true",
        help="fail instead of skipping when the Codex CLI is not installed",
    )
    args = parser.parse_args(argv)

    result = probe(args.codex_bin, require_installed=args.require_installed)
    for message in result.errors:
        stream = sys.stdout if result.skipped else sys.stderr
        print(message, file=stream)
    if result.skipped:
        return 0
    if result.errors:
        return 1
    print("Codex CLI surface probe passed: plugin marketplace and app-server help markers present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
