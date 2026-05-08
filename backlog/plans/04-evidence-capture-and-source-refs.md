# Plan 04: Evidence Capture and Source References

## Purpose

Make v2 packet evidence honest enough for stable handoff without implementing
review import, packet archive pointers, or release-gate replacement.

Plan 03 made packet lifecycle mechanics executable. Plan 04 makes evidence
references checkable:

- source refs must use allowed forms and resolve to durable local material
- result evidence refs must preserve origin, relation, and durable target type
- command evidence must distinguish observed command status from claimed evidence
- search-set before/after refs must be represented for harness-affecting work
- runtime, public, or proof-like claims must require raw artifact/log/trace refs
- post-import `archive/v1/` waiver provenance must be represented in packet
  judgment/evidence before accepted archive edits rely on v2 governance

## Problem Framing

Decision: define the Plan 04 implementation boundary for evidence capture and
source-reference validation.

Stakes: if Plan 04 is too weak, stable packets can claim evidence that does not
exist; if too broad, v2 reintroduces v1-style complexity before review import and
archive integration are ready.

Constraints:

- Preserve the public packet surface: `meta`, `input`, and `result`.
- Do not implement review transcript import; that remains Plan 05.
- Do not implement packet archive pointers, canonical packet hashes, or active
  indexes; that remains Plan 07 after Plan 06 complexity consolidation.
- Do not wire packet checks into release/pre-commit gates; that remains Plan 08.
- Keep `check` read-only.
- Apply the Plan 06 Evidence Ownership Boundary: Plan 04 content rules classify
  risk and evidence requirements; they do not prove semantic truth.

Presuppositions:

- Evidence refs can be validated before packet archive integrity exists.
- Source-ref validation is useful even while refs are still string-shaped.
- Content rules can conservatively identify proof-like documentation claims well
  enough to raise review/evidence requirements, without claiming semantic truth
  validation.

Critics must be allowed to reject this frame if one of these presuppositions is
unwarranted.

## Success Criteria

- `scripts/check-governance-acceptance.py check` rejects stable packets with
  missing, unsupported, or unresolved source refs.
- Stable packets with command evidence must preserve command, status, and
  artifact refs; artifact refs must resolve to local durable material.
- `terminal:<id>` is a local observation placeholder only. It may appear in valid
  non-stable packets, but it cannot satisfy stable-handoff evidence unless it is
  paired with a durable local artifact ref that can be reopened later.
- Harness-affecting or protected changes require search-set before/after refs or
  targeted skipped-evidence records with provenance. Missing before/after search
  refs must not silently pass stable handoff.
- Runtime, public, or proof-like claim records require raw evidence refs such as
  logs, exported traces, screenshots, or repository artifacts.
- Content rules can raise otherwise routine docs paths to high-risk when they
  contain proof-like claims.
- Post-import `archive/v1/` archive-edit waivers must be represented as targeted
  packet judgment/evidence records before a packet can be stable.
- Stable packets must close every required evidence item through exactly one
  packet-local acceptance record: passed durable evidence, targeted waiver,
  targeted downgrade, or targeted skipped evidence with provenance.
- `start`/`finalize` remain small: they may capture local refs and command status
  that they can honestly observe, but they do not import reviews or archive
  packets.

## Scope

In scope:

- `scripts/check-governance-acceptance.py`
- tests for source-ref validation, artifact-ref validation, search-set evidence
  closure, proof-like claim rules, and archive-waiver evidence representation
- Plan 04 fixtures only if new negative or positive examples are required
- `backlog/v2-roadmap.md` and this plan

Out of scope:

- Review transcript import, critic rerun parsing, or multi-review record
  generation
- Packet archive storage, canonical hashing, active pointers, or immutable packet
  indexes
- Release/pre-commit integration
- Network validation of URLs or external artifacts
- Full natural-language proof detection; Plan 04 uses conservative seed content
  rules only

## Evidence Model

Plan 04 keeps the public surface unchanged and adds detail under
`result.evidence`:

- `source_refs`: caller-provided or generated refs to local files, packet files,
  trace files, commits, or terminal records.
- `resolved_refs`: generated ref resolution records with `origin`, `relation`,
  `ref`, `status`, and durable target details.
- `command_results`: local commands the harness actually ran or verified from
  packet fixtures.
- `artifact_refs`: durable local artifacts that command results or claim records
  point to.
- `trace_refs`: search-set before/after refs, evolution refs, failure refs, and a
  disposition.
