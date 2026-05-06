# Multi-Review Global Critic Lenses

## Purpose

Improve the global `multi-review` skill so it catches failures that are missed
when critics only ask whether an implementation followed the stated contract.

This is not a Plan 03, Plan 04, packet, or repository-governance-specific plan.
It generalizes a recent failure mode into a global review technique for any
high-stakes artifact: code, schemas, generated outputs, reports, release notes,
benchmark results, configuration, process records, or decision documents.

The goal is to change the question structure, not to increase reviewer count.
Multi-review should keep using the smallest useful critic set, but the critic
design must force invariant and adversarial questions when an artifact can look
acceptable while still being stale, misleading, unauditable, or out of scope.

## Failure Mode

The current skill already separates critic scopes and asks reviewers to evaluate
presuppositions. That protects against narrow consensus, but it can still miss
cases where the artifact appears to satisfy the explicit request while violating
an unstated invariant.

Common misses:

- A derived or generated field is trusted instead of recomputed.
- A success status, score, or output label hides a blocked or incomplete result.
- Evidence exists but lacks the criteria, source, or provenance needed to audit
  it later.
- A waiver, exception, skip, downgrade, or residual risk is too broad or has no
  durable target.
- The same identifier or label is used in two meaning spaces and reviewers
  accidentally merge them.
- A risk is marked out of scope but is not carried to a future artifact.
- The review validates the artifact as written without asking how a stale or
  adversarially hand-authored version could falsely pass.

## Design Principles

- Keep the skill global. Do not mention specific plan numbers or make packet
  review the default mental model.
- Treat the new roles as critic lenses, not a mandatory five-agent roster.
  A 2-4 critic review can cover several lenses by assigning them explicitly.
- Preserve concise skill loading. Add only core prompts and examples to
  `SKILL.md`; do not create auxiliary skill documentation.
- Prefer adversarial examples that apply across domains.
- Keep normal reviews lightweight. Require these lenses when the decision
  affects durable artifacts, public claims, release confidence, acceptance
  criteria, generated outputs, exceptions, or handoff records.

## Proposed Skill Changes

Add a global section such as `Invariant and Adversarial Review` to the
multi-review protocol.

The section should tell the agent:

1. Before trusting an artifact, imagine a stale, misleading, or adversarially
   hand-authored version of it.
2. Ask which invariant would catch the false green.
3. Assign the invariant to at least one critic, or explicitly add it to every
   relevant critic's prompt.
4. Do not accept an artifact only because its own generated fields, labels, or
   summaries claim success.

This guidance must be wired into the operative review flow, not appended as
background prose. For durable or high-stakes artifacts, critic design must assign
at least one applicable invariant/adversarial lens, and each assigned critic
prompt must include the false-green question. Final synthesis should treat the
review as incomplete if no critic covered adversarial false acceptance.

Suggested prompt addition:

```text
Before trusting the artifact, imagine a stale, misleading, or adversarially
hand-authored version of it. Identify how it could falsely appear acceptable,
which invariant would catch that case, and whether the provided evidence lets an
operator audit the conclusion later.
```

## Critic Lenses

Use these as reusable lenses during critic design. They are not fixed personas
and they do not require five separate reviewers.

- **Contract Fidelity Critic**: checks the public shape, schema, inputs, outputs,
  and the boundary between user-authored values and derived/generated values.
- **Decision Correctness Critic**: checks false greens, thresholds, score rules,
  status labels, exit semantics, negative cases, and whether success is computed
  from facts instead of asserted by the artifact.
- **Auditability Critic**: checks whether the final artifact alone preserves the
  criteria, evidence, source references, actor/reviewer provenance, and rationale
  needed to reconstruct the decision.
- **Adversarial Artifact Critic**: imagines stale, misleading, or hand-authored
  artifacts that would falsely pass; checks identifier collisions, stale derived
  fields, ambiguous targets, and misleading summaries.
- **Scope Boundary Critic**: checks whether the work smuggles future-scope
  behavior into the current change, or loses carry-over risks that were deferred
  to a later artifact.

## Invariant Questions

For durable or high-stakes reviews, cover the relevant questions below:

- Are generated, derived, scored, or summarized fields recomputed or checked
  against primary facts?
- Are validity, acceptance, stability, readiness, and success labels separated
  when they mean different things?
- Does every waiver, exception, skip, downgrade, and residual risk have a
  specific target, kind, actor, reason, date, and durable source?
- Can an operator audit the final artifact without relying on transient
  conversation context?
- If the same string or identifier appears in multiple meaning spaces, does the
  artifact preserve type, kind, or namespace?
- Does every out-of-scope risk have a durable carry-over location?
- Could a stale or manually edited artifact claim success while the underlying
  evidence would not support it?

## Adversarial Examples

Use domain-appropriate examples rather than copying these literally into every
review:

- A generated summary is edited by hand to say success.
- A report status says pass while the body describes a blocked condition.
- A score or threshold is present, but missing reviewer, evaluator, or run
  provenance.
- A derived classification is favorable, but the source data implies a stricter
  class.
- A waiver or skip applies to a broad category instead of a specific failed
  requirement.
- The same identifier names both an evidence item and a review item.
- An initial baseline, input set, or scope differs from the final one without
  being recorded.
- A future-scope risk is mentioned in prose but not preserved in the next
  durable artifact.

