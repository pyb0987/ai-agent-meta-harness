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
- Active core backlog has one unstarted concrete process item from recent
  current-main methodology reviews: item 60 should make the archive lifecycle
  operational for completed active backlog records.
  Items 56-59 and 61 are complete, so future maintenance should not select
  them as available implementation candidates.
  Items 41-55 are complete, so future maintenance should not select them as
  available implementation candidates.
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

Status: 완료
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

- Backlog status: `완료`.
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

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .harness/traces/evolution/
- tests/test_repository_search_set.py
- backlog/core.md

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

Implementation notes:

- Added `.harness/traces/evolution/002-self-application-evidence-review.md`, a
  substantive repository self-application evolution trace using the documented
  evolution frontmatter shape.
- Recorded the 2026-05-04 review concern that tracked self-application evidence
  is still thin, without manufacturing failure or experiment traces.
- Documented that legacy `.claude/traces/` history was not blindly copied
  because it is ignored and may contain provider/session-local context.
- Extended `tests/test_repository_search_set.py` so the second evolution trace
  remains part of the minimum self-application trace surface and preserves the
  evidence-boundary wording.

Search-set verification:

- before: PASS `python3 scripts/run-search-set.py`.
- after: PASS `python3 scripts/run-search-set.py`.
- after: PASS `python3 scripts/run-search-set.py --case SS-006`.
- after: PASS `python3 -m unittest tests/test_repository_search_set.py`.
- after: PASS `python3 scripts/check-maintenance-review.py`.
- after: PASS `python3 scripts/check-compat-mirrors.py`.
- after: PASS `python3 -m unittest discover -s tests`.
- after: PASS `python3 -m unittest discover -s adapters/claude/tests`.
- after: PASS `python3 -m unittest discover -s adapters/codex/tests`.
- after: PASS `sh .githooks/pre-commit`.
- after: PASS `python3 scripts/check-search-set-evidence.py`.

Review notes:

- Initial isolated reviewer score: 8/10 VETO. Blocking findings: missing
  Completion Gate / multi-review record, and evolution trace `files_changed`
  omitted `tests/test_repository_search_set.py`.
- VETO handling before re-review: updated the trace frontmatter to include the
  focused test and added this Completion Gate.

Multi-review:

- Result: PASS after VETO handling and final isolated re-review.
- Isolated evidence reviewer, initial: score 8/10; verdict VETO; Blocking
  findings: missing Completion Gate / search-set evidence record and
  underreported trace `files_changed`; not accepted until VETO findings are
  fixed and rerun.
- Isolated evidence reviewer, final rerun: score 9/10; verdict PASS; Blocking
  findings: none. Why not 10: final review-record closure was still pending at
  the moment of review; no backlog follow-up because this record now closes it.
- Score handling: score below 9 was treated as VETO. Blocking findings were
  addressed before rerun; final rerun reached 9/10.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: final isolated re-review completed after Completion Gate and
  metadata correction; score 9/10 PASS.
- Final acceptance: accepted; ready for item 47 commit.

Completion Gate:

- Backlog status: `완료`.
- Changed files:
  `.harness/traces/evolution/002-self-application-evidence-review.md`,
  `tests/test_repository_search_set.py`, `backlog/core.md`.
- Scope deviations: `tests/test_repository_search_set.py` was added to Scope
  before editing so the new trace is mechanically protected.
- Verification results: PASS `python3 -m unittest
  tests/test_repository_search_set.py`; PASS `python3 scripts/run-search-set.py
  --case SS-006`; PASS `python3 scripts/run-search-set.py`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 -m unittest discover -s
  tests`; PASS `python3 -m unittest discover -s adapters/claude/tests`; PASS
  `python3 -m unittest discover -s adapters/codex/tests`; PASS `sh
  .githooks/pre-commit`; PASS `python3 scripts/check-search-set-evidence.py`;
  PASS `git diff --check`.
- Search-set verification: PASS before/after with `python3
  scripts/run-search-set.py`; targeted after check also PASS with `python3
  scripts/run-search-set.py --case SS-006`.
- Multi-review required: yes; repository self-application trace evidence is
  durable regression-memory/methodology evidence.
- Multi-review result: PASS after final isolated re-review.
- Reviewer scores and VETO handling: initial isolated reviewer 8/10 VETO;
  blocking findings addressed; final isolated reviewer rerun 9/10 PASS.
- For each score-9 result, why not 10: final review-record closure was still
  pending at the moment of final review; accepted as procedural residual because
  this record now closes it.
- Backlog items added from score-9 residual risk: none; no actionable
  repository improvement.
- Residual risk/follow-up: none.
- Accepted: yes; ready for item 47 commit.

### 48. P2 add one executable release verification gate

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- scripts/verify-release.py
- tests/test_verify_release.py
- MAINTENANCE.md
- backlog/core.md

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

Decision implemented:

- Added `scripts/verify-release.py` as the executable stable-handoff gate.
- The release gate runs the documented Standard verification commands, the
  repository Active search-set runner, and `python3 scripts/check-clean-worktree.py`.
- Added `--list` so maintainers and tests can inspect the exact command list
  without running it.
- Added `--skip-clean-worktree` for validating an in-progress maintenance diff
  before the final clean handoff; the default release path still includes the
  clean-worktree gate.
- Added focused tests that protect the command list, ensure plain root-level
  `python3 -m unittest discover` is not used, verify clean-worktree skipping
  only removes the clean gate, and check that `MAINTENANCE.md` documents the
  preferred stable-handoff command.
- Documented `python3 scripts/verify-release.py` in `MAINTENANCE.md`.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because this
  release-gate item started from a clean `main`; baseline
  `python3 scripts/run-search-set.py --list`, `python3
  scripts/check-maintenance-review.py backlog/core.md`, and `python3
  scripts/check-search-set-evidence.py` passed before edits.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Multi-review:

- First isolated release-gate reviewer: score 8/10, VETO. Blocking findings:
  P1 `scripts/verify-release.py` had a shebang but lacked executable file mode;
  P2 command-list tests duplicated expected strings instead of deriving the
  Standard verification block from `MAINTENANCE.md`, and did not protect the
  autoresearch hook smoke command against drift. Not accepted.
- Score handling: score below 9 was treated as VETO. Blocking findings were
  fixed by making `scripts/verify-release.py` executable and updating
  `tests/test_verify_release.py` to parse the Standard verification block from
  `MAINTENANCE.md` and require every documented command in the release gate.
- Affected reviewer rerun: score 9/10, PASS. Blocking findings: none. Why not
  10: the rerun happened while this record still said final acceptance was
  blocked pending that rerun; final closure was still needed after receiving the
  rerun result.
- Score handling: the score-9 why-not-10 reason was procedural and is addressed
  by this Completion Gate; no backlog follow-up is needed.
- Rerun status: affected reviewer rerun reached score 9/10 PASS.
- Follow-up/residual risk: none.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `scripts/verify-release.py`, `tests/test_verify_release.py`,
  `MAINTENANCE.md`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest tests/test_verify_release.py`;
  PASS `python3 scripts/verify-release.py --list`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `python3
  scripts/run-search-set.py`; PASS `python3 scripts/check-maintenance-review.py
  backlog/core.md`; PASS `python3 scripts/check-maintenance-review.py`; PASS
  `python3 scripts/check-search-set-evidence.py`; PASS `python3 -m unittest
  tests/test_backlog_heading_uniqueness.py`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED with reason above.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; release/stable-handoff gate semantics.
- Multi-review result: PASS after VETO fix and affected reviewer rerun.
- Reviewer scores and VETO handling: see Multi-review records above; initial
  VETO blocking findings were fixed and the affected reviewer rerun passed.
- For each score-9 result, why not 10: final backlog closure was still pending
  at the moment of rerun; addressed by this Completion Gate.
- Backlog items added from score-9 residual risk: none; procedural closure was
  completed in this item.
- Residual risk/follow-up: none.
- Accepted: yes; ready for commit.

Follow-up multi-review revalidation, 2026-05-04:

- Reason: maintainer clarified that required multi-review should use multiple
  reviewers/critics rather than the earlier single isolated reviewer path. This
  follow-up revalidates item 48 under the clarified policy without changing the
  implementation files.
- Changed files for this follow-up: `backlog/core.md`.
- Verification results: PASS `python3 -m unittest tests/test_verify_release.py`;
  PASS `python3 scripts/verify-release.py --list`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED; follow-up is review-record-only and does not change
    harness behavior. Existing item 48 search-set implementation evidence is
    recorded above.
  - AFTER: SKIPPED; follow-up is review-record-only and does not change harness
    behavior.
