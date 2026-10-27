"""Single opt-in wiring point for provider-backed fiscal read and event operations.

The caller must explicitly supply an approved FiscalOperationsClient. The
factory never discovers credentials, chooses providers or enables production.
Prepared XML issuance and recovery require explicit durable application, gateway
and retention inputs; client-only callers keep their existing read/event surface.
"""

from __future__ import annotations

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.archive import RetentionPolicyMetadata
from kordena_fiscal.gateway import FiscalGatewayClient
from kordena_fiscal.operations import FiscalOperationsClient

from .fiscal_runtime import FiscalOperationHandler
from .provider_event_handlers import (
    build_provider_cancel_handler,
    build_provider_inutilization_handler,
)
from .provider_issuance_handler import (
    build_provider_issuance_handler,
    build_provider_reconciliation_handler,
)
from .provider_query_handler import build_provider_query_handler


def build_provider_operation_handlers(
    client: FiscalOperationsClient,
    *,
    application: FiscalApplicationService | None = None,
    prepared_xml_gateway: FiscalGatewayClient | None = None,
    archive_retention: RetentionPolicyMetadata | None = None,
) -> dict[str, FiscalOperationHandler]:
    """Compose the existing provider client into the canonical Portal/Bridge path."""
    if not isinstance(client, FiscalOperationsClient):
        raise TypeError("an explicitly configured FiscalOperationsClient is required")
    handlers = {
        "queryFiscalDocument": build_provider_query_handler(client),
        "cancelFiscalDocument": build_provider_cancel_handler(client),
        "inutilizeFiscalRange": build_provider_inutilization_handler(client),
    }
    if any(value is not None for value in (application, prepared_xml_gateway, archive_retention)):
        if (
            not isinstance(application, FiscalApplicationService)
            or not isinstance(prepared_xml_gateway, FiscalGatewayClient)
            or not isinstance(archive_retention, RetentionPolicyMetadata)
        ):
            raise TypeError("prepared XML operations require application, gateway and retention")
        handlers["issueFiscalDocument"] = build_provider_issuance_handler(
            application,
            resolve_prepared=application.load_prepared_authorization,
            gateway=prepared_xml_gateway,
        )
        handlers["reconcileFiscalOperation"] = build_provider_reconciliation_handler(
            application,
            client=client,
            archive_retention=archive_retention,
        )
    return handlers