## Implementation Scope

Canonical sources to edit:

- `adapters/claude/skills/multi-review/SKILL.md`
- `adapters/codex/skills/multi-review/SKILL.md`

Generated or compatibility copies to refresh:

- `skills/multi-review/SKILL.md`
- `plugins/ai-agent-meta-harness/skills/multi-review/SKILL.md`

Tests to update:

- `tests/test_claude_multi_review_skill.py`
- `adapters/codex/tests/test_multi_review_skill.py`

No new skill resources, scripts, or reference files are planned. The change
should stay in the existing `SKILL.md` bodies and their mirror/generated copies.

The Claude and Codex skill variants should receive the same review concepts, but
not necessarily identical prose. Claude's phase-oriented protocol should place
the guidance in critic design and the prompt structure. Codex's compact protocol
should place shorter equivalent guidance in the numbered protocol and prompt
shape.

## Acceptance Criteria

- The skill remains global and does not encode Plan 03, Plan 04, packet-only, or
  repository-only wording as the default path.
- The protocol explicitly requires adversarial artifact imagination for durable
  or high-stakes reviews.
- The operative critic design or prompt shape requires the false-green question;
  implementation is incomplete if the guidance only appears as explanatory
  prose.
- Final synthesis rejects a durable or high-stakes review as incomplete when no
  critic covered an adversarial false-acceptance path.
- The reusable lens names appear in both Claude and Codex skill variants.
- The skill says the lenses are coverage prompts, not a requirement to spawn
  more agents.
- The skill includes generic adversarial examples that apply outside this
  repository.
- Mirror/generated skill copies stay synchronized with their canonical sources.
- Focused tests prove the new protocol text is present, the operative prompt or
  critic-design requirement is present, and the copies match.

## Validation

Run focused checks after implementation:

```bash
python3 -m unittest tests/test_claude_multi_review_skill.py
python3 -m unittest adapters/codex/tests/test_multi_review_skill.py
python3 scripts/check-compat-mirrors.py
python3 scripts/sync-codex-plugin.py --write
python3 scripts/sync-codex-plugin.py --check
git diff --check
```

Search-set verification:

- BEFORE: SKIPPED no pre-change search-set run was captured before implementing
  this global multi-review skill update; the missing BEFORE evidence is recorded
  here as sequencing debt rather than silently treated as passing.
- AFTER: PASS `python3 scripts/run-search-set.py` during
  `python3 scripts/verify-release.py --skip-clean-worktree --timeout 300`; all
  Active search-set cases passed.

Add at least one focused scenario or golden-text assertion that would fail if the
implementation only added passive prose. The scenario should involve a stale or
hand-authored artifact that falsely claims success, and the expected skill text
must require critics to identify the false green and preserve any deferred risk
in a durable carry-over location.

Because `check-compat-mirrors.py` and `sync-codex-plugin.py --check` inspect the
Git index for staged/pre-commit validation, focused unit tests must also read the
working-tree skill copies directly. They should fail when the operative prompt or
synthesis rules allow null, empty, or generic false-green coverage to count as
review coverage.
They should also reject contradictory operative wording that contains the
required keywords while allowing generic or unverified false-green values to
pass.
If tests add a helper for substantive false-green coverage, it should reject
common vacuous values such as `none`, `n/a`, `ok`, `checked`, `generic`, and
`not applicable`, not only literal `null` or empty strings.

If the work is later accepted as repository maintenance, follow the repository's
current maintenance review policy for skill changes.

## Implementation Review Outcome

Multi-review:

- Contract fidelity critic: score 10, PASS. Blocking findings: none. Follow-up/residual risk: none blocking; release verification and semantic coverage exhaustion were delegated to separate critics.
- Decision correctness and adversarial artifact critic: score 9, PASS. Blocking findings: none. Why not 10: tests are marker-based and sample representative contradictory phrasings rather than semantically exhausting every permissive synonym a future edit could introduce. Follow-up/residual risk: accepted; current no-coverage, vacuous-value, and contradictory-wording fixtures cover the named false-green risks.
- Auditability and release evidence critic: score 9, PASS. Blocking findings: none after staged review record was added. Why not 10: release gates that inspect the Git index must be rerun after staging the exact release candidate. Follow-up/residual risk: addressed by staging the plan evidence record and rerunning staged/index checks plus full release verification.
- Scope boundary and skill minimality critic: score 9, PASS. Blocking findings: none. Why not 10: the skill still carries conditional false-green fields and repository-governance guidance, so future edits must keep ordinary reviews lightweight and repository wording bounded. Follow-up/residual risk: accepted; the implementation keeps the lenses as coverage prompts and gates the stronger checks to durable or high-stakes artifacts.
- Score handling: all required critics reached score 9 or higher. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: residual risks from earlier self-review rounds were fixed and the final independent multi-review produced no VETO.
- Follow-up/residual risk: before commit or release, keep the staged evidence record with the skill/test changes and rerun staged/index gates so the accepted artifact boundary is auditable.
- Final acceptance: accepted for the global multi-review critic-lens implementation.

## Open Questions

- Whether the Claude and Codex skill variants should converge further in wording
  while preserving their runtime-specific execution instructions.
- Whether future usage should promote any recurring lens into a dedicated
  sub-skill, or keep all lens guidance inside `multi-review`.
