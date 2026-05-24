# Plan 13: Strategy Search Runner Isolation And Ledger Anchoring

## Status

Planned post-MVP hardening.

## Motivation

Plan 12 provides a repository-local strategy-search MVP: directions, candidate
evaluation, proposer bundles, trace/search-set summaries, and selected
adoption artifacts. The MVP now detects ordinary source, `.git`, run-store,
 workspace, evaluator-closure, and public-context drift. Four boundaries still
need a stronger design before strategy search can be described as fully
isolated:

- Detached descendants can outlive the evaluator process group, close stdio,
  sleep past the settle window, and mutate source or run-store paths after a
  candidate is recorded.
- Proposal ledgers are repository files. They detect duplicate or inconsistent
  entries, but they are not append-only anchors against a local rewrite of both
  `proposal.yml` and `proposals.jsonl`.
- Selected candidate artifacts remain diagnostic unless they are tied back to
  an eval-produced candidate record. A self-consistent handwritten
  `score.yml`/`trace.yml`/logs bundle should not be enough to create adoption
  evidence once ledger anchoring exists.
- Evaluator stdout/stderr logs are diagnostic text views. If they become raw
  stable evidence, the runner must preserve and hash exact output bytes beside
  the replacement-decoded text view.

## Scope

- Run evaluators in an isolation boundary that prevents writes to the source
  repository and run store by construction, not only by digest-and-restore.
- Remove or sharply reduce source-root absolute paths from evaluator execution
  context.
- Add a post-evaluator quiescence model that is not a fixed short sleep.
- Anchor proposal creation records in a non-self-attesting store, such as
  Git-pinned commits, signed ledger entries, or an append-only log outside the
  mutable run directory.
- Anchor candidate evaluation records in the same non-self-attesting store so
  `select` can require proof that `eval` produced the candidate before it
  materializes durable diagnostic artifacts.
- Define how selected strategy-search artifacts become pointer-bound stable
  evidence, or explicitly keep them diagnostic-only until wrapped by existing
  v2 evidence types.

## Non-Goals

- No change to Plan 12 candidate scoring semantics.
- No claim that selected strategy-search artifacts replace v2
  AcceptancePackets, MultiReviewResult imports, or active pointer publication.
- No package-manager distribution requirement.

## Acceptance Criteria

- A detached descendant probe cannot mutate source, `.git`, or the run store
  after `eval` has returned `pass`.
- Rewriting a ready proposal, its patch, and its local ledger entry cannot
  produce an accepted evaluation unless the external anchor also matches.
- Hand-authoring a self-consistent candidate directory cannot pass `select`
  unless the candidate is present in the external eval ledger.
- The selected-artifact adoption path states exactly which refs are
  pointer-bound stable evidence and which remain diagnostic.
- Multi-review includes isolation, ledger-authenticity, governance-boundary,
  and operator-simplicity critics.
