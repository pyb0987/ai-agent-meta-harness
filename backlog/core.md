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

Status: 완료
Owner: Codex session codex-plugin-index-check worktree
Branch: codex/codex-plugin-index-check
Started: 2026-05-01
Scope:
- scripts/sync-codex-plugin.py
- tests/test_sync_codex_plugin.py
- backlog/core.md

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

Decision implemented for Codex generated plugin drift:

- `scripts/sync-codex-plugin.py --check` now reads canonical and generated
  plugin content from the Git index when run inside a Git worktree, matching
  pre-commit's staged-content contract.
- Generated plugin checks compare indexed file contents, executable modes,
  missing generated files, and extra generated files instead of unstaged
  working-tree content.
- Dynamic plugin mappings for skills, templates, scripts, and examples are
  discovered from the same staged view, so newly staged canonical files require
  corresponding staged generated files.
- Non-Git temp trees continue to use filesystem validation so the checker can
  still be unit-tested without a repository index.

Remaining follow-up work:

- Add temp-git staged-added coverage if the compatibility mirror contract starts
  accepting newly introduced mirror pairs during the transition period.

Verification:

- PASS: `python3 -m unittest tests/test_sync_codex_plugin.py`
- PASS: `python3 scripts/sync-codex-plugin.py --check`
- PASS: `python3 scripts/check-maintenance-review.py`
- PASS: `python3 scripts/check-compat-mirrors.py`
- PASS: `python3 scripts/check-claude-adapter-paths.py`
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
- Release-gate/index contract critic: score 10, verdict PASS, Blocking
  findings: none. Follow-up/residual risk: none; `--check` now validates the
  staged/index view used by pre-commit.
- Generated-artifact coverage critic: score 10, verdict PASS, Blocking
  findings: none. Follow-up/residual risk: none; tests cover unstaged
  generated drift, partially staged content and mode changes, staged-added
  canonical files, staged-added generated extras, and staged-deleted generated
  files.
- Maintenance compliance critic: score 9, verdict PASS, Blocking findings:
  none. Why not 10: review used the documented sequential fallback rather than
  isolated reviewers. No backlog item added because the residual risk is
  process-level review independence in this session, not an actionable
  repository change.
- Score handling: no critic scored below 9; no VETO triggered. The one score 9
  records why it was not 10 and does not create an actionable follow-up item.
- Rerun status: all sequential fallback critics reviewed the final scoped diff
  after verification passed; no VETO fixes required.
- Final acceptance: accepted and merged to `main` in commit
  `e7b985e merge: check codex plugin drift from index`.

### 11. Add maintenance review summary checker

Status: 완료
Owner: Codex session maintenance-review-standard-verify worktree
Branch: codex/maintenance-review-standard-verify
Started: 2026-05-01
Scope:
- MAINTENANCE.md
- backlog/core.md

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
- `MAINTENANCE.md` now includes
  `python3 scripts/check-maintenance-review.py` in the documented standard
  verification command set.
- The release checklist now requires maintenance review summaries to pass the
  checker so score, VETO, rerun, residual-risk, and final-acceptance handling
  stay explicit.

Remaining follow-up work:

- Add to pre-commit only after the review-summary format is stable enough to
  avoid noisy local failures.

Verification:

- PASS: `python3 scripts/check-maintenance-review.py`
- PASS: `python3 scripts/check-compat-mirrors.py`
- PASS: `python3 scripts/check-claude-adapter-paths.py`
- PASS: `python3 scripts/sync-codex-plugin.py --check`
- PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
- PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
- PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
- PASS: `python3 -m unittest discover -s tests`
- PASS: `python3 -m unittest discover -s adapters/claude/tests`
- PASS: `python3 -m unittest discover -s adapters/codex/tests`
- PASS: `rg -n "python3 scripts/check-maintenance-review.py|Maintenance review summaries pass|Add maintenance review summary checker|Remaining follow-up work" MAINTENANCE.md backlog/core.md`
- PASS: `git diff --check`
- Search-set verification: SKIPPED; no `search-set.md` exists in this
  repository worktree.

Review outcome:

- Multi-review mode: `FALLBACK_NONINDEPENDENT` sequential review; no independent
  sub-agents were requested for this worktree session.
- Release-gate contract critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the checker is now both in the standard
  verification command block and named in the release checklist.
- Verification completeness critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the full standard verification set plus
  focused search and whitespace checks passed.
- Backlog/process compliance critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the item has the required worktree
  reservation, verification, skipped search-set reason, review handling, and
  final review-ready status.
- Score handling: no critic scored below 9; no VETO triggered. No score was 9,
  so no why-not-10 residual-risk item was required.
