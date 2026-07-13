---
description: "Repository regression search-set for ai-agent-meta-harness maintenance."
last_updated: "2026-07-13"
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
- **verify**: `python3 scripts/check-compat-mirrors.py --worktree`

### SS-003: Pre-commit release gate remains wired
- **Source**: backlog/core.md item 18, item 29, and Codex adapter release-gate follow-ups.
- **Symptom**: Repository drift, smoke, marketplace metadata, or maintenance-review checks can fall out of the tracked pre-commit gate.
- **verify**: `python3 -m unittest tests/test_pre_commit_hook.py tests/test_check_compat_mirrors.py tests/test_sync_codex_plugin.py`

### SS-004: Claude autoresearch preserves REJECT evidence
- **Source**: backlog/claude-adapter.md item 13.
- **Symptom**: REJECT handling can regress to reverting candidate changes before raw evaluator JSON and candidate diffs are recorded for future proposer search.
- **verify**: `python3 -m unittest tests/test_claude_autoresearch_reject_evidence.py`

### SS-005: Codex activation evidence stays aligned
- **Source**: backlog/codex-adapter.md item 31.
- **Symptom**: Root docs and verification policy can again describe local plugin activation as pending or overclaim that CLI activation proves runtime model-visible skill surfacing.
- **verify**: `python3 -m unittest tests/test_pre_commit_hook.py`

### SS-006: Repository search-set stays outside maintainer traces
- **Source**: Maintainer/user boundary review: "Trace is working memory; harness changes are the product."
- **Symptom**: The repository regression manifest is stored under `.harness/traces/`, mixing maintainer working-memory traces with the shipped product surface.
- **verify**: `python3 -m unittest tests/test_repository_search_set.py`

### SS-007: Claude worktrees keep one shared trace root
- **Source**: backlog/review-2026-06-18-worktree-trace-root.md
- **Symptom**: Claude projects that do feature work in git worktrees can leave harness routing only in a local ignored instruction file and write traces to missing or per-worktree `.claude/traces/` roots.
- **verify**: `python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_claude_init_harness_fixture.py tests/test_maintenance_policy_boundaries.py`

### SS-008: Claude global profile drift checker ships with adapter
- **Source**: 2026-07-01 Claude global rules scope review.
- **Symptom**: Users install the harness globally and work in other projects, while hand-authored `~/.claude/rules` and `~/.claude/settings*.json` drift outside repository-local governance.
- **verify**: `python3 -m unittest tests/test_claude_profile_drift.py tests/test_claude_compat_install_smoke.py`

### SS-009: Global traces do not replace project-local guards
- **Source**: backlog/review-2026-07-03-global-project-trace-boundary.md
- **Symptom**: An agent sees no project-local `.harness/traces/` or `.claude/traces/`, concludes the harness has no trace memory, and misses the installed global trace root; or it treats the global trace root as if it covered project-specific search-set guards.
- **verify**: `python3 -m unittest tests/test_core_methodology_boundaries.py tests/test_maintenance_policy_boundaries.py`

### SS-010: ChatGPT desktop plugin and multi-repository contracts stay aligned
- **Source**: 2026-07-13 ChatGPT desktop, plugin marketplace, hooks, and multi-repository compatibility review.
- **Symptom**: The Codex adapter can regress to deferred marketplace metadata, stale hook compatibility claims, Codex Desktop terminology, or one implicit trace root for a multi-repository project.
- **verify**: `python3 -m unittest tests/test_check_codex_marketplace_metadata.py tests/test_core_methodology_boundaries.py adapters.codex.tests.test_hook_schema_drift adapters.codex.tests.test_init_codex_project_fixtures.InitCodexProjectFixtureSmokeTests.test_init_guidance_and_template_cover_multi_repository_projects tests/test_pre_commit_hook.py`

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

### Search-set before 20260713071856 95f69a33.yml e616aa73
- **phase**: before
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: 2cf5bf2f3dfdc9ab4edf1d2a7a834c596a68ea3d8ce1de31b7794e6f33ed7d65
- **stderr_sha256**: 36becea9e0b49507a0e91031479b0cd325a6465139fd93456edf43a89cb28815
- **head_ref**: `a26253b6fba552ee3b915d057496ce9882a67f7d`
- **captured_at**: 2026-07-13
- **packet_ref**: `archive/v2/packets/pkt-20260713161845-95f69a33.yml`

### Search-set after 20260713081640 95f69a33.yml 253ffba8
- **phase**: after
- **status**: FAIL
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 1
- **stdout_sha256**: afa517754d096dfdda8e2d1f7fbaa33e7cc0c54e99220d498edc44d60f8edd58
- **stderr_sha256**: 0bba9d1b3f02d1ce198abdd622b252123bef0836ae70243fcfce5bd51f27619b
- **head_ref**: `a26253b6fba552ee3b915d057496ce9882a67f7d`
- **captured_at**: 2026-07-13
- **packet_ref**: `archive/v2/packets/pkt-20260713161845-95f69a33.yml`

### Search-set after 20260713081809 95f69a33.yml 0484e870
- **phase**: after
- **status**: PASS
- **command**: `python3 scripts/run-search-set.py`
- **exit_code**: 0
- **stdout_sha256**: a6c7167e5c041029c4a059f20918622327dff98f8003f5e815fac606b023fde6
- **stderr_sha256**: f467c3495ea8dbb8dda0e7b733f5299dd977ab4160d042d5b459ca78f2b2d0a5
- **head_ref**: `a26253b6fba552ee3b915d057496ce9882a67f7d`
- **captured_at**: 2026-07-13
- **packet_ref**: `archive/v2/packets/pkt-20260713161845-95f69a33.yml`
