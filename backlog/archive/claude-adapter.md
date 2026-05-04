# Claude Adapter Backlog Archive

Completed backlog records moved from the active backlog file. Preserve full Completion Gate, review score, VETO, search-set, and residual-risk records here.

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

- Backlog status: `완료`.
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

- Backlog status: `완료`.
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

- Backlog status: `완료`.
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

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-02
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

Source review: 2026-05-02 multi-review MIXED.

Claude `/init-harness` currently creates and orients around `.claude/traces/`.
When a migrated project already has meaningful `.harness/traces/` history, this
can split trace history and hide previous failures, search-set cases, or
experiment episodes.

Original improvement:

- Add evidence-based trace-root selection or migration guidance to
  `adapters/claude/commands/init-harness.md` for projects that already contain
  meaningful `.harness/traces/` history.
- Define when Claude should reuse, migrate, or explicitly report uncertainty
  instead of blindly initializing a separate `.claude/traces/` root.
- Keep `commands/init-harness.md` synchronized through compatibility mirror
  checks.

Decision implemented:

- `adapters/claude/commands/init-harness.md` now requires Step 3 to select the
  active trace root before writing new traces.
- Claude defaults to `.claude/traces/`, but must also inspect existing
  `.harness/traces/` for meaningful migrated history.
- Meaningful history is defined as Active search-set cases, unresolved
  failures, non-template evolution entries, experiment episodes, or recent
  project-specific trace content; empty directories, `.keep` files, and
  untouched templates do not count.
- If `.harness/traces/` has meaningful history and `.claude/traces/` is absent,
  empty, or template-only, `/init-harness` must reuse that history as the
  source of truth by migrating/copying it into `.claude/traces/` or explicitly
  recording `.harness/traces/` as the temporary active root.
- If both roots have divergent meaningful history, `/init-harness` must stop
  and report uncertainty with a migration plan before writing new traces.
- The completion checklist now requires evidence-based active-root selection.
- `commands/init-harness.md` was synchronized as the compatibility mirror.
- `tests/test_claude_init_harness_fixture.py` now asserts the migrated
  trace-root selection guidance exists in the canonical command and mirror.

Remaining follow-up work:

- True Claude Code slash-command execution and hook runtime activation remain
  future work from item 3; this item only locks the documented output contract.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`,
  `commands/init-harness.md`, `tests/test_claude_init_harness_fixture.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_init_harness_fixture.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, `git diff --check`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Claude init trace-root and
  migration behavior that affects future trace reuse.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Trace-root selection semantics critic
  score 10, verdict PASS, Blocking findings: none. Compatibility mirror critic
  score 10, verdict PASS, Blocking findings: none. Fixture coverage critic
  score 9, verdict PASS, Blocking findings: none. Maintenance compliance critic
  score 9, verdict PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Fixture coverage critic was 9 because the test
  validates documented command policy rather than executing Claude Code
  `/init-harness`; no backlog item added because true slash-command execution
  remains listed in item 3 follow-up work. Maintenance compliance critic was 9
  because review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: true Claude Code slash-command execution and hook
  runtime activation remain future work.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 6. P2 harden Claude autoresearch protected-file hooks

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-02
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_hook_guidance.py
- backlog/claude-adapter.md

Source review: 2026-05-02 multi-review MIXED.

The Claude autoresearch Bash hook guidance appears easier to bypass than the
Codex checker, especially for pathlib/open variants and less obvious mutating
modes. This leaves the fixed-evaluator boundary uneven across adapters.

Original improvement:

- Strengthen `adapters/claude/skills/autoresearch/SKILL.md` hook guidance or
  templates to cover pathlib/open write variants and write-capable modes.
- Add focused smoke or unit coverage for representative bypass patterns.
- Keep mirrored `skills/autoresearch/SKILL.md` synchronized through
  compatibility mirror checks.

Decision implemented:

- `adapters/claude/skills/autoresearch/SKILL.md` now broadens the
  `protect-files-bash.sh` write-intent heuristic beyond simple
  `open(..., 'w')`.
- The documented Bash guard now covers common Python `open(..., mode=...)`,
  positional write modes, pathlib `Path(...).open(...)` write-capable modes,
  and pathlib `write_text` / `write_bytes` calls, while still treating the
  Bash hook as a heuristic layer rather than a parser.
- The guidance now explicitly keeps pre-commit/CI protected-file diff checks as
  the hard protection layer.
- The smoke guidance now includes redirect, pathlib `open('r+')`, keyword
  `open(file=..., mode='w')`, and read-only `mode='r'` examples with expected
  outcomes.
- `skills/autoresearch/SKILL.md` was synchronized as the compatibility mirror.
- `tests/test_claude_autoresearch_hook_guidance.py` extracts the documented
  `WRITE_VERBS` regex and checks representative bypass/read-only patterns
  against `grep -E`, plus verifies canonical/mirror guidance alignment.

Remaining follow-up work:

- none.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/autoresearch/SKILL.md`,
  `skills/autoresearch/SKILL.md`,
  `tests/test_claude_autoresearch_hook_guidance.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_autoresearch_hook_guidance.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, `git diff --check`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes fixed-evaluator protection
  guidance for the Claude adapter.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review;
  no critic scored below 9.
- Reviewer scores and VETO handling: Bypass-pattern coverage critic score 9,
  verdict PASS, Blocking findings: none. Heuristic-boundary clarity critic
  score 10, verdict PASS, Blocking findings: none. Compatibility mirror and
  focused-test critic score 10, verdict PASS, Blocking findings: none.
  Maintenance compliance critic score 9, verdict PASS, Blocking findings:
  none. No VETO triggered.
