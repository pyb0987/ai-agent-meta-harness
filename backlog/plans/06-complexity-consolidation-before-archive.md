# Plan 06: Complexity Consolidation Before Archive Integration

## Purpose

Prevent v2 governance from repeating the v1 failure mode where each missing
guard became another manual rule, schema field, fixture exception, or review
ritual.

Plans 03-05 made packets, evidence, review imports, replay boundaries, and
durable transcript bindings mechanically checkable. Those changes improved
false-green resistance, but they also created operational complexity:

- transcript fixtures now bind result refs, packet refs, source refs, and hashes
- packet fixtures and command logs must be regenerated together
- source refs, artifact refs, trace refs, review refs, and probe evidence refs
  use overlapping string forms
- benchmark pending/replay behavior is easy to misread if the mode is not
  explicit
- multi-review tends to add guardrails unless it is also asked to remove or
  consolidate them

Plan 06 is a consolidation checkpoint before packet archive integration. It
adds no new governance surface and no new stable-handoff obligation unless that
obligation replaces scattered existing behavior.

## Problem Framing

Decision: define the smallest consolidation layer needed before archive
integration can safely add immutable packet pointers and active indexes.

Stakes: if this step is skipped, archive integration will likely preserve the
current hand-maintained transcript/hash patterns and make them harder to change.
If this step grows too large, it becomes another governance subsystem and
recreates the complexity it is meant to reduce.

Constraints:

- Preserve the public packet surface: `meta`, `input`, and `result`.
- Do not add new top-level packet sections or user-authored governance fields.
- Do not implement archive storage, active pointers, release/pre-commit wiring,
  or semantic scoring.
- Keep `check` read-only and replay explicit.
- Prefer helper functions, generated fixtures, and documented ref taxonomy over
  new schema fields.
- Any new rule must either replace repeated local logic or close a concrete
  false-green path that cannot be closed by an existing rule.

Presuppositions:

- v2 can keep the operator model simple even if internal validation is strong.
- Most current complexity is operational drift from hand-maintained fixtures,
  not unavoidable methodology complexity.
- A short consolidation pass before archive integration is cheaper than
  retrofitting simplicity after archive pointers exist.

Critics must be allowed to reject this frame if consolidation would hide an
unresolved correctness gap or merely rename complexity.

## Success Criteria

- A maintainer can explain the active governance model in four boundaries:
  `check` is read-only, `replay` is explicit, `stable` validates durable
  evidence, and artifact refs use explicit schemes.
- A maintainer can check transcript/review-import fixture drift by running one
  required helper command, not by manually syncing hashes across packet files,
  wrapper files, command logs, and transcripts.
- Ref taxonomy is documented and tested:
  - `source_ref`: repository-local source or provenance material; bare repo
    paths remain allowed unless a later plan narrows them.
  - `artifact_ref`: durable generated artifact; stable refs use `file:`.
  - `probe_evidence_ref`: durable probe transcript artifact; stable refs use
    `file:`.
  - `trace_ref`: trace material; stable refs use `trace:`.
  - `review_provenance_ref` and `waiver_provenance_ref`: durable local
    provenance material; generated artifact provenance must use `file:`.
- Multi-review prompts and maintenance guidance require at least one critic to
  ask whether a new guard can replace or consolidate existing guards.
- Benchmark pending output names pending checks generically and cannot be
  mistaken for a green gate unless `--allow-pending` is explicit.
- No checker path gains command execution during stable `check`.
- No new public CLI surface is required for operators to understand this plan.

## Scope

In scope:

- A small transcript/review-import fixture drift helper with `--check`; `--write`
  may be added if it stays fixture-only and deterministic.
- Ref taxonomy documentation near the checker, plans, or maintenance guidance.
- Tests that prevent bare `probe_evidence_refs`, command-artifact record drift,
  and pending-as-green regressions.
- Small refactoring of duplicated checker helper logic if it reduces total
  surface and keeps behavior unchanged.
- Updates to `MAINTENANCE.md`, `backlog/v2-roadmap.md`, and multi-review skill
  guidance so anti-bloat review becomes explicit.

Out of scope:

- Packet archive storage, canonical active pointers, immutable packet indexes,
  or archive migration.
- Release/pre-commit integration of v2 packet checks.
- Release-gate wiring for the fixture drift helper.
- Semantic scorer implementation for evidence relevance or frame quality.
- Renaming the public packet shape.
- Replacing multi-review with a new review protocol.

## Consolidation Model

Plan 06 uses four consolidation moves.

### 1. Ref Taxonomy

Ref strings must be understandable by role, not only by syntax.

- Source refs identify material being reviewed or used as provenance.
- Artifact refs identify generated evidence that must be reopenable later.
- Probe evidence refs are artifact refs whose content is a structured
  `ProbeTranscript`.
- Trace refs identify search-set or harness trace material.
- Git refs identify version boundaries and must stay separate from local
  artifact evidence.

The checker may continue to accept broad source refs, but artifact-like refs
must be explicit. This preserves current flexibility without letting generated
evidence hide behind ambiguous bare paths.

