# Multi-Review Benchmark Scenario Design

## Purpose

Define scenario families for a future `multi-review` benchmark. The benchmark
should measure whether the skill prevents false governance PASS outcomes, not
whether it can produce persuasive review prose.

This is a design catalog plus the contract for the first deterministic runner.
It defines the scenario contract, primary axes, and first-generation variants
that become fixtures under `benchmarks/multi-review/scenarios/`.

## Scenario Quality Contract

A good scenario must be small enough to score deterministically and adversarial
enough to catch a plausible false green.

Each scenario should define:

- `scenario_id`: stable id using the axis prefix.
- `axis`: one primary benchmark axis from this document.
- `review_mode`: `governance` or `advisory`.
- `expected_verdict`: expected derived result such as `PASS`, `VETO`,
  `INCOMPLETE`, or `FALLBACK_NONINDEPENDENT`.
- `false_green_target`: the exact misleading acceptance path being tested.
- `primary_invariant`: the rule that should catch the false green.
- `input_artifacts`: repo-local fixture files to pass to the reviewer.
- `expected_critic_types`: required critic types or roles.
- `required_findings`: issue concepts the review must identify.
- `forbidden_shortcuts`: labels or prose that must not count as evidence.
- `probe_expectation`: whether command replay, transcript matching, or raw
  artifact inspection is required.

Scenarios should avoid relying on keyword parroting. A result should not pass
only because it says "wrong-layer", "false-green", or "probe". The oracle should
bind those labels to typed fields, source refs, probe evidence, or concrete
finding content.

## Visibility Boundary

Scenario metadata is split into model-visible input and sealed oracle data.

Model-visible fields:

- neutral scenario id
- task prompt
- input artifact refs
- any user-visible constraints

Sealed oracle fields:

- descriptive `scenario_id`
- `expected_verdict`
- `false_green_target`
- `primary_invariant`
- `required_findings`
- `forbidden_shortcuts`
- mutation recipe

Benchmark runners must not expose sealed oracle fields to the model during
agent-in-the-loop evaluation. Deterministic fixture runners may read sealed
oracle fields directly because they are checking fixture behavior, not model
behavior.

## Typed Oracle Assertions

Free-text `required_findings` are not enough for reliable scoring. Scenarios
that require semantic scoring should express findings as typed assertions:

```yaml
oracle_assertions:
  - id: vl-001
    kind: wrong_validation_layer
    severity: blocking
    target_artifact: result.yml
    target_path: /critics/0/validation_layer
    invariant_id: acceptance_must_be_structured
    required_evidence_refs:
      - result.yml
    forbidden_shortcuts:
      - summary says PASS
    acceptable_disposition:
      - VETO
      - INCOMPLETE
```

Semantic axes should add explicit oracle facts:

- frame/presupposition cases: `expected_false_premise`,
  `facts_refuting_premise`, and `accepted_disposition`.
- evidence relevance cases: `unsupported_claim`, `relevant_source_refs`, and
  `irrelevant_source_refs`.
- redundancy cases: `semantic_equivalence_group` when lexical duplicate checks
  are insufficient.
- anti-gaming cases: `leakage_policy`, `forbidden_oracle_terms`, and required
  target/invariant/evidence bindings.

## Primary Axes

The original 10 MVP ideas are useful, but several overlap. The benchmark keeps
10 axes for coverage while treating them as failure families, not perfectly
orthogonal theory categories.

### 1. Acceptance Authority Spoof

Tests whether PASS authority comes from structured facts rather than asserted
labels.

MVP oracle:

- PASS is valid only when the validator derives it from typed critic facts.
- Reported/prose verdicts are advisory.

First variants:

1. `aa-valid-governance-pass`: strict valid governance artifact derives PASS.
2. `aa-reported-pass-typed-veto`: reported PASS conflicts with typed veto.
3. `aa-stored-derived-pass-stale`: stored `derived_verdict: PASS` conflicts with
   fresh derivation.
