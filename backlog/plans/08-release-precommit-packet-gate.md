# Plan 08: Release and Pre-Commit Packet Gate

## Purpose

Wire active v2 stable handoff into release and pre-commit entry points without
expanding the operator surface. Plan 08 owns the transition from legacy release
verification to packet-backed stable acceptance.

## Scope

- Define how release/pre-commit receives the active archive pointer without
  adding routine operator input:
  - release `--base-ref REF` discovers exactly one changed pointer under
    `archive/v2/pointers/` from `REF...HEAD`
  - staged pre-commit discovers exactly one staged pointer when staged
    `archive/v2/` packet/artifact/pointer bytes are present
  - staged validation reads the Git index snapshot, not worktree bytes
  - `--pointer` is only an explicit selector inside a `--base-ref` or `--staged`
    scope; pointer-only validation stays in `check-governance-acceptance.py
    check-pointer`
- Require the pointed packet to pass the stable packet checker and to be
  finalized, base-ref mode, and stable-handoff eligible.
- Require release `--base-ref REF` to match the pointed packet comparison ref so
  uncovered commits cannot ride outside the active packet scope.
- Keep `scripts/verify-release.py --base-ref` as broad release verification,
  now with the active packet pointer gate included.
- Preserve staged mode as preflight only; ordinary non-archive staged changes do
  not require a pointer.
- Avoid a bare no-op standard packet-gate command; the active gate runs only in
  `--base-ref` or `--staged` scope.

## Out of Scope

- Active archive pointer publication; Plan 07 owns that backlog.
- Historical archive namespace closure, durable archive refs, and runner
  attestation; Plan 09 owns that backlog.
- Running artifact-supplied commands during stable check.
- Adding user-authored packet sections beyond `meta`, `input`, and `result`.

## Acceptance Seed

- Release and pre-commit gates fail when a required active packet pointer is
  absent.
- Release and pre-commit gates fail unless the pointed packet is finalized,
  base-ref mode, and stable eligible.
- Release `--base-ref` remains argv-based and listable while adding the active
  packet pointer gate.

## Implementation

- `scripts/check-active-packet-gate.py`
  - `--base-ref REF` requires a pointer discovered from `REF...HEAD`
  - `--staged` requires a pointer only when staged `archive/v2/` evidence bytes
    are present
  - validates the active pointer, then validates the pointed packet with
    `require_stable=True`
  - validates staged mode against the staged index snapshot, not worktree bytes
- `scripts/verify-release.py` includes the active packet pointer gate and passes
  `--base-ref` and optional base-ref-scoped `--pointer` through when release
  verification uses base-ref mode.
- `.githooks/pre-commit` runs the staged active packet gate.
