---
name: multi-review
description: "Dynamic multi-perspective review: spawn parallel critics with role separation for high-stakes decisions. Use when a decision needs validation from multiple independent viewpoints, or when the user says 'review this carefully', 'am I missing anything?', 'validate this from multiple angles', or 'get several independent perspectives'."
---

<!-- Compatibility mirror of `adapters/claude/skills/multi-review/SKILL.md`. Edit the canonical source, not this file. -->

# Multi-Review Protocol

For important decisions, run independent-perspective Critics in parallel to perform multi-angle validation.
The protocol is fixed; Critic composition is designed dynamically per problem.

## When to Activate

### User trigger
`/multi-review`, or phrases like "validate this from multiple angles", "review from several perspectives".

### Claude auto-suggest (suggestion only, not mandatory)
Suggest multi-review to the user when these signals are detected:
- Hard-to-reverse decisions (locking in strategy parameters, live deployments, application submissions)
- High-uncertainty judgments (insufficient data, unclear trade-offs)
- Domains where single-perspective evaluation has missed things before

## Protocol

### Phase 1: Problem Framing

Structure the decision under review:

```
Decision: [what is being decided]
Stakes: [what is the cost if it goes wrong]
Constraints: [already-fixed constraints]
Presuppositions: [what this question silently assumes — list 2-3 items]
Input: [materials to pass to the Critics]
```

**About Presuppositions (required, not optional)**:

A question's presuppositions are claims it treats as given without evaluating. Critics narrowly scoped around the decision will leave these unexamined, allowing flawed premises to reach verdicts unchallenged. Surface them here before critic design.

Examples:
- "Which benchmark should we use?" — presupposes we need a benchmark at all
- "What's the best storage schema?" — presupposes we need persistent storage
- "How should we structure the plugin API?" — presupposes plugins are the right abstraction

Rule: include at least one critic whose scope is "evaluate whether one of the listed presuppositions is actually warranted," OR explicitly allow all critics in their prompt to flag "the question itself is wrongly framed" as a valid verdict.

If Phase 1's Presuppositions block is empty or vague, Phase 2 critic design is incomplete — critics will optimize within the presupposed frame and systematically miss frame-level errors. This is the canonical failure mode of multi-review: N iterations of "which option is best?" when the question itself was wrong.

### Phase 2: Critic Design (Dynamic)

Design 2-4 Critics fitted to the problem on the spot.

**Design principles**:
- Each Critic's evaluation scope must be **explicitly disjoint** (overlap creates redundancy, not consensus)
- Assign each Critic a **natural persona** (a perspective, not a role title)
- One Critic may hold **Veto authority** (forcing rejection if its perspective sees a fatal flaw)
- For durable, governance, or high-stakes artifacts, assign concrete attack
  surfaces, not only abstract viewpoints. Each required Critic must try to
  falsify the artifact from its own scope with an adversarial probe when tools
  or raw artifacts are available.
- Treat existing acceptance records, implementation review outcomes, generated
  summaries, and score labels as artifacts under review, not as evidence that
  the review already succeeded.
- Include a **Review Quality Meta-Critic** for durable or governance reviews.
  Its scope is the review itself: independence, probe quality, validation
  command existence/executability, critic frame disjointness, and whether PASS
  relies on self-attestation.
- Include or assign a **Validation Layer Critic** for durable, governance, or
  high-stakes acceptance. Its scope is whether each invariant is checked at the
  right layer before anyone spends effort enumerating wording variants.
- For durable or high-stakes artifacts, assign at least one invariant/adversarial lens and include the false-green question in the assigned Critic prompts. If no Critic covers adversarial false acceptance, the final synthesis is incomplete, not PASS.

**Critic design template**:
```
Critic N: [name]
  Persona: [whose perspective this is]
  Scope: [evaluation scope — only this is examined]
  Anti-scope: [explicitly excluded — what is NOT evaluated]
  Invariant lens: [if durable/high-stakes, which false-green or auditability invariant this Critic covers]
  Attack surface: [specific false-pass mechanism this Critic will try to trigger]
  Primary failure mode: [the distinct way this Critic expects the artifact or decision to fail]
  Frame challenge: [true when this Critic evaluates a listed presupposition or can reject the question frame]
  Adversarial probe: [temp mutation, command, fixture, or manual check to run]
  Veto: [if any, under what condition it triggers]
```

