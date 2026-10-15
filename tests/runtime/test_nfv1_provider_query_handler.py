"""Explicit provider query wiring contract: no implicit real/synthetic provider."""
from datetime import UTC, datetime

import pytest

from kordena_fiscal.domain import Cnpj, ElectronicInvoiceModel, ExecutionScope, FiscalEnvironment, FiscalValidationError
from kordena_fiscal.operations import FakeFiscalOperationsGateway, FiscalOperationsClient, FiscalQueryStatus
from kordena_fiscal.runtime.provider_query_handler import build_provider_query_handler
from kordena_fiscal.xml import AccessKeyInput, build_access_key


def _scope(unit: str = "unit-a") -> ExecutionScope:
    return ExecutionScope(
        tenant_id="tenant-a", unit_id=unit,
        environment=FiscalEnvironment.HOMOLOGATION, correlation_id="query-test",
    )


def _key() -> str:
    return build_access_key(
        AccessKeyInput(
            state_ibge_code="35",
            issued_at=datetime(2026, 9, 11, tzinfo=UTC),
            issuer_cnpj=Cnpj("12.345.678/0001-95"),
            model=ElectronicInvoiceModel.NFCE,
            series=3, invoice_number=10, emission_type=1, numeric_code=12345678,
        )
    ).value


def test_provider_query_delegates_to_same_scope_and_returns_verified_result() -> None:
    gateway = FakeFiscalOperationsGateway(query_status=FiscalQueryStatus.AUTHORIZED)
    handler = build_provider_query_handler(FiscalOperationsClient(gateway))
    result = handler(_scope(), {"access_key": _key()}, None)
    assert result["status"] == "authorized"
    assert result["protocol_reference"] == "SYNTHETIC-AUTH-PROTOCOL"
    assert result["access_key"] == _key()
    assert gateway.query_calls[0].scope == _scope()
    assert gateway.query_calls[0].access_key.value == _key()
    assert len(gateway.query_calls) == 1


def test_provider_query_never_forwards_invalid_or_missing_access_key() -> None:
    gateway = FakeFiscalOperationsGateway()
    handler = build_provider_query_handler(FiscalOperationsClient(gateway))
    for payload in ({}, {"access_key": 123}, {"access_key": "not-an-access-key"}):
        with pytest.raises(FiscalValidationError):
            handler(_scope(), payload, None)
    assert gateway.query_calls == ()


def test_provider_query_keeps_exact_requested_unit_scope() -> None:
    gateway = FakeFiscalOperationsGateway(query_status=FiscalQueryStatus.NOT_FOUND)
    handler = build_provider_query_handler(FiscalOperationsClient(gateway))
    result = handler(_scope("unit-b"), {"access_key": _key()}, None)
    assert result["status"] == "not_found"
    assert result["protocol_reference"] is None
    assert gateway.query_calls[0].scope.unit_id == "unit-b"
