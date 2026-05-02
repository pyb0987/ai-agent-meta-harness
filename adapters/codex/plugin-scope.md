# Codex Plugin Bundle Scope

This document defines what belongs in the Codex plugin bundle and what remains
outside it. The shared harness methodology stays in `core/`; this bundle carries
only the Codex runtime adapter surfaces needed to apply that methodology.

## Scope Stages

| Stage | Bundle contents | Status |
|-------|-----------------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, and CI template implemented; install docs planned | Partial |
| Later release | Examples, marketplace metadata, richer install validation, optional generated assets | Planned |

## Current Generated Contents

The generated plugin at `plugins/ai-agent-meta-harness/` currently includes:

- `.codex-plugin/plugin.json`
- `README.md`
- `hook-schema.md`
- `plugin-scope.md`
- `skills/autoresearch/SKILL.md`
- `skills/harness-engineer/SKILL.md`
- `skills/init-codex-harness/SKILL.md`
- `skills/multi-review/SKILL.md`
- `templates/AGENTS.md.template`
- `templates/autoresearch-protected.txt`
- `templates/hooks/codex-hooks.json.template`
- `templates/hooks/pre-commit-autoresearch-protected.sh`
- `templates/hooks/github-actions-autoresearch-protected.yml`
- `templates/hooks/agents-autoresearch-protection.md`
- `examples/AGENTS.md.example`
- `scripts/check-autoresearch-protected.py`
- `scripts/check-codex-hook-schema-drift.py`
- `scripts/smoke-autoresearch-hooks.py`
- `scripts/smoke-local-plugin.py`

The sync map recursively copies all files under the canonical `skills/`,
`templates/`, `scripts/`, and `examples/` trees, while still requiring the
minimum v1 assets listed here to exist. Future templates, scripts, or examples
must be added to this scope document before they are considered supported bundle
surface.

`adapters/codex/` remains the editable canonical source. Generated plugin files
must be updated with `python3 scripts/sync-codex-plugin.py --write` and checked
with `python3 scripts/sync-codex-plugin.py --check`.

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
- Marketplace metadata until local activation is smoke-tested.

## v1 Canonical Path Policy

| Asset class | Canonical source | Generated plugin path | Notes |
|-------------|------------------|-----------------------|-------|
| Codex hook templates | `adapters/codex/templates/hooks/codex-hooks.json.template` | `templates/hooks/codex-hooks.json.template` | Template-only guardrail; hard enforcement stays in pre-commit/CI until activation and tool-event delivery coverage are smoke-tested |
| Pre-commit template | `adapters/codex/templates/hooks/pre-commit-autoresearch-protected.sh` | `templates/hooks/pre-commit-autoresearch-protected.sh` | Hard local guardrail using the shared checker |
| CI template | `adapters/codex/templates/hooks/github-actions-autoresearch-protected.yml` | `templates/hooks/github-actions-autoresearch-protected.yml` | Pull-request guardrail using the shared checker |
| AGENTS reminder snippet | `adapters/codex/templates/hooks/agents-autoresearch-protection.md` | `templates/hooks/agents-autoresearch-protection.md` | Level 1 instruction layer for target projects |
| Runtime Codex hook config | `adapters/codex/hooks/` | `hooks/` plus manifest `hooks` field | Only after isolated local activation and Codex plugin tool-event delivery smoke tests pass |
| Autoresearch checker reference | `adapters/codex/scripts/check-autoresearch-protected.py` | `scripts/check-autoresearch-protected.py` | Shared by Codex hooks, pre-commit, and CI templates |
| Hook schema drift reference | `adapters/codex/hook-schema.md` | `hook-schema.md` | Records verified Codex hook output assumptions and official source URLs |
| Hook schema drift checker | `adapters/codex/scripts/check-codex-hook-schema-drift.py` | `scripts/check-codex-hook-schema-drift.py` | Fails when hook-sensitive staged changes omit schema re-verification |
| Hook smoke assertions | `adapters/codex/scripts/smoke-autoresearch-hooks.py` | `scripts/smoke-autoresearch-hooks.py` | Mechanically asserts Codex hook deny JSON shapes |
| Local plugin artifact smoke test | `adapters/codex/scripts/smoke-local-plugin.py` | `scripts/smoke-local-plugin.py` | Verifies manifest, expected skills, protection assets, and degraded fallback warning |
| Protected-path template | `adapters/codex/templates/autoresearch-protected.txt` | `templates/autoresearch-protected.txt` | Project bootstrap asset copied to `.harness/autoresearch-protected.txt` |
| Completed Codex example | `adapters/codex/examples/` | `examples/` | Onboarding reference; additional examples should come from real project dry runs |

## Manifest Rules

The manifest exposes only `skills` in v0 because the plugin currently ships
skills and static templates. Add manifest fields such as `hooks` only when the
repo has an executable hook config under `adapters/codex/hooks/` that is
smoke-tested through both the isolated local plugin activation path and a Codex
plugin tool-event delivery path. Template-only files under `templates/hooks/`
should not be advertised as active runtime hooks.

## Marketplace Metadata Policy

Marketplace metadata is a release surface, not part of the local-only dogfood
path. Keep `.codex-plugin/plugin.json` limited to metadata required for local
plugin loading until local activation, install, and hook-event coverage have
mechanical smoke tests.

Official source check (2026-05-03): public OpenAI Codex help/release-note pages
describe plugins and a curated plugins directory, but this repository has not
found a published canonical marketplace metadata schema or category taxonomy to
validate against. Keep the category below provisional until an official schema
or taxonomy is cited in this document.

Use these stable identity values when a marketplace path is introduced:

- Package name: `ai-agent-meta-harness`
- Display name: `AI Agent Meta-Harness`
- Category: developer tools / agent harnessing
- Installation policy: local-plugin first until a release checklist explicitly
  accepts marketplace publication
- Authentication policy: no external authentication required unless a future
  runtime surface adds a documented need

Do not generate or update `.agents/plugins/marketplace.json` for normal local
plugin development. Add that file only when all of these are true:

- Codex local plugin activation has an automated smoke test.
- Marketplace installation behavior is documented for the supported Codex
  surface.
- The release checklist includes marketplace metadata validation.
- Any published metadata can be generated from canonical adapter files without
  manual dual-editing.

If Codex UI ordering eventually needs local marketplace-like metadata before
publication, keep it explicitly local-only and smoke-test that it does not
change plugin activation, skill discovery, or hook registration semantics.

Run `python3 scripts/check-codex-marketplace-metadata.py` before any publication
prep. In the current deferred state, it passes only when no publication manifest
exists. If marketplace metadata appears before the readiness conditions above
are documented, the check fails instead of guessing a taxonomy or allowing
manual dual-edited metadata to become a release surface.

## Methodology Boundary

Meta-Harness paper principles are acceptance criteria here, not duplicated
content. For this bundle, that means:

- Raw traces remain project files, not plugin state.
- Immutable evaluator protection uses a shared checker plus structural templates in v1.
- Enforcement assets should be shared by hooks, pre-commit, and CI where possible.
- Scope should grow additively: ship v0, add v1 protection assets, then add release metadata.
