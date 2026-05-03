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
- Active core backlog currently has no unstarted concrete implementation item.
- Recent adapter follow-ups in `backlog/claude-adapter.md` items 10-12,
  `backlog/codex-adapter.md` items 27-34, and core process item 31 are
  complete; use new backlog entries for newly discovered work rather than
  treating these completed items as available candidates.

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
