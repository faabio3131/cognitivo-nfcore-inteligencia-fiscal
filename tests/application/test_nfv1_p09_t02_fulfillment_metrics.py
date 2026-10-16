"""Metrics of canonical committed/replayed commercial fulfillment, without tenant labels."""

from datetime import UTC, datetime

from kordena_fiscal.application.commercial_fulfillment import CommercialFulfillmentService
from kordena_fiscal.runtime.observability import MetricsRegistry
from tests.application.test_cl11_commercial_fulfillment_service import (
    MemoryCommercialDatabase,
    event,
)


def test_committed_and_replayed_fulfillment_count_without_pii() -> None:
    metrics = MetricsRegistry()
    service = CommercialFulfillmentService(MemoryCommercialDatabase(), metrics=metrics)
    now = datetime(2026, 10, 16, tzinfo=UTC)
    service.process(event=event(), received_at=now)
    service.process(event=event(), received_at=now)
    samples = [s for s in metrics.as_dicts() if s["name"] == "nfcore_commercial_fulfillment_total"]
    assert {tuple(sorted(s["labels"].items())): s["value"] for s in samples} == {
        (("outcome", "succeeded"),): 1.0,
        (("outcome", "replay"),): 1.0,
    }
