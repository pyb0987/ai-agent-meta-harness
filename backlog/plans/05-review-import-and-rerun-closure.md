# Plan 05: Review Import and Rerun Closure

## Purpose

Make v2 review records usable for stable handoff without implementing packet
archive storage, immutable hashes, or release-gate wiring.

Plan 04 made source, artifact, trace, and provenance refs durable enough for
stable packets. Plan 05 makes multi-review outcomes mechanically checkable:

- required review categories must be inferred from changed paths and content
- review records must preserve score, VETO, critic scope, false-green coverage,
  why-not-10, packet-local identity, rerun lineage, and durable provenance
- score below 9 must block stable handoff unless the same review target reruns
  to at least 9 after the blocking finding is addressed
- score 9 must preserve why-not-10 and disposition
- `not required` must be represented as a targeted waiver or downgrade, not as a
  generic bypass

## Problem Framing

Decision: define the Plan 05 implementation boundary for importing review
outcomes into v2 AcceptancePackets and using those outcomes for stable
eligibility.

Stakes: if Plan 05 is too weak, a packet can claim multi-review passed while
required critics, VETO recovery, review provenance, or false-green coverage are
missing. If too broad, v2 recreates v1 manual review bureaucracy before archive
integration exists.

Constraints:

- Preserve the public packet surface: `meta`, `input`, and `result`.
- Reuse Plan 04 `resolved_refs` and `review-provenance`; do not introduce a
  fourth public packet section.
- Do not implement packet archive storage, canonical hashes, active pointers, or
  immutable review transcript storage; those remain Plan 06.
- Do not wire packet checks into release/pre-commit gates; that remains Plan 07.
- Keep `check` read-only.
- Keep `start` and `finalize` honest: they may infer required review categories,
  but they do not fabricate successful review outcomes.

Presuppositions:

- Multi-review output can be reduced to structured review records without losing
  the essential judgment boundary.
- The same-review-target rerun rule is sufficient for VETO recovery before a
  full packet archive exists.
- False-green coverage can be validated by required fields and targeted negative
  tests, even though natural-language quality remains partly judgment-heavy.

Critics must be allowed to reject this frame if one of these presuppositions is
unwarranted.

## Success Criteria

- Stable packets with required reviews must contain one accepted review record,
  targeted review waiver, or targeted review downgrade for each required review
  target.
- Stable review records must include `review_id`, `critic`, `scope`,
  `anti_scope`, `score`, `veto`, `actor`, `role`, `date`, `source_ref`,
  `false_green_risk`, and `invariant_checked`.
- Stable score-9 reviews must include `why_not_10` and `disposition`.
- Stable packets must reject any review score below 9 unless a later rerun for
  the same review target names the exact failed `review_id`, reaches at least 9,
  records `veto: false`, and records the fixed blocking finding.
- Stable packets must reject any VETO review unless a later rerun for the same
  review target names the exact failed `review_id`, reaches at least 9, and
  records `veto: false`.
- Stable packets must reject null, empty, generic, or non-specific
  `false_green_risk` and `invariant_checked` values.
- Review `source_ref` values must resolve through `review-provenance`; terminal
  or conversation-only review provenance cannot satisfy stable handoff.
- Stable review imports must be complete: every review outcome in a structured
  review artifact must appear in `result.judgment.reviews`, including failed and
  VETO records.
- Review waivers and downgrades must target exactly one required review item and
  record actor, role, date, reason, and source.
- Required review inference must be computed from protected paths, high-impact
  inference, proof-like public/runtime claims, evaluator-boundary changes, and
  review-governance changes.

## Scope

In scope:

- `scripts/check-governance-acceptance.py`
- tests for review import fields, VETO/rerun closure, score-9 handling,
  false-green coverage, review provenance, and mandatory review inference
- Plan 05 fixtures only if positive or negative examples are required
- `backlog/v2-roadmap.md` and this plan

Out of scope:

- Packet archive storage, canonical hashing, active pointers, or immutable
  transcript indexes
- Release/pre-commit integration
- Natural-language validation that a review actually reasoned well
- Network validation of review links
- Replacing the local multi-review skill protocol

## Review Model

Plan 05 keeps reviews under `result.judgment.reviews`.

Stable review records must be typed enough for checker use:

- `review_id`: packet-local unique review identifier
- `critic`: the required review target this record satisfies
- `scope`: what the critic evaluated
- `anti_scope`: what the critic explicitly did not evaluate
- `score`: numeric review score
- `veto`: boolean
- `actor`, `role`, `date`, `source_ref`: durable provenance fields
- `false_green_risk`: concrete stale, misleading, or hand-authored false-pass
  mechanism the critic considered
- `invariant_checked`: concrete invariant, recomputation, or audit check that
  catches that false pass
- `why_not_10`: required when `score == 9`
- `disposition`: required when `score == 9`, and allowed for higher scores when
  residual risk exists
