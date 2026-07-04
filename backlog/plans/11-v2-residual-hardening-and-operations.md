# Plan 11: v2 Residual Hardening and Operations

## Purpose

Plan 10 completes the v2 core governance path: packet lifecycle, multi-review
import, active pointer publication, status inventory, and release/pre-commit
verification. Plan 11 labels the remaining work that is deliberately outside
that core path so it can be handled without overstating v2 completion.

These items are follow-up hardening and operations work. They are not blockers
for the Plan 10 active pointer flow unless an item is explicitly promoted by a
review finding.

## Completion Boundary

Completed v2 core:

- `governance start/finalize/import-review/write-pointer/check/status`
- target-bound `AcceptancePacketReviewImport` materialization
- active `archive/v2` pointer publication
- release/pre-commit active packet gate integration
- routine single-publication release shape: content commits first, then one
  archive publication commit

Not claimed by v2 core:

- complete removal of legacy v1 compatibility surfaces
- treating historical fixtures as active governance records
- package-manager installation of the public `governance` command
- chained multi-publication release validation
- timeless re-evaluation of old packets under newer checker rules

## Residual Labels

### v2-residual-01 legacy-v1-boundary

Boundary: `archive/v1` remains frozen historical evidence. Legacy checkers may
guard immutability or compatibility, but they must not imply active v2 coverage
for old v1 records.

Acceptance criteria:

- Docs say v1 records are archived compatibility evidence, not active v2
  handoff records.
- Tests lock that `archive/v1` changes remain either blocked or explicitly
  waived with provenance.
- No release or status path treats v1 records as current packet evidence.

### v2-residual-02 historical-fixture-boundary

Boundary: fixtures, benchmark transcripts, and historical review artifacts are
checker examples or archived traces unless they are explicitly published through
active `archive/v2` pointers.

Acceptance criteria:

- Fixture docs distinguish positive/negative controls from active publication
  evidence.
- Generated fixture materialization remains test-only.
- Release/status inventory reports active pointers only from `archive/v2`
  publication records, not fixture-like files.

### v2-residual-03 governance-packaging

Boundary: `governance` is the public command name, but the current implementation
is a repository-local wrapper.

Acceptance criteria:

- Roadmap treats the remaining decision as installation/exposure mechanics, not
  command naming.
- CI may continue to call repository-local scripts while docs prefer
  `governance` for operator flow.
- Any future package entry point delegates to the same checker logic.

### v2-residual-04 multi-publication-release

Boundary: the accepted routine release model is one active pointer publication
per base-ref release range. Chained active pointer publications are a future
explicit model, not an implicit release-gate behavior.

Acceptance criteria:

- Docs tell operators to finish content commits before the archive publication
  commit when a single release pointer is desired.
- Release gate rejects hidden archive rewrites and does not collapse multiple
  archive publications into a fake first publication.
- Any future chained-pointer support validates each publication boundary rather
  than trusting net final tree state.

### v2-residual-05 checker-versioned-history

Boundary: old packets may have been authored under earlier checker and inference
rules. Current validation must not silently reinterpret them as stronger
evidence than their rule version supports.

Acceptance criteria:

- Packet evidence records enough checker/inference identity to explain the
  validation boundary.
- Historical audit messages distinguish structural byte integrity from current
  policy acceptance.
- Future re-evaluation policy is explicit before old packets are used as
  current governance proof.

### v2-residual-06 worktree-mode-boundary

Boundary: `--worktree` is always non-stable exploratory/in-progress evidence.
Stable handoff uses `--base-ref`; staged mode is preflight.

Acceptance criteria:

- Docs and tests keep worktree packets from satisfying active stable handoff.
- Any worktree status output names pending human/operator actions rather than
  publishing readiness.
- No active pointer path accepts worktree-only refs as publication evidence.

### v2-residual-07 packet-hash-placement

Boundary: active pointer bytes are the current packet-bound integrity root. A
packet-internal hash remains an open design choice because it risks
self-reference and migration churn.

Acceptance criteria:

- Current active validation keeps packet digests in pointers and review-import
  target bindings.
- Roadmap names packet-internal hash placement as a design decision, not a
  missing Plan 10 implementation.
- If packet-internal hashes are introduced, canonical serialization excludes the
  hash field or otherwise avoids self-reference.

