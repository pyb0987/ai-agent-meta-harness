import unittest


class RootUnittestDiscoveryGuard(unittest.TestCase):
    def test_use_explicit_unittest_roots(self):
        self.fail(
            "Do not use plain `python3 -m unittest discover` from the "
            "repository root as a verification signal. It can miss the real "
            "test suites. Run the explicit Standard verification unittest "
            "commands instead: `python3 -m unittest discover -s tests`, "
            "`python3 -m unittest discover -s adapters/claude/tests`, and "
            "`python3 -m unittest discover -s adapters/codex/tests`."
        )
