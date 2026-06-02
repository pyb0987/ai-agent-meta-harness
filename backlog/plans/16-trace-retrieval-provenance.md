# Plan 16: Trace Retrieval Provenance

## Status

Implemented for the repository-local harness. This plan defines the next
evidence-discipline layer for trace retrieval. It is not an access-control
plan.

## Purpose

Meta-Harness depends on raw traces, not summaries. As trace roots grow, however,
agents can miss relevant history, over-read the whole tree, or cite a trace path
without proving that the cited raw bytes were actually inspected.

Plan 16 keeps the raw-data-first principle while making retrieval claims more
checkable:

```text
Trace catalog: helps find raw traces.
Raw trace quote: supports evidence claims.
Checker: verifies quoted bytes match the cited raw trace.
Review: judges whether the selected traces were sufficient and relevant.
```

The goal is to improve retrieval honesty without making ordinary users learn a
new workflow or turning the repository into a filesystem sandbox.

## Core Position

Selective retrieval is a discipline and evidence rule, not a filesystem
access-control boundary.

Agents may still full-scan trace roots when justified. That is intentional: raw
trace access must remain available for small trace roots, migration audits,
catalog-corruption checks, broad forensic passes, and explicit user requests to
audit the whole history.

The enforceable boundary is narrower:

- harness-changing claims must record `retrieval.mode`;
- raw-trace evidence must cite raw trace bytes, not catalog entries alone;
- catalog entries must not certify or replace raw trace evidence;
- checkers verify quote/path/line integrity, not semantic completeness.

## Problem Statement

Current trace retrieval has three practical gaps:

1. **Selective access is recommended, not enforced.** Skill prose can ask agents
   to search first, but an agent can still read every trace or claim retrieval
   without leaving a useful record.
2. **There is no retrieval catalog.** `grep` plus `search-set.md` is useful but
   keyword fragile. Relevant traces can be missed when they use different words
   or when important evidence lies beyond the initial read window.
3. **Experiment traces degrade fastest.** `experiments/` records are often
   prose episodes without classification fields, so retrieval tends toward
   whole-file reads as the subtree grows.

Plan 16 addresses those gaps without replacing raw traces with summaries.

## Non-Goals

- Do not block filesystem reads.
- Do not require a sandbox, tool proxy, separate evaluator user, or permission
  gate for trace files.
- Do not introduce semantic/embedding retrieval in the MVP.
- Do not let catalog summaries stand in for raw trace evidence.
- Do not require ordinary users to write retrieval records by hand.
- Do not make every feature request run trace retrieval.

## Retrieval Modes

Harness-changing records may use one of three modes inside a single
`retrieval` block. Do not support a separate top-level `retrieval_mode` field;
two parallel spellings would create avoidable drift.

```yaml
retrieval:
  mode: selective
```

Used when the agent searched targeted trace history and opened selected raw
trace files.

```yaml
retrieval:
  mode: full_scan
  reason: "Catalog was suspected stale after trace-root migration."
```

Used when the agent intentionally inspected the whole trace root or a whole
subtree. This is allowed, but `reason` is mandatory so broad inspection remains
auditable instead of becoming a silent default. Because `full_scan` still makes
a trace-history claim, it also requires byte-matching `raw_trace_refs`.

```yaml
retrieval:
  mode: not_needed
  reason: "Format-only change; no historical trace claim was made."
```

Used when the change does not depend on historical trace evidence, such as a
format-only fix or a new project with no meaningful trace history. `reason` is
mandatory for `not_needed`.

## Mandatory Evidence Shape

For harness-impacting claims that depend on trace history, require raw trace
refs with byte-matching quotes:

```yaml
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .claude/traces/failures/001-simulator-bot-logdd-divergence.md
      lines: 17-27
      quote: "시뮬레이터 | **All-time expanding max**"
```

MVP checker behavior:

- `file` must resolve under the configured trace root.
- `lines` must be a bounded positive line range.
- `quote` must encode to UTF-8 bytes that occur inside the byte span for the
  cited line range. The checker should split source files by raw newline bytes,
  preserve line endings for span calculation, and avoid replacing this with a
  generated summary comparison.
