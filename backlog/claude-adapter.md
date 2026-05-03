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

Status: 대기
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
