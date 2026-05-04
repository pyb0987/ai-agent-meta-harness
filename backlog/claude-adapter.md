# Claude Adapter Backlog

Claude Code-specific follow-ups live here. Shared methodology belongs in
`backlog/core.md`; Codex runtime work belongs in `backlog/codex-adapter.md`.

## Priority Candidates

### 1. Keep Claude trace and hook paths mechanically consistent

Status: 완료
Archived: `backlog/archive/claude-adapter.md#1-keep-claude-trace-and-hook-paths-mechanically-consistent`

### 2. Add old Claude compatibility install smoke test

Status: 완료
Archived: `backlog/archive/claude-adapter.md#2-add-old-claude-compatibility-install-smoke-test`

### 3. Add Claude init-harness project-fixture smoke test

Status: 완료
Archived: `backlog/archive/claude-adapter.md#3-add-claude-init-harness-project-fixture-smoke-test`

### 4. P1 preserve verifier exit status in init-harness examples

Status: 완료
Archived: `backlog/archive/claude-adapter.md#4-p1-preserve-verifier-exit-status-in-init-harness-examples`

### 5. P2 add Claude trace-root evidence selection for migrated projects

Status: 완료
Archived: `backlog/archive/claude-adapter.md#5-p2-add-claude-trace-root-evidence-selection-for-migrated-projects`

### 6. P2 harden Claude autoresearch protected-file hooks

Status: 완료
Archived: `backlog/archive/claude-adapter.md#6-p2-harden-claude-autoresearch-protected-file-hooks`

### 7. P1 preserve verifier exit status in Claude hook recipes

Status: 완료
Archived: `backlog/archive/claude-adapter.md#7-p1-preserve-verifier-exit-status-in-claude-hook-recipes`

### 8. P2 respect migrated active trace roots in Claude harness-engineer

Status: 완료
Archived: `backlog/archive/claude-adapter.md#8-p2-respect-migrated-active-trace-roots-in-claude-harness-engineer`

### 9. P2 add hard-layer protection guidance for Claude evaluator files

Status: 완료
Archived: `backlog/archive/claude-adapter.md#9-p2-add-hard-layer-protection-guidance-for-claude-evaluator-files`

### 10. P2 align init-harness completion checklist with active trace root

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

Claude `/init-harness` can select or temporarily reuse meaningful
`.harness/traces/` history, but the completion verification checklist still
requires `.claude/traces/*`, `.claude/traces/search-set.md`,
`.claude/traces/evolution/001-initial-harness.md`, and
`.claude/traces/failures/*.md`. In a migrated project where `.harness/traces/`
is intentionally active, this can recreate a second trace tree and split future
history.

Potential improvement:

- Reword `adapters/claude/commands/init-harness.md` completion checks to use
  the selected active trace root instead of hardcoding `.claude/traces/` for
  trace infrastructure.
- Preserve `.claude/traces/` as the normal Claude default, but allow
  evidence-selected `.harness/traces/` completion when reuse is explicitly
  recorded.
- Add focused lexical or fixture coverage proving the completion checklist does
  not force `.claude/traces/` after intentional `.harness/traces/` reuse.

Decision:

- Updated `/init-harness` Step 7 and Completion Verification to use the
  selected `{trace_root}` for search-set, evolution, failures, and experiments
  checks instead of hardcoding `.claude/traces/`.
- Preserved `.claude/traces/` as the normal Claude default while allowing
  explicitly reused meaningful `.harness/traces/` history to satisfy completion.
- Updated the compatibility mirror `commands/init-harness.md`.
- Extended fixture coverage so the normal `.claude/traces/` project and a
  migrated `.harness/traces/` project both satisfy the init-harness output
  contract.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/claude/commands/init-harness.md`
  - `commands/init-harness.md`
  - `tests/test_claude_init_harness_fixture.py`
  - `backlog/claude-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_init_harness_fixture.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes Claude adapter initialization
  behavior and trace-root semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Active trace-root contract critic: 10/10 PASS; completion checks now use
    `{trace_root}` and preserve `.claude/traces/` as the default.
  - Migrated history safety critic: 10/10 PASS; fixture coverage proves
    intentionally reused `.harness/traces/` can complete without forcing a
    second `.claude/traces/` history.
  - Compatibility mirror critic: 10/10 PASS; mirror sync and path checks pass.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update,
    verification, search-set SKIPPED reason, and Completion Gate are recorded,
    with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 11. P2 make Claude autoresearch honor the active trace root

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_trace_root.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