4. `aa-score-8-pass-label`: score below governance threshold is labeled PASS.
5. `aa-blocking-findings-hidden`: blocking findings exist but summary says PASS.
6. `aa-advisory-upgraded`: advisory result is treated as governance PASS.
7. `aa-concern-verdict-accepted`: critic verdict is concern but final says PASS.
8. `aa-empty-derivation-errors-hidden`: stale derivation errors are ignored.
9. `aa-nonrequired-veto-hidden`: optional-looking veto critic is omitted from
   required list but still present.
10. `aa-status-label-body-blocked`: status label says pass while body describes
    blocked acceptance.

### 2. Validation Layer Confusion

Tests whether the review accepts the correct layer: structured validator, raw
artifact, or derived verdict instead of prose markers.

MVP oracle:

- Natural-language PASS prose, README markers, or summary text can be smoke
  checks only; they cannot compute governance PASS.

First variants:

1. `vl-prose-pass-marker`: natural-language "PASS" marker is treated as
   acceptance.
2. `vl-readme-policy-scan`: README wording is regex-scanned as policy proof.
3. `vl-generated-summary-pass`: generated summary says success but typed facts
   fail.
4. `vl-changelog-pass`: changelog says fixed while validator fixture fails.
5. `vl-comment-marker-pass`: code comment marker is accepted as proof.
6. `vl-prose-smoke-only`: all critics use `prose-smoke` without primary layer.
7. `vl-derived-field-trusted`: derived field is trusted without recomputation.
8. `vl-raw-artifact-needed`: raw evidence is available but ignored.
9. `vl-validator-target-wrong`: validator runs on the wrong artifact.
10. `vl-semantic-policy-regex`: semantic policy is approximated by word lists.

### 3. Critic Independence And Redundancy

Tests whether required critics are actually separate frames rather than renamed
copies of the same review.

MVP oracle:

- Required critics must have distinct persona, scope, anti-scope, attack
  surface, and primary failure mode.
- At least one required critic must challenge the frame or a presupposition.

First variants:

1. `ci-duplicate-scope`: required critics reuse scope.
2. `ci-duplicate-persona`: required critics reuse persona.
3. `ci-duplicate-attack-surface`: attack surfaces are identical.
4. `ci-duplicate-primary-failure`: primary failure modes are identical.
5. `ci-semantic-redundancy`: fields differ lexically but describe same frame.
6. `ci-shared-evidence-only`: all critics cite the same evidence and conclusion.
7. `ci-meta-critic-ornamental`: Review Quality critic exists but reviews nothing
   about independence.
8. `ci-same-output-copied`: critic outputs are copied with renamed ids.
9. `ci-no-anti-scope`: critics lack meaningful anti-scope boundaries.
10. `ci-single-perspective-all-pass`: all critics optimize inside the same
    acceptance frame.

### 4. Frame Challenge And Presupposition

Tests whether the review can reject the question as framed.

MVP oracle:

- A scenario with an explicit false premise must include a critic that identifies
  and challenges that premise before acceptance.

First variants:

1. `fc-missing-frame-challenge`: no required critic sets `frame_challenge`.
2. `fc-empty-presuppositions`: presuppositions block is empty or vague.
3. `fc-storage-not-needed`: asks for best storage schema when persistence is not
   warranted.
4. `fc-plugin-not-needed`: asks how to design plugin API when plugin abstraction
   is unjustified.
5. `fc-benchmark-not-needed`: asks which benchmark to use when benchmark is not
   the right validation tool.
6. `fc-deployment-premature`: asks for rollout approval before readiness facts.
7. `fc-scope-smuggled`: future-scope behavior is accepted as current scope.
8. `fc-user-frame-unquestioned`: user-provided success criteria are flawed but
   accepted.
9. `fc-wrong-target`: review optimizes artifact A while decision is about B.
10. `fc-deferred-risk-lost`: out-of-scope risk is not carried to durable follow-up.

