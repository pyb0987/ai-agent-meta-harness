# Repository-Local Meta-Harness System

This document explains the practical Meta-Harness system implemented in this
repository. It describes what is complete, what remains an evaluation layer, and
how the strategy-search evolution engine connects to v2 governance.

This repository does not claim local reproduction of the Meta-Harness paper's
benchmark gains. It implements a repository-local method for changing harnesses,
preserving trace evidence, evaluating candidate strategy changes, and adopting
successful changes through the v2 packet and pointer publication flow.

## What Agent-In-The-Loop Semantic Evaluation Means

Agent-in-the-loop semantic evaluation is a benchmark layer, not the core
governance or runner mechanism.

In the current implementation, many checks are structural:

- Did a candidate patch touch only the allowed search surface?
- Did the fixed evaluator run in an isolated workspace?
- Did stdout, stderr, trace, score, and patch bytes match their hashes?
- Did the candidate come from a Git-anchored `eval` event?
- Did v2 stable handoff use an AcceptancePacket and active pointer?

Those checks can prove that the process was followed and that the recorded bytes
match. They do not prove that an AI critic independently understood the public
input, discovered the important issue, and judged evidence relevance at a human
semantic level.

Agent-in-the-loop semantic evaluation would measure that missing layer. A runner
would give agents controlled public inputs, ask them to review or score
candidates, and compare their judgments against expected semantic findings. For
example:

- Can an agent identify a hidden false-green risk from public evidence?
- Can independent critics disagree usefully instead of repeating the same
  surface summary?
- Can a reviewer tell whether cited evidence is relevant to the claim, not only
  whether the file reference resolves?
- Can a strategy-search candidate improve benchmark behavior rather than only
  satisfy schema and hash checks?

That layer is useful for measuring methodology fidelity and critic quality. It
is intentionally separate from the implemented repository-local mechanics.

## System Overview

The implemented system has two cooperating halves:

1. v2 governance decides whether repository changes are acceptable and
   publishable.
2. Strategy search proposes and evaluates candidate changes to harness strategy.

They meet at a strict adoption boundary: strategy-search output is diagnostic
history, while stable repository adoption still requires a normal content commit
and v2 AcceptancePacket publication.

```text
strategy direction
  -> proposal bundle
  -> candidate patch
  -> isolated fixed-evaluator run
  -> Git-anchored candidate trace
  -> diagnostic selection summary
  -> adopted content commit
  -> v2 AcceptancePacket
  -> active pointer publication
```

## Layer 1: Strategy Direction

A strategy-search run starts from a direction file. The direction declares:

- the objective;
- the base commit;
- the mutable search surface;
- the fixed evaluator command;
- protected evaluator paths;
- oracle paths;
- score parser paths;
- success criteria.

The central boundary is simple:

- candidate patches may change the search surface;
- candidate patches must not change evaluator closure, oracle material, score
  parsers, governance publication files, or `archive/v2`;
- evaluator dependencies must be declared and hashed.

This turns strategy improvement into code-space search: the agent proposes
diffs against versioned files, and the same fixed evaluator judges every
candidate.

## Layer 2: Proposal Bundle

`strategy-search.py propose` creates a public proposal bundle for a candidate.
The bundle is designed for a human or agent proposer. It includes the objective,
allowed write paths, sanitized prior candidate summaries, and the fixed
evaluation instruction.

The bundle deliberately excludes sealed material:

- evaluator internals;
- oracle paths;
- score-parser internals;
- raw run-store trace files;
- raw stdout or stderr logs;
- archive evidence.

This keeps proposer creativity focused on the search surface instead of letting
the proposer overfit hidden evaluator details.

## Layer 3: Isolated Evaluation

