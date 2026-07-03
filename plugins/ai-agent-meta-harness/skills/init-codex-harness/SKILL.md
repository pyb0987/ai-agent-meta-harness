---
name: init-codex-harness
description: "Initialize or update a Codex-compatible harness for a project using the shared AI Agent Meta-Harness methodology. Use when the user asks to apply meta-harness, apply codex-harness, set up agent memory/traces, initialize a harness for Codex, convert a Claude harness to Codex, or set up trace/search-set driven project instructions."
---

# Init Codex Harness

Bootstrap a project harness for Codex while keeping the methodology sourced from `core/`.

## Inputs

- Shared methodology: `core/methodology.md`
- Shared reference: `core/reference.md`
- Codex project template: bundled `assets/AGENTS.md.template` (adapter compatibility mirror: `adapters/codex/templates/AGENTS.md.template`)

If this skill is installed outside the repository and shared `core/` files are unavailable, use the workflow below and the bundled AGENTS template; state that shared references were not locally available.

## Objective

Create the minimal project-local structure Codex needs to work reliably:

```text
.harness/
└── traces/
    ├── evolution/
    ├── failures/
    ├── experiments/
    └── search-set.md
AGENTS.md
```

Prefer `.harness/traces/` for runtime-neutral projects when history evidence is
absent or equivalent. If the project already has `.claude/traces/`, keep it
temporarily when it contains meaningful history so Codex does not split
evidence across roots.

The global Codex trace root at `${CODEX_HOME:-~/.codex}/harness/traces` does
not satisfy this project-local structure. Use it only for cross-project
agent/harness failures; initialize a project trace root for project-specific
guards and verification.

## Workflow

### Step 1: Inspect the Project

Read raw files, not summaries:

- package/build files
- existing `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.harness/`, `.codex/`
- test, lint, typecheck, build commands
- CI configuration
- docs that define architecture or domain constraints

Use `rg --files` first. Keep inspection targeted.

### Step 2: Choose Trace Root

Choose by meaningful history before path preference:

1. Inspect both `.harness/traces/` and `.claude/traces/` when either exists.
2. Use `.harness/traces/` when it is the only root with meaningful history.
3. Use `.claude/traces/` temporarily when it has meaningful history and
   `.harness/traces/` is missing, empty, or template-only.
4. If both roots have meaningful but divergent history, stop and propose a
   migration/merge plan before writing new traces.
5. If neither root exists, or neither existing root has meaningful history,
   initialize `.harness/traces/`.

Do not create both `.claude/traces/` and `.harness/traces/` in the same project unless the user explicitly asks for split histories.

Meaningful history means `search-set.md` has Active cases, `failures/` has
diagnoses, `evolution/` has prior harness changes, or `experiments/` has
episodes relevant to current work. Empty directories, `.keep` files, and
untouched `search-set.md` templates are not meaningful history and must not
outrank real history in the other root. If `.claude/traces/` exists but is
empty or template-only, initialize `.harness/traces/` instead.

Propose migration from `.claude/traces/` to `.harness/traces/` when Codex is now
the primary runtime, the Claude history is stable enough to preserve, and the
user is ready to update project instructions. Minimum migration plan:

- copy or move the full trace tree without dropping `search-set.md`
- preserve Active/Archived cases and raw trace files unchanged unless a merge is
  explicitly reviewed
- update `AGENTS.md` and any remaining project docs to name the new trace root
- write an evolution trace recording the migration source, destination, and
  verification result
- keep using `.claude/traces/` until the migration plan is applied

### Step 3: Create Trace Filesystem

Create:

```text
{trace_root}/evolution/
{trace_root}/failures/
{trace_root}/experiments/
{trace_root}/search-set.md
```

`search-set.md` must use the Active/Archived format from `core/reference.md` and contain at least one Active case with an executable `verify` command. Choose the most important command found during inspection, usually typecheck, tests, lint, or build.

Verify command discovery order:

1. package manager scripts or build-tool tasks (`package.json`, `pyproject.toml`,
   `Makefile`, `justfile`, `Taskfile`, language-native test config)
2. CI jobs that run locally without secrets or network access
3. README or project docs that name test/lint/typecheck/build commands
4. existing `AGENTS.md`, `CLAUDE.md`, or adapter instructions
5. direct framework defaults only when project files confirm the framework

Initial Active verify choices by project type:

- TypeScript/frontend: prefer typecheck, then focused tests, then lint/build.
- Python/backend/research: prefer focused tests, then lint/typecheck when
  configured, then evaluator smoke if the repo is research-oriented.
- Mixed/monorepo: prefer the narrow workspace command that covers the current
  harness risk before a repo-wide command.
- Fixed-evaluator research: prefer the evaluator command only when it is
  deterministic, local, non-interactive, and exits non-zero on regression.

Do not seed Active cases with commands that only print information. If network,
credentials, sandbox approval, missing dependencies, or high cost are
unavoidable, record that requirement in the search-set entry.

### Step 4: Write or Update AGENTS.md

If `AGENTS.md` exists, merge without overwriting. Keep it concise.

Required sections:

- Build: dev/build/test/lint/typecheck commands discovered from the project
- Architecture: only non-obvious boundaries that tools cannot infer
- Harness: trace root, search-set policy, change strategy, verification rule
- Harness: bounded self-evolution rule for dogfood-gap review and diagnostic
  trace/search-set/instruction candidates
- Codex Notes: permission/escalation or local workflow facts that affect Codex

Do not duplicate rules already enforced by linters, tests, or typecheckers. Mention the command instead.

### Step 5: Verification Discipline

Codex does not consume Claude Code `PostToolUse` hooks. Replace hook assumptions with explicit verification:

- Before meaningful harness changes, run Active `search-set.md` verify commands when practical.
- After code or harness changes, run the relevant verify commands.
- Record PASS/FAIL and key output lines in the evolution trace.

If verification is expensive or unsafe, record why it was skipped and what command should be run later.

### Step 6: Write Initial Evolution Trace

Write `{trace_root}/evolution/001-initial-codex-harness.md` with YAML frontmatter and sections for Trigger, Diagnosis, Change, Result, and Lesson.

Include trace retrieval provenance in the frontmatter:

- Use `retrieval.mode: not_needed` plus a short `reason` when the initial
  harness setup did not rely on prior trace history.
- Use `retrieval.mode: selective` plus byte-matching `raw_trace_refs` when the
  setup reuses existing `.claude/traces/` or `.harness/traces/` history.
- Treat trace catalogs as retrieval pointers only; cite raw evolution/failure
  traces when making a historical claim.
- If existing work suggests a dogfood gap, record only a diagnostic proposal:
  a concrete trigger-evidence pointer, affected surface, reusable future value,
  proposed action, and no automatic Active search-set edit or adoption claim.
  During ordinary work, surface at most one diagnostic maintenance note.

### Step 7: Completion Check

Confirm:

- Trace directories exist
- `search-set.md` has at least one Active executable `verify`
- `AGENTS.md` names the trace root and verification policy
- Initial evolution trace exists
- Initial evolution trace records `retrieval.mode`
- AGENTS.md says bounded self-evolution proposals are diagnostic until adopted
- No Claude-only hook configuration was added for Codex

## Output

Report:

- trace root chosen
- files created or changed
- Active search-set verify command
- verification result or reason skipped
- any Claude harness history reused
