from __future__ import annotations

from pathlib import Path
import importlib.util
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "trace-query.py"

spec = importlib.util.spec_from_file_location("trace_query", SCRIPT)
assert spec and spec.loader
trace_query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace_query)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TraceQueryTests(unittest.TestCase):
    def test_catalog_uses_frontmatter_metadata_without_summary_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            write(
                trace_root / "failures" / "001-typecheck-loop.md",
                """---
date: "2026-06-01"
resolved: false
tags: [typecheck, loop]
files: ["src/app.ts"]
search_set_id: "SS-001"
summary: "This narrative field must not enter catalog output."
---

## Failure
Raw typecheck loop output.
""",
            )

            records = trace_query.build_catalog(trace_root)

            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record["kind"], "failure")
            self.assertEqual(record["status"], "unresolved")
            self.assertEqual(record["tags"], ["loop", "typecheck"])
            self.assertEqual(record["files"], ["src/app.ts"])
            self.assertEqual(record["search_set_refs"], ["SS-001"])
            self.assertNotIn("summary", record)
            self.assertNotIn("lesson", record)

    def test_query_matches_catalog_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            write(
                trace_root / "evolution" / "001-typecheck-guard.md",
                """---
date: "2026-06-01"
verdict: improved
tags: [typecheck]
files_changed: ["AGENTS.md"]
---

## Change
Added typecheck guard.
""",
            )
            write(
                trace_root / "failures" / "001-login-loop.md",
                """---
date: "2026-06-01"
resolved: false
tags: [login]
---

## Failure
Login retry loop.
""",
            )

            matches = trace_query.query_records(
                trace_query.build_catalog(trace_root),
                "typecheck AGENTS",
                limit=10,
            )

            self.assertEqual(len(matches), 1)
            self.assertTrue(matches[0]["trace"].endswith("001-typecheck-guard.md"))

    def test_stored_catalog_detects_changed_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            trace = trace_root / "failures" / "001-drift.md"
            write(
                trace,
                """---
resolved: false
---

first version
""",
            )
            records = trace_query.build_catalog(trace_root)
            trace_query.write_catalog(trace_root, records)
            trace.write_text(
                """---
resolved: false
---

second version
""",
                encoding="utf-8",
            )

            errors = trace_query.stale_catalog_errors(trace_root, trace_query.read_catalog(trace_root / "trace-catalog.jsonl"))

            self.assertTrue(any("catalog stale" in error for error in errors), errors)

    def test_stored_catalog_detects_fabricated_metadata_with_same_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            trace = trace_root / "failures" / "001-drift.md"
            write(
                trace,
                """---
resolved: false
tags: [real-tag]
---

raw trace
""",
            )
            records = trace_query.build_catalog(trace_root)
            records[0]["tags"] = ["fabricated-tag"]

            errors = trace_query.stale_catalog_errors(trace_root, records)

            self.assertTrue(any("catalog stale" in error for error in errors), errors)

    def test_experiment_metadata_warning_is_best_effort(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            write(
                trace_root / "experiments" / "001-episode.md",
                """---
kind: experiment
date: "2026-06-01"
verdict: rejected
---

## Episode
Raw experiment details.
""",
            )

            warnings = trace_query.experiment_metadata_warnings(trace_root)

            self.assertTrue(any("objective" in warning for warning in warnings), warnings)

    def test_complete_experiment_metadata_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            write(
                trace_root / "experiments" / "001-episode.md",
                """---
kind: experiment
date: "2026-06-01"
objective: "reduce drift"
metric: "unit pass"
verdict: rejected
tags: [drift]
evaluator: "python3 evaluate.py"
---

## Episode
Raw experiment details.
""",
            )

            self.assertEqual(trace_query.experiment_metadata_warnings(trace_root), [])

    def test_malformed_experiment_metadata_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_root = root / ".harness" / "traces"
            write(
                trace_root / "experiments" / "001-episode.md",
                """---
kind: experiment
date: ""
objective: ""
metric: ["unit pass"]
verdict: rejected
tags: []
evaluator: 123
---

## Episode
Raw experiment details.
""",
            )

            warnings = trace_query.experiment_metadata_warnings(trace_root)

            self.assertTrue(any("date must be" in warning for warning in warnings), warnings)
            self.assertTrue(any("objective must be" in warning for warning in warnings), warnings)
            self.assertTrue(any("metric must be" in warning for warning in warnings), warnings)
            self.assertTrue(any("tags must be" in warning for warning in warnings), warnings)
            self.assertTrue(any("evaluator must be" in warning for warning in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
