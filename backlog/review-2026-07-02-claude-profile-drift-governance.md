# Claude Profile Drift Governance Review

Review scope: Claude global profile drift checker, default profile-governance
manifest, README install path, Claude harness-engineer routing, compatibility
mirror, SS-008 search-set entry, and the evolution trace for the change.

Search-set verification:

- BEFORE: SKIPPED no pre-change Active search-set run was captured before the
  Claude profile drift governance implementation began.
- AFTER: PASS `python3 -m unittest tests/test_harness_dogfood.py tests/test_claude_profile_drift.py tests/test_claude_compat_install_smoke.py tests/test_maintenance_policy_boundaries.py`
  covered dogfood regressions, profile checker false greens, install smoke, and
  README/policy boundaries.
- AFTER: PASS `python3 scripts/run-search-set.py --case SS-008` covered the new
  Active search-set case.
- AFTER: PASS `python3 scripts/check-compat-mirrors.py` covered Claude root
  compatibility mirrors.
- AFTER: PASS `python3 scripts/check-claude-adapter-paths.py` covered Claude
  adapter path wording.
- AFTER: PASS `python3 scripts/check-trace-retrieval-provenance.py .harness/traces/evolution/007-claude-profile-drift-governance.md`
  covered trace retrieval provenance.
- AFTER: PASS `git diff --check` covered whitespace safety.

Multi-review:

- Dogfood-boundary critic: score 9.0 PASS, critic scope repeated dogfood
  findings against `scripts/check-harness-dogfood.py` and Codex templates.
  Blocking findings: none after post-task output suppresses explicit-only
  candidates, malformed candidates cannot become notes, rename parsing uses
  porcelain `-z`, trigger-evidence pointer wording is in place, and the broad
  "we did a lot of work" trigger is absent. Why not 10: the repeated external
  review text still includes stale findings, so future reviewers may need to
  distinguish stale reports from current code.
- Profile-checker critic: score 9.0 PASS, critic scope false-green paths in
  `check-claude-profile-drift.py` and profile-governance fixtures. Blocking
  findings: none after the checker covers installed command and skills,
  constrains profile paths to Claude home, constrains `repo:` sources to the
  declared source root, requires non-empty hook command fragments, and reads
  only real Claude hook command entries. Why not 10: the checker remains a
  diagnostic profile guard, not proof that Claude runtime loaded a profile.
- Product/methodology critic: score 9.0 PASS, critic scope global install and
  target-project user flow. Blocking findings: none after README uses
  `CLAUDE_HOME`, installs canonical mirrors plus checker assets, keeps target
  projects on `/init-harness`, and states the profile check is diagnostic rather
  than v2 publication evidence. Why not 10: users with custom hook docs must
  still opt those contracts into the manifest.
- Blocking findings: none remaining for this Claude global profile governance
  batch.
- Follow-up/residual risk: profile governance is explicit-manifest based and
  does not semantic-parse every `~/.claude` rule or prove runtime hook
  registration. Users add hook contracts or blocked model IDs only for local
  files they intentionally govern.
- Score handling: all critic scores are 9.0 PASS; why-not-10 items are accepted
  residual risks for diagnostic profile governance and downstream local setup.
- Rerun status: repeated focused tests, SS-008, compatibility checks, trace
  provenance, and manual adversarial probes passed after follow-up fixes.
- Final acceptance: PASS for committing and pushing the Claude profile drift
  governance batch.
