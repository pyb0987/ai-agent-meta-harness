# Maintenance Recovery Multi-Review

Date: 2026-04-30

This is a commit-visible recovery summary for an over-batched backlog
implementation pass. It is not a precedent for normal backlog workflow.
Future backlog work must return to one concrete item per iteration:
implement, run relevant checks, run required multi-review, record trace or
skipped trace/search-set reason, then update backlog wording.

## Why This Exists

The maintenance pass implemented several harness-affecting backlog items before
the `MAINTENANCE.md` iteration and multi-review gates were enforced. A local
evolution trace was written at
`.claude/traces/evolution/002-maintenance-backlog-review-recovery.md`, but
`.claude/` is ignored, so this tracked summary records the review outcome and
residual risk in the repository diff.

Project search-set verification was skipped because this repository trace root
does not have `.claude/traces/search-set.md`. Standard repository checks passed,
but those checks are not counted as project search-set PASS.

## Score Policy Note

`MAINTENANCE.md` now treats reviewer scores below 9 as VETO. Historical review
entries that were recorded as PASS with scores below 9 are not accepted under
the restored policy unless a rerun reaches at least 9. If a critic returned a
0-1 decimal score, this summary records the normalized 0-10 score.

## Reviewed Units

### Core Methodology and Reference

Files:

- `core/methodology.md`
- `core/reference.md`
- `docs/methodology.md`
- `docs/reference.md`
- `backlog/core.md`

Items covered:

- Fixed-evaluator search-loop detection heuristics.
- Trace history tie-breakers.
- Active verify command quality rules.
- Partially initialized trace-root handling.
- Archived search-set restore/re-archive workflow.
- Fixed-evaluator reference details.
- Documentation abstraction boundaries.
- Compatibility mirror removal planning.

Review outcome:

- Initial review: score 7, MIXED/VETO. Blocking finding: stale
  `Fixed Evaluator (for autoresearch)` wording leaked Python/JSON/git-diff
  specifics into core.
- Recovery: generalized the section to adapter-defined evaluator commands,
  immutable evaluator boundaries, machine-readable output, project-defined
  verdicts, candidate diff/raw evaluator output preservation, and abstract
  escalation triggers.
- Rerun status: core critic rerun after fixes.
- Re-review: score 9, PASS. Blocking findings: none.
- Score handling: initial score 7 triggered VETO recovery; final accepted score
  was 9.
- Follow-up/residual risk: none for this reviewed unit.
- Final acceptance: accepted for this reviewed unit.

### Codex Adapter Behavior

Files:

- `adapters/codex/README.md`
- `adapters/codex/skills/harness-engineer/SKILL.md`
- `adapters/codex/skills/init-codex-harness/SKILL.md`
- `adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template`
- `backlog/codex-adapter.md`

Items covered:

- Sandbox/escalation recording template.
- `.claude/traces/` to `.harness/traces/` migration behavior.
- Verify command discovery.
- Sub-agent surface matrix.
- Permission/escalation guidance.
- MCP/tool-use policy.

Review outcome:

- Initial review: score 8, MIXED/VETO. Blocking finding:
  `harness-engineer` could still reuse empty
  `.claude/traces/`; README overclaimed `.claude/traces/` reuse and sub-agent
  availability; tool discovery was not qualified by runtime surface.
- Recovery: aligned `.claude/traces/` reuse with meaningful-history checks,
  qualified top-level README behavior, and made `tool_search` conditional on
  the active surface exposing tool discovery.
- Rerun status: Codex adapter critic rerun after fixes.
- Re-review: score 9, PASS. Blocking findings: none.
- Score handling: initial score 8 triggered VETO recovery; final accepted score
  was 9.
- Follow-up/residual risk: none for this reviewed unit.
- Final acceptance: accepted for this reviewed unit.

### Plugin, Generated Bundle, and Release Gates

Files:

- `.githooks/pre-commit`
- `adapters/codex/examples/AGENTS.md.example`
- `adapters/codex/plugin-scope.md`
- `adapters/codex/scripts/smoke-local-plugin.py`
- `adapters/codex/tests/test_local_plugin_smoke.py`
- `plugins/ai-agent-meta-harness/`
- `scripts/sync-codex-plugin.py`
- `tests/test_sync_codex_plugin.py`

