# Core Backlog

Agent-agnostic quality backlog for the shared Meta-Harness methodology. These items came from the strict multi-review of the Codex `harness-engineer` skill, but their ownership belongs in the shared core because they apply across agents.

## Priority Candidates

### 1. Add fixed-evaluator search-loop detection heuristics

Status: 완료
Archived: `backlog/archive/core.md#1-add-fixed-evaluator-search-loop-detection-heuristics`

### 2. Define meaningful trace history tie-breakers

Status: 완료
Archived: `backlog/archive/core.md#2-define-meaningful-trace-history-tie-breakers`

### 3. Strengthen Active seed verification quality rules

Status: 완료
Archived: `backlog/archive/core.md#3-strengthen-active-seed-verification-quality-rules`

### 4. Handle partially initialized trace roots

Status: 완료
Archived: `backlog/archive/core.md#4-handle-partially-initialized-trace-roots`

### 5. Specify Archived case restore and re-archive workflow

Status: 완료
Archived: `backlog/archive/core.md#5-specify-archived-case-restore-and-re-archive-workflow`

### 6. Expand standalone fixed-evaluator reference details

Status: 완료
Archived: `backlog/archive/core.md#6-expand-standalone-fixed-evaluator-reference-details`

### 7. Define documentation abstraction boundaries

Status: 완료
Archived: `backlog/archive/core.md#7-define-documentation-abstraction-boundaries`

### 8. Plan compatibility mirror removal

Status: 완료
Archived: `backlog/archive/core.md#8-plan-compatibility-mirror-removal`

### 9. Define repository release checklist

Status: 완료
Archived: `backlog/archive/core.md#9-define-repository-release-checklist`

### 10. Make repository drift checks staged-content-aware

Status: 완료
Archived: `backlog/archive/core.md#10-make-repository-drift-checks-staged-content-aware`

### 11. Add maintenance review summary checker

Status: 완료
Archived: `backlog/archive/core.md#11-add-maintenance-review-summary-checker`

### 12. Clarify prompt-as-code search boundary

Status: 완료
Archived: `backlog/archive/core.md#12-clarify-prompt-as-code-search-boundary`

### 13. Label sub-agent guidance as an applied extension

Status: 완료
Archived: `backlog/archive/core.md#13-label-sub-agent-guidance-as-an-applied-extension`

### 14. Calibrate README evidence-level claims

Status: 완료
Archived: `backlog/archive/core.md#14-calibrate-readme-evidence-level-claims`

### 15. Validate embedded backlog review outcomes

Status: 완료
Archived: `backlog/archive/core.md#15-validate-embedded-backlog-review-outcomes`

### 20. P1 harden low-score maintenance review validation

Status: 완료
Archived: `backlog/archive/core.md#20-p1-harden-low-score-maintenance-review-validation`

### 21. P2 frame structural hardening as repository practice

Status: 완료
Archived: `backlog/archive/core.md#21-p2-frame-structural-hardening-as-repository-practice`

### 22. P2 subordinate sub-agent routing to the paper core

Status: 완료
Archived: `backlog/archive/core.md#22-p2-subordinate-sub-agent-routing-to-the-paper-core`

### 23. P3 label maintenance review policy as local release discipline

Status: 완료
Archived: `backlog/archive/core.md#23-p3-label-maintenance-review-policy-as-local-release-discipline`

### 24. P3 reconcile stale accepted backlog statuses

Status: 완료
Archived: `backlog/archive/core.md#24-p3-reconcile-stale-accepted-backlog-statuses`

### 25. P1 make maintenance review checker staged-content aware

Status: 완료
Archived: `backlog/archive/core.md#25-p1-make-maintenance-review-checker-staged-content-aware`

### 26. P3 label README autoresearch filenames as repository conventions

Status: 완료
Archived: `backlog/archive/core.md#26-p3-label-readme-autoresearch-filenames-as-repository-conventions`

### 27. P3 refresh core backlog Current Status guidance

Status: 완료
Archived: `backlog/archive/core.md#27-p3-refresh-core-backlog-current-status-guidance`

## Current Status

- Completed core records with `Status: 완료` or legacy `Decision implemented`
  summaries now live in `backlog/archive/core.md` with short pointers retained
  here.
- Active core backlog has unstarted concrete items from the 2026-05-04
  current-main methodology reviews: item 47 should thicken repository self-application trace
  evidence beyond the initial trace-root scaffold, item 48 should bundle release
  verification into one executable gate, item 49 should prevent default unittest
  discovery from looking like a valid release signal, item 50 should harden
  search-set evidence text matching, item 51 should keep Current Status aligned
  with completed items, and item 52 should schema-check repository
  self-application evolution traces. Items 41-46 are complete or ready for
  maintainer review, so future
  maintenance should not select them as available implementation candidates.
- Recent adapter follow-ups in `backlog/claude-adapter.md` items 10-12,
  `backlog/codex-adapter.md` items 27-34, and core process item 31 are
  complete; use new backlog entries for newly discovered work rather than
  treating these completed items as available candidates.

### 34. P3 refresh active backlog status after core trace-schema boundary item

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- backlog/core.md

Source discussion: 2026-05-04 maintainer request to continue after completing
core item 32.

The active `Current Status` block still said item 32 was the one unstarted core
implementation item, even though item 32 is now complete. That stale summary can
make future single-session maintenance reselect completed work instead of
reporting that no concrete unstarted item remains.

Decision implemented:

- Updated `Current Status` to state that active core backlog currently has no
  unstarted concrete implementation item.
- Recorded item 32 as complete rather than available for selection.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting status cleanup.
- Multi-review required: no; this is backlog status-summary cleanup only.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no
  VETO path.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 46. P2 add executable repository search-set runner

Status: 리뷰대기
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- scripts/run-search-set.py
- tests/test_run_search_set.py
- MAINTENANCE.md
- backlog/core.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The repository now has an Active self-application search-set at
`.harness/traces/search-set.md`, and standard verification currently runs the
same important checks. The operational review still found a gap: the repository
does not yet provide a generic command that parses Active `verify` entries from
the selected search-set and executes them as the search-set itself. That leaves
the "executable trace memory" contract partly dependent on humans copying the
commands or on standard verification happening to overlap the Active set.

Potential improvement:

- Add a small script, likely `scripts/run-search-set.py`, that reads a
  `search-set.md`, extracts Active `verify` commands, and runs either all
  Active entries or a selected subset.
- Preserve command exit status and print enough context to diagnose which
  search-set case failed.
- Default to `.harness/traces/search-set.md` for this repository, while
  allowing an explicit path for target-project use.
- Keep parsing conservative; fail closed on malformed Active entries rather
  than silently skipping them.
- Add focused tests that cover Active/Archived boundaries, failing commands,
  selected IDs, malformed entries, and command output reporting.

Done when:

- A maintainer can run one command to execute this repository's Active
  `.harness/traces/search-set.md` verify entries without manually copying them.
- The runner fails if an Active case has no executable `verify` command or if
  any selected verify command fails.
- `MAINTENANCE.md` and/or the search-set guidance names the runner as the
  preferred way to execute Active repository self-application cases.
- Focused tests cover the parser and failure behavior.
- Multi-review checks the result because this changes verification policy and
  search-set execution semantics.

Implementation notes:

- Added `scripts/run-search-set.py`, a conservative Active search-set runner
  that defaults to `.harness/traces/search-set.md`, supports repeated `--case`
  filters, lists cases with `--list`, fails on missing or duplicate Active
  `verify` lines, and returns non-zero when any selected verify command fails.
- Added focused parser and runner tests for Active/Archived boundaries, missing
  verify lines, selected IDs, unknown IDs, failing commands, and list mode.
