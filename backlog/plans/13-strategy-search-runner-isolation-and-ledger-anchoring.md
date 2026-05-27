# Plan 13: Strategy Search Runner Isolation And Ledger Anchoring

## Status

Complete for the repository-local default path.

- Slice 1 complete: plan and maintenance contract are documented.
- Slice 2 complete: evaluator execution uses a byte-copied disposable
  workspace, and `--keep-worktree` is a post-eval diagnostic copy rather than
  the evaluator's execution root.
- Slice 3 complete: `propose` and `eval` append repository-local Git anchor
  events automatically, while JSONL files remain run-store mirrors.
- Slice 4 complete: candidate records carry `candidate_digest`,
  `eval_anchor_ref`, and `eval_anchor_commit`; `validate-candidate` and
  `select` reject candidate records that are not bound to a reachable
  `candidate_evaluated` anchor event.
- Slice 5 complete: evaluator `stdout`/`stderr` are stored both as decoded
  diagnostic logs and exact raw byte sidecars, with both views bound in the
  candidate record, trace, digest, and validator.
- Slice 6 complete: proposal-created anchors are enforced during
  `eval --proposal`, raw stdout/stderr sidecars are sealed from public proposal
  context, and the remaining late absolute host-write case is documented as an
  OS-sandbox residual rather than a default repository-local guarantee.
- Final hardening complete: malformed, symbolic, dangling, and non-direct
  strategy-search anchor refs fail closed; anchor writes use direct-ref
  semantics and do not follow symbolic refs.

## Completion Target

Plan 13 is the closing slice for the practical repository-local Meta-Harness
methodology:

```text
strategy direction
  -> proposer or human candidate
  -> fixed evaluator in an isolated workspace
  -> anchored proposal/eval records
  -> selected diagnostic candidate
  -> normal v2 content commit and active pointer publication
```

After this plan, the repository can claim a complete practical method for
searching, evaluating, and adopting harness strategy changes. It must still not
claim paper-benchmark reproduction, hostile-operator tamper resistance, or that
strategy-search records are stable governance evidence by themselves.

## Motivation

Plan 12 provides a repository-local strategy-search MVP: directions, candidate
evaluation, proposer bundles, trace/search-set summaries, and selected
adoption artifacts. The MVP now detects ordinary source, `.git`, run-store,
workspace, evaluator-closure, and public-context drift. Four boundaries still
need a stronger design before strategy search can be described as methodology
complete:

- Detached descendants can outlive the evaluator process group, close stdio,
  sleep past the settle window, and mutate source or run-store paths after a
  candidate is recorded.
- Proposal ledgers are repository files. They detect duplicate or inconsistent
  entries, but they are not append-only anchors against a local rewrite of both
  `proposal.yml` and `proposals.jsonl`.
- Selected candidate records become selectable diagnostic output only when they
  are tied back to an eval-produced anchor event. A self-consistent handwritten
  `score.yml`/`trace.yml`/logs bundle should not become selectable, stable, or
  adoption evidence.
- Evaluator stdout/stderr logs are diagnostic text views. If they become raw
  stable evidence, the runner must preserve and hash exact output bytes beside
  the replacement-decoded text view.

## Scope

- Run evaluators in an isolation boundary that prevents ordinary writes to the
  source repository and run store by construction for the default non-hostile
  repository-local workflow, not by digest-and-restore.
- Remove source-root and run-store absolute paths from evaluator execution
  context. Directions that require a fixed evaluator to know those paths are
  out of scope for the simple path.
- Relative-path detached descendants can only mutate the disposable evaluation
  workspace after the runner has captured output. A fixed evaluator that already
  knows absolute source or run-store paths can still daemonize a late host
  write without an OS sandbox; that is a documented residual of the default
  repository-local path.
- Anchor proposal creation, ready sealing, and candidate evaluation records in
  a Git-backed event chain outside the mutable run directory. The run-local
  JSONL files remain readable mirrors, not the trust root.
- Require `select` to prove that the selected candidate was produced by an
  anchored `eval` event before it writes diagnostic selection summaries.
- Keep selected strategy-search artifacts diagnostic-only. Stable handoff is
  completed by applying the selected patch as a normal content commit and then
  using the existing v2 AcceptancePacket, review import, active pointer
  publication, and release verification path.

## Non-Goals

- No change to Plan 12 candidate scoring semantics.
- No claim that selected strategy-search artifacts replace v2
  AcceptancePackets, MultiReviewResult imports, or active pointer publication.
