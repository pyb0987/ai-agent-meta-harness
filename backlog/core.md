# Core Backlog

Agent-agnostic quality backlog for the shared Meta-Harness methodology. These items came from the strict multi-review of the Codex `harness-engineer` skill, but their ownership belongs in the shared core because they apply across agents.

## Priority Candidates

### 1. Add fixed-evaluator search-loop detection heuristics

Current adapter wording can leave fixed-evaluator/search-loop detection to the
agent without a shared abstraction.

Decision implemented:

- `core/methodology.md` now defines adapter-neutral detection signals for a
  direction file, mutable search surface, immutable evaluator boundary,
  machine-readable experiment log, and episode traces.
- The rule requires nearby docs, project instructions, scripts, and traces to
  be inspected when only one signal exists.
- Conflicting signals must be recorded as uncertainty instead of triggering
  fixed-evaluator-specific changes blindly.

Remaining follow-up work:

- Let adapters add runtime-specific examples only when they differ from the
  shared signal model.

### 2. Define meaningful trace history tie-breakers

When more than one trace root or trace history exists, the harness should define how to choose the active history.

Decision implemented:

- `core/methodology.md` now selects active trace history by evidence instead of
  path preference alone.
- Roots with `search-set.md` Active cases, unresolved failures, recent
  evolution entries, or relevant experiment episodes outrank empty/template
  roots.
- Runtime adapter defaults only break ties when history evidence is absent or
  equivalent.
- Divergent non-empty roots are treated as migration questions that need a
  copy/move/merge plan before new traces are written.

Remaining follow-up work:

- Let adapters define their concrete source and destination paths for migration.

### 3. Strengthen Active seed verification quality rules

The methodology requires auto-executable verify commands, but should define what makes one good enough.

Decision implemented:

- `core/reference.md` now defines verify command quality rules for Active
  search-set entries.
- Verify commands must be deterministic, non-interactive, regression-sensitive,
  and non-zero on recurrence.
- Local, low-cost commands are preferred, and unavoidable sandbox, permission,
  network, dependency, or fixture requirements must be recorded.
- Print-only commands are rejected unless they pipe into an assertion.

Remaining follow-up work:

- Add mechanical validation only if search-set entries become machine-parsed in
  this repository.

## Later Improvements

### 4. Handle partially initialized trace roots

A trace root may exist while one or more required subdirectories or files are missing.

Decision implemented:

- `core/methodology.md` now requires checking the selected trace root for
  `evolution/`, `failures/`, `experiments/`, and `search-set.md`.
- Applied harness changes must create missing minimum trace infrastructure
  before writing traces.
- Diagnosis-only work should report missing trace infrastructure instead of
  silently expanding the project.

Remaining follow-up work:

- Let adapters define the exact empty `search-set.md` template they install.

### 5. Specify Archived case restore and re-archive workflow

The methodology allows restoring Archived search-set cases but should define when to re-archive them.

Decision implemented:

- `core/reference.md` now defines when to restore Archived search-set cases:
  recurring failure class, changed prevention mechanism, or Active coverage
  dropping to zero.
- Restored cases preserve original Source/Symptom/verify fields and require a
  related trace note explaining why the case became relevant again.
- Re-archive only after updated prevention passes, and refresh
  `archived_reason` with date and reason.

Remaining follow-up work:

- Add parser-level support only if search-set migration becomes automated.

### 6. Expand standalone fixed-evaluator reference details

Standalone users may benefit from a short relationship map around
fixed-evaluator trace artifacts.

Decision implemented:

- `core/reference.md` states that machine-readable experiment logs record
  "what" while episode traces record diagnostic "why".
- Episode timing rules clarify that multiple episode files may be written in one
  session.
- The reference now includes a minimum exhausted-axis research-state example
  that adapters can map to their concrete files.

Remaining follow-up work:

- Adapter examples may name concrete state files when a runtime chooses one.

### 7. Define documentation abstraction boundaries

The repository now has a shared core plus runtime adapters. The boundary should be made explicit so future work does not duplicate methodology across adapters.

Decision implemented:

- `core/methodology.md` now defines core-owned what/why surfaces and
  adapter-owned runtime how surfaces.
- Adapter docs may reference core rules but should not fork large methodology
  blocks unless runtime behavior truly differs.
- Review should treat copied methodology blocks in adapters as drift risks.

Remaining follow-up work:

- Add mechanical duplicate-block detection only if drift recurs.

### 8. Plan compatibility mirror removal

Temporary top-level Claude paths are currently retained as compatibility mirrors. They need a removal plan before they become permanent accidental API.

Decision implemented:

- `MAINTENANCE.md` now defines the compatibility mirror lifecycle for top-level
  `docs/`, `commands/`, and `skills/`.
- Mirrors stay until at least one stable handoff after canonical Claude install
  commands and old mirrored install commands both have smoke coverage.
