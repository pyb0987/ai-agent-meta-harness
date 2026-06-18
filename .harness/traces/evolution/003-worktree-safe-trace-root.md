---
iteration: 3
date: "2026-06-18"
type: additive
verdict: improved
files_changed: ["core/methodology.md", "docs/methodology.md", "adapters/claude/commands/init-harness.md", "commands/init-harness.md", "adapters/claude/examples/CLAUDE.md.example", "tests/test_core_methodology_boundaries.py", "tests/test_claude_init_harness_fixture.py", "tests/test_maintenance_policy_boundaries.py", "tests/test_repository_search_set.py", ".harness/traces/search-set.md", ".harness/traces/failures/002-worktree-local-trace-loss.md", ".harness/traces/evolution/003-worktree-safe-trace-root.md", "backlog/review-2026-06-18-worktree-trace-root.md"]
refs: [1, 2]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/failures/002-worktree-local-trace-loss.md
      lines: 12-24
      quote: "A downstream Claude project reported that feature and bugfix work happened in"
    - file: .harness/traces/evolution/001-repository-self-application-root.md
      lines: 27-40
      quote: "This repository now uses `.harness/traces/` as its tracked active trace root for"
    - file: .harness/traces/search-set.md
      lines: 43-46
      quote: "Claude worktrees keep one shared trace root"
---

## Iteration 003: worktree-safe trace root guidance

Trigger: A downstream Claude project reported zero trace accumulation because
feature work happened in git worktrees where local harness routing and
`.claude/traces/` did not exist.

### Diagnosis

The repository already had a tracked self-application trace root under
`.harness/traces/`, and legacy `.claude/traces/` history was intentionally not
the write target for repository maintenance. The new failure was in the Claude
adapter guidance shipped to downstream projects: it selected between
`.claude/traces/` and `.harness/traces/` by meaningful history, but did not
state the git worktree hazard.

When a project uses multiple git worktrees, a relative `.claude/traces/` root is
per-worktree unless an adapter or bootstrap points every worktree at one shared
root. If harness routing lives only in an ignored local file, feature worktrees
may not load the harness at all.

- Referenced files: `.harness/traces/failures/002-worktree-local-trace-loss.md`
- Referenced files: `.harness/traces/evolution/001-repository-self-application-root.md`
- Referenced files: `.harness/traces/search-set.md`

### Change

- Diff summary: Added runtime-neutral worktree trace-root policy to
  `core/methodology.md` and compatibility mirror `docs/methodology.md`.
- Diff summary: Updated Claude `/init-harness` and its compatibility mirror to
  inspect worktree/local-only instruction surfaces, choose one shared trace
  root, and require routing visibility in every worktree.
- Diff summary: Added a Claude example note, focused regression tests, SS-007,
  and a failure diagnosis trace for the downstream worktree trace-loss report.

### Result

- Before: trace-root policy required exactly one active root, but did not say how git worktrees can break that invariant.
- After: Claude init guidance and core methodology both require one shared root for all worktrees, with SS-007 covering the policy and mirrors.

Verification:

```text
$ python3 scripts/run-search-set.py --case SS-007
Ran 45 tests in 0.023s
OK
SS-007: PASS
run-search-set: PASS (1 Active case(s))

$ python3 scripts/check-compat-mirrors.py
Compatibility mirrors are in sync.

$ python3 -m unittest tests/test_repository_search_set.py
Ran 13 tests in 0.006s
OK
```

During verification, `tests/test_repository_search_set.py` initially failed
because it expected `last_updated: "2026-05-04"`. The test was updated to
expect the new `2026-06-18` search-set date and to include SS-007 in the active
coverage markers.

### Lesson

Trace-root selection has to account for the filesystem topology agents actually
work in. For Claude projects using git worktrees, local ignored routing files
and project-relative trace roots must be treated as incomplete until every
worktree session can see the routing and write to the same active trace root.