- No package-manager distribution requirement.
- No Docker, VM, signing-key, or network service requirement for the default
  path.
- No defense against a fully malicious local operator who can rewrite both the
  repository and `.git` history. The boundary is candidate/proposer/evaluator
  side effects and accidental or local-run-store tampering.
- No defense, in the default path, against a hostile same-user fixed evaluator
  that can exploit host filesystem races, runtime symlink or ancestor
  replacement, case-insensitive aliases, temp-sibling discovery, or detached
  descendants after the runner's settle window. Claiming that boundary requires
  a future OS-level sandbox.
- No guarantee that concurrent `eval --proposal` processes are transactionally
  isolated from one another beyond Git compare-and-swap failure. If concurrent
  writers race, the safe operator action is to rerun from a fresh proposal/run,
  not to rely on automatic conflict repair.

## Design Principles

- User input stays the same: `start`, `propose`, `eval`, `summarize`, and
  `select` manage isolation and anchors automatically.
- The evaluator is fixed and file-based. Inline evaluators, wrapper eval
  strings, and source-root-aware evaluators remain invalid rather than gaining
  more per-tool exceptions.
- The run store is useful diagnostic history. The anchor chain is the
  authenticity record. Stable governance acceptance remains the v2 archive
  publication path.
- Prefer fail-closed outcomes over silent convenience. Pre-evaluation anchor
  failures produce no selectable result. Post-run evaluator or workspace
  boundary failures record invalid diagnostic candidates when applicable.
- Do not add per-finding operator prompts or bespoke runtime exceptions to chase
  same-user sandbox gaps. If a finding requires defending against a hostile
  process with the same filesystem privileges as the runner, classify it as a
  sandbox/concurrency residual unless it breaks the default non-hostile
  workflow.

## Review Triage Boundary

The Plan 13 default path is complete when the existing `start`, `propose`,
`eval`, `summarize`, and `select` commands produce anchored diagnostic records
without requiring the operator to supply manual digests, refs, runtime paths, or
sandbox configuration. Reviews should use this boundary:

- In scope: false greens in the default non-hostile workflow; missing anchor or
  digest checks for runner-produced records; public proposal leaks of raw
  diagnostic run-store data; selected diagnostic summaries that claim stable
  governance evidence; crashes that prevent an invalid candidate record from
  being written for ordinary evaluator failures.
- Out of scope for Plan 13: hostile same-user runtime replacement through
  symlink directories or writable ancestors; transient hijack-and-restore of
  runtime/shim paths; temp-sibling source discovery by an evaluator that can
  inspect host paths; case-insensitive filesystem aliases used as an attack
  channel; concurrent proposal sealing races that require transactional
  multi-writer coordination; hostile local rewinds of otherwise valid Git
  anchor refs.
- Future work: an explicit Plan 14-style sandbox/concurrency layer may add a
  platform sandbox, container, dedicated unprivileged evaluator user, external
  append-only/high-water mark, or transactional proposal store. That future
  layer must not change the normal v2 stable handoff rule: strategy-search
  records remain diagnostic until adopted through a content commit and active
  pointer publication.

## Proposed Architecture

### Isolated Evaluation Workspace

`eval` creates a disposable evaluation root outside the source repository and
outside `.harness/search-runs/`.

Rules:

- Export only the direction base commit plus the allowed `search_surface` and
  evaluator closure into the evaluation root.
- Copy file bytes into the evaluation root. Do not symlink, hardlink, bind, or
  otherwise mount source-repository or run-store paths into the workspace.
- Run the evaluator with `cwd` inside the evaluation root and a scrubbed
  environment that omits source-root, run-store, caller `HOME`, caller temp-dir,
  and Git worktree variables. The runner supplies per-evaluation external
  `HOME` and `TMPDIR` values outside the source repository, archive tree, and
  run store, and fails closed if no such parent exists.
- If the runner adds a platform-stability runtime path binding, bind the binding
  text, target executable path/hash, and post-evaluation binding/target hashes
  into `score.yml`/`candidate_digest`; treat target mutation as an evaluator
  boundary failure. The target executable and containing directory must not be
  writable by the evaluator user.
- Store captured stdout/stderr in runner memory until the evaluator exits, then
  write diagnostic logs to the run store from the parent runner process.
- Treat writes to the disposable evaluation root after evaluator exit as
  irrelevant to source cleanliness; no source or run-store path is mounted as
  the evaluator's output target.
- Reject directions whose evaluator command, closure, or configured
  environment needs the source repository path or run-store path.

