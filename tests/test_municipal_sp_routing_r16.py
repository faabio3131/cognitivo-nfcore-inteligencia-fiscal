"""R16 SP municipal resolver: scope, IBGE, approval and provider routing tests.

All integrations are synthetic: no municipal system, A1, or official taxpayer
credentials are invoked by these tests.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kordena_fiscal.domain import (
    BrazilianJurisdiction,
    ExecutionScope,
    FiscalDocumentKind,
    FiscalEnvironment,
    FiscalValidationError,
)
from kordena_fiscal.gateway.municipal_sp_routing import (
    SP_MUNICIPAL_CANDIDATES,
    ApprovedMunicipalProviderBinding,
    GovernedSpMunicipalProviderResolver,
)
from kordena_fiscal.gateway.provider import (
    ProviderOperation,
    ProviderSelectionResolver,
    UnsupportedProviderError,
)


def _scope(
    tenant_id: str = "tenant-1",
    unit_id: str = "unit-1",
    environment: FiscalEnvironment = FiscalEnvironment.HOMOLOGATION,
) -> ExecutionScope:
    return ExecutionScope(
        host_namespace="nfcore", tenant_id=tenant_id, unit_id=unit_id,
        environment=environment, correlation_id="r16-test",
    )


def _binding(
    scope: ExecutionScope, code: str, provider: str = "nota-paulistana",
) -> ApprovedMunicipalProviderBinding:
    assert scope.host_namespace is not None
    return ApprovedMunicipalProviderBinding(
        host_namespace=scope.host_namespace, tenant_id=scope.tenant_id,
        unit_id=scope.unit_id, environment=scope.environment,
        issuer_municipality_ibge=code, provider_id=provider,
        version=3, approved_by="platform-admin", approved_at=datetime.now(UTC),
        enabled=True, permitted_operations=frozenset(
            {ProviderOperation.AUTHORIZE, ProviderOperation.QUERY}
        ),
    )


def _resolve(
    resolver: GovernedSpMunicipalProviderResolver,
    scope: ExecutionScope,
    code: str = "3550308",
    kind: FiscalDocumentKind = FiscalDocumentKind.NFSE,
    operation: str = "authorize",
) -> str:
    return resolver.resolve_provider_id(
        scope=scope,
        document_kind=kind,
        jurisdiction=BrazilianJurisdiction("SP", code),
        operation=operation,
    )


def test_catalog_covers_all_22_requested_ibge_codes() -> None:
    expected = {
        "3505708", "3550308", "3509502", "3552205", "3518800",
        "3548500", "3548807", "3525904", "3552502", "3547304",
        "3534401", "3522505", "3525003", "3528502", "3503901",
        "3527306", "3556206", "3523909", "3545209", "3531803",
        "3518701", "3551009",
    }
    assert set(SP_MUNICIPAL_CANDIDATES) == expected
    assert len(SP_MUNICIPAL_CANDIDATES) == 22


def test_resolver_implements_existing_canonical_provider_port() -> None:
    scope = _scope()
    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda s, code: _binding(s, code)
    )
    selector: ProviderSelectionResolver = resolver
    assert _resolve(resolver, scope) == "nota-paulistana"
    assert selector.resolve_provider_id(
        scope=scope, document_kind=FiscalDocumentKind.NFSE,
        jurisdiction=BrazilianJurisdiction("SP", "3550308"),
        operation="query",
    ) == "nota-paulistana"


def test_provider_is_not_derived_from_advisory_city_catalog() -> None:
    scope = _scope()
    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda s, code: _binding(s, code, "governed-2026-adapter")
    )
    assert _resolve(resolver, scope, code="3505708") == "governed-2026-adapter"


@pytest.mark.parametrize(
    ("scope", "code", "kind", "operation"),
    [
        (_scope(), "3550308", FiscalDocumentKind.NFE, "authorize"),
        (_scope(), "9999999", FiscalDocumentKind.NFSE, "authorize"),
        (_scope(), "3550308", FiscalDocumentKind.NFSE, "cancel"),
        (_scope(tenant_id="other-tenant"), "3550308", FiscalDocumentKind.NFSE, "authorize"),
        (_scope(unit_id="other-unit"), "3550308", FiscalDocumentKind.NFSE, "authorize"),
        (
            _scope(environment=FiscalEnvironment.PRODUCTION),
            "3550308", FiscalDocumentKind.NFSE, "authorize",
        ),
    ],
)
def test_routing_fails_closed_on_invalid_scope_kind_or_operation(
    scope: ExecutionScope, code: str, kind: FiscalDocumentKind, operation: str,
) -> None:
    approved = _scope()
    binding = _binding(approved, "3550308")
    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda _scope, _code: binding
    )
    with pytest.raises(UnsupportedProviderError):
        _resolve(resolver, scope, code=code, kind=kind, operation=operation)


def test_unknown_municipality_and_no_approval_never_fall_back() -> None:
    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda _scope, _code: None
    )
    with pytest.raises(UnsupportedProviderError):
        _resolve(resolver, _scope())
    with pytest.raises(UnsupportedProviderError):
        _resolve(resolver, _scope(), code="3500000")


def test_taker_location_cannot_override_issuer_routing() -> None:
    scope = _scope()
    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda s, code: _binding(s, code)
    )
    assert _resolve(resolver, scope, "3550308") == "nota-paulistana"
    with pytest.raises(UnsupportedProviderError):
        _resolve(resolver, scope, "3509502")


def test_disabled_and_unapproved_operations_are_rejected() -> None:
    scope = _scope()
    record = _binding(scope, "3550308")
    from dataclasses import replace

    resolver = GovernedSpMunicipalProviderResolver(
        load_approved_binding=lambda _s, _code: replace(record, enabled=False)
    )
    with pytest.raises(UnsupportedProviderError):
        _resolve(resolver, scope)


def test_invalid_approval_metadata_fails_before_routing() -> None:
    with pytest.raises(FiscalValidationError):
        ApprovedMunicipalProviderBinding(
            host_namespace="nfcore", tenant_id="t", unit_id="u",
            environment=FiscalEnvironment.HOMOLOGATION,
            issuer_municipality_ibge="bad", provider_id="dsf",
            version=1, approved_by="admin", approved_at=datetime.now(UTC),
            enabled=True, permitted_operations=frozenset({ProviderOperation.AUTHORIZE}),
        )