- Multi-review required: yes; item 48 changes release/stable-handoff gate
  semantics and is being revalidated under the clarified multi-review policy.

Follow-up multi-review:

- Release-gate command coverage critic: score 10/10, PASS. Blocking findings:
  none.
- Test/drift-protection critic: score 9/10, PASS. Blocking findings: none. Why
  not 10: tests protect Standard verification inclusion plus search-set and
  clean-worktree gates, but do not assert exact command ordering or exact
  command-list equality beyond those required gates.
- Process-compliance critic: score 8/10, VETO. Blocking findings: item 48 still
  recorded the old single-review path rather than the true multi-review
  revalidation, and `Status: 진행중` conflicted with the existing Completion Gate.
  Not accepted.
- Score handling: the score below 9 was treated as VETO. Blocking findings were
  fixed by adding this follow-up multi-review record with critic scopes, scores,
  verdicts, why-not-10 handling, VETO handling, rerun status, and a consistent
  `리뷰대기` status.
- Affected process-compliance critic rerun: score 9/10, PASS. Blocking
  findings: none. Why not 10: final closure still depended on recording this
  rerun result and updating final acceptance from blocked to accepted.
- Rerun status: affected process-compliance critic rerun reached score 9/10
  PASS.
- Follow-up/residual risk: the test/drift-protection score-9 reason is accepted
  as residual risk for this revalidation because item 48's current contract is
  Standard command inclusion plus explicit search-set and clean-worktree gates,
  not a frozen total order. No backlog item added.
- Final acceptance: accepted after this follow-up Completion Gate.

Follow-up Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `backlog/core.md`.
- Scope deviations: none; follow-up revalidation changed only the item 48
  record.
- Verification results: PASS `python3 -m unittest tests/test_verify_release.py`;
  PASS `python3 scripts/verify-release.py --list`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED; record-only follow-up, no harness behavior changed.
  - AFTER: SKIPPED; record-only follow-up, no harness behavior changed.
- Multi-review required: yes; follow-up revalidates release-gate semantics under
  the clarified multi-review policy.
- Multi-review result: PASS after three-critic multi-review, VETO fix, and
  affected process-compliance critic rerun.
- Reviewer scores and VETO handling: command-coverage critic 10/10 PASS;
  test/drift-protection critic 9/10 PASS; process-compliance critic 8/10 VETO,
  fixed and rerun to 9/10 PASS.
- For each score-9 result, why not 10: test/drift-protection critic noted the
  tests do not enforce exact command ordering or exact command-list equality
  beyond Standard inclusion plus explicit release-only gates; process-compliance
  critic noted final closure was pending at rerun time, addressed by this gate.
- Backlog items added from score-9 residual risk: none; ordering/equality is
  accepted as residual risk for the current release-gate contract, and
  procedural closure is completed here.
- Residual risk/follow-up: accepted command-order/equality residual risk.
- Accepted: yes; ready for commit.

### 49. P3 guard against root unittest discovery false greens

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- test_root_unittest_discovery.py
- backlog/core.md

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

Decision implemented:

- Added root-level `test_root_unittest_discovery.py` as a sentinel discovered by
  plain `python3 -m unittest discover`.
- The sentinel fails intentionally with a message directing maintainers to the
  three explicit Standard verification unittest roots.
- Updated `MAINTENANCE.md` to state that plain root-level unittest discovery is
  not a repository verification signal and that the explicit suite roots remain
  canonical.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the item
  was selected from a clean `main`, baseline `python3 -m unittest discover`
  already reproduced the false green, and `python3 scripts/run-search-set.py
  --list` confirmed the Active case inventory before edits. Baseline
  `python3 -m unittest discover -s tests` passed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Multi-review:

- First isolated release-gate reviewer: score 8/10, VETO. Blocking findings:
  P1 record search-set evidence before acceptance; P2 Scope named
  `tests/test_root_unittest_discovery.py`, but the actual sentinel is
  root-level `test_root_unittest_discovery.py`. Not accepted.
- Score handling: score below 9 was treated as VETO. Blocking findings were
  fixed by correcting the Scope path and adding this search-set evidence
  record.
- Affected reviewer rerun: score 9/10, PASS. Blocking findings: none. Why not
  10: the rerun happened while this record still said `Final acceptance: no`;
  final closure was still needed after receiving the rerun result.
- Score handling: the score-9 why-not-10 reason was procedural and is addressed
  by this Completion Gate; no backlog follow-up is needed.
- Rerun status: affected reviewer rerun reached score 9/10 PASS.
- Follow-up/residual risk: none.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `MAINTENANCE.md`, `test_root_unittest_discovery.py`,
  `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest discover -s tests`; PASS
  `python3 -m unittest discover -s adapters/claude/tests`; PASS `python3 -m
  unittest discover -s adapters/codex/tests`; EXPECTED FAIL `python3 -m
  unittest discover` with the root sentinel guidance message; PASS `python3
  scripts/run-search-set.py`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; PASS `python3
  scripts/check-codex-marketplace-metadata.py` with deferred publication
  manifest note; PASS `python3 scripts/check-claude-adapter-paths.py`; PASS
  `python3 scripts/sync-codex-plugin.py --check`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `git diff --check`.
- Search-set verification: BEFORE SKIPPED with reason above; AFTER PASS
  `python3 scripts/run-search-set.py`.
- Multi-review required: yes; release/test verification gate semantics.
- Multi-review result: PASS after VETO fix and affected reviewer rerun.
- Reviewer scores and VETO handling: see Multi-review records above; initial
  VETO blocking findings were fixed and the affected reviewer rerun passed.
- For each score-9 result, why not 10: final backlog closure was still pending
  at the moment of rerun; addressed by this Completion Gate.
- Backlog items added from score-9 residual risk: none; procedural closure was
  completed in this item.
- Residual risk/follow-up: none.
- Accepted: yes; ready for commit.

### 50. P2 harden search-set evidence checker text matching

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- scripts/check-search-set-evidence.py
- tests/test_search_set_evidence.py
- MAINTENANCE.md
- backlog/core.md

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

Decision implemented:

- Tightened `scripts/check-search-set-evidence.py` so `Search-set verification`
  records must use structured `BEFORE:` / `AFTER:` evidence lines with
  PASS/FAIL/SKIPPED status, or a structured `SKIPPED:` reason.
- Ambiguous text such as `not skipped`, `TODO`, `TBD`, or `unchecked` invalidates
  the record instead of satisfying it by keyword accident.
- Updated `MAINTENANCE.md` with the accepted structured evidence examples.
- Added focused tests for valid before/after evidence, valid skipped reasons,
  `not skipped` false positives, vague before/after prose, and TODO text inside
  otherwise structured evidence.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because this
  checker-hardening item started from a clean `main`, baseline `python3 -m
  unittest tests/test_search_set_evidence.py` passed, baseline `python3
  scripts/check-search-set-evidence.py` passed, and `python3
  scripts/run-search-set.py --list` confirmed the Active case inventory before
  edits.
- AFTER: PASS `python3 scripts/run-search-set.py`; PASS rerun after VETO fixes
  with the same command.

Multi-review:

- First isolated release-gate reviewer: score 8/10, VETO. Blocking findings:
  P1 structured PASS evidence still accepted prose-only lines without command
  evidence; P2 legacy no-colon `BEFORE PASS` / `AFTER PASS` shape still matched
  despite docs requiring `BEFORE:` / `AFTER:`. Not accepted.
- Score handling: score below 9 was treated as VETO. Blocking findings were
  fixed by requiring colons in `BEFORE:` / `AFTER:` lines and requiring
  backticked command evidence for PASS/FAIL before-after records.
- Affected reviewer rerun: score 9/10, PASS. Blocking findings: none. Why not
  10: the checker is intentionally syntactic; it confirms structured evidence
  and backticked command text, but does not prove the command is the correct
  Active search-set command or that it actually ran.
- Score handling: the score-9 why-not-10 reason is accepted as residual risk
  because `MAINTENANCE.md` explicitly says the checker is lightweight and does
  not prove full methodology compliance.
