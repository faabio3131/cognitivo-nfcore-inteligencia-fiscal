"""Worker observer drives the same metrics monitor without changing worker authority."""

from types import SimpleNamespace
from unittest.mock import Mock

from kordena_fiscal.runtime.alert_rules import InternalAlertMonitor
from kordena_fiscal.runtime.observability import MetricsRegistry, SafeTracer
from kordena_fiscal.runtime.worker_composition import _TracingWorkerObserver


def test_worker_cycle_evaluates_its_own_metrics_and_never_claims_jobs() -> None:
    metrics = MetricsRegistry()
    monitor = InternalAlertMonitor(metrics)
    observer = Mock()
    wrapper = _TracingWorkerObserver(observer, SafeTracer(), monitor)
    metrics.increment("nfcore_worker_jobs_total", 0, outcome="dead_letter")
    monitor.poll()
    metrics.increment("nfcore_worker_jobs_total", outcome="dead_letter")
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert {candidate.code for candidate in monitor.latest} == {"worker_dead_letter"}
    observer.cycle_completed.assert_called_once()
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert monitor.latest == ()


def test_worker_alert_failure_does_not_change_worker_failure_path() -> None:
    observer = Mock()
    broken = Mock()
    broken.poll.side_effect = RuntimeError("alert evaluator down")
    wrapper = _TracingWorkerObserver(observer, SafeTracer(), broken)
    wrapper.cycle_failed(error_type="runtime_error", elapsed_seconds=0.01)
    observer.cycle_failed.assert_called_once()