Items covered:

- Codex example bundle asset.
- Recursive plugin sync for owned adapter trees.
- Executable mode preservation and mismatch detection.
- Local plugin smoke coverage for example assets and executable hook assets.
- Pre-commit inclusion of autoresearch hook smoke assertions.

Review outcome:

- Initial review: score 8, MIXED/VETO. Blocking finding:
  `plugin-scope.md` omitted the new example asset. Follow-up suggested:
  additional release-gate tests.
- Recovery: documented `examples/AGENTS.md.example`, updated recursive scope
  wording, regenerated the plugin bundle.
- Rerun status: plugin/release critic rerun after fixes.
- Re-review: score 9, PASS. Blocking findings: none.
- Score handling: initial score 8 triggered VETO recovery; final accepted score
  was 9.
- Follow-up/residual risk: extra plugin sync tests split into later follow-up
  iterations.
- Final acceptance: accepted for this reviewed unit. Extra tests remained
  residual risk and were split into follow-up iterations.

### Maintenance Process

Files:

- `MAINTENANCE.md`
- `README.md`
- `backlog/README.md`
- this review summary

Review outcome:

- Initial review: score 3, VETO. Blocking findings: the diff batched multiple
  functional harness-affecting changes and did not yet record review/search-set
  obligations.
- Recovery: local evolution trace and this commit-visible summary record the
  multi-review outcome, skipped search-set verification, reviewed units, and
  residual risk.
- Historical re-review: score 8, PASS under the previous advisory-score policy,
  but VETO under the restored score policy. Blocking findings: accepted only as
  historical context, not as final restored-policy approval.
- Rerun status: all required process critics were rerun in the score-policy
  restoration follow-up after the restored VETO threshold was applied.
- Score handling: score 3 and historical score 8 were treated as VETO under
  the restored threshold; final acceptance depended on the later score-policy
  restoration rerun reaching score 9.
- Follow-up/residual risk: automated enforcement was promoted to
  `backlog/core.md` item 11 and is implemented in the maintenance review
  checker follow-up below.
- Final acceptance: accepted after the score-policy restoration follow-up.

## Verification

Passed after recovery edits:

```bash
python3 scripts/check-compat-mirrors.py
python3 scripts/check-claude-adapter-paths.py
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
sh .githooks/pre-commit
```

## Follow-Up Iteration: Required Example Source Test

The first normal follow-up iteration after the recovery batch addressed one
residual plugin-sync risk: missing required example source coverage.

Change:

- Added a focused `tests/test_sync_codex_plugin.py` case that writes a valid
  generated plugin tree, removes
  `adapters/codex/examples/AGENTS.md.example` from the canonical source, then
  asserts `check_files()` fails with `MISSING REQUIRED SOURCE`.

Verification:

```bash
python3 -m unittest tests/test_sync_codex_plugin.py
python3 -m unittest discover -s tests
python3 scripts/sync-codex-plugin.py --check
```

Multi-review:

- Release-gate critic: score 8, VETO under restored policy. Blocking findings:
  none recorded, but score is below the restored acceptance threshold.
- Test-isolation critic: normalized score 7.8, MIXED/VETO at first because the
  generated plugin tree was not written before source deletion. Blocking
  finding: test failure was not isolated to the missing required example source.
- Recovery: the test now writes the generated plugin tree first.
- Rerun status: test-isolation critic rerun after fixes; release-gate critic was
  not rerun after the restored score policy.
- Re-review: test-isolation critic normalized score 9.3, PASS. Blocking
  findings: none.
- Re-review: test scope critic rerun under restored policy, score 9, PASS.
  Blocking findings: none. Optional follow-up: end-to-end CLI sequence coverage
  may be added later.
- Re-review: release-gate critic rerun under restored policy, score 9, PASS.
  Blocking findings: none.
- Score handling: score 8 and normalized score 7.8 triggered VETO recovery;
  final accepted scores were normalized score 9.3 and score 9 from all required
  critics.
- Follow-up/residual risk: optional end-to-end CLI sequence coverage only.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Extra Generated File Test

The second normal follow-up iteration addressed one residual plugin-sync risk:
extra generated file rejection.