### v2-residual-08 release-command-replay-gate

Boundary: the release/base-ref active packet gate is the final publication
acceptance gate, so it must replay pointer-bound command evidence. Staged
preflight and stable packet `check` remain non-executing structural gates.

Acceptance criteria:

- Release/base-ref active packet validation calls pointer replay for archived
  command evidence.
- A forged passing command artifact whose command now fails is rejected by the
  release gate, not only by manual `check-pointer --replay-command-evidence`.
- Staged preflight keeps validating staged archive bytes without executing
  artifact-supplied commands.

### v2-residual-09 search-set-trace-fidelity

Boundary: targeted skips for `search_set_before` and `search_set_after` are
valid human-disposition records, but they are lower-fidelity than reusable trace
refs for high-risk packets.

Acceptance criteria:

- High-risk packet tooling can capture or prompt for distinct before/after
  `backlog/repository-search-set.md` refs.
- Targeted skips remain explicit human/operator decisions with provenance.
- Review scoring treats targeted skips as acceptable but not equivalent to full
  trace reuse.

Implementation note: `governance capture-search-set --phase before|after`
records reusable `backlog/repository-search-set.md#search-set-before-*` and
`#search-set-after-*` anchors, and `governance finalize` accepts
`--search-set-before/after` to bind those refs instead of generating targeted
skips.

### v2-residual-10 review-template-completion-ergonomics

Boundary: `review-template` owns the target-bound wrapper/probe skeleton, but
reviewers still have to complete substantive probe, lineage, and critic fields.
Future helpers may reduce YAML editing without auto-certifying PASS.

Acceptance criteria:

- Any helper keeps reviewer judgment explicit and refuses to generate a PASS
  from placeholders alone.
- Generated drafts distinguish prompts from certifying evidence.
- Review-import validation continues to reject incomplete templates.

### v2-residual-11 publish-wrapper-ergonomics

Boundary: v2 uses safe primitives today. A future one-command wrapper can
compose those primitives, but must preserve content commits first and one
archive-only publication commit last.

Acceptance criteria:

- The wrapper does not merge content and archive publication bytes into the same
  commit.
- It fails closed when review import, command replay, pointer audit, or active
  gate validation fails.
- It remains a composition layer over the existing checker semantics rather
  than a second policy implementation.

### v2-residual-12 agent-in-loop-multi-review-eval

Boundary: current multi-review v2 validation is deterministic artifact
validation. It structurally blocks governance PASS false greens in typed
fixtures, but it does not yet measure whether independent agents discover
issues from `public_input`, whether critic frames are semantically diverse, or
whether evidence relevance passes a semantic scorer.

Acceptance criteria:

- A future runner hides sealed oracles and asks an agent to produce
  `MultiReviewResult` artifacts from public inputs.
- Semantic scoring evaluates critic diversity, issue discovery, and evidence
  relevance separately from structural schema validity.
- Deterministic fixture checks remain the stable regression layer and are not
  overclaimed as agent-in-the-loop benchmark evidence.

## Processing Order

1. Close `v2-residual-01` and `v2-residual-02` together because they both guard
   historical material from being mistaken for active v2 evidence.
2. Design `v2-residual-04` before changing release behavior, because it can
   widen the active archive trust boundary.
3. Resolve `v2-residual-03` after the repo-local wrapper remains stable across
   one or more release cycles.
4. Handle `v2-residual-05`, `v2-residual-06`, and `v2-residual-07` as policy
   hardening unless a critic promotes one to release-blocking.
5. Close `v2-residual-08` before relying on release verification as the only
   command-evidence replay surface.
6. Handle `v2-residual-09`, `v2-residual-10`, and `v2-residual-11` as
   post-v2 simplicity/fidelity improvements unless a critic promotes one to
   release-blocking.
7. Handle `v2-residual-12` as evaluation-methodology work after the structural
   validator fixture layer remains stable.

## Implementation Iteration 1

Closed in this iteration:

- `v2-residual-01 legacy-v1-boundary`: docs identify v1 as frozen
  compatibility evidence, and `tests/test_v1_archive_boundary.py` locks
  immutability plus waiver provenance behavior.
- `v2-residual-02 historical-fixture-boundary`: Plan 02, fixture README, and
  Plan 09 label fixtures and historical bytes as controls/traces rather than
  active closure inputs; `tests/test_maintenance_policy_boundaries.py` locks the
  wording.

