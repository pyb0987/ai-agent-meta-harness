# Harness Engineering Reference

Detailed runtime-neutral reference loaded when init-harness or harness-engineer skills are invoked.
Not auto-loaded every session. Core principles are in core/methodology.md.

## 1. Trace Filesystem — Structure and Format

These filenames, frontmatter fields, and search-set sections are repository
contracts for projects adopting this harness. They operationalize the
Meta-Harness principle of reusable trace evidence, but they are not
paper-mandated names or schemas.

### Evolution Log Format (`traces/evolution/NNN-{name}.md`)
```markdown
---
iteration: NNN
date: "YYYY-MM-DD"
type: additive | subtractive | structural
verdict: improved | regressed | neutral
files_changed: ["file1.md", "file2.sh"]
refs: [1, 2]  # Referenced prior iteration numbers
---

## Iteration NNN: {title}
Trigger: {why was the change needed}

### Diagnosis
{Diagnosis based on reading prior traces/code/scores}
- Referenced files: {specific paths/lines}

### Change
- Diff summary: {core changes, 1-3 lines}

### Result
- Before: {pre-change metrics}
- After: {post-change metrics}

### Lesson
{Lesson for subsequent iterations to reference}
```

### Failure Diagnosis Format (`traces/failures/NNN-{name}.md`)
```markdown
---
date: "YYYY-MM-DD"
escalated_to: instructions | docs | skill | hook | tool | none
search_set_id: "SS-NNN"  # Reference to search-set entry if applicable
resolved: true | false
---

## Failure: {title}

### Observation
{What failed — include raw error messages, test output, execution logs}

### Root Cause
{Why it failed — specific cause in code/config/data. File:line references}

### Fix
{How it was fixed — change details}

### Prevention
{How to prevent recurrence — added rules/hooks/tests and their content}
```

### Fixed-Evaluator Failure Trace Supplement

When recording a rejected fixed-evaluator experiment in failures/, additionally
include:
- **candidate diff**: the full diff for the rejected candidate, captured before
  any revert or cleanup
- **evaluator output**: the raw machine-readable evaluator result, including
  guard details and metrics
- **causal analysis**: 1-2 line summary of why hypothesis and result diverged

**Reject workflow**: (1) parse verdict -> (2) if a recording trigger applies,
capture candidate diff + evaluator output -> (3) revert or discard the rejected
candidate using the adapter's approved mechanism -> (4) append the experiment
log. Candidate code may be unrecoverable after revert, so order matters.

### Numbering
- `NNN` is a 3-digit sequence number (001, 002, ...)
- `traces/evolution/` and `traces/failures/` within a project have independent numbering
- `{name}` is a kebab-case summary (e.g., `001-add-env-bootstrap`, `003-zscore-drift-bug`)

### Experiment Episode Format (`traces/experiments/NNN-{name}.md`)

Preserves fixed-evaluator or search-loop session results as episodes.
Machine-readable experiment logs are usually one-line summaries, insufficient
for diagnosis context. Episode traces preserve "why this hypothesis
succeeded/failed" with raw context.

```markdown
---
session: "auto-search/session-YYYYMMDD-HHMMSS"
date: "YYYY-MM-DD"
experiment_range: "E1-E12"        # Experiment number range in this episode
adopts: 2                         # Number of ADOPTs
rejects: 10                      # Number of REJECTs
metric_start: 0.15               # Baseline metric at episode start
metric_end: 0.22                  # Baseline metric at episode end
---

## Episode NNN: {session summary title}

### Context
{Direction and motivation explored in this session}
- Current direction: {research direction at this point, with file/path if applicable}
- Prior episode lessons: {referenced episode numbers + key lessons}

### Key Experiments
| # | Hypothesis | Verdict | Metric | Δ% | Insight |
|---|-----------|---------|--------|-----|---------|
| E1 | ... | ADOPT | 0.18 | +5.2% | {1-line lesson} |
| E2 | ... | REJECT_GUARD | - | - | {why it failed} |

### Adopted Changes
{Summary of specific code changes from ADOPTed experiments — not diff-level but what was changed and why}

### Exhausted Axes (axes exhausted in this episode)
- {axis}: {why exhausted, supporting data}

### Lesson
{Key lessons for subsequent episodes/sessions}
- Promising directions: {remaining exploration possibilities}
- Warnings: {approaches to avoid}
```

#### Episode Recording Timing — Immediate Recording Principle
Do not wait for session end. Write immediately when milestones occur.
(Reason: if the user hits Ctrl+C, there is no recording opportunity)

- **On ADOPT**: immediately record the adopted change and rationale
- **On axis exhaustion**: record experiment range and exhaustion rationale, then
  update the adapter-defined research state with the exhausted axis so the next
  session does not re-explore it
- **On termination**: record full session experiment summary
- **Every 10 experiments**: write an interim summary (even without ADOPTs)
- Multiple episode files are possible per session

#### Relationship with Machine-Readable Experiment Logs
- Experiment log: machine-readable 1-line log per experiment for loop resumption
- `traces/experiments/NNN-*.md`: episode-level diagnostic context for humans/agents (why?)
- Not duplication but complementary: jsonl records "what", episodes record "why"

#### Minimum Research State Example
Adapters may choose the concrete research-state file, but it should preserve
exhausted axes in a machine-readable or grep-able form so later sessions do not
retest the same failed direction.

