# v2 Planning

This directory holds implementation plans for the v2 transition.

Each plan should be developed through multi-review until every required critic
scores at least 9 and no VETO remains. Plans should preserve the v2 product
requirement: simplify the user interface and overall operating model while
keeping Meta-Harness evidence intact.

Use one plan per implementation layer. Do not carry v1 backlog items forward by
default; extract only the failure modes that explain a v2 requirement.

Plan 12 starts the post-v2 strategy-search layer. It is intentionally separate
from v2 governance: search runs produce candidate diffs and traces, while v2
AcceptancePackets remain the adoption and publication path.

Plan 13 is the post-MVP hardening layer for strategy-search runner isolation,
proposal-ledger anchoring, and any future pointer-bound route for selected
search artifacts.