Guardrails added in this iteration:

- Import-review operator flow remains archive-generating and stdin-capable:
  `tests/test_governance_review_import.py` covers `--from -` with both explicit
  and default `archive/v2/artifacts/` output.
- Import-review probe binding is materialized by the command rather than
  requiring reviewers to predict the final packet SHA.
- Residual labels remain inventory metadata; the multi-review benchmark
  regression proves label-like prose cannot override typed VETO facts.

Still pending:

- `v2-residual-04 multi-publication-release` design before any release-gate
  behavior change.
- `v2-residual-03 governance-packaging` after the repository-local wrapper has
  survived release use.
- `v2-residual-05`, `v2-residual-06`, and `v2-residual-07` as policy hardening
  unless a later critic promotes one to blocking.

## Implementation Iteration 2

Designed in this iteration:

- `v2-residual-04 multi-publication-release`: keep the current release gate on
  the single-publication model while documenting the required future chained
  publication invariants.

Current policy:

- One base-ref release range should contain content commits first, then exactly
  one active `archive/v2` publication commit.
- `verify-release.py --base-ref <ref> --pointer <pointer>` selects one pointer
  for that release range; it must not silently merge multiple active pointer
  publications into one apparent publication.
- Multiple active pointer publications in one release range should be split
  into separate release segments unless a later chained-pointer design is
  implemented and reviewed.

Future chained-pointer design requirements:

- Validate each active publication commit in topological order instead of
  trusting the final tree or a net diff.
- Preserve each pointer's own `comparison_ref`, `accepted_head_commit`,
  publication commit, packet bytes, artifact bytes, review import bytes, and
  probe transcript bytes.
- Permit no-ff merge commits that introduce no archive-side content, but reject
  merge-side archive content that was not published by a valid pointer.
- Allow later unrelated valid publications without causing old pointer audits
  to fail.
- Reject archive rewrites, deletes, relabels, or drift even when a later commit
  reverts the final bytes back to the original tree.
- Reject a synthetic release snapshot that collapses several archive-only
  commits into a fake first publication.

False-green probes a future implementation must cover:

- valid pointer publication, archive rewrite, then byte-for-byte revert;
- valid pointer publication followed by an unrelated valid pointer publication;
- no-ff merge checkout with no merge-side archive content;
- no-ff merge checkout that introduces archive content from the merge side;
- two pointers whose publication order is reversed or whose `comparison_ref`
  does not match the previous content boundary.

Not implemented in this iteration:

- The release gate still does not accept chained active publications in one
  release range as a completed model.
- `governance status` remains inventory, not a chain trust ledger.
- Any code change that attempts chained support must add behavioral tests for
  all false-green probes above before changing release semantics.

## Implementation Iteration 3

Closed in this iteration:

- `v2-residual-03 governance-packaging`: `governance` is the public operator
  command for v2. The current repository-local executable delegates to the same
  checker logic used by CI and release verification; package-manager
  installation is future distribution work, not an unfinished v2 semantics
  item.
- `v2-residual-05 checker-versioned-history`: active pointers record
  `checker_version` and `inference_rule_version`, and current validation treats
  mismatches as unsupported historical boundaries rather than silently
  reinterpreting old packets as current-proof evidence.
- `v2-residual-06 worktree-mode-boundary`: `--worktree` remains
  exploratory/non-stable; it can produce a valid packet for local diagnosis,
  but it cannot satisfy `--require-stable` or active pointer publication.
- `v2-residual-07 packet-hash-placement`: v2 keeps packet digest roots in active
  pointers and review-import target bindings. A packet-internal hash is not part
  of the v2 active model because it would introduce self-reference and migration
  churn without closing the active publication boundary.

Final v2 completion policy:

- The v2 active handoff path is complete for single-publication base-ref
  releases: `governance start`, `finalize`, `review-template`,
  `import-review`, `write-pointer`, `check`, `status`, release verification,
  and pre-commit active packet gating.
- `review-template` owns the target-bound review-import skeleton shape and probe
  transcript paths without auto-certifying PASS; reviewers still have to replace
  TODO fields, clear blocking findings, and record substantive probe evidence.
- Repository-local `governance` is the supported command surface for this repo;
  installers or package entry points may be added later only if they delegate to
  the same checker semantics.