```markdown
## Exhausted Axes
- beam-width-search: exhausted 2026-04-30 after E12-E19; no metric lift above
  baseline and guard failures increased. See traces/experiments/004-beam-width.md.
```

### Trace Usage Patterns
When harness-engineer diagnoses:
1. Check the full list of `traces/evolution/` — understand prior changes and results
2. grep `traces/failures/` for similar failures
3. Check `traces/experiments/` episodes for exhausted axes and lessons
4. Read Lesson/Prevention sections of related traces
5. Verify new changes do not repeat prior confounding variables

Useful grep filters:
- `grep -l 'verdict: regressed' traces/evolution/` — find regressed changes
- `grep -l 'resolved: false' traces/failures/` — find unresolved failures
- `grep -l 'type: structural' traces/evolution/` — find structural changes

## 2. Analysis — Project Diagnosis

When applying a harness to a new project, analyze the following. Runtime adapters decide concrete instruction filenames and hook mechanisms.

### Project Characteristics
- Type: web | mobile | game | research | backend | monorepo | hybrid
- Package manager & build system
- Framework & core dependencies
- Directory structure & architecture patterns
- Linter/formatter configuration
- Test framework & structure
- CI/CD pipeline
- Existing documentation (README, AGENTS.md, CLAUDE.md, etc.)

### Environment Mapping
- Build commands (dev, build, test, lint)
- Environment variable patterns
- Deployment targets
- External system connections (DB, API, monitoring)

## 3. Decision — What Is Needed

Determine components based on analysis results. Do not include everything.

### Required (All Projects)

| Component | Content |
|-----------|---------|
| Build | dev, build, test, lint commands |
| Conventions | Naming, structure, style rules (extracted from linter) |
| Architecture | Layer direction, dependency rules, prohibited patterns |
| Traces | trace root initialization using the adapter's chosen path |
| Feedback rules | Rules to prevent repeated failures (added incrementally) |

### Conditional (Only When Applicable)

| Project Characteristic | Additional Component |
|----------------------|---------------------|
| Monorepo | Workspace structure, inter-package dependency direction |
| Frontend | Component patterns, state management, routing rules |
| Backend/API | API design, DB patterns, error handling, auth flow |
| Research | Data flow, experiment structure, reproducibility rules |
| Tests exist | Test commands, coverage criteria, test patterns |
| CI exists | CI reference, lint pass conditions, merge gates |

### MCP vs CLI Decision Criteria
- Tools the model already knows (git, docker, gh, psql, curl, etc.) should use CLI over MCP
- MCP tool descriptions consume system prompt space, eating into instruction budget
- MCP should only connect to external systems not coverable by CLI

## 4. Generation — Project Instruction Writing Principles

### Structure
- Keep core instructions concise (serving as a table of contents)
- Detailed documents separated into a project docs/ directory or adapter-specific reference path
- Imperative sentences the agent can read and act on immediately

### Prohibited
- Long-form natural language explanations
- Repeating information inferable from code/linters
- Codebase overviews, directory listings
- Excessively long instruction files (split to docs/ if needed)

## 5. Search-Set — Regression Verification

### Format (`traces/search-set.md`)
```markdown
---
description: "Collection of failure cases for verifying harness changes."
last_updated: "YYYY-MM-DD"
---
# Harness Search Set

Curated failure cases for verifying harness changes don't regress.

## Active

### SS-001: {failure title}
- **Source**: traces/failures/003-zscore-drift-bug.md
- **Symptom**: {what went wrong}
- **verify**: `{command that can be run to check this case}`

## Archived

### SS-002: {failure title}
- **Source**: traces/failures/007-missing-env-var.md
- **Symptom**: {what went wrong}
- **verify**: `{command that can be run to check this case}`
- **archived_reason**: {why this no longer needs to be active}
```

### Usage
- Before applying a harness change, run all Active `verify` commands to check for regressions
- After applying a change, run all relevant Active `verify` commands again and compare results
- Each Active entry must have a `verify` field — an automatically executable verification command
- Keep at least one Active entry; if Active reaches 0, restore an Archived entry or register an unresolved failure
- Add new Active entries when a failure is worth guarding against in future changes

### Archived Restore Workflow
- Restore an Archived case to Active when the same failure class recurs, when a
  harness change touches the same prevention mechanism, or when Active coverage
  would otherwise drop to zero.
- When restoring, preserve the original Source/Symptom/verify fields and add a
  short note in the related evolution or failure trace explaining why it became
  relevant again.
- Re-archive only after the updated prevention has passed its verify command and
  the case no longer needs active regression coverage.
- Update `archived_reason` with the re-archive date and reason instead of
  leaving stale context from the first archive.

### Verify Command Quality
- Deterministic: repeated runs against the same checkout should produce the same
  pass/fail result.
- Non-interactive: the command must not wait for prompts, editors, GUI input, or
  manual confirmation.
- Regression-sensitive: the command must exit non-zero when the guarded failure
  recurs. Commands that only print information are not sufficient unless they
  pipe into an assertion.
- Local by default: prefer commands that avoid network calls, paid services,
  credentials, and high-cost resources.
- Explicit requirements: record sandbox, permission, network, dependency, or
  fixture requirements in the search-set entry when they are unavoidable.
- Narrow enough to diagnose: prefer the smallest command that covers the failure
  pattern without hiding it behind unrelated long-running checks.