- `claims`: structured runtime, public, or proof-like claims with required raw
  evidence refs.

Allowed source-ref forms:

- repository paths, for example `docs/usage.md`
- `file:<repo-path>`
- `trace:<repo-path>#<anchor>`
- `terminal:<id>` for current Plan 03/04 local terminal placeholders in valid
  non-stable packets only
- `git:<ref>` or `git:<ref>:<path>` when git can resolve the ref

Unsupported or missing refs fail stable handoff.

For stable packets, each ref that participates in evidence closure must have a
generated `resolved_refs` record:

- `origin`: `input` or `generated`
- `relation`: `source`, `artifact`, `trace`, `claim-evidence`,
  `review-provenance`, or `waiver-provenance`
- `ref`: the original ref string
- `status`: `resolved`
- `target`: the resolved repository path, git object/path, or trace anchor

`terminal:<id>` may be recorded as `relation: observation` with
`status: local-placeholder`, but that relation is never sufficient for stable
handoff evidence closure.

## CLI Semantics

### `start`

- Preserve `baseline_ref` for all modes.
- For `--base-ref`, record the exact comparison ref and require finalize to use
  the same ref.
- For stable packets, `baseline_ref` and `comparison_ref` must resolve to the git
  boundary used by the finalized evidence.
- Do not capture search-set evidence beyond refs that already exist locally.

### `finalize`

- Preserve `baseline_ref` and `comparison_ref`.
- Run only local command-status checks the skeleton can honestly observe.
- For protected or harness-affecting changes, record missing search-set
  before/after refs as skipped evidence unless explicit refs are supplied by later
  implementation options.
- Infer high-risk claim requirements when changed text contains proof-like
  phrases such as `verified`, `guaranteed`, `proves`, `runtime`, `public API`,
  `release-ready`, or `production-ready`. This is a risk-classification trigger,
  not a semantic proof checker.
- Do not mark protected, harness-affecting, proof-like, or archive-waiver packets
  stable during Plan 04 finalization unless the required evidence is already
  represented and `check --require-stable` accepts it.

### `check`

- Validate source refs and artifact refs for stable packets.
- Validate generated `resolved_refs` for stable packets and reject mixed-origin
  or relation-less refs.
- Reject `terminal:<id>` as stable evidence unless a durable artifact relation
  also resolves the same evidence item.
- Validate `baseline_ref` and `comparison_ref` resolution and ensure they match
  the finalized evidence boundary.
- Validate search-set before/after closure for harness-affecting stable packets.
- Validate proof-like claim records and raw evidence refs for stable packets.
- Validate that archive-edit waiver/downgrade records are targeted, typed, and
  durable in `result.judgment`/`result.evidence`.
- Validate that residual-risk, skipped-evidence, waiver, and downgrade records
  close specific required evidence/review items rather than broad categories.
- Keep packet validity distinct from stable-handoff eligibility.

## Invariants

- Stable packets cannot rely on missing files, unsupported ref schemes, or
  unresolvable git refs.
- Stable packets cannot rely on `terminal:<id>` placeholders as durable evidence.
- Stable packets cannot use string-only source refs as proof for runtime/public
  claims; they need raw evidence refs.
- Stable packets cannot mix input-provided refs and generated refs without
  generated `resolved_refs` records that preserve `origin` and `relation`.
- Stable protected changes cannot omit search-set before/after refs unless
  skipped evidence is targeted and carries actor, role, date, reason, and source.
- Stable packets cannot preserve `baseline_ref` or `comparison_ref` as strings
  only; those refs must resolve to the git comparison boundary used by evidence.
- A source ref and an artifact ref are not interchangeable unless the record
  explicitly names the relation.
- Any out-of-scope evidence limitation must be represented in packet evidence or
  roadmap carry-over, not only in conversation.

## Validation

Run:

```bash
python3 -m unittest tests/test_acceptance_packet_fixtures.py
python3 -m unittest tests/test_governance_acceptance_cli.py
python3 -m unittest tests/test_governance_evidence_refs.py
python3 -m unittest tests/test_governance_evidence_false_greens.py
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-routine.yml --require-stable
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml --require-stable
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml --require-stable
git diff --check
```

## Search-Set Verification

Search-set verification:

- BEFORE: SKIPPED no pre-change search-set run was captured before implementing
  the Plan 04 false-green corrections.
