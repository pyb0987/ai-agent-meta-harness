# Claude Adapter Backlog

Claude Code-specific follow-ups live here. Shared methodology belongs in
`backlog/core.md`; Codex runtime work belongs in `backlog/codex-adapter.md`.

## Priority Candidates

### 1. Keep Claude trace and hook paths mechanically consistent

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- adapters/claude/tests/test_claude_adapter_paths.py
- backlog/claude-adapter.md

Decision implemented: Claude adapter docs now use concrete Claude Code paths for
adapter-owned artifacts, and pre-commit validates the path contract.

This check is index-oriented lexical documentation validation. It does not
prove Claude Code runtime hook activation, `.claude/settings.local.json` schema
acceptance, or actual `/init-harness` generated project output.

Implemented foundation:

- Claude adapter trace paths resolve to `.claude/traces/...`.
- Claude hook scripts resolve to `.claude/hooks/...`.
- Claude hook settings resolve to `.claude/settings.local.json`.
- `scripts/check-claude-adapter-paths.py` rejects bare `traces/...`,
  `traces/`, `failures/`, `hooks/...`, `hooks/`, and `settings.local.json` in
  Claude adapter docs.
- The tracked pre-commit hook runs the path contract check after compatibility
  mirror validation.
- The checker discovers indexed `adapters/claude/**/*.md` surfaces plus the
  indexed README Claude section; core docs and Codex docs are intentionally
  outside its scope.

Decision implemented for temp-git fixture coverage:

- `adapters/claude/tests/test_claude_adapter_paths.py` now exercises the path
  checker inside temporary Git repositories instead of only monkeypatching
  indexed file lists.
- The temp-git tests prove staged clean Claude paths pass even when the working
  tree has unstaged bare-path drift.
- The tests prove staged-added Claude markdown with a bare hook path fails.
- The tests prove paths removed from the index with `git rm --cached` are not
  discovered by the checker.

Remaining follow-up work:

- Add an old Claude install command smoke test while compatibility mirrors exist.
- Add a project-fixture smoke test that runs `/init-harness` output expectations
  against a minimal target project once command execution can be tested
  mechanically.
- Add Claude hook settings schema/runtime activation smoke coverage when it can
  be tested mechanically.
- Track repo-wide staged-content semantics for compatibility mirror checks in
  `backlog/core.md`.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `adapters/claude/tests/test_claude_adapter_paths.py` and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest adapters/claude/tests/test_claude_adapter_paths.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this validates release-gate/index
  semantics for the Claude pre-commit path checker.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Index-semantics coverage critic score 10,
  verdict PASS, Blocking findings: none. Regression isolation critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score
  9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: remaining Claude hook/runtime and install smoke
  follow-ups stay listed above.
- Accepted: yes; accepted by maintainer review and ready for commit.

## Current Status

- Source review: external session found Claude adapter trace/hook path drift as
  the largest remaining operability issue.
