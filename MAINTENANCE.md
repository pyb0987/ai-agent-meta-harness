# Maintenance Plan

This document defines the active maintenance model for the v2 transition.
This repository operationalizes Meta-Harness paper principles into a practical
harness toolkit, runtime adapters, and verification gates; it is not a paper
reproduction package or a claim that this local repo has demonstrated the
paper's benchmark gains.

The v1 maintenance system is frozen at `archive/v1/MAINTENANCE.md`. Its Start
Gate, Completion Gate, review-summary labels, fallback-threshold disposition,
and backlog archive lifecycle are historical evidence, not the active design
target.

## Active Direction

AI Agent Meta-Harness v2 replaces human-authored maintenance gates with
generated acceptance packets. The active roadmap is `backlog/v2-roadmap.md`.

The v2 maintenance model is:

1. Humans provide small intent and judgment inputs.
2. The harness infers change class, impact, required evidence, required review,
   and eligibility from git state, path/content rules, traces, and artifacts.
3. The harness stores the result as an `AcceptancePacket`.
4. Stable handoff is accepted only from packet-backed base-ref verification;
   staged verification is preflight evidence, not active stable handoff.

The main v2 product requirement is simplicity: reduce the user interface and
the mental model, not the methodology evidence. If a maintenance change makes
operators hand-author more governance fields, remember more special cases, or
inspect more top-level concepts than `meta`, `input`, and `result`, treat that
as design debt unless the change removes a concrete failure mode that cannot be
handled by packet generation or checker inference.

The public packet shape is:

```yaml
AcceptancePacket:
  meta: {}
  input: {}
  result:
    inference: {}
    evidence: {}
    judgment: {}
    decision: {}
```

## Methodology Anchors

Maintenance work must preserve these Meta-Harness anchors:

- Fixed evaluator boundary: evaluator commands, protected paths, boundary
  changes, and disposition must be visible in packet evidence.
- Trace reuse: search-set before/after evidence, evolution trace disposition, and
  failure trace disposition must be preserved when relevant.
- Confounder isolation: packet evidence must distinguish intended scope, actual
  changed files, deviations, and whether the change was isolated or bundled.
- Evidence honesty: runtime, public, or proof-like claims must be structured;
  verified claims require raw artifact, log, screenshot, or exported trace refs.
- Human judgment boundary: waivers, downgrades, skipped required evidence,
  residual-risk acceptance, and review exceptions require actor, role, date,
  reason, and source reference.

## v2 Packet Lifecycle

Target commands:

```bash
governance start --intent "..." [--exception ...] [--output <packet>]
governance finalize --packet <packet> --staged|--base-ref REF|--worktree
governance check --packet <packet>
```

Lifecycle rules:

- `start` captures baseline state before edits.
- `finalize` updates evidence and computes `result.decision.eligibility`.
- `check` is read-only and does not mutate packet lifecycle state.
- Stable handoff uses `--base-ref`; `--staged` is preflight-only.
- `--worktree` is exploratory or in-progress unless explicitly marked
  non-stable.
- Harness-affecting finalization fails closed without a start packet unless an
  exact skipped-before reason and maintainer/reviewer disposition are recorded.

Until the v2 checker exists, v2 implementation work must record a bootstrap
transition note that includes:

- intent
- changed files
- whether the work would be harness-affecting under the v2 rule table
- required evidence that could not yet be captured as a packet
- exact skipped-before reason when no start packet exists
- reviewer or maintainer disposition for any waiver, downgrade, skipped required
  evidence, or residual risk
- explicit statement that the record is not a finalized v2 packet

This bootstrap note is temporary compatibility evidence, not the v2 target.

## Active Roadmap

Use `backlog/v2-roadmap.md` as the single active roadmap.

Do not carry v1 backlog items forward by default. Extract v2 requirements from
v1 only when they explain a repeated failure mode or a packet/checker
requirement.

## v1 Compatibility

The frozen v1 archive is a historical trace corpus:

- `archive/v1/README.md`
- `archive/v1/MAINTENANCE.md`
- `archive/v1/backlog/`

Legacy checkers may remain useful while v2 is bootstrapped, but they are
compatibility checks for old record shapes. They do not prove that frozen v1
records under `archive/v1/` are fully covered unless the checker explicitly says
so.

The first v2 implementation sequence should close that compatibility gap before
claiming stable packet governance:

