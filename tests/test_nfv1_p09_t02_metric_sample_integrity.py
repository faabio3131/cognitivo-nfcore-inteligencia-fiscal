"""P09-T02: invalid operational samples cannot poison the canonical metrics registry."""

import math

import pytest

from kordena_fiscal.runtime.observability import MetricsRegistry


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf"), -1.0])
def test_invalid_counter_value_does_not_mutate_snapshot(invalid: float) -> None:
    metrics = MetricsRegistry()
    with pytest.raises(ValueError, match="finite and non-negative"):
        metrics.increment("nfcore_provider_errors_total", invalid, outcome="error")
    assert metrics.snapshot() == ()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf"), -0.1])
def test_invalid_latency_does_not_create_partial_observation(invalid: float) -> None:
    metrics = MetricsRegistry()
    with pytest.raises(ValueError, match="finite and non-negative"):
        metrics.observe_seconds("nfcore_provider", invalid, outcome="error")
    assert metrics.snapshot() == ()


def test_valid_latency_updates_both_samples() -> None:
    metrics = MetricsRegistry()
    metrics.observe_seconds("nfcore_provider", 0.125, outcome="error")
    values = {sample.name: sample.value for sample in metrics.snapshot()}
    assert values == {"nfcore_provider_count": 1.0, "nfcore_provider_seconds_total": 0.125}
    assert all(math.isfinite(value) for value in values.values())


def test_invalid_metric_labels_leave_no_partial_latency_sample() -> None:
    metrics = MetricsRegistry()
    with pytest.raises(ValueError, match="unsupported"):
        metrics.observe_seconds("nfcore_provider", 0.1, tenant_id="private")
    assert metrics.snapshot() == ()
