# Codex Plugin Bundle Scope

This document defines what belongs in the Codex plugin bundle and what remains
outside it. The shared harness methodology stays in `core/`; this bundle carries
only the Codex runtime adapter surfaces needed to apply that methodology.

## Scope Stages

| Stage | Bundle contents | Status |
|-------|-----------------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, CI template, target-project install docs, and local smoke commands | Implemented for copied target-project guardrails; runtime plugin hook delivery remains deferred until a product-supported smoke or reviewed manual gate exists |
| experimental orientation | Opt-in `SessionStart` context hook, exact-command mode tracker, example hook config, and subprocess smoke tests | Implemented as copied assets only; not advertised by the plugin manifest and not evidence of live runtime delivery |
| marketplace distribution | Repo marketplace metadata, schema validation, and ChatGPT desktop installation guidance | Implemented for the repository-local marketplace; public directory submission remains separate |
| Later release | Richer install validation and optional generated assets | Planned |

## Current Generated Contents

The generated plugin at `plugins/ai-agent-meta-harness/` currently includes:

- `.codex-plugin/plugin.json`
- `README.md`
- `hook-schema.md`
- `plugin-scope.md`
- `hooks/experimental/harness_orientation.py`
- `hooks/experimental/harness-orientation-hooks.json.example`
- `skills/autoresearch/SKILL.md`
- `skills/harness-engineer/SKILL.md`
- `skills/init-codex-harness/SKILL.md`
- `skills/init-codex-harness/assets/AGENTS.md.template`
- `skills/multi-review/SKILL.md`
- `templates/AGENTS.md.template`
- `templates/autoresearch-protected.txt`
- `templates/hooks/codex-hooks.json.template`
- `templates/hooks/pre-commit-autoresearch-protected.sh`
- `templates/hooks/github-actions-autoresearch-protected.yml`
- `templates/hooks/agents-autoresearch-protection.md`
- `examples/AGENTS.md.example`
- `scripts/check-autoresearch-protected.py`
- `scripts/check-codex-cli-surface.py`
- `scripts/check-codex-hook-schema-drift.py`
- `scripts/check-multi-review-result.py`
- `scripts/install-autoresearch-protection.py`
- `scripts/smoke-autoresearch-hooks.py`
- `scripts/smoke-init-codex-project-fixtures.py`
- `scripts/smoke-local-plugin-activation.py`
- `scripts/smoke-local-plugin.py`

The sync map recursively copies all files under the canonical `skills/`,
`templates/`, `scripts/`, `examples/`, and `hooks/` trees, while still requiring
the minimum supported assets listed here to exist. Future templates, scripts,
examples, or hooks must be added to this scope document before they are
considered supported bundle surface.

`adapters/codex/` remains the editable canonical source. Generated plugin files
must be updated with `python3 scripts/sync-codex-plugin.py --write` and checked
with `python3 scripts/sync-codex-plugin.py --check --worktree` during development.
The pre-commit hook omits `--worktree` so it checks exactly what is staged.

## Inclusion Rules

Include a file in the plugin bundle when all of these are true:

- It is Codex-specific adapter surface, not shared methodology.
- It is useful at install or project bootstrap time.
- It can be generated from `adapters/codex/` without manual dual-editing.
- Its safety behavior is either executable now or explicitly marked as a template.

Do not include:

- Core methodology copies from `core/`.
- Claude adapter files or Claude hook schemas.
- Project-specific traces, evaluator outputs, or local secrets.
- Public-directory submission metadata or claims that have not passed the release review.

## v1 Canonical Path Policy