- Rerun status: affected reviewer rerun reached score 9/10 PASS.
- Follow-up/residual risk: accepted syntactic-checker limitation; no backlog
  item added because stronger semantic proof is outside this checker's stated
  policy.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `scripts/check-search-set-evidence.py`,
  `tests/test_search_set_evidence.py`, `MAINTENANCE.md`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_search_set_evidence.py`; PASS `python3 scripts/check-search-set-evidence.py`;
  PASS `python3 scripts/check-maintenance-review.py backlog/core.md`; PASS
  `python3 scripts/check-maintenance-review.py`; PASS `python3 -m unittest
  discover -s tests`; PASS `python3 -m unittest discover -s
  adapters/claude/tests`; PASS `python3 -m unittest discover -s
  adapters/codex/tests`; PASS `python3 scripts/check-compat-mirrors.py`; PASS
  `python3 scripts/check-claude-adapter-paths.py`; PASS `python3
  scripts/sync-codex-plugin.py --check`; PASS `python3
  adapters/codex/scripts/check-codex-hook-schema-drift.py`; PASS `python3
  adapters/codex/scripts/smoke-autoresearch-hooks.py --checker
  adapters/codex/scripts/check-autoresearch-protected.py --protected-file
  adapters/codex/templates/autoresearch-protected.txt`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin.py`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; PASS `python3
  scripts/check-codex-marketplace-metadata.py` with deferred publication
  manifest note; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED with reason above.
  - AFTER: PASS `python3 scripts/run-search-set.py`, including rerun after
    VETO fixes.
- Multi-review required: yes; release/search-set evidence checker semantics.
- Multi-review result: PASS after VETO fix and affected reviewer rerun.
- Reviewer scores and VETO handling: see Multi-review records above; initial
  VETO blocking findings were fixed and the affected reviewer rerun passed.
- For each score-9 result, why not 10: checker remains intentionally syntactic
  and does not prove command correctness or execution.
- Backlog items added from score-9 residual risk: none; accepted as the
  lightweight checker policy documented in `MAINTENANCE.md`.
- Residual risk/follow-up: accepted syntactic-checker limitation.
- Accepted: yes; ready for commit.

### 51. P3 keep active core Current Status aligned with completed items

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- tests/test_backlog_heading_uniqueness.py
- backlog/core.md

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

Decision implemented:

- Added a focused backlog consistency test that parses `backlog/core.md`
  `Current Status` active candidate wording of the form `item N should`.
- Every named active candidate must currently have `Status: 대기`; completed,
  review-pending, in-progress, or missing items fail the check.
- The check allows an accurate no-active-candidate state by passing when
  `Current Status` names no `item N should` candidates.
- Refreshed `Current Status` so only item 48 and item 52 remain selectable core
  candidates; items 41-47 and 49-51 are explicitly non-selectable.

Search-set verification:

- SKIPPED: backlog consistency/test-only governance guard; no harness runtime,
  release gate, adapter behavior, or search-set contract changed.

Multi-review:

- First isolated backlog-consistency reviewer: score 8/10, VETO. Blocking findings:
  the initial test required `Current Status` to name at least one
  active candidate, which would fail an accurate no-selectable-items state. Not
  accepted.
- Score handling: score below 9 was treated as VETO. Blocking finding fixed by
  allowing zero active candidates while still rejecting any named candidate that
  is not `Status: 대기`.
- Affected reviewer rerun: score 9/10, PASS. Blocking findings: none. Why not
  10: the guard is intentionally wording-convention based; it protects the
  current `item N should` active-candidate phrasing, but does not semantically
  detect every possible future wording for selectable work.
- Score handling: the score-9 why-not-10 reason is accepted as residual risk
  because this backlog uses the `item N should` convention in `Current Status`,
  and broader natural-language inference would make the focused checker brittle.
- Rerun status: affected reviewer rerun reached score 9/10 PASS.
- Follow-up/residual risk: accepted wording-convention limitation; no backlog
  item added.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `tests/test_backlog_heading_uniqueness.py`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_backlog_heading_uniqueness.py`; PASS `python3 scripts/check-maintenance-review.py
  backlog/core.md`; PASS `python3 scripts/check-search-set-evidence.py`; PASS
  `python3 -m unittest discover -s tests`; PASS `python3 -m unittest discover
  -s adapters/claude/tests`; PASS `python3 -m unittest discover -s
  adapters/codex/tests`; PASS `python3 scripts/check-compat-mirrors.py`; PASS
  `python3 scripts/check-claude-adapter-paths.py`; PASS `python3
  scripts/sync-codex-plugin.py --check`; PASS `python3
  scripts/check-codex-marketplace-metadata.py` with deferred publication
  manifest note; PASS `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`;
  PASS `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker
  adapters/codex/scripts/check-autoresearch-protected.py --protected-file
  adapters/codex/templates/autoresearch-protected.txt`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin.py`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; PASS `git diff
  --check`.
- Search-set verification: SKIPPED; backlog consistency/test-only governance
  guard; no harness runtime, release gate, adapter behavior, or search-set
  contract changed.
- Multi-review required: yes; committed stable handoff review loop.
- Multi-review result: PASS after VETO fix and affected reviewer rerun.
- Reviewer scores and VETO handling: see Multi-review records above; initial
  VETO blocking finding was fixed and the affected reviewer rerun passed.
- For each score-9 result, why not 10: checker is wording-convention based and
  does not infer every possible future phrasing.
- Backlog items added from score-9 residual risk: none; accepted as scoped
  checker behavior for the current `Current Status` convention.
- Residual risk/follow-up: accepted wording-convention limitation.
- Accepted: yes; ready for commit.

### 52. P3 schema-check repository self-application evolution traces

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .harness/traces/evolution/001-repository-self-application-root.md
- tests/test_repository_search_set.py
- backlog/core.md

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

Decision implemented:

- Updated `.harness/traces/evolution/001-repository-self-application-root.md`
  from a reduced bootstrap record to the full repository evolution schema:
  `iteration`, `type`, `verdict`, `files_changed`, `refs`, and the
  Diagnosis/Change/Result/Lesson structure.
- Added a focused schema test for every tracked repository evolution record in
  `.harness/traces/evolution/*.md`.
- The schema check requires the frontmatter fields documented in
  `core/reference.md`, validates allowed `type` and `verdict` values, checks
  `files_changed` and `refs` list syntax, and requires Before/After result
  bullets.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the item
  was selected from a clean `main`, baseline `python3 -m unittest
  tests/test_repository_search_set.py` passed, baseline `python3
  scripts/run-search-set.py --list` confirmed the Active case inventory, and the
  change was a trace-schema/test hardening pass.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Multi-review:

- Isolated trace-schema reviewer: score 9/10, PASS. Blocking findings: none.
  Why not 10: the schema check is intentionally syntactic rather than a full
  YAML/schema parser; it does not validate date format, parse `files_changed` or
  `refs` as actual lists, or require Before/After to appear specifically inside
  `### Result`.
- Score handling: the score-9 why-not-10 reason is accepted as residual risk
  because this is a scoped P3 hardening item and the repository currently needs
  a lightweight guard against missing fields/sections rather than a full schema
  validator.
- Rerun status: no VETO, so no rerun required.
- Follow-up/residual risk: accepted syntactic-schema limitation; no backlog item
  added.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files:
  `.harness/traces/evolution/001-repository-self-application-root.md`,
  `tests/test_repository_search_set.py`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_repository_search_set.py`; PASS `python3 -m unittest
  tests/test_backlog_heading_uniqueness.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/check-search-set-evidence.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-maintenance-review.py`; PASS `python3 -m unittest discover -s
  tests`; PASS `python3 -m unittest discover -s adapters/claude/tests`; PASS
  `python3 -m unittest discover -s adapters/codex/tests`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3 scripts/check-claude-adapter-paths.py`;
  PASS `python3 scripts/sync-codex-plugin.py --check`; PASS `python3
  adapters/codex/scripts/check-codex-hook-schema-drift.py`; PASS `python3
  adapters/codex/scripts/smoke-autoresearch-hooks.py --checker
  adapters/codex/scripts/check-autoresearch-protected.py --protected-file
  adapters/codex/templates/autoresearch-protected.txt`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin.py`; PASS `python3
  adapters/codex/scripts/smoke-local-plugin-activation.py`; PASS `python3
  scripts/check-codex-marketplace-metadata.py` with deferred publication
  manifest note; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED with reason above.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; repository trace/schema durable contract.
- Multi-review result: PASS.
- Reviewer scores and VETO handling: see Multi-review record above; isolated
  trace-schema reviewer passed and no VETO occurred.
- For each score-9 result, why not 10: schema check is syntactic and does not
  fully parse YAML/list/date semantics or enforce Before/After placement within
  `### Result`.
