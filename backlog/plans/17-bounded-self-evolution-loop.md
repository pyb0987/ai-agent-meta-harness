# Plan 17: Bounded Self-Evolution Proposal Loop

## Status

Implemented for the repository-local harness. This plan accepts the methodology
direction that the Meta-Harness should notice its own dogfood gaps and draft
improvement proposals, while keeping adoption conservative and evidence-bound.

## Purpose

Plans 12 and 13 provide the repository-local strategy-search evolution engine.
Plan 15 lets installed agents route ordinary user language to the right harness
behavior. Plan 16 makes trace retrieval claims checkable through raw trace
quotes.

Plan 17 connects those layers into a bounded self-evolution loop:

```text
observed work / repeated failure / stale trace gap
  -> diagnostic detection
  -> proposed trace, search-set, instruction, or strategy-search direction
  -> raw evidence and verification
  -> normal reviewable content change
  -> ordinary v2 governance when the repository needs stable publication
```

The loop is intentionally not an automatic self-modifying harness. Automation
may nominate, cluster, draft, and preflight. Adoption still requires raw
evidence, executable verification, and a reviewable content change.

## Core Position

The repository should improve from its own usage logs without making ordinary
users operate the harness by hand.

The enforceable boundary is:

- detectors and agents may create improvement candidates;
- candidates are diagnostic until adopted;
- generated summaries, catalogs, detectors, and strategy-search selections are
  pointers or proposals, not evidence by themselves;
- adoption must cite raw evidence, preserve retrieval provenance when trace
  history is used, and pass executable checks;
- high-risk or stable-publication changes still use the normal v2
  packet/pointer flow.

## Problem Statement

After Plan 15 and Plan 16, a user can mostly work normally and agents have a
way to cite raw trace bytes. A remaining practical gap is that a repository can
accumulate substantial work while its harness memory does not keep up:

1. repeated failures may be fixed locally without becoming failure traces;
2. experiments may produce outputs without becoming experiment episodes;
3. search-set guards may remain stale after new recurring risks appear;
4. strategy-search/autoresearch output may look promising but remain
   disconnected from the normal adoption boundary;
5. users may not know when to ask for harness engineering, and should not need
   to know.

Plan 17 addresses those gaps by making the harness propose its own maintenance
work. It does not promote those proposals automatically.

## Non-Goals

- Do not add background orchestration or silent auto-commit behavior.
- Do not let detectors modify active search-set entries without review.
- Do not turn strategy-search selections into stable governance evidence.
- Do not make every normal feature request run dogfood review.
- Do not require ordinary users to name skills, retrieval modes, or plan
  numbers.
- Do not claim semantic completeness from trace volume, catalog metadata, or
  detector output.
- Do not implement Plan 14 sandbox/concurrency features here.

## Candidate Kinds

Plan 17 recognizes four candidate kinds. All are diagnostic until adopted.

### Trace Candidate

Created when a repeated failure, important experiment, or harness-changing
decision appears to lack a durable trace record.

Required adoption evidence:

- raw file or trace refs that explain the triggering event;
- `retrieval.mode` and byte-matching raw trace refs when prior trace history is
  used;
- a concise reason why this event deserves durable trace memory.

### Search-Set Candidate

Created when a new recurring risk has a cheap executable guard.

Required adoption evidence:

- raw failure, review, experiment, or evolution evidence for the risk;
- a deterministic verify command;
- a before/after run of the relevant command when practical;
- explicit choice to add, update, archive, or reject the candidate.

### Instruction Candidate

Created when agent behavior repeatedly misses an existing rule or when ordinary
user language should route to an existing harness behavior.

Required adoption evidence:

- raw trace or review evidence of the behavior gap;
- a minimal instruction/template change;
- focused tests or mirror checks when the instruction is distributed through an
  adapter or plugin.

### Strategy-Search Candidate

Created when a bounded mutable surface and fixed evaluator can test candidate
harness strategies.

Required adoption evidence:

- a valid direction file;
- anchored strategy-search evaluation records;
- diagnostic selection only;
- an ordinary content commit before any stable claim;
- v2 governance when stable repository publication is needed.

## Dogfood Sweep

The repository includes a small diagnostic command:

```bash
python3 scripts/check-harness-dogfood.py
```

The command does not edit files. It reports candidate gaps such as:

- tracked or staged harness-affecting changes with concrete usage or review
  evidence but no matching evolution trace;