- Historical packets whose checker or inference rule version does not match the
  current validator are compatibility/history evidence, not current stable
  proof.
- Worktree packets are local diagnostic records. Stable handoff remains
  base-ref packet-backed, and staged mode remains preflight.
- Packet bytes are bound externally by pointer `packet_sha256` and
  review-import `review_target_digest`; no packet-internal digest is required
  for v2 completion.

Future work after v2 completion:

- Optional package-manager distribution for `governance`.
- Optional chained-pointer release support, subject to the false-green probes
  listed in Implementation Iteration 2.
- Optional packet-internal hash design, only if canonical serialization avoids
  self-reference and migration ambiguity.
- Optional review completion helper that reduces manual YAML editing without
  certifying placeholders.
- Optional `governance publish` wrapper that composes safe primitives without
  weakening content-first, archive-last publication.
- Optional agent-in-the-loop multi-review runner plus semantic scorer for
  critic diversity, issue discovery, and evidence relevance.

## Implementation Iteration 4

Closed in this iteration:

- `v2-residual-08 release-command-replay-gate`: release/base-ref active packet
  validation now calls pointer command replay, so forged PASS metadata cannot
  satisfy the release gate when the underlying archived command fails.

Still pending:

- `v2-residual-10 review-template-completion-ergonomics`: review-template
  skeletons reduce shape burden, but future helpers can further reduce manual
  probe/lineage field editing without auto-certifying PASS.
- `v2-residual-11 publish-wrapper-ergonomics`: a future wrapper can compose the
  current primitives while preserving the two-commit content/archive boundary.
- `v2-residual-12 agent-in-loop-multi-review-eval`: deterministic fixtures
  remain structural validator checks; agent discovery and semantic relevance
  scoring are explicitly later evaluation work.

## Implementation Iteration 5

Closed in this iteration:

- `v2-residual-10 review-template-completion-ergonomics`: `review-template`
  now supports `--scratch-output` for draft-only wrapper/probe templates outside
  `archive/v2/artifacts/`, including `/private/tmp/...` or repo-local
  `.claude/...` workspace paths. Durable import evidence remains archive-bound
  through `--output` or `import-review --from -`.

Still pending:

- `v2-residual-09 search-set-trace-fidelity`
- `v2-residual-11 publish-wrapper-ergonomics`
- `v2-residual-12 agent-in-loop-multi-review-eval`

## Implementation Iteration 6

Closed in this iteration:

- Draft `MultiReviewResult` templates now use `reported_final_verdict:
  INCOMPLETE`, so generated review skeletons no longer look like human-facing
  PASS records before reviewers complete the fields and probes.
- The multi-review validator treats draft lifecycle results as draft verdicts,
  and the lifecycle fixture now locks draft plus reported PASS as an explicit
  validator error.
- `review-template --scratch-output` messaging now states that scratch wrapper
  and probe refs are draft-only workspace files and must be materialized through
  archive-bound output before import.

Still pending:

- `v2-residual-09 search-set-trace-fidelity`
- `v2-residual-11 publish-wrapper-ergonomics`
- `v2-residual-12 agent-in-loop-multi-review-eval`

Search-set verification:

- SKIPPED: This iteration is validator/template wording polish; focused
  unittest, fixture replay, maintenance review, py_compile, and whitespace
  checks cover the changed boundary while `v2-residual-09` keeps full
  before/after trace capture as follow-up work.

Multi-review:

- Verdict: PASS for draft-template semantics and scratch-output guidance
  polish.
- Template semantics critic: score 9 PASS; Blocking findings: none after draft
  templates stopped reporting PASS and validator coverage locked the draft
  verdict boundary; residual risk accepted for future reviewer-wizard polish.
- Scratch workflow critic: score 9 PASS; Blocking findings: none after
  operator-facing output and maintenance guidance identified scratch files as
  draft-only, non-import evidence; residual risk accepted for future
  import-remapping helpers.
- Follow-up/residual risk: the future reviewer-wizard and publish-wrapper
  ergonomics remain labeled residuals rather than active v2 requirements.
- Score handling: score 9; not 10 because this iteration improves draft
  clarity without implementing a one-command reviewer or publisher workflow.
- Rerun status: focused unittest, fixture replay, maintenance review, py_compile,
  and whitespace checks rerun after the wording and validator changes.