- For each score 9, why not 10: Bypass-pattern coverage critic was 9 because
  the Claude Bash hook remains a documented heuristic, not a shell/Python
  parser; no backlog item added because the guidance explicitly keeps
  pre-commit/CI diff protection as the hard layer and no repository runtime
  parser exists for Claude hooks yet. Maintenance compliance critic was 9
  because review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: Claude Bash hook detection remains heuristic by
  design; hard fixed-evaluator protection still depends on pre-commit/CI diff
  checks and runtime hook activation coverage remains future work from item 3.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 7. P1 preserve verifier exit status in Claude hook recipes

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_verify_examples.py
- backlog/claude-adapter.md

Source review: 2026-05-03 candidate triage.

The seeded `search-set.md` verify examples preserve verifier exit status, but
the Claude `/init-harness` hook recipe still recommends commands such as
`tsc --noEmit 2>&1 | tail -20` and `pytest -x -q 2>&1 | tail -15`. Without
`pipefail` or explicit status capture, the hook can observe `tail` success
instead of verifier failure, allowing a failing blocking hook to pass.

Decision implemented:

- The TypeScript, Python typed, and Python test hook recipe commands in
  `adapters/claude/commands/init-harness.md` now write verifier output to a
  temporary file, capture the verifier status, print the configured tail, and
  exit with the captured status.
- `commands/init-harness.md` stays synchronized as the compatibility mirror.
- `tests/test_claude_init_harness_verify_examples.py` now proves the hook
  recipe commands fail with the underlying verifier status and no longer use
  direct `2>&1 | tail` truncation.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`,
  `commands/init-harness.md`,
  `tests/test_claude_init_harness_verify_examples.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_init_harness_verify_examples.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`, `git diff --check`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Claude adapter hook
  verification semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Hook exit-status preservation critic
  score 10, verdict PASS, Blocking findings: none. Output truncation and hook
  usability critic score 10, verdict PASS, Blocking findings: none.
  Compatibility mirror and focused-test critic score 10, verdict PASS,
  Blocking findings: none. Maintenance compliance critic score 9, verdict
  PASS, Blocking findings: none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: actual Claude Code runtime hook activation remains
  covered by the existing future runtime smoke follow-up; this item only proves
  the documented shell recipes preserve verifier status.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 8. P2 respect migrated active trace roots in Claude harness-engineer

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/harness-engineer/SKILL.md
- skills/harness-engineer/SKILL.md
- tests/test_claude_harness_engineer_trace_root.py
- backlog/claude-adapter.md

Source review: 2026-05-03 candidate triage.

Claude `/init-harness` can now reuse or explicitly select meaningful
`.harness/traces/` history, but `adapters/claude/skills/harness-engineer/SKILL.md`
still hardcodes `.claude/traces/` for diagnosis, search-set verification,
Active-zero recovery, and trace recording. Migrated projects can still split or
ignore prior trace history during later harness evolution.

Decision implemented:

- Claude `harness-engineer` now selects the active trace root before trace
  reads or writes.
- `.claude/traces/` remains the default for normal Claude projects, while
  explicitly documented or evidence-selected `.harness/traces/` roots are
  respected for migrated projects.
- The skill defines evidence for active-root selection, including project
  guidance, Active search-set cases, unresolved failures, recent evolution
  entries, meaningful experiment episodes, and `/init-harness` migration notes.
- Divergent meaningful `.claude/traces/` and `.harness/traces/` histories now
  require stopping and reporting uncertainty with a migration plan before new
  traces are written.
- Procedural diagnosis, search-set, Active-zero, recording, and periodic review
  paths now use `{trace_root}` after selection.
- `tests/test_claude_harness_engineer_trace_root.py` locks the active-root
  contract and verifies the compatibility mirror carries the same markers.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/harness-engineer/SKILL.md`,
  `skills/harness-engineer/SKILL.md`,
  `tests/test_claude_harness_engineer_trace_root.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_harness_engineer_trace_root.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`, `git diff --check`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Claude adapter trace
  selection semantics for later harness evolution.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Active trace-root semantics critic score
  10, verdict PASS, Blocking findings: none. Migration-safety critic score 10,
  verdict PASS, Blocking findings: none. Compatibility mirror and lexical
  regression coverage critic score 10, verdict PASS, Blocking findings: none.
  Maintenance compliance critic score 9, verdict PASS, Blocking findings:
  none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: this is lexical skill-contract coverage, not actual
  Claude Code skill execution in a migrated fixture; future true runtime
  execution coverage remains out of scope until mechanically available.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 9. P2 add hard-layer protection guidance for Claude evaluator files

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_hard_layer_guidance.py
- backlog/claude-adapter.md

Source review: 2026-05-03 candidate triage.

The Claude autoresearch Bash guard is documented as heuristic and points to
pre-commit/CI diff protection as the hard layer, but setup guidance still only
installs Claude hooks and smoke-tests examples. Fixed-evaluator protection is
therefore weaker than the Codex adapter's checker-plus-gate pattern.

Decision implemented:

- Claude autoresearch setup now documents a project-local hard-layer Git diff
  check for protected evaluator files and dependencies.
- The guidance distinguishes Claude tool hooks as fast local warning/blocking
  layers from the pre-commit/CI diff check as the hard protection layer.
- The documented script reads `.claude/autoresearch-protected.txt`, rejects
  staged protected-path edits in pre-commit mode, and supports CI range checks
  through `BASE_REF`.
- The guidance includes pre-commit wiring, CI base-ref expectations, and smoke
  expectations for protected evaluator edits versus mutable genome edits.
