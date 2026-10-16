"""The canonical API must not silently drop traces with default composition."""

import json

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("google.cloud.secretmanager_v1", reason="requires canonical GSM dependency")

from kordena_fiscal.runtime.api import create_runtime_app
from kordena_fiscal.runtime.observability import StructuredLogger


def test_default_api_tracer_uses_existing_safe_structured_sink() -> None:
    lines: list[str] = []
    logger = StructuredLogger(service="nfcore-api", environment="test", sink=lines.append)
    with TestClient(create_runtime_app(logger=logger)) as client:
        response = client.get("/health/live", headers={"Authorization": "Bearer never-record"})
    assert response.status_code == 200
    traces = [json.loads(line) for line in lines if '"event":"runtime.trace"' in line]
    assert any(trace["operation"] == "http.request" for trace in traces)
    assert all("never-record" not in line for line in lines)