The Claude `autoresearch` skill still hardcodes `.claude/traces/` for reject
preservation, experiment episodes, escalation failures, and numbering. That
conflicts with the newer trace-root rule that migrated projects may temporarily
keep `.harness/traces/` active, so raw experiment and failure history can still
split across roots.

Potential improvement:

- Update `adapters/claude/skills/autoresearch/SKILL.md` so Setup and Run Mode
  select an active trace root before writing failures, experiments, or
  escalation records.
- Use `{trace_root}` or equivalent wording for reject preservation, experiment
  episode timing, failure escalation, and numbering.
- Keep `.claude/traces/` as the Claude default, but respect documented
  `.harness/traces/` reuse for migrated projects.
- Add focused coverage that rejects hardcoded trace writes where active-root
  selection is required.

Decision:

- Added a Claude autoresearch Setup Mode step to select the active trace root
  before writing experiment episodes, failure diagnoses, or escalation records.
- Kept `.claude/traces/` as the default Claude root while allowing meaningful
  `.harness/traces/` migrated history to be reused as `{trace_root}` when
  `.claude/traces/` is absent, empty, or template-only.
- Reworded reject preservation, episode paths, numbering, escalation failures,
  and continuity references to use `{trace_root}`.
- Updated the root `skills/autoresearch` compatibility mirror.
- Added focused lexical coverage proving post-selection trace writes use
  `{trace_root}` and that canonical/mirror skill copies match.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/claude/skills/autoresearch/SKILL.md`
  - `skills/autoresearch/SKILL.md`
  - `tests/test_claude_autoresearch_trace_root.py`
  - `backlog/claude-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_trace_root.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes Claude autoresearch trace-writing
  behavior and migration semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Active trace-root contract critic: 10/10 PASS; Setup Mode now selects
    `{trace_root}` before writing traces and uses it for later trace writes.
  - Migrated history safety critic: 10/10 PASS; meaningful `.harness/traces/`
    history can be reused without silently splitting experiment/failure traces.
  - Compatibility mirror critic: 10/10 PASS; root skill mirror matches the
    canonical Claude adapter skill and compatibility mirror checks pass.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update,
    verification, search-set SKIPPED reason, and Completion Gate are recorded,
    with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 12. P2 require Claude autoresearch hard-layer protection before setup completion

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_hard_layer_guidance.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

The Claude `autoresearch` skill documents pre-commit/CI diff protection as the
hard evaluator-protection layer, but the Setup Completion Checklist only
requires the two Claude hooks and settings registration. A maintainer can
therefore mark Setup Mode complete while fixed-evaluator protection remains
heuristic-only.

Potential improvement:

- Update the Setup Completion Checklist in
  `adapters/claude/skills/autoresearch/SKILL.md` to require the documented
  hard-layer protected-file diff check, or an explicit skipped reason when the
  project cannot install it yet.
- Require a smoke result showing protected evaluator edits fail and mutable
  genome edits pass before Setup Mode is considered complete.
- Keep the two Claude hooks as fast local protection, but make clear they do
  not replace the hard pre-commit/CI layer.
- Add focused documentation tests so future edits do not remove this setup
  completion requirement.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/claude/skills/autoresearch/SKILL.md
  - skills/autoresearch/SKILL.md
  - tests/test_claude_autoresearch_hard_layer_guidance.py
  - backlog/claude-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_hard_layer_guidance.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; Claude autoresearch setup/protection semantics changed.
- Multi-review result: PASS by sequential `FALLBACK_NONINDEPENDENT` review.
- Reviewer scores and VETO handling:
  - Setup completion contract critic: 10/10 PASS; checklist now requires hard-layer install or explicit skipped reason plus smoke evidence before setup completion.
  - Hard-layer protection honesty critic: 10/10 PASS; Claude hooks are explicitly framed as fast local protection, not a replacement for the pre-commit/CI layer.
  - Compatibility mirror/test critic: 10/10 PASS; canonical and mirror skills carry the same new completion requirements and focused tests cover both paths.
  - Maintenance compliance critic: 9/10 PASS; no VETO. Reservation, Start Gate, scoped edits, verification, search-set skipped reason, and Completion Gate are present.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used the required sequential `FALLBACK_NONINDEPENDENT` form in this single-session run instead of independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the residual is procedural review independence, not an actionable repository defect for this item.
