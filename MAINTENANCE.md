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

The v2 maintenance target model is:

1. Humans provide small intent and judgment inputs.
2. The harness infers change class, impact, required evidence, required review,
   and eligibility from git state, path/content rules, traces, and artifacts.
3. The harness stores the result as an `AcceptancePacket`.
4. Stable handoff is accepted by the packet checker only from packet-backed
   base-ref verification; staged verification is preflight evidence, not active
   stable handoff. Release/pre-commit now route active archive packet
   publication through the packet-pointer gate.

The main v2 product requirement is simplicity: reduce the user interface and
the mental model, not the methodology evidence. If a maintenance change makes
operators hand-author more governance fields, remember more special cases, or
inspect more top-level concepts than `meta`, `input`, and `result`, treat that
as design debt unless the change removes a concrete failure mode that cannot be
handled by packet generation or checker inference.

Plan 10 completes the v2 core governance path, not every future operation around
it. Label follow-up work with the residual IDs in
`backlog/plans/11-v2-residual-hardening-and-operations.md`:

- `v2-residual-01 legacy-v1-boundary`
- `v2-residual-02 historical-fixture-boundary`
- `v2-residual-03 governance-packaging`
- `v2-residual-04 multi-publication-release`
- `v2-residual-05 checker-versioned-history`
- `v2-residual-06 worktree-mode-boundary`
- `v2-residual-07 packet-hash-placement`
- `v2-residual-08 release-command-replay-gate`
- `v2-residual-09 search-set-trace-fidelity`
- `v2-residual-10 review-template-completion-ergonomics`
- `v2-residual-11 publish-wrapper-ergonomics`
- `v2-residual-12 agent-in-loop-multi-review-eval`

Use those labels for hardening and operations work that follows the core v2
handoff path. Do not cite a residual label as completed active functionality
until a later packet closes that label with its own evidence and review.

Plan 11 closes the original residual labels for the v2 active model and keeps
new post-v2 hardening labels separate from v2 deployment readiness. The closure
does not claim optional future features: package-manager installation, chained
active publication releases, packet-internal hashes, or reviewer-wizard
completion remain post-v2 design choices until their own packets close them.
The repository-local `governance publish` wrapper and perspective-eval scorer
are now available as composition/evaluation aids, but they do not replace
reviewer judgment or a future AI judge.
For this repository, `governance` is the supported public command surface and
delegates to the repository-local checker; old packets with non-current checker
or inference versions remain historical compatibility evidence; `--worktree`
packets remain diagnostic/non-stable; and active integrity roots remain the
pointer `packet_sha256` plus review-import target bindings.

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
governance start --base-ref REF --intent "..." [--output <packet>]
governance finalize --packet <packet> --staged|--base-ref REF|--worktree
# For high-risk search-set trace reuse:
governance capture-search-set --phase before --packet <packet>
governance capture-search-set --phase after --packet <packet>
governance finalize --packet <packet> --base-ref REF \
  --search-set-before trace:.harness/traces/search-set.md#search-set-before-... \
  --search-set-after trace:.harness/traces/search-set.md#search-set-after-...
governance review-template --packet <packet> [--output <artifact>|--scratch-output <draft>]
governance import-review --packet <packet> --from <review-artifact-or-stdin> [--output <artifact>]
governance write-pointer --packet <packet>
governance publish --packet <packet> [--pointer <pointer>] [--message <commit message>]
governance check --packet <packet> --require-stable
governance status --base-ref REF
```

Lifecycle rules:

- `start` captures baseline state before edits.
- For active base-ref archive flows, omit `--output` to use the default
  `archive/v2/packets/<packet_id>.yml` path.
- `start` and `finalize` resolve `--base-ref` to a full commit SHA before
  writing packet boundary fields or evidence commands.
- `capture-search-set` appends a reusable before/after record under
  `.harness/traces/search-set.md#search-set-before-*` or
  `#search-set-after-*`; pass those refs to `finalize --search-set-before` and
  `--search-set-after` for full trace reuse.
