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
- Item 40 records the current runtime-delivery evidence boundary, while item 44
  defines the reviewed manual evidence gate for Desktop/runtime delivery while
  product-supported smoke coverage is unavailable. Item 47 tracks the first
  real runtime evidence packet or automated smoke when a suitable runtime
  surface exists.
- Item 42 tracks an optional local Codex CLI surface probe so documentation can
  mechanically pin the observed `plugin marketplace` and `app-server` surface
  without claiming Desktop runtime delivery.
- Item 48 tracks a narrower live-init evidence gap: the fixture smoke proves
  expected generated files, but not that a running Codex session can invoke the
  `init-codex-harness` skill end to end.
- Item 49 tracks target-project protection install automation, because the
  current guardrail assets are documented and smoke-tested but still copied and
  merged manually into adopting projects.
- Item 51 tracks the remaining adopter-facing install UX gap: the installer
  exists, but the docs/skill command path still needs to be unambiguous when the
  user starts from a target project rather than this repository checkout.

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
Archived: `backlog/archive/codex-adapter.md#11-test-codex-adapter-on-real-project-types`
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
Archived: `backlog/archive/codex-adapter.md#19-add-true-codex-local-plugin-activation-smoke-test`
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
Archived: `backlog/archive/codex-adapter.md#26-reconcile-codex-distribution-epic-follow-up-text`
### 27. Define direct-copy fallback limitation reporting

Status: 완료
Archived: `backlog/archive/codex-adapter.md#27-define-direct-copy-fallback-limitation-reporting`
### 28. Gate runtime hook manifest fields on tool-event coverage

Status: 완료
Archived: `backlog/archive/codex-adapter.md#28-gate-runtime-hook-manifest-fields-on-tool-event-coverage`
### 29. P2 make marketplace metadata manifest discovery index-only in pre-commit

Status: 완료
Archived: `backlog/archive/codex-adapter.md#29-p2-make-marketplace-metadata-manifest-discovery-index-only-in-pre-commit`
### 43. P3 refresh Codex plugin-scope v1 protection status

Status: 완료
Archived: `backlog/archive/codex-adapter.md#43-p3-refresh-codex-plugin-scope-v1-protection-status`
### 42. P3 add optional Codex CLI surface probe for runtime-delivery docs

Status: 완료
Archived: `backlog/archive/codex-adapter.md#42-p3-add-optional-codex-cli-surface-probe-for-runtime-delivery-docs`
### 35. P3 refresh active backlog summaries after Codex items 32-34

Status: 완료
Archived: `backlog/archive/codex-adapter.md#35-p3-refresh-active-backlog-summaries-after-codex-items-32-34`
### 36. P2 pin bounded timeouts in Codex hook templates

Status: 완료
Archived: `backlog/archive/codex-adapter.md#36-p2-pin-bounded-timeouts-in-codex-hook-templates`
### 40. P2 add Codex Desktop/runtime plugin delivery smoke when surface exists

Status: 완료
Archived: `backlog/archive/codex-adapter.md#40-p2-add-codex-desktop-runtime-plugin-delivery-smoke-when-surface-exists`
### 41. P3 refresh Codex v1 protection scope status

Status: 완료
Archived: `backlog/archive/codex-adapter.md#41-p3-refresh-codex-v1-protection-scope-status`
### 37. P3 refresh Codex hook schema freshness signaling

Status: 완료
Archived: `backlog/archive/codex-adapter.md#37-p3-refresh-codex-hook-schema-freshness-signaling`
### 38. P2 add end-to-end Codex adoption smoke for generated search-set commands

Status: 완료
Archived: `backlog/archive/codex-adapter.md#38-p2-add-end-to-end-codex-adoption-smoke-for-generated-search-set-commands`
### 39. P3 list init fixture smoke in Codex plugin-scope generated contents

Status: 완료
Archived: `backlog/archive/codex-adapter.md#39-p3-list-init-fixture-smoke-in-codex-plugin-scope-generated-contents`
### 32. P2 add activation smoke to release checklist

Status: 완료
Archived: `backlog/archive/codex-adapter.md#32-p2-add-activation-smoke-to-release-checklist`
### 33. P2 include hard-layer hook templates in hook-sensitive drift policy

