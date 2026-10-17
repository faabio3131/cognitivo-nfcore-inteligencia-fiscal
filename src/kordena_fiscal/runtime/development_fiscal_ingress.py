"""Explicit local-only fiscal query wiring using the existing synthetic contract gateway.

This is not a fiscal provider integration, fiscal issuance or homologation.
All official fiscal writes remain unavailable unless separately composed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kordena_fiscal.domain import ExecutionScope
from kordena_fiscal.operations import (
    FakeFiscalOperationsGateway,
    FiscalOperationsClient,
    FiscalQueryStatus,
)

from .config import RuntimeConfigurationError, RuntimeEnvironment, RuntimeSettings
from .fiscal_runtime import FiscalOperationHandler
from .provider_query_handler import build_provider_query_handler


def development_fiscal_ingress(
    settings: RuntimeSettings, variables: Mapping[str, str]
) -> dict[str, FiscalOperationHandler]:
    """Opt in to a clearly identified synthetic read-only query, never writes."""
    if settings.environment not in {RuntimeEnvironment.DEVELOPMENT, RuntimeEnvironment.TEST}:
        return {}

    mode = variables.get("NFCORE_DEV_FISCAL_QUERY_MODE", "").strip()
    if not mode:
        return {}
    if mode != "synthetic_pending":
        raise RuntimeConfigurationError("unsupported local-only fiscal query mode")

    delegate = build_provider_query_handler(
        FiscalOperationsClient(FakeFiscalOperationsGateway(query_status=FiscalQueryStatus.PENDING))
    )

    def query(
        scope: ExecutionScope, payload: Mapping[str, Any], idempotency_key: str | None
    ) -> Mapping[str, Any]:
        result = delegate(scope, payload, idempotency_key)
        return {
            **result,
            "simulation": True,
            "official_fiscal_evidence": False,
            "provider_origin": "synthetic_local_only",
        }

    return {"queryFiscalDocument": query}