- Updated `MAINTENANCE.md` to name `python3 scripts/run-search-set.py` as the
  preferred repository self-application Active search-set execution command.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/run-search-set.py`.
- after: PASS `python3 scripts/run-search-set.py --list`.
- after: PASS `python3 scripts/run-search-set.py --case SS-001 --case SS-002`.
- after: PASS `python3 -m unittest tests/test_run_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.
- after: PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`.

Review notes:

- Initial isolated reviewer score: 8/10 VETO. Blocking findings: missing
  Completion Gate / search-set evidence record, and risk of staging unrelated
  pre-existing backlog additions with the item 46 commit.
- First VETO handling: added search-set evidence and commit-scope notes.
- First re-review score: 8/10 VETO. Blocking findings: item still lacked full
  Completion Gate, `리뷰대기` status, and required multi-review score record.
- Second VETO handling: added the full Completion Gate below, changed backlog
  status to `리뷰대기`, and will request another isolated re-review before
  staging or committing.

Multi-review:

- Result: PASS after VETO handling and final isolated re-review.
- Isolated maintenance reviewer, initial: score 8/10; verdict VETO; Blocking
  findings: missing Completion Gate/search-set evidence and contaminated commit
  scope risk; not accepted until VETO findings were fixed and rerun.
- Isolated maintenance reviewer, first rerun: score 8/10; verdict VETO;
  Blocking findings: missing full Completion Gate, `리뷰대기` status, and
  required multi-review score record; not accepted until VETO findings were
  fixed and rerun.
- Isolated maintenance reviewer, final rerun: score 9/10; verdict PASS;
  Blocking findings: none. Why not 10: final review-record closure was still
  pending at the moment of review; no backlog follow-up because this is a
  procedural closure step completed in this record.
- Score handling: scores below 9 were treated as VETO. Blocking findings were
  addressed before rerun; final rerun reached 9/10.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: final isolated re-review completed after Completion Gate
  correction; score 9/10 PASS.
- Final acceptance: accepted; ready for commit with item 46-only staging.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `scripts/run-search-set.py`, `tests/test_run_search_set.py`,
  `MAINTENANCE.md`, `backlog/core.md`.
- Scope deviations: none for item 46 implementation. The worktree also contains
  pre-existing backlog-seeding edits in `backlog/README.md`,
  `backlog/claude-adapter.md`, `backlog/codex-adapter.md`, and broader
  `backlog/core.md` hunks for items 47-52; those are not part of the item 46
  commit and must not be staged with it.
- Verification results: PASS `python3 -m unittest tests/test_run_search_set.py`;
  PASS `python3 scripts/run-search-set.py --list`; PASS `python3
  scripts/run-search-set.py --case SS-001 --case SS-002`; PASS `python3
  scripts/run-search-set.py`; PASS `python3 scripts/check-maintenance-review.py`;
  PASS `python3 scripts/check-compat-mirrors.py`; PASS `python3 -m unittest
  discover -s tests`; PASS `python3 -m unittest discover -s
  adapters/claude/tests`; PASS `python3 -m unittest discover -s
  adapters/codex/tests`; PASS `python3 -m unittest tests/test_pre_commit_hook.py`;
  PASS `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`;
  PASS `python3 -m unittest tests/test_repository_search_set.py`; PASS `sh
  .githooks/pre-commit`; PASS `python3 scripts/check-search-set-evidence.py`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above. The after set includes `python3 scripts/run-search-set.py`,
  which executed all six Active repository cases successfully.
- Multi-review required: yes; verification policy and search-set execution
  semantics.
- Multi-review result: PASS after final isolated re-review.
- Reviewer scores and VETO handling: initial isolated reviewer 8/10 VETO; first
  rerun 8/10 VETO; both VETO blocking findings addressed; final isolated
  reviewer rerun 9/10 PASS.
- For each score-9 result, why not 10: final review-record closure was still
  pending at the moment of final review; accepted as procedural residual because
  this record now closes it.
- Backlog items added from score-9 residual risk: none; no actionable
  repository improvement.
- Residual risk/follow-up: none.
- Accepted: yes; ready for item 46-only commit.

### 47. P2 thicken repository self-application trace evidence

Status: 대기

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The repository has the required `.harness/traces/` surface and an Active
search-set, but its tracked self-application evidence is still thin:
`failures/` and `experiments/` only contain placeholders, and the initial
evolution trace records that legacy `.claude/traces/` history was not copied.
That is acceptable as a bootstrap state, but it means trace reuse is more
prospective than demonstrated for the repository's own maintenance loop.

Potential improvement:

- Add a follow-up evolution trace summarizing the 2026-05-04 methodology
  multi-review result, including the specific concern that self-application raw
  evidence is thin.
- If local `.claude/traces/` contains reusable non-sensitive lessons, create a
  reviewed migration or summary trace under `.harness/traces/` without copying
  provider/session-local content blindly.
- Add a failure trace only if there is a concrete repository harness failure or
  review VETO with reusable diagnostic value; do not manufacture failures just
  to populate the directory.
- Consider adding a short trace index or maintenance note that tells future
  maintainers how to decide whether a legacy local trace is safe to summarize.

Done when:

- `.harness/traces/evolution/` contains at least one substantive repository
  self-application review or maintenance trace beyond the initial root
  bootstrap.
- Any legacy `.claude/traces/` reuse decision is documented as copied,
  summarized, intentionally excluded, or deferred with a concrete reason.
- The repository does not claim richer self-application evidence than it has;
  `failures/` and `experiments/` may remain empty if no qualifying raw evidence
  exists.
- Search-set verification or an explicit skipped reason is recorded for the
  trace-writing change.

### 48. P2 add one executable release verification gate

Status: 대기

Source review: 2026-05-04 executable-implementation critic in the current-main
methodology multi-review.

`MAINTENANCE.md` documents a Standard verification set and release checklist,
but the full stable-handoff gate is still a Markdown checklist rather than one
executable command. `.githooks/pre-commit` intentionally runs a lighter subset
and omits clean-worktree verification, activation smoke, unit suites, and full
search-set evidence checks. That is acceptable for commit-time latency, but it
means a maintainer can accidentally skip release-only checks while still seeing
pre-commit pass.

Potential improvement:

- Add a script such as `scripts/verify-release.py` or
  `scripts/verify-standard.py` that runs the documented Standard verification
  commands in order and returns non-zero on the first failure or with a clear
  summary of failures.
- Include clean-worktree verification, compatibility/generated drift checks,
  Codex activation smoke, marketplace metadata check, maintenance review
  checks, and the three explicit unittest discovery roots.
- Keep `.githooks/pre-commit` as the lighter index-oriented gate unless this
  item explicitly changes pre-commit policy.
- Document the new command in `MAINTENANCE.md` as the preferred stable-handoff
  command.

Done when:

- A maintainer can run one local command before treating `main` as a stable
  handoff point.
- The command does not rely on plain root-level `python3 -m unittest discover`
  as a success signal.
- Focused tests or a dry-run/list mode protect the command list from drifting
  away from `MAINTENANCE.md`.
- Multi-review checks the result because this changes release-gate semantics.

### 49. P3 guard against root unittest discovery false greens

Status: 대기

Source review: 2026-05-04 executable-implementation critic in the current-main
methodology multi-review.

The documented verification commands correctly run `python3 -m unittest
discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and
`python3 -m unittest discover -s adapters/codex/tests`. However, plain
`python3 -m unittest discover` from the repository root reports zero tests. A
generic CI runner or maintainer muscle memory could treat that false green as
test coverage even though it exercises none of the implementation suites.

Potential improvement:

- Decide whether to add root-level test discovery glue, a clear failing sentinel,
  or documentation/tooling that explicitly forbids using plain
  `python3 -m unittest discover` as a release signal.
- Prefer the smallest change that prevents accidental false confidence while
  keeping the existing explicit suite commands intact.
- If item 48 adds a release verification script first, this item may be handled
  by making that script and docs the canonical test entrypoint.

Done when:

- A maintainer or CI configuration cannot easily report a passing root-level
  unittest run with zero tests and mistake it for repository verification.
- The Standard verification docs continue to name all three real unittest roots.
- Focused tests or documentation checks cover the chosen behavior.

### 50. P2 harden search-set evidence checker text matching

Status: 대기

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`scripts/check-search-set-evidence.py` now makes search-set before/after
evidence mechanically visible, but the parser accepts weak text: any occurrence
of `skipped`, or any section containing both `before` and `after`, satisfies the
gate. Text such as `not skipped`, TODO prose, or vague notes can pass without
concrete Active search-set results or an explicit skipped reason. That weakens
the repository's regression-memory loop for harness-affecting changes.

Potential improvement:

- Require structured `BEFORE:` / `AFTER:` records with PASS/FAIL/SKIPPED
  status, or a structured `SKIPPED:` reason.
- Reject ambiguous negations such as `not skipped`, unchecked TODOs, or prose
  that mentions before/after without command evidence.
- Keep the checker lightweight; it should catch common omission and ambiguity,
  not prove full methodology compliance.
- Add focused tests for false positives, valid before/after records, valid
  skipped reasons, and stale unrelated records.

Done when:

- Harness-affecting changes cannot satisfy the search-set evidence gate with
  vague prose or accidental keywords.
- `MAINTENANCE.md` and backlog Completion Gate examples use the accepted shape.
- Focused tests prove both valid and invalid evidence text.

### 51. P3 keep active core Current Status aligned with completed items

Status: 대기

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The `Current Status` block has repeatedly pointed future maintainers at items
that were already marked `Status: 완료`, most recently item 42. This does not
change runtime behavior, but it weakens backlog-as-regression-memory quality and
can cause agents to reselect completed work instead of creating new follow-up
items.

Potential improvement:

- Add a focused backlog consistency check that verifies every item listed as an
  active implementation candidate in `Current Status` is not marked complete.
