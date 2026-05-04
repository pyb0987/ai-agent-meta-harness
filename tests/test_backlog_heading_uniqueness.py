from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_BACKLOGS = (
    ROOT / "backlog" / "core.md",
    ROOT / "backlog" / "claude-adapter.md",
    ROOT / "backlog" / "codex-adapter.md",
)
HEADING_RE = re.compile(r"^### (?P<number>\d+)\. (?P<title>.+)$", re.MULTILINE)
SECTION_RE = re.compile(r"^### (?P<number>\d+)\. .+?(?=^### \d+\. |\Z)", re.MULTILINE | re.DOTALL)
STATUS_RE = re.compile(r"^Status:\s*(?P<status>\S+)", re.MULTILINE)
CURRENT_STATUS_RE = re.compile(r"^## Current Status\n(?P<body>.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL)
ACTIVE_ITEM_RE = re.compile(r"\bitem (?P<number>\d+) should\b")


class BacklogHeadingUniquenessTests(unittest.TestCase):
    def test_active_backlog_numbered_headings_are_unique_per_file(self) -> None:
        for path in ACTIVE_BACKLOGS:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                numbers = [match.group("number") for match in HEADING_RE.finditer(text)]
                duplicates = sorted(number for number, count in Counter(numbers).items() if count > 1)
                self.assertEqual(duplicates, [])

    def test_core_current_status_active_candidates_are_waiting(self) -> None:
        path = ROOT / "backlog" / "core.md"
        text = path.read_text(encoding="utf-8")
        current_status = CURRENT_STATUS_RE.search(text)
        self.assertIsNotNone(current_status, "backlog/core.md must keep a Current Status block")

        statuses: dict[str, str] = {}
        for section in SECTION_RE.finditer(text):
            status = STATUS_RE.search(section.group(0))
            if status:
                statuses[section.group("number")] = status.group("status")

        active_candidates = sorted(set(ACTIVE_ITEM_RE.findall(current_status.group("body"))), key=int)
        not_waiting = {
            number: statuses.get(number, "<missing>")
            for number in active_candidates
            if statuses.get(number) != "대기"
        }
        self.assertEqual(not_waiting, {})


if __name__ == "__main__":
    unittest.main()
