<!-- Compatibility mirror of `core/methodology.md`. Edit the canonical source, not this file. -->

# Harness Engineering Methodology — Core

Runtime-neutral core principles. For detailed reference in an installed Claude setup, see `~/.claude/docs/harness-reference.md`. Repository source: `core/reference.md`.

> The bottleneck is environment design, not model intelligence.
> Richer diagnostic context produces better harnesses. (Meta-Harness, Lee et al. 2026)

## Trace-Based Diagnosis — The Core of Diagnosis

### Principle: Raw Over Summaries, Traces Over Scores
- LLM summaries compress away details needed for diagnosis (proven by ablation: summary < raw trace)
- When diagnosing failures, read **raw execution logs, code, and scores** directly from the filesystem
- Use `grep`, `cat`, `diff` for selective access — don't dump everything into the prompt

### Trace Filesystem (Required for All Projects)
Every harnessed project must have exactly one active trace root. Adapters choose
the concrete path for their runtime and must document migration behavior when a
project already has history in another trace root. Do not split harness history
across multiple trace roots without an explicit migration plan.

When more than one candidate trace root exists, choose the active history by
evidence:

- Prefer roots with `search-set.md` and Active cases over empty or template-only
  roots.
- Prefer roots with unresolved failures, recent evolution entries, or
  experiment episodes relevant to the current issue.
- Prefer the runtime adapter's default root only when history evidence is tied
  or absent.
- Treat divergent non-empty roots as a migration question, not as a normal write
  target. Propose a copy/move/merge plan before recording new traces.

After selecting the active trace root, check for the minimum trace surface:
`evolution/`, `failures/`, `experiments/`, and `search-set.md`. For applied
harness changes, create missing minimum directories/files before writing traces
so future work has a complete history surface. For diagnosis-only work, report
missing trace infrastructure in the proposal or handoff instead of silently
expanding the project.
```
{trace_root}/
├── evolution/           # Harness change history
│   └── NNN-{name}.md   # Changes + reasoning + results (YAML frontmatter)
├── failures/            # Failure diagnosis (with raw context)
│   └── NNN-{name}.md   # Failure situation + cause + fix (YAML frontmatter)
├── experiments/         # Autoresearch episodes (per-session experiment context)
│   └── NNN-{name}.md   # Experiment range + adopted/exhausted axes + lessons (YAML frontmatter)
├── search-set.md        # Past failure cases for verifying harness changes (verify commands included)
```

- YAML frontmatter enables programmatic filtering: `grep -l 'verdict: regressed'` etc.
- Evolution log/failure diagnosis formats: see reference.md
- Preserve: failures requiring causal reasoning, before/after comparisons, confounding variable identification
- Don't preserve: simple typos, obvious fixes
- **failures/ recording triggers** (objective criteria):
  1. New guard violation type (a guard failure not seen before)
  2. Result opposite to hypothesis (e.g., expected improvement → degradation)
  3. Structural code change failure (logic change, not parameter tuning)
  Simple threshold misses (REJECT_THRESHOLD) don't need recording — experiments/ episode tables suffice
