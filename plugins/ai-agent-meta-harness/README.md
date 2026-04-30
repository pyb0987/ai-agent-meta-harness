# Codex Adapter

Codex support is an adapter over the shared harness core, not a fork of the methodology.

## Current Scope

The first Codex adapter layer provides:

- `init-codex-harness` skill for project bootstrap
- `harness-engineer` skill for Codex harness evolution
- `autoresearch` skill for measurable autonomous experiment loops
- `AGENTS.md` template for project-local instructions
- Trace filesystem guidance using `.harness/traces/` by default
- Codex hook enforcement strategy plus explicit verify-command discipline in place of Claude Code hook assumptions

## Design Choices

- Shared principles stay in `core/methodology.md` and `core/reference.md`.
- Codex-specific behavior lives here: skill trigger wording, project instruction filenames, verification workflow, and sub-agent usage.
- Claude Code hook schemas are not copied into Codex. Codex enforcement should use Codex hooks where available, backed by CI, git hooks, and project-local scripts for hard enforcement.
- Non-blocking adapter follow-up work is tracked in `backlog/codex-adapter.md`; shared methodology follow-ups live in `backlog/core.md`.

## Distribution Decision

Primary distribution path: **local Codex plugin bundle**.

Rationale: the Codex adapter now includes more than standalone skill text. Autoresearch protection needs hooks, checker scripts, templates, and examples to travel together. A plugin bundle is the smallest distribution unit that can carry those assets without turning the adapter into a fork of the core methodology.

Source-of-truth rule: `adapters/codex/` is the canonical editable Codex adapter source. The local plugin bundle will be generated from it; manual dual-editing between adapter files and plugin files is not allowed.

Plugin layout decision:

- Plugin root: `plugins/ai-agent-meta-harness/`
- Canonical source: `adapters/codex/`
- Generated output: `plugins/ai-agent-meta-harness/`
- Sync command: `python3 scripts/sync-codex-plugin.py --write`
- Drift check: pre-commit/release checks must verify generated plugin files match canonical adapter files

Supported paths:

| Path | Status | Use |
|------|--------|-----|
| Local plugin bundle | Primary bundle artifact, scaffolded | Generated at `plugins/ai-agent-meta-harness/`; activation smoke test still pending |
| Direct skill copy | Development fallback | Fast iteration on skill text only |
| Marketplace/plugin bundle | Future release path | Published distribution after plugin layout stabilizes |
| `skill-installer` | Compatibility investigation | Skill-only install if safe degraded behavior is documented |

## Bundle Scope

The bundle scope is staged so packaging does not outrun tested behavior. Full details live in `plugin-scope.md`.

| Stage | Includes | Status |
|-------|----------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, and CI template implemented; install docs planned | Partial |
| Later release | Examples, marketplace metadata, richer install validation | Planned |

The Meta-Harness paper informs the acceptance criteria for this scope, but its methodology remains in `core/`; the plugin should not copy core content into a Codex-specific fork.

## Autoresearch Protection Assets

The generated plugin now carries a reference checker at `scripts/check-autoresearch-protected.py`, hook JSON smoke assertions at `scripts/smoke-autoresearch-hooks.py`, a protected-path template at `templates/autoresearch-protected.txt`, and enforcement templates plus an AGENTS reminder snippet under `templates/hooks/`. These are project assets to copy during autoresearch setup; they are not advertised as active plugin runtime hooks until local activation smoke tests exist.

Hook schema drift is tracked in `hook-schema.md`. Before changing Codex hook templates, checker hook output, or autoresearch hook instructions, re-check the official Codex hooks documentation and run `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`.

## Sub-Agent Capability Matrix

Codex sub-agent support is surface-dependent. Treat sub-agents as an optional
tactical mechanism, not a required persistence model.

| Surface | Sub-agent expectation | Harness behavior |
|---------|-----------------------|------------------|
| Codex Desktop | Available when the runtime exposes `spawn_agent`/worker/explorer tools | Use for independent exploration, multi-review, and sidecar implementation only when tasks can run in parallel |
| Codex CLI | May be unavailable or policy-limited depending on release and invocation | Fall back to a sequential review checklist and fixed evaluator scripts for independence |
| Codex API | Do not assume sub-agent orchestration unless the caller provides it | Keep evaluator independence in deterministic scripts or caller-managed review passes |
| Local plugin bundle | Carries skills/assets, not guaranteed sub-agent activation | Skills must describe fallback behavior instead of requiring sub-agents |

Fallback rules:

- For multi-review without sub-agents, run independent checklist passes
  sequentially and record the loss of independence as residual risk.
- For evaluator independence without sub-agents, prefer fixed evaluator scripts
  with immutable boundaries.
- For explorer/evaluator patterns without sub-agents, keep the work in the
  parent context only if contamination risk is low; otherwise stop and request a
  runtime surface that supports the needed isolation.

## Tool-Use Policy

Prefer repo-local evidence and CLI commands for harness diagnosis. Use richer
tools only when they expose information the filesystem cannot.

| Surface | Use when | Notes |
|---------|----------|-------|
| Shell/CLI | Reading files, running tests, inspecting Git, validating generated artifacts | Default path for repo-local harness work |
| MCP resources | The runtime exposes project or external-system context more directly than files/CLI | Prefer resources over web search when they are authoritative for the local task |
| `tool_search` | The active Codex surface exposes tool discovery and a needed MCP/app tool is not already visible | Search for automation, browser, or plugin-specific tools before inventing a workaround |
| Browser plugin | Inspecting local browser targets such as localhost or file previews | Use for local UI/runtime verification, not as a replacement for repo checks |
| Web search | Live external state, official docs, standards, or source-backed current facts are required | Cite sources and prefer primary/official sources |

When a tool cannot run because of sandbox, permissions, network, missing
dependencies, or product-surface limits, record the limitation as a verification
outcome and include the command or action that should be retried later.

## Local Development Install

Generate and verify the repo-local plugin bundle before artifact-level dogfooding:

```bash
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py --skip-staged-policy
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
```

The generated plugin lives at `plugins/ai-agent-meta-harness/`. The smoke test validates the bundle artifact: manifest, expected skills, checker/hook/template assets, and degraded fallback warnings. The exact Codex local-plugin activation command is intentionally not documented here until Codex activation can be exercised mechanically; track that in `backlog/codex-adapter.md`.

Until the activation workflow is validated, use the degraded direct-copy fallback for executable local skill iteration:

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
```

This fallback does not install Codex hooks, checker scripts, templates outside bundled skill assets, or plugin metadata. Do not treat it as the full autoresearch safety path.

Then ask Codex:

```text
apply codex-harness to this project
```
