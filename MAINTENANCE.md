# Maintenance Plan

This repository operationalizes Meta-Harness paper principles into a practical
harness toolkit, runtime adapters, and verification gates. It is not a paper
reproduction package or a claim that this local repo has demonstrated the
paper's benchmark gains. The primary maintenance goal is to keep the shared
methodology, runtime adapters, generated bundles, and compatibility surfaces
aligned while the harness evolves.

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
- Meta-Harness paper for the harness-sensitivity lesson, including the
  introduction's cited prior evidence that changing only the harness can
  produce a 6x performance gap on the same benchmark.
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
8. Use multi-review for adapter behavior, release gates, hook semantics, core
   methodology boundaries, or durable contracts named in `Multi-Review Use`.
   Routine backlog/status/doc cleanup can use focused checks without mandatory
   multi-review when it does not change those contracts.
9. Apply this repository's local release discipline for review scores: treat
   reviewer or critic scores below 9 as VETO. Fix the blocking findings and
   rerun the affected critics until every required critic scores at least 9, or
   stop and record that the item is not accepted.
10. Under the same local governance rule, identify why every score of 9 was not
   10. Record the residual risk, and add a backlog follow-up when it is
   actionable.
11. Record actionable residual risk as follow-up work.

Repeated nonindependent multi-review fallback is allowed only as a disclosed
degraded review mode. It remains advisory in `scripts/check-maintenance-review.py`
so old accepted records and low-risk cleanup do not become retroactive blockers,
but it requires maintainer disposition when it becomes frequent: at least 5
fallback records across checked review sections, or fallback records in at
least 3 review sections. When that threshold is met, the active maintenance
session must record one of these dispositions before stable handoff:

- `Fallback-threshold disposition: accepted residual risk because ...`, with
  the reason independent critics were impractical or unnecessary for the
  affected work.
- `Fallback-threshold disposition: independent re-review because ...`, when an
  independent multi-review re-run was completed for the affected
  durable-contract item.
- `Fallback-threshold disposition: follow-up backlog item because ...`, when
  the repeated fallback indicates a systemic review-process problem.

Use the exact `Fallback-threshold disposition:` label in the active item
Completion Gate, release note, or review summary. In default git-index mode,
the checker treats a matching record with explanatory detail in the current
staged backlog/review record as a dispositioned threshold signal and keeps an
undispositioned threshold visible as an action prompt. Historical archive
dispositions do not mask later stable handoffs unless the archive record itself
is part of the current staged handoff.

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
- `리뷰대기`: implementation is ready but still waiting for external review,
  merge coordination, or maintainer acceptance.
- `완료`: accepted and completed in the current maintenance flow or merged;
  keep decision and follow-up notes.
- `보류`: intentionally paused, blocked, or superseded; record the reason.

If the work must expand beyond the recorded scope, update the backlog item
before touching the new area. If a session abandons an item, it must change
`진행중` to `보류` or back to `대기` and record what happened.

### Reviewed Commit Loop

When a maintenance session is expected to commit a backlog item, use this
repeatable loop so future sessions can reproduce the handoff discipline:

1. Start from local `main` and inspect `git status --short --branch`.
2. Pick exactly one concrete `Status: 대기` backlog item.
3. Add the reservation block and report the Start Gate before implementation
   edits.
4. Run the relevant baseline verification, including Active search-set commands
   for harness-affecting changes.
5. Implement only the selected item. If scope expands, update the item's Scope
   before editing the new path.
6. Run focused verification, then the relevant standard verification for the
   changed contract.
7. If multi-review is required, run the multi-review skill or an explicitly
   documented equivalent with multiple reviewers/critics before acceptance. A
   single isolated reviewer does not satisfy required multi-review.
8. If multi-review is not required but the item will be committed as a stable
   handoff, ask a single isolated reviewer to review the item-specific diff
   before acceptance. The reviewer must not edit files.
9. Treat every reviewer or critic score below 9 as VETO. Fix the blocking
   findings, record the VETO and handling in the backlog item, and rerun the
   affected reviewer or critic until the score is at least 9.
10. For every score of 9, record why it was not 10. If the reason is an
   actionable repository improvement, add a follow-up backlog item before
   acceptance; otherwise record why it is accepted as residual risk.
11. Complete the Completion Gate, mark an accepted completed item `완료`, rerun
    the maintenance review and search-set evidence checkers, and record the
    results. Use `리뷰대기` only when the implementation is ready but still
    awaiting external review, merge coordination, or maintainer acceptance.
12. Stage only the selected item's intended files or hunks. If the worktree has
    unrelated dirty backlog additions or user edits, leave them unstaged and
    mention them in the Completion Gate or final handoff.
13. Inspect the staged patch with `git diff --cached`, verify the staged file
    list with `git diff --cached --name-status`, run `git diff --cached
    --check`, then commit.