- **search-set**: each entry must have a `verify` field — an auto-executable verification command
- **experiments/**: record experiment episodes immediately at adapter-defined
  milestones so interruption does not erase diagnostic context. Format: see
  reference.md

### Fixed-Evaluator Search-Loop Detection

Treat fixed-evaluator search loops as an adapter-neutral project pattern, not
as a runtime-specific label. A project likely uses this pattern when two or
more of these signals are present:

- A direction file that defines the search objective, such as `program.md` or
  an adapter-defined equivalent.
- A mutable search surface that is safe for the agent to edit, such as source,
  configuration, genomes, prompts-as-code, or generated candidates.
- An immutable evaluator boundary: evaluator command, protected evaluator
  files/dependencies, and a machine-readable verdict.
- A machine-readable experiment log that records one result per attempt, such
  as `experiments.jsonl`.
- Episode traces under `{trace_root}/experiments/` that preserve diagnostic
  context around adopted changes, rejected hypotheses, and exhausted axes.

If only one signal exists, inspect nearby docs, project instructions, scripts,
and trace files before deciding that search-loop rules apply. If signals
conflict, record the uncertainty in the proposal or trace instead of applying
fixed-evaluator-specific changes blindly.

## Additive Modification — Change Strategy

Key finding from Meta-Harness experiments:

> Modifying existing working structures introduces confounding variables.
> Adding information is safer than changing structure.

### Rules
1. **Additive first**: Try changes that add new information/context first
2. **Subtractive second**: Removing unnecessary elements comes second
3. **Structural last**: Modifying existing control flow/logic is the last resort
4. **Isolate changes**: One change at a time. Bundling changes introduces confounding variables
   - **Exception — health batch fixes**: Non-functional fixes (dead references, state inconsistencies, missing docs) found via audit can be batched. Conditions: (1) each change is independent (no confounders), (2) changes don't alter agent behavior (infrastructure only), (3) individual changes listed in evolution trace. Functional changes must be separated.
5. **Diagnose regressions**: When regression occurs, isolate which part of the change caused it → record in traces

### Confounding Variable Identification Pattern
- Fix A + Fix B applied together → regression
- Fix A applied alone → slight regression or neutral
- → Common factor B is the primary cause
- **When this pattern is recognized**: separate the changes and evaluate each independently

### Surgical Diff Discipline (within a single edit)

Additive Modification governs change strategy *across iterations*. This rule governs diff shape *within a single edit*:

- **Diff self-check**: after editing, every changed line must trace directly to the user's request. If a line doesn't, remove it.
- **Pre-existing dead code** (not orphaned by your change) is mentioned, not removed — removal requires explicit request.
- **No drive-by cleanups**: don't reformat, rename, or "improve" unrelated code while solving a different problem. Bundled cleanups become confounding variables when regressions appear.

Why this sits next to Additive Modification: both stem from the same finding — touching more than necessary introduces confounders. This rule is the single-edit corollary of the multi-iteration principle above.

## Minimal Outer Loop & Code-Space Search — Design Principles

### P3: The outer loop must be simple enough to verify by inspection
- Harness control flow (hook chain, evaluator path, done conditions) must be immediately understandable
- Complex conditional branching, multi-stage orchestration, agent-to-agent protocols increase outer loop cost
- **Self-check**: "Can I explain this harness's entire flow in 5 minutes?" → No means simplify
- **Fixed-evaluator application**: direction file -> mutable search surface ->
  immutable evaluator -> adopt/reject decision is the entire loop. Don't make it
  more complex

### P4: Agents search in code space
- What agents modify is **versioned, executable search surfaces**, not vague
  natural language exhortations
- Source, configuration, prompt templates, prompt-construction code, generated
  candidates, hooks, skill documents, and project instructions can be search
  space when they are isolated, diffable, and evaluated by the same verifier
- Rewriting prompts in natural language ("try harder") without an evaluator,
  isolation boundary, or raw diff trail is noise, not search
- **Fixed-evaluator application**: directly modify the mutable search surface to
  explore performance. Prompt-as-code changes are allowed only when they are
  part of that mutable surface and judged by the immutable evaluator boundary

### P5: Recurring failures are absorbed by structure, not rules

> "Don't do this" fails. "Can't do this" succeeds.

When the same failure category repeats, move beyond telling the agent what not to do — make **violation structurally impossible**.

**Escalation ladder** (stronger going down):

| Level | Mechanism | Enforcement | Limitation |
|-------|-----------|-------------|------------|
| 0. Rule | Project instruction constraint | Voluntary compliance | Leaks via context rot |
| 1. Warning | Runtime hook or explicit verification warning | Reminder | Can be ignored |
| 2. Block | Runtime hook, CI, git hook, or protected command path | Direct modification blocked | Bypass routes may exist |
| 3. **Structural impossibility** | Single Source + Codegen + Protect | **Drift itself is impossible** | Initial setup cost |

**Single Source + Generated Derivatives pattern**:
```
Human-editable truth (YAML / schema / config)
    → Generator (codegen / template / build script)
        → Derived artifact (code / docs / UI text)
            → Protection (chmod 444 + blocking hook)
```

**When to apply**:
- Same failure category with 3+ evidence items → structural elimination review is mandatory
- Truth source exists in 2+ places → apply Single Source + Codegen + Protect pattern
- Only judgment-dependent domains (aesthetics, trade-offs) should remain as rules

**Self-check**: "Can this failure category be eliminated by structure rather than rules?" If yes, aim for ladder level 3.

## Sub-Agent Invocation — Applied Runtime Extension

The core Meta-Harness loop is a single coding-agent proposer using filesystem
evidence, scores, and traces. Sub-agents, external reviewers, sequential
checklists, and fixed evaluator scripts are **applied runtime mechanisms** for
isolation and independent judgment; they are not the paper's core claim.

Using an isolation mechanism does not violate the single-agent principle as long
as the project does not create persistent multi-persona orchestrators.
Sub-agents are tools, not teammates, and adapters decide which isolation
mechanisms their runtime can support.

### Trigger categories

Two triggers justify adapter-defined isolation mechanisms. Generic sub-agent
uses (parallel exploration, context firewall) are runtime tool patterns, not
harness policy — invoke them at your own judgment without a trigger table.

| Trigger | Mechanism | When |
|---------|-----------|------|
| **Qualitative multi-perspective judgment** | Parallel critics, external review, or separated sequential checklist | Hard-to-reverse decisions, regressions with suspected confounders, domains where single-perspective evaluation has failed before |
| **Evaluator independence** | Fixed immutable evaluator, dedicated evaluator context, or external scorer | High-stakes generation where self-evaluation bias is the primary risk; the generator must not score its own output. A fixed evaluator is the cheapest and strongest form when a binary verdict is viable; a dedicated context or external scorer is the alternative when judgment cannot be scripted |

This is why Meta-Harness can absorb isolation benefits without abandoning the
single-agent paradigm: each benefit has a tactical mechanism that does not
require persistent agent definitions or multi-persona orchestration.

### Rules
- **Independence**: isolated reviewers or evaluator contexts must not share intermediate results — independence is the source of value, contamination kills it
- **No orchestrator persistence**: sub-agents are spawned per-task and discarded. Do not create persistent agent-team definitions
- **Conclusion-only return**: isolated reviewers return distilled findings, not raw transcripts — the firewall is the point
- **Trigger threshold**: prefer over-invoking these mechanisms to under-invoking them. The cost of an unnecessary sub-agent call is small; the cost of a contaminated decision or context-rotted parent is large

### Model routing
Use the runtime's available model routing when spawning sub-agents:

| Task type | Model | Examples |
|-----------|-------|---------|
| Complex judgment, architecture, irreversible decisions | Strongest reasoning model available | High-stakes multi-review critics, design validation, strategy decisions |
| Standard analysis, exploration, implementation | Default capable coding model | Explore agents, code review, standard evaluators, routine critics |
| Mechanical verification (no judgment needed) | Small/fast model if available | Binary pass/fail checks, format validation, file existence checks |

- Use small models only for judgment-free mechanical checks
- When uncertain, choose the more capable model; slight cost increase beats quality loss
- Adapters may define concrete model names for their runtime

### Anti-patterns
- Spawning sub-agents for trivial tasks (3-line edits, single-file reads)
- Using sub-agents to "split work" without independence (sequential dependencies → use the parent agent)
- Creating named persistent agents (Reviewer, Architect, Tester) — this is multi-persona collaboration, not Meta-Harness

## Feedback Loop — Evolution Protocol

### Failure → Trace Recording → Rule Addition Loop
1. Agent fails or repeats the same fix
2. **Record in traces**: preserve raw context in `{trace_root}/failures/NNN-{name}.md`
3. **Structural elimination check** (P5): "Can this category be eliminated by structure, not rules?"
4. Respond: add knowledge to docs, add constraint to project instructions, add tooling/hooks, or **apply Single Source + Codegen + Protect** (P5 ladder level 3) as appropriate
4. **Record change in evolution log**: `{trace_root}/evolution/NNN-{name}.md`
5. **Verify with search-set**: confirm past failures in `{trace_root}/search-set.md` don't recur
6. Add new failure to search-set if it has verification value

### Completion Criteria
Before starting work, define: `Done when: [specific, verifiable condition]`

### Fixed Evaluator Search Loops
- Evaluator: adapter-defined command with an immutable evaluator boundary and
  machine-readable output.
- Verdict: binary or thresholded adopt/reject decision defined by the project.
- Rejected candidate preservation: before reverting or discarding a rejected
  candidate, capture the candidate diff and raw evaluator output in traces when
  recording triggers apply. Candidate code may be unrecoverable after cleanup.
- Escalation: repeated rejects, suspected evaluator defects, or exhausted search
  axes should stop normal experimentation and trigger manual review.

### Hooks vs Backpressure
- **Hooks**: enforced externally (type checks, formatters)
- **Backpressure**: agent self-verification (tests, coverage)

### Rule Quality Criteria
- **Specific**: "clean code" ✗ → "functions under 50 lines" ✓
- **Verifiable**: prefer rules checkable by linters/tests
- **Just enough**: excessive rules waste tokens

## Skill Document — The Highest-Leverage Investment

> Skill document quality has a larger impact on performance than iteration count or population size.

### Documentation Abstraction Boundaries
- Core owns what and why: methodology principles, trace semantics, verification
  policy, general failure recording, and agent-agnostic workflow contracts.
- Adapters own how: runtime-specific instruction files, hook schemas,
  permission models, install paths, tool surfaces, and examples.
- Adapter docs may reference core rules, but should not fork or copy large
  methodology blocks unless runtime behavior truly differs.
- During review, treat copied methodology blocks in adapters as drift risks and
  either replace them with references or document the runtime-specific reason.

### Skill Document Writing Principles
- **State prohibitions and goals**, leave diagnosis methods free (agent decides)
- Define role, directory structure, CLI commands, output format
- Debug skill documents with 3-5 short test iterations before production runs
- After enough iterations, **accumulated traces shape behavior more strongly than the skill document itself**
