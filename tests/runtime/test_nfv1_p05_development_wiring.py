"""P05 local-only fiscal/Command wiring: no external fiscal or payment effects."""

from datetime import UTC, datetime, timedelta

import pytest

from kordena_fiscal.domain import (
    Cnpj,
    ElectronicInvoiceModel,
    ExecutionScope,
    FiscalEnvironment,
    FiscalValidationError,
)
from kordena_fiscal.product.command_commercial import CommandBinding
from kordena_fiscal.runtime.config import RuntimeConfigurationError, RuntimeSettings
from kordena_fiscal.runtime.development_commercial_ingress import (
    development_command_resolver,
    development_commercial_ingress,
)
from kordena_fiscal.runtime.development_fiscal_ingress import development_fiscal_ingress
from kordena_fiscal.security.secrets import SecretReference, SecretResolutionError, SecretScope
from kordena_fiscal.xml import AccessKeyInput, build_access_key


def _settings(environment: str) -> RuntimeSettings:
    values = {"NFCORE_ENVIRONMENT": environment}
    if environment in {"staging", "production"}:
        values.update(
            {
                "NFCORE_PERSISTENCE_BACKEND": "postgres",
                "NFCORE_SECRET_BACKEND": "external",
                "NFCORE_REQUIRE_HTTPS": "true",
                "DATABASE_URL": "postgresql://local:local@localhost/nfcore",
            }
        )
    if environment == "production":
        values["NFCORE_PUBLIC_HOSTNAME"] = "nfcore.example.com"
    return RuntimeSettings.from_mapping(values)


def _scope() -> ExecutionScope:
    return ExecutionScope(
        tenant_id="tenant-a",
        unit_id="unit-a",
        environment=FiscalEnvironment.HOMOLOGATION,
        correlation_id="dev-query",
    )


def _access_key() -> str:
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


FISCAL_FLAG = {"NFCORE_DEV_FISCAL_QUERY_MODE": "synthetic_pending"}
COMMAND_FLAGS = {
    "NFCORE_DEV_COMMAND_KEY_ID": "command-local",
    "NFCORE_DEV_COMMAND_BINDING_ID": "local-binding",
    "NFCORE_DEV_COMMAND_SECRET_REFERENCE": "sec_local_only_command_0001",
    "NFCORE_DEV_COMMAND_HMAC_SECRET": "local-only-command-test-secret-32-characters",
}


@pytest.mark.parametrize("environment", ("development", "test"))
def test_no_implicit_fiscal_or_command_wiring(environment: str) -> None:
    settings = _settings(environment)
    assert development_fiscal_ingress(settings, {}) == {}
    assert development_command_resolver(settings, {}) is None


@pytest.mark.parametrize("environment", ("staging", "production"))
def test_local_only_wiring_cannot_activate_in_hosted_environments(environment: str) -> None:
    settings = _settings(environment)
    assert development_fiscal_ingress(settings, FISCAL_FLAG) == {}
    assert development_command_resolver(settings, COMMAND_FLAGS) is None
    assert (
        development_commercial_ingress(
            settings, {"NFCORE_DEV_TRIAL_KEY_ID": "trial", "NFCORE_DEV_TRIAL_HMAC_SECRET": "t" * 40}
        )
        == {}
    )


def test_development_fiscal_query_uses_canonical_client_and_labels_simulation() -> None:
    handlers = development_fiscal_ingress(_settings("development"), FISCAL_FLAG)
    assert set(handlers) == {"queryFiscalDocument"}
    result = handlers["queryFiscalDocument"](_scope(), {"access_key": _access_key()}, None)
    assert result["access_key"] == _access_key()
    assert result["status"] == "pending"
    assert result["protocol_reference"] is None
    assert result["simulation"] is True
    assert result["official_fiscal_evidence"] is False
    assert result["provider_origin"] == "synthetic_local_only"
    # Issuance, cancellation, inutilization and reconciliation remain unconfigured.
    assert "issueFiscalDocument" not in handlers
    assert "cancelFiscalDocument" not in handlers
    assert "inutilizeFiscalRange" not in handlers


def test_development_fiscal_query_rejects_invalid_inputs() -> None:
    handler = development_fiscal_ingress(_settings("test"), FISCAL_FLAG)["queryFiscalDocument"]
    with pytest.raises(FiscalValidationError):
        handler(_scope(), {"access_key": "invalid"}, None)


def test_invalid_development_fiscal_mode_fails_closed() -> None:
    with pytest.raises(RuntimeConfigurationError, match="unsupported local-only"):
        development_fiscal_ingress(
            _settings("development"), {"NFCORE_DEV_FISCAL_QUERY_MODE": "real_authorized"}
        )


def test_local_command_resolver_matches_canonical_binding_scope_only() -> None:
    resolver = development_command_resolver(_settings("development"), COMMAND_FLAGS)
    assert resolver is not None and resolver.environment == "development"
    binding = CommandBinding(
        key_id=COMMAND_FLAGS["NFCORE_DEV_COMMAND_KEY_ID"],
        binding_id=COMMAND_FLAGS["NFCORE_DEV_COMMAND_BINDING_ID"],
        product_id="nfcore",
        environment="development",
        secret_reference=COMMAND_FLAGS["NFCORE_DEV_COMMAND_SECRET_REFERENCE"],
        secret_version=1,
        not_after=datetime.now(UTC) + timedelta(days=1),
    )
    with resolver.resolve(
        SecretReference(binding.secret_reference, 1), scope=binding.scope
    ) as secret:
        assert secret.reveal() == COMMAND_FLAGS["NFCORE_DEV_COMMAND_HMAC_SECRET"].encode()
    with pytest.raises(SecretResolutionError):
        resolver.resolve(
            SecretReference(binding.secret_reference, 1),
            scope=SecretScope("other-tenant", None, "commercial.command.webhook"),
        )


@pytest.mark.parametrize("missing", tuple(COMMAND_FLAGS))
def test_partial_local_command_configuration_fails_closed(missing: str) -> None:
    flags = dict(COMMAND_FLAGS)
    flags.pop(missing)
    with pytest.raises(RuntimeConfigurationError, match="incomplete"):
        development_command_resolver(_settings("development"), flags)


def test_short_or_invalid_local_command_key_fails_closed() -> None:
    flags = dict(COMMAND_FLAGS)
    flags["NFCORE_DEV_COMMAND_HMAC_SECRET"] = "too-short"
    with pytest.raises(RuntimeConfigurationError):
        development_command_resolver(_settings("development"), flags)
    flags = dict(COMMAND_FLAGS)
    flags["NFCORE_DEV_COMMAND_SECRET_REFERENCE"] = "not-a-reference"
    with pytest.raises(RuntimeConfigurationError):
        development_command_resolver(_settings("development"), flags)
