#!/usr/bin/env python3
"""Install Codex autoresearch protection assets into a target project."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PRE_COMMIT_WRAPPER = """#!/bin/sh
set -eu

.githooks/pre-commit-autoresearch-protected.sh
"""

PRE_COMMIT_BLOCK = """

# Autoresearch evaluator protection.
.githooks/pre-commit-autoresearch-protected.sh
"""


@dataclass
class Action:
    status: str
    path: Path
    detail: str


class Installer:
    def __init__(self, source_root: Path, target_root: Path, dry_run: bool = False) -> None:
        self.source_root = source_root.resolve()
        self.target_root = target_root.resolve()
        self.dry_run = dry_run
        self.actions: list[Action] = []

    def source(self, relative: str) -> Path:
        path = self.source_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing adapter asset: {path}")
        return path

    def target(self, relative: str) -> Path:
        return self.target_root / relative

    def record(self, status: str, path: Path, detail: str) -> None:
        self.actions.append(Action(status, path.relative_to(self.target_root), detail))

    def write_text(self, relative: str, text: str, *, executable: bool = False, replace: bool = False) -> None:
        path = self.target(relative)
        if path.exists() and not replace:
            self.record("exists", path, "left unchanged")
            return
        self.record("write" if not path.exists() else "update", path, "created from installer template")
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if executable:
            path.chmod(0o755)

    def copy_asset(self, source_relative: str, target_relative: str, *, executable: bool = False) -> None:
        source = self.source(source_relative)
        target = self.target(target_relative)
        if target.exists():
            self.record("exists", target, "left unchanged")
            return
        self.record("copy", target, f"from {source_relative}")
        if self.dry_run:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if executable:
            target.chmod(0o755)

    def copy_if_missing(self, source_relative: str, target_relative: str, *, executable: bool = False) -> bool:
        target = self.target(target_relative)
        if target.exists():
            self.record("exists", target, "left unchanged")
            return False
        self.copy_asset(source_relative, target_relative, executable=executable)
        return True

    def copy_hook_config_if_missing(self) -> None:
        hooks_json = self.target(".codex/hooks.json")
        config_toml = self.target(".codex/config.toml")
        if config_toml.exists():
            self.record("merge-required", config_toml, "existing Codex config left unchanged")
            return
        if hooks_json.exists():
            self.record("merge-required", hooks_json, "existing Codex hook config left unchanged")
            return
        self.copy_if_missing("templates/hooks/codex-hooks.json.template", ".codex/hooks.json")

    def copy_ci_if_missing(self) -> None:
        target = self.target(".github/workflows/autoresearch-protected.yml")
        if target.exists():
            self.record("merge-required", target, "existing workflow left unchanged")
            return
        self.copy_asset(
            "templates/hooks/github-actions-autoresearch-protected.yml",
            ".github/workflows/autoresearch-protected.yml",
        )

    def configure_hooks_path(self) -> None:
        git_dir = self.target_root / ".git"
        if not git_dir.exists():
            self.record("manual-step", self.target(".githooks/pre-commit"), "run `git config core.hooksPath .githooks` after git init")
            return
        current = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=self.target_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        value = current.stdout.strip()
        if value == ".githooks":
            self.record("exists", self.target(".githooks/pre-commit"), "core.hooksPath already points at .githooks")
            return
        if value and value != ".githooks":
            self.record("merge-required", self.target(".githooks/pre-commit"), f"existing core.hooksPath={value!r} left unchanged")
            return
        if self.dry_run:
            self.record("configure", self.target(".githooks/pre-commit"), "would set core.hooksPath to .githooks")
            return
        result = subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=self.target_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            self.record("manual-step", self.target(".githooks/pre-commit"), "failed to set core.hooksPath; run `git config core.hooksPath .githooks`")
            return
        self.record("configure", self.target(".githooks/pre-commit"), "set core.hooksPath to .githooks")

    def install_pre_commit(self) -> None:
        self.copy_asset(
            "templates/hooks/pre-commit-autoresearch-protected.sh",
            ".githooks/pre-commit-autoresearch-protected.sh",
            executable=True,
        )
        hook = self.target(".githooks/pre-commit")
        if not hook.exists():
            self.write_text(".githooks/pre-commit", PRE_COMMIT_WRAPPER, executable=True)
            self.configure_hooks_path()
            return
        text = hook.read_text(encoding="utf-8")
        if "pre-commit-autoresearch-protected.sh" in text:
            self.record("exists", hook, "already calls autoresearch protection")
            self.configure_hooks_path()
            return
        self.record("merge", hook, "appended autoresearch protection call")
        if self.dry_run:
            return
        hook.write_text(text.rstrip() + PRE_COMMIT_BLOCK, encoding="utf-8")
        hook.chmod(hook.stat().st_mode | 0o111)
        self.configure_hooks_path()

    def install_agents_snippet(self) -> None:
        snippet = self.source("templates/hooks/agents-autoresearch-protection.md").read_text(encoding="utf-8")
        agents = self.target("AGENTS.md")
        if not agents.exists():
            self.write_text("AGENTS.md", snippet)
            return
        text = agents.read_text(encoding="utf-8")
        if "## Autoresearch Protection" in text:
            self.record("exists", agents, "already contains Autoresearch Protection section")
            return
        self.record("merge", agents, "appended Autoresearch Protection section")
        if not self.dry_run:
            agents.write_text(text.rstrip() + "\n\n" + snippet, encoding="utf-8")

    def install(self) -> list[Action]:
        self.copy_asset("scripts/check-autoresearch-protected.py", "scripts/check-autoresearch-protected.py", executable=True)
        self.copy_asset("scripts/smoke-autoresearch-hooks.py", "scripts/smoke-autoresearch-hooks.py", executable=True)
        self.copy_if_missing("templates/autoresearch-protected.txt", ".harness/autoresearch-protected.txt")
        self.copy_hook_config_if_missing()
        self.install_pre_commit()
        self.copy_ci_if_missing()
        self.install_agents_snippet()
        return self.actions


def default_source_root() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[1]
    if (candidate / "templates" / "hooks").is_dir():
        return candidate
    return Path.cwd()


def print_actions(actions: list[Action]) -> None:
    for action in actions:
        print(f"{action.status}: {action.path} ({action.detail})")


def smoke_command() -> str:
    return (
        "python3 scripts/smoke-autoresearch-hooks.py "
        "--checker scripts/check-autoresearch-protected.py "
        "--protected-file .harness/autoresearch-protected.txt"
    )


def run_command(command: list[str], target_root: Path) -> int:
    return subprocess.run(command, cwd=target_root).returncode


def has_git_base(target_root: Path) -> bool:
    if not is_git_worktree(target_root):
        return False
    head = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=target_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return head.returncode == 0


def is_git_worktree(target_root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=target_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def run_smokes(target_root: Path) -> tuple[bool, list[str]]:
    skipped: list[str] = []
    if run_command(smoke_command().split(), target_root) != 0:
        return False, skipped
    if not is_git_worktree(target_root):
        skipped.append("pre-commit smoke skipped because target is not a git repository")
        skipped.append("CI/base-ref smoke skipped because target is not a git repository with an initial commit")
        return True, skipped
    if run_command(["python3", "scripts/check-autoresearch-protected.py", "--pre-commit"], target_root) != 0:
        return False, skipped
    if has_git_base(target_root):
        if run_command(["python3", "scripts/check-autoresearch-protected.py", "--ci", "--base-ref", "HEAD"], target_root) != 0:
            return False, skipped
    else:
        skipped.append("CI/base-ref smoke skipped because target is not a git repository with an initial commit")
    return True, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=default_source_root())
    parser.add_argument("--target", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-smoke", action="store_true")
    args = parser.parse_args(argv)

    installer = Installer(args.source_root, args.target, dry_run=args.dry_run)
    try:
        actions = installer.install()
    except (FileNotFoundError, OSError) as exc:
        print(f"install-autoresearch-protection: {exc}", file=sys.stderr)
        return 1

    print_actions(actions)
    print()
    print("Smoke commands:")
    print(smoke_command())
    print("python3 scripts/check-autoresearch-protected.py --pre-commit")
    print("python3 scripts/check-autoresearch-protected.py --ci")
    print("Local initial-commit CI smoke command:")
    print("python3 scripts/check-autoresearch-protected.py --ci --base-ref HEAD")
    has_merge_required = any(action.status == "merge-required" for action in actions)
    has_manual_step = any(action.status == "manual-step" for action in actions)
    if has_merge_required or has_manual_step:
        print()
        print("Protection level: incomplete")
        print("Reason: one or more hook, CI, or git-hook activation steps require reviewed merge or manual setup.")
    elif not args.run_smoke or args.dry_run:
        print()
        print("Protection level: incomplete")
        print("Reason: templates are installed; run or review the smoke results before reporting local-only or shared-repo protection.")

    if args.run_smoke and not args.dry_run:
        ok, skipped = run_smokes(args.target.resolve())
        for reason in skipped:
            print(f"SKIPPED: {reason}")
        if ok and not (has_merge_required or has_manual_step):
            print("Protection level: local-only")
            if skipped:
                print("CI/shared-repo status: skipped with reason above.")
            else:
                print("CI/shared-repo status: local CI command passed against HEAD base.")
            return 0
        if ok:
            print("Protection level: incomplete")
            print("Reason: smoke commands passed, but hook, CI, or git-hook activation still requires reviewed setup.")
            return 0
        print("Protection level: incomplete")
        print("Reason: one or more smoke commands failed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