- Backlog items added from score-9 residual risk: none; accepted as scoped P3
  hardening and lightweight repository-applied schema guard.
- Residual risk/follow-up: accepted syntactic-schema limitation.
- Accepted: yes; ready for commit.

### 53. P2 document the reviewed commit loop

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- backlog/core.md

Source discussion: 2026-05-04 maintainer request to make the current
single-item, isolated-review, why-not-10, verification, and commit procedure
reproducible for future sessions.

The maintenance policy already required Start Gate, Completion Gate,
multi-review, VETO handling, and score-9 why-not-10 recording. It did not yet
state the new stable handoff loop as one repeatable sequence that includes
isolated reviewer review, rerun after VETO, item-only staging, staged diff
checks, commit, and clean-worktree handling.

Decision implemented:

- Added `MAINTENANCE.md` `Reviewed Commit Loop` under Single-Session
  Maintenance.
- The loop explicitly tells future sessions to pick exactly one item, reserve
  it, run baseline/focused/standard verification, use an isolated reviewer
  before acceptance, treat scores below 9 as VETO, record every score-9
  why-not-10 reason, complete the Completion Gate, stage only the selected
  item's files or hunks, inspect and verify the staged diff, commit, and run or
  record the clean-worktree handoff check.

Search-set verification:

- SKIPPED: this was a direct maintainer-requested governance documentation
  clarification started before a backlog record existed. After the record was
  added, `python3 scripts/check-search-set-evidence.py` passed, confirming the
  skipped reason is explicit.

Multi-review:

- Result: PASS after isolated reviewer check.
- Isolated governance reviewer: score 9/10; verdict PASS; Blocking findings:
  none. Why not 10: the staged-diff step originally required
  `git diff --cached --name-status` and `git diff --cached --check`, but did
  not explicitly require inspecting the staged patch itself. This was fixed in
  this item by adding `git diff --cached`.
- Score handling: score 9 accepted after recording why not 10 and folding the
  actionable improvement into this item.
- Blocking findings: none.
- Follow-up/residual risk: none.
- Rerun status: no VETO, so no rerun required.
- Final acceptance: accepted; ready for commit.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `MAINTENANCE.md`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 scripts/check-maintenance-review.py`;
  PASS `git diff --check`; PASS `python3 scripts/check-search-set-evidence.py`
  after this backlog record was added.
- Search-set verification: SKIPPED with reason above.
- Multi-review required: yes; maintenance governance / reviewed commit
  procedure.
- Multi-review result: PASS.
- Reviewer scores and VETO handling: isolated governance reviewer 9/10 PASS; no
  VETO.
- For each score-9 result, why not 10: staged patch inspection was not explicit
  enough in the first draft; fixed in this item by adding `git diff --cached`.
- Backlog items added from score-9 residual risk: none; actionable improvement
  was handled in this item.
- Residual risk/follow-up: none.
- Accepted: yes; ready for commit.

### 54. P2 distinguish multi-review skill use from isolated reviewer gate

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- tests/test_maintenance_policy_boundaries.py
- backlog/core.md

Source discussion: 2026-05-04 maintainer clarification that when multi-review is
required, the intended direction is to use the multi-review skill with multiple
reviewers/critics, not to satisfy the requirement with a single isolated
reviewer.

The `Reviewed Commit Loop` currently says to ask an isolated reviewer when
multi-review is required or when an item will be committed as a stable handoff.
That wording can make a single-reviewer stable-handoff check look equivalent to
required multi-review. It should distinguish:

- required multi-review for adapter behavior, release gates, hook semantics,
  core methodology boundaries, and durable contracts; and
- single isolated reviewer checks for committed handoff hygiene when
  multi-review is not required.

Done when:

- `MAINTENANCE.md` clearly says required multi-review uses multiple
  reviewers/critics through the multi-review skill or an explicitly documented
  equivalent.
- The reviewed commit loop no longer implies one isolated reviewer can satisfy
  required multi-review.
- Completion Gate wording remains able to record single-reviewer stable-handoff
  checks separately from required multi-review.

Decision implemented:

- Updated the `Reviewed Commit Loop` so required multi-review must use the
  multi-review skill or an explicitly documented equivalent with multiple
  reviewers/critics.
- Clarified that a single isolated reviewer is used for committed
  stable-handoff hygiene when multi-review is not required, and must not be
  recorded as satisfying required multi-review.
- Added `Multi-Review Use` wording that defines required multi-review as
  multiple distinct reviewers or critics, prefers the multi-review skill, and
  requires explicit fallback documentation if the skill cannot be used.
- Added a focused maintenance policy boundary test for the distinction.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation; operator did
  not run the full Active set before the first policy edit. Baseline focused
  gates did pass before edits: `python3 scripts/check-maintenance-review.py
  backlog/core.md` and `python3 scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Multi-review:

- Policy-semantics critic: score 8/10, VETO. Blocking findings: stable-handoff
  reviewer wording was internally inconsistent because `Reviewed Commit Loop`
  required a single reviewer for non-multi-review stable handoffs while
  `Multi-Review Use` called it optional. Not accepted.
- Test/enforceability critic: score 8/10, VETO. Blocking findings:
  `tests/test_maintenance_policy_boundaries.py` asserted the new wording existed
  but did not reject the old combined wording that asked for an isolated
  reviewer when multi-review was required. Not accepted.
- Process-compliance critic: score 8/10, VETO. Blocking findings: item lacked a
  complete multi-review/Completion Gate record, and the original BEFORE
  search-set skipped reason was too weak for a harness-affecting governance
  change. Not accepted.
- Score handling: all scores below 9 were treated as VETO. Blocking findings
  were fixed by clarifying that the single-reviewer stable-handoff hygiene check
  is required only when multi-review is not required, adding negative tests for
  the old combined wording, and replacing the BEFORE search-set record with the
  exact focused baseline commands plus the full Active skip reason.
- Final policy-semantics critic rerun: score 10/10, PASS. Blocking findings:
  none.
- Final test/enforceability critic rerun: score 9/10, PASS. Blocking findings:
  none. Why not 10: wording-marker enforcement remains intentionally limited
  and cannot catch every semantically equivalent future regression.
- Final process-compliance critic rerun: score 9/10, PASS. Blocking findings:
  none. Why not 10: full Active search-set was not run before the first edit,
  though the record is now honest and focused baseline gates plus full AFTER
  PASS are recorded.
- Score handling: the policy-semantics score-9 reason was addressed in this
  item by harmonizing `reviewer or critic` score wording in general policy
  areas. The remaining score-9 reasons are accepted as residual risk: focused
  wording-marker tests are appropriate for this policy boundary, and the BEFORE
  search-set process imperfection is recorded honestly rather than overclaimed.
- Rerun status: all affected critics reran; final scores are 10/10, 9/10, and
  9/10 PASS.
- Follow-up/residual risk: accepted marker-test limitation and recorded BEFORE
  search-set process imperfection; no backlog item added.
- Final acceptance: accepted after this Completion Gate.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `MAINTENANCE.md`,
  `tests/test_maintenance_policy_boundaries.py`, `backlog/core.md`.
- Scope deviations: `tests/test_maintenance_policy_boundaries.py` was added to
  Scope after the implementation needed a focused policy-boundary test; Scope
  was updated before final acceptance.