- Alternatively, remove item-specific active pointers from `Current Status` and
  replace them with a generated or checker-backed summary.
- Preserve short completed-item pointers, but make them clearly non-selectable.

Done when:

- A completed item cannot be named as the active unstarted core candidate without
  a checker or review failure catching it.
- The `Current Status` block remains useful as handoff guidance without becoming
  another stale source of truth.

### 52. P3 schema-check repository self-application evolution traces

Status: 대기

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`.harness/traces/evolution/001-repository-self-application-root.md` establishes
the active self-application trace root, but it uses a lighter bootstrap shape
than the evolution schema in `core/reference.md`. The current repository tests
check that the minimum trace surface exists and that the legacy `.claude/traces/`
relationship is documented, but they do not protect frontmatter fields such as
`iteration`, `type`, `verdict`, `files_changed`, or the expected Before/After
result shape.

Potential improvement:

- Decide whether bootstrap trace-root records have an explicitly allowed reduced
  schema, or update the initial trace to follow the full evolution format.
- Add a focused trace-schema check for repository self-application evolution
  files.
- Keep the schema repository-applied rather than paper-core: the paper requires
  reusable raw trace evidence, while this repository chooses the exact fields.

Done when:

- Repository self-application evolution traces either conform to the documented
  evolution schema or use a documented bootstrap exception.
- Tests or a checker fail when future evolution traces omit required fields.
- The trace-root completeness tests and `core/reference.md` agree on the accepted
  shape.

### 35. P2 separate paper-result claims from repository implementation evidence

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- README.md
- tests/test_readme_methodology_boundaries.py
- backlog/core.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The review agreed that this repository implements many paper-inspired harness
principles well as a practical toolkit, but identified claim-inflation risk when
paper benchmark results and this repository's implementation quality appear in
the same narrative. Existing wording already separates paper-backed principles
from repository practice in several places, but the README and maintenance
framing can still be read as implying that this repository has empirically
demonstrated the paper's end-to-end performance gains.

Potential improvement:

- Add a compact evidence-category map that distinguishes:
  - paper results and benchmark claims,
  - repository methodology/documentation correctness,
  - adapter and generated-artifact operability,
  - this repository's own self-application evidence.
- Calibrate top-level wording so it remains clear that the repo is a
  paper-inspired harness toolkit unless a claim is backed by local end-to-end
  evaluation evidence.
- Keep this item scoped to claim/evidence framing. Do not require new
  self-application traces or external dogfooding as part of this item; those are
  broader empirical-evidence work and are intentionally deferred at this stage.

Done when:

- README and/or maintenance docs make the evidence categories explicit enough
  that a reader can tell what the Meta-Harness paper demonstrated versus what
  this repository has locally verified.
- Any strong claim about this repository's own implementation is backed by a
  local artifact, command, trace, or explicitly marked as future evidence.
- Multi-review checks the resulting wording because this touches core
  methodology claim boundaries.

Decision implemented:

- Updated the README opening to describe this repository as a paper-inspired
  toolkit and to state that local checks do not claim a local reproduction of
  the paper's end-to-end benchmark gains.
- Added a compact README evidence-category map distinguishing paper results,
  repository methodology/documentation correctness, adapter/generated-artifact
  operability, and repository self-application evidence.
- Left precise paper-result examples in place as paper context while tying local
  repository claims to concrete local surfaces such as `core/`, tests,
  compatibility checks, adapter smoke tests, `.harness/traces/search-set.md`,
  evolution traces, and backlog Completion Gates.
- Extended `tests/test_readme_methodology_boundaries.py` so README wording must
  keep paper benchmark claims separate from local repository evidence and must
  not drift into local reproduction claims.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Claim-boundary critic: PASS, score 10/10. Blocking findings: none. The README
  now explicitly separates published paper results from local repository
  verification and says the repo does not claim a local reproduction of the
  paper's benchmark gains.
- Evidence-map critic: PASS, score 10/10. Blocking findings: none. The
  evidence categories are compact and cover paper results, methodology/docs,
  adapter/generated artifacts, and repository self-application without adding
  new empirical obligations.
- Test-coverage critic: PASS, score 10/10. Blocking findings: none. Focused
  README boundary tests assert the evidence map, preserve precise paper numbers
  as paper context, and reject local reproduction wording.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - README.md
  - tests/test_readme_methodology_boundaries.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_readme_methodology_boundaries.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - BEFORE PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 -m unittest tests/test_repository_search_set.py`
- Multi-review required: yes; this changes core methodology claim/evidence
  boundaries.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 claim-boundary critic, 10/10
  evidence-map critic, 10/10 test-coverage critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 36. P1 add clean-worktree release verification gate

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- scripts/check-clean-worktree.py
- tests/test_clean_worktree.py
- MAINTENANCE.md
- backlog/codex-adapter.md
- backlog/core.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The verification critic identified a release-readiness gap: the tracked
pre-commit and several drift/review checkers intentionally validate the Git
index, but the current working tree can still contain unstaged governance drift
while those checks pass. During the review, `backlog/core.md` was dirty,
`git diff --cached --name-only` was empty, and `sh .githooks/pre-commit`
passed. Index-aware pre-commit behavior is correct for commit-time checks, but
release or stable-handoff verification should make dirty working-tree state
visible instead of letting it hide outside the checked index.

Potential improvement:

- Add a release-oriented verification command or script that fails or clearly
  reports when `git status --porcelain` is non-empty.
- Keep pre-commit index semantics intact; do not make commit-time checks reject
  unrelated unstaged work unless the repository intentionally changes that
  policy.
- Add the clean-worktree check to `MAINTENANCE.md` Standard verification or
  Release Checklist wording, and make clear whether dirty state is a hard fail
  or an explicit recorded exception.
- Cover the new release gate with a focused test or checker assertion so future
  maintenance cannot silently drop it.

Done when:

- A maintainer treating local `main` as a stable handoff point has one explicit
  command that reports PASS/FAIL for dirty worktree state.
- The release guidance distinguishes pre-commit/index validation from
  release/handoff clean-tree validation.
- The current dirty-worktree failure mode from the multi-review can no longer be
  reported as a clean release verification pass without an explicit exception.

Decision implemented:

- Added `scripts/check-clean-worktree.py`, a release/handoff checker that runs
  `git status --porcelain`, passes on a clean worktree, and fails with listed
  dirty paths when tracked, staged, or untracked state exists.
- Documented the command in `MAINTENANCE.md` as a release or stable handoff
  gate, separate from pre-commit's intentional Git-index validation semantics.
- Added the clean-worktree gate to the Release Checklist with an explicit
  dirty-state exception rule for handoff notes.
- Added `tests/test_clean_worktree.py` coverage for clean Git worktrees, dirty
  Git worktrees, non-Git directories, and the distinction that the command is
  documented for release/handoff but not wired into pre-commit.
- Added the Codex adapter follow-up candidates discovered by the same
  multi-review to `backlog/codex-adapter.md`.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Release-gate critic: PASS, score 10/10. Blocking findings: none. The new
  command gives maintainers an explicit PASS/FAIL clean-worktree gate before
  treating `main` as a stable handoff point.
- Pre-commit semantics critic: PASS, score 10/10. Blocking findings: none.
  Pre-commit remains index-oriented and does not reject unrelated unstaged work;
  the clean-worktree command is documented separately for release/handoff.
- Verification critic: PASS, score 10/10. Blocking findings: none. Focused
  tests exercise clean, dirty, and non-Git cases, and the current dirty
  maintenance worktree produced the expected non-zero release-gate result.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - scripts/check-clean-worktree.py
  - tests/test_clean_worktree.py
  - MAINTENANCE.md
  - backlog/codex-adapter.md
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_clean_worktree.py`
  - EXPECTED FAIL: `python3 scripts/check-clean-worktree.py` in this active
    maintenance worktree; it reported dirty paths including `MAINTENANCE.md`,
    `backlog/core.md`, `backlog/codex-adapter.md`, and the new checker/test
    files. This confirms the release gate catches the dirty-worktree state that
    pre-commit intentionally ignores.
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
- Multi-review required: yes; this changes release/handoff gate semantics.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 release-gate critic, 10/10
  pre-commit semantics critic, 10/10 verification critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 37. P3 create paper-claim traceability map for precise citations

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- README.md
- tests/test_readme_methodology_boundaries.py
- backlog/core.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The review agreed that the repository should be framed as inspired by the
Meta-Harness paper, not as a complete implementation or reproduction of the
paper. A remaining risk is that README claims with precise numbers or appendix
references, such as benchmark deltas, Table 3, Appendix A.2, and Appendix D,
are stronger than the arXiv abstract alone. Those claims may be accurate, but
future reviewers need a small traceability surface showing which local wording
is backed by the paper, which is repository practice, and which is not locally
verified.

Potential improvement:

- Add a compact paper-claim traceability map in `README.md`, `MAINTENANCE.md`, or
  a linked core document.
- For each precise paper claim used in top-level docs, record:
  - local claim text or section,
  - paper location or citation granularity,
  - whether the repository has local implementation evidence,
  - whether the claim is only inspiration/context rather than a local result.
- Keep the map small enough to maintain; do not copy the paper or turn the
  repository into a paper reproduction package.
- Use the map to decide whether strong wording should remain, be softened, or
  move behind a citation-specific note.

Done when:

- A reviewer can distinguish arXiv abstract-level claims, paper-body/appendix
  claims, and repository-local verification evidence without rereading every
  top-level document.
- README wording that cites precise paper results is either backed by the map or
  softened to an inspired-by framing.
- Multi-review checks the resulting map because it touches core methodology
  claim boundaries.

Decision implemented:

- Added a compact README `Paper claim traceability` table mapping major
  top-level paper claims to paper locations and local repository status.
- Recorded that the 6x harness sensitivity claim is paper Introduction context
  and not locally reproduced here.
- Recorded that the 7.7 point / 4x context-token result is a paper
  Abstract/Section 4.1 result, while this repository locally verifies
  documentation, adapters, generated assets, and self-application traces.
- Recorded that Table 3 raw-trace ablation motivates this repo's trace
  discipline, with local evidence coming from search-set and trace-root
  verification rather than benchmark reproduction.
- Recorded Appendix A/A.2 and Appendix D claims as paper locations for
  qualitative search trajectory and practical implementation tips.
- Extended `tests/test_readme_methodology_boundaries.py` to require the map and
  keep precise paper numbers labeled as paper context.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Citation-boundary critic: PASS, score 10/10. Blocking findings: none. The
  README now maps precise paper claims to paper locations and states local
  reproduction status rather than blending paper results with repo evidence.
- Scope critic: PASS, score 10/10. Blocking findings: none. The map stays small,
  does not copy the paper, and does not require new self-application traces or
  external dogfooding.
- Test-coverage critic: PASS, score 10/10. Blocking findings: none. Focused
  README boundary tests require the traceability map and guard against local
  reproduction wording.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - README.md
  - tests/test_readme_methodology_boundaries.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_readme_methodology_boundaries.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - BEFORE PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 -m unittest tests/test_repository_search_set.py`
- Multi-review required: yes; this changes core methodology claim/citation
  boundaries.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 citation-boundary critic, 10/10
  scope critic, 10/10 test-coverage critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 38. P3 remove duplicate core backlog item numbering

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- backlog/core.md
- tests/test_backlog_heading_uniqueness.py

Source discussion: 2026-05-04 multi-review of local `main` backlog governance.

Before this item, the active backlog had two `### 32` records: one for repository
self-application search-set work and one for core trace-schema boundary wording.
Both are completed, and `Current Status` no longer points to item 32 as active,
but duplicate numbered headings still weaken backlog governance. Future
maintenance agents, archive tooling, or review summaries can link to the wrong
item or treat completed records as ambiguous current work.

Potential improvement:

- Renumber one of the duplicate item 32 records, or move completed records into
  `backlog/archive/core.md` with stable archive anchors and compact active-file
  pointers.
- Update any `Archived:` links, source references, tests, and review records that
  depend on the affected heading.
- Add a lightweight backlog hygiene check if practical so active backlog files do
  not accumulate duplicate `### <number>.` headings again.

Done when:

- `backlog/core.md` has no duplicate numbered backlog headings.
- Existing completed-record history and archive pointers remain navigable.
- A future maintenance agent can identify active items without ambiguous item
  numbers.

Decision implemented:

- Renumbered the completed core trace-schema boundary record from `### 32` to
  `### 40`, leaving the repository self-application search-set record as
  `### 32`.
- Preserved the completed record in place and did not move archive pointers or
  historical Completion Gates.
- Added `tests/test_backlog_heading_uniqueness.py`, which fails if any active
  backlog file has duplicate numbered `### <number>.` headings.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - backlog/core.md
  - tests/test_backlog_heading_uniqueness.py
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_backlog_heading_uniqueness.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting backlog hygiene.
- Multi-review required: no; this is backlog heading/status hygiene only and
  does not change adapter behavior, hook semantics, release gates, checker
  policy, or core methodology contracts.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no
  VETO path.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 41. P3 refresh active backlog status after item 37 completion

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- backlog/core.md

Source discussion: 2026-05-04 multi-review of local `main` backlog governance.

The active `Current Status` block says item 37 is the one unstarted concrete core
implementation item, but item 37 is already marked `Status: 완료`. That does not
weaken the Meta-Harness methodology implementation, but it can mislead future
maintenance agents into selecting completed work instead of creating a new
backlog item for newly discovered work.

Potential improvement:

- Update `Current Status` so it no longer points at completed item 37 as
  available work.
- State the actual active backlog state after items 35, 36, 37, 38, and 39 are
  complete.
- If a new item is created from fresh review feedback, point to that item
  explicitly; otherwise say there is no unstarted concrete core implementation
  item.

Done when:

- `Current Status` does not point future maintainers at completed work.
- The active core backlog summary matches the statuses of the numbered records
  below it.
- `python3 scripts/check-maintenance-review.py backlog/core.md` passes.

Implementation notes:

- Updated `Current Status` so it no longer lists handled items 41, 43, 44, or
  45 as available implementation candidates.
- Left item 42 as the one remaining unstarted concrete core item from the
  current-main methodology review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 scripts/check-maintenance-review.py
  backlog/core.md`; PASS `python3 scripts/check-search-set-evidence.py`; PASS
  `git diff --check`.
- Search-set verification: SKIPPED; not harness-affecting, backlog status
  summary only.
- Multi-review required: no; backlog-only status cleanup that does not change
  core methodology, adapter behavior, hook semantics, release gates, or a
  durable contract.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not applicable; no required critics and no
  VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 43. P2 make search-set before/after evidence compliance mechanically visible

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- scripts/check-search-set-evidence.py
- tests/test_search_set_evidence.py
- MAINTENANCE.md
- backlog/README.md
- backlog/codex-adapter.md
- backlog/core.md

Source review: 2026-05-04 executable-implementation critic in the current-main
methodology multi-review.

The repository now has an executable self-application search-set under
`.harness/traces/search-set.md`, and maintenance policy requires relevant Active
verify commands to run before and after harness-affecting changes. However, the
current mechanical gates mostly prove that search-set commands exist and that
fixed pre-commit/release checks pass. They do not detect harness-affecting
staged paths and require a corresponding recorded before/after search-set
result, evolution trace, or explicit skipped reason.

Potential improvement:

- Add a lightweight checker or documented release command that identifies
  harness-affecting staged/changed paths and verifies that the touched backlog,
  trace, or review record includes search-set before/after evidence or an
  explicit skipped reason.
- Keep the rule local and practical; do not try to prove all methodology
  compliance automatically.
- Prefer a checker that catches the common omission without blocking ordinary
  docs/status cleanup that `MAINTENANCE.md` already treats as non
  harness-affecting.

Done when:

- A harness-affecting change cannot easily be presented as release-ready while
  omitting all search-set before/after evidence or skipped-reason recording.
- The checker or release command is covered by focused tests and documented in
  the relevant verification tier.
- Existing pre-commit index semantics remain intact unless explicitly changed by
  the item.

Decision implemented:

- Added `scripts/check-search-set-evidence.py`, a lightweight release/standard
  checker that inspects changed paths, identifies common harness-affecting
  repository surfaces, and requires a touched backlog/trace record to contain
  search-set before/after evidence or an explicit skipped reason.
- Kept pre-commit index semantics unchanged. The checker is documented in
  Standard verification and release/stable handoff guidance, not wired into the
  tracked pre-commit hook.
- Scoped the checker to practical omission detection rather than full
  methodology proof. Backlog-only cleanup remains non-harness-affecting, while
  checker/release-gate/script/core/adapter surfaces are treated as
  harness-affecting.
- Made backlog record validation prefer `진행중` item sections over unrelated
  `리뷰대기` sections so stale or unrelated completed records cannot satisfy the
  active item's evidence requirement.
- Added `tests/test_search_set_evidence.py` for missing evidence, before/after
  evidence, skipped reasons, non-harness backlog cleanup, checker path
  classification, stale-record rejection, unrelated-review-pending rejection,
  and MAINTENANCE documentation.
- Updated backlog overview and Codex adapter backlog with follow-up candidates
  discovered by the same review pass.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Checker-behavior critic: PASS, score 10/10. Blocking findings: none. The
  checker catches harness-affecting changed paths without recorded search-set
  evidence and avoids accepting stale completed records for a current
  in-progress item.
- Scope/pre-commit critic: PASS, score 10/10. Blocking findings: none. The
  checker remains a release/standard command and does not alter pre-commit's
  index-oriented behavior.
- Test/documentation critic: PASS, score 10/10. Blocking findings: none.
  Focused tests cover the common omission and false-positive boundaries, and
  MAINTENANCE documents where to run the checker and what it proves.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - scripts/check-search-set-evidence.py
  - tests/test_search_set_evidence.py
  - MAINTENANCE.md
  - backlog/README.md
  - backlog/codex-adapter.md
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_search_set_evidence.py`
  - EXPECTED FAIL before Completion Gate was recorded: `python3 scripts/check-search-set-evidence.py`
    reported missing search-set evidence for the active harness-affecting
    checker/MAINTENANCE changes.
  - PASS: `python3 scripts/check-search-set-evidence.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - BEFORE PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 -m unittest tests/test_repository_search_set.py`
