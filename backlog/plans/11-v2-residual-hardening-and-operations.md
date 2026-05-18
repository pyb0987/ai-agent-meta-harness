# Plan 11: v2 Residual Hardening and Operations

## Purpose

Plan 10 completes the v2 core governance path: packet lifecycle, multi-review
import, active pointer publication, status inventory, and release/pre-commit
verification. Plan 11 labels the remaining work that is deliberately outside
that core path so it can be handled without overstating v2 completion.

These items are follow-up hardening and operations work. They are not blockers
for the Plan 10 active pointer flow unless an item is explicitly promoted by a
review finding.

## Completion Boundary

Completed v2 core:

- `governance start/finalize/import-review/write-pointer/check/status`
- target-bound `AcceptancePacketReviewImport` materialization
- active `archive/v2` pointer publication
- release/pre-commit active packet gate integration
- routine single-publication release shape: content commits first, then one
  archive publication commit

Not claimed by v2 core:

- complete removal of legacy v1 compatibility surfaces
- treating historical fixtures as active governance records
- package-manager installation of the public `governance` command
- chained multi-publication release validation
- timeless re-evaluation of old packets under newer checker rules

## Residual Labels

### v2-residual-01 legacy-v1-boundary

Boundary: `archive/v1` remains frozen historical evidence. Legacy checkers may
guard immutability or compatibility, but they must not imply active v2 coverage
for old v1 records.

Acceptance criteria:

- Docs say v1 records are archived compatibility evidence, not active v2
  handoff records.
- Tests lock that `archive/v1` changes remain either blocked or explicitly
  waived with provenance.
- No release or status path treats v1 records as current packet evidence.

### v2-residual-02 historical-fixture-boundary

Boundary: fixtures, benchmark transcripts, and historical review artifacts are
checker examples or archived traces unless they are explicitly published through
active `archive/v2` pointers.

Acceptance criteria:

- Fixture docs distinguish positive/negative controls from active publication
  evidence.
- Generated fixture materialization remains test-only.
- Release/status inventory reports active pointers only from `archive/v2`
  publication records, not fixture-like files.

### v2-residual-03 governance-packaging

Boundary: `governance` is the public command name, but the current implementation
is a repository-local wrapper.

Acceptance criteria:

- Roadmap treats the remaining decision as installation/exposure mechanics, not
  command naming.
- CI may continue to call repository-local scripts while docs prefer
  `governance` for operator flow.
- Any future package entry point delegates to the same checker logic.

### v2-residual-04 multi-publication-release

Boundary: the accepted routine release model is one active pointer publication
per base-ref release range. Chained active pointer publications are a future
explicit model, not an implicit release-gate behavior.

Acceptance criteria:

- Docs tell operators to finish content commits before the archive publication
  commit when a single release pointer is desired.
- Release gate rejects hidden archive rewrites and does not collapse multiple
  archive publications into a fake first publication.
- Any future chained-pointer support validates each publication boundary rather
  than trusting net final tree state.

### v2-residual-05 checker-versioned-history

Boundary: old packets may have been authored under earlier checker and inference
rules. Current validation must not silently reinterpret them as stronger
evidence than their rule version supports.

Acceptance criteria:

- Packet evidence records enough checker/inference identity to explain the
  validation boundary.
- Historical audit messages distinguish structural byte integrity from current
  policy acceptance.
- Future re-evaluation policy is explicit before old packets are used as
  current governance proof.

### v2-residual-06 worktree-mode-boundary

Boundary: `--worktree` is always non-stable exploratory/in-progress evidence.
Stable handoff uses `--base-ref`; staged mode is preflight.

Acceptance criteria:

- Docs and tests keep worktree packets from satisfying active stable handoff.
- Any worktree status output names pending human/operator actions rather than
  publishing readiness.
- No active pointer path accepts worktree-only refs as publication evidence.

### v2-residual-07 packet-hash-placement

Boundary: active pointer bytes are the current packet-bound integrity root. A
packet-internal hash remains an open design choice because it risks
self-reference and migration churn.

Acceptance criteria:

- Current active validation keeps packet digests in pointers and review-import
  target bindings.
- Roadmap names packet-internal hash placement as a design decision, not a
  missing Plan 10 implementation.
- If packet-internal hashes are introduced, canonical serialization excludes the
  hash field or otherwise avoids self-reference.

## Processing Order

1. Close `v2-residual-01` and `v2-residual-02` together because they both guard
   historical material from being mistaken for active v2 evidence.
2. Design `v2-residual-04` before changing release behavior, because it can
   widen the active archive trust boundary.
3. Resolve `v2-residual-03` after the repo-local wrapper remains stable across
   one or more release cycles.
4. Handle `v2-residual-05`, `v2-residual-06`, and `v2-residual-07` as policy
   hardening unless a critic promotes one to release-blocking.

## Implementation Iteration 1

Closed in this iteration:

- `v2-residual-01 legacy-v1-boundary`: docs identify v1 as frozen
  compatibility evidence, and `tests/test_v1_archive_boundary.py` locks
  immutability plus waiver provenance behavior.
- `v2-residual-02 historical-fixture-boundary`: Plan 02, fixture README, and
  Plan 09 label fixtures and historical bytes as controls/traces rather than
  active closure inputs; `tests/test_maintenance_policy_boundaries.py` locks the
  wording.

Guardrails added in this iteration:

- Import-review operator flow remains archive-generating and stdin-capable:
  `tests/test_governance_review_import.py` covers `--from -` with both explicit
  and default `archive/v2/artifacts/` output.
- Import-review probe binding is materialized by the command rather than
  requiring reviewers to predict the final packet SHA.