- cited line spans must be narrow: at most 40 lines.
- quotes must be substantial: at least 24 non-whitespace characters.
- multi-line quotes are allowed when they match bytes within the cited span.
- catalog files are not accepted as `raw_trace_refs`.
- a record that cites only a catalog entry is not sufficient evidence.
- `mode: full_scan` and `mode: not_needed` require `reason`.
- `mode: selective` and `mode: full_scan` require non-empty `raw_trace_refs`.
- structural evolution traces cannot use `mode: not_needed`.

This proves that the cited bytes exist. It does not prove that the agent's
interpretation is correct or that retrieval was complete.

## Optional Retrieval Detail

Agents may include richer provenance when it helps review, but these fields are
not required for ordinary harness changes:

```yaml
retrieval:
  mode: selective
  query: "logDD simulator live bot drift"
  candidates_considered:
    - .claude/traces/failures/001-simulator-bot-logdd-divergence.md
    - .claude/traces/experiments/001-retroactive-r1-r24.md
  raw_trace_refs:
    - file: .claude/traces/failures/001-simulator-bot-logdd-divergence.md
      lines: 17-27
      quote: "시뮬레이터 | **All-time expanding max**"
  why_selected: "The failure trace records the original simulator/live bot drift."
  why_excluded:
    .claude/traces/experiments/001-retroactive-r1-r24.md: "Experiment result context, not the root failure."
```

The design deliberately keeps the mandatory layer small to preserve v2's
operator-minimal product shape.

## Trace Catalog Boundary

The catalog is a retrieval aid, not a summary layer.

Allowed catalog fields:

```yaml
trace: .claude/traces/failures/001-simulator-bot-logdd-divergence.md
kind: failure
status: active
date: "2026-04-19"
tags: [logdd, simulator, live-bot, drift]
files:
  - simulation/strategy_simulator.py
  - bot/asset_dd.py
search_set_refs: [SS-001]
```

Avoid narrative `summary` or `lesson` fields in the MVP catalog. If a later
version adds them, they must be labeled non-certifying and must not satisfy
evidence requirements.

Catalog generation must be deterministic from current trace files. If a query
helper uses a stored catalog, it should either rebuild it first or fail closed
when the catalog is stale relative to the trace tree metadata it claims to
cover. Stale-catalog handling is about retrieval freshness, not evidence
certification.

## Experiment Metadata

Experiment episodes should become grep-able without becoming summaries. New or
updated experiment traces should carry minimal frontmatter:

```yaml
kind: experiment
date: "2026-06-01"
objective: "reduce card spawn drift"
metric: "lint pass + unit tests"
verdict: rejected
tags: [card-spawn, codegen, lint]
evaluator: "python3 scripts/lint_card_spawn.py"
```

The episode body remains the raw trace. The frontmatter only makes retrieval
less fragile.

## Implementation Slices

### Slice 1: Schema And Documentation

- Define the retrieval block shape in `core/reference.md`.
- Update Codex and Claude project templates to state that trace catalog entries
  are pointers, not evidence.
- Document the three retrieval modes and the byte-matching quote rule.
- Add examples for `.harness/traces/` and `.claude/traces/`.

### Slice 2: Quote Checker

- Add a small checker for retrieval blocks in evolution/failure traces.
- Validate trace-root confinement, line ranges, and quote byte matches.
- Reject catalog-only evidence for harness-impacting claims.
- Require `reason` for `mode: full_scan` and `mode: not_needed`.
- Require non-empty `raw_trace_refs` for `mode: selective` and
  `mode: full_scan`.
- Treat top-level `retrieval_mode` as invalid so the schema has only one
  spelling.
- Keep semantic sufficiency out of the checker.

### Slice 3: Lightweight Catalog Builder

- Add a deterministic catalog builder that scans frontmatter only.
- Write `trace-catalog.jsonl` or equivalent under the trace root.
- Include only path, kind, status, date, tags, touched files, and
  search-set refs.
- Do not generate narrative summaries.
- Include enough catalog metadata for the query helper to detect stale stored
  catalogs and rebuild or fail closed.

### Slice 4: Trace Query Helper

