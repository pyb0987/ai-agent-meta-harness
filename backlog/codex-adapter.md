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

Remaining follow-up work:

- Add a fixture smoke test when init skill execution can be tested
  mechanically.
- Align the `autoresearch` skill's Setup Mode trace-root selection with the same
  meaningful-history rule. In particular, do not let an empty `.harness/traces/`
  outrank a `.claude/traces/` root that contains real prior failures, episodes,
  or Active search-set entries.

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

The marketplace path is future work, but plugin metadata choices can leak into local plugin structure if left implicit.

Potential improvement:

- Decide plugin name, display name, category, installation policy, and authentication policy.
- Keep marketplace metadata out of the local-only path unless needed for Codex UI ordering.
- Document when `.agents/plugins/marketplace.json` should be generated or updated.
- Avoid publishing-oriented metadata churn while the local plugin layout is still stabilizing.

### 18. Add local plugin artifact smoke test

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

Remaining follow-up work:

- Add the local plugin artifact smoke test to the formal release checklist when that checklist is introduced.

### 19. Add true Codex local plugin activation smoke test

The artifact smoke test proves the generated plugin bundle is internally coherent, but it does not prove Codex has loaded the plugin in a running session.

Potential improvement:

- Identify the exact local Codex plugin activation command or manifest registration path for the supported Codex surface.
- Add an automated smoke test that installs or activates `plugins/ai-agent-meta-harness/` in an isolated Codex home and verifies the expected skills are discoverable through Codex.
- Keep runtime hook manifest fields gated until activation and tool-event coverage are both smoke-tested.

## Current Status

- Source reviews: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md` and `adapters/codex/skills/autoresearch/SKILL.md`.
- Last reviewed baselines are the commits linked from the relevant review notes or release notes; avoid keeping a single stale baseline here.
- Core follow-ups have been moved to `backlog/core.md` to avoid duplicating methodology work across adapters.