- Rerun status: all sequential fallback critics reviewed the final scoped diff
  after verification passed.
- Final acceptance: accepted and merged to `main` in commit
  `cbf44e9 merge: add maintenance review checker to standard verification`.

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
- Follow-up/residual risk: add a short prompt-as-code example when a future
  core documentation pass needs concrete examples; the other score-9 concerns
  were addressed before acceptance.
- Score handling: no critic scored below 9; no VETO triggered. Every score 9
  recorded why it was not 10. The remaining actionable why-not-10 reason is
  already captured as remaining follow-up work above; rerun score-9 reasons
  were addressed in the final diff.
- Rerun status: affected critics were rerun after README/backlog updates; final
  scores were 9, 10, and 10.
- Final acceptance: accepted and merged to `main` in commit
  `e5c1410 docs: clarify prompt-as-code search boundary`.

### 13. Label sub-agent guidance as an applied extension

Status: 완료
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
- Final acceptance: accepted and merged to `main` in commit
  `ae81589 merge: label sub-agent guidance as runtime extension`.

### 14. Calibrate README evidence-level claims

Status: 완료
Owner: Codex session readme-evidence worktree
Branch: codex/readme-evidence-claims-main
Started: 2026-05-01
Scope:
- README.md
- backlog/core.md

The README says the listed principles come directly from experiments and
ablation studies. Some principles are directly supported by reported
experiments, while others, such as skill document quality and practical adapter
guidance, are better framed as engineering lessons inferred from applying the
methodology.

Decision implemented:

- README now says the project combines Meta-Harness experimental findings with
  engineering guidance from applying those findings to everyday agentic
  workflows.
- The Core Principles section distinguishes paper-backed findings from
  repository practice.
- Individual bullets preserve direct paper claims where cited, while adapter and
  harness-writing guidance is framed as repository practice unless a paper
  source is named.

Remaining follow-up work:

- Keep future README principle additions evidence-labeled when they mix paper
  claims with adapter practice.

Review outcome:

- Verification: PASS; `rg -n "experiments|ablation|paper-backed|engineering guidance|repository practice|principles" README.md backlog/core.md`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, and `python3 scripts/sync-codex-plugin.py --check`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because the README evidence framing affects core
  methodology claims future maintainers may rely on.
- Multi-review result: PASS; no reviewer scored below 9, so no VETO was
  triggered.
- Core evidence-boundary critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; the README now separates paper-backed
  claims from repository practice while preserving direct paper references.
- README reader-impact critic: score 9, verdict PASS, Blocking findings: none.
  Why not 10: README bullets remain compact instead of adding a full evidence
  matrix or per-claim citation table. No backlog item added because the residual
  risk is acceptable for a top-level README; detailed source mapping belongs in
  core docs or future paper/reference work if needed.
- Maintenance compliance critic: score 10, verdict PASS, Blocking findings:
  none. Follow-up/residual risk: none; scope, verification, search-set skip,
  score handling, and merge eligibility are recorded.
- Score handling: no critic scored below 9; no VETO triggered. The one score 9
  records why it was not 10 and does not create an actionable follow-up item.
- Rerun status: all critics reviewed the final scoped diff after verification
  passed; no VETO fixes required.
- Final acceptance: accepted and merged to `main` in commit
  `e8b4dea merge: calibrate readme evidence claims`.

## Current Status

- Source review: strict multi-review of `adapters/codex/skills/harness-engineer/SKILL.md`.
- Last reviewed baseline: `987dca0 fix: tighten codex harness engineer guardrails`.
- Recommended next quality pass: start with autoresearch detection heuristics, then trace-history tie-breakers, then verify-command quality rules.

### 15. Validate embedded backlog review outcomes

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- scripts/check-maintenance-review.py
- tests/test_check_maintenance_review.py
- backlog/core.md
- backlog/codex-adapter.md

The maintenance review checker currently validates `backlog/review-*.md` by
default, but accepted review outcomes are now also recorded directly inside
`backlog/core.md` and `backlog/codex-adapter.md`. This lets standard
verification pass while embedded `Review outcome:` sections can miss required
fields such as follow-up/residual risk, score handling, or rerun status.

Original improvement:

- Extend `scripts/check-maintenance-review.py` default paths to include backlog
  ownership files that contain embedded review outcomes.
- Add tests proving embedded `Review outcome:` sections in backlog files are
  checked by default.
- Fix existing embedded review records that fail the checker when checked
  explicitly.
- Keep the checker focused on review-result structure, not prose style.

Decision implemented:

- `scripts/check-maintenance-review.py` now validates
  `backlog/core.md`, `backlog/claude-adapter.md`, and
  `backlog/codex-adapter.md` by default alongside `backlog/review-*.md`.
- The default path list only includes existing ownership files, so missing
  adapter backlog files in reduced fixtures do not fail path discovery.
- `tests/test_check_maintenance_review.py` now proves default path discovery
  includes review summaries and backlog ownership files.
- Existing embedded review outcomes in `backlog/core.md` and
  `backlog/codex-adapter.md` pass the stricter default checker without further
  backfill.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `scripts/check-maintenance-review.py`,
  `tests/test_check_maintenance_review.py`, and `backlog/core.md`.
- Scope deviations: none; `backlog/codex-adapter.md` was in scope for
  validation/backfill but did not require edits.
- Verification results: PASS; `python3 -m unittest tests/test_check_maintenance_review.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-maintenance-review.py backlog/core.md backlog/codex-adapter.md`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes release-gate/review-checker
  default semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Default-path coverage critic score 10,
  verdict PASS, Blocking findings: none. Embedded-record compatibility critic
  score 10, verdict PASS, Blocking findings: none. Maintenance compliance
  critic score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 20. P1 harden low-score maintenance review validation

Source review: 2026-05-02 multi-review MIXED.

The maintenance review checker currently accepts a low-score record when broad
tokens such as `VETO`, `MIXED`, `FAIL`, or `not accepted` appear anywhere in
the record. A record can therefore say `No VETO` or otherwise mention the token
without concretely resolving the below-9 score.

Potential improvement:

- Tighten `scripts/check-maintenance-review.py` so scores below 9 require an
  explicit blocking disposition such as `VETO triggered`, `not accepted`, or a
  recorded rerun score at least 9.
- Reject negated or merely descriptive forms such as `No VETO` for below-9
  scores.
- Add tests proving low-score PASS with negated VETO language fails.
- Re-run `python3 scripts/check-maintenance-review.py` and
  `sh .githooks/pre-commit`.

### 21. P2 frame structural hardening as repository practice

Source review: 2026-05-02 multi-review MIXED.

The P5 structural-impossibility ladder and Single Source + Codegen + Protect
model are useful applied repository patterns, but they can read as first-class
Meta-Harness paper methodology beside P3/P4. The core should more clearly
separate paper-backed method claims from this repository's applied hardening
practice.

Potential improvement:

- Reframe the P5 escalation ladder and Single Source + Codegen + Protect
  section in `core/methodology.md` as an applied repository hardening pattern.
- Preserve the practical guidance while labeling what is paper core versus
  repository implementation discipline.
- Keep `docs/methodology.md` synchronized through compatibility mirror checks.

### 22. P2 subordinate sub-agent routing to the paper core

Source review: 2026-05-02 multi-review MIXED.

The sub-agent section is labeled as an applied runtime extension, but the
detailed routing rules can still make parallel critics feel like core
methodology. The paper core is the proposer/evaluator/trace loop; parallel
critics should remain clearly subordinate runtime tactics.

Potential improvement:

- Shorten or reframe detailed sub-agent routing in `core/methodology.md` so it
  is explicitly subordinate to the proposer/evaluator/trace loop.
- Move runtime-specific routing detail to adapters when it is not core
  methodology.
- Keep `docs/methodology.md` synchronized through compatibility mirror checks.

### 23. P3 label maintenance review policy as local release discipline

Source review: 2026-05-02 multi-review MIXED.

The score-9 explanation and below-9 VETO workflow are sensible governance for
this repository, but they are stronger than what the Meta-Harness paper itself
establishes. The docs should label this as local release discipline rather than
paper-derived methodology.

Potential improvement:

- Update `MAINTENANCE.md` review policy wording to frame score thresholds,
  score-9 explanations, VETO handling, and rerun requirements as repository
  governance/release discipline.
- Avoid implying those exact thresholds are paper claims.
- Keep the maintenance review checker behavior unchanged unless item 20 changes
  its enforcement semantics.

### 24. P3 reconcile stale accepted backlog statuses

Source review: 2026-05-02 multi-review MIXED.

Some previously accepted maintenance entries can remain marked `리뷰대기`, which
weakens handoff quality and regression memory even when implementation and
verification are already accepted.

Potential improvement:

- Audit backlog entries with `Status: 리뷰대기` whose Completion Gate already
  records accepted work.
- Move accepted entries to `완료` when the maintainer has accepted them, without
  changing unrelated implementation history.
- Add or adjust a lightweight maintenance check only if stale statuses recur.

