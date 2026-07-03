# AI Agent Meta-Harness

A practical framework for maintaining trace-backed AI-assisted development environments across coding agents, inspired by the [Meta-Harness](https://arxiv.org/abs/2603.28052) paper (Lee et al., Stanford 2026).

The Meta-Harness paper frames harness design as a major factor in agent performance, and its introduction cites prior harness-sensitivity evidence that changing only the harness can produce a 6x performance gap on the same benchmark. This project operationalizes Meta-Harness paper principles into a practical harness toolkit, runtime adapters, and verification gates. It combines published findings with repository-local engineering practices and checks for documentation, adapters, generated assets, and self-application traces, but it does not claim a local reproduction of the paper's end-to-end benchmark gains.

The repository is split into a shared core plus thin runtime adapters. The methodology should be edited once in `core/`; Claude Code and Codex integration details live under `adapters/`.

The repository-local **AI Agent Meta-Harness v2** flow is the practical default
for stable work in this repository. The v2 roadmap and post-v2 boundary notes
live in `backlog/v2-roadmap.md`.

## What's Inside

| Component | Description | Path |
|-----------|-------------|------|
| **Core methodology** | Runtime-neutral principles and trace formats | `core/` |
| **Meta-Harness system overview** | Repository-local v2 governance and strategy-search architecture | `docs/meta-harness-system.md` |
| **Claude adapter** | Claude Code commands, skills, examples, hooks guidance | `adapters/claude/` |
| **Codex adapter** | Codex skills and project instruction templates | `adapters/codex/` |
| **Backlog** | v2 roadmap, completed plans, and optional post-v2 boundaries | `backlog/` |
| **Maintenance plan** | Repository upkeep, tests, release checks, review policy | `MAINTENANCE.md` |

## Install For Your Agent

Start from a local clone:

```bash
git clone https://github.com/pyb0987/ai-agent-meta-harness.git
cd ai-agent-meta-harness
```

### Codex

Executable install path: copy the Codex skills into the active Codex home.

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R adapters/codex/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
```

The agent receives these routing surfaces:

- `init-codex-harness`
- `harness-engineer`
- `autoresearch`
- `multi-review`

Ordinary users do not need to memorize those names. They are listed here so an
installing agent can verify what it copied.

The local plugin bundle is the fuller packaging artifact for Codex surfaces that
support local plugin activation. Build and smoke-test it before enabling it in
that surface:

```bash
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 adapters/codex/scripts/smoke-local-plugin-activation.py
```

The activation smoke creates an isolated `CODEX_HOME`; it proves the bundle
shape and local activation mechanism, but it does not install the plugin into
your real Codex home and does not prove a running Codex Desktop session has surfaced those skills.
If your Codex surface does not expose local plugin
activation, keep the direct skill-copy install above.

Direct skill copy is enough for init, harness-engineering, multi-review, and
basic autoresearch guidance. When a project adopts autoresearch and needs the
project protection assets, install them explicitly:

```bash
python3 plugins/ai-agent-meta-harness/scripts/install-autoresearch-protection.py --target /path/to/project --run-smoke
```

After install, ask Codex in the target project:

```text
Apply meta-harness to this project.
```

`Apply codex-harness to this project` is also accepted as a Codex-specific
alias.

### Claude Code

Install the shared methodology, reference docs, Claude skills, the
`/init-harness` command, and the optional global-profile drift checker:

```bash
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
mkdir -p "$CLAUDE_HOME/rules/common" "$CLAUDE_HOME/docs" "$CLAUDE_HOME/skills" "$CLAUDE_HOME/commands" "$CLAUDE_HOME/harness/scripts" "$CLAUDE_HOME/harness/canonical/commands" "$CLAUDE_HOME/harness/canonical/skills"
cp core/methodology.md "$CLAUDE_HOME/rules/common/harness-methodology.md"
cp core/methodology.md "$CLAUDE_HOME/harness/canonical/harness-methodology.md"
cp core/reference.md "$CLAUDE_HOME/docs/harness-reference.md"
cp core/reference.md "$CLAUDE_HOME/harness/canonical/harness-reference.md"
cp -R adapters/claude/skills/* "$CLAUDE_HOME/skills/"
cp -R adapters/claude/skills/* "$CLAUDE_HOME/harness/canonical/skills/"
cp adapters/claude/commands/init-harness.md "$CLAUDE_HOME/commands/"
cp adapters/claude/commands/init-harness.md "$CLAUDE_HOME/harness/canonical/commands/init-harness.md"
cp adapters/claude/scripts/check-claude-profile-drift.py "$CLAUDE_HOME/harness/scripts/"
cp adapters/claude/templates/profile-governance.json "$CLAUDE_HOME/harness/profile-governance.json"
python3 "$CLAUDE_HOME/harness/scripts/check-claude-profile-drift.py"
```

After install, run this in the target project:

```text
> /init-harness
```

Claude projects normally write `CLAUDE.md` and `.claude/traces/`. Codex
projects normally write `AGENTS.md` and `.harness/traces/`. Both adapters use
the same core methodology and the same v2 governance model.

The Claude profile drift checker is for the user's global Claude surface:
`~/.claude/rules`, `~/.claude/docs`, selected `~/.claude/settings*.json`, and
any hook contracts listed in `~/.claude/harness/profile-governance.json`. It is
not repository-local v2 publication evidence. It is a lightweight diagnostic
guard that helps catch drift in the installed methodology, reference,
`/init-harness` command, and Claude skills. It can also catch manifest-listed
hook documentation/settings mismatches and stale model IDs before they steer
daily work. Add hook contracts or blocked model IDs when you intentionally
govern those local files.

For example, to govern a local hook note, add a `hook_contracts` entry with
`event`, non-empty `command_contains`, and optional `declared_in`. The checker then
requires the hook command to exist in the selected Claude settings file and, if
`declared_in` is set, requires that documentation file to mention the same hook
event and command fragment.

Agent installation prepares Codex or Claude to bootstrap and maintain a target
project. It does not install the repository-local v2 `governance` CLI into that
target project. Use the `./governance` commands below inside this repository, or
inside another repository that intentionally carries the same v2 governance
scripts.

## Using Meta-Harness In A Target Project

After the first setup prompt, use the agent normally. Users do not need to name
harness skills. The point of this adapter is that the user should not need to
know whether the next step is init, harness-engineering, multi-review, or
autoresearch.

Common user phrases:

| User says | Agent should do |
|-----------|-----------------|
| "Apply meta-harness to this project." | Initialize or update project instructions and trace folders. |
| "set up agent memory/traces." | Initialize the same trace-backed harness surface. |
| "Please build/fix/add this feature." | Work normally, using the project instructions and verifier. |
| "This keeps failing." | Inspect raw traces, find recurrence, and evolve the harness before retrying. |
| "stop repeating this mistake." | Turn the repeated failure into a trace-backed rule, verifier, hook, or test. |
| "Review this carefully." or "am I missing anything?" | Use multi-perspective review when the decision is high risk or easy to misframe. |
| "Try variants and keep the winner." or "keep the measurable winner." | Propose an autoresearch loop only when there is a fixed evaluator and metric. |
| "Did the harness learn from this?" or "check for dogfood gaps." | Propose trace, search-set, instruction, or strategy-search candidates only when a concrete trigger-evidence pointer, reusable future value, and a clear next action are all present. |

What appears in the target project:

```text
AGENTS.md or CLAUDE.md          # Short project instructions for the agent
.harness/traces/ or .claude/traces/
.harness/traces/evolution/ or .claude/traces/evolution/
.harness/traces/failures/ or .claude/traces/failures/
.harness/traces/experiments/ or .claude/traces/experiments/
.harness/traces/search-set.md or .claude/traces/search-set.md
```

The trace folders are the project memory. They are not a task queue for the
user. The agent reads and writes them when a failure pattern, harness change, or
measurable experiment makes that useful.

Global installs are a routing and cross-project memory layer, not a replacement
for project-local traces. Codex may have
`${CODEX_HOME:-~/.codex}/harness/traces`; Claude may have
`${CLAUDE_HOME:-~/.claude}/harness/traces`. Those global roots are useful for
agent/harness failures that span projects, such as install drift or a repeated
routing mistake. Project-specific recurrence guards, JD filters, tests, and
verification commands still belong in the target project's active trace root.
If a target project has no trace root, the agent should report that gap and
propose initialization instead of claiming that the global harness fully covers
the project.

During normal work, the harness stays quiet unless a concrete trigger-evidence
pointer, reusable future value, and a clear next action are all visible. Even
then, the agent should surface at most one diagnostic maintenance note.
Explicit dogfood review may inspect the wider candidate list, but proposals are
diagnostic until adopted. Low trace volume is not a failure by itself, and
agents should not auto-edit Active search-set entries.

## Using The Repository-Local Meta-Harness

Most projects use only the target-project harness above. Use this section only
inside this repository, or inside another repository that intentionally carries
the same v2 `governance` scripts.

The practical default is intentionally small: make the content change, let
`governance` infer the required evidence, then publish one archive-only
AcceptancePacket publication for the finished release range.

For routine work:

```bash
./governance start --base-ref <comparison-ref> --intent "short human intent"
# edit, test, and commit the content change
./governance finalize --packet <packet> --base-ref <comparison-ref>
./governance publish --packet <packet>
```

Use `origin/main`, the previous release publication, or another explicit
comparison commit as `<comparison-ref>`. Stable handoff should use `--base-ref`;
`--staged` is preflight, and `--worktree` is diagnostic only.

When the packet requires review judgment, add the review import step before
publishing:

```bash
./governance review-template --packet <packet> --scratch-output /tmp/review.yml
# reviewers complete the draft with real findings, probe results, and lineage
./governance import-review --packet <packet> --from /tmp/review.yml
./governance publish --packet <packet>
```

The operator should not hand-author stable archive bytes. `review-template`,
`import-review`, `write-pointer`, and `publish` materialize the archive-bound
packet, review, probe, and pointer files. If a generated template still contains
TODO or draft fields, it is a prompt for human judgment, not evidence.

For release-like verification after publication:

```bash
python3 scripts/verify-release.py --base-ref <comparison-ref>
```

Use `--skip-clean-worktree` only as local preflight while work is still in
progress; it is not stable release evidence.

### What Users Usually Provide

- A short intent string.
- A comparison ref.
- Normal content commits and test evidence.
- Completed human review judgment only when `finalize` says review is required.

Everything else should be inferred, generated, or checked by the repository
tools. If a proposed workflow asks the operator to manually compute packet
hashes, edit pointer files, classify archive paths, or remember hidden staging
rules, treat that as design debt.

### Strategy Search

`scripts/strategy-search.py` is the optional evolution engine. Use it when you
want the harness to search over a bounded strategy surface with a fixed
evaluator.

The shape is:

```bash
python3 scripts/strategy-search.py start --direction <direction.yml>
python3 scripts/strategy-search.py propose --run <run> --candidate-id <id> --patch <patch.diff>
python3 scripts/strategy-search.py eval --run <run> --proposal <proposal.yml>
python3 scripts/strategy-search.py select --run <run> --candidate <id>
```

Strategy-search records are diagnostic. To adopt a selected candidate, apply
the selected patch as an ordinary content commit, then use the `governance`
packet/pointer publication flow above. Selection files under
`.harness/search-runs/` are not stable evidence by themselves.

Plan 14 documents optional sandbox and concurrency hardening boundaries. It is
not required for the normal repository-local workflow.

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
| Repository methodology and documentation correctness | This repository's interpretation of runtime-neutral harness principles, trace formats, and claim boundaries | `core/`, `docs/`, README boundary tests, and multi-review records |
| Adapter and generated-artifact operability | Claude/Codex adapter instructions, hook templates, generated plugin assets, and smoke-tested local workflows | Adapter unit tests, drift checks, plugin sync checks, hook smoke tests, and local activation smoke |
| Repository self-application evidence | This repository applying its own maintenance loop and preserving regression memory | AcceptancePacket artifacts, packet-linked traces, checker-computed eligibility, `.harness/search-runs/` diagnostic records, and active pointer publication checks |

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

- **Raw traces over summaries** — Paper-backed: full trace access achieved 56.7% accuracy vs 38.7% with summaries (Table 3). Repository practice: agents diagnose failures by reading raw execution logs via `grep` and `cat`, not by ingesting compressed summaries. Trace files use YAML frontmatter for programmatic querying — `grep -l 'verdict: regressed' .harness/traces/evolution/` instantly filters regression cases.
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
├── README.md               # v2 planning guide
├── v2-roadmap.md           # v2 roadmap and meta-plan
└── plans/                  # completed plans and optional boundaries
adapters/
├── claude/
│   ├── commands/
│   ├── examples/
│   └── skills/
└── codex/
    ├── skills/
    └── templates/
```

## Verification

For release-like local verification during the v2 transition, prefer the
executable release gate:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

That release gate runs the Standard verification set plus this repository's
Active search-set, active packet pointer gate, and clean-worktree gate. The
`--base-ref` flag makes packet and pointer checks compare committed changes
against `REF...HEAD`, which is the intended mode for a clean release candidate.
A release diff should publish one active pointer; use
`--pointer <archive/v2/pointers/...>` only with `--base-ref` when explicitly
selecting that single publication. During an in-progress maintenance diff, use
`python3 scripts/verify-release.py --skip-clean-worktree` without `--base-ref` to
validate the worktree-status command list before final local verification; that
preflight does not require an active packet pointer.

The checked-in GitHub Actions workflow runs the deterministic CI release-gate
subset for pull requests and pushes to `main` with `--ci --base-ref <base>`.
Maintainers still run the full local verification command with the
clean-worktree gate and Codex local plugin activation smoke before release-like
handoff. CI does not prove Codex Desktop/runtime plugin skill surfacing, plugin
hook event delivery, or maintainer-local Codex CLI activation.

See `MAINTENANCE.md` for the standard verification set, release checklist, and
rules for when this repository should add tests versus rely on multi-review.

### Pre-commit Hook

Enable the tracked git hook in local clones:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs the repository's fast local checks for adapter paths,
generated Codex plugin assets, marketplace metadata, maintenance review records,
search-set evidence, backlog lifecycle records, and staged active packet publications.
The heavier local plugin activation smoke is part of Standard verification rather than pre-commit.

For a quick pre-commit-adjacent check:

```bash
sh .githooks/pre-commit
```

The hook includes:

```bash
python3 scripts/check-codex-marketplace-metadata.py
python3 scripts/check-v1-archive-boundary.py --staged
python3 scripts/check-trace-retrieval-provenance.py --staged
python3 scripts/check-backlog-archive-lifecycle.py --staged
python3 scripts/check-active-packet-gate.py --staged
```

Those cover marketplace metadata readiness, the frozen v1 archive boundary,
trace retrieval provenance, completed backlog archive pointers, and staged
active packet publications.

## How It Works

### Daily governance flow

```text
1. Start a packet with a base ref and short intent
2. Make and commit the content change
3. Finalize the packet so the checker infers evidence and review requirements
4. Import human review only when required
5. Publish one archive-only v2 pointer commit
6. Run release verification against the base ref
```

### Strategy-search flow

```text
1. Write a direction: objective, search surface, fixed evaluator, protected paths
2. Propose candidate patches inside the allowed search surface
3. Evaluate candidates in disposable workspaces with anchored diagnostic records
4. Select a runner-produced candidate as diagnostic adoption context
5. Apply the selected patch as a normal content commit
6. Use v2 governance for stable publication
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
# .harness/traces/failures/001-type-error-loop.md
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
