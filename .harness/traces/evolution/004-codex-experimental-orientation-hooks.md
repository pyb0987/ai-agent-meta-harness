---
iteration: 4
date: "2026-06-22"
type: additive
verdict: improved
files_changed: ["adapters/codex/hooks/experimental/harness_orientation.py", "adapters/codex/hooks/experimental/harness-orientation-hooks.json.example", "adapters/codex/hook-schema.md", "adapters/codex/plugin-scope.md", "adapters/codex/README.md", "plugins/ai-agent-meta-harness/hooks/experimental/harness_orientation.py", "plugins/ai-agent-meta-harness/hooks/experimental/harness-orientation-hooks.json.example", "backlog/review-2026-06-22-codex-orientation-hooks.md", ".harness/traces/evolution/004-codex-experimental-orientation-hooks.md"]
refs: [1]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/search-set.md
      lines: 23-26
      quote: "### SS-003: Pre-commit release gate remains wired\n- **Source**: backlog/core.md item 18, item 29, and Codex adapter release-gate follow-ups.\n- **Symptom**: Repository drift, smoke, marketplace metadata, or maintenance-review checks can fall out of the tracked pre-commit gate.\n- **verify**: `sh .githooks/pre-commit`"
---

## Iteration 004: Codex experimental orientation hooks

Trigger: A comparison with Ponytail suggested that prompt-injection-style hook
orientation could improve this repository's Codex harness, provided it stayed
opt-in, evidence-oriented, and bounded by the meta-harness methodology.

### Diagnosis

The repository was right to avoid active runtime hooks by default because the
meta-harness values fixed evaluator boundaries, trace reuse, confounder
isolation, and human judgment boundaries over invisible runtime mutation. The
Codex adapter still had room for a narrower hook pattern: session orientation
that reads tracked harness context and returns additional session context
without changing files, running evaluators, or claiming stable acceptance.

The Codex hook schema itself is experimental. The implementation therefore
needed three guardrails:

- keep hook assets under `hooks/experimental/`
- require explicit local hook configuration before execution
- pin documentation and drift checks to the currently verified hook contract

### Change

- Diff summary: Added an experimental `harness_orientation.py` hook and example
  Codex hook config for `SessionStart` and `UserPromptSubmit`.
- Diff summary: Extended plugin sync and smoke checks so the synced Codex
  plugin carries the hook assets and preserves executable mode.
- Diff summary: Updated hook-schema documentation and drift checks for the
  2026-06-22 `features.hooks` contract and deprecated `features.codex_hooks`
  alias.
- Diff summary: Added focused unit tests for context selection, JSON output,
  explicit activation docs, and executable-mode enforcement.
- Referenced files: `adapters/codex/hook-schema.md`
- Referenced files: `adapters/codex/plugin-scope.md`

### Result

- Before: Codex adapter hook orientation was only a design possibility, with no
  tracked experimental hook asset or drift-checked plugin sync path.
- After: Codex adapter hook orientation is recorded as opt-in experimental
  context delivery with tests, plugin sync coverage, and explicit no-stable-
  acceptance scope.

Verification:

```text
$ python3 -m unittest adapters/codex/tests/test_experimental_orientation_hooks.py adapters/codex/tests/test_hook_schema_drift.py adapters/codex/tests/test_hook_templates.py adapters/codex/tests/test_local_plugin_smoke.py tests/test_sync_codex_plugin.py
Ran 60 tests
OK

$ python3 adapters/codex/scripts/smoke-local-plugin.py
Local Codex plugin smoke test passed: plugins/ai-agent-meta-harness

$ python3 adapters/codex/scripts/check-codex-hook-schema-drift.py --skip-staged-policy
Codex hook schema drift check passed.

$ python3 -m py_compile adapters/codex/hooks/experimental/harness_orientation.py plugins/ai-agent-meta-harness/hooks/experimental/harness_orientation.py
PASS

$ git diff --check
PASS
```

Multi-review outcome: FALLBACK_NONINDEPENDENT advisory pass. No blocking
findings were recorded. Residual risk is accepted only for opt-in experimental
use, with no plugin manifest hook activation.

### Lesson

Ponytail-style hook orientation fits the meta-harness when it is treated as a
bounded context conveyor, not as hidden policy execution. The durable method is
to keep runtime hooks experimental, explicit, testable, and synchronized through
the same adapter/plugin evidence path as the rest of the Codex harness.
