"""Dev-only ingress wiring regression: no implicit trust or staging activation."""

import pytest

from kordena_fiscal.runtime.config import RuntimeConfigurationError, RuntimeSettings
from kordena_fiscal.runtime.development_commercial_ingress import (
    development_commercial_ingress,
)
from kordena_fiscal.security.s2s import WebhookSecurity


def _settings(environment: str) -> RuntimeSettings:
    if environment == "staging":
        return RuntimeSettings.from_mapping({
            "NFCORE_ENVIRONMENT": "staging",
            "NFCORE_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": "postgresql://local:local@localhost/nfcore",
            "NFCORE_SECRET_BACKEND": "external",
            "NFCORE_REQUIRE_HTTPS": "true",
        })
    return RuntimeSettings.from_mapping({"NFCORE_ENVIRONMENT": environment})


def test_no_implicit_development_ingress() -> None:
    assert development_commercial_ingress(_settings("development"), {}) == {}


def test_incomplete_development_signing_configuration_fails_closed() -> None:
    with pytest.raises(RuntimeConfigurationError):
        development_commercial_ingress(
            _settings("development"),
            {"NFCORE_DEV_TRIAL_KEY_ID": "test-trial"},
        )


def test_explicit_development_channels_use_existing_webhook_security() -> None:
    result = development_commercial_ingress(
        _settings("development"),
        {
            "NFCORE_DEV_TRIAL_KEY_ID": "trial-dev",
            "NFCORE_DEV_TRIAL_HMAC_SECRET": "t" * 40,
            "NFCORE_DEV_ACQUISITION_KEY_ID": "purchase-dev",
            "NFCORE_DEV_ACQUISITION_HMAC_SECRET": "p" * 40,
        },
    )
    assert set(result) == {
        "commercial_trial_security",
        "commercial_acquisition_security",
    }
    assert all(isinstance(value, WebhookSecurity) for value in result.values())


def test_staging_cannot_enable_development_ingress() -> None:
    assert development_commercial_ingress(
        _settings("staging"),
        {
            "NFCORE_DEV_TRIAL_KEY_ID": "trial-dev",
            "NFCORE_DEV_TRIAL_HMAC_SECRET": "t" * 40,
        },
    ) == {}
