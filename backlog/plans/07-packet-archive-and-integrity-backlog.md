# Plan 07: Packet Archive and Integrity Backlog

## Purpose

Add v2 packet archive integration without expanding the public operator surface.
Plan 07 is also the backlog for deferred integrity work that should not be
patched into Plans 03-06 as another layer of ad hoc checks.

The user-facing shape remains `meta`, `input`, and `result`. Archive mechanics,
freshness policy, semantic evidence review, and release wiring must be generated,
derived, or validator-owned.

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

Plan 07 should make these durable while keeping Plan 06's simplicity budget.

## Scope

In scope:

- Define the archive location for accepted v2 packets.
- Define active pointer records that bind packet id, packet hash, checker version,
  inference version, and current stable target.
- Validate archived packet bytes against active pointers.
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
- Full release/pre-commit migration. Plan 08 owns release integration.
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
- prose-only plan approval lacking durable review artifact linkage
- semantic evidence scenario recorded as pending/non-acceptance rather than PASS

## Multi-Review Requirements

Before implementation, run multi-review with at least these critic scopes:

- Archive integrity critic
- Simplicity and public-surface critic
- Artifact freshness/binding critic
- Semantic-evidence boundary critic
- Release-boundary critic