- Removal requires README/release-note warning for one transition window,
  continued drift checks until removal, migration guidance, and an explicit
  decision between fail-fast old commands or thin redirect docs.
- README points maintainers to `MAINTENANCE.md` for the removal lifecycle.

Remaining follow-up work:

- Execute the warning/removal plan only after old Claude install smoke coverage
  exists.

### 9. Define repository release checklist

Release readiness should be verified with a stable checklist instead of ad hoc manual review.

Decision implemented:

- `MAINTENANCE.md` now defines verification tiers, the standard verification
  set, release checklist, test policy, multi-review use, and backlog pointers
  for current planning.

Remaining follow-up work:

- Add skill frontmatter validation if skill metadata grows beyond current
  smoke-test coverage.
- Add adapter install smoke tests as the Claude and Codex install paths become
  mechanically executable.
- Add old Claude install command smoke test while compatibility mirrors exist.
- Add Codex activation smoke test for the chosen primary distribution path.
- Add release note policy when versioned releases begin.

### 10. Make repository drift checks staged-content-aware

Pre-commit checks should validate the content that will actually be committed,
not only the current working tree. The Claude adapter path checker already reads
indexed files, but other repository drift checks should converge on the same
semantics.

Decision implemented for compatibility mirrors:

- `scripts/check-compat-mirrors.py` now checks the fixed required mirror path
  list against the Git index and reads canonical/mirror contents with
  `git show :path`.
- Unstaged working-tree drift does not affect pre-commit results.
- Staged mirror drift and staged deletion of required canonical/mirror files
  fail the check.
- Temp-git integration tests cover unstaged drift, staged modified mirrors, and
  staged deleted mirrors.

Remaining follow-up work:

- Decide whether generated artifact checks should use index content, working
  tree content, or an explicit mode flag.
- Make `scripts/sync-codex-plugin.py --check` safe for pre-commit by validating
  the staged/index view of generated plugin content and executable modes, or by
  adding an explicit staged mode. Cover partially staged commits where generated
  content or mode changes are omitted from the index.
- Add tests for staged-added, staged-modified, and staged-deleted paths that are
  relevant to generated-artifact drift.
- Add temp-git staged-added coverage if the compatibility mirror contract starts
  accepting newly introduced mirror pairs during the transition period.

### 11. Add maintenance review summary checker

`MAINTENANCE.md` now requires multi-review summaries to record critic scope,
score, verdict, blocking findings, follow-up/residual risk, score handling,
rerun status, and final acceptance. It also treats reviewer scores below 9 as
VETO. Those rules should be mechanically checked so future maintenance work does
not rely on memory.

Decision implemented:

- Added `scripts/check-maintenance-review.py` to validate tracked
  `backlog/review-*.md` summaries.
- The checker fails when a required critic score below 9 lacks VETO or
  not-accepted handling.
- The checker fails when unresolved `pending`, active re-review, or not-yet
  accepted status remains in rerun/final-acceptance fields.
- The checker fails when required review fields are missing from a multi-review
  or review-outcome section.
- Tests cover accepted score 9, rejected score 8, pending review status, and
  missing required fields.

Remaining follow-up work:

- Start as a standard verification command; add to pre-commit only after the
  format is stable enough not to create noisy local failures.
- Add `python3 scripts/check-maintenance-review.py` to the documented standard
  verification set before relying on review-summary enforcement as a release
  gate. Add it to pre-commit only after the summary format is stable enough to
  avoid noisy local failures.

### 12. Clarify prompt-as-code search boundary

Status: 완료
Owner: Codex session prompt-boundary worktree
Branch: codex/prompt-as-code-boundary
Started: 2026-05-01
Scope:
- core/methodology.md
- docs/methodology.md
- README.md
- backlog/core.md

The core methodology currently risks over-forbidding prompt edits by saying
agents modify code/configuration, not natural language prompts. That matches the
anti-pattern of vague exhortation-only prompt tweaks, but it can incorrectly
exclude executable prompt-template or prompt-construction changes that are
isolated, versioned, and evaluated like other code-space changes.

Decision implemented:

- `core/methodology.md` and its temporary compatibility mirror
  `docs/methodology.md` now define P4 search surfaces as isolated, diffable,
  versioned, executable surfaces instead of only code/configuration files.
- Prompt templates, prompt-construction code, generated candidates, hooks,
  skill documents, and project instructions can be search space only when they
  are evaluated by the same verifier and preserve an isolation/diff trail.
- Vague natural-language exhortation rewrites such as "try harder" remain an
  anti-pattern when they lack an evaluator, isolation boundary, or raw diff
  trail.
- The README summary now mirrors the same distinction for top-level readers.

Remaining follow-up work:

- Add a short prompt-as-code example that distinguishes generated candidates or
  project instructions used as evaluated search surfaces from vague prompt
  tweaking.

