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
| Local plugin bundle | Primary bundle artifact with isolated activation smoke | Generated at `plugins/ai-agent-meta-harness/`; activation smoke registers a temp local marketplace and enables the plugin in an isolated `CODEX_HOME` |
| Direct skill copy | Development fallback | Fast iteration on skill text only |
| Marketplace/plugin bundle | Future release path | Published distribution after plugin layout stabilizes |
| `skill-installer` | Compatibility investigation | Skill-only install if safe degraded behavior is documented |

## Bundle Scope

The bundle scope is staged so packaging does not outrun tested behavior. Full details live in `plugin-scope.md`.

| Stage | Includes | Status |
|-------|----------|--------|
| v0 scaffold | Skills, AGENTS template, README, plugin manifest, scope document | Implemented |
| v1 protection | Checker, hook smoke assertions, protected-path template, AGENTS reminder snippet, Codex hook template, pre-commit template, CI template, target-project install docs, and local smoke commands | Implemented for copied target-project guardrails; runtime plugin hook delivery remains deferred until a product-supported smoke or reviewed manual gate exists |
| Later release | Examples, marketplace metadata, richer install validation | Planned |

The Meta-Harness paper informs the acceptance criteria for this scope, but its methodology remains in `core/`; the plugin should not copy core content into a Codex-specific fork.

## Autoresearch Protection Assets

The generated plugin now carries a reference checker at `scripts/check-autoresearch-protected.py`, hook JSON smoke assertions at `scripts/smoke-autoresearch-hooks.py`, a protected-path template at `templates/autoresearch-protected.txt`, and enforcement templates plus an AGENTS reminder snippet under `templates/hooks/`. These are project assets to copy during autoresearch setup; they are not advertised as active plugin runtime hooks until both isolated local activation and Codex plugin tool-event delivery are smoke-tested.

Hook schema drift is tracked in `hook-schema.md`. Before changing Codex hook templates, checker hook output, or autoresearch hook instructions, re-check the official Codex hooks documentation and run `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`.

### Target-Project Protection Install

When a project adopts autoresearch, copy the protection assets from the
generated plugin bundle, or from `adapters/codex/` while developing this repo,
into the target project:

| Source in plugin bundle | Target project path | Purpose |
|-------------------------|---------------------|---------|
| `scripts/check-autoresearch-protected.py` | `scripts/check-autoresearch-protected.py` | Shared checker used by Codex hooks, pre-commit, and CI |
| `scripts/smoke-autoresearch-hooks.py` | `scripts/smoke-autoresearch-hooks.py` | Local smoke assertion for Codex hook deny JSON |
| `templates/autoresearch-protected.txt` | `.harness/autoresearch-protected.txt` | Protected evaluator or benchmark path list |
| `templates/hooks/codex-hooks.json.template` | `.codex/hooks.json` or the active Codex hook config layer | Codex hook config template for project-local experimentation |
| `templates/hooks/pre-commit-autoresearch-protected.sh` | `.githooks/pre-commit-autoresearch-protected.sh` | Local Git hard-block guardrail |
| `templates/hooks/github-actions-autoresearch-protected.yml` | `.github/workflows/autoresearch-protected.yml` | Pull-request CI guardrail |
| `templates/hooks/agents-autoresearch-protection.md` | A project `AGENTS.md` autoresearch protection section | Instruction-level reminder layer |

After copying, make the scripts executable if the target filesystem did not
preserve modes, wire the pre-commit wrapper from the project's tracked hook, and
run:

```bash
python3 scripts/smoke-autoresearch-hooks.py --checker scripts/check-autoresearch-protected.py --protected-file .harness/autoresearch-protected.txt
```

This proves the copied checker still emits the expected Codex hook deny shapes.
It does not prove that Codex has registered plugin runtime hooks. Runtime hook
registration remains gated on local plugin activation and tool-event coverage.

### CI Base Reference Outside GitHub Actions

The CI checker compares changed paths between `HEAD` and a merge base. It picks
the comparison base in this order:

1. `--base-ref <ref>` command-line argument.
2. `BASE_REF` environment variable.
3. `GITHUB_BASE_REF` environment variable.
4. `origin/main`.

