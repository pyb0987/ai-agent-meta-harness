# Claude Adapter Backlog

Claude Code-specific follow-ups live here. Shared methodology belongs in
`backlog/core.md`; Codex runtime work belongs in `backlog/codex-adapter.md`.

## Priority Candidates

### 1. Keep Claude trace and hook paths mechanically consistent

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- adapters/claude/tests/test_claude_adapter_paths.py
- backlog/claude-adapter.md

Decision implemented: Claude adapter docs now use concrete Claude Code paths for
adapter-owned artifacts, and pre-commit validates the path contract.

This check is index-oriented lexical documentation validation. It does not
prove Claude Code runtime hook activation, `.claude/settings.local.json` schema
acceptance, or actual `/init-harness` generated project output.

Implemented foundation:

- Claude adapter trace paths resolve to `.claude/traces/...`.
- Claude hook scripts resolve to `.claude/hooks/...`.
- Claude hook settings resolve to `.claude/settings.local.json`.
- `scripts/check-claude-adapter-paths.py` rejects bare `traces/...`,
  `traces/`, `failures/`, `hooks/...`, `hooks/`, and `settings.local.json` in
  Claude adapter docs.
- The tracked pre-commit hook runs the path contract check after compatibility
  mirror validation.
- The checker discovers indexed `adapters/claude/**/*.md` surfaces plus the
  indexed README Claude section; core docs and Codex docs are intentionally
  outside its scope.

Decision implemented for temp-git fixture coverage:

- `adapters/claude/tests/test_claude_adapter_paths.py` now exercises the path
  checker inside temporary Git repositories instead of only monkeypatching
  indexed file lists.
- The temp-git tests prove staged clean Claude paths pass even when the working
  tree has unstaged bare-path drift.
- The tests prove staged-added Claude markdown with a bare hook path fails.
- The tests prove paths removed from the index with `git rm --cached` are not
  discovered by the checker.

Remaining follow-up work:

- Add an old Claude install command smoke test while compatibility mirrors exist.
- Add a project-fixture smoke test that runs `/init-harness` output expectations
  against a minimal target project once command execution can be tested
  mechanically.
- Add Claude hook settings schema/runtime activation smoke coverage when it can
  be tested mechanically.
- Track repo-wide staged-content semantics for compatibility mirror checks in
  `backlog/core.md`.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `adapters/claude/tests/test_claude_adapter_paths.py` and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest adapters/claude/tests/test_claude_adapter_paths.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this validates release-gate/index
  semantics for the Claude pre-commit path checker.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Index-semantics coverage critic score 10,
  verdict PASS, Blocking findings: none. Regression isolation critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score
  9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: remaining Claude hook/runtime and install smoke
  follow-ups stay listed above.
- Accepted: yes; accepted by maintainer review and ready for commit.

## Current Status

- Source review: external session found Claude adapter trace/hook path drift as
  the largest remaining operability issue.

### 2. Add old Claude compatibility install smoke test

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- tests/test_claude_compat_install_smoke.py
- backlog/claude-adapter.md

Compatibility mirrors stay until old mirrored install commands and canonical
Claude install commands both have smoke coverage. The old top-level
`docs/`, `commands/`, and `skills/` paths should be mechanically checked so
existing user scripts can still install working Claude Code assets during the
transition window.

Original improvement:

- Add a temp-directory smoke test for the old compatibility install source
  paths.
- Verify old mirrored paths install the same core Claude global files as the
  canonical adapter paths.
- Keep the smoke test local-only; it should not write to the real
  `~/.claude/` directory.

Decision implemented:

- `tests/test_claude_compat_install_smoke.py` now installs the old top-level
  compatibility mirrors into a temporary fake Claude home.
- The smoke test installs the canonical `core/` and `adapters/claude/` sources
  into a second fake Claude home and compares the expected global Claude files.
- Docs, command, and skill comparisons reuse the compatibility mirror
  normalizer so allowed mirror banners and install wording do not create false
  failures.
- The smoke test asserts the old install source still provides methodology,
  reference, `/init-harness`, `autoresearch`, `harness-engineer`, and
  `multi-review` assets without writing to the real `~/.claude/`.

Remaining follow-up work:

- Add a project-fixture smoke test that runs `/init-harness` output expectations
  against a minimal target project once command execution can be tested
  mechanically.
- Add Claude hook settings schema/runtime activation smoke coverage when it can
  be tested mechanically.
- Track repo-wide staged-content semantics for compatibility mirror checks in
  `backlog/core.md`.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `tests/test_claude_compat_install_smoke.py` and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_compat_install_smoke.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `git diff --check`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this affects Claude install/distribution
  compatibility and mirror-removal readiness.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Install compatibility critic score 10,
  verdict PASS, Blocking findings: none. Mirror-normalization critic score 10,
  verdict PASS, Blocking findings: none. Maintenance compliance critic score
  9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: remaining Claude project-fixture and hook/runtime
  smoke follow-ups stay listed above.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 3. Add Claude init-harness project-fixture smoke test

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-01
Scope:
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

The Claude `/init-harness` command documents completion verification for a
target project, but the repository does not yet have a mechanical smoke test
that applies those output expectations to a minimal project fixture.

Original improvement:

- Add a temp-project fixture smoke test for the documented `/init-harness`
  output contract.
- Validate trace directories, `search-set.md`, initial evolution trace,
  `CLAUDE.md` harness section, hook settings, and the absence of
  `.claude/agents/`.
