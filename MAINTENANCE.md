# Maintenance Plan

This repository is a maintainable Meta-Harness artifact, not only a document
collection. The primary maintenance goal is to keep the shared methodology,
runtime adapters, generated bundles, and compatibility surfaces aligned while
the harness evolves.

## Maintenance Model

Maintain the repo as three layers:

| Layer | Owns | Maintenance Rule |
|-------|------|------------------|
| Core | Runtime-neutral methodology, trace semantics, verification policy | Edit once in `core/`; do not fork into adapters unless runtime behavior differs |
| Adapters | Runtime-specific instructions, paths, hooks, install UX, examples | Keep runtime assumptions explicit and backed by smoke tests where possible |
| Generated and compatibility surfaces | Codex plugin bundle, temporary Claude mirrors | Treat as derived artifacts; enforce drift checks in pre-commit and release checks |

## Methodology Anchors

Do not duplicate the full paper or core methodology here. Use this section as a
maintenance compass when deciding whether a change belongs in the harness.

Primary sources:

- `core/methodology.md` for runtime-neutral operating principles.
- `core/reference.md` for trace formats and analysis workflow.
- Meta-Harness paper for the claim that harness design can dominate model
  choice in long-running agent performance.
- Effective harness writing guidance for practical project-instruction hygiene.

Maintenance decisions should preserve these anchors:

- Raw evidence beats summaries. Prefer trace files, executable logs, and
  grep-able frontmatter over compressed retrospectives.
- The evaluator boundary must stay clean. Agents may improve harness and search
  code, but must not silently alter the measurement signal.
- Additive harness changes are safer than rewriting working control flow.
  Preserve known-good behavior unless a regression trace justifies replacing it.
- Code-space search is the optimization surface. A small script, hook, template,
  or check is often better than a larger instruction block.
- Verification should be executable where possible. When it cannot be, record
  the skipped condition and make the residual risk visible.
- Core owns what and why; adapters own runtime-specific how. Duplication across
  adapters is a drift risk unless runtime behavior truly differs.

## Backlog Policy

Backlog items are grouped by ownership in `backlog/` and by theme in
`backlog/README.md`.

Use this workflow for backlog work:

1. Pick a theme and one concrete item.
2. Mark the item before editing with the session gate fields below.
3. Implement the smallest useful contract, document, smoke test, or adapter
   change.
4. Keep one functional harness change per iteration. Batch only independent
   non-functional health fixes, and list each item separately in the review or
   evolution trace.
5. For harness-affecting changes, run the Active verify commands from the
   relevant trace root's `search-set.md` before and after the change when
   practical. Record PASS/FAIL or the skipped reason.
6. Record harness behavior changes in the relevant evolution trace. If no trace
   is written because the change is repository-only maintenance, state that in
   the review summary, PR description, or backlog entry.
7. Run the relevant checks before review.
8. Use multi-review for adapter behavior, release gates, hook semantics, or
   anything that can steer future work in the wrong direction.
9. Treat reviewer scores below 9 as VETO. Fix the blocking findings and rerun
   the affected critics until every required critic scores at least 9, or stop
   and record that the item is not accepted.
10. For every score of 9, identify why the score was not 10. Record the
   residual risk, and add a backlog follow-up when it is actionable.
11. Record actionable residual risk as follow-up work.

When a backlog item becomes implemented foundation, keep it in place but change
the wording from "Potential improvement" to "Decision implemented" plus
"Remaining follow-up work". This preserves history without making completed
work look unstarted.

## Single-Session Maintenance

Routine maintenance should run through one active session at a time. The active
session may edit every file required by the selected item, but should still keep
one functional harness change per iteration. This keeps ownership clear, avoids
under-scoped edits caused by file-count anxiety, and gives review enough shared
context to apply this maintenance policy consistently.

Before implementation edits, the active session must record or report a Start
Gate:

- Selected item
- Status block added or updated
- Harness-affecting: yes/no
- Multi-review required: yes/no, with reason
- Minimum verification commands
- Expected scope

Before marking an item accepted, the active session must record a Completion
Gate:

- Backlog status
- Changed files
- Scope deviations, or `none`
- Verification results
- Search-set verification status, or skipped reason
- Multi-review result, or reason not required
- Reviewer scores and VETO handling
- For each score 9: why not 10, and whether that reason created a backlog item
- Residual risk or follow-up
- Accepted: yes/no

An item is accepted only when relevant verification is recorded, required
multi-review is recorded, every required critic score is at least 9, every
score of 9 has a recorded "why not 10" reason, and residual risk is either
accepted or split into follow-up work.

Record the active item reservation above the implementation notes:

