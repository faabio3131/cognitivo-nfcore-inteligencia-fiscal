"""Single opt-in wiring point for provider-backed fiscal read and event operations.

The caller must explicitly supply an approved FiscalOperationsClient. The
factory never discovers credentials, chooses providers or enables production.
Issue and reconciliation intentionally remain unconfigured until their own
deterministic execution contracts are certified.
"""

from __future__ import annotations

from kordena_fiscal.operations import FiscalOperationsClient

from .fiscal_runtime import FiscalOperationHandler
from .provider_event_handlers import (
    build_provider_cancel_handler,
    build_provider_inutilization_handler,
)
from .provider_query_handler import build_provider_query_handler


def build_provider_operation_handlers(
    client: FiscalOperationsClient,
) -> dict[str, FiscalOperationHandler]:
    """Compose the existing provider client into the canonical Portal/Bridge path."""
    if not isinstance(client, FiscalOperationsClient):
        raise TypeError("an explicitly configured FiscalOperationsClient is required")
    return {
        "queryFiscalDocument": build_provider_query_handler(client),
        "cancelFiscalDocument": build_provider_cancel_handler(client),
        "inutilizeFiscalRange": build_provider_inutilization_handler(client),
    }
