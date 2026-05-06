# Plan 01: Compatibility Checker Migration

## Purpose

Prepare the repository for v2 packet governance without creating false
confidence from v1 checkers.

The v1 archive now lives under `archive/v1/`, while existing checkers were built
around active v1 backlog paths such as `backlog/archive/*`. This plan defines
the first implementation layer: make checker and test behavior honest about what
is validated, what is frozen historical evidence, and what remains a documented
gap before packet governance exists.

## Success Criteria

- v1 archive records under `archive/v1/` are either explicitly indexed by
  compatibility checks or explicitly exempted as frozen historical evidence.
- No checker output implies that frozen v1 archive records were validated unless
  they actually were.
- Active `backlog/` remains v2-oriented and does not revive v1 backlog queues.
- Future v2 packet archive validation has a distinct namespace, currently
  `archive/v2/packets/`.
- Tests cover the chosen archive compatibility rule and fail if docs claim more
  coverage than the checkers provide.

## Scope

In scope:

- `scripts/check-maintenance-review.py`
- `scripts/check-backlog-archive-lifecycle.py`
- tests for maintenance review, archive lifecycle, and v2 maintenance boundary
- `MAINTENANCE.md`
- `backlog/v2-roadmap.md`
- v1 archive index documentation

Out of scope:

- Implementing `check-governance-acceptance.py`
- Defining the full `AcceptancePacket` schema
- Migrating old v1 records into packet form
- Rewriting adapter behavior or runtime hooks

## Design Options

### Option A: validate frozen v1 archive records

Extend compatibility checkers to scan `archive/v1/backlog/` in addition to any
legacy active backlog paths.

Pros:

- Preserves mechanical review-quality visibility over the frozen evidence corpus.
- Avoids ambiguity when old review records are cited as v2 requirements.

Cons:

- Keeps v1 record-shape parsing alive longer.
- Can make v1 archive warnings look like active v2 blockers unless output is
  carefully labeled.

### Option B: explicitly exempt frozen v1 archive records

Teach checkers and tests that `archive/v1/` is immutable historical evidence and
not part of active release validation.

Pros:

- Keeps active maintenance focused on v2.
- Avoids spending implementation effort on deeper v1 compatibility.

Cons:

- Loses mechanical validation of frozen v1 review/archive quality.
- Requires docs to be very honest that v1 archive evidence is preserved, not
  actively revalidated.

### Recommendation

Start with **Option B plus mandatory reporting and immutability guard**:

- Exempt `archive/v1/` from active v1 checker failure semantics.
- Add a default checker or required report line that says frozen v1 archive
  records are preserved but not actively revalidated by the compatibility gate.
  This report must appear in the normal validation path, not only in optional
  prose or verbose mode.
- Add a mechanical immutability guard for `archive/v1/`: either a hash/index
  check, a git-diff guard that fails on archive changes without an explicit
  maintainer waiver, or an equivalent tested mechanism.
- Add tests that prevent the docs from claiming full v1 archive validation.

This keeps v2 simple, makes the validation gap visible, and preserves v1 as a
stable trace corpus. If future work cites v1 archive records as active evidence,
a later plan can add targeted indexing.

## Implementation Steps

1. Add `scripts/check-v1-archive-boundary.py` as the explicit compatibility
   report and immutability guard for `archive/v1/`.
2. Add fixture tests for the frozen v1 archive boundary.
3. Update default checker output or a required report command so compatibility
   checks do not imply coverage of `archive/v1/` unless they scan it.
4. Add an immutability guard for `archive/v1/`, with a waiver fixture for
   intentional archive index/path-repair work.
5. Ensure active backlog lifecycle checks ignore packet paths and v1 archive
   paths by design.
6. Add tests for active v2 backlog stubs and roadmap-only planning.
7. Record the selected compatibility rule in `MAINTENANCE.md` and
   `backlog/v2-roadmap.md`.

## Validation

Run:

```bash
python3 scripts/check-maintenance-review.py
python3 scripts/check-v1-archive-boundary.py
python3 scripts/check-v1-archive-boundary.py --base-ref origin/main
python3 scripts/check-backlog-archive-lifecycle.py
python3 scripts/check-v1-archive-boundary.py --staged
python3 scripts/check-backlog-archive-lifecycle.py --staged
python3 scripts/check-search-set-evidence.py
python3 -m unittest tests/test_maintenance_policy_boundaries.py
python3 -m unittest tests/test_v1_archive_boundary.py
python3 -m unittest tests/test_backlog_archive_lifecycle.py
python3 -m unittest tests/test_check_maintenance_review.py
python3 -m unittest tests/test_backlog_heading_uniqueness.py
python3 -m unittest tests/test_pre_commit_hook.py
python3 -m unittest tests/test_verify_release.py
git diff --check
```

If release/pre-commit integration is intentionally deferred for this first
migration, the implementation must record that boundary and add a test proving
the checker/report command still prevents false confidence about `archive/v1/`.

## Multi-Review Requirements

Before accepting this plan or its implementation, run multi-review with at least
these critic scopes:

- v2 methodology fidelity: confirms the plan does not revive v1 human-authored
  governance.
- checker correctness: confirms the selected compatibility rule cannot produce
  false green release confidence.
- operator simplicity: confirms the plan reduces user-facing governance burden.

All required critic scores must be at least 9. Any VETO requires updating the
plan or implementation and rerunning the affected critic.

Review acceptance must also preserve v2 judgment provenance:

- every waiver, downgrade, skipped required evidence, residual-risk acceptance,
  or review exception records actor, role, date, reason, and source reference
- every score 9 records why-not-10 and residual-risk or follow-up disposition
- compatibility checker changes identify whether evaluator/checker boundaries
  changed and why the change is eligible for acceptance

## Open Questions

- Should `archive/v1/` immutability be enforced by a dedicated checker,
  hash/index fixture, or git-diff guard?
- Should the mandatory v1 archive coverage report live in each compatibility
  checker's default output or in one required report command?
- When v2 packet validation exists, should frozen v1 archive references be
  allowed as `source_ref` values?
