"""Opt-in public trial intake backed by the existing governed commercial service.

No S2S secret in browsers, no authority from client-supplied tenant fields.
Deployment requires explicit allowlisted origin, activation delivery and an
external shared anti-abuse gate; never automatically enabled in runtime.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from kordena_fiscal.application.commercial_trial import GovernedTrialService
from kordena_fiscal.product.commercial_fulfillment import CommercialFulfillmentError
from kordena_fiscal.security.s2s import FixedWindowRateLimiter
from kordena_fiscal.web.human_recovery import PasswordResetDelivery


def create_public_trial_router(
    service: GovernedTrialService,
    *,
    allowed_origins: tuple[str, ...],
    rate_limiter: FixedWindowRateLimiter,
    delivery: PasswordResetDelivery,
) -> APIRouter:
    """Produce first-party trial ingress without modifying the signed S2S route."""
    if not allowed_origins or any(
        urlsplit(value).scheme != "https"
        or not urlsplit(value).netloc
        or urlsplit(value).username is not None
        or urlsplit(value).password is not None
        or urlsplit(value).path not in ("", "/")
        or urlsplit(value).query
        or urlsplit(value).fragment
        or value.rstrip("/") != value
        for value in allowed_origins
    ):
        raise ValueError("public trial requires explicit HTTPS origins")

    router = APIRouter(tags=["public-commercial-trial"])

    @router.post("/v1/public/trials")
    async def public_trial(request: Request) -> JSONResponse:
        origin = request.headers.get("origin", "")
        headers = {"Cache-Control": "no-store, max-age=0"}
        if origin not in allowed_origins:
            return JSONResponse(status_code=403, content={"detail": "origin denied"}, headers=headers)
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return JSONResponse(status_code=415, content={"detail": "JSON required"}, headers=headers)
        if request.headers.get("cookie") or request.headers.get("authorization"):
            return JSONResponse(status_code=403, content={"detail": "anonymous request required"}, headers=headers)
        identity = request.client.host if request.client is not None else "unknown"
        if not rate_limiter.allow(f"public-trial:{identity}", datetime.now(UTC)):
            return JSONResponse(status_code=429, content={"detail": "rate limited"}, headers=headers)
        key = request.headers.get("Idempotency-Key", "").strip()
        if not (8 <= len(key) <= 128 and key.isascii() and key.isprintable()):
            return JSONResponse(status_code=400, content={"detail": "invalid idempotency key"}, headers=headers)
        body = await request.body()
        if len(body) > 4096:
            return JSONResponse(status_code=413, content={"detail": "payload too large"}, headers=headers)
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return JSONResponse(status_code=400, content={"detail": "invalid JSON"}, headers=headers)
        fields = {"plan_id", "price_id", "buyer_email", "legal_name"}
        if not isinstance(payload, dict) or set(payload) != fields or not all(
            isinstance(payload[field], str) for field in fields
        ):
            return JSONResponse(status_code=400, content={"detail": "invalid trial fields"}, headers=headers)
        now = datetime.now(UTC)
        try:
            started = service.begin(
                plan_id=payload["plan_id"],
                price_id=payload["price_id"],
                buyer_email=payload["buyer_email"],
                legal_name=payload["legal_name"],
                idempotency_key=key,
                now=now,
            )
        except CommercialFulfillmentError:
            return JSONResponse(status_code=409, content={"detail": "trial unavailable"}, headers=headers)
        except Exception:
            return JSONResponse(status_code=503, content={"detail": "trial temporarily unavailable"}, headers=headers)
        if started.activation_reset is not None:
            try:
                delivery.deliver(
                    email=payload["buyer_email"].strip().casefold(),
                    reset=started.activation_reset,
                )
            except Exception:
                return JSONResponse(status_code=503, content={"detail": "activation delivery unavailable"}, headers=headers)
        return JSONResponse(
            status_code=200 if started.replay else 201,
            content={
                "status": "trial_activation_pending",
                "trial_expires_at": started.expires_at.isoformat(),
                "replay": started.replay,
            },
            headers=headers,
        )

    return router
