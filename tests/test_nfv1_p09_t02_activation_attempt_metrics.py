"""P09-T02: commercial activation attempts are bounded, not approval authority."""

import pytest

from kordena_fiscal.runtime.api import _record_commercial_activation_attempt
from kordena_fiscal.runtime.observability import MetricsRegistry


def test_activation_attempt_counts_success_without_identity() -> None:
    metrics = MetricsRegistry()
    called = []
    _record_commercial_activation_attempt(lambda: called.append(True), metrics)
    assert called == [True]
    assert any(
        item["name"] == "nfcore_commercial_activation_attempts_total"
        and item["labels"] == {"outcome": "succeeded"}
        and item["value"] == 1
        for item in metrics.as_dicts()
    )


def test_activation_error_preserved_and_counted() -> None:
    metrics = MetricsRegistry()

    def fail() -> None:
        raise RuntimeError("activation rejected")

    with pytest.raises(RuntimeError, match="activation rejected"):
        _record_commercial_activation_attempt(fail, metrics)
    assert any(
        item["name"] == "nfcore_commercial_activation_attempts_total"
        and item["labels"] == {"outcome": "failed"}
        and item["value"] == 1
        for item in metrics.as_dicts()
    )
    assert all("activation rejected" not in str(x) for x in metrics.as_dicts())


def test_telemetry_failure_cannot_change_success_or_failure() -> None:
    class BrokenMetrics(MetricsRegistry):
        def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
            raise RuntimeError("telemetry unavailable")

    _record_commercial_activation_attempt(lambda: None, BrokenMetrics())

    def fail() -> None:
        raise ValueError("original domain error")

    with pytest.raises(ValueError, match="original domain error"):
        _record_commercial_activation_attempt(fail, BrokenMetrics())