Review outcome:

- Verification: PASS; `rg -n "natural language prompts|prompt-as-code|try harder|mutable search surface|Code-space search|isolated, diffable|prompt-construction" README.md core/methodology.md docs/methodology.md backlog/core.md`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/sync-codex-plugin.py --check`, and `python3 adapters/codex/scripts/smoke-local-plugin.py`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because the change affects core methodology
  boundaries and durable fixed-evaluator/search-surface semantics.
- Multi-review result: PASS; no reviewer scored below 9, so no VETO was
  triggered.
- Core methodology boundary critic: score 9, verdict PASS, Blocking findings:
  none. Why not 10: generated candidates and project instructions would benefit
  from a concrete example; recorded as remaining follow-up work above. Rerun
  after README/backlog updates: score 9, verdict PASS.
- Fixed-evaluator/search-loop critic: initial score 9, verdict PASS, Blocking
  findings: none. Why not 10: README should mirror the isolation/diffability
  guardrail; addressed by updating README and rerunning the critic. Rerun score
  10, verdict PASS.
- Maintenance/backlog compliance critic: initial score 9, verdict PASS,
  Blocking findings: none. Why not 10: Completion Gate details still needed.
  Addressed by updating this backlog record and rerunning the critic. Rerun
  score 10, verdict PASS.
- Final acceptance: accepted and merged to `main` in commit
  `e5c1410 docs: clarify prompt-as-code search boundary`.

### 13. Label sub-agent guidance as an applied extension

Status: 리뷰대기
Owner: Codex session prompt-contract worktree
Branch: codex/prompt-as-code-contract
Started: 2026-05-01
Scope:
- core/methodology.md
- docs/methodology.md
- README.md
- backlog/core.md

The sub-agent section was useful operational guidance, but it could read as if
parallel critics or isolated evaluator contexts were part of the paper's core
Meta-Harness claim. The paper's core loop is a coding-agent proposer using
filesystem evidence, scores, and traces; sub-agents are an adapter/runtime
mechanism layered on top.

Decision implemented:

- `core/methodology.md` and its temporary compatibility mirror
  `docs/methodology.md` now label sub-agent usage as an applied runtime
  extension rather than the paper's core claim.
- The section keeps the contamination/isolation guidance while framing
  sub-agents, external reviewers, sequential checklists, and fixed evaluator
  scripts as runtime mechanisms selected by adapters.
- README multi-review flow now names sub-agents as one isolation mechanism and
  documents external review or separated sequential checklist fallback when
  isolated sub-agents are unavailable.

Remaining follow-up work:

- Adapter docs may update runtime-specific wording only when their local
  mechanism names or capabilities diverge from the shared framing.

Verification:

- PASS: `python3 scripts/check-compat-mirrors.py`
- PASS: `python3 scripts/check-claude-adapter-paths.py`
- PASS: `python3 scripts/sync-codex-plugin.py --check`
- PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
- PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
- PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
- PASS: `python3 -m unittest discover -s tests`
- PASS: `python3 -m unittest discover -s adapters/claude/tests`
- PASS: `python3 -m unittest discover -s adapters/codex/tests`
- PASS: `git diff --check`
- Search-set verification: SKIPPED; no `search-set.md` exists in this
  repository worktree.

Review outcome:

- Multi-review mode: `FALLBACK_NONINDEPENDENT` sequential review; no independent
  sub-agents were requested for this worktree session.
- Core-boundary critic: score 10, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: none; the section now explicitly separates the
  paper's core loop from applied runtime mechanisms.
- Adapter-compatibility critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the heading keeps `Sub-Agent Invocation`
  for existing adapter references while adding the applied-extension label.
- Verification/backlog critic: score 10, verdict PASS, Blocking findings: none.
  Follow-up/residual risk: none; standard verification, skipped search-set
  reason, scope, and review handling are recorded.
- Score handling: no critic scored below 9; no VETO triggered. No score was 9,
  so no why-not-10 residual-risk item was required.
- Rerun status: all sequential fallback critics reviewed the final scoped diff
  after verification passed.
- Final acceptance: ready for merge coordination.

### 14. Calibrate README evidence-level claims

The README says the listed principles come directly from experiments and
ablation studies. Some principles are directly supported by reported
experiments, while others, such as skill document quality and practical adapter
guidance, are better framed as engineering lessons inferred from applying the
methodology.

Potential improvement:

- Separate "paper-backed experimental findings" from "engineering guidance used
  by this repository".
- Avoid implying every README principle is ablation-backed when some are
  practical harness-writing lessons.
- Preserve the strong claims where the paper or traces directly support them,
  but lower the evidence level for repository-specific adapter practices.

## Current Status

- Source review: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md`.
- Last reviewed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Recommended next quality pass: start with autoresearch detection heuristics, then trace-history tie-breakers, then verify-command quality rules.
