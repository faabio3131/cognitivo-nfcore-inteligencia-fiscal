"""P09-T01: trace export must be bounded, scrubbed and non-authoritative."""

from datetime import UTC, datetime
import json

from kordena_fiscal.runtime.observability import (
    SafeTracer,
    StructuredLogger,
    StructuredLogTraceSink,
    TraceContext,
)


def test_structured_trace_export_scrubs_identifiers_and_attributes() -> None:
    lines: list[str] = []
    logger = StructuredLogger(service="nfcore-worker", environment="staging", sink=lines.append)
    tracer = SafeTracer(StructuredLogTraceSink(logger))
    tracer.record(
        operation="db.outbox_counts",
        context=TraceContext(trace_id="a" * 32, correlation_id="tenant-private"),
        started_at=datetime.now(UTC),
        elapsed_seconds=0.125,
        outcome="ok",
        attributes={"authorization": "Bearer sensitive", "tenant_id": "private-tenant"},
    )
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event"] == "runtime.trace"
    assert parsed["operation"] == "db.outbox_counts"
    assert parsed["elapsed_seconds"] == 0.125
    assert "private" not in lines[0]
    assert "sensitive" not in lines[0]
    assert "a" * 32 not in lines[0]


def test_structured_trace_export_denies_freeform_operation_and_outcome() -> None:
    lines: list[str] = []
    tracer = SafeTracer(StructuredLogTraceSink(
        StructuredLogger(service="nfcore-worker", environment="staging", sink=lines.append)
    ))
    tracer.record(
        operation="Bearer secret",
        context=TraceContext(trace_id="b" * 32, correlation_id="private"),
        started_at=datetime.now(UTC),
        elapsed_seconds=0.0,
        outcome="secret value",
    )
    parsed = json.loads(lines[0])
    assert parsed["operation"] == "other"
    assert parsed["outcome"] == "other"
    assert "secret" not in lines[0]


def test_exporter_failure_never_breaks_fiscal_execution() -> None:
    def broken_sink(_line: str) -> None:
        raise RuntimeError("telemetry offline")

    tracer = SafeTracer(StructuredLogTraceSink(
        StructuredLogger(service="nfcore-worker", environment="staging", sink=broken_sink)
    ))
    tracer.record(
        operation="worker.poll",
        context=TraceContext(trace_id="c" * 32, correlation_id="safe"),
        started_at=datetime.now(UTC),
        elapsed_seconds=0.1,
        outcome="ok",
    )


def test_canonical_http_entrypoint_emits_scrubbed_trace(capsys: object) -> None:
    from fastapi.testclient import TestClient
    from kordena_fiscal.web.app import create_app

    with TestClient(create_app()) as client:
        response = client.get("/health/live", headers={"Authorization": "Bearer never-log"})
    assert response.status_code == 200
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert '"event":"runtime.trace"' in output
    assert '"operation":"http.request"' in output
    assert "never-log" not in output
    assert "/health/live" not in output