`strategy-search.py eval` evaluates a candidate patch outside the source
repository. The runner exports only the needed base-commit files into a
disposable workspace, applies the candidate patch there, initializes a temporary
Git repository, and runs the fixed evaluator from that workspace.
The evaluator receives a scrubbed environment: source-root paths, run-store
paths, caller `HOME` and temp-dir variables, runtime hook variables, and Git
worktree variables are removed or replaced with runner-selected external temp
paths outside the source/archive/run-store roots. `HOME` and `TMPDIR` are
per-evaluation so candidate caches and temp markers cannot silently carry
across later evaluations. If the runner supplies a `python3` PATH binding for
platform stability, the target executable and its containing directory must be
non-writable by the evaluator user. The path binding text, target path, target
hash, and post-eval binding and target hashes are bound into the candidate
record and candidate digest; runtime target mutation is an evaluator boundary
failure.

This design reduces the old false-green class where an evaluator could mutate
source files, `.git` metadata, run-store files, or `archive/v2` and still appear
to pass. The source repository and run store are not mounted as evaluator output
targets. The runner remains responsible for writing candidate records after the
evaluator exits.

The default repository-local path is not an OS sandbox. If a hostile fixed
evaluator already knows absolute host paths and daemonizes a child that writes
after the runner's settle window, that boundary needs a future platform sandbox
such as a container or OS policy layer. Plan 13 closes the practical
relative-path/run-store false-green path without adding operator prompts.
The same boundary applies to hostile same-user runtime replacement,
case-insensitive path aliases, temp-sibling checkout discovery, and concurrent
proposal-sealing races. Those are sandbox/concurrency concerns, not extra
operator steps in the default Meta-Harness workflow.

`backlog/plans/14-sandbox-and-concurrency-boundary.md` records that optional
future layer. It is a boundary definition, not a requirement for the normal
repository-local workflow.

The evaluator output is stored in two forms:

- decoded `stdout.log` and `stderr.log` for human inspection;
- exact `stdout.raw` and `stderr.raw` byte sidecars for reproducible hashing.

Both forms are bound into the candidate record and validator.

## Layer 4: Commit-Anchored Trace

The immutable trace idea is implemented as a repository-local Git event chain.
Each strategy-search run has an anchor ref:

```text
refs/meta-harness/strategy-search/<run-id>
```

The runner appends small Git commits to that ref. Each commit contains a
canonical `event.yml` and, when possible, uses the previous anchor commit as its
parent. The important event types are:

- `proposal_created`;
- `proposal_ready`;
- `candidate_evaluated`.

These events record the run id, candidate id, direction digest, proposal digest,
patch hash, candidate digest, previous anchor, timestamp, and runner version.

The run directory still contains readable YAML and JSONL files, but those files
are mirrors. The trust root is the Git anchor chain. If someone hand-edits a
candidate directory, rewrites a local ledger row, or fabricates a self-consistent
`score.yml`, `select` rejects it unless the candidate matches a reachable
`candidate_evaluated` anchor event.

The anchor is not a hostile-owner security mechanism. A local operator with full
repository control can rewrite Git history. Its purpose is more practical:
separate runner-produced diagnostic records from mutable run-store sidecars
without asking the operator to manage manual digests or signatures.
Git compare-and-swap failures are fail-closed concurrency signals. The default
repair is to rerun from a fresh proposal/run; the repository-local path does not
claim transactional multi-writer proposal repair.

## Layer 5: Candidate Digest

Each evaluated candidate receives a `candidate_digest`. The digest is computed
before the future eval anchor commit is known, so it excludes
`eval_anchor_commit` and the digest field itself.

The digest binds:

- `patch.diff`;
- `score.yml` without circular fields;
- `trace.yml`;
- decoded stdout and stderr log hashes;
- raw stdout and stderr byte hashes;
- run and candidate identity;
- direction digest;
- the pre-eval anchor.

This lets validation ask one question: does this selected candidate match the
runner-produced payload that was anchored at evaluation time?

## Layer 6: Diagnostic Selection

`strategy-search.py select` selects a candidate for adoption. Selection is
diagnostic-only. It writes selection and summary YAML under the run directory,
not under `archive/v2/artifacts`.