Change:

- Added a focused `tests/test_sync_codex_plugin.py` case that writes a valid
  generated plugin tree, adds
  `plugins/ai-agent-meta-harness/examples/unexpected.md`, then asserts
  `check_files()` fails with `EXTRA GENERATED`.

Verification:

```bash
python3 -m unittest tests/test_sync_codex_plugin.py
python3 -m unittest discover -s tests
python3 scripts/sync-codex-plugin.py --check
```

Multi-review:

- Test scope critic: score 9, PASS. Blocking findings: none.
- Release-gate critic: score 9, PASS. Blocking findings: none.
- Rerun status: no fixes were needed, so no rerun was required.
- Score handling: all required critics scored at least 9, so no VETO iteration
  was needed.
- Follow-up/residual risk: none for this follow-up iteration.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Generated Manifest Validation Test

The third normal follow-up iteration addressed the remaining plugin-sync
residual risk: generated manifest validation failures.

Change:

- Added a focused `tests/test_sync_codex_plugin.py` case that writes a valid
  generated plugin tree, keeps generated files byte-synced, monkeypatches
  `validate_manifest()` to fail only for the generated plugin manifest path,
  then asserts `check_files()` validates that generated path, reports
  `plugin.json skills must point to ./skills/`, and does not report
  `OUT OF SYNC`.

Verification:

```bash
python3 -m unittest tests/test_sync_codex_plugin.py
python3 -m unittest discover -s tests
python3 scripts/sync-codex-plugin.py --check
```

Multi-review:

- Test scope critic: score 8, VETO under restored policy. Blocking finding: the test proves generated manifest
  validation runs, with a caveat that editing a mapped generated manifest also
  triggers the generic out-of-sync path. The semantic manifest diagnostic keeps
  the test from passing only because of byte drift.
- Release-gate critic: score 8, VETO under restored policy. Blocking finding: the test meaningfully locks down
  generated manifest validation and has no blocking gap for this item.
- Recovery: changed the test to keep source/generated manifests byte-synced and
  use a path-sensitive `validate_manifest()` spy so the failure proves generated
  manifest validation rather than generic drift.
- Optional follow-up: add broader manifest cases later for invalid name, missing
  `interface.displayName`, malformed JSON, and missing generated manifest if
  broader manifest-contract coverage is desired.
- Rerun status: all required critics rerun after recovery.
- Re-review: test scope critic score 9, PASS. Blocking findings: none.
- Re-review: release-gate critic score 9, PASS. Blocking findings: none.
- Score handling: both initial score 8 reviews triggered VETO recovery; all
  required critics were rerun and reached score 9.
- Follow-up/residual risk: optional broader manifest cases may be added later,
  but no required follow-up remains for this scoped item.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Restore Score VETO Policy

This iteration restores the score policy selected by the user: scores below 9
are VETO.

Change:

- Updated `MAINTENANCE.md` to make score below 9 a VETO in both backlog workflow
  and multi-review policy.
- Added required review summary fields: critic scope, score, verdict, blocking
  findings, follow-up/residual risk, score handling, rerun status, and final
  acceptance.
- Updated this review summary so score-8 reviews are not marked accepted under
  the restored policy.

Verification:

```bash
rg -n "advisory|below 9|score 8|VETO|accepted|not accepted|Review summaries" MAINTENANCE.md backlog/review-2026-04-30-maintenance-recovery.md
```

Multi-review:

- Policy clarity critic: score 9, PASS. Blocking findings: none.
- Process/systemization critic: score 8, VETO. Blocking findings: earlier
  review sections lacked required score/rerun/final acceptance fields and the
  Maintenance Process section still said re-review was pending.
- Recovery: this summary now records score, verdict, blocking finding status,
  rerun status, and final acceptance status for each reviewed unit or follow-up
  iteration, and explicitly records follow-up/residual risk.
- Rerun status: all required critics rerun after this recovery.
- Re-review: policy clarity critic score 9, PASS. Blocking findings: none.
- Re-review: process/systemization critic score 9, PASS. Blocking findings:
  none.
- Score handling: process/systemization score 8 triggered VETO recovery; all
  required critics were rerun and reached score 9.