- Verification results: PASS `python3 -m unittest
  tests/test_maintenance_policy_boundaries.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation with exact
    reason above; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes maintenance review-contract
  semantics.
- Multi-review result: PASS after three-critic multi-review, VETO fixes, and
  affected critic reruns.
- Reviewer scores and VETO handling: see Multi-review records above; all
  initial VETO blocking findings were fixed and all final affected reruns
  passed.
- For each score-9 result, why not 10: test/enforceability critic says the guard
  is marker/string-level and cannot catch every semantically equivalent future
  regression; process critic says full Active search-set was not run before the
  first edit, though this is now recorded honestly with focused baseline gates
  and AFTER PASS.
- Backlog items added from score-9 residual risk: none; both score-9 reasons are
  accepted residual risks for this scoped policy clarification.
- Residual risk/follow-up: accepted marker-test limitation and recorded BEFORE
  search-set process imperfection.
- Accepted: yes; ready for commit.

### 55. P3 mark accepted completed maintenance items as complete

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- tests/test_maintenance_policy_boundaries.py
- backlog/core.md

Source discussion: 2026-05-04 maintainer clarification that completed
maintenance items should be moved from `리뷰대기` to `완료`.

The reviewed commit loop still says to complete the Completion Gate and mark
the item `리뷰대기`, even when the same workflow has accepted, committed, and
cleanly verified the item. That can leave completed maintenance records in a
handoff state after acceptance and makes future backlog scans noisier.

Potential improvement:

- Update `MAINTENANCE.md` so accepted items that are completed in the current
  maintenance session are marked `완료`, not left at `리뷰대기`.
- Preserve `리뷰대기` for work that is implemented but awaiting external review,
  merge coordination, or maintainer acceptance.
- Add a focused policy-boundary test so the reviewed commit loop does not
  regress to marking accepted completed items `리뷰대기`.

Done when:

- The status definitions and reviewed commit loop distinguish review-pending
  handoff from completed accepted work.
- Focused maintenance policy tests pass.

Decision implemented:

- Updated `MAINTENANCE.md` status definitions so `리뷰대기` is reserved for
  implementation that is still waiting for external review, merge coordination,
  or maintainer acceptance.
- Updated the reviewed commit loop so accepted completed items are marked
  `완료`, while `리뷰대기` remains available for genuinely pending handoffs.
- Added a focused maintenance policy boundary test that asserts the new
  completed-item wording and rejects the old `mark the item 리뷰대기` loop.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py --list` confirmed the Active
  case inventory before edits; focused baseline gates also passed: `python3 -m
  unittest tests/test_maintenance_policy_boundaries.py`, `python3
  scripts/check-maintenance-review.py backlog/core.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Multi-review:

- Policy-semantics critic: score 9/10, PASS. Blocking findings: none. Why not
  10: the first draft of the `완료` definition repeated "accepted" wording; this
  actionable wording issue was fixed in this item by simplifying the definition.
- Test/enforceability critic: score 9/10, PASS. Blocking findings: none. Why
  not 10: the test is intentionally marker-string based rather than a structural
  parser for all semantically equivalent policy wording.
- Process-compliance critic: score 7/10, VETO. Blocking findings: missing
  Completion Gate evidence and item still marked `진행중`; not accepted.
- Score handling: the score below 9 was treated as VETO. Blocking findings were
  fixed by adding this Decision implemented section, search-set evidence,
  multi-review score record, Completion Gate, and by marking the accepted item
  `완료`.
- Affected process-compliance critic rerun: score 9/10, PASS. Blocking
  findings: none. Why not 10: final backlog closure still needed to record the
  rerun result and switch final acceptance from pending to accepted.
- Rerun status: all affected critics reran; final scores are 9/10, 9/10, and
  9/10 PASS.
- Follow-up/residual risk: accepted marker-test limitation and procedural
  final-closure timing.
- Final acceptance: accepted after affected critic rerun.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `MAINTENANCE.md`,
  `tests/test_maintenance_policy_boundaries.py`, `backlog/core.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_maintenance_policy_boundaries.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py --list` confirmed Active
    case inventory before edits; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes maintenance workflow/status
  semantics.
- Multi-review result: PASS after three-critic multi-review, VETO fix, and
  affected process-compliance critic rerun.
- Reviewer scores and VETO handling: policy-semantics critic 9/10 PASS;
  test/enforceability critic 9/10 PASS; process-compliance critic 7/10 VETO.
  VETO blocking findings were fixed by completing the backlog evidence and
  changing status to `완료`; affected process-compliance critic rerun reached
  9/10 PASS.
- For each score-9 result, why not 10:
  - Policy-semantics critic: not 10 because of redundant accepted wording in the
    `완료` definition; fixed in this item.
  - Test/enforceability critic: not 10 because marker-string tests remain
    somewhat brittle; accepted as residual risk for this focused
    policy-boundary test style.
  - Process-compliance critic rerun: not 10 because final backlog closure still
    needed recording at rerun time; addressed by this Completion Gate.
- Backlog items added from score-9 residual risk: none; the actionable wording
  issue was fixed here, and the marker-test limitation is accepted residual
  risk.
- Residual risk/follow-up: accepted marker-test limitation; procedural
  final-closure timing addressed by this Completion Gate.
- Accepted: yes.

### 56. P2 track repeated nonindependent multi-review fallback as systemic risk

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- scripts/check-maintenance-review.py
- tests/test_check_maintenance_review.py
- backlog/core.md

Source review: 2026-05-04 multi-review of current local `main` against the
Meta-Harness methodology.

The latest governance critic passed the current maintenance and multi-review
gates, but noted one repeated residual risk: several durable-contract backlog
items were accepted through documented `FALLBACK_NONINDEPENDENT` or sequential
review paths. The records are honest and the current policy now distinguishes
required multi-review from single isolated reviewer checks, but repeated
fallback use can become a quiet assurance downgrade if it is always treated as
session-local rather than as an observable maintenance signal.

Potential improvement:

- Add a lightweight policy or checker signal that counts or flags required
  multi-review records using `FALLBACK_NONINDEPENDENT`, sequential fallback, or
  another explicitly weaker review mode.
- Define when repeated fallback is acceptable, such as unavailable sub-agent
  support, emergency recovery, or explicitly low-risk documentation cleanup.
- Define when repeated fallback should create follow-up work, such as multiple
  durable-contract acceptances in a short window without independent critics.
- Keep this as a governance visibility item; do not retroactively invalidate
  completed records that already document fallback and VETO handling honestly.

Done when:

- `MAINTENANCE.md` or the review checker makes repeated nonindependent fallback
  visible as a review-quality signal.
- Future Completion Gates can distinguish a one-off fallback from a repeated
  systemic fallback pattern.
- Focused tests or checker fixtures cover the chosen signal if it is made
  mechanical.
- Multi-review checks the result because this changes review-governance policy.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline PASS
  `python3 -m unittest tests/test_check_maintenance_review.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `git diff --check`.

Decision implemented:

- Added `MAINTENANCE.md` policy that treats one-off nonindependent fallback as
  acceptable only when explicitly justified, while repeated nonindependent
  fallback on durable-contract decisions becomes a review-quality signal.
- Added a non-failing `scripts/check-maintenance-review.py` quality-signal pass
  that reports `FALLBACK_NONINDEPENDENT`, documented sequential fallback, and
  related nonindependent multi-review records found inside review sections.
- Added focused checker tests showing fallback quality signals are visible
  without retroactively invalidating otherwise valid review records.

Multi-review:

- Governance-policy critic: score 9, PASS. Blocking findings: none. Why not
  10: the policy relies on active-session judgment to decide whether repeated
  fallback concerns durable-contract decisions rather than mechanically
  classifying durable-contract records. No backlog item added because this item
  intentionally chose visibility over retroactive enforcement.
- Checker/test critic: score 9, PASS. Blocking findings: none. Why not 10: the
  matcher is phrase-based around documented markers and may miss nearby
  spellings such as hyphenated `non-independent`. No backlog item added because
  the signal is a visibility aid, not the enforcement gate.
- Maintenance-process critic: initial score 6, VETO. Blocking findings:
  Completion Gate and required multi-review results were not yet recorded, and
  post-implementation verification was not fully listed in the item record.
- Maintenance-process critic re-review: score 9, PASS. Blocking findings:
  none. Why not 10: the process record was substantively complete after VETO
  recovery, but still needed final placeholder cleanup before commit. No
  backlog item added because this was resolved in the current item record.
- Score handling: two required critics scored 9; the process critic score 6
  triggered VETO recovery before acceptance; affected process critic rerun
  reached score 9. Every score 9 records why not 10 and residual-risk
  disposition.
- Rerun status: affected process critic rerun completed after adding the
  missing Multi-review and Completion Gate record; final process score 9.
- Follow-up/residual risk: accepted phrase-based matcher and judgment-based
  durable-contract classification as scoped residual risks for this visibility
  item.
- Final acceptance: accepted after process critic rerun.

Completion Gate:

- Backlog status: `완료` after process VETO recovery and re-review.
- Changed files: `MAINTENANCE.md`, `scripts/check-maintenance-review.py`,
  `tests/test_check_maintenance_review.py`, `backlog/core.md`.
- Scope deviations: none; unrelated dirty `backlog/README.md` remains outside
  this item and unstaged.
