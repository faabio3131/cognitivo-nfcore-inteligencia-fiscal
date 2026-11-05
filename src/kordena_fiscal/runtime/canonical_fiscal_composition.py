"""Canonical runtime composition with explicit fail-closed fiscal provider boundaries.

The handlers are always registered. Provider credentials and official transports
must be provisioned independently; this module never simulates authorization.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.archive import RetentionPolicyMetadata
from kordena_fiscal.control_plane.commercial import ConfiguredFiscalOperation
from kordena_fiscal.control_plane.service import ControlPlaneNotFoundError
from kordena_fiscal.domain import (
    BrazilianJurisdiction,
    ExecutionScope,
    FiscalDocumentKind,
    FiscalEnvironment,
    FiscalValidationError,
)
from kordena_fiscal.gateway import FiscalGatewayClient
from kordena_fiscal.gateway.nfe_sp_homologation import (
    MG_NFE_HOMOLOGATION_PROVIDER_ID,
    HomologationAuthorizationTarget,
    SefazSpHomologationGateway,
)
from kordena_fiscal.gateway.nfe_sp_operations_homologation import (
    SefazHomologationOperationsGateway,
    SefazSpHomologationOperationsGateway,
)
from kordena_fiscal.gateway.nfse_nacional_homologation import (
    NfseNacionalHomologationGateway,
)
from kordena_fiscal.issuance import NfseAuthorizationRequest, NfseGatewayClient
from kordena_fiscal.operations import (
    CancellationRequest,
    CancellationResult,
    FiscalOperationsClient,
    FiscalOperationsGateway,
    FiscalQueryRequest,
    FiscalQueryResult,
    InutilizationRequest,
    InutilizationResult,
)
from kordena_fiscal.vault import EphemeralCertificateMaterial
from kordena_fiscal.vault.encrypted_a1 import EncryptedA1Vault

from .fiscal_runtime import FiscalOperationHandler
from .provider_operation_wiring import build_provider_operation_handlers


def fiscal_external_dependency_snapshot(
    *, certificate_vault: EncryptedA1Vault | None,
    trusted_signed_dps_builder: Callable[
        [NfseAuthorizationRequest, EphemeralCertificateMaterial], bytes
    ] | None = None,
) -> dict[str, bool]:
    """Configuration status only; never assert taxpayer-specific issuance readiness.

    A configured Vault is not proof that a tenant has uploaded a valid certificate.
    Both SP NF-e and National NFS-e require a trustworthy signed-document
    preparation boundary; until that is provisioned, external execution is NOT ready.
    """
    vault_ready = isinstance(certificate_vault, EncryptedA1Vault)
    nfe_transport_ready = vault_ready
    nfse_transport_ready = vault_ready and callable(trusted_signed_dps_builder)
    # Python signer and A1 mTLS are imported at composition time, but a signing
    # capability is only configured when an A1 Vault exists.
    signer_ready = vault_ready
    return {
        "fiscal_provider_transport_real_configured": nfe_transport_ready,
        "fiscal_external_secret_client_configured": vault_ready,
        "fiscal_signer_configured": signer_ready,
        "fiscal_runtime_external_execution_ready": (
            nfe_transport_ready and nfse_transport_ready and signer_ready
        ),
    }


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


class _GovernedMgQueryGateway:
    def __init__(
        self,
        *,
        legacy: FiscalOperationsGateway,
        mg: FiscalOperationsGateway,
        application: FiscalApplicationService,
    ) -> None:
        self._legacy = legacy
        self._mg = mg
        self._application = application

    def query(self, request: FiscalQueryRequest) -> FiscalQueryResult:
        if request.access_key.value[:2] != "31":
            return self._legacy.query(request)
        scope = request.scope
        if scope.environment is not FiscalEnvironment.HOMOLOGATION:
            raise FiscalValidationError("Consulta MG disponível apenas em homologação")
        if request.access_key.model.value != 55:
            raise FiscalValidationError("Consulta MG disponível apenas para NF-e modelo 55")
        try:
            provider_id = self._application.resolve_configured_provider_id(
                scope=scope,
                document_kind=FiscalDocumentKind.NFE,
                jurisdiction=BrazilianJurisdiction("MG"),
                operation=ConfiguredFiscalOperation.QUERY.value,
            )
        except ControlPlaneNotFoundError as exc:
            raise FiscalValidationError("Vínculo fiscal de consulta MG indisponível") from exc
        if provider_id != MG_NFE_HOMOLOGATION_PROVIDER_ID:
            raise FiscalValidationError("Provedor do vínculo de consulta MG incompatível")
        return self._mg.query(request)

    def cancel(self, request: CancellationRequest) -> CancellationResult:
        return self._legacy.cancel(request)

    def inutilize(self, request: InutilizationRequest) -> InutilizationResult:
        return self._legacy.inutilize(request)


def build_runtime_fiscal_handler_factory(
    *,
    operations_gateway: Any | None = None,
    authorization_gateway: Any | None = None,
    certificate_vault: EncryptedA1Vault | None = None,
    nfse_gateway: NfseGatewayClient | None = None,
    trusted_signed_dps_builder: Callable[
        [NfseAuthorizationRequest, EphemeralCertificateMaterial], bytes
    ] | None = None,
) -> Any:
    """Register all four canonical operations without granting fiscal readiness.

    Real official adapters can be supplied by the deployment composition.
    The default boundary is intentionally non-transmitting.
    """
    selected_operations = operations_gateway
    if selected_operations is None and certificate_vault is not None:
        selected_operations = SefazSpHomologationOperationsGateway(
            resolve_certificate=lambda scope, cnpj: certificate_vault.resolve(
                scope=scope, issuer_cnpj=cnpj
            )
        )
    selected_authorization = authorization_gateway
    if selected_authorization is None and certificate_vault is not None:
        selected_authorization = SefazSpHomologationGateway(
            resolve_certificate=lambda scope, cnpj: certificate_vault.resolve(
                scope=scope, issuer_cnpj=cnpj
            )
        )
    authorization = FiscalGatewayClient(
        selected_authorization or UnprovisionedFiscalGateway()
    )
    # National NFS-e requires an approved, trusted DPS preparation and XMLDSig
    # port; never derive its contents from browser payloads or send unsigned XML.
    if nfse_gateway is not None and trusted_signed_dps_builder is not None:
        raise ValueError("configure either an NFS-e gateway or a trusted DPS builder")
    selected_nfse = nfse_gateway
    if (
        selected_nfse is None
        and certificate_vault is not None
        and trusted_signed_dps_builder is not None
    ):
        selected_nfse = NfseGatewayClient(
            NfseNacionalHomologationGateway(
                resolve_certificate=lambda scope, cnpj: certificate_vault.resolve(
                    scope=scope, issuer_cnpj=cnpj
                ),
                build_signed_dps=trusted_signed_dps_builder,
            )
        )
    retention = RetentionPolicyMetadata(
        policy_id="nfcore-fiscal-archive", policy_version=1
    )

    def factory(
        application: FiscalApplicationService,
    ) -> Mapping[str, FiscalOperationHandler]:
        gateway = selected_operations or UnprovisionedFiscalGateway()
        if operations_gateway is None and certificate_vault is not None:
            vault = certificate_vault

            def resolve_mg_certificate(
                scope: ExecutionScope, cnpj: str,
            ) -> EphemeralCertificateMaterial:
                return vault.resolve(scope=scope, issuer_cnpj=cnpj)

            gateway = _GovernedMgQueryGateway(
                legacy=gateway,
                mg=SefazHomologationOperationsGateway(
                    resolve_certificate=resolve_mg_certificate,
                    target=HomologationAuthorizationTarget.MG_NFE,
                ),
                application=application,
            )
        handlers = build_provider_operation_handlers(
            FiscalOperationsClient(gateway),
            application=application,
            prepared_xml_gateway=authorization,
            prepared_nfse_gateway=selected_nfse,
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