1. Define how frozen v1 archives are indexed or intentionally exempted.
2. Add tests for `archive/v1/` immutability or documented exemption.
3. Define the v2 packet archive namespace.
4. Add packet pointer/hash/source-ref validation fixtures.

## Packet Archive Direction

Use a distinct v2 packet namespace. Prefer `archive/v2/packets/` unless an
implementation review chooses a stronger location such as
`.harness/governance/packets/`.

Do not reuse v1 backlog archive semantics for v2 packets. A completed active
pointer should eventually validate:

- packet file exists
- packet hash matches if present
- packet lifecycle is finalized
- `result.decision.accepted: yes`
- required source refs resolve

## Active Governance Boundaries

During the v2 transition, keep the active operator model to four boundaries:

- `check` is read-only. Stable handoff validation may read packets, source
  refs, transcripts, and command artifacts, but it must not execute
  artifact-supplied probe commands.
- `replay` is explicit. Probe commands may run only through an explicit replay
  path such as `python3 scripts/check-multi-review-result.py --result <path>
  --replay-probe-commands`; replay is not part of stable packet `check`.
- `stable` validates durable structural evidence. A stable packet proves
  closure through recomputed required evidence/review, structured imports,
  source refs, transcripts, and reopenable packet-bound command artifacts, not
  by trusting reported PASS prose. Command artifact authenticity remains an
  archive/trusted-runner provenance responsibility for Plan 07.
- generated artifact refs use explicit schemes. Stable artifact and probe
  evidence refs use `file:`, trace refs use `trace:`, and active base-ref
  stable changed-path source refs use HEAD-pinned `git:<full-commit-sha>:<path>`
  refs. Broader source refs are allowed only for non-active fixtures or later
  archive policy decisions.

## Verification During Transition

Before the v2 checker exists, run the narrow compatibility checks that still
cover the changed surface and record known gaps honestly. For this transition,
passing legacy v1 checkers means only that old record-shape validators did not
find an error in their configured paths.

Standard verification:

```bash
python3 scripts/check-compat-mirrors.py
python3 scripts/check-claude-adapter-paths.py
python3 scripts/sync-codex-plugin.py --check
python3 adapters/codex/scripts/check-codex-hook-schema-drift.py
python3 adapters/codex/scripts/smoke-autoresearch-hooks.py --checker adapters/codex/scripts/check-autoresearch-protected.py --protected-file adapters/codex/templates/autoresearch-protected.txt
python3 adapters/codex/scripts/smoke-local-plugin.py
python3 adapters/codex/scripts/smoke-local-plugin-activation.py
python3 scripts/check-codex-marketplace-metadata.py
python3 scripts/check-maintenance-review.py
python3 scripts/check-v1-archive-boundary.py
python3 scripts/check-search-set-evidence.py
python3 scripts/check-backlog-archive-lifecycle.py
python3 -m unittest discover -s tests
python3 -m unittest discover -s adapters/claude/tests
python3 -m unittest discover -s adapters/codex/tests
```

For stable handoff, the preferred stable-handoff command is:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

During an in-progress maintenance diff, use:

```bash
python3 scripts/verify-release.py --skip-clean-worktree
```

The clean worktree stable handoff guard is:

```bash
python3 scripts/check-clean-worktree.py
```

It is not part of pre-commit because in-progress staged checks must be able to
run before the working tree is clean.

When editing governance fixtures or transcript artifacts, also run the Plan 06
developer helper. It remains outside the stable release gate until v2 archive
integration defines the release policy:

```bash
python3 scripts/update-governance-fixtures.py --check
```

For staged pre-commit evidence, use:

```bash
python3 scripts/check-v1-archive-boundary.py --staged
python3 scripts/check-search-set-evidence.py --staged
python3 scripts/check-backlog-archive-lifecycle.py --staged
```

For release-candidate search-set evidence, use:

```bash
python3 scripts/check-v1-archive-boundary.py --base-ref origin/main
python3 scripts/check-search-set-evidence.py --base-ref origin/main
```