### Invariant and Adversarial Review

Use these lenses for durable artifacts, public claims, release confidence,
acceptance criteria, generated outputs, exceptions, or handoff records. They are
coverage prompts, not a requirement to spawn more agents; a 2-4 Critic review can
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
  and probe-backed; validation commands exist and can be rerun; critic frames
  are materially non-redundant; PASS is not copied from a hand-authored
  acceptance record.

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
- Are required Critics materially distinct by persona, scope, anti-scope,
  attack surface, and primary failure mode rather than merely differently named?

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

- For durable or governance reviews, each required Critic must report
  `probe_run`, `probe_command`, `probe_exit_code`, `probe_result`,
  `probe_interpretation`, and `probe_evidence_refs`, or a specific
  `reason_no_probe`.
- `probe_evidence_refs` must point to repository-local structured transcript
  artifacts that name the exact `probe_command`, observed `probe_exit_code`,
  result ref/digest, packet ref/hash when packet-bound, source refs, cwd,
  generator, date, and raw stdout/stderr byte hashes. The transcript text must
  match the strict UTF-8 decode of those raw bytes; undecodable replay output is
  VETO. Substantive prose or marker text is not enough for governance PASS.
- `reason_no_probe` is not coverage by itself. It only explains why a Critic
  could not run a probe; the final synthesis must downgrade to incomplete,
  FALLBACK_NONINDEPENDENT, or VETO unless the Review Quality Meta-Critic records
  why the residual review gap is acceptable for a non-acceptance advisory review.
- Values such as null, empty string, none, n/a, ok, checked, generic, not
  applicable, "read the plan", or "existing review says PASS" are no probe
  coverage.

Structured result requirement:

- For governance acceptance, produce a `MultiReviewResult` artifact using schema
  `multi-review-result/v1` and validate it with
  `python3 scripts/check-multi-review-result.py --result <path>
  --require-governance-pass --replay-probe-commands` before reporting PASS.
- Do not run artifact-supplied probe commands from AcceptancePacket
  `check --require-stable`; stable handoff validation is read-only and accepts
  only durable transcript/source-reference evidence.
- Treat `reported_final_verdict` and Critic prose verdict labels as advisory;
  the validator-derived verdict is the only acceptance authority.
- Treat the validator-derived verdict as artifact-internal consistency plus
  linked probe transcript references only. It is not stable handoff evidence by
  itself.
- A validator-derived verdict is not AcceptancePacket stable-handoff evidence
  until a later review-provenance/import step durably references the artifact.

Governance complexity check:

- When reviewing a governance guard, schema field, fixture kind, or durable
  evidence rule, include a required anti-bloat Critic. This Critic should ask
  which concrete false-green path is closed, whether an existing guard can be
  generalized instead, whether any user-authored field or multi-file fixture
  burden is added, and what complexity is removed, generated, or deferred.
- VETO governance changes that spread one policy across hand-synced fixtures
  without a helper/generator, or that expand the operator-facing model beyond
  `meta`, `input`, and `result` without replacing a larger surface.

**Model assignment criteria**:
- High-stakes / complex judgment (architecture, strategy, irreversible decisions) → **opus**
- Standard analysis / code review → **sonnet**
- Checklist / format verification (binary pass/fail only) → **haiku**
- Default: **sonnet**

### Phase 3: Parallel Execution

Run each Critic as an **independent sub-agent** (Agent tool).

