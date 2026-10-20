"""BLD-03: deterministic shared limiter contract and fail-closed persistence."""

from contextlib import contextmanager
from datetime import UTC, datetime

from kordena_fiscal.runtime.public_trial_abuse import PostgresPublicTrialAbuseGate, SCHEMA


class Cursor:
    def __init__(self, row: tuple[int] | None) -> None:
        self.row = row

    def fetchone(self) -> tuple[int] | None:
        return self.row


class Store:
    def __init__(self) -> None:
        self.windows: dict[tuple[str, int], int] = {}
        self.broken = False

    @contextmanager
    def connection(self):
        yield self

    def execute(self, statement, params=()):
        if self.broken:
            raise RuntimeError("database unavailable")
        assert "ON CONFLICT" in statement
        identity, window, limit = params
        key = (identity, window)
        current = self.windows.get(key, 0)
        if current >= limit:
            return Cursor(None)
        self.windows[key] = current + 1
        return Cursor((current + 1,))


def test_shared_limiter_counts_across_instances_and_windows() -> None:
    store = Store()
    first = PostgresPublicTrialAbuseGate(store.connection, max_requests=2)
    second = PostgresPublicTrialAbuseGate(store.connection, max_requests=2)
    now = datetime(2026, 10, 20, 15, tzinfo=UTC)
    assert first.allow("198.51.100.3", now)
    assert second.allow("198.51.100.3", now)
    assert not first.allow("198.51.100.3", now)
    assert second.allow("198.51.100.4", now)
    assert first.allow("198.51.100.3", datetime(2026, 10, 20, 16, tzinfo=UTC))
    assert all("198.51.100.3" not in key for key in store.windows)
    assert "CREATE TABLE fm_public_trial_rate_windows" in SCHEMA


def test_shared_limiter_denies_storage_failure_and_invalid_identity() -> None:
    store = Store()
    limiter = PostgresPublicTrialAbuseGate(store.connection)
    now = datetime(2026, 10, 20, 15, tzinfo=UTC)
    assert not limiter.allow("", now)
    store.broken = True
    assert not limiter.allow("198.51.100.3", now)
