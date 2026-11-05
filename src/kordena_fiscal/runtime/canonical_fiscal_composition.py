"""Canonical runtime composition with explicit fail-closed fiscal provider boundaries.

The handlers are always registered. Provider credentials and official transports
must be provisioned independently; this module never simulates authorization.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.archive import RetentionPolicyMetadata
from kordena_fiscal.domain import FiscalValidationError
from kordena_fiscal.gateway import FiscalGatewayClient
from kordena_fiscal.operations import FiscalOperationsClient

from .fiscal_runtime import FiscalOperationHandler
from .provider_operation_wiring import build_provider_operation_handlers


class UnprovisionedFiscalGateway:
    """Concrete deny-by-default boundary until a tenant-scoped official adapter is bound."""

    @staticmethod
    def _unavailable() -> None:
        raise FiscalValidationError(
            "Certificado A1 não cadastrado para o CNPJ emitente ou provedor fiscal "
            "de homologação não configurado"
        )

    def authorize(self, request: Any) -> Any:
        self._unavailable()

    def query(self, request: Any) -> Any:
        self._unavailable()

    def cancel(self, request: Any) -> Any:
        self._unavailable()

    def inutilize(self, request: Any) -> Any:
        self._unavailable()


def build_runtime_fiscal_handler_factory(
    *,
    operations_gateway: Any | None = None,
    authorization_gateway: Any | None = None,
) -> Any:
    """Register all four canonical operations without granting fiscal readiness.

    Real official adapters can be supplied by the deployment composition.
    The default boundary is intentionally non-transmitting.
    """
    operations = FiscalOperationsClient(operations_gateway or UnprovisionedFiscalGateway())
    authorization = FiscalGatewayClient(
        authorization_gateway or UnprovisionedFiscalGateway()
    )
    retention = RetentionPolicyMetadata(
        policy_id="nfcore-fiscal-archive", policy_version=1
    )

    def factory(
        application: FiscalApplicationService,
    ) -> Mapping[str, FiscalOperationHandler]:
        handlers = build_provider_operation_handlers(
            operations,
            application=application,
            prepared_xml_gateway=authorization,
            archive_retention=retention,
        )
        required = {
            "issueFiscalDocument",
            "queryFiscalDocument",
            "cancelFiscalDocument",
            "reconcileFiscalOperation",
        }
        if not required.issubset(handlers):
            raise RuntimeError("canonical fiscal operation composition is incomplete")
        return handlers

    return factory
