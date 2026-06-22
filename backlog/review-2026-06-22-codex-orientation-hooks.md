# Codex Experimental Orientation Hooks Review

Review scope: opt-in experimental Codex orientation hook assets, their synced
plugin copy, hook-schema documentation, plugin smoke checks, and regression
tests for explicit activation and non-executable failure modes.

Search-set verification:

- BEFORE: SKIPPED no pre-change Active search-set run was captured before the
  experimental hook implementation began.
- AFTER: PASS `python3 -m unittest adapters/codex/tests/test_experimental_orientation_hooks.py adapters/codex/tests/test_hook_schema_drift.py adapters/codex/tests/test_hook_templates.py adapters/codex/tests/test_local_plugin_smoke.py tests/test_sync_codex_plugin.py`
  covered hook behavior, schema drift, docs expectations, local plugin smoke
  policy, and plugin sync.
- AFTER: PASS `python3 adapters/codex/scripts/smoke-local-plugin.py` covered
  synced plugin bundle requirements.
- AFTER: PASS `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py --skip-staged-policy`
  covered the re-verified Codex hook schema markers.
- AFTER: PASS `python3 -m py_compile adapters/codex/hooks/experimental/harness_orientation.py plugins/ai-agent-meta-harness/hooks/experimental/harness_orientation.py`
  covered syntax for canonical and synced hook scripts.
- AFTER: PASS `git diff --check` covered whitespace safety.

## Implementation Review

Multi-review:

- Governance critic: score 9.0 PASS, critic scope methodology fit for opt-in
  Codex runtime hooks. Blocking findings: none after hook assets remain under
  `hooks/experimental`, require explicit local opt-in configuration, and do not
  mutate repository state. Why not 10: independent sub-agent review was
  unavailable, so this is accepted as a nonindependent multi-review fallback
  advisory pass rather than a formal governance PASS.
- Runtime safety critic: score 9.0 PASS, critic scope prompt-injection and
  runtime behavior. Blocking findings: none after the hook constrains context
  lookup to tracked harness surfaces, handles missing context as status output,
  and returns session context rather than active tool instructions. Why not 10:
  the Codex hook contract remains experimental and must be re-verified when
  upstream docs change.
- Evidence critic: score 9.0 PASS, critic scope tests, smoke checks, and sync
  evidence. Blocking findings: none after focused unit tests, schema drift
  checks, local plugin smoke, bytecode compilation, `git diff --check`, and
  direct mirror diffs passed. Why not 10: no live Codex runtime hook invocation
  was performed in this repository session.
- Blocking findings: none remaining for this opt-in experimental hook batch.
- Follow-up/residual risk: accepted for experimental adoption only; the plugin
  manifest remains inactive and users must opt in through local Codex hook
  configuration before any orientation hook runs.
- Score handling: all critic scores are 9.0 PASS; why-not-10 items are accepted
  residual risks for experimental Codex hook stability and nonindependent
  review evidence.
- Rerun status: no blocking fixes were requested after the implementation
  review; focused verification passed after docs, tests, smoke checks, and
  synced plugin assets were updated.
- Final acceptance: PASS for committing and pushing the opt-in experimental
  orientation hook batch.
