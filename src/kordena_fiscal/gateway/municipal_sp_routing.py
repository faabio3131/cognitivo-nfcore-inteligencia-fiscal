"""Governed São Paulo NFS-e municipal provider routing (R16).

Catalog entries describe candidate integrations, NOT certified municipal authorizations.
Actual routing is authorized only by a scoped, approved, versioned configuration
retrieved from the canonical configuration authority on each request.

A municipality's subscription to the national ADN does not imply that contributors
may issue invoices through the national SEFIN API. Never infer provider activation
from the candidate catalog.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from kordena_fiscal.domain import (
    BrazilianJurisdiction,
    ExecutionScope,
    FiscalDocumentKind,
    FiscalEnvironment,
    FiscalValidationError,
)
from kordena_fiscal.gateway.provider import (
    ProviderOperation,
    ProviderSelectionResolver,
    UnsupportedProviderError,
)

# Advisory migration / onboarding catalog. No entry authorizes transmissions.
# Multiple technical families are deliberately NOT collapsed into one active provider.
SP_MUNICIPAL_CANDIDATES: dict[str, tuple[str, tuple[str, ...]]] = {
    "3505708": ("Barueri", ("barueri-proprio",)),
    "3550308": ("São Paulo", ("nota-paulistana", "nfse-nacional")),
    "3509502": ("Campinas", ("dsf", "nfse-nacional")),
    "3552205": ("Sorocaba", ("dsf", "nfse-nacional")),
    "3518800": ("Guarulhos", ("ginfes", "nfse-nacional")),
    "3548500": ("Santos", ("ginfes", "nfse-nacional")),
    "3548807": ("São Caetano do Sul", ("ginfes", "nfse-nacional")),
    "3525904": ("Jundiaí", ("ginfes", "nfse-nacional")),
    "3552502": ("Suzano", ("ginfes", "nfse-nacional")),
    "3547304": ("Santana de Parnaíba", ("smarapd", "municipal-proprio")),
    "3534401": ("Osasco", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3522505": ("Itapevi", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3525003": ("Jandira", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3528502": ("Mairiporã", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3503901": ("Arujá", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3527306": ("Louveira", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3556206": ("Valinhos", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3523909": ("Itu", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3545209": ("Salto", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3531803": ("Monte Mor", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3518701": ("Guarujá", ("sigiss", "betha", "e-receita", "nfse-nacional")),
    "3551009": ("São Vicente", ("sigiss", "betha", "e-receita", "nfse-nacional")),
}


@dataclass(frozen=True, slots=True)
class ApprovedMunicipalProviderBinding:
    """Approval record issued and persisted by the platform configuration authority.

    The lookup MUST return an exact tenant/unit/host/environment/issuer municipality
    binding; no browser-provided value can serve as an approval.
    """

    host_namespace: str
    tenant_id: str
    unit_id: str
    environment: FiscalEnvironment
    issuer_municipality_ibge: str
    provider_id: str
    version: int
    approved_by: str
    approved_at: datetime
    enabled: bool
    permitted_operations: frozenset[ProviderOperation]

    def __post_init__(self) -> None:
        if not self.host_namespace or not self.tenant_id or not self.unit_id:
            raise FiscalValidationError("Municipal routing requires bound host/tenant/unit")
        if not isinstance(self.environment, FiscalEnvironment):
            raise FiscalValidationError("Invalid routing environment")
        code = self.issuer_municipality_ibge
        if not isinstance(code, str) or len(code) != 7 or not code.isdecimal():
            raise FiscalValidationError("Issuer municipality requires seven-digit IBGE code")
        if not isinstance(self.provider_id, str) or not self.provider_id.strip():
            raise FiscalValidationError("Municipal provider id is required")
        if (
            not isinstance(self.version, int)
            or isinstance(self.version, bool)
            or self.version < 1
            or not self.approved_by
        ):
            raise FiscalValidationError("Routing approval metadata is required")
        if (
            not isinstance(self.approved_at, datetime)
            or self.approved_at.tzinfo is None
            or self.approved_at.utcoffset() is None
        ):
            raise FiscalValidationError("Routing approval timestamp requires timezone")
        if not isinstance(self.enabled, bool) or not self.permitted_operations:
            raise FiscalValidationError("Routing requires explicit enabled/operation permissions")
        if not all(isinstance(op, ProviderOperation) for op in self.permitted_operations):
            raise FiscalValidationError("Invalid municipal routing operations")


MunicipalBindingLoader = Callable[
    [ExecutionScope, str], ApprovedMunicipalProviderBinding | None
]


class GovernedSpMunicipalProviderResolver(ProviderSelectionResolver):
    """Resolve the *issuer* municipality via the existing ProviderGatewayService port.

    Correctly configured municipal providers require the canonical ProviderRegistry,
    readiness service, tenant scoped credentials and approval independently.
    """

    def __init__(self, *, load_approved_binding: MunicipalBindingLoader) -> None:
        if not callable(load_approved_binding):
            raise ValueError("A governed municipal binding loader is required")
        self._load = load_approved_binding

    def resolve_provider_id(
        self,
        *,
        scope: ExecutionScope,
        document_kind: FiscalDocumentKind,
        jurisdiction: BrazilianJurisdiction,
        operation: str,
    ) -> str:
        if document_kind is not FiscalDocumentKind.NFSE:
            raise UnsupportedProviderError("Municipal provider router supports NFS-e only")
        if jurisdiction.state_code != "SP":
            raise UnsupportedProviderError("Municipal provider router is limited to SP")
        code = jurisdiction.municipality_ibge_code
        if code is None or code not in SP_MUNICIPAL_CANDIDATES:
            raise UnsupportedProviderError(
                "Issuer municipality is not registered in the SP catalog"
            )
        if scope.host_namespace is None:
            raise UnsupportedProviderError("Fiscal scope requires a trusted host namespace")
        try:
            requested_operation = ProviderOperation(operation)
        except ValueError:
            raise UnsupportedProviderError("Unsupported municipal provider operation") from None
        binding = self._load(scope, code)
        if binding is None or not isinstance(binding, ApprovedMunicipalProviderBinding):
            raise UnsupportedProviderError(
                "Municipal provider is not approved for this fiscal scope"
            )
        if (
            binding.host_namespace != scope.host_namespace
            or binding.tenant_id != scope.tenant_id
            or binding.unit_id != scope.unit_id
            or binding.environment is not scope.environment
            or binding.issuer_municipality_ibge != code
            or not binding.enabled
            or requested_operation not in binding.permitted_operations
        ):
            raise UnsupportedProviderError("Municipal routing scope or approval does not match")
        # Candidate metadata never decides the provider: approval remains sovereign.
        # New provider integrations can be configured without changing the router.
        return binding.provider_id.strip().lower()