- Follow-up/residual risk: add an automated maintenance review checker in a
  later iteration.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Track Maintenance Review Checker

This iteration promoted automated maintenance review enforcement into the core
backlog before implementation.

Change:

- Added `backlog/core.md` item 11, `Add maintenance review summary checker`.
- Linked this recovery summary's automated-enforcement residual risk to that
  backlog item.

Verification:

```bash
rg -n "maintenance review summary checker|check-maintenance-review|item 11|score below 9|pending|required review fields" backlog/core.md backlog/review-2026-04-30-maintenance-recovery.md
```

Multi-review:

- Backlog item selection critic: score 9, PASS. Blocking findings: none.
  Follow-up: keep the future checker conservative and avoid overfitting one
  summary format.
- Maintenance process fit critic: score 9, PASS. Blocking findings: none.
- Rerun status: no fixes were needed, so no rerun was required.
- Score handling: all required critics scored at least 9, so no VETO iteration
  was needed.
- Follow-up/residual risk: implement `scripts/check-maintenance-review.py` in a
  later one-item iteration.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Maintenance Review Summary Checker

This iteration implemented `backlog/core.md` item 11 as one release-gate
support change.

Change:

- Added `scripts/check-maintenance-review.py` to validate tracked
  `backlog/review-*.md` summaries.
- Added `tests/test_check_maintenance_review.py` coverage for accepted score 9,
  rejected score 8 without VETO handling, unresolved pending rerun status, and
  missing required fields.
- Updated this recovery summary's Maintenance Process section so the previously
  unresolved restored-policy review status reflects the accepted follow-up
  state.
- Updated `backlog/core.md` item 11 from potential improvement to implemented
  foundation.

Verification:

```bash
python3 -m unittest tests/test_check_maintenance_review.py
python3 -m unittest discover -s tests
python3 scripts/check-maintenance-review.py
```

Multi-review:

- Checker correctness critic: score 7, VETO. Blocking findings:
  `score handling` was not enforced, required fields were checked at section
  scope instead of review-block/critic-record scope, and tests did not cover
  those gaps.
- Process/release-gate critic: score 7, VETO. Blocking findings: required
  fields could be satisfied by non-review prose, critic scope and score
  handling were not enforced, and the current review section was still pending.
- Recovery: restricted required-field checks to the actual review block, added
  explicit `Score handling:` enforcement, added per-score-record scope/verdict/
  blocking-finding checks, and added tests for prose false positives, missing
  critic scope, and score records without blocking findings.
- Rerun status: all required critics were rerun after recovery, not only the
  failed critic.
- Re-review: checker correctness critic score 9, PASS. Blocking findings:
  none.
- Re-review: process/release-gate critic score 9, PASS. Blocking findings:
  none.
- Score handling: both initial score 7 reviews triggered VETO recovery; all
  required critics were rerun and reached score 9.
- Follow-up/residual risk: keep the checker out of pre-commit until the review
  summary format is stable enough not to create noisy local failures.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Codex Local-Only Protection Reporting

This iteration implemented `backlog/codex-adapter.md` item 15 as one
autoresearch protection-reporting change.

Change:

- Updated `adapters/codex/skills/autoresearch/SKILL.md` to require
  `Protection level: incomplete | local-only | shared-repo | structural` in
  Setup Mode output.
- Defined skipped, missing, or unsmoke-tested minimum local protection as
  `incomplete` and unsafe for unattended autoresearch runs.
- Defined unavailable CI with passing minimum local protection as `local-only`
  with an explicit skipped CI reason.
- Re-verified Codex hook-schema assumptions and recorded the item 15
  re-verification in `adapters/codex/hook-schema.md`.
- Regenerated the local Codex plugin bundle and updated `backlog/codex-adapter.md`
  item 15 from potential improvement to implemented foundation.

Verification:

```bash
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 scripts/check-maintenance-review.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/codex/tests
```

Multi-review:

- Autoresearch protection semantics critic: score 9, PASS. Blocking findings:
  none. Follow-up: a future polish pass may narrow broad skipped-status wording,
  but the surrounding tier contract resolves the risk.
- Process/release-gate critic: score 8, VETO. Blocking findings: the
  hook-sensitive autoresearch skill changed without a hook-schema
  re-verification update, so staged release gates could reject the item.
