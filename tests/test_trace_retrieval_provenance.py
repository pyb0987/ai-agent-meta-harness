from __future__ import annotations

from pathlib import Path
import importlib.util
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-trace-retrieval-provenance.py"

spec = importlib.util.spec_from_file_location("check_trace_retrieval_provenance", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TraceRetrievalProvenanceTests(unittest.TestCase):
    def test_selective_raw_quote_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "failures" / "001-drift.md"
            write(
                trace,
                """---
date: "2026-06-01"
resolved: false
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/failures/001-drift.md
      lines: 13
      quote: "raw drift output"
---

## Failure
raw drift output
line two
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertEqual(errors, [])

    def test_staged_reader_does_not_fall_back_to_worktree_raw_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "evolution" / "001-change.md"
            raw_ref = root / ".harness" / "traces" / "failures" / "001-drift.md"
            write(raw_ref, "worktree-only raw evidence\n")
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/failures/001-drift.md
      lines: 1
      quote: "worktree-only raw evidence"
---

## Change
""",
            )

            def staged_reader(path: Path) -> bytes:
                if path.resolve() == trace.resolve():
                    return trace.read_bytes()
                raise FileNotFoundError("not staged")

            errors = checker.validate_file(trace, repo_root=root, read_bytes=staged_reader)

            self.assertTrue(any("cannot read raw trace ref" in error for error in errors), errors)
            self.assertTrue(any("not staged" in error for error in errors), errors)

    def test_missing_retrieval_fails_when_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "evolution" / "001-change.md"
            write(
                trace,
                """---
date: "2026-06-01"
---

## Change
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("missing retrieval block" in error for error in errors), errors)

    def test_top_level_retrieval_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "evolution" / "001-change.md"
            write(
                trace,
                """---
date: "2026-06-01"
retrieval_mode: selective
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/evolution/001-change.md
      lines: 10
      quote: "raw line"
---
raw line
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("use retrieval.mode" in error for error in errors), errors)

    def test_quote_must_match_cited_line_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "failures" / "001-drift.md"
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/failures/001-drift.md
      lines: 10
      quote: "not in line"
---
actual raw line
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("quote bytes do not match" in error for error in errors), errors)

    def test_catalog_cannot_be_raw_trace_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".harness" / "traces" / "evolution" / "001-change.md"
            catalog = root / ".harness" / "traces" / "trace-catalog.jsonl"
            write(catalog, '{"trace": ".harness/traces/evolution/001-change.md"}\n')
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: selective
  raw_trace_refs:
    - file: .harness/traces/trace-catalog.jsonl
      lines: 1
      quote: "trace"
---
body
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("catalog files cannot be raw_trace_refs" in error for error in errors), errors)

    def test_full_scan_requires_reason_and_raw_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".claude" / "traces" / "evolution" / "001-change.md"
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: full_scan
---
body
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("requires a non-empty reason" in error for error in errors), errors)
            self.assertTrue(any("requires raw_trace_refs" in error for error in errors), errors)

    def test_not_needed_requires_reason_and_forbids_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".claude" / "traces" / "evolution" / "001-change.md"
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: not_needed
  raw_trace_refs:
    - file: .claude/traces/evolution/001-change.md
      lines: 9
      quote: "body"
---
body
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertTrue(any("requires a non-empty reason" in error for error in errors), errors)
            self.assertTrue(any("must not include raw_trace_refs" in error for error in errors), errors)

    def test_not_needed_with_reason_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / ".claude" / "traces" / "evolution" / "001-change.md"
            write(
                trace,
                """---
date: "2026-06-01"
retrieval:
  mode: not_needed
  reason: "Initial trace root setup; no prior trace history exists."
---
body
""",
            )

            errors = checker.validate_file(trace, repo_root=root)

            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
