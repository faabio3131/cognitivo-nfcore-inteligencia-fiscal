"""Alert publishing uses the existing tenant-scoped V2-13 registry."""

from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment
from kordena_fiscal.observability import (
    AlertKind,
    AlertRegistry,
    InMemoryAlertSink,
    ObservabilityContext,
)
from kordena_fiscal.runtime.alert_rules import AlertCandidate, publish_alert_candidates


def test_bridge_reuses_canonical_dedup_and_explicit_trusted_context() -> None:
    sink = InMemoryAlertSink()
    registry = AlertRegistry(sink=sink)
    context = ObservabilityContext(scope=ExecutionScope(
        host_namespace="fm.nfcore", tenant_id="tenant-test", unit_id="unit-test",
        environment=FiscalEnvironment.HOMOLOGATION, correlation_id="corr-test",
    ))
    candidates = (AlertCandidate("db_unavailable", "critical", "db", 1.0, 0.0),)
    assert publish_alert_candidates(candidates, registry=registry, context=context) == 1
    assert publish_alert_candidates(candidates, registry=registry, context=context) == 0
    assert sink.alerts[0].kind is AlertKind.DB_UNAVAILABLE
    assert sink.alerts[0].message_code == "runtime.db_unavailable"
    assert sink.alerts[0].context == context