- Recovery: re-checked the official Codex hooks and config references, confirmed
  `PreToolUse`, `PermissionRequest`, and `features.codex_hooks` assumptions were
  unchanged, recorded the re-verification note in the canonical hook schema, and
  regenerated the plugin copy.
- Rerun status: all required critics were rerun after recovery, not only the
  failed critic.
- Re-review: autoresearch protection semantics critic score 10, PASS. Blocking
  findings: none.
- Re-review: process/release-gate critic score 10, PASS. Blocking findings:
  none.
- Score handling: initial process/release-gate score 8 triggered VETO recovery;
  all required critics were rerun and reached score 10.
- Follow-up/residual risk: add a concrete setup transcript after a real
  autoresearch dry run exercises all protection levels. Runtime hook activation
  and tool-event coverage remain tracked outside this item.
- Final acceptance: accepted for this follow-up iteration.

## Follow-Up Iteration: Codex Pathlib Evaluator Write Protection

This iteration completed the `backlog/codex-adapter.md` item 12 follow-up for
Bash hook detection of pathlib evaluator writes.

Change:

- Updated `adapters/codex/scripts/check-autoresearch-protected.py` so Bash hook
  mutation detection treats pathlib `.open(...)` write modes and built-in
  `open(..., mode=...)` write-capable modes as mutating.
- Added regression tests for `Path('evaluate.py').open('w').write(...)`,
  `Path('evaluate.py').open('r+').write(...)`, built-in
  `open('evaluate.py', mode='r+')`, built-in
  `open(file='evaluate.py', mode='w')`, and read-only `mode='r'`.
- Updated `adapters/codex/scripts/smoke-autoresearch-hooks.py` to exercise a
  pathlib evaluator-write payload.
- Recorded item 12 hook-schema re-verification in
  `adapters/codex/hook-schema.md`.
- Regenerated the local Codex plugin bundle and updated
  `backlog/codex-adapter.md` item 12 implemented foundation.

Verification:

```bash
python3 -m unittest adapters.codex.tests.test_check_autoresearch_protected
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 scripts/check-maintenance-review.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/codex/tests
sh .githooks/pre-commit
```

Multi-review:

- Protected-file checker correctness critic: score 8, VETO. Blocking findings:
  pathlib `.open('r+')` write-capable modes still bypassed hook-time mutation
  detection.
- Release-gate/generated-bundle critic: score 9, PASS. Blocking findings:
  none.
- Recovery: broadened write-mode detection to include `+` modes such as `r+`
  and added regression coverage.
- Rerun status: all required critics were rerun after the first recovery, not
  only the failed critic.
- Re-review: protected-file checker correctness critic score 8, VETO. Blocking
  findings: built-in `open('evaluate.py', mode='r+')` and
  `open(file='evaluate.py', mode='w')` keyword forms still bypassed protection.
- Re-review: release-gate/generated-bundle critic score 9, PASS. Blocking
  findings: none.
- Second recovery: added built-in `open(..., mode=...)` write-mode detection and
  regression tests for keyword mode forms while preserving read-only `mode='r'`.
- Rerun status: all required critics were rerun after the second recovery, not
  only the failed critic.
- Re-review: protected-file checker correctness critic score 9, PASS. Blocking
  findings: none.
- Re-review: release-gate/generated-bundle critic score 9, PASS. Blocking
  findings: none.
- Score handling: both protected-file checker correctness score 8 reviews
  triggered VETO recovery; all required critics were rerun after each recovery
  and reached score 9.
- Follow-up/residual risk: Bash detection remains heuristic rather than a full
  shell or Python parser. Hard protection still depends on pre-commit and CI
  detecting actual protected-file diffs, and runtime Codex hook activation
  coverage remains tracked separately.
- Final acceptance: accepted for this follow-up iteration.

## Residual Risk

- This remains an exceptional recovery batch rather than a normal
  one-item-per-iteration sequence.
- The maintenance review checker is not yet part of pre-commit; that remains
  deferred until the format is stable enough not to create noisy local failures.
- Codex runtime hook activation and tool-event coverage still require the
  separate activation smoke-test backlog item.