- Residual risk/follow-up: future externally reviewed passes may provide stronger independent critique, but no known implementation risk remains.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 13. P1 preserve raw evidence before Claude autoresearch REJECT revert

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_reject_evidence.py
- backlog/claude-adapter.md

Source review: 2026-05-03 multi-review feedback.

`core/reference.md` requires preserving rejected candidate diffs and raw
evaluator output before revert/cleanup, but Claude autoresearch Run Mode still
summarizes the reject path as `REJECT -> git reset --hard HEAD~1 + log`. That
ordering can cause an executor to lose candidate source changes or raw
evaluator output before they are recorded in `experiments.jsonl` or
`{trace_root}` traces. The Codex autoresearch guidance states this ordering
more safely.

Potential improvement:

- Reword Claude autoresearch Run Mode so REJECT handling explicitly captures
  raw evaluator output and candidate diff before any reset/revert.
- Ensure the recorded evidence includes enough detail for future proposer
  search over rejected candidates, consistent with `core/reference.md`.
- Update the root `skills/autoresearch` mirror and add focused lexical coverage
  that rejects a revert-before-capture sequence.

Decision:

- Updated Claude autoresearch setup guidance so every REJECT captures the
  candidate diff and raw evaluator JSON into temporary evidence outside the
  rejected commit before any reset/revert.
- Replaced the unsafe Run Mode shorthand `REJECT -> git reset --hard HEAD~1 +
  log` with an ordered sequence: preserve JSON and diff outside the rejected
  commit, reset/revert, then append full evaluator result and rejection
  metadata to `experiments.jsonl` and write `{trace_root}` episode/failure
  evidence from the preserved evidence when triggers apply.
- Added an explicit safety note to stop with evidence already saved if the
  revert needs approval or is blocked by local policy, and not to rely on
  pre-revert appends to tracked files that a hard reset can erase.
- Updated the root `skills/autoresearch` compatibility mirror and added
  focused lexical tests that enforce capture-before-revert ordering and reject
  the previous revert-then-log shorthand.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/claude/skills/autoresearch/SKILL.md
  - skills/autoresearch/SKILL.md
  - tests/test_claude_autoresearch_reject_evidence.py
  - backlog/claude-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; this changes Claude autoresearch run-mode evidence preservation semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Evidence ordering critic: 10/10 PASS; REJECT handling now preserves raw evaluator JSON and candidate diff before any reset/revert.
  - Trace reuse critic: 10/10 PASS; rejection evidence is recorded in `experiments.jsonl` and `{trace_root}` episode/failure traces when triggers apply, preserving future proposer search material.
  - Mirror/test critic: 10/10 PASS; canonical and root mirror skills match, and focused tests reject the old reset-then-log shorthand.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, full verification, search-set SKIPPED reason, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 14. P2 align Claude init sub-agent trigger wording with core isolation policy

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

Start Gate:

- Selected item: `backlog/claude-adapter.md` item 14, align Claude init
  sub-agent trigger wording with core isolation policy.
- Status block added: yes, item 14 marked `진행중`.
- Harness-affecting: yes; Claude init guidance changes adapter
  methodology/runtime boundary behavior.
- Multi-review required: yes; this changes adapter behavior and core
  methodology boundary semantics.
