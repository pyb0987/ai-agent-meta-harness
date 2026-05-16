# Plan 09: Historical Archive Closure and Attestation

## Purpose

Define a small, explicit model for trusting historical `archive/v2/` bytes after
Plan 07 active pointers exist. Plan 09 owns the questions that proved too broad
for Plan 07: historical namespace closure, replay-verified command status without
routine command execution, durable archive object/ref semantics, and optional
runner attestation.

Plan 09 should reduce operator burden, not add a new hand-authored audit layer.
If a rule requires operators to inspect or edit archived packet internals, it is
probably the wrong rule.

## Slice 1 Scope

In scope for this first slice:

- Treat historical `archive/v2/` bytes as committed repository bytes, not as a
  dedicated index, signed publication record, attestation, or future closure
  whitelist.
- Preserve the rule that prior archive pointers do not whitelist historical or
  future archive paths for later packet finalization.
- Keep routine `finalize`, stable `check`, release, and pre-commit flows from
  running or trusting historical command artifacts.
- Retain `archive_commit` as a reproducible synthetic hash while relying on
  committed publication bytes for clone durability.
- Add negative tests for forged historical pass records, fake historical review
  imports, hidden/new archive bytes, and clone durability without adding an
  operator-authored ledger.
- Keep replay and temporary snapshot validation independent of caller-local Git
  environment and caller `PATH` poisoning.
- Reject symlinked archive packet inputs and archive file refs before they can
  redirect reads or writes outside the named archive path.
- Reject new, unexpected `archive/v2/` bytes in active base-ref finalized
  packets even when the packet is not yet stable-handoff eligible.

Out of scope:

- Active pointer byte binding for the current packet; Plan 07 owns this.
- Release/pre-commit entry wiring; Plan 08 owns this.
- Dedicated archive indexes, signed/attested publication records, external
  runner identity, and durable archive refs.
- Prior-pointer whitelist semantics for future packet closure.
- Running artifact-supplied commands during routine `finalize` or stable
  `check`.
- User-authored packet sections beyond `meta`, `input`, and `result`.
- CI/documentation cleanup that removes now-redundant `--skip-clean-worktree`
  spelling from `--ci` release examples.

## Deferred Findings From Plan 07

- A historical pointer publication commit that also modified non-archive paths
  must not be accepted as archive namespace closure unless the historical trust
  model explicitly permits and records that scope.
- A historical command artifact can claim `status: pass` with empty hashes even
  when replay would fail. Plan 09 needs replay-verified status, runner
  attestation, or a narrower claim that does not rely on historical pass truth.
- Plan 07 records a reproducible synthetic `archive_commit` hash and validates
  current publication bytes. Plan 09 must decide whether that hash becomes a
  durable Git object/ref or remains only a deterministic digest.
- Documentation and review artifacts must distinguish active pointer byte
  binding from historical archive ledger integrity.

## Acceptance Seed

- A normal `start -> finalize` flow after prior archive publications remains
  user-input-minimal and does not execute historical commands.
- A forged historical pass result cannot whitelist future archive bytes.
- A prior pointer whose publication commit includes non-archive changes cannot
  whitelist archive paths unless the Plan 09 trust model records and accepts that
  publication scope.
- A clone can revalidate whatever Plan 09 claims without relying on unreachable
  local Git objects.

## Decision

Plan 09 keeps the historical trust model deliberately small:

- Historical `archive/v2/` bytes are committed repository bytes, not an active
  whitelist or attestation layer.
- Prior pointers are not used to close future `archive/v2/` namespace scope.
  They may be inspected with `check-pointer`, but routine `start`, `finalize`,
  stable `check`, release, and pre-commit flows do not trust their command
  status, review import list, or probe transcript list as closure for a later
  packet.
- Routine `finalize` and stable `check` never execute historical command
  artifacts. Explicit replay remains a user-selected `check-pointer
  --replay-command-evidence` action for the pointer being checked.
- The `archive_commit` field remains a reproducible synthetic hash over
  pointer-bound bytes. Published clone durability is proved from committed
  publication bytes, not from a hidden durable Git object.
- External runner identity, signatures, and durable archive refs remain out of
  scope until a later plan can justify their operator cost.

This means Plan 09 does not add a new user-authored ledger. The safety rule is
negative and simple: historical archive bytes can remain in history, but they do
not grant permission for new archive bytes to appear in the accepted work commit
or for future packets to skip their own active pointer publication.

## Implementation Notes

- Base-ref finalization ignores `archive/v2/` bytes that already exist at the
  comparison commit, because they are historical committed bytes rather than new
  work under review.
- Base-ref finalization rejects unexpected `archive/v2/` changes between the
  comparison commit and the accepted head, even if an older pointer appears to
  reference or whitelist those paths.
- The checker does not validate historical pointer closure while finalizing a
  new packet. This avoids executing or trusting forged historical command
  results and keeps the routine operator path input-minimal.
- `check-pointer` may audit a previously published pointer after later
  non-archive content commits. It finds the first archive publication after the
  pointer's accepted head, verifies the pointer-bound bytes there, and rejects
  later `archive/v2/` rewrites; release ordering remains owned by the active
  release/pre-commit gate.

## Review Record

Multi-review:

- Historical audit and isolation critic: score 9 PASS; Blocking findings: three
  accepted P2 issues were found and fixed for later valid publications, ambient
  HEAD recomputation, and staged-gate object DB writes.
- Release flow critic: score 9 PASS; Blocking findings: no remaining P1/P2
  findings after focused rerun; the intended operator path remains
  start/finalize/write-pointer/verify-release.
- Blocking findings: none remaining for Plan 09 Slice 1 implementation.
- Follow-up/residual risk: final active pointer publication and release gate
  execution must happen after the work commit in the current handoff.
- Score handling: why not 10: final publication is still being executed in this
  handoff; residual risk is limited to release sequencing and is addressed by
  the active pointer gate.
- Rerun status: full repository tests and focused historical-audit/staged-gate
  regressions passed after the accepted fixes.
- Final acceptance: accepted for Plan 09 Slice 1 implementation and release
  handoff.
