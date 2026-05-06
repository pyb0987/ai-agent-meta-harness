# Codex Adapter Backlog Archive

Completed backlog records moved from the active backlog file. Preserve full Completion Gate, review score, VETO, search-set, and residual-risk records here.

### 2. Clarify Codex trace-root migration behavior

Status: 완료
Owner: Codex session autoresearch trace-root worktree
Branch: codex/autoresearch-trace-root-alignment
Started: 2026-05-01
Scope:
- adapters/codex/skills/autoresearch/SKILL.md
- adapters/codex/hook-schema.md
- plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md
- plugins/ai-agent-meta-harness/hook-schema.md
- backlog/codex-adapter.md

Codex prefers `.harness/traces/`, but may need to reuse existing `.claude/traces/` history when a project is migrated from Claude Code.

Decision implemented:

- `init-codex-harness` now keeps `.claude/traces/` temporarily only when it has
  meaningful history, and initializes `.harness/traces/` when the Claude root is
  empty or template-only.
- `harness-engineer` now labels `.claude/traces/` reuse as temporary history
  reuse when Codex is operating on a migrated project.
- Both skills define when to propose migration into `.harness/traces/` and the
  minimum migration plan: preserve `search-set.md`, copy or move raw trace
  files, update `AGENTS.md`, record source/destination roots, and write an
  evolution trace before writing new traces to the new root.
- `autoresearch` Setup Mode now chooses trace roots by meaningful history
  instead of directory existence alone, so an empty or template-only
  `.harness/traces/` does not outrank a `.claude/traces/` root with real
  failures, evolution entries, experiment episodes, or Active search-set cases.
- The generated local plugin copy of the `autoresearch` skill is synchronized
  with the canonical adapter skill.
- Hook schema assumptions were re-verified because the changed `autoresearch`
  skill is a hook-sensitive adapter surface; no Codex hook output or config
  contract changes were needed.

Remaining follow-up work:

- Add a fixture smoke test when init skill execution can be tested
  mechanically.

Review outcome:

- Verification: PASS; `rg -n "meaningful history|trace root|\\.claude/traces|\\.harness/traces|Setup Mode|temporary history reuse|template-only" adapters/codex/skills/autoresearch/SKILL.md plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md backlog/codex-adapter.md`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, and `git diff --check`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review mode: `FALLBACK_NONINDEPENDENT` sequential review; no
  independent sub-agents were requested for this worktree session.
- Trace-root semantics critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the skill now evaluates both roots by
  meaningful history before selecting `.harness/traces/`.
- Generated plugin critic: score 10, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: none; the plugin copy is generated from the
  canonical adapter skill and `--check` passes.
- Hook schema critic: score 10, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: none; the official Codex hooks and config docs were
  re-checked and the existing `PreToolUse`, `PermissionRequest`, and
  `features.codex_hooks` assumptions remain unchanged.
- Maintenance compliance critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; scope, verification, search-set skip,
  review handling, and merge eligibility are recorded.
- Score handling: no critic scored below 9; no VETO triggered. No score was 9,
  so no why-not-10 residual-risk item was required.
- Rerun status: all sequential fallback critics reviewed the final scoped diff
  after verification passed; no VETO fixes required.
- Final acceptance: accepted and merged to `main` in commit
  `d231ccb merge: refresh autoresearch trace root branch`.
### 17. Define Codex plugin marketplace metadata policy

Status: 완료
Owner: Codex session codex-label-sub-agent-extension
Branch: codex-label-sub-agent-extension
Started: 2026-05-01
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- backlog/codex-adapter.md

Recovery note:
- Original session compliance: incomplete; implementation files were edited
  before the Start Gate was reported.
- Actual changed files: `adapters/codex/plugin-scope.md`,
  `plugins/ai-agent-meta-harness/plugin-scope.md`, and
  `backlog/codex-adapter.md`.
- Scope deviations: none from the reconstructed scope.
- Verification: PASS; `python3 scripts/sync-codex-plugin.py --check` and
  `python3 adapters/codex/scripts/smoke-local-plugin.py`.
- Search-set verification: SKIPPED; no `search-set.md` exists in this
  repository worktree.
- Multi-review required: yes, because this affects Codex plugin distribution
  policy and future marketplace metadata contracts.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; all required critics scored at least 9, and every score of 9 records
  why it was not 10.
- Merge eligible: yes; merged to `main` in commit
  `d77759e docs: define codex marketplace metadata policy`.

The marketplace path is future work, but plugin metadata choices can leak into local plugin structure if left implicit.

Decision implemented:

- `adapters/codex/plugin-scope.md` now treats marketplace metadata as a release
  surface, separate from local-only plugin dogfooding.
- The policy fixes future identity values: package name
  `ai-agent-meta-harness`, display name `AI Agent Meta-Harness`, developer
  tools / agent harnessing category, local-plugin-first installation, and no
  external authentication by default.
- `.agents/plugins/marketplace.json` must not be generated during normal local
  plugin development.
- Marketplace metadata is gated on local activation smoke coverage, documented
  marketplace install behavior, release-checklist validation, and generated
  single-source metadata.
- Any local UI-ordering metadata before publication must be marked local-only
  and smoke-tested for activation, skill discovery, and hook registration
  neutrality.

Remaining follow-up work:

- Add marketplace metadata validation to the release checklist only when the
  marketplace path is ready to publish.
- Revisit the category if Codex publishes an official marketplace taxonomy.

Review outcome:

- Distribution contract critic: score 9, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: the category is intentionally provisional
  until Codex publishes an official taxonomy. Why not 10: the policy names a
  sensible category but cannot prove future marketplace taxonomy alignment yet.
- Generated artifact critic: score 9, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: generated `plugins/ai-agent-meta-harness/plugin-scope.md`
  must remain sync-checked with canonical `adapters/codex/plugin-scope.md`.
  Why not 10: correctness depends on the existing sync check continuing to
  cover this generated document.
- Release-gate critic: score 9, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: marketplace metadata validation is deliberately
  deferred until the marketplace path becomes real release work. Why not 10:
  the release gate is specified as a future condition, not implemented as an
  executable check now.
- Score handling: no critic scored below 9; no VETO triggered.
- Rerun status: all sequential fallback critics reviewed the final scoped diff
  after verification passed.
- Final acceptance: accepted and merged to the integration branch.
### 18. Add local plugin artifact smoke test

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- backlog/codex-adapter.md

The local plugin bundle cannot be considered ready until the artifact can be checked mechanically. This item intentionally validates the generated plugin artifact, not Codex runtime activation.

Decision implemented: ship a local plugin artifact smoke test that validates the generated bundle before Codex dogfooding.

Implemented foundation:

- `adapters/codex/scripts/smoke-local-plugin.py` validates `.codex-plugin/plugin.json` exists, parses, and points skills at `./skills/`.
- The smoke test verifies the expected Codex skills exist and declare matching skill names.
- The smoke test verifies checker, hook smoke, hook templates, AGENTS template, and protected-path template assets are present and non-empty.
- The smoke test fails if the generated plugin README stops documenting the degraded direct-copy fallback safety warning.
- The smoke test rejects a manifest that advertises runtime `hooks` before Codex activation coverage is smoke-tested.
- Unit tests cover the passing bundle and missing-manifest, invalid-manifest, wrong-skills-path, runtime-hooks, missing-skill, missing-asset, and missing-warning failures.
- The tracked pre-commit hook runs the smoke test after the generated plugin sync check.

Decision implemented for release checklist:

- `MAINTENANCE.md` now includes "Codex local plugin artifact smoke test passes"
  in the formal release checklist.
- The standard verification set also runs
  `python3 adapters/codex/scripts/smoke-local-plugin.py`.

Remaining follow-up work:

- none for the local plugin artifact smoke test.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `rg -n "Codex local plugin artifact smoke test passes|smoke-local-plugin.py" MAINTENANCE.md backlog/codex-adapter.md`, `python3 scripts/check-maintenance-review.py`, and `git diff --check`.
- Search-set verification: SKIPPED; backlog-only reconciliation does not change
  harness behavior, and this repository worktree has no `search-set.md`.
- Multi-review required: no, because this only reconciles stale backlog wording
  with an already implemented release checklist item.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no critics ran and no VETO
  handling was needed.
- For each score 9, why not 10: not applicable.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 20. Add Codex marketplace metadata release validation

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- scripts/check-codex-marketplace-metadata.py
- tests/test_check_codex_marketplace_metadata.py
- backlog/codex-adapter.md

Marketplace metadata is intentionally deferred, but before publication the
repository should mechanically validate that published metadata matches the
adapter policy and official Codex marketplace expectations.

Original improvement:

- Re-check the official Codex marketplace taxonomy and replace the provisional
  `developer tools / agent harnessing` category if a canonical category exists.
- Add a validation command for marketplace metadata once `.agents/plugins/marketplace.json`
  or an equivalent publication manifest exists.
- Include marketplace metadata validation in the release checklist only after
  the marketplace distribution path is ready to publish.
- Confirm the metadata source remains generated from canonical adapter files
  rather than manually dual-edited plugin metadata.

Decision implemented:

- Re-checked public official OpenAI Codex sources on 2026-05-03. The available
  help/release-note pages describe Codex plugins and a curated plugins
  directory, but did not expose a canonical marketplace metadata schema or
  category taxonomy usable by this repository.
- `adapters/codex/plugin-scope.md` now records that official-source check and
  keeps `developer tools / agent harnessing` provisional until an official
  taxonomy/schema is cited.
- `scripts/check-codex-marketplace-metadata.py` now validates the current
  deferred release state: it passes when no publication manifest exists, and
  fails if `.agents/plugins/marketplace.json` appears before the policy records
  publication readiness, official schema/taxonomy evidence, and a generated
  metadata source.
- `tests/test_check_codex_marketplace_metadata.py` covers the accepted deferred
  state, fail-fast behavior when a publication manifest appears too early,
  ready-policy markers, and missing policy markers.
- `plugins/ai-agent-meta-harness/plugin-scope.md` was synchronized with the
  canonical adapter policy.
- The release checklist remains unchanged because marketplace publication is
  still not release-ready; this validator is a publication-prep guard, not part
  of the standard pre-commit path yet.

Remaining follow-up work:

- Add full marketplace metadata validation to the release checklist only after
  an official schema/taxonomy is cited and the marketplace publication path is
  ready to publish.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/plugin-scope.md`,
  `plugins/ai-agent-meta-harness/plugin-scope.md`,
  `scripts/check-codex-marketplace-metadata.py`,
  `tests/test_check_codex_marketplace_metadata.py`, and
  `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_check_codex_marketplace_metadata.py`, `python3 scripts/check-codex-marketplace-metadata.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 -m unittest discover -s adapters/codex/tests`, `git diff --check`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Codex distribution/release
  validation policy and generated plugin policy surface.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Deferred-state guard critic score 10,
  verdict PASS, Blocking findings: none. Official-source boundary critic score
  9, verdict PASS, Blocking findings: none. Generated-plugin policy sync critic
  score 10, verdict PASS, Blocking findings: none. Maintenance compliance
  critic score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Official-source boundary critic was 9 because
  public official Codex pages currently mention plugins but do not expose a
  canonical marketplace taxonomy/schema to validate against; no backlog item
  added because the remaining action is already captured above as future
  release-checklist validation once official publication metadata exists.
  Maintenance compliance critic was 9 because review used documented
  sequential fallback rather than independent sub-agents; no backlog item added
  because the residual risk is process-level review independence in this
  session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: marketplace taxonomy/category remains provisional
  until an official schema or taxonomy is cited; the new checker fails if
  publication metadata appears before that readiness evidence is recorded.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 21. Document Codex hook template install paths

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/README.md
- backlog/codex-adapter.md

The Codex adapter ships checker, hook, pre-commit, CI, protected-path, and
AGENTS reminder templates, but target-project setup docs do not yet say exactly
where each template should be copied or which smoke command confirms the copied
assets still produce the expected deny JSON.

Original improvement:

- Document target-project destination paths for each Codex autoresearch
  protection asset.
- Distinguish active local project guardrails from plugin runtime hook
  registration, which remains gated on activation smoke coverage.
- Keep the generated plugin README synchronized with the canonical adapter
  README.

Decision implemented:

- `adapters/codex/README.md` now maps every shipped autoresearch protection
  asset to a concrete target-project path.
- The install docs include the copied-project smoke command that checks Codex
  hook deny JSON using the target project's copied checker and protected-path
  file.
- The docs explicitly distinguish project-local copied guardrails from Codex
  plugin runtime hook registration, which remains gated on local plugin
  activation and tool-event coverage.
- `plugins/ai-agent-meta-harness/README.md` is synchronized from the canonical
  adapter README.

Remaining follow-up work:

- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks`
  only after local plugin activation and tool-event coverage are smoke-tested.
- Revisit templates when Codex hook interception semantics change, especially
  whether file-edit tools emit `PreToolUse`.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/README.md`,
  `plugins/ai-agent-meta-harness/README.md`, and `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 scripts/sync-codex-plugin.py --write`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 -m unittest discover -s adapters/codex/tests`, and `git diff --check`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Codex install/distribution
  guidance and hook/protection setup instructions.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Install-path clarity critic score 10,
  verdict PASS, Blocking findings: none. Hook-registration boundary critic
  score 10, verdict PASS, Blocking findings: none. Generated-plugin sync critic
  score 10, verdict PASS, Blocking findings: none. Maintenance compliance
  critic score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: runtime hook registration remains gated on Codex
  local plugin activation and tool-event smoke coverage.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 22. Document non-GitHub CI BASE_REF setup

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/README.md
- backlog/codex-adapter.md

The autoresearch protected-path checker supports CI mode outside GitHub
Actions, but the adapter docs only ship a GitHub Actions template. Other CI
systems need explicit guidance for choosing `BASE_REF` or passing `--base-ref`
so the checker compares `HEAD` against the intended merge base.

Original improvement:

- Document `BASE_REF`, `GITHUB_BASE_REF`, and `--base-ref` precedence.
- Give non-GitHub CI examples that fetch the base branch and run the checker.
- Keep the generated plugin README synchronized with the canonical adapter
  README.

Decision implemented:

- `adapters/codex/README.md` now documents CI comparison-base precedence:
  `--base-ref`, `BASE_REF`, `GITHUB_BASE_REF`, then `origin/main`.
- The docs explain how plain branch names are expanded to `origin/<branch>` and
  that CI must fetch the selected base ref before running the checker.
- The docs include environment-variable, explicit `--base-ref`, and generic
  merge-request examples for non-GitHub CI.
- The generated plugin README is synchronized with the canonical adapter README.

Remaining follow-up work:

- Add a concrete CI provider template only if a non-GitHub CI surface becomes a
  supported distribution target.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/README.md`,
  `plugins/ai-agent-meta-harness/README.md`, and `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 scripts/sync-codex-plugin.py --write`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 scripts/check-maintenance-review.py`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 -m unittest discover -s adapters/codex/tests`, and `git diff --check`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes CI guardrail setup guidance
  for autoresearch protection.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: CI base-ref correctness critic score 10,
  verdict PASS, Blocking findings: none. Install-doc clarity critic score 10,
  verdict PASS, Blocking findings: none. Generated-plugin sync critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score 9,
  verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: add provider-specific CI templates only after a
  non-GitHub CI provider becomes a supported target.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 23. P1 align Codex multi-review threshold with maintenance VETO policy

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-02
Scope:
- adapters/codex/skills/multi-review/SKILL.md
- plugins/ai-agent-meta-harness/skills/multi-review/SKILL.md
- adapters/codex/tests/test_multi_review_skill.py
- backlog/codex-adapter.md
- backlog/core.md
- backlog/claude-adapter.md

Source review: 2026-05-02 multi-review MIXED.

`MAINTENANCE.md` treats reviewer scores below 9 as blocking VETO unless the
finding is resolved and rerun, but the Codex `multi-review` skill can still
allow PASS when all reviewers score at least 7. That lets adapter or harness
decisions pass under a weaker local rule than the repository governance gate.

Original improvement:

- Update `adapters/codex/skills/multi-review/SKILL.md` so repository
  maintenance and harness-affecting decisions use the same below-9 VETO
  threshold as `MAINTENANCE.md`.
- Preserve any lower-score advisory mode only when clearly labeled as
  non-governance/non-acceptance review.
- Sync the generated plugin skill copy and add or update tests/checks if a
  mechanical skill-content assertion exists.

Decision implemented:

- `adapters/codex/skills/multi-review/SKILL.md` now separates governance mode
  from advisory mode.
- Governance mode covers repository maintenance, harness-affecting changes,
  release gates, hooks, protected-file semantics, adapter behavior, and durable
  install/distribution contracts.
- Governance PASS now requires every required critic to score at least 9 with
  no veto; any required critic below 9 is VETO until resolved and rerun.
- Score 9 requires why-not-10 handling plus backlog follow-up or explicit
  residual-risk acceptance.
- The old 7-point threshold survives only as `ADVISORY PASS` for
  non-governance, non-acceptance exploratory review.
- `plugins/ai-agent-meta-harness/skills/multi-review/SKILL.md` is synchronized
  from the canonical adapter skill.
- `adapters/codex/tests/test_multi_review_skill.py` asserts the governance
  threshold and generated plugin sync.
- The source review follow-up findings are recorded as new backlog items in
  `backlog/core.md`, `backlog/claude-adapter.md`, and this file so the
  threshold-alignment review does not lose actionable residual risks.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/skills/multi-review/SKILL.md`,
  `plugins/ai-agent-meta-harness/skills/multi-review/SKILL.md`,
  `adapters/codex/tests/test_multi_review_skill.py`, and
  `backlog/codex-adapter.md`, plus source-review follow-up backlog additions in
  `backlog/core.md` and `backlog/claude-adapter.md`.
