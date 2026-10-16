"""External webhook trace is proven internally without contacting a provider."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kordena_fiscal.runtime.observability import SafeTracer, TraceRecord
from kordena_fiscal.runtime.worker_composition import _TracedWebhookTransport


class _Collector:
    def __init__(self) -> None:
        self.traces: list[TraceRecord] = []

    def record(self, trace: TraceRecord) -> None:
        self.traces.append(trace)


def test_external_transport_failure_exports_bounded_trace_and_preserves_error() -> None:
    collector = _Collector()
    transport = Mock()
    transport.deliver.side_effect = ConnectionError("private provider detail")
    adapter = _TracedWebhookTransport(transport, SafeTracer(collector))
    request = SimpleNamespace(
        scope=SimpleNamespace(correlation_id="private-tenant"),
        outbox_entry_id="private-outbox",
    )
    with pytest.raises(ConnectionError, match="private provider detail"):
        adapter.deliver(request)
    assert len(collector.traces) == 1
    trace = collector.traces[0]
    assert trace.operation == "external.webhook"
    assert trace.outcome == "error"
    assert trace.attributes == {}
    assert transport.deliver.call_count == 1