- Minimum verification commands: `python3 scripts/check-compat-mirrors.py`;
  `python3 scripts/check-claude-adapter-paths.py`; `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`; `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; `python3
  scripts/check-search-set-evidence.py`; `python3 scripts/run-search-set.py`;
  `python3 scripts/verify-release.py --skip-clean-worktree`; `git diff
  --check`.
- Expected scope: Claude init-harness canonical command, root compatibility
  mirror, focused Claude init fixture tests, and this backlog record.

Source review: 2026-05-04 adapter/plugin alignment critic in the current-main
methodology multi-review.

The shared core now says only two methodology-level isolation triggers belong in
the core: qualitative multi-perspective judgment and evaluator independence.
Generic parallel exploration, context firewalls, model routing, and exact
sub-agent thresholds are runtime policy. Claude `/init-harness` mostly respects
that boundary, but still refers to "three trigger categories" and says "Prefer
over-invoking to under-invoking" for sub-agent triggers. That can make the Claude
adapter sound broader than the core policy, especially for trivial or generic
sub-agent use.

Potential improvement:

- Reword `adapters/claude/commands/init-harness.md` so methodology-level
  sub-agent guidance names the two core isolation triggers and treats any extra
  Claude-specific routing as runtime policy.
- Remove or qualify "Prefer over-invoking to under-invoking" so it does not
  override the core anti-pattern against trivial sub-agent use.
- Keep Claude-specific tactical guidance where it belongs, but make the
  core-vs-adapter boundary explicit.
- Update compatibility mirror `commands/init-harness.md` and focused path/docs
  tests if wording changes.

Done when:

- Claude init guidance cannot be read as adding a third paper/core
  methodology-level sub-agent trigger.
- Claude-specific sub-agent tactics are clearly runtime policy, not paper-core
  Meta-Harness claims.
- Mirror/path checks pass after the wording update.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the
  first edit happened after focused baseline checks only. Focused baseline gates
  passed: `python3 scripts/check-compat-mirrors.py`, `python3
  scripts/check-claude-adapter-paths.py`, `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`, `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`, and `python3
  scripts/check-search-set-evidence.py` before the evidence record was needed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Updated Claude `/init-harness` guidance to name the two core isolation
  triggers: multi-review for qualitative judgment and Fixed Evaluator for
  evaluator independence.
- Reframed generic parallel Explore/context firewall usage as Claude Code
  runtime tactics, not harness methodology, and bounded them to material
  independence or bounded parallel work.
- Removed the old "Prefer over-invoking to under-invoking" and "three trigger
  categories" wording from the canonical command and compatibility mirror.
- Added focused tests that pin the two-trigger/runtime-policy boundary and
  reject the legacy phrases in both canonical and mirror command files.

Multi-review:

- Methodology-boundary critic: score 9/10, PASS. Blocking findings: none. Why
  not 10: the first revision still had a broad "context isolation and tactical
  decision support" sentence; fixed in this item by narrowing temporary
  subagents to bounded runtime tactics.
- Mirror/test enforceability critic: score 8/10, VETO. Blocking findings:
  mirror-specific tests did not reject the legacy phrases in the root mirror;
  not accepted.
- Process-compliance critic: score 9/10, PASS. Blocking findings: none. Why not
  10: the backlog record initially lacked explicit Start Gate fields; fixed in
  this item by adding the full Start Gate.
- Score handling: the score below 9 was treated as VETO. The mirror/test VETO
  was fixed by adding forbidden-phrase assertions for the mirror. The
  methodology-boundary score-9 concern was fixed by narrowing the broad
  subagent allowance. The process score-9 concern was fixed by recording the
  full Start Gate.
- Affected methodology-boundary critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Affected mirror/test critic rerun: score 10/10, PASS. Blocking findings:
  none.
- Affected process-compliance critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Rerun status: all affected critics reran; final scores are 10/10, 10/10, and
  10/10 PASS.
- Follow-up/residual risk: none; actionable score-9 reasons were handled in
  this item.
- Final acceptance: accepted after VETO fix and affected critic reruns.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`,
  `commands/init-harness.md`, `tests/test_claude_init_harness_fixture.py`,
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-claude-adapter-paths.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation with reason
    above; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Claude adapter behavior and
  core-methodology boundary semantics.
- Multi-review result: PASS after three-critic multi-review, VETO fix, and
  affected critic reruns.
- Reviewer scores and VETO handling: methodology-boundary critic 9/10 PASS
  rerun to 10/10 PASS; mirror/test enforceability critic 8/10 VETO fixed and
  rerun to 10/10 PASS; process-compliance critic 9/10 PASS rerun to 10/10 PASS.
- For each score-9 result, why not 10:
  - Methodology-boundary critic: not 10 because broad temporary-subagent wording
    still remained; fixed in this item and rerun to 10/10 PASS.
  - Process-compliance critic: not 10 because Start Gate fields were not
    recorded in the backlog item yet; fixed in this item and rerun to 10/10
    PASS.