### 19. Add prompt-as-code search example

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- core/methodology.md
- docs/methodology.md
- backlog/core.md

The prompt-as-code boundary now allows prompt templates, prompt-construction
code, generated candidates, and project instructions as search surfaces when
they are isolated, diffable, and evaluated. A short concrete example would help
maintainers distinguish evaluated prompt-as-code changes from vague prompt
tweaking.

Original improvement:

- Add a compact example of an acceptable evaluated prompt-as-code search
  surface.
- Add a contrasting non-example for vague natural-language exhortation.
- Keep the compatibility mirror synchronized with the canonical core
  methodology.

Decision implemented:

- `core/methodology.md` now includes a prompt-as-code example where candidate
  prompt templates live under an isolated path, run through the same fixed
  evaluator, and preserve raw output plus candidate diffs before promotion.
- The example contrasts that with vague prompt exhortation such as changing a
  prompt to "try harder" without evaluator execution, candidate isolation, or a
  raw diff/output trail.
- `docs/methodology.md` is synchronized as the temporary compatibility mirror.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `core/methodology.md`, `docs/methodology.md`, and
  `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS; `rg -n "Prompt-as-code example|prompts/candidates|try harder|raw diff/output trail|isolated, diffable|generated candidates" core/methodology.md docs/methodology.md backlog/core.md`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-maintenance-review.py`, `git diff --check`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this clarifies core methodology and
  fixed-evaluator search-surface semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Prompt-as-code boundary critic score 10,
  verdict PASS, Blocking findings: none. Compatibility mirror critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score
  9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 16. Enforce score-9 why-not-10 review handling

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- scripts/check-maintenance-review.py
- tests/test_check_maintenance_review.py
- backlog/review-2026-04-30-maintenance-recovery.md
- backlog/core.md

`MAINTENANCE.md` now requires every score of 9 to record why the score was not
10 and whether that reason produced a backlog item. The checker still treats
scores >= 9 as structurally accepted without validating the why-not-10 record,
so this policy is not mechanically enforced.

Original improvement:

- Update `scripts/check-maintenance-review.py` so every score 9 record requires
  a `Why not 10:` explanation or an equivalent explicit field.
- Require score-9 records or the section-level score handling to state whether
  the reason created a backlog item or was accepted as residual risk.
- Add tests that reject score-9 review records without why-not-10 handling.
- Backfill existing review records so the stricter checker can pass.

Decision implemented:

- `scripts/check-maintenance-review.py` now requires score 9 and 9.x review
  records to have why-not-10 handling either on the critic record or in the
  section-level score-handling record.
- Score-9 handling must also state a disposition through backlog follow-up,
  residual-risk acceptance, or resolution in the final reviewed diff.
- Review markers are recognized only as standalone `Multi-review:` or
  `Review outcome:` lines, so prose that mentions those labels does not become
  a false review section.
- `tests/test_check_maintenance_review.py` covers accepted score-9 handling,
  missing why-not-10 rejection, missing disposition rejection, section-level
  handling, and inline marker text.
- `backlog/review-2026-04-30-maintenance-recovery.md` now backfills historical
  score-9 why-not-10 and backlog/residual-risk disposition notes so the stricter
  checker passes.
- One existing embedded review outcome in this file was backfilled with
  follow-up/residual risk, score handling, and rerun status so explicit
  validation of `backlog/core.md` passes.

Remaining follow-up work:

- Complete `core.md` item 15 before adding embedded backlog review outcomes to
  the default checker path.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `scripts/check-maintenance-review.py`,
  `tests/test_check_maintenance_review.py`,
  `backlog/review-2026-04-30-maintenance-recovery.md`, and `backlog/core.md`.
- Scope deviations: `backlog/review-2026-04-30-maintenance-recovery.md` was
  added to Scope before editing because standard verification exposed existing
  score-9 records that needed backfill for the stricter checker.
- Verification results: PASS; `python3 -m unittest tests/test_check_maintenance_review.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-maintenance-review.py backlog/core.md`, `python3 scripts/check-maintenance-review.py backlog/core.md backlog/codex-adapter.md`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes release-gate/review-checker
  semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Checker correctness critic score 10,
  verdict PASS, Blocking findings: none. Historical-record compatibility critic
  score 9, verdict PASS, Blocking findings: none. Maintenance compliance critic
  score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Historical-record compatibility critic was 9
  because default validation still covers only `backlog/review-*.md`, while
  embedded backlog review outcomes remain tracked by item 15; no new backlog
  item added because that actionable follow-up already exists. Maintenance
  compliance critic was 9 because review used documented sequential fallback
  rather than independent sub-agents; no backlog item added because the residual
  risk is process-level review independence for this session, not a repository
  change.
