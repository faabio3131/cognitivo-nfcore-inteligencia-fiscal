"""P09-T02: duration samples have atomic count and total updates."""

import sys

import pytest

from kordena_fiscal.runtime.observability import MetricsRegistry


def test_repeated_duration_observations_update_both_values() -> None:
    metrics = MetricsRegistry()
    metrics.observe_seconds("nfcore_worker_dispatch", 0.25, outcome="failed")
    metrics.observe_seconds("nfcore_worker_dispatch", 0.75, outcome="failed")
    samples = {sample.name: sample.value for sample in metrics.snapshot()}
    assert samples == {
        "nfcore_worker_dispatch_count": 2.0,
        "nfcore_worker_dispatch_seconds_total": 1.0,
    }


def test_duration_overflow_preserves_both_previous_samples() -> None:
    metrics = MetricsRegistry()
    metrics.observe_seconds("nfcore_worker_dispatch", sys.float_info.max, outcome="failed")
    before = metrics.snapshot()
    with pytest.raises(ValueError, match="accumulation must remain finite"):
        metrics.observe_seconds("nfcore_worker_dispatch", sys.float_info.max, outcome="failed")
    assert metrics.snapshot() == before


def test_bad_labels_leave_no_duration_samples() -> None:
    metrics = MetricsRegistry()
    with pytest.raises(ValueError, match="unsupported"):
        metrics.observe_seconds("nfcore_worker_dispatch", 0.5, tenant_id="secret")
    assert metrics.snapshot() == ()
