"""Offline contract tests for the canonical P05 staging smoke shell script.

A fake curl is supplied via PATH. No actual HTTP requests or provider credentials.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SMOKE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "staging_smoke.sh"

FAKE_CURL = """#!/bin/sh
last=""
for item do
  last="$item"
done
case "$last" in
  */health/live) exit 0 ;;
  */health/ready)
    if [ "${FAKE_SMOKE_SCENARIO:-}" = "not_ready" ]; then exit 22; fi
    exit 0 ;;
  */runtime/profile)
    if [ "${FAKE_SMOKE_SCENARIO:-}" = "bad_profile" ]; then
      printf '%s' '{"environment":"production"}'
    else
      printf '%s' '{"environment":"staging","persistence_backend":"postgres",' \
        '"secret_backend_profile":"external","https_required":true,' \
        '"fiscal_production_activated":false}'
    fi ;;
  */v1/portal/bootstrap)
    case "${FAKE_SMOKE_SCENARIO:-}" in
      bootstrap_open) printf '200' ;;
      bootstrap_forbidden) printf '403' ;;
      bootstrap_unreachable) exit 28 ;;
      *) printf '401' ;;
    esac ;;
  https://portal.example.test/) exit 0 ;;
  *) printf '%s\\n' "unexpected smoke URL" >&2; exit 9 ;;
esac
"""


@pytest.mark.skipif(os.name == "nt" or shutil.which("sh") is None, reason="POSIX smoke contract")
@pytest.mark.parametrize(
    ("scenario", "expected_ok"),
    [
        ("good", True),
        ("bootstrap_open", False),
        ("bootstrap_forbidden", False),
        ("bootstrap_unreachable", False),
        ("bad_profile", False),
        ("not_ready", False),
    ],
)
def test_staging_smoke_fail_closed(tmp_path: Path, scenario: str, expected_ok: bool) -> None:
    fake_curl = tmp_path / "curl"
    fake_curl.write_text(FAKE_CURL, encoding="utf-8")
    fake_curl.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}",
        "FAKE_SMOKE_SCENARIO": scenario,
    }
    result = subprocess.run(
        ["sh", str(SMOKE_SCRIPT), "https://api.example.test", "https://portal.example.test"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert (result.returncode == 0) is expected_ok, result.stdout + result.stderr
    if scenario == "good":
        assert "staging smoke: PASS" in result.stdout
    if scenario in {"bootstrap_open", "bootstrap_forbidden"}:
        assert "unauthenticated portal bootstrap" in result.stdout


@pytest.mark.skipif(os.name == "nt" or shutil.which("sh") is None, reason="POSIX smoke contract")
@pytest.mark.parametrize(
    ("api", "portal"),
    [
        ("http://api.example.test", "https://portal.example.test"),
        ("https://api.example.test", "http://portal.example.test"),
    ],
)
def test_staging_smoke_requires_https(api: str, portal: str) -> None:
    result = subprocess.run(
        ["sh", str(SMOKE_SCRIPT), api, portal],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode != 0
    assert "HTTPS URL required" in result.stdout
