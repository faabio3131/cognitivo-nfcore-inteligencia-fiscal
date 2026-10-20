"""BLD-02 unified injection preserves canonical contracts and fail-closed defaults."""

import pytest

from kordena_fiscal.domain import FiscalValidationError
from kordena_fiscal.operations import FakeFiscalOperationsGateway, FiscalOperationsClient
from kordena_fiscal.runtime.provider_operation_wiring import (
    build_provider_operation_handlers,
)


def test_requires_explicit_client() -> None:
    with pytest.raises(TypeError):
        build_provider_operation_handlers(None)  # type: ignore[arg-type]


def test_wires_only_certified_provider_operations() -> None:
    client = FiscalOperationsClient(FakeFiscalOperationsGateway())
    handlers = build_provider_operation_handlers(client)
    assert set(handlers) == {
        "queryFiscalDocument",
        "cancelFiscalDocument",
        "inutilizeFiscalRange",
    }
    assert "issueFiscalDocument" not in handlers
    assert "reconcileFiscalOperation" not in handlers


def test_invalid_query_fails_before_provider_execution() -> None:
    gateway = FakeFiscalOperationsGateway()
    handlers = build_provider_operation_handlers(FiscalOperationsClient(gateway))
    with pytest.raises(FiscalValidationError):
        handlers["queryFiscalDocument"](None, {"access_key": "invalid"}, None)  # type: ignore[arg-type]
    assert gateway.query_calls == ()
