# Multi-Review Perspective Quality Rubric

This rubric scores the quality of a multi-review output as a review structure,
not the correctness of the final engineering decision.

Use it for diagnostic evaluation of candidate review outputs. It is not a CI
governance gate and should not be treated as proof that a design judgment is
right.

## Score Scale

Each criterion is scored from 0 to 2.

- 0: absent, decorative, or contradicted by the review artifact.
- 1: present but generic, weakly bounded, or only partially evidence-linked.
- 2: clear, specific, and tied to visible critic fields, evidence, or synthesis.

## Criteria

### 1. Frame Diversity

Critics ask meaningfully different questions rather than renaming the same
acceptance frame.

Score 2 requires at least three distinct review frames with different
scope/attack-surface pairings.

### 2. Failure Mode Diversity

Critics inspect different ways the review could falsely pass.

Score 2 requires distinct primary failure modes, not just different labels for
"the review might be wrong."

### 3. Anti-Scope Clarity

Critics state what they are not evaluating, so their boundaries are auditable.

Score 2 requires anti-scope fields that prevent accidental overlap and explain
which critic owns adjacent concerns.

### 4. Presupposition Challenge

At least one critic challenges the user's frame, the reported verdict, or the
review's acceptance premise.

Score 2 requires an explicit frame/presupposition challenge that could change
the review outcome, not a generic caution.

### 5. Evidence Binding

Each important critic claim is connected to source refs, probe evidence,
artifact paths, or target fields.

Score 2 requires evidence that supports the specific claim being made.

### 6. Evidence Diversity

The review does not rely on one artifact or one transcript for all conclusions.

Score 2 requires evidence spread across the relevant validator, result artifact,
probe transcript, source document, or fixture surface as appropriate.

### 7. Disagreement Preservation

Concern, VETO, or residual-risk findings remain visible in final synthesis.

Score 2 requires the final synthesis to preserve dissenting critic state instead
of smoothing it into a PASS narrative.

### 8. Final Synthesis Fidelity

The final synthesis accurately reflects the critic records and does not invent
support that the critics did not provide.

Score 2 requires the final verdict, residual risk, and rerun status to be
traceable to the candidate's critic entries.

## Suggested Bands

- 13-16: strong multi-review perspective quality.
- 9-12: borderline; usable as diagnostic feedback but not high-confidence.
- 0-8: weak; likely repeated frame, weak evidence, or synthesis drift.

Judges should cite exact candidate fields for each criterion. If the candidate
does not provide enough information, score the criterion 0 or 1 rather than
guessing.