- Multi-review required: yes; this changes repository verification/release-gate
  behavior.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 checker-behavior critic, 10/10
  scope/pre-commit critic, 10/10 test/documentation critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 44. P2 remove runtime-specific instruction filenames from core examples

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- core/methodology.md
- docs/methodology.md
- tests/test_core_methodology_boundaries.py
- backlog/core.md

Source review: 2026-05-04 adapter/plugin alignment critic in the current-main
methodology multi-review.

The core methodology says adapters own runtime-specific instruction files,
install paths, hook schemas, permission models, and examples. One core example
still names `AGENTS.md` directly while explaining prompt-as-code boundaries.
That makes the runtime-neutral core lean toward the Codex surface, even though
the concept applies equally to `CLAUDE.md`, `AGENTS.md`, or another
adapter-defined project instruction file.

Potential improvement:

- Replace the core `AGENTS.md` example with runtime-neutral wording such as
  "project instruction file".
- If concrete filenames are helpful, move or duplicate them into adapter docs
  where `AGENTS.md` and `CLAUDE.md` are runtime-specific examples.
- Add or update a focused boundary test if existing tests do not already guard
  against runtime-specific filename leakage in core methodology prose.

Done when:

- `core/methodology.md` keeps the prompt-as-code warning without naming a
  specific runtime's project instruction file as the canonical example.
- Adapter docs remain free to use their concrete filenames.
- Core/adapters ownership boundaries remain mechanically or review-protected.

Implementation notes:

- Replaced the core prompt-as-code anti-example's concrete `AGENTS.md` filename
  with runtime-neutral "project instruction file" wording.
- Mirrored the same wording in `docs/methodology.md`.
- Added a focused core methodology boundary test that rejects `AGENTS.md` and
  `CLAUDE.md` leakage in the canonical methodology and compatibility mirror.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.

Multi-review:

- Result: PASS; required because this changes a core methodology boundary.
  Used `FALLBACK_NONINDEPENDENT` sequential review because this single-session
  maintenance pass was not authorized to spawn independent reviewers.
- Paper/core-boundary critic: score 10/10; verdict PASS; Blocking findings:
  none. The change preserves the evaluator/candidate-diff warning while
  removing a Codex-specific filename from the shared core.
- Adapter-ownership/mirror critic: score 10/10; verdict PASS; blocking
  findings: none. Adapter docs remain free to name concrete runtime files, and
  the compatibility methodology mirror stays synchronized.
- Verification/release critic: score 10/10; verdict PASS; blocking findings:
  none. Focused boundary tests, mirror drift check, Active search-set commands,
  and standard repository tests passed.
- Score handling: no score below 9, so no VETO; no score 9, so no why-not-10
  residual risk or follow-up backlog item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `core/methodology.md`, `docs/methodology.md`,
  `tests/test_core_methodology_boundaries.py`, `backlog/core.md`.
- Scope deviations: none in final diff. A transient reservation block was
  initially placed on item 41, noticed from `git diff`, and corrected before
  completion.
- Verification results: PASS `python3 -m unittest
  tests/test_core_methodology_boundaries.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 scripts/check-maintenance-review.py`;
  PASS `python3 -m unittest tests/test_pre_commit_hook.py`; PASS `python3 -m
  unittest tests/test_claude_autoresearch_reject_evidence.py`; PASS `python3 -m
  unittest tests/test_repository_search_set.py`; PASS `python3 -m unittest
  discover -s tests`; PASS `python3 -m unittest discover -s
  adapters/claude/tests`; PASS `python3 -m unittest discover -s
  adapters/codex/tests`; PASS `sh .githooks/pre-commit`; PASS `git diff
  --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above.
- Multi-review required: yes; core methodology boundary contract.
- Multi-review result: PASS; `FALLBACK_NONINDEPENDENT` sequential review.
- Reviewer scores and VETO handling: 10/10 paper/core-boundary critic, 10/10
  adapter-ownership/mirror critic, 10/10 verification/release critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 45. P2 make the operationalized-toolkit framing explicit in public docs

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- README.md
- MAINTENANCE.md
- backlog/README.md
- tests/test_readme_methodology_boundaries.py
- backlog/core.md

Source discussion: 2026-05-04 maintainer framing preference after current-main
Meta-Harness methodology review.

The desired framing is: this repository is not a paper reproduction package or a
claim that the local repo has demonstrated Meta-Harness benchmark gains. It is a
project that operationalizes the paper's core principles into a practical
harness toolkit, runtime adapters, and verification gates. That sentence should
become the stable public framing used by README, maintenance docs, and any
high-level core/backlog guidance that explains what this repository is.

Potential improvement:

- Add or refine a short canonical sentence in README and maintenance docs along
  these lines: "This project operationalizes Meta-Harness paper principles into
  a practical harness toolkit, runtime adapters, and verification gates."
- Use that framing when contrasting paper results, repository-local evidence,
  adapter operability, and self-application traces.
- Avoid wording that implies this repo is a full Meta-Harness implementation,
  a benchmark reproduction, or empirical proof of the paper's performance
  claims.
- Keep the phrasing compatible with existing evidence-category and paper-claim
  traceability tables instead of duplicating them.

Done when:

- README first-viewport wording, `MAINTENANCE.md` opening, and any directly
  linked core/backlog guidance consistently use the operationalized-toolkit
  framing.
- Focused README or methodology-boundary tests protect the framing from drifting
  back toward reproduction/implementation overclaiming.
- Multi-review checks the result because this is a public claim-boundary change.

Implementation notes:

- Added the canonical operationalized-toolkit framing to the README first
  viewport, `MAINTENANCE.md` opening, and `backlog/README.md` opening.
- Kept the README's paper benchmark numbers explicitly labeled as paper
  context and retained the no-local-reproduction disclaimer.
- Updated the README methodology-boundary test so README, maintenance, and
  backlog guidance all keep the same canonical framing and avoid overclaiming
  reproduction/proof.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.
- after: PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`.

Multi-review:

- Result: PASS; required because this is a public claim-boundary change. Used
  `FALLBACK_NONINDEPENDENT` sequential review because this single-session
  maintenance pass was not authorized to spawn independent reviewers.
- Paper-claim boundary critic: score 10/10; verdict PASS; Blocking findings:
  none. The wording says the repository operationalizes paper principles and
  explicitly does not claim local benchmark reproduction.
- Public-doc consistency critic: score 10/10; verdict PASS; Blocking findings:
  none. README, maintenance, and backlog overview now share the same canonical
  framing, with focused tests guarding the normalized text.
- Verification/release critic: score 10/10; verdict PASS; Blocking findings:
  none. Focused boundary tests, standard tests, pre-commit, and Active
  search-set commands passed.
- Score handling: no score below 9, so no VETO; no score 9, so no why-not-10
  residual risk or follow-up backlog item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `README.md`, `MAINTENANCE.md`, `backlog/README.md`,
  `tests/test_readme_methodology_boundaries.py`, `backlog/core.md`.
- Scope deviations: `backlog/README.md` was added to Scope before editing to
  cover directly linked backlog guidance. A transient reservation block was
  initially placed on item 41, noticed from `git diff`, and corrected before
  completion.
- Verification results: PASS `python3 -m unittest
  tests/test_readme_methodology_boundaries.py`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 -m unittest discover -s
  tests`; PASS `python3 -m unittest discover -s adapters/claude/tests`; PASS
  `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3 -m
  unittest tests/test_pre_commit_hook.py`; PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`; PASS `python3 -m
  unittest tests/test_repository_search_set.py`; PASS `sh .githooks/pre-commit`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above.
- Multi-review required: yes; public paper-claim boundary change.
- Multi-review result: PASS; `FALLBACK_NONINDEPENDENT` sequential review.
- Reviewer scores and VETO handling: 10/10 paper-claim boundary critic, 10/10
  public-doc consistency critic, 10/10 verification/release critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 39. P2 add trace-root completeness to the Active search-set

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .harness/traces/search-set.md
- tests/test_repository_search_set.py
- backlog/core.md

