"""P09-T03 deterministic candidate alerts: no side effects, no false green."""

from kordena_fiscal.runtime.alert_rules import evaluate_alert_candidates
from kordena_fiscal.runtime.observability import MetricsRegistry


def test_alert_candidates_use_existing_low_cardinality_metrics() -> None:
    metrics = MetricsRegistry()
    metrics.increment("nfcore_http_requests_total", status_class="5xx", method="GET")
    metrics.increment("nfcore_http_requests_total", status_class="2xx", method="GET")
    metrics.increment("nfcore_provider_errors_total", outcome="error")
    metrics.increment("nfcore_worker_jobs_total", outcome="dead_letter")
    metrics.set_gauge("nfcore_worker_backlog_jobs", 3)
    candidates = evaluate_alert_candidates(metrics.snapshot())
    assert {a.code for a in candidates} == {
        "http_5xx", "provider_errors", "worker_dead_letter", "worker_backlog"
    }
    assert all(a.observed > a.threshold for a in candidates)


def test_missing_series_does_not_invent_healthy_or_alarm() -> None:
    assert evaluate_alert_candidates(()) == ()
    metrics = MetricsRegistry()
    metrics.set_gauge("nfcore_worker_backlog_jobs", 0)
    assert evaluate_alert_candidates(metrics.snapshot()) == ()