- Scope deviations: source-review follow-up backlog additions were recorded
  outside the Codex adapter backlog so cross-cutting and Claude-specific
  residual risks remain discoverable in their owning backlog files.
- Verification results: PASS; `python3 scripts/sync-codex-plugin.py --write`, `python3 -m unittest adapters/codex/tests/test_multi_review_skill.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 -m unittest discover -s adapters/codex/tests`, `python3 scripts/check-maintenance-review.py`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Codex adapter review-gate
  semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Governance-threshold critic score 10,
  verdict PASS, Blocking findings: none. Advisory-mode boundary critic score
  10, verdict PASS, Blocking findings: none. Generated-plugin/test critic score
  10, verdict PASS, Blocking findings: none. Maintenance compliance critic
  score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Backlog items added from source review: `backlog/core.md` items 20-24,
  `backlog/claude-adapter.md` items 4-6, and this `backlog/codex-adapter.md`
  item 23.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

## Current Status

- Source reviews: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` and `adapters/codex/skills/autoresearch/SKILL.md`.
- Last reviewed baselines are the commits linked from the relevant review notes or release notes; avoid keeping a single stale baseline here.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
### 24. P2 prefer meaningful Claude history over empty Codex trace roots

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/skills/init-codex-harness/SKILL.md
- plugins/ai-agent-meta-harness/skills/init-codex-harness/SKILL.md
- tests/test_codex_init_trace_root_selection.py
- backlog/codex-adapter.md

Source review: 2026-05-03 candidate triage.

The Codex init workflow currently chooses existing `.harness/traces/` before
checking existing `.claude/traces/` with meaningful history. That can prefer an
empty or template-only `.harness/traces/` over meaningful Claude history,
recreating the split-history risk that active trace-root selection is meant to
avoid.

Decision implemented:

- `init-codex-harness` now chooses trace roots by meaningful history before
  path preference.
- `.harness/traces/` remains preferred when history evidence is absent or
  equivalent, but meaningful `.claude/traces/` history is reused temporarily
  when `.harness/traces/` is missing, empty, or template-only.
- Empty directories, `.keep` files, and untouched `search-set.md` templates are
  explicitly non-meaningful and must not outrank real history in the other
  root.
- Both roots with meaningful but divergent history now require a migration or
  merge plan before new traces are written.
- The generated local plugin copy is synchronized with the canonical adapter
  skill.
- `tests/test_codex_init_trace_root_selection.py` locks the meaningful-history
  selection contract and checks that the generated plugin carries the same
  markers.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/skills/init-codex-harness/SKILL.md`,
  `plugins/ai-agent-meta-harness/skills/init-codex-harness/SKILL.md`,
  `tests/test_codex_init_trace_root_selection.py`, and
  `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_codex_init_trace_root_selection.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`, `git diff --check`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Codex init trace-root
  selection semantics for migrated projects.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Trace-root selection semantics critic
  score 10, verdict PASS, Blocking findings: none. Migration-safety critic
  score 10, verdict PASS, Blocking findings: none. Generated plugin and
  regression coverage critic score 10, verdict PASS, Blocking findings: none.
  Maintenance compliance critic score 9, verdict PASS, Blocking findings:
  none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: coverage is lexical skill-contract validation rather
  than actual Codex skill execution on a migrated project fixture; real project
  dry-run work remains tracked by item 11.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 25. P2 connect marketplace metadata checker to publication gates when ready

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- .githooks/pre-commit
- MAINTENANCE.md
- scripts/check-codex-marketplace-metadata.py
- tests/test_pre_commit_hook.py
- tests/test_check_codex_marketplace_metadata.py
- backlog/codex-adapter.md

Source review: 2026-05-03 candidate triage.

`scripts/check-codex-marketplace-metadata.py` protects publication readiness,
but it is intentionally not part of current pre-commit or standard verification
while no marketplace publication manifest exists. Once a publication manifest
or ready marker is introduced, relying on manual invocation could let metadata
bypass the intended release guard.

Decision implemented:

- `.githooks/pre-commit` now runs
  `python3 scripts/check-codex-marketplace-metadata.py`.
- The release checklist in `MAINTENANCE.md` now requires the Codex marketplace
  metadata readiness check to pass.
- The current deferred state remains unchanged: the checker passes while no
  publication manifest exists and fails if marketplace metadata appears before
  publication readiness, official schema/taxonomy evidence, and generated
  metadata source are recorded.
- In a Git worktree, the checker validates the staged policy and staged
  publication manifest state so pre-commit cannot be bypassed by partial-stage
  working-tree edits.
- `tests/test_pre_commit_hook.py` now verifies the pre-commit hook includes the
  marketplace metadata checker.
- `tests/test_check_codex_marketplace_metadata.py` now covers a staged
  publication manifest hidden by a cleaned working-tree copy.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `.githooks/pre-commit`, `MAINTENANCE.md`,
  `scripts/check-codex-marketplace-metadata.py`,
  `tests/test_pre_commit_hook.py`,
  `tests/test_check_codex_marketplace_metadata.py`, and
  `backlog/codex-adapter.md`.
- Scope deviations: expanded to make the newly automated pre-commit gate
  staged-content aware before acceptance.
- Verification results: PASS; `python3 scripts/check-codex-marketplace-metadata.py`, `python3 -m unittest tests/test_pre_commit_hook.py tests/test_check_codex_marketplace_metadata.py`, `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`, `git diff --check`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes release/pre-commit gate
  coverage for Codex marketplace publication readiness.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Gate-trigger critic score 10, verdict
  PASS, Blocking findings: none. Deferred-publication policy critic score 10,
  verdict PASS, Blocking findings: none. Pre-commit coverage critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score 9,
  verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: marketplace publication is still deferred until
  official schema/taxonomy evidence, publication readiness, and generated
  metadata source are recorded; the checker now protects that deferred boundary
  through pre-commit and release checklist paths.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 1. Add Codex sandbox/escalation recording template

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

The Codex `harness-engineer` skill says sandbox, permission, and network outcomes are first-class verification outcomes, but it does not give a compact recording template.

Decision implemented:

- `adapters/codex/skills/harness-engineer/SKILL.md` now includes a compact
  command outcome template with `command`, `status`, `blocked_by`,
  `escalation_required`, `approval_reason`, and `rerun_status`.
- The template lives with Codex verification discipline so actual approval
  mechanics remain in runtime instructions instead of shared core methodology.

Remaining follow-up work:

- Add examples only after real project traces show which blocked-command fields
  need clarification.
### 3. Harden Codex hook enforcement templates

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Decision implemented: ship template-only Codex hook, pre-commit, and CI guardrails that call the shared autoresearch checker without advertising active runtime hooks in the plugin manifest.

Implemented foundation:

- `adapters/codex/templates/hooks/codex-hooks.json.template` calls the checker from Codex `PreToolUse` and `PermissionRequest`.
- `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` provides the local hard-block layer.
- `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml` provides a pull-request CI guardrail with full checkout history and explicit `BASE_REF`.
- `adapters/codex/templates/hooks/agents-autoresearch-protection.md` provides the Level 1 project-instruction reminder layer.
- `adapters/codex/tests/test_hook_templates.py` validates that templates call the shared checker in the expected modes.
- The plugin sync map generates these templates into `plugins/ai-agent-meta-harness/templates/hooks/`.

Remaining follow-up work:

- Add install/smoke-test docs that show exactly where to copy each template in a target project.
- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks` only after local plugin activation and tool-event coverage are smoke-tested.
- Revisit templates when Codex hook interception semantics change, especially whether file-edit tools emit `PreToolUse`.
### 5. Define Codex plugin bundle scope

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Decision implemented: use staged plugin scope so the bundle carries tested Codex adapter surfaces without copying shared core methodology. Details live in `adapters/codex/plugin-scope.md` and the generated plugin copy.

Implemented v0 scope:

- Include skills, explicitly mapped AGENTS template, README, plugin manifest, and plugin scope document.
- Keep `adapters/codex/` canonical and generate plugin files from it.
- Keep direct skill-copy installation only as a documented degraded path for skill text iteration.
- Treat Meta-Harness paper principles as acceptance criteria, not duplicated plugin content.

Remaining follow-up work:

- Runtime hook config under `adapters/codex/hooks/` and manifest `hooks` field are still gated on a local activation smoke test and verified Codex tool-event coverage; template hook/pre-commit/CI/AGENTS assets already exist under `adapters/codex/templates/hooks/`.
- Add completed Codex examples after a real project dry run.
- Expand `plugin.json` beyond `skills` only after runtime assets are executable and smoke-tested.
- Keep marketplace metadata deferred until local plugin activation is proven.
### 6. Standardize Codex verify command discovery

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Claude-oriented flows often center hook recipes. Codex harnesses rely more heavily on `search-set.md` Active verify commands and explicit terminal verification.

Decision implemented:

- `init-codex-harness` now defines command discovery order: package/build-tool
  scripts, local CI jobs, README/project docs, existing AGENTS/CLAUDE
  instructions, then confirmed framework defaults.
- It defines initial Active verify choices for TypeScript/frontend,
  Python/backend/research, mixed repos, and fixed-evaluator research projects.
- `harness-engineer` uses the same discovery order when creating new Active
  seed cases.
- Both skills require deterministic, non-interactive, local commands by default
  and require sandbox, permission, network, dependency, or cost requirements to
  be recorded.

Remaining follow-up work:

- Refine the project-type examples after real TypeScript and Python dry runs.
### 7. Document sub-agent capability matrix by Codex surface

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Codex sub-agent availability may differ across Desktop, CLI, API, and future surfaces.

Decision implemented:

- `adapters/codex/README.md` now documents Codex Desktop, CLI, API, and local
  plugin bundle sub-agent expectations.
- Multi-review falls back to sequential checklist passes with residual risk
  recorded when sub-agents are unavailable.
- Evaluator independence falls back to fixed evaluator scripts with immutable
  boundaries.
- Explorer/evaluator patterns must either accept low contamination risk in the
  parent context or stop and request a runtime surface with isolation.

Remaining follow-up work:

- Update the matrix when Codex CLI/API expose stable sub-agent semantics.
### 8. Expand Codex permission and escalation guidance

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Codex execution depends on sandbox mode, approval policy, writable roots, and network restrictions. This differs from Claude hook/permission assumptions.

Decision implemented:

- The Codex `AGENTS.md` template now asks projects to record sandbox mode,
  writable roots, network availability, approval/escalation policy, missing
  dependencies, and unsafe commands when they affect verification.
- Skipped verification caused by permissions, network, sandboxing, cost, or
  unsafe side effects must be recorded as SKIPPED with the exact reason and
  rerun command, not treated as PASS.

Remaining follow-up work:

- Add a concrete filled example after `adapters/codex/examples/AGENTS.md.example`
  exists.
### 9. Codexize MCP and tool-use policy

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

The core principle favors CLI and direct filesystem access unless an external system requires a tool. Codex has additional surfaces such as tool search, MCP resources, browser plugin, and local browser workflows.

Decision implemented:

- `adapters/codex/README.md` now defines when to use shell/CLI, MCP resources,
  `tool_search`, browser plugin, and web search.
- The policy keeps shell/CLI as the default for repo-local harness diagnosis and
  reserves web search for live external state or source-backed current facts.
- Tool limitations from sandbox, permissions, network, missing dependencies, or
  product-surface limits must be recorded as verification outcomes.

Remaining follow-up work:

- Add surface-specific examples when Codex plugin activation docs exist.
### 10. Add Codex examples

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Claude has a `CLAUDE.md.example`; Codex currently has an `AGENTS.md.template` but not a completed example.

Decision implemented:

- Added `adapters/codex/examples/AGENTS.md.example` as a realistic TypeScript
  web app onboarding reference.
- The example includes trace root, migration note, search-set policy, verify
  commands, Codex permission notes, and an autoresearch pointer.
- `scripts/sync-codex-plugin.py` now maps Codex examples into the generated
  plugin bundle, and `smoke-local-plugin.py` requires the example asset.

Remaining follow-up work:

- Add additional Python/research examples after real dry runs.
### 12. Provide a Codex autoresearch protection checker reference implementation

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Decision implemented: ship a reference checker as a Codex plugin asset, plus a protected-path template and unit tests for the matcher and hook outputs.

Implemented foundation:

- `adapters/codex/scripts/check-autoresearch-protected.py` supports Codex `PreToolUse`, Codex `PermissionRequest`, pre-commit, and CI modes.
- `adapters/codex/templates/autoresearch-protected.txt` provides the project-local `.harness/autoresearch-protected.txt` starting point.
- `adapters/codex/tests/test_check_autoresearch_protected.py` covers exact path matching, prefix matching, Codex deny JSON shapes, Bash/pathlib evaluator-write detection, and pre-commit violation detection.
- `adapters/codex/scripts/smoke-autoresearch-hooks.py` asserts Codex hook deny shapes for a pathlib evaluator write payload.
- The plugin sync map generates checker and protected-path template assets into `plugins/ai-agent-meta-harness/`.

Remaining follow-up work:

- Add install/smoke-test docs that wire the checker and templates into a target project.
- Add a non-GitHub CI variant or document how to set `BASE_REF` outside GitHub Actions.
### 13. Make Codex hook smoke tests mechanically assert output

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Decision implemented: ship an executable smoke assertion script that fails non-zero when Codex hook output JSON drifts from the expected event-specific deny shapes.

Implemented foundation:

- `adapters/codex/scripts/smoke-autoresearch-hooks.py` runs checker hook modes with protected `evaluate.py` payloads.
- The smoke script asserts `PreToolUse` returns `hookSpecificOutput.permissionDecision == "deny"`.
- The smoke script asserts `PermissionRequest` returns `hookSpecificOutput.decision.behavior == "deny"`.
- The smoke script rejects missing output, invalid JSON, malformed key sets, and the legacy top-level `decision` shape.
- The plugin sync map generates the smoke script into `plugins/ai-agent-meta-harness/scripts/`.

Remaining follow-up work:

- Add install docs that show when to run the smoke script during target-project setup.
- Re-run smoke assertions when Codex hook schemas change.
### 14. Track Codex hook schema drift

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Codex hook output shapes may change over time. The adapter now depends on current `PreToolUse` and `PermissionRequest` semantics.

Decision implemented: record the currently verified Codex hook schema and enforce re-verification when hook-sensitive adapter surfaces change.

Implemented foundation:

- `adapters/codex/hook-schema.md` records the verified date, Codex CLI version, official hooks/config source URLs, and expected `PreToolUse`/`PermissionRequest` blocking output shapes.
- `adapters/codex/scripts/check-codex-hook-schema-drift.py` validates the schema reference markers.
- The drift checker fails in pre-commit when hook-sensitive staged changes omit a staged `adapters/codex/hook-schema.md` update or re-verification.
- The drift reference and checker are generated into the local plugin bundle.
- Unit tests cover reference validation and the staged-change policy.

Remaining follow-up work:

- If official Codex hook interception semantics change, add a specific backlog item before enabling runtime plugin `hooks` manifest fields.
- Add the hook schema drift check to the formal release checklist when that checklist is introduced.
### 15. Clarify local-only protection reporting

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

The `autoresearch` skill allows local-only protection when CI is unavailable, but the reporting format can be more explicit.

Decision implemented:

- `adapters/codex/skills/autoresearch/SKILL.md` now reports
  `Protection level: incomplete | local-only | shared-repo | structural` in
  Setup Mode output.
- Skipped or unsmoke-tested minimum local protection is `incomplete` and unsafe
  for unattended autoresearch runs.
- Passing minimum local protection with unavailable CI is `local-only` and must
  include the skipped CI reason.
- `shared-repo` and `structural` are reserved for CI/shared enforcement and
  additional single-source/drift-check protections.

Remaining follow-up work:

- Add a concrete setup transcript after a real autoresearch dry run exercises
  all protection levels.
### 16. Extend the Codex plugin layout as assets grow

Status: 완료

Legacy archive exception:

- This record predates the modern Completion Gate policy and was preserved
  during backlog archive migration; no reconstructed Completion Gate is added.

Decision implemented: `plugins/ai-agent-meta-harness/` is the generated local plugin root, with `adapters/codex/` remaining canonical. `scripts/sync-codex-plugin.py` owns `--write` and `--check`, and pre-commit runs the check.

Remaining follow-up work:

- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks` only after local plugin activation and tool-event coverage are smoke-tested; template hook/pre-commit/CI/AGENTS mappings are already implemented.
- Add examples to the generated path mapping when Codex examples are introduced.
- Decide whether `.codex-plugin/plugin.json` should remain hand-authored canonical metadata or become generated from a smaller metadata source.
- Document and smoke-test the exact local plugin activation command before calling the plugin path fully installed.
- Revisit marketplace metadata only after the local plugin activation path is proven.
### 11. Test Codex adapter on real project types

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/scripts/smoke-init-codex-project-fixtures.py
- adapters/codex/tests/test_init_codex_project_fixtures.py
- adapters/codex/README.md
- adapters/codex/scripts/smoke-local-plugin.py
- plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py
- plugins/ai-agent-meta-harness/README.md
- plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py
- scripts/sync-codex-plugin.py
- backlog/codex-adapter.md