- `finalize` updates evidence and computes `result.decision.stable_handoff_eligible`;
  `--base-ref` also generates commit-pinned changed-path source refs.
- `check` is read-only and does not mutate packet lifecycle state.
- `status` is read-only inventory: it summarizes active pointers, publication
  commits, stable-handoff readiness, and separates pending human decisions from
  generated artifact refreshes without replaying command evidence.
- `review-template` writes a target-bound draft `AcceptancePacketReviewImport`
  skeleton plus probe transcript templates; it is deliberately incomplete until
  reviewers replace the TODO fields, clear blocking findings, and record real
  probe evidence.
- `review-template --scratch-output` may write draft-only wrapper/probe
  templates outside `archive/v2/artifacts/` for reviewer workspace use. Scratch
  outputs are not durable import evidence and out-of-repo `file:` refs are not
  imported directly; use `--output` under `archive/v2/artifacts/` or
  `import-review --from - --output file:archive/v2/artifacts/<name>.yml` to
  materialize the completed review.
- `import-review` materializes a durable `AcceptancePacketReviewImport` artifact
  and records it in packet evidence when reviewer judgment is required.
- Strategy-search runs under `.harness/search-runs/` are diagnostic search
  history, not stable evidence. To adopt a selected candidate, run
  `python3 scripts/strategy-search.py select --run <run> --candidate <id>` to
  write a diagnostic selection summary under that run directory, then apply the
  patch in a content commit and use the normal AcceptancePacket, review import
  if required, active pointer publication, and release verification flow.
  Strategy-search selection files are not archive/v2 evidence and cannot make
  stable handoff claims by themselves.
- `publish` is a composition wrapper for already-stable archive packets. It
  refuses staged or non-archive dirty content, requires current `HEAD` to equal
  packet `accepted_head_commit`, runs `write-pointer`, stages only pointer-bound
  `archive/v2` files, validates the staged active gate, creates the archive-only
  publication commit, and reruns the base-ref active gate for the published
  pointer.
- Stable handoff uses `--base-ref`; `--staged` is preflight-only.
- `--worktree` is always non-stable exploratory/in-progress evidence.
- Harness-affecting finalization fails closed without a start packet unless an
  exact skipped-before reason and maintainer/reviewer disposition are recorded.

Historical v2 implementation work before `governance start` and stable packet
checks existed used a bootstrap transition note. New active v2 implementation
work should use the packet lifecycle above; use bootstrap notes only when
describing archived transition evidence. A bootstrap note includes:

- intent
- changed files
- whether the work would be harness-affecting under the v2 rule table
- required evidence that could not yet be captured as a packet
- exact skipped-before reason when no start packet exists
- reviewer or maintainer disposition for any waiver, downgrade, skipped required
  evidence, or residual risk
- explicit statement that the record is not a finalized v2 packet

This bootstrap note is temporary compatibility evidence, not the current v2
target.

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

Use a distinct v2 packet namespace. Routine active base-ref starts default to
`archive/v2/packets/` and reject non-archive output paths, unless an
implementation review chooses a stronger location such as
`.harness/governance/packets/`.

Do not reuse v1 backlog archive semantics for v2 packets. A completed active
pointer is a generated artifact outside the public packet shape. The normal
publication path is:

```bash
python3 scripts/check-governance-acceptance.py write-pointer --packet archive/v2/packets/<packet_id>.yml
python3 scripts/check-governance-acceptance.py check-pointer --pointer archive/v2/pointers/<packet_id>.yml --replay-command-evidence
```

Release verification must replay archived command evidence through the active
base-ref pointer gate. Staged pre-commit, `finalize`, and stable `check` keep
command/probe execution out of their routine validation path; direct pointer
audit replay remains available for debugging:

```bash
python3 scripts/check-governance-acceptance.py check-pointer --pointer archive/v2/pointers/<packet_id>.yml --replay-command-evidence
```

The active pointer validates:

- packet file exists
- packet hash matches archived packet bytes
- packet lifecycle is finalized
- `result.decision.accepted: yes`
- required source refs resolve
- checker version, inference rule version, baseline/comparison refs, packet-bound
  accepted HEAD commit, stable target, and decision status match the archived
  packet
