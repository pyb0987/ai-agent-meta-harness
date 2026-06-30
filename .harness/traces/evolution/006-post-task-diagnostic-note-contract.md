---
iteration: 6
date: "2026-06-30"
type: additive
verdict: improved
files_changed: ["README.md", "adapters/claude/commands/init-harness.md", "adapters/claude/examples/CLAUDE.md.example", "adapters/claude/skills/harness-engineer/SKILL.md", "adapters/codex/skills/harness-engineer/SKILL.md", "adapters/codex/skills/init-codex-harness/SKILL.md", "adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template", "adapters/codex/templates/AGENTS.md.template", "backlog/plans/17-bounded-self-evolution-loop.md", "commands/init-harness.md", "docs/meta-harness-system.md", "plugins/ai-agent-meta-harness/skills/harness-engineer/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/assets/AGENTS.md.template", "plugins/ai-agent-meta-harness/templates/AGENTS.md.template", "scripts/check-harness-dogfood.py", "skills/harness-engineer/SKILL.md", "tests/test_harness_dogfood.py", "tests/test_maintenance_policy_boundaries.py", ".harness/traces/evolution/006-post-task-diagnostic-note-contract.md"]
refs: [5]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/evolution/005-bounded-self-evolution-proposal-loop.md
      lines: 36-43
      quote: "A repository can accumulate work, failures, experiments, or stale\nguards while the agent waits for an explicit \"please improve the harness\"\nrequest. That loses the product goal of user-input minimization."
    - file: .harness/traces/evolution/005-bounded-self-evolution-proposal-loop.md
      lines: 95-99
      quote: "Implementation multi-review: initial advisory review found one blocking\ndetector-output ambiguity. `check-harness-dogfood.py` now labels reports and\ncandidate objects with `evidence_status: diagnostic_only`"
---

## Iteration 006: post-task diagnostic note contract

Trigger: A follow-up multi-review found that Plan 17 was methodologically
correct but still too easy to make noisy. The checker could report multiple
internal candidates, and candidate records did not explicitly explain reusable
future value. That left a gap between "dogfood candidates are diagnostic" and
the desired product experience where ordinary users do not have to think about
the harness after every task.

### Diagnosis

The existing Plan 17 trace established the right boundary: dogfood work should
connect usage evidence to proposed harness work without automatic adoption.
The missing layer was the user surface. A diagnostic report can contain many
candidate records for audit, but ordinary task completion should expose zero or
one concise note at most. The note should be machine-readable enough to test
and should require three concrete parts before it can be shown:

- a concrete trigger-evidence pointer;
- reusable future value;
- a clear next action.

This keeps dogfood review available without turning every feature task into a
second harness-maintenance ceremony.

### Change

- Diff summary: Extended `harness-dogfood-report/v1` with
  `maintenance_note_kind`, `surface_mode`, and `maintenance_note`.
- Diff summary: Added `reusable_future_value`, `surface_scope`, and
  deterministic `surfacing_priority` to dogfood candidate records.
- Diff summary: Added `post_task` and `explicit_dogfood` modes. `post_task`
  may surface only current-work candidates; global stale search-set records stay
  in the internal candidate list unless an explicit dogfood review is requested.
- Diff summary: Updated Plan 17, README, system docs, Codex/Claude templates,
  and harness-engineer/init skill mirrors with the zero-or-one diagnostic note
  rule.
- Diff summary: Added tests for no-evidence/no-note, multiple internal
  candidates producing one surfaced note, stale search-set records staying out
  of post-task notes, and forbidden stable-claim wording.
- Diff summary: Accepted follow-up review findings by suppressing
  explicit-only search-set health candidates from `post_task` output, excluding
  malformed records from note selection, parsing Git rename records safely, and
  replacing "raw trigger evidence" wording with trigger-evidence pointers.

### Result

- Before: `scripts/check-harness-dogfood.py` produced diagnostic candidates but
  did not define a separate capped user-facing note contract.
- After: The checker still preserves all internal diagnostic candidates, while
  the user-facing maintenance note is `null` or exactly one
  `quiet_post_task_diagnostic_candidate` object. In `post_task`, unrelated
  explicit-only health candidates are suppressed from the public candidate list
  and counted separately.

Verification:

```text
$ python3 -m unittest tests.test_harness_dogfood tests.test_maintenance_policy_boundaries
Ran 36 tests
OK

$ python3 -m py_compile scripts/check-harness-dogfood.py
OK

$ python3 scripts/check-harness-dogfood.py
candidate_count: 0
suppressed_candidate_count: 0
maintenance_note: null

$ python3 scripts/check-harness-dogfood.py --surface-mode explicit_dogfood
candidate_count: 0
suppressed_candidate_count: 0
maintenance_note: null

$ python3 scripts/check-compat-mirrors.py
Compatibility mirrors are in sync.

$ python3 scripts/sync-codex-plugin.py --check
Codex plugin bundle is in sync.

$ python3 scripts/run-search-set.py
run-search-set: PASS (7 Active case(s))
```

### Lesson

Self-evolution should be quiet by default. The harness may notice possible
maintenance work, but ordinary users should see only a bounded diagnostic note
when concrete evidence, future value, and a next action are all present.
