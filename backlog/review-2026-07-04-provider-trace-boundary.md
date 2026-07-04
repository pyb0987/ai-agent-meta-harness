# Provider Trace Boundary Review

Review scope: provider-repository boundary for maintainer/user traces, including
README, core methodology/reference mirrors, harness-engineer skills, repository
search-set relocation, governance/search-set scripts, acceptance fixtures, and
tests that prevent raw maintainer traces from being shipped as product state.

Search-set verification:

- SKIPPED: pre-change search-set capture was unavailable because this migration
  intentionally moves the repository regression manifest out of
  `.harness/traces/` and avoids adding new tracked raw trace records. The
  after-checks below cover the accepted boundary.
- AFTER: PASS `python3 -m unittest tests/test_repository_search_set.py tests/test_search_set_evidence.py tests/test_core_methodology_boundaries.py tests/test_readme_methodology_boundaries.py tests/test_maintenance_policy_boundaries.py`
  covered the repository search-set product boundary, search-set evidence
  checker path migration, methodology/reference mirrors, README claims, and
  maintenance policy boundaries.
- AFTER: PASS `python3 -m unittest tests/test_governance_evidence_refs.py tests/test_governance_acceptance_cli.py tests/test_governance_review_import.py tests/test_harness_dogfood.py tests/test_verify_release.py tests/test_run_search_set.py`
  covered governance evidence refs, acceptance CLI fixtures, review import
  fixtures, target-project dogfood fallback behavior, release verification, and
  run-search-set path resolution.
- AFTER: PASS `python3 scripts/update-governance-fixtures.py --check` covered
  deterministic fixture binding after packet/path updates.
- AFTER: PASS `python3 scripts/run-search-set.py --list` confirmed the tracked
  repository manifest is loaded from `backlog/repository-search-set.md`.
- AFTER: PASS `python3 scripts/run-search-set.py --case SS-006` covered the
  active regression that repository search-set state stays outside maintainer
  traces.
- AFTER: PASS `python3 scripts/check-compat-mirrors.py` covered core/reference
  and Claude compatibility mirrors.
- AFTER: PASS `python3 scripts/sync-codex-plugin.py --check` covered Codex
  plugin bundle copies.

Multi-review:

- Review mode: `FALLBACK_NONINDEPENDENT`. Critics were run sequentially in this
  session, not as independent sub-agents; this is sufficient for advisory
  repository maintenance review but not stable governance acceptance evidence.
- Product-boundary critic: score 9.0 PASS, critic scope whether the public repo
  now ships harness product changes rather than maintainer raw working memory.
  Blocking findings: none. The raw `.harness/traces/evolution`,
  `.harness/traces/failures`, and `.harness/traces/experiments` paths are
  removed from the git index, `.harness/traces/` is ignored, and
  `tests/test_repository_search_set.py` checks `git ls-files .harness/traces`
  remains empty. Why not 10: local ignored traces can still exist in a
  maintainer checkout, by design.
- User-experience critic: score 9.0 PASS, critic scope whether ordinary users
  still get the trace-backed target-project experience. Blocking findings:
  none. Target-project guidance, dogfood fallback tests, and harness-engineer
  skills still preserve `.harness/traces/` or `.claude/traces/` as project
  memory; only this provider repository stops publishing maintainer raw traces.
  Why not 10: users still need an initialized project or global install before
  traces can accumulate.
- Validation-layer critic: score 9.0 PASS, critic scope false-green paths where
  docs could claim the boundary but tracked files still violate it. Blocking
  findings: none. The invariant is enforced at git-file and executable-test
  layers: `.gitignore`, `git ls-files .harness/traces`, run-search-set loading
  `backlog/repository-search-set.md`, fixture update checks, and focused tests.
  Why not 10: some tests are wording smoke checks around docs; the hard
  invariant is the tracked-file/search-set check.
- Governance-compatibility critic: score 9.0 PASS, critic scope whether v2
  packet/search-set validation still works after moving the repository
  manifest. Blocking findings: none. `scripts/check-governance-acceptance.py`,
  `scripts/check-search-set-evidence.py`, fixtures, and governance tests now use
  `backlog/repository-search-set.md`; acceptance fixture command evidence was
  re-bound with `scripts/update-governance-fixtures.py --write` and verified
  with `--check`. Why not 10: stable evidence fields still use the historical
  `trace:` prefix for search-set anchors; renaming that schema would be larger
  and is not needed for this boundary.
- Anti-bloat critic: score 9.0 PASS, critic scope whether the change adds
  ceremony or user-facing complexity. Blocking findings: none. The change
  removes shipped raw trace state and replaces it with one tracked repository
  regression manifest, while keeping target-project trace behavior unchanged.
  Why not 10: scripts needed a compatibility fallback for target projects that
  still use `.harness/traces/search-set.md`.
- Review-quality critic: score 9.0 PASS, critic scope whether this review is
  probe-backed rather than self-attested. Blocking findings: none for advisory
  repository maintenance. Focused and governance test commands were executed,
  fixture drift was checked, SS-006 was run, mirrors and plugin sync were
  checked. Why not 10: no structured `MultiReviewResult` artifact was generated,
  so this is not governance-mode acceptance evidence.
- Blocking findings: none remaining for the provider trace boundary batch.
- Follow-up/residual risk: This does not prevent a maintainer from manually
  committing a future trace-like file outside `.harness/traces/`; ordinary code
  review and the repository-search-set tests should catch the intended boundary
  if it regresses.
- Score handling: all critic scores are 9.0 PASS; why-not-10 items are accepted
  residual risks for a low-ceremony provider-boundary cleanup.
- Rerun status: focused tests, governance tests, fixture drift check, SS-006,
  compatibility mirrors, and plugin sync all passed.
- Final acceptance: PASS for staging this provider trace boundary batch.