Values such as `main` or `release/next` are expanded to `origin/main` or
`origin/release/next`. Values already starting with `origin/` or `refs/` are
used as provided. CI jobs must fetch the selected base ref before running the
checker.

Non-GitHub CI jobs can use either environment or CLI form:

```bash
git fetch origin main
BASE_REF=main python3 scripts/check-autoresearch-protected.py --ci
```

```bash
git fetch origin release/next
python3 scripts/check-autoresearch-protected.py --ci --base-ref origin/release/next
```

If your CI exposes a target branch variable, map it to `BASE_REF` before
running the checker. For example, a generic merge-request job can run:

```bash
git fetch origin "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
BASE_REF="$CI_MERGE_REQUEST_TARGET_BRANCH_NAME" python3 scripts/check-autoresearch-protected.py --ci
```

The job should fail closed if the fetch fails or the base ref cannot be resolved.
That means the checker could not prove protected evaluator paths stayed
unchanged.

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
python3 adapters/codex/scripts/smoke-init-codex-project-fixtures.py
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 adapters/codex/scripts/smoke-local-plugin-activation.py
python3 adapters/codex/scripts/check-codex-cli-surface.py
```

The generated plugin lives at `plugins/ai-agent-meta-harness/`. The artifact smoke test validates the bundle artifact: manifest, expected skills, checker/hook/template assets, and degraded fallback warnings.

The init project fixture smoke creates representative TypeScript, Python, and
migrated-Claude-history project fixtures and validates the expected
`init-codex-harness` contract: trace-root selection, Active executable
search-set verifier, AGENTS.md harness policy, initial evolution trace, and no
Claude-only hook assumptions. It also runs each generated Active
`search-set.md` verify command inside the fixture project, so masked exit
statuses, missing command dependencies, and non-running verifier text fail the
smoke. It does not run a live Codex model against an external project or prove
Codex Desktop skill surfacing.

The activation smoke test creates an isolated `CODEX_HOME`, creates a temporary local marketplace that points at a copy of the generated plugin, runs `codex plugin marketplace add <marketplace-root>`, enables `[plugins."ai-agent-meta-harness@local-ai-agent-meta-harness"]`, and verifies the activated marketplace copy still exposes the expected skill files. This proves the local CLI marketplace registration path and enabled-plugin config shape, but it does not prove a running Codex Desktop session has surfaced those skills to the model or delivered plugin runtime hook events.

### Runtime Delivery Evidence Status

Runtime delivery has three evidence levels:

1. Generated artifact integrity: `python3 adapters/codex/scripts/smoke-local-plugin.py`.
2. Isolated CLI activation/config: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`.
3. Runtime model-visible skill surfacing or plugin hook delivery: no stable noninteractive smoke exists in this repo yet.

As of the 2026-05-04 maintenance pass, the local Codex CLI exposes plugin marketplace management (`codex plugin marketplace add|upgrade|remove`) and experimental app-server protocol tooling. `python3 adapters/codex/scripts/check-codex-cli-surface.py` optionally probes that local CLI help surface when `codex` is installed and skips when it is absent; use `--require-installed` when a local environment must fail instead of skip. This probe does not assert that a running Desktop session surfaced plugin skills to the model or delivered plugin runtime hook events. Keep runtime hook manifest fields disabled until that level has a product-supported smoke or explicitly reviewed manual gate.

For executable local skill iteration without plugin registration, use the degraded direct-copy fallback:

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
```

This fallback does not install Codex hooks, checker scripts, templates outside bundled skill assets, or plugin metadata. Do not treat it as the full autoresearch safety path.

When a skill-only direct-copy install reaches autoresearch setup and cannot
read the bundled protection assets, it must report
`DEGRADED_DIRECT_COPY_PROTECTION`, list the missing checker, smoke, protected
path, hook, pre-commit, CI, and AGENTS reminder assets, and keep
`Protection level: incomplete`. It must not claim Codex hooks, checker scripts,
pre-commit, or CI protection were installed until those assets are copied from
the generated plugin bundle and smoke-tested.

Then ask Codex:

```text
apply codex-harness to this project
```
