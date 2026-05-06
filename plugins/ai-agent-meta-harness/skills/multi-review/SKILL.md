---
name: multi-review
description: "Run a Codex-compatible multi-perspective review with independent critics for high-stakes decisions, regressions with suspected confounders, or user requests for review from multiple angles."
---

# Multi-Review for Codex

Use this skill when the user asks for multi-review, several independent perspectives, or validation of a high-stakes decision.

## Protocol

1. Frame the decision:
   - Decision
   - Stakes
   - Constraints
   - Presuppositions
   - Input materials
2. Design 2-4 critics with disjoint scopes.
3. Include at least one critic that may challenge a presupposition, or explicitly allow all critics to say the question is wrongly framed.
4. For durable, governance, or high-stakes artifacts, assign concrete attack
   surfaces and at least one invariant/adversarial lens. Include the
   false-green question and an adversarial probe in the assigned critic prompts.
5. Spawn critics as independent Codex sub-agents only when sub-agent use is available and appropriate for the task.
6. If sub-agents are unavailable, run a sequential fallback: evaluate each critic in a fresh, clearly separated section, do not revise earlier critic outputs after seeing later ones, and label the result `FALLBACK_NONINDEPENDENT` in the final report.
7. Do not share intermediate critic results between critics when true sub-agents are available.
8. Treat existing acceptance records, implementation review outcomes, generated
   summaries, and score labels as artifacts under review, not as proof that the
   work already passed.
9. Include a Review Quality Meta-Critic for durable or governance reviews. It
   reviews the review itself: independence, probe substance, validation command
   existence/executability, and whether PASS relies on self-attestation.
10. Include or assign a Validation Layer Critic for durable, governance, or
   high-stakes acceptance. It checks whether each invariant is enforced at the
   right layer before the review spends effort enumerating wording variants.
11. Synthesize results with PASS, VETO, MIXED, FAIL, or ADVISORY PASS. For durable or high-stakes artifacts, mark the review incomplete instead of PASS if no critic covered an adversarial false-acceptance path.

## Invariant and Adversarial Review

Use these lenses for durable artifacts, public claims, release confidence,
acceptance criteria, generated outputs, exceptions, or handoff records. They are
coverage prompts, not a requirement to spawn more agents; a small critic set can
cover several lenses explicitly.

- **Contract Fidelity Critic**: public shape, inputs/outputs, schema, and the
  boundary between user-authored and derived/generated values.
- **Decision Correctness Critic**: false greens, thresholds, score rules, status
  labels, exit semantics, negative cases, and success computed from facts.
- **Auditability Critic**: final artifact preserves criteria, evidence, source
  references, provenance, and rationale without relying on conversation context.
- **Adversarial Artifact Critic**: stale, misleading, or hand-authored artifacts
  that could falsely pass; identifier collisions and ambiguous targets.
- **Scope Boundary Critic**: future-scope behavior smuggled in, or deferred risk
  lost instead of carried to a durable artifact.
- **Validation Layer Critic**: the acceptance invariant is enforced by the
  correct artifact and mechanism: structured data, raw evidence, executable
  validator, or derived verdict, not regex/marker scans of natural-language
  instructions, summaries, or hand-authored PASS prose. VETO when governance
  acceptance depends on prose semantics unless that prose check is only a
  smoke/drift detector and the actual PASS is computed elsewhere.
- **Review Quality Meta-Critic**: the review itself is auditable, independent,
  and probe-backed; validation commands exist and can be rerun; PASS is not
  copied from a hand-authored acceptance record.

Invariant questions:

- Are generated, derived, scored, or summarized fields recomputed or checked
  against primary facts?
- Is the current validation target at the right layer, or is a semantic policy
  being approximated with natural-language markers, word lists, or regex?
- If prose, docs, or summaries are checked, are they only smoke/drift detectors
  while a structured validator computes the acceptance verdict?
- Are validity, acceptance, stability, readiness, and success labels separated
  when they mean different things?
- Does every waiver, exception, skip, downgrade, and residual risk have a
  specific target, kind, actor, reason, date, and durable source?
- If the same identifier appears in multiple meaning spaces, is type, kind, or
  namespace preserved?
- Does every out-of-scope risk have a durable carry-over location?

Generic adversarial examples:

- A generated summary is edited by hand to say success.
- A natural-language instruction is marker-scanned to prove a policy that should
  be enforced by structured results or a validator.
- A status label says pass while the body describes a blocked condition.
- A score or threshold is present but reviewer, evaluator, or run provenance is
  missing.
- A waiver or skip applies to a broad category instead of a specific failed
  requirement.
- The same identifier names both an evidence item and a review item.

Adversarial probe examples:

- Delete or weaken a generated obligation and confirm validation fails.
- Replace a durable artifact reference with an unrelated existing file.
- Use an alternate parser form, escaping path, stale pointer, or unsupported
  scheme that should not satisfy the contract.
- Change a status label to success while preserving body evidence for a blocked
  state.
- Run each validation command named by the artifact, or verify that the command
  target exists and is executable when execution is unavailable.

Probe requirement:

- For durable or governance reviews, each required critic reports `probe_run`,
  `probe_command`, `probe_result`, and `probe_interpretation`, or a specific
  `reason_no_probe`.
- `reason_no_probe` is not coverage by itself. It only explains why a probe
  could not run; final synthesis must downgrade to incomplete,
  FALLBACK_NONINDEPENDENT, or VETO unless the Review Quality Meta-Critic records
  why the residual review gap is acceptable for a non-acceptance advisory review.