- Verification results: PASS `python3 -m unittest
  tests/test_check_maintenance_review.py`; PASS `python3 -m unittest
  tests/test_maintenance_policy_boundaries.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `git diff --check`.
- Search-set verification: BEFORE and AFTER PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; review-governance policy and checker behavior.
- Multi-review result: PASS after process critic rerun.
- Reviewer scores and VETO handling: governance-policy critic 9 PASS;
  checker/test critic 9 PASS; maintenance-process critic initial 6 VETO; VETO
  addressed by adding the missing required multi-review and Completion Gate
  records before acceptance; maintenance-process critic rerun 9 PASS.
- Score-9 why-not-10 handling: governance-policy critic was 9 because
  durable-contract classification remains session-judgment based; checker/test
  critic was 9 because fallback detection is phrase-based and intentionally
  limited to documented markers; maintenance-process re-review was 9 because
  the process record needed final placeholder cleanup after rerun.
- Backlog items added from score-9 residual risk: none; both score-9 reasons
  are accepted residual risks for a non-failing visibility signal, and the
  process placeholder cleanup was completed in this item.
- Residual risk/follow-up: accepted residual risks above; no new follow-up.
- Accepted: yes.

### 57. P2 make search-set evidence checks work on staged or release candidate diffs

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .githooks/pre-commit
- scripts/check-search-set-evidence.py
- tests/test_search_set_evidence.py
- tests/test_pre_commit_hook.py
- MAINTENANCE.md
- backlog/core.md

Start Gate:

- Selected item: `backlog/core.md` item 57, make search-set evidence checks
  work on staged or release candidate diffs.
- Status block added: yes, item 57 marked `진행중`.
- Harness-affecting: yes; this changes release-gate/evidence-check semantics.
- Multi-review required: yes; this changes release-gate semantics and the
  maintenance verification contract.
- Minimum verification commands: `python3 -m unittest
  tests/test_search_set_evidence.py`; `python3 -m unittest
  tests/test_pre_commit_hook.py`; `python3 scripts/check-search-set-evidence.py`;
  `python3 scripts/check-search-set-evidence.py --staged`; `python3
  scripts/check-search-set-evidence.py --base-ref origin/main`; `sh
  .githooks/pre-commit`; `python3 scripts/check-maintenance-review.py
  backlog/core.md`; `python3 scripts/run-search-set.py`; `python3
  scripts/verify-release.py --skip-clean-worktree`; `git diff --check`.
- Expected scope: search-set evidence checker, pre-commit staged wiring,
  focused checker/pre-commit tests, maintenance guidance, and this backlog
  record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`scripts/check-search-set-evidence.py` currently reads `git status --porcelain`
to identify harness-affecting changes. That catches dirty in-progress work, but
it becomes weak at the stable handoff point: `scripts/verify-release.py` runs
the evidence checker and also requires a clean worktree, so a clean release
candidate can make the evidence checker pass with no affected paths to inspect.

Potential improvement:

- Add a mode that checks staged paths, a commit range, or another explicit path
  list rather than relying only on dirty worktree state.
- Decide where that mode belongs: pre-commit, `verify-release.py`, a reviewed
  commit loop command, or a release-candidate command that compares `HEAD`
  against a base ref.
- Preserve the current dirty-worktree behavior for in-progress checks if it is
  still useful.
- Add focused tests for clean tree, staged changes, explicit path lists, and
  commit-range or base-ref behavior if implemented.

Done when:

- A harness-affecting staged or release-candidate change cannot bypass
  search-set evidence checking merely because the worktree is clean.
- `MAINTENANCE.md` explains which mode maintainers should run before commit,
  before release, and during in-progress review.
- Focused tests cover the chosen source of changed paths.
- Multi-review checks the result because this changes release-gate semantics.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 -m unittest tests/test_search_set_evidence.py`, `python3
  scripts/check-search-set-evidence.py`, and `python3
  scripts/check-maintenance-review.py backlog/core.md`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Added `--staged` mode to `scripts/check-search-set-evidence.py`; it reads
  changed paths and backlog/trace records from the Git index.
- Added `--base-ref REF` mode for clean release-candidate or branch-handoff
  checks over `REF...HEAD`, with a `REF..HEAD` fallback, reading backlog/trace
  evidence records from `HEAD`.
- Kept explicit path arguments for focused/manual checks and preserved the
  default dirty-worktree mode for in-progress review.
- Wired `.githooks/pre-commit` to run `python3
  scripts/check-search-set-evidence.py --staged`.
- Updated `MAINTENANCE.md` to document default, staged, and base-ref evidence
  checker modes and when to run each.
- Added focused and temp-repo integration tests for staged index record reading,
  staged failures, base-ref path selection and committed-record reading,
  explicit-path argument conflicts, documentation, and pre-commit wiring.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `.githooks/pre-commit`; `scripts/check-search-set-evidence.py`;
  `tests/test_search_set_evidence.py`; `tests/test_pre_commit_hook.py`;
  `MAINTENANCE.md`; `backlog/core.md`.
- Scope deviations: `.githooks/pre-commit` and `tests/test_pre_commit_hook.py`
  were added to Scope before editing because staged evidence checking belongs
  in the commit-time hook. Unrelated dirty `backlog/README.md` remains outside
  item 57 and will not be staged or committed with it.
- Verification results: PASS `python3 -m unittest
  tests/test_search_set_evidence.py tests/test_pre_commit_hook.py`; PASS
  `python3 scripts/check-search-set-evidence.py`; PASS `python3
  scripts/check-search-set-evidence.py --staged`; PASS `python3
  scripts/check-search-set-evidence.py --base-ref origin/main`; PASS `sh
  .githooks/pre-commit`; PASS `python3 scripts/check-maintenance-review.py
  backlog/core.md`; PASS `python3 scripts/run-search-set.py`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes.
- Multi-review result: checker semantics critic PASS after score-9 fix;
  tests/pre-commit/docs critic PASS after score-9 fix; process critic PASS
  after VETO and score-9 completion-wording fixes.
- Reviewer scores and VETO handling: checker semantics critic initially 9/10
  PASS because `--base-ref` read record files from the working tree and relied
  on surrounding clean-worktree discipline, then fixed to read records from
  `HEAD` and rerun to 10/10 PASS; tests/pre-commit/docs critic initially 9/10
  PASS because tests monkeypatched Git-facing helpers rather than exercising a
  real Git index/range, then fixed with temp-repo integration tests and rerun
  to 10/10 PASS; process critic initially 8/10 VETO because the Start Gate had
  been misplaced under item 50, Scope underreported pre-commit/test files, and
  Completion Gate was not yet recorded; Start Gate was moved under item 57,
  Scope was corrected, and Completion Gate is now recorded.
- For each score 9, why not 10: checker semantics critic's temporary 9 was due
  to base-ref evidence records being read from the worktree instead of `HEAD`;
  fixed in this item. tests/pre-commit/docs critic's temporary 9 was due to
  lack of temp-repo integration coverage for real Git index/base-ref behavior;
  fixed in this item. Process critic's temporary 9 was due to final Completion
  Gate wording still saying process rerun and acceptance were pending; fixed in
  this item.
- Backlog items added from score-9 residual risk: none; both score-9 reasons
  and the process score-9 bookkeeping reason were actionable in-scope fixes and
  were resolved before acceptance.
- Residual risk/follow-up: none.
- Accepted: yes.

### 58. P3 decide whether search-set evidence records must reference Active cases

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- MAINTENANCE.md
- tests/test_search_set_evidence.py
- backlog/core.md

Start Gate:

- Selected item: `backlog/core.md` item 58, decide whether search-set evidence
  records must reference Active cases.
- Status block added: yes, item 58 marked `진행중`.
- Harness-affecting: yes; this clarifies release/evidence-check policy for
  harness-affecting changes.
- Multi-review required: no; this documents the checker's existing boundary
  rather than changing checker enforcement semantics.
- Minimum verification commands: `python3 -m unittest
  tests/test_search_set_evidence.py`; `python3 scripts/check-search-set-evidence.py`;
  `python3 scripts/check-search-set-evidence.py --base-ref origin/main`;
  `python3 scripts/check-maintenance-review.py backlog/core.md`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: maintenance policy text, focused checker-policy test, and
  this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The current evidence checker intentionally validates record shape, not full
methodology compliance. It accepts structured `BEFORE:` / `AFTER:` command
records or a structured `SKIPPED:` reason, but it does not verify that the
recorded command is one of the Active entries in `.harness/traces/search-set.md`
or that `python3 scripts/run-search-set.py` actually ran. This is honest
lightweight enforcement, but the repository should explicitly decide whether
stronger semantic checking is worth the extra complexity.

