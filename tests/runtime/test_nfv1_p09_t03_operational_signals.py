"""Explicit operational evidence and rejection-rate denominators, fail closed."""

import pytest

from kordena_fiscal.runtime.alert_rules import (
    InternalAlertMonitor,
    OperationalSignals,
    evaluate_operational_signals,
    fiscal_rejection_rate,
)
from kordena_fiscal.runtime.observability import MetricsRegistry


def test_operational_signals_missing_is_unknown_and_explicit_failures_alert() -> None:
    assert evaluate_operational_signals(OperationalSignals()) == ()
    observed = evaluate_operational_signals(OperationalSignals(
        certificate_days_remaining=7, secret_resolution_ok=False,
        database_ready=False, deployment_healthy=False,
    ))
    assert {a.code for a in observed} == {
        "certificate_expiry", "secret_failure", "db_unavailable", "deployment_unhealthy"
    }
    with pytest.raises(ValueError):
        evaluate_operational_signals(OperationalSignals(certificate_days_remaining=float("nan")))


def test_rejection_rate_requires_finalized_denominator_and_two_samples() -> None:
    registry = MetricsRegistry()
    registry.increment("nfcore_fiscal_rejections_total", 1)
    assert fiscal_rejection_rate(registry.snapshot(), ()) is None
    registry.increment("nfcore_fiscal_authorizations_finalized_total", 10)
    previous = registry.snapshot()
    registry.increment("nfcore_fiscal_rejections_total", 2)
    registry.increment("nfcore_fiscal_authorizations_finalized_total", 5)
    candidate = fiscal_rejection_rate(registry.snapshot(), previous)
    assert candidate is not None
    assert candidate.observed == 0.4
    assert candidate.code == "fiscal_rejection_rate"


def test_monitor_polls_registry_without_duplicate_counter_alerts() -> None:
    registry = MetricsRegistry()
    monitor = InternalAlertMonitor(registry)
    assert monitor.poll() == ()
    registry.increment("nfcore_http_requests_total", status_class="5xx")
    assert {a.code for a in monitor.poll()} == set()
    registry.increment("nfcore_http_requests_total", status_class="5xx")
    assert {a.code for a in monitor.poll(signals=OperationalSignals(database_ready=False))} == {
        "http_5xx", "db_unavailable"
    }
    assert monitor.poll() == ()
