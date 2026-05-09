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

Plan 06 uses five consolidation moves.

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
allowed only if it rewrites deterministic derived fixture fields and remains
separate from stable `check`.

The helper owns only derived fixture bindings, at minimum:

- `result.evidence.review_imports[*].source_digest`
- review-import wrapper `target_binding`
- review-import wrapper and packet import `review_target_digest`
- packet SHA values recorded in command evidence logs
- `ProbeTranscript.result_ref`
- `ProbeTranscript.result_digest`
- `ProbeTranscript.packet_ref`
- `ProbeTranscript.packet_sha256`

The helper does not decide whether a claim is semantically true. It recomputes
or checks derived bytes, hashes, refs, and binding fields, then reports mismatch.
It does not own observed command strings, observed command status, probe stdout,
probe stderr, transcript body, probe exit status, or transcript source refs.
Those fields may change only through the runner, explicit replay, or explicit
regeneration path that produced the observation.

It should not run arbitrary artifact-supplied probe commands as part of stable
`check`. Active replay remains explicit.

### 3. Evidence Ownership Boundary Amendment

This amendment is the binding cross-plan boundary for Plans 04-07. It is not a
new plan layer. It supersedes any Plan 04/05/06 wording that implies helpers can
rewrite observations, that stable `check` can judge prose quality, or that two
tools may parse the same artifact differently.

Ownership matrix:

| Artifact | Owner | Parser / Canonical Contract | Helper Role | Stable Consequence |
| --- | --- | --- | --- | --- |
| Command evidence log | runner or fixture regeneration path | one `# Command Evidence` section parser shared by helper and checker | update derived packet hash/ref bindings only; never rewrite `command` or `status` | mismatch fails stable evidence |
| `ProbeTranscript` | replay runner or transcript regeneration path | structured `ProbeTranscript` parser shared by validator/helper/archive checks | update derived result/packet bindings only when observed command, exit, stdout, stderr, and source refs already match | stale or unbound transcript cannot support governance PASS |
| `AcceptancePacketReviewImport` | review import generator | structured wrapper parser shared by checker/helper/archive checks | update digest and target binding from wrapper bytes | digest or target drift fails stable review import |
| `MultiReviewResult` | multi-review protocol / replay validator | schema validator plus replay transcript verifier | no semantic rewrite; fixture binding only when transcript ownership is clear | derived PASS proves structure and bound probes, not full prose quality |
| AcceptancePacket stable check | checker | read-only packet/ref/artifact validation | no writes and no command execution | reports VALID/STABLE/BLOCKED only from existing artifacts |
| Archive pointer | Plan 07 archive process | archive pointer parser and packet hash verifier | no ownership until Plan 07 | stale or changed archived bytes require revalidation |

Layer rules:

- Observed evidence is immutable. `command`, `status`, stdout/stderr,
  transcript body, probe exit status, source refs, and runner output hashes are
  runner-owned. A helper mismatch is a failure plus replay/regeneration
  instruction, not a rewrite opportunity. The helper can check self-consistent
  transcript hashes, but it cannot prove a hand-edited transcript body without
  replay or regeneration evidence.
- Stable `check` is read-only. It does not replay commands, rewrite artifacts, or
  generate missing evidence.
- The checker validates schema, targets, bindings, provenance, digests,
  derivable closure, exact parser contracts, and non-vacuous scalar presence. It
  does not claim full semantic adequacy of prose such as
  `false_green_risk` or `invariant_checked`.
- Review Quality critics, durable review artifacts, semantic benchmarks, or a
  future evaluator own full prose specificity and semantic adequacy.
- One artifact type has one parser/canonicalization contract. If helper and
  checker disagree, the artifact contract is wrong and must be consolidated
  before adding more guards.

Disposition table for future feedback:

| Feedback Type | Disposition | Owner |
| --- | --- | --- |
| Live stable structural/binding false-green | `FIX_NOW` | owning checker/helper plan |
| Helper can rewrite observed evidence | `FIX_NOW` | Plan 06 |
| Parser divergence for the same artifact | `FIX_NOW` | Plan 06 |
| Scalar container or vacuous placeholder accepted as structure | `FIX_NOW` | Plan 05 / validator |
| Semantic prose specificity overclaim | `LOWER_CLAIM` | Plan 05 amendment |
| Proof-like content truth or semantic evidence relevance | `DEFER_PENDING_NONACCEPTANCE` | Plan 07 evaluator backlog |
| Archive freshness, immutable pointers, version drift | `DEFER_PENDING_NONACCEPTANCE` | Plan 07 archive backlog |
| Archive-owned audit neatness without stable false-green | `DEFER_PENDING_NONACCEPTANCE` | Plan 07 |
| Non-archive audit neatness without stable false-green | `DEFER_PENDING_NONACCEPTANCE` | later non-archive cleanup, not Plan 07 |

