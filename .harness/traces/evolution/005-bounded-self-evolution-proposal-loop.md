---
iteration: 5
date: "2026-06-22"
type: additive
verdict: improved
files_changed: ["README.md", "adapters/claude/commands/init-harness.md", "adapters/claude/examples/CLAUDE.md.example", "adapters/claude/skills/harness-engineer/SKILL.md", "adapters/codex/skills/harness-engineer/SKILL.md", "adapters/codex/skills/init-codex-harness/SKILL.md", "adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template", "adapters/codex/templates/AGENTS.md.template", "backlog/plans/17-bounded-self-evolution-loop.md", "backlog/plans/README.md", "commands/init-harness.md", "docs/meta-harness-system.md", "plugins/ai-agent-meta-harness/skills/harness-engineer/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/assets/AGENTS.md.template", "plugins/ai-agent-meta-harness/templates/AGENTS.md.template", "scripts/check-harness-dogfood.py", "skills/harness-engineer/SKILL.md", "tests/test_harness_dogfood.py", "tests/test_maintenance_policy_boundaries.py", ".harness/traces/evolution/004-codex-experimental-orientation-hooks.md", ".harness/traces/evolution/005-bounded-self-evolution-proposal-loop.md"]
refs: [1]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/evolution/004-codex-experimental-orientation-hooks.md
      lines: 18-29
      quote: "prompt-injection-style hook\norientation could improve this repository's Codex harness, provided it stayed\nopt-in, evidence-oriented, and bounded by the meta-harness methodology."
    - file: .harness/traces/evolution/002-self-application-evidence-review.md
      lines: 24-32
      quote: "There is no concrete\nrepository harness failure or rejected experiment in this pass that should be\nmanufactured into `failures/` or `experiments/` just to populate directories."
---

## Iteration 005: bounded self-evolution proposal loop

Trigger: A methodology discussion clarified that the next repository-level
improvement should not be a cwaa-specific workflow. It should be an
ai-agent-meta-harness rule for letting agents notice dogfood gaps and draft
improvement candidates without silently adopting them.

### Diagnosis

The repository already has three necessary pieces:

- Plan 12 and Plan 13 define strategy-search as a diagnostic evolution engine.
- Plan 15 teaches installed agents to route ordinary user language without
  requiring users to know skill names.
- Plan 16 makes trace-history claims checkable through byte-matching raw trace
  references.

The remaining method gap is the connection between usage evidence and proposed
harness work. A repository can accumulate work, failures, experiments, or stale
guards while the agent waits for an explicit "please improve the harness"
request. That loses the product goal of user-input minimization.

At the same time, the earlier self-application trace warns against fabricating
failures or experiments just to populate trace directories. The correct
boundary is therefore diagnostic proposal generation, not automatic adoption.

### Change

- Diff summary: Added Plan 17 to define a bounded self-evolution proposal loop.
- Diff summary: Updated the plan index so Plan 17 sits after autonomous routing
  and trace retrieval provenance.
- Diff summary: Updated the system overview to describe self-evolution as
  usage evidence -> diagnostic candidate -> raw evidence and verification ->
  reviewable content change.
- Diff summary: Added `scripts/check-harness-dogfood.py` as a diagnostic-only
  dogfood sweep that emits `harness-dogfood-report/v1` without editing files.
- Diff summary: Updated Codex/Claude routing surfaces and harness-engineer
  skills so ordinary dogfood-gap language routes to diagnostic proposals.
- Diff summary: Added regression tests for low-trace non-failure, trace-gap
  evidence requirements, search-set verify drift, and strategy-search selection
  diagnostic boundaries.

### Result

- Before: The repository had strategy-search, autonomous routing, and trace
  retrieval provenance, but no named plan connecting usage evidence to bounded
  harness improvement proposals.
- After: Plan 17 defines bounded self-evolution as diagnostic proposal
  generation only, with adoption still requiring raw evidence, verification,
  and reviewable content changes.

The repository now distinguishes three layers:

- automatic detection and candidate drafting are allowed;
- generated candidates, catalogs, summaries, and strategy-search selections are
  not evidence by themselves;
- adoption still requires raw evidence, executable verification, and ordinary
  reviewable content changes, with v2 governance for stable publication.

Verification:

```text
$ python3 -m unittest tests.test_harness_dogfood tests.test_maintenance_policy_boundaries
Ran 30 tests
OK

$ python3 scripts/check-harness-dogfood.py
candidate_count: 0

$ python3 scripts/check-compat-mirrors.py
Compatibility mirrors are in sync.

$ python3 scripts/run-search-set.py
run-search-set: PASS (7 Active case(s))
```

Implementation multi-review: initial advisory review found one blocking
detector-output ambiguity. `check-harness-dogfood.py` now labels reports and
candidate objects with `evidence_status: diagnostic_only`, `evidence_role:
pointer_only`, and `adoption_boundary: not_adoption_evidence`; focused
re-review scored 9 with no blocking findings.

### Lesson

Meta-Harness self-evolution should be bounded. Agents may propose how the
harness should learn from its own usage, but the repository should accept only
changes that cross the normal evidence and adoption boundary.