- Values such as null, empty string, none, n/a, ok, checked, generic, not
  applicable, "read the plan", or "existing review says PASS" are no probe
  coverage.

Structured result requirement:

- For governance acceptance, produce a `MultiReviewResult` artifact using schema
  `multi-review-result/v1` and validate it with
  `python3 scripts/check-multi-review-result.py --result <path>
  --require-governance-pass` before reporting PASS.
- Treat `reported_final_verdict` and critic prose verdict labels as advisory;
  the validator-derived verdict is the only acceptance authority.
- Treat the validator-derived verdict as artifact-internal consistency only. It
  does not prove probe execution, command provenance, source relevance, or
  command output truth by itself.
- A validator-derived verdict is not AcceptancePacket stable-handoff evidence
  until a later review-provenance/import step durably references the artifact.

## Critic Prompt Shape

```text
You are [persona].
Evaluate only: [scope].
Do not evaluate: [anti-scope].
For durable or high-stakes artifacts, answer the false-green question: before trusting the artifact, imagine a stale, misleading, or hand-authored version that could falsely pass; identify the invariant that catches it and any deferred risk that needs durable carry-over.
For durable, governance, or high-stakes acceptance, answer the validation-layer
question before proposing more cases: is this invariant checked by structured
data, raw artifacts, executable validators, or a derived verdict? If acceptance
depends on natural-language markers, word lists, regex, or summaries, treat that
as a wrong-layer risk unless it is explicitly only a smoke/drift detector.
For durable or governance artifacts, run an adversarial probe for your assigned
attack surface when tools or raw artifacts are available. Prefer a temporary
mutation, negative fixture, parser variant, stale/ref mismatch, or command
existence/executability check. Existing acceptance records, generated review
outcomes, and PASS summaries are not evidence; they are artifacts to probe.
Input: [decision framing and materials].
Return JSON with score, verdict, key_findings, evidence, veto_reason, false_green_risk, invariant_checked, validation_layer, probe_run, probe_command, probe_result, probe_interpretation, reason_no_probe.
For durable or high-stakes artifacts, false_green_risk and invariant_checked must be non-null and specific; null, empty, or generic answers do not count as adversarial coverage.
Any prompt or synthesis wording that allows null, empty, generic, or unverified false-green values to pass conflicts with this protocol and must be treated as no coverage.
Coverage quality gate: `false_green_risk` must name a concrete stale, misleading, or hand-authored false-pass mechanism; `invariant_checked` must name a concrete invariant, recomputation, or audit check. Values such as null, empty string, whitespace, none, n/a, ok, checked, generic, or not applicable are no coverage.
Probe quality gate: `probe_run` must be true for acceptance reviews when tools
or raw artifacts are available, and `probe_command`, `probe_result`, and
`probe_interpretation` must be specific. If `probe_run` is false,
`reason_no_probe` must name the concrete blocker and the final synthesis cannot
use that critic as probe coverage.
```

## Model Routing

Use Codex's available model controls rather than Claude model names:

- Complex judgment: strongest reasoning model available
- Standard review: default capable coding model
- Mechanical checks: small/fast model only if no judgment is needed

## Verdict Rules

- Repository maintenance, harness-affecting changes, release gates, hooks,
  protected-file semantics, adapter behavior, and durable install/distribution
  contracts use governance mode:
  - PASS: all required critics score at least 9 and no veto
  - VETO: any required critic scores below 9, finds a fatal flaw, or leaves a
    blocking finding unresolved
  - VETO or incomplete: required critics did not run scope-specific adversarial
    probes where tools/raw artifacts were available, no Validation Layer Critic
    checked that acceptance is enforced at the right layer, or no Review Quality
    Meta-Critic checked the review itself
  - VETO: governance acceptance depends on natural-language markers, word lists,
    regex, summaries, or PASS prose, unless that check is only a smoke/drift
    detector and a structured validator or derived verdict computes PASS
  - Score 9 is acceptable only with why-not-10 handling and either backlog
    follow-up or explicit residual-risk acceptance
  - After a VETO fix, rerun affected critics and record the rerun score before
    accepting the work
- Non-governance exploratory reviews may use advisory mode only when clearly
  labeled as non-acceptance review:
  - ADVISORY PASS: all critics score at least 7 and no veto
  - MIXED: mean score at least 7 but one or more critics score below 7
  - FAIL: mean score below 7
- Do not use advisory mode to accept repository maintenance or harness-affecting
  work.

## Output

Present a compact table with critic, score, verdict, key finding, and probe summary, followed by the integrated recommendation. If sequential fallback was used, disclose that independence was weaker. For durable or high-stakes artifacts, name which critic covered adversarial false acceptance; if none did, or if the only false_green_risk/invariant_checked values are null, empty, or generic, listed no-coverage values, or allowed by contradictory wording, report the review as incomplete rather than PASS. For durable or governance reviews, also name the Validation Layer Critic and Review Quality Meta-Critic; summarize whether acceptance is computed at the correct layer and whether validation commands existed and were executable. If probe_run/probe_command/probe_result/probe_interpretation are null, empty, generic, listed no-coverage values, self-attestation, or only `reason_no_probe`, report the review as incomplete, FALLBACK_NONINDEPENDENT, or VETO rather than PASS. For governance-mode reviews, include VETO handling, rerun status, and score-9 why-not-10 handling. The user retains final decision authority.