| Asset class | Canonical source | Generated plugin path | Notes |
|-------------|------------------|-----------------------|-------|
| Codex hook templates | `adapters/codex/templates/hooks/codex-hooks.json.template` | `templates/hooks/codex-hooks.json.template` | Template-only guardrail; hard enforcement stays in pre-commit/CI until activation and tool-event delivery coverage are smoke-tested |
| Pre-commit template | `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` | `templates/hooks/pre-commit-autoresearch-protected.sh` | Hard local guardrail using the shared checker |
| CI template | `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml` | `templates/hooks/github-actions-autoresearch-protected.yml` | Pull-request guardrail using the shared checker |
| AGENTS reminder snippet | `adapters/codex/templates/hooks/agents-autoresearch-protection.md` | `templates/hooks/agents-autoresearch-protection.md` | Level 1 instruction layer for target projects |
| Experimental orientation hooks | `adapters/codex/hooks/experimental/` | `hooks/experimental/` | Opt-in `SessionStart` orientation and exact-command mode tracking; copied as assets only, not referenced from the plugin manifest |
| Runtime Codex hook config | `adapters/codex/hooks/` | `hooks/` plus manifest `hooks` field | Only after isolated local activation and Codex plugin tool-event delivery smoke tests pass |
| Autoresearch checker reference | `adapters/codex/scripts/check-autoresearch-protected.py` | `scripts/check-autoresearch-protected.py` | Shared by Codex hooks, pre-commit, and CI templates |
| Optional Codex CLI surface probe | `adapters/codex/scripts/check-codex-cli-surface.py` | `scripts/check-codex-cli-surface.py` | Checks local `codex plugin marketplace` and `codex app-server` help markers when Codex is installed; does not prove ChatGPT desktop model-visible skill surfacing or plugin tool-event delivery |
| Hook schema drift reference | `adapters/codex/hook-schema.md` | `hook-schema.md` | Records verified Codex hook output assumptions and official source URLs |
| Hook schema drift checker | `adapters/codex/scripts/check-codex-hook-schema-drift.py` | `scripts/check-codex-hook-schema-drift.py` | Fails when hook-sensitive staged changes omit schema re-verification |
| Multi-review governance validator | `adapters/codex/scripts/check-multi-review-result.py` | `scripts/check-multi-review-result.py` | Project-local validator copied only into projects that declare meta-harness governance acceptance; global multi-review remains advisory without it |
| Target-project protection installer | `adapters/codex/scripts/install-autoresearch-protection.py` | `scripts/install-autoresearch-protection.py` | Copies missing protection assets into adopting projects, appends safe local snippets, and reports merge-required hook or CI files without overwriting them |
| Hook smoke assertions | `adapters/codex/scripts/smoke-autoresearch-hooks.py` | `scripts/smoke-autoresearch-hooks.py` | Mechanically asserts Codex hook deny JSON shapes |
| Init project fixture smoke test | `adapters/codex/scripts/smoke-init-codex-project-fixtures.py` | `scripts/smoke-init-codex-project-fixtures.py` | Deterministic artifact/adoption check that runs generated Active search-set verifiers in fixture projects; does not prove live Codex model dogfooding |
| Local plugin artifact smoke test | `adapters/codex/scripts/smoke-local-plugin.py` | `scripts/smoke-local-plugin.py` | Verifies manifest, expected skills, protection assets, and degraded fallback warning |
| Local plugin activation smoke test | `adapters/codex/scripts/smoke-local-plugin-activation.py` | `scripts/smoke-local-plugin-activation.py` | Proves isolated CLI marketplace registration and enabled-plugin config shape; does not prove ChatGPT desktop model-visible skill surfacing or plugin tool-event delivery |
| Protected-path template | `adapters/codex/templates/autoresearch-protected.txt` | `templates/autoresearch-protected.txt` | Project bootstrap asset copied to `.harness/autoresearch-protected.txt` |
| Init skill project template asset | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` | `skills/init-codex-harness/assets/AGENTS.md.template` | Skill-local project template used by the init skill; top-level `templates/AGENTS.md.template` remains a compatibility/bootstrap template |
| Completed Codex example | `adapters/codex/examples/` | `examples/` | Onboarding reference; additional examples should come from real project dry runs |

## Manifest Rules

The manifest exposes only `skills` in v0 because the plugin currently ships
skills, static templates, and opt-in experimental hook assets. Add manifest
fields such as `hooks` only when the repo has an executable hook config under
`adapters/codex/hooks/` that is smoke-tested through both the isolated local
plugin activation path and a Codex plugin tool-event delivery path.
Template-only files under `templates/hooks/`, and experimental orientation files
under `hooks/experimental/`, should not be advertised as active runtime hooks.

Runtime delivery evidence remains distinct from packaging evidence. Local
evidence covers generated artifact integrity, repository marketplace metadata,
and isolated CLI activation/config shape. The local Codex CLI exposes plugin
marketplace management and app-server protocol tooling; the
optional CLI surface probe can mechanically confirm those help markers when a
local Codex CLI is installed. That probe is not runtime delivery evidence and
does not prove ChatGPT desktop model-visible skill surfacing or plugin hook event
delivery. Runtime hook manifest fields must remain absent until a
product-supported smoke or explicitly reviewed manual gate covers that third
evidence level.

An explicitly reviewed manual gate may substitute for an automated runtime
delivery smoke only when it records a concrete evidence packet: Codex app or
runtime version, surface name, OS, plugin source path, passing local artifact and
activation smokes, CLI surface probe result or skipped reason, and a fresh
session transcript, screenshot, or exported runtime trace showing the generated
`ai-agent-meta-harness` plugin surfaced the expected skills to the running
model. Manifest `hooks` fields still require separate evidence that a plugin
hook received a real tool event from that runtime surface and that Codex
accepted the hook output. CLI help probes and isolated activation smokes are
prerequisites, not substitutes, for this manual runtime delivery evidence.

## Marketplace Metadata Policy

Marketplace publication ready: yes, for this repository-local marketplace.
Public Plugins Directory submission remains a separate release decision.

- Official marketplace schema: https://learn.chatgpt.com/docs/build-plugins
- Official marketplace taxonomy: the local schema requires a non-empty category; this repository uses the documented `Productivity` example category.
- Generated metadata source: `.agents/plugins/marketplace.json`, created with the Codex `plugin-creator` marketplace helper and validated against the canonical plugin bundle.

The repository marketplace entry uses these stable values:

- Package name: `ai-agent-meta-harness`
- Source: `local` at `./plugins/ai-agent-meta-harness`
- Category: `Productivity`
- Installation policy: `AVAILABLE`
- Authentication policy: `ON_INSTALL`; the plugin has no external app authentication today, but the field is required by the marketplace contract.

The ChatGPT desktop app reads repo marketplaces from
`.agents/plugins/marketplace.json`. After installation or a plugin update,
start a new task so newly bundled skills and tools are loaded. Keep the
marketplace entry generated through the plugin-creator workflow; do not maintain
a second hand-authored plugin source path.

Run `python3 scripts/check-codex-marketplace-metadata.py --worktree` during
development and the command without `--worktree` in staged/pre-commit mode. The
checker validates the marketplace root, install policy, category, local source
path, and plugin manifest identity. It does not claim public-directory approval
or live model-visible delivery.

## Methodology Boundary

Meta-Harness paper principles are acceptance criteria here, not duplicated
content. For this bundle, that means:

- Raw traces remain project files, not plugin state.
- Immutable evaluator protection uses a shared checker plus structural templates in v1.
- Enforcement assets should be shared by hooks, pre-commit, and CI where possible.
- Scope should grow additively: ship v0, add v1 protection assets, then add release metadata.
