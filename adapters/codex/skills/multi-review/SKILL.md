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
4. For durable or high-stakes artifacts, assign at least one invariant/adversarial lens and include the false-green question in the assigned critic prompts.
5. Spawn critics as independent Codex sub-agents only when sub-agent use is available and appropriate for the task.
6. If sub-agents are unavailable, run a sequential fallback: evaluate each critic in a fresh, clearly separated section, do not revise earlier critic outputs after seeing later ones, and label the result `FALLBACK_NONINDEPENDENT` in the final report.
7. Do not share intermediate critic results between critics when true sub-agents are available.
8. Synthesize results with PASS, VETO, MIXED, FAIL, or ADVISORY PASS. For durable or high-stakes artifacts, mark the review incomplete instead of PASS if no critic covered an adversarial false-acceptance path.

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

Invariant questions:

- Are generated, derived, scored, or summarized fields recomputed or checked
  against primary facts?
- Are validity, acceptance, stability, readiness, and success labels separated
  when they mean different things?
- Does every waiver, exception, skip, downgrade, and residual risk have a
  specific target, kind, actor, reason, date, and durable source?
- If the same identifier appears in multiple meaning spaces, is type, kind, or
  namespace preserved?
- Does every out-of-scope risk have a durable carry-over location?

Generic adversarial examples:

- A generated summary is edited by hand to say success.
- A status label says pass while the body describes a blocked condition.
- A score or threshold is present but reviewer, evaluator, or run provenance is
  missing.
- A waiver or skip applies to a broad category instead of a specific failed
  requirement.
- The same identifier names both an evidence item and a review item.

## Critic Prompt Shape

```text
You are [persona].
Evaluate only: [scope].
Do not evaluate: [anti-scope].
For durable or high-stakes artifacts, answer the false-green question: before trusting the artifact, imagine a stale, misleading, or hand-authored version that could falsely pass; identify the invariant that catches it and any deferred risk that needs durable carry-over.
Input: [decision framing and materials].
Return JSON with score, verdict, key_findings, evidence, veto_reason, false_green_risk, invariant_checked.
For durable or high-stakes artifacts, false_green_risk and invariant_checked must be non-null and specific; null, empty, or generic answers do not count as adversarial coverage.
Any prompt or synthesis wording that allows null, empty, generic, or unverified false-green values to pass conflicts with this protocol and must be treated as no coverage.
Coverage quality gate: `false_green_risk` must name a concrete stale, misleading, or hand-authored false-pass mechanism; `invariant_checked` must name a concrete invariant, recomputation, or audit check. Values such as null, empty string, whitespace, none, n/a, ok, checked, generic, or not applicable are no coverage.
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

Present a compact table with critic, score, verdict, and key finding, followed by the integrated recommendation. If sequential fallback was used, disclose that independence was weaker. For durable or high-stakes artifacts, name which critic covered adversarial false acceptance; if none did, or if the only false_green_risk/invariant_checked values are null, empty, or generic, listed no-coverage values, or allowed by contradictory wording, report the review as incomplete rather than PASS. For governance-mode reviews, include VETO handling, rerun status, and score-9 why-not-10 handling. The user retains final decision authority.
