"""P09-T03: canonical alert registry isolation and dedup must be preserved."""

from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment
from kordena_fiscal.observability import (
    AlertRegistry,
    InMemoryAlertSink,
    ObservabilityContext,
)
from kordena_fiscal.runtime.alert_rules import AlertCandidate, publish_alert_candidates


def _context(tenant: str) -> ObservabilityContext:
    return ObservabilityContext(scope=ExecutionScope(
        host_namespace="fm.nfcore",
        tenant_id=tenant,
        unit_id="unit-one",
        environment=FiscalEnvironment.HOMOLOGATION,
        correlation_id="safe-correlation",
    ))


def test_registry_deduplicates_per_tenant_and_does_not_lose_other_tenants() -> None:
    sink = InMemoryAlertSink()
    registry = AlertRegistry(sink=sink)
    incident = (AlertCandidate("secret_failure", "critical", "secret_failure", 1.0, 0.0),)
    first = _context("tenant-one")
    second = _context("tenant-two")
    assert publish_alert_candidates(incident, registry=registry, context=first) == 1
    assert publish_alert_candidates(incident, registry=registry, context=first) == 0
    assert publish_alert_candidates(incident, registry=registry, context=second) == 1
    assert len(sink.alerts) == 2
    assert sink.alerts[0].deduplication_key != sink.alerts[1].deduplication_key
    assert registry.resolve(sink.alerts[0].deduplication_key)
    assert publish_alert_candidates(incident, registry=registry, context=first) == 1
    assert publish_alert_candidates(incident, registry=registry, context=second) == 0


def test_unknown_candidate_cannot_be_forwarded_into_canonical_registry() -> None:
    sink = InMemoryAlertSink()
    registry = AlertRegistry(sink=sink)
    unknown = (AlertCandidate("unsupported", "critical", "other", 1.0, 0.0),)
    assert publish_alert_candidates(unknown, registry=registry, context=_context("tenant-one")) == 0
    assert sink.alerts == ()