```md
Status: 진행중
Owner: <session name>
Branch: <current branch>
Started: YYYY-MM-DD
Scope:
- path/or/directory
```

Use these status values:

- `대기`: available and not currently owned.
- `진행중`: editing, verification, or review is active.
- `리뷰대기`: implementation is ready for review or merge coordination.
- `완료`: merged or otherwise accepted; keep decision and follow-up notes.
- `보류`: intentionally paused, blocked, or superseded; record the reason.

If the work must expand beyond the recorded scope, update the backlog item
before touching the new area. If a session abandons an item, it must change
`진행중` to `보류` or back to `대기` and record what happened.

## Exceptional Parallel Worktree Recovery

Parallel worktree maintenance is discouraged for routine backlog work. It should
be used only when explicitly requested for an exceptional split, and the owner
must ensure the sessions share enough context to satisfy the same review,
verification, VETO, and score-9 follow-up rules as a single session.

If a worktree session skips reservation, scope control, verification,
multi-review, or review-score handling, do not merge the branch as normal
backlog work. Follow the recovery procedure below first, then tighten the item
record before continuing.

## Noncompliant Worktree Recovery

Use this procedure when a parallel session produced useful changes but did not
follow this maintenance process.

1. Treat the branch as `보류`, not `리뷰대기`, until the missing record is
   reconstructed.
2. Identify the intended backlog item, actual changed files, and any scope
   overlap with other `예약됨`, `진행중`, or `리뷰대기` items.
3. Add a recovery note to the relevant backlog item. Do not claim the original
   session complied; state that the entry is reconstructed after the fact.
4. Record whether the change is harness-affecting and whether multi-review is
   required under `Multi-Review Use`.
5. Run or rerun the minimum verification for the actual changed files. Record
   PASS, FAIL, or SKIPPED with exact skipped reasons.
6. If the change is harness-affecting, run relevant Active `search-set.md`
   verify commands before and after when practical. If no project search-set
   exists, record that exact skipped reason.
7. Run the required multi-review if the change affects adapter behavior,
   release gates, hook semantics, core methodology boundaries, or another
   durable contract.
8. Treat every reviewer score below 9 as VETO, even if the session had marked
   the work accepted. Fix the blocking findings and rerun the affected critics,
   or leave the branch `보류`.
9. Move the item to `리뷰대기` only after the reconstructed record shows scope,
   verification, search-set status, review status, residual risk, and merge
   eligibility.

Recovery notes should be explicit and short. Use this shape when practical:

```md
Recovery note:
- Original session compliance: incomplete
- Actual changed files:
- Scope deviations:
- Verification:
- Search-set verification:
- Multi-review required:
- Multi-review result:
- Merge eligible: yes/no
```

Recovered work remains blocked if the intended backlog item cannot be
identified, if active scopes conflict, if required verification cannot be
reconstructed, or if any required critic remains below score 9.

## Test Policy

Tests should cover repository contracts, not prose taste.

Add or keep tests for:

- Derived artifact drift, such as compatibility mirrors and generated plugin
  bundles.
- Runtime path contracts, such as `.claude/traces/`, `.claude/hooks/`, and
  `.harness/traces/`.
- Hook and checker output shapes consumed by agent runtimes.
- Evaluator or protected-file boundaries that must not be silently bypassed.
- Index-vs-working-tree behavior for pre-commit checks.
- Install, activation, or target-project smoke tests when the runtime can be
  exercised mechanically.

Do not add tests for:

- Preferred wording, tone, or explanatory style.
- Methodology judgment that needs human review.
- Agent behavior that cannot be observed without a real runtime surface.

Use unit tests for pure validators and temp-repo integration tests for Git
index semantics. Prefer smoke tests when the artifact is a generated bundle or
runtime-facing install surface.

## Verification Tiers

Run the narrowest tier that covers the files changed while iterating. Before
multi-review, release-like commits, or changes that alter repository contracts,
run the full standard verification set.

| Change area | Minimum verification |
|-------------|----------------------|
| Docs/backlog only | Review changed docs plus any linked command examples |
| Core methodology or reference | Docs/backlog tier + multi-review when behavior changes + relevant search-set verify commands if a trace root applies |
| Claude adapter | `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 -m unittest discover -s adapters/claude/tests` |
| Codex adapter/plugin | `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests` |
| Compatibility/generated surfaces | Drift check for the generated or mirrored surface plus its owning adapter tests |
| Harness-affecting behavior | Relevant tier above + Active `search-set.md` verify commands before and after the change, with skipped reasons recorded |

