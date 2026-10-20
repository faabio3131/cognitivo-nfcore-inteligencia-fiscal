"""Public trial ingress: explicit origin and canonical service without browser HMAC."""
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kordena_fiscal.security.s2s import FixedWindowRateLimiter
from kordena_fiscal.web.public_trial import create_public_trial_router


class Trial:
    def __init__(self) -> None:
        self.calls = []

    def begin(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            replay=False,
            expires_at=datetime.now(UTC) + timedelta(days=7),
            activation_reset=None,
        )


class Delivery:
    def deliver(self, **kwargs):
        raise AssertionError("no activation reset was issued")


def client(service: Trial) -> TestClient:
    app = FastAPI()
    app.include_router(create_public_trial_router(
        service,  # type: ignore[arg-type]
        pricing=SimpleNamespace(current=None),  # type: ignore[arg-type]
        allowed_origins=("https://fmtecnologia.com.br",),
        rate_limiter=FixedWindowRateLimiter(max_requests=3, window_seconds=3600),
        delivery=Delivery(),  # type: ignore[arg-type]
    ))
    return TestClient(app)


def test_public_trial_requires_approved_origin_and_rejects_authority_fields() -> None:
    service = Trial()
    c = client(service)
    body = {"plan_id": "p", "price_id": "price", "buyer_email": "a@example.com",
            "legal_name": "ACME"}
    headers = {"Origin": "https://fmtecnologia.com.br", "Idempotency-Key": "public-trial-0001"}
    assert c.post("/v1/public/trials", json=body).status_code == 403
    assert c.post("/v1/public/trials", json={**body, "tenant_id": "spoof"},
                  headers=headers).status_code == 400
    response = c.post("/v1/public/trials", json=body, headers=headers)
    assert response.status_code == 201
    assert response.json()["status"] == "trial_activation_pending"
    assert response.headers["access-control-allow-origin"] == headers["Origin"]
    assert "reset_token" not in response.text
    assert len(service.calls) == 1


def test_public_trial_rejects_unsigned_browser_authority_and_large_payload() -> None:
    service = Trial()
    c = client(service)
    headers = {"Origin": "https://fmtecnologia.com.br", "Idempotency-Key": "public-trial-0002"}
    assert c.post("/v1/public/trials", json={}, headers={**headers,
        "Authorization": "Bearer forged"}).status_code == 403
    assert c.post("/v1/public/trials", content=json.dumps({"x": "a" * 5000}),
                  headers={**headers, "Content-Type": "application/json"}).status_code == 413
    assert service.calls == []


def test_public_trial_requires_explicit_https_origin() -> None:
    with pytest.raises(ValueError):
        create_public_trial_router(
            Trial(),  # type: ignore[arg-type]
            pricing=SimpleNamespace(current=None),  # type: ignore[arg-type]
            allowed_origins=("http://fmtecnologia.com.br",),
            rate_limiter=FixedWindowRateLimiter(max_requests=1, window_seconds=60),
            delivery=Delivery(),  # type: ignore[arg-type]
        )


def test_public_trial_cors_preflight_requires_origin_and_restricted_headers() -> None:
    service = Trial()
    c = client(service)
    good = {
        "Origin": "https://fmtecnologia.com.br",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,idempotency-key",
    }
    response = c.options("/v1/public/trials", headers=good)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == good["Origin"]
    denied = c.options(
        "/v1/public/trials",
        headers={**good, "Access-Control-Request-Headers": "authorization"},
    )
    assert denied.status_code == 403
    assert c.options("/v1/public/trials", headers={
        **good, "Origin": "https://attacker.example"
    }).status_code == 403
    assert service.calls == []


def test_unpublished_pricing_does_not_invent_trial_offers() -> None:
    service = Trial()
    response = client(service).get(
        "/v1/public/trial-plans",
        headers={"Origin": "https://fmtecnologia.com.br"},
    )
    assert response.status_code == 503
    assert "plans" not in response.json()
    assert service.calls == []