**Prompt structure passed to each Critic**:
```
## Your Role
You are [Persona].

## Your Scope
You evaluate ONLY [Scope].
Do NOT evaluate [Anti-scope].

## Input
[Problem framing + relevant materials]

## False-Green Check
For durable or high-stakes artifacts: before trusting the artifact, imagine a
stale, misleading, or hand-authored version that could falsely pass. Identify
the invariant that catches it and any deferred risk that needs durable
carry-over. `false_green_risk` and `invariant_checked` must be non-null and
specific; null, empty, or generic answers do not count as adversarial coverage.
For durable, governance, or high-stakes acceptance: answer the validation-layer
question before proposing more cases: is this invariant checked by structured
data, raw artifacts, executable validators, or a derived verdict? If acceptance
depends on natural-language markers, word lists, regex, or summaries, treat that
as a wrong-layer risk unless it is explicitly only a smoke/drift detector.
Any prompt or synthesis wording that allows null, empty, generic, or unverified
false-green values to pass conflicts with this protocol and must be treated as
no coverage.
Coverage quality gate: `false_green_risk` must name a concrete stale,
misleading, or hand-authored false-pass mechanism; `invariant_checked` must name
a concrete invariant, recomputation, or audit check. Values such as null, empty
string, whitespace, none, n/a, ok, checked, generic, or not applicable are no
coverage.

## Adversarial Probe
For durable or governance artifacts: run a concrete probe for your assigned
attack surface when tools or raw artifacts are available. Prefer a temporary
mutation, negative fixture, parser variant, stale/ref mismatch, or command
existence/executability check. Existing acceptance records, generated review
outcomes, and PASS summaries are not evidence; they are artifacts to probe.
If you cannot run a probe, set `probe_run` to false and give a specific
`reason_no_probe`; do not claim PASS from that gap.

## Output Format (JSON)
{
  "score": 1-10,
  "verdict": "pass" | "concern" | "veto",
  "key_findings": ["up to 3 key findings"],
  "evidence": ["supporting evidence for each finding"],
  "veto_reason": null | "veto rationale (if applicable)",
  "persona": "natural perspective used by this Critic",
  "anti_scope": "what this Critic explicitly did not evaluate",
  "attack_surface": "specific false-pass mechanism probed by this Critic",
  "primary_failure_mode": "the distinct way this Critic expects the artifact or decision to fail",
  "frame_challenge": true | false,
  "false_green_risk": null | "how a stale, misleading, or hand-authored artifact could falsely pass",
  "invariant_checked": null | "the invariant used to catch that false green",
  "validation_layer": null | "structured-validator | raw-artifact | derived-verdict | prose-smoke | wrong-layer",
  "probe_run": true | false,
  "probe_command": null | "command, temp mutation, fixture, or manual probe performed",
  "probe_exit_code": null | 0,
  "probe_result": null | "observed result, including exit status when applicable",
  "probe_interpretation": null | "why this probe supports or rejects the artifact",
  "probe_evidence_refs": ["repository-local structured transcript refs matching command, exit code, result/source binding, and raw output byte hashes"],
  "reason_no_probe": null | "specific blocker if probe_run is false"
}
```

**Execution rules**:
- Run all Critics **simultaneously** (parallel Agent tool calls)
- Each Critic must NOT see other Critics' results (independence guarantee)
- Constrain Critics in the prompt to not opine outside their scope

### Phase 4: Convergence Check

For reviews that iterate on the same artifact or decision more than once,
include a convergence note before the final verdict. Cluster open findings by
root failure class or invariant family, using existing critic evidence such as
`attack_surface`, `primary_failure_mode`, `invariant_checked`, affected
path/source refs, and probe evidence. Mark whether each new finding is a new root
class or a variant of an already open class, report whether the loop is
converging, drifting, or blocked, and recommend stop, merge, drop, escalate, or
keep iterating. This note is advisory for `multi-review-result/v1`: a
hand-authored "converged" label is not acceptance evidence and cannot turn VETO
into PASS or suppress an unresolved blocking finding. If prior review artifacts
or previous finding evidence are missing, incomplete, or not comparable, mark the
note as insufficient history and report only the current findings instead of
inferring convergence or drift.

### Repository Governance Mode

When reviewing this repository's maintenance work, harness-affecting changes,
release gates, hook semantics, core methodology boundaries, or durable adapter
contracts, apply the repository's local release discipline from `MAINTENANCE.md`:
any reviewer or Critic score below 9 is a **VETO** until the blocking finding is
fixed and the affected Critic reruns to at least 9. A score of 9 is acceptable
only when the final report records why it was not 10 and either accepts the
residual risk or creates follow-up backlog work.

The generic 7/10 threshold below applies only to non-governance qualitative
reviews where the repository maintenance policy is not the acceptance contract.

| Condition | Verdict |
|-----------|---------|
| All Critics ≥ 7 AND no veto | **PASS** — report with one-line summary |
| Any Critic vetoes | **VETO** — present veto rationale + that Critic's full output |
| Mean ≥ 7 BUT some < 7 | **MIXED** → Phase 5 Synthesis |
| Mean < 7 | **FAIL** → Phase 5 Synthesis |