Status: 완료
Archived: `backlog/archive/codex-adapter.md#33-p2-include-hard-layer-hook-templates-in-hook-sensitive-drift-policy`
### 34. P2 list activation smoke in Codex plugin-scope generated contents

Status: 완료
Archived: `backlog/archive/codex-adapter.md#34-p2-list-activation-smoke-in-codex-plugin-scope-generated-contents`
### 30. P3 reconcile active backlog summaries after completed Codex follow-ups

Status: 완료
Archived: `backlog/archive/codex-adapter.md#30-p3-reconcile-active-backlog-summaries-after-completed-codex-follow-ups`
### 31. P2 align root Codex activation smoke documentation with implementation

Status: 완료
Archived: `backlog/archive/codex-adapter.md#31-p2-align-root-codex-activation-smoke-documentation-with-implementation`

### 44. P2 keep Codex Desktop/runtime delivery smoke open until product surface exists

Status: 완료
Archived: `backlog/archive/codex-adapter.md#44-p2-keep-codex-desktop-runtime-delivery-smoke-open-until-product-surface-exists`

### 45. P3 keep embedded Codex hook examples bounded

Status: 완료
Archived: `backlog/archive/codex-adapter.md#45-p3-keep-embedded-codex-hook-examples-bounded`
### 46. P3 list bundled init AGENTS asset in Codex plugin scope

Status: 완료
Archived: `backlog/archive/codex-adapter.md#46-p3-list-bundled-init-agents-asset-in-codex-plugin-scope`

### 47. P2 record first Codex Desktop/runtime delivery evidence packet

Status: 보류
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- backlog/codex-adapter.md

Originating source review: 2026-05-04 multi-review of clean local `main`
against the Meta-Harness methodology.

Items 40 and 44 correctly prevent overclaiming: artifact smoke and isolated CLI
activation prove bundle/config shape, while item 44 defines a reviewed manual
gate for runtime delivery when no product-supported automated smoke exists.
The repo still has no actual evidence packet proving that a running Codex
Desktop or equivalent runtime surfaced the generated plugin skills to the model
or delivered plugin hook tool events.

Potential improvement:

- When Codex exposes a suitable runtime surface, record the first reviewed
  runtime evidence packet using the item 44 manual gate or replace it with an
  automated smoke.
- Include runtime version, surface, OS, plugin source path, artifact smoke,
  activation smoke, CLI surface probe result or skipped reason, and transcript,
  screenshot, or exported trace evidence from the running runtime.
- Keep plugin manifest `hooks` fields disabled unless a separate reviewed packet
  proves hook tool-event delivery and accepted hook output.
- Update adapter README/plugin-scope docs and tests only after real runtime
  evidence exists.

Done when:

- The repository contains a reviewed runtime delivery evidence packet or
  automated smoke result for model-visible skill surfacing.
- Hook manifest enablement remains separately gated on actual tool-event
  delivery evidence.
- Existing documentation still distinguishes artifact integrity, isolated CLI
  activation/config, and runtime delivery proof.

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 47, P2 record first Codex
  Desktop/runtime delivery evidence packet.
- Status block added: yes, `진행중` reservation was added before
  implementation edits; this record is now `보류` because acceptance evidence is
  unavailable.
- Harness-affecting: yes, because the item concerns Codex adapter runtime
  delivery evidence and plugin delivery claims.
- Multi-review required: yes for accepting a runtime delivery evidence packet;
  if no packet exists, the correct outcome is non-acceptance rather than
  simulated review acceptance.
- Minimum verification commands: `python3 scripts/check-maintenance-review.py
  backlog/codex-adapter.md`; `python3 adapters/codex/scripts/smoke-local-plugin.py`;
  `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`; `python3
  adapters/codex/scripts/check-codex-cli-surface.py`; `python3
  scripts/sync-codex-plugin.py --check`; `python3 -m unittest
  adapters/codex/tests/test_hook_templates.py
  adapters/codex/tests/test_local_plugin_smoke.py
  adapters/codex/tests/test_local_plugin_activation_smoke.py`.
