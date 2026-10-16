"""Opt-in OpenTelemetry adapter over the existing SafeTracer authority.

Only fixed operation/outcome/duration are exported: never context IDs, HTTP
headers, tenant/customer identifiers, credentials, endpoints or free-form fields.
"""

from __future__ import annotations

import math
import os
from datetime import UTC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .observability import TraceRecord, TraceSink


class OtelTraceSink:
    """Emit an already governed span using an injected OpenTelemetry tracer."""

    def __init__(self, tracer: object) -> None:
        self._tracer = tracer

    def record(self, trace: TraceRecord) -> None:
        from .observability import StructuredLogTraceSink

        operation = trace.operation
        if operation not in StructuredLogTraceSink._ALLOWED_OPERATIONS:
            operation = "other"
        outcome = trace.outcome
        if outcome not in StructuredLogTraceSink._ALLOWED_OUTCOMES:
            outcome = "other"
        seconds = trace.elapsed_seconds
        if not math.isfinite(seconds):
            seconds = 0.0
        start = int(trace.started_at.astimezone(UTC).timestamp() * 1_000_000_000)
        end = start + int(max(0.0, seconds) * 1_000_000_000)
        # A span is detached from untrusted user-provided trace/correlation identifiers.
        span = self._tracer.start_span(  # type: ignore[attr-defined]
            operation,
            start_time=start,
            attributes={"nfcore.outcome": outcome},
        )
        span.end(end_time=end)


class _FanoutTraceSink:
    def __init__(self, first: TraceSink, second: TraceSink) -> None:
        self._first = first
        self._second = second

    def record(self, trace: TraceRecord) -> None:
        for sink in (self._first, self._second):
            try:
                sink.record(trace)
            except Exception:
                continue


def build_trace_sink(logger: object, *, service: str) -> TraceSink:
    """Keep structured logs; add OTLP only if the endpoint is configured.

    Neither telemetry failures nor a missing optional dependency affect execution.
    """
    from .observability import StructuredLogTraceSink

    log_sink = StructuredLogTraceSink(logger)  # type: ignore[arg-type]
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return log_sink
    if not endpoint.startswith(("http://", "https://")):
        return log_sink
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
        )

        provider = TracerProvider(resource=Resource.create({"service.name": service}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        return _FanoutTraceSink(log_sink, OtelTraceSink(provider.get_tracer("nfcore.runtime")))
    except Exception:
        return log_sink