- Keep actual Claude Code slash-command execution out of scope until it can be
  exercised mechanically.

Decision implemented:

- `tests/test_claude_init_harness_fixture.py` now builds a minimal temporary
  target project fixture and validates the documented `/init-harness`
  completion outputs.
- The smoke validator checks `.claude/traces/{evolution,failures,experiments}/`,
  `.claude/hooks/`, `.claude/traces/search-set.md`, initial evolution trace,
  `CLAUDE.md` harness markers, `.claude/settings.local.json` hook structure,
  and the absence of `.claude/agents/`.
- Negative tests reject forbidden `.claude/agents/` creation and missing
  `SS-001` Active search-set coverage.
- Actual Claude Code slash-command execution remains out of scope until this
  repository can exercise it mechanically.

Remaining follow-up work:

- Add true Claude Code slash-command execution coverage when the runtime can be
  exercised mechanically.
- Add Claude hook settings schema/runtime activation smoke coverage when it can
  be tested mechanically.

Completion Gate:

- Backlog status: `리뷰대기`.
- Changed files: `tests/test_claude_init_harness_fixture.py` and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_init_harness_fixture.py`, `python3 scripts/check-maintenance-review.py`, `python3 scripts/check-claude-adapter-paths.py`, `git diff --check`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, and `python3 -m unittest discover -s adapters/codex/tests`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this validates Claude adapter init output
  expectations that future release gates may rely on.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Fixture contract critic score 10, verdict
  PASS, Blocking findings: none. Runtime-boundary critic score 9, verdict PASS,
  Blocking findings: none. Maintenance compliance critic score 9, verdict PASS,
  Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Runtime-boundary critic was 9 because the smoke
  validates a fixture contract rather than executing Claude Code `/init-harness`;
  no backlog item added because the runtime execution follow-up remains listed
  above. Maintenance compliance critic was 9 because review used documented
  sequential fallback rather than independent sub-agents; no backlog item added
  because the residual risk is process-level review independence in this
  session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: true Claude Code slash-command execution and hook
  runtime activation remain future work.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 4. P1 preserve verifier exit status in init-harness examples

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-02
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_verify_examples.py
- backlog/claude-adapter.md

Source review: 2026-05-02 multi-review MIXED.

The `/init-harness` seeded `search-set.md` examples pipe verifier output through
`tail` and then print `$?`. In common shell behavior this can report the status
of `tail` or `echo` rather than the actual verifier, allowing failing commands
to look successful in the regression loop.

Original improvement:

- Rewrite the TypeScript, Python, and Godot verify examples in
  `adapters/claude/commands/init-harness.md` so they preserve the verifier exit
  status while still limiting output.
- Add a small test or fixture that proves failing verifier examples exit
  non-zero after output truncation.
- Keep `commands/init-harness.md` synchronized through compatibility mirror
  checks.

Decision implemented:

- The TypeScript, Python, and Godot seed verify examples now redirect verifier
  output to a temporary file, save the verifier status, print only the tail of
  the captured output, print `EXIT: <status>`, and exit with the saved status.
- `commands/init-harness.md` was updated with the same examples as the
  compatibility mirror.
- `tests/test_claude_init_harness_verify_examples.py` extracts the documented
  examples, runs them with failing fake `tsc`, `pytest`, and `godot`
  executables, and asserts the shell command exits with the verifier's failing
  status after output truncation.
- The focused test also asserts the canonical command and compatibility mirror
  contain the same seed verify examples.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`,
  `commands/init-harness.md`,
  `tests/test_claude_init_harness_verify_examples.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_init_harness_verify_examples.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, `git diff --check`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes seeded verifier examples
  that future harness search-set entries may rely on.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Exit-status preservation critic score 10,
  verdict PASS, Blocking findings: none. Output-truncation behavior critic
  score 10, verdict PASS, Blocking findings: none. Compatibility mirror and
  focused-test critic score 10, verdict PASS, Blocking findings: none.
  Maintenance compliance critic score 9, verdict PASS, Blocking findings:
  none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 5. P2 add Claude trace-root evidence selection for migrated projects

Source review: 2026-05-02 multi-review MIXED.

Claude `/init-harness` currently creates and orients around `.claude/traces/`.
When a migrated project already has meaningful `.harness/traces/` history, this
can split trace history and hide previous failures, search-set cases, or
experiment episodes.

Potential improvement:

- Add evidence-based trace-root selection or migration guidance to
  `adapters/claude/commands/init-harness.md` for projects that already contain
  meaningful `.harness/traces/` history.
- Define when Claude should reuse, migrate, or explicitly report uncertainty
  instead of blindly initializing a separate `.claude/traces/` root.
- Keep `commands/init-harness.md` synchronized through compatibility mirror
  checks.

### 6. P2 harden Claude autoresearch protected-file hooks

Source review: 2026-05-02 multi-review MIXED.

The Claude autoresearch Bash hook guidance appears easier to bypass than the
Codex checker, especially for pathlib/open variants and less obvious mutating
modes. This leaves the fixed-evaluator boundary uneven across adapters.

Potential improvement:

- Strengthen `adapters/claude/skills/autoresearch/SKILL.md` hook guidance or
  templates to cover pathlib/open write variants and write-capable modes.
- Add focused smoke or unit coverage for representative bypass patterns.
- Keep mirrored `skills/autoresearch/SKILL.md` synchronized through
  compatibility mirror checks.