The Codex skills should be exercised on representative projects and refined from traces.

Potential improvement:

- Apply `init-codex-harness` to a TypeScript app.
- Apply it to a Python research repo.
- Apply it to an existing project with `.claude/traces/` history.
- Review the generated traces and search-set entries, then update skill docs based on observed failures.

Decision:

- Added `smoke-init-codex-project-fixtures.py`, which creates representative TypeScript, Python, and migrated-Claude-history project fixtures and validates the expected `init-codex-harness` output contract.
- The smoke checks trace-root selection, Active executable search-set verifier, AGENTS.md harness policy, initial evolution trace shape, exit-status masking guardrails, and no Claude-only hook assumptions.
- Added focused unit tests for passing fixtures and rejection cases: missing expected verifier, masked verifier exit status, split migrated trace roots, stale fixture replacement, and missing migrated-history guidance.
- Bundled the smoke into the generated local Codex plugin and made `smoke-local-plugin.py` require it as an executable asset.
- Documented the fixture smoke command and its boundary in the Codex adapter README.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/codex/README.md`
  - `adapters/codex/scripts/smoke-init-codex-project-fixtures.py`
  - `adapters/codex/scripts/smoke-local-plugin.py`
  - `adapters/codex/tests/test_init_codex_project_fixtures.py`
  - `plugins/ai-agent-meta-harness/README.md`
  - `plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py`
  - `plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py`
  - `scripts/sync-codex-plugin.py`
  - `backlog/codex-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_init_codex_project_fixtures.py`
  - PASS: `python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py`
  - PASS: `python3 plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists (`rg --files -g 'search-set.md'` returned no files). The new fixture smoke itself validates generated fixture search-set entries.
- Multi-review required: yes; this adds Codex adapter smoke coverage that can affect release confidence and future initialization behavior.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Fixture coverage critic: 10/10 PASS; TypeScript, Python, and migrated Claude-history fixtures cover the concrete project-type branches named by the item.
  - Generated plugin/sync critic: 10/10 PASS; the smoke is included in sync requirements, generated into the plugin bundle, executable in the generated bundle, and required by the local plugin artifact smoke.
  - Runtime realism critic: 9/10 PASS; the smoke validates deterministic project-fixture outputs but does not run a live Codex model against external repositories.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, focused verification, standard verification, search-set SKIPPED reason, and Completion Gate are recorded, with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each 9/10 reviewer rating, why not 10:
  - Runtime realism critic: not 10 because this is a deterministic fixture smoke, not live model dogfooding on externally maintained repositories. No backlog item added because the missing piece is a runtime/product-surface and sample-repo availability issue rather than a concrete repo-local fix for this pass.
  - Maintenance compliance critic: not 10 because multi-review was sequential fallback in the parent context, not independent parallel critics. No backlog item added because this is session-surface residual risk, not repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: live Codex model dogfooding on external representative projects would still provide stronger evidence if a stable noninteractive skill runner or approved sample-repo workflow becomes available.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 19. Add true Codex local plugin activation smoke test

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/scripts/smoke-local-plugin-activation.py
- adapters/codex/scripts/smoke-local-plugin.py
- adapters/codex/tests/test_local_plugin_activation_smoke.py
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/scripts/smoke-local-plugin-activation.py
- plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py
- plugins/ai-agent-meta-harness/README.md
- scripts/sync-codex-plugin.py
- tests/test_sync_codex_plugin.py
- backlog/codex-adapter.md

The artifact smoke test proves the generated plugin bundle is internally coherent, but it does not prove Codex has loaded the plugin in a running session.

Potential improvement:

- Identify the exact local Codex plugin activation command or manifest registration path for the supported Codex surface.
- Add an automated smoke test that installs or activates `plugins/ai-agent-meta-harness/` in an isolated Codex home and verifies the expected skills are discoverable through Codex.
- Keep runtime hook manifest fields gated until activation and tool-event coverage are both smoke-tested.

Decision:

- Added `smoke-local-plugin-activation.py`, which creates an isolated `CODEX_HOME`, builds a temporary local marketplace, runs `codex plugin marketplace add <marketplace-root>`, enables `[plugins."ai-agent-meta-harness@local-ai-agent-meta-harness"]`, and validates the activated marketplace copy exposes the expected skill files.
- Generated the activation smoke into the local plugin bundle and made the artifact smoke require the activation smoke as an executable bundled asset.
- Documented the activation smoke command and its boundary: it proves CLI marketplace registration plus enabled-plugin config shape, but not a running Codex Desktop session surfacing the skills to the model or delivering runtime hook events.
- Added focused tests for marketplace metadata generation, enabled-plugin config validation, missing activated skills, successful fake Codex CLI activation, and Codex CLI failure reporting.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/codex/README.md`
  - `adapters/codex/scripts/smoke-local-plugin-activation.py`
  - `adapters/codex/scripts/smoke-local-plugin.py`
  - `adapters/codex/tests/test_local_plugin_activation_smoke.py`
  - `plugins/ai-agent-meta-harness/README.md`
  - `plugins/ai-agent-meta-harness/scripts/smoke-local-plugin-activation.py`
  - `plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py`
  - `scripts/sync-codex-plugin.py`
  - `backlog/codex-adapter.md`
- Scope deviations: none. `tests/test_sync_codex_plugin.py` was inspected as planned but did not need edits because it derives required script fixtures from `REQUIRED_SCRIPT_FILES`.
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_local_plugin_activation_smoke.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no `search-set.md` exists in this repository (`rg --files -g 'search-set.md'` returned no files). Standard verification and focused plugin activation smoke passed.
- Multi-review required: yes; Codex local plugin activation/install behavior affects the adapter distribution gate.
- Multi-review result: PASS with sequential `FALLBACK_NONINDEPENDENT` review because this single-session maintenance pass did not use parallel sub-agents.
- Reviewer scores and VETO handling:
  - Activation CLI path critic: 10/10 PASS; the smoke exercises `codex plugin marketplace add` in isolated `CODEX_HOME`, enables the expected plugin key, and validates the activated marketplace copy.
  - Generated plugin/sync critic: 10/10 PASS; the activation smoke is required by the sync source list, generated into the plugin bundle, and required as an executable artifact by the local plugin artifact smoke.
  - Runtime-boundary honesty critic: 9/10 PASS; docs and script comments explicitly avoid claiming model-visible Desktop session activation or runtime hook delivery.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update, focused verification, standard verification, search-set SKIPPED reason, and Completion Gate are recorded, with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each 9/10 reviewer rating, why not 10:
  - Runtime-boundary honesty critic: not 10 because Codex CLI currently exposes `plugin marketplace add/remove/upgrade` but no noninteractive `plugin list` or session-inspection command to prove model-visible skill discovery in a running Desktop session. This is accepted as product-surface residual risk rather than a repository follow-up for this item.
  - Maintenance compliance critic: not 10 because multi-review was sequential fallback in the parent context, not independent parallel critics. This is accepted as session-surface residual risk.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: runtime plugin hook manifest fields remain gated until separate tool-event coverage exists; the activation smoke proves local CLI marketplace registration and enabled config, not runtime hook delivery.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 26. Reconcile Codex distribution epic follow-up text

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- backlog/codex-adapter.md

The Codex distribution epic retained stale follow-up wording after local plugin
activation and project-fixture smoke coverage landed.

Potential improvement:

- Update item 4 so it no longer says activation smoke is pending.
- Keep only real remaining follow-up work, such as direct-copy fallback
  limitations and runtime hook/tool-event gating.

Decision:

- Updated item 4 to say the local plugin bundle now has artifact, fixture, and
  isolated activation smoke coverage.
- Removed the stale "real local plugin install smoke test" follow-up because
  item 19 added isolated CLI marketplace activation coverage.
- Kept the real remaining follow-ups around direct-copy fallback limitations
  and runtime hook/tool-event gating.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `backlog/codex-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting and no repository
  `search-set.md` exists.
- Multi-review required: no; backlog text reconciliation only, with no adapter
  behavior, hook semantics, release gate, or checker policy change.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no
  VETO path.
- For each score 9, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: remaining item 4 follow-ups are now current:
  direct-copy fallback limitation reporting and runtime hook/tool-event gating.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 27. Define direct-copy fallback limitation reporting

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/README.md
- adapters/codex/hook-schema.md
- adapters/codex/skills/autoresearch/SKILL.md
- adapters/codex/tests/test_direct_copy_fallback_reporting.py
- plugins/ai-agent-meta-harness/README.md
- plugins/ai-agent-meta-harness/hook-schema.md
- plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md
- backlog/codex-adapter.md

The direct skill copy path is intentionally degraded, but the runtime-facing
skill guidance should say exactly how to report missing hook/checker/template
assets instead of letting users infer full protection.

Potential improvement:

- Define a stable degraded-mode report marker and minimum missing-asset fields
  for skill-only direct-copy operation.
- Make the autoresearch setup guidance refuse to claim hooks, checker scripts,
  pre-commit, or CI protection were installed when only skill text is present.
- Keep README guidance aligned with the runtime-facing skill text.

Decision:

- Defined `DEGRADED_DIRECT_COPY_PROTECTION` as the stable report marker for
  skill-only direct-copy autoresearch setup when bundled protection assets are
  unavailable.
- Required the report to list missing checker, hook smoke, protected-path,
  Codex hook, pre-commit, CI, and AGENTS reminder assets, and to keep
  `Protection level: incomplete`.
- Updated autoresearch setup guidance so a skill-only copy cannot claim hooks,
  checker scripts, pre-commit, or CI protection were installed.
- Aligned README fallback guidance and generated plugin skill/README copies.
- Re-verified Codex hook/config output assumptions because the autoresearch
  skill guidance is hook-sensitive.
- Added lexical tests that pin the canonical and generated runtime-facing
  guidance.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/codex/README.md`
  - `adapters/codex/hook-schema.md`
  - `adapters/codex/skills/autoresearch/SKILL.md`
  - `adapters/codex/tests/test_direct_copy_fallback_reporting.py`
  - `plugins/ai-agent-meta-harness/README.md`
  - `plugins/ai-agent-meta-harness/hook-schema.md`
  - `plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md`
  - `backlog/codex-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_direct_copy_fallback_reporting.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes runtime-facing adapter guidance for
  degraded install and protection reporting.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Degraded reporting contract critic: 10/10 PASS; stable marker, missing
    asset list, incomplete protection level, and next-step guidance are pinned.
  - Protection honesty critic: 10/10 PASS; skill-only copy is explicitly barred
    from claiming hook, checker, pre-commit, or CI protection.
  - Generated plugin sync critic: 10/10 PASS; canonical and generated skill and
    README copies match, and plugin smoke/sync checks passed.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, verification,
    search-set SKIPPED reason, and Completion Gate are recorded, with
    nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: runtime hook manifest fields remain gated until
  Codex plugin tool-event delivery can be smoke-tested.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 28. Gate runtime hook manifest fields on tool-event coverage

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/README.md
- adapters/codex/plugin-scope.md
- adapters/codex/scripts/smoke-local-plugin.py
- adapters/codex/tests/test_local_plugin_smoke.py
- adapters/codex/tests/test_hook_templates.py
- plugins/ai-agent-meta-harness/README.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py
- backlog/codex-adapter.md

The plugin bundle ships hook templates but must not advertise active runtime
hook manifest fields until Codex plugin tool-event delivery is mechanically
smoke-tested.

Potential improvement:

- Update manifest rules so `hooks` requires both isolated activation coverage
  and tool-event delivery coverage.
- Make the local plugin smoke rejection message and tests enforce the
  activation-plus-tool-event gate.

Decision:

- Updated plugin scope manifest rules so runtime `hooks` fields require both
  isolated local activation and Codex plugin tool-event delivery smoke coverage.
- Updated README wording so bundled hook templates are not described as active
  plugin runtime hooks until both coverage conditions are met.
- Updated `smoke-local-plugin.py` to reject manifest `hooks` with an
  activation-plus-tool-event gate message.
- Added tests that pin the plugin-scope gate and the local plugin smoke
  rejection message.
- Fixed the runtime-hooks rejection test so the temporary copied plugin remains
  alive while the smoke command runs.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/codex/README.md`
  - `adapters/codex/plugin-scope.md`
  - `adapters/codex/scripts/smoke-local-plugin.py`
  - `adapters/codex/tests/test_local_plugin_smoke.py`
  - `adapters/codex/tests/test_hook_templates.py`
  - `plugins/ai-agent-meta-harness/README.md`
  - `plugins/ai-agent-meta-harness/plugin-scope.md`
  - `plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py`
  - `backlog/codex-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_local_plugin_smoke.py adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this tightens plugin manifest/release gating for
  runtime hook semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Manifest gate critic: 10/10 PASS; runtime `hooks` exposure is gated on
    both isolated activation and plugin tool-event delivery coverage.
  - Smoke enforcement critic: 10/10 PASS; the local plugin smoke rejects
    manifest `hooks` and the test pins the new gate reason.
  - Generated plugin sync critic: 10/10 PASS; plugin README, scope doc, and
    smoke script are synchronized with canonical adapter sources.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update,
    verification, search-set SKIPPED reason, and Completion Gate are recorded,
    with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: runtime hook manifest fields remain gated until a
  future Codex surface supports mechanical plugin tool-event delivery smoke
  coverage.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 29. P2 make marketplace metadata manifest discovery index-only in pre-commit

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- scripts/check-codex-marketplace-metadata.py
- tests/test_check_codex_marketplace_metadata.py
- backlog/codex-adapter.md

Source review: 2026-05-03 feedback triage.

`scripts/check-codex-marketplace-metadata.py` reads policy text from the Git
index in pre-commit mode, but `existing_publication_manifests(use_index=True)`
still starts from `path.exists()` before adding indexed paths. If
`.agents/plugins/marketplace.json` is tracked and staged for deletion while a
working-tree copy remains, pre-commit can still treat the manifest as present
even though the staged commit removes it.

Potential improvement:

- Make manifest discovery fully index-based when `use_index=True`.
- Preserve working-tree manifest validation for non-index/manual runs.
- Add a staged-deletion fixture test showing pre-commit/index mode ignores a
  working-tree copy that is absent from the staged commit.

Decision:

- Made `existing_publication_manifests(use_index=True)` return only manifests
  present in the Git index, without mixing in working-tree existence.
- Preserved working-tree manifest discovery and file/dir validation for
  non-index/manual runs.
- Avoided working-tree file-shape checks in index mode after readiness markers
  are present, so staged index validation does not depend on an out-of-date
  working-tree copy.
- Added a staged-deletion fixture proving index mode ignores a worktree
  `.agents/plugins/marketplace.json` that is absent from the staged commit,
  while manual working-tree validation still reports it.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - scripts/check-codex-marketplace-metadata.py
  - tests/test_check_codex_marketplace_metadata.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_check_codex_marketplace_metadata.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; this changes pre-commit/release checker staged-index semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Index semantics critic: 10/10 PASS; pre-commit mode now discovers publication manifests only from the staged index.
  - Manual validation critic: 10/10 PASS; non-index runs still validate working-tree manifest presence and file shape.
  - Regression fixture critic: 10/10 PASS; tests cover staged addition hidden by the worktree and staged deletion with a remaining worktree copy.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope correction, full verification, search-set SKIPPED reason, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 43. P3 refresh Codex plugin-scope v1 protection status

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 43, refresh Codex
  plugin-scope v1 protection status.
- Status block added: yes, item 43 marked `진행중`.
- Harness-affecting: yes; this changes Codex plugin bundle
  distribution/readiness wording generated into the plugin artifact.
- Multi-review required: yes; this changes Codex distribution/readiness
  contract wording for the plugin bundle.
- Minimum verification commands: `python3 scripts/sync-codex-plugin.py
  --check`; `python3 -m unittest adapters/codex/tests/test_hook_templates.py`;
  `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`;
  `python3 scripts/check-search-set-evidence.py`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: canonical Codex plugin-scope status row, generated plugin
  mirror, focused Codex docs tests, and this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`adapters/codex/README.md` now describes v1 protection as implemented for
copied target-project guardrails while runtime plugin hook delivery remains
deferred. However, `adapters/codex/plugin-scope.md` still says v1 protection has
install docs planned and status `Partial`. Because `plugin-scope.md` is
generated into `plugins/ai-agent-meta-harness/`, this stale status creates a
mixed readiness signal even though plugin sync passes.

Potential improvement:

- Update canonical and generated `plugin-scope.md` so the v1 protection row
  matches the README's implemented/deferred boundary.
- Preserve the runtime-delivery caveat: copied guardrails, install docs, and
  local smoke commands are implemented; runtime plugin hook delivery is still
  gated on product-supported smoke or reviewed manual evidence.
- Add or update focused Codex docs tests so README and plugin-scope status do
  not drift again.

Done when:

- `adapters/codex/README.md`, `adapters/codex/plugin-scope.md`, and the
  generated plugin mirrors describe the same v1 protection readiness state.
- `python3 scripts/sync-codex-plugin.py --check` and focused Codex docs tests
  pass.