- `write-pointer` records a reproducible synthetic `archive_commit` hash over
  the packet, command artifact, review import artifact, and linked probe
  transcript bytes it hashed; `check-pointer` recomputes that hash and verifies
  committed publication bytes when a pointer has been published. The synthetic
  commit object is not required to remain reachable in every clone.
- archived active base-ref boundary refs use full commit SHAs; mutable refs such
  as `HEAD` cannot certify archived stable boundaries. Routine start/finalize
  normalizes user-provided refs such as `HEAD~1` or `origin/main` to the resolved
  commit SHA.
- archived review-import artifacts and linked probe transcripts are bound by
  SHA-256, target digest, result digest, packet ref, and packet SHA-256
- archived active source refs use commit-pinned `git:<full-commit-sha>:<path>`
  refs for changed-path evidence; bare paths, mutable `git:` refs, opaque blobs,
  and protected directory-root refs cannot certify archived stable source
  evidence. Routine base-ref finalization generates these changed-path refs, so
  operators do not hand-author them.
- routine base-ref finalization into `archive/v2/packets/` also materializes the
  durable command artifact and marks the packet stable when the generated
  evidence validates, so `write-pointer` can publish without manual packet or
  artifact edits
- `write-pointer` materializes pointer-bound replay metadata and recorded
  exit/stdout/stderr hashes for matched `# Command Evidence` sections rather
  than accepting pre-authored replay/provenance fields; `--overwrite` regenerates
  existing pointer-bound replay metadata for retry/output recovery; stable packet
  preflight runs before artifact mutation, and pointer/materialization failures
  roll artifact bytes back so retries are not poisoned
- archived command artifacts are bound by SHA-256 and include pointer-bound
  replay metadata for the matched `# Command Evidence` section
- release active pointer validation and explicit pointer replay rerun archived
  command evidence and compare recorded exit/stdout/stderr hashes without
  making stable `check`, `finalize`, or staged pre-commit execute
  artifact-supplied commands

## Active Governance Boundaries

During the v2 transition, keep the active operator model to these boundaries:

- `check` is read-only. Stable handoff validation may read packets, source
  refs, transcripts, and command artifacts, but it must not execute
  artifact-supplied probe commands.
- `replay` is scoped. Release active pointer validation replays archived
  command evidence because it is the final publication gate. Probe commands may
  run only through an explicit replay path such as
  `python3 scripts/check-multi-review-result.py --result <path>
  --replay-probe-commands`; probe replay is not part of stable packet `check`.
- `stable` validates durable structural evidence. A stable packet proves
  closure through recomputed required evidence/review, structured imports,
  source refs, transcripts, and reopenable packet-bound command artifacts, not
  by trusting reported PASS prose. Plan 07 binds command artifact bytes with
  pointer-bound replay metadata and explicit replay, but it is not an external
  runner identity or signature attestation.
- historical `archive/v2/` bytes are committed repository bytes, not a future
  whitelist. Routine `finalize`, stable `check`, release, and pre-commit flows
  do not execute or trust prior pointer command results to close a later packet;
  unexpected new `archive/v2/` bytes still require the current active pointer
  publication path.
- generated artifact refs use explicit schemes. Stable artifact and probe
  evidence refs use `file:`, trace refs use `trace:`, and active base-ref
  stable changed-path source refs use commit-pinned `git:<full-commit-sha>:<path>`
  refs: `HEAD` for additions/modifications and the comparison side for deleted
  paths. Base-ref finalization generates those changed-path refs automatically;
  broader source refs are allowed only for non-active fixtures or later archive
  policy decisions.

## Verification During Transition

For historical transition work before the v2 checker existed, run the narrow
compatibility checks that still cover the changed surface and record known gaps
honestly. For active v2 work, prefer packet lifecycle checks; passing legacy v1
checkers means only that old record-shape validators did not find an error in
their configured paths.

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

For release-like local verification, use:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