Harness-affecting behavior means a change that alters agent-visible runtime
behavior or the rules used to judge it: project instruction templates, skills,
commands, hook behavior, checker semantics, trace/search-set schemas,
evaluator-boundary policy, install/activation behavior, or release gates.
Docs, README text, backlog wording, generated metadata, and smoke-test-only
changes do not require search-set verification unless they change one of those
contracts.

Standard verification:

```bash
python3 scripts/check-compat-mirrors.py
python3 scripts/check-claude-adapter-paths.py
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 scripts/check-maintenance-review.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
```

The tracked pre-commit hook runs the drift and smoke checks, but not the full
unit test suites:

```bash
git config core.hooksPath .githooks
sh .githooks/pre-commit
```

Search-set verification is project-contextual rather than repo-global: use the
active trace root for the project whose harness behavior is changing. If this
repository is the target harnessed project and no trace root exists, record that
there is no project search-set yet instead of marking the check PASS.

## Release Checklist

Use this checklist before tagging, publishing, or treating `main` as a stable
handoff point:

- Compatibility mirrors pass from the Git index.
- Claude adapter path contract check passes.
- Codex plugin sync check passes.
- Codex local plugin artifact smoke test passes.
- Codex hook schema drift check passes; hook-sensitive changes update or
  intentionally re-verify `adapters/codex/hook-schema.md`.
- Codex autoresearch hook smoke passes against the real checker and protected
  path template.
- Maintenance review summaries pass the review-summary checker so score,
  VETO, rerun, residual-risk, and final-acceptance handling stay explicit.
- Unit and integration tests pass for root, Claude adapter, and Codex adapter
  test suites.
- Harness-affecting changes ran relevant Active search-set verify commands
  before and after the change, or recorded the skipped reason.
- README repository name, install commands, and adapter paths match the current
  repo layout.
- Backlog entries touched by the change are updated from potential work to
  implemented foundation when appropriate.
- Multi-review is recorded or summarized for high-impact adapter or release-gate
  changes.

## Compatibility Mirror Lifecycle

Top-level Claude compatibility mirrors (`docs/`, `commands/`, and `skills/`)
are temporary transition surfaces, not permanent source paths. Keep them until
at least one stable handoff point after the canonical `adapters/claude/` install
commands and old mirrored install commands both have smoke coverage.

Before removing mirrors:

- Announce the removal in README guidance and release notes for one release or
  transition window.
- Keep `scripts/check-compat-mirrors.py` enforcing drift until the removal
  commit.
- Document the migration path from `docs/`, `commands/`, and `skills/` to
  `core/` and `adapters/claude/`.
- Decide whether old install commands should fail fast with guidance or remain
  as thin redirect docs for one additional window.
- Remove mirrors and mirror checks in the same release-oriented change so stale
  compatibility policy does not remain behind.

## Multi-Review Use

Use multi-review when a change affects:

- Adapter direction or install/distribution UX.
- Hook enforcement or protected-file semantics.
- Release gates and pre-commit behavior.
- Core methodology boundaries.
- Durable contracts that future harness-engineer or autoresearch work will rely
  on, such as trace schemas, evaluator-boundary rules, install behavior, or
  runtime enforcement semantics.

Reviewer scores below 9 are VETO. Scores of 9 mean the change is acceptable
with remaining risk tracked. Scores of 10 should be rare and reserved for cases
where there is no meaningful known follow-up.

When a critic returns VETO, the next iteration must fix or explicitly reject the
blocking findings, rerun the affected critic, and record the rerun score before
the work can be accepted. Do not treat an earlier PASS from another critic as
covering the changed area after a VETO fix unless that critic's scope is still
unchanged.

When a critic returns score 9, record why the score was not 10. If the reason is
an actionable repository improvement, add it to the relevant backlog file before
marking the current item accepted. If the reason is residual risk rather than
actionable work, record why it is accepted without a new backlog item.

Review summaries for multi-review items must record:

- critic name or scope
- score
- for score 9, why not 10 and whether a backlog item was added
- verdict
- blocking findings or "none"
- follow-up or residual risk
- score handling, especially whether any score below 9 triggered iteration
- rerun status after fixes, including whether all critics were rerun
- final acceptance status

Do not mark an item accepted while any required critic score is below 9.

## Current Maintenance Plan

Near-term work lives in `backlog/`, not as permanent policy. Current pointers:

- `backlog/core.md` for shared methodology and repo-wide release-gate follow-up.
- `backlog/claude-adapter.md` for Claude fixture and runtime activation follow-up.
- `backlog/codex-adapter.md` for Codex plugin activation, examples, and install
  validation.

Update those backlog files when the next sequence changes. Keep this document
focused on maintenance rules that should survive the current implementation
queue.
