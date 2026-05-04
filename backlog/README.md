# Backlog

Repository-level backlog for non-blocking improvements discovered while this
project operationalizes Meta-Harness paper principles into a practical harness
toolkit, runtime adapters, and verification gates.

Operational maintenance rules, verification commands, release checks, and test
policy live in `../MAINTENANCE.md`. This folder tracks future work; the
maintenance plan describes how that work should be selected, reviewed, and
verified.

Routine maintenance should run through one active session at a time. Reserve
one concrete item with the `Status`/`Owner`/`Branch`/`Started`/`Scope` fields
described in `../MAINTENANCE.md`, pass the Start Gate before implementation
edits, and complete the item before starting another one. Parallel worktrees are
exceptional recovery or explicitly requested split-work tools, not the default
backlog workflow.

Use this folder by ownership, not by where an issue was discovered:

| Area | File | Ownership |
|------|------|-----------|
| Core methodology | `core.md` | Agent-agnostic harness rules, trace formats, verification policy |
| Claude adapter | `claude-adapter.md` | Claude Code-specific trace roots, project hooks, slash commands, global skill install surfaces |
| Codex adapter | `codex-adapter.md` | Codex-specific runtime surfaces, sandbox behavior, AGENTS.md/plugin/git-hook integration |
| Completed records | `archive/*.md` | Full completed-item records moved out of active backlog files without losing Completion Gate or review history |

Adapter reviews may uncover core work. Put those items in `core.md` so Claude, Codex, and future adapters do not solve the same problem separately.

## Archive Policy

Keep active backlog files focused on available, in-progress, review-pending,
and short follow-up pointers. Move completed records to the matching
`backlog/archive/` file only after the item has a complete Completion Gate. The
archive must preserve the full record, including verification, search-set
status, multi-review scores, VETO handling, score-9 why-not-10 notes, residual
risk, and acceptance status.

The active backlog should retain a compact pointer for each archived completed
item. `scripts/check-maintenance-review.py` validates archive files by default,
so moving a record must not remove it from review-gate coverage.

## Theme Index

Use this index when choosing the next item. Several backlog entries describe the
same larger problem from different runtime angles; treat them as one theme unless
the adapter behavior truly differs.

| Theme | What It Covers | Related Items |
|-------|----------------|---------------|
| Distribution and install UX | How users install, activate, migrate, and eventually publish adapter bundles | `core.md` 8-9; `claude-adapter.md` 1 old install smoke; `codex-adapter.md` 4-5, 16-19, 39-40 |
| Hook and protection enforcement | Runtime hooks, pre-commit/CI guardrails, protected-file checks, schema drift, and honest protection-level reporting | `claude-adapter.md` 1 hook/runtime follow-ups; `codex-adapter.md` 3, 12-15, 28, 40; `core.md` 10 |
| Verification and release gates | Deterministic verify commands, adapter smoke tests, release checklist, and staged/index semantics for repository checks | `core.md` 3, 9-10, 43, 46, 48-49; `claude-adapter.md` 1 fixture/temp-git follow-ups; `codex-adapter.md` 6, 11, 18-19, 38 |
| Trace lifecycle and migration | Trace-root selection, partial initialization, history tie-breakers, archive restore, and `.claude/traces` to `.harness/traces` migration | `core.md` 2, 4-5, 47; `claude-adapter.md` 1 path contract; `codex-adapter.md` 2 |
| Autoresearch semantics | Detecting autoresearch projects, preserving evaluator boundaries, experiment episode traces, rejection history, and local-only protection states | `core.md` 1, 6; `codex-adapter.md` 12, 15 |
| Codex execution model | Codex sandbox, permissions, sub-agent availability, MCP/tool policy, browser/web usage, and skipped verification reporting | `codex-adapter.md` 1, 7-9 |
| Maintenance process control | Review-summary enforcement, score handling, and whether backlog work runs in one session or parallel worktrees | `core.md` 11, 15-17 |
| Documentation boundary and examples | Keeping core as what/why, adapters as runtime how, and adding realistic examples without duplicating methodology | `core.md` 7, 42, 44-45; `claude-adapter.md` 14; `codex-adapter.md` 10-11; adapter README/example follow-ups |

## Consolidation Notes

- `codex-adapter.md` 4, 5, 16, 17, 18, and 19 are one distribution epic:
  local plugin first, generated bundle integrity, activation smoke, then
  marketplace policy.
- `codex-adapter.md` 3, 12, 13, 14, and 15 are one protection epic: checker
  implementation, hook templates, hook output smoke, schema drift, and
  protection-level reporting.
- `core.md` 9-10 plus adapter smoke items are one release-gate epic. Keep
  adapter-specific smoke tests in adapter backlogs, but keep the checklist and
  staged/index policy in core.
- `core.md` 11 and 15-16 are one review-checker epic: summary structure,
  embedded backlog review outcomes, VETO handling, and score-9 why-not-10
  enforcement should stay aligned.
- `core.md` 17 supersedes the experimental parallel-worktree operating model
  for routine maintenance; keep only the parts that improve single-session
  discipline.
- `core.md` 2, 4, and 5 plus `codex-adapter.md` 2 are one trace-lifecycle epic.
  Core should define the general trace-history rules; Codex should only define
  how `.claude/traces` and `.harness/traces` interact in that runtime.
- `claude-adapter.md` currently has one umbrella item because the Claude-specific
  debt is narrow: path consistency and smoke coverage around the existing
  Claude surfaces. Split it only if it grows beyond trace/hook/install smoke.