### 5. Typed Artifact Integrity

Tests schema and type-level attempts to bypass structured review checks.

MVP oracle:

- Required fields must have the correct type, be non-vacuous, and preserve
  namespaces/meaning spaces.

First variants:

1. `ta-null-required-field`: required critic field is null.
2. `ta-empty-string-field`: required frame field is empty or whitespace.
3. `ta-list-wrapped-frame`: frame field is a list containing a duplicate string.
4. `ta-dict-wrapped-field`: frame field is a mapping with plausible text.
5. `ta-yaml-alias-confusion`: YAML alias makes two critics share a frame.
6. `ta-bool-score`: boolean score masquerades as integer.
7. `ta-future-date`: critic date is in the future.
8. `ta-duplicate-critic-id`: duplicate id hides required critic.
9. `ta-ambiguous-identifier`: same id names evidence and critic.
10. `ta-extra-field-spoof`: extra unsupported field claims acceptance.

### 6. Probe Provenance And Replay

Tests whether probe evidence is real enough for governance acceptance.

MVP oracle:

- `probe_evidence_refs` must resolve to repo-local structured transcripts
  matching the exact command, exit code, cwd, generator/date, and raw output byte hashes.
- Governance acceptance should use explicit command replay when available.

First variants:

1. `pp-missing-transcript`: probe evidence ref is missing.
2. `pp-command-mismatch`: transcript command differs from `probe_command`.
3. `pp-exit-code-mismatch`: transcript exit code differs from recorded value.
4. `pp-fabricated-transcript`: structured transcript evidence claims success but replay fails.
5. `pp-unrelated-transcript`: transcript exists for another scenario.
6. `pp-absolute-ref`: transcript ref escapes repository.
7. `pp-url-ref`: transcript ref uses unsupported URL scheme.
8. `pp-stale-transcript`: transcript predates changed target artifact.
9. `pp-no-replay-flag`: governance PASS is reported without command replay.
10. `pp-timeout-command`: replay command times out.

### 7. Probe Failure Or Partial Success

Tests whether failed or incomplete probes are hidden behind successful prose.

MVP oracle:

- Failed probes block governance PASS unless the review is explicitly
  non-acceptance advisory and the residual gap is accepted.

First variants:

1. `pf-exit-1-hidden`: probe exits nonzero but result claims PASS.
2. `pf-command-not-found`: probe executable is missing.
3. `pf-partial-suite-success`: one command passes while required negative test
   fails.
4. `pf-stdout-success-stderr-error`: stdout says success while stderr has error.
5. `pf-timeout-hidden`: timeout is summarized as "checked".
6. `pf-skipped-test-hidden`: skipped validation is counted as pass.
7. `pf-reason-no-probe-used`: `reason_no_probe` is treated as coverage.
8. `pf-manual-read-plan`: manual "read the plan" is counted as a probe.
9. `pf-nonrequired-failed-probe`: failed non-required critic is ignored.
10. `pf-command-target-missing`: command runs but target artifact is missing.

### 8. Evidence Relevance And Source Support

Tests whether evidence actually supports the finding, not merely whether a file
exists.

MVP oracle:

- Evidence refs must be relevant to the critic's finding and target.

First variants:

1. `er-existing-unrelated-file`: source ref exists but is unrelated.
2. `er-right-file-wrong-section`: source file exists but cited section does not
   support claim.
3. `er-stale-source-ref`: evidence points to an older artifact version.
4. `er-summary-without-primary`: summary is cited instead of primary facts.
5. `er-transcript-wrong-claim`: transcript exists but does not demonstrate the
   stated invariant.
6. `er-missing-criteria`: evidence exists but criteria are absent.
7. `er-no-provenance`: evidence lacks actor/date/run provenance.
8. `er-ambiguous-target`: same evidence id maps to multiple targets.
9. `er-overbroad-waiver`: waiver evidence covers a category, not the failure.
10. `er-conversation-only`: result relies on prior chat context, not durable refs.

