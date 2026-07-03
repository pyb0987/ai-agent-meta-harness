# Global Project Trace Boundary Review

Review scope: global/project trace-root boundary across core methodology,
reference docs, README target-project guidance, Codex/Claude harness-engineer
skills, init templates, plugin copies, SS-009, and installed global Codex trace
SS-002.

Search-set verification:

- SKIPPED: pre-change search-set capture was unavailable because this review
  was added after the global/project trace-boundary patch had already been
  drafted; focused after-checks below cover the accepted boundary.
- AFTER: PASS `python3 -m unittest tests/test_harness_dogfood.py tests/test_claude_profile_drift.py tests/test_claude_compat_install_smoke.py tests/test_maintenance_policy_boundaries.py tests/test_core_methodology_boundaries.py`
  covered dogfood regressions, Claude profile drift regressions, install smoke,
  README/policy boundaries, and methodology boundary markers.
- AFTER: PASS `python3 scripts/run-search-set.py --case SS-008` covered the
  existing Claude global profile drift boundary.
- AFTER: PASS `python3 scripts/run-search-set.py --case SS-009` covered the new
  global/project trace boundary.
- AFTER: PASS `python3 scripts/check-compat-mirrors.py` covered core/reference
  and Claude compatibility mirrors.
- AFTER: PASS `python3 scripts/sync-codex-plugin.py --check` covered Codex
  plugin bundle copies.
- AFTER: PASS `python3 scripts/check-trace-retrieval-provenance.py .harness/traces/evolution/008-global-project-trace-boundary.md`
  covered trace retrieval provenance.
- AFTER: PASS `python3 /Users/fainders/.claude/harness/scripts/check-claude-profile-drift.py --claude-home /Users/fainders/.claude --json`
  covered the installed Claude profile.
- AFTER: PASS global Codex SS-002 condition checked that
  `/Users/fainders/.codex/harness/traces/failures/002-global-trace-root-blind-spot.md`
  exists and the failure/search-set preserve "Global traces do not replace
  project-local search-set guards".
- AFTER: PASS `git diff --check` covered whitespace safety.

Multi-review:

- Scope critic: score 9.0 PASS, critic scope problem framing and responsibility
  boundary. Blocking findings: none. The change addresses the real problem:
  global trace roots are cross-project agent/harness memory, while
  project-specific recurrence guards stay in the target project's active trace
  root. Why not 10: the project-specific JD-router guard itself still belongs
  in the downstream project, not this repository.
- Validation-layer critic: score 9.0 PASS, critic scope false-green paths in
  docs/skills/templates/tests. Blocking findings: none. SS-009 and unit tests
  now fail if the global/project boundary wording disappears from core,
  reference, README, templates, Claude example, or Codex harness-engineer skill.
  Why not 10: this is instruction-mediated routing clarity, not a sandbox or
  daemon that can force every future agent to inspect global traces.
- User-experience critic: score 9.0 PASS, critic scope user-input minimization.
  Blocking findings: none. The change does not add a new command, hook, daemon,
  or user ceremony; it reduces the chance that users must remember the harness
  topology during ordinary work. Why not 10: users still need to initialize a
  project-local harness when they want project-specific guards.
- Anti-bloat critic: score 9.0 PASS, critic scope complexity and operator-facing
  model. Blocking findings: none. The patch is additive instruction plus
  focused tests and avoids expanding v2 governance or profile checker schemas.
  Why not 10: the boundary is duplicated across several adapter surfaces, so
  compatibility mirror and plugin-sync checks remain important.
- Evidence critic: score 9.0 PASS, critic scope trace evidence and global
  installation. Blocking findings: none after follow-up. The repository records
  failure `003-global-trace-blind-spot.md` and evolution
  `008-global-project-trace-boundary.md`; the installed global Codex trace also
  records `failures/002-global-trace-root-blind-spot.md` and global SS-002. Why
  not 10: the installed global trace is outside the repository commit, so final
  acceptance must report it as an applied local installation update.
- Blocking findings: none remaining for this global/project trace boundary
  batch.
- Follow-up/residual risk: Agent compliance remains instruction-mediated.
  Global traces do not replace project-local search-set guards, and downstream
  projects still need local initialization for domain-specific recurrence
  prevention.
- Score handling: all critic scores are 9.0 PASS; why-not-10 items are accepted
  residual risks for a lightweight routing-boundary improvement.
- Rerun status: focused tests, SS-008, SS-009, compatibility checks, plugin sync,
  trace provenance, installed Claude profile check, and global Codex SS-002
  condition passed.
- Final acceptance: PASS for committing and pushing the global/project trace
  boundary batch.
