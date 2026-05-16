# Plan 07: Packet Archive and Integrity Backlog

## Purpose

Add v2 packet archive integration without expanding the public operator surface.
Plan 07 is also the backlog for deferred integrity work that should not be
patched into Plans 03-06 as another layer of ad hoc checks.

The user-facing shape remains `meta`, `input`, and `result`. Archive mechanics,
freshness policy, semantic evidence review, and release wiring must be generated,
derived, or validator-owned.

Plan 07 receives only archive-owned deferred risks from the Plan 06 Evidence
Ownership Boundary: immutable pointers, archive-bound freshness, semantic
evaluator seeds, source-ref archive policy, and version-drift semantics. Live
stable structural false-greens remain Plan 04-06 implementation work rather than
Plan 07 backlog.

Plan 07's implementation boundary is intentionally narrower than a full archive
ledger. It certifies the current active pointer, the packet/artifact bytes that
pointer names, and the current publication commit or pre-publication worktree
state. It does not certify the entire historical `archive/v2/` namespace or use
older pointers as a whitelist for new acceptance. Historical archive closure,
durable archive refs, and runner/attestation semantics are deferred to Plan 09.

## Problem Framing

Plans 03-06 made acceptance packets, evidence refs, review imports, replay
transcripts, and fixture drift mechanically checkable. The remaining deferred
risks are real, but they are archive-level risks rather than reasons to add more
fields to active packet authoring:

- stable packets need immutable storage and active pointers
- transcript and review artifacts need archive-bound freshness semantics
- plan approvals should be auditable as artifacts, not prose-only summaries
- semantic evidence relevance needs an evaluator, not path-based string rules
- fixture drift checks need a clear release policy after archive pointers exist
- command evidence authenticity needs pointer-bound replay metadata; active
  stable `check` only proves reopenable, packet-bound command records

Plan 07 should make these durable while keeping Plan 06's simplicity budget.

## Scope

In scope:

- Define the archive location for accepted v2 packets.
- Define active pointer records that bind packet id, packet hash, checker version,
  inference version, and current stable target.
- Validate archived packet bytes against active pointers.
- Validate current publication bytes for the active pointer, including packet,
  command artifact, review import artifact, linked probe transcript, accepted
  HEAD, and full-SHA base-ref boundaries.
- Reject unexpected `archive/v2/` changes introduced in the current
  `comparison_ref...accepted_head` work range, while treating archive bytes that
  already existed before `comparison_ref` as historical repository state.
- Bind transcript and review-import artifacts to archived result and packet
  digests rather than relying on wall-clock freshness alone.
- Represent plan acceptance and rerun history as packet/review artifacts where
  practical.
- Decide whether fixture drift helper checks become release-gate checks after the
  archive pointer model exists.
- Seed semantic-evidence backlog scenarios for a future evaluator.

Out of scope:

- New user-authored packet sections beyond `meta`, `input`, and `result`.
- Running artifact-supplied commands during stable `check`.
- Using historical pointers as archive namespace closure for future packets.
- Validating all preexisting `archive/v2/` bytes before allowing a new active
  packet to finalize.
- Proving historical command results without explicit replay or attestation.
- Requiring the synthetic `archive_commit` hash to exist as a persisted Git
  object in every clone.
- External runner identity, signatures, durable archive refs, or global archive
  ledger semantics; Plan 09 owns those questions.
- Full release/pre-commit migration. Plan 08
  (`backlog/plans/08-release-precommit-packet-gate.md`) owns release
  integration.
- Network validation of external sources.
- A general semantic scorer implementation unless a narrow, testable seed is
  explicitly accepted by multi-review.

## Backlog Items

### 1. Archive Store and Active Pointer

Define the minimal archive store, initially one of:

- `archive/v2/packets/<packet_id>.yml`
- `.harness/governance/packets/<packet_id>.yml`

The active pointer must be machine-readable and bind:

- packet id
- packet file ref
- packet SHA-256
- checker version
- inference rule version
- baseline/comparison ref used for stable evidence
- decision status

The checker should reject a stable pointer if the archived packet bytes no
longer match the pointer hash.

### 2. Archive-Bound Freshness

