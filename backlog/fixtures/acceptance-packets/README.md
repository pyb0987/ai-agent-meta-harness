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

Residual label: `v2-residual-02 historical-fixture-boundary`. A fixture can be a
positive or negative validator control, but it is not an active handoff record,
future archive whitelist, or routine trusted command-evidence source.

Active stable handoff is base-ref canonical. Staged stable-looking fixtures are
kept only as compatibility examples for packet-shape and validator regression
coverage; they are not active handoff records.

`worktree-nonstable.yml` is a negative stable-handoff fixture: it may be accepted
as exploratory evidence, but it must never be stable-handoff eligible.
