# Operational Friction Recording Trigger Review

Review scope: successful-but-costly operational friction that previously did
not enter trace recording, including cwd drift, orphaned dev-server cleanup,
sandbox/permission/network recovery, and session-state drift. Changed surfaces:
core methodology/reference mirrors, Codex/Claude harness-engineer skills,
Codex project templates, Claude init/example project surfaces, plugin copies,
and boundary tests.

Search-set verification:

- SKIPPED: pre-change search-set capture was unavailable because this change
  was planned and implemented from an external operational failure report after
  the relevant downstream session had already completed. The failure mode is a
  recording-trigger gap, so the accepted after-checks below focus on the
  productized harness guidance and tests.
- AFTER: PASS `python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_maintenance_policy_boundaries.py`
  covered the shared methodology/reference mirrors and agent-visible
  Codex/Claude surfaces for the new operational-workaround trigger.
- AFTER: PASS `python3 scripts/check-compat-mirrors.py` covered Claude
  compatibility mirrors.
- AFTER: PASS `python3 scripts/sync-codex-plugin.py --check` covered Codex
  plugin copies.
- AFTER: PASS `git diff --check` covered whitespace safety.
- AFTER: PASS `python3 scripts/check-search-set-evidence.py` covered
  search-set evidence compliance.
- AFTER: PASS `python3 scripts/check-maintenance-review.py` covered
  maintenance-review record shape. The existing one-off fallback review-quality
  signal remains advisory and non-failing.

Multi-review:

- Review mode: `FALLBACK_NONINDEPENDENT`. Critics were run sequentially in the
  implementation session; this is advisory repository maintenance review, not
  stable governance acceptance evidence.
- Problem-framing critic: score 9.0 PASS, critic scope recording trigger
  correctness. Blocking findings: none. The root problem is not counting or
  structural elimination; the harness could not internalize operational
  friction because successful tasks with non-obvious workarounds were outside
  the recording trigger.
- User-input minimization critic: score 9.0 PASS, critic scope ordinary user
  experience. Blocking findings: none. The patch does not require users to name
  a skill or ask "dogfood gap"; it gives the agent a quiet trigger for one
  diagnostic note when a concrete non-obvious workaround has reusable future
  value.
- Over-recording critic: score 9.0 PASS, critic scope trace noise prevention.
  Blocking findings: none. The change explicitly excludes simple typos,
  obvious one-off fixes, one-off CLI deprecations, and agent-created
  verification mistakes with no environment lesson.
- Anti-bloat critic: score 9.0 PASS, critic scope complexity and structural
  escalation. Blocking findings: none. The patch avoids automatic turn
  counters, daemon hooks, and immediate `dev.sh` tooling; structural fixes stay
  behind the existing recurrence and prior-prevention-failed ladder.
- Validation-layer critic: score 9.0 PASS, critic scope executable coverage.
  Blocking findings: none for this instruction-mediated trigger. Focused tests
  assert the trigger appears in shared core docs and agent-facing surfaces, and
  assert the numeric corrective-round threshold remains explicitly rejected.
- Blocking findings: none remaining for this batch.
- Follow-up implementation review: accepted and fixed two findings before
  close-out. Claude `/init-harness` and `CLAUDE.md.example` now include the
  operational-workaround recording trigger, and the shared methodology no
  longer labels the mixed trigger list as purely objective criteria.
- Follow-up/residual risk: This remains an agent judgment trigger, not a
  filesystem-enforced detector. A future tally-by-tag checker is useful only
  after these occurrences are actually recorded.
- Score handling: all critic scores are 9.0 PASS; why-not-10 residuals are
  accepted for a lightweight recording-trigger correction.
- Rerun status: focused tests, compatibility mirror check, plugin sync check,
  search-set evidence check, maintenance review check, and whitespace check
  passed.
- Final acceptance: PASS for committing the operational-friction recording
  trigger change.
