# Plan 12: Strategy Search Loop MVP

## Purpose

Plan 12 adds the missing paper-shaped Meta-Harness layer above the v2
governance substrate: a reproducible loop for proposing, evaluating, recording,
and selecting candidate harness strategies.

Plan 12 does not replace v2 acceptance. It produces candidate diffs and
evaluation records. Any accepted candidate still enters the v2 governance path:
content commit, AcceptancePacket, evidence/review import when required, active
pointer publication, and release verification.

## Product Boundary

Plan 12 is about search, not release acceptance.

- Search layer: explores candidate harness strategies under a fixed evaluator.
- Governance layer: decides whether an adopted candidate is stable handoff
  evidence.
- Candidate scores are recommendations, not governance PASS.
- Candidate traces are search evidence, not active archive publication evidence
  unless later bound by an AcceptancePacket.

## Target Flow

```text
direction.yml
  -> candidate worktree
  -> apply candidate patch or proposer change
  -> fixed evaluator
  -> score + stdout/stderr + trace record
  -> next candidate or selected candidate
  -> v2 governance adoption path
```

The MVP starts with a manual candidate loop. Automated proposer integration is a
later step after the direction schema, evaluator immutability checks, and
candidate run store are stable.

## Core Concepts

### Direction

A direction fixes the search objective and allowed mutation boundary.

Required fields:

```yaml
schema_version: strategy-search-direction/v1
direction_id: init-codex-harness-trace-root
objective: Improve trace-root selection in generated Codex harness projects.
base_ref: <full commit sha>
search_surface:
  - adapters/codex/skills/init-codex-harness/SKILL.md
  - adapters/codex/skills/init-codex-harness/assets/AGENTS.md.template
protected_evaluator_paths:
  - benchmarks/init-codex-harness/
  - tests/test_claude_init_harness_fixture.py
evaluator:
  command: python3 benchmarks/init-codex-harness/run_cases.py
  timeout_seconds: 120
  protected_paths:
    - benchmarks/init-codex-harness/
    - tests/test_claude_init_harness_fixture.py
    - scripts/score-init-codex-harness.py
  oracle_paths:
    - benchmarks/init-codex-harness/expected/
  score_parser_paths:
    - scripts/score-init-codex-harness.py
success:
  min_score: 0.95
  max_regressions: 0
notes: []
```

Rules:

- `search_surface` is the only mutable target for candidate patches.
- `protected_evaluator_paths` is a shorthand for the evaluator closure, and
  `evaluator.protected_paths`, `evaluator.oracle_paths`, and
  `evaluator.score_parser_paths` are the explicit dependency closure used by
  the runner.
- All evaluator closure paths are immutable during candidate evaluation.
- Direction changes start a new search run or explicitly invalidate previous
  score comparisons.
- `base_ref` is a full commit SHA, not a moving branch name, so candidate
  replay identity has an immutable baseline.

### Candidate Run Store

Candidate runs are durable search traces under `.harness/search-runs/`.

```text
.harness/search-runs/<run-id>/
  direction.yml
  run.yml
  scores.jsonl
  proposals.jsonl
  proposals/
    cand-001/
      public-context.yml
      policy.yml
      prompt.md
      patch.diff
      proposal.yml
  candidates/
    cand-001/
      patch.diff
      score.yml
      stdout.log
      stderr.log
      trace.yml
      trace.md
    cand-002/
      ...
  summary.yml
```

The run store is runner/operator diagnostic history. Proposers receive only the
public proposal bundle plus the allowed source surface; the full run store is
not an archive/v2 publication surface and is not proposer-readable evidence.

### Candidate Metadata

Every candidate must record enough identity to be replayed or audited.

Required candidate fields:

```yaml
schema_version: strategy-search-candidate/v1
candidate_id: cand-001
run_id: 2026-05-19-init-codex-harness
base_commit: <full commit sha>
direction_digest: <sha256>
search_surface_digest_before: <sha256 over listed source bytes>
patch_sha256: <sha256>
evaluator_command: python3 benchmarks/init-codex-harness/run_cases.py
evaluator_digest: <sha256 over evaluator protected/oracle/score-parser closure>
evaluator_closure:
  protected_paths:
    before_sha256: <sha256>
    after_sha256: <sha256>
  oracle_paths:
    before_sha256: <sha256>
    after_sha256: <sha256>
  score_parser_paths:
    before_sha256: <sha256>
    after_sha256: <sha256>
started_at: <iso timestamp>
finished_at: <iso timestamp>
exit_code: 0
score: 0.97
case_results:
  - case_id: fresh-empty-repo
    status: pass
stdout_sha256: <sha256>
stderr_sha256: <sha256>
verdict: pass
```

Rules:

- Candidate `score.yml` must name the exact evaluator command and digest.
- Candidate `score.yml` must preserve before/after digests for every evaluator
  closure group.
- stdout/stderr logs must match their recorded hashes.
- Candidate records must include case-level output when the evaluator can emit
  it.
- A candidate with missing metadata is diagnostic only and cannot be selected.
- Slice 1 validates candidate metadata and patch-declared paths. Slice 2's
  evaluator runner must additionally inspect the isolated candidate workspace
  for side-effect mutations outside `search_surface` and run-output paths.

### Fixed Evaluator Boundary

The evaluator boundary must be enforced mechanically.

Invalid candidate conditions:

- Patch touches any `protected_evaluator_paths`.
- Patch touches any `evaluator.protected_paths`, `evaluator.oracle_paths`, or
  `evaluator.score_parser_paths`.
- Patch touches hidden oracle, fixture expected output, sealed rubric, or score
  parser files.
- Evaluator command differs from the direction without creating a new run.
- Any evaluator closure digest changes between before and after evaluation.
- Candidate leaves dirty files outside `search_surface` and run-output paths.
- Candidate writes `archive/v2/` as part of evaluation.

The runner should report these as candidate-invalid, not as low-scoring
candidate passes.

### Isolation

Candidate evaluation runs outside the main working tree.

MVP isolation rules:

- Use a temporary Git worktree or equivalent copy rooted at the direction base
  commit.
- Apply candidate patches only inside the candidate workspace.
- Capture evaluator stdout/stderr and exit code.
- Enforce timeout.
- Clean up temporary worktrees by default unless `--keep-worktree` is requested.
- Never run `write-pointer`, `check-pointer`, `verify-release`, or active
  archive publication commands inside candidate evaluation.

### Selection and Adoption

Selection means "worth adopting", not "accepted".

Selected candidate requirements:

- Candidate passed evaluator or explicitly records why score is acceptable.
- Candidate did not mutate evaluator or protected paths.
- Candidate metadata is complete.
- Summary names residual risks and case-result counts, without publishing raw
  evaluator case IDs.
- Human/operator chooses whether to apply the patch to main.

Durability rule:

- Full `.harness/search-runs/` directories are diagnostic search history and
  are not required to be committed by default.
- When a candidate is selected, `select` writes only a public selection
  manifest and summary inside `.harness/search-runs/<run-id>/selections/`.
  Raw candidate `score.yml`, stdout/stderr logs, `trace.yml`, `trace.md`, and
  `patch.diff` remain diagnostic run-store history and are not archive
  publication artifacts.
- No strategy-search selection output is v2 stable evidence by itself.
  AcceptancePackets must not rely on `.harness/search-runs/` refs for stable
  handoff. The selected patch becomes real only when the operator applies it in
  a normal content commit, after which the normal v2 packet, review import,
  pointer publication, and release gate decide acceptance.

Adoption path:

```text
selected candidate patch
  -> apply to main or integration branch
  -> content commit
  -> v2 AcceptancePacket
  -> evidence/review import as required
  -> active pointer publication
  -> release verification
```

## CLI Sketch

Repository-local command surface can live under `scripts/strategy-search.py`
first. A later wrapper may expose `meta-harness search`.

Slice 1 commands:

```bash
python3 scripts/strategy-search.py validate-direction --direction directions/example.yml
python3 scripts/strategy-search.py validate-candidate --direction directions/example.yml --candidate .harness/search-runs/<run-id>/candidates/<candidate-id>/score.yml
```

Slice 2 commands:

```bash
python3 scripts/strategy-search.py start --direction directions/example.yml
python3 scripts/strategy-search.py eval --run .harness/search-runs/<run-id> --patch candidate.diff --candidate-id cand-001
python3 scripts/strategy-search.py summarize --run .harness/search-runs/<run-id>
```

Slice 3 trace/search-set options:

```bash
python3 scripts/strategy-search.py eval --run .harness/search-runs/<run-id> --patch candidate.diff --candidate-id cand-001 --why "try narrower trace-root heuristic" --next-hypothesis "compare against path-depth heuristic"
python3 scripts/strategy-search.py summarize --run .harness/search-runs/<run-id> --write-search-set
```

Later commands:

```bash
python3 scripts/strategy-search.py select --run .harness/search-runs/<run-id> --candidate cand-003
```

Slice 4 proposer commands:

```bash
python3 scripts/strategy-search.py propose --run .harness/search-runs/<run-id> --candidate-id cand-003
# Save the proposer-returned unified diff as:
# .harness/search-runs/<run-id>/proposals/cand-003/patch.diff
# The eval step seals that patch into proposal.yml and proposals.jsonl before running it.
python3 scripts/strategy-search.py propose --run .harness/search-runs/<run-id> --candidate-id cand-003 --patch candidate.diff
python3 scripts/strategy-search.py eval --run .harness/search-runs/<run-id> --proposal .harness/search-runs/<run-id>/proposals/cand-003/proposal.yml
```

Slice 5 adoption bridge command:

```bash
python3 scripts/strategy-search.py select --run .harness/search-runs/<run-id> --candidate cand-003
# Then apply the selected patch in a content commit and use the v2 AcceptancePacket,
# review import if required, active pointer publication, and release verification flow.
```

## Implementation Slices

### Slice 1: Direction and Candidate Schemas

Deliverables:

- Direction schema validator.
- Candidate score schema validator.
- Tests for missing required fields, invalid paths, and protected evaluator
  mutations.

Acceptance criteria:

- Invalid directions fail before worktree creation.
- Candidate records without replay identity are rejected.
- Docs explain that search scores are not governance acceptance.

### Slice 2: Manual Candidate Evaluation Runner

Deliverables:

- `start` creates `.harness/search-runs/<run-id>/direction.yml`.
- `eval` creates isolated candidate workspace, applies patch, runs evaluator,
  captures logs, computes score metadata, and rejects invalid mutations.
- `summarize` reports ranked candidates and invalid candidates.

Acceptance criteria:

- Candidate patches cannot touch protected evaluator paths.
- Candidate eval detects, rejects, and restores ordinary in-window main
  worktree dirtiness; full prevention of detached descendant writes is Plan 13.
- stdout/stderr hashes are recorded and validated.
- Timeout is enforced.

### Slice 3: Search-Set and Trace Integration

Deliverables:

- Candidate traces record why the candidate was tried, what changed, evaluator
  result, and next hypothesis.
- Optional search-set entries can be generated from recurring candidate
  failures.

Acceptance criteria:

- Search traces preserve raw evaluator output refs.
- Summary points to candidate traces, not only scalar scores.
- No trace output is treated as archive/v2 evidence.

### Slice 4: Proposer Integration

Deliverables:

- Prompt/policy for a proposer agent to inspect the public proposal bundle:
  direction summary, prior patches, sanitized trace summaries, and scores.
- Generated patch is stored before evaluation.
- Proposer may read the public proposal bundle and allowed source surface, but
  must not read raw trace files or edit evaluator files.
- `propose` creates a diagnostic-only public context bundle that omits evaluator
  command details, oracle contents, and run summary/search-set refs. The
  bundle lists only the objective, allowed `search_surface`, sanitized prior
  candidate summaries, explicit null run-ref fields, and patch policy.