Source discussion: 2026-05-04 multi-review of whether local `main` implements
the Meta-Harness methodology well.

The repository self-application trace root now has the required minimum
surfaces, and `tests/test_repository_search_set.py` mechanically checks that
`.harness/traces/` contains `search-set.md`, `evolution/`, `failures/`, and
`experiments/`. The remaining governance gap is that
`.harness/traces/search-set.md` does not name this invariant as an Active
regression case, so a maintainer running only the documented Active cases may
miss the exact self-application failure that previously caused a multi-review
VETO.

Potential improvement:

- Add an Active search-set case for repository trace-root completeness.
- Use the existing focused test command if it remains the narrowest stable
  verifier: `python3 -m unittest tests/test_repository_search_set.py`.
- Make the search-set entry's Source/Symptom wording point back to the
  self-application VETO and item 33 completion record.
- Keep the case narrow enough that it guards trace-root completeness without
  turning the Active search-set into the full Standard verification suite.

Done when:

- `.harness/traces/search-set.md` has an Active case that directly covers
  repository self-application trace-root completeness.
- The Active verify command fails if the sibling minimum trace surfaces are
  missing.
- Maintenance review can no longer pass full Active search-set verification
  while omitting the trace-root completeness invariant.

Decision implemented:

- Added Active search-set case `SS-006: Repository trace root keeps minimum
  self-application surface` to `.harness/traces/search-set.md`.
- Pointed the case at `backlog/core.md` item 33 and the 2026-05-04
  self-application trace-root multi-review VETO.
- Used the existing focused verifier
  `python3 -m unittest tests/test_repository_search_set.py` so the Active case
  fails when `.harness/traces/` has `search-set.md` but lacks `evolution/`,
  `failures/`, or `experiments/`.
- Extended `tests/test_repository_search_set.py` to require the new Active case,
  its source/symptom wording, and its verify command.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Search-set coverage critic: PASS, score 10/10. Blocking findings: none. The
  Active set now directly names repository trace-root completeness and points
  to the prior self-application VETO and item 33 completion record.
- Verifier quality critic: PASS, score 10/10. Blocking findings: none. The
  verify command is narrow, executable, non-piped, and fails through the focused
  repository trace-root surface test if sibling minimum surfaces disappear.
- Scope critic: PASS, score 10/10. Blocking findings: none. The change stays
  limited to the repository self-application search-set, its focused test, and
  the backlog record; it does not broaden Active coverage into the full
  Standard verification suite.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - .harness/traces/search-set.md
  - tests/test_repository_search_set.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 -m unittest tests/test_repository_search_set.py`
- Multi-review required: yes; this changes repository search-set coverage and
  trace-root regression contract.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 search-set coverage critic, 10/10
  verifier quality critic, 10/10 scope critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 28. P2 archive completed backlog items without losing review records

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- backlog/core.md
- backlog/claude-adapter.md
- backlog/codex-adapter.md
- backlog/archive/core.md
- backlog/archive/claude-adapter.md
- backlog/archive/codex-adapter.md
- backlog/README.md
- scripts/check-maintenance-review.py
- tests/test_check_maintenance_review.py

Source discussion: 2026-05-03 maintainer request.

The backlog files now carry both active work candidates and completed
decision/review records. Keeping all completed Completion Gates inline preserves
regression memory, but it also makes the active backlog long and harder to
scan. Deleting completed records would lose review evidence, score handling,
and residual-risk history.

Decision implemented:

- Created `backlog/archive/core.md`, `backlog/archive/claude-adapter.md`, and
  `backlog/archive/codex-adapter.md`.
- Moved completed records with `Status: 완료` and legacy `Decision implemented`
  summaries from active backlog files to the owning archive file.
- Left compact `Status: 완료` plus `Archived:` pointers in active backlog files.
- Updated `backlog/README.md` with archive policy and the completed-records
  ownership row.
- Updated `scripts/check-maintenance-review.py` so archive files are included
  in default validation.
- Updated `tests/test_check_maintenance_review.py` so filesystem and staged
  default path coverage includes archive files, and staged archive records are
  validated.
- Restored a compact active `Current Status` block in `backlog/core.md` after
  moving completed records.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `backlog/core.md`, `backlog/claude-adapter.md`,
  `backlog/codex-adapter.md`, `backlog/archive/core.md`,
  `backlog/archive/claude-adapter.md`,
  `backlog/archive/codex-adapter.md`, `backlog/README.md`,
  `scripts/check-maintenance-review.py`, and
  `tests/test_check_maintenance_review.py`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_check_maintenance_review.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-maintenance-review.py backlog/core.md backlog/claude-adapter.md backlog/codex-adapter.md backlog/archive/core.md backlog/archive/claude-adapter.md backlog/archive/codex-adapter.md`, `git diff --check`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes backlog record storage and
  maintenance review checker default validation coverage.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Record-preservation critic score 10,
  verdict PASS, Blocking findings: none. Active-backlog usability critic score
  10, verdict PASS, Blocking findings: none. Checker coverage critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score 9,
  verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: older legacy `Decision implemented` records that
  predate Completion Gate policy were preserved as-is in the archive; they do
  not gain reconstructed Completion Gates from this archive move.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 19. Add prompt-as-code search example

Status: 완료
Archived: `backlog/archive/core.md#19-add-prompt-as-code-search-example`

### 16. Enforce score-9 why-not-10 review handling

Status: 완료
Archived: `backlog/archive/core.md#16-enforce-score-9-why-not-10-review-handling`

### 17. Restore single-session maintenance pipeline

Status: 완료
Archived: `backlog/archive/core.md#17-restore-single-session-maintenance-pipeline`

### 18. Add maintenance review checker to pre-commit

Status: 완료
Archived: `backlog/archive/core.md#18-add-maintenance-review-checker-to-pre-commit`

### 29. P2 add marketplace metadata checker to standard verification

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- MAINTENANCE.md
- README.md
- tests/test_pre_commit_hook.py
- backlog/core.md

Source review: 2026-05-03 feedback triage.

The tracked pre-commit hook now runs
`python3 scripts/check-codex-marketplace-metadata.py`, and the release checklist
mentions Codex marketplace metadata readiness. However, the Standard
verification command block in `MAINTENANCE.md` still omits this checker, so
maintainers following the documented full command set can miss a release-surface
gate.

Potential improvement:

- Add `python3 scripts/check-codex-marketplace-metadata.py` to the Standard
  verification command block in `MAINTENANCE.md`.
- Keep the checker's deferred-state wording clear: it passes while no
  publication manifest exists and fails if marketplace metadata appears before
  publication readiness evidence is recorded.
- Verify that `.githooks/pre-commit`, the release checklist, and Standard
  verification all name the same marketplace metadata readiness gate.

Decision:

- Added `python3 scripts/check-codex-marketplace-metadata.py` to the Standard
  verification command block in `MAINTENANCE.md`.
- Aligned README pre-commit and pre-commit-adjacent command guidance so it names
  the marketplace metadata readiness gate.
- Added focused tests proving Standard verification, README docs, and the
  tracked pre-commit hook name the marketplace metadata checker.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `MAINTENANCE.md`
  - `README.md`
  - `tests/test_pre_commit_hook.py`
  - `backlog/core.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes documented release/verification
  gate coverage.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Standard verification parity critic: 10/10 PASS; Standard verification now
    names the marketplace metadata checker.
  - Release-gate consistency critic: 10/10 PASS; README, pre-commit, release
    checklist, and Standard verification all name the same readiness gate.
  - Deferred-state clarity critic: 10/10 PASS; the checker output and release
    checklist still say validation is deferred while no publication manifest
    exists and fails before readiness evidence is recorded.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, verification,
    search-set SKIPPED reason, and Completion Gate are recorded, with
    nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 32. P2 add repository self-application search-set

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- .harness/traces/search-set.md
- MAINTENANCE.md
- tests/test_repository_search_set.py
- backlog/core.md

Source review: 2026-05-03 feedback triage.

This repository describes and distributes Meta-Harness methodology, but it does
not currently have a repository `search-set.md`. That is not fatal for using
the repository as methodology documentation and adapter distribution, but it is
a self-application gap: raw traces may exist, while Active regression memory for
this repository's own maintenance loop is incomplete.

Potential improvement:

- Add an Active search-set for this repository under the selected trace root
  or another documented repository-level location.
- Seed it with current recurring regression risks, such as backlog status drift,
  adapter mirror drift, release gate drift, and evaluator-boundary evidence
  preservation.
- Update maintenance guidance so future harness-affecting repository changes
  can run concrete before/after search-set verify commands instead of always
  recording search-set verification as skipped.

Decision:

- Added tracked repository self-application search-set at
  `.harness/traces/search-set.md`.
- Seeded Active cases for enforceable backlog review records, compatibility
  mirror drift, pre-commit/release gate drift, Claude REJECT evidence
  preservation, and Codex activation evidence/documentation alignment.
- Updated `MAINTENANCE.md` so this repository's own harness-maintenance loop
  uses `.harness/traces/search-set.md` for relevant before/after Active verify
  commands.
- Added focused tests that validate the repository search-set exists, has
  Active entries with executable verify commands, covers the current recurring
  regression risks, and is referenced by maintenance guidance.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - .harness/traces/search-set.md
  - MAINTENANCE.md
  - tests/test_repository_search_set.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE: SKIPPED; no tracked repository self-application `search-set.md` existed before this item, so there were no Active commands to run.
  - AFTER: PASS; all new Active verify commands in `.harness/traces/search-set.md` passed: `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `sh .githooks/pre-commit`, `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`, and `python3 -m unittest tests/test_pre_commit_hook.py`.
