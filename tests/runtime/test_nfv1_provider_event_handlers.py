"""BLD-02: provider-neutral event handlers stay opt-in, scoped and fail-closed."""
from datetime import UTC, datetime

import pytest

from kordena_fiscal.domain import (
    Cnpj,
    ElectronicInvoiceModel,
    ExecutionScope,
    FiscalEnvironment,
    FiscalValidationError,
)
from kordena_fiscal.operations import (
    FakeFiscalOperationsGateway,
    FiscalOperationsClient,
    FiscalOperationsContractError,
    MutatingFiscalOperationsGateway,
)
from kordena_fiscal.runtime.provider_event_handlers import (
    build_provider_cancel_handler,
    build_provider_inutilization_handler,
)
from kordena_fiscal.xml import AccessKeyInput, build_access_key


def scope() -> ExecutionScope:
    return ExecutionScope(
        tenant_id="tenant-a",
        unit_id="unit-a",
        environment=FiscalEnvironment.HOMOLOGATION,
        correlation_id="event-test",
    )


def access_key() -> str:
    return build_access_key(
        AccessKeyInput(
            state_ibge_code="35",
            issued_at=datetime(2026, 9, 11, tzinfo=UTC),
            issuer_cnpj=Cnpj("12.345.678/0001-95"),
            model=ElectronicInvoiceModel.NFCE,
            series=3,
            invoice_number=10,
            emission_type=1,
            numeric_code=12345678,
        )
    ).value


def test_cancel_delegates_verified_identity_to_supplied_client() -> None:
    gateway = FakeFiscalOperationsGateway()
    handler = build_provider_cancel_handler(FiscalOperationsClient(gateway))
    result = handler(scope(), {
        "access_key": access_key(),
        "authorization_protocol": "AUTH-123",
        "justification": "Cancelamento de teste controlado",
    }, "retry-key")
    assert result["status"] == "accepted"
    assert result["request_id"] == gateway.cancel_calls[0].request_id
    assert result["event_protocol_reference"] == "SYNTHETIC-CANCEL-PROTOCOL"
    assert gateway.cancel_calls[0].scope == scope()


def test_inutilization_delegates_validated_range_to_supplied_client() -> None:
    gateway = FakeFiscalOperationsGateway()
    handler = build_provider_inutilization_handler(FiscalOperationsClient(gateway))
    payload = {"model": 55, "series": 1, "first_number": 10,
               "last_number": 12, "justification": "Faixa de teste controlada"}
    result = handler(scope(), payload, "retry-key")
    assert result["status"] == "accepted"
    assert result["request_id"] == gateway.inutilization_calls[0].request_id
    assert gateway.inutilization_calls[0].scope == scope()
    assert result["first_number"] == 10


def test_invalid_event_requests_do_not_call_gateway() -> None:
    gateway = FakeFiscalOperationsGateway()
    cancel = build_provider_cancel_handler(FiscalOperationsClient(gateway))
    inutilize = build_provider_inutilization_handler(FiscalOperationsClient(gateway))
    with pytest.raises(FiscalValidationError):
        cancel(scope(), {"access_key": access_key()}, None)
    with pytest.raises(FiscalValidationError):
        inutilize(scope(), {"model": True, "series": 1, "first_number": 1,
                            "last_number": 2, "justification": "Justificativa válida"}, None)
    assert not gateway.cancel_calls
    assert not gateway.inutilization_calls


def test_provider_identity_mismatch_is_rejected_before_result_exposure() -> None:
    cancel = build_provider_cancel_handler(
        FiscalOperationsClient(MutatingFiscalOperationsGateway(mutate="cancel_scope"))
    )
    with pytest.raises(FiscalOperationsContractError):
        cancel(scope(), {
            "access_key": access_key(),
            "authorization_protocol": "AUTH-123",
            "justification": "Cancelamento de teste controlado",
        }, None)
    inutilize = build_provider_inutilization_handler(
        FiscalOperationsClient(MutatingFiscalOperationsGateway(mutate="inutilization_range"))
    )
    with pytest.raises(FiscalOperationsContractError):
        inutilize(scope(), {
            "model": 55, "series": 1, "first_number": 10, "last_number": 12,
            "justification": "Faixa de teste controlada",
        }, None)
