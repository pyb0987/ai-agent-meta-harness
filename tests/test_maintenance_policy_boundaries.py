from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "MAINTENANCE.md"
ROADMAP = ROOT / "backlog" / "v2-roadmap.md"
PLAN10 = ROOT / "backlog" / "plans" / "10-stable-packet-materialization-and-operator-minimal-cli.md"


def maintenance_text() -> str:
    return MAINTENANCE.read_text(encoding="utf-8")


def normalized_text() -> str:
    return " ".join(maintenance_text().split())


def normalized_file_text(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


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
            "Release/pre-commit now route active archive packet publication through the packet-pointer gate",
            "governance start --base-ref REF --intent",
            "governance finalize --packet <packet> --staged|--base-ref REF|--worktree",
            "governance import-review --packet <packet> --from <review-artifact-or-stdin> [--output <artifact>]",
            "governance write-pointer --packet <packet>",
            "governance check --packet <packet> --require-stable",
            "python3 scripts/check-active-packet-gate.py --base-ref origin/main",
            "python3 scripts/check-active-packet-gate.py --staged",
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
            "Routine active base-ref starts default to",
            "reject non-archive output paths",
            "Do not reuse v1 backlog archive semantics for v2 packets",
            "python3 scripts/check-governance-acceptance.py check-pointer --pointer archive/v2/pointers/<packet_id>.yml",
            "packet lifecycle is finalized",
            "`result.decision.accepted: yes`",
            "required source refs resolve",
            "checker version, inference rule version, baseline/comparison refs, packet-bound accepted HEAD commit, stable target, and decision status match the archived packet",
            "`write-pointer` records a reproducible synthetic `archive_commit` hash",
            "The synthetic commit object is not required to remain reachable in every clone",
            "routine base-ref finalization into `archive/v2/packets/` also materializes the durable command artifact",
            "archived review-import artifacts and linked probe transcripts are bound by",
            "`status` is read-only inventory",
            "archived active source refs use commit-pinned `git:<full-commit-sha>:<path>`",
            "`write-pointer` materializes pointer-bound replay metadata and recorded exit/stdout/stderr hashes",
            "`--overwrite` regenerates existing pointer-bound replay metadata",
            "archived command artifacts are bound by SHA-256 and include pointer-bound replay metadata",
            "explicit pointer replay can rerun archived command evidence and compare recorded exit/stdout/stderr hashes",
            "historical `archive/v2/` bytes are committed repository bytes, not a future whitelist",
            "Routine `finalize`, stable `check`, release, and pre-commit flows do not execute or trust prior pointer command results",
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

    def test_plan10_locks_operator_minimal_contract(self) -> None:
        text = normalized_file_text(PLAN10)

        for marker in (
            "governance start --base-ref <comparison-ref> --intent",
            "governance import-review --packet <packet> --from <review-artifact-or-stdin> [--output <artifact>]",
            "Generated claim-evidence prompts and placeholders cannot certify stable handoff by shape alone",
            "Runtime, proof-like, or public claims still require a raw artifact",
            "imported review judgment",
            "before stable publication",
            "Plan 08 replay policy is stream-specific",
            "`verify-release.py --list` stdout must remain bound exactly",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_roadmap_commits_public_governance_wrapper_name(self) -> None:
        text = normalized_file_text(ROADMAP)

        for marker in (
            "governance start --base-ref <comparison-ref> --intent",
            "governance import-review --packet <packet> --from <review-artifact-or-stdin>",
            "[--output <artifact>]",
            "How the public `governance` wrapper should be installed or exposed",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("whether the public cli should be `governance`", text.lower())


if __name__ == "__main__":
    unittest.main()