Current finding disposition:

| Finding | Disposition | Boundary Reason |
| --- | --- | --- |
| Command evidence parser accepts non-command headings | `FIX_NOW` | parser contract divergence |
| Helper can rebind stale command logs | `FIX_NOW` | helper rewrites observed evidence |
| Replay benchmark expected VETO hides extra structural errors | `FIX_NOW` | replay benchmark parser masks structural drift |
| Review scalar containers pass review lineage / result target | `FIX_NOW` | scalar structure false-green |
| Residual risk lacks target/provenance validation | `FIX_NOW` for structure; semantic quality deferred | stable closure structure |
| Downgrade closes without replacement | `FIX_NOW` | targeted downgrade structure |
| Generic review prose specificity | `LOWER_CLAIM` | deterministic checker is wrong layer |
| Benchmark-only transcript ownership | `FIX_NOW` if helper claims ownership; otherwise narrow helper claim | ownership mismatch |
| Bare source-ref archive policy | `DEFER_PENDING_NONACCEPTANCE` | archive pointer policy |
| Finalize-time search-set skip provenance for non-stable packets | `DEFER_PENDING_NONACCEPTANCE` outside Plan 07 | auditability gap, not stable false-green or archive-owned risk |

### 4. Complexity Budget

Every future plan or implementation that adds a guard, schema field, or fixture
kind must answer:

- Which concrete false-green path does this close?
- Can an existing guard be generalized instead?
- Does this add anything the user must hand-author?
- Does this create a multi-file regeneration burden?
- What can be removed, merged, or generated as a result?

If those questions cannot be answered, the change is deferred or redesigned.

### 5. Multi-Review Anti-Bloat Critic

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
optional. The helper may compute hashes and rewrite derived binding fields in
fixture artifacts. It must not rewrite observed command/probe evidence, must not
be required for `governance check` or `verify-release` in Plan 06, and must not
execute artifact-supplied probe commands unless an explicit replay mode is added
later with an allowlisted runner.

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

## Plan Review Outcome

Plan 06 was accepted as a consolidation plan, not a new governance layer. The
review disposition is:

- PASS, score 9: the evidence ownership boundary reduces scattered Plan 04/05/06
  rules into one helper/checker/replay ownership matrix.
- Why not 10: archive-era source-ref policy, semantic relevance, and pointer
  freshness remain Plan 07 responsibilities rather than Plan 06 implementation.
- Residual risk disposition: Plan 07 carries archive-owned deferred risks; live
  stable false-greens stay in the active checker/helper implementation.

## Implementation Review Outcome

Current implementation review disposition: accepted for the Plan 06
consolidation scope.

- Verdict: PASS, with no open Plan 06 VETO after the focused
  validator-hardening iteration.
- Score: 9.
- Rerun status: affected checker/helper/benchmark paths were rerun through the
  focused negative tests and the release validation below.
- Why not 10: command artifact authenticity, archive-bound freshness, and full
  semantic relevance remain Plan 07 responsibilities.
- Residual risk disposition: accepted only as Plan 07 archive/integrity backlog,
  not as active Plan 06 stable-handoff truth.

Implementation acceptance covered focused negative tests for:

- helper attempts to rewrite observed command/probe/source evidence
- checker/helper parser divergence for command evidence
- transcript/result/packet binding drift
- review-import target binding and lineage closure drift
- benchmark oracle strings losing source/path specificity

Search-set verification:

- BEFORE: SKIPPED pre-change search-set output was not captured before this
  focused validator hardening iteration.
- AFTER: PASS `python3 scripts/run-search-set.py` for base-ref canonical stable
  handoff, HEAD-pinned source refs, proof-like impact escalation from commit
  content, search-set skip/trace consistency, semantic oracle
  source-ref/vacuous/disposition gates, probe transcript public metadata,
  source-ref closure, and benchmark sealed-oracle boundary changes affecting
  `scripts/check-governance-acceptance.py` and
  `benchmarks/multi-review/check-fixtures.py`.

Any implementation review VETO must be closed by changing the checker/helper or
by lowering an overbroad Plan 06 claim. Do not add a new public packet field to
close Plan 06 findings.

## Open Questions

- Should `source_refs` keep allowing bare repo paths after archive integration,
  or should stable source refs also move to explicit schemes?
- Should the anti-bloat critic be embedded in the multi-review skill, in
  `MAINTENANCE.md`, or both?
- Should the helper generate transcripts only from existing recorded output, or
  also support an explicit replay mode in a later plan?