- Multi-review required: yes; this changes repository trace/search-set contract and future harness-affecting verification workflow.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Search-set schema critic: 10/10 PASS; the new file follows the `core/reference.md` Active/Archived shape and every Active case has an executable verify command.
  - Regression coverage critic: 10/10 PASS; Active cases cover current recurring maintenance risks around review records, mirrors, release gates, evaluator evidence, and activation evidence.
  - Maintenance integration critic: 10/10 PASS; `MAINTENANCE.md` now points repository self-application work at the tracked search-set for future before/after checks.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, verification, search-set before/after status, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 31. P2 narrow backlog workflow multi-review trigger

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- MAINTENANCE.md
- tests/test_maintenance_policy_boundaries.py
- backlog/core.md

Source review: 2026-05-03 feedback triage.

The backlog workflow says to use multi-review for adapter behavior, release
gates, hook semantics, or "anything that can steer future work in the wrong
direction." Later `Multi-Review Use` narrows required multi-review to adapter
direction, hook/protected-file semantics, release gates, core boundaries, and
durable contracts. The earlier broader sentence can pull routine docs/backlog
edits into mandatory multi-review and partially reintroduce the process-drag
risk that the single-session pipeline was meant to remove.

Potential improvement:

- Align the backlog workflow trigger with `Multi-Review Use`.
- Keep multi-review required for behavior-changing durable contracts, but make
  routine backlog/status/doc cleanup eligible for focused checks without
  mandatory multi-review.
- Add or update a lightweight test/check if the repository has a suitable
  policy-text assertion for this maintenance rule.

Decision:

- Replaced the broad backlog workflow trigger with the concrete categories from
  `Multi-Review Use`: adapter behavior, release gates, hook semantics, core
  methodology boundaries, and durable contracts.
- Explicitly allowed routine backlog/status/doc cleanup to use focused checks
  without mandatory multi-review when those contracts do not change.
- Added a focused policy-boundary test that pins the narrowed trigger and
  rejects the previous broad "anything that can steer future work" wording.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - MAINTENANCE.md
  - tests/test_maintenance_policy_boundaries.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_maintenance_policy_boundaries.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; this changes maintenance workflow policy and durable review-contract wording.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Required-review coverage critic: 10/10 PASS; the Backlog Policy trigger now points to the same durable contract categories as `Multi-Review Use`.
  - Process-drag reduction critic: 10/10 PASS; routine backlog/status/doc cleanup is explicitly eligible for focused checks when no durable contract changes.
  - Policy test critic: 10/10 PASS; the narrowed trigger and removal of the broad wording are pinned by `tests/test_maintenance_policy_boundaries.py`.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, full verification, search-set SKIPPED reason, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 30. P3 refresh active backlog Current Status after adapter follow-ups

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- backlog/core.md

Source discussion: 2026-05-03 maintainer request to continue with the next
backlog item after completing the current Claude adapter follow-ups.

The active `Current Status` block still described item 29 as open and Claude
adapter items 10-12 as remaining unstarted work, even though those records are
now complete. That stale status can cause future single-session maintenance to
reselect already completed work.

Decision:

- Updated `Current Status` to state that there is currently no unstarted
  concrete core implementation item.
- Marked item 29 and Claude adapter items 10-12 as completed follow-ups in the
  status summary.
- Preserved the guidance that newly discovered work should become new backlog
  entries instead of reopening completed records as available candidates.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
- Search-set verification: SKIPPED; not harness-affecting and no repository `search-set.md` exists.
- Multi-review required: no; this is active backlog status text cleanup only, with no adapter behavior, hook semantics, release gate, or checker policy change.
- Multi-review result: not required.
- Reviewer scores and VETO handling: not required; no reviewer scores and no VETO path.
- For each score 9, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 40. P3 label core trace schemas as repository-applied conventions

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- core/methodology.md
- docs/methodology.md
- core/reference.md
- docs/reference.md
- tests/test_core_methodology_boundaries.py
- backlog/core.md

Source review: 2026-05-04 multi-review residual risk from the current-main
Meta-Harness methodology assessment.

The latest multi-review passed, but two critics noted a small clarity risk:
top-level and core-reference wording such as `AI Agent Meta-Harness`, `Trace
Filesystem (Required for All Projects)`, and `maintainable Meta-Harness
artifact` can invite an over-literal reading that this repository implements
every Meta-Harness paper detail as a reference specification. The surrounding
README, core methodology, and maintenance policy correctly say this project is
a practical framework inspired by the paper, with repository-applied
conventions layered on top. The remaining risk is local to prescriptive trace
schema sections that do not always repeat that boundary near the requirement.

Potential improvement:

- Add a short boundary sentence near `core/methodology.md` trace filesystem
  requirements explaining that the exact trace-root directories, YAML
  frontmatter, and search-set schema are this repository's applied convention
  for preserving the paper's richer prior-experience signal.
- Add matching wording near `core/reference.md` trace format sections so the
  schemas read as repository contracts, not paper-mandated filenames.
- Keep the wording concise and avoid weakening the operational requirement for
  projects that adopt this harness.
- Keep `docs/methodology.md` and `docs/reference.md` compatibility mirrors in
  sync through the existing mirror check.

Acceptance criteria:

- A reader can distinguish paper-backed principles from repository-specific
  trace schema conventions without needing to jump back to the README.
- No adapter-specific path behavior moves into `core/`; adapters still own
  `.claude/traces/` versus `.harness/traces/` decisions.
- Boundary tests or existing methodology-boundary tests cover the new wording
  if the change affects durable methodology interpretation.

Decision implemented:

- Added a concise boundary paragraph in `core/methodology.md` immediately under
  the trace filesystem requirement: raw prior-experience reuse is the
  paper-backed principle, while the exact trace-root surface, YAML frontmatter,
  and search-set schema are this repository's applied convention.
- Added matching boundary wording in `core/reference.md` so trace filenames,
  frontmatter fields, and search-set sections read as repository contracts for
  adopters, not paper-mandated names or schemas.
- Kept `docs/methodology.md` and `docs/reference.md` compatibility mirrors in
  sync.
- Extended `tests/test_core_methodology_boundaries.py` to assert the new
  methodology/reference boundary wording and mirror presence.

Multi-review:

- Mode: FALLBACK_NONINDEPENDENT sequential review; separate sub-agents were not
  used in this single-session pass.
- Verdict: PASS.
- Methodology critic: PASS, score 10/10. Blocking findings: none. The wording
  clearly separates the paper-backed principle from repository-applied trace
  schema conventions without weakening the trace requirement.
- Scope/adapter critic: PASS, score 10/10. Blocking findings: none. No
  adapter-specific path decision moved into `core/`; adapters still own
  concrete runtime path behavior.
- Verification/mirror critic: PASS, score 10/10. Blocking findings: none.
  Boundary tests cover the new durable interpretation, docs mirrors were
  updated, and both official index-based mirror verification plus working-tree
  mirror verification passed.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Score handling: all required critic scores were 10/10, so there is no
  why-not-10 handling and no VETO path.
- Rerun status: no critic rerun required; the only rerun was the corrected
  boundary-test marker rerun, which passed.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - core/methodology.md
  - docs/methodology.md
  - core/reference.md
  - docs/reference.md
  - tests/test_core_methodology_boundaries.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_core_methodology_boundaries.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: working-tree mirror check using `scripts/check-compat-mirrors.py`
    validation helpers with filesystem reads
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
  - Note: an intermediate boundary-test run failed because a test marker crossed
    a line wrap in the reference text; the test marker was narrowed and the
    affected test was rerun to PASS.
- Search-set verification:
  - BEFORE PASS: `python3 scripts/check-maintenance-review.py`
  - BEFORE PASS: `python3 scripts/check-compat-mirrors.py`
  - BEFORE PASS: `sh .githooks/pre-commit`
  - BEFORE PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - BEFORE PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - AFTER PASS: `python3 scripts/check-maintenance-review.py`
  - AFTER PASS: `python3 scripts/check-compat-mirrors.py`
  - AFTER PASS: `sh .githooks/pre-commit`
  - AFTER PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - AFTER PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
