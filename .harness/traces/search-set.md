---
description: "Repository self-application search-set for claude-code-harness maintenance."
last_updated: "2026-06-18"
---
# Harness Search Set

Active regression cases for this repository's own harness-maintenance loop.
Run relevant Active verify commands before and after harness-affecting
repository changes when practical.

## Active

### SS-001: Backlog review records keep enforceable gates
- **Source**: backlog/core.md item 20, item 25, and repeated maintenance review follow-ups.
- **Symptom**: Review records can drift into prose that appears accepted while missing required Completion Gate fields, VETO handling, or score-9 why-not-10 disposition.
- **verify**: `python3 scripts/check-maintenance-review.py`

### SS-002: Compatibility mirrors stay synchronized
- **Source**: backlog/core.md item 8 and Claude adapter compatibility mirror follow-ups.
- **Symptom**: Root compatibility mirrors can silently diverge from canonical adapter/core sources, causing old install paths to serve stale instructions.
- **verify**: `python3 scripts/check-compat-mirrors.py`

### SS-003: Pre-commit release gate remains wired
- **Source**: backlog/core.md item 18, item 29, and Codex adapter release-gate follow-ups.
- **Symptom**: Repository drift, smoke, marketplace metadata, or maintenance-review checks can fall out of the tracked pre-commit gate.
- **verify**: `sh .githooks/pre-commit`

### SS-004: Claude autoresearch preserves REJECT evidence
- **Source**: backlog/claude-adapter.md item 13.
- **Symptom**: REJECT handling can regress to reverting candidate changes before raw evaluator JSON and candidate diffs are recorded for future proposer search.
- **verify**: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`

### SS-005: Codex activation evidence stays aligned
- **Source**: backlog/codex-adapter.md item 31.
- **Symptom**: Root docs and verification policy can again describe local plugin activation as pending or overclaim that CLI activation proves runtime model-visible skill surfacing.
- **verify**: `python3 -m unittest tests/test_pre_commit_hook.py`

### SS-006: Repository trace root keeps minimum self-application surface
- **Source**: backlog/core.md item 33 and the 2026-05-04 self-application trace-root multi-review VETO.
- **Symptom**: Repository maintenance can have `.harness/traces/search-set.md` while missing sibling `evolution/`, `failures/`, or `experiments/` surfaces, so future trace reuse silently becomes incomplete.
- **verify**: `python3 -m unittest tests/test_repository_search_set.py`

### SS-007: Claude worktrees keep one shared trace root
- **Source**: .harness/traces/failures/002-worktree-local-trace-loss.md
- **Symptom**: Claude projects that do feature work in git worktrees can leave harness routing only in a local ignored instruction file and write traces to missing or per-worktree `.claude/traces/` roots.
- **verify**: `python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_claude_init_harness_fixture.py tests/test_maintenance_policy_boundaries.py`

## Archived

## Search-set Evidence Captures

### Search-set after v2 fixture
- **phase**: after
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- **stderr_sha256**: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- **head_ref**: `dc0545f5f9403b52b81221fc0cd27a0a7ecd1165`
- **captured_at**: 2026-05-18
- **packet_ref**: `backlog/fixtures/acceptance-packets/finalized-harness-affecting.yml`
