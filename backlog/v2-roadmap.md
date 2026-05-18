# AI Agent Meta-Harness v2 Roadmap

v2 replaces human-authored maintenance gates with generated acceptance packets.
The goal is a smaller operator surface and stronger mechanical governance:
humans provide intent, exceptions, waiver requests, and residual-risk acceptance;
the harness infers requirements, captures evidence, and computes eligibility.

## Target Shape

```yaml
AcceptancePacket:
  meta: {}
  input: {}
  result:
    inference: {}
    evidence: {}
    judgment: {}
    decision: {}
```

CLI surface:

```bash
governance start --base-ref <comparison-ref> --intent "..."
governance finalize --packet <packet> --base-ref <comparison-ref>
governance review-template --packet <packet> [--output <artifact>|--scratch-output <draft>]
governance import-review --packet <packet> --from <review-artifact-or-stdin> [--output <artifact>]
governance write-pointer --packet <packet>
governance check --packet <packet> --require-stable
governance status --base-ref <comparison-ref>
```

Stable handoff should use `--base-ref`. `--staged` is a preflight mode, and
`--worktree` is always non-stable exploratory/in-progress evidence.
`import-review` is required only when inference or policy requires durable
review judgment.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py` before this hardening batch
  verified active repository search-set cases while `scripts/check-governance-acceptance.py`
  was in scope.
- AFTER: PASS `python3 scripts/run-search-set.py` after this hardening batch
  verified active repository search-set cases while `scripts/check-governance-acceptance.py`
  was in scope.
- RECORDED: this roadmap started as v2 transition planning evidence. The current
  workspace now includes the v2 acceptance-packet checker and stable fixture
  checks; remaining search-set notes here are historical planning context unless
  a later plan explicitly marks them as active release evidence.

Multi-review:

- Governance boundary critic: score 9.2 PASS, critic scope active
  stable-handoff fixture/deletion/benchmark leakage boundary, Blocking findings:
  none after implementation, why not 10: command-evidence authenticity remains
  a Plan 07 residual risk.
- Blocking findings: none remaining for the accepted feedback batch.
- Follow-up/residual risk: command-evidence authenticity remains Plan 07 archive
  ownership work; this batch only tightens current structural false greens.
- Score handling: score 9.2 keeps why-not-10 residual risk in Plan 07 rather
  than adding new active workflow surface.
- Rerun status: rerun completed after implementation and release validation.
- Final acceptance: PASS for this hardening batch.
- Accepted current feedback on fixture materialization bypass, deleted-path
  source refs, benchmark sealed-oracle leakage, benchmark-generated transcript
  binding, and stale roadmap wording.
- Implementation narrows active fixture exemption to canonical fixtures plus
  test-only materialization, allows comparison-pinned refs only for deleted
  active base-ref paths, and binds public transcript metadata to the actual
  scenario result ref.
- Validation: PASS `python3 -m unittest tests.test_governance_evidence_false_greens tests.test_governance_review_import tests.test_multi_review_benchmark_cli`.
- Validation: PASS `python3 -m unittest discover -s tests`.
- Validation: PASS `python3 benchmarks/multi-review/check-fixtures.py --allow-pending`.
- Validation: PASS `python3 benchmarks/multi-review/check-fixtures.py --replay-probe-commands --allow-pending`.
- Validation: PASS `python3 scripts/update-governance-fixtures.py --check`.
- Validation: PASS `python3 scripts/verify-release.py --skip-clean-worktree`.

## Methodology Plan

v2 must preserve the Meta-Harness essentials:

- Fixed evaluator boundary: packet records evaluator commands, protected paths,
  boundary changes, and disposition. Candidate evidence must state whether the
  evaluator stayed fixed, was intentionally changed with disposition, or is not
  eligible as fixed-evaluator evidence.
- Trace reuse: packet records search-set before/after evidence, evolution trace
  disposition, and failure trace disposition.
- Confounder isolation: packet records intended scope, actual changed files,
  deviations, and isolation status.
- Evidence honesty: runtime/public/proof claims require structured claim records;
  verified claims require raw artifact, log, screenshot, or exported trace refs.
- Human judgment boundary: residual risk, skipped required evidence, review
  waiver, or downgrade acceptance requires actor, role, date, reason, and
  source reference.

## Architecture Plan

1. Define the `AcceptancePacket` schema with the three public sections:
   `meta`, `input`, and `result`.
2. Define `result.inference`, `result.evidence`, `result.judgment`, and
   `result.decision` as stable machine-readable sub-sections.
3. Define canonical packet hashing. The current active model keeps packet
   digests in active pointers and review-import target bindings. Any future
   packet-internal hash must avoid self-reference by excluding the hash field
   from canonical serialization or by using an equivalent non-self-referential
   rule.
4. Define source reference validation. Active base-ref stable handoff requires
   changed-path refs to be commit-pinned to the accepted side
   (`git:<full-commit-sha>:<repo-path>` for additions/modifications, and the
   comparison side for deletions). Broader packet input, review artifacts, trace
   artifacts, log files, commits, or maintainer notes are allowed only for
   fixture, non-active, or later archive contexts.
5. Define packet archive paths, initially `archive/v2/packets/<packet_id>.yml`
   unless implementation review chooses a stronger location such as
   `.harness/governance/packets/`, plus active pointer format and optional hash
   validation.

## Governance Checker Plan

Create one checker command:

```bash
python3 scripts/check-governance-acceptance.py start --base-ref <comparison-ref> --intent "..."
python3 scripts/check-governance-acceptance.py finalize --packet <packet> --base-ref <comparison-ref>
python3 scripts/check-governance-acceptance.py write-pointer --packet <packet>
python3 scripts/check-governance-acceptance.py check --packet <packet> --require-stable
```

Required behavior:

- `start` captures baseline git state, trace-root state, human intent, checker
  version, inference rules version, and any available before evidence.
- `finalize` updates packet evidence, infers class/impact from git diff and
  content rules, computes required evidence/review/traces, and computes
  `result.decision.stable_handoff_eligible`.
- `check` is read-only and never changes packet lifecycle state.
- Harness-affecting finalization fails closed without a start packet unless an
  exact skipped-before reason and maintainer/reviewer disposition are recorded.
- Verified runtime claims fail without raw evidence refs.
- Score below 9 fails unless the same review scope reruns at 9 or above, or the
  packet is not accepted.
- Score 9 requires why-not-10 and residual/follow-up disposition.

## Inference Plan

Keep inference explicit and inspectable.

- Maintain a small path/content rule table for durable-contract and
  harness-affecting changes.
- Default high-risk paths to stricter requirements, then allow downgrade only
  with recorded disposition.
- Keep non-harness exemptions explicit and tested.
- Version the inference rule table separately from checker implementation.

Initial high-risk surfaces:

- `core/`
- `adapters/`
- `scripts/`
- `.githooks/`
- `.harness/traces/search-set.md`
- `commands/`
- `skills/`
- `plugins/`
- `MAINTENANCE.md`
- `README.md`
- runtime adapter docs, install docs, release notes, and public evidence claims

## Migration Plan

1. Treat `archive/v1/` as frozen historical trace evidence.
2. Do not carry v1 backlog items forward by default.
3. Extract only v2 requirements that correspond to repeated v1 failure modes:
   manual class declaration, missing before evidence, review waiver ambiguity,
   runtime proof overclaiming, score/VETO drift, and archive record drift.
4. Keep legacy archive compatibility while v2 packet archive validation is added:
   `scripts/check-v1-archive-boundary.py` reports that `archive/v1/` is frozen
   historical evidence, allows the initial import, and blocks later archive
   changes unless a maintainer/reviewer waiver records a concrete reason.
5. After release/pre-commit packet-pointer gating exists, require new completed
   active work to point to finalized accepted packets.

## Implementation Plan

1. Compatibility checker migration: keep frozen `archive/v1/` records
   intentionally exempt from active v1 record-shape validation, report that
   boundary explicitly, and add tests so legacy checks cannot create false
   confidence about unvalidated archive paths.
2. Schema and fixtures: add packet schema examples for start, finalized routine,
   finalized harness-affecting, finalized waiver/downgrade, runtime evidence,
   and blocked packets. Plan 02 owns the first fixture set under
   `backlog/fixtures/acceptance-packets/`; these are checker fixtures, not
   active archived governance packets. Some finalized fixtures are
   stable-handoff eligible positive controls, and non-stable fixtures are
   negative controls.
3. Packet CLI skeleton: implement `start`, `finalize`, and `check` without
   replacing release gates. Plan 03 owns the repository-local
   `scripts/check-governance-acceptance.py` skeleton and keeps packet validity
   separate from stable-handoff eligibility via `--require-stable`.
4. Evidence capture: add search-set before/after capture and source-ref
   validation. Carry forward Plan 03's residual requirement that post-import
   `archive/v1/` waiver provenance must move from bootstrap CLI strings into
   durable packet judgment/evidence before accepted archive edits rely on v2
   governance. Add content rules so runtime, public, or proof-like documentation
   claims infer high-risk evidence requirements even when the changed paths are
   otherwise routine docs paths. Stable packets must use generated resolved-ref
   records with origin, relation, resolved status, and durable target; terminal
   placeholders alone cannot satisfy stable evidence, and baseline/comparison
   refs must resolve to the finalized evidence boundary.
5. Review import: add structured review records with score, VETO, rerun,
   false-green coverage, durable review provenance, and score-9 handling. The
   checker must infer mandatory-review categories from changed paths and change
   content; `not required` is a waiver/downgrade, not a generic bypass, and must
   record actor, role, date, reason, and source. Failed reviews must remain in
   the packet and can be closed only by same-target reruns that score at least 9
   with `veto: false`.
6. Complexity consolidation: before archive integration, reduce operational
   complexity from Plans 03-05 by documenting ref taxonomy, adding or specifying
   fixture regeneration, and making anti-bloat review an explicit governance
   critic.
7. Archive integration and deferred integrity backlog: use
   `backlog/plans/07-packet-archive-and-integrity-backlog.md` to add packet
   archive pointers, archive-bound freshness, durable plan-approval evidence, and
   semantic-evidence backlog boundaries without expanding the public packet
   surface. Post-import `archive/v1/` waiver provenance must move from bootstrap
   CLI input into durable packet judgment/evidence before accepted archive edits
   are allowed.
8. Release integration: wire packet checks into pre-commit/release once the v2
   checker covers v1 review/search/archive invariants.
9. Documentation transition: update README and maintenance guidance from v1 gates
   to v2 packet lifecycle.
10. Stable packet materialization and operator-minimal CLI: use
   `backlog/plans/10-stable-packet-materialization-and-operator-minimal-cli.md`
   to make stable closure generation, multi-review import, active pointer
   publication, and archive status reporting routine commands rather than
   manual YAML/hash/provenance work.
11. Residual hardening and operations: use
   `backlog/plans/11-v2-residual-hardening-and-operations.md` to label the
   remaining work outside the Plan 10 v2 core without overstating completion.

## v2 Completion Boundary

Plan 10 completes the v2 core governance path: the `governance` wrapper,
packet lifecycle, multi-review import, active pointer publication, status
inventory, and release/pre-commit active packet gate can run through a
single-publication release shape. Plan 11 closes the remaining residual labels
for the v2 active model without claiming optional post-v2 features such as
package-manager distribution, chained active publication releases, or
packet-internal hashes.

Residual labels:

- `v2-residual-01 legacy-v1-boundary`: frozen `archive/v1` records remain
  historical compatibility evidence, not active v2 handoff records.
- `v2-residual-02 historical-fixture-boundary`: fixtures, benchmark
  transcripts, and historical review artifacts are examples or archived traces
  unless active `archive/v2` pointers publish them.
- `v2-residual-03 governance-packaging`: closed for v2. `governance` is the
  public repository command and delegates to the same checker logic; external
  installation/exposure is post-v2 distribution work.
- `v2-residual-04 multi-publication-release`: the routine accepted release
  model is content commits first, then one active archive publication per
  base-ref release range; chained publications need an explicit later model
  that validates each publication boundary in order and rejects archive drift
  hidden by later reverts.
- `v2-residual-05 checker-versioned-history`: closed for v2. Active pointers
  bind checker and inference rule versions; mismatches mark historical
  compatibility evidence rather than current stable proof.
- `v2-residual-06 worktree-mode-boundary`: closed for v2. `--worktree` is
  always non-stable exploratory/in-progress evidence, `--staged` is preflight,
  and stable handoff uses `--base-ref`.
- `v2-residual-07 packet-hash-placement`: closed for v2. Active pointers and
  review-import target bindings are the current packet digest roots; adding a
  packet-internal hash is optional post-v2 design work.
- `v2-residual-08 release-command-replay-gate`: accepted as post-v2 hardening.
  The release/base-ref active packet gate must replay pointer-bound command
  evidence; staged preflight and stable packet `check` remain non-executing.
- `v2-residual-09 search-set-trace-fidelity`: closed for repository-local v2.
  `governance capture-search-set --phase before|after` records reusable
  `.harness/traces/search-set.md` anchors, and `governance finalize
  --search-set-before/after` binds those refs instead of targeted skips.
- `v2-residual-10 review-template-completion-ergonomics`: accepted as post-v2
  simplification. `review-template` owns the target-bound skeleton, but a
  future helper can reduce reviewer field-editing without auto-certifying PASS.
- `v2-residual-11 publish-wrapper-ergonomics`: closed for repository-local v2.
  `governance publish` composes the safe primitives for already-stable packets
  while preserving content commits first and one archive-only publication commit
  last.
- `v2-residual-12 agent-in-loop-multi-review-eval`: closed as an evaluation
  contract for repository-local v2. The perspective scorer emits public-only
  agent prompts and scores candidate outputs against sealed rubric criteria for
  critic diversity, issue/disagreement preservation, and evidence relevance;
  it remains calibration infrastructure, not a replacement for reviewer
  judgment or a future AI judge.

## Validation Plan

Validate v2 using the method it introduces:

- Use the current packet lifecycle for active v2 implementation work:
  `governance start --base-ref <comparison-ref> --intent "..."`,
  `governance finalize --packet <packet> --base-ref <comparison-ref>`, and
  `governance review-template --packet <packet> [--output <artifact>|--scratch-output <draft>]` when
  durable review judgment is required, then
  `governance import-review --packet <packet> --from <review-artifact-or-stdin> [--output <artifact>]`
  after reviewers complete the draft artifact, then `governance publish
  --packet <packet>`, followed by `governance check --packet <packet>
  --require-stable`.
- Treat older bootstrap transition notes as archived compatibility evidence,
  not as the current implementation path.
- Preserve before/after search-set evidence where relevant.
- Run multi-review for packet schema, checker semantics, complexity
  consolidation, archive integration, and release gate wiring.
- Treat any critic score below 9 as blocking until fixed and rerun.
- Preserve v2 packet examples as trace artifacts.

## Post-v2 Design Choices

- Whether to add package-manager distribution for `governance`; the current
  repository-local executable is the v2 command surface.
- Whether to add chained active publication release support; current v2 accepts
  one active archive publication per base-ref release range.
- Whether to add a packet-internal hash later; current active validation stores
  packet digests in active pointers and review-import target bindings.
- Which future stable-closure gaps are safe for materialization commands to
  repair automatically, and which must remain explicit human judgment.
- Whether to add a review completion helper that keeps human judgment explicit
  while reducing manual probe/lineage YAML edits.
- Whether to package `governance publish` outside the repository-local command
  surface; current semantics stay in the repo-local wrapper.
- Whether to replace or augment the perspective-eval calibration scorer with an
  AI judge; current scoring remains deterministic calibration, not a claim of
  full semantic adjudication.
