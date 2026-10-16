"""P09-T03: counter deltas, reset protection and non-authoritative gauges."""

from kordena_fiscal.runtime.alert_rules import evaluate_alert_candidates
from kordena_fiscal.runtime.observability import MetricsRegistry


def test_counter_deltas_and_gauges_not_lifetime_totals() -> None:
    metrics = MetricsRegistry()
    metrics.increment("nfcore_http_requests_total", status_class="5xx", method="GET")
    metrics.set_gauge("nfcore_worker_backlog_jobs", 3)
    baseline = metrics.snapshot()
    # Historic errors cannot repeatedly page; backlog is a present-state gauge.
    assert {a.code for a in evaluate_alert_candidates(baseline)} == {"worker_backlog"}
    metrics.increment("nfcore_http_requests_total", status_class="5xx", method="GET")
    metrics.increment("nfcore_provider_errors_total", outcome="error")
    metrics.increment("nfcore_worker_jobs_total", outcome="dead_letter")
    current = metrics.snapshot()
    # First samples of new series cannot be treated as a trusted increase.
    assert {a.code for a in evaluate_alert_candidates(current, previous=baseline)} == {
        "http_5xx", "worker_backlog"
    }
    metrics.increment("nfcore_provider_errors_total", outcome="error")
    metrics.increment("nfcore_worker_jobs_total", outcome="dead_letter")
    later = metrics.snapshot()
    assert {a.code for a in evaluate_alert_candidates(later, previous=current)} == {
        "provider_errors", "worker_dead_letter", "worker_backlog"
    }


def test_missing_series_and_counter_reset_fail_closed() -> None:
    assert evaluate_alert_candidates(()) == ()
    prior = MetricsRegistry()
    prior.increment("nfcore_fiscal_rejections_total", 5)
    fresh = MetricsRegistry()
    fresh.increment("nfcore_fiscal_rejections_total", 1)
    assert evaluate_alert_candidates(fresh.snapshot(), previous=prior.snapshot()) == ()
    assert evaluate_alert_candidates(fresh.snapshot()) == ()
