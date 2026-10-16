"""Existing API metrics/ready routes drive bounded alert evaluation."""

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("google.cloud.secretmanager_v1", reason="requires canonical GSM dependency")

from kordena_fiscal.runtime.api import create_runtime_app
from kordena_fiscal.runtime.config import RuntimeSettings
from kordena_fiscal.runtime.observability import MetricsRegistry


def test_alert_polling_is_composed_in_existing_api_without_new_route() -> None:
    settings = RuntimeSettings.from_mapping({
        "NFCORE_ENVIRONMENT": "test",
        "NFCORE_PERSISTENCE_BACKEND": "sqlite",
        "NFCORE_SECRET_BACKEND": "memory",
        "NFCORE_REQUIRE_HTTPS": "false",
    })
    metrics = MetricsRegistry()
    app = create_runtime_app(settings, metrics=metrics)
    with TestClient(app) as client:
        first = client.get("/internal/metrics")
        assert first.status_code == 200
        assert first.json()["alert_candidates"] == []
        metrics.set_gauge("nfcore_worker_backlog_jobs", 4)
        next_response = client.get("/internal/metrics")
        assert next_response.status_code == 200
        assert "worker_backlog" in {
            item["code"] for item in next_response.json()["alert_candidates"]
        }
        assert client.get("/health/ready").status_code == 200
        assert app.state.nfcore_alert_monitor is not None
