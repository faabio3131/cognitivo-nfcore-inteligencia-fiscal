"""Explicit provider-backed fiscal document query adapter.

Only an operator-supplied FiscalOperationsClient enables this handler. This module
never creates a provider, credentials, production grant, synthetic reply or route.
The canonical Portal/Bridge boundary establishes the trusted execution scope.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kordena_fiscal.domain import ExecutionScope, FiscalValidationError
from kordena_fiscal.operations import FiscalOperationsClient, FiscalQueryRequest
from kordena_fiscal.xml import NfeAccessKey

from .fiscal_runtime import FiscalOperationHandler


def build_provider_query_handler(client: FiscalOperationsClient) -> FiscalOperationHandler:
    """Bind an approved provider-neutral client to the canonical query operation."""

    def query(
        scope: ExecutionScope,
        payload: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        del idempotency_key  # Provider query is read-only, not an issuance intent.
        raw_key = payload.get("access_key")
        if not isinstance(raw_key, str):
            raise FiscalValidationError("access_key is required")
        result = client.query(FiscalQueryRequest(scope=scope, access_key=NfeAccessKey(raw_key)))
        return {
            "access_key": result.access_key.value,
            "status": result.status.value,
            "provider_request_id": result.provider_request_id,
            "protocol_reference": result.protocol_reference,
        }

    return query
