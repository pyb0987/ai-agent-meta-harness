---
date: "2026-06-18"
escalated_to: instructions
search_set_id: "SS-007"
resolved: true
retrieval:
  mode: not_needed
  reason: "Failure record is based on the current downstream user report, not prior trace history."
---

## Failure: worktree-local harness routing lost trace capture

### Observation

A downstream Claude project reported that feature and bugfix work happened in
separate git worktrees, while the harness routing file and trace directories
existed only in the main worktree:

```text
CLAUDE.local.md (harness routing/trace instructions): missing in feature worktrees
.claude/traces/ (trace infrastructure): missing in feature worktrees
.git/info/exclude: excludes both, so git does not carry them into worktrees
```

The reported effect was trace count zero for ordinary feature work: sessions in
feature worktrees could not read the local harness instructions and had no
trace filesystem to write to.

### Root Cause

The Claude adapter documented a normal project-relative `.claude/traces/` root
and selected-root migration behavior, but it did not state the worktree-specific
invariant: a relative trace root is per-worktree unless all worktrees are
bootstrapped to the same root. It also did not require harness routing to be
visible in every worktree when project instructions are ignored/local-only.

Relevant gaps before the fix:

- `core/methodology.md` required one active trace root but did not name the git
  worktree hazard.
- `adapters/claude/commands/init-harness.md` scanned existing Claude files and
  trace roots, but not ignored/local-only instruction files or worktree
  bootstrap scripts.
- `adapters/claude/commands/init-harness.md` did not require the initial
  `CLAUDE.md`/evolution log to record one shared trace root for all worktrees.

### Fix

The repository now escalates this into instructions and regression tests:

- `core/methodology.md` and `docs/methodology.md` state that worktree projects
  need one shared active root, either by stable absolute path outside the
  worktree set or by bootstrapping every worktree to the same root.
- `adapters/claude/commands/init-harness.md` and `commands/init-harness.md`
  instruct `/init-harness` to inspect worktree usage, ignored/local-only
  instruction files, and bootstrap scripts; select one shared root; and ensure
  routing is visible in every worktree session.
- `adapters/claude/examples/CLAUDE.md.example` marks the trace root as a single
  root and tells worktree projects to replace the relative root with the shared
  absolute or migrated root.

### Prevention

SS-007 runs focused unittest coverage over the methodology, Claude init command,
compatibility mirror, and Claude example. The guard should fail if future edits
remove the worktree-safe single-root policy or let the Claude init mirror drift
away from the canonical command.
