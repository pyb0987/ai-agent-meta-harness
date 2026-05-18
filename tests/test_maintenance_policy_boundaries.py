from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "MAINTENANCE.md"
ROADMAP = ROOT / "backlog" / "v2-roadmap.md"
PLAN10 = ROOT / "backlog" / "plans" / "10-stable-packet-materialization-and-operator-minimal-cli.md"
PLAN11 = ROOT / "backlog" / "plans" / "11-v2-residual-hardening-and-operations.md"
PLAN02 = ROOT / "backlog" / "plans" / "02-acceptance-packet-schema-and-fixtures.md"
PLAN09 = ROOT / "backlog" / "plans" / "09-historical-archive-closure-and-attestation.md"
FIXTURE_README = ROOT / "backlog" / "fixtures" / "acceptance-packets" / "README.md"


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
            "governance review-template --packet <packet> [--output <artifact>|--scratch-output <draft>]",
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
            "release active pointer validation and explicit pointer replay rerun archived command evidence and compare recorded exit/stdout/stderr hashes",
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
            "governance review-template --packet <packet> [--output <artifact>|--scratch-output <draft>]",
            "governance import-review --packet <packet> --from <review-artifact-or-stdin>",
            "[--output <artifact>]",
            "current repository-local executable is the v2 command surface",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertNotIn("whether the public cli should be `governance`", text.lower())

    def test_residual_registry_labels_follow_up_scope(self) -> None:
        maintenance = normalized_text()
        roadmap = normalized_file_text(ROADMAP)
        plan11 = normalized_file_text(PLAN11)

        for label in (
            "v2-residual-01 legacy-v1-boundary",
            "v2-residual-02 historical-fixture-boundary",
            "v2-residual-03 governance-packaging",
            "v2-residual-04 multi-publication-release",
            "v2-residual-05 checker-versioned-history",
            "v2-residual-06 worktree-mode-boundary",
            "v2-residual-07 packet-hash-placement",
            "v2-residual-08 release-command-replay-gate",
            "v2-residual-09 search-set-trace-fidelity",
            "v2-residual-10 review-template-completion-ergonomics",
            "v2-residual-11 publish-wrapper-ergonomics",
            "v2-residual-12 agent-in-loop-multi-review-eval",
        ):
            with self.subTest(label=label):
                self.assertIn(label, maintenance)
                self.assertIn(label, roadmap)
                self.assertIn(label, plan11)

        self.assertIn("Plan 10 completes the v2 core governance path", roadmap)
        self.assertIn("Do not cite a residual label as completed active functionality", maintenance)
        self.assertIn("They are not blockers for the Plan 10 active pointer flow", plan11)
        self.assertIn("not as implementation closure", plan11)

    def test_residual_fixture_and_history_boundaries_are_marked(self) -> None:
        plan02 = normalized_file_text(PLAN02)
        fixture_readme = normalized_file_text(FIXTURE_README)
        plan09 = normalized_file_text(PLAN09)

        for text in (plan02, fixture_readme, plan09):
            with self.subTest(text=text[:80]):
                self.assertIn("v2-residual-02 historical-fixture-boundary", text)

        self.assertIn("fixture PASS/FAIL outcomes are validator controls, not active project governance evidence", plan02)
        self.assertIn("not an active handoff record, future archive whitelist, or routine trusted command-evidence source", fixture_readme)
        self.assertIn("they do not become active closure inputs for future packets", plan09)

    def test_worktree_and_packet_hash_residuals_do_not_overclaim(self) -> None:
        roadmap = normalized_file_text(ROADMAP)
        maintenance = normalized_text()
        plan10 = normalized_file_text(PLAN10)
        plan11 = normalized_file_text(PLAN11)

        for text in (roadmap, maintenance, plan10):
            with self.subTest(text=text[:80]):
                self.assertIn("`--worktree` is always non-stable exploratory/in-progress evidence", text)

        self.assertIn("current active model keeps packet digests in active pointers and review-import target bindings", roadmap)
        self.assertIn("Whether to add a packet-internal hash later", roadmap)
        self.assertIn("active pointer bytes are the current packet-bound integrity root", plan11)
        self.assertNotIn("`--worktree` is exploratory unless explicitly marked non-stable", roadmap)
        self.assertNotIn("`--worktree` remains exploratory unless explicitly marked non-stable", plan10)

    def test_plan10_completion_is_scoped_to_single_publication_path(self) -> None:
        text = normalized_file_text(PLAN10)

        self.assertIn("Plan 10 owns the operator-minimal single-publication path", text)
        self.assertIn("Plan 10's single-publication materialization path", text)
        self.assertIn("within the Plan 10 single-publication materialization scope", text)
        self.assertNotIn("Plan 10 owns the remaining usability gap", text)

    def test_plan11_iteration_closes_first_two_residual_boundaries_only(self) -> None:
        text = normalized_file_text(PLAN11)

        self.assertIn("Implementation Iteration 1", text)
        self.assertIn("Closed in this iteration", text)
        self.assertIn("v2-residual-01 legacy-v1-boundary", text)
        self.assertIn("tests/test_v1_archive_boundary.py", text)
        self.assertIn("v2-residual-02 historical-fixture-boundary", text)
        self.assertIn("tests/test_maintenance_policy_boundaries.py", text)
        self.assertIn("Import-review operator flow remains archive-generating and stdin-capable", text)
        self.assertIn("requiring reviewers to predict the final packet SHA", text)
        self.assertIn("Still pending", text)
        self.assertIn("v2-residual-04 multi-publication-release", text)
        self.assertIn("v2-residual-03 governance-packaging", text)

    def test_multi_publication_release_residual_is_design_only(self) -> None:
        maintenance = normalized_text()
        roadmap = normalized_file_text(ROADMAP)
        plan11 = normalized_file_text(PLAN11)

        for marker in (
            "Implementation Iteration 2",
            "Current policy",
            "Future chained-pointer design requirements",
            "False-green probes a future implementation must cover",
            "The release gate still does not accept chained active publications in one release range as a completed model",
            "governance status` remains inventory, not a chain trust ledger",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, plan11)

        for marker in (
            "valid pointer publication, archive rewrite, then byte-for-byte revert",
            "valid pointer publication followed by an unrelated valid pointer publication",
            "no-ff merge checkout with no merge-side archive content",
            "no-ff merge checkout that introduces archive content from the merge side",
            "two pointers whose publication order is reversed",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, plan11)

        self.assertIn("v2-residual-04 multi-publication-release", maintenance)
        self.assertIn("validate each publication boundary in order", maintenance)
        self.assertIn("reject archive rewrites even when later reverted", maintenance)
        self.assertIn("avoid turning `governance status` into a trust ledger", maintenance)
        self.assertIn("chained publications need an explicit later model", roadmap)
        self.assertIn("rejects archive drift hidden by later reverts", roadmap)

    def test_plan11_closes_remaining_v2_residuals_without_optional_features(self) -> None:
        maintenance = normalized_text()
        roadmap = normalized_file_text(ROADMAP)
        plan11 = normalized_file_text(PLAN11)

        for marker in (
            "Implementation Iteration 3",
            "v2-residual-03 governance-packaging`: `governance` is the public operator command for v2",
            "v2-residual-05 checker-versioned-history`: active pointers record `checker_version` and `inference_rule_version`",
            "v2-residual-06 worktree-mode-boundary`: `--worktree` remains exploratory/non-stable",
            "v2-residual-07 packet-hash-placement`: v2 keeps packet digest roots in active pointers and review-import target bindings",
            "Final v2 completion policy",
            "`review-template` owns the target-bound review-import skeleton shape",
            "Future work after v2 completion",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, plan11)

        self.assertIn("Plan 11 closes the original residual labels for the v2 active model", maintenance)
        self.assertIn("reviewer-wizard completion, one-command publish wrappers, or agent-in-the-loop semantic multi-review scoring remain post-v2 design choices", maintenance)
        self.assertIn("old packets with non-current checker or inference versions remain historical compatibility evidence", maintenance)
        self.assertIn("Plan 11 closes the remaining residual labels for the v2 active model", roadmap)
        self.assertIn("Post-v2 Design Choices", roadmap)
        self.assertIn("current repository-local executable is the v2 command surface", roadmap)
        self.assertNotIn("## Open Decisions", roadmap)
        self.assertNotIn("remaining question is installation/exposure mechanics", roadmap)

    def test_post_v2_residuals_accept_replay_and_simplicity_hardening(self) -> None:
        maintenance = normalized_text()
        roadmap = normalized_file_text(ROADMAP)
        plan11 = normalized_file_text(PLAN11)

        for marker in (
            "it must replay pointer-bound command evidence",
            "targeted skips for `search_set_before` and `search_set_after` are valid",
            "Future helpers may reduce YAML editing without auto-certifying PASS",
            "future one-command wrapper can compose those primitives",
            "current multi-review v2 validation is deterministic artifact validation",
            "Implementation Iteration 5",
            "`review-template` now supports `--scratch-output`",
            "Implementation Iteration 4",
            "v2-residual-08 release-command-replay-gate",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, plan11)

        self.assertIn("Release verification must replay archived command evidence", maintenance)
        self.assertIn("release active pointer validation and explicit pointer replay rerun archived command evidence", maintenance)
        self.assertIn("v2-residual-09 search-set-trace-fidelity", roadmap)
        self.assertIn("v2-residual-10 review-template-completion-ergonomics", roadmap)
        self.assertIn("v2-residual-11 publish-wrapper-ergonomics", roadmap)
        self.assertIn("v2-residual-12 agent-in-loop-multi-review-eval", roadmap)


if __name__ == "__main__":
    unittest.main()
