# Plan 15: Agent Autonomous Routing And User Experience

## Status

Implementation slice. The goal is to make the installed harness usable without
requiring ordinary users to remember skill names.

## Purpose

Plans 12 and 13 make the repository-local Meta-Harness practical for governance
and strategy-search. Plan 15 closes a user-experience gap: README language can
say "the agent handles the harness", but the actual installed agent needs clear
routing instructions before that is true.

The desired product shape is:

```text
User: Apply meta-harness to this project.
Agent: Initializes the project harness.

User: Please fix this feature.
Agent: Works normally.

User: This keeps failing / make this stop recurring.
Agent: Routes to harness evolution and uses raw traces.

User: This decision is risky / review this carefully.
Agent: Routes to multi-perspective review.

User: Try variants and keep the measurable winner.
Agent: Routes to autoresearch or strategy-search, depending on repository scope.
```

The user may still name a skill explicitly, but the normal path should not
require it.

## In Scope

- Skill descriptions that include ordinary user phrases, not only skill names.
- Project instruction templates that tell the installed agent when to route to
  initialization, harness evolution, multi-review, and autoresearch.
- README wording that presents the target-project experience as "ordinary agent
  use after one setup prompt".
- Regression tests that lock the routing phrases into README and templates.

## Out Of Scope

- Adding persistent background orchestration.
- Making every normal code request run multi-review or autoresearch.
- Requiring users to learn `init-codex-harness`, `harness-engineer`,
  `multi-review`, or `autoresearch`.
- Changing repository-local v2 governance semantics.

## Design Rules

- Prefer user-facing phrases over skill names.
- Keep the routing rules short enough for project instruction files.
- Use automatic routing for low-cost diagnosis and setup signals.
- Ask before starting expensive or long-running experiment loops unless the user
  explicitly requested them.
- Preserve the ordinary path: most feature and bug-fix requests should remain
  normal agent work.

## Acceptance

- README explains that ordinary users can use the harness after setup without
  memorizing skill names.
- Codex and Claude skill descriptions include natural-language triggers.
- Codex `AGENTS.md` templates include an agent routing section.
- Claude `/init-harness` and example `CLAUDE.md` include the same routing rule.
- Tests fail if these routing affordances are removed.

Search-set verification:

- BEFORE: SKIPPED no pre-change Active search-set run was captured before
  implementing Plan 15 routing guidance.
- AFTER: PASS `python3 scripts/run-search-set.py` after restoring README
  pre-commit verification markers and recording this search-set evidence block.

Multi-review:

- Mode: sequential fallback review with separated critics; no sub-agent
  independence claimed.
- User Experience Critic: score 9, PASS. Blocking findings: none. README now
  presents the normal target-project path as one setup prompt followed by
  ordinary agent use. Why not 10: runtime auto-selection is not directly smoke
  tested here. Follow-up/residual risk: accepted for this documentation and
  skill-surface slice.
- Agent Routing Critic: score 9, PASS. Blocking findings: none. Canonical
  Codex and Claude skill descriptions include user-facing phrases for setup,
  recurrence, high-risk review, and measurable experiment routing. Why not 10:
  actual agent skill-selection behavior remains runtime-dependent.
  Follow-up/residual risk: accepted; end-to-end runtime activation can be a
  later smoke if needed.
- Distribution Critic: score 9, PASS after fix. Blocking findings: initial
  VETO because Claude compatibility mirrors lacked the new routing
  descriptions; fixed by syncing `commands/` and `skills/` mirrors with
  canonical Claude adapter files. Why not 10: mirror consistency is checked
  mechanically, not by installing every legacy surface. Follow-up/residual
  risk: accepted.
- Verification Critic: score 9, PASS. Blocking findings: none after rerun.
  `tests.test_maintenance_policy_boundaries`, Codex init fixture tests, Claude
  mirror-sensitive skill tests, Codex plugin sync, Codex hook-schema drift
  check, and `git diff --check` passed. Why not 10: no live Codex/Claude skill
  selection smoke was run. Follow-up/residual risk: accepted.
- Scope Critic: score 9, PASS. Blocking findings: none. The change adds
  routing text and tests only; it does not add background orchestration, new
  user prompts, or governance semantic changes. Why not 10: this remains an
  adapter-surface improvement rather than a runtime guarantee.
  Follow-up/residual risk: accepted.
- Score handling: all required critics scored at least 9. Every score 9 records
  why not 10 and accepts the residual risk.
- Rerun status: rerun completed after the compatibility-mirror VETO fix.
- Follow-up/residual risk: accepted; future live runtime skill-selection smoke
  is useful but not required for this slice.
- Final acceptance: accepted for Plan 15 zero-skill routing guidance.