- Add a lexical query helper over catalog metadata and raw filenames.
- Return candidate raw trace paths with matched fields.
- Require callers to open raw traces before using them as evidence.
- Keep query output non-certifying.

### Slice 5: Experiment Frontmatter Migration

- Add or update experiment trace templates with `kind`, `objective`, `metric`,
  `verdict`, `tags`, and `evaluator`.
- Provide a best-effort checker warning for experiment records missing these
  fields.
- Avoid rewriting historical experiment bodies unless a migration is explicitly
  reviewed.

### Slice 6: Project Template Routing

- Update installed project instructions so agents naturally use catalog/query
  for discovery and raw trace quotes for claims.
- Keep ordinary user language unchanged: users should still ask normal
  questions, report repeated failures, or request review without naming the
  retrieval machinery.

## Acceptance

- Harness-impacting trace claims can be checked for raw quote/path/line
  integrity.
- Retrieval records use one canonical schema: `retrieval.mode`.
- `full_scan` and `not_needed` records explain why broad retrieval or no
  retrieval was appropriate.
- Catalog entries cannot satisfy raw trace evidence requirements by themselves.
- Experiment records have enough metadata for deterministic retrieval.
- The default user experience remains unchanged: users do not need to know
  retrieval modes, catalog files, or checker internals.
- Documentation states the residual clearly: the checker verifies cited bytes,
  not semantic relevance or retrieval completeness.

## Implementation Record

- Slice 1 implemented in `core/reference.md`, `docs/reference.md`, Codex
  AGENTS templates, Claude examples, and harness-engineer skills.
- Slice 2 implemented in `scripts/check-trace-retrieval-provenance.py` and
  `.githooks/pre-commit`, with staged-index-only reads, bounded quote spans,
  minimum quote substance, and a `not_needed` block for structural evolution
  traces.
- Slice 3 and Slice 4 implemented in `scripts/trace-query.py`: catalog output
  is metadata-only JSONL, query output is candidate raw trace paths, and stored
  catalog use fails closed when source hashes are stale.
- Slice 5 implemented as best-effort experiment metadata warnings in
  `scripts/trace-query.py check-experiments`.
- Slice 6 implemented through init-harness instructions and generated Codex
  fixture contracts so initial traces record `retrieval.mode` without user
  ceremony.

Search-set verification:

- BEFORE: SKIPPED no pre-change Active search-set run was captured before Plan
  16 implementation began.
- AFTER: PASS `python3 scripts/run-search-set.py` (6 Active case(s), including
  pre-commit with trace retrieval provenance).

## Residual Risks

- A byte-matching quote proves that cited text exists, not that the agent read
  enough surrounding context.
- A catalog can still be incomplete or stale; broad scans remain legitimate when
  catalog quality is in doubt.
- Semantic relevance and completeness remain review responsibilities.
- Strong access-control claims remain Plan 14 territory and are not part of this
  default workflow.

## Multi-review

- Mode: sequential fallback review with separated critics; no sub-agent
  independence claimed.
- Raw-Data Principle Critic: score 9, PASS. Blocking findings: none. The plan
  correctly treats the catalog as a retrieval pointer and makes raw trace quotes
  the evidence surface. Why not 10: later implementation must keep catalog
  fields non-narrative. Follow-up/residual risk: accepted.
- Verifiability Critic: initial score 8, VETO; final score 9, PASS after fix.
  Initial issue: the plan used both top-level `retrieval_mode` and
  `retrieval.mode`, and "byte-matching" did not specify how the checker should
  compare quotes to raw files. Fix: one canonical `retrieval.mode` schema,
  invalid top-level `retrieval_mode`, mandatory `reason` for `full_scan` and
  `not_needed`, and UTF-8 byte-span quote matching over cited line ranges. Why
  not 10: semantic relevance is intentionally outside the checker.
  Follow-up/residual risk: accepted.
- User-Experience Critic: score 9, PASS. Blocking findings: none. Mandatory
  ceremony is limited to `retrieval.mode` plus byte-matching raw refs when trace
  history is used; ordinary users do not need to know the mechanism. Why not
  10: agents still need good templates to choose the mode automatically.
  Follow-up/residual risk: accepted.
