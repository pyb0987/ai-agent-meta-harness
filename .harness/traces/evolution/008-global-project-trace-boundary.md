---
iteration: 8
date: "2026-07-03"
type: additive
verdict: improved
files_changed: [".harness/traces/evolution/008-global-project-trace-boundary.md", ".harness/traces/failures/003-global-trace-blind-spot.md", ".harness/traces/search-set.md", "README.md", "adapters/claude/commands/init-harness.md", "adapters/claude/examples/CLAUDE.md.example", "adapters/claude/skills/harness-engineer/SKILL.md", "adapters/codex/examples/AGENTS.md.example", "adapters/codex/skills/harness-engineer/SKILL.md", "adapters/codex/skills/init-codex-harness/SKILL.md", "adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template", "adapters/codex/templates/AGENTS.md.template", "backlog/review-2026-07-03-global-project-trace-boundary.md", "commands/init-harness.md", "core/methodology.md", "core/reference.md", "docs/meta-harness-system.md", "docs/methodology.md", "docs/reference.md", "plugins/ai-agent-meta-harness/examples/AGENTS.md.example", "plugins/ai-agent-meta-harness/skills/harness-engineer/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/SKILL.md", "plugins/ai-agent-meta-harness/skills/init-codex-harness/assets/AGENTS.md.template", "plugins/ai-agent-meta-harness/templates/AGENTS.md.template", "skills/harness-engineer/SKILL.md", "tests/test_core_methodology_boundaries.py", "tests/test_maintenance_policy_boundaries.py"]
refs: [6, 7]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/failures/003-global-trace-blind-spot.md
      lines: 28-36
      quote: "That global trace root existed, but it did not contain the JD location-filter\nfailure. The accurate diagnosis was two-layered:"
---

## Iteration 008: global/project trace boundary

Trigger: A downstream usage report showed a target project with no local trace
root, while the installed global Codex trace root existed. The agent first
reported only the local absence, then corrected itself after the user asked
about the global harness.

### Diagnosis

The prior Plan 17 work correctly kept dogfood proposals quiet and diagnostic.
The prior Claude profile-drift work correctly recognized that users install the
harness globally and then work in other projects. The missing boundary was how
to reason when both facts meet:

- global installs can carry cross-project agent/harness memory;
- project-specific failures still need local trace roots and executable guards;
- the agent must inspect both layers before claiming "no trace history exists."

Without that boundary, an agent can either miss global trace memory or overclaim
that global traces cover project-specific guards. Both outcomes increase user
burden, because the user has to remember the harness topology.

### Change

- Added a global/project trace-root boundary to core methodology and reference
  docs.
- Updated README target-project guidance so global installs are described as
  routing and cross-project memory, not a replacement for local project traces.
- Updated Codex and Claude harness-engineer surfaces to inspect global trace
  roots when diagnosing missing project harnesses or cross-project failures.
- Updated Codex/Claude init and generated project templates so new projects do
  not treat global installation as sufficient local harness setup.
- Added failure trace `003-global-trace-blind-spot.md`.
- Added Active search-set case SS-009 plus unit-test markers for the boundary.
- Synced Codex plugin copies so direct skill-copy and plugin paths agree.

### Result

The intended behavior is now:

```text
target-project issue
  -> check project trace roots for project guards
  -> if absent, report/project-init gap
  -> also check global trace root for cross-project agent/harness patterns
  -> record project-specific guards locally and cross-project misses globally
```

This does not add an automatic logging daemon and does not make low trace volume
a failure. It only prevents the agent from collapsing the global and local
layers during harness diagnosis.

Multi-review:

- Review date: 2026-07-03.
- Review mode: `FALLBACK_NONINDEPENDENT` sequential multi-review after user
  requested plan/acceptance review before further adoption.
- Frame: decide whether the global/project trace boundary change is the right
  response to a downstream JD-router incident where the agent first missed the
  installed global Codex trace root.
- Scope critic: PASS. The change fixes the real boundary: global trace roots
  are cross-project agent/harness memory, while project-specific recurrence
  guards stay in the target project's active trace root.
- Validation-layer critic: ADVISORY PASS. The boundary is enforced through
  docs, skills, generated templates, and SS-009 smoke tests; it is not a
  filesystem access-control or automatic logging boundary.
- User-experience critic: PASS. The change does not add a daemon, hook, or new
  user command. It reduces the chance that users must remember the harness
  topology during ordinary work.
- Anti-bloat critic: PASS. The change is additive instruction plus focused
  tests, and it avoids expanding the operator-facing v2 governance model.
- Evidence critic: PASS after follow-up. The repository trace records the
  method change, and the installed global Codex trace now also records
  `failures/002-global-trace-root-blind-spot.md` with global SS-002.
- Residual: Agent compliance remains instruction-mediated. This is acceptable
  because the method goal here is routing clarity and trace discipline, not a
  sandbox-enforced access-control boundary.

### Verification

```text
$ python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_maintenance_policy_boundaries.py
Ran 38 tests
OK

$ python3 scripts/run-search-set.py --case SS-009
SS-009: PASS
run-search-set: PASS (1 Active case(s))

$ python3 scripts/check-trace-retrieval-provenance.py .harness/traces/evolution/008-global-project-trace-boundary.md
Trace retrieval provenance is valid.

$ python3 scripts/check-compat-mirrors.py
Compatibility mirrors are in sync.

$ python3 scripts/sync-codex-plugin.py --check
Codex plugin bundle is in sync.

$ python3 scripts/check-maintenance-review.py
Maintenance review summaries are valid.

$ git diff --check
OK
```