- changed experiment outputs without a recent experiment trace;
- repeated failure-like edits without a failure trace candidate;
- active search-set entries whose verify commands are stale or missing;
- strategy-search selections that have not crossed the normal content-commit
  adoption boundary.

Sparse trace volume is not a failure by itself. A sweep may report a candidate
only when it can name the triggering evidence, affected surface, and proposed
next action.

The command is a suggestion layer. It exits nonzero only for malformed records
or explicitly configured repository policy. By default it keeps ordinary user
work unblocked.

The report may contain many internal candidates, but the post-task user
surface is capped. `maintenance_note` is either `null` or one
`quiet_post_task_diagnostic_candidate` object selected by a deterministic
priority rule. A candidate can be surfaced only when it has all three parts: a
concrete trigger-evidence pointer, reusable future value, and a clear next
action. In `post_task` mode, unrelated repository-wide stale guards remain
suppressed from the public candidate list. In `explicit_dogfood` mode, one note
may be selected from the full diagnostic report.

## User Experience

The user-facing product shape remains:

```text
User: Please fix this.
Agent: Works normally.

User: This keeps failing.
Agent: Creates or proposes failure trace and harness improvement candidates.

User: We have done a lot of work; did the harness learn from it?
Agent: Runs dogfood review and reports at most one diagnostic follow-up when a
concrete trigger-evidence pointer, reusable future value, and a clear next
action are all present.
```

Users should not need to know `harness-engineer`, `multi-review`,
`autoresearch`, `strategy-search`, `retrieval.mode`, or this plan number.

## Implementation Slices

### Slice 1: Documentation And Routing Contract

- Update system docs, plan index, and installed project guidance to describe
  bounded proposal generation.
- Name the exact agent-facing surfaces that should learn this rule:
  `skills/harness-engineer/SKILL.md`, Codex `AGENTS.md` templates, Claude
  init/example surfaces, and README usage language.
- Keep the user-facing rule simple: normal work stays normal. At completion,
  the agent may do a cheap threshold check when concrete signals are already
  visible, but it does not run a separate dogfood checker for every task.

### Slice 2: Diagnostic Report Schema

- Define a small dogfood report shape with `candidate_kind`, `trigger_evidence`,
  `reusable_future_value`, `proposed_action`, `status`, and `reason`.
- Keep the report diagnostic-only. It must not contain PASS/adopted labels
  unless a later adoption record supplies raw evidence and verification.
- Include a negative fixture proving that a report cannot classify low trace
  count alone as failure.
- Include a machine-readable `maintenance_note` contract. The value is `null`
  or one `quiet_post_task_diagnostic_candidate` object with
  `evidence_status: diagnostic_only`, `evidence_role: pointer_only`, and
  `adoption_boundary: not_adoption_evidence`.
- Test that multiple internal candidates still produce at most one surfaced
  note, and that candidate-like signals without a trigger-evidence pointer
  produce no note.

### Slice 3: Trace Gap Detector

- Detect harness-impacting changes that have concrete usage or review evidence
  but no matching evolution/failure/experiment trace candidate.
- Treat missing traces as suggestions, not errors, unless repository policy
  explicitly configures a stricter gate.
- Require the candidate to name raw files or trace refs that explain why the
  trace would be useful.

### Slice 4: Search-Set Candidate Detector

- Detect candidate Active guards only when there is a cheap deterministic
  verify command and raw evidence of a recurring risk.
- Emit proposed `SS-*` entries as candidates, not as direct edits to Active
  search-set state.
- Include negative coverage for stale or missing guard claims without a
  runnable command.

### Slice 5: Strategy-Search Adoption Boundary Detector

- Detect selected strategy-search candidates that have not crossed the ordinary
  content-commit adoption boundary.
- Report them as diagnostic follow-up only.
- Keep selected strategy-search files out of stable evidence unless a later v2
  packet/pointer flow binds the adopted content change.

### Slice 6: Verification And Multi-Review

- Add focused tests for every detector and negative case above.
- Run trace retrieval provenance checks for new evolution traces.
- Run Active search-set verification when the implementation changes tracked
  harness behavior.
- Multi-review the implementation with methodology-fidelity, usage-fit, and
  anti-bloat critics before marking Plan 17 implemented.

## Acceptance

Plan 17 is accepted when:

- documentation describes bounded proposal generation as distinct from
  automatic adoption;
- project and skill guidance says agents should propose trace/search-set or
  instruction updates only when a concrete trigger-evidence pointer, reusable
  future value, and a clear next action indicate a harness memory gap;