For durable or high-stakes artifacts, do not report PASS if no Critic covered an
adversarial false-acceptance path. Report the review as incomplete and rerun with
an assigned invariant/adversarial lens. Treat null, empty, or generic
`false_green_risk` or `invariant_checked` values, and any contradictory wording
that allows them to pass, as no coverage. Also treat listed no-coverage values
as no coverage.

For durable or governance artifacts, do not report PASS unless required Critics
ran scope-specific adversarial probes, a Validation Layer Critic checked that
acceptance is enforced at the right layer, and a Review Quality Meta-Critic
checked review independence, critic frame disjointness, probe substance,
validation command existence, transcript provenance, and executability where
possible. Required Critics must be materially distinct by persona, scope,
anti-scope, attack surface, and primary failure mode, and at least one required
Critic must be accountable for challenging a listed presupposition or the frame
itself. A
wrong-layer validation finding is VETO for
governance acceptance unless the natural-language check is only a smoke/drift
detector and a structured validator or derived verdict computes PASS. A
probe-less durable/governance review is incomplete, FALLBACK_NONINDEPENDENT, or
VETO, not PASS. Treat null, empty, generic, not applicable, or self-attestation
probe fields as no coverage. Treat missing or mismatched probe transcript refs
as no provenance coverage. For governance acceptance, rerun explicitly with
`--replay-probe-commands` so the validator replays commands and compares
observed exit codes and raw stdout/stderr byte hashes; replay output must strict-decode as UTF-8 to match transcript text. Do not invoke replay from
AcceptancePacket stable checks.

### Phase 5: Synthesis (when MIXED/FAIL)

Identify conflicts between Critic results and produce an integrated judgment:

```
## Conflicts
- Critic A judged [X], Critic B judged [Y]
- Source of conflict: [why they reached different conclusions]

## Unified Assessment
- [integrated judgment + rationale]
- Residual risk: [unresolved concerns]

## Recommendation
- [concrete action proposal]
- Conditional go-ahead viability: [if any, specify the conditions]
```

### Phase 6: Present to User

**Result table**:
```
| Critic | Score | Verdict | Key Finding |
|--------|-------|---------|-------------|
| ...    | ...   | ...     | ...         |
```

**Final verdict**: PASS / VETO / MIXED + integrated recommendation
**User decision**: Human-in-the-loop — the final decision is always the user's

## Harness Feedback Loop

After review completion, learn:
- If a Critic missed a perspective → add that perspective for similar problems next time
- If the user overruled a Critic's judgment → revisit that Critic's prompt / scope
- If the domain recurs → promote that Critic to a dedicated skill in `.claude/skills/` (Level 3)

Learning feedback recording paths:
- **Project-specific learning** → that project's memory/ (e.g., `feedback_review_*.md`)
- **Multi-review protocol improvement itself** → add to this SKILL.md's Anti-Patterns
- Scope discrimination: "Does this learning apply to other projects?" → Yes = SKILL.md, No = project memory

## Anti-Patterns

- Overusing multi-review on trivial decisions (4 Critics for a 3-line code change is overkill)
- Critic scopes overlapping such that they repeat the same point
- Using the same model for every Critic (reduces perspective diversity)
- Averaging scores without Synthesis to reach a verdict
- Ignoring user decision authority (Critic consensus ≠ final decision)
- **Iteration drift**: when iterating on the same problem 3+ times, if complexity (number of changes / number of mechanisms) is increasing, that is divergence, not convergence. Stop the mechanism-on-mechanism stacking and revert to the minimal-viable. No global interventions without root-cause diagnosis. At every iteration ask: "Does this change resolve the absence of an existing rule, or compensate for a violation of an existing rule?" — if the latter, do NOT strengthen the rule; **diagnose the cause of the violation first**.
- **Convergence Critic always included**: any multi-review iterating 2+ times must include a Convergence vs Drift meta-Critic to monitor iteration health.
- **Unexamined presuppositions**: critics scoped narrowly will evaluate the decision as posed and miss frame-level errors in the question itself. If after multiple iterations a reframing by the user (not the critics) reveals that the question was wrong, Phase 1's Presuppositions block was probably empty or vague. Fix: surface presuppositions explicitly in Phase 1 and either assign a critic to attack one, or grant all critics permission to verdict "question is wrongly framed."