- Implementation-Scope Critic: initial score 8, VETO; final score 9, PASS after
  fix. Initial issue: catalog freshness and optional provenance examples could
  drift into a second evidence path. Fix: stored catalogs must rebuild or fail
  closed when stale, optional provenance examples now include the mandatory raw
  quote block, and catalog output remains non-certifying. Why not 10: exact
  stale-catalog metadata belongs in Slice 3 design. Follow-up/residual risk:
  accepted.
- Completeness/Residual Critic: score 9, PASS. Blocking findings: none. The
  residual is stated honestly: quote matching proves bytes exist, not that the
  retrieval was complete or semantically sufficient. Why not 10: completeness
  still requires review judgment. Follow-up/residual risk: accepted.
- Score handling: all final critic scores are at least 9. Initial sub-9
  findings were fixed before this record.
- Final acceptance: accepted for Plan 16 planning. Proceed to Slice 1 when
  implementation is requested.

## Implementation Multi-review

Multi-review:

- Mode: sequential fallback review with separated critics; no sub-agent
  independence claimed.
- Raw-Evidence Critic: score 9, PASS. Blocking findings: none. The checker
  verifies raw trace byte quotes, rejects catalog refs as evidence, caps cited
  spans, and rejects trivial quotes. Residual: quote existence still does not
  prove semantic sufficiency.
- User-Experience Critic: score 9, PASS. Blocking findings: none. Init
  instructions and fixture contracts choose `not_needed` for first setup and
  `selective` for reused history, so ordinary users do not need to know the
  schema.
- Catalog-Boundary Critic: score 9, PASS. Blocking findings: none.
  `trace-query.py` emits metadata-only catalog rows and query results are raw
  trace path candidates. Stored catalog use fails closed on full canonical
  catalog-record drift, not only source-hash drift.
- Verification Critic: score 9, PASS. Blocking findings: none. New unit tests
  cover quote matching, catalog staleness, query behavior, experiment metadata
  warnings, pre-commit wiring, templates, and mirror sync.
- Follow-up/residual risk: semantic completeness remains an explicit review
  responsibility, not a checker claim.
- Score handling: all final critic scores are at least 9. Why not 10: byte
  matching cannot prove semantic completeness, and this was accepted as
  residual risk rather than expanded into access control.
- Rerun status: after implementation fixes, targeted unit tests, mirror checks,
  maintenance review validation, diff whitespace checks, and Active search-set
  verification all passed.
- Final acceptance: accepted for Plan 16 repository implementation as advisory
  implementation review. This prose multi-review is not a governance-mode
  MultiReviewResult artifact and is not stable acceptance evidence by itself.

## Follow-up Review

Multi-review:

- Mode: sequential fallback review with separated critics; no sub-agent
  independence claimed.
- Provenance-Theater Critic: score 9, PASS. Blocking findings: fixed before
  acceptance. Initial issue: wide line spans and trivial quotes could satisfy
  byte matching while proving little. Fix: cap cited spans at 40 lines and
  require at least 24 non-whitespace quote characters. Why not 10: quote
  matching still cannot prove the agent read enough context. Follow-up/residual
  risk: accepted.
- Escape-Hatch Critic: score 9, PASS. Blocking findings: fixed before
  acceptance. Initial issue: `mode: not_needed` could be used on high-stakes
  structural harness changes. Fix: structural evolution traces cannot use
  `not_needed`. Why not 10: lower-risk additive/subtractive records can still
  use `not_needed` with a reason. Follow-up/residual risk: accepted.
- Target-Project Critic: score 9, PASS. Blocking findings: none. The docs now
  state that git-excluded target-project traces are not covered by repository
  pre-commit and need manual checker or project hook invocation. Why not 10:
  automatic enforcement in every target project remains adapter/runtime
  specific. Follow-up/residual risk: accepted.
- Score handling: all final critic scores are at least 9. Why not 10:
  semantic completeness and non-staged target-project hooks remain outside the
  repository-local checker boundary.
- Rerun status: targeted unit tests, mirror checks, maintenance review
  validation, and pre-commit passed after the follow-up fixes.
- Final acceptance: accepted for Plan 16 follow-up implementation.
