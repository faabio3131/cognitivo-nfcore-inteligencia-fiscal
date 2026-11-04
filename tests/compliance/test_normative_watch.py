"""No external HTTP during tests; periodic monitoring remains non-authoritative."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from kordena_fiscal.compliance.normative_watch import (
    SOURCES,
    NormativeWatchError,
    fetch_official_portal,
    poll_normative_sources,
)


def test_first_poll_change_and_unchanged(tmp_path: Path) -> None:
    counter = {"n": 0}

    def fetch(url: str) -> bytes:
        return ("first:" + url + str(counter["n"])).encode()

    when = datetime(2026, 11, 3, tzinfo=UTC)
    state = tmp_path / "watch-state.json"
    first = poll_normative_sources(state_path=state, fetch=fetch, observed_at=when)
    assert len(first) == len(SOURCES) == 4
    assert all(e["status"] == "FIRST_OBSERVATION_REVIEW_REQUIRED" for e in first)
    assert all(e["normative_approved"] == "false" for e in first)
    second = poll_normative_sources(state_path=state, fetch=fetch, observed_at=when)
    assert all(e["status"] == "UNCHANGED" for e in second)
    counter["n"] = 1
    third = poll_normative_sources(state_path=state, fetch=fetch, observed_at=when)
    assert all(e["status"] == "PORTAL_CONTENT_CHANGED_REVIEW_REQUIRED" for e in third)
    saved = json.loads(state.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 1
    assert set(saved["hashes"]) == set(SOURCES)


def test_failed_fetch_preserves_previous_snapshot(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    poll_normative_sources(state_path=state, fetch=lambda url: b"baseline")
    original = state.read_bytes()

    def bad(url: str) -> bytes:
        if "svrs" in url:
            raise NormativeWatchError("unreachable")
        return b"modified"

    with pytest.raises(NormativeWatchError):
        poll_normative_sources(state_path=state, fetch=bad)
    assert state.read_bytes() == original
    assert not (tmp_path / "state.json.lock").exists()


def test_corrupt_checkpoint_and_parallel_poll_fail_closed(tmp_path: Path) -> None:
    state = tmp_path / "watch.json"
    state.write_text("{}", encoding="utf-8")
    with pytest.raises(NormativeWatchError):
        poll_normative_sources(state_path=state, fetch=lambda url: b"x")
    state.unlink()
    (tmp_path / "watch.json.lock").write_text("locked", encoding="utf-8")
    with pytest.raises(NormativeWatchError):
        poll_normative_sources(state_path=state, fetch=lambda url: b"x")
    assert not state.exists()


def test_no_unapproved_url_fetch() -> None:
    with pytest.raises(NormativeWatchError):
        fetch_official_portal("https://localhost/metadata")


def test_invalid_bytes_and_relative_state_rejected(tmp_path: Path) -> None:
    with pytest.raises(NormativeWatchError):
        poll_normative_sources(state_path=Path("relative"), fetch=lambda url: b"x")
    with pytest.raises(NormativeWatchError):
        poll_normative_sources(state_path=tmp_path / "state.json", fetch=lambda url: b"")
