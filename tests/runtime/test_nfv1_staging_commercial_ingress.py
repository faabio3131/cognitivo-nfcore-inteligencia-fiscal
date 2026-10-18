"""Staging commercial ingress is real vault-backed or absent, never dev HMAC."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

import pytest

from kordena_fiscal.runtime.config import RuntimeConfigurationError
from kordena_fiscal.runtime.staging_commercial_ingress import staging_commercial_ingress
from kordena_fiscal.security.secret_binding import SecretBinding


class _GuardedDatabase:
    def __init__(self, binding: SecretBinding | None = None) -> None:
        self.binding = binding
        self.reads = 0

    def __call__(self) -> Any:
        self.reads += 1
        return nullcontext(self)

    @property
    def secret_bindings(self) -> _GuardedDatabase:
        return self

    def get(self, _reference: str) -> SecretBinding | None:
        return self.binding


def _values(**extra: str) -> dict[str, str]:
    return {
        "NFCORE_ENVIRONMENT": "staging",
        "NFCORE_API_GSM_MODE": "scoped-staging-sa-v1",
        "NFCORE_STAGING_COMMERCIAL_INGRESS_MODE": "scoped-staging-gsm-v1",
        "NFCORE_STAGING_COMMERCIAL_TRIAL_REFERENCE": "sec_nfcore_commercial_trial_staging_01",
        "NFCORE_STAGING_COMMERCIAL_TRIAL_VERSION": "1",
        "NFCORE_STAGING_COMMERCIAL_TRIAL_RESOURCE":
            "projects/fm-nfcore-staging/secrets/nfcore-commercial-trial-stg",
        **extra,
    }


def test_no_opt_in_does_not_read_database_or_open_a_trial_route() -> None:
    database = _GuardedDatabase()
    assert staging_commercial_ingress(database, {}) == {}  # type: ignore[arg-type]
    assert database.reads == 0


@pytest.mark.parametrize(
    "override",
    [
        {"NFCORE_ENVIRONMENT": "production"},
        {"NFCORE_ENVIRONMENT": "development"},
        {"NFCORE_API_GSM_MODE": ""},
        {"NFCORE_STAGING_COMMERCIAL_INGRESS_MODE": "development"},
    ],
)
def test_development_or_unapproved_identity_cannot_be_promoted(
    override: dict[str, str],
) -> None:
    database = _GuardedDatabase()
    with pytest.raises(RuntimeConfigurationError, match="identity denied"):
        staging_commercial_ingress(database, _values(**override))  # type: ignore[arg-type]
    assert database.reads == 0


def test_gsm_resource_must_be_in_staging_project_before_any_secret_read() -> None:
    database = _GuardedDatabase()
    with pytest.raises(RuntimeConfigurationError, match="CHANNEL_BINDING"):
        staging_commercial_ingress(database, _values(
            NFCORE_STAGING_COMMERCIAL_TRIAL_RESOURCE=
                "projects/other-project/secrets/unknown",
        ))  # type: ignore[arg-type]
    assert database.reads == 0


def test_cannot_route_trial_with_unbound_secret_or_pilot_webhook() -> None:
    database = _GuardedDatabase()
    with pytest.raises(RuntimeConfigurationError, match="CHANNEL_BINDING"):
        staging_commercial_ingress(database, _values())  # type: ignore[arg-type]
    assert database.reads == 1


def test_staging_commercial_requires_at_least_one_explicit_channel() -> None:
    database = _GuardedDatabase()
    with pytest.raises(RuntimeConfigurationError, match="no approved channels"):
        staging_commercial_ingress(
            database,
            {k: v for k, v in _values().items() if "COMMERCIAL_TRIAL_" not in k},
        )  # type: ignore[arg-type]
    assert database.reads == 0


def test_distinct_approved_trial_channel_fails_closed_without_api_identity() -> None:
    database = _GuardedDatabase(SecretBinding(
        reference_id="sec_nfcore_commercial_trial_staging_01",
        tenant_id="nfcore-platform",
        unit_id=None,
        purpose="commercial-trial-ingress",
        runtime_environment="staging",
        fiscal_environment=None,
        provider_id="google-secret-manager",
        workload_id="nfcore-api",
        kind="signature",
        canonical_version=1,
        resource="projects/fm-nfcore-staging/secrets/nfcore-commercial-trial-stg",
        cloud_version="1",
    ))
    with pytest.raises(RuntimeConfigurationError, match="SERVICE_IDENTITY"):
        staging_commercial_ingress(database, _values())  # type: ignore[arg-type]
    assert database.reads == 1
