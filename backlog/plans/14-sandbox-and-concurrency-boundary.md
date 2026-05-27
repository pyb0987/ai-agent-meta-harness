# Plan 14: Sandbox And Concurrency Boundary

## Status

Boundary definition only. Not scheduled for implementation. Any implementation
requires a later explicit decision slice.

Plan 14 exists to keep the Plan 13 repository-local default path simple while
labeling the harder sandbox and multi-writer guarantees that require a different
execution model.

## Purpose

Plan 13 completes the default Meta-Harness strategy-search mechanics:

```text
start -> propose -> eval -> select -> content commit -> v2 packet/pointer
```

That path assumes a non-hostile local operator and a fixed evaluator that is not
trying to exploit same-user OS privileges after the runner returns. Plan 14
defines the next boundary if the project later wants stronger claims:

- hostile same-user evaluator containment;
- transactional multi-writer proposal/eval coordination;
- external high-water marks for anchor refs;
- platform-level runtime and filesystem isolation.

This plan must not change the normal v2 stable handoff rule. Strategy-search
records remain diagnostic until a selected patch is applied as a content commit
and published through the v2 AcceptancePacket and active pointer flow.

## Design Principles

- Preserve the Plan 13 operator workflow by default.
- Do not add per-run manual digests, anchor refs, runtime paths, or sandbox
  knobs to the routine path.
- If Plan 14 later adds a hardening mode, prefer repository configuration or a
  single explicit mode over repeated per-command prompts.
- Prefer one optional hardening mode over many platform-specific flags.
- Treat platform sandbox failures as fail-closed diagnostics, not as stable
  governance evidence.
- Keep selected strategy-search output diagnostic-only even if sandboxed.

## In Scope

- A threat model for hostile same-user evaluator behavior.
- A platform abstraction for sandboxed evaluation, such as a container,
  restricted OS policy, or dedicated unprivileged evaluator user.
- A transactional proposal/eval store or lock model for concurrent writers.
- An external high-water mark or append-only anchor policy for environments that
  need protection against local ref rewinds.
- If an implementation mode is selected, tests that demonstrate Plan 13
  residual probes are either blocked by that mode or explicitly documented as
  still out of scope.

## Out Of Scope

- Making sandbox mode mandatory for normal repository-local strategy search.
- Changing v2 AcceptancePacket, review import, active pointer, or publication
  semantics.
- Claiming paper benchmark reproduction or agent semantic quality from sandbox
  isolation alone.
- Chasing every platform alias, race, or privilege edge case in the default
  non-sandboxed path.
- Replacing Plan 13 Git anchor events with an unrelated evidence system.

## Decision Gate

Plan 14 stays documentation-only unless a future deployment needs one of these
stronger claims:

- evaluators may be hostile same-user processes;
- more than one writer routinely runs `propose` or `eval` against the same run;
- local Git refs can be rewound by an actor outside the normal operator role;
- a release or benchmark claim depends on sandboxed evaluator containment.

Without one of those triggers, Plan 13 remains the completed repository-local
methodology and Plan 14 should not add new runtime options.

## Evidence Requirements By Decision

- Documentation-only: maintain the residual registry and do not add runtime
  tests beyond Plan 13 boundary checks.
- Local lock or high-water mark: add focused race/rewind regression tests and
  prove the normal single-operator path is unchanged.
- Sandbox mode: add probes for late host writes, runtime hijack, temp-sibling
  discovery, and process cleanup. Record sandbox diagnostics as diagnostic
  evidence only.
- Container or dedicated-user mode: document installation cost, platform
  support, filesystem visibility, and cleanup behavior before implementation.

## Candidate Slices

These are planning slices. No slice below implies implementation until Slice 4
chooses a concrete mode and records why the extra complexity is worth it.

### Slice 1: Threat Model And Residual Registry

Collect the residuals intentionally left outside Plan 13:

- detached descendants writing absolute host paths after runner exit;
- transient runtime or shim hijack-and-restore by the evaluator user;
- temp-sibling discovery of source or run-store paths;
- case-insensitive or platform alias attacks;
- concurrent proposal sealing races;
- hostile local rewinds of otherwise valid Git anchor refs.

Acceptance: each residual has an actor, required capability, expected impact,
and whether Plan 14 should block, detect, or explicitly defer it.

### Slice 2: Sandbox Contract

Define a single runner-facing contract:

```text
evaluate(candidate, workspace, command) -> stdout/stderr bytes, exit status,
traceable sandbox diagnostics
```

Acceptance: the contract says what paths are visible, what writes are possible,
how process cleanup works, and what evidence is recorded when sandbox setup or
cleanup fails.

### Slice 3: Concurrency Contract

Define whether Plan 14 needs:

- a run-level lock;
- transactional proposal sealing;
- append-only anchor storage;
- an external high-water mark.

Acceptance: normal single-operator commands remain unchanged, and concurrent
failures do not leave partially sealed proposals that look ready.

### Slice 4: Optional Implementation Decision

Choose one of:

- no implementation, only documented residuals;
- local lock/high-water mark only;
- sandbox mode for one supported platform;
- container or dedicated-user execution mode.

Acceptance: the decision includes cost, portability, new dependencies, and the
effect on user input minimization.

### Slice 5: Multi-Review

Run the plan through these critic lenses:

- simplicity and operator-minimality;
- methodology completeness;
- security boundary honesty;
- portability and maintenance cost;
- v2 governance separation.

Acceptance: no critic may require changing the Plan 13 default flow unless the
project explicitly decides to make sandbox mode mandatory.

## Initial Recommendation

Do not implement Plan 14 immediately. Keep it as a boundary and residual
registry unless a real deployment needs hostile same-user containment or
multi-writer transactional guarantees.

The next productive work is to multi-review this boundary and decide whether
Plan 14 should stay as documentation or split into a narrow implementation
slice.

## Multi-Review Iteration 1

Verdict: PASS as a boundary document; no implementation slice selected.

- Simplicity and operator-minimality critic: score 9 PASS. Finding accepted:
  boundary-only wording could drift into a hidden implementation plan. Fixed by
  the Decision Gate, user-input budget, and evidence requirements by decision.
- Methodology completeness critic: score 9 PASS. Plan 13 remains the completed
  repository-local methodology; Plan 14 only names stronger optional claims.
- Security boundary honesty critic: score 9 PASS. The plan now distinguishes
  documentation-only residual tracking from actual sandbox or concurrency
  enforcement.
- Portability and maintenance critic: score 9 PASS. No platform sandbox,
  container, or dedicated-user mode is selected without a later cost decision.
- v2 governance separation critic: score 10 PASS. Sandboxed search output stays
  diagnostic and cannot replace content commits, AcceptancePackets, or active
  pointer publication.

Follow-up: keep Plan 14 as documentation until a concrete deployment need
triggers the Decision Gate.