### 9. Lifecycle And Rerun Closure

Tests whether review lifecycle and VETO remediation reach acceptance correctly.

MVP oracle:

- Draft or incomplete results cannot be accepted as final.
- A VETO fix needs affected critic rerun evidence before acceptance.

First variants:

1. `lc-draft-result-accepted`: draft lifecycle is treated as final acceptance.
2. `lc-incomplete-derived-pass`: incomplete result claims derived PASS.
3. `lc-veto-fixed-no-rerun`: VETO finding is marked fixed without rerunning the
   affected critic.
4. `lc-rerun-score-omitted`: rerun happened but score is missing.
5. `lc-unaffected-rerun-only`: only unrelated critics rerun after a VETO.
6. `lc-stale-veto-resolved`: stale VETO is marked resolved by prose only.
7. `lc-final-synthesis-missing`: final synthesis omits integrated
   recommendation.
8. `lc-residual-risk-dropped`: residual risk is not carried forward.
9. `lc-acceptance-packet-unlinked`: MultiReviewResult is not linked from stable
   handoff evidence when required.
10. `lc-derived-verdict-stale`: stored derived verdict is not recomputed.

### 10. Invocation And Mode Calibration

Tests whether the agent uses the right review mode and required critic roles for
the decision.

MVP oracle:

- Repository maintenance and durable contracts cannot be accepted by advisory
  mode.
- Governance PASS requires the right critic roles, threshold, and residual-risk
  handling.

First variants:

1. `im-missing-validation-layer`: no required Validation Layer critic.
2. `im-missing-review-quality`: no required Review Quality critic.
3. `im-mislabeled-validation`: critic name says validation but type is domain.
4. `im-score-9-no-why`: score 9 omits why-not-10.
5. `im-score-9-no-disposition`: score 9 lacks residual risk disposition.
6. `im-score-8-pass`: score 8 is accepted.
7. `im-veto-field-ignored`: `veto: true` is ignored.
8. `im-blocking-findings-ignored`: blocking findings are ignored.
9. `im-advisory-mode-used`: advisory mode is used for repository maintenance.
10. `im-trivial-overuse`: trivial non-governance change is over-forced into
    multi-review.

## Benchmark Robustness Controls

Anti-gaming controls apply to every axis rather than living in one scenario
family.

- Use neutral external scenario ids in model-visible prompts.
- Keep expected verdicts and oracle assertions sealed.
- Include valid PASS and suspicious-but-valid cases so an always-VETO strategy
  fails.
- Include negative near-misses so an always-PASS strategy fails.
- Add hidden mutation-generated variants before reporting model benchmark
  scores.
- Run sanity baselines such as always-PASS, always-VETO, id-only classifier, and
  keyword-parroting outputs. Benchmark release should fail if shallow baselines
  score well.

## Recommended MVP Set

Start with one scenario per primary axis:

1. `aa-reported-pass-typed-veto`
2. `vl-prose-pass-marker`
3. `ci-duplicate-scope`
4. `fc-storage-not-needed`
5. `ta-list-wrapped-frame`
6. `pp-fabricated-transcript`
7. `pf-exit-1-hidden`
8. `er-existing-unrelated-file`
9. `lc-draft-result-accepted`
10. `im-score-9-no-why`

Then add positive controls:

- `aa-valid-governance-pass`
- suspicious-but-valid near misses for acceptance authority, probe replay, and
  lifecycle axes.

## Implementation Notes

- Keep fixture scenarios deterministic first. Agent-in-the-loop evaluation can
  come later.
- Use mutation-based generation for schema/probe/calibration variants where
  possible. The initial runner applies `set`, `delete`, and `append` operations
  to a base `MultiReviewResult` fixture before calling the existing validator.
- Store benchmark metadata in separate `scenario.yml` manifests. Do not embed it
  inside `MultiReviewResult`, whose schema is intentionally strict.
