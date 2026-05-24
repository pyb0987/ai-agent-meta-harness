from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections.abc import Callable
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "strategy-search.py"


def load_strategy_search():
    spec = importlib.util.spec_from_file_location("strategy_search", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def run_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), "--root", str(root), *args],
        cwd=root,
        encoding="utf-8",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StrategySearchCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.strategy = load_strategy_search()
        self._init_repo()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _init_repo(self) -> None:
        (self.root / "src").mkdir(parents=True)
        (self.root / "src" / "prompt.md").write_text("old prompt\n", encoding="utf-8")
        (self.root / "benchmarks" / "init-codex-harness" / "expected").mkdir(parents=True)
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.97')\nprint('case: fresh-empty-repo: pass')\n",
            encoding="utf-8",
        )
        (self.root / "benchmarks" / "init-codex-harness" / "expected" / "output.txt").write_text(
            "expected\n",
            encoding="utf-8",
        )
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "score-init-codex-harness.py").write_text(
            "print('score')\n",
            encoding="utf-8",
        )
        git(self.root, "init")
        git(self.root, "config", "user.name", "Test")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "initial")
        self.base_commit = git(self.root, "rev-parse", "HEAD")

    def direction(self) -> dict:
        return {
            "schema_version": "strategy-search-direction/v1",
            "direction_id": "init-codex-harness-trace-root",
            "objective": "Improve trace-root selection in generated Codex harness projects.",
            "base_ref": self.base_commit,
            "search_surface": ["src/prompt.md"],
            "protected_evaluator_paths": ["benchmarks/init-codex-harness/run_cases.py"],
            "evaluator": {
                "command": "python3 benchmarks/init-codex-harness/run_cases.py",
                "timeout_seconds": 120,
                "protected_paths": [
                    "benchmarks/init-codex-harness/run_cases.py",
                    "scripts/score-init-codex-harness.py",
                ],
                "oracle_paths": ["benchmarks/init-codex-harness/expected/"],
                "score_parser_paths": ["scripts/score-init-codex-harness.py"],
            },
            "success": {"min_score": 0.95, "max_regressions": 0},
            "notes": [],
        }

    def write_direction(self, direction: dict | None = None) -> Path:
        direction = direction or self.direction()
        path = self.root / "direction.yml"
        path.write_text(yaml.safe_dump(direction, sort_keys=False), encoding="utf-8")
        return path

    def write_patch(self, text: str | None = None) -> Path:
        path = self.root / "candidate.diff"
        path.write_text(
            text
            or "\n".join(
                [
                    "diff --git a/src/prompt.md b/src/prompt.md",
                    "index 1111111..2222222 100644",
                    "--- a/src/prompt.md",
                    "+++ b/src/prompt.md",
                    "@@ -1 +1 @@",
                    "-old prompt",
                    "+better prompt",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path

    def write_candidate(
        self,
        *,
        direction: dict | None = None,
        patch_text: str | None = None,
        mutate: Callable[[dict], None] | None = None,
    ) -> Path:
        direction = direction or self.direction()
        candidate_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001"
        candidate_dir.mkdir(parents=True)
        patch = candidate_dir / "patch.diff"
        patch.write_text(
            patch_text
            or "\n".join(
                [
                    "diff --git a/src/prompt.md b/src/prompt.md",
                    "index 1111111..2222222 100644",
                    "--- a/src/prompt.md",
                    "+++ b/src/prompt.md",
                    "@@ -1 +1 @@",
                    "-old prompt",
                    "+better prompt",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        stdout = candidate_dir / "stdout.log"
        stderr = candidate_dir / "stderr.log"
        stdout.write_text("score: 0.97\ncase: fresh-empty-repo: pass\n", encoding="utf-8")
        stderr.write_text("", encoding="utf-8")
        trace = self.strategy.candidate_trace_record(
            direction=direction,
            run_id="run-001",
            candidate_id="cand-001",
            base_commit=self.base_commit,
            patch_path=patch,
            stdout_path=stdout,
            stderr_path=stderr,
            verdict="pass",
            score=0.97,
            exit_code=0,
            case_results=[{"case_id": "fresh-empty-repo", "status": "pass"}],
            timed_out=False,
            why="manual test candidate",
            next_hypothesis="prepare for adoption",
            created_at="2026-05-19T00:00:01Z",
        )
        trace_path = self.strategy.write_candidate_trace(candidate_dir, trace)
        closure = self.strategy.closure_digest_record(self.root, direction)
        candidate = {
            "schema_version": "strategy-search-candidate/v1",
            "candidate_id": "cand-001",
            "run_id": "run-001",
            "base_commit": self.base_commit,
            "direction_digest": self.strategy.digest_direction(direction),
            "search_surface_digest_before": self.strategy.digest_paths(self.root, direction["search_surface"]),
            "patch_sha256": file_sha256(patch),
            "evaluator_command": direction["evaluator"]["command"],
            "evaluator_digest": self.strategy.evaluator_digest(self.root, direction),
            "evaluator_closure": closure,
            "started_at": "2026-05-19T00:00:00Z",
            "finished_at": "2026-05-19T00:00:01Z",
            "exit_code": 0,
            "score": 0.97,
            "case_results": [{"case_id": "fresh-empty-repo", "status": "pass"}],
            "stdout_sha256": file_sha256(stdout),
            "stderr_sha256": file_sha256(stderr),
            "trace_sha256": file_sha256(trace_path),
            "verdict": "pass",
        }
        if mutate is not None:
            mutate(candidate)
        score = candidate_dir / "score.yml"
        score.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")
        return score

    def test_validate_direction_accepts_complete_schema(self) -> None:
        direction_path = self.write_direction()
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("VALID direction", completed.stdout)
        self.assertIn("direction_digest:", completed.stdout)

    def test_validate_direction_rejects_search_surface_overlap_with_evaluator(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["benchmarks/init-codex-harness/"]
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("search_surface must not overlap evaluator closure", completed.stderr)

    def test_validate_direction_requires_shorthand_inside_explicit_closure(self) -> None:
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/"]
        direction["evaluator"]["protected_paths"] = ["scripts/score-init-codex-harness.py"]
        direction["evaluator"]["oracle_paths"] = ["scripts/score-init-codex-harness.py"]
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("protected_evaluator_paths must be represented", completed.stderr)

    def test_validate_direction_rejects_undercovered_protected_shorthand(self) -> None:
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["benchmarks/"]
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("protected_evaluator_paths must be represented", completed.stderr)

    def test_validate_direction_rejects_mutable_base_ref(self) -> None:
        direction = self.direction()
        direction["base_ref"] = git(self.root, "rev-parse", "--abbrev-ref", "HEAD")
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("base_ref must be a full commit SHA", completed.stderr)

    def test_validate_direction_requires_evaluator_command_in_closure(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "python3 src/prompt.md"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator.command path must be represented", completed.stderr)

    def test_validate_direction_checks_option_valued_command_paths(self) -> None:
        (self.root / "docs" / "gold.yml").parent.mkdir(exist_ok=True)
        (self.root / "docs" / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["command"] = (
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=docs/gold.yml"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator.command path must be represented", completed.stderr)

    def test_validate_direction_checks_root_option_valued_command_paths(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("gold.yml")
        direction["evaluator"]["command"] = (
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator.command path must be represented", completed.stderr)

    def test_validate_direction_rejects_post_target_assignment_decoy(self) -> None:
        (self.root / "gold").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add extensionless gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("gold")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py gold=oracle"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("equals-style decoration", completed.stderr)

    def test_validate_direction_checks_attached_and_decorated_option_paths(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        (self.root / "hidden.yml").write_text("hidden\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command in (
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml:oracle",
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml,oracle",
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml@oracle",
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml=oracle",
            "python3 benchmarks/init-codex-harness/run_cases.py --inputs=gold.yml,hidden.yml",
            "python3 benchmarks/init-codex-harness/run_cases.py gold.yml::case",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["search_surface"].append("gold.yml")
                direction["search_surface"].append("hidden.yml")
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                if "," in command:
                    self.assertIn("comma-style decoration", completed.stderr)
                elif "@" in command:
                    self.assertIn("at-style decoration", completed.stderr)
                elif "gold.yml=" in command:
                    self.assertIn("equals-style decoration", completed.stderr)
                elif ":" in command:
                    self.assertIn("colon-style decoration", completed.stderr)
                else:
                    self.assertIn("evaluator.command path must be represented", completed.stderr)

    def test_validate_direction_rejects_decorated_option_path_even_when_closed(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = (
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml:oracle"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("colon-style decoration", completed.stderr)

    def test_validate_direction_rejects_path_valued_short_options(self) -> None:
        for option in ("-qggold.yml", "-g=gold.yml", "-1gold.yml"):
            with self.subTest(option=option):
                direction = self.direction()
                direction["evaluator"]["command"] = f"python3 benchmarks/init-codex-harness/run_cases.py {option}"
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("path-valued short options are not supported", completed.stderr)

    def test_validate_direction_rejects_split_path_valued_short_options(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py -g gold.yml"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("separated path-valued options are not supported", completed.stderr)

    def test_validate_direction_rejects_existing_dash_cluster_decoys(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        (self.root / "-qggold.yml").write_text("decoy\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add gold and dash decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("gold.yml")
        direction["evaluator"]["protected_paths"].append("-qggold.yml")
        direction["evaluator"]["oracle_paths"].append("-qggold.yml")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py -qggold.yml"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("dash-leading paths must be passed after '--'", completed.stderr)

    def test_validate_direction_rejects_existing_two_character_dash_path(self) -> None:
        (self.root / "-x").write_text("dash path\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add short dash path")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("-x")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py -g -x"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("separated path-valued options are not supported", completed.stderr)

    def test_validate_direction_allows_positional_paths_after_flags(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command in (
            "python3 -q benchmarks/init-codex-harness/run_cases.py",
            "python3 --quiet benchmarks/init-codex-harness/run_cases.py",
            "python3 benchmarks/init-codex-harness/run_cases.py -- gold.yml",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["evaluator"]["protected_paths"].append("gold.yml")
                direction["evaluator"]["oracle_paths"].append("gold.yml")
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_validate_direction_tracks_dash_leading_repo_path_tokens(self) -> None:
        (self.root / "--gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add dash-leading gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("--gold.yml")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py --gold --gold.yml"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("separated path-valued options are not supported", completed.stderr)

    def test_validate_direction_tracks_single_dash_repo_path_tokens(self) -> None:
        (self.root / "-case.py").write_text("print('score: 1')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add dash-leading case file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("-case.py")
        direction["evaluator"]["command"] = "python3 -case.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("dash-leading paths must be passed after '--'", completed.stderr)

    def test_validate_direction_honors_option_terminator_for_inline_guard(self) -> None:
        (self.root / "-case.py").write_text("print('score: 1')\nprint('case: fresh-empty-repo: pass')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add dash-leading evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["-case.py"]
        direction["evaluator"]["protected_paths"] = ["-case.py"]
        direction["evaluator"]["score_parser_paths"] = ["-case.py"]
        direction["evaluator"]["command"] = "python3 -- -case.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_validate_direction_rejects_repeated_option_terminator_target_decoy(self) -> None:
        (self.root / "--").write_text("print('score: 1')\n", encoding="utf-8")
        (self.root / "eval.py").write_text("print('score: 1')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add terminator decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("--")
        direction["protected_evaluator_paths"] = ["eval.py"]
        direction["evaluator"]["protected_paths"] = ["eval.py"]
        direction["evaluator"]["score_parser_paths"] = ["eval.py"]
        direction["evaluator"]["command"] = "python3 -- -- eval.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_repeated_post_target_option_terminator(self) -> None:
        (self.root / "--").write_text("operand\n", encoding="utf-8")
        (self.root / "eval.py").write_text("print('score: 1')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add repeated terminator fixture")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command, expected in (
            ("python3 eval.py -- --", "repeated option terminators are not supported"),
            ("python3 eval.py -g --", "separated path-valued options are not supported"),
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["protected_evaluator_paths"] = ["eval.py"]
                direction["evaluator"]["protected_paths"] = ["eval.py"]
                direction["evaluator"]["score_parser_paths"] = ["eval.py"]
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected, completed.stderr)

    def test_validate_direction_rejects_ambiguous_single_dash_repo_path_even_when_closed(self) -> None:
        (self.root / "-case.py").write_text("print('score: 1')\nprint('case: fresh-empty-repo: pass')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add dash-leading evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["-case.py"]
        direction["evaluator"]["protected_paths"] = ["-case.py"]
        direction["evaluator"]["score_parser_paths"] = ["-case.py"]
        direction["evaluator"]["command"] = "python3 -case.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("dash-leading paths must be passed after '--'", completed.stderr)

    def test_validate_direction_rejects_pathspec_magic_paths(self) -> None:
        direction = self.direction()
        direction["evaluator"]["protected_paths"].append(":(literal)gold.yml")
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not git pathspec magic", completed.stderr)

    def test_validate_direction_rejects_query_decorated_paths(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml?oracle"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("query-style decoration", completed.stderr)

    def test_validate_direction_rejects_fragment_decorated_paths(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml#oracle"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("fragment-style decoration", completed.stderr)

    def test_validate_direction_canonicalizes_decorated_root_option_decoys(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        decoy = self.root / "gold.yml:oracle" / "test.py::case"
        decoy.parent.mkdir()
        decoy.write_text("decoy\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add gold and decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("gold.yml")
        direction["evaluator"]["protected_paths"].append("gold.yml:oracle/test.py::case")
        direction["evaluator"]["oracle_paths"].append("gold.yml:oracle/test.py::case")
        direction["evaluator"]["command"] = (
            "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml:oracle/test.py::case"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("colon-style decoration", completed.stderr)

    def test_validate_direction_rejects_exact_colon_path_decoys(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        (self.root / "gold.yml:oracle").write_text("decorated\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add exact colon decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("gold.yml:oracle")
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/run_cases.py --gold=gold.yml:oracle"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("colon-style decoration", completed.stderr)

    def test_validate_direction_rejects_inline_command_closure_bypass(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = (
            "node -e \"console.log('score: 1')\" "
            "benchmarks/init-codex-harness/run_cases.py"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_attached_inline_command_flag(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = (
            "python3 -c\"exec(open('src/prompt.md').read())\" "
            "benchmarks/init-codex-harness/run_cases.py"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_wrapper_inline_code_after_option_terminator(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = (
            "env -- python3 -c \"print('score: 1')\" "
            "benchmarks/init-codex-harness/run_cases.py"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_env_split_string_inline_code(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = (
            "env -S 'python3 -c \"print(1)\"' "
            "benchmarks/init-codex-harness/run_cases.py"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_env_options(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "env --chdir=.. python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("env options are not supported", completed.stderr)

    def test_validate_direction_rejects_repo_local_env_wrapper(self) -> None:
        (self.root / "env").write_text("#!/bin/sh\nexec \"$@\"\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add env shim")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("env")
        direction["evaluator"]["protected_paths"].append("env")
        direction["evaluator"]["command"] = "./env FOO=bar python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_keeps_env_terminator_separate_from_script_args(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add root gold file")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("gold.yml")
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = (
            "env -- python3 benchmarks/init-codex-harness/run_cases.py -g gold.yml"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("separated path-valued options are not supported", completed.stderr)

    def test_validate_direction_rejects_python_pre_target_option_operands(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "python3 -W ignore benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_node_print_inline_eval(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "node -p '1' benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_direct_evaluator_path_without_runtime(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_repo_local_runtime_alias(self) -> None:
        (self.root / "python3").write_text("#!/bin/sh\nexec /usr/bin/python3 \"$@\"\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add runtime alias")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("python3")
        direction["evaluator"]["protected_paths"].append("python3")
        direction["evaluator"]["command"] = "./python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_python_runtime_alias(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "python benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_missing_path_shaped_evaluator_target(self) -> None:
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["benchmarks/"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/"]
        direction["evaluator"]["command"] = "python3 benchmarks/missing.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_directory_evaluator_target(self) -> None:
        evalpkg = self.root / "benchmarks" / "init-codex-harness" / "evalpkg"
        evalpkg.mkdir()
        (evalpkg / "__main__.py").write_text("print('score: 0.97')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add evaluator package directory")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/evalpkg/"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/evalpkg/"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/evalpkg/"]
        direction["evaluator"]["command"] = "python3 benchmarks/init-codex-harness/evalpkg"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_tracks_env_assignment_path_dependencies(self) -> None:
        (self.root / "cases").write_text("case fixture\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add extensionless evaluator input")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"].append("cases")
        direction["evaluator"]["command"] = "env CASES=cases python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator.command path must be represented", completed.stderr)

    def test_validate_direction_allows_closed_env_assignment_path_dependency(self) -> None:
        (self.root / "gold.yml").write_text("gold\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add evaluator assignment input")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"].append("gold.yml")
        direction["evaluator"]["command"] = "env GOLD=gold.yml python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_validate_direction_rejects_stdin_pseudo_target_before_repo_arg(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add js evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command in (
            "python3 - benchmarks/init-codex-harness/run_cases.py",
            "node - benchmarks/init-codex-harness/run_cases.js",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_shell_stdin_mode_before_repo_arg(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.sh").write_text(
            "printf 'score: 0.97\\n'\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add shell evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/run_cases.sh"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/run_cases.sh"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/run_cases.sh"]
        direction["evaluator"]["command"] = "sh -s benchmarks/init-codex-harness/run_cases.sh"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_nonpath_script_operand_before_repo_arg(self) -> None:
        for command in (
            "python3 runner benchmarks/init-codex-harness/run_cases.py",
            "python3 -- - benchmarks/init-codex-harness/run_cases.py",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_evaluator_env_scrubs_runtime_hook_variables(self) -> None:
        original = os.environ.copy()
        try:
            os.environ["PYTHONPATH"] = "src"
            os.environ["NODE_OPTIONS"] = "--require ./src/hook.js"
            os.environ["NODE_PATH"] = "src"
            os.environ["BASH_ENV"] = "src/hook.sh"
            os.environ["GIT_DIR"] = ".git"
            os.environ["PATH"] = os.pathsep.join(["src", str(self.root / "src"), "/usr/bin", "/bin"])
            env = self.strategy.evaluator_env(self.root)
        finally:
            os.environ.clear()
            os.environ.update(original)
        for key in ("PYTHONPATH", "NODE_OPTIONS", "NODE_PATH", "BASH_ENV", "GIT_DIR"):
            self.assertNotIn(key, env)
        path_entries = env["PATH"].split(os.pathsep)
        self.assertNotIn("src", path_entries)
        self.assertNotIn(str(self.root / "src"), path_entries)
        self.assertIn("/usr/bin", path_entries)
        self.assertEqual(env["STRATEGY_SEARCH_WORKSPACE"], str(self.root))

    def test_evaluator_env_scrubs_source_repo_path_entries_for_temp_workspace(self) -> None:
        original = os.environ.copy()
        try:
            workspace = Path(self.tmp.name) / "workspace"
            workspace.mkdir()
            source_link = self.root / "source-bin"
            workspace_link = workspace / "workspace-bin"
            source_link.symlink_to("/usr/bin", target_is_directory=True)
            workspace_link.symlink_to("/usr/bin", target_is_directory=True)
            os.environ["PATH"] = os.pathsep.join(
                [str(self.root / "src"), str(source_link), str(workspace / "bin"), str(workspace_link), "/usr/bin"]
            )
            env = self.strategy.evaluator_env(workspace, source_root=self.root)
        finally:
            os.environ.clear()
            os.environ.update(original)
        path_entries = env["PATH"].split(os.pathsep)
        self.assertNotIn(str(self.root / "src"), path_entries)
        self.assertNotIn(str(self.root / "source-bin"), path_entries)
        self.assertNotIn(str(workspace / "bin"), path_entries)
        self.assertNotIn(str(workspace / "workspace-bin"), path_entries)
        self.assertIn("/usr/bin", path_entries)

    def test_validate_direction_rejects_node_bare_preload_specifier(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        (self.root / "hook").write_text("module.exports = {}\n", encoding="utf-8")
        (self.root / "node_modules" / "hook").mkdir(parents=True)
        (self.root / "node_modules" / "hook" / "index.js").write_text("module.exports = {}\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add js evaluator and hook module")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["search_surface"] = ["node_modules/hook/"]
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/run_cases.js", "hook"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/run_cases.js", "hook"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["oracle_paths"] = ["benchmarks/init-codex-harness/expected/output.txt"]
        direction["evaluator"]["command"] = "node --require hook benchmarks/init-codex-harness/run_cases.js"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_explicit_node_preload_path(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        (self.root / "setup.js").write_text("module.exports = {}\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add explicit js preload")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/run_cases.js", "setup.js"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/run_cases.js", "setup.js"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["command"] = "node --require ./setup.js benchmarks/init-codex-harness/run_cases.js"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_nodejs_runtime_alias(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add js evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["command"] = "nodejs benchmarks/init-codex-harness/run_cases.js"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_rejects_explicit_runtime_hook_env_assignment(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add js evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["protected_evaluator_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["protected_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["score_parser_paths"] = ["benchmarks/init-codex-harness/run_cases.js"]
        direction["evaluator"]["command"] = (
            "env NODE_OPTIONS=--require=hook node benchmarks/init-codex-harness/run_cases.js"
        )
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not set runtime hook environment variable: NODE_OPTIONS", completed.stderr)

    def test_validate_direction_rejects_explicit_path_env_assignment(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "env PATH=src python3 benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not set runtime hook environment variable: PATH", completed.stderr)

    def test_validate_direction_rejects_explicit_loader_env_assignment(self) -> None:
        (self.root / "hook.so").write_text("loader hook\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add loader hook")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for env_key in ("LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH"):
            with self.subTest(env_key=env_key):
                direction = self.direction()
                direction["evaluator"]["protected_paths"].append("hook.so")
                direction["evaluator"]["oracle_paths"].append("hook.so")
                direction["evaluator"]["command"] = (
                    f"env {env_key}=./hook.so python3 benchmarks/init-codex-harness/run_cases.py"
                )
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(f"must not set runtime hook environment variable: {env_key}", completed.stderr)

    def test_validate_direction_rejects_runtime_option_operand_inline_eval(self) -> None:
        (self.root / "setup.js").write_text("module.exports = {}\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add setup preload")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command in (
            "node --require setup.js -e 'console.log(\"score:1\")' benchmarks/init-codex-harness/run_cases.js",
            "node --require benchmarks/init-codex-harness/run_cases.js -e 'console.log(\"score:1\")'",
            "python3 -W benchmarks/init-codex-harness/run_cases.py -c \"print('score:1')\"",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["evaluator"]["command"] = command
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_inline_hidden_behind_runtime_option_operand(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.sh").write_text(
            "printf 'score: 0.97\\n'\n",
            encoding="utf-8",
        )
        (self.root / "setup.js").write_text("module.exports = {}\n", encoding="utf-8")
        (self.root / "bashrc").write_text(":\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add runtime operand decoys")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command in (
            "node --conditions ./setup.js -e 'console.log(\"score:1\")' benchmarks/init-codex-harness/run_cases.js",
            "bash --init-file bashrc -c 'printf ok' benchmarks/init-codex-harness/run_cases.sh",
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["base_ref"] = self.base_commit
                direction["evaluator"]["command"] = command
                direction["protected_evaluator_paths"] = [
                    "benchmarks/init-codex-harness/run_cases.py",
                    "benchmarks/init-codex-harness/run_cases.js",
                    "benchmarks/init-codex-harness/run_cases.sh",
                    "setup.js",
                    "bashrc",
                ]
                direction["evaluator"]["protected_paths"] = list(direction["protected_evaluator_paths"])
                direction["evaluator"]["score_parser_paths"] = list(direction["protected_evaluator_paths"])
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_awk_inline_evaluator(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "awk 'BEGIN { print \"score: 1\" }' benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must execute a repository-local evaluator file via a supported runtime", completed.stderr)

    def test_validate_direction_allows_evaluator_script_arguments_named_like_inline_flags(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.js").write_text(
            "console.log('score: 0.97')\n",
            encoding="utf-8",
        )
        (self.root / "cases.yml").write_text("cases: []\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add evaluator args")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        for command, path in (
            ("node benchmarks/init-codex-harness/run_cases.js --print=summary", "benchmarks/init-codex-harness/run_cases.js"),
            ("node benchmarks/init-codex-harness/run_cases.js -- -p", "benchmarks/init-codex-harness/run_cases.js"),
            ("python3 benchmarks/init-codex-harness/run_cases.py --command=cases.yml", "cases.yml"),
            ("python3 benchmarks/init-codex-harness/run_cases.py -m smoke", "benchmarks/init-codex-harness/run_cases.py"),
        ):
            with self.subTest(command=command):
                direction = self.direction()
                direction["evaluator"]["command"] = command
                if path.endswith(".js"):
                    direction["protected_evaluator_paths"] = [path]
                    direction["evaluator"]["protected_paths"] = [path]
                    direction["evaluator"]["score_parser_paths"] = [path]
                if path == "cases.yml":
                    direction["evaluator"]["oracle_paths"].append("cases.yml")
                direction_path = self.write_direction(direction)
                completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_validate_direction_rejects_dash_leading_inline_decoy(self) -> None:
        (self.root / "-cprint").write_text("decoy\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add inline flag decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("-cprint")
        direction["evaluator"]["protected_paths"].append("-cprint")
        direction["evaluator"]["command"] = "python3 -cprint benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_wrapper_inline_decoy_after_terminator(self) -> None:
        (self.root / "-cprint").write_text("decoy\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add inline flag decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("-cprint")
        direction["evaluator"]["protected_paths"].append("-cprint")
        direction["evaluator"]["command"] = "env -- python3 -cprint benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("not inline/module code", completed.stderr)

    def test_validate_direction_rejects_wrapper_dash_path_after_terminator(self) -> None:
        (self.root / "-x.py").write_text("print('score: 1')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add dash evaluator decoy")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["protected_evaluator_paths"].append("-x.py")
        direction["evaluator"]["protected_paths"].append("-x.py")
        direction["evaluator"]["command"] = "env -- python3 -x.py benchmarks/init-codex-harness/run_cases.py"
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("dash-leading paths must be passed after '--'", completed.stderr)

    def test_validate_direction_rejects_publication_command(self) -> None:
        direction = self.direction()
        direction["evaluator"]["command"] = "python3 scripts/check-governance-acceptance.py publish"
        direction["evaluator"]["protected_paths"].append("scripts/check-governance-acceptance.py")
        (self.root / "scripts" / "check-governance-acceptance.py").write_text("print('bad')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add release script")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction["base_ref"] = self.base_commit
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not run governance publication", completed.stderr)

    def test_validate_candidate_accepts_replay_identity(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("VALID candidate", completed.stdout)

    def test_validate_candidate_rejects_symlinked_sidecars(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        candidate_dir = score_path.parent
        external_stdout = self.root / "archive" / "v2" / "external-stdout.log"
        external_stdout.parent.mkdir(parents=True)
        external_stdout.write_bytes((candidate_dir / "stdout.log").read_bytes())
        (candidate_dir / "stdout.log").unlink()
        (candidate_dir / "stdout.log").symlink_to(os.path.relpath(external_stdout, candidate_dir))
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("stdout", completed.stderr)
        self.assertIn("symlink", completed.stderr)

    def test_validate_candidate_rejects_hard_linked_sidecars(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        candidate_dir = score_path.parent
        external_stdout = self.root / "archive" / "v2" / "external-stdout.log"
        external_stdout.parent.mkdir(parents=True)
        external_stdout.write_bytes((candidate_dir / "stdout.log").read_bytes())
        (candidate_dir / "stdout.log").unlink()
        os.link(external_stdout, candidate_dir / "stdout.log")
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate stdout must not be hard-linked", completed.stderr)

    def test_validate_candidate_rejects_linked_score_before_loading(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        archive_score = self.root / "archive" / "v2" / "score.yml"
        archive_score.parent.mkdir(parents=True)
        archive_score.write_bytes(score_path.read_bytes())
        score_path.unlink()
        score_path.symlink_to(os.path.relpath(archive_score, score_path.parent))
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("score", completed.stderr)
        self.assertIn("symlink", completed.stderr)

    def test_validate_candidate_rejects_patch_override_to_link_target(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        candidate_dir = score_path.parent
        archive_patch = self.root / "archive" / "v2" / "patch.diff"
        archive_patch.parent.mkdir(parents=True)
        archive_patch.write_bytes((candidate_dir / "patch.diff").read_bytes())
        (candidate_dir / "patch.diff").unlink()
        (candidate_dir / "patch.diff").symlink_to(os.path.relpath(archive_patch, candidate_dir))
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
            "--patch",
            str(archive_patch),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--patch must match the candidate directory patch.diff", completed.stderr)

    def test_validate_candidate_rejects_protected_evaluator_patch(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n",
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch must not touch evaluator closure", completed.stderr)

    def test_validate_candidate_rejects_external_patch_override(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n",
        )
        benign_patch = self.write_patch()
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
            "--patch",
            str(benign_patch),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--patch must match the candidate directory patch.diff", completed.stderr)

    def test_validate_candidate_rejects_run_id_mismatch(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=direction)
        trace_path = score_path.with_name("trace.yml")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["run_id"] = "other-run"
        trace["run_id"] = "other-run"
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("run_id must match the containing search run directory", completed.stderr)

    def test_validate_candidate_rejects_space_path_patch_escape(self) -> None:
        (self.root / "src" / "allowed").write_text("allowed\n", encoding="utf-8")
        (self.root / "src" / "allowed file").write_text("outside\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add spaced path fixture")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["search_surface"] = ["src/allowed"]
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="\n".join(
                [
                    "diff --git a/src/allowed b/src/allowed",
                    "--- a/src/allowed file",
                    "+++ b/src/allowed file",
                    "@@ -1 +1 @@",
                    "-outside",
                    "+changed",
                    "",
                ]
            ),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch touches path outside search_surface: src/allowed file", completed.stderr)

    def test_validate_candidate_rejects_unprefixed_space_path_patch_escape(self) -> None:
        (self.root / "src" / "allowed").write_text("allowed\n", encoding="utf-8")
        (self.root / "src" / "allowed file").write_text("outside\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add unprefixed spaced path fixture")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["search_surface"] = ["src/allowed"]
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="\n".join(
                [
                    "--- src/allowed file",
                    "+++ src/allowed file",
                    "@@ -1 +1 @@",
                    "-outside",
                    "+changed",
                    "",
                ]
            ),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch touches path outside search_surface: src/allowed file", completed.stderr)

    def test_validate_candidate_rejects_unified_protected_evaluator_patch(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="\n".join(
                [
                    "--- a/benchmarks/init-codex-harness/run_cases.py",
                    "+++ b/benchmarks/init-codex-harness/run_cases.py",
                    "@@ -1 +1 @@",
                    "-print('ok')",
                    "+print('changed')",
                    "",
                ]
            ),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch must not touch evaluator closure", completed.stderr)

    def test_validate_candidate_rejects_archive_mutation(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            patch_text="diff --git a/archive/v2/packets/pkt.yml b/archive/v2/packets/pkt.yml\n",
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch must not touch archive/v2", completed.stderr)

    def test_validate_candidate_rejects_evaluator_closure_digest_drift(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            mutate=lambda candidate: candidate["evaluator_closure"]["oracle_paths"].update(
                {"after_sha256": "f" * 64}
            ),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator_closure.oracle_paths changed", completed.stderr)

    def test_validate_candidate_rejects_regenerated_digest_after_protected_file_mutation(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('mutated')\n",
            encoding="utf-8",
        )
        score_path = self.write_candidate(direction=direction)
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("evaluator_digest must match evaluator closure bytes", completed.stderr)

    def test_validate_candidate_rejects_direction_digest_mismatch(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            mutate=lambda candidate: candidate.update({"direction_digest": "1" * 64}),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("direction_digest must match", completed.stderr)

    def test_validate_candidate_requires_id_to_match_directory(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            mutate=lambda candidate: candidate.update({"candidate_id": "cand-elsewhere"}),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate_id must match the candidate directory name", completed.stderr)

    def test_validate_candidate_rejects_passing_verdict_with_failed_evaluator(self) -> None:
        direction = self.direction()
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(
            direction=direction,
            mutate=lambda candidate: candidate.update(
                {
                    "exit_code": 1,
                    "score": 0.4,
                    "case_results": [{"case_id": "fresh-empty-repo", "status": "fail"}],
                }
            ),
        )
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("verdict pass requires exit_code 0", completed.stderr)
        self.assertIn("verdict pass requires score >= success.min_score", completed.stderr)
        self.assertIn("verdict pass exceeds success.max_regressions", completed.stderr)

    def test_validate_direction_rejects_symlinked_search_surface(self) -> None:
        (self.root / "src" / "alias.py").symlink_to(
            self.root / "benchmarks" / "init-codex-harness" / "run_cases.py"
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add symlink")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"] = ["src/alias.py"]
        direction_path = self.write_direction(direction)
        completed = run_cli(self.root, "validate-direction", "--direction", str(direction_path))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must not be or contain a symlink", completed.stderr)

    def test_validate_candidate_rejects_invalid_direction_without_traceback(self) -> None:
        direction = self.direction()
        del direction["base_ref"]
        direction_path = self.write_direction(direction)
        score_path = self.write_candidate(direction=self.direction())
        completed = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("direction missing fields", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_start_creates_run_directory(self) -> None:
        direction_path = self.write_direction()
        completed = run_cli(
            self.root,
            "start",
            "--direction",
            str(direction_path),
            "--run-id",
            "run-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        self.assertTrue((run_dir / "direction.yml").is_file())
        self.assertTrue((run_dir / "run.yml").is_file())
        self.assertTrue((run_dir / "scores.jsonl").is_file())
        self.assertTrue((run_dir / "proposals.jsonl").is_file())

    def test_start_rejects_symlinked_run_store_parent_before_writing(self) -> None:
        direction_path = self.write_direction()
        real_runs = self.root / "archive" / "v2" / "search-runs"
        real_runs.mkdir(parents=True)
        (self.root / ".harness").mkdir()
        (self.root / ".harness" / "search-runs").symlink_to("../archive/v2/search-runs", target_is_directory=True)
        completed = run_cli(
            self.root,
            "start",
            "--direction",
            str(direction_path),
            "--run-id",
            "run-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("run-store parent must not be a symlink", completed.stderr)
        self.assertFalse((real_runs / "run-001" / "run.yml").exists())

    def test_eval_records_passing_candidate_and_summary(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch()
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(patch_path),
            "--candidate-id",
            "cand-001",
            "--why",
            "try narrower trace-root heuristic",
            "--next-hypothesis",
            "compare against path-depth heuristic",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("verdict: pass", completed.stdout)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        self.assertEqual(score["verdict"], "pass")
        self.assertEqual(score["score"], 0.97)
        self.assertEqual(score["case_results"], [{"case_id": "fresh-empty-repo", "status": "pass"}])
        trace_path = score_path.with_name("trace.yml")
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        self.assertEqual(score["trace_sha256"], file_sha256(trace_path))
        self.assertEqual(trace["schema_version"], "strategy-search-trace/v1")
        self.assertEqual(trace["evidence_status"], "diagnostic_only")
        self.assertEqual(trace["stdout_ref"]["ref"], "stdout.log")
        self.assertEqual(trace["stderr_ref"]["ref"], "stderr.log")
        self.assertEqual(trace["changed_paths"], ["src/prompt.md"])
        self.assertEqual(trace["why"], "try narrower trace-root heuristic")
        self.assertEqual(trace["next_hypothesis"], "compare against path-depth heuristic")
        self.assertIn("not archive/v2 evidence", "\n".join(trace["notes"]))
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

        summary = run_cli(self.root, "summarize", "--run", ".harness/search-runs/run-001")
        self.assertEqual(summary.returncode, 0, summary.stderr)
        self.assertIn("cand-001: verdict=pass score=0.97 exit_code=0", summary.stdout)
        summary_path = self.root / ".harness" / "search-runs" / "run-001" / "summary.yml"
        summary_record = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary_record["evidence_status"], "diagnostic_only")
        self.assertEqual(summary_record["counts"]["pass"], 1)
        self.assertEqual(summary_record["candidates"][0]["trace_ref"], "candidates/cand-001/trace.yml")
        self.assertEqual(summary_record["candidates"][0]["trace_sha256"], file_sha256(trace_path))
        self.assertIn("not archive/v2 evidence", "\n".join(summary_record["notes"]))

    def test_eval_rejects_out_of_repo_patch_source_before_copying(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        with tempfile.TemporaryDirectory() as outside_tmp:
            outside_patch = Path(outside_tmp) / "candidate.diff"
            outside_patch.write_bytes(self.write_patch().read_bytes())
            completed = run_cli(
                self.root,
                "eval",
                "--run",
                ".harness/search-runs/run-001",
                "--patch",
                str(outside_patch),
                "--candidate-id",
                "cand-001",
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("patch source must be inside repository root", completed.stderr)
        self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001").exists())

    def test_eval_rejects_linked_patch_sources_before_copying(self) -> None:
        for link_kind in ("symlink", "hardlink"):
            with self.subTest(link_kind=link_kind):
                self.tearDown()
                self.setUp()
                direction_path = self.write_direction()
                run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
                self.assertEqual(run.returncode, 0, run.stderr)
                real_patch = self.write_patch()
                linked_patch = self.root / f"eval-{link_kind}-source.patch"
                if link_kind == "symlink":
                    linked_patch.symlink_to(real_patch.name)
                    expected = "patch source path must not contain symlinks"
                else:
                    os.link(real_patch, linked_patch)
                    expected = "patch source must not be hard-linked"
                completed = run_cli(
                    self.root,
                    "eval",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--patch",
                    str(linked_patch),
                    "--candidate-id",
                    "cand-001",
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(expected, completed.stderr)
                self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001").exists())

    def test_eval_rejects_patch_source_with_parent_segment(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        safe_dir = self.root / "safe"
        safe_dir.mkdir()
        (safe_dir / "link").symlink_to(self.root, target_is_directory=True)
        patch = self.write_patch()
        patch.rename(self.root / "patch.diff")
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            "safe/link/../patch.diff",
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("patch source path must not contain '..'", completed.stderr)
        self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001").exists())

    def test_eval_rejects_silent_evaluator_output(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('all good but no structured score')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "silent evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        stderr_log = score_path.with_name("stderr.log").read_text(encoding="utf-8")
        self.assertEqual(score["verdict"], "invalid")
        self.assertIn("evaluator output must include an explicit score line", stderr_log)
        self.assertIn("evaluator output must include at least one explicit case line", stderr_log)

    def test_validate_candidate_rejects_silent_fail_with_forged_typed_results(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "silent failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["verdict"] = "fail"
        score["score"] = 0.97
        score["case_results"] = [{"case_id": "fresh-empty-repo", "status": "pass"}]
        trace["result"]["verdict"] = "fail"
        trace["result"]["score"] = 0.97
        trace["result"]["case_results"] = [{"case_id": "fresh-empty-repo", "status": "pass"}]
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("evaluator output must include an explicit score line", accepted.stderr)
        self.assertIn("evaluator output must include at least one explicit case line", accepted.stderr)

    def test_eval_records_binary_evaluator_output_as_diagnostic_text(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "import sys",
                    "sys.stdout.buffer.write(b'\\xff\\nscore: 0.97\\ncase: fresh-empty-repo: pass\\n')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "binary output evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        stdout_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stdout.log"
        ).read_text(encoding="utf-8")
        self.assertIn("\ufffd\nscore: 0.97", stdout_log)

    def test_eval_detects_source_git_metadata_mutation(self) -> None:
        git_side_path = self.root / ".git" / "logs" / "strategy-search-side"
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(git_side_path)!r}).parent.mkdir(parents=True, exist_ok=True)",
                    f"Path({str(git_side_path)!r}).write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "source git metadata mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied source repository git metadata", stderr_log)
        self.assertFalse(git_side_path.exists())

    def test_eval_detects_linked_worktree_gitdir_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as gitdir_parent:
            gitdir = Path(gitdir_parent) / "actual-gitdir"
            marker = gitdir / "strategy-search-marker"
            (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
                "\n".join(
                    [
                        "from pathlib import Path",
                        f"Path({str(marker)!r}).write_text('bad\\n')",
                        "print('score: 0.97')",
                        "print('case: fresh-empty-repo: pass')",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            git(self.root, "add", "-A")
            git(self.root, "commit", "-m", "linked gitdir mutator")
            self.base_commit = git(self.root, "rev-parse", "HEAD")
            shutil.move(str(self.root / ".git"), str(gitdir))
            (self.root / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
            direction_path = self.write_direction()
            run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
            self.assertEqual(run.returncode, 0, run.stderr)
            completed = run_cli(
                self.root,
                "eval",
                "--run",
                ".harness/search-runs/run-001",
                "--patch",
                str(self.write_patch()),
                "--candidate-id",
                "cand-001",
            )
            self.assertNotEqual(completed.returncode, 0)
            stderr_log = (
                self.root
                / ".harness"
                / "search-runs"
                / "run-001"
                / "candidates"
                / "cand-001"
                / "stderr.log"
            ).read_text(encoding="utf-8")
            self.assertIn("candidate evaluation dirtied source repository git metadata", stderr_log)
            self.assertFalse(marker.exists())

    def test_source_git_metadata_binds_common_gitdir(self) -> None:
        with tempfile.TemporaryDirectory() as git_parent:
            git_parent_path = Path(git_parent)
            worktree_gitdir = git_parent_path / "worktree-gitdir"
            common_gitdir = git_parent_path / "common-gitdir"
            worktree_gitdir.mkdir()
            common_gitdir.mkdir()
            (worktree_gitdir / "commondir").write_text(str(common_gitdir), encoding="utf-8")
            (worktree_gitdir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            (common_gitdir / "config").write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
            original_git = self.root / ".git"
            if original_git.is_dir():
                shutil.rmtree(original_git)
            else:
                original_git.unlink()
            original_git.write_text(f"gitdir: {worktree_gitdir}\n", encoding="utf-8")

            before = self.strategy.source_git_metadata_digest(self.root)
            snapshot = self.strategy.capture_git_metadata_snapshot(self.root)
            marker = common_gitdir / "strategy-search-common-marker"
            marker.write_text("bad\n", encoding="utf-8")
            after = self.strategy.source_git_metadata_digest(self.root)
            self.assertNotEqual(before, after)
            self.strategy.restore_git_metadata_snapshot(self.root, snapshot)
            self.assertFalse(marker.exists())
            self.assertEqual(self.strategy.source_git_metadata_digest(self.root), before)

    def test_source_git_metadata_restores_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as git_parent:
            gitdir = Path(git_parent) / "symlink-gitdir"
            gitdir.mkdir()
            (gitdir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            original_git = self.root / ".git"
            if original_git.is_dir():
                shutil.rmtree(original_git)
            else:
                original_git.unlink()
            original_git.symlink_to(gitdir)

            before = self.strategy.source_git_metadata_digest(self.root)
            snapshot = self.strategy.capture_git_metadata_snapshot(self.root)
            marker = gitdir / "strategy-search-symlink-marker"
            marker.write_text("bad\n", encoding="utf-8")
            after = self.strategy.source_git_metadata_digest(self.root)
            self.assertNotEqual(before, after)
            self.strategy.restore_git_metadata_snapshot(self.root, snapshot)
            self.assertFalse(marker.exists())
            self.assertTrue(original_git.is_symlink())
            self.assertEqual(self.strategy.source_git_metadata_digest(self.root), before)

    def test_eval_restores_deleted_source_git_metadata(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "import shutil",
                    f"shutil.rmtree(Path({str(self.root / '.git')!r}))",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "source git metadata deleter")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_commit)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied source repository git metadata", stderr_log)

    def test_eval_restores_source_type_swapped_directory(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "import shutil",
                    f"shutil.rmtree(Path({str(self.root / 'src')!r}))",
                    f"Path({str(self.root / 'src')!r}).write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "source type swap mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue((self.root / "src").is_dir())
        self.assertEqual((self.root / "src" / "prompt.md").read_text(encoding="utf-8"), "old prompt\n")
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied the source repository outside the run store", stderr_log)

    def test_eval_detects_nested_source_git_directory_mutation(self) -> None:
        nested_marker = self.root / "src" / ".git" / "hidden.txt"
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(nested_marker)!r}).parent.mkdir(parents=True, exist_ok=True)",
                    f"Path({str(nested_marker)!r}).write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "nested source git mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(nested_marker.exists())
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied the source repository outside the run store", stderr_log)

    def test_eval_detects_source_root_mode_mutation(self) -> None:
        original_mode = self.root.stat().st_mode & 0o777
        changed_mode = 0o755 if original_mode != 0o755 else 0o700
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(self.root)!r}).chmod({changed_mode})",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "source root mode mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(self.root.stat().st_mode & 0o777, original_mode)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied the source repository outside the run store", stderr_log)

    def test_restore_filesystem_snapshot_replaces_root_symlink_itself(self) -> None:
        protected = self.root / "protected-root"
        protected.mkdir()
        (protected / "state.txt").write_text("original\n", encoding="utf-8")
        snapshot = self.strategy.capture_filesystem_snapshot(protected, skip_git=False)
        with tempfile.TemporaryDirectory() as external_tmp:
            external = Path(external_tmp)
            (external / "external.txt").write_text("external\n", encoding="utf-8")
            shutil.rmtree(protected)
            protected.symlink_to(external, target_is_directory=True)

            self.strategy.restore_filesystem_snapshot(protected, snapshot, skip_git=False)

            self.assertTrue(protected.is_dir())
            self.assertFalse(protected.is_symlink())
            self.assertEqual((protected / "state.txt").read_text(encoding="utf-8"), "original\n")
            self.assertEqual((external / "external.txt").read_text(encoding="utf-8"), "external\n")

    def test_eval_detects_search_run_store_mutation(self) -> None:
        run_side_path = self.root / ".harness" / "search-runs" / "run-001" / "tampered.txt"
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(run_side_path)!r}).write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "run store mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied the search run store", stderr_log)
        self.assertFalse(run_side_path.exists())

    def test_eval_detects_search_run_store_git_directory_mutation(self) -> None:
        run_side_path = self.root / ".harness" / "search-runs" / "run-001" / ".git" / "hidden.txt"
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(run_side_path)!r}).parent.mkdir(parents=True, exist_ok=True)",
                    f"Path({str(run_side_path)!r}).write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "run store hidden git mutator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate evaluation dirtied the search run store", stderr_log)
        self.assertFalse(run_side_path.exists())

    def test_eval_detects_detached_late_workspace_write(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "import subprocess, sys, textwrap",
                    "subprocess.Popen([sys.executable, '-c', \"import pathlib, time; time.sleep(0.1); pathlib.Path('archive/v2/late.txt').parent.mkdir(parents=True, exist_ok=True); pathlib.Path('archive/v2/late.txt').write_text('late')\"], start_new_session=True)",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "detached child evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        stderr_log = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "candidates"
            / "cand-001"
            / "stderr.log"
        ).read_text(encoding="utf-8")
        self.assertIn("candidate workspace changed after patch application", stderr_log)

    def test_select_writes_diagnostic_run_store_selection_without_certifying(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertIn("stable_handoff_eligible: false", selected.stdout)
        self.assertIn("evidence_status: diagnostic_only", selected.stdout)
        selection_path = self.root / ".harness" / "search-runs" / "run-001" / "selections" / "cand-001-selection.yml"
        summary_copy = selection_path.with_name("cand-001-summary.yml")
        patch_copy = selection_path.with_name("cand-001-patch.diff")
        score_copy = selection_path.with_name("cand-001-score.yml")
        stdout_copy = selection_path.with_name("cand-001-stdout.log")
        stderr_copy = selection_path.with_name("cand-001-stderr.log")
        trace_copy = selection_path.with_name("cand-001-trace.yml")
        trace_md_copy = selection_path.with_name("cand-001-trace.md")
        for path in (selection_path, summary_copy):
            self.assertTrue(path.is_file(), path)
        for path in (patch_copy, score_copy, stdout_copy, stderr_copy, trace_copy, trace_md_copy):
            self.assertFalse(path.exists(), path)
        manifest = yaml.safe_load(selection_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "strategy-search-adoption-selection/v1")
        self.assertEqual(manifest["evidence_status"], "diagnostic_only")
        self.assertNotIn("source", manifest)
        self.assertIn("diagnostic-only", manifest["diagnostic_source"])
        self.assertNotIn("direction_id", manifest["direction"])
        self.assertFalse(manifest["governance"]["stable_handoff_eligible"])
        self.assertTrue(manifest["governance"]["requires_acceptance_packet"])
        self.assertTrue(manifest["governance"]["requires_active_pointer_publication"])
        self.assertTrue(manifest["governance"]["search_pass_is_not_governance_pass"])
        self.assertNotIn("case_results", manifest["candidate"])
        self.assertNotIn("changed_paths", manifest["candidate"])
        output_refs = {item["kind"]: item for item in manifest["diagnostic_outputs"]}
        self.assertEqual(
            output_refs["summary"]["ref"],
            ".harness/search-runs/run-001/selections/cand-001-summary.yml",
        )
        self.assertEqual(set(output_refs), {"summary"})
        summary = yaml.safe_load(summary_copy.read_text(encoding="utf-8"))
        self.assertEqual(summary["schema_version"], "strategy-search-selected-candidate-summary/v1")
        self.assertEqual(summary["candidate_id"], "cand-001")
        self.assertIn("direction_digest", summary)
        self.assertNotIn("direction_id", summary)
        self.assertNotIn("failed_cases", summary)
        self.assertNotIn("changed_paths", summary)

    def test_select_rejects_run_yml_identity_mismatch(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        run_yml = self.root / ".harness" / "search-runs" / "run-001" / "run.yml"
        run_meta = yaml.safe_load(run_yml.read_text(encoding="utf-8"))
        run_meta["run_id"] = "other-run"
        run_yml.write_text(yaml.safe_dump(run_meta, sort_keys=False), encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("run.yml run_id must match the search run directory name", selected.stderr)

    def test_select_refuses_archive_output_prefix(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            "archive/v2/artifacts/selected-cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("diagnostic-only", selected.stderr)

    def test_select_requires_canonical_search_run_directory(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        archive_run = self.root / "archive" / "v2" / "run-001"
        archive_run.parent.mkdir(parents=True)
        shutil.copytree(self.root / ".harness" / "search-runs" / "run-001", archive_run)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            "archive/v2/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("canonical diagnostic path .harness/search-runs/<run-id>", selected.stderr)
        self.assertFalse((archive_run / "selections" / "cand-001-selection.yml").exists())

    def test_select_rejects_symlinked_canonical_run_directory(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        canonical_run = self.root / ".harness" / "search-runs" / "run-001"
        archive_run = self.root / "archive" / "v2" / "run-001"
        archive_run.parent.mkdir(parents=True)
        canonical_run.rename(archive_run)
        canonical_run.symlink_to("../../archive/v2/run-001", target_is_directory=True)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("run directory path must not contain symlinks", selected.stderr)
        self.assertFalse((archive_run / "selections" / "cand-001-selection.yml").exists())

    def test_run_load_rejects_symlinked_run_store_parent(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        real_runs = self.root / "archive" / "v2" / "search-runs"
        real_runs.parent.mkdir(parents=True)
        (self.root / ".harness" / "search-runs").rename(real_runs)
        (self.root / ".harness" / "search-runs").symlink_to("../archive/v2/search-runs", target_is_directory=True)
        proposed = run_cli(self.root, "propose", "--run", ".harness/search-runs/run-001")
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("run-store parent must not be a symlink", proposed.stderr)
        self.assertFalse((real_runs / "run-001" / "proposals" / "cand-001" / "proposal.yml").exists())

    def test_select_rejects_symlinked_run_metadata_before_reading(self) -> None:
        for metadata_name in ("run.yml", "direction.yml"):
            with self.subTest(metadata_name=metadata_name):
                self.tearDown()
                self.setUp()
                direction_path = self.write_direction()
                run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
                self.assertEqual(run.returncode, 0, run.stderr)
                completed = run_cli(
                    self.root,
                    "eval",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--patch",
                    str(self.write_patch()),
                    "--candidate-id",
                    "cand-001",
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                metadata_path = self.root / ".harness" / "search-runs" / "run-001" / metadata_name
                archive_meta = self.root / "archive" / "v2" / metadata_name
                archive_meta.parent.mkdir(parents=True)
                archive_meta.write_text(metadata_path.read_text(encoding="utf-8"), encoding="utf-8")
                metadata_path.unlink()
                metadata_path.symlink_to(f"../../../archive/v2/{metadata_name}")
                selected = run_cli(
                    self.root,
                    "select",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--candidate",
                    "cand-001",
                )
                self.assertNotEqual(selected.returncode, 0)
                self.assertIn(f"run metadata file must not be a symlink: {metadata_name}", selected.stderr)
                self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "selections").exists())

    def test_select_rejects_hardlinked_run_metadata_before_reading(self) -> None:
        for metadata_name in ("run.yml", "direction.yml"):
            with self.subTest(metadata_name=metadata_name):
                self.tearDown()
                self.setUp()
                direction_path = self.write_direction()
                run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
                self.assertEqual(run.returncode, 0, run.stderr)
                metadata_path = self.root / ".harness" / "search-runs" / "run-001" / metadata_name
                archive_meta = self.root / "archive" / "v2" / metadata_name
                archive_meta.parent.mkdir(parents=True)
                archive_meta.write_bytes(metadata_path.read_bytes())
                metadata_path.unlink()
                os.link(archive_meta, metadata_path)
                selected = run_cli(
                    self.root,
                    "select",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--candidate",
                    "cand-001",
                )
                self.assertNotEqual(selected.returncode, 0)
                self.assertIn(f"run metadata file {metadata_name} must not be hard-linked", selected.stderr)

    def test_select_rejects_invalid_candidate_id_before_path_use(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "../direction",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("candidate must contain only letters", selected.stderr)
        self.assertNotIn("../direction", selected.stderr)

    def test_select_rejects_symlinked_candidate_sources(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        candidate_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001"
        real_score = candidate_dir / "score-real.yml"
        (candidate_dir / "score.yml").rename(real_score)
        (candidate_dir / "score.yml").symlink_to(real_score.name)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selected candidate score must not be a symlink", selected.stderr)

    def test_select_rejects_hardlinked_candidate_sources_before_loading(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        candidate_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001"
        external_score = self.root / "archive" / "v2" / "score.yml"
        external_score.parent.mkdir(parents=True, exist_ok=True)
        external_score.write_bytes((candidate_dir / "score.yml").read_bytes())
        (candidate_dir / "score.yml").unlink()
        os.link(external_score, candidate_dir / "score.yml")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selected candidate score must not be hard-linked", selected.stderr)

    def test_select_rejects_symlinked_candidate_directory(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        candidates_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates"
        candidate_dir = candidates_dir / "cand-001"
        real_candidate_dir = candidates_dir / "cand-real"
        candidate_dir.rename(real_candidate_dir)
        candidate_dir.symlink_to("cand-real", target_is_directory=True)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selected candidate score path must not contain a symlink", selected.stderr)

    def test_select_rejects_symlinked_output_even_with_overwrite(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selections_dir = self.root / ".harness" / "search-runs" / "run-001" / "selections"
        selections_dir.mkdir(parents=True)
        target = selections_dir / "symlink-target-summary.yml"
        target.write_text("do not overwrite\n", encoding="utf-8")
        (selections_dir / "symlink-output-summary.yml").symlink_to("symlink-target-summary.yml")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            ".harness/search-runs/run-001/selections/symlink-output",
            "--overwrite",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("summary output must not be a symlink", selected.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_select_rejects_hardlinked_output_even_with_overwrite(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        archive_file = self.root / "archive" / "v2" / "artifacts" / "linked-summary.yml"
        archive_file.parent.mkdir(parents=True)
        archive_file.write_text("do not overwrite\n", encoding="utf-8")
        selections_dir = self.root / ".harness" / "search-runs" / "run-001" / "selections"
        selections_dir.mkdir(parents=True)
        os.link(archive_file, selections_dir / "hardlink-output-summary.yml")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            ".harness/search-runs/run-001/selections/hardlink-output",
            "--overwrite",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("summary output must not be a hard link", selected.stderr)
        self.assertEqual(archive_file.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_select_rejects_file_output_parent_without_traceback(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        bad_parent = self.root / ".harness" / "search-runs" / "run-001" / "not-a-dir"
        bad_parent.write_text("file\n", encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            ".harness/search-runs/run-001/not-a-dir/output",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("output parent must be a directory", selected.stderr)
        self.assertNotIn("Traceback", selected.stderr)

    def test_select_rejects_directory_output_prefix(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            ".harness/search-runs/run-001/selections/",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("output_prefix must be a file prefix", selected.stderr)

    def test_select_rejects_stale_same_prefix_siblings(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        stale = self.root / ".harness" / "search-runs" / "run-001" / "selections" / "cand-001-patch.diff"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale\n", encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--overwrite",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("stale diagnostic selection sibling", selected.stderr)

    def test_select_rejects_stale_same_prefix_siblings_with_glob_chars(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selections_dir = self.root / ".harness" / "search-runs" / "run-001" / "selections"
        stale = selections_dir / "sel[1]-stdout.log"
        stale.parent.mkdir(parents=True)
        stale.write_text("stale\n", encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--output-prefix",
            ".harness/search-runs/run-001/selections/sel[1]",
            "--overwrite",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("stale diagnostic selection sibling", selected.stderr)

    def test_select_does_not_archive_trace_markdown(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        trace_md = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "trace.md"
        trace_md.write_text("forged markdown\n", encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        copied = self.root / ".harness" / "search-runs" / "run-001" / "selections" / "cand-001-trace.md"
        self.assertFalse(copied.exists())

    def test_select_rejects_trace_text_that_exposes_sealed_paths(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
            "--why",
            "checked benchmarks/init-codex-harness/expected/output.txt",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selected candidate trace.why must not expose sealed evaluator/oracle material", selected.stderr)
        self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "selections" / "cand-001-summary.yml").exists())

    def test_select_rejects_trace_text_that_points_to_run_store_patch(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
            "--why",
            "file:.harness/search-runs/run-001/candidates/cand-001/patch.diff:1",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selected candidate trace.why must not expose sealed evaluator/oracle material", selected.stderr)

    def test_select_public_artifacts_omit_unsanitized_direction_id(self) -> None:
        direction = self.direction()
        direction["direction_id"] = "benchmarks/init-codex-harness/expected/output.txt"
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        artifacts = sorted((self.root / ".harness" / "search-runs" / "run-001" / "selections").glob("cand-001-*"))
        self.assertTrue(artifacts)
        for artifact in artifacts:
            self.assertNotIn(
                "benchmarks/init-codex-harness/expected/output.txt",
                artifact.read_text(encoding="utf-8", errors="replace"),
            )

    def test_select_does_not_archive_trace_notes(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        trace["notes"] = ["see benchmarks/init-codex-harness/expected/output.txt"]
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        artifacts = sorted((self.root / ".harness" / "search-runs" / "run-001" / "selections").glob("cand-001-*"))
        self.assertTrue(artifacts)
        for artifact in artifacts:
            self.assertNotIn(
                "benchmarks/init-codex-harness/expected/output.txt",
                artifact.read_text(encoding="utf-8", errors="replace"),
            )

    def test_select_rejects_reason_that_exposes_sealed_paths(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.2')\nprint('case: fresh-empty-repo: fail')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--allow-nonpass",
            "--reason",
            "benchmarks/init-codex-harness/expected/output.txt",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("selection reason must not expose sealed evaluator/oracle material", selected.stderr)

    def test_select_does_not_archive_raw_logs(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('benchmarks/init-codex-harness/expected/output.txt')\n"
            "print('score: 0.97')\n"
            "print('case: fresh-empty-repo: pass')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "leaky evaluator output")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertFalse((self.root / ".harness" / "search-runs" / "run-001" / "selections" / "cand-001-stdout.log").exists())
        artifacts = sorted((self.root / ".harness" / "search-runs" / "run-001" / "selections").glob("cand-001-*"))
        self.assertTrue(artifacts)
        for artifact in artifacts:
            self.assertNotIn(
                "benchmarks/init-codex-harness/expected/output.txt",
                artifact.read_text(encoding="utf-8", errors="replace"),
            )

    def test_select_refuses_nonpass_without_explicit_reason(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.2')\nprint('case: trace-root: fail')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("candidate verdict must be pass", selected.stderr)
        allowed = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--allow-nonpass",
            "--reason",
            "adopting the trace to document a deliberately rejected strategy",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        manifest = yaml.safe_load(
            (
                self.root
                / ".harness"
                / "search-runs"
                / "run-001"
                / "selections"
                / "cand-001-selection.yml"
            ).read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(manifest["candidate"]["nonpass_selected"])
        self.assertFalse(manifest["governance"]["stable_handoff_eligible"])

    def test_select_rejects_invalid_candidate_even_with_allow_nonpass(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "Path('archive/v2/side.yml').parent.mkdir(parents=True, exist_ok=True)",
                    "Path('archive/v2/side.yml').write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "invalid evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        selected = run_cli(
            self.root,
            "select",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate",
            "cand-001",
            "--allow-nonpass",
            "--reason",
            "diagnose invalid side effect",
        )
        self.assertNotEqual(selected.returncode, 0)
        self.assertIn("invalid candidates cannot be selected for adoption", selected.stderr)

    def test_validate_candidate_rejects_tampered_trace(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        trace["stdout_ref"]["sha256"] = "0" * 64
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("trace_sha256 must match trace.yml", accepted.stderr)

    def test_validate_candidate_rejects_score_contradicting_raw_logs(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.2')\nprint('case: trace-root: fail')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["score"] = 0.97
        score["case_results"] = [{"case_id": "trace-root", "status": "pass"}]
        score["verdict"] = "pass"
        trace["result"]["score"] = 0.97
        trace["result"]["case_results"] = [{"case_id": "trace-root", "status": "pass"}]
        trace["result"]["verdict"] = "pass"
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("score must match parsed stdout/stderr evaluator output", accepted.stderr)

    def test_validate_candidate_rejects_duplicate_score_lines(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.97')\nprint('score: 0.20')\nprint('case: fresh-empty-repo: pass')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "ambiguous evaluator score")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        stderr_log = score_path.with_name("stderr.log").read_text(encoding="utf-8")
        self.assertIn("evaluator output must include exactly one explicit score line", stderr_log)

    def test_eval_rejects_ambiguous_failing_evaluator_output(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.97')\nprint('score: 0.20')\nprint('case: fresh-empty-repo: fail')\nraise SystemExit(1)\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "ambiguous failing evaluator score")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        self.assertEqual(score["verdict"], "invalid")
        self.assertIn(
            "evaluator output must include exactly one explicit score line",
            score_path.with_name("stderr.log").read_text(encoding="utf-8"),
        )

    def test_eval_rejects_tampered_run_metadata(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_direction_path = self.root / ".harness" / "search-runs" / "run-001" / "direction.yml"
        direction = yaml.safe_load(run_direction_path.read_text(encoding="utf-8"))
        direction["success"]["min_score"] = 0.1
        run_direction_path.write_text(yaml.safe_dump(direction, sort_keys=False), encoding="utf-8")
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("direction_digest does not match", completed.stderr)

    def test_summarize_marks_tampered_score_invalid(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch()
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(patch_path),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        score["patch_sha256"] = "0" * 64
        score["score"] = "not-a-number"
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        summary = run_cli(self.root, "summarize", "--run", ".harness/search-runs/run-001")
        self.assertEqual(summary.returncode, 0, summary.stderr)
        summary_path = self.root / ".harness" / "search-runs" / "run-001" / "summary.yml"
        summary_record = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary_record["counts"]["pass"], 0)
        self.assertEqual(summary_record["counts"]["invalid"], 1)
        self.assertEqual(summary_record["candidates"][0]["verdict"], "invalid")

    def test_summarize_rejects_hardlinked_candidate_sources_before_loading(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        candidate_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001"
        external_score = self.root / "archive" / "v2" / "linked-score.yml"
        external_score.parent.mkdir(parents=True)
        external_score.write_bytes((candidate_dir / "score.yml").read_bytes())
        (candidate_dir / "score.yml").unlink()
        os.link(external_score, candidate_dir / "score.yml")
        summary = run_cli(self.root, "summarize", "--run", ".harness/search-runs/run-001")
        self.assertEqual(summary.returncode, 0, summary.stderr)
        summary_path = self.root / ".harness" / "search-runs" / "run-001" / "summary.yml"
        summary_record = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary_record["counts"]["invalid"], 1)
        self.assertIn(
            "selected candidate score must not be hard-linked",
            "\n".join(summary_record["candidates"][0]["validation_errors"]),
        )

    def test_summarize_does_not_glob_through_symlinked_candidate_directory(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        candidates_dir = run_dir / "candidates"
        real_candidate_dir = run_dir / "cand-real"
        (candidates_dir / "cand-001").rename(real_candidate_dir)
        (candidates_dir / "cand-001").symlink_to("../cand-real", target_is_directory=True)
        summary = run_cli(self.root, "summarize", "--run", ".harness/search-runs/run-001")
        self.assertEqual(summary.returncode, 0, summary.stderr)
        summary_path = self.root / ".harness" / "search-runs" / "run-001" / "summary.yml"
        summary_record = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary_record["counts"]["invalid"], 1)
        self.assertIn(
            "candidate directory must not be a symlink",
            "\n".join(
                item["validation_errors"][0]
                for item in summary_record["candidates"]
                if item.get("validation_errors")
            ),
        )

    def test_summarize_rejects_linked_outputs_before_writing(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        archive_summary = self.root / "archive" / "v2" / "summary.yml"
        archive_summary.parent.mkdir(parents=True)
        archive_summary.write_text("do not overwrite\n", encoding="utf-8")
        os.link(archive_summary, run_dir / "summary.yml")
        summary = run_cli(self.root, "summarize", "--run", ".harness/search-runs/run-001")
        self.assertNotEqual(summary.returncode, 0)
        self.assertIn("summary.yml must not be hard-linked", summary.stderr)
        self.assertEqual(archive_summary.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_summarize_rejects_linked_search_set_output_before_writing(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        archive_search_set = self.root / "archive" / "v2" / "search-set.yml"
        archive_search_set.parent.mkdir(parents=True)
        archive_search_set.write_text("do not overwrite\n", encoding="utf-8")
        os.link(archive_search_set, run_dir / "search-set.yml")
        summary = run_cli(
            self.root,
            "summarize",
            "--run",
            ".harness/search-runs/run-001",
            "--write-search-set",
        )
        self.assertNotEqual(summary.returncode, 0)
        self.assertIn("search-set.yml must not be hard-linked", summary.stderr)
        self.assertEqual(archive_search_set.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_summarize_writes_search_set_for_recurring_failures(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.2')\nprint('case: trace-root: fail')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        for candidate_id in ("cand-001", "cand-002"):
            completed = run_cli(
                self.root,
                "eval",
                "--run",
                ".harness/search-runs/run-001",
                "--patch",
                str(self.write_patch()),
                "--candidate-id",
                candidate_id,
                "--why",
                f"try {candidate_id}",
            )
            self.assertNotEqual(completed.returncode, 0)
        summary = run_cli(
            self.root,
            "summarize",
            "--run",
            ".harness/search-runs/run-001",
            "--write-search-set",
        )
        self.assertEqual(summary.returncode, 0, summary.stderr)
        self.assertIn("search_set_path:", summary.stdout)
        search_set_path = self.root / ".harness" / "search-runs" / "run-001" / "search-set.yml"
        search_set = yaml.safe_load(search_set_path.read_text(encoding="utf-8"))
        self.assertEqual(search_set["schema_version"], "strategy-search-set/v1")
        self.assertEqual(search_set["evidence_status"], "diagnostic_only")
        self.assertEqual(len(search_set["entries"]), 1)
        entry = search_set["entries"][0]
        self.assertEqual(entry["case_id"], "trace-root")
        self.assertEqual(entry["candidate_ids"], ["cand-001", "cand-002"])
        self.assertEqual(
            entry["trace_refs"],
            ["candidates/cand-001/trace.yml", "candidates/cand-002/trace.yml"],
        )

    def test_summarize_excludes_invalid_candidates_from_search_set(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "print('score: 0.2')\nprint('case: trace-root: fail')\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "failing evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        for candidate_id in ("cand-001", "cand-002"):
            completed = run_cli(
                self.root,
                "eval",
                "--run",
                ".harness/search-runs/run-001",
                "--patch",
                str(self.write_patch()),
                "--candidate-id",
                candidate_id,
            )
            self.assertNotEqual(completed.returncode, 0)
            score_path = (
                self.root
                / ".harness"
                / "search-runs"
                / "run-001"
                / "candidates"
                / candidate_id
                / "score.yml"
            )
            score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
            score["trace_sha256"] = "0" * 64
            score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        summary = run_cli(
            self.root,
            "summarize",
            "--run",
            ".harness/search-runs/run-001",
            "--write-search-set",
        )
        self.assertEqual(summary.returncode, 0, summary.stderr)
        search_set_path = self.root / ".harness" / "search-runs" / "run-001" / "search-set.yml"
        search_set = yaml.safe_load(search_set_path.read_text(encoding="utf-8"))
        self.assertEqual(search_set["entries"], [])

    def test_propose_writes_public_bundle_without_oracle_contents(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        proposal_dir = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001"
        proposal = yaml.safe_load((proposal_dir / "proposal.yml").read_text(encoding="utf-8"))
        context = yaml.safe_load((proposal_dir / "public-context.yml").read_text(encoding="utf-8"))
        policy = yaml.safe_load((proposal_dir / "policy.yml").read_text(encoding="utf-8"))
        prompt = (proposal_dir / "prompt.md").read_text(encoding="utf-8")
        self.assertEqual(proposal["status"], "awaiting_patch")
        self.assertEqual(context["evidence_status"], "diagnostic_only")
        self.assertEqual(context["direction"]["search_surface"], ["src/prompt.md"])
        bundle_text = "\n".join(
            [
                yaml.safe_dump(proposal, sort_keys=False),
                yaml.safe_dump(context, sort_keys=False),
                yaml.safe_dump(policy, sort_keys=False),
                prompt,
            ]
        )
        for forbidden in (
            "python3 benchmarks/init-codex-harness/run_cases.py",
            "benchmarks/init-codex-harness/run_cases.py",
            "benchmarks/init-codex-harness/expected",
            "scripts/score-init-codex-harness.py",
            "oracle_paths:",
            "score_parser_paths:",
            "stdout.log",
            "stderr.log",
            "trace_ref",
        ):
            self.assertNotIn(forbidden, bundle_text)
        self.assertEqual(policy["allowed_write_paths"], ["src/prompt.md"])
        self.assertIn("Do not inspect or modify evaluator/oracle internals", prompt)

    def test_propose_context_uses_sanitized_prior_trace_summary(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
            "--why",
            "first try mentioned stdout\\.log, candidates/cand-001/trace\\.yml, "
            "candidates/cand-001/trace%2emd, benchmarks/init-codex-harness/./expected, "
            "benchmarks/init-codex-harness/../init-codex-harness/expected, and "
            "benchmarks/init-codex-harness%2fexpected",
            "--next-hypothesis",
            "second try should not read scripts/sub/../score-init-codex-harness.py or "
            "scripts%2fscore-init-codex-harness.py",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-002",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_dir = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-002"
        context = yaml.safe_load((proposal_dir / "public-context.yml").read_text(encoding="utf-8"))
        prompt = (proposal_dir / "prompt.md").read_text(encoding="utf-8")
        prior = context["prior_candidates"][0]
        self.assertNotIn("trace_ref", prior)
        self.assertIn("[sealed]", prior["trace_summary"]["why"])
        self.assertIn("[sealed]", prior["trace_summary"]["next_hypothesis"])
        self.assertNotIn("benchmarks/init-codex-harness/expected", prior["trace_summary"]["why"])
        self.assertNotIn("benchmarks/init-codex-harness/./expected", prior["trace_summary"]["why"])
        self.assertNotIn("benchmarks/init-codex-harness/../init-codex-harness/expected", prior["trace_summary"]["why"])
        self.assertNotIn("benchmarks/init-codex-harness%2fexpected", prior["trace_summary"]["why"])
        self.assertNotIn("scripts/score-init-codex-harness.py", prior["trace_summary"]["next_hypothesis"])
        self.assertNotIn("scripts/sub/../score-init-codex-harness.py", prior["trace_summary"]["next_hypothesis"])
        self.assertNotIn("scripts%2fscore-init-codex-harness.py", prior["trace_summary"]["next_hypothesis"])
        self.assertNotIn("stdout\\.log", prior["trace_summary"]["why"])
        self.assertNotIn("trace\\.yml", prior["trace_summary"]["why"])
        self.assertNotIn("trace%2emd", prior["trace_summary"]["why"])
        self.assertNotIn("trace\\.md", prior["trace_summary"]["why"])
        self.assertNotIn("trace.yml", prompt)
        self.assertNotIn("trace.md", prompt)
        self.assertNotIn("trace\\.md", prompt)
        self.assertNotIn("stdout.log", prompt)
        self.assertNotIn("stderr.log", prompt)

    def test_propose_context_skips_hardlinked_prior_candidate_files(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        external_score = self.root / "archive" / "v2" / "prior-score.yml"
        external_score.parent.mkdir(parents=True, exist_ok=True)
        external_score.write_bytes(score_path.read_bytes())
        score_path.unlink()
        os.link(external_score, score_path)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-002",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        context_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-002" / "public-context.yml"
        context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
        self.assertEqual(context["prior_candidates"], [])

    def test_propose_context_skips_linked_prior_candidate_sidecars(self) -> None:
        for link_kind in ("symlink", "hardlink"):
            with self.subTest(link_kind=link_kind):
                self.tearDown()
                self.setUp()
                direction_path = self.write_direction()
                run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
                self.assertEqual(run.returncode, 0, run.stderr)
                evaluated = run_cli(
                    self.root,
                    "eval",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--patch",
                    str(self.write_patch()),
                    "--candidate-id",
                    "cand-001",
                )
                self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
                candidate_dir = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001"
                external_stdout = self.root / "archive" / "v2" / f"{link_kind}-stdout.log"
                external_stdout.parent.mkdir(parents=True, exist_ok=True)
                external_stdout.write_bytes((candidate_dir / "stdout.log").read_bytes())
                (candidate_dir / "stdout.log").unlink()
                if link_kind == "symlink":
                    (candidate_dir / "stdout.log").symlink_to(os.path.relpath(external_stdout, candidate_dir))
                else:
                    os.link(external_stdout, candidate_dir / "stdout.log")
                proposed = run_cli(
                    self.root,
                    "propose",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--candidate-id",
                    "cand-002",
                )
                self.assertEqual(proposed.returncode, 0, proposed.stderr)
                context_path = (
                    self.root
                    / ".harness"
                    / "search-runs"
                    / "run-001"
                    / "proposals"
                    / "cand-002"
                    / "public-context.yml"
                )
                context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
                self.assertEqual(context["prior_candidates"], [])

    def test_propose_context_does_not_glob_through_symlinked_prior_candidate_directory(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        candidates_dir = run_dir / "candidates"
        real_candidate_dir = run_dir / "cand-real"
        (candidates_dir / "cand-001").rename(real_candidate_dir)
        (candidates_dir / "cand-001").symlink_to("../cand-real", target_is_directory=True)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-002",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        context_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-002" / "public-context.yml"
        context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
        self.assertEqual(context["prior_candidates"], [])

    def test_propose_auto_candidate_id_does_not_glob_through_symlinked_candidates_store(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        external_candidates = self.root / "archive" / "v2" / "external-candidates"
        external_candidates.mkdir(parents=True)
        (external_candidates / "cand-999").mkdir()
        shutil.rmtree(run_dir / "candidates")
        (run_dir / "candidates").symlink_to("../../archive/v2/external-candidates", target_is_directory=True)
        proposed = run_cli(self.root, "propose", "--run", ".harness/search-runs/run-001")
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        self.assertIn("proposal_path:", proposed.stdout)
        self.assertTrue((run_dir / "proposals" / "cand-001" / "proposal.yml").is_file())
        self.assertFalse((run_dir / "proposals" / "cand-1000").exists())

    def test_propose_context_sanitizes_spaced_closure_paths(self) -> None:
        oracle_path = self.root / "benchmarks" / "oracle dir" / "expected output.txt"
        score_parser_path = self.root / "scripts" / "score parser.py"
        oracle_path.parent.mkdir(parents=True)
        oracle_path.write_text("expected\n", encoding="utf-8")
        score_parser_path.write_text("print('score parser')\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add spaced closure paths")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"] = ["benchmarks/oracle dir/expected output.txt"]
        direction["evaluator"]["score_parser_paths"] = ["scripts/score parser.py"]
        direction["evaluator"]["protected_paths"].append("scripts/score parser.py")
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
            "--why",
            "first try inspected benchmarks/oracle dir/expected output.txt",
            "--next-hypothesis",
            "then inspect scripts/score parser.py for hints",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-002",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_dir = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-002"
        context_text = (proposal_dir / "public-context.yml").read_text(encoding="utf-8")
        prompt = (proposal_dir / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("[sealed]", context_text)
        self.assertNotIn("benchmarks/oracle dir/expected output.txt", context_text)
        self.assertNotIn("scripts/score parser.py", context_text)
        self.assertNotIn("benchmarks/oracle dir/expected output.txt", prompt)
        self.assertNotIn("scripts/score parser.py", prompt)

    def test_propose_rejects_spaced_sealed_token(self) -> None:
        oracle_path = self.root / "benchmarks" / "oracle dir" / "expected output.txt"
        oracle_path.parent.mkdir(parents=True)
        oracle_path.write_text("expected\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add spaced oracle path")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["oracle_paths"] = ["benchmarks/oracle dir/expected output.txt"]
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--why",
            "looked at benchmarks/oracle dir/expected output.txt",
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("proposal.why must not expose sealed evaluator/oracle material", proposed.stderr)

    def test_propose_context_omits_public_summary_refs(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        summary = run_cli(
            self.root,
            "summarize",
            "--run",
            ".harness/search-runs/run-001",
            "--write-search-set",
        )
        self.assertEqual(summary.returncode, 0, summary.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-002",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        context = yaml.safe_load(
            (
                self.root
                / ".harness"
                / "search-runs"
                / "run-001"
                / "proposals"
                / "cand-002"
                / "public-context.yml"
            ).read_text(encoding="utf-8")
        )
        self.assertIsNone(context["public_run_refs"]["summary_ref"])
        self.assertIsNone(context["public_run_refs"]["search_set_ref"])

    def test_eval_proposal_rejects_public_summary_refs_reintroduced(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        context_path = proposal_path.with_name("public-context.yml")
        context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
        context["public_run_refs"]["summary_ref"] = "summary.yml"
        context["public_run_refs"]["search_set_ref"] = "search-set.yml"
        context_path.write_text(yaml.safe_dump(context, sort_keys=False), encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["context_sha256"] = file_sha256(context_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("public-context.yml public_run_refs.summary_ref must be null", evaluated.stderr)
        self.assertIn("public-context.yml public_run_refs.search_set_ref must be null", evaluated.stderr)

    def test_eval_proposal_rejects_out_of_run_bundle_without_traceback(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        with tempfile.TemporaryDirectory() as outside_tmp:
            outside = Path(outside_tmp)
            proposal_path = outside / "proposal.yml"
            proposal_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "strategy-search-proposal/v1",
                        "run_id": "run-001",
                        "candidate_id": "cand-001",
                        "status": "ready_for_evaluation",
                        "evidence_status": "diagnostic_only",
                        "base_commit": self.base_commit,
                        "direction_digest": "0" * 64,
                        "prompt_ref": "prompt.md",
                        "prompt_sha256": "0" * 64,
                        "policy_ref": "policy.yml",
                        "policy_sha256": "0" * 64,
                        "context_ref": "public-context.yml",
                        "context_sha256": "0" * 64,
                        "patch_ref": "patch.diff",
                        "patch_sha256": "0" * 64,
                        "why": "try it",
                        "next_hypothesis": "retry",
                        "validation_errors": [],
                        "evaluation_command": "python3 scripts/strategy-search.py eval --run x --proposal y",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            evaluated = run_cli(
                self.root,
                "eval",
                "--run",
                ".harness/search-runs/run-001",
                "--proposal",
                str(proposal_path),
            )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal.yml must be inside the search run directory", evaluated.stderr)
        self.assertNotIn("Traceback", evaluated.stderr)

    def test_eval_proposal_rejects_malformed_policy_without_traceback(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        policy_path = proposal_path.with_name("policy.yml")
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        policy.pop("allowed_write_paths")
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["policy_sha256"] = file_sha256(policy_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("policy.yml missing fields", evaluated.stderr)
        self.assertNotIn("Traceback", evaluated.stderr)

    def test_propose_rejects_public_metadata_with_sealed_token(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--why",
            "looked at stdout.log",
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("proposal.why must not expose sealed evaluator/oracle material", proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        self.assertFalse(proposal_path.exists())

    def test_public_sanitizer_rejects_decorated_relative_run_store_refs(self) -> None:
        direction = self.direction()
        for value in (
            "file:candidates/cand-001/trace.yml",
            "../candidates/cand-001/trace.yml",
            "../../candidates/cand-001/stdout.log",
            "../../summary.yml",
            "candidates/cand-001/patch.diff:1",
            "candidates/cand-001/patch.diff.",
            "candidates/cand-001/trace.yml:raw",
            "candidates/cand-001/trace.yml/raw",
            "candidates/cand-001/patch.diff:raw",
            "candidates/cand-001/patch.diff/raw",
            "candidates/cand-001/score.yml",
            "candidates/cand-001/score.yml=raw",
            "score.yml",
            "score.yml#L1",
            "score.yml?raw=1",
            "score.yml,raw",
            "score.yml=raw",
            "patch.diff:1",
            "patch.diff:raw",
            "patch.diff,raw",
            "patch.diff=raw",
            "patch.diff#L1",
            "patch.diff?raw=1",
            "patch.diff):1",
            "patch.diff:L1",
            "trace.yml:raw",
            "trace.yml,raw",
            "stdout.log:raw",
            "score . yml",
            "trace . yml",
            "patch . diff:raw",
            "candidates / cand-001 / trace . yml",
            "path:benchmarks/init-codex-harness/expected/output.txt",
            "scripts/score-init-codex-harness.py:L1",
            "scripts/score-init-codex-harness.py:1-2",
            "scripts/score-init-codex-harness.py=raw",
            "path:candidates/cand-001/stdout.log",
            "path:candidates/cand-001/stdout.log:raw",
            "file://localhost/candidates/cand-001/trace.yml",
            "vscode:file/candidates/cand-001/trace.yml",
            "cursor:file/candidates/cand-001/patch.diff?raw=1",
            "vscode://file/candidates/cand-001/trace.yml",
            "vscode ://file/candidates/cand-001/trace.yml",
            "vscode://file/candidates/cand-001/trace.yml:raw",
            "vscode://file:///candidates/cand-001/trace.yml:raw",
            "cursor://file/candidates/cand-001/patch.diff?raw=1",
            "vscode://file/patch.diff#L1",
            "scripts/score-init-codex-harness.py:raw",
            "scripts/score-init-codex-harness.py,raw",
            "vscode://file:///scripts/score-init-codex-harness.py:raw",
            "vscode ://file/scripts/score-init-codex-harness.py:raw",
            "benchmarks/init-codex-harness/expected/output.txt:raw",
            ":raw/candidates/cand-001/trace.yml",
            ",raw/candidates/cand-001/trace.yml",
            ":raw/patch.diff",
            "raw/candidates/cand-001/trace.yml",
            "direction.yml",
            "run.yml",
            "scores.jsonl",
            "proposals.jsonl",
            "summary.yml:raw",
            "search-set.yml:raw",
            "benchmarks / init-codex-harness / expected / output.txt",
        ):
            with self.subTest(value=value):
                errors: list[str] = []
                self.strategy.validate_no_forbidden_public_tokens(value, source="probe", direction=direction, errors=errors)
                self.assertTrue(errors, value)
                self.assertIn("must not expose sealed evaluator/oracle material", errors[0])

    def test_public_sanitizer_allows_declared_candidates_source_surface(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["candidates/model.md"]
        errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "update candidates/model.md",
            source="probe",
            direction=direction,
            errors=errors,
        )
        self.assertEqual(errors, [])

    def test_public_sanitizer_allows_source_path_with_forbidden_prefix_substring(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["benchmarks/init-codex-harness/expected-public.md"]
        errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "update benchmarks/init-codex-harness/expected-public.md",
            source="probe",
            direction=direction,
            errors=errors,
        )
        self.assertEqual(errors, [])

    def test_public_sanitizer_preserves_at_and_equals_in_file_names(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["src/foo@public.txt", "src/bar=public.txt"]
        direction["evaluator"]["oracle_paths"].extend(["src/foo", "src/foo@secret.txt", "src/bar", "src/bar=secret.txt"])
        for allowed in ("src/foo@public.txt", "src/bar=public.txt"):
            with self.subTest(allowed=allowed):
                errors: list[str] = []
                self.strategy.validate_no_forbidden_public_tokens(f"edit {allowed}", source="probe", direction=direction, errors=errors)
                self.assertEqual(errors, [])
        for sealed in ("src/foo@secret.txt", "src/bar=secret.txt"):
            with self.subTest(sealed=sealed):
                errors = []
                self.strategy.validate_no_forbidden_public_tokens(f"inspect {sealed}", source="probe", direction=direction, errors=errors)
                self.assertTrue(errors, sealed)
        for sealed_alias in ("src / foo @ secret . txt", "src/bar = secret.txt"):
            with self.subTest(sealed_alias=sealed_alias):
                errors = []
                self.strategy.validate_no_forbidden_public_tokens(f"inspect {sealed_alias}", source="probe", direction=direction, errors=errors)
                self.assertTrue(errors, sealed_alias)

    def test_public_sanitizer_rejects_raw_candidates_sidecar_even_with_broad_surface(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["candidates/"]
        errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "inspect candidates/cand-001/trace.yml",
            source="probe",
            direction=direction,
            errors=errors,
        )
        self.assertTrue(errors)
        self.assertIn("must not expose sealed evaluator/oracle material", errors[0])

    def test_public_sanitizer_file_surface_does_not_allow_raw_child_alias(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["trace.md"]
        exact_errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "edit trace.md",
            source="probe",
            direction=direction,
            errors=exact_errors,
        )
        self.assertEqual(exact_errors, [])
        for value in ("trace.md/raw", "vscode://file/trace.md/raw"):
            with self.subTest(value=value):
                errors: list[str] = []
                self.strategy.validate_no_forbidden_public_tokens(value, source="probe", direction=direction, errors=errors)
                self.assertTrue(errors, value)
                self.assertIn("must not expose sealed evaluator/oracle material", errors[0])

    def test_public_sanitizer_file_surface_child_alias_for_plain_file(self) -> None:
        direction = self.direction()
        errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "edit src/prompt.md",
            source="probe",
            direction=direction,
            errors=errors,
        )
        self.assertEqual(errors, [])
        for value in ("src/prompt.md/raw", "src/prompt.md,raw", "vscode://file/src/prompt.md/raw"):
            with self.subTest(value=value):
                errors = []
                self.strategy.validate_no_forbidden_public_tokens(value, source="probe", direction=direction, errors=errors)
                self.assertTrue(errors, value)
                self.assertIn("must not expose sealed evaluator/oracle material", errors[0])

    def test_public_sanitizer_allows_directory_surface_children_without_trailing_slash(self) -> None:
        direction = self.direction()
        direction["search_surface"] = ["src"]
        errors = self.strategy.validate_direction(direction, root=self.root)
        self.assertEqual(errors, [])
        self.assertEqual(direction["search_surface"], ["src/"])
        token_errors: list[str] = []
        self.strategy.validate_no_forbidden_public_tokens(
            "edit src/prompt.md",
            source="probe",
            direction=direction,
            errors=token_errors,
        )
        self.assertEqual(token_errors, [])

    def test_public_sanitizer_does_not_treat_extensionless_file_surface_as_directory(self) -> None:
        (self.root / "Makefile").write_text("all:\n\ttrue\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add extensionless file surface")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"] = ["Makefile"]
        direction["base_ref"] = self.base_commit
        errors = self.strategy.validate_direction(direction, root=self.root)
        self.assertEqual(errors, [])
        errors: list[str] = []
        for value in ("Makefile/raw", "Makefile:raw", "vscode://file/Makefile:raw"):
            with self.subTest(value=value):
                errors = []
                self.strategy.validate_no_forbidden_public_tokens(
                    f"edit {value}",
                    source="probe",
                    direction=direction,
                    errors=errors,
                )
                self.assertTrue(errors, value)
                self.assertIn("must not expose sealed evaluator/oracle material", errors[0])

    def test_public_sanitizer_rejects_special_character_sealed_paths(self) -> None:
        oracle_path = self.root / "benchmarks" / "oracle@v1" / "expected.txt"
        oracle_path.parent.mkdir(parents=True)
        oracle_path.write_text("sealed\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add special oracle")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["base_ref"] = self.base_commit
        direction["evaluator"]["oracle_paths"].append("benchmarks/oracle@v1/expected.txt")
        errors = self.strategy.validate_direction(direction, root=self.root)
        self.assertEqual(errors, [])
        for value in (
            "benchmarks/oracle@v1/expected.txt",
            "benchmarks / oracle@v1 / expected.txt",
        ):
            with self.subTest(value=value):
                token_errors: list[str] = []
                self.strategy.validate_no_forbidden_public_tokens(value, source="probe", direction=direction, errors=token_errors)
                self.assertTrue(token_errors, value)

    def test_sanitize_public_text_redacts_normalized_aliases(self) -> None:
        direction = self.direction()
        for value in (
            "proposals / cand-001 / proposal . yml",
            "benchmarks / init-codex-harness / expected / output.txt",
            "file://localhost/benchmarks/init-codex-harness/expected/output.txt:raw",
            "vscode://file:///scripts/score-init-codex-harness.py:raw",
        ):
            with self.subTest(value=value):
                sanitized = self.strategy.sanitize_public_text(value, direction)
                self.assertIn("[sealed]", sanitized)
                self.assertNotIn("proposal.yml", sanitized)
                self.assertNotIn("expected/output.txt", sanitized)
                self.assertNotIn("file://", sanitized)
                self.assertNotIn("score-init-codex-harness.py", sanitized)

    def test_propose_allows_sidecar_named_source_surface(self) -> None:
        (self.root / "trace.md").write_text("public source file\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "add trace named source")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["search_surface"] = ["trace.md"]
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--why",
            "edit trace.md as the allowed source file",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)

    def test_propose_rejects_scheme_and_spaced_sealed_paths(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        for index, why in enumerate((
            "path:benchmarks/init-codex-harness/expected/output.txt",
            "benchmarks / init-codex-harness / expected / output.txt",
            "scripts/score-init-codex-harness.py:L1",
        ), start=1):
            with self.subTest(why=why):
                proposed = run_cli(
                    self.root,
                    "propose",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--candidate-id",
                    f"cand-00{index}",
                    "--why",
                    why,
                )
                self.assertNotEqual(proposed.returncode, 0)
                self.assertIn("proposal.why must not expose sealed evaluator/oracle material", proposed.stderr)

    def test_propose_stores_patch_before_eval_and_eval_uses_fixed_runner(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch()
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(patch_path),
            "--why",
            "proposer tried a direct prompt replacement",
            "--next-hypothesis",
            "compare with a smaller edit",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        policy = yaml.safe_load(proposal_path.with_name("policy.yml").read_text(encoding="utf-8"))
        stored_patch = proposal_path.with_name("patch.diff")
        self.assertEqual(proposal["status"], "ready_for_evaluation")
        self.assertEqual(proposal["patch_sha256"], file_sha256(stored_patch))
        self.assertEqual(
            proposal["evaluation_command"],
            "python3 scripts/strategy-search.py eval --run <run> --proposal <proposal.yml> --overwrite",
        )
        self.assertEqual(policy["evaluation"]["runner"], proposal["evaluation_command"])
        self.assertNotIn(".harness/search-runs", proposal["evaluation_command"])
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(score_path.with_name("trace.yml").read_text(encoding="utf-8"))
        self.assertEqual(score["verdict"], "pass")
        self.assertEqual(file_sha256(score_path.with_name("patch.diff")), proposal["patch_sha256"])
        self.assertEqual(trace["why"], "proposer tried a direct prompt replacement")
        self.assertEqual(trace["next_hypothesis"], "compare with a smaller edit")

    def test_propose_rejects_linked_patch_sources_before_copying(self) -> None:
        for link_kind in ("symlink", "hardlink"):
            with self.subTest(link_kind=link_kind):
                self.tearDown()
                self.setUp()
                direction_path = self.write_direction()
                run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
                self.assertEqual(run.returncode, 0, run.stderr)
                real_patch = self.write_patch()
                linked_patch = self.root / f"{link_kind}-source.patch"
                if link_kind == "symlink":
                    linked_patch.symlink_to(real_patch.name)
                    expected = "patch source path must not contain symlinks"
                else:
                    os.link(real_patch, linked_patch)
                    expected = "patch source must not be hard-linked"
                proposed = run_cli(
                    self.root,
                    "propose",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--candidate-id",
                    "cand-001",
                    "--patch",
                    str(linked_patch),
                )
                self.assertNotEqual(proposed.returncode, 0)
                self.assertIn(expected, proposed.stderr)
                stored_patch = (
                    self.root
                    / ".harness"
                    / "search-runs"
                    / "run-001"
                    / "proposals"
                    / "cand-001"
                    / "patch.diff"
                )
                self.assertFalse(stored_patch.exists())

    def test_propose_rejects_patch_source_with_symlinked_parent_before_copying(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        real_dir = self.root / "real-patches"
        link_dir = self.root / "linked-patches"
        real_dir.mkdir()
        real_patch = real_dir / "candidate.diff"
        real_patch.write_bytes(self.write_patch().read_bytes())
        link_dir.symlink_to(real_dir, target_is_directory=True)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(link_dir / "candidate.diff"),
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("patch source path must not contain symlinks", proposed.stderr)
        stored_patch = (
            self.root
            / ".harness"
            / "search-runs"
            / "run-001"
            / "proposals"
            / "cand-001"
            / "patch.diff"
        )
        self.assertFalse(stored_patch.exists())

    def test_propose_rejects_symlinked_proposals_parent_before_writing(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        external_proposals = self.root / "archive" / "v2" / "proposals-out"
        external_proposals.mkdir(parents=True)
        shutil.rmtree(run_dir / "proposals")
        (run_dir / "proposals").symlink_to(external_proposals)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("proposal output path must not contain symlinks", proposed.stderr)
        self.assertFalse((external_proposals / "cand-001").exists())

    def test_propose_overwrite_replaces_prior_ledger_entry(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        first = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        first_proposal = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        first_eval = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(first_proposal),
        )
        self.assertEqual(first_eval.returncode, 0, first_eval.stderr)
        second = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
            "--overwrite",
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
            "--overwrite",
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)

    def test_propose_keeps_invalid_patch_diagnostic(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch(
            "diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n"
        )
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(patch_path),
        )
        self.assertNotEqual(proposed.returncode, 0)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "invalid")
        self.assertEqual(proposal["evaluation_command"], "")
        self.assertTrue((proposal_path.with_name("patch.diff")).is_file())
        self.assertIn("candidate patch must not touch evaluator closure", "\n".join(proposal["validation_errors"]))
        self.assertNotIn("benchmarks/init-codex-harness/run_cases.py", "\n".join(proposal["validation_errors"]))

    def test_propose_rejects_public_validation_error_tampering(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        for value, source in (
            (["see benchmarks/init-codex-harness/run_cases.py"], "proposal.validation_errors[0]"),
            ("see benchmarks/init-codex-harness/run_cases.py", "proposal.validation_errors"),
            ({"detail": "benchmarks/init-codex-harness/run_cases.py"}, "proposal.validation_errors.detail"),
            (
                {"outer": [{"inner": "benchmarks/init-codex-harness/run_cases.py"}]},
                "proposal.validation_errors.outer[0].inner",
            ),
            (
                {"benchmarks/init-codex-harness/run_cases.py": "hidden as key"},
                "proposal.validation_errors key",
            ),
        ):
            with self.subTest(value=value):
                proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
                proposal["validation_errors"] = value
                proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
                evaluated = run_cli(
                    self.root,
                    "eval",
                    "--run",
                    ".harness/search-runs/run-001",
                    "--proposal",
                    str(proposal_path),
                )
                self.assertNotEqual(evaluated.returncode, 0)
                self.assertIn(f"{source} must not expose sealed evaluator/oracle material", evaluated.stderr)

    def test_eval_proposal_rejects_symlinked_public_bundle_sidecar(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        context_path = proposal_path.with_name("public-context.yml")
        archive_context = self.root / "archive" / "v2" / "public-context.yml"
        archive_context.parent.mkdir(parents=True)
        archive_context.write_text("not: [valid\n", encoding="utf-8")
        context_path.unlink()
        context_path.symlink_to("../../../../../archive/v2/public-context.yml")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal public-context.yml must not be a symlink", evaluated.stderr)
        self.assertNotIn("could not parse YAML", evaluated.stderr)

    def test_eval_proposal_rejects_tampered_policy_runner(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        policy_path = proposal_path.with_name("policy.yml")
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        policy["evaluation"]["runner"] = "bad runner"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["policy_sha256"] = file_sha256(policy_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("policy.yml evaluation.runner must match", evaluated.stderr)

    def test_eval_proposal_seals_awaiting_patch_bundle(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        initial_proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(initial_proposal["status"], "awaiting_patch")
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertEqual(evaluated.returncode, 0, evaluated.stderr)
        sealed = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(sealed["status"], "ready_for_evaluation")
        self.assertEqual(sealed["patch_ref"], "patch.diff")
        self.assertEqual(sealed["patch_sha256"], file_sha256(proposal_path.with_name("patch.diff")))
        self.assertEqual(
            sealed["evaluation_command"],
            "python3 scripts/strategy-search.py eval --run <run> --proposal <proposal.yml> --overwrite",
        )
        self.assertNotIn(".harness/search-runs", sealed["evaluation_command"])
        ledger_lines = (
            self.root / ".harness" / "search-runs" / "run-001" / "proposals.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        ready_entries = [yaml.safe_load(line) for line in ledger_lines if "ready_for_evaluation" in line]
        self.assertEqual(len(ready_entries), 1)
        self.assertEqual(ready_entries[0]["proposal_sha256"], file_sha256(proposal_path))
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        self.assertEqual(score["verdict"], "pass")

    def test_eval_proposal_does_not_seal_awaiting_bundle_when_candidate_exists(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        (self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001").mkdir(parents=True)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("candidate already exists", evaluated.stderr)
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "awaiting_patch")
        ledger_lines = (
            self.root / ".harness" / "search-runs" / "run-001" / "proposals.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        self.assertFalse(any("ready_for_evaluation" in line for line in ledger_lines))

    def test_eval_proposal_does_not_seal_awaiting_bundle_when_ready_ledger_exists(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        ready_row = {
            "schema_version": self.strategy.PROPOSAL_LEDGER_SCHEMA_VERSION,
            "run_id": "run-001",
            "candidate_id": "cand-001",
            "proposal_ref": "proposals/cand-001/proposal.yml",
            "status": "ready_for_evaluation",
            "base_commit": proposal["base_commit"],
            "direction_digest": proposal["direction_digest"],
            "prompt_sha256": proposal["prompt_sha256"],
            "policy_sha256": proposal["policy_sha256"],
            "context_sha256": proposal["context_sha256"],
            "patch_sha256": file_sha256(proposal_path.with_name("patch.diff")),
            "proposal_sha256": file_sha256(proposal_path),
        }
        with (run_dir / "proposals.jsonl").open("a", encoding="utf-8") as ledger:
            ledger.write(json.dumps(ready_row, sort_keys=True) + "\n")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("ready_for_evaluation entry before sealing", evaluated.stderr)
        unsealed = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(unsealed["status"], "awaiting_patch")
        ledger_lines = (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines()
        ready_entries = [line for line in ledger_lines if "ready_for_evaluation" in line]
        self.assertEqual(len(ready_entries), 1)

    def test_eval_proposal_does_not_seal_awaiting_bundle_when_candidate_path_is_broken_symlink(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        (run_dir / "candidates" / "cand-001").symlink_to("missing-candidate")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("candidate already exists", evaluated.stderr)
        self.assertNotIn("Traceback", evaluated.stderr)
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "awaiting_patch")
        ledger_lines = (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertFalse(any("ready_for_evaluation" in line for line in ledger_lines))

    def test_eval_proposal_does_not_seal_awaiting_bundle_when_candidate_parent_is_symlink(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        external_candidates = self.root / "archive" / "v2" / "run-candidates"
        external_candidates.mkdir(parents=True)
        shutil.rmtree(run_dir / "candidates")
        (run_dir / "candidates").symlink_to(external_candidates)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("candidate output path must not contain symlinks", evaluated.stderr)
        self.assertFalse((external_candidates / "cand-001").exists())
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "awaiting_patch")
        ledger_lines = (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertFalse(any("ready_for_evaluation" in line for line in ledger_lines))

    def test_eval_proposal_does_not_seal_awaiting_bundle_when_keep_worktree_exists(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        (run_dir / "worktrees" / "cand-001").mkdir(parents=True)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
            "--keep-worktree",
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("kept worktree already exists", evaluated.stderr)
        self.assertFalse((run_dir / "candidates" / "cand-001").exists())
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "awaiting_patch")
        ledger_lines = (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertFalse(any("ready_for_evaluation" in line for line in ledger_lines))

    def test_eval_proposal_rejects_symlinked_keep_worktree_parent_before_export(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        external_worktrees = self.root / "archive" / "v2" / "worktrees-out"
        external_worktrees.mkdir(parents=True)
        (run_dir / "worktrees").symlink_to(external_worktrees)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
            "--keep-worktree",
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("kept worktree path must not contain symlinks", evaluated.stderr)
        self.assertFalse((external_worktrees / "cand-001").exists())

    def test_eval_proposal_rejects_symlinked_proposal_path_before_loading(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        external_proposal = self.root / "archive" / "v2" / "proposal-out"
        external_proposal.mkdir(parents=True)
        (external_proposal / "proposal.yml").write_text("not: canonical\n", encoding="utf-8")
        (external_proposal / "patch.diff").write_text("not a diff\n", encoding="utf-8")
        (run_dir / "proposals" / "linked").symlink_to(external_proposal)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            ".harness/search-runs/run-001/proposals/linked/proposal.yml",
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal path must not contain symlinks", evaluated.stderr)
        self.assertNotIn("proposal.yml missing fields", evaluated.stderr)

    def test_run_load_rejects_symlinked_ledgers(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        external = self.root / "archive" / "v2" / "proposals.jsonl"
        external.parent.mkdir(parents=True, exist_ok=True)
        external.write_text("", encoding="utf-8")
        (run_dir / "proposals.jsonl").unlink()
        (run_dir / "proposals.jsonl").symlink_to(external)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("run ledger file proposals.jsonl must not be a symlink", proposed.stderr)

    def test_run_load_rejects_hardlinked_ledgers(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        external = self.root / "archive" / "v2" / "proposals.jsonl"
        external.parent.mkdir(parents=True, exist_ok=True)
        external.write_text("", encoding="utf-8")
        (run_dir / "proposals.jsonl").unlink()
        os.link(external, run_dir / "proposals.jsonl")
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(proposed.returncode, 0)
        self.assertIn("run ledger file proposals.jsonl must not be hard-linked", proposed.stderr)

    def test_eval_proposal_rejects_hardlinked_awaiting_proposal_before_seal(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        run_dir = self.root / ".harness" / "search-runs" / "run-001"
        proposal_path = run_dir / "proposals" / "cand-001" / "proposal.yml"
        external = self.root / "archive" / "v2" / "proposal.yml"
        external.parent.mkdir(parents=True, exist_ok=True)
        external.write_bytes(proposal_path.read_bytes())
        proposal_path.unlink()
        os.link(external, proposal_path)
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal.yml must not be hard-linked", evaluated.stderr)
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "awaiting_patch")

    def test_eval_proposal_rejects_hardlinked_ready_proposal_before_loading(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        external = self.root / "archive" / "v2" / "ready-proposal.yml"
        external.parent.mkdir(parents=True, exist_ok=True)
        external.write_bytes(proposal_path.read_bytes())
        proposal_path.unlink()
        os.link(external, proposal_path)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal.yml must not be hard-linked", evaluated.stderr)

    def test_eval_proposal_rejects_symlinked_awaiting_patch_sidecar(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        real_patch = proposal_path.with_name("real.patch.diff")
        shutil.copyfile(
            self.write_patch(
                "diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n"
            ),
            real_patch,
        )
        proposal_path.with_name("patch.diff").symlink_to(real_patch.name)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal patch.diff must not be a symlink", evaluated.stderr)
        self.assertNotIn("candidate patch must not touch evaluator closure", evaluated.stderr)

    def test_eval_proposal_rejects_hardlinked_awaiting_patch_sidecar(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        external_patch = self.root / "archive" / "v2" / "patch.diff"
        external_patch.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.write_patch(), external_patch)
        os.link(external_patch, proposal_path.with_name("patch.diff"))
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal patch.diff must not be hard-linked", evaluated.stderr)

    def test_eval_proposal_rejects_awaiting_metadata_with_sealed_token(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["next_hypothesis"] = "read benchmarks/init-codex-harness/expected"
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("awaiting proposal ledger proposal_sha256 must match", evaluated.stderr)

    def test_eval_proposal_rejects_tampered_awaiting_bundle_before_seal(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["why"] = "changed after the awaiting ledger was written"
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        shutil.copyfile(self.write_patch(), proposal_path.with_name("patch.diff"))
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("awaiting proposal ledger proposal_sha256 must match", evaluated.stderr)

    def test_eval_proposal_rejects_tampered_stored_patch(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal_path.with_name("patch.diff").write_text(
            "diff --git a/src/prompt.md b/src/prompt.md\n",
            encoding="utf-8",
        )
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal.patch_sha256 must match patch.diff", evaluated.stderr)

    def test_eval_proposal_rejects_ready_patch_symlink_without_reading_target(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        real_patch = proposal_path.with_name("real.patch.diff")
        real_patch.write_text(
            "diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n",
            encoding="utf-8",
        )
        proposal_path.with_name("patch.diff").unlink()
        proposal_path.with_name("patch.diff").symlink_to(real_patch.name)
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal patch.diff must not be a symlink", evaluated.stderr)
        self.assertNotIn("candidate patch must not touch evaluator closure", evaluated.stderr)
        self.assertNotIn("proposal.patch_sha256 must match patch.diff", evaluated.stderr)

    def test_eval_proposal_rejects_tampered_public_bundle(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        context_path = proposal_path.with_name("public-context.yml")
        context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
        context["leaked_oracle_path"] = "benchmarks/init-codex-harness/expected/output.txt"
        context_path.write_text(yaml.safe_dump(context, sort_keys=False), encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["context_sha256"] = file_sha256(context_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("public-context.yml extra fields", evaluated.stderr)
        self.assertIn("proposal ledger context_sha256 must match", evaluated.stderr)

    def test_eval_proposal_rejects_escaped_sealed_yaml_value(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        context_path = proposal_path.with_name("public-context.yml")
        context_text = context_path.read_text(encoding="utf-8")
        context_text = context_text.replace(
            "\nnotes:\n- This proposer context is diagnostic-only strategy-search input.\n"
            "- It omits evaluator and oracle internals; the fixed evaluator is run only by eval.\n",
            '\nnotes:\n- "benchmarks/init-codex-harness/\\x65xpected/output.txt"\n',
        )
        context_path.write_text(context_text, encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["context_sha256"] = file_sha256(context_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("public-context.yml.notes[0] must not expose sealed evaluator/oracle material", evaluated.stderr)

    def test_eval_proposal_rejects_sealed_yaml_key(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        context_path = proposal_path.with_name("public-context.yml")
        context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
        sealed_bytes = b"benchmarks/init-codex-harness/expected/output.txt"
        utf16_bytes = "scripts/score-init-codex-harness.py".encode("utf-16-le")
        context["notes"] = [{sealed_bytes: "hidden as binary key"}, sealed_bytes, utf16_bytes]
        context_path.write_text(yaml.safe_dump(context, sort_keys=False), encoding="utf-8")
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["context_sha256"] = file_sha256(context_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("public-context.yml.notes[0] key must not expose sealed evaluator/oracle material", evaluated.stderr)
        self.assertIn("public-context.yml.notes[1] must not expose sealed evaluator/oracle material", evaluated.stderr)
        self.assertIn("public-context.yml.notes[2] must not contain binary YAML scalar", evaluated.stderr)
        self.assertIn("public-context.yml.notes[2] must not expose sealed evaluator/oracle material", evaluated.stderr)

    def test_eval_proposal_rejects_self_attested_patch_replacement(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        patch_path = proposal_path.with_name("patch.diff")
        patch_path.write_text(
            "\n".join(
                [
                    "diff --git a/src/prompt.md b/src/prompt.md",
                    "index 1111111..3333333 100644",
                    "--- a/src/prompt.md",
                    "+++ b/src/prompt.md",
                    "@@ -1 +1 @@",
                    "-old prompt",
                    "+different prompt",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["patch_sha256"] = file_sha256(patch_path)
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal ledger patch_sha256 must match", evaluated.stderr)

    def test_eval_proposal_rejects_forged_later_ledger_entry(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        ledger_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals.jsonl"
        ledger_entry = ledger_path.read_text(encoding="utf-8").splitlines()[-1]
        with ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(ledger_entry + "\n")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal ledger must contain exactly one", evaluated.stderr)

    def test_eval_proposal_rejects_malformed_ledger_row(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        ledger_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals.jsonl"
        original = ledger_path.read_text(encoding="utf-8")
        ledger_path.write_text("{malformed-json\n" + original, encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("malformed JSONL row 1", evaluated.stderr)

    def test_eval_proposal_rejects_tampered_replay_command(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        proposed = run_cli(
            self.root,
            "propose",
            "--run",
            ".harness/search-runs/run-001",
            "--candidate-id",
            "cand-001",
            "--patch",
            str(self.write_patch()),
        )
        self.assertEqual(proposed.returncode, 0, proposed.stderr)
        proposal_path = self.root / ".harness" / "search-runs" / "run-001" / "proposals" / "cand-001" / "proposal.yml"
        proposal = yaml.safe_load(proposal_path.read_text(encoding="utf-8"))
        proposal["evaluation_command"] = (
            "python3 scripts/strategy-search.py eval --run .harness/search-runs/run-001 "
            "--proposal .harness/search-runs/run-001/proposals/cand-001/proposal.yml"
        )
        proposal_path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
        evaluated = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--proposal",
            str(proposal_path),
        )
        self.assertNotEqual(evaluated.returncode, 0)
        self.assertIn("proposal.evaluation_command must not expose sealed evaluator/oracle material", evaluated.stderr)

    def test_eval_rejects_protected_patch_before_workspace_creation(self) -> None:
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch(
            "diff --git a/benchmarks/init-codex-harness/run_cases.py b/benchmarks/init-codex-harness/run_cases.py\n"
        )
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(patch_path),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("candidate patch must not touch evaluator closure", completed.stderr)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        self.assertEqual(yaml.safe_load(score_path.read_text(encoding="utf-8"))["verdict"], "invalid")

    def test_eval_rejects_archive_side_effects(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "Path('archive/v2/packets').mkdir(parents=True, exist_ok=True)",
                    "Path('archive/v2/packets/side.yml').write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch()
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(patch_path),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        self.assertEqual(yaml.safe_load(score_path.read_text(encoding="utf-8"))["verdict"], "invalid")
        stderr_log = score_path.with_name("stderr.log").read_text(encoding="utf-8")
        self.assertIn("candidate workspace must not write archive/v2", stderr_log)

    def test_validate_candidate_rejects_invalid_side_effect_promoted_to_pass(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "Path('archive/v2/packets').mkdir(parents=True, exist_ok=True)",
                    "Path('archive/v2/packets/side.yml').write_text('bad\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["verdict"] = "pass"
        trace["result"]["verdict"] = "pass"
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("strategy-search invalid diagnostics", accepted.stderr)

    def test_eval_rejects_source_repo_side_effects(self) -> None:
        side_effect_path = self.root / "archive" / "v2" / "packets" / "source-side-effect.yml"
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"target = Path({str(side_effect_path)!r})",
                    "target.parent.mkdir(parents=True, exist_ok=True)",
                    "target.write_text('bad\\\\n')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "source side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        self.assertEqual(yaml.safe_load(score_path.read_text(encoding="utf-8"))["verdict"], "invalid")
        self.assertIn("source repository", score_path.with_name("stderr.log").read_text(encoding="utf-8"))
        self.assertFalse(side_effect_path.exists())

    def test_eval_restores_source_file_mode_side_effects(self) -> None:
        target = self.root / "src" / "prompt.md"
        original_mode = target.stat().st_mode & 0o777
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(target)!r}).chmod(0o700)",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "chmod side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(target.stat().st_mode & 0o777, original_mode)

    def test_eval_restores_source_directory_mode_side_effects(self) -> None:
        target = self.root / "src"
        original_mode = target.stat().st_mode & 0o777
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    f"Path({str(target)!r}).chmod(0o700)",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "directory chmod side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(target.stat().st_mode & 0o777, original_mode)

    def test_eval_rejects_search_surface_symlink_side_effect(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "\n".join(
                [
                    "from pathlib import Path",
                    "target = Path('src/prompt.md')",
                    "target.unlink()",
                    "target.symlink_to('../benchmarks/init-codex-harness/run_cases.py')",
                    "print('score: 0.97')",
                    "print('case: fresh-empty-repo: pass')",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "symlink side-effect evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction_path = self.write_direction()
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        self.assertEqual(yaml.safe_load(score_path.read_text(encoding="utf-8"))["verdict"], "invalid")
        self.assertIn("symlink", score_path.with_name("stderr.log").read_text(encoding="utf-8"))

    def test_eval_records_timeout_as_failure(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "import time\ntime.sleep(2)\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "slow evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["timeout_seconds"] = 1
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        patch_path = self.write_patch()
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(patch_path),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        self.assertEqual(score["verdict"], "fail")
        self.assertEqual(score["exit_code"], 124)
        self.assertIn("timed out", score_path.with_name("stderr.log").read_text(encoding="utf-8"))

    def test_validate_candidate_rejects_trace_timeout_drift(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "import time\ntime.sleep(2)\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "slow evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["timeout_seconds"] = 1
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        trace_path = score_path.with_name("trace.yml")
        original_score_text = score_path.read_text(encoding="utf-8")
        original_trace_text = trace_path.read_text(encoding="utf-8")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["exit_code"] = 0
        trace["result"]["exit_code"] = 0
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("timeout diagnostics require exit_code 124", accepted.stderr)

        score_path.write_text(original_score_text, encoding="utf-8")
        trace_path.write_text(original_trace_text, encoding="utf-8")
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        trace = yaml.safe_load(trace_path.read_text(encoding="utf-8"))
        score["exit_code"] = 0
        score["score"] = 1.0
        score["case_results"] = [{"case_id": "evaluator", "status": "pass"}]
        score["verdict"] = "pass"
        trace["result"]["exit_code"] = 0
        trace["result"]["score"] = 1.0
        trace["result"]["case_results"] = [{"case_id": "evaluator", "status": "pass"}]
        trace["result"]["verdict"] = "pass"
        trace["result"]["timed_out"] = False
        trace_path.write_text(yaml.safe_dump(trace, sort_keys=False), encoding="utf-8")
        score["trace_sha256"] = file_sha256(trace_path)
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("trace.result.timed_out must match", accepted.stderr)
        self.assertIn("timeout diagnostics require exit_code 124", accepted.stderr)
        self.assertIn("timeout diagnostics must not validate as verdict pass", accepted.stderr)

    def test_validate_candidate_rejects_timeout_with_forged_typed_results(self) -> None:
        (self.root / "benchmarks" / "init-codex-harness" / "run_cases.py").write_text(
            "import time\ntime.sleep(2)\n",
            encoding="utf-8",
        )
        git(self.root, "add", "-A")
        git(self.root, "commit", "-m", "slow evaluator")
        self.base_commit = git(self.root, "rev-parse", "HEAD")
        direction = self.direction()
        direction["evaluator"]["timeout_seconds"] = 1
        direction_path = self.write_direction(direction)
        run = run_cli(self.root, "start", "--direction", str(direction_path), "--run-id", "run-001")
        self.assertEqual(run.returncode, 0, run.stderr)
        completed = run_cli(
            self.root,
            "eval",
            "--run",
            ".harness/search-runs/run-001",
            "--patch",
            str(self.write_patch()),
            "--candidate-id",
            "cand-001",
        )
        self.assertNotEqual(completed.returncode, 0)
        score_path = self.root / ".harness" / "search-runs" / "run-001" / "candidates" / "cand-001" / "score.yml"
        score = yaml.safe_load(score_path.read_text(encoding="utf-8"))
        score["score"] = 0.97
        score["case_results"] = [{"case_id": "fresh-empty-repo", "status": "pass"}]
        score_path.write_text(yaml.safe_dump(score, sort_keys=False), encoding="utf-8")
        accepted = run_cli(
            self.root,
            "validate-candidate",
            "--direction",
            str(direction_path),
            "--candidate",
            str(score_path),
        )
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("timeout diagnostics must use the canonical fail score", accepted.stderr)


if __name__ == "__main__":
    unittest.main()
