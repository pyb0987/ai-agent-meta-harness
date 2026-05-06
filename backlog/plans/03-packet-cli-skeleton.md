# Plan 03: Packet CLI Skeleton

## Purpose

Implement the first repository-local v2 packet command without replacing release
gates.

Plan 02 fixed the `AcceptancePacket` shape and examples. Plan 03 turns that shape
into a small executable skeleton:

```bash
python3 scripts/check-governance-acceptance.py start --output <packet> --intent "..."
python3 scripts/check-governance-acceptance.py finalize --packet <packet> --staged
python3 scripts/check-governance-acceptance.py check --packet <packet>
```

The skeleton should make packet lifecycle mechanics real while leaving deeper
evidence capture, source-ref validation, review import, archive pointers, and
release integration to later plans.

## Success Criteria

- `start` writes a valid `AcceptancePacket` with public sections limited to
  `meta`, `input`, and `result`.
- `finalize` reads a start packet, updates lifecycle and generated result fields,
  and preserves the rule that users do not hand-author change class, required
  evidence, required review, or final eligibility.
- `check` is read-only and validates packet shape, lifecycle invariants, targeted
  input exception requests, targeted generated waivers/downgrades, score/VETO
  rules, and stable-handoff eligibility rules already fixed by Plan 02 fixtures.
- `--worktree` packets remain exploratory and cannot satisfy stable handoff.
- Stable accepted packets require closed required evidence and review records, but
  Plan 03 only validates review records already present in the packet. It does not
  import transcripts, discover reviews, or synthesize review records. Stable
  review records must carry critic, actor, role, date, source ref, score/VETO, and
  score-9 disposition fields.
- The command is not wired into pre-commit, release checks, or README install
  guidance in this plan.
- Tests cover CLI success and failure paths using temporary repositories and Plan
  02 fixtures.

## Scope

In scope:

- `scripts/check-governance-acceptance.py`
- tests for the packet CLI skeleton
- minimal shared fixture/schema checks if needed to avoid duplicated drift
- `backlog/v2-roadmap.md` only to mark Plan 03 boundaries

Out of scope:

- Replacing `scripts/verify-release.py`
- Wiring the packet checker into `.githooks/pre-commit`
- Full source-ref existence validation
- Search-set before/after capture
- Runtime/public/proof claim validation
- Review transcript import
- Packet archive pointers, canonical packet hashing, or active packet indexes
- Migrating v1 backlog records into packet form

## CLI Semantics

### `start`

Required behavior:

- Accept `--output`, `--intent`, optional `--actor`, and exactly one mode:
  `--staged`, `--base-ref <ref>`, or `--worktree`.
- Generate `meta.packet_id`, `schema_version`, `lifecycle: start`, `mode`,
  `created_at`, and `finalized_at: null`.
- Record caller input under `input.intent`, `input.actor`, `input.source_refs`,
  and `input.user_judgment`.
- Initialize fixture-shaped neutral generated result groups under
  `result.inference`, `result.evidence`, `result.judgment`, and
  `result.decision`; do not use bare empty objects where required packet fields
  are known.
- Refuse to overwrite an existing output file unless an explicit overwrite flag
  is introduced and tested.

### `finalize`

Required behavior:

- Read an existing start packet and write the same packet path.
- Support `--staged`, `--base-ref <ref>`, and `--worktree`; the finalize mode must
  match the packet mode. For `--base-ref`, the ref used at finalize must match the
  baseline ref recorded by `start`, and finalized evidence must preserve that ref
  for audit.
- Populate minimal generated inference from git diff paths:
  `changed_paths`, `intended_scope`, `actual_scope`, `deviations`, `isolation`,
  `change_class`, `impact`, `protected_boundary_changed`, `required_evidence`,
  and `required_review`.
- Populate minimal evidence only for local command status the skeleton can
  honestly observe, such as `git diff --check`. Plan 03 does not collect
  artifacts, capture before/after traces, validate runtime/public/proof claims,
  or resolve source refs. Missing required evidence must be represented as
  skipped or failed evidence, not silently accepted.
- Compute `decision.accepted` and `decision.stable_handoff_eligible` from packet
  contents. `worktree` mode always sets `stable_handoff_eligible: false`.
- Fail closed for harness-affecting or protected-boundary changes. Because review
  import is out of scope, Plan 03 finalization does not promote protected changes
  to stable handoff even if review-like records are already present; stable
  eligibility for such packets is checked only for pre-existing fixtures or later
  plans that introduce review import.

### `check`

Required behavior:

- Validate any packet without mutating it.
- Enforce the Plan 02 public shape and lifecycle invariants.
- Enforce stable packet requirements:
  required evidence passed or explicitly targeted by valid waiver/downgrade,
  required review covered by score >= 9 and no VETO or explicitly targeted by a
  valid waiver/downgrade, score 9 has why-not-10 plus disposition, and no broad
  untargeted waiver.
