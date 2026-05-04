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