- `rerun_of`: optional exact `review_id` of the earlier review record being
  superseded; required for rerun records
- `blocking_findings_fixed`: required when `rerun_of` is present

Review target names must remain in the review namespace. Evidence items and
review items may share human-readable text, but waivers and downgrades must
carry `kind: review` when they target a review requirement.

## Review Import Completeness

Plan 05 must not trust hand-authored review summaries as the only source of
truth for stable handoff.

Stable packets that rely on review records must include structured import
material under `result.evidence.review_imports`:

- `source_ref`: durable local structured review artifact
- `format`: initially `multi-review-json-v1`
- `review_ids`: all review IDs found in the artifact
- `source_digest`: SHA-256 digest of the imported artifact bytes
- `status`: `imported`

The checker must parse each imported review artifact and verify:

- every artifact review outcome appears exactly once in
  `result.judgment.reviews`
- every packet review with that `source_ref` appears in the artifact
- `review_id` values are unique within the packet
- `review_imports.review_ids` equals the parsed artifact IDs
- `review_imports.source_digest` matches the current artifact bytes
- failed and VETO reviews remain present even when a later rerun closes them

This is intentionally weaker than Plan 06 immutable archive integrity, but it is
strong enough to prevent stable handoff from deleting a failed review while
claiming that the surviving packet-local summary is complete, or from drifting
away from the current structured review artifact.

## Required Review Inference

`finalize` may compute required review targets from changed paths and inferred
risk, but it must not mark protected or review-required work stable merely
because requirements were inferred.

Initial inferred review targets:

- `checker correctness`: protected paths, scripts, hooks, or acceptance checker
  behavior changed
- `methodology fidelity`: core methodology, maintenance policy, roadmap, plan, or
  public methodology claim changed
- `evidence auditability`: source refs, artifact refs, trace refs, packet
  evidence, review provenance, or archive evidence changed
- `release integration`: release, pre-commit, stable handoff, or archive boundary
  checks changed
- `scope boundary`: a change alters what is deferred, waived, downgraded, or
  treated as not required
- `claim evidence`: runtime, public, proof-like, release-ready, or
  production-ready claims changed

The exact target table may start conservative and small, but stable handoff must
fail if the checker detects a protected or high-impact change with no inferred
required review target.

## Rerun Semantics

For stable packets:

- Any review with `veto: true` is blocking unless a later review record names it
  via exact `rerun_of: <review_id>`, uses the same `critic`, records
  `veto: false`, and scores at least 9.
- Any review with `score < 9` is blocking unless a later review record names it
  via exact `rerun_of: <review_id>`, uses the same `critic`, records
  `veto: false`, and scores at least 9.
- A rerun cannot satisfy a different critic target.
- A rerun cannot satisfy more than one failed review.
- A rerun must include `blocking_findings_fixed` with concrete fixed findings.
- A rerun source must itself resolve through `review-provenance`.
- The packet must keep the failed review and the successful rerun so the
  recovery path is auditable.

## CLI Semantics

### `start`

- Preserve any user-provided review waiver or downgrade requests under
  `input.user_judgment`.
- Do not fabricate review outcomes.

### `finalize`

- Infer required review targets from changed paths, content rules, and
  evaluator-boundary changes.
- Preserve existing `result.judgment.reviews` rather than deleting imported
  review records.
- For protected or review-required work, keep `stable_handoff_eligible: false`
  unless imported review records already satisfy `check --require-stable`.
- Do not turn a `not required` operator note into absence of review; represent it
  as a waiver or downgrade request.

### `check`

- Validate stable review records and their `review-provenance` refs.
- Validate that required review targets are satisfied by passing reviews,
  targeted waivers, or targeted downgrades.
- Validate VETO and score-below-9 closure through same-target reruns.
- Validate structured review import completeness.
- Validate packet-local `review_id` uniqueness and exact `rerun_of` references.
- Validate score-9 why-not-10 and disposition.
- Validate false-green coverage fields for specificity.
- Validate review/evidence namespace separation for waivers and downgrades.
- Keep packet validity distinct from stable-handoff eligibility.

## Invariants

- A required review target is never satisfied by silence.
- A VETO is never canceled by deleting the failed review record.
- A rerun never satisfies a different review target or an ambiguous failed
  review.
- A stable review summary is never trusted unless its structured source artifact
  is parsed and all artifact review IDs are represented in the packet.
- A stable review import cannot drift from its local source artifact; the
  artifact digest must match the packet record.
- Score 9 is accepted only with why-not-10 and disposition.
- Review provenance cannot rely on terminal or conversation-only refs for stable
  handoff.
- False-green coverage cannot be null, empty, generic, or unrelated to the
  review scope.
- A review waiver or downgrade cannot apply to a broad category; it must target
  exactly one required review item.
- Human-authored `not required` text cannot bypass checker-inferred review
  requirements.

## Validation

Run:

```bash
python3 -m unittest tests/test_acceptance_packet_fixtures.py
python3 -m unittest tests/test_governance_acceptance_cli.py
python3 -m unittest tests/test_governance_evidence_refs.py
python3 -m unittest tests/test_governance_review_import.py
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml --require-stable
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml --require-stable
git diff --check
```

## Multi-Review Requirements

Use the current `multi-review` skill protocol.

Problem framing must include the `Decision`, `Stakes`, `Constraints`, and
`Presuppositions` above. Critic prompts must either include one presupposition
challenge or explicitly allow each critic to say the question itself is wrongly
framed.

Required critic lenses:

- Contract Fidelity Critic: review record shape, review/evidence namespace
  separation, and generated/user boundary.
- Decision Correctness Critic: stable review satisfaction, VETO closure,
  score-9 handling, rerun identity, import completeness, and false-green field
  checks.
- Auditability Critic: durable review provenance, retained failed reviews,
  structured import artifacts, rerun lineage, and packet-local rationale.
- Scope Boundary Critic: confirms Plan 05 does not implement archive pointers,
  immutable transcript storage, release integration, or full natural-language
  review quality grading.

For repository governance work, any score below 9 is VETO until fixed and rerun.
Every score 9 must record why-not-10 and residual-risk or follow-up disposition.
No final PASS is valid unless at least one critic records a concrete
false-green path and the invariant that catches it.

## Plan Review Outcome

Multi-review:

- Contract fidelity critic: score 8, VETO on first pass. Blocking finding:
  rerun identity was not stable enough because `rerun_of` was optional and
  `review_id` was left as an open question. Rerun score 9 after adding required
  packet-local `review_id`, exact `rerun_of`, and structured
  `review_imports`. Why not 10 at that rerun: digest drift could still let a
  packet summary diverge from the structured review artifact. Final quick rerun
  score 10 after requiring SHA-256 `source_digest`.
- Decision correctness critic: score 8, VETO on first pass. Blocking findings:
  a failed/VETO review could be omitted from a hand-authored stable packet, and
  rerun identity was ambiguous. Rerun score 9 after adding structured import
  completeness and exact same-review rerun closure. Why not 10 at that rerun:
  digest drift could still preserve a stale review import while the packet
  claimed acceptance. Final quick rerun score 10 after adding digest-drift
  rejection.
- Auditability critic: score 8, VETO on first pass. Blocking finding: rerun
  lineage was not auditable without a unique review identity. Rerun score 9
  after adding retained failed review IDs and import completeness. Why not 10 at
  that rerun: artifact digest verification was not yet required. Final quick
  rerun score 10 after requiring artifact digest verification.
- Scope-boundary and presupposition critic: score 9, PASS. Blocking findings:
  none. Why not 10 at that point: rerun identity was still intentionally
  unsettled. Disposition: resolved by making `review_id` mandatory in Plan 05
  while keeping immutable archive storage deferred to Plan 06.
- False-green coverage: critics named concrete stale or hand-authored packet
  paths involving ambiguous reruns, deleted failed/VETO reviews, stale local
  review artifacts, and generic packet summaries that did not match structured
  review artifacts.
- Score handling: all VETO findings were fixed in the plan and affected critics
  reran to at least 9; digest tightening then raised the affected reruns to 10.
- Rerun status: contract fidelity, decision correctness, and auditability critics
  reran after plan fixes; digest-specific quick reruns then confirmed the final
  plan shape.
- Follow-up/residual risk: implementation must add negative tests for omitted
  failed reviews, ambiguous reruns, stale imports, digest drift, score-9 gaps, and
  broad review waivers before acceptance.
- Final acceptance: accepted for Plan 05 planning.

## Open Questions

- Should `false_green_risk` and `invariant_checked` be required for all stable
  reviews, or only for review targets that affect durable/public/release claims?
- Should Plan 05 add a CLI import command, or should review records be supplied
  as packet edits until Plan 06 introduces archive storage?

## Negative Test Requirements

- A stable packet with a required review target and no review/waiver/downgrade
  must fail.
- A stable packet with review score below 9 and no same-target rerun must fail.
- A stable packet with `veto: true` and no same-target rerun must fail.
- A stable packet with a rerun for a different critic target must fail.
- A stable packet with `rerun_of` that does not exactly name one retained failed
  `review_id` must fail.
- A stable packet with duplicate `review_id` values must fail.
- A stable packet whose structured review artifact contains a failed review that
  is missing from `result.judgment.reviews` must fail.
- A stable packet whose review import digest does not match the structured
  review artifact bytes must fail.
- A stable packet with score 9 but no `why_not_10` or no `disposition` must fail.
- A stable packet with terminal-only review provenance must fail.
- A stable packet with null, empty, generic, or unrelated `false_green_risk` or
  `invariant_checked` must fail.
- A stable packet where a review waiver or downgrade omits `kind: review` for a
  review target must fail.
- A stable packet where `not required` appears as a broad bypass instead of a
  targeted waiver or downgrade must fail.
