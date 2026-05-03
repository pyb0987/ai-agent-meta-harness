---
date: "2026-05-04"
change: "Established .harness/traces as the active repository self-application trace root."
status: "active"
---
# Repository Self-Application Trace Root

This repository now uses `.harness/traces/` as its tracked active trace root for
repository maintenance. The minimum trace surface is present:

- `search-set.md` for Active verification cases.
- `evolution/` for repository harness-maintenance changes.
- `failures/` for unresolved or diagnosed repository harness failures.
- `experiments/` for autoresearch-style experiment episodes when this
  repository is itself the target project.

Legacy Claude-local history remains under `.claude/traces/`. That history is
not copied here in this pass because `.claude/` is ignored and may contain
local provider/session context. Future repository maintenance traces should be
written under `.harness/traces/` unless a later migration item explicitly moves
or summarizes legacy Claude-local history.