- any dogfood sweep implementation is diagnostic by default and does not edit
  files;
- dogfood reports expose at most one post-task maintenance note, and no note is
  emitted unless a concrete trigger-evidence pointer, reusable future value,
  and clear next action are all present;
- search-set candidates cannot become Active solely because a detector found a
  stale or missing record;
- strategy-search output remains diagnostic until applied as a normal content
  commit;
- trace-history claims use Plan 16 retrieval provenance;
- ordinary users still ask normal questions and do not operate the mechanism by
  hand.

## Residual Risks

- A detector can miss a real harness gap or over-report a harmless sparse trace
  history. Review remains responsible for deciding whether the candidate matters.
- A generated proposal can be plausible but not useful. The adoption boundary
  must require concrete raw evidence and an executable verification path.
- This plan does not prove benchmark-level agent-in-the-loop semantic quality.
  It improves repository-local dogfood discipline.

## Implementation Record

- Slice 1 implemented in README target-project usage, Codex AGENTS templates,
  Claude example/init guidance, and harness-engineer skills. The installed
  agent routing contract now includes ordinary phrases such as "did the harness
  learn from this" and "check for dogfood gaps."
- Slice 2 implemented in `scripts/check-harness-dogfood.py` with
  `harness-dogfood-report/v1`. Reports include `candidate_kind`,
  `trigger_evidence`, `affected_surface`, `reusable_future_value`,
  `proposed_action`, `status`, `evidence_status: diagnostic_only`,
  `evidence_role: pointer_only`, and `adoption_boundary:
  not_adoption_evidence` at report and candidate level. Reports also include
  `maintenance_note`, which is `null` or one
  `quiet_post_task_diagnostic_candidate` selected from eligible public
  candidates. `post_task` exposes only post-task candidates and records
  suppressed global-health candidates by count; generated candidates remain
  diagnostic.
- Slice 3 implemented as a trace-gap detector that requires concrete usage or
  review evidence and refuses to classify sparse trace volume alone as failure.
- Slice 4 implemented as an Active search-set verify-command detector. Missing
  verify commands are malformed records; stale command paths are diagnostic
  candidates.
- Slice 5 implemented as a strategy-search selection boundary detector for
  changed `.harness/search-runs/*/selections/*-selection.yml` files.