- Final acceptance: accepted as v2 polish that reduces false PASS appearance
  without weakening durable archive import rules.

## Implementation Iteration 7

Closed in this iteration:

- `v2-residual-09 search-set-trace-fidelity`: `governance
  capture-search-set --phase before|after` now appends reusable
  `backlog/repository-search-set.md#search-set-before-*` and
  `#search-set-after-*` anchors, and `governance finalize` can bind those refs
  through `--search-set-before/after` instead of emitting targeted skips.

Still pending:

- `v2-residual-11 publish-wrapper-ergonomics`
- `v2-residual-12 agent-in-loop-multi-review-eval`

Search-set verification:

- BEFORE: SKIPPED no pre-change `capture-search-set --phase before` trace was
  recorded before this implementation began; this iteration closes the tooling
  gap for future high-risk packets.
- AFTER: PASS `python3 scripts/run-search-set.py` after the capture/finalize
  binding change.

Multi-review:

- Verdict: PASS for search-set trace fidelity closure.
- Trace fidelity critic: score 9 PASS; Blocking findings: none after capture
  anchors became first-class packet refs and targeted skips remained explicit
  fallback records. Follow-up/residual risk: accepted; semantic scoring stays
  tracked separately under `v2-residual-12`.
- Evidence honesty critic: score 9 PASS; Blocking findings: none; capture refs
  bind command, status, exit code, stream hashes, head ref, and packet ref
  without treating targeted skips as equivalent to full trace reuse.
  Follow-up/residual risk: accepted; publication wrapping stays tracked under
  `v2-residual-11`.
- Follow-up/residual risk: semantic agent-in-loop review scoring remains
  `v2-residual-12`, and one-command publication remains `v2-residual-11`.
- Score handling: score 9; not 10 because this closes trace reuse ergonomics
  while keeping broader semantic scoring and publish wrapping out of scope.
- Rerun status: focused unittest, Active search-set, maintenance review,
  py_compile, search-set evidence, and whitespace checks rerun after the
  capture/finalize binding changes.
- Final acceptance: accepted as v2-residual-09 closure for repository-local
  v2.

## Implementation Iteration 8

Closed in this iteration:

- `v2-residual-09 search-set-trace-fidelity` hardening: capture-shaped
  `backlog/repository-search-set.md#search-set-before-*` and
  `#search-set-after-*` refs now require a capture record with phase, PASS
  status, zero exit code, command, stdout/stderr SHA-256 values, head ref, and
  capture date. `governance finalize` rejects incomplete or phase-mismatched
  capture refs instead of accepting a hand-authored heading that only looks like
  a reusable trace.

Still pending:

- `v2-residual-11 publish-wrapper-ergonomics`
- `v2-residual-12 agent-in-loop-multi-review-eval`

Search-set verification:

- BEFORE: SKIPPED no pre-change `capture-search-set --phase before` trace was
  recorded before this validator hardening began; the gap was discovered during
  the local multi-review pass after Iteration 7.
- AFTER: PASS `python3 scripts/run-search-set.py` after the capture-record
  validator and negative tests were added.

Multi-review:

- Verdict: PASS for capture-ref hardening.
- Trace fidelity critic: score 9 PASS; Blocking findings: none after
  capture-shaped refs must carry the generated record fields and phase must
  match the `search_set_before`/`search_set_after` slot. Follow-up/residual
  risk: accepted; this still validates structured capture records, not semantic
  agent-in-loop issue discovery.
- Evidence honesty critic: score 9 PASS; Blocking findings: none after
  incomplete hand-authored capture headings and phase-swapped refs became
  explicit validator failures. Follow-up/residual risk: accepted; future
  semantic scoring remains `v2-residual-12`.
- Anti-bloat critic: score 9 PASS; Blocking findings: none; the validator
  generalizes the existing capture record shape and adds two negative tests
  without adding new packet fields. Follow-up/residual risk: accepted; one
  helper parses markdown sections for capture validation.
- Follow-up/residual risk: one-command publication remains
  `v2-residual-11`, and semantic multi-review scoring remains
  `v2-residual-12`.
- Score handling: score 9; not 10 because this is a structural fidelity lock,
  not a semantic review scorer or publisher wrapper.