With `--base-ref`, `verify-release.py` also runs the active packet pointer gate
and discovers the pointer from `REF...HEAD`. A packet-backed stable handoff for
a clean release candidate therefore requires a published pointer under
`archive/v2/pointers/` whose pointed packet is finalized, base-ref mode, and
stable-handoff eligible. The release diff should publish one active pointer.
Use `--pointer <archive/v2/pointers/...>` only together with `--base-ref` when
explicitly selecting that single publication; split multiple pointer
publications instead of hiding them behind one release command.

`v2-residual-04 multi-publication-release` keeps chained active publications out
of the routine release model for now. A future chained-pointer release gate must
validate each publication boundary in order, reject archive rewrites even when
later reverted, allow no-ff merge commits only when they introduce no merge-side
archive content, and avoid turning `governance status` into a trust ledger.

During an in-progress maintenance diff, use:

```bash
# PRE-FLIGHT ONLY: not stable release evidence.
python3 scripts/verify-release.py --skip-clean-worktree
```

The clean worktree stable handoff guard is:

```bash
python3 scripts/check-clean-worktree.py
```

It is not part of pre-commit because in-progress staged checks must be able to
run before the working tree is clean.

When editing governance fixtures or transcript artifacts, also run the Plan 06
developer helper. Plan 07 keeps this helper outside the stable release gate:
archive pointer validation binds archived packet, command artifact, review
import artifact, and probe transcript bytes, but fixture regeneration remains a
developer maintenance action rather than stable handoff evidence.

```bash
python3 scripts/update-governance-fixtures.py --check
```

For staged pre-commit evidence, use the hook wrapper:

```bash
sh .githooks/pre-commit
```

The hook runs the staged archive boundary, search-set evidence, backlog
lifecycle, and active packet pointer gates. Use the lower-level commands only
when debugging a failing hook result:

```bash
python3 scripts/check-v1-archive-boundary.py --staged
python3 scripts/check-search-set-evidence.py --staged
python3 scripts/check-backlog-archive-lifecycle.py --staged
python3 scripts/check-active-packet-gate.py --staged
```

The staged active packet gate is preflight only: it passes ordinary staged
non-archive changes, but staged `archive/v2/` packet/artifact/pointer changes
must include exactly one active pointer candidate or an explicit `--pointer`.
Stage active pointer publication separately from work/content changes: commit
the accepted work first, then stage only the generated `archive/v2/` packet,
artifact, and pointer bytes for the publication preflight. In staged mode the
gate validates the Git index snapshot, not worktree bytes, so unrelated
unstaged or untracked files do not affect the pre-commit result and untracked
archive artifacts cannot satisfy a staged publication.

For release-candidate verification, use the release wrapper:

```bash
python3 scripts/verify-release.py --base-ref origin/main
```

The release wrapper runs the base-ref v1 archive boundary, search-set evidence,
and active packet pointer gates. Use the lower-level commands only when
debugging a failing release result:

```bash
python3 scripts/check-v1-archive-boundary.py --base-ref origin/main
python3 scripts/check-search-set-evidence.py --base-ref origin/main
python3 scripts/check-active-packet-gate.py --base-ref origin/main
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
High-risk packet flows can run `governance capture-search-set --phase before`
and `--phase after` to append reusable `Search-set Evidence Captures` anchors,
then pass those refs to `governance finalize --search-set-before/after`.
Targeted skips remain valid human dispositions, but captured before/after refs
are the higher-fidelity reuse path.
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

Release and pre-commit packet integration normally runs through
`python3 scripts/verify-release.py --base-ref origin/main` and
`.githooks/pre-commit`. Raw packet-gate triage commands are:

```bash
python3 scripts/check-active-packet-gate.py --base-ref origin/main
python3 scripts/check-active-packet-gate.py --staged
python3 scripts/check-governance-acceptance.py check --packet <packet> --require-stable
python3 scripts/check-governance-acceptance.py finalize --packet <packet> --staged
python3 scripts/check-governance-acceptance.py finalize --packet <packet> --base-ref origin/main
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