- Backlog items added from score-9 residual risk: none; all actionable score-9
  reasons were fixed here.
- Residual risk/follow-up: none.
- Accepted: yes.

### 15. P2 align Claude multi-review threshold with repository governance

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/skills/multi-review/SKILL.md
- skills/multi-review/SKILL.md
- tests/test_claude_multi_review_skill.py
- backlog/claude-adapter.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`MAINTENANCE.md` treats repository governance reviews below score 9 as VETO, and
the Codex multi-review skill has a governance mode for that local release
discipline. The Claude `multi-review` skill still marks all critics scoring at
least 7 with no veto as PASS. Claude-side maintainers can therefore accept
methodology, adapter, hook, or release-gate decisions under a weaker local rule
than this repository now requires.

Potential improvement:

- Add a repository-governance mode or explicit note to the Claude multi-review
  skill: when reviewing this repository's maintenance, harness-affecting changes,
  release gates, or durable adapter contracts, scores below 9 are VETO.
- Preserve the generic 7/10 PASS threshold only for non-governance qualitative
  reviews if that remains useful.
- Update the root compatibility mirror for the Claude skill and any focused
  tests or mirror checks affected by the wording.

Done when:

- Claude-side multi-review guidance cannot approve repository governance work
  with a critic score below 9.
- The generic multi-review threshold and repository release discipline are
  clearly separated.
- Compatibility mirror checks pass after the update.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the
  first edit happened after focused baseline checks only. Focused baseline gates
  passed: `python3 scripts/check-compat-mirrors.py`, `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`, and `python3
  scripts/check-search-set-evidence.py` before the evidence record was needed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Added a `Repository Governance Mode` section to the Claude multi-review skill
  so repository maintenance, harness-affecting changes, release gates, hook
  semantics, core methodology boundaries, and durable adapter contracts apply
  this repository's local release discipline.
- The Claude skill now says any reviewer or Critic score below 9 is VETO until
  the blocking finding is fixed and the affected Critic reruns to at least 9.
- Preserved the generic 7/10 PASS threshold only for non-governance qualitative
  reviews where repository maintenance policy is not the acceptance contract.
- Updated the root compatibility mirror and added focused tests for the
  governance mode, generic threshold separation, and mirror equality.

Multi-review:

- Governance semantics critic: score 10/10, PASS. Blocking findings: none.
- Mirror/test enforceability critic: score 9/10, PASS. Blocking findings: none.
  Why not 10: tests are lexical guardrails rather than a semantic parser of the
  full verdict table; accepted as residual risk because this matches the
  repository's focused policy-boundary test style.
- Process-compliance critic: score 9/10, PASS. Blocking findings: none. Why not
  10: final Completion Gate and acceptance record still needed to be written at
  report time; addressed by this Completion Gate.
- Score handling: no reviewer score below 9; no VETO.
- Rerun status: no VETO, so no affected critic rerun required.
- Follow-up/residual risk: accepted lexical-test limitation; procedural
  final-closure timing addressed by this Completion Gate.
- Final acceptance: accepted after three-critic multi-review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/multi-review/SKILL.md`,
  `skills/multi-review/SKILL.md`, `tests/test_claude_multi_review_skill.py`,
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_claude_multi_review_skill.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation with reason
    above; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Claude adapter review-contract
  semantics.
- Multi-review result: PASS after three-critic multi-review; no VETO.
- Reviewer scores and VETO handling: governance semantics critic 10/10 PASS;
  mirror/test enforceability critic 9/10 PASS; process-compliance critic 9/10
  PASS; no score below 9 and no VETO.
- For each score-9 result, why not 10:
  - Mirror/test enforceability critic: not 10 because tests are lexical
    guardrails rather than a semantic parser of the full verdict table; accepted
    as residual risk for this focused wording boundary.
  - Process-compliance critic: not 10 because final Completion Gate and
    acceptance record still needed to be written at report time; addressed by
    this Completion Gate.
- Backlog items added from score-9 residual risk: none; lexical guardrail
  limitation is accepted as residual risk, and procedural final-closure timing
  was handled here.
- Residual risk/follow-up: accepted lexical-test limitation.
- Accepted: yes.
