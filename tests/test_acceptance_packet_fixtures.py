from __future__ import annotations

import datetime as dt
from pathlib import Path
import re
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "backlog" / "fixtures" / "acceptance-packets"
REQUIRED_FIXTURES = {
    "start.yml",
    "finalized-routine.yml",
    "finalized-harness-affecting.yml",
    "finalized-waiver-downgrade.yml",
    "blocked.yml",
    "worktree-nonstable.yml",
}
META_FIELDS = {"packet_id", "schema_version", "lifecycle", "mode", "created_at", "finalized_at"}
INPUT_FIELDS = {"intent", "actor", "source_refs", "user_judgment"}
RESULT_GROUPS = {"inference", "evidence", "judgment", "decision"}
LIFECYCLES = {"start", "finalized", "blocked"}
MODES = {"staged", "base-ref", "worktree"}
CHANGE_CLASSES = {"routine", "harness-affecting", "archive-boundary"}
IMPACTS = {"low", "high"}
ISOLATION_STATUSES = {"pending-finalize", "isolated", "isolated-but-incomplete", "exploratory-worktree"}
EVALUATOR_STATUSES = {"unchanged", "intentionally-changed", "exploratory"}
COMMAND_STATUSES = {"pass", "fail"}
PROVENANCE_FIELDS = {"actor", "role", "date", "reason", "source_ref"}
REVIEW_PROVENANCE_FIELDS = {"actor", "role", "date", "source_ref"}


