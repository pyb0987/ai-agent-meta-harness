# Multi-Review Benchmark Fixtures

This directory contains deterministic fixture scenarios for the `multi-review`
validator and benchmark contract. This is not an agent-in-the-loop benchmark:
it does not ask an AI to inspect `public_input` and produce a review. It checks
that benchmark manifests are well-formed and that existing validator fixtures
derive the expected verdict after declared mutations.

Each scenario lives at `scenarios/<axis>/<scenario_id>/scenario.yml`.
Scenario manifests are intentionally separate from `MultiReviewResult` artifacts
because the result schema is strict and should not carry benchmark-only oracle
metadata.

## Visibility Boundary

`public_input` is model-visible in future agent-in-the-loop evaluations. It uses
neutral ids and task-facing artifact refs.

`sealed_oracle` is runner-only metadata. It contains the expected derived
verdict, required validator error substrings, false-green target, primary
invariant, and typed oracle assertions. Do not expose sealed oracle fields to a
model under evaluation.

## Mutation Model

Most deterministic scenarios start from an existing valid fixture and apply
JSON-pointer-like mutations relative to the inner `MultiReviewResult` mapping.

Supported mutation operations:

- `set`: assign a value at a mapping key or list index.
- `delete`: remove a mapping key or list item.
- `append`: append a value to a list.

The runner is deliberately thin: it applies mutations, calls
`scripts/check-multi-review-result.py`'s `derive_verdict()`, then compares the
fresh verdict and error substrings to the sealed oracle.

## What This Checks

`check-fixtures.py` checks:

- scenario manifest shape;
- public/sealed oracle field separation;
- JSON-pointer mutation syntax;
- fresh `derive_verdict()` output from `scripts/check-multi-review-result.py`;
- expected verdict and expected validator error substrings;
- optional probe command replay for scenarios that request it.

It does not yet evaluate whether an AI can independently find the issue,
whether critic frames are semantically diverse beyond validator-visible fields,
or whether evidence relevance is judged by a semantic scorer.

## Running

Run all scenarios:

```bash
python3 benchmarks/multi-review/check-fixtures.py
```

Pending scenarios are not green by default. Use `--allow-pending` only for an
explicitly advisory benchmark pass, and use `--replay-probe-commands` when a
scenario declares active replay as part of its oracle.

## Perspective Eval Corpus

`perspective-eval/` is a separate starter corpus for future rubric-based
Perspective Quality Tests. It contains public scenario prompts, sealed rubric
anchors, and strong/weak candidate review outputs.

Those files are calibration material for a human or AI judge. They are not
currently scored by `check-fixtures.py`, and they should not be treated as
governance acceptance evidence.

Validate the corpus shape:

```bash
python3 benchmarks/multi-review/check-perspective-corpus.py
```
