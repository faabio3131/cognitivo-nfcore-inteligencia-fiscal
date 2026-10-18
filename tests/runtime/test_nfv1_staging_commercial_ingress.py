"""Staging commercial ingress is real vault-backed or absent, never dev HMAC."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
from typing import Any

import pytest

from kordena_fiscal.runtime import staging_commercial_ingress as commercial_module
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


def test_governed_trial_binding_composes_existing_signed_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = SecretBinding(
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
    )
    db = _GuardedDatabase(binding)
    # Only the GSM access transport is stubbed. Secret binding, scope,
    # SecretResolver and WebhookSecurity execute their actual contracts.
    monkeypatch.setattr(commercial_module, "_credentials", lambda *_args: object())
    monkeypatch.setattr(
        commercial_module, "build_staging_workload_gsm_access",
        lambda **_kwargs: object(),
    )

    class StubGsmReader:
        environment = "staging"

        def __init__(self, **kwargs: Any) -> None:
            assert kwargs["workload_id"] == "nfcore-api"
            assert kwargs["allowed_resources"] == frozenset({binding.resource})

        def read(self, **kwargs: Any) -> tuple[SecretBinding, bytes, None]:
            assert kwargs["reference_id"] == binding.reference_id
            assert kwargs["scope"].purpose == "commercial-trial-ingress"
            assert kwargs["kind"] == "signature"
            return binding, b"g" * 48, None

    monkeypatch.setattr(commercial_module, "DurableGsmReader", StubGsmReader)
    values = _values(
        NFCORE_API_GSM_CREDENTIAL_JSON="opaque-stub-value",
        NFCORE_API_GSM_KEY_ID="a" * 40,
        NFCORE_API_GSM_KEY_CREATED_AT="2026-10-18T00:00:00+00:00",
        NFCORE_API_GSM_KEY_NOT_AFTER="2026-11-18T00:00:00+00:00",
    )
    configured = staging_commercial_ingress(db, values)  # type: ignore[arg-type]
    assert set(configured) == {"commercial_trial_security"}
    security = configured["commercial_trial_security"]
    now = datetime.now(UTC)
    signature = security.sign(b'{"plan_id":"plan"}', now=now)
    security.verify(b'{"plan_id":"plan"}', signature, now=now)
