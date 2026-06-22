#!/usr/bin/env python3
"""Experimental Codex orientation hooks for AI Agent Meta-Harness.

These hooks are intentionally not enforcement. They provide small, model-visible
project orientation when manually wired into a Codex hook config. The generated
plugin manifest must not advertise them as active runtime hooks until runtime
delivery evidence exists.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


VALID_MODES = {
    "normal",
    "harness-evolution",
    "autoresearch-setup",
    "autoresearch-run",
    "multi-review",
    "off",
}

COMMAND_TO_MODE = {
    "/harness normal": "normal",
    "/harness evolve": "harness-evolution",
    "/harness autoresearch-setup": "autoresearch-setup",
    "/harness autoresearch-run": "autoresearch-run",
    "/harness multi-review": "multi-review",
    "/harness off": "off",
}

STATE_FILE = "harness-mode.txt"


def state_dir() -> Path:
    for name in ("AI_AGENT_META_HARNESS_STATE_DIR", "PLUGIN_DATA", "CODEX_PLUGIN_DATA"):
        value = os.environ.get(name)
        if value:
            return Path(value)
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "ai-agent-meta-harness-state"
    return Path.home() / ".cache" / "ai-agent-meta-harness"


def state_path() -> Path:
    return state_dir() / STATE_FILE


def read_mode() -> tuple[str, str | None]:
    try:
        raw = state_path().read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "normal", None
    except OSError as exc:
        return "normal", f"state unreadable: {exc}"
    if raw in VALID_MODES:
        return raw, None
    return "normal", "ignored invalid mode state"


def write_mode(mode: str) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(mode + "\n", encoding="utf-8")


def load_hook_input() -> dict[str, object]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def find_trace_roots(project_root: Path) -> list[Path]:
    candidates = [project_root / ".harness" / "traces", project_root / ".claude" / "traces"]
    return [path for path in candidates if path.exists()]


def rel(project_root: Path, path: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def parse_active_search_set(search_set: Path) -> tuple[list[str], list[str]]:
    try:
        lines = search_set.read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], []

    in_active = False
    titles: list[str] = []
    verifies: list[str] = []
    for line in lines:
        if line.startswith("## "):
            in_active = line.strip() == "## Active"
            continue
        if not in_active:
            continue
        if line.startswith("### "):
            titles.append(line[4:].strip())
        if line.startswith("- **verify**:"):
            verify = line.split(":", 1)[1].strip()
            if verify.startswith("`") and verify.endswith("`") and len(verify) >= 2:
                verify = verify[1:-1]
            verifies.append(verify)
    return titles, verifies


def unresolved_failure_count(trace_root: Path) -> int | str:
    failures = trace_root / "failures"
    if not failures.is_dir():
        return "unknown"
    count = 0
    for path in failures.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "resolved: false" in text:
            count += 1
    return count


def detect_protection_level(project_root: Path) -> str:
    agents = project_root / "AGENTS.md"
    docs = project_root / "docs" / "autoresearch.md"
    for path in (agents, docs):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if "Protection level:" in line:
                    return line.split("Protection level:", 1)[1].strip() or "unknown_not_evidence"
        except OSError:
            continue
    protected = project_root / ".harness" / "autoresearch-protected.txt"
    checker = project_root / "scripts" / "check-autoresearch-protected.py"
    if protected.exists() or checker.exists():
        return "assets_detected_not_evidence"
    return "unknown_not_evidence"


def orientation_context(project_root: Path) -> str:
    mode, state_note = read_mode()
    trace_roots = find_trace_roots(project_root)
    chosen = trace_roots[0] if trace_roots else None
    search_set = chosen / "search-set.md" if chosen else None
    titles: list[str] = []
    verifies: list[str] = []
    if search_set and search_set.exists():
        titles, verifies = parse_active_search_set(search_set)

    lines = [
        "AI Agent Meta-Harness orientation hook",
        "This context is orientation only, not evidence and not enforcement.",
        f"mode: {mode}",
        f"detected_trace_root: {rel(project_root, chosen) if chosen else 'not_detected'}",
        "trace_root_candidates: "
        + (", ".join(rel(project_root, root) for root in trace_roots) if trace_roots else "none"),
        f"search_set: {rel(project_root, search_set) if search_set and search_set.exists() else 'not_detected'}",
        f"active_search_set_cases: {len(titles)}",
        f"active_verify_examples: {', '.join(verifies[:3]) if verifies else 'none_detected'}",
        f"unresolved_failures: {unresolved_failure_count(chosen) if chosen else 'unknown'}",
        f"autoresearch_protection_level: {detect_protection_level(project_root)}",
        "reminder: inspect raw traces before making historical claims.",
        "reminder: run relevant Active verify commands before and after harness-affecting changes when practical.",
        "runtime_delivery: smoke tests for this hook prove script behavior only; plugin manifest hooks remain disabled until runtime delivery evidence exists.",
    ]
    if state_note:
        lines.append(f"state_note: {state_note}")
    if len(trace_roots) > 1:
        lines.append("trace_note: multiple trace roots detected; choose by evidence before writing traces.")
    return "\n".join(lines)


def write_hook_output(event: str, mode: str, context: str | None = None) -> None:
    output: dict[str, object] = {"systemMessage": f"AI_AGENT_META_HARNESS:{mode.upper()}"}
    if context:
        output["hookSpecificOutput"] = {
            "hookEventName": event,
            "additionalContext": context,
        }
    sys.stdout.write(json.dumps(output))


def session_start(project_root: Path) -> None:
    mode, _state_note = read_mode()
    if mode == "off":
        write_hook_output("SessionStart", "off")
        return
    write_hook_output("SessionStart", mode, orientation_context(project_root))


def user_prompt_submit() -> None:
    data = load_hook_input()
    prompt = str(data.get("prompt", "")).strip()
    mode = COMMAND_TO_MODE.get(prompt)
    if mode is None:
        return
    write_mode(mode)
    if mode == "off":
        write_hook_output("UserPromptSubmit", mode, "AI Agent Meta-Harness orientation hook disabled.")
        return
    write_hook_output("UserPromptSubmit", mode, f"AI Agent Meta-Harness mode changed: {mode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--session-start", action="store_true")
    action.add_argument("--user-prompt-submit", action="store_true")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    if args.session_start:
        session_start(args.project_root.resolve())
    else:
        user_prompt_submit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