- Expected scope: current runtime surface/evidence check plus this item 47
  backlog record only; adapter docs and generated plugin mirrors remain
  unchanged unless real runtime delivery proof exists.

Attempted in 2026-05-04 single-session maintenance pass:

- Local artifact smoke passed.
- Isolated local Codex CLI marketplace activation smoke passed.
- Local Codex CLI surface probe passed for `plugin marketplace` and
  `app-server` help markers.
- Current Codex Desktop session did not expose the generated
  `ai-agent-meta-harness` plugin skills (`autoresearch`, `harness-engineer`,
  `init-codex-harness`) in the active runtime skill list, so this pass cannot
  honestly record the first model-visible runtime delivery packet.
- Hook manifest enablement remains gated on separate tool-event delivery
  evidence.

Completion Gate:

- Backlog status: `보류`; prerequisite evidence was refreshed, but the item is
  not accepted because the required runtime model-visible delivery evidence is
  unavailable in this session.
- Changed files: `backlog/codex-adapter.md`.
- Scope deviations: narrowed to backlog evidence/status only; no adapter docs
  changed because no runtime delivery proof exists. Unrelated dirty work remains
  intentionally unstaged in `backlog/README.md`, `backlog/core.md`, and
  pre-existing `backlog/codex-adapter.md` hunks outside item 47, including item
  48 and the top-level distribution-summary refresh.
- Verification results: PASS `python3 scripts/check-maintenance-review.py
  backlog/codex-adapter.md`; PASS `python3 adapters/codex/scripts/smoke-local-plugin.py`;
  PASS `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`;
  PASS `python3 adapters/codex/scripts/check-codex-cli-surface.py`; PASS
  `python3 scripts/sync-codex-plugin.py --check`; PASS `python3 -m unittest
  adapters/codex/tests/test_hook_templates.py
  adapters/codex/tests/test_local_plugin_smoke.py
  adapters/codex/tests/test_local_plugin_activation_smoke.py`.
- Search-set verification: SKIPPED because this pass made no accepted harness
  behavior or adapter contract change; it records that the required product
  runtime evidence is still absent.
- Multi-review required: yes for acceptance of a runtime delivery evidence
  packet; this pass instead ran multiple reviewers on the non-acceptance/blocked
  handoff record.
- Multi-review result: SKIPPED; no runtime delivery evidence packet exists in
  this session, so there is no acceptance packet to review.
- Reviewer scores and VETO handling: runtime-boundary critic 9 PASS;
  blocked-item appropriateness critic 9 PASS; maintenance-process critic 7 VETO
  on dirty-handoff disclosure, out-of-scope item 48 disclosure, and missing
  in-record Start Gate. VETO handled by adding this Start Gate, clarifying
  originating source review wording, and recording unrelated dirty/out-of-scope
  hunks explicitly. Maintenance-process re-review: 9 PASS, no blocking
  findings.
- For each score 9, why not 10: runtime-boundary critic was not 10 because
  `Originating source review` could be confused with this pass's acceptance
  multi-review; wording was clarified. Blocked-item appropriateness critic was
  not 10 because the active skill-list absence is recorded from session
  observation rather than an attached transcript/screenshot/exported trace; this
  is accepted for `보류` because it is evidence of absence sufficient to avoid
  false acceptance, not evidence used to prove runtime delivery.
  Maintenance-process re-review was not 10 because final commit readiness still
  depends on precise hunk staging that excludes disclosed unrelated/out-of-scope
  dirty changes; this will be handled by staging only item 47 and checking the
  staged patch before commit.
- Backlog items added from score-9 residual risk: none; no actionable
  repository improvement was created by the score-9 residuals. Item 48 was
  pre-existing user-added backlog work, not a follow-up added by this pass.
- Residual risk/follow-up: rerun this item only when the active Codex runtime
  can surface the generated `ai-agent-meta-harness` plugin skills or provides a
  product-supported noninteractive smoke for model-visible skill delivery.
- Accepted: no.

### 48. P3 record live init-codex-harness execution evidence when possible

Status: 보류
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- backlog/codex-adapter.md

