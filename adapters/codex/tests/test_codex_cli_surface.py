#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "check-codex-cli-surface.py"

spec = importlib.util.spec_from_file_location("check_codex_cli_surface", SCRIPT)
assert spec and spec.loader
surface = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = surface
spec.loader.exec_module(surface)


def write_fake_codex(
    path: Path,
    *,
    marketplace: str,
    app_server: str,
    fail_marketplace: bool = False,
    fail_app_server: bool = False,
) -> None:
    body = f"""#!/bin/sh
set -eu
if [ "$1" = "plugin" ] && [ "$2" = "marketplace" ] && [ "$3" = "--help" ]; then
  if [ "{str(fail_marketplace).lower()}" = "true" ]; then
    echo "marketplace help failed" >&2
    exit 17
  fi
  cat <<'EOF'
{marketplace}
EOF
  exit 0
fi
if [ "$1" = "app-server" ] && [ "$2" = "--help" ]; then
  if [ "{str(fail_app_server).lower()}" = "true" ]; then
    echo "app-server help failed" >&2
    exit 18
  fi
  cat <<'EOF'
{app_server}
EOF
  exit 0
fi
echo "unexpected args: $*" >&2
exit 64
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


class CodexCliSurfaceTests(unittest.TestCase):
    def test_probe_accepts_expected_marketplace_and_app_server_help(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_codex = Path(tmp) / "codex"
            write_fake_codex(
                fake_codex,
                marketplace=textwrap.dedent(
                    """\
                    Manage plugin marketplaces for Codex
                    Commands:
                      add
                      upgrade
                      remove
                    """
                ),
                app_server=textwrap.dedent(
                    """\
                    [experimental] Run the app server or related tooling
                    Commands:
                      generate-ts
                      generate-json-schema
                    """
                ),
            )

            result = surface.probe(str(fake_codex))

            self.assertFalse(result.skipped)
            self.assertEqual(result.errors, ())

    def test_probe_rejects_missing_help_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_codex = Path(tmp) / "codex"
            write_fake_codex(
                fake_codex,
                marketplace="Commands:\n  add\n  remove\n",
                app_server="Run the app server\nCommands:\n  generate-ts\n",
            )

            result = surface.probe(str(fake_codex))

            self.assertFalse(result.skipped)
            self.assertIn("MISSING PLUGIN MARKETPLACE HELP MARKER: upgrade", result.errors)
            self.assertIn("MISSING APP-SERVER HELP MARKER: [experimental]", result.errors)
            self.assertIn("MISSING APP-SERVER HELP MARKER: generate-json-schema", result.errors)

    def test_probe_skips_when_codex_is_missing_by_default(self) -> None:
        result = surface.probe("definitely-not-installed-codex-for-test")

        self.assertTrue(result.skipped)
        self.assertEqual(result.errors, ("SKIPPED: Codex CLI not found: definitely-not-installed-codex-for-test",))

    def test_probe_can_require_installed_codex(self) -> None:
        result = surface.probe("definitely-not-installed-codex-for-test", require_installed=True)

        self.assertFalse(result.skipped)
        self.assertEqual(result.errors, ("MISSING CODEX CLI: definitely-not-installed-codex-for-test",))

    def test_probe_reports_help_command_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_codex = Path(tmp) / "codex"
            write_fake_codex(
                fake_codex,
                marketplace="unused",
                app_server="unused",
                fail_marketplace=True,
                fail_app_server=True,
            )

            result = surface.probe(str(fake_codex))

            self.assertFalse(result.skipped)
            self.assertIn("CODEX PLUGIN MARKETPLACE HELP FAILED: 17", result.errors)
            self.assertTrue(any("marketplace help failed" in error for error in result.errors), result.errors)
            self.assertIn("CODEX APP-SERVER HELP FAILED: 18", result.errors)
            self.assertTrue(any("app-server help failed" in error for error in result.errors), result.errors)

    def test_main_reports_skip_and_required_missing_cli(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            skip_code = surface.main(["--codex-bin", "definitely-not-installed-codex-for-test"])

        self.assertEqual(skip_code, 0)
        self.assertIn("SKIPPED: Codex CLI not found", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            fail_code = surface.main(
                ["--codex-bin", "definitely-not-installed-codex-for-test", "--require-installed"]
            )

        self.assertEqual(fail_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("MISSING CODEX CLI", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