- Rerun status: py_compile, focused capture/finalize unittest, governance CLI
  evidence-ref and maintenance-policy tests, Active search-set, and whitespace
  checks rerun after the validator change.
- Final acceptance: accepted as v2-residual-09 hardening for repository-local
  v2.

## Implementation Iteration 9

Closed in this iteration:

- `v2-residual-11 publish-wrapper-ergonomics`: `governance publish --packet
  <packet>` now composes the existing safe primitives for already-stable
  packets. It requires current `HEAD` to equal packet `accepted_head_commit`,
  refuses preexisting staged changes or non-archive dirty content, runs
  `write-pointer`, stages only pointer-bound `archive/v2` files, validates the
  staged active packet gate, creates the archive-only publication commit, and
  reruns the base-ref active gate for the published pointer.
- `v2-residual-12 agent-in-loop-multi-review-eval`: the perspective-eval
  contract now has a deterministic scorer that emits public-only agent prompts
  and scores candidate outputs against sealed rubric criteria for critic
  diversity, issue/disagreement preservation, and evidence relevance.

Still pending:

- Package-manager installation for the public `governance` command remains a
  distribution choice.
- A future AI judge may replace or augment the deterministic perspective scorer,
  but the current scorer is the repository-local calibration layer.

Search-set verification:

- BEFORE: SKIPPED this iteration started from the completed residual-09
  publication; no new before-capture was recorded for this follow-up wrapper and
  benchmark-scorer implementation.
- AFTER: PASS `python3 scripts/run-search-set.py` after the publish wrapper and
  perspective scorer changes.

Multi-review:

- Verdict: PASS for residual-11/12 closure.
- Publish-wrapper critic: score 9 PASS; Blocking findings: none after the
  wrapper remained a composition layer over `write-pointer`, staged active gate,
  git commit, and base-ref active gate rather than a second policy
  implementation. Follow-up/residual risk: accepted; package installation stays
  out of scope.
- Content/archive boundary critic: score 9 PASS; Blocking findings: none after
  tests locked that `publish` creates an archive-only commit and rejects
  uncommitted content dirt. Follow-up/residual risk: accepted; chained
  multi-publication releases remain governed by residual-04 boundaries.
- Perspective-eval critic: score 9 PASS; Blocking findings: none after the
  scorer separated public prompt emission from sealed rubric scoring and
  calibration tests reject sealed-rubric source refs. Follow-up/residual risk:
  accepted; this is deterministic calibration, not an AI judge.
- Evidence honesty critic: score 9 PASS; Blocking findings: none after roadmap
  and benchmark docs state that the scorer is calibration infrastructure and not
  governance acceptance evidence. Follow-up/residual risk: accepted; formal
  stable handoff still requires packet and active pointer publication.
- Anti-bloat critic: score 9 PASS; Blocking findings: none; `publish` delegates
  to existing validators and the perspective scorer uses the existing corpus
  format instead of adding packet fields. Follow-up/residual risk: accepted.
- Score handling: score 9; not 10 because package distribution and AI-judge
  semantics remain intentionally outside this repository-local closure.
- Rerun status: publish focused unittest, perspective scorer unittest,
  perspective corpus/scorer CLIs, maintenance policy checks, Active search-set,
  py_compile, and whitespace checks rerun after the implementation.
- Final acceptance: accepted as residual-11/12 repository-local closure.

## Multi-Review Seed

Required critic lenses:

- historical-boundary critic
- fixture-boundary critic
- release-boundary critic
- operator-simplicity critic
- evidence-honesty critic

Blocking rule: any critic finding that a residual label can be read as completed
active v2 functionality must be fixed before the label registry is accepted.

Multi-review:

- Verdict: PASS for creating the residual registry as a labeling and sequencing
  artifact.
- Residual registry critic: score 9 PASS; Blocking findings: none after the
  registry labels were scoped to inventory metadata and follow-up acceptance
  criteria rather than implementation closure.
- Blocking findings: none for labeling; implementation of each residual remains
  separately tracked by its label.
- Follow-up/residual risk: each label needs its own later acceptance packet when
  moved from registry to implementation.
- Score handling: score 9; not 10 because this plan intentionally records
  follow-up work instead of closing it.
- Rerun status: initial registry review complete.
- Final acceptance: accepted as roadmap taxonomy, not as implementation closure.