- Multi-review checks the result because this changes distribution/readiness
  wording for the Codex plugin bundle.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 scripts/sync-codex-plugin.py --check`, `python3 -m
  unittest adapters/codex/tests/test_hook_templates.py`, `python3
  scripts/check-maintenance-review.py backlog/codex-adapter.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Updated canonical `adapters/codex/plugin-scope.md` and generated
  `plugins/ai-agent-meta-harness/plugin-scope.md` so the v1 protection row
  matches the README's implemented/deferred boundary.
- The row now says copied target-project guardrails, target-project install
  docs, and local smoke commands are implemented while runtime plugin hook
  delivery remains deferred until product-supported smoke or reviewed manual
  evidence exists.
- Extended focused Codex docs tests so README, generated README, plugin-scope,
  and generated plugin-scope all share the same v1 protection row and no longer
  contain `install docs planned` or `Partial` for that row.

Multi-review:

- Distribution/readiness wording critic: score 10/10, PASS. Blocking findings:
  none.
- Generated sync/test coverage critic: score 10/10, PASS. Blocking findings:
  none.
- Maintenance-process critic: score 8/10, VETO. Blocking findings: Completion
  Gate and required multi-review result were not yet recorded.
- Score handling: scores below 9 are VETO. The maintenance-process VETO is
  handled by recording this Completion Gate and rerunning the affected process
  critic. For process critic score 9 why not 10, the only remaining issue was
  final bookkeeping to record the rerun and acceptance; this was addressed in
  this item and does not create a backlog follow-up.
- Rerun status: maintenance-process critic re-review score 9/10, PASS.
  Blocking findings: none.
- Follow-up/residual risk: no implementation residual risk identified by the
  two implementation critics. Unrelated user-added backlog changes in
  `backlog/README.md`, `backlog/core.md`, and `backlog/claude-adapter.md`
  remain outside item 43 scope and will be left unstaged.
- Final acceptance: accepted yes after affected process critic re-review scored
  at least 9 and final bookkeeping was recorded.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - adapters/codex/plugin-scope.md
  - plugins/ai-agent-meta-harness/plugin-scope.md
  - adapters/codex/tests/test_hook_templates.py
  - backlog/codex-adapter.md
- Scope deviations: none for implementation files; unrelated user-added backlog
  changes in `backlog/README.md`, `backlog/core.md`, and
  `backlog/claude-adapter.md` are outside item 43 scope and are intentionally
  left unstaged.
- Verification results:
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `python3 scripts/check-search-set-evidence.py`
  - PASS: `python3 scripts/run-search-set.py`
  - PASS: `python3 scripts/verify-release.py --skip-clean-worktree`
  - PASS: `git diff --check`
- Search-set verification: BEFORE PASS `python3 scripts/run-search-set.py`;
  AFTER PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Codex distribution/readiness
  contract wording for the plugin bundle.
- Multi-review result: PASS for implementation critics; PASS for process critic
  after final record update.
- Reviewer scores and VETO handling:
  - Distribution/readiness wording critic: 10/10 PASS; no VETO.
  - Generated sync/test coverage critic: 10/10 PASS; no VETO.
  - Maintenance-process critic: 8/10 VETO because Completion Gate and
    multi-review result were not yet recorded; affected rerun rating 9/10 PASS.
- For each 9/10 reviewer rating, why not 10:
  - Maintenance-process critic rerun: not 10 because final bookkeeping still
    needed to record the process rerun and acceptance; fixed in this item.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: runtime plugin hook delivery remains deferred under
  the existing item 40 boundary until product-supported smoke or reviewed manual
  evidence exists. The dirty backlog files outside item 43 are unrelated
  user-added backlog candidates and remain unstaged.
- Accepted: yes.
### 42. P3 add optional Codex CLI surface probe for runtime-delivery docs

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/scripts/check-codex-cli-surface.py
- plugins/ai-agent-meta-harness/scripts/check-codex-cli-surface.py
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/README.md
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_codex_cli_surface.py
- adapters/codex/tests/test_hook_templates.py
- adapters/codex/scripts/smoke-local-plugin.py
- plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py
- scripts/sync-codex-plugin.py
- backlog/codex-adapter.md

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 42, add optional Codex CLI
  surface probe for runtime-delivery docs.
- Status block added: yes, item 42 marked `진행중`.
- Harness-affecting: yes; this adds an adapter-facing optional verification
  probe and generated plugin script for Codex CLI surface evidence.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary verification semantics.
- Minimum verification commands: `python3 scripts/sync-codex-plugin.py
  --check`; `python3 -m unittest adapters/codex/tests/test_codex_cli_surface.py`;
  `python3 -m unittest adapters/codex/tests/test_hook_templates.py`;
  `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`;
  `python3 scripts/check-search-set-evidence.py`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: optional Codex CLI surface probe script, generated plugin
  mirror, Codex adapter docs/scope docs, focused adapter tests, plugin sync
  required-script list, and this backlog record.

Source: score-9 residual risk from item 40 local/product-surface evidence
critic.

Item 40 documents the 2026-05-04 local Codex CLI surface evidence for
`codex plugin marketplace add|upgrade|remove` and experimental `codex
app-server` protocol tooling, but the focused test only pins that evidence as
documented strings. A future optional/local-only probe could mechanically
inspect the installed Codex CLI help surface without overclaiming Desktop
runtime skill surfacing or plugin hook event delivery.

Potential improvement:

- Add an optional smoke or docs-check mode that runs against a locally
  installed Codex CLI when available and verifies the observed plugin
  marketplace and app-server command surface.
- Keep the probe separate from CI-required release checks unless the Codex CLI
  is guaranteed in that environment.
- Make the probe explicitly non-substitutive for runtime model-visible skill or
  plugin hook delivery evidence.

Done when:

- The optional probe or documented manual check can confirm the local CLI help
  surface behind the item 40 runtime-delivery docs.
- Repository docs/tests continue to state that CLI help evidence does not prove
  Desktop runtime plugin delivery.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 scripts/sync-codex-plugin.py --check`, `python3 -m
  unittest adapters/codex/tests/test_hook_templates.py`, `python3
  scripts/check-maintenance-review.py backlog/codex-adapter.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py` after staging the selected
  item files so index-aware pre-commit/plugin sync checks could see the new
  required script. An earlier unstaged run failed SS-003 because the new script
  was not yet present in the Git index.

Decision implemented:

- Added `adapters/codex/scripts/check-codex-cli-surface.py`, an optional local
  Codex CLI help-surface probe that checks `codex plugin marketplace` and
  `codex app-server` markers when the CLI is installed.
- The probe skips cleanly when `codex` is absent by default and fails with
  `--require-installed` when a local environment must provide the CLI.
- Documented the probe in the Codex README and plugin-scope generated surface
  as CLI help evidence only, not Desktop runtime skill surfacing or plugin hook
  delivery evidence.
- Synced the generated plugin mirror and required the new script in
  `scripts/sync-codex-plugin.py`.
- Added focused tests for pass, marker failure, missing-CLI skip,
  require-installed failure, subprocess help failures, and `main()` stream/exit
  behavior.
- Updated the local plugin artifact smoke expected assets so the new generated
  probe remains part of bundle asset verification.

Multi-review:

- Runtime evidence-boundary critic: score 9/10, PASS. Blocking findings: none.
  Why not 10: the new probe was not included in the artifact smoke expected
  asset list, leaving one local evidence check slightly stale.
- Generated sync/test critic: score 9/10, PASS. Blocking findings: none. Why
  not 10: tests did not cover `main()` stream/exit behavior, nonzero help
  subprocess failures, and `--require-installed` used a `SKIPPED:` prefix while
  returning failure.
- Maintenance-process critic: score 8/10, VETO. Blocking finding: the item was
  not completion-ready before this record because Completion Gate and
  multi-review results were not yet recorded.
- Score handling: scores below 9 are VETO. The process VETO is handled by
  completing this record and rerunning the affected process critic. Both score
  9 reasons were actionable and fixed in this item before acceptance. For
  process critic score 9 why not 10, the only remaining issue was final
  bookkeeping to record the rerun and acceptance; this was addressed in this
  item and does not create a backlog follow-up.
- Rerun status: runtime evidence-boundary critic re-review score 10/10, PASS.
  Blocking findings: none. Generated sync/test critic re-review score 10/10,
  PASS. Blocking findings: none. Maintenance-process critic re-review score
  9/10, PASS. Blocking findings: none.
- Follow-up/residual risk: no new backlog item added because both score-9
  actionable issues were fixed in this item. The remaining runtime-delivery
  limitation is the existing item 40 boundary: CLI help evidence does not prove
  Desktop model-visible skill surfacing or plugin hook event delivery.
- Final acceptance: accepted yes after affected process critic re-review scored
  at least 9 and final bookkeeping was recorded.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - adapters/codex/scripts/check-codex-cli-surface.py
  - plugins/ai-agent-meta-harness/scripts/check-codex-cli-surface.py
  - adapters/codex/README.md
  - plugins/ai-agent-meta-harness/README.md
  - adapters/codex/plugin-scope.md
  - plugins/ai-agent-meta-harness/plugin-scope.md
  - adapters/codex/tests/test_codex_cli_surface.py
  - adapters/codex/tests/test_hook_templates.py
  - adapters/codex/scripts/smoke-local-plugin.py
  - plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py
  - scripts/sync-codex-plugin.py
  - backlog/codex-adapter.md
- Scope deviations: `adapters/codex/scripts/smoke-local-plugin.py` and the
  generated mirror were added to Scope before editing so the artifact smoke
  could cover the new probe asset.
- Verification results:
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 -m unittest adapters/codex/tests/test_codex_cli_surface.py`
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 -m unittest adapters/codex/tests/test_codex_cli_surface.py adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-cli-surface.py --require-installed`
  - PASS: `python3 plugins/ai-agent-meta-harness/scripts/check-codex-cli-surface.py --require-installed`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `python3 scripts/check-search-set-evidence.py`
  - PASS: `python3 scripts/run-search-set.py`
  - PASS: `python3 scripts/verify-release.py --skip-clean-worktree`
  - PASS: `git diff --cached --check`
- Search-set verification: BEFORE PASS `python3 scripts/run-search-set.py`;
  AFTER PASS `python3 scripts/run-search-set.py` after staging selected item
  files for index-aware checks. An unstaged AFTER attempt failed SS-003 because
  the new required script was not yet in the Git index; the staged rerun passed.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary verification semantics.
- Multi-review result: PASS for runtime evidence-boundary and generated
  sync/test critics after score-9 fixes; PASS for process critic after final
  record update.
- Reviewer scores and VETO handling:
  - Runtime evidence-boundary critic: 9/10 PASS initially; artifact smoke asset
    coverage gap fixed; rerun rating 10/10 PASS.
  - Generated sync/test critic: 9/10 PASS initially; CLI probe failure/main
    coverage gap fixed; rerun rating 10/10 PASS.
  - Maintenance-process critic: 8/10 VETO initially because Completion Gate and
    multi-review record were not yet present; affected rerun rating 9/10 PASS.
- For each 9/10 reviewer rating, why not 10:
  - Runtime evidence-boundary critic: not 10 because the artifact smoke did not
    include the new probe in expected assets; fixed in this item.
  - Generated sync/test critic: not 10 because `main()` stream/exit behavior,
    nonzero help subprocess failures, and require-installed failure wording
    needed coverage; fixed in this item.
  - Maintenance-process critic rerun: not 10 because final bookkeeping still
    needed to record the process rerun and acceptance; fixed in this item.
- Backlog items added from score-9 residual risk: none; both actionable
  implementation score-9 reasons were fixed in this item before acceptance, and
  the process score-9 reason was final bookkeeping fixed in this item.
- Residual risk/follow-up: CLI help-surface evidence remains non-substitutive
  for Desktop runtime plugin delivery evidence; runtime hook manifest fields
  remain disabled under the item 40 boundary until a product-supported smoke or
  explicitly reviewed manual gate exists.
- Accepted: yes.
### 35. P3 refresh active backlog summaries after Codex items 32-34

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- backlog/codex-adapter.md
- backlog/core.md

Source discussion: 2026-05-03 maintainer request to continue after completing
Codex adapter follow-ups 32-34.

The active backlog had no remaining `Status: 대기` item, but the compact core
Current Status summary still only named Codex items 27-29 as completed recent
adapter follow-ups. That can make freshly completed items 32-34 look invisible
to future handoff scans.

Decision:

- Updated `backlog/core.md` Current Status so recent completed Codex adapter
  follow-ups cover items 27-34.
- Left the Codex distribution epic summary unchanged because it already says no
  active implementation follow-up remains in that epic.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - backlog/codex-adapter.md
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md backlog/core.md`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting status summary cleanup.
- Multi-review required: no; this is backlog/status summary cleanup only, with no adapter behavior, hook semantics, release gate, checker policy, or durable contract change.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no VETO path.
- For each score 9, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes
### 36. P2 pin bounded timeouts in Codex hook templates

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/templates/hooks/codex-hooks.json.template
- adapters/codex/hook-schema.md
- plugins/ai-agent-meta-harness/templates/hooks/codex-hooks.json.template
- plugins/ai-agent-meta-harness/hook-schema.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The Codex autoresearch hook templates provide `PreToolUse` and
`PermissionRequest` guardrails for protected evaluator files, but the JSON hook
template does not set explicit `timeout` values. Current Codex hook behavior has
a long default timeout, which is acceptable for rare manual commands but too
generous for frequent protected-file checks if git resolution, Python startup,
or the checker stalls. The protection model should fail fast enough to preserve
interactive agent flow while still allowing normal repository paths to resolve.

Potential improvement:

- Add explicit bounded `timeout` values to
  `adapters/codex/templates/hooks/codex-hooks.json.template`.
- Mirror the change into the generated plugin bundle through
  `scripts/sync-codex-plugin.py --write`.
- Update hook template tests to assert the timeout is present and intentionally
  sized for the protected-file checker.
- Keep timeout guidance adapter-owned; do not move Codex hook timing policy into
  shared core methodology.

Done when:

- The Codex hook template no longer relies on the runtime default timeout for
  protected-file checks.
- Canonical and generated templates are synchronized.
- Focused tests fail if future template edits drop the timeout.

Decision implemented:

- Added explicit `timeout: 5` values to the canonical Codex `PreToolUse` and
  `PermissionRequest` command hooks in
  `adapters/codex/templates/hooks/codex-hooks.json.template`.
- Synced the generated plugin bundle with `python3 scripts/sync-codex-plugin.py --write`,
  updating `plugins/ai-agent-meta-harness/templates/hooks/codex-hooks.json.template`.
- Updated the canonical and generated hook schema references with the
  2026-05-04 timeout re-verification note and the timeout contract:
  `timeout` is in seconds, omitted timeout defaults to 600 seconds, and this
  adapter pins protected-file checks to 5 seconds.
- Extended `adapters/codex/tests/test_hook_templates.py` so focused tests
  require both hook commands to carry a short integer timeout in the 3-10 second
  range and assert the current value is 5 seconds.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Hook behavior critic: PASS, score 10/10. Blocking findings: none. Protected
  file hook checks no longer rely on the runtime default timeout and now fail
  fast enough for interactive `PreToolUse` and `PermissionRequest` flows.
- Adapter-boundary critic: PASS, score 10/10. Blocking findings: none. Timeout
  policy remains Codex-adapter-owned and does not move runtime timing guidance
  into shared core methodology.
- Sync/test critic: PASS, score 10/10. Blocking findings: none. Canonical and
  generated hook templates are synchronized, hook smoke still passes, and
  focused tests fail if future edits drop or unbound the timeout.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/codex/templates/hooks/codex-hooks.json.template
  - adapters/codex/hook-schema.md
  - plugins/ai-agent-meta-harness/templates/hooks/codex-hooks.json.template
  - plugins/ai-agent-meta-harness/hook-schema.md
  - adapters/codex/tests/test_hook_templates.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: official Codex hooks documentation check; `timeout` is documented as
    seconds and omitted timeout defaults to 600 seconds.
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
- Multi-review required: yes; this changes Codex hook semantics for protected
  file checks.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 hook behavior critic, 10/10
  adapter-boundary critic, 10/10 sync/test critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.
### 40. P2 add Codex Desktop/runtime plugin delivery smoke when surface exists

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/README.md
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 40, add Codex
  Desktop/runtime plugin delivery smoke when surface exists.
- Status block added: yes, item 40 marked `진행중`.
- Harness-affecting: yes; this changes Codex plugin distribution/runtime
  evidence boundary documentation and hook enablement gate.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary semantics.
- Minimum verification commands: `python3 scripts/sync-codex-plugin.py
  --check`; `python3 -m unittest adapters/codex/tests/test_hook_templates.py`;
  `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`;
  `python3 scripts/check-search-set-evidence.py`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: Codex README/plugin-scope canonical docs, generated plugin
  mirrors, focused Codex docs tests, and this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The Codex local plugin activation smoke now proves isolated CLI marketplace
registration and enabled-plugin config shape. The docs correctly avoid
overclaiming that this proves a running Codex Desktop session has surfaced the
skills to the model or delivered plugin runtime hook events. The remaining
valuable follow-up is to add runtime-level smoke coverage once Codex exposes a
stable, automatable surface for it.

Potential improvement:

- Identify an official or product-supported way to verify that a running Codex
  Desktop or equivalent runtime has loaded the generated plugin and can surface
  the expected skills to the model.