Selection proves:

- the candidate passed or was explicitly selected as non-pass diagnostic
  context;
- the candidate came from an anchored evaluator run;
- the candidate digest matches its runner-produced sidecars;
- the selected output is not pretending to be v2 stable evidence.

Selection does not prove stable handoff. To adopt the change, the operator
applies the selected patch as an ordinary content commit.

## Layer 7: v2 Governance Adoption

After a selected strategy-search patch becomes a content commit, the v2
governance layer takes over.

The stable adoption path is:

```text
content commit
  -> governance start/finalize
  -> required evidence and review imports
  -> write-pointer
  -> governance publish
  -> check/verify-release
```

The active pointer publication binds the accepted packet and archive evidence.
This is where repository history says, "this change is stable governance
evidence." Strategy-search run files alone never make that claim.

## Bounded Self-Evolution

The repository-local Meta-Harness can improve from its own usage without
becoming an invisible self-modifying system.

The default loop is:

```text
usage evidence or trace gap
  -> diagnostic candidate
  -> raw evidence and executable verification
  -> reviewable content change
  -> v2 governance when stable publication is needed
```

During ordinary agent work, agents may surface at most one diagnostic
maintenance note when a concrete trigger-evidence pointer, reusable future
value, and a clear next action are all visible. Explicit dogfood checks may
inspect the wider candidate list. Those nominations are proposals only. A
detector saying "this looks stale" or "this search-set may be missing" is a
pointer to inspect, not proof that the harness has improved.

This preserves the raw-data-first rule:

- trace catalogs and generated summaries help retrieval, but do not certify
  evidence;
- trace-history claims use byte-matching raw trace refs from Plan 16;
- strategy-search selections stay diagnostic until applied as ordinary content
  changes;
- stable publication still flows through v2 packets and active pointers.

This is the intended meaning of self-evolution in this repository: during agent
work or explicit diagnostic checks, the harness can propose ways to improve
itself, while adoption remains bounded by evidence, verification, and review.

Global agent installs add one more diagnostic layer, not a replacement project
memory. `${CODEX_HOME:-~/.codex}/harness/traces` and
`${CLAUDE_HOME:-~/.claude}/harness/traces` are for cross-project agent/harness
failures such as routing, install drift, or profile drift. Project-specific
guards and verification remain in the target project's active trace root.

## Why Commits Are The Unit

Commits are the unit because the system needs a stable, inspectable boundary
between content changes and publication records.

For v2 governance:

- the content commit is the change being accepted;
- the archive publication commit records the packet, pointer, and bound
  artifacts;
- release verification checks that the pointer corresponds to exactly one
  active publication unit.

For strategy search:

- the base commit fixes the candidate's starting point;
- the evaluator workspace exports files from that base commit;
- the Git anchor chain records proposal and eval events without relying on
  mutable run-store files.

Commits therefore give the system a durable byte boundary for both adopted
repository changes and diagnostic evolution traces.

## Completion Boundary

Plans 12 and 13 define and harden the repository-local evolution engine:

- define a strategy-search direction;
- generate or import candidate patches;
- evaluate candidates with a fixed evaluator in an isolated workspace;
- preserve decoded and raw evaluator output;
- anchor proposal and eval records in Git;
- reject handwritten or rewritten candidates during selection;
- adopt selected changes only through normal v2 governance.

Plans 15, 16, and 17 describe the usability and evidence layers around that
engine:

- route ordinary user language to the right harness behavior without skill-name
  ceremony;
- make trace retrieval claims checkable through raw byte quotes;
- let agents propose dogfood-derived trace, search-set, instruction, and
  strategy-search improvements without automatic adoption.

The remaining non-core layer is measurement:

- agent-in-the-loop semantic evaluation;
- benchmark scoring of critic quality;
- paper-style reproduction claims.

Those layers can measure how well the system searches and reviews. They are not
required for the repository-local mechanics described here to function.
