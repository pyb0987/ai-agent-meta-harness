# Repository Instructions

## Build and Verification

- Run `python3 scripts/run-search-set.py` for the repository's Active regression cases.
- Run `python3 scripts/sync-codex-plugin.py --check` after Codex adapter changes.
- Run `sh .githooks/pre-commit` for the fast staged gate.
- Run `python3 scripts/verify-release.py --base-ref origin/main` only for a clean, packet-backed release candidate; use `--skip-clean-worktree` for in-progress preflight.

## Architecture

- `core/` is the canonical runtime-neutral methodology. Runtime behavior belongs under `adapters/`.
- `adapters/codex/` is the editable Codex source; `plugins/ai-agent-meta-harness/` is generated. Update it with `python3 scripts/sync-codex-plugin.py --write`.
- `archive/v1/` is frozen historical evidence. Active planning and governance use `backlog/`, `MAINTENANCE.md`, and the `governance` command.

## Harness

- Before harness-affecting changes, run `./governance start --base-ref <ref> --intent "..."` and capture the relevant before evidence. Finalize against the same immutable comparison boundary.
- Use `backlog/repository-search-set.md` as this provider repository's tracked regression manifest. Raw maintainer traces under `.harness/traces/` or `.claude/traces/` are ignored working memory and must not be published as product state.
- If local trace roots diverge, select or migrate the active root by evidence before writing new traces. Do not split one repository's history across roots by accident.
- In a multi-repository ChatGPT desktop project, each repository owns its own instructions, trace root, and verification commands. Change only repositories explicitly in task scope; cross-repository work must name and verify each in-scope repository without collapsing histories into one implicit root.
- Bounded self-evolution proposals are diagnostic until adopted. Do not auto-edit Active search-set cases or treat low trace volume as a failure.
- Governance-grade multi-review PASS requires `scripts/check-multi-review-result.py`; otherwise multi-review is advisory.

## Codex Notes

- The repo marketplace is `.agents/plugins/marketplace.json`; the canonical plugin source remains `adapters/codex/` and the installable generated bundle remains `plugins/ai-agent-meta-harness/`.
- Delegate independent work only when the user, an applicable `AGENTS.md`, or a selected skill explicitly requests subagents. Keep write-heavy work coordinated to avoid conflicts.
- Preserve user changes in dirty worktrees and use scoped approval for network access, writes outside the workspace, or destructive actions.
