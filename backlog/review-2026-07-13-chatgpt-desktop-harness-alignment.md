# Review: ChatGPT desktop harness alignment

- Date: 2026-07-13
- Scope: plugin marketplace packaging, worktree/staged validation boundaries,
  multi-repository trace ownership, init authorization, hook baseline language,
  generated plugin synchronization, and release/search-set coverage.
- Decision: accept the alignment only after independent critics close concrete
  false-green paths and the structured review validator replays every final
  probe.
- Structured result:
  `backlog/multi-review-2026-07-13-chatgpt-desktop-harness-alignment.yml`

Multi-review:

Independent governance review with Validation Layer, Contract Fidelity /
frame-challenge, Governance Anti-Bloat, and Review Quality Meta-Critic roles.

## VETO and rerun lineage

| Critic | Initial result | Blocking class | Resolution | Final result |
|---|---:|---|---|---:|
| Marketplace validation | 7 VETO | Release mixed worktree marketplace validation with index-only plugin sync; malformed extra marketplace entries passed | Added explicit worktree sync mode, release/Standard wiring, single-entry catalog enforcement, and negative tests | 9 PASS |
| Methodology contract | 7 VETO, then 8 VETO | Runtime-specific wording leaked into core; cross-repository writes lacked an explicit scope gate; a narrower wording fix still left `desktop project container` | Made core/reference runtime-neutral, limited writes to explicitly in-scope repositories, kept out-of-scope repositories read-only, and strengthened semantic guards | 9 PASS |
| Anti-bloat | 7 VETO | Plugin and compatibility derivative checks inspected only the index during worktree review | Added symmetric worktree modes while retaining staged defaults, plus unstaged-drift tests | 9 PASS |
| Review quality | 8 VETO | Critic JSON and terminal summaries had no durable transcript/result binding | Added this lineage record, a structured result, exact probe transcripts, and replay validation | 9 PASS |

The initial VETOs were not waived or averaged away. Each affected critic reran
after the corresponding fix. Score-9 residual risks are recorded in the
structured result; none changes the current repository-local acceptance
decision.

## Validation boundary

Repository checks prove artifact shape, staged/worktree selection, generated
copy equality, and documented methodology guards. They do not prove live
ChatGPT desktop skill surfacing or runtime hook event delivery. Hook delivery
remains deferred and the plugin manifest intentionally does not declare a
runtime `hooks` field.

Search-set verification:

- BEFORE: PASS `python3 scripts/run-search-set.py` recorded at
  `trace:backlog/repository-search-set.md#search-set-before-20260713071856-95f69a33-yml-e616aa73`.
- AFTER: PASS `python3 scripts/run-search-set.py` recorded at
  `trace:backlog/repository-search-set.md#search-set-after-20260713081809-95f69a33-yml-0484e870`.
