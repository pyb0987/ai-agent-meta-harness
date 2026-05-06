# v1 Archive Import Manifest

This manifest records the initial `archive/v1/` import used during the v2
transition. Files that match the pre-transition `HEAD` source are faithful
relocations. Files that differ from `HEAD` are preserved as local pre-v2
worktree snapshot content and are hash-pinned here so the initial import does
not silently present unverified edits as active v2 evidence.

| Archive path | SHA256 | Source note |
|--------------|--------|-------------|
| `archive/v1/README.md` | `d0fde6fa9df873f5062b7bd81a00f524c97252c2bf6fe21c3094d7109da9edfa` | v1 archive index created for the v2 transition |
| `archive/v1/MAINTENANCE.md` | `b176863006d6bbc609271fc32aad1a1999826f7eceef58cca740a51575d7c9d9` | `HEAD:MAINTENANCE.md` |
| `archive/v1/backlog/README.md` | `47cdd291da5d9c16255cbf74655b653bf3b979ae9f5770b3c185dbdc7a0f99c8` | local pre-v2 worktree snapshot of `backlog/README.md` |
| `archive/v1/backlog/archive/claude-adapter.md` | `a7885184ce1cab815d35cc942fbdc9055774d56e57def0440eae9871e03a28b8` | `HEAD:backlog/archive/claude-adapter.md` |
| `archive/v1/backlog/archive/codex-adapter.md` | `1622a620d2b9293cabb34a612ab049a8bd0a1343df09c94b59e5a706ef6be9b9` | `HEAD:backlog/archive/codex-adapter.md` |
| `archive/v1/backlog/archive/core.md` | `c7ba907f6c5b8117faf67f99741884e87e5c4ee9fa8f90f2f834b05527cbb871` | `HEAD:backlog/archive/core.md` |
| `archive/v1/backlog/claude-adapter.md` | `88f552cb41e7bfddbbc64ecd57129781c6f5c9eefbf064a6ba7c41844aecf811` | `HEAD:backlog/claude-adapter.md` |
| `archive/v1/backlog/codex-adapter.md` | `612d1f2b9d547a766892d643b1b025f0c3bdcb77aef6067bd63c789195234502` | local pre-v2 worktree snapshot of `backlog/codex-adapter.md` |
| `archive/v1/backlog/core.md` | `0e4c0e63509aef52b4e289e32c3c3590885c93422883900451f768ed90b99ee8` | local pre-v2 worktree snapshot of `backlog/core.md` |
| `archive/v1/backlog/review-2026-04-30-maintenance-recovery.md` | `51830033b11ef35fedc5ee2dae10a5556a244a0ffcc8a3cf7178600cb9788d48` | `HEAD:backlog/review-2026-04-30-maintenance-recovery.md` |