class AcceptancePacketFixtureTests(unittest.TestCase):
    def fixture_packets(self) -> dict[str, dict]:
        packets: dict[str, dict] = {}
        for path in sorted(FIXTURE_ROOT.glob("*.yml")):
            packets[path.name] = yaml.safe_load(path.read_text(encoding="utf-8"))["AcceptancePacket"]
        return packets

    def test_required_fixtures_exist(self) -> None:
        existing = {path.name for path in FIXTURE_ROOT.glob("*.yml")}

        self.assertTrue(REQUIRED_FIXTURES.issubset(existing))

    def test_fixtures_keep_three_public_sections(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                self.assertEqual(set(packet), {"meta", "input", "result"})

    def test_required_schema_fields_are_locked(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                self.assertEqual(set(packet["meta"]), META_FIELDS)
                self.assertEqual(set(packet["input"]), INPUT_FIELDS)
                self.assertEqual(set(packet["result"]), RESULT_GROUPS)
                self.assertIn(packet["meta"]["lifecycle"], LIFECYCLES)
                self.assertIn(packet["meta"]["mode"], MODES)
                self.assertIsInstance(packet["meta"]["packet_id"], str)
                self.assertIsInstance(packet["meta"]["schema_version"], str)
                self.assertIsInstance(packet["input"]["intent"], str)
                self.assertIsInstance(packet["input"]["actor"], str)
                self.assertIsInstance(packet["input"]["source_refs"], list)
                self.assertIsInstance(packet["input"]["user_judgment"], dict)
                self.assert_packet_date(packet["meta"]["created_at"])
                if packet["meta"]["finalized_at"] is not None:
                    self.assert_packet_date(packet["meta"]["finalized_at"])

    def test_result_groups_are_present(self) -> None:
        for path in sorted(FIXTURE_ROOT.glob("*.yml")):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for group in ("inference", "evidence", "judgment", "decision"):
                    self.assertIsNotNone(re.search(rf"^    {group}:$", text, flags=re.MULTILINE), path.name)

    def test_required_evidence_has_result_or_skip_record(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                result = packet["result"]
                required = set(result["inference"].get("required_evidence", []))
                recorded = {entry.get("command") for entry in result["evidence"].get("command_results", [])}
                skipped = {entry.get("evidence") for entry in result["evidence"].get("skipped", [])}
                self.assertTrue(required.issubset(recorded | skipped), name)

    def test_stable_packets_have_passing_required_evidence(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                if not packet["result"]["decision"]["stable_handoff_eligible"]:
                    continue
                result = packet["result"]
                required = set(result["inference"].get("required_evidence", []))
                passed = {
                    entry.get("command")
                    for entry in result["evidence"].get("command_results", [])
                    if entry.get("status") == "pass"
                }
                skipped = {entry.get("evidence") for entry in result["evidence"].get("skipped", [])}
                self.assertTrue(required.issubset(passed), name)
                self.assertFalse(required & skipped, name)

    def test_confounder_isolation_fields_are_present(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                inference = packet["result"]["inference"]
                for field in ("intended_scope", "actual_scope", "deviations", "isolation"):
                    self.assertIn(field, inference)
                self.assertIn(inference["isolation"], ISOLATION_STATUSES)
                if inference.get("change_class"):
                    self.assertIn(inference["change_class"], CHANGE_CLASSES)
                if inference.get("impact"):
                    self.assertIn(inference["impact"], IMPACTS)

    def test_nested_evidence_enums_are_locked(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                evidence = packet["result"]["evidence"]
                if "evaluator_boundary" in evidence:
                    self.assertIn(evidence["evaluator_boundary"]["status"], EVALUATOR_STATUSES)
                for entry in evidence.get("command_results", []):
                    self.assertIn(entry["status"], COMMAND_STATUSES)
                    self.assertIsInstance(entry["artifact_ref"], str)
                for source_ref in evidence.get("source_refs", []):
                    self.assertIsInstance(source_ref, str)

    def test_accepted_harness_affecting_fixture_models_trace_reuse(self) -> None:
        packet = self.fixture_packets()["finalized-harness-affecting.yml"]
        trace_refs = packet["result"]["evidence"]["trace_refs"]

        self.assertTrue(trace_refs["search_set_before"])
        self.assertTrue(trace_refs["search_set_after"])
        self.assertTrue(trace_refs["evolution"])

    def test_residual_risk_records_judgment_provenance(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                residual = packet["result"]["judgment"]["residual_risk"]
                for entry in residual:
                    for field in ("actor", "role", "date", "reason", "source_ref"):
                        self.assertIn(field, entry)

    def test_lifecycle_examples_cover_start_finalized_and_blocked(self) -> None:
        lifecycles = {
            match.group(1)
            for path in FIXTURE_ROOT.glob("*.yml")
            for match in re.finditer(r"^    lifecycle: ([a-z-]+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
        }

        self.assertEqual(lifecycles, {"start", "finalized", "blocked"})

    def test_lifecycle_decision_invariants(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                meta = packet["meta"]
                decision = packet["result"]["decision"]
                reviews = packet["result"]["judgment"].get("reviews", [])
                has_veto = any(review.get("veto") is True for review in reviews)
                if meta["lifecycle"] == "start":
                    self.assertIsNone(decision["accepted"])
                    self.assertFalse(decision["stable_handoff_eligible"])
                if meta["lifecycle"] == "blocked":
                    self.assertFalse(decision["accepted"])
                    self.assertFalse(decision["stable_handoff_eligible"])
                if meta["mode"] == "worktree":
                    self.assertFalse(decision["stable_handoff_eligible"])
                if decision["stable_handoff_eligible"]:
                    self.assertTrue(decision["accepted"])
                    self.assertFalse(has_veto)

    def test_required_review_is_closed_for_stable_packets(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                decision = packet["result"]["decision"]
                if not decision["stable_handoff_eligible"]:
                    continue
                required = set(packet["result"]["inference"].get("required_review", []))
                reviewed = {review.get("critic") for review in packet["result"]["judgment"].get("reviews", [])}
                waived = {
                    waiver.get("review")
                    for waiver in packet["result"]["judgment"].get("waivers", [])
                    if waiver.get("review")
                }
                downgraded = {
                    downgrade.get("from")
                    for downgrade in packet["result"]["judgment"].get("downgrades", [])
                    if downgrade.get("from")
                }
                self.assertTrue(required.issubset(reviewed | waived | downgraded), name)

    def test_waivers_and_downgrades_target_required_items(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                result = packet["result"]
                required_evidence = set(result["inference"].get("required_evidence", []))
                required_review = set(result["inference"].get("required_review", []))
                for waiver in result["judgment"].get("waivers", []):
                    target_fields = [field for field in ("evidence", "review") if waiver.get(field)]
                    self.assertEqual(1, len(target_fields), name)
                    target_field = target_fields[0]
                    if target_field == "evidence":
                        self.assertIn(waiver["evidence"], required_evidence, name)
                    else:
                        self.assertIn(waiver["review"], required_review, name)
                for downgrade in result["judgment"].get("downgrades", []):
                    self.assertIn(downgrade.get("kind"), {"evidence", "review"}, name)
                    if downgrade["kind"] == "evidence":
                        self.assertIn(downgrade.get("from"), required_evidence, name)
                    else:
                        self.assertIn(downgrade.get("from"), required_review, name)

    def test_input_exception_requests_target_required_items(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                required_evidence = set(packet["result"]["inference"].get("required_evidence", []))
                required_review = set(packet["result"]["inference"].get("required_review", []))
                user_judgment = packet["input"].get("user_judgment", {})
                for key, request in user_judgment.items():
                    if "waiver" not in key and "downgrade" not in key:
                        continue
                    target_fields = [field for field in ("evidence", "review", "from") if request.get(field)]
                    self.assertEqual(1, len(target_fields), name)
                    target_field = target_fields[0]
                    if target_field == "evidence":
                        self.assertIn(request["evidence"], required_evidence, name)
                    elif target_field == "review":
                        self.assertIn(request["review"], required_review, name)
                    else:
                        self.assertIn(request.get("kind"), {"evidence", "review"}, name)
                        if request["kind"] == "evidence":
                            self.assertIn(request["from"], required_evidence, name)
                        else:
                            self.assertIn(request["from"], required_review, name)

    def test_stable_review_scores_are_accepted_with_score_9_disposition(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                if not packet["result"]["decision"]["stable_handoff_eligible"]:
                    continue
                for review in packet["result"]["judgment"].get("reviews", []):
                    self.assertGreaterEqual(review.get("score", 0), 9, name)
                    self.assertIs(review.get("veto"), False, name)
                    if review.get("score") == 9:
                        self.assertIn("why_not_10", review, name)
                        self.assertIn("disposition", review, name)
                        self.assertTrue(review["why_not_10"], name)
                        self.assertTrue(review["disposition"], name)

    def test_stable_reviewed_packets_use_structured_review_imports(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                if not packet["result"]["decision"]["stable_handoff_eligible"]:
                    continue
                reviews = packet["result"]["judgment"].get("reviews", [])
                if not reviews:
                    continue
                imports = packet["result"]["evidence"].get("review_imports", [])
                self.assertTrue(imports, name)
                imported_refs = {item.get("source_ref") for item in imports}
                for item in imports:
                    self.assertEqual("acceptance-packet-review-import/v1", item.get("format"), name)
                    self.assertEqual("imported", item.get("status"), name)
                    self.assertIn("target_binding", item, name)
                for review in reviews:
                    self.assertIn(review.get("source_ref"), imported_refs, name)

    def test_fixtures_are_documented_as_non_active_packets(self) -> None:
        readme = (FIXTURE_ROOT / "README.md").read_text(encoding="utf-8")
        plan = (ROOT / "backlog" / "plans" / "02-acceptance-packet-schema-and-fixtures.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("not active governance\npackets", readme)
        self.assertIn("do not satisfy stable handoff", readme)
        self.assertIn("not active packets", plan)
        self.assertIn("do not satisfy stable handoff", plan)

    def test_waiver_fixture_records_judgment_provenance(self) -> None:
        text = (FIXTURE_ROOT / "finalized-waiver-downgrade.yml").read_text(encoding="utf-8")

        for field in ("actor:", "role:", "date:", "reason:", "source_ref:"):
            self.assertIn(field, text)

    def test_judgment_and_skipped_evidence_records_have_provenance(self) -> None:
        for name, packet in self.fixture_packets().items():
            with self.subTest(path=name):
                judgment = packet["result"]["judgment"]
                for collection in ("waivers", "downgrades", "residual_risk"):
                    for entry in judgment.get(collection, []):
                        self.assertTrue(PROVENANCE_FIELDS.issubset(entry), f"{name}:{collection}")
                        self.assert_packet_date(entry["date"])
                for review in judgment.get("reviews", []):
                    self.assertTrue(REVIEW_PROVENANCE_FIELDS.issubset(review), f"{name}:reviews")
                    self.assert_packet_date(review["date"])
                for skipped in packet["result"]["evidence"].get("skipped", []):
                    self.assertTrue(PROVENANCE_FIELDS.issubset(skipped), f"{name}:skipped")
                    self.assert_packet_date(skipped["date"])

    def assert_packet_date(self, value: object) -> None:
        if isinstance(value, dt.date):
            return
        if isinstance(value, str):
            dt.date.fromisoformat(value)
            return
        self.fail(f"invalid packet date value: {value!r}")


if __name__ == "__main__":
    unittest.main()
