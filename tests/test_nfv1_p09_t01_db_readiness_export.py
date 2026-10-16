"""P09-T01: canonical DB readiness operation survives bounded trace export."""

import json
from datetime import UTC, datetime

from kordena_fiscal.runtime.observability import (
    SafeTracer,
    StructuredLogger,
    StructuredLogTraceSink,
    TraceContext,
)


def test_db_readiness_trace_keeps_bounded_operation_and_scrubs_context() -> None:
    lines: list[str] = []
    tracer = SafeTracer(StructuredLogTraceSink(
        StructuredLogger(service="nfcore-api", environment="staging", sink=lines.append)
    ))
    tracer.record(
        operation="db.readiness",
        context=TraceContext(trace_id="a" * 32, correlation_id="private-customer"),
        started_at=datetime.now(UTC),
        elapsed_seconds=0.25,
        outcome="error",
        attributes={"password": "do-not-leak", "tenant_id": "private-customer"},
    )
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["operation"] == "db.readiness"
    assert event["outcome"] == "error"
    assert event["elapsed_seconds"] == 0.25
    assert "private-customer" not in lines[0]
    assert "do-not-leak" not in lines[0]