### 2. Fixture Drift Helper

Transcript and packet fixture drift must become a tool problem, not a reviewer
memory problem.

Plan 06 must add a fixture-only helper. `--check` is required. `--write` is
allowed only if it rewrites deterministic fixture fields and remains separate
from stable `check`.

The helper owns the derived fixture surface, at minimum:

- `result.evidence.review_imports[*].source_digest`
- review-import wrapper `target_binding`
- review-import wrapper and packet import `review_target_digest`
- packet SHA values recorded in command evidence logs
- command log section binding for `packet_id`, `packet_ref`, `command`, and
  `status`
- `ProbeTranscript.result_ref`
- `ProbeTranscript.result_digest`
- `ProbeTranscript.packet_ref`
- `ProbeTranscript.packet_sha256`
- `ProbeTranscript.source_refs`
- transcript stdout/stderr hashes when fixture command output changes

The helper does not decide whether a claim is semantically true. It recomputes
or checks derived bytes, hashes, refs, and binding fields, then reports mismatch.

It should not run arbitrary artifact-supplied probe commands as part of stable
`check`. Active replay remains explicit.

### 3. Complexity Budget

Every future plan or implementation that adds a guard, schema field, or fixture
kind must answer:

- Which concrete false-green path does this close?
- Can an existing guard be generalized instead?
- Does this add anything the user must hand-author?
- Does this create a multi-file regeneration burden?
- What can be removed, merged, or generated as a result?

If those questions cannot be answered, the change is deferred or redesigned.

### 4. Multi-Review Anti-Bloat Critic

Governance multi-review must include a critic whose primary job is not to find
more checks, but to challenge unnecessary complexity.

This critic should VETO when:

- a new rule duplicates an existing invariant under another name
- a guard can pass only through hand-synced fixture state
- an implementation spreads one policy across several unrelated files without a
  helper or generator
- a design increases operator-facing concepts beyond `meta`, `input`, and
  `result`
- a PASS depends on prose explaining why complexity is acceptable rather than
  machine-checkable boundaries

## CLI Semantics

Plan 06 should not add a new operator CLI. The helper is a developer
maintenance tool rather than part of the public packet lifecycle.

Allowed helper shape:

```bash
python3 scripts/update-governance-fixtures.py --check
python3 scripts/update-governance-fixtures.py --write
```

`--check` is required for Plan 06 implementation acceptance. `--write` is
optional. The helper may compute hashes and rewrite fixture artifacts. It must
not be required for `governance check` or `verify-release` in Plan 06, and it
must not execute artifact-supplied probe commands unless an explicit replay mode
is added later with an allowlisted runner.

## Invariants

- Stable `check` remains read-only.
- Replay remains explicit and active.
- Generated evidence refs use explicit schemes.
- Source refs and artifact refs are not interchangeable unless a record names
  the relation.
- Fixture drift is either caught by validation or repaired by a documented
  helper.
- New governance strength must not require more hand-authored user fields.
- A plan that adds complexity must also state what complexity it removes,
  consolidates, or defers.

## Validation

Plan 06 implementation should run:

```bash
python3 -m unittest tests/test_multi_review_result_cli.py
python3 -m unittest tests/test_multi_review_benchmark_cli.py
python3 -m unittest tests/test_governance_acceptance_cli.py
python3 -m unittest tests/test_governance_review_import.py
python3 benchmarks/multi-review/check-fixtures.py --replay-probe-commands
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-routine.yml --require-stable
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml --require-stable
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml --require-stable
python3 scripts/update-governance-fixtures.py --check
python3 scripts/check-maintenance-review.py
python3 scripts/check-compat-mirrors.py
python3 scripts/sync-codex-plugin.py --check
git diff --check
```

Full release verification remains:

```bash
python3 scripts/verify-release.py --skip-clean-worktree
```

## Multi-Review Requirements

Before accepting this plan or its implementation, run multi-review with at
least these critic scopes:

- Simplicity and operator-surface critic: confirms the plan reduces user-facing
  complexity and does not add new hand-authored governance fields.
- Checker-boundary critic: confirms `check` remains read-only, replay remains
  explicit, and explicit artifact schemes are preserved.
- Fixture-drift critic: confirms transcript, packet hash, wrapper digest, and
  command log maintenance becomes generated or mechanically checkable.
- Scope-boundary critic: confirms Plan 06 does not implement archive storage,
  release integration, semantic scoring, or a new review protocol.

Every required critic must score at least 9. Any VETO requires updating the
plan or implementation and rerunning the affected critic. Every score 9 must
record why-not-10 and residual-risk or follow-up disposition.

## Open Questions

- Should `source_refs` keep allowing bare repo paths after archive integration,
  or should stable source refs also move to explicit schemes?
- Should the anti-bloat critic be embedded in the multi-review skill, in
  `MAINTENANCE.md`, or both?
- Should the helper generate transcripts only from existing recorded output, or
  also support an explicit replay mode in a later plan?
