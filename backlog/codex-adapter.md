# Codex Adapter Backlog

Codex-specific backlog for adapter behavior that should not be pushed into the shared core. Core methodology follow-ups live in `backlog/core.md`.

## Priority Candidates

### 1. Add Codex sandbox/escalation recording template

Status: 완료
Archived: `backlog/archive/codex-adapter.md#1-add-codex-sandbox-escalation-recording-template`

### 2. Clarify Codex trace-root migration behavior

Status: 완료
Archived: `backlog/archive/codex-adapter.md#2-clarify-codex-trace-root-migration-behavior`

### 3. Harden Codex hook enforcement templates

Status: 완료
Archived: `backlog/archive/codex-adapter.md#3-harden-codex-hook-enforcement-templates`

### 4. Implement the chosen Codex distribution path

Decision: use a **local Codex plugin bundle** as the primary distribution path.

Status of paths:

- Local plugin bundle: primary bundle target for normal local development and dogfooding; artifact, fixture, and isolated activation smokes are implemented.
- Direct skill copy: development fallback for fast skill text iteration only.
- Marketplace/plugin bundle: future release path after local plugin layout stabilizes.
- `skill-installer`: compatibility investigation for skill-only degraded installs.

Implemented foundation:

- `plugins/ai-agent-meta-harness/.codex-plugin/plugin.json` is generated from canonical adapter metadata.
- `scripts/sync-codex-plugin.py --write` materializes the local plugin bundle from `adapters/codex/`.
- `scripts/sync-codex-plugin.py --check` fails on missing, stale, extra, invalid, binary-different, or semantically empty required plugin surfaces.
- `.githooks/pre-commit` runs the plugin drift check alongside compatibility mirror checks.
- README install guidance points to the generated local plugin bundle first, with direct skill copy as a degraded fallback.
- `smoke-local-plugin.py`, `smoke-local-plugin-activation.py`, and
  `smoke-init-codex-project-fixtures.py` cover generated artifact integrity,
  isolated CLI marketplace activation, and representative init fixture output.

Remaining follow-up work:

- Direct-copy fallback limitation reporting is completed in item 27, and
  runtime hook manifest fields remain intentionally gated by item 28.
- Item 40 records the current runtime-delivery evidence boundary and keeps
  runtime hook manifest fields disabled until a product-supported smoke or
  reviewed manual gate exists.
- Item 42 tracks an optional local Codex CLI surface probe so documentation can
  mechanically pin the observed `plugin marketplace` and `app-server` surface
  without claiming Desktop runtime delivery.

### 5. Define Codex plugin bundle scope

Status: 완료
Archived: `backlog/archive/codex-adapter.md#5-define-codex-plugin-bundle-scope`

### 6. Standardize Codex verify command discovery

Status: 완료
Archived: `backlog/archive/codex-adapter.md#6-standardize-codex-verify-command-discovery`

### 7. Document sub-agent capability matrix by Codex surface

Status: 완료
Archived: `backlog/archive/codex-adapter.md#7-document-sub-agent-capability-matrix-by-codex-surface`

### 8. Expand Codex permission and escalation guidance

Status: 완료
Archived: `backlog/archive/codex-adapter.md#8-expand-codex-permission-and-escalation-guidance`

### 9. Codexize MCP and tool-use policy

Status: 완료
Archived: `backlog/archive/codex-adapter.md#9-codexize-mcp-and-tool-use-policy`

### 10. Add Codex examples

Status: 완료
Archived: `backlog/archive/codex-adapter.md#10-add-codex-examples`

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

### 12. Provide a Codex autoresearch protection checker reference implementation

Status: 완료
Archived: `backlog/archive/codex-adapter.md#12-provide-a-codex-autoresearch-protection-checker-reference-implementation`

### 13. Make Codex hook smoke tests mechanically assert output

Status: 완료
Archived: `backlog/archive/codex-adapter.md#13-make-codex-hook-smoke-tests-mechanically-assert-output`

### 14. Track Codex hook schema drift

Status: 완료
Archived: `backlog/archive/codex-adapter.md#14-track-codex-hook-schema-drift`

### 15. Clarify local-only protection reporting

Status: 완료
Archived: `backlog/archive/codex-adapter.md#15-clarify-local-only-protection-reporting`

### 16. Extend the Codex plugin layout as assets grow

Status: 완료
Archived: `backlog/archive/codex-adapter.md#16-extend-the-codex-plugin-layout-as-assets-grow`

### 17. Define Codex plugin marketplace metadata policy

Status: 완료
Archived: `backlog/archive/codex-adapter.md#17-define-codex-plugin-marketplace-metadata-policy`

### 18. Add local plugin artifact smoke test

Status: 완료
Archived: `backlog/archive/codex-adapter.md#18-add-local-plugin-artifact-smoke-test`

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

### 20. Add Codex marketplace metadata release validation

Status: 완료
Archived: `backlog/archive/codex-adapter.md#20-add-codex-marketplace-metadata-release-validation`

### 21. Document Codex hook template install paths

Status: 완료
Archived: `backlog/archive/codex-adapter.md#21-document-codex-hook-template-install-paths`

### 22. Document non-GitHub CI BASE_REF setup

Status: 완료
Archived: `backlog/archive/codex-adapter.md#22-document-non-github-ci-base-ref-setup`

### 23. P1 align Codex multi-review threshold with maintenance VETO policy

Status: 완료
Archived: `backlog/archive/codex-adapter.md#23-p1-align-codex-multi-review-threshold-with-maintenance-veto-policy`

### 24. P2 prefer meaningful Claude history over empty Codex trace roots

Status: 완료
Archived: `backlog/archive/codex-adapter.md#24-p2-prefer-meaningful-claude-history-over-empty-codex-trace-roots`

### 25. P2 connect marketplace metadata checker to publication gates when ready

Status: 완료
Archived: `backlog/archive/codex-adapter.md#25-p2-connect-marketplace-metadata-checker-to-publication-gates-when-ready`

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