- AFTER: FAIL `python3 scripts/run-search-set.py` before this evidence block was
  added; SS-003 reported missing search-set evidence for the staged
  harness-affecting checker change.
- AFTER: PASS `python3 scripts/run-search-set.py` after adding this evidence
  block and rerunning the active search-set.

## Multi-Review Requirements

Use the current `multi-review` skill protocol.

Problem framing must include the `Decision`, `Stakes`, `Constraints`, and
`Presuppositions` above. Critic prompts must either include one presupposition
challenge or explicitly allow each critic to say the question itself is wrongly
framed.

Required critic lenses:

- Contract Fidelity Critic: packet surface, generated/user boundary, and ref
  schema shape.
- Decision Correctness Critic: false stable handoff, exit/status labels, missing
  evidence, and proof-like claims.
- Auditability Critic: finalized packet preserves refs, criteria, provenance, and
  rationale without conversation context.
- Adversarial Artifact Critic: stale packet, fake refs, ambiguous terminal refs,
  evidence/review identifier collisions, and unsupported schemes.
- Scope Boundary Critic: confirms Plan 04 does not implement Plan 05 review
  import, Plan 06 complexity consolidation, Plan 07 archive pointers/hashing, or
  Plan 08 release integration, and that deferred risks are durably carried
  forward.

For repository governance work, any score below 9 is VETO until fixed and rerun.
Every score 9 must record why-not-10 and residual-risk or follow-up disposition.
No final PASS is valid unless at least one critic records a concrete
false-green path and the invariant that catches it.

## Plan Review Outcome

Multi-review:

- Contract fidelity critic: score 8, VETO on first pass. Blocking findings:
  mixed input/generated refs lacked origin/relation, and `terminal:<id>` could
  satisfy stable evidence without durable material. Rerun score 9, PASS. Why not
  10: `source_refs` remains broad, with `resolved_refs` carrying the
  disambiguating contract. Follow-up/residual risk: accepted for Plan 04 because
  stable evidence closure now requires generated origin/relation/status/target
  records.
- Decision correctness critic: score 4, VETO on first pass. Blocking findings:
  unsupported refs, missing artifacts, missing search-set refs, and proof-like
  claims could still falsely pass in the current implementation. Rerun score 9,
  PASS. Why not 10: proof-like detection remains conservative seed-rule work,
  not full semantic claim detection. Follow-up/residual risk: accepted as a Plan
  04 implementation boundary with negative tests required.
- Auditability critic: score 7, VETO on first pass. Blocking findings:
  terminal placeholders were not durable, baseline/comparison refs were not tied
  to the finalized evidence boundary, and skipped/residual closure was not
  packet-local enough. Rerun score 9, PASS. Why not 10: the roadmap needed a
  short mirror of Plan 04's terminal/baseline invariant, now added. Follow-up/
  residual risk: accepted for Plan 04.
- Scope-boundary and presupposition critic: score 9, PASS on first pass and score
  10 after rerun. Blocking findings: none. Why not 10 on first pass: the plan
  still needed explicit wording that local durability validation does not claim
  archive immutability. Follow-up/residual risk: accepted after rerun because the
  scope boundary now keeps archive integrity in later plans. Presupposition
  assessed: local evidence refs can be validated before archive integrity exists,
  as long as Plan 04 validates local durability without claiming immutable
  archive guarantees.
- False-green coverage: critics named concrete stale or hand-authored stable
  packet paths involving terminal-only evidence, copied input refs, unsupported
  schemes, unresolved artifacts, missing search-set refs, and disappeared
  out-of-scope archive risk.
- Score handling: all VETO findings were fixed in the plan and affected critics
  reran to at least 9.
- Rerun status: contract fidelity, decision correctness, and auditability critics
  reran after plan fixes; scope-boundary critic reran to confirm no scope creep.
- Follow-up/residual risk: Plan 04 implementation must add the listed negative
  tests before acceptance.
- Final acceptance: accepted for Plan 04 planning.

## Implementation Review Outcome

Multi-review after implementation:

- Contract fidelity critic: score 9, PASS. Why not 10: `source_refs` remains a
  broad string list and `resolved_refs` carries the origin/relation contract.
  Disposition: accepted for Plan 04 because stable validation requires input
  source refs to be mirrored and resolved with `origin: input`.
- Decision correctness critic: score 9, PASS. Why not 10: proof-like claim
  detection remains a conservative seed rule based on changed markdown paths.
  Disposition: accepted for Plan 04; later plans may improve semantic claim
  detection.