- Add a smoke test or documented manual verification flow that proves plugin
  tool-event delivery before enabling runtime hook manifest fields.
- Keep the existing CLI activation smoke and artifact smoke as prerequisites,
  not replacements, for runtime delivery evidence.
- If no stable noninteractive runtime surface exists, leave runtime hook
  manifest fields gated and record the product-surface limitation explicitly.

Done when:

- Codex adapter docs distinguish three evidence levels: generated artifact
  integrity, isolated CLI activation/config, and runtime model-visible skill or
  hook delivery.
- A new smoke/manual gate covers the runtime delivery level, or the backlog item
  is deliberately deferred with concrete product-surface evidence.
- Runtime hook manifest fields remain disabled until tool-event delivery is
  mechanically or explicitly verified.
- Multi-review checks the result because this changes Codex distribution and
  runtime evidence boundaries.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the
  first edit happened after focused baseline checks and local Codex surface
  inspection only. Focused baseline gates passed: `python3
  scripts/sync-codex-plugin.py --check`, `python3 -m unittest
  adapters/codex/tests/test_hook_templates.py`, `python3
  scripts/check-maintenance-review.py backlog/codex-adapter.md`, and `python3
  scripts/check-search-set-evidence.py` before the evidence record was needed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Documented three Codex runtime-delivery evidence levels in the canonical
  README and generated plugin README: generated artifact integrity, isolated
  CLI activation/config, and runtime model-visible skill surfacing or plugin
  hook delivery.
- Recorded the 2026-05-04 local Codex surface evidence: `codex plugin
  marketplace add|upgrade|remove` exists and `codex app-server` protocol
  tooling exists, but no stable noninteractive command proves Desktop
  model-visible skill surfacing or plugin hook event delivery.
- Kept runtime hook manifest fields disabled until a product-supported smoke or
  explicitly reviewed manual gate covers the runtime-delivery level.
- Updated the v1 protection scope row and focused tests so they no longer imply
  item 40 itself is the runtime hook delivery enabling gate.

Multi-review:

- Runtime evidence-boundary critic: score 8/10, VETO. Blocking finding:
  the README v1 protection row still said runtime plugin hook delivery remained
  gated on item 40, which conflicted with item 40's deferral outcome.
- Local/product-surface evidence critic: score 9/10, PASS. Blocking findings:
  none.
- Maintenance-process critic: score 9/10, PASS. Blocking findings: none.
- Score handling: scores below 9 are VETO. The 8/10 VETO was fixed before
  acceptance. For score 9 why not 10, the local/product-surface critic noted
  that tests pin documented evidence as strings rather than mechanically
  inspecting `codex plugin marketplace --help` or `codex app-server --help`;
  this actionable follow-up was added to backlog item 42. For score 9 why not
  10, the maintenance-process critic noted the BEFORE full Active search-set
  sequencing skip; that residual risk is accepted as recorded process debt, not
  a repository defect.
- Rerun status: affected runtime evidence-boundary critic re-review score
  10/10, PASS. Blocking findings: none.
- Follow-up/residual risk: item 42 was added for the actionable CLI surface
  probe. Runtime model-visible skill surfacing and plugin hook event delivery
  remain unproven until Codex exposes a product-supported smoke or this
  repository adopts an explicitly reviewed manual gate.
- Final acceptance: accepted yes after VETO fix, affected critic rerun, and all
  reviewer ratings at or above 9.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - adapters/codex/README.md
  - plugins/ai-agent-meta-harness/README.md
  - adapters/codex/plugin-scope.md
  - plugins/ai-agent-meta-harness/plugin-scope.md
  - adapters/codex/tests/test_hook_templates.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `python3 scripts/check-search-set-evidence.py`
  - PASS: `python3 scripts/run-search-set.py`
  - PASS: `python3 scripts/verify-release.py --skip-clean-worktree`
  - PASS: `git diff --check`
- Search-set verification: BEFORE SKIPPED with recorded sequencing reason;
  AFTER PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary semantics.
- Multi-review result: PASS after VETO fix and affected critic rerun.
- Reviewer scores and VETO handling:
  - Runtime evidence-boundary critic: 8/10 VETO initially; fixed stale runtime
    delivery gate wording; rerun rating 10/10 PASS.
  - Local/product-surface evidence critic: 9/10 PASS; no VETO.
  - Maintenance-process critic: 9/10 PASS; no VETO.
- For each 9/10 reviewer rating, why not 10:
  - Local/product-surface evidence critic: not 10 because the new focused test
    pins the documented evidence boundary as strings but does not mechanically
    inspect `codex plugin marketplace --help` or `codex app-server --help`.
  - Maintenance-process critic: not 10 because the full Active search-set
    BEFORE run was skipped after sequencing had already moved past the first
    edit; the skip was honestly recorded and the AFTER search-set passed.
- Backlog items added from score-9 residual risk:
  - Added item 42 for an optional local Codex CLI surface probe covering
    `plugin marketplace` and `app-server` help evidence without claiming
    Desktop runtime delivery.
- Residual risk/follow-up: runtime model-visible skill surfacing and plugin
  hook event delivery remain unproven until Codex exposes a product-supported
  smoke or this repository adopts an explicitly reviewed manual gate. The
  BEFORE search-set sequencing skip is accepted as a recorded process residual,
  not a repository defect.
- Accepted: yes.
### 41. P3 refresh Codex v1 protection scope status

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/README.md
- adapters/codex/tests/test_hook_templates.py
- scripts/check-search-set-evidence.py
- tests/test_search_set_evidence.py
- backlog/codex-adapter.md

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 41, refresh Codex v1
  protection scope status.
- Status block added: yes, item 41 marked `진행중`.
- Harness-affecting: yes; this changes Codex adapter distribution and
  runtime-evidence boundary documentation generated into the plugin bundle.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary wording.
- Minimum verification commands: `python3 scripts/sync-codex-plugin.py
  --check`; `python3 -m unittest adapters/codex/tests/test_hook_templates.py`;
  `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`;
  `python3 scripts/check-search-set-evidence.py`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: `adapters/codex/README.md`, generated
  `plugins/ai-agent-meta-harness/README.md`, focused Codex docs test,
  search-set evidence checker/test support for completed dirty records, and
  this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`adapters/codex/README.md` still describes the v1 protection stage as
`install docs planned` and `Partial`, but the same README now includes
target-project protection install guidance, smoke commands, and asset mapping.
Because this README is generated into the plugin bundle, the stale source status
propagates to the generated artifact even though `sync-codex-plugin.py --check`
passes.

Potential improvement:

- Update the bundle scope table so v1 protection accurately reflects the
  implemented install documentation and any remaining limitations.
- Preserve the distinction between copied target-project guardrails and active
  plugin runtime hooks; do not overclaim Codex Desktop tool-event delivery.
- Synchronize the generated plugin README and add or update focused docs checks
  if needed.

Done when:

- Codex README and generated plugin README no longer say v1 protection install
  docs are merely planned after the install section exists.
- Remaining limitations are stated precisely, such as runtime delivery smoke
  deferred until a product-supported smoke or reviewed manual gate exists,
  instead of using a stale generic Partial status.
- Plugin sync and local plugin smoke checks pass.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py --list` confirmed the Active
  case inventory before edits; focused baseline gates passed: `python3
  scripts/sync-codex-plugin.py --check`, `python3 -m unittest
  adapters/codex/tests/test_hook_templates.py`, `python3
  scripts/check-maintenance-review.py backlog/codex-adapter.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Updated the Codex adapter README bundle scope row so v1 protection no longer
  says install docs are planned or uses a stale generic `Partial` status.
- The v1 protection row now says target-project guardrails, install docs, and
  local smoke commands are implemented while runtime plugin hook delivery
  remains deferred until a product-supported smoke or reviewed manual gate
  exists.
- Synchronized the generated plugin README and added a focused test that
  requires exactly one current v1 protection row in both README copies.

Multi-review:

- Runtime-boundary wording critic: score 10/10, PASS. Blocking findings: none.
- Generated sync/test critic: score 8/10, VETO. Blocking findings: exact
  duplicate v1 rows were not detected because the first test removed all
  matching expected rows before checking for leftovers; not accepted.
- Process-compliance critic: score 8/10, VETO. Blocking findings: Start Gate
  fields were reported in the session but missing from the backlog record; not
  accepted.
- Score handling: scores below 9 were treated as VETO. The generated sync/test
  VETO was fixed by asserting exactly one `| v1 protection |` marker and exactly
  one expected row. The process VETO was fixed by recording the full Start Gate
  in this backlog item.
- Affected generated sync/test critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Affected process-compliance critic rerun: score 9/10, PASS. Blocking
  findings: none. Why not 10: final Completion Gate still needed to record the
  rerun result and completed reviewer-score handling before acceptance.
- Expanded-scope process critic rerun: score 8/10, VETO. Blocking findings:
  Completion Gate omitted `scripts/check-search-set-evidence.py` and
  `tests/test_search_set_evidence.py`, and did not close out the earlier failed
  release verification. Not accepted.
- Expanded-scope test/checker critic rerun: score 8/10, VETO. Blocking
  findings: completed fallback could accept stale completed evidence from an
  unrelated old section in the changed backlog file. Not accepted.
- Expanded-scope score handling: scores below 9 were treated as VETO. The
  Completion Gate omission was fixed by adding expanded files and final release
  PASS evidence. The stale completed-evidence hole was fixed by requiring
  completed evidence sections to mention an affected harness path, with a
  focused regression test. A follow-up review noted the test did not directly
  pin completed evidence against review-pending records; this actionable gap was
  fixed with an additional regression test.
- Expanded-scope test/checker critic rerun: score 9/10, PASS. Blocking
  findings: none. Why not 10: completed evidence precedence against
  review-pending records was verified synthetically but not yet pinned by a
  committed test.
- Second expanded-scope test/checker critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Final process-compliance critic rerun: score 9/10, PASS. Blocking findings:
  none. Why not 10: final record still needed to add this latest process-rerun
  result after the report.
- Rerun status: all affected critics reran; final scores are 10/10, 10/10,
  10/10, and 9/10 PASS.
- Follow-up/residual risk: procedural final-closure timing addressed by this
  Completion Gate.
- Final acceptance: accepted after VETO fixes and affected critic reruns.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/README.md`,
  `plugins/ai-agent-meta-harness/README.md`,
  `adapters/codex/tests/test_hook_templates.py`,
  `scripts/check-search-set-evidence.py`, `tests/test_search_set_evidence.py`,
  `backlog/codex-adapter.md`.
- Scope deviations: scope expanded to include
  `scripts/check-search-set-evidence.py` and `tests/test_search_set_evidence.py`
  before editing them, after the completed-item policy exposed that the
  search-set evidence checker did not accept completed dirty handoff records.
- Verification results: PASS `python3 scripts/sync-codex-plugin.py --check`;
  PASS `python3 -m unittest adapters/codex/tests/test_hook_templates.py`; PASS
  `python3 -m unittest tests/test_search_set_evidence.py`; PASS
  `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`; PASS
  `python3 scripts/check-search-set-evidence.py`; PASS `python3
  scripts/run-search-set.py`; PASS `git diff --check`. Initial `python3
  scripts/verify-release.py --skip-clean-worktree` failed only because
  search-set evidence had not yet been recorded; after the record was added,
  final `python3 scripts/verify-release.py --skip-clean-worktree` passed.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py --list` confirmed Active
    case inventory before edits; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Codex distribution/runtime evidence
  boundary wording.
- Multi-review result: PASS after three-critic multi-review, VETO fixes, and
  affected critic reruns.
- Reviewer scores and VETO handling: runtime-boundary wording critic 10/10
  PASS; generated sync/test critic 8/10 VETO fixed and rerun to 10/10 PASS;
  process-compliance critic 8/10 VETO fixed and rerun to 9/10 PASS. Expanded
  scope process critic 8/10 VETO and expanded-scope test/checker critic 8/10
  VETO were fixed. Expanded-scope test/checker critic reran to 9/10 PASS, then
  to 10/10 PASS after adding the review-pending precedence regression test;
  final process critic reran to 9/10 PASS after the record update.
- For each score-9 result, why not 10:
  - Process-compliance critic rerun: not 10 because final Completion Gate still
    needed to record rerun result and completed score handling at rerun time;
    addressed by this Completion Gate.
  - Expanded-scope test/checker critic rerun: not 10 because completed evidence
    precedence against review-pending records was not directly pinned; fixed in
    this item with a focused regression test and rerun to 10/10 PASS.
  - Final process-compliance critic rerun: not 10 because final record still
    needed to add the latest process-rerun result at report time; addressed by
    this Completion Gate.
- Backlog items added from score-9 residual risk: none; the only score-9 reason
  was procedural final-closure timing or an actionable test gap handled here.
- Residual risk/follow-up: none.
- Accepted: yes.
### 37. P3 refresh Codex hook schema freshness signaling

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/hook-schema.md
- adapters/codex/scripts/check-codex-hook-schema-drift.py
- adapters/codex/scripts/smoke-autoresearch-hooks.py
- adapters/codex/tests/test_hook_schema_drift.py
- plugins/ai-agent-meta-harness/hook-schema.md
- plugins/ai-agent-meta-harness/scripts/check-codex-hook-schema-drift.py
- plugins/ai-agent-meta-harness/scripts/smoke-autoresearch-hooks.py
- backlog/codex-adapter.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The hook schema reference records later re-verification notes, but the enforced
verified-date marker in the drift checker still points at an older date. This is
not a behavior failure because the hook schema drift check passes and the
reference documents the relevant Codex hook output shapes. Still, stale-looking
freshness metadata weakens reviewer confidence when hook-sensitive changes are
being evaluated.

Potential improvement:

- Decide whether the enforced verified-date marker should track the most recent
  official-doc re-check or only the last behavior-affecting schema update.
- Update `adapters/codex/hook-schema.md` and
  `adapters/codex/scripts/check-codex-hook-schema-drift.py` so the freshness
  convention is explicit.
- Sync generated plugin copies and update tests if the marker changes.
- Keep this as metadata/freshness work; do not imply hook semantics changed
  unless official docs or smoke evidence require a behavior update.

Done when:

- A reviewer can tell what the hook schema verified date means.
- Canonical hook schema docs, drift checker markers, and generated plugin copies
  agree.
- Hook schema drift tests cover the chosen freshness convention.

Decision implemented:

- Defined the hook-schema freshness convention in
  `adapters/codex/hook-schema.md`: `Verified date` tracks the most recent
  official hooks/config documentation re-check that the adapter depends on, and
  unchanged output/config contracts should be recorded with dated
  re-verification notes.
- Updated the enforced drift marker from `2026-04-30` to `2026-05-04`, matching
  the existing item 36 re-verification note for bounded command hook timeouts.
- Updated `adapters/codex/scripts/check-codex-hook-schema-drift.py` and
  `adapters/codex/scripts/smoke-autoresearch-hooks.py` metadata markers.
- Synced generated plugin copies with `python3 scripts/sync-codex-plugin.py --write`.
- Extended `adapters/codex/tests/test_hook_schema_drift.py` to require the
  freshness convention wording.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Freshness-convention critic: PASS, score 10/10. Blocking findings: none. The
  reference now states what `Verified date` means and how to record unchanged
  output/config contracts after re-checking official docs.
- Drift-marker critic: PASS, score 10/10. Blocking findings: none. Canonical
  hook schema docs, drift checker constants, smoke metadata, and generated
  plugin copies all agree on `2026-05-04`.
- Scope critic: PASS, score 10/10. Blocking findings: none. The change is
  metadata/freshness only and does not imply new hook output semantics or plugin
  runtime hook-event coverage.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/codex/hook-schema.md
  - adapters/codex/scripts/check-codex-hook-schema-drift.py
  - adapters/codex/scripts/smoke-autoresearch-hooks.py
  - adapters/codex/tests/test_hook_schema_drift.py
  - plugins/ai-agent-meta-harness/hook-schema.md
  - plugins/ai-agent-meta-harness/scripts/check-codex-hook-schema-drift.py
  - plugins/ai-agent-meta-harness/scripts/smoke-autoresearch-hooks.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_schema_drift.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - BEFORE PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 -m unittest tests/test_repository_search_set.py`
- Multi-review required: yes; this changes Codex hook schema drift/freshness
  contract.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 freshness-convention critic, 10/10
  drift-marker critic, 10/10 scope critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.
### 38. P2 add end-to-end Codex adoption smoke for generated search-set commands

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/scripts/smoke-init-codex-project-fixtures.py
- adapters/codex/tests/test_init_codex_project_fixtures.py
- adapters/codex/README.md
- plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py
- plugins/ai-agent-meta-harness/README.md
- backlog/codex-adapter.md

Source review: 2026-05-04 multi-review of current local `main` against the
Meta-Harness methodology.

The trace/evaluator critic found that the Codex adapter has strong deterministic
fixture coverage for representative `init-codex-harness` outputs, but the
adoption flow remains mostly instruction-and-template driven. Existing
`smoke-init-codex-project-fixtures.py` validates generated AGENTS policy,
trace-root selection, initial evolution trace shape, and executable-looking
Active search-set entries. It does not fully exercise the next adoption step:
run the seeded search-set verify commands in the generated target projects and
fail if the initialized harness produces commands that do not actually execute.

Potential improvement:

- Extend the Codex init fixture smoke, or add a focused sibling smoke, that
  creates representative target projects, applies the expected initialized
  harness fixture output, parses `.harness/traces/search-set.md`, and runs the
  Active `verify` commands.
- Cover at least the current TypeScript, Python research, and migrated
  `.claude/traces/` fixture shapes unless one is intentionally documented as
  non-executable.
- Preserve the existing boundary: this is deterministic repo-local adoption
  smoke, not proof that a live Codex Desktop session surfaced skills or executed
  a model-driven init.
- Generate the smoke into `plugins/ai-agent-meta-harness/` if it becomes part
  of the supported plugin artifact surface, and update plugin sync/smoke checks
  accordingly.

Done when:

- The Codex adapter has a repeatable command that initializes representative
  fixture projects and then executes each generated Active search-set `verify`
  command successfully.
- The smoke fails on masked verifier exit status, non-executable verify text, or
  generated search-set commands that do not run in the target fixture project.
- README or adapter docs clearly state what this smoke proves and what remains
  outside its evidence boundary.
- Multi-review checks the result because it changes adapter release confidence
  and future initialization evidence.

Implementation notes:

- Extended the canonical Codex init fixture smoke so it parses Active
  `search-set.md` `verify` commands and executes them in each generated fixture
  project.
- Made the TypeScript, Python, and migrated-Claude-history fixtures runnable
  without external project dependencies by adding minimal local fixture runners.
- Added regression tests for failing verify execution and missing Active verify
  entries, while keeping the existing masked-exit-status rejection.
- Synced the generated plugin copy and documented the stronger evidence boundary
  in the adapter and plugin READMEs.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.
- after: PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`.

