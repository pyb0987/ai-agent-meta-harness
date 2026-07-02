---
iteration: 7
date: "2026-07-01"
type: structural
verdict: improved
files_changed: ["README.md", ".harness/traces/evolution/007-claude-profile-drift-governance.md", ".harness/traces/search-set.md", "adapters/claude/scripts/check-claude-profile-drift.py", "adapters/claude/skills/harness-engineer/SKILL.md", "adapters/claude/templates/profile-governance.json", "skills/harness-engineer/SKILL.md", "tests/test_claude_compat_install_smoke.py", "tests/test_claude_profile_drift.py", "tests/test_maintenance_policy_boundaries.py"]
refs: [6]
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/search-set.md
      lines: 43-51
      quote: "Users install the harness globally and work in other projects, while hand-authored `~/.claude/rules` and `~/.claude/settings*.json` drift outside repository-local governance."
---

## Iteration 007: Claude profile drift governance

Trigger: A Claude-side usage review noted that real users install this harness
globally and then work in other projects. The repository already checks its own
adapter mirrors and search-set, but a user's hand-authored `~/.claude/rules`
and `~/.claude/settings*.json` files were outside the governed surface.

### Diagnosis

The existing repository-local checks are correct for this repo, but they stop at
the repo edge. For Claude Code, the daily-work steering layer can include global
rules, global docs, settings hooks, and local model-selection notes. If those
files drift from the installed harness methodology or describe hooks that are
not present in settings, the user experiences a harness failure even though the
repo's own self-checks still pass.

The smallest structural fix is not to govern the user's whole home directory.
It is to ship an adapter-owned checker plus an explicit manifest. The manifest
declares only the global Claude profile files the user wants governed. The
checker then verifies canonical rule mirrors, hook contracts, and blocked model
IDs from raw installed files.

### Change

- Added `adapters/claude/scripts/check-claude-profile-drift.py`, a dependency-free
  JSON-manifest checker for installed Claude profiles.
- Added `adapters/claude/templates/profile-governance.json`, whose default
  scope checks only the installed harness methodology/reference mirrors against
  canonical copies under `~/.claude/harness/canonical/`.
- Updated README Claude install commands to install the checker, manifest, and
  canonical copies, then run the drift check.
- Updated the Claude `harness-engineer` skill and compatibility mirror so
  repeated-failure diagnosis can run the installed profile checker when global
  Claude rules, settings, hook docs, or model IDs are implicated.
- Added fixture tests for valid profiles, canonical mirror drift, missing hook
  commands, documented hook events absent from settings, stale model IDs, the
  default template, and CLI JSON failure output.
- Accepted implementation multi-review findings by expanding the default
  manifest to installed `commands/` and `skills/`, honoring `CLAUDE_HOME` in the
  README install block, constraining manifest paths to the governed Claude home,
  constraining `repo:` sources to the declared source root, and requiring
  non-empty hook command fragments.
- Accepted a second implementation review by narrowing hook command extraction
  to actual Claude hook entries with `type: "command"` and rejecting empty
  command fragments, so metadata-only `command` fields cannot satisfy hook
  contracts.
- Added an Active search-set case for the Claude global profile drift boundary.

### Result

The Claude adapter now covers the real user path more directly:

```text
ai-agent-meta-harness clone
  -> install Claude adapter globally
  -> ~/.claude/harness/profile-governance.json
  -> python3 ~/.claude/harness/scripts/check-claude-profile-drift.py
```

This is still diagnostic profile governance, not repository-local stable
publication evidence. It does not semantic-parse every user rule and it does
not make arbitrary `~/.claude` files part of v2 governance. Users opt files into
the manifest when those files actually steer daily Claude behavior.

Multi-review:

- Review date: 2026-07-02.
- Review mode: Codex multi-review with dogfood-boundary critic,
  profile-checker correctness critic, and product/methodology critic.
- Verdict: PASS after follow-up fixes.
- Findings disposition: repeated dogfood findings were stale/closed by existing
  tests and bounded diagnostic output; default profile governance now covers
  installed command and skills; manifest/profile path escape is rejected; empty
  hook fragments are rejected; metadata-only `command` fields do not satisfy
  hook contracts.
- Verification: `python3 -m unittest tests/test_harness_dogfood.py
  tests/test_claude_profile_drift.py tests/test_claude_compat_install_smoke.py
  tests/test_maintenance_policy_boundaries.py`; `python3 scripts/run-search-set.py
  --case SS-008`; `python3 scripts/check-compat-mirrors.py`;
  `python3 scripts/check-claude-adapter-paths.py`; `python3
  scripts/check-trace-retrieval-provenance.py
  .harness/traces/evolution/007-claude-profile-drift-governance.md`; `git diff
  --check`.

### Lesson

Global agent profiles are harness surfaces when they steer daily work. They
should be governed with the same single-source and runnable-check discipline,
but only through explicit manifests so the user's mental model stays small.
