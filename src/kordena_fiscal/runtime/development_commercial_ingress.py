"""Explicit development-only signed ingress composition for existing commercial routes.

Never enables unauthenticated public acquisition/trial or silently generates credentials.
Staging and production keep their separately governed security dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping

from kordena_fiscal.runtime.config import (
    RuntimeConfigurationError,
    RuntimeEnvironment,
    RuntimeSettings,
)
from kordena_fiscal.security.s2s import InMemoryWebhookKeyRing, WebhookSecurity


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
