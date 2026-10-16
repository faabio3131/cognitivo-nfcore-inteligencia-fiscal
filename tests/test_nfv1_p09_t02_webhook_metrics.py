"""P09-T02 webhook delivery metrics are bounded and non-authoritative."""

from kordena_fiscal.runtime.observability import MetricsRegistry


def test_webhook_transport_errors_are_counted_without_client_data() -> None:
    from types import SimpleNamespace
    from unittest.mock import Mock

    import pytest

    from kordena_fiscal.runtime.observability import SafeTracer
    from kordena_fiscal.runtime.worker_composition import _TracedWebhookTransport

    metrics = MetricsRegistry()
    transport = Mock()
    transport.deliver.side_effect = RuntimeError("provider unavailable")
    handler = _TracedWebhookTransport(transport, SafeTracer(), metrics=metrics)
    request = SimpleNamespace(
        scope=SimpleNamespace(correlation_id="private-tenant"),
        outbox_entry_id="private-outbox",
    )
    with pytest.raises(RuntimeError, match="provider unavailable"):
        handler.deliver(request)
    samples = metrics.as_dicts()
    assert any(
        item["name"] == "nfcore_webhook_delivery_total"
        and item["labels"] == {"outcome": "error"}
        and item["value"] == 1
        for item in samples
    )
    assert "private" not in str(samples)


def test_webhook_metrics_failure_does_not_replace_transport_error() -> None:
    from types import SimpleNamespace
    from unittest.mock import Mock

    import pytest

    from kordena_fiscal.runtime.observability import SafeTracer
    from kordena_fiscal.runtime.worker_composition import _TracedWebhookTransport

    class BrokenMetrics(MetricsRegistry):
        def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
            raise ValueError("metrics down")

    transport = Mock()
    transport.deliver.side_effect = RuntimeError("canonical transport error")
    handler = _TracedWebhookTransport(
        transport, SafeTracer(), metrics=BrokenMetrics()
    )
    request = SimpleNamespace(scope=None, outbox_entry_id="opaque")
    with pytest.raises(RuntimeError, match="canonical transport error"):
        handler.deliver(request)