- Residual labels remain inventory metadata; the multi-review benchmark
  regression proves label-like prose cannot override typed VETO facts.

Still pending:

- `v2-residual-04 multi-publication-release` design before any release-gate
  behavior change.
- `v2-residual-03 governance-packaging` after the repository-local wrapper has
  survived release use.
- `v2-residual-05`, `v2-residual-06`, and `v2-residual-07` as policy hardening
  unless a later critic promotes one to blocking.

## Implementation Iteration 2

Designed in this iteration:

- `v2-residual-04 multi-publication-release`: keep the current release gate on
  the single-publication model while documenting the required future chained
  publication invariants.

Current policy:

- One base-ref release range should contain content commits first, then exactly
  one active `archive/v2` publication commit.
- `verify-release.py --base-ref <ref> --pointer <pointer>` selects one pointer
  for that release range; it must not silently merge multiple active pointer
  publications into one apparent publication.
- Multiple active pointer publications in one release range should be split
  into separate release segments unless a later chained-pointer design is
  implemented and reviewed.

Future chained-pointer design requirements:

- Validate each active publication commit in topological order instead of
  trusting the final tree or a net diff.
- Preserve each pointer's own `comparison_ref`, `accepted_head_commit`,
  publication commit, packet bytes, artifact bytes, review import bytes, and
  probe transcript bytes.
- Permit no-ff merge commits that introduce no archive-side content, but reject
  merge-side archive content that was not published by a valid pointer.
- Allow later unrelated valid publications without causing old pointer audits
  to fail.
- Reject archive rewrites, deletes, relabels, or drift even when a later commit
  reverts the final bytes back to the original tree.
- Reject a synthetic release snapshot that collapses several archive-only
  commits into a fake first publication.

False-green probes a future implementation must cover:

- valid pointer publication, archive rewrite, then byte-for-byte revert;
- valid pointer publication followed by an unrelated valid pointer publication;
- no-ff merge checkout with no merge-side archive content;
- no-ff merge checkout that introduces archive content from the merge side;
- two pointers whose publication order is reversed or whose `comparison_ref`
  does not match the previous content boundary.

Not implemented in this iteration:

- The release gate still does not accept chained active publications in one
  release range as a completed model.
- `governance status` remains inventory, not a chain trust ledger.
- Any code change that attempts chained support must add behavioral tests for
  all false-green probes above before changing release semantics.

## Implementation Iteration 3

Closed in this iteration:

- `v2-residual-03 governance-packaging`: `governance` is the public operator
  command for v2. The current repository-local executable delegates to the same
  checker logic used by CI and release verification; package-manager
  installation is future distribution work, not an unfinished v2 semantics
  item.
- `v2-residual-05 checker-versioned-history`: active pointers record
  `checker_version` and `inference_rule_version`, and current validation treats
  mismatches as unsupported historical boundaries rather than silently
  reinterpreting old packets as current-proof evidence.
- `v2-residual-06 worktree-mode-boundary`: `--worktree` remains
  exploratory/non-stable; it can produce a valid packet for local diagnosis,
  but it cannot satisfy `--require-stable` or active pointer publication.
- `v2-residual-07 packet-hash-placement`: v2 keeps packet digest roots in active
  pointers and review-import target bindings. A packet-internal hash is not part
  of the v2 active model because it would introduce self-reference and migration
  churn without closing the active publication boundary.

Final v2 completion policy:

- The v2 active handoff path is complete for single-publication base-ref
  releases: `governance start`, `finalize`, `review-template`,
  `import-review`, `write-pointer`, `check`, `status`, release verification,
  and pre-commit active packet gating.
- `review-template` owns the target-bound review-import skeleton shape and probe
  transcript paths without auto-certifying PASS; reviewers still have to replace
  TODO fields, clear blocking findings, and record substantive probe evidence.
- Repository-local `governance` is the supported command surface for this repo;
  installers or package entry points may be added later only if they delegate to
  the same checker semantics.
- Historical packets whose checker or inference rule version does not match the
  current validator are compatibility/history evidence, not current stable
  proof.
- Worktree packets are local diagnostic records. Stable handoff remains
  base-ref packet-backed, and staged mode remains preflight.
- Packet bytes are bound externally by pointer `packet_sha256` and
  review-import `review_target_digest`; no packet-internal digest is required
  for v2 completion.

Future work after v2 completion:

- Optional package-manager distribution for `governance`.
- Optional chained-pointer release support, subject to the false-green probes
  listed in Implementation Iteration 2.
- Optional packet-internal hash design, only if canonical serialization avoids
  self-reference and migration ambiguity.

## Multi-Review Seed

Required critic lenses:

- historical-boundary critic
- fixture-boundary critic
- release-boundary critic
- operator-simplicity critic
- evidence-honesty critic

Blocking rule: any critic finding that a residual label can be read as completed
active v2 functionality must be fixed before the label registry is accepted.

Multi-review:

- Verdict: PASS for creating the residual registry as a labeling and sequencing
  artifact.
- Residual registry critic: score 9 PASS; Blocking findings: none after the
  registry labels were scoped to inventory metadata and follow-up acceptance
  criteria rather than implementation closure.
- Blocking findings: none for labeling; implementation of each residual remains
  separately tracked by its label.
- Follow-up/residual risk: each label needs its own later acceptance packet when
  moved from registry to implementation.
- Score handling: score 9; not 10 because this plan intentionally records
  follow-up work instead of closing it.
- Rerun status: initial registry review complete.
- Final acceptance: accepted as roadmap taxonomy, not as implementation closure.