Do not add a generic "fresh enough by date" rule. A transcript or review artifact
is fresh for stable handoff only when it is bound to the archived packet/result
digest and target binding it claims to support.

If a packet changes, the archive pointer or artifact binding must change. Old
transcripts may remain historical evidence, but they cannot certify a different
result artifact.

Decision after the second pointer layer: active pointers bind review-import
artifacts and linked probe transcripts by SHA-256. Imported review results still
derive from `review_target_digest`, `source_digest`, `result_digest`,
`packet_ref`, and `packet_sha256`; stale transcript result or packet digests are
rejected before stable acceptance.

### 3. Plan Approval Evidence

Plan documents may summarize multi-review outcomes, but stable plan acceptance
should point to durable review artifacts when the packet archive exists.

Backlog requirement:

- preserve critic ids, scores, VETO state, rerun ids, source refs, probe refs, and
  digest bindings for accepted plan changes
- keep prose summaries as navigation, not as the only proof of acceptance

### 4. Semantic Evidence Relevance

Keep path/content validators conservative. Do not turn semantic relevance into a
large rule table inside `check-governance-acceptance.py`.

Backlog requirement:

- keep unrelated-but-existing evidence scenarios pending or non-acceptance until a
  semantic evaluator can judge them
- require raw claim evidence for proof-like/runtime/public claims, but leave
  deeper claim truth evaluation to a future narrow evaluator
- preserve benchmark scenarios that distinguish structural PASS from semantic
  acceptance

### 5. Fixture Drift Release Policy

Plan 06's fixture helper remains a developer maintenance command:

```bash
python3 scripts/update-governance-fixtures.py --check
```

Plan 07 must decide whether archived packet pointers make this helper safe and
useful as a release-gate check. If not, keep it documented but outside
`verify-release`.

Decision after the first pointer layer: keep
`python3 scripts/update-governance-fixtures.py --check` outside
`verify-release`. Active pointer validation now binds archived packet bytes and
command artifact digests, but fixture regeneration is still a developer
maintenance helper rather than stable handoff evidence. Plan 08 may revisit
release wiring after packet pointers become the release/pre-commit entry point.

### 6. Source-Ref Archive Policy

Plan 06 keeps active stable source refs intentionally narrow, but archive
integration still needs a durable policy for bare refs and historical source
evidence.

Backlog requirement:

- decide whether archived stable packet refs must use explicit schemes for every
  source relation, or whether bare repo paths remain allowed after pointer
  binding
- bind any accepted bare source ref to the archived baseline/comparison target so
  it cannot drift with the working tree
- add negative tests for directory-root protected refs, mutable `git:` refs, and
  opaque blob refs in archived source evidence
- document the migration path for existing bare fixture refs before enabling
  archive pointer validation

Decision after the second pointer layer: archived active stable packets must use
explicit, commit-pinned `git:<full-commit-sha>:<repo-path>` source refs for
changed-path source evidence. Bare repo paths remain allowed only for
non-active fixtures and fixture materialization. Mutable `git:` refs, opaque
blob refs, directory-root protected refs, and bare source refs cannot certify an
archived active pointer.

### 7. Rerun Audit Shape

Plan 05 now keeps rerun closure simple: `fixed_finding_ids` must exactly cover
the retained blocking review's finding IDs. Duplicate `fixed_finding_ids` were
pulled forward into the active Plan 04-06 checker during Plan 06 consolidation,
so they are no longer open archive-era work.

Backlog requirement:

- keep the concrete finding summaries in the original blocking review rather than
  adding a second fixed-finding object list

### 8. Observed Command Evidence Authenticity

Plan 04-06 stable checks validate that command evidence is structured,
repo-local, reopenable, packet-bound, and internally consistent. They do not
prove that a `# Command Evidence` section was produced by a trusted runner
rather than hand-authored to match the packet.

Backlog requirement:

- decide whether archived stable command evidence must be produced by a
  repository-owned runner, signed/generated artifact, or archive pointer process
- keep stable `check` read-only; do not execute artifact-supplied commands to
  prove authenticity
- add a negative archive-era test where a hand-authored command log echoes
  packet id/ref/hash, command, and pass status without pointer-bound replay
  metadata

