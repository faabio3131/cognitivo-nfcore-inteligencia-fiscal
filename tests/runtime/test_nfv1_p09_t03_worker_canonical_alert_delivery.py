"""Scoped Worker publishes bounded candidates into the *existing* registry."""

from types import SimpleNamespace
from unittest.mock import Mock

from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment
from kordena_fiscal.observability import (
    AlertRegistry,
    InMemoryAlertSink,
    ObservabilityContext,
)
from kordena_fiscal.runtime.alert_rules import (
    InternalAlertMonitor,
    StructuredLogAlertSink,
)
from kordena_fiscal.runtime.observability import MetricsRegistry, SafeTracer, StructuredLogger
from kordena_fiscal.runtime.worker_composition import _TracingWorkerObserver


def _scope() -> ObservabilityContext:
    return ObservabilityContext(scope=ExecutionScope(
        host_namespace="fm.nfcore", tenant_id="pilot-tenant", unit_id="pilot-unit",
        environment=FiscalEnvironment.HOMOLOGATION, correlation_id="test-correlation",
    ))


def test_worker_alert_emission_dedup_recovery_and_recurrence() -> None:
    metrics = MetricsRegistry()
    metrics.set_gauge("nfcore_worker_backlog_jobs", 0)
    monitor = InternalAlertMonitor(metrics)
    sink = InMemoryAlertSink()
    registry = AlertRegistry(sink=sink)
    wrapper = _TracingWorkerObserver(Mock(), SafeTracer(), monitor, registry, _scope())
    monitor.poll()
    metrics.set_gauge("nfcore_worker_backlog_jobs", 3)
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert len(sink.alerts) == 1
    assert sink.alerts[0].message_code == "runtime.worker_backlog"
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert len(sink.alerts) == 1  # same unresolved incident is deduplicated
    metrics.set_gauge("nfcore_worker_backlog_jobs", 0)
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert not registry.is_active(sink.alerts[0].deduplication_key)
    metrics.set_gauge("nfcore_worker_backlog_jobs", 4)
    wrapper.cycle_completed(SimpleNamespace(elapsed_seconds=0.001))
    assert len(sink.alerts) == 2  # recovered incident can alert again


def test_structured_sink_never_logs_customer_scope_or_secret() -> None:
    from kordena_fiscal.runtime.alert_rules import AlertCandidate, publish_alert_candidates

    lines: list[str] = []
    logger = StructuredLogger(service="nfcore-worker", environment="test", sink=lines.append)
    registry = AlertRegistry(sink=StructuredLogAlertSink(logger))
    incident = (AlertCandidate("secret_failure", "critical", "secret_failure", 1.0, 0.0),)
    assert publish_alert_candidates(incident, registry=registry, context=_scope()) == 1
    assert len(lines) == 1
    assert "runtime.secret_failure" in lines[0]
    assert "pilot-tenant" not in lines[0] and "pilot-unit" not in lines[0]
