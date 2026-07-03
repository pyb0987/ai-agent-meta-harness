---
date: "2026-07-03"
escalated_to: instructions
search_set_id: "SS-009"
resolved: true
retrieval:
  mode: not_needed
  reason: "Failure record is based on the current user-provided incident transcript, not prior trace history."
---

## Failure: global trace root missed during target-project diagnosis

### Observation

A downstream Codex session diagnosed a repeated JD location-filter failure in a
target project. The first diagnosis reported that the target project had no
`.harness/`, `.harness/traces`, `.claude/traces`, `AGENTS.md`, or `CLAUDE.md`,
and therefore implied that the ai-agent-meta-harness trace root had not been
initialized there.

The user then asked whether the harness was globally installed. A follow-up
diagnosis found the global Codex trace root at:

```text
/Users/fainders/.codex/harness/traces
```

That global trace root existed, but it did not contain the JD location-filter
failure. The accurate diagnosis was two-layered:

- the target project lacked a project-local trace root for project-specific JD
  filters and executable guards;
- the global trace root existed and should have been checked before claiming
  there was no trace memory;
- the agent's own diagnostic miss was a cross-project harness behavior worth
  recording globally or in this repository's self-application trace.

### Root Cause

The installed Codex `harness-engineer` skill told agents to select the trace
root from the project itself and explicitly said the project trace root was
"not assumed globally." That was correct for project-specific guards, but it
left a product-experience gap: an agent could forget that global installs also
carry cross-project trace memory.

The methodology also did not state the two-layer boundary plainly enough:

- project trace roots hold project-specific recurrence guards, verification
  commands, and domain failures;
- global trace roots hold cross-project agent/harness failures such as routing,
  installation, profile drift, or missing global-trace checks.

### Fix

Escalate the boundary into methodology, reference docs, generated project
templates, Codex/Claude harness-engineer skills, and Active search-set coverage.

The new rule is not an automatic logging daemon. Agents should still avoid
turning ordinary work into harness ceremony. But when diagnosing whether a
harness is present or whether a failure should have been recorded, they must
check both the project-local layer and the installed global layer before making
a trace-history claim.

### Prevention

SS-009 verifies that the methodology, reference, README, Codex project template,
Claude example, and Codex harness-engineer skill preserve this boundary:
global trace roots are cross-project memory only, and they do not replace
project-local search-set guards.
