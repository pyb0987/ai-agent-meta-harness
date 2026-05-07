# Multi-Review Perspective Eval Corpus

This corpus is the starting point for future Perspective Quality Tests.

It is intentionally different from `check-fixtures.py`:

- `check-fixtures.py` is deterministic and validates benchmark manifests plus
  validator behavior.
- `perspective-eval/` contains candidate review outputs that a human or AI judge
  can score with `../perspective-rubric.md`.

The goal is not to decide whether the reviewed design is correct. The goal is to
measure whether a multi-review output actually provides multiple review
perspectives, binds those perspectives to evidence, and preserves disagreement
or residual risk in synthesis.

## Scenario Layout

Each scenario directory contains:

- `public-input.md`: model-visible task context for a future agent run.
- `sealed-rubric.yml`: runner/judge-only anchors and scoring expectations.
- `candidate-strong.yml`: calibration candidate that should score high.
- `candidate-weak.yml`: calibration candidate that should score low.

The sealed rubric should identify anchored risks rather than hidden "gotcha"
answers. Good anchors point to specific critic fields, source refs, evidence
refs, or synthesis contradictions.

## Current Scope

These fixtures are calibration material for a future semantic judge. They are
not currently scored by an automated AI judge, and they are not governance
acceptance evidence.
