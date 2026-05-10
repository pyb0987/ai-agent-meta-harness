# Plan 08: Release and Pre-Commit Packet Gate

## Purpose

Wire active v2 stable handoff into release and pre-commit entry points without
expanding the operator surface. Plan 08 owns the transition from legacy release
verification to packet-backed stable acceptance.

## Scope

- Define how release/pre-commit receives the finalized `AcceptancePacket`
  pointer.
- Require `governance check --packet <packet> --require-stable` for active
  stable handoff.
- Keep `scripts/verify-release.py --base-ref` as broad legacy verification
  until packet pointers are wired.
- Preserve staged mode as preflight only.

## Out of Scope

- Archive storage and immutable pointer publication; Plan 07 owns that backlog.
- Running artifact-supplied commands during stable check.
- Adding user-authored packet sections beyond `meta`, `input`, and `result`.

## Acceptance Seed

- Release and pre-commit gates fail when a required active packet pointer is
  absent.
- Release and pre-commit gates fail when the pointed packet is not finalized,
  base-ref mode, and stable eligible.
- Legacy verification commands remain runnable for compatibility but are not
  described as sufficient stable handoff.