Originating source review: 2026-05-04 multi-review of clean local `main`
against the Meta-Harness methodology.

The Codex init fixture smoke is useful contract coverage: it proves the expected
trace root, `AGENTS.md`, search-set, and evolution output shape for a
representative project fixture. It does not prove that a running Codex session
can load the generated plugin or direct-copy skill, execute
`init-codex-harness`, inspect a real target project, and produce those artifacts
from the live skill instructions.

Potential improvement:

- When a practical Codex runtime surface exists, run `init-codex-harness` against
  an isolated sample project and record the runtime, installation mode, input
  project, generated files, selected trace root, Active verify command, and
  transcript or exported trace evidence.
- Keep this separate from item 47 if item 47 proves only plugin skill surfacing;
  live init execution should prove the skill's workflow, not just availability.
- If live automation is unavailable, define a reviewed manual evidence packet
  analogous to the runtime-delivery gate and keep the fixture smoke as contract
  coverage rather than operability proof.
- Update README/plugin-scope wording only after the evidence exists.

Done when:

- The repository contains either an automated smoke or reviewed manual evidence
  that a live Codex session executed `init-codex-harness` on an isolated target
  project.
- The evidence distinguishes fixture contract coverage from live runtime
  operability.
- Existing fixture smoke remains as deterministic regression coverage even if
  live runtime evidence is manual or environment-dependent.

Start Gate:

- Selected item: `backlog/codex-adapter.md` item 48, P3 record live
  `init-codex-harness` execution evidence when possible.
- Status block added: yes, `진행중` reservation was added before
  implementation edits; this record is now `보류` because live skill execution
  evidence is unavailable.
- Harness-affecting: yes, because the item concerns Codex adapter live-init
  operability claims and evidence boundaries.
- Multi-review required: yes for accepting a live-init evidence packet or
  runtime-operability claim; if no live execution evidence exists, the correct
  outcome is non-acceptance rather than substituting fixture evidence.
- Minimum verification commands: `python3 scripts/check-maintenance-review.py
  backlog/codex-adapter.md`; `python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py`;
  `python3 adapters/codex/scripts/smoke-local-plugin.py`; `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; `python3
  adapters/codex/scripts/check-codex-cli-surface.py`; `python3
  scripts/sync-codex-plugin.py --check`.
- Expected scope: item 48 backlog evidence/status only unless a true live
  `init-codex-harness` invocation surface is available; fixture smoke and
  manually reading `SKILL.md` are not live skill execution evidence.

Attempted in 2026-05-04 single-session maintenance pass:

- Deterministic init project fixture smoke passed for TypeScript, Python, and
  migrated Claude-history fixtures.
- Local artifact smoke passed.
- Isolated local Codex CLI marketplace activation smoke passed.
- Local Codex CLI surface probe passed for `plugin marketplace` and
  `app-server` help markers.
- Current Codex runtime did not expose `init-codex-harness` as an active
  runtime skill, and no direct-copy `init-codex-harness` installation was found
  under the active `~/.codex/skills` or plugin cache skill roots.
- This pass did not run the local `SKILL.md` instructions manually as a
  substitute, because that would prove the agent can read repository docs, not
  that a live Codex session invoked the installed skill.

Completion Gate:

- Backlog status: `보류`; prerequisite evidence was refreshed, but the item is
  not accepted because live `init-codex-harness` execution evidence is
  unavailable in this session.
- Changed files: `backlog/codex-adapter.md`.
- Scope deviations: none for item 48. Unrelated dirty work remains
  intentionally unstaged in `backlog/README.md`, `backlog/core.md`, and
  pre-existing `backlog/codex-adapter.md` hunks outside item 48, including the
  top-level distribution-summary refresh.
- Verification results: PASS `python3 scripts/check-maintenance-review.py
  backlog/codex-adapter.md`; PASS `python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py`;
  PASS `python3 adapters/codex/scripts/smoke-local-plugin.py`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; PASS `python3
  adapters/codex/scripts/check-codex-cli-surface.py`; PASS `python3
  scripts/sync-codex-plugin.py --check`; SKIPPED live runtime invocation because
  the active runtime does not expose the skill.
- Search-set verification: SKIPPED because this pass made no accepted harness
  behavior or adapter contract change; it records that the required live-init
  runtime evidence is still absent.
- Multi-review required: yes for acceptance of a live-init runtime evidence
  packet; this pass will run multiple reviewers on the non-acceptance/blocked
  handoff record instead.
- Multi-review result: PASS for the blocked/non-acceptance handoff; no live-init
  runtime evidence packet was accepted.
- Reviewer scores and VETO handling: live-init evidence-boundary critic 9 PASS;
  blocked-item appropriateness critic 9 PASS; maintenance-process critic 8 VETO
  on pending multi-review closure fields. VETO handled by replacing the pending
  placeholders with concrete multi-review results, score-9 reasons, and backlog
  residual-risk disposition. Maintenance-process re-review remained 8 VETO
  because the rerun score was not yet recorded; this was fixed by recording the
  rerun-result issue in this field. Final maintenance-process re-review: 9 PASS,
  no blocking findings.
- For each score 9, why not 10: evidence-boundary critic was not 10 because the
  review bookkeeping fields were still pending at review time; blocked-item
  appropriateness critic was not 10 for the same pending-field reason. This was
  actionable within the item and fixed before handoff. Final maintenance-process
  re-review was not 10 because the Completion Gate still needed to record that
  final rerun result and staging still required precise hunk selection; the
  rerun result is recorded here, and staging will be checked before commit.
- Backlog items added from score-9 residual risk: none; the score-9 residual was
  resolved in this item by closing the review bookkeeping fields.
- Residual risk/follow-up: rerun this item only when the active Codex runtime
  can invoke `init-codex-harness` from the generated plugin or a direct-copy
  skill installation against an isolated target project, or when a
  product-supported noninteractive smoke exists for live skill execution.
- Accepted: no.

### 49. P2 automate target-project autoresearch protection install

Status: 재검토 필요
Archived: `backlog/archive/codex-adapter.md#49-p2-automate-target-project-autoresearch-protection-install`

