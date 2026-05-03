---
description: "Repository self-application search-set for claude-code-harness maintenance."
last_updated: "2026-05-03"
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

## Archived
