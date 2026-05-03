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

- No active implementation follow-up remains in this epic. Direct-copy fallback
  limitation reporting is completed in item 27, and runtime hook manifest
  fields remain intentionally gated by item 28 until Codex exposes a mechanical
  plugin tool-event delivery smoke surface.

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
- For each score 9, why not 10:
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
- For each score 9, why not 10:
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