- Multi-review required: yes; this changes core methodology boundary wording
  and durable trace-schema interpretation.
- Multi-review result: PASS; FALLBACK_NONINDEPENDENT sequential review recorded
  above.
- Reviewer scores and VETO handling: 10/10 methodology critic, 10/10
  scope/adapter critic, 10/10 verification/mirror critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 42. P3 audit aphoristic methodology slogans for claim-boundary clarity

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- core/methodology.md
- docs/methodology.md
- tests/test_core_methodology_boundaries.py
- backlog/core.md

Source review: 2026-05-04 multi-review of current local `main` against the
Meta-Harness methodology.

The review passed overall, but the paper-fidelity critic noted a small residual
claim-boundary risk: compact slogans such as "The bottleneck is environment
design, not model intelligence" are useful as methodology cues, yet can read
broader than the paper's evidence if quoted without the surrounding
paper-inspired-toolkit framing. The repository already separates paper results
from local evidence in the README and labels repository-applied conventions in
core docs. This item is only about tightening high-level wording that may travel
out of context.

Potential improvement:

- Audit README, `core/methodology.md`, `core/reference.md`, and
  `MAINTENANCE.md` for aphoristic or absolute methodology slogans that could be
  mistaken for direct paper claims.
- Keep useful short cues, but attach local framing where needed: paper-backed
  motivation, repository practice, or adopter contract.
- Avoid weakening operational requirements that are intentionally part of this
  repository's harness contract.
- Add or extend focused boundary tests only if durable public wording changes.

Done when:

- Top-level and core methodology wording still communicates the harness lesson
  crisply, but no standalone sentence implies local reproduction or a stronger
  universal claim than the cited paper supports.
- Any changed wording preserves the README evidence-category and paper-claim
  traceability boundaries.
- Multi-review checks the result if public claim boundaries or core methodology
  wording change.

Implementation notes:

- Audited README, `MAINTENANCE.md`, `core/methodology.md`, and
  `core/reference.md` for standalone aphoristic or absolute claim wording.
  README and `MAINTENANCE.md` already carry the operationalized-toolkit and
  no-local-reproduction framing from item 45; `core/reference.md` did not have
  a matching standalone slogan that needed edits.
- Added claim-boundary context before the opening methodology cues so they read
  as paper-backed motivation for this repository's applied harness toolkit, not
  local benchmark reproduction claims.
- Reworded the structural hardening aphorism as repository shorthand tied to
  repeated trace evidence and mechanical guardrails.
- Mirrored the methodology wording in `docs/methodology.md` and added a focused
  boundary test.

Search-set verification:

- before: PASS `python3 scripts/check-maintenance-review.py`.
- before: PASS `python3 scripts/check-compat-mirrors.py`.
- before: PASS `sh .githooks/pre-commit`.
- before: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 -m unittest tests/test_pre_commit_hook.py`.
- after: PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`.

Multi-review:

- Result: PASS; required because this changes core methodology/public
  claim-boundary wording. Used `FALLBACK_NONINDEPENDENT` sequential review
  because this single-session maintenance pass was not authorized to spawn
  independent reviewers.
- Paper-claim boundary critic: score 10/10; verdict PASS; Blocking findings:
  none. The wording keeps the memorable cues but labels them as paper-backed
  motivation and repository-applied hardening, not local benchmark proof.
- Methodology-contract critic: score 10/10; verdict PASS; Blocking findings:
  none. The change does not weaken trace, evaluator-boundary, or guardrail
  requirements; it ties the hardening shorthand to repeated trace evidence.
- Verification/mirror critic: score 10/10; verdict PASS; Blocking findings:
  none. Focused boundary tests, compatibility mirror checks, standard tests,
  pre-commit, and Active search-set commands passed.
- Score handling: no score below 9, so no VETO; no score 9, so no why-not-10
  residual risk or follow-up backlog item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no critic rerun required.
- Final acceptance: accepted; ready for maintainer review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `core/methodology.md`, `docs/methodology.md`,
  `tests/test_core_methodology_boundaries.py`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_core_methodology_boundaries.py
  tests/test_readme_methodology_boundaries.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3 -m unittest discover -s
  tests`; PASS `python3 -m unittest discover -s adapters/claude/tests`; PASS
  `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3 -m
  unittest tests/test_pre_commit_hook.py`; PASS `python3 -m unittest
  tests/test_claude_autoresearch_reject_evidence.py`; PASS `python3 -m
  unittest tests/test_repository_search_set.py`; PASS `sh .githooks/pre-commit`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after for relevant Active commands, as
  listed above.
- Multi-review required: yes; core methodology/public claim-boundary wording.
- Multi-review result: PASS; `FALLBACK_NONINDEPENDENT` sequential review.
- Reviewer scores and VETO handling: 10/10 paper-claim boundary critic, 10/10
  methodology-contract critic, 10/10 verification/mirror critic; no VETO.
- For each score-9 result, why not 10: none.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; ready for maintainer review.

### 33. P2 complete repository self-application trace root

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .harness/traces/evolution/
- .harness/traces/failures/
- .harness/traces/experiments/
- MAINTENANCE.md
- tests/test_repository_search_set.py
- backlog/core.md

Source review: 2026-05-04 multi-review residual risk from the current-main
Meta-Harness methodology assessment.

The repository now has `.harness/traces/search-set.md` with Active verify
commands, so the earlier repository search-set gap is mostly resolved. However,
`core/methodology.md` defines the minimum trace surface as `evolution/`,
`failures/`, `experiments/`, and `search-set.md`. The active self-application
root currently only has `search-set.md`; older history remains under
`.claude/traces/`. From the methodology's own perspective, repository
self-application is still split or incomplete.

Potential improvement:

- Create the missing `.harness/traces/evolution/`, `.harness/traces/failures/`,
  and `.harness/traces/experiments/` surfaces, with tracked placeholders or
  initial records as appropriate for Git.
- Record whether existing `.claude/traces/` history is migrated, copied,
  referenced as legacy Claude history, or intentionally left as temporary
  historical context.
- Update maintenance guidance if needed so repository self-application uses one
  active trace root and does not silently split future trace history.
- Add a focused check or test that fails when the repository self-application
  trace root has `search-set.md` but lacks the sibling minimum trace surfaces.

Acceptance criteria:

- `.harness/traces/` has the minimum repository self-application surface:
  `evolution/`, `failures/`, `experiments/`, and `search-set.md`.
- The relationship between existing `.claude/traces/` history and the active
  `.harness/traces/` root is explicitly documented.
- Repository maintenance guidance and tests agree on the active trace root and
  fail if the minimum trace surface becomes incomplete again.

Decision:

- Created tracked `.harness/traces/evolution/`,
  `.harness/traces/failures/`, and `.harness/traces/experiments/` surfaces.
- Added `.harness/traces/evolution/001-repository-self-application-root.md`
  to document `.harness/traces/` as the active repository self-application
  trace root.
- Left existing `.claude/traces/` history in place as legacy Claude-local
  context rather than copying or migrating it in this item.
- Updated `MAINTENANCE.md` to direct future repository maintenance traces to
  `.harness/traces/` and to avoid writing new repository maintenance traces
  under `.claude/traces/` unless explicitly migrating or recovering that
  history.
- Extended repository trace-root tests so the minimum trace surface and legacy
  Claude history relationship are checked.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - .harness/traces/evolution/001-repository-self-application-root.md
  - .harness/traces/failures/.gitkeep
  - .harness/traces/experiments/.gitkeep
  - MAINTENANCE.md
  - tests/test_repository_search_set.py
  - backlog/core.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_repository_search_set.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `sh .githooks/pre-commit`
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin-activation.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
- Search-set verification:
  - BEFORE: PASS; relevant Active commands passed before implementation: `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-compat-mirrors.py`, `sh .githooks/pre-commit`, and `python3 -m unittest tests/test_pre_commit_hook.py`.
  - AFTER: PASS; the same relevant Active commands passed after implementation, plus `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py` was run for full Active coverage.
- Multi-review required: yes; this changes repository self-application trace-root contract and future trace-writing guidance.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Minimum trace surface critic: 10/10 PASS; `.harness/traces/` now has `search-set.md`, `evolution/`, `failures/`, and `experiments/`.
  - Legacy history critic: 10/10 PASS; `.claude/traces/` is explicitly documented as legacy Claude-local context rather than a second active root.
  - Test coverage critic: 10/10 PASS; focused tests fail if the repository self-application trace root lacks sibling minimum surfaces or loses the legacy-history note.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, search-set before/after verification, full verification, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes
