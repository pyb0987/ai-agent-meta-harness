# Codex Hook Schema Reference

This reference records the Codex hook contract that the Codex adapter currently
depends on. It is an adapter-maintainer guardrail, not shared Meta-Harness core
methodology.

This drift check validates documented output-shape assumptions only. It does not prove hook event coverage, command interception coverage, or Codex plugin runtime activation.

## Verification Metadata

- Verified date: 2026-05-04
- Codex CLI checked: 0.126.0-alpha.8
- Primary source: https://developers.openai.com/codex/hooks
- Config source: https://developers.openai.com/codex/config-reference
- Freshness convention: `Verified date` tracks the most recent official
  hooks/config documentation re-check that this adapter depends on. If the
  output/config contract is unchanged, keep the behavior contract stable and add
  a dated re-verification note explaining the non-behavior change.
- Re-verification note: 2026-05-04 item 36 added bounded command hook
  `timeout` values for protected-file checks; official Codex hooks docs were
  re-checked, and `timeout` remains a per-command-hook value in seconds with a
  600 second default when omitted. Hook output shapes remain unchanged.
- Re-verification note: 2026-05-04 item 45 aligned the embedded autoresearch
  skill `.codex/hooks.json` example with the already-verified item 36 bounded
  timeout contract; hook output shapes and timeout semantics remain unchanged.
- Re-verification note: 2026-05-03 item 27 defined direct-copy degraded
  reporting only; official Codex hooks/config docs were re-checked, and
  `PreToolUse`, `PermissionRequest`, `hookSpecificOutput`, and
  `features.codex_hooks` output/config assumptions remain unchanged.
- Re-verification note: 2026-04-30 item 15 changed autoresearch protection
  reporting only; `PreToolUse`, `PermissionRequest`, and `features.codex_hooks`
  output/config assumptions were re-checked and remain unchanged.
- Re-verification note: 2026-05-01 item 2 aligned autoresearch trace-root
  selection only; official Codex hooks and config docs were re-checked, and
  `PreToolUse`, `PermissionRequest`, and `features.codex_hooks` output/config
  assumptions remain unchanged.
- Re-verification note: 2026-04-30 item 12 hardened Bash mutation detection for
  pathlib evaluator writes; hook output shapes were re-checked and remain
  unchanged.

Before changing Codex hook templates, hard-layer pre-commit/CI protection
templates, hook checker output, or autoresearch hook instructions, check the
official Codex hooks documentation again and update this file if the contract
changed or was re-verified. Hard-layer template changes also require
protection-contract review even when the Codex hook JSON output shape is
unchanged.

## Expected Blocking Output Shapes

### PreToolUse

The adapter expects protected-path denials to return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Autoresearch evaluator boundary violation: protected path evaluate.py would be modified."
  }
}
```

Expected `hookSpecificOutput` keys:

- `hookEventName`
- `permissionDecision`
- `permissionDecisionReason`

### PermissionRequest

The adapter expects escalation denials to return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Autoresearch evaluator boundary violation: protected path evaluate.py would be modified."
    }
  }
}
```

Expected `hookSpecificOutput` keys:

- `hookEventName`
- `decision`

Expected nested `decision` keys:

- `behavior`
- `message`

Do not use the legacy top-level `{"decision": "block"}` shape for this adapter.

## Hook Command Timeout Contract

Codex command hooks support a `timeout` field in seconds; if omitted, Codex uses
a 600 second default. This adapter pins protected-file `PreToolUse` and
`PermissionRequest` hook commands to 5 seconds so evaluator-boundary checks fail
fast enough for interactive use while still allowing normal repository-local
Python startup and git-root resolution.

## Drift Procedure

When a hook-sensitive adapter file changes:

1. Re-check the official Codex hooks and config documentation.
2. Update `Verified date` and `Codex CLI checked` above when the official
   hooks/config docs are re-verified; add a dated re-verification note even
   when the output/config contract remains unchanged.
3. Re-run `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py` in a
   target-project fixture with `.harness/autoresearch-protected.txt`.
4. Re-run `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`.
5. If Codex interception semantics changed, add or update a backlog item before
   enabling runtime hook manifest fields.
