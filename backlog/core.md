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
- Active core backlog has one standard-verification follow-up, item 29.
- Remaining unstarted work is currently adapter-owned:
  `backlog/claude-adapter.md` items 10-12.

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