- Auditability critic: score 7, VETO on first implementation pass because review
  provenance could remain terminal-only and stable packets could omit
  `baseline_ref`/`comparison_ref`. Rerun score 9, PASS after adding
  `review-provenance` closure and requiring stable boundary refs. Why not 10:
  the plan relation list initially omitted `review-provenance`; corrected here.
- Scope-boundary and presupposition critic: score 10, PASS. It found no
  unacceptable scope creep because the public packet surface remains
  `meta`/`input`/`result`, and archive integrity/review import remain deferred.
- False-green coverage: tests now cover terminal-only artifacts, unsupported or
  wrong-origin source refs, missing artifact files, missing protected search-set
  refs, base-ref boundary mismatch, archive/v1 routine misclassification,
  proof-like docs without raw evidence, broad skipped evidence, unresolved
  skipped provenance, missing stable boundary refs, and terminal-only review
  provenance.
- Final acceptance: accepted for Plan 04 implementation after affected VETO
  critic rerun reached 9.

## Follow-up False-Green Corrections

Additional Plan 04 review found runnable false-green gaps after the initial
implementation acceptance. The earlier PASS is treated as an artifact under
review, not as evidence that these probes had succeeded:

- Stable evidence obligations could be erased by hand-editing
  `required_evidence` and `command_results` to empty. Correction: stable packets
  must match evidence obligations computed by the checker from packet mode,
  changed paths, and stable boundary refs; `required_evidence` and
  `result.evidence.evaluator_boundary.commands` are both checked against that
  derived set. False-green tests mutate `finalized-routine.yml` to prove
  erasure, non-empty spoofing, and packet-authored evaluator-boundary spoofing
  all fail.
- Repository refs could escape the repository root through absolute `file:` or
  bare paths. Correction: local ref resolution now rejects absolute paths,
  parent traversal, and paths that resolve outside the repository root.
- Base-ref boundary parsing missed the `--base-ref=<ref>` form. Correction:
  command base-ref parsing now recognizes both separated and equals forms.
- Command evidence could point at an unrelated existing repository file and still
  satisfy artifact existence. Correction: stable command artifacts must record
  the command string and status they support.
- Protected source refs could hide behind routine `changed_paths`. Correction:
  stable validation now requires changed paths to have resolved source refs and
  rejects protected source refs outside the changed-path set.
- Review provenance could point at an unrelated existing file and still close
  required reviews. Correction: stable review-provenance refs must resolve to a
  bounded `record_type: governance-review` record that matches the packet id,
  critic, actor, role, date, score, veto, and score-9 disposition fields.
- Review provenance could self-attest by pointing back at an acceptance packet
  that already contains matching review fields. Correction: stable
  review-provenance refs cannot be acceptance packet files.
- The documented `tests/test_governance_evidence_false_greens.py` validation file
  was missing. Correction: the module now exists and covers the false-green
  regressions above.
- Review-system correction: durable/governance multi-review now requires
  independent adversarial probes and a Review Quality Meta-Critic before PASS.

## Open Questions

- Should proof-like content rules be regex-only in Plan 04, or should they use a
  small structured claim marker to avoid over-triggering prose?
- Should source refs remain strings through Plan 04, or should Plan 04 introduce
  optional object refs under `result.evidence` while preserving string input refs?

## Negative Test Requirements

- A stable packet with `artifact_ref: terminal:<id>` and no durable artifact
  relation must fail.
- A stable packet that copies input refs into `result.evidence.source_refs`
  without generated `resolved_refs` origin/relation records must fail.
- A stable packet with `baseline_ref` or `comparison_ref` that cannot be resolved
  to the finalized comparison boundary, or that omits either field, must fail.
- A protected stable packet with missing search-set before/after refs and no
  targeted skipped-evidence provenance must fail.
- A stable packet with runtime/public/proof-like claims and no raw evidence refs
  must fail.
- A stable packet where one residual-risk or skipped-evidence record attempts to
  close a broad category instead of a specific required evidence item must fail.
- A stable packet with review provenance that points only to terminal or
  conversation context must fail.
- A stable packet that erases generated required evidence obligations must fail.
- A stable packet whose command artifact points to an unrelated existing file
  must fail.
- A stable packet whose source refs include protected paths hidden outside
  `changed_paths` must fail.
- A stable packet whose review provenance points to an unrelated existing file
  must fail.
- A stable packet whose review provenance points back at an acceptance packet
  file must fail.