- Backlog items added from score-9 residual risk: none; item 15 already tracks
  the actionable embedded-review default-path follow-up.
- Residual risk/follow-up: complete item 15 before default checker validation is
  expanded to embedded backlog review outcomes.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 17. Restore single-session maintenance pipeline

Status: 리뷰대기
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- MAINTENANCE.md
- backlog/README.md
- backlog/core.md

Parallel worktree maintenance exposed process failure modes: sessions tried to
touch too few files even when the correct change crossed boundaries, ownership
became diffuse enough to create a bystander effect, and reviewers lacked enough
shared context to apply `MAINTENANCE.md`, multi-review, and iteration rules
consistently. The repository should return to the earlier single-session
maintenance model unless a future coordination mechanism proves these risks are
controlled.

Decision implemented:

- `MAINTENANCE.md` now makes one active maintenance session at a time the
  routine maintenance model.
- The session gate keeps explicit item selection, expected scope, verification,
  multi-review, VETO iteration, score-9 follow-up, and final acceptance.
- Parallel worktree maintenance is now framed as exceptional recovery or
  explicitly requested split work, not the default backlog workflow.
- `backlog/README.md` now directs maintainers to complete one item in one
  active session before starting another.
- The observed failure modes are recorded here so future maintainers do not
  reintroduce parallel routine maintenance without stronger shared-context and
  ownership controls.

Remaining follow-up work:

- Update any external prompt snippets or operator playbooks that still ask
  routine maintenance sessions to create separate worktrees.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `MAINTENANCE.md`, `backlog/README.md`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS; `rg -n "Single-Session Maintenance|Exceptional Parallel Worktree Recovery|Parallel Worktree Coordination|Worktree Session Gates|Routine maintenance should run through one active session" MAINTENANCE.md backlog/README.md`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, and `git diff --check`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes the repository maintenance
  process and future backlog operating model.
- Multi-review result: PASS; no critic scored below 9.
- Reviewer scores and VETO handling: Maintenance process critic score 10,
  verdict PASS, Blocking findings: none. Gate-preservation critic score 9,
  verdict PASS, Blocking findings: none. Backlog discoverability critic score
  9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Gate-preservation critic was 9 because the
  external session prompts still need to be updated outside the repository
  files; recorded as remaining follow-up work above. Backlog discoverability
  critic was 9 because the new items live after `Current Status`; accepted as
  residual risk because backlog theme indexing now points to item 17 and a
  larger backlog reorganization is not needed for this change.
- Residual risk/follow-up: update external prompts/playbooks before launching
  new routine maintenance sessions.
- Accepted: yes, ready for maintainer review and commit.

### 18. Add maintenance review checker to pre-commit

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- .githooks/pre-commit
- README.md
- MAINTENANCE.md
- tests/test_pre_commit_hook.py
- backlog/core.md

The maintenance review checker is now stable enough to validate embedded
backlog review outcomes and score-9 handling by default. It should move from
standard verification only into the tracked pre-commit hook so review-summary
policy drift is caught before commit.

Original improvement:

- Run `python3 scripts/check-maintenance-review.py` from `.githooks/pre-commit`.
- Update repository docs that enumerate pre-commit checks.
- Add a lightweight test so the tracked hook does not silently drop the
  maintenance review checker.

Decision implemented:

- `.githooks/pre-commit` now runs
  `python3 scripts/check-maintenance-review.py` after the drift and smoke
  checks.
- README and `MAINTENANCE.md` now describe the tracked hook as running the
  maintenance review checker in addition to drift and smoke checks.
- `tests/test_pre_commit_hook.py` asserts the tracked hook continues to invoke
  the maintenance review checker.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `.githooks/pre-commit`, `README.md`, `MAINTENANCE.md`,
  `tests/test_pre_commit_hook.py`, and `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 scripts/check-maintenance-review.py`, `sh .githooks/pre-commit`, `python3 -m unittest tests/test_pre_commit_hook.py`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes tracked pre-commit/release
  gate behavior.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Pre-commit gate critic score 10, verdict
  PASS, Blocking findings: none. Review-checker noise critic score 9, verdict
  PASS, Blocking findings: none. Documentation sync critic score 10, verdict
  PASS, Blocking findings: none. Maintenance compliance critic score 9, verdict
  PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Review-checker noise critic was 9 because
  pre-commit now validates all embedded review outcomes and could block commits
  when future backlog records are incomplete; no backlog item added because
  that stricter behavior is the intended repository protection and the checker
  has passed on current records. Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.