Decision after the first pointer layer: archived stable command evidence may be
bound by the archive pointer process. `write-pointer` rejects pre-authored
replay/provenance fields, replays the command, and materializes pointer-bound
replay metadata plus recorded exit/stdout/stderr hashes into the matched
`# Command Evidence` section before hashing the command artifact into the
pointer. Active `check --require-stable` remains structural and read-only;
`check-pointer` performs pointer-bound replay-metadata and digest checks, and
`check-pointer --replay-command-evidence` explicitly reruns archived command
evidence to compare recorded exit/stdout/stderr hashes. This is local
pointer-bound replay evidence, not proof of writer identity, an external runner
signature, or independent identity attestation. `write-pointer --overwrite`
may replace existing pointer-bound replay metadata for the same packet/ref/hash
and command evidence identity so retry and output-recovery flows stay
idempotent without accepting legacy provenance fields.
Active pointers bind the accepted HEAD through archived packet evidence, not a
pointer-only field. Base-ref packets record `accepted_head_commit`, stable
targets include that commit, and generated command/source evidence is pinned to
that commit rather than mutable `HEAD`. `write-pointer` records a reproducible
synthetic `archive_commit` hash for the packet, command artifact, review import
artifact, and linked probe transcript bytes hashed by the pointer. `check-pointer`
recomputes that hash and verifies the pointer-bound bytes from the current
publication commit or pre-publication worktree; clones do not need the synthetic
commit object to be reachable. Historical `archive/v2/` closure is out of Plan
07 scope and belongs to Plan 09.

## Simplicity Budget

Plan 07 may add archive files and pointer validation, but it should not add new
manual concepts for routine users. Before accepting any new archive rule,
multi-review must answer:

- Which existing false-green does this close?
- Is the rule archive-owned rather than user-authored?
- Does it replace a scattered fixture or provenance convention?
- Does it avoid command execution during stable `check`?
- What older transitional rule can be removed or demoted after archive validation
  exists?

## Validation Seed

Plan 07 implementation should add tests for:

- pointer hash mismatch
- archived packet bytes changed after pointer creation
- stale transcript bound to a different result digest
- review artifact bound to a different packet target
- bare source refs either archive-bound or rejected according to the selected
  source-ref archive policy
- prose-only plan approval lacking durable review artifact linkage
- semantic evidence scenario recorded as pending/non-acceptance rather than PASS
- hand-authored command evidence without pointer-bound replay metadata
  cannot certify an archived stable packet
- command artifact bytes changed after pointer creation
- forged command replay output hashes in a pre-pointer artifact
- pre-authored replay/provenance fields cannot be accepted by `write-pointer`
- unexpected `archive/v2/` paths introduced in the active base-ref work range
  are rejected
- preexisting `archive/v2/` paths before the active comparison ref are not
  treated as Plan 07 evidence and are left to Plan 09 historical closure

Search-set verification:

- BEFORE: SKIPPED no pre-change search-set run was captured before accepting this
  governance hardening feedback batch.
- AFTER: PASS `python3 scripts/run-search-set.py` during the Plan 06 hardening
  batch after evaluator-boundary, transcript, closure, and fixture-helper guards
  were added.
- BEFORE: SKIPPED no pre-change search-set run was captured before implementing
  the Plan 07 active pointer validation layer.
- AFTER: PASS `python3 scripts/run-search-set.py` after adding
  `write-pointer`/`check-pointer`, archive-bound pointer tests, command artifact
  replay-metadata/digest checks, and release handoff wording fixes.
- Plan 07 archive pointer validation now has a first executable layer through
  `python3 scripts/check-governance-acceptance.py check-pointer`; command
  artifact digest binding, pointer-bound replay metadata, and
  explicit replay output hashes are checked there.
- The second layer extends pointer validation to review-import artifacts, linked
  probe transcripts, and archived source-ref policy without adding new
  user-authored packet sections.

## Current Implementation Slice

Implemented in the first Plan 07 layer:

- `write-pointer` and `check-pointer` for active v2 archive pointers under
  `archive/v2/pointers/`.
- Pointer binding for archived packet SHA-256, checker version, inference rule
  version, baseline/comparison refs, packet-bound accepted HEAD commit, stable
  target, accepted decision status, reproducible synthetic archive commit hash,
  and command artifact SHA-256.
