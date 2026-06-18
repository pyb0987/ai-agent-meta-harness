# Worktree Trace Root Review

Review scope: worktree-safe trace-root guidance in core methodology, Claude
init-harness instructions, compatibility mirrors, example CLAUDE.md, focused
tests, and repository trace records.

Search-set verification:

- BEFORE: SKIPPED no pre-change Active search-set run was captured before
  applying the worktree trace-root guidance patch.
- AFTER: PASS `python3 scripts/check-compat-mirrors.py` covered compatibility
  mirrors.
- AFTER: PASS `python3 -m unittest tests/test_repository_search_set.py`
  covered repository trace-root surface.
- AFTER: PASS `python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_claude_init_harness_fixture.py tests/test_maintenance_policy_boundaries.py`
  covered the new Claude worktree shared-root guard.

Multi-review:

- Mode: sequential fallback review in the parent context; no sub-agent
  independence claimed.
- Trace-root critic: score 9.0 PASS, critic scope shared trace-root invariant
  for git worktree projects. Blocking findings: none after the guidance states
  that relative trace roots are worktree-relative unless made shared, and that
  local-only instruction files are insufficient unless bootstrapped everywhere.
  Why not 10: downstream projects still need to choose the actual stable
  absolute path or bootstrap mechanism during installation.
- Claude adapter critic: score 9.0 PASS, critic scope `/init-harness` behavior
  and generated `CLAUDE.md` requirements. Blocking findings: none after the
  command scans worktree usage, ignored/local-only instruction files, and
  bootstrap scripts, then requires one recorded active root for every worktree.
  Why not 10: no live downstream Claude worktree was created in this repo run.
- Evidence critic: score 9.0 PASS, critic scope regression coverage and trace
  provenance. Blocking findings: none after SS-007, the failure trace, the
  evolution trace, compatibility mirror checks, and trace retrieval provenance
  validation passed. Why not 10: the guard verifies shipped guidance, not a
  target project's external `~/.claude` install state.
- Blocking findings: none remaining for this instruction/test/trace batch.
- Follow-up/residual risk: target projects must still reinstall the Claude
  command and methodology files into `~/.claude`, then choose or document the
  concrete shared trace root for their own worktree layout.
- Score handling: all critic scores are 9.0 PASS; why-not-10 items are accepted
  residual risks for downstream installation and project-specific path choice.
- Rerun status: focused search-set and mirror/provenance verification passed
  after the review record was added.
- Final acceptance: PASS for committing and pushing the worktree trace-root
  hardening batch.
