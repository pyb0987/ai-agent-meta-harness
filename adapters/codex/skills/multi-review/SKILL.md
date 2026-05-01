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
4. Spawn critics as independent Codex sub-agents only when sub-agent use is available and appropriate for the task.
5. If sub-agents are unavailable, run a sequential fallback: evaluate each critic in a fresh, clearly separated section, do not revise earlier critic outputs after seeing later ones, and label the result `FALLBACK_NONINDEPENDENT` in the final report.
6. Do not share intermediate critic results between critics when true sub-agents are available.
7. Synthesize results with PASS, VETO, MIXED, FAIL, or ADVISORY PASS.

## Critic Prompt Shape

```text
You are [persona].
Evaluate only: [scope].
Do not evaluate: [anti-scope].
Input: [decision framing and materials].
Return JSON with score, verdict, key_findings, evidence, veto_reason.
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

Present a compact table with critic, score, verdict, and key finding, followed by the integrated recommendation. If sequential fallback was used, disclose that independence was weaker. For governance-mode reviews, include VETO handling, rerun status, and score-9 why-not-10 handling. The user retains final decision authority.