- `tests/test_claude_autoresearch_hard_layer_guidance.py` extracts the
  documented shell template and verifies it blocks a staged `evaluate.py` edit
  while allowing a staged mutable `genome.py` edit.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/autoresearch/SKILL.md`,
  `skills/autoresearch/SKILL.md`,
  `tests/test_claude_autoresearch_hard_layer_guidance.py`, and
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS; `python3 -m unittest tests/test_claude_autoresearch_hard_layer_guidance.py`, `python3 -m unittest tests/test_claude_autoresearch_hook_guidance.py`, `python3 scripts/check-compat-mirrors.py`, `python3 scripts/check-claude-adapter-paths.py`, `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`, `git diff --check`, `python3 scripts/check-maintenance-review.py`, `python3 -m unittest discover -s tests`, `python3 -m unittest discover -s adapters/claude/tests`, `python3 scripts/sync-codex-plugin.py --check`, `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`, `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`, `python3 adapters/codex/scripts/smoke-local-plugin.py`, `python3 -m unittest discover -s adapters/codex/tests`, and `sh .githooks/pre-commit`.
- Search-set verification: SKIPPED; this repository worktree has no
  `search-set.md`.
- Multi-review required: yes, because this changes Claude fixed-evaluator
  protection guidance and release-gate expectations for autoresearch projects.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling: Hard-layer protection semantics critic
  score 10, verdict PASS, Blocking findings: none. Runtime-overclaim boundary
  critic score 10, verdict PASS, Blocking findings: none. Documented-template
  smoke coverage critic score 10, verdict PASS, Blocking findings: none.
  Maintenance compliance critic score 9, verdict PASS, Blocking findings:
  none. No VETO triggered.
- For each score 9, why not 10: Maintenance compliance critic was 9 because
  review used documented sequential fallback rather than independent
  sub-agents; no backlog item added because the residual risk is process-level
  review independence in this session, not an actionable repository change.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: the hard-layer script is documented as a
  project-local template rather than installed by this repository into target
  projects; true Claude Code runtime hook activation coverage remains a
  separate future smoke concern.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 10. P2 align init-harness completion checklist with active trace root

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

Claude `/init-harness` can select or temporarily reuse meaningful
`.harness/traces/` history, but the completion verification checklist still
requires `.claude/traces/*`, `.claude/traces/search-set.md`,
`.claude/traces/evolution/001-initial-harness.md`, and
`.claude/traces/failures/*.md`. In a migrated project where `.harness/traces/`
is intentionally active, this can recreate a second trace tree and split future
history.

Potential improvement:

- Reword `adapters/claude/commands/init-harness.md` completion checks to use
  the selected active trace root instead of hardcoding `.claude/traces/` for
  trace infrastructure.
- Preserve `.claude/traces/` as the normal Claude default, but allow
  evidence-selected `.harness/traces/` completion when reuse is explicitly
  recorded.
- Add focused lexical or fixture coverage proving the completion checklist does
  not force `.claude/traces/` after intentional `.harness/traces/` reuse.

Decision:

- Updated `/init-harness` Step 7 and Completion Verification to use the
  selected `{trace_root}` for search-set, evolution, failures, and experiments
  checks instead of hardcoding `.claude/traces/`.
- Preserved `.claude/traces/` as the normal Claude default while allowing
  explicitly reused meaningful `.harness/traces/` history to satisfy completion.
- Updated the compatibility mirror `commands/init-harness.md`.
- Extended fixture coverage so the normal `.claude/traces/` project and a
  migrated `.harness/traces/` project both satisfy the init-harness output
  contract.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/claude/commands/init-harness.md`
  - `commands/init-harness.md`
  - `tests/test_claude_init_harness_fixture.py`
  - `backlog/claude-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_init_harness_fixture.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes Claude adapter initialization
  behavior and trace-root semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Active trace-root contract critic: 10/10 PASS; completion checks now use
    `{trace_root}` and preserve `.claude/traces/` as the default.
  - Migrated history safety critic: 10/10 PASS; fixture coverage proves
    intentionally reused `.harness/traces/` can complete without forcing a
    second `.claude/traces/` history.
  - Compatibility mirror critic: 10/10 PASS; mirror sync and path checks pass.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update,
    verification, search-set SKIPPED reason, and Completion Gate are recorded,
    with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 11. P2 make Claude autoresearch honor the active trace root

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_trace_root.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

The Claude `autoresearch` skill still hardcodes `.claude/traces/` for reject
preservation, experiment episodes, escalation failures, and numbering. That
conflicts with the newer trace-root rule that migrated projects may temporarily
keep `.harness/traces/` active, so raw experiment and failure history can still
split across roots.

Potential improvement:

- Update `adapters/claude/skills/autoresearch/SKILL.md` so Setup and Run Mode
  select an active trace root before writing failures, experiments, or
  escalation records.
- Use `{trace_root}` or equivalent wording for reject preservation, experiment
  episode timing, failure escalation, and numbering.
- Keep `.claude/traces/` as the Claude default, but respect documented
  `.harness/traces/` reuse for migrated projects.
- Add focused coverage that rejects hardcoded trace writes where active-root
  selection is required.

Decision:

- Added a Claude autoresearch Setup Mode step to select the active trace root
  before writing experiment episodes, failure diagnoses, or escalation records.
- Kept `.claude/traces/` as the default Claude root while allowing meaningful
  `.harness/traces/` migrated history to be reused as `{trace_root}` when
  `.claude/traces/` is absent, empty, or template-only.
- Reworded reject preservation, episode paths, numbering, escalation failures,
  and continuity references to use `{trace_root}`.
- Updated the root `skills/autoresearch` compatibility mirror.
- Added focused lexical coverage proving post-selection trace writes use
  `{trace_root}` and that canonical/mirror skill copies match.

Completion Gate:

- Backlog status: 완료
- Changed files:
  - `adapters/claude/skills/autoresearch/SKILL.md`
  - `skills/autoresearch/SKILL.md`
  - `tests/test_claude_autoresearch_trace_root.py`
  - `backlog/claude-adapter.md`
- Scope deviations: none.
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_trace_root.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; no repository `search-set.md` exists
  (`rg --files -g 'search-set.md'` returned no files).
- Multi-review required: yes; this changes Claude autoresearch trace-writing
  behavior and migration semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential
  review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Active trace-root contract critic: 10/10 PASS; Setup Mode now selects
    `{trace_root}` before writing traces and uses it for later trace writes.
  - Migrated history safety critic: 10/10 PASS; meaningful `.harness/traces/`
    history can be reused without silently splitting experiment/failure traces.
  - Compatibility mirror critic: 10/10 PASS; root skill mirror matches the
    canonical Claude adapter skill and compatibility mirror checks pass.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope update,
    verification, search-set SKIPPED reason, and Completion Gate are recorded,
    with nonindependent multi-review fallback called out.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review was sequential
    fallback in the parent context, not independent parallel critics. No
    backlog item added because this is session-surface residual risk, not
    repository work.
- Backlog items added from score-9 residual risk: none.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 12. P2 require Claude autoresearch hard-layer protection before setup completion

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_hard_layer_guidance.py
- backlog/claude-adapter.md

Source review: 2026-05-03 feedback triage.

The Claude `autoresearch` skill documents pre-commit/CI diff protection as the
hard evaluator-protection layer, but the Setup Completion Checklist only
requires the two Claude hooks and settings registration. A maintainer can
therefore mark Setup Mode complete while fixed-evaluator protection remains
heuristic-only.

Potential improvement:

- Update the Setup Completion Checklist in
  `adapters/claude/skills/autoresearch/SKILL.md` to require the documented
  hard-layer protected-file diff check, or an explicit skipped reason when the
  project cannot install it yet.
- Require a smoke result showing protected evaluator edits fail and mutable
  genome edits pass before Setup Mode is considered complete.
- Keep the two Claude hooks as fast local protection, but make clear they do
  not replace the hard pre-commit/CI layer.
- Add focused documentation tests so future edits do not remove this setup
  completion requirement.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/claude/skills/autoresearch/SKILL.md
  - skills/autoresearch/SKILL.md
  - tests/test_claude_autoresearch_hard_layer_guidance.py
  - backlog/claude-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_hard_layer_guidance.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; Claude autoresearch setup/protection semantics changed.
- Multi-review result: PASS by sequential `FALLBACK_NONINDEPENDENT` review.
- Reviewer scores and VETO handling:
  - Setup completion contract critic: 10/10 PASS; checklist now requires hard-layer install or explicit skipped reason plus smoke evidence before setup completion.
  - Hard-layer protection honesty critic: 10/10 PASS; Claude hooks are explicitly framed as fast local protection, not a replacement for the pre-commit/CI layer.
  - Compatibility mirror/test critic: 10/10 PASS; canonical and mirror skills carry the same new completion requirements and focused tests cover both paths.
  - Maintenance compliance critic: 9/10 PASS; no VETO. Reservation, Start Gate, scoped edits, verification, search-set skipped reason, and Completion Gate are present.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used the required sequential `FALLBACK_NONINDEPENDENT` form in this single-session run instead of independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the residual is procedural review independence, not an actionable repository defect for this item.
- Residual risk/follow-up: future externally reviewed passes may provide stronger independent critique, but no known implementation risk remains.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 13. P1 preserve raw evidence before Claude autoresearch REJECT revert

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-03
Scope:
- adapters/claude/skills/autoresearch/SKILL.md
- skills/autoresearch/SKILL.md
- tests/test_claude_autoresearch_reject_evidence.py
- backlog/claude-adapter.md

Source review: 2026-05-03 multi-review feedback.

`core/reference.md` requires preserving rejected candidate diffs and raw
evaluator output before revert/cleanup, but Claude autoresearch Run Mode still
summarizes the reject path as `REJECT -> git reset --hard HEAD~1 + log`. That
ordering can cause an executor to lose candidate source changes or raw
evaluator output before they are recorded in `experiments.jsonl` or
`{trace_root}` traces. The Codex autoresearch guidance states this ordering
more safely.

Potential improvement:

- Reword Claude autoresearch Run Mode so REJECT handling explicitly captures
  raw evaluator output and candidate diff before any reset/revert.
- Ensure the recorded evidence includes enough detail for future proposer
  search over rejected candidates, consistent with `core/reference.md`.
- Update the root `skills/autoresearch` mirror and add focused lexical coverage
  that rejects a revert-before-capture sequence.

Decision:

- Updated Claude autoresearch setup guidance so every REJECT captures the
  candidate diff and raw evaluator JSON into temporary evidence outside the
  rejected commit before any reset/revert.
- Replaced the unsafe Run Mode shorthand `REJECT -> git reset --hard HEAD~1 +
  log` with an ordered sequence: preserve JSON and diff outside the rejected
  commit, reset/revert, then append full evaluator result and rejection
  metadata to `experiments.jsonl` and write `{trace_root}` episode/failure
  evidence from the preserved evidence when triggers apply.
- Added an explicit safety note to stop with evidence already saved if the
  revert needs approval or is blocked by local policy, and not to rely on
  pre-revert appends to tracked files that a hard reset can erase.
- Updated the root `skills/autoresearch` compatibility mirror and added
  focused lexical tests that enforce capture-before-revert ordering and reject
  the previous revert-then-log shorthand.

Completion Gate:
- Backlog status: 완료
- Changed files:
  - adapters/claude/skills/autoresearch/SKILL.md
  - skills/autoresearch/SKILL.md
  - tests/test_claude_autoresearch_reject_evidence.py
  - backlog/claude-adapter.md
- Scope deviations: none
- Verification results:
  - PASS: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`
  - PASS: `python3 scripts/check-compat-mirrors.py`
  - PASS: `python3 scripts/check-maintenance-review.py backlog/claude-adapter.md`
  - PASS: `git diff --check`
  - PASS: `python3 scripts/check-claude-adapter-paths.py`
  - PASS: `python3 -m unittest discover -s adapters/claude/tests`
  - PASS: `python3 scripts/sync-codex-plugin.py --check`
  - PASS: `python3 adapters/codex/scripts/check-codex-hook-schema-drift.py`
  - PASS: `python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt`
  - PASS: `python3 adapters/codex/scripts/smoke-local-plugin.py`
  - PASS: `python3 scripts/check-codex-marketplace-metadata.py`
  - PASS: `python3 scripts/check-maintenance-review.py`
  - PASS: `python3 -m unittest discover -s tests`
  - PASS: `python3 -m unittest discover -s adapters/codex/tests`
  - PASS: `sh .githooks/pre-commit`
- Search-set verification: SKIPPED; `rg --files -g 'search-set.md'` found no repository search-set file, so there is no defined search-set target to run.
- Multi-review required: yes; this changes Claude autoresearch run-mode evidence preservation semantics.
- Multi-review result: PASS through `FALLBACK_NONINDEPENDENT` sequential review; no critic scored below 9.
- Reviewer scores and VETO handling:
  - Evidence ordering critic: 10/10 PASS; REJECT handling now preserves raw evaluator JSON and candidate diff before any reset/revert.
  - Trace reuse critic: 10/10 PASS; rejection evidence is recorded in `experiments.jsonl` and `{trace_root}` episode/failure traces when triggers apply, preserving future proposer search material.
  - Mirror/test critic: 10/10 PASS; canonical and root mirror skills match, and focused tests reject the old reset-then-log shorthand.
  - Maintenance compliance critic: 9/10 PASS; Start Gate, scope, full verification, search-set SKIPPED reason, multi-review record, and Completion Gate are present.
  - VETO handling: no reviewer score below 9; no VETO.
- For each score 9, why not 10:
  - Maintenance compliance critic: not 10 because multi-review used documented sequential fallback in the parent context rather than independent sub-agent critics.
- Backlog items added from score-9 residual risk: none; the score-9 reason is session review independence, not an actionable repository defect.
- Residual risk/follow-up: none.
- Accepted: yes; accepted by maintainer review and ready for commit.

### 14. P2 align Claude init sub-agent trigger wording with core isolation policy

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- backlog/claude-adapter.md

Start Gate:

- Selected item: `backlog/claude-adapter.md` item 14, align Claude init
  sub-agent trigger wording with core isolation policy.
- Status block added: yes, item 14 marked `진행중`.
- Harness-affecting: yes; Claude init guidance changes adapter
  methodology/runtime boundary behavior.
- Multi-review required: yes; this changes adapter behavior and core
  methodology boundary semantics.
- Minimum verification commands: `python3 scripts/check-compat-mirrors.py`;
  `python3 scripts/check-claude-adapter-paths.py`; `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`; `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; `python3
  scripts/check-search-set-evidence.py`; `python3 scripts/run-search-set.py`;
  `python3 scripts/verify-release.py --skip-clean-worktree`; `git diff
  --check`.
- Expected scope: Claude init-harness canonical command, root compatibility
  mirror, focused Claude init fixture tests, and this backlog record.

Source review: 2026-05-04 adapter/plugin alignment critic in the current-main
methodology multi-review.

The shared core now says only two methodology-level isolation triggers belong in
the core: qualitative multi-perspective judgment and evaluator independence.
Generic parallel exploration, context firewalls, model routing, and exact
sub-agent thresholds are runtime policy. Claude `/init-harness` mostly respects
that boundary, but still refers to "three trigger categories" and says "Prefer
over-invoking to under-invoking" for sub-agent triggers. That can make the Claude
adapter sound broader than the core policy, especially for trivial or generic
sub-agent use.

Potential improvement:

- Reword `adapters/claude/commands/init-harness.md` so methodology-level
  sub-agent guidance names the two core isolation triggers and treats any extra
  Claude-specific routing as runtime policy.
- Remove or qualify "Prefer over-invoking to under-invoking" so it does not
  override the core anti-pattern against trivial sub-agent use.
- Keep Claude-specific tactical guidance where it belongs, but make the
  core-vs-adapter boundary explicit.
- Update compatibility mirror `commands/init-harness.md` and focused path/docs
  tests if wording changes.

Done when:

- Claude init guidance cannot be read as adding a third paper/core
  methodology-level sub-agent trigger.
- Claude-specific sub-agent tactics are clearly runtime policy, not paper-core
  Meta-Harness claims.
- Mirror/path checks pass after the wording update.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the
  first edit happened after focused baseline checks only. Focused baseline gates
  passed: `python3 scripts/check-compat-mirrors.py`, `python3
  scripts/check-claude-adapter-paths.py`, `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`, `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`, and `python3
  scripts/check-search-set-evidence.py` before the evidence record was needed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Updated Claude `/init-harness` guidance to name the two core isolation
  triggers: multi-review for qualitative judgment and Fixed Evaluator for
  evaluator independence.
- Reframed generic parallel Explore/context firewall usage as Claude Code
  runtime tactics, not harness methodology, and bounded them to material
  independence or bounded parallel work.
- Removed the old "Prefer over-invoking to under-invoking" and "three trigger
  categories" wording from the canonical command and compatibility mirror.
- Added focused tests that pin the two-trigger/runtime-policy boundary and
  reject the legacy phrases in both canonical and mirror command files.

Multi-review:

- Methodology-boundary critic: score 9/10, PASS. Blocking findings: none. Why
  not 10: the first revision still had a broad "context isolation and tactical
  decision support" sentence; fixed in this item by narrowing temporary
  subagents to bounded runtime tactics.
- Mirror/test enforceability critic: score 8/10, VETO. Blocking findings:
  mirror-specific tests did not reject the legacy phrases in the root mirror;
  not accepted.
- Process-compliance critic: score 9/10, PASS. Blocking findings: none. Why not
  10: the backlog record initially lacked explicit Start Gate fields; fixed in
  this item by adding the full Start Gate.
- Score handling: the score below 9 was treated as VETO. The mirror/test VETO
  was fixed by adding forbidden-phrase assertions for the mirror. The
  methodology-boundary score-9 concern was fixed by narrowing the broad
  subagent allowance. The process score-9 concern was fixed by recording the
  full Start Gate.
- Affected methodology-boundary critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Affected mirror/test critic rerun: score 10/10, PASS. Blocking findings:
  none.
- Affected process-compliance critic rerun: score 10/10, PASS. Blocking
  findings: none.
- Rerun status: all affected critics reran; final scores are 10/10, 10/10, and
  10/10 PASS.
- Follow-up/residual risk: none; actionable score-9 reasons were handled in
  this item.
- Final acceptance: accepted after VETO fix and affected critic reruns.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`,
  `commands/init-harness.md`, `tests/test_claude_init_harness_fixture.py`,
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_claude_init_harness_fixture.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-claude-adapter-paths.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation with reason
    above; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Claude adapter behavior and
  core-methodology boundary semantics.
- Multi-review result: PASS after three-critic multi-review, VETO fix, and
  affected critic reruns.
- Reviewer scores and VETO handling: methodology-boundary critic 9/10 PASS
  rerun to 10/10 PASS; mirror/test enforceability critic 8/10 VETO fixed and
  rerun to 10/10 PASS; process-compliance critic 9/10 PASS rerun to 10/10 PASS.
- For each score-9 result, why not 10:
  - Methodology-boundary critic: not 10 because broad temporary-subagent wording
    still remained; fixed in this item and rerun to 10/10 PASS.
  - Process-compliance critic: not 10 because Start Gate fields were not
    recorded in the backlog item yet; fixed in this item and rerun to 10/10
    PASS.
- Backlog items added from score-9 residual risk: none; all actionable score-9
  reasons were fixed here.
- Residual risk/follow-up: none.
- Accepted: yes.

### 15. P2 align Claude multi-review threshold with repository governance

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/skills/multi-review/SKILL.md
- skills/multi-review/SKILL.md
- tests/test_claude_multi_review_skill.py
- backlog/claude-adapter.md

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

`MAINTENANCE.md` treats repository governance reviews below score 9 as VETO, and
the Codex multi-review skill has a governance mode for that local release
discipline. The Claude `multi-review` skill still marks all critics scoring at
least 7 with no veto as PASS. Claude-side maintainers can therefore accept
methodology, adapter, hook, or release-gate decisions under a weaker local rule
than this repository now requires.

Potential improvement:

- Add a repository-governance mode or explicit note to the Claude multi-review
  skill: when reviewing this repository's maintenance, harness-affecting changes,
  release gates, or durable adapter contracts, scores below 9 are VETO.
- Preserve the generic 7/10 PASS threshold only for non-governance qualitative
  reviews if that remains useful.
- Update the root compatibility mirror for the Claude skill and any focused
  tests or mirror checks affected by the wording.

Done when:

- Claude-side multi-review guidance cannot approve repository governance work
  with a critic score below 9.
- The generic multi-review threshold and repository release discipline are
  clearly separated.
- Compatibility mirror checks pass after the update.

Search-set verification:

- BEFORE: SKIPPED full Active search-set before implementation because the
  first edit happened after focused baseline checks only. Focused baseline gates
  passed: `python3 scripts/check-compat-mirrors.py`, `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`, and `python3
  scripts/check-search-set-evidence.py` before the evidence record was needed.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Added a `Repository Governance Mode` section to the Claude multi-review skill
  so repository maintenance, harness-affecting changes, release gates, hook
  semantics, core methodology boundaries, and durable adapter contracts apply
  this repository's local release discipline.
- The Claude skill now says any reviewer or Critic score below 9 is VETO until
  the blocking finding is fixed and the affected Critic reruns to at least 9.
- Preserved the generic 7/10 PASS threshold only for non-governance qualitative
  reviews where repository maintenance policy is not the acceptance contract.
- Updated the root compatibility mirror and added focused tests for the
  governance mode, generic threshold separation, and mirror equality.

Multi-review:

- Governance semantics critic: score 10/10, PASS. Blocking findings: none.
- Mirror/test enforceability critic: score 9/10, PASS. Blocking findings: none.
  Why not 10: tests are lexical guardrails rather than a semantic parser of the
  full verdict table; accepted as residual risk because this matches the
  repository's focused policy-boundary test style.
- Process-compliance critic: score 9/10, PASS. Blocking findings: none. Why not
  10: final Completion Gate and acceptance record still needed to be written at
  report time; addressed by this Completion Gate.
- Score handling: no reviewer score below 9; no VETO.
- Rerun status: no VETO, so no affected critic rerun required.
- Follow-up/residual risk: accepted lexical-test limitation; procedural
  final-closure timing addressed by this Completion Gate.
- Final acceptance: accepted after three-critic multi-review.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/multi-review/SKILL.md`,
  `skills/multi-review/SKILL.md`, `tests/test_claude_multi_review_skill.py`,
  `backlog/claude-adapter.md`.
- Scope deviations: none.
- Verification results: PASS `python3 -m unittest
  tests/test_claude_multi_review_skill.py`; PASS `python3
  scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: SKIPPED full Active search-set before implementation with reason
    above; focused baseline gates passed.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes; this changes Claude adapter review-contract
  semantics.
- Multi-review result: PASS after three-critic multi-review; no VETO.
- Reviewer scores and VETO handling: governance semantics critic 10/10 PASS;
  mirror/test enforceability critic 9/10 PASS; process-compliance critic 9/10
  PASS; no score below 9 and no VETO.
- For each score-9 result, why not 10:
  - Mirror/test enforceability critic: not 10 because tests are lexical
    guardrails rather than a semantic parser of the full verdict table; accepted
    as residual risk for this focused wording boundary.
  - Process-compliance critic: not 10 because final Completion Gate and
    acceptance record still needed to be written at report time; addressed by
    this Completion Gate.
- Backlog items added from score-9 residual risk: none; lexical guardrail
  limitation is accepted as residual risk, and procedural final-closure timing
  was handled here.
- Residual risk/follow-up: accepted lexical-test limitation.
- Accepted: yes.

### 16. P2 align Claude init search-set template with core reference schema

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/commands/init-harness.md
- commands/init-harness.md
- tests/test_claude_init_harness_fixture.py
- tests/test_claude_init_harness_verify_examples.py
- backlog/claude-adapter.md

Start Gate:

- Selected item: `backlog/claude-adapter.md` item 16, align Claude init
  search-set template with core reference schema.
- Status block added: yes, item 16 marked `진행중`.
- Harness-affecting: yes; this changes Claude initialization trace/search-set
  schema behavior.
- Multi-review required: yes; this changes Claude initialization and trace
  schema behavior.
- Minimum verification commands: `python3 scripts/check-compat-mirrors.py`;
  `python3 scripts/check-claude-adapter-paths.py`; `python3 -m unittest
  tests/test_claude_init_harness_fixture.py
  tests/test_claude_init_harness_verify_examples.py`; `python3 -m unittest
  discover -s adapters/claude/tests`; `python3 scripts/check-maintenance-review.py
  backlog/claude-adapter.md`; `python3 scripts/check-search-set-evidence.py`;
  `python3 scripts/run-search-set.py`; `python3 scripts/verify-release.py
  --skip-clean-worktree`; `git diff --check`.
- Expected scope: Claude init command canonical source, root compatibility
  mirror, focused Claude init fixture/verify tests, and this backlog record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The shared reference schema for `search-set.md` uses Active entries with
`Source`, `Symptom`, and executable `verify` fields. The Claude `/init-harness`
surface still seeds or describes a different shape in places, including legacy
fields such as `ref`. That can make Claude-initialized projects less aligned
with the provider-neutral trace/search-set contract and harder to migrate into
`.harness/traces/`.

Potential improvement:

- Update `adapters/claude/commands/init-harness.md` and the root compatibility
  mirror so new Claude projects seed the core `Source` / `Symptom` / `verify`
  Active-entry shape.
- Preserve backward-compatible reading guidance for older Claude projects if
  needed, but stop generating the legacy shape for new projects.
- Add or extend fixture coverage so Claude init output matches the shared
  reference schema and compatibility mirrors remain synchronized.

Done when:

- Claude `/init-harness` no longer generates or recommends a search-set shape
  that conflicts with `core/reference.md`.
- Existing Claude migration guidance remains clear for projects with older
  trace files.
- Focused Claude init tests and compatibility mirror checks pass.
- Multi-review checks the result because this changes Claude initialization and
  trace schema behavior.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 scripts/check-compat-mirrors.py`, `python3
  scripts/check-claude-adapter-paths.py`, `python3 -m unittest
  tests/test_claude_init_harness_fixture.py
  tests/test_claude_init_harness_verify_examples.py`, `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`, and `python3
  scripts/check-search-set-evidence.py`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Updated Claude `/init-harness` search-set template to generate shared
  `Source` / `Symptom` / `verify` Active entries.
- Removed new-template generation of the legacy `ref` field while documenting
  that older Claude projects may preserve legacy `ref` fields when reading or
  migrating history.
- Synchronized the root compatibility mirror at `commands/init-harness.md`.
- Strengthened focused fixture coverage so generated/reused Claude search-set
  examples require `Source`, `Symptom`, and executable `verify`, and so the
  canonical command and compatibility mirror do not generate `- **ref**:` in the
  new search-set template.
- After schema reviewer re-review, also removed the adjacent generated
  CLAUDE.md hardcoded `.claude/traces/failures/*.md` failure-escalation wording
  in favor of selected trace root wording.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/commands/init-harness.md`;
  `commands/init-harness.md`; `tests/test_claude_init_harness_fixture.py`;
  `backlog/claude-adapter.md`.
- Scope deviations: `tests/test_claude_init_harness_verify_examples.py` was in
  planned verification scope but did not require edits. `backlog/claude-adapter.md`
  also contains user-added item 17 context that was already adjacent in the
  selected backlog file. Unrelated dirty `backlog/README.md` remains outside
  this item and is not part of the selected scope.
- Verification results: PASS `python3 scripts/check-compat-mirrors.py`; PASS
  `python3 scripts/check-claude-adapter-paths.py`; PASS `python3 -m unittest
  tests/test_claude_init_harness_fixture.py
  tests/test_claude_init_harness_verify_examples.py`; PASS `python3 -m unittest
  discover -s adapters/claude/tests`; PASS `python3 scripts/check-maintenance-review.py
  backlog/claude-adapter.md`; PASS `python3 scripts/check-search-set-evidence.py`;
  PASS `python3 scripts/run-search-set.py`; PASS `python3 scripts/verify-release.py
  --skip-clean-worktree`; PASS `git diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes.
- Multi-review result: schema/trace-root critic VETO resolved and final PASS;
  tests/mirror critic PASS; process critic PASS.
- Reviewer scores and VETO handling: schema/trace-root critic initially 8/10
  VETO for hardcoded `.claude/traces/failures/`, fixed to `{trace_root}/failures/`,
  then 9/10 PASS for adjacent generated CLAUDE.md wording, then fixed and
  rerun to 10/10 PASS; tests/mirror critic initially 9/10 PASS for limited
  mirror equality, fixed with full canonical-vs-mirror equality assertion and
  rerun to 10/10 PASS; process critic initially 7/10 VETO because Completion
  Gate and final acceptance were not yet recorded, then rerun to 10/10 PASS
  after the Completion Gate was recorded.
- For each score 9, why not 10: schema/trace-root critic's temporary 9 was due
  to adjacent generated CLAUDE.md failure-escalation wording hardcoding
  `.claude/traces/failures/*.md`; fixed in this item. tests/mirror critic's
  temporary 9 was due to marker/count coverage rather than full equality; fixed
  in this item.
- Backlog items added from score-9 residual risk: none; both score-9 reasons
  were actionable in-scope fixes and were resolved before acceptance.
- Residual risk/follow-up: none.
- Accepted: yes.

### 17. P3 keep Claude diagnosis-only reviews from silently creating trace infrastructure

Status: 완료
Owner: Codex single-session maintenance pass
Branch: main
Started: 2026-05-04
Scope:
- adapters/claude/skills/harness-engineer/SKILL.md
- skills/harness-engineer/SKILL.md
- tests/test_claude_harness_engineer_trace_root.py
- backlog/claude-adapter.md

Start Gate:

- Selected item: `backlog/claude-adapter.md` item 17, keep Claude
  diagnosis-only reviews from silently creating trace infrastructure.
- Status block added: yes, item 17 marked `진행중`.
- Harness-affecting: yes; this changes Claude adapter harness-engineer runtime
  guidance.
- Multi-review required: yes; this changes adapter behavior and the
  diagnosis/application boundary.
- Minimum verification commands: `python3 -m unittest
  tests/test_claude_harness_engineer_trace_root.py`; `python3 -m unittest
  discover -s adapters/claude/tests`; `python3 scripts/check-claude-adapter-paths.py`;
  `python3 scripts/check-compat-mirrors.py`; `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; `python3
  scripts/check-search-set-evidence.py`; `python3 scripts/run-search-set.py`;
  `python3 scripts/verify-release.py --skip-clean-worktree`; `git diff --check`.
- Expected scope: Claude harness-engineer skill canonical source, root
  compatibility mirror, focused trace-root boundary test, and this backlog
  record.

Source review: 2026-05-04 multi-review of local `main` against the
Meta-Harness methodology.

The core methodology says applied harness changes may create missing minimum
trace surfaces, while diagnosis-only work should report missing trace
infrastructure instead of silently expanding the project. The Claude
`harness-engineer` skill still contains wording that can be read as creating the
trace directory whenever it is missing, even for review or diagnosis-only
sessions.

Potential improvement:

- Reword the Claude `harness-engineer` skill so diagnosis-only or proposal-only
  work reports missing trace infrastructure without mutating the project.
- Keep applied harness evolution behavior intact: when the user asks to apply a
  harness change, create the missing minimum trace surface before writing new
  traces.
- Add focused lexical or fixture coverage for the distinction between
  diagnosis-only reporting and applied trace initialization.

Done when:

- Claude harness-engineer guidance matches the core diagnosis-only boundary.
- Applied harness changes can still initialize the minimum trace surface when
  appropriate.
- Compatibility mirror checks and focused Claude adapter tests pass.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py`; focused baseline gates
  passed: `python3 -m unittest tests/test_claude_harness_engineer_trace_root.py`,
  `python3 scripts/check-claude-adapter-paths.py`, and `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`.
- AFTER: PASS `python3 scripts/run-search-set.py`.

Decision implemented:

- Clarified the Claude harness-engineer mode boundary: diagnosis-only,
  review-only, and proposal-only work reports missing trace infrastructure
  without creating directories or files.
- Preserved applied harness evolution behavior by allowing creation of the
  missing minimum trace surface only when the user asks to apply a harness
  change.
- Synchronized the root compatibility mirror at
  `skills/harness-engineer/SKILL.md`.
- Added focused coverage for the diagnosis-only no-mutation boundary, applied
  setup wording, legacy `(create directory if missing)` removal, and mirror
  marker/count synchronization.

Completion Gate:

- Backlog status: `완료`.
- Changed files: `adapters/claude/skills/harness-engineer/SKILL.md`;
  `skills/harness-engineer/SKILL.md`;
  `tests/test_claude_harness_engineer_trace_root.py`;
  `backlog/claude-adapter.md`.
- Scope deviations: `skills/harness-engineer/SKILL.md` was added to Scope
  before editing because the selected change had to keep the root compatibility
  mirror synchronized. Unrelated dirty `backlog/README.md` remains outside this
  item and will not be staged or committed with item 17.
- Verification results: PASS `python3 -m unittest
  tests/test_claude_harness_engineer_trace_root.py`; PASS `python3 -m unittest
  discover -s adapters/claude/tests`; PASS `python3 scripts/check-claude-adapter-paths.py`;
  PASS `python3 scripts/check-compat-mirrors.py`; PASS `python3
  scripts/check-maintenance-review.py backlog/claude-adapter.md`; PASS `python3
  scripts/check-search-set-evidence.py`; PASS `python3 scripts/run-search-set.py`;
  PASS `python3 scripts/verify-release.py --skip-clean-worktree`; PASS `git
  diff --check`.
- Search-set verification:
  - BEFORE: PASS `python3 scripts/run-search-set.py`.
  - AFTER: PASS `python3 scripts/run-search-set.py`.
- Multi-review required: yes.
- Multi-review result: semantics critic PASS; tests/mirror critic PASS after
  score-9 coverage improvement; process critic PASS after VETO and score-9
  completion-wording fixes.
- Reviewer scores and VETO handling: semantics critic 10/10 PASS; tests/mirror
  critic initially 9/10 PASS because the focused unit test rejected the legacy
  `(create directory if missing)` phrase only in the canonical skill and relied
  on the mirror gate for the compatibility mirror, then fixed with a direct
  mirror forbidden-phrase assertion and rerun to 10/10 PASS; process critic
  initially 8/10 VETO because Start Gate was not recorded in the backlog item,
  the unrelated dirty `backlog/README.md` was not explicitly handled, and
  Completion Gate was not yet recorded, then rerun to 9/10 PASS because final
  acceptance still said the process rerun was pending.
- For each score 9, why not 10: tests/mirror critic's temporary 9 was due to
  mirror forbidden-phrase coverage relying on the separate compatibility mirror
  gate rather than the focused unit test; fixed in this item. Process critic's
  temporary 9 was due to final Completion Gate wording still saying process
  rerun and acceptance were pending; fixed in this item.
- Backlog items added from score-9 residual risk: none; the score-9 reason was
  an actionable in-scope test/process-record improvement and was resolved
  before acceptance.
- Residual risk/follow-up: none.
- Accepted: yes.