Recheck reason: the installer implementation and fixture coverage are archived
as accepted, but the 2026-05-06 runtime/adoption review found that the
adopter-facing command path can still be interpreted as relative to the target
project. A normal target project usually will not have
`plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py`, so
item 51 should confirm the install entrypoint, path resolution, and direct-copy
fallback wording before this pointer returns to compact `Status: 완료`.

### 50. P3 add deeper installer protection fixture coverage

Status: 완료
Archived: `backlog/archive/codex-adapter.md#50-p3-add-deeper-installer-protection-fixture-coverage`

### 51. P2 clarify Codex plugin and autoresearch installer entrypoints for adopters

Status: 대기

Source review: 2026-05-06 multi-review of clean local `main` against the
Meta-Harness methodology.

The local plugin bundle is documented as the primary distribution artifact, and
item 49 added a repeatable target-project protection installer. The latest
runtime/adoption review still found an adopter UX gap: guidance in the Codex
README and autoresearch skill can read as if a target project can run
`python3 plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py
--target . --run-smoke` from its own root. That path exists in this repository
or an installed/generated plugin bundle, not in an arbitrary target project
unless the bundle has already been made available.

Potential improvement:

- Document a concrete local-plugin install or activation command flow for normal
  adopters, distinct from repository development smokes.
- Make autoresearch protection install examples explicit about the current
  working directory and source root: generated plugin bundle checkout,
  canonical adapter checkout, or installed plugin asset location.
- If direct skill copy is used, keep the existing degraded marker and state that
  protection assets are unavailable until copied from the plugin/adapter source.
- Add or adjust smoke/text-contract tests so target-project-relative examples do
  not imply nonexistent `plugins/...` paths.
- Sync generated plugin mirrors after changing canonical Codex adapter text.

Done when:

- A user starting in a target project can tell exactly where the installer script
  lives and what absolute or checkout-relative command to run.
- README, Codex autoresearch skill, and generated plugin copies agree on the
  install path and degraded direct-copy fallback.
- Item 49 can return to compact `Status: 완료` because the implementation and
  adopter-facing command surface no longer disagree.