- Recompute seed inference consistency from `changed_paths`: protected paths must
  align with `protected_boundary_changed: true`, `change_class:
  harness-affecting`, `impact: high`, and required review.
- Enforce input-side exception request targetability before generated judgment is
  accepted. A `waiver_request` or `downgrade_request` without a required evidence
  or required review target is invalid.
- Require downgrades to declare `kind: evidence` or `kind: review`; one downgrade
  cannot satisfy both evidence and review obligations when names overlap.
- Treat packet validity and stable-handoff eligibility as distinct results. By
  default, `check` may return success for a valid blocked or non-stable packet
  while reporting `VALID: not stable-handoff eligible`, never `PASS`. A
  `--require-stable` option fails unless `result.decision.stable_handoff_eligible`
  is true.
- Report clear failures with non-zero exit status.

## Inference Boundary

Plan 03 uses a deliberately small rule table:

- `scripts/`, `.githooks/`, `core/`, `adapters/`, `skills/`, `commands/`,
  `plugins/`, `MAINTENANCE.md`, `README.md`, and `.harness/traces/search-set.md`
  are protected or harness-affecting surfaces.
- Protected or harness-affecting changes infer high impact, require at least
  `git diff --check`, already-present review closure, and any local command
  status the skeleton can honestly run without artifact collection.
- Documentation-only or fixture-only changes may infer routine impact, but must
  still record changed paths and isolation.

This rule table is intentionally seed-sized. Plan 04 can expand evidence capture
and source-ref validation without changing the public packet surface.

## Validation

Run:

```bash
python3 -m unittest tests/test_acceptance_packet_fixtures.py
python3 -m unittest tests/test_governance_acceptance_cli.py
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/start.yml
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-routine.yml
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/finalized-waiver-downgrade.yml
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/blocked.yml
python3 scripts/check-governance-acceptance.py check --packet backlog/fixtures/acceptance-packets/worktree-nonstable.yml
git diff --check
```

## Multi-Review Requirements

Before accepting this plan or its implementation, run multi-review with at least
these critic scopes:

- schema fidelity: confirms the CLI preserves the Plan 02 `meta`, `input`,
  `result` surface and does not make users hand-author generated fields.
- checker correctness: confirms `check` cannot green-light unstable packets,
  untargeted waivers, sub-threshold reviews, VETO records, or worktree stable
  handoff.
- implementation minimality: confirms Plan 03 does not smuggle Plan 04 evidence
  capture, Plan 05 review import, or Plan 06 archive integration into the
  skeleton.

All required critic scores must be at least 9. Any VETO requires updating the
plan or implementation and rerunning the affected critic. Every score 9 must
record a why-not-10 reason and residual-risk or follow-up disposition.

## Implementation Review Outcome

Multi-review:

- Schema fidelity critic: score 9, PASS. Blocking findings: none after reruns. Why not 10: skipped-input provenance has implementation coverage without an exact parallel fixture test. Follow-up/residual risk: accepted for Plan 03 because waiver, downgrade, residual, review, generated-inference, and public-shape checks are covered by CLI tests.
- Checker correctness critic: score 9, PASS. Blocking findings: none after reruns. Why not 10: Plan 03 still trusts packet-local evidence strings and defers source-ref and artifact validation to Plan 04. Follow-up/residual risk: accepted and carried to Plan 04 evidence capture.
- Implementation minimality critic: score 9, PASS. Blocking findings: none. Why not 10: skeleton placeholders such as trace refs and artifact refs are intentionally inert but close to later evidence-capture vocabulary. Follow-up/residual risk: accepted with Plan 04 boundary recorded below.
- Score handling: all required critics reached score 9 or higher after VETO-driven reruns. Every score 9 records why not 10 and residual-risk disposition.
- Rerun status: checker-correctness and schema-fidelity findings were fixed and rerun to score 9 with no VETO.
- Follow-up/residual risk: Plan 04 must validate source refs, artifacts, runtime/public/proof-like claim evidence, and v1 archive waiver durability.
- Final acceptance: accepted for Plan 03 implementation.

## Open Questions

- Whether the final public CLI should be `governance` or remain repository-local
  as `scripts/check-governance-acceptance.py`.
- Whether packet IDs should be timestamp-based, content-derived, or caller
  supplied before canonical archive hashing exists.
- How much inference belongs in the Plan 03 skeleton before Plan 04 source-ref
  and evidence capture are implemented.

## Carry-Over Requirements

- Plan 04 or Plan 06 must move any post-import `archive/v1/` waiver provenance
  from bootstrap CLI strings into durable packet `result.judgment` and/or
  `result.evidence` records before accepted archive edits are allowed to rely on
  v2 governance.
- Plan 04 must add content rules for runtime, public, or proof-like documentation
  claims so docs paths cannot remain routine/stable merely because they are
  outside the protected path table.
