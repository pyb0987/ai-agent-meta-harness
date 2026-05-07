# AcceptancePacket Fixtures

These files are checker fixtures for the Plan 02 AcceptancePacket surface. Some
finalized fixtures are stable-handoff eligible and must pass
`scripts/check-governance-acceptance.py check --require-stable`; nonstable
fixtures remain negative controls.

Each fixture keeps the public packet surface to:

- `meta`
- `input`
- `result`

The fixtures are examples for validating `governance start`, `governance
finalize`, and `governance check` behavior, not active project governance
packets.

`worktree-nonstable.yml` is a negative stable-handoff fixture: it may be accepted
as exploratory evidence, but it must never be stable-handoff eligible.
