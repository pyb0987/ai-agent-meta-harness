---
iteration: 1
date: "2026-05-04"
type: additive
verdict: improved
files_changed: [".harness/traces/search-set.md", ".harness/traces/evolution/001-repository-self-application-root.md", ".harness/traces/failures/.gitkeep", ".harness/traces/experiments/.gitkeep", "backlog/core.md"]
refs: []
---

## Iteration 001: repository self-application trace root

Trigger: Repository maintenance needed a tracked active trace root so future
harness changes could reuse raw search-set and evolution evidence instead of
depending only on backlog summaries.

### Diagnosis

The repository had legacy Claude-local trace history under `.claude/traces/`,
but no tracked provider-neutral `.harness/traces/` root for repository
self-application. That made the intended trace surface implicit.

- Referenced files: `.claude/traces/`
- Referenced files: `backlog/core.md` item 33

### Change

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

### Result

- Before: repository maintenance had no tracked provider-neutral
  `.harness/traces/` self-application root.
- After: `.harness/traces/` contains `search-set.md`, `evolution/`,
  `failures/`, and `experiments/` as the active repository trace surface.

### Lesson

Repository self-application evidence should live in tracked `.harness/traces/`
records. Legacy provider-local traces can inform future work, but should not be
copied into the tracked root without a reviewed migration reason.