This intentionally avoids platform-specific sandbox setup while closing the
Plan 12 detached-descendant false-green class for the default repository-local
workflow. It does not claim hostile same-user containment.

### Git-Backed Event Anchor

Each run gets an append-only event chain under a repository-local Git ref:

```text
refs/meta-harness/strategy-search/<run-id>
```

Each event is a small Git commit whose tree contains a canonical event YAML:

```yaml
schema_version: strategy-search-anchor-event/v1
event_type: proposal_created | proposal_ready | candidate_evaluated
run_id: <run-id>
candidate_id: <candidate-id>
previous_anchor: <commit-or-null>
direction_digest: <sha256>
proposal_digest: <sha256-or-null>
patch_sha256: <sha256-or-null>
candidate_digest: <sha256-or-null>
created_at: <timestamp>
runner_version: strategy-search/v1
```

Rules:

- `propose` appends `proposal_created`.
- `eval --proposal` appends `proposal_ready` before evaluation only after all
  preflight conflicts are known to be clear.
- `eval` appends `candidate_evaluated` after writing `score.yml`, `trace.yml`,
  and diagnostic logs.
- `score.yml` records `eval_anchor_ref`, `eval_anchor_commit`, and
  `candidate_digest`.
- `select` requires a matching `candidate_evaluated` event reachable from the
  run ref. Rewriting only the run directory or local JSONL mirrors cannot make
  a handwritten candidate selectable.
- Anchor appends use compare-and-swap ref updates: the current ref must still
  equal `previous_anchor` when the new event is written. If another process
  advances the ref, the command fails closed. Ordinary non-mutating anchor
  appends can retry the same command; proposal-sealing races should recover with
  a fresh proposal or run rather than relying on transactional repair.
- The Git commit parent should be the same value as `previous_anchor` when one
  exists, so ordinary Git history and the event YAML describe the same chain.
- Anchor validation walks the chain from the current ref and verifies each
  event's `previous_anchor`, event type, run id, candidate id, and recorded
  digests. A ref that skips, forks, or rewrites expected history is not a valid
  anchor for `eval` or `select`.

The anchor is not a cryptographic anti-owner seal. It is the repository-local
truth source that separates runner-produced records from mutable run-store
sidecars without adding user prompts.

### Diagnostic Selection Boundary

`select` continues to write only diagnostic selection and summary YAML under
`.harness/search-runs/<run-id>/selections/`.

Rules:

- Selection summaries may name the selected candidate id, score, digest, and
  eval anchor commit.
- Selection summaries must not publish raw run-store paths, stdout/stderr log
  refs, trace refs, or patch refs as stable evidence.
- The selected patch becomes meaningful only when the operator applies it to
  the repository and creates a normal content commit.
- v2 stable handoff evidence must cite the resulting content commit, command
  artifacts, review imports, and pointer-bound archive bytes, not diagnostic
  run-store files.

### Candidate Digest

`candidate_digest` is computed before the `candidate_evaluated` event is
written, so it must not depend on the future eval anchor commit. It is a
canonical SHA-256 over runner-produced candidate payloads, excluding the digest
field itself and excluding `eval_anchor_commit`:

- `patch.diff`
- `score.yml` without `candidate_digest` and without `eval_anchor_commit`
- `trace.yml`
- decoded `stdout.log` / `stderr.log` hashes
- exact `stdout.raw` / `stderr.raw` byte hashes
- `run_id`, `candidate_id`, `direction_digest`, and the proposal or pre-eval
  anchor used as the event's `previous_anchor`

After the `candidate_evaluated` event is appended, `score.yml` may record
`eval_anchor_commit` as provenance, but validation recomputes
`candidate_digest` with that field removed. The digest does not include mutable
summaries, selection files, or public proposal bundles. This keeps `select`
simple: it checks one anchored digest instead of asking the operator to compare
many sidecar hashes.

### Raw Output Bytes

Evaluator output remains diagnostic. The runner stores both:

- exact stdout/stderr byte hashes for reproducibility; and
- UTF-8 replacement-decoded text views for inspection.

If a later plan wants evaluator logs to become stable raw claim evidence, it
must explicitly add a pointer-bound evidence wrapper. Plan 13 only preserves
the bytes needed to audit diagnostic candidate records.

## Implementation Slices

### Slice 1: Plan And Fixture Contract

- Update Plan 13 and maintenance docs with the architecture above.
- Add tests that lock the diagnostic-only boundary and anchor terminology.

