"""P09-T01: deterministic tests of safe OTLP span projection without a live exporter."""

from datetime import UTC, datetime

from kordena_fiscal.runtime.observability import TraceContext, TraceRecord
from kordena_fiscal.runtime.otel_trace_sink import OtelTraceSink


class _Span:
    def __init__(self) -> None:
        self.end_time: int | None = None

    def end(self, *, end_time: int) -> None:
        self.end_time = end_time


class _Tracer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str], int]] = []
        self.span = _Span()

    def start_span(self, name: str, *, start_time: int, attributes: dict[str, str]) -> _Span:
        self.calls.append((name, attributes, start_time))
        return self.span


def test_otlp_sink_exports_only_bounded_non_sensitive_fields() -> None:
    tracer = _Tracer()
    started = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
    OtelTraceSink(tracer).record(TraceRecord(
        operation="db.readiness",
        context=TraceContext(trace_id="a" * 32, correlation_id="private-customer"),
        started_at=started,
        elapsed_seconds=0.125,
        outcome="error",
        attributes={"authorization": "Bearer forbidden", "tenant_id": "private-customer"},
    ))
    assert len(tracer.calls) == 1
    name, attributes, start_ns = tracer.calls[0]
    assert name == "db.readiness"
    assert attributes == {"nfcore.outcome": "error"}
    assert tracer.span.end_time == start_ns + 125_000_000
    assert "private-customer" not in str(tracer.calls)
    assert "forbidden" not in str(tracer.calls)


def test_otlp_sink_denies_freeform_names_and_outcomes() -> None:
    tracer = _Tracer()
    OtelTraceSink(tracer).record(TraceRecord(
        operation="tenant-secret",
        context=TraceContext(trace_id="b" * 32, correlation_id="private"),
        started_at=datetime.now(UTC), elapsed_seconds=0.0, outcome="secret-value",
    ))
    assert tracer.calls[0][0] == "other"
    assert tracer.calls[0][1] == {"nfcore.outcome": "other"}
