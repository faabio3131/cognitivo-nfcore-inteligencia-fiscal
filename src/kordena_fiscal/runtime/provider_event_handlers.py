"""Provider-neutral cancellation and inutilization handlers for the canonical fiscal path.

Handlers are inert unless a trusted composition root injects a real,
approved FiscalOperationsClient. No provider, credentials or synthetic result
is created here. Official execution remains fail-closed by default.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kordena_fiscal.domain import ElectronicInvoiceModel, ExecutionScope, FiscalValidationError
from kordena_fiscal.operations import (
    CancellationRequest,
    FiscalOperationsClient,
    InutilizationRequest,
)
from kordena_fiscal.xml import NfeAccessKey

from .fiscal_runtime import FiscalOperationHandler


def build_provider_cancel_handler(client: FiscalOperationsClient) -> FiscalOperationHandler:
    """Validate a scoped cancellation and delegate through the existing client."""

    def cancel(
        scope: ExecutionScope,
        payload: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        del idempotency_key  # Request identity is deterministically derived by the domain.
        raw_key = payload.get("access_key")
        protocol = payload.get("authorization_protocol")
        reason = payload.get("justification")
        if not all(isinstance(item, str) for item in (raw_key, protocol, reason)):
            raise FiscalValidationError("cancellation requires access_key, authorization_protocol and justification")
        request = CancellationRequest.build(
            scope=scope,
            access_key=NfeAccessKey(raw_key),
            authorization_protocol=protocol,
            justification=reason,
        )
        result = client.cancel(request)
        return {
            "status": result.status.value,
            "request_id": result.request_id,
            "access_key": result.access_key.value,
            "provider_request_id": result.provider_request_id,
            "event_protocol_reference": result.event_protocol_reference,
            "rejection_code": result.rejection_code,
            "rejection_message": result.rejection_message,
        }

    return cancel


def build_provider_inutilization_handler(client: FiscalOperationsClient) -> FiscalOperationHandler:
    """Validate the canonical number range before crossing the provider boundary."""

    def inutilize(
        scope: ExecutionScope,
        payload: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        del idempotency_key  # Domain request_id is stable for retries of the same intent.
        model = payload.get("model")
        series = payload.get("series")
        first = payload.get("first_number")
        last = payload.get("last_number")
        reason = payload.get("justification")
        if any(type(item) is not int for item in (model, series, first, last)) or not isinstance(reason, str):
            raise FiscalValidationError("inutilization requires integer model/series/range and justification")
        request = InutilizationRequest.build(
            scope=scope,
            model=ElectronicInvoiceModel(model),
            series=series,
            first_number=first,
            last_number=last,
            justification=reason,
        )
        result = client.inutilize(request)
        return {
            "status": result.status.value,
            "request_id": result.request_id,
            "model": result.model.value,
            "series": result.series,
            "first_number": result.first_number,
            "last_number": result.last_number,
            "provider_request_id": result.provider_request_id,
            "event_protocol_reference": result.event_protocol_reference,
            "rejection_code": result.rejection_code,
            "rejection_message": result.rejection_message,
        }

    return inutilize
