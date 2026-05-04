---
date: "2026-05-04"
escalated_to: docs
search_set_id: "none"
resolved: true
---

## Failure: misplaced Start Gate backlog reservation

### Observation

During single-session maintenance, a generic patch intended to reserve one
active backlog item matched an earlier `Status: 대기` block instead of the
selected item.

Raw command evidence from item 59 baseline verification:

```text
$ python3 -m unittest tests/test_repository_search_set.py tests/test_backlog_heading_uniqueness.py
..........F
======================================================================
FAIL: test_core_current_status_active_candidates_are_waiting (tests.test_backlog_heading_uniqueness.BacklogHeadingUniquenessTests)
AssertionError: {'56': '진행중'} != {}
```

The same class occurred during item 57 process review: the process critic found
that item 57's Start Gate had been recorded under item 50, and scored the
process review 8/10 VETO until the Start Gate was moved under the correct
heading and Scope was corrected.

### Root Cause

The maintenance edit used a broad markdown replacement around the first matching
`Status: 대기` text instead of anchoring the patch to the selected backlog
heading. In a backlog file with multiple active candidates, an unanchored patch
can reserve the wrong item while the conversational Start Gate names the correct
one.

Relevant files:

- `backlog/core.md` item 57 process record, where the misplaced Start Gate was
  repaired before acceptance.
- `backlog/core.md` item 59 reservation attempt, where item 56 was temporarily
  marked `진행중`.
- `tests/test_backlog_heading_uniqueness.py`, which caught the Current Status
  mismatch when an item listed as an active `should` candidate was no longer
  `대기`.

### Fix

The incorrect item 56 reservation was removed and item 59 received the actual
reservation block and Start Gate under its own heading before implementation
edits continued.

Item 57's earlier process VETO was also resolved by moving the misplaced Start
Gate under the item 57 heading, correcting Scope, recording Completion Gate, and
rerunning the affected process critic to 10/10 PASS.

### Prevention

When reserving a backlog item, patch the section anchored by its exact heading
and immediately inspect the surrounding section plus nearby candidate statuses
before implementation edits. Run `python3 -m unittest
tests/test_backlog_heading_uniqueness.py` when Current Status names active
candidate items, because it detects candidates that are no longer `대기`.

No new search-set Active case was added for this trace. The failure is valuable
as raw process evidence, but its durable prevention is covered by scoped patch
discipline, process review, and the existing backlog Current Status test rather
than a new narrow executable regression command.