### Slice 2: Evaluation Workspace Isolation

- Move evaluator execution into a disposable evaluation root.
- Remove source-root, run-store, caller `HOME`, and caller temp-dir path exposure from
  evaluator environment.
- Add regression probes for detached descendants attempting late writes to
  source, `.git`, and run-store paths.

### Slice 3: Anchor Event Chain

- Add anchor event writer/reader helpers.
- Append proposal and eval events automatically.
- Keep `proposals.jsonl` and `scores.jsonl` as mirrors.
- Use compare-and-swap Git ref updates and reject malformed, non-linear, or
  digest-mismatched anchor chains during `eval` and `select`.

### Slice 4: Select Requires Eval Provenance

- Add candidate digest and eval anchor fields to `score.yml`.
- Make `validate-candidate` and `select` verify anchor reachability and digest
  equality.
- Reject handwritten candidates that have no matching anchored eval event.
- Reject candidates whose anchored digest omits runner-produced payloads or
  includes mutable diagnostic summaries.

### Slice 5: Raw Byte Diagnostic Output

- Preserve exact stdout/stderr byte hashes and decoded text views.
- Write `stdout.raw` and `stderr.raw` beside decoded `stdout.log` and
  `stderr.log`; bind both forms in `score.yml`, `trace.yml`, and the anchored
  candidate digest.
- Keep raw bytes diagnostic-only unless a future v2 evidence wrapper is added.

### Slice 6: Review And Publication

- Run focused tests plus multi-review with isolation, ledger-authenticity,
  governance-boundary, and operator-simplicity critics.
- Publish via the normal v2 packet/pointer flow.

## Acceptance Criteria

- A relative-path detached descendant probe in the default non-hostile workflow
  cannot mutate source, `.git`, or the run store after `eval` has returned
  `pass`; hostile same-user host-path, runtime replacement, alias, and
  concurrency attacks are the documented OS-sandbox/concurrency residuals
  above.
- Eval workspace setup copies bytes and rejects symlink/hardlink paths that
  would let evaluator writes escape into source or run-store locations.
- Rewriting a ready proposal, its patch, and its local JSONL mirror cannot
  produce an accepted evaluation unless the Git-backed anchor chain also
  matches.
- A malformed, non-linear, or digest-mismatched anchor ref cannot be used to
  validate a proposal or selected candidate. A local operator who rewinds the
  entire Git ref to an earlier valid anchor is outside the default trust model
  unless a future external high-water mark is added.
- Hand-authoring a self-consistent candidate directory cannot pass `select`
  unless the candidate is present in the anchored eval chain.
- `select` verifies one canonical `candidate_digest` that binds patch, score,
  trace, output byte hashes, identity, and the pre-eval anchor without creating
  a circular dependency on the future eval anchor commit.
- The selected-artifact adoption path states that strategy-search files remain
  diagnostic, while the applied patch content commit and v2 archive publication
  are the stable evidence path.
- Existing Plan 12 commands remain the operator-facing workflow; no new manual
  digest, anchor, or ref input is required.
- Multi-review includes isolation, ledger-authenticity, governance-boundary,
  and operator-simplicity critics, and classifies findings using the Review
  Triage Boundary instead of treating every same-user sandbox variant as a Plan
  13 blocker.

## Validation Plan

Minimum focused tests:

```bash
python3 -m unittest tests.test_strategy_search
python3 scripts/strategy-search.py start --direction <fixture>
python3 scripts/strategy-search.py propose --run .harness/search-runs/<run-id> --candidate-id cand-001 --patch <patch>
python3 scripts/strategy-search.py eval --run .harness/search-runs/<run-id> --proposal .harness/search-runs/<run-id>/proposals/cand-001/proposal.yml
python3 scripts/strategy-search.py validate-candidate --direction <fixture> --candidate .harness/search-runs/<run-id>/candidates/cand-001/score.yml
python3 scripts/strategy-search.py select --run .harness/search-runs/<run-id> --candidate cand-001
```

Required regression probes:

- detached descendant attempts a late source, `.git`, and run-store write;
- symlink or hardlink evaluation workspace escape;
- rewritten `proposal.yml` plus rewritten JSONL mirror without matching anchor;
- non-linear or digest-mismatched anchor ref;
- handwritten candidate directory with matching local sidecars but no eval
  anchor;
- tampered `score.yml`, `trace.yml`, or output hash after anchored eval;
- selected diagnostic summary does not expose raw run-store refs or claim stable
  evidence status.
