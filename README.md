# AI Agent Meta-Harness

A practical framework for maintaining trace-backed AI-assisted development environments across coding agents, inspired by the [Meta-Harness](https://arxiv.org/abs/2603.28052) paper (Lee et al., Stanford 2026).

The Meta-Harness paper frames harness design as a major factor in agent performance, and its introduction cites prior harness-sensitivity evidence that changing only the harness can produce a 6x performance gap on the same benchmark. This project operationalizes Meta-Harness paper principles into a practical harness toolkit, runtime adapters, and verification gates. It combines published findings with repository-local engineering practices and checks for documentation, adapters, generated assets, and self-application traces, but it does not claim a local reproduction of the paper's end-to-end benchmark gains.

The repository is split into a shared core plus thin runtime adapters. The methodology should be edited once in `core/`; Claude Code and Codex integration details live under `adapters/`.

The current active roadmap is the **AI Agent Meta-Harness v2** transition in
`backlog/v2-roadmap.md`. The previous human-authored gate/backlog model is
frozen as v1 historical evidence under `archive/v1/`.

## What's Inside

| Component | Description | Path |
|-----------|-------------|------|
| **Core methodology** | Runtime-neutral principles and trace formats | `core/` |
| **Claude adapter** | Claude Code commands, skills, examples, hooks guidance | `adapters/claude/` |
| **Codex adapter** | Codex skills and project instruction templates | `adapters/codex/` |
| **Backlog** | Active v2 transition roadmap | `backlog/` |
| **v1 archive** | Frozen v1 backlog, review, and maintenance evidence | `archive/v1/` |
| **Maintenance plan** | Repository upkeep, tests, release checks, review policy | `MAINTENANCE.md` |

## Core Principles

This repository separates paper-backed experimental findings from engineering
guidance inferred while applying the methodology to Claude Code, Codex, and
project-local harnesses. The strongest claims below cite the Meta-Harness paper
or its ablations directly; adapter and skill guidance should be read as
repository practice unless a paper source is named.

Evidence categories used in this repository:

| Category | What It Means Here | Local Evidence |
|----------|--------------------|----------------|
| Paper results and benchmark claims | Published Meta-Harness findings, such as benchmark deltas, ablations, tables, and appendix observations | Cited as paper context only; not local reproduction evidence |
| Repository methodology and documentation correctness | This repository's interpretation of runtime-neutral harness principles, trace formats, and claim boundaries | `core/`, `docs/`, README boundary tests, compatibility mirror checks, and multi-review records |
| Adapter and generated-artifact operability | Claude/Codex adapter instructions, hook templates, generated plugin assets, and smoke-tested local workflows | Adapter unit tests, drift checks, plugin sync checks, hook smoke tests, and local activation smoke |
| Repository self-application evidence | This repository applying its own maintenance loop and preserving regression memory | v2 target: AcceptancePacket artifacts, packet-linked traces, and checker-computed eligibility; v1 archive evidence: `.harness/traces/search-set.md`, `.harness/traces/evolution/`, backlog Completion Gates, and Active search-set verification |

Paper claim traceability:

| README Claim | Paper Location | Local Status |
|--------------|----------------|--------------|
| Changing only the harness can produce a 6x performance gap on the same benchmark | Paper Introduction, citing prior harness sensitivity evidence | Paper context only; not locally reproduced here |
| Meta-Harness improves online text classification by 7.7 points while using 4x fewer context tokens | Paper Abstract and Section 4.1 comparison against ACE | Paper result only; this repo tests documentation, adapters, generated assets, and self-application traces |
| Full traces outperform summaries in the online text-classification ablation | Paper Table 3: scores-only, scores-plus-summary, and full-interface comparison | Paper result used to motivate this repo's trace discipline; local evidence is search-set and trace-root verification |
| Meta-Harness searches over harness code with source, scores, and execution traces available through the filesystem | Paper Abstract and system design description of the agentic proposer/filesystem interface | Paper-backed design principle adapted into this repo's code-space search and trace-root conventions |
| The outer loop proposes, evaluates, and logs candidates rather than adding persistent multi-agent orchestration | Paper system design: agentic proposer plus evaluator plus filesystem trace history | Repository-calibrated workflow rule; verified here through maintenance gates and review records, not benchmark reproduction |
| Additive modification and confounding-variable isolation are safer change strategies | Paper Appendix A/A.2 qualitative search trajectory and discussion | Repository methodology rule; enforced through maintenance workflow and backlog review records, not a local benchmark reproduction |
| Skill text quality is a high-leverage implementation detail | Paper Appendix D practical implementation tips | Paper engineering lesson adapted into repository skill-writing guidance |

- **Raw traces over summaries** — Paper-backed: full trace access achieved 56.7% accuracy vs 38.7% with summaries (Table 3). Repository practice: agents diagnose failures by reading raw execution logs via `grep` and `cat`, not by ingesting compressed summaries. Trace files use YAML frontmatter for programmatic querying — `grep -l 'verdict: regressed' traces/evolution/` instantly filters regression cases.
- **Additive modification** — Paper-backed: 6 consecutive iterations regressed when modifying control flow or prompts (Appendix A.2). Iteration 7 won by adding information (environment bootstrap) without touching existing logic. Repository practice: prefer adding evidence or guardrails before restructuring.
- **Code-space search** — Paper-backed by the Meta-Harness proposer/filesystem design: agents explore by modifying isolated, diffable, executable search surfaces such as source, configuration, prompt templates, or generated candidates that are evaluated by the same verifier. Repository-calibrated rule: "try harder" is noise; a 3-line config or prompt-construction change with a fixed evaluator is search.
- **Minimal outer loop** — Paper-backed by the system's propose -> evaluate -> log loop over candidate harnesses. Repository-calibrated rule: avoid orchestration that makes the harness harder to verify by inspection.
- **Skill document quality as highest leverage** — Paper-backed: "Iterating on the skill text had a larger effect on search quality than changing iteration count or population size" (Appendix D). Repository practice: define goals and prohibitions; leave diagnosis free.
- **Confounding variable isolation** — Paper-backed: prompt changes were confounded with structural fixes (Appendix A.2, iteration 3), leading to misattributed regressions. Repository practice: keep one functional change per iteration.

## Repository Layout

```text
core/
├── methodology.md          # Runtime-neutral principles
└── reference.md            # Trace formats and analysis workflow
backlog/
├── README.md               # Active v2 planning guide
└── v2-roadmap.md           # v2 transition roadmap and meta-plan
archive/v1/
├── README.md               # v1 archive index
├── IMPORT.md               # initial import manifest and hash record
├── MAINTENANCE.md          # v1 maintenance policy snapshot
└── backlog/                # Frozen v1 backlog and review records
adapters/
├── claude/
│   ├── commands/
│   ├── examples/
│   └── skills/
└── codex/
    ├── skills/
    └── templates/
```

## Claude Code Adapter

### Global setup

```bash
# Clone the repo
git clone https://github.com/pyb0987/ai-agent-meta-harness.git
cd ai-agent-meta-harness

# Copy core docs (loaded every session)
mkdir -p ~/.claude/rules/common
cp core/methodology.md ~/.claude/rules/common/harness-methodology.md

# Copy reference docs (loaded on demand)
mkdir -p ~/.claude/docs
cp core/reference.md ~/.claude/docs/harness-reference.md

# Copy skills (autoresearch + harness-engineer + multi-review)
# multi-review is a global dependency consumed from ~/.claude/skills/multi-review/
mkdir -p ~/.claude/skills
cp -r adapters/claude/skills/* ~/.claude/skills/

# Copy commands
mkdir -p ~/.claude/commands
cp adapters/claude/commands/init-harness.md ~/.claude/commands/
```

### Per-project setup

Run the bootstrap command in any project:

```text
> /init-harness
```

This analyzes your project and generates:

```text
your-project/
├── .claude/
│   ├── traces/
│   │   ├── evolution/            # Harness change history
│   │   ├── failures/             # Failure diagnosis records
│   │   ├── experiments/          # Autoresearch episodes
│   │   └── search-set.md         # Verification test cases
│   ├── hooks/                    # Project-specific hook scripts
│   ├── settings.local.json        # Hook configuration
│   └── skills/                   # Domain-specific skills (if needed)
├── CLAUDE.md                     # Project instructions
```

## Codex Adapter

Codex support is intentionally an adapter, not a fork. Shared methodology stays in `core/`; Codex-specific skills describe how Codex should apply it using `AGENTS.md`, `.harness/traces/` by default, existing `.claude/traces/` only when it contains meaningful history, terminal verification, and optional Codex sub-agents when the active surface supports them.

Initial Codex adapter contents:

| Component | Path |
|-----------|------|
| Bootstrap skill | `adapters/codex/skills/init-codex-harness/SKILL.md` |
| Project instruction template | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` |
| Harness-engineer skill | `adapters/codex/skills/harness-engineer/SKILL.md` |
| Autoresearch skill | `adapters/codex/skills/autoresearch/SKILL.md` |
| Multi-review skill | `adapters/codex/skills/multi-review/SKILL.md` |
| Local plugin bundle | `plugins/ai-agent-meta-harness/` |

Suggested local plugin workflow while developing the adapter:

```bash
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py --skip-staged-policy
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 adapters/codex/scripts/smoke-local-plugin-activation.py
```

The generated plugin bundle lives at `plugins/ai-agent-meta-harness/`. The local smoke test validates the plugin artifact. The activation smoke creates an isolated `CODEX_HOME`, registers a temporary local marketplace, enables the generated plugin, and verifies the activated marketplace copy exposes the expected skills. This proves local CLI marketplace registration and enabled-plugin config shape; it does not prove a running Codex Desktop session has surfaced those skills to the model or delivered plugin runtime hook events. Direct skill copy remains the executable degraded fallback for fast skill text iteration:

```bash
mkdir -p ~/.codex/skills
cp -r adapters/codex/skills/* ~/.codex/skills/
```

Use the skill by asking Codex to "init codex harness" or "apply codex-harness to this project". Use Codex multi-review by asking for a multi-perspective review.

Codex does not consume Claude Code slash commands or `.claude/settings.local.json` hooks. The adapter therefore starts with explicit verify commands and trace discipline; stronger enforcement should be added through Codex plugins, CI, git hooks, or project-local scripts where appropriate.

## Migration Notes

Top-level `docs/`, `commands/`, and `skills/` paths are retained as temporary compatibility mirrors for one transition period. Old install commands continue to install working Claude Code assets, but new work should edit `core/` and `adapters/`; mirror files are only there to protect existing bookmarks, scripts, and user muscle memory. `MAINTENANCE.md` owns the mirror removal lifecycle: announce one transition window, keep drift checks until removal, and migrate users to `core/` plus `adapters/claude/`.

Compatibility mirror mapping:

| Old path | New source of truth |
|----------|---------------------|
| `docs/methodology.md` | `core/methodology.md` |
| `docs/reference.md` | `core/reference.md` |
| `commands/init-harness.md` | `adapters/claude/commands/init-harness.md` |
| `skills/*` | `adapters/claude/skills/*` |
| `adapters/codex/templates/AGENTS.md.template` | `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template` |

For a quick pre-commit-adjacent check before committing focused mirror, adapter,
generated plugin, marketplace, or backlog-review changes, run the tracked hook:

```bash
sh .githooks/pre-commit
```

For release-like local verification during the v2 transition, prefer the
executable release gate:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

That release gate runs the Standard verification set plus this repository's
Active search-set, active packet pointer gate, and clean-worktree gate. The
`--base-ref` flag makes the search-set evidence, v1 archive boundary, and active
packet pointer checks compare committed changes against `REF...HEAD`, which is
the intended mode for a clean release candidate. A release diff should publish
one active pointer; use `--pointer <archive/v2/pointers/...>` only with
`--base-ref` when explicitly selecting that single publication. During an
in-progress maintenance diff, use
`python3 scripts/verify-release.py --skip-clean-worktree` without `--base-ref` to
validate the worktree-status command list before final local verification; that
preflight does not require an active packet pointer.

The checked-in GitHub Actions workflow runs the deterministic CI release-gate
subset for pull requests and pushes to `main` with `--ci --base-ref <base>`.
Maintainers still run the full local legacy verification
command with the clean-worktree gate and Codex local plugin activation smoke
before release-like handoff. CI does not prove Codex Desktop/runtime plugin
skill surfacing, plugin hook event delivery, or maintainer-local Codex CLI
activation.

See `MAINTENANCE.md` for the standard verification set, release checklist, and
rules for when this repository should add tests versus rely on multi-review.

### Pre-commit Hook

Enable the tracked git hook in local clones:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 scripts/check-codex-marketplace-metadata.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-v1-archive-boundary.py --staged`, `python3 scripts/check-search-set-evidence.py --staged`, `python3 scripts/check-backlog-archive-lifecycle.py --staged`, and `python3 scripts/check-active-packet-gate.py --staged` so temporary compatibility mirrors, Claude path contracts, Codex hook output shapes, generated Codex plugin assets, marketplace metadata readiness, maintenance review records, the frozen v1 archive boundary, search-set evidence, completed backlog archive pointers, and staged active packet publications cannot silently drift. The heavier local plugin activation smoke is part of Standard verification rather than pre-commit.

## How It Works

### Daily development flow

```text
1. Start session → project instructions and relevant skills load
2. Work normally with the coding agent
3. On failure → harness-engineer diagnoses from traces
4. Fix applied → recorded in traces/evolution/
5. Trace-backed harness changes accumulate for future maintenance
```

### Multi-review flow

```text
1. Frame the decision (what, stakes, constraints, input)
2. Design 2-4 disjoint critics on the spot
3. Run critics through isolated runtime mechanisms: sub-agents when available,
   or external review / separated sequential checklist when unavailable
4. Convergence check → PASS / VETO / MIXED
5. Present table + final verdict; user retains final decision authority
```

### Autoresearch flow

```text
1. Set up a direction file + immutable evaluator + mutable search surface
   (this repository's examples usually call them program.md, evaluate.py, and genome)
2. Agent runs autonomous experiment loop: hypothesis → implement → evaluate → ADOPT or REJECT
3. Results logged to experiments.jsonl + episode traces
4. After 100 experiments or 20 consecutive rejects → escalate
```

## Example: Trace-Based Diagnosis

When an agent repeatedly fails at TypeScript type errors:

```markdown
# traces/failures/001-type-error-loop.md
---
date: "2026-04-01"
escalated_to: hook
search_set_id: "SS-001"
resolved: true
---

## Failure: Agent ignores tsc errors and continues coding

### Observation
Agent edited 3 files, each introducing type errors. Continued to next task
without running tsc. Build failed in CI 20 minutes later.

### Root Cause
No automated type check on file edit. Agent relies on self-discipline
to run tsc, which is unreliable under context pressure.

### Fix
Added a structural verification path for `tsc --noEmit`.

### Prevention
The project harness now makes typecheck failures visible before completion.
```

## Design Decisions

**Why adapters?** The methodology should not be duplicated across agent runtimes. Runtime-specific details such as slash commands, hook schemas, project instruction filenames, and sub-agent model names belong in adapters.

**Why YAML frontmatter in traces?** Enables programmatic querying: `grep -l 'verdict: regressed'` instantly filters regression cases across hundreds of traces. This mirrors the paper's filesystem-based access pattern.

**Why concise project instructions?** Every token loaded every session competes with task context. Detailed docs go in project documentation or adapter references; project instructions are the table of contents.

**Why an immutable evaluator?** The paper principle: if the agent can modify its own evaluator, it contaminates the feedback signal. `evaluate.py` is this repository's common filename convention, not a paper-level requirement. Adapters choose the runtime-appropriate evaluator file, command, and enforcement mechanism.

**Why transfer rules to tooling?** Rules enforceable by linters/CI should live in tooling, not agent instructions. Project instruction files should contain only intent and judgment criteria that tools cannot enforce.

## Acknowledgments

Core principles are derived from:

- [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/abs/2603.28052) (Lee et al., 2026)
- [Effective Harnesses for Long-Running Agents](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic, 2025)

## License

MIT