Multi-review:

- Result: PASS; required because this changes Codex adapter release confidence
  and generated initialization evidence. Used `FALLBACK_NONINDEPENDENT`
  sequential review because this single-session maintenance pass was not
  authorized to spawn independent reviewers.
- Trace/evaluator critic: score 10/10; verdict PASS; Blocking findings: none.
  The smoke now exercises the actual generated Active verify commands in the
  fixture cwd and fails on non-running commands, missing Active entries, and
  masked exit-status patterns.
- Adapter/plugin artifact critic: score 10/10; verdict PASS; Blocking
  findings: none. The canonical adapter script and README were synced into the
  generated plugin bundle, and `sync-codex-plugin.py --check` confirms no drift.
- Evidence-boundary/release critic: score 10/10; verdict PASS; Blocking
  findings: none. The README wording states that this is deterministic
  repo-local adoption smoke, not proof of live Codex Desktop model/plugin
  surfacing.
- Score handling: no score below 9, so no VETO; no score 9, so no why-not-10
  residual risk or follow-up backlog item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/scripts/smoke-init-codex-project-fixtures.py`,
  `adapters/codex/tests/test_init_codex_project_fixtures.py`,
  `adapters/codex/README.md`,
  `plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py`,
  `plugins/ai-agent-meta-harness/README.md`, `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3
  adapters/codex/scripts/smoke-init-codex-project-fixtures.py`; PASS `python3
  plugins/ai-agent-meta-harness/scripts/smoke-init-codex-project-fixtures.py`;
  PASS `python3 -m unittest
  adapters/codex/tests/test_init_codex_project_fixtures.py`; PASS `python3
  scripts/sync-codex-plugin.py --check`; PASS `python3 -m unittest discover -s
  adapters/codex/tests`; PASS `python3 -m unittest discover -s tests`; PASS
  `python3 -m unittest discover -s adapters/claude/tests`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 -m unittest
  tests/test_pre_commit_hook.py`; PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`; PASS `python3 -m
  unittest tests/test_repository_search_set.py`; PASS `sh .githooks/pre-commit`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above.
- Multi-review required: yes; Codex adapter release confidence and generated
  initialization evidence boundary.
- Multi-review result: PASS; `FALLBACK_NONINDEPENDENT` sequential review.
- Reviewer scores and VETO handling: 10/10 trace/evaluator critic, 10/10
  adapter/plugin artifact critic, 10/10 evidence-boundary/release critic; no
  VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.
### 39. P3 list init fixture smoke in Codex plugin-scope generated contents

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md

Source review: 2026-05-04 adapter/plugin alignment critic in the current-main
methodology multi-review.

The generated Codex plugin bundle includes
`scripts/smoke-init-codex-project-fixtures.py`, and the sync/local-plugin smoke
paths require it as an executable generated asset. However, `plugin-scope.md`
does not list that script in the current generated contents or canonical path
table. The artifact and generator are aligned, but the supported-surface
document is stale.

Potential improvement:

- Add `scripts/smoke-init-codex-project-fixtures.py` to
  `adapters/codex/plugin-scope.md` Current Generated Contents.
- Add it to the canonical path table with its generated plugin path and evidence
  boundary.
- Sync `plugins/ai-agent-meta-harness/plugin-scope.md` and extend focused tests
  if needed so the documented plugin scope stays aligned with required generated
  assets.

Done when:

- Canonical and generated plugin-scope docs both list the init fixture smoke as
  part of the generated plugin surface.
- `python3 scripts/sync-codex-plugin.py --check` and the local plugin smoke pass.
- A reviewer can tell from `plugin-scope.md` that the fixture smoke is a
  deterministic artifact/adoption check, not live model dogfooding.

Implementation notes:

- Added `scripts/smoke-init-codex-project-fixtures.py` to the canonical
  `adapters/codex/plugin-scope.md` Current Generated Contents list.
- Added the init project fixture smoke to the v1 canonical path policy table
  with its generated plugin path and evidence boundary.
- Synced `plugins/ai-agent-meta-harness/plugin-scope.md`.
- Extended the focused plugin-scope test so canonical and generated scope docs
  must both list the init fixture smoke and its deterministic, non-live-model
  evidence boundary.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.
- after: PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`.

Multi-review:

- Result: PASS; required because this updates the documented Codex generated
  plugin support surface. Used `FALLBACK_NONINDEPENDENT` sequential review
  because this single-session maintenance pass was not authorized to spawn
  independent reviewers.
- Adapter support-surface critic: score 10/10; verdict PASS; Blocking
  findings: none. The current contents list and canonical path table now name
  the fixture smoke and its generated path.
- Generated-artifact drift critic: score 10/10; verdict PASS; Blocking
  findings: none. The generated `plugin-scope.md` matches the canonical source,
  and plugin sync plus local plugin smoke passed.
- Evidence-boundary critic: score 10/10; verdict PASS; Blocking findings:
  none. The scope table describes the smoke as deterministic artifact/adoption
  evidence and explicitly avoids live Codex model dogfooding claims.
- Score handling: no score below 9, so no VETO; no score 9, so no why-not-10
  residual risk or follow-up backlog item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/codex/plugin-scope.md`,
  `plugins/ai-agent-meta-harness/plugin-scope.md`,
  `adapters/codex/tests/test_hook_templates.py`, `backlog/codex-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  adapters/codex/tests/test_hook_templates.py`; PASS `python3
  scripts/sync-codex-plugin.py --check`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin.py`; PASS `python3
  plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 -m unittest discover -s
  tests`; PASS `python3 -m unittest discover -s adapters/claude/tests`; PASS
  `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3 -m
  unittest tests/test_pre_commit_hook.py`; PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`; PASS `python3 -m
  unittest tests/test_repository_search_set.py`; PASS `sh .githooks/pre-commit`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above.
- Multi-review required: yes; Codex generated plugin support-surface change.
- Multi-review result: PASS; `FALLBACK_NONINDEPENDENT` sequential review.
- Reviewer scores and VETO handling: 10/10 adapter support-surface critic,
  10/10 generated-artifact drift critic, 10/10 evidence-boundary critic; no
  VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.
### 32. P2 add activation smoke to release checklist

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- MAINTENANCE.md
- tests/test_pre_commit_hook.py
- backlog/codex-adapter.md

Source review: 2026-05-03 feedback triage.

`MAINTENANCE.md` Standard verification includes
`python3 adapters/codex/scripts/smoke-local-plugin-activation.py`, and root
README documents the smoke as part of the Codex plugin workflow. The Release
Checklist still names only the local plugin artifact smoke, so someone using
the checklist before treating `main` as stable could skip activation coverage.

Potential improvement:

- Add the Codex local plugin activation smoke to the Release Checklist.
- Keep the checklist wording clear that this proves isolated CLI marketplace
  registration and enabled-plugin config shape, not running Desktop skill
  surfacing or plugin tool-event delivery.
- Add focused test coverage so Standard verification and Release Checklist do
  not drift on activation smoke coverage.

Decision:

- Added Codex local plugin activation smoke to the `MAINTENANCE.md` Release
  Checklist.
- Kept the evidence boundary explicit: the activation smoke proves isolated CLI
  marketplace registration and enabled-plugin config shape, not running Codex
  Desktop skill surfacing or plugin tool-event delivery.
- Extended focused verification-policy tests so Standard verification and the
  Release Checklist both name the activation smoke and its evidence boundary.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - MAINTENANCE.md
  - tests/test_pre_commit_hook.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 -m unittest discover -s tests`
- Search-set verification:
  - BEFORE: PASS; relevant Active commands passed before implementation: `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `sh .githooks/pre-commit`, and `python3 -m unittest tests/test_pre_commit_hook.py`.
  - AFTER: PASS; the same relevant Active commands passed after implementation, plus `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py` was run for full Active coverage.
- Multi-review required: yes; this changes release checklist and verification gate guidance.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Release checklist parity critic: 10/10 PASS; the checklist now includes the activation smoke already present in Standard verification.
  - Runtime-boundary critic: 10/10 PASS; the checklist states what activation proves and does not overclaim Desktop skill surfacing or tool-event delivery.
  - Focused coverage critic: 10/10 PASS; tests pin Standard verification, Release Checklist, and root README activation smoke wording.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, search-set before/after verification, full verification, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 33. P2 include hard-layer hook templates in hook-sensitive drift policy

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/scripts/check-codex-hook-schema-drift.py
- adapters/codex/tests/test_hook_schema_drift.py
- adapters/codex/hook-schema.md
- plugins/ai-agent-meta-harness/scripts/check-codex-hook-schema-drift.py
- plugins/ai-agent-meta-harness/hook-schema.md
- backlog/codex-adapter.md

Source review: 2026-05-03 feedback triage.

`check-codex-hook-schema-drift.py` requires hook-schema re-verification for
changes to the Codex hook template and AGENTS reminder, but it omits
`adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` and
`adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml`.
Those templates carry hard-layer protected-file semantics, so changing them can
alter the protection contract without forcing a schema/protection review note.

Potential improvement:

- Add the pre-commit and GitHub Actions autoresearch protection templates to
  `HOOK_SENSITIVE_PATHS`.
- Extend hook-schema drift tests so staged changes to either hard-layer
  template require a staged `adapters/codex/hook-schema.md` update or
  re-verification.
- Clarify in the hook schema reference that hard-layer template changes require
  protection-contract review even when Codex hook JSON output shape is
  unchanged.

Decision:

- Added `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh`
  and `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml`
  to `HOOK_SENSITIVE_PATHS`.
- Extended hook-schema drift tests so both hard-layer protection templates
  trigger the staged policy requiring a staged `adapters/codex/hook-schema.md`
  update or re-verification.
- Clarified `adapters/codex/hook-schema.md` so hard-layer pre-commit/CI
  template changes require protection-contract review even when Codex hook JSON
  output shape is unchanged.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/codex/scripts/check-codex-hook-schema-drift.py
  - adapters/codex/tests/test_hook_schema_drift.py
  - adapters/codex/hook-schema.md
  - plugins/ai-agent-meta-harness/scripts/check-codex-hook-schema-drift.py
  - plugins/ai-agent-meta-harness/hook-schema.md
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_schema_drift.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 -m unittest discover -s tests`
- Search-set verification:
  - BEFORE: PASS; relevant Active commands passed before implementation: `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `sh .githooks/pre-commit`, and `python3 -m unittest tests/test_pre_commit_hook.py`.
  - AFTER: PASS; the same relevant Active commands passed after implementation, plus `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py` was run for full Active coverage.
- Multi-review required: yes; this changes hook/protected-file hard-layer protection drift policy.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Hard-layer coverage critic: 10/10 PASS; both pre-commit and GitHub Actions protection templates are now hook-sensitive.
  - Drift enforcement critic: 10/10 PASS; focused tests prove staged changes to hard-layer templates require schema re-verification.
  - Contract honesty critic: 10/10 PASS; hook schema guidance distinguishes JSON output shape checks from protection-contract review needs.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, search-set before/after verification, full verification, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 34. P2 list activation smoke in Codex plugin-scope generated contents

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md

Source review: 2026-05-03 feedback triage.

The generated plugin bundle and README know about
`scripts/smoke-local-plugin-activation.py`, but `adapters/codex/plugin-scope.md`
and the generated plugin-scope mirror omit it from `Current Generated Contents`
and the canonical path table. Because plugin-scope defines the generated
bundle's supported surface, this creates documentation/distribution drift.

Potential improvement:

- Add `scripts/smoke-local-plugin-activation.py` to Current Generated Contents.
- Add the activation smoke to the canonical path table with its generated
  plugin path and evidence boundary.
- Update the generated plugin-scope mirror and focused plugin-scope tests so
  the activation smoke remains part of the documented generated surface.

Decision:

- Added `scripts/smoke-local-plugin-activation.py` to Current Generated
  Contents in canonical and generated `plugin-scope.md`.
- Added the activation smoke to the v1 canonical path table with canonical
  source, generated plugin path, and evidence-boundary wording.
- Added focused plugin-scope coverage that checks both canonical and generated
  plugin-scope docs and asserts they remain identical.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/codex/plugin-scope.md
  - plugins/ai-agent-meta-harness/plugin-scope.md
  - adapters/codex/tests/test_hook_templates.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 -m unittest discover -s tests`
- Search-set verification:
  - BEFORE: PASS; relevant Active commands passed before implementation: `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `sh .githooks/pre-commit`, and `python3 -m unittest tests/test_pre_commit_hook.py`.
  - AFTER: PASS; the same relevant Active commands passed after implementation, plus `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py` was run for full Active coverage.
- Multi-review required: yes; this changes Codex plugin generated-surface and distribution documentation contract.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Generated-surface critic: 10/10 PASS; activation smoke now appears in Current Generated Contents and the canonical path table.
  - Mirror sync critic: 10/10 PASS; generated plugin-scope mirror matches canonical and sync check passes.
  - Runtime-boundary critic: 10/10 PASS; plugin-scope records activation evidence without overclaiming Desktop skill surfacing or plugin tool-event delivery.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, search-set before/after verification, full verification, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes
### 30. P3 reconcile active backlog summaries after completed Codex follow-ups

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- backlog/codex-adapter.md
- backlog/core.md

Source discussion: 2026-05-03 maintainer request to continue with the next
backlog item after completing the current Codex and core maintenance
follow-ups.

The active summaries still made completed work look available: the Codex
distribution epic listed direct-copy fallback reporting as remaining after item
27 completed it, and `backlog/core.md` still described item 31 as an unstarted
core cleanup after it was completed.

Decision:

- Updated the Codex distribution epic's `Remaining follow-up work` to state
  that no active implementation follow-up remains there.
- Preserved the runtime hook manifest gating note as an intentional product
  surface wait, not an available backlog implementation item.
- Updated core `Current Status` so it no longer lists item 31 as unstarted and
  explicitly treats recent Claude, Codex, and core follow-ups as completed.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - backlog/codex-adapter.md
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md backlog/core.md`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting and no repository `search-set.md` exists.
- Multi-review required: no; this is active backlog/status summary cleanup only, with no adapter behavior, hook semantics, release gate, checker policy, or durable contract change.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no VETO path.
- For each score 9, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
### 31. P2 align root Codex activation smoke documentation with implementation

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- README.md
- MAINTENANCE.md
- tests/test_pre_commit_hook.py
- backlog/codex-adapter.md

Source review: 2026-05-03 multi-review feedback.

Root `README.md` still says the exact Codex local-plugin activation command is
pending an activation smoke test, but
`adapters/codex/scripts/smoke-local-plugin-activation.py` exists and the
adapter README/backlog describe it as passing. This makes the root README,
standard verification guidance, release/pre-commit expectations, and adapter
artifact state look out of sync.

Potential improvement:

- Update root `README.md` to describe the activation smoke as implemented and
  distinguish it from runtime model-visible skill surfacing and plugin
  tool-event delivery.
- Decide whether `MAINTENANCE.md` Standard verification, release checklist, and
  `.githooks/pre-commit` should include the activation smoke or explicitly
  leave it as focused/release-only evidence.
- Add focused docs/check coverage so root README and adapter README do not
  regress to saying activation smoke is pending after the implementation
  exists.

Decision:

- Updated root `README.md` so Codex local plugin activation smoke is described
  as implemented, with the exact command listed in the local plugin workflow.
- Distinguished activation evidence from runtime model-visible skill surfacing
  and plugin tool-event delivery: the smoke proves local CLI marketplace
  registration and enabled-plugin config shape only.
- Added `python3 adapters/codex/scripts/smoke-local-plugin-activation.py` to
  `MAINTENANCE.md` Standard verification.
- Left `.githooks/pre-commit` unchanged and documented that the heavier local
  plugin activation smoke is Standard verification rather than pre-commit.