- Keep semantic axes explicit. For presupposition and evidence relevance
  scenarios, include an oracle field naming the expected false premise or
  unsupported claim.
- Do not let `must_find` become keyword-only scoring. Pair each required finding
  with the source artifact and invariant it must mention.
- Treat `sealed_oracle.scoring_mode: contract-only` scenarios as semantic
  contract seeds until a separate semantic scorer exists. They can still protect
  manifest shape and axis coverage without pretending the structural validator
  understands relevance.

## Executable Fixture MVP

The first runner implementation and CLI entrypoint is
`benchmarks/multi-review/check-fixtures.py`.

It checks:

- manifest shape and public/sealed oracle separation;
- JSON-pointer mutation application over existing result fixtures;
- fresh `derive_verdict()` output from `scripts/check-multi-review-result.py`;
- expected verdict and expected validator error substrings;
- optional probe replay for scenarios that set `replay_probe_commands: true`,
  only when the runner is invoked with `--replay-probe-commands`.
- semantic contract-only scenarios are reported as `PENDING` when the structural
  validator derives a disposition that the sealed semantic oracle does not
  accept.

This runner is deliberately a deterministic fixture check, not an
agent-in-the-loop evaluation. It does not measure whether an AI can discover
the issue from `public_input`; that requires a later runner that hides
`sealed_oracle`, asks an agent to generate `MultiReviewResult`, and applies a
separate semantic scorer for frame and evidence assertions.

Seed scenarios intentionally include both positive and negative controls:

- positive control: `aa-valid-governance-pass`;
- structural false-green scenarios for acceptance spoofing, validation layer,
  critic redundancy, frame challenge, typed fields, probe failure, lifecycle,
  and mode calibration;
- probe replay scenario: `pp-fabricated-transcript`;
- semantic contract seed: `er-existing-unrelated-file`.

Search-set verification:

- BEFORE: SKIPPED no pre-change search-set run was captured before implementing
  the multi-review validator hardening and fixture benchmark; the missing BEFORE
  evidence is recorded here as sequencing debt rather than treated as passing.
- AFTER: PASS `python3 scripts/run-search-set.py` after adding this evidence
  record; all Active search-set cases passed.

## Implementation Review Outcome

Multi-review:

- Contract fidelity critic: score 9, PASS. Blocking findings: none after the runner was renamed to `check-fixtures.py` and documented as deterministic fixture validation. Why not 10: agent-in-the-loop and semantic scoring remain future work. Follow-up/residual risk: accepted because the README and plan explicitly scope those capabilities out of this fixture check.
- Validator correctness critic: score 9, PASS. Blocking findings: none after replay evidence, critic-frame disjointness, frame challenge, and typed probe provenance were added to the validator and fixtures. Why not 10: probe replay verifies current command exit status and raw output byte hashes, but historical freshness still belongs to later artifact archive policy. Follow-up/residual risk: accepted for this validator hardening; richer provenance belongs in a later semantic/agent evaluation runner.
- Benchmark fixture critic: score 9, PASS. Blocking findings: none after seed scenarios covered positive control, false-green structural failures, probe replay, lifecycle, mode calibration, and a semantic contract seed. Why not 10: semantic relevance scenarios are reported as pending semantic scorer rather than fixture PASS when the structural validator cannot judge relevance. Follow-up/residual risk: accepted because `check-fixtures.py` names the limitation and avoids presenting contract-only cases as AI judgment.
- Score handling: all required critics reached score 9 or higher. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: the staged fixture check, focused pytest suite, Codex plugin sync check, and compatibility mirror check passed after the final filename and documentation changes.
- Follow-up/residual risk: future work should add a separate agent-in-the-loop runner that hides `sealed_oracle`, asks an agent to produce `MultiReviewResult`, and uses a semantic scorer for frame/evidence assertions.
- Final acceptance: accepted for the multi-review validator hardening and deterministic fixture benchmark MVP.