- Active base-ref archive boundary policy requiring baseline/comparison refs to
  be full commit SHAs, with a negative test for mutable refs such as `HEAD`.
- Start/finalize normalization of user-provided `--base-ref` values to resolved
  full commit SHAs, keeping routine operator input friendly while storing stable
  archive boundaries and evidence commands.
- Pointer binding for review-import artifact SHA-256 plus linked probe transcript
  SHA-256, result digest, packet ref, and packet SHA-256; those review/probe
  bytes are included in the reproducible archive hash and committed publication
  byte checks rather than being trusted from the current worktree alone.
- Archive source-ref policy requiring commit-pinned `git:` refs for active
  changed-path source evidence, with negative tests for bare refs, mutable
  `git:` refs, opaque blob refs, and protected directory-root refs.
- Base-ref finalization now generates commit-pinned `git:` source refs for
  changed paths, using `HEAD` for additions/modifications and the comparison
  commit for deleted or renamed-preimage paths, so active archive validation
  does not require operators to hand-author routine source refs.
- Routine base-ref finalization into `archive/v2/packets/` materializes the
  durable `git diff --check` command artifact and marks the packet stable when
  the generated evidence validates, so the start/finalize/write-pointer path can
  publish without manual packet promotion.
- Routine active base-ref `start` defaults to `archive/v2/packets/<packet_id>.yml`
  and rejects non-archive output paths early, so operators do not discover the
  archive namespace requirement only at pointer publication time.
- Base-ref command evidence is pinned to `accepted_head_commit` instead of
  mutable `HEAD`, and `write-pointer` records a reproducible synthetic
  `archive_commit` hash over the packet, command artifact, review import
  artifact, and linked probe transcript bytes it hashes. `check-pointer`
  recomputes that hash, verifies publication bytes when the pointer is committed,
  requires `head_commit` to match the packet-bound `accepted_head_commit`, and
  rejects pointer-only rewrites of the accepted HEAD. The synthetic commit object
  itself is not required to be persisted across clones.
- Pointer-owned materialization of archive command evidence replay metadata and
  output hashes for matched `# Command Evidence` sections is scoped to local
  pointer binding and explicit replay rather than writer identity proof.
- `write-pointer --overwrite` regenerates existing pointer-bound replay metadata
  for matched command artifacts, keeping pointer output recovery idempotent while
  still rejecting pre-authored replay metadata on the initial path.
- `write-pointer` preflights stable packet validation before materializing command
  artifact replay metadata and rolls materialized artifact bytes back if pointer
  validation or pointer-file replacement fails, so failed attempts leave
  artifacts retryable.
- Explicit `check-pointer --replay-command-evidence` replay of archived command
  evidence exit/stdout/stderr hashes.
- Documentation boundary that keeps `check --require-stable` read-only and keeps
  release/pre-commit migration in Plan 08.
- A durable Plan 07 multi-review artifact at
  `backlog/fixtures/multi-review/plan07-archive-pointer-pass.yml`.

Remaining Plan 07 backlog after this layer:

- Convert future plan acceptance summaries into archived packet/review artifacts
  when a concrete plan-change packet is published.
- Keep semantic evidence relevance as a future evaluator seed rather than adding
  broad path/content heuristics to the structural checker; the benchmark
  scenarios remain the accepted seed.
- Treat cryptographic signing or external runner attestation as future hardening;
  the current layer proves pointer-generated artifact bytes plus explicit replay
  output-hash consistency.
- Move historical archive namespace closure, replay-verified historical command
  status, and persisted archive object/ref semantics to Plan 09 rather than
  adding more historical trust rules to Plan 07.

## Multi-Review Requirements

Before stable acceptance, run multi-review with at least these critic scopes:

- Archive integrity critic
- Simplicity and public-surface critic
- Artifact freshness/binding critic
- Semantic-evidence boundary critic
- Release-boundary critic

Current Plan 07 review is recorded as:

```bash
python3 scripts/check-multi-review-result.py --result backlog/fixtures/multi-review/plan07-archive-pointer-pass.yml --require-governance-pass --replay-probe-commands
```

The current review covers the implemented archive pointer layer with archive
integrity, artifact freshness, source-ref archive policy, command provenance,
semantic-boundary, release-boundary, and review-quality critics.
