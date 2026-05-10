from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "MAINTENANCE.md"


def maintenance_text() -> str:
    return MAINTENANCE.read_text(encoding="utf-8")


def normalized_text() -> str:
    return " ".join(maintenance_text().split())


class MaintenancePolicyBoundaryTests(unittest.TestCase):
    def test_v2_packet_lifecycle_is_active_policy(self) -> None:
        text = normalized_text()

        for marker in (
            "This document defines the active maintenance model for the v2 transition",
            "AI Agent Meta-Harness v2 replaces human-authored maintenance gates with generated acceptance packets",
            "The active roadmap is `backlog/v2-roadmap.md`",
            "The harness infers change class, impact, required evidence, required review, and eligibility",
            "The harness stores the result as an `AcceptancePacket`",
            "Stable handoff is accepted by the packet checker only from packet-backed base-ref verification; staged verification is preflight evidence, not active stable handoff",
            "Release/pre-commit packet-pointer gating is still Plan 08 transition work",
            "governance start --intent",
            "governance finalize --packet <packet> --staged|--base-ref REF|--worktree",
            "governance check --packet <packet>",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_v1_gates_are_archived_not_active_target(self) -> None:
        text = normalized_text()
        lower = text.lower()

        for marker in (
            "The v1 maintenance system is frozen at `archive/v1/MAINTENANCE.md`",
            "Its Start Gate, Completion Gate, review-summary labels, fallback-threshold disposition, and backlog archive lifecycle are historical evidence, not the active design target",
            "Legacy checkers may remain useful while v2 is bootstrapped, but they are compatibility checks for old record shapes",
            "They do not prove that frozen v1 records under `archive/v1/` are fully covered unless the checker explicitly says so",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

        self.assertNotIn("pick exactly one concrete `Status: 대기` backlog item", text)
        self.assertNotIn("Complete the Completion Gate", text)
        self.assertNotIn("Current Maintenance Plan", text)
        self.assertNotIn("backlog/core.md for shared methodology", text)
        self.assertNotIn("paper requires reviewer scores below 9", lower)
        self.assertNotIn("paper requires score 9", lower)

    def test_methodology_anchors_are_packet_fields(self) -> None:
        text = normalized_text()

        for marker in (
            "Fixed evaluator boundary: evaluator commands, protected paths, boundary changes, and disposition must be visible in packet evidence",
            "Trace reuse: search-set before/after evidence, evolution trace disposition, and failure trace disposition must be preserved when relevant",
            "Confounder isolation: packet evidence must distinguish intended scope, actual changed files, deviations, and whether the change was isolated or bundled",
            "Evidence honesty: runtime, public, or proof-like claims must be structured; verified claims require raw artifact, log, screenshot, or exported trace refs",
            "Human judgment boundary: waivers, downgrades, skipped required evidence, residual-risk acceptance, and review exceptions require actor, role, date, reason, and source reference",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_bootstrap_rules_cover_pre_packet_transition(self) -> None:
        text = normalized_text()

        for marker in (
            "Historical v2 implementation work before `governance start` and stable packet checks existed used a bootstrap transition note",
            "New active v2 implementation work should use the packet lifecycle above",
            "exact skipped-before reason when no start packet exists",
            "reviewer or maintainer disposition for any waiver, downgrade, skipped required evidence, or residual risk",
            "explicit statement that the record is not a finalized v2 packet",
            "This bootstrap note is temporary compatibility evidence, not the current v2 target",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_packet_archive_direction_avoids_v1_archive_semantics(self) -> None:
        text = normalized_text()

        for marker in (
            "Use a distinct v2 packet namespace",
            "Prefer `archive/v2/packets/`",
            "Do not reuse v1 backlog archive semantics for v2 packets",
            "packet lifecycle is finalized",
            "`result.decision.accepted: yes`",
            "required source refs resolve",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_review_thresholds_are_bootstrap_policy_not_paper_claim(self) -> None:
        text = normalized_text()

        for marker in (
            "Use multi-review for v2 packet schema, checker semantics, archive integration, release-gate wiring, evaluator-boundary changes, runtime evidence claims, and public methodology claims",
            "During bootstrap, any critic score below 9 is blocking for stable handoff until the finding is fixed or the work is explicitly not accepted",
            "Score 9 requires a why-not-10 reason and a residual-risk or follow-up disposition",
            "These records should move into packet fields once the v2 checker can capture them",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