The v1 archive boundary checker has three modes: worktree, `--staged`, and
`--base-ref REF`. Initial `archive/v1/` import must either match comparable v1
source files from the baseline ref or be hash-pinned in `archive/v1/IMPORT.md`
as a local pre-v2 worktree snapshot. After the archive exists in the baseline,
any `archive/v1/` change fails unless an explicit maintainer/reviewer waiver is
recorded. The bootstrap waiver CLI requires
`actor=<name> role=<maintainer|reviewer> date=<YYYY-MM-DD> reason=<why>
source=<file:path|git:ref>` with non-empty fields, a real ISO calendar date, and
a resolvable source file or git ref.

High-impact staged changes under `.githooks/`, `adapters/`, `core/`, `scripts/`,
`MAINTENANCE.md`, or `README.md` must include a changed review record with a
`Multi-review:` section or an explicit `Multi-review not required:` reason. The
maintenance review checker treats missing high-impact review disposition as a
blocking error, not an advisory signal.

Known bootstrap residual risks:

- `Multi-review not required:` is still a broad explicit disposition. During the
  transition, use it only for narrow low-risk work and do not use it to downgrade
  checker semantics, archive integration, release-gate wiring, public methodology
  claims, or other changes that this document says require multi-review. The v2
  packet checker should infer mandatory-review categories and require structured
  waiver provenance for any downgrade.
- `scripts/check-v1-archive-boundary.py` validates archive-waiver provenance when
  supplied on the CLI, but the waiver is not yet durably stored as packet
  evidence. The v2 packet model should store archive waiver actor, role, date,
  reason, and source reference in packet judgment/evidence before post-import
  archive changes can be accepted.

Search-set evidence compliance is shape-only: the checker verifies that a
required evidence record exists for the changed surface, not that the underlying
search cases all passed. In staged mode it reads the git index; in base-ref mode
it compares `REF...HEAD`. The checker parses `.harness/traces/search-set.md`
and requires recorded BEFORE/AFTER commands to match the changed paths, but it
does not prove that `python3 scripts/run-search-set.py` actually
ran. Active-case execution is enforced by the separate verification policy.
Optional strict mode is available for handoffs that need the evidence checker to
require an active run record:

```bash
python3 scripts/check-search-set-evidence.py --staged --require-active-run
```

For this repository's own harness-maintenance loop, use the
`.harness/traces/` tree as the active repository self-application trace root,
including `.harness/traces/search-set.md`. Active verify commands should cite
that trace root when repository maintenance changes need search-set evidence.
Historical `.claude/traces/` files are legacy
Claude-local context; do not write new repository maintenance traces there.

The Codex marketplace metadata readiness check passes when generated plugin
marketplace metadata is present and points at the expected local plugin bundle.
Codex local plugin activation smoke test passes when the isolated activation
fixture exposes the expected plugin skills.
The heavier Codex local plugin activation smoke is part of Standard verification
rather than pre-commit; it validates isolated CLI
  marketplace registration and enabled-plugin config shape, while not running Codex
  Desktop skill surfacing or plugin tool-event delivery.

During v1-to-v2 bootstrap, `scripts/check-v1-archive-boundary.py` is the
compatibility report for `archive/v1/`. It says the archive is frozen historical
evidence, not actively revalidated by legacy v1 gates. The initial import is
allowed while `archive/v1/` is absent from `HEAD`; later changes fail unless a
maintainer/reviewer waiver is supplied with a concrete reason.

After the v2 checker exists, release and pre-commit should prefer packet checks:

```bash
governance check --packet <packet>
governance finalize --packet <packet> --staged
governance finalize --packet <packet> --base-ref origin/main
```

Keep release commands argv-based and inspectable. Do not hide governance
decisions behind shell strings or prose-only records.

## Review During Transition

Use multi-review for v2 packet schema, checker semantics, archive integration,
release-gate wiring, evaluator-boundary changes, runtime evidence claims, and
public methodology claims.

During bootstrap, any critic score below 9 is blocking for stable handoff until
the finding is fixed or the work is explicitly not accepted. Score 9 requires a
why-not-10 reason and a residual-risk or follow-up disposition. These records
should move into packet fields once the v2 checker can capture them.

For governance work, include an anti-bloat critic before accepting a new guard,
schema field, or fixture kind. That critic should ask which false-green path is
closed, whether an existing guard can be generalized, whether any new user field
or hand-authored fixture burden is added, and what complexity is removed,
generated, or deferred. Fixture hash/ref drift should be handled by
`python3 scripts/update-governance-fixtures.py --check` rather than reviewer
memory.
