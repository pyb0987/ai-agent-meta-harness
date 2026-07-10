# Multi-Review Governance Boundary Review

Review scope: make the global multi-review skill safe outside harness-governed
projects by moving strict `check-multi-review-result.py` use to a project-local
governance contract. Changed surfaces: Claude and Codex multi-review skills,
init/bootstrap guidance, Codex plugin asset inventory, generated plugin copies,
and targeted tests.

Search-set verification:

- SKIPPED: pre-change aggregate search-set capture was not taken before this
  focused global-skill/governance-boundary correction. The accepted after-checks
  below cover the changed skill, plugin, mirror, and validator surfaces.
- AFTER: PASS `python3 scripts/sync-codex-plugin.py --check` covered staged
  Codex plugin source/generated consistency.
- AFTER: PASS `python3 adapters/codex/scripts/smoke-local-plugin.py` covered
  plugin bundle asset inventory, including the new multi-review validator.
- AFTER: PASS `python3 -m py_compile adapters/codex/scripts/check-multi-review-result.py`
  covered syntax for the new Codex adapter validator copy.
- AFTER: PASS `python3 -m unittest tests.test_claude_compat_install_smoke tests.test_claude_multi_review_skill adapters.codex.tests.test_multi_review_skill adapters.codex.tests.test_local_plugin_smoke tests.test_sync_codex_plugin adapters.codex.tests.test_direct_copy_fallback_reporting`
  covered Claude mirrors, skill wording, plugin smoke behavior, sync inventory,
  and direct-copy fallback documentation.
- AFTER: PASS `git diff --check` covered whitespace safety.

Multi-review:

- Review mode: `FALLBACK_NONINDEPENDENT`. Critics were run sequentially in the
  implementation session; this is repository-maintenance review evidence, not a
  stable `MultiReviewResult` governance artifact.
- Portability boundary critic: score 9.0 PASS. Blocking findings: none. Why
  not 10: the global skill is now explicit that advisory multi-review is always
  available and project-local governance mode activates only with a local
  declaration plus `scripts/check-multi-review-result.py`; residual risk is
  accepted because future project declarations remain prose-detected.
- Validation-layer critic: score 9.0 PASS. Blocking findings: none. Why not
  10: governance PASS is bound to the executable project-local validator, while
  non-governance projects are directed to advisory results; residual risk is
  accepted because this patch does not introduce a new structured project
  manifest for governance opt-in.
- Distribution and drift critic: score 9.0 PASS. Blocking findings: none. Why
  not 10: the Codex plugin now carries and smoke-tests the validator asset, but
  there is still no dedicated installer command; residual risk is accepted
  because init/bootstrap guidance names the target copy path.
- Anti-bloat critic: score 9.0 PASS. Blocking findings: none. Why not 10: the
  change adds one shipped validator asset and conditional activation wording
  rather than another governance mechanism; residual risk is accepted because
  future installer work could still add ceremony if not kept narrow.
- Review quality critic: score 9.0 PASS. Blocking findings: none. Why not 10:
  the review used a sequential fallback instead of independent sub-agent
  critics; residual risk is accepted because critic scopes were kept separated
  and the change is covered by executable sync, smoke, mirror, and wording
  tests.
- Fallback-threshold disposition: accepted residual risk because current item
  used sequential fallback only for bounded review synthesis, and executable
  tests cover the changed contract.
- Blocking findings: none remaining for this batch.
- Score handling: all required critics scored 9.0 PASS. Every score 9 records
  why not 10 and residual-risk disposition.
- Rerun status: no blocking fixes were needed after the final review; targeted
  tests, plugin sync check, plugin smoke, py_compile, and whitespace check
  passed.
- Follow-up/residual risk: consider a dedicated target-project installer for
  `scripts/check-multi-review-result.py` if governance validator setup recurs
  often enough to justify more tooling.
- Final acceptance: PASS for committing the multi-review governance boundary
  change.