- Slice 6 implemented with `tests/test_harness_dogfood.py`,
  `tests/test_maintenance_policy_boundaries.py`, trace provenance checks, and
  Active search-set verification.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py` after Plan 17 planning
  acceptance and before implementation began.
- AFTER: PASS `python3 scripts/run-search-set.py` after implementation (7
  Active case(s)).

## Initial Multi-Review

Multi-review:

- Mode: sub-agent advisory review; no governance-mode MultiReviewResult
  artifact claimed.
- Methodology Fidelity Critic: score 9, PASS. Blocking findings: none after
  wording narrowed self-evolution to ordinary agent work or explicit dogfood
  checks. The plan preserves raw-data-first evidence, diagnostic-vs-adoption
  boundaries, and v2 publication for stable claims. Why not 10: implementation
  behavior remains future work. Follow-up/residual risk: accepted.
- Usage-Fit Critic: score 9, PASS. Blocking findings: none. The plan now reads
  as a general ai-agent-meta-harness layer, not a cwaa-specific workflow, and
  explicitly says sparse trace volume is not failure by itself. Why not 10:
  detector precision will be proven only in implementation. Follow-up/residual
  risk: accepted.
- Simplicity/Anti-Bloat Critic: score 9, PASS. Blocking findings: none after
  implementation slices were added. The plan avoids background orchestration,
  automatic adoption, user skill-name burden, and Plan 14 sandbox scope creep.
  Why not 10: Slice 1 must avoid mirror/documentation sprawl during
  implementation. Follow-up/residual risk: accepted.
- Score handling: all final critic scores are at least 9. Initial sub-9
  planning feedback was fixed by adding concrete slices, narrowing
  self-evolution wording, and stating that sparse trace volume is not a failure
  by itself.
- Follow-up/residual risk: why-not-10 items were accepted as bounded residual
  risk because implementation precision was scheduled into the slices and later
  verified.
- Rerun status: no rerun required after the final planning critics all reached
  score 9 PASS.
- Final acceptance: advisory only; Plan 17 planning was sufficient to proceed
  to Slice 1 when implementation was requested, and it is not stable governance
  evidence by itself.

## Implementation Multi-Review

Multi-review:

- Mode: sub-agent advisory review; no governance-mode MultiReviewResult
  artifact claimed.
- Methodology Fidelity Critic: initial score 8, MIXED/VETO before fix; rerun
  score 9, PASS after fix. Blocking findings: detector JSON could be mistaken
  for evidence because candidate records lacked a machine-readable adoption
  boundary. Fix: `scripts/check-harness-dogfood.py` now emits
  `evidence_status: diagnostic_only`, `evidence_role: pointer_only`,
  `adoption_boundary: not_adoption_evidence`, and `trigger_evidence_role:
  pointer_only` at the candidate/report boundary. Why not 10: downstream misuse
  of pointer fields is still a review concern.
- Simplicity/Anti-Bloat Critic: score 9, PASS. Blocking findings: none. The
  checker is diagnostic-only, does not edit files, keeps candidate suggestions
  exit-zero by default, and preserves the ordinary user path. Why not 10: the
  detector is intentionally coarse. Follow-up/residual risk: accepted.
- Validation/False-Green Critic: score 8, MIXED/VETO before fix; rerun score 9,
  PASS after focused re-review. Blocking findings: initial JSON-boundary
  ambiguity was fixed. Coverage includes low trace count non-failure, trace-gap
  trigger evidence, changed evolution trace closure, malformed/missing
  search-set verify, stale verify command diagnostics, and strategy-search
  selection diagnostic boundary. Why not 10: there is no formal JSON
  schema/golden output test for every candidate type.
- Score handling: scores below 9 were treated as VETO before fix and accepted
  only after same-target focused reruns reached score 9 PASS. Score-9
  why-not-10 items are accepted as residual risk because the shared constructor
  keeps candidate boundary fields consistent.
- Follow-up/residual risk: downstream misuse of pointer fields and lack of a
  formal JSON schema/golden output remain accepted advisory residual risks, not
  stable governance evidence.
- Rerun status: same-target focused rerun completed after the JSON-boundary fix;
  rerun critics reached score 9 PASS with no blocking findings.
- Final acceptance: advisory only; the first Plan 17 repository implementation
  was sufficient for follow-up hardening. The dogfood sweep remains a
  diagnostic proposal layer, not stable governance evidence.

## Post-Task Note Contract Review

Multi-review:

- Mode: sub-agent advisory review; no governance-mode MultiReviewResult
  artifact claimed.
- Methodology Fidelity Critic: score 9, PASS with wording fixes. Blocking
  findings: none. Why not 10: wording still needed tightening around
  completion-time threshold checks. Follow-up accepted: clarify that agents may
  perform only a cheap completion-time threshold check when concrete signals are
  already visible, and that low trace volume or a single wish is not a
  candidate by itself.
- Usage-Fit Critic: score 8, MIXED/VETO before fix; rerun score 9, PASS after
  fix. Blocking findings: internal candidates were uncapped at the user
  surface, and candidate records did not explicitly name reusable future value.
  Fix: `maintenance_note` now surfaces zero or one deterministic diagnostic
  note, and every candidate includes `reusable_future_value`. Why not 10:
  rendered note length remained a polish residual and was later capped by test.
- Implementation/Testability Critic: score 8, MIXED/VETO before fix; rerun
  score 9, PASS after fix. Blocking findings: machine-readable note contract,
  negative no-evidence/no-note coverage, forbidden stable-claim wording checks,
  and deterministic one-note coverage were missing before fix. Why not 10:
  formal JSON-schema/golden coverage remains a future residual.
- Blocking findings: initial sub-9 critics found uncapped user-surface
  candidates, missing reusable future value, and weak note-contract tests.
  Fixes were implemented in `scripts/check-harness-dogfood.py` and
  `tests/test_harness_dogfood.py`.
- Score handling: score 9 PASS has why-not-10 wording fixes accepted as
  residual risk. Score 8 MIXED findings were treated as VETO before fix and
  accepted only after focused verification covered the note contract.
- Follow-up/residual risk: rendered maintenance-note length was accepted as a
  polish risk and then capped by a focused test. No stable governance evidence
  claim is made from this advisory review.
- Rerun status: focused verification reran after the note-contract fixes;
  `tests/test_harness_dogfood.py` now covers no-evidence/no-note, multiple
  internal candidates producing one note, explicit-vs-post-task surfacing,
  forbidden stable-claim wording, copy/rename status parsing, and rendered-note
  length.
- Final acceptance: advisory only; the post-task note contract is sufficient
  after focused verification, and `scripts/run-search-set.py` remains PASS for
  all Active cases.
