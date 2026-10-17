"""Explicit local-only signed commercial ingress, never implicit provider authority.

External staging and production credentials use their own governed secret backends.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from kordena_fiscal.product.command_commercial import CommandBinding
from kordena_fiscal.product.commercial_fulfillment import CommercialFulfillmentError
from kordena_fiscal.runtime.config import (
    RuntimeConfigurationError,
    RuntimeEnvironment,
    RuntimeSettings,
)
from kordena_fiscal.security.s2s import InMemoryWebhookKeyRing, WebhookSecurity
from kordena_fiscal.security.secrets import (
    InMemorySecretBackend,
    SecretResolutionError,
    SecretResolver,
)


def development_commercial_ingress(
    settings: RuntimeSettings,
    variables: Mapping[str, str],
) -> dict[str, WebhookSecurity]:
    """Compose optional signed S2S channels exclusively for local development/test."""
    if settings.environment not in {RuntimeEnvironment.DEVELOPMENT, RuntimeEnvironment.TEST}:
        return {}

    result: dict[str, WebhookSecurity] = {}
    for channel, argument in (
        ("ACQUISITION", "commercial_acquisition_security"),
        ("TRIAL", "commercial_trial_security"),
    ):
        key_id = variables.get(f"NFCORE_DEV_{channel}_KEY_ID", "").strip()
        secret = variables.get(f"NFCORE_DEV_{channel}_HMAC_SECRET", "")
        if not key_id and not secret:
            continue
        if not key_id or len(secret.encode("utf-8")) < 32:
            raise RuntimeConfigurationError(
                f"development {channel.lower()} signing configuration is incomplete"
            )
        resolver = InMemoryWebhookKeyRing(
            active_key_id=key_id,
            keys={key_id: secret.encode("utf-8")},
        )
        result[argument] = WebhookSecurity(
            key_resolver=resolver,
            signing_key_id=key_id,
        )
    return result


def development_command_resolver(
    settings: RuntimeSettings,
    variables: Mapping[str, str],
) -> SecretResolver | None:
    """Resolve explicitly provisioned local Command binding keys without new auth.

    The binding metadata must *already* be configured through the canonical
    commercial administration. No binding, checkout, offer or purchase is created.
    The local backend is structurally forbidden in staging/production.
    """
    if settings.environment not in {RuntimeEnvironment.DEVELOPMENT, RuntimeEnvironment.TEST}:
        return None

    names = (
        "NFCORE_DEV_COMMAND_BINDING_ID",
        "NFCORE_DEV_COMMAND_KEY_ID",
        "NFCORE_DEV_COMMAND_SECRET_REFERENCE",
        "NFCORE_DEV_COMMAND_HMAC_SECRET",
    )
    supplied = {name: variables.get(name, "").strip() for name in names}
    if not any(supplied.values()):
        return None
    if not all(supplied.values()) or len(supplied[names[-1]].encode("utf-8")) < 32:
        raise RuntimeConfigurationError("local Command signing configuration is incomplete")

    try:
        # Only reuse CommandBinding's canonical scope derivation. This ephemeral
        # shape is never persisted or used to authorize any commercial action.
        binding = CommandBinding(
            key_id=supplied[names[1]],
            binding_id=supplied[names[0]],
            product_id="nfcore",
            environment=settings.environment.value,
            secret_reference=supplied[names[2]],
            secret_version=1,
            not_after=datetime.now(UTC) + timedelta(days=1),
        )
        backend = InMemorySecretBackend()
        backend.put(
            reference_id=binding.secret_reference,
            scope=binding.scope,
            value=supplied[names[3]].encode("utf-8"),
        )
        return SecretResolver(backend, environment=settings.environment.value)
    except (CommercialFulfillmentError, SecretResolutionError) as exc:
        raise RuntimeConfigurationError("invalid local Command signing configuration") from exc