14. After commit, run `python3 scripts/check-clean-worktree.py` when a clean
    stable handoff is expected. If unrelated work intentionally remains dirty,
    record that exception instead of claiming a clean handoff.

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
8. Treat every reviewer or critic score below 9 as VETO, even if the session
   had marked the work accepted. Fix the blocking findings and rerun the
   affected critics, or leave the branch `보류`.
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
| Harness-affecting behavior | Relevant tier above + `python3 scripts/run-search-set.py` before and after the change, or the relevant Active `search-set.md` verify commands with skipped reasons recorded |

Harness-affecting behavior means a change that alters agent-visible runtime
behavior or the rules used to judge it: project instruction templates, skills,
commands, hook behavior, checker semantics, trace/search-set schemas,
evaluator-boundary policy, install/activation behavior, or release gates.
Docs, README text, backlog wording, generated metadata, and smoke-test-only
changes do not require search-set verification unless they change one of those
contracts.

For this repository's self-application trace root, prefer
`python3 scripts/run-search-set.py` to execute the Active cases in
`.harness/traces/search-set.md`. Use individual Active verify commands only
when narrowing to a relevant subset, and record the command or skipped reason in
the backlog Completion Gate.

Standard verification:

```bash
python3 scripts/check-compat-mirrors.py
python3 scripts/check-claude-adapter-paths.py
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 adapters/codex/scripts/smoke-local-plugin-activation.py
python3 scripts/check-codex-marketplace-metadata.py
python3 scripts/check-maintenance-review.py
python3 scripts/check-search-set-evidence.py
python3 scripts/check-backlog-archive-lifecycle.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
```

The preferred stable-handoff command is the executable release gate:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

It runs the Standard verification set, the repository Active search-set, and the
clean-worktree release gate. The `--base-ref` argument makes the search-set
evidence check compare `REF...HEAD`, so committed harness-affecting release
candidates are checked even when the worktree is clean. Use `python3
scripts/verify-release.py --list --base-ref origin/main` to inspect the release
candidate command list without running it. During an in-progress maintenance
diff, omit `--base-ref` to use worktree-status search-set evidence mode, and use
`--skip-clean-worktree` to validate the release command list before the final
clean-worktree handoff.

The repository CI workflow at `.github/workflows/release-gate.yml` runs the
deterministic release-gate subset with `--ci --skip-clean-worktree --base-ref
<base>`. CI fetches full history so pull requests compare against their base
branch and protected-branch pushes compare against the previous pushed commit.
The clean-worktree gate remains local-only because GitHub Actions checks out an
ephemeral workspace, not the maintainer's handoff worktree. The Codex local
plugin activation smoke also remains local-only because CI does not provision a
maintainer-owned Codex CLI/plugin environment; CI still checks generated plugin
artifact integrity. Product/runtime evidence such as Codex Desktop model-visible
plugin surfacing or plugin hook tool-event delivery remains outside CI until a
product-supported noninteractive smoke exists; CI must not treat local plugin
artifact or CLI activation smokes as that proof.

Do not use plain root-level `python3 -m unittest discover` as a repository
verification signal. It is guarded by a root sentinel that fails on purpose so a
generic unittest runner cannot report a zero-test false green. Use the three
explicit unittest discovery roots in the Standard verification set instead.

The tracked pre-commit hook runs the drift, artifact smoke, maintenance review,
staged search-set evidence, and staged backlog archive lifecycle checks, but
not the full unit test suites or the heavier Codex local plugin activation
smoke:

```bash
git config core.hooksPath .githooks
sh .githooks/pre-commit
```

For release or stable handoff verification, also run the clean-worktree gate:

```bash
python3 scripts/check-clean-worktree.py
```

This command is intentionally not part of pre-commit. Pre-commit validates the
Git index so unrelated unstaged work does not block commit-time checks; staged
archive lifecycle validation catches completed active backlog records before
they enter a commit. The release/handoff gate validates that no tracked, staged,
or untracked worktree state is being hidden outside the checked index. A dirty
result is a release blocker unless the handoff notes explicitly record the
exception.

For harness-affecting repository changes, run the search-set evidence
compliance checker before stable handoff. Use the default mode while reviewing
an in-progress dirty worktree, the staged mode immediately before commit, and
the base-ref mode for a clean release candidate or branch handoff:

```bash
python3 scripts/check-search-set-evidence.py
python3 scripts/check-search-set-evidence.py --staged
python3 scripts/check-search-set-evidence.py --base-ref origin/main
```

This checker is intentionally lightweight. It detects common harness-affecting
changed paths and requires a touched backlog, review, or trace record to include
search-set before/after evidence or an explicit skipped reason. It does not try
to prove full methodology compliance and intentionally remains shape-only: it
does not parse `.harness/traces/search-set.md`, prove that a recorded command is
currently Active, or prove that `python3 scripts/run-search-set.py` actually
ran. Active-case execution is enforced by the separate verification policy: run
`python3 scripts/run-search-set.py` for harness-affecting repository changes, or
record a precise skipped/narrowed reason in the Completion Gate. The staged mode
reads both changed paths and backlog/trace records from the Git index so
unstaged user work does not hide or satisfy commit-time evidence. The base-ref
mode compares `REF...HEAD` so a clean release candidate still checks the
committed harness-affecting diff.

Use structured evidence lines so the checker can reject vague prose and
accidental keywords:

```md
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`
  - AFTER: PASS `python3 scripts/run-search-set.py`
```

If search-set execution is not applicable or not practical, record a structured
skipped reason instead:

```md
- Search-set verification:
  - SKIPPED: docs-only cleanup; no harness-affecting behavior changed.
```

Search-set verification is project-contextual rather than repo-global: use the
active trace root for the project whose harness behavior is changing. If this
repository is the target harnessed project and no trace root exists, record that
there is no project search-set yet instead of marking the check PASS.
For this repository's own harness-maintenance loop, use the tracked
`.harness/traces/` tree as the active repository self-application trace root
and run the relevant Active verify commands from
`.harness/traces/search-set.md` before and after harness-affecting repository
changes when practical. Historical `.claude/traces/` files are legacy
Claude-local context; do not write new repository maintenance traces there
unless explicitly performing a migration or recovery of that history.

## Release Checklist

Use this checklist before tagging, publishing, or treating `main` as a stable
handoff point:

- Clean-worktree release gate passes with `python3 scripts/check-clean-worktree.py`,
  or the release/handoff record explicitly names the dirty paths and why they
  are accepted as an exception.
- Compatibility mirrors pass from the Git index.
- Claude adapter path contract check passes.
- Codex plugin sync check passes.
- Codex local plugin artifact smoke test passes.
- Codex local plugin activation smoke test passes. This proves isolated CLI
  marketplace registration and enabled-plugin config shape, not running Codex
  Desktop skill surfacing or plugin tool-event delivery.
- Codex hook schema drift check passes; hook-sensitive changes update or
  intentionally re-verify `adapters/codex/hook-schema.md`.
- Codex autoresearch hook smoke passes against the real checker and protected
  path template.
- Codex marketplace metadata readiness check passes. This check is deferred
  while no publication manifest exists, and fails if marketplace metadata
  appears before publication readiness, official schema/taxonomy evidence, and
  generated metadata source are recorded.
- Maintenance review summaries pass the review-summary checker so score,
  VETO, rerun, residual-risk, and final-acceptance handling stay explicit.
- Search-set evidence compliance check passes for harness-affecting repository
  changes, or the release/handoff record explicitly explains why it is skipped.
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

The score thresholds in this section are repository governance and release
discipline for this maintainable harness artifact. They are intentionally
stricter than the Meta-Harness paper's methodological claims: the paper
motivates evaluator boundaries, trace reuse, and harness design, while this
repository chooses numeric review gates to keep local maintenance decisions
auditable.

Use multi-review when a change affects:

- Adapter direction or install/distribution UX.
- Hook enforcement or protected-file semantics.
- Release gates and pre-commit behavior.
- Core methodology boundaries.
- Durable contracts that future harness-engineer or autoresearch work will rely
  on, such as trace schemas, evaluator-boundary rules, install behavior, or
  runtime enforcement semantics.

Required multi-review means multiple distinct reviewers or critics. Prefer the
multi-review skill when available. If the skill cannot be used, record the
fallback explicitly, including why it is equivalent enough for the item and
which independent critic scopes were covered. When a committed stable-handoff
item does not require multi-review, the Reviewed Commit Loop uses a single
isolated reviewer as the required handoff hygiene check; that check must still
not be recorded as satisfying required multi-review.

The maintenance review checker emits a review-quality signal, not a validation
failure, when staged high-impact paths have no recorded `Multi-review:` section
or explicit `Multi-review not required:` reason in the staged backlog/review
records. High-impact paths are adapter surfaces, core methodology, scripts,
pre-commit hooks, README/maintenance policy, and similar release or evaluator
contracts. Use the explicit not-required reason only for routine cleanup whose
changed paths look broad but do not alter one of the durable contracts named
above.

A one-off nonindependent fallback can be accepted only when the item record
states why independent critics were unavailable or unnecessary for the
remaining risk, such as temporary sub-agent unavailability, emergency recovery,
or explicitly low-risk documentation cleanup. Repeated nonindependent fallback
on durable-contract decisions is a review-quality signal, not an automatic
retroactive failure. When the review checker reports repeated fallback records,
the active session must decide whether the pattern is still justified or should
create follow-up work before accepting the current item. Record that decision
with the exact `Fallback-threshold disposition:` label so the checker can
distinguish "threshold met and undispositioned" from "threshold met and
disposition recorded" during stable handoff.

As local release policy, reviewer or critic scores below 9 are VETO. Scores of
9 mean the change is acceptable with remaining risk tracked. Scores of 10 should
be rare and reserved for cases where there is no meaningful known follow-up.

When a critic returns VETO, local release discipline requires the next
iteration to fix or explicitly reject the blocking findings, rerun the affected
critic, and record the rerun score before the work can be accepted. Do not
treat an earlier PASS from another critic as covering the changed area after a
VETO fix unless that critic's scope is still unchanged.

When a critic returns score 9, local governance requires recording why the
score was not 10. If the reason is an actionable repository improvement, add it
to the relevant backlog file before marking the current item accepted. If the
reason is residual risk rather than actionable work, record why it is accepted
without a new backlog item.

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