Potential improvement:

- Review whether repository maintenance should require
  `scripts/run-search-set.py` for harness-affecting changes by default, with
  explicit skipped reasons for narrower or impossible cases.
- If stronger checking is desired, teach the checker to parse Active verify
  commands from the repository search-set and compare them with recorded
  evidence, while still allowing documented subsets or skipped reasons.
- If the current syntactic checker remains the right boundary, document that as
  an intentional policy and avoid implying that the checker proves execution.
- Add tests only for the policy that is actually chosen.

Done when:

- The repository has an explicit decision on whether search-set evidence is
  shape-only or tied to Active search-set commands.
- `MAINTENANCE.md` and checker tests match that decision.
- The policy still allows practical skipped reasons for docs-only, unsafe,
  unavailable, or intentionally narrowed verification.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 -m unittest tests/test_search_set_evidence.py`, `python3
  scripts/check-search-set-evidence.py`, and `python3
  scripts/check-maintenance-review.py backlog/core.md`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Kept `scripts/check-search-set-evidence.py` intentionally shape-only: it
  checks structured `BEFORE:` / `AFTER:` or `SKIPPED:` evidence shape, not
  whether commands are current Active cases or actually executed.
- Documented that Active-case execution remains a separate verification policy:
  run `python3 scripts/run-search-set.py` for harness-affecting repository
  changes, or record a precise skipped/narrowed reason in the Completion Gate.
- Added focused documentation coverage in `tests/test_search_set_evidence.py`
  so the shape-only boundary and separate Active execution policy remain
  explicit.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `MAINTENANCE.md`; `tests/test_search_set_evidence.py`;
  `backlog/core.md`.
- Scope deviations: `backlog/core.md` Current Status was updated within the
  selected backlog file so completed items 57 and 58 are no longer listed as
  active `should` candidates. Unrelated dirty `backlog/README.md` remains
  outside item 58 and will not be staged or committed with it.
- Verification results: PASS `python3 -m unittest tests/test_search_set_evidence.py`;
  PASS `python3 scripts/check-search-set-evidence.py`; PASS `python3
  scripts/check-search-set-evidence.py --base-ref origin/main`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/run-search-set.py`; PASS `python3 scripts/verify-release.py
  --skip-clean-worktree`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: no; this documents the checker boundary without
  changing checker enforcement semantics.
- Multi-review result: not required. Single isolated reviewer scored 9/10 PASS
  for stable handoff hygiene.
- Reviewer scores and VETO handling: isolated reviewer 9/10 PASS; no VETO.
- For each score 9, why not 10: reviewer noted that enforcement remains split
  between documented process and `run-search-set.py` rather than adding
  end-to-end mechanical proof that every Completion Gate followed the policy.
  This is accepted as residual risk because item 58 explicitly chose the
  shape-only checker boundary instead of changing checker semantics.
- Backlog items added from score-9 residual risk: none; adding end-to-end
  semantic enforcement would reverse the explicit item 58 policy decision
  rather than follow from it.
- Residual risk/follow-up: accepted shape-only checker boundary.
- Accepted: yes.

### 59. P2 capture future qualifying repository raw traces

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- .harness/traces/failures/001-misplaced-start-gate.md
- tests/test_repository_search_set.py
- backlog/core.md

Start Gate:

- Selected item: `backlog/core.md` item 59, capture future qualifying
  repository raw traces.
- Status block added: yes, item 59 marked `진행중`.
- Harness-affecting: yes; this updates the repository self-application trace
  memory.
- Multi-review required: no; this records a concrete raw failure trace and does
  not change durable methodology, release, or verification contracts.
- Minimum verification commands: `python3 scripts/run-search-set.py`; `python3
  -m unittest tests/test_repository_search_set.py
  tests/test_backlog_heading_uniqueness.py`; `python3
  scripts/check-maintenance-review.py backlog/core.md`; `python3
  scripts/check-search-set-evidence.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: one repository failure trace under
  `.harness/traces/failures/`, focused repository trace-root schema coverage,
  and this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The trace/evaluator critic passed the repository's executable trace and
search-set contracts, but noted that this repository's own tracked
self-application raw trace evidence remains intentionally thin. Item 47 added a
substantive evolution trace and explicitly avoided manufacturing failures or
experiments just to populate `.harness/traces/failures/` or
`.harness/traces/experiments/`. The useful follow-up is not to create synthetic
evidence, but to make sure the next real qualifying repository harness failure,
review VETO with reusable diagnosis, or autoresearch-style experiment episode is
captured in the appropriate trace directory.

Potential improvement:

- During future harness-affecting maintenance, record a failure trace when a
  real repository harness failure, repeated VETO, evaluator-boundary defect, or
  regression has reusable diagnostic value.
- Record an experiment episode only when the repository actually runs an
  autoresearch-style fixed-evaluator episode or comparable structured
  experiment.
- Add the new trace to `.harness/traces/search-set.md` only when it yields a
  durable regression case with an executable verify command.
- Do not write placeholder, synthetic, or retrospective-fiction traces merely
  to make `failures/` or `experiments/` look populated.

Done when:

- The next qualifying real repository failure or experiment has a raw trace
  under `.harness/traces/failures/` or `.harness/traces/experiments/`, or the
  item records that no qualifying event occurred during the selected maintenance
  pass.
- Any new trace follows `core/reference.md` format and preserves raw command
  output, diffs, evaluator output, or review evidence as applicable.
- Search-set coverage is added only if the trace contains a reusable executable
  regression case.
- Multi-review checks the result if the new trace changes durable methodology,
  release, or verification contracts.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 -m unittest tests/test_repository_search_set.py
  tests/test_backlog_heading_uniqueness.py`, `python3
  scripts/check-maintenance-review.py backlog/core.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Added `.harness/traces/failures/001-misplaced-start-gate.md` for the real
  repository maintenance failure where broad backlog reservation patches placed
  Start Gate/reservation data under the wrong item.
- Preserved raw evidence from the failing Current Status test and the item 57
  process VETO class that caught a misplaced Start Gate under item 50.
- Marked the failure trace `resolved: true` because the current item 59
  reservation was corrected before implementation continued, and item 57's
  process VETO had already been fixed and rerun to 10/10 PASS.
- Did not add a new search-set Active case: the trace is useful process memory,
  but the durable executable guard is already covered by
  `tests/test_backlog_heading_uniqueness.py` plus process review rather than a
  new narrow regression command.
- Added focused repository trace-root coverage so committed failure traces must
  keep the required failure frontmatter and sections from `core/reference.md`.

Search-set verification update:

- AFTER: PASS `python3 scripts/run-search-set.py` after adding failure trace
  schema coverage.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `.harness/traces/failures/001-misplaced-start-gate.md`;
  `tests/test_repository_search_set.py`; `backlog/core.md`.
- Scope deviations: `tests/test_repository_search_set.py` was added to Scope
  before editing so committed repository failure traces have focused schema
  coverage. Unrelated dirty `backlog/README.md` remains outside item 59 and
  will not be staged or committed with it.
- Verification results: PASS `python3 scripts/run-search-set.py`; PASS
  `python3 -m unittest tests/test_repository_search_set.py
  tests/test_backlog_heading_uniqueness.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/core.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3
  scripts/verify-release.py --skip-clean-worktree`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: no; this records a concrete raw failure trace and does
  not change durable methodology, release, or verification contracts.
- Multi-review result: not required. Single isolated reviewer initially scored
  8/10 VETO because the review scope omitted the modified test file and the
  Completion Gate was not yet recorded; after review scope and Completion Gate
  fixes, the reviewer rerun also scored 8/10 VETO because final status and
  pending verification/acceptance wording were not yet updated; final rerun
  scored 9/10 PASS.
- Reviewer scores and VETO handling: isolated reviewer 8/10 VETO; the trace
  itself was accepted as real qualifying process evidence, but the handoff was
  blocked on scope/review coverage for `tests/test_repository_search_set.py`
  and missing Completion Gate. The affected reviewer rerun confirmed the
  substantive work and verification but blocked on final status/pending wording;
  this record now marks item 59 complete and records final verification.
- For each score 9, why not 10: the final reviewer score was 9 because the
  Completion Gate necessarily still said the final reviewer rerun and
  acceptance were pending at the time of review. This is procedural closure
  timing, not a repository improvement.
- Backlog items added from score-9 residual risk: none; procedural finalization
  is completed in this item.
- Residual risk/follow-up: none.
- Accepted: yes.

### 60. P3 operationalize active backlog archive lifecycle

Status: 대기

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`backlog/README.md` says active backlog files should focus on available,
in-progress, review-pending, and compact follow-up pointers, with completed
records moved to matching `backlog/archive/` files after they have complete
Completion Gates. Current active backlog files still contain many long completed
records with full Completion Gates. This does not weaken runtime harness
behavior, but it makes the active backlog harder to scan and shows that the
archive lifecycle is policy rather than an operational routine.

Potential improvement:

- Move completed records with complete Completion Gates from active backlog files
  to the matching archive files, leaving compact active-file pointers.
- Preserve anchors and enough pointer text so old references remain navigable.
- Add or strengthen a backlog hygiene check that flags long completed records in
  active backlog files after an accepted item is ready to archive.
- Keep genuinely active, in-progress, review-pending, or intentionally compact
  pointer records in active files.

Done when:

- Active backlog files mostly contain actionable items and compact completed
  pointers, not full completed histories.
- Archive files preserve the full Completion Gate, verification, search-set,
  multi-review, VETO, score-9, residual-risk, and acceptance records.
- `scripts/check-maintenance-review.py` or another focused check protects the
  chosen archive lifecycle from drifting again.

### 61. P3 align README quick verification guidance with release gate

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- README.md
- tests/test_pre_commit_hook.py
- backlog/core.md

Start Gate:

- Selected item: `backlog/core.md` item 61, align README quick verification
  guidance with release gate.
- Status block added: yes, item 61 marked `진행중`; an initial reservation was
  accidentally attached under other new core items and was corrected before
  acceptance.
- Harness-affecting: yes; this changes repository verification guidance that
  maintainers use for stable handoff decisions.
- Multi-review required: yes; this changes release/stable-handoff verification
  guidance.
- Minimum verification commands: `python3 -m unittest
  tests/test_pre_commit_hook.py`; `python3 scripts/check-maintenance-review.py
  backlog/core.md`; `python3 scripts/check-search-set-evidence.py`; `python3
  scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: root README quick verification guidance, focused README
  verification tests, and this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The README's before-commit shortcut lists important adapter and backlog checks,