- Added focused README/MAINTENANCE assertions so root docs do not regress to
  saying activation smoke is pending.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - README.md
  - MAINTENANCE.md
  - tests/test_pre_commit_hook.py
  - backlog/codex-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/codex-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; this changes Codex plugin activation/release verification guidance and documentation contract.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Activation evidence critic: 10/10 PASS; root README now states the activation smoke is implemented and describes exactly what it proves.
  - Runtime-boundary critic: 10/10 PASS; README preserves the distinction between CLI activation/config evidence and model-visible skill surfacing or plugin tool-event delivery.
  - Verification placement critic: 10/10 PASS; activation smoke is included in Standard verification while pre-commit remains the lighter artifact/drift gate.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, full verification, search-set SKIPPED reason, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 45. P3 keep embedded Codex hook examples bounded

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/skills/autoresearch/SKILL.md
- plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md
- adapters/codex/hook-schema.md
- plugins/ai-agent-meta-harness/hook-schema.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md
- backlog/archive/codex-adapter.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

Item 36 pinned bounded timeouts in the canonical Codex hook template, and the
template tests cover that surface. The Codex `autoresearch` skill also embeds a
minimal `.codex/hooks.json` example for users who follow the skill text directly
instead of copying the template. That embedded example should carry the same
bounded-timeout expectation so project-local hook setup does not accidentally
depend on runtime defaults.

Potential improvement:

- Add explicit short `timeout` values to the embedded `.codex/hooks.json`
  example in `adapters/codex/skills/autoresearch/SKILL.md`.
- Update the generated plugin skill mirror through `scripts/sync-codex-plugin.py
  --write`.
- Add or extend focused tests so canonical templates and embedded examples both
  preserve bounded checker timeouts.

Done when:

- Users following either the template path or the embedded skill example install
  bounded Codex hook commands.
- `python3 scripts/sync-codex-plugin.py --check` and focused Codex hook tests
  pass.

Decision implemented:

- The embedded `.codex/hooks.json` example in
  `adapters/codex/skills/autoresearch/SKILL.md` now pins `timeout: 5` on both
  the `PreToolUse` and `PermissionRequest` checker hooks.
- The generated plugin skill mirror was refreshed with
  `python3 scripts/sync-codex-plugin.py --write`.
- `adapters/codex/tests/test_hook_templates.py` now checks that the embedded
  skill example preserves short checker timeouts, matching the canonical hook
  template expectation.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py` from the previous stable
  handoff before item 45 implementation.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Completion Gate:

- Backlog status: `완료`; archived to `backlog/archive/codex-adapter.md`
  after process/scope VETO recovery re-review passed.
- Changed files: `adapters/codex/skills/autoresearch/SKILL.md`,
  `plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md`,
  `adapters/codex/hook-schema.md`,
  `plugins/ai-agent-meta-harness/hook-schema.md`,
  `adapters/codex/tests/test_hook_templates.py`,
  `backlog/codex-adapter.md`, `backlog/archive/codex-adapter.md`.
- Scope deviations: none for item 45. Dirty out-of-scope `backlog/README.md`
  remains unstaged. User-added `backlog/codex-adapter.md` items 44 and 46 are
  unrelated backlog additions in the same file; final staging must include only
  the selected item 45 record/hunks plus implementation files.
- Verification results: BEFORE PASS `python3 scripts/run-search-set.py` from
  the previous stable handoff before item 45 implementation; AFTER PASS
  `python3 -m unittest adapters/codex/tests/test_hook_templates.py`; AFTER PASS
  `python3 scripts/sync-codex-plugin.py --check`; AFTER PASS
  `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`; AFTER PASS
  `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker
  adapters/codex/scripts/check-autoresearch-protected.py --protected-file
  adapters/codex/templates/autoresearch-protected.txt`; AFTER PASS
  `python3 scripts/run-search-set.py`; AFTER PASS
  `python3 scripts/check-maintenance-review.py`; AFTER PASS
  `python3 scripts/check-search-set-evidence.py`; AFTER PASS
  `python3 scripts/verify-release.py --skip-clean-worktree --base-ref
  origin/main`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py` from the previous stable
    handoff before item 45 implementation.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Codex adapter hook guidance and the
  generated plugin skill surface.
- Multi-review result: PASS after process/scope VETO recovery re-review.
- Reviewer scores and VETO handling: hook/example semantics critic 9 PASS;
  generated artifact/test coverage critic 9 PASS; process/scope critic 8 VETO
  because Completion Gate and multi-review outcome were not yet recorded, dirty
  out-of-scope `backlog/README.md` needed explicit handling, and same-file
  user-added items 44/46 needed final staging discipline. This gate addresses
  those blockers; affected process/scope re-review scored 9 PASS.
- For each score 9, why not 10: hook/example semantics critic noted the
  embedded-example test is string-based rather than parsing the Markdown JSON
  block, accepted because it directly checks the narrow user-facing snippet;
  generated artifact/test coverage critic noted the focused test checks the
  adapter source and relies on plugin sync for the generated mirror, accepted
  because `sync-codex-plugin.py --check` covers generated copy drift;
  process/scope critic noted same-file staging discipline still depends on
  careful partial staging or equivalent index construction, accepted because
  this final handoff stages only item 45 files/hunks.
- Backlog items added from score-9 residual risk: none; score-9 residuals
  are accepted as narrow doc-snippet, generated-mirror test design, or
  final-staging discipline tradeoffs.
- Residual risk/follow-up: no follow-up. The embedded example now matches
  canonical bounded timeout guidance, and final staging excludes unrelated
  same-file backlog additions.
- Accepted: yes.

Multi-review:

- Hook/example semantics critic: score 9, PASS. Blocking findings: none. Why
  not 10: the embedded-example test is string-based rather than parsing the JSON
  block out of Markdown. Follow-up/residual risk: accepted because this is a
  narrow documentation/example guard that directly checks the user-facing
  snippet.
- Generated artifact/test coverage critic: score 9, PASS. Blocking findings:
  none. Why not 10: the focused test checks the adapter skill source directly
  and relies on plugin sync to guard the generated mirror, rather than asserting
  both copies in the same focused test. Follow-up/residual risk: accepted
  because `python3 scripts/sync-codex-plugin.py --check` covers the generated
  mirror.
- Process/scope critic: score 8, VETO. Blocking findings: Completion Gate and
  multi-review outcome were not yet recorded; dirty out-of-scope
  `backlog/README.md` needed explicit handling; same-file user-added items 44
  and 46 must not be unintentionally committed with item 45. Not accepted until
  affected re-review reaches score 9.
- Process/scope re-review: score 9, PASS. Blocking findings: none. Why not 10:
  same-file staging discipline for items 44/46 still depends on careful partial
  staging or equivalent index construction. Follow-up/residual risk: accepted
  because final staging excludes unrelated same-file backlog additions.
- Score handling: score 8 triggered VETO recovery; affected process/scope
  critic re-review reached score 9. Every score 9 records why not 10 and
  residual-risk disposition.
- Rerun status: process/scope affected critic re-review after Completion Gate;
  final score 9.
- Follow-up/residual risk: no backlog follow-up from score-9 residuals; final
  closure is complete in this record.
- Final acceptance: yes.

### 49. P2 automate target-project autoresearch protection install

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-05
Scope:
- adapters/codex/scripts/
- adapters/codex/skills/autoresearch/SKILL.md
- adapters/codex/README.md
- adapters/codex/hook-schema.md
- adapters/codex/tests/
- plugins/ai-agent-meta-harness/
- scripts/sync-codex-plugin.py
- backlog/codex-adapter.md
- backlog/archive/codex-adapter.md

Source review: 2026-05-05 multi-review of clean local `main` against the
Meta-Harness methodology.

The Codex autoresearch protection bundle is well specified: the generated plugin
contains the checker, hook smoke script, protected-path template, Codex hook
template, pre-commit template, CI template, and AGENTS reminder snippet. The
remaining operability gap is that target projects still copy and merge those
assets manually. That keeps the evidence boundary honest, but makes partial
installation, stale hook wiring, or skipped smoke tests easier than the
methodology wants for evaluator-boundary protection.

Potential improvement:

- Provide a target-project install helper, skill-local script, or guided command
  that copies the protection assets from the generated plugin or canonical
  adapter source into an adopting project.
- Merge with existing `.codex/`, `.githooks/`, `.github/workflows/`, and
  `AGENTS.md` surfaces without silently overwriting project-owned hooks or CI.
- Run or print the exact smoke commands needed to prove the copied checker,
  Codex hook deny shapes, pre-commit wrapper, and CI/base-ref behavior.
- Preserve the existing protection-level honesty: incomplete installs must still
  report `Protection level: incomplete`, and local-only installs must record the
  missing shared CI reason.

Done when:

- A target project can install the Codex autoresearch protection assets through a
  repeatable helper or explicitly reviewed workflow instead of manual copy/paste.
- The install path has fixture or temp-project coverage for new projects and
  projects with existing hooks/CI/AGENTS content.
- Adapter docs and skill output distinguish installed, smoke-tested protection
  from template-only or direct-copy degraded states.

Completion Gate:

- Backlog status: `완료`; archived to `backlog/archive/codex-adapter.md`.
- Changed files: `adapters/codex/README.md`,
  `adapters/codex/hook-schema.md`, `adapters/codex/plugin-scope.md`,
  `adapters/codex/scripts/check-codex-hook-schema-drift.py`,
  `adapters/codex/scripts/install-autoresearch-protection.py`,
  `adapters/codex/scripts/smoke-autoresearch-hooks.py`,
  `adapters/codex/scripts/smoke-local-plugin.py`,
  `adapters/codex/skills/autoresearch/SKILL.md`,
  `adapters/codex/tests/test_direct_copy_fallback_reporting.py`,
  `adapters/codex/tests/test_hook_schema_drift.py`,
  `adapters/codex/tests/test_install_autoresearch_protection.py`,
  `plugins/ai-agent-meta-harness/README.md`,
  `plugins/ai-agent-meta-harness/hook-schema.md`,
  `plugins/ai-agent-meta-harness/plugin-scope.md`,
  `plugins/ai-agent-meta-harness/scripts/check-codex-hook-schema-drift.py`,
  `plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py`,
  `plugins/ai-agent-meta-harness/scripts/smoke-autoresearch-hooks.py`,
  `plugins/ai-agent-meta-harness/scripts/smoke-local-plugin.py`,
  `plugins/ai-agent-meta-harness/skills/autoresearch/SKILL.md`,
  `scripts/sync-codex-plugin.py`, `backlog/codex-adapter.md`,
  `backlog/archive/codex-adapter.md`.
- Scope deviations: added `adapters/codex/hook-schema.md` and generated
  `plugins/ai-agent-meta-harness/hook-schema.md` to Scope before editing because
  the autoresearch skill change is hook-sensitive and required a fresh
  hook-schema re-verification record. Existing dirty out-of-scope
  `backlog/README.md` and `backlog/core.md` remain unstaged.
- Verification results: PASS `python3 -m unittest adapters/codex/tests/test_install_autoresearch_protection.py adapters/codex/tests/test_direct_copy_fallback_reporting.py adapters/codex/tests/test_local_plugin_smoke.py adapters/codex/tests/test_hook_templates.py`; PASS `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3 -m unittest adapters/codex/tests/test_hook_schema_drift.py adapters/codex/tests/test_install_autoresearch_protection.py adapters/codex/tests/test_hook_templates.py`; PASS `python3 scripts/sync-codex-plugin.py --check`; PASS `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`; PASS `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`; PASS `python3 adapters/codex/scripts/smoke-local-plugin.py`; PASS Git-target installer smoke with `core.hooksPath` output `.githooks`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation because the
    session proceeded from Start Gate directly into implementation; this
    sequencing miss is recorded as process residual rather than backfilled.
  - DURING: FAIL `python3 scripts/run-search-set.py`; SS-003 failed while the
    new installer source was still untracked and invisible to index-aware
    plugin sync.
  - AFTER: PASS `python3 scripts/run-search-set.py` after staging this
    Completion Gate and selected item files.
- Multi-review required: yes; this changes Codex adapter install behavior,
  evaluator-boundary protection assets, hook/pre-commit/CI semantics, and
  generated plugin distribution surface.
- Multi-review result: PASS after VETO fixes and affected critic reruns.
- Reviewer scores and VETO handling: install-behavior critic initially scored 6
  VETO because Git pre-commit activation was implicit, protected paths were
  hardcoded instead of copied from the canonical template, `--run-smoke` did not
  validate pre-commit/CI behavior, and `.codex/config.toml` was not detected;
  fixed by copying the canonical template, configuring `core.hooksPath` when
  safe, adding explicit manual/merge-required handling, and expanding smoke
  behavior. Affected re-review scored 9 PASS. Protection-honesty critic
  initially scored 7 VETO because the installer reported non-tier `Protection
  level: template-installed` and only ran hook smoke; fixed by reporting only
  defined tiers and running/skipping smokes with explicit reasons. Affected
  re-review scored 9 PASS. Bundle/verification critic initially scored 7 VETO
  because new installer files were untracked and index-aware sync failed, then
  scored 8 VETO because hook-sensitive staged changes lacked hook-schema
  re-verification; fixed by staging the source/generated installer files and
  updating hook-schema, drift-checker metadata, smoke metadata, and tests.
  Affected re-review scored 9 PASS.
- For each score 9, why not 10: install-behavior critic noted that
  `.codex/config.toml` merge-required reporting is less precise than it could be
  and that fixture coverage does not directly exercise `.codex/config.toml` or a
  CI smoke path with an initial commit. Protection-honesty critic noted that
  pre-commit smoke is a direct checker invocation, not a negative proof that an
  actual `git commit` hook blocks a protected-path change. Bundle/verification
  critic noted final Completion Gate and search-set records were pending during
  the re-review.
- Backlog items added from score-9 residual risk: added
  `backlog/codex-adapter.md` item 50 for deeper installer fixture coverage
  covering `.codex/config.toml`, initial-commit CI smoke, and optional negative
  git-hook blocking proof. The bundle/verification critic's why-not-10 was final
  closure timing, not a separate backlog improvement.
- Residual risk/follow-up: item 50 tracks the remaining actionable fixture
  precision. BEFORE search-set was skipped because it was not captured before
  implementation; AFTER search-set passed.
- Follow-up/residual risk: item 50 tracks the remaining actionable fixture
  precision; AFTER search-set verification passed before commit.
- Accepted: yes.

Multi-review:

- Install-behavior critic: score 6, VETO. Blocking findings: missing Git
  pre-commit activation, hardcoded protected template content, insufficient
  smoke coverage, and missing `.codex/config.toml` merge detection. Not accepted
  until fixed and rerun.
- Install-behavior re-review: score 9, PASS. Blocking findings: none. Why not
  10: `.codex/config.toml` merge-required reporting and initial-commit CI smoke
  coverage can be more precise. Follow-up: item 50.
- Protection-honesty critic: score 7, VETO. Blocking finding: non-tier
  `Protection level: template-installed` plus hook-only smoke could overstate
  readiness. Not accepted until fixed and rerun.
- Protection-honesty re-review: score 9, PASS. Blocking findings: none. Why not
  10: pre-commit smoke does not prove an actual negative `git commit` hook
  block. Follow-up: item 50.
- Bundle/verification critic: score 7, VETO. Blocking finding: index-aware sync
  failed while new installer files were untracked. Not accepted until fixed and
  rerun.
- Bundle/verification re-review: score 8, VETO. Blocking finding:
  hook-sensitive staged changes lacked a staged hook-schema re-verification
  record. Not accepted until fixed and rerun.
- Bundle/verification second re-review: score 9, PASS. Blocking findings: none.
  Why not 10: Completion Gate and final search-set records were still pending at
  review time. Follow-up: no backlog item; this final record closes that timing
  gap.
- Score handling: all scores below 9 were treated as VETO; affected critics
  were rerun after fixes until all required scores reached 9.
- Rerun status: all affected critics rerun; final scores are 9, 9, and 9.
- Follow-up/residual risk: item 50 tracks actionable fixture precision from the
  score-9 residuals; final search-set verification must pass before commit.
- Final acceptance: yes.

### 50. P3 add deeper installer protection fixture coverage

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-05
Scope:
- adapters/codex/scripts/install-autoresearch-protection.py
- adapters/codex/tests/test_install_autoresearch_protection.py
- plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py
- backlog/codex-adapter.md
- backlog/archive/codex-adapter.md

Source: item 49 multi-review score-9 residual risk.

The target-project autoresearch protection installer now covers fresh Git
targets, existing hook/CI/AGENTS/protected-file projects, non-Git manual setup,
and conflicting `core.hooksPath` cases. The score-9 reviewers accepted the
current local-only reporting, but noted that fixture coverage can be more exact:
it does not run an actual negative `git commit` hook block, does not directly
cover `.codex/config.toml` merge-required behavior, and does not exercise the CI
smoke path against a target with an initial commit.

Potential improvement:

- Add installer fixture coverage for existing `.codex/config.toml` so the
  merge-required record names the active config surface precisely.
- Add a target Git fixture with an initial commit so `--run-smoke` exercises the
  CI checker path instead of only recording the no-base skipped reason.
- Consider a negative commit-hook fixture that proves protected-path changes are
  blocked by the installed `.githooks/pre-commit` hook without leaving target
  fixtures dirty.

Completion Gate:

- Backlog status: `완료`; archived to `backlog/archive/codex-adapter.md`.
- Changed files: `adapters/codex/scripts/install-autoresearch-protection.py`,
  `adapters/codex/tests/test_install_autoresearch_protection.py`,
  `plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py`,
  `backlog/codex-adapter.md`, `backlog/archive/codex-adapter.md`.
- Scope deviations: none. Existing dirty out-of-scope `backlog/README.md` and
  `backlog/core.md` remain unstaged.
- Verification results: BEFORE PASS `python3 scripts/run-search-set.py`; PASS
  `python3 -m unittest adapters/codex/tests/test_install_autoresearch_protection.py`;
  PASS `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3
  scripts/sync-codex-plugin.py --check`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin.py`; PASS `git diff --cached
  --check`.
- Search-set verification: BEFORE PASS `python3 scripts/run-search-set.py`;
  AFTER PASS `python3 scripts/run-search-set.py` after this Completion Gate and
  selected item files were staged.
- Multi-review required: yes; this changes Codex adapter installer protection
  behavior and fixture evidence for hook/pre-commit/CI semantics.
- Multi-review result: PASS after affected re-review for output precision.
- Reviewer scores and VETO handling: installer-behavior critic scored 9 PASS,
  then after the local CI smoke command output was made explicit reran at 10
  PASS; protection-honesty critic scored 9 PASS, then affected re-review scored
  10 PASS; verification/bundle critic scored 9 PASS with a completion-readiness
  note. No reviewer score was below 9, so no VETO handling was required.
- For each score 9, why not 10: initial installer-behavior 9 noted the printed
  generic CI command did not show the actual `--base-ref HEAD` local smoke
  command; fixed before acceptance and rerun to 10. Initial protection-honesty 9
  noted that `--base-ref HEAD` proves local command wiring but not a PR-base
  protected-path CI rejection; accepted as honest local-only scope after the
  explicit local command output was added, and affected re-review scored 10.
  Verification/bundle 9 noted Completion Gate/archive closure and out-of-scope
  dirty files were still pending; this final record and selective staging close
  the timing concern.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: no follow-up. Item 50 now covers
  `.codex/config.toml` merge-required precision, initial-commit local CI smoke,
  and a real negative `git commit` hook block. The remaining CI boundary is
  explicitly local-only and does not claim shared-repo PR comparison proof.
- Follow-up/residual risk: no follow-up; residual CI scope is accepted as
  honest local-only evidence, not shared-repo protection.
- Accepted: yes.

Multi-review:

- Installer-behavior critic: score 9, PASS. Blocking findings: none. Why not
  10: printed smoke commands still showed generic `--ci` while the actual local
  initial-commit smoke used `--base-ref HEAD`. Follow-up/residual risk:
  addressed immediately by printing the explicit local CI smoke command and
  asserting it in the focused test.
- Installer-behavior affected re-review: score 10, PASS. Blocking findings:
  none. Prior why-not-10 resolved.
- Protection-honesty critic: score 9, PASS. Blocking findings: none. Why not
  10: `--base-ref HEAD` proves local command wiring/executability, not a
  shared-repo PR-base protected-path rejection. Follow-up/residual risk:
  accepted as honest local-only evidence after explicit command output.
- Protection-honesty affected re-review: score 10, PASS. Blocking findings:
  none. Evidence boundary is clear and bounded.
- Verification/bundle critic: score 9, PASS. Blocking findings: none. Why not
  10: item 50 was still `진행중`, archive/Completion Gate were pending, and
  unrelated dirty backlog files required careful commit boundaries. Follow-up:
  no backlog item; this final archive and selective staging close the process
  timing concern.
- Score handling: no score below 9; no VETO.
- Rerun status: affected behavior/protection critics rerun after output
  precision fix; final scores are 10, 10, and 9.
- Follow-up/residual risk: no backlog follow-up. The only final score-9 reason
  was pre-acceptance closure timing, resolved in this record.
- Final acceptance: yes.

### 44. P2 keep Codex Desktop/runtime delivery smoke open until product surface exists

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/README.md
- adapters/codex/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- plugins/ai-agent-meta-harness/
- backlog/codex-adapter.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

Item 40 correctly completed the evidence-boundary work: docs now distinguish
generated artifact integrity, isolated CLI activation/config shape, and runtime
model-visible skill surfacing or plugin hook event delivery. It also kept
runtime hook manifest fields disabled. The remaining unsolved work is the
actual runtime delivery proof, which was intentionally deferred because the repo
does not yet have a stable noninteractive Codex Desktop or equivalent runtime
surface for that claim.

Potential improvement:

- Track official or product-supported Codex runtime surfaces that can prove a
  running session has loaded the generated plugin and surfaced the expected
  skills to the model.
- Add a smoke test or explicitly reviewed manual gate for runtime plugin
  delivery before enabling plugin manifest `hooks` fields.
- Keep CLI help-surface probes and isolated activation smokes as prerequisites,
  not substitutes, for runtime delivery evidence.
- Update plugin-scope and README docs when the runtime proof exists, without
  weakening the current evidence-boundary wording.

Done when:

- The repo has a product-supported automated smoke or reviewed manual procedure
  for Desktop/runtime plugin delivery evidence.
- Runtime hook manifest fields remain disabled until tool-event delivery is
  verified by that gate.
- Existing tests continue to reject overclaims that CLI activation proves
  runtime model-visible skill surfacing or plugin hook event delivery.

Implementation notes:

- Decision implemented: keep the actual runtime delivery proof open until a
  product-supported automated smoke exists, but define an explicitly reviewed
  manual evidence gate that can close the gap without overclaiming CLI
  activation as runtime delivery.
- The manual evidence packet must record Codex runtime version, surface, OS,
  plugin source path, local artifact/activation smoke results, CLI surface probe
  result or skipped reason, and fresh transcript/screenshot/exported-trace
  evidence that the running Codex surface loaded `ai-agent-meta-harness` and
  surfaced the expected skills.
- Manifest `hooks` fields remain disabled unless a separate reviewed evidence
  packet shows a plugin hook receiving a real tool event and Codex accepting the
  hook output from that runtime surface.
- Search-set verification:
  - SKIPPED: documentation/test-only Codex runtime-delivery evidence gate
    clarification; no runtime hook manifest field, plugin activation behavior,
    checker semantics, trace schema, or release gate changed.

Completion Gate:

- Backlog status: 완료; archived after multi-review PASS and final verification.
- Changed files:
  - `adapters/codex/README.md`
  - `adapters/codex/plugin-scope.md`
  - `adapters/codex/tests/test_hook_templates.py`
  - `plugins/ai-agent-meta-harness/README.md`
  - `plugins/ai-agent-meta-harness/plugin-scope.md`
  - `backlog/codex-adapter.md`
  - `backlog/archive/codex-adapter.md`
- Scope deviations:
  - `backlog/README.md` remains a pre-existing unrelated dirty user edit and
    must stay unstaged.
- Verification results:
  - BEFORE: PASS `python3 scripts/sync-codex-plugin.py --check`
  - BEFORE: PASS `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - BEFORE: PASS `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - BEFORE: PASS `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - AFTER: PASS `python3 -m unittest adapters/codex/tests/test_hook_templates.py`
  - AFTER: PASS `python3 scripts/sync-codex-plugin.py --check`
  - AFTER: PASS `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - AFTER: PASS `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - AFTER: PASS `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - AFTER: PASS `python3 adapters/codex/scripts/check-codex-cli-surface.py`
  - AFTER: PASS `python3 scripts/check-maintenance-review.py`
  - AFTER: PASS `python3 scripts/check-search-set-evidence.py`
  - AFTER: PASS `python3 scripts/check-backlog-archive-lifecycle.py`
  - AFTER: PASS `python3 scripts/verify-release.py --skip-clean-worktree --base-ref origin/main`
  - AFTER: PASS `git diff --check`
- Search-set verification:
  - SKIPPED: documentation/test-only Codex runtime-delivery evidence gate
    clarification; no runtime hook manifest field, plugin activation behavior,
    checker semantics, trace schema, or release gate changed.
- Multi-review required: yes, Codex distribution/runtime delivery evidence and
  manifest hook gating are durable adapter contracts.
- Multi-review result: PASS with three independent sub-agent reviewers using
  the Codex multi-review governance protocol.
- Reviewer scores and VETO handling:
  - Runtime delivery boundary critic: 9/10 PASS; no VETO.
  - Test/generated artifact coverage critic: 9/10 PASS; no VETO.
  - Maintenance process/scope critic: 9/10 PASS; no VETO.
- For each score 9, why not 10:
  - Runtime delivery boundary critic: manual gate is prose plus
    string-asserted documentation, not a structured evidence packet template or
    validator. Accepted as residual risk because item 44 only required a
    reviewed manual gate while no product-supported runtime smoke exists; no
    follow-up needed before first real runtime review.
  - Test/generated artifact coverage critic: `sync-codex-plugin.py --check`
    is index-oriented, so `--check` alone is not a complete reviewer tool for
    unstaged generated-artifact drift. Accepted as residual risk because the
    focused unit test compares working-tree canonical/generated docs for this
    item and the release/pre-commit contract is intentionally index-based.
  - Maintenance process/scope critic: completion evidence and archive closure
    were still pending at review time, and `backlog/README.md` was dirty outside
    scope. Addressed by this Completion Gate, staged-only discipline, and
    archive closure; no follow-up needed.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up:
  - No new follow-up. A structured runtime-delivery evidence template can be
    added later if maintainers want stronger ergonomics before the first real
    manual runtime review.
- Accepted: yes.

Multi-review:

- Runtime delivery boundary critic: score 9, PASS. Blocking findings: none.
  Why not 10: the gate is still prose plus string-asserted documentation, not a
  structured evidence packet template or validator. Follow-up/residual risk:
  accepted for this item because the goal was to define a reviewed manual gate
  while no stable runtime smoke exists.
- Test/generated artifact coverage critic: score 9, PASS. Blocking findings:
  none. Why not 10: `sync-codex-plugin.py --check` is index-oriented and is not
  alone a complete reviewer tool for unstaged generated-artifact drift.
  Follow-up/residual risk: accepted because the focused unit test compares the
  working-tree canonical and generated docs for this change, while pre-commit
  and release checks intentionally use the index.
- Maintenance process/scope critic: score 9, PASS. Blocking findings: none.
  Why not 10: completion evidence and archive closure were pending at review
  time, and `backlog/README.md` was dirty outside the item scope.
  Follow-up/residual risk: addressed by this Completion Gate, archive closure,
  and staged-only discipline.
- Score handling: no VETO. Every score 9 records why not 10 and residual-risk
  disposition.
- Rerun status: no affected critic rerun required.
- Follow-up/residual risk: no backlog follow-up from score-9 residuals.
- Final acceptance: yes.

### 46. P3 list bundled init AGENTS asset in Codex plugin scope

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/codex/plugin-scope.md
- plugins/ai-agent-meta-harness/plugin-scope.md
- adapters/codex/tests/test_hook_templates.py
- backlog/codex-adapter.md
- backlog/archive/codex-adapter.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`adapters/codex/plugin-scope.md` lists the generated
`skills/init-codex-harness/SKILL.md` and the top-level
`templates/AGENTS.md.template`, but it does not list the bundled
`skills/init-codex-harness/assets/AGENTS.md.template` that the init skill names
as its local project template. The recursive-copy note explains why it ships,
but the supported generated-contents inventory is incomplete for consumers
checking the init skill's bundled assets.

Potential improvement:

- Add `skills/init-codex-harness/assets/AGENTS.md.template` to canonical and
  generated plugin-scope generated contents.
- Clarify the distinction between the skill-local init asset and the top-level
  compatibility template if needed.
- Add or extend focused plugin-scope tests so bundled skill assets remain listed
  when they are part of the supported generated surface.

Done when:

- Plugin-scope generated contents enumerate the init skill's bundled AGENTS
  asset.
- Canonical and generated plugin-scope files remain synchronized.
- Plugin sync and focused Codex docs tests pass.

Decision implemented:

- `adapters/codex/plugin-scope.md` now lists
  `skills/init-codex-harness/assets/AGENTS.md.template` in the generated
  contents inventory.
- The v1 canonical path policy now distinguishes the init skill-local project
  template asset from the top-level compatibility/bootstrap
  `templates/AGENTS.md.template`.
- `adapters/codex/tests/test_hook_templates.py` now checks both canonical and
  generated plugin-scope docs for the bundled init AGENTS asset entry.
- The generated plugin-scope mirror was refreshed with
  `python3 scripts/sync-codex-plugin.py --write`.

Search-set verification:

- SKIPPED: docs/test-only generated plugin inventory clarification; no
  agent-visible runtime behavior, hook/checker semantics, trace schema,
  evaluator-boundary policy, or release gate changed.

Completion Gate:

- Backlog status: `완료`; archived to `backlog/archive/codex-adapter.md`
  after process/scope VETO recovery re-review passed.
- Changed files: `adapters/codex/plugin-scope.md`,
  `plugins/ai-agent-meta-harness/plugin-scope.md`,
  `adapters/codex/tests/test_hook_templates.py`,
  `backlog/codex-adapter.md`, `backlog/archive/codex-adapter.md`.
- Scope deviations: none for item 46. Dirty out-of-scope `backlog/README.md`
  remains unstaged. Same-file item 44 and status-summary text are unrelated
  user-added backlog changes; final staging must include only the selected item
  46 record/hunks plus implementation files.
- Verification results: BEFORE PASS `python3 -m unittest
  adapters/codex/tests/test_local_plugin_smoke.py`; BEFORE PASS
  `python3 scripts/sync-codex-plugin.py --check`; AFTER PASS
  `python3 -m unittest adapters/codex/tests/test_hook_templates.py`; AFTER PASS
  `python3 scripts/sync-codex-plugin.py --check`; AFTER PASS
  `python3 adapters/codex/scripts/smoke-local-plugin.py`; AFTER PASS
  `python3 scripts/check-maintenance-review.py`; AFTER PASS
  `python3 scripts/check-search-set-evidence.py`; AFTER PASS
  `python3 scripts/verify-release.py --skip-clean-worktree --base-ref
  origin/main`; PASS `git diff --check`.
- Search-set verification:
  - SKIPPED: docs/test-only generated plugin inventory clarification; no
    agent-visible runtime behavior, hook/checker semantics, trace schema,
    evaluator-boundary policy, or release gate changed.
- Multi-review required: yes; this changes Codex generated plugin-scope
  inventory and distribution-surface documentation.
- Multi-review result: PASS after process/scope VETO recovery re-review.
- Reviewer scores and VETO handling: plugin-scope generated-surface critic 9
  PASS; tests/generated artifact coverage critic 9 PASS; process/scope critic
  8 VETO because Completion Gate and multi-review outcome were not yet recorded,
  dirty out-of-scope `backlog/README.md` needed explicit handling, and same-file
  item 44/status-summary changes needed final staging discipline. This gate
  addressed those blockers; affected process/scope re-review scored 9 PASS.
- For each score 9, why not 10: plugin-scope generated-surface critic noted the
  local plugin smoke expected assets still do not explicitly check the
  skill-local bundled AGENTS asset, accepted because recursive sync ownership
  plus focused plugin-scope coverage is sufficient for this P3 docs/surface fix;
  tests/generated artifact coverage critic noted the test is string-based
  rather than deriving inventory from the sync map or parsing Markdown
  structurally, accepted because user-facing plugin-scope wording is the guarded
  behavior; process/scope critic noted final archive/staging/commit closure
  was still pending during re-review, addressed by this final status/archive
  update.
- Backlog items added from score-9 residual risk: none; score-9 residuals
  are accepted as documentation-inventory test design or final-closure timing
  tradeoffs for this item.
- Residual risk/follow-up: no follow-up. Plugin-scope generated contents now
  enumerate the skill-local init AGENTS asset, and final process closure is
  complete.
- Accepted: yes.

Multi-review:

- Plugin-scope generated-surface critic: score 9, PASS. Blocking findings:
  none. Why not 10: local plugin smoke expected assets still check only the
  top-level `templates/AGENTS.md.template`, not the skill-local bundled asset.
  Follow-up/residual risk: accepted because sync recursively owns skill assets
  and the focused plugin-scope test locks the documented generated surface.
- Tests/generated artifact coverage critic: score 9, PASS. Blocking findings:
  none. Why not 10: the test is string-based against prose/table text rather
  than deriving expected inventory from the sync map or parsing Markdown
  structurally. Follow-up/residual risk: accepted because this docs inventory
  item guards user-facing wording, and harmless copy edits can update the test.
- Process/scope critic: score 8, VETO. Blocking findings: Completion Gate and
  multi-review outcome were not yet recorded; dirty out-of-scope
  `backlog/README.md` needed explicit handling; same-file item 44/status-summary
  changes must not be unintentionally committed with item 46. Not accepted until
  affected re-review reaches score 9.
- Process/scope re-review: score 9, PASS. Blocking findings: none. Why not 10:
  final archive/staging/commit closure was still pending during re-review.
  Follow-up/residual risk: addressed by this final status/archive update.
- Score handling: score 8 triggered VETO recovery; affected process/scope
  critic re-review reached score 9. Every score 9 records why not 10 and
  residual-risk disposition.
- Rerun status: process/scope affected critic re-review after Completion Gate;
  final score 9.
- Follow-up/residual risk: no backlog follow-up from score-9 residuals; final
  closure is complete in this record.
- Final acceptance: yes.
