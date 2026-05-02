# Codex Adapter Backlog

Codex-specific backlog for adapter behavior that should not be pushed into the shared core. Core methodology follow-ups live in `backlog/core.md`.

## Priority Candidates

### 1. Add Codex sandbox/escalation recording template

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

### 3. Harden Codex hook enforcement templates

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

### 4. Implement the chosen Codex distribution path

Decision: use a **local Codex plugin bundle** as the primary distribution path.

Status of paths:

- Local plugin bundle: primary bundle target for normal local development and dogfooding; activation smoke test still pending.
- Direct skill copy: development fallback for fast skill text iteration only.
- Marketplace/plugin bundle: future release path after local plugin layout stabilizes.
- `skill-installer`: compatibility investigation for skill-only degraded installs.

Implemented foundation:

- `plugins/ai-agent-meta-harness/.codex-plugin/plugin.json` is generated from canonical adapter metadata.
- `scripts/sync-codex-plugin.py --write` materializes the local plugin bundle from `adapters/codex/`.
- `scripts/sync-codex-plugin.py --check` fails on missing, stale, extra, invalid, binary-different, or semantically empty required plugin surfaces.
- `.githooks/pre-commit` runs the plugin drift check alongside compatibility mirror checks.
- README install guidance now points to the generated local plugin bundle first, with direct skill copy as a degraded fallback.

Remaining follow-up work:

- Add a real local plugin install smoke test once the exact Codex local-plugin activation workflow is documented.
- Decide how the fallback direct-copy path reports missing hooks/checker assets at runtime.
- Keep README install instructions aligned as hook/checker assets are added to the plugin bundle.

### 5. Define Codex plugin bundle scope

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

### 11. Test Codex adapter on real project types

The Codex skills should be exercised on representative projects and refined from traces.

Potential improvement:

- Apply `init-codex-harness` to a TypeScript app.
- Apply it to a Python research repo.
- Apply it to an existing project with `.claude/traces/` history.
- Review the generated traces and search-set entries, then update skill docs based on observed failures.

### 12. Provide a Codex autoresearch protection checker reference implementation

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

Decision implemented: `plugins/ai-agent-meta-harness/` is the generated local plugin root, with `adapters/codex/` remaining canonical. `scripts/sync-codex-plugin.py` owns `--write` and `--check`, and pre-commit runs the check.

Remaining follow-up work:

- Add runtime hook config under `adapters/codex/hooks/` and manifest `hooks` only after local plugin activation and tool-event coverage are smoke-tested; template hook/pre-commit/CI/AGENTS mappings are already implemented.
- Add examples to the generated path mapping when Codex examples are introduced.
- Decide whether `.codex-plugin/plugin.json` should remain hand-authored canonical metadata or become generated from a smaller metadata source.
- Document and smoke-test the exact local plugin activation command before calling the plugin path fully installed.
- Revisit marketplace metadata only after the local plugin activation path is proven.

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

### 19. Add true Codex local plugin activation smoke test

The artifact smoke test proves the generated plugin bundle is internally coherent, but it does not prove Codex has loaded the plugin in a running session.

Potential improvement:

- Identify the exact local Codex plugin activation command or manifest registration path for the supported Codex surface.
- Add an automated smoke test that installs or activates `plugins/ai-agent-meta-harness/` in an isolated Codex home and verifies the expected skills are discoverable through Codex.
- Keep runtime hook manifest fields gated until activation and tool-event coverage are both smoke-tested.

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
