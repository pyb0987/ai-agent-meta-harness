# AcceptancePacket Fixtures

These files are planning fixtures for Plan 02. They are not active governance
packets and do not satisfy stable handoff.

Each fixture keeps the public packet surface to:

- `meta`
- `input`
- `result`

The next implementation plan should use these examples as checker fixtures before
adding `governance start`, `governance finalize`, or `governance check`.

`worktree-nonstable.yml` is a negative stable-handoff fixture: it may be accepted
as exploratory evidence, but it must never be stable-handoff eligible.