- Proposal bundles are schema-closed and hash-bound in `proposal.yml` plus the
  run-level `proposals.jsonl` ledger before `eval --proposal` can run them.
  Prior invalid candidates are excluded from proposer context so protected path
  mistakes do not leak into the next proposer prompt.

Acceptance criteria:

- Proposer receives only the sanitized public context bundle and allowed source
  surface, not raw run-store refs or sealed oracle internals.
- Generated patch is evaluated by the same fixed evaluator.
- Failed proposer attempts remain useful diagnosis records.

### Slice 5: v2 Adoption Bridge

Deliverables:

- Selected candidate summary and selection manifest are diagnostic-only records
  under `.harness/search-runs/<run-id>/selections/`.
- `select` refuses archive/v2 output targets; the `.harness/search-runs/`
  store remains diagnostic history only.
- Governance docs explain how to move from search result to content commit and
  active pointer publication.

Acceptance criteria:

- Bridge does not auto-certify search PASS as stable handoff.
- Bridge refuses archive/v2 publication output for strategy-search selections.
- Protected/high-risk adopted candidates still require review import.
- Release verification remains the final publication gate.

## Multi-Review Seed

Required critic lenses:

- Methodology fidelity: verifies Plan 12 preserves source/score/trace search
  rather than becoming a generic CI wrapper.
- Evaluator-boundary critic: checks protected evaluator immutability and oracle
  leakage.
- Reproducibility critic: checks candidate metadata and replay identity.
- Isolation critic: checks worktree, timeout, cleanup, and no archive mutation.
- Governance-boundary critic: checks search results do not become acceptance
  evidence without v2 publication.
- Overfitting critic: checks benchmark-integrity and holdout limitations are
  documented.
- Operator-simplicity critic: checks MVP remains manual-first and inspectable.

Score policy:

- Any score below 9 blocks implementation.
- Any evaluator mutation or search-result-as-governance-PASS finding is P1.
- Semantic agent-in-loop quality claims remain out of scope until Slice 4 or
  later.

## Explicit Non-Goals

- No claim to reproduce the paper's benchmark gains.
- No fully autonomous strategy optimizer in the MVP.
- No package-manager distribution.
- No active archive/v2 publication from candidate workspaces.
- No hidden-oracle exposure to proposer agents.
- No claim that the MVP fully sandboxes detached descendants after evaluator
  exit or cryptographically anchors mutable proposal ledgers. Those are
  deferred to Plan 13.

## Validation Plan

Minimum validation for Slice 1 through Slice 4:

```bash
python3 -m unittest tests/test_strategy_search.py
python3 scripts/strategy-search.py validate-direction --direction <fixture>
python3 scripts/strategy-search.py validate-candidate --direction <fixture-direction> --candidate <fixture-score>
python3 scripts/strategy-search.py summarize --run <fixture-run> --write-search-set
python3 scripts/strategy-search.py propose --run <fixture-run> --candidate-id <candidate-id> --patch <candidate-patch>
python3 scripts/strategy-search.py eval --run <fixture-run> --proposal <fixture-run>/proposals/<candidate-id>/proposal.yml
python3 scripts/strategy-search.py select --run <fixture-run> --candidate <candidate-id>
git diff --check
```

Later validation:

```bash
python3 scripts/check-governance-acceptance.py capture-search-set --phase before --packet <packet-ref>
python3 scripts/check-governance-acceptance.py capture-search-set --phase after --packet <packet-ref>
# In-progress pointer-scoped validation only; final release verification must
# use the normal v2 release gate without copying --skip-clean-worktree as
# stable release evidence.
python3 scripts/verify-release.py --skip-clean-worktree --base-ref <last-publication> --pointer <pointer>
```

## Open Questions

- Should the first evaluator target existing adapter fixtures, multi-review
  perspective calibration, or a new small init-harness benchmark?
- What minimal case-level score format should evaluators emit so different
  benchmarks can share the same runner?
- Which paths count as hidden oracle material for each benchmark family?
