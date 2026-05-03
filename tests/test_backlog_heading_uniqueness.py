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


class BacklogHeadingUniquenessTests(unittest.TestCase):
    def test_active_backlog_numbered_headings_are_unique_per_file(self) -> None:
        for path in ACTIVE_BACKLOGS:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                numbers = [match.group("number") for match in HEADING_RE.finditer(text)]
                duplicates = sorted(number for number, count in Counter(numbers).items() if count > 1)
                self.assertEqual(duplicates, [])


if __name__ == "__main__":
    unittest.main()