but it omits newer stable-handoff evidence such as Codex activation smoke,
search-set evidence checking, the repository search-set runner, and
`scripts/verify-release.py`. `MAINTENANCE.md` and the executable release gate are
stronger, but a maintainer following only README can skip recent executable
trace-memory verification.

Potential improvement:

- Replace the long README inline command list with a clear split between quick
  pre-commit-adjacent checks and the canonical stable-handoff command.
- Name `python3 scripts/verify-release.py --skip-clean-worktree` or the
  appropriate release command as the preferred full local verification path.
- Keep README concise by pointing detailed tiering and exceptions to
  `MAINTENANCE.md`.
- Add or update focused README/maintenance tests so README quick guidance cannot
  drift behind the executable release gate again.

Done when:

- README readers can tell when the short command list is enough and when to run
  the full release/stable-handoff gate.
- README mentions the executable release verifier and does not silently omit
  trace-memory verification from its stable-handoff guidance.
- Focused docs tests or release-gate list checks protect the relationship between
  README, `MAINTENANCE.md`, and `scripts/verify-release.py`.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 -m unittest tests/test_pre_commit_hook.py`, `python3
  scripts/check-maintenance-review.py backlog/core.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Replaced the README's long inline before-commit command list with a split
  between quick pre-commit-adjacent checks and stable handoff verification.
- The quick path now points to `sh .githooks/pre-commit`.
- The stable handoff path now points first to `python3
  scripts/verify-release.py` and reserves `python3 scripts/verify-release.py
  --skip-clean-worktree` for in-progress maintenance diffs before the final
  clean handoff.
- README states that the release gate runs Standard verification plus the
  repository Active search-set and clean-worktree gate.
- Added focused README coverage in `tests/test_pre_commit_hook.py` so the quick
  hook and release-gate distinction cannot silently drift.

Multi-review:

- README verification guidance critic: score 9/10, PASS. Blocking findings:
  none. Why not 10: README initially listed `--skip-clean-worktree` first under
  stable handoff wording, while `MAINTENANCE.md` treats the no-skip command as
  preferred for stable handoff.
- Focused README test critic: score 8/10, VETO. Blocking finding: the new test
  was too coupled to exact prose and hard-wrapped newlines instead of the
  durable guidance contract.
- Maintenance-process critic: score 4/10, VETO. Blocking findings: the initial
  reservation was attached under the wrong item, item 61 itself still said
  `대기`, Completion Gate was missing, and required multi-review was not
  recorded.
- Score handling: scores below 9 are VETO. The README guidance issue was fixed
  by listing `python3 scripts/verify-release.py` first for clean stable handoff
  and reserving `--skip-clean-worktree` for in-progress diffs. The test VETO was
  fixed by normalizing whitespace and checking contract-level markers. The
  process VETO was handled by correcting the misplaced reservation, marking
  item 61 `완료`, recording this Completion Gate, and rerunning the affected
  process critic. For score 9 why not 10, the remaining lexical-test limitation
  is accepted as residual risk because README guidance still needs some
  text-level guard and the executable release behavior is covered elsewhere.
  For process critic score 9 why not 10, the only remaining issue was final
  bookkeeping to record the process rerun and acceptance; this was addressed in
  this item and does not create a backlog follow-up.
- Rerun status: README verification guidance critic re-review score 10/10,
  PASS. Blocking findings: none. Focused README test critic re-review score
  9/10, PASS. Blocking findings: none. Maintenance-process critic re-review
  score 9/10, PASS. Blocking findings: none.
- Follow-up/residual risk: no new backlog item added. The score-9 lexical guard
  limitation is accepted as residual risk, not a separate actionable repository
  improvement.
- Final acceptance: accepted yes after affected process critic re-review scored
  at least 9 and final bookkeeping was recorded.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - README.md
  - tests/test_pre_commit_hook.py
  - backlog/core.md
- Scope deviations: `backlog/core.md` already contained user-added candidate
  context for items 56-61 when item 61 was selected; this commit preserves that
  core backlog context together with the item 61 record. Unrelated user-added
  backlog candidates in `backlog/README.md` and `backlog/claude-adapter.md`
  remain outside item 61 scope and will not be staged for this commit.
- Verification results:
  - PASS: `python3 -m unittest tests/test_pre_commit_hook.py`
  - PASS: `python3 -m unittest tests/test_backlog_heading_uniqueness.py tests/test_pre_commit_hook.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/core.md`
  - PASS: `python3 scripts/check-search-set-evidence.py`
  - PASS: `python3 scripts/run-search-set.py`
  - PASS: `python3 scripts/verify-release.py --skip-clean-worktree`
  - PASS: `git diff --check`
- Search-set verification: BEFORE PASS `python3 scripts/run-search-set.py`;
  AFTER PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes release/stable-handoff verification
  guidance.
- Multi-review result: PASS for README guidance critic after score-9 fix; PASS
  for focused README test critic after VETO fix; PASS for process critic after
  final record update.
- Reviewer scores and VETO handling:
  - README verification guidance critic: 9/10 PASS initially; README command
    ordering fixed; rerun rating 10/10 PASS.
  - Focused README test critic: 8/10 VETO initially; brittle prose/newline
    assertions fixed; rerun rating 9/10 PASS.
  - Maintenance-process critic: 4/10 VETO initially; misplaced reservation
    corrected and Completion Gate recorded; affected rerun rating 9/10 PASS.
- For each 9/10 reviewer rating, why not 10:
  - README verification guidance critic initial review: not 10 because
    `--skip-clean-worktree` appeared first under stable handoff wording; fixed
    in this item.
  - Focused README test critic rerun: not 10 because the README guard remains a
    lexical documentation test and cannot prove how readers interpret the
    guidance; accepted as residual risk because command behavior is protected by
    `tests/test_verify_release.py` and release-gate execution.
  - Maintenance-process critic rerun: not 10 because final bookkeeping still
    needed to record the process rerun and acceptance; fixed in this item.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: README wording is still partly protected by lexical
  assertions, but normalized contract-level checks plus executable
  `verify-release.py` tests cover the durable behavior.
- Accepted: yes.

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
