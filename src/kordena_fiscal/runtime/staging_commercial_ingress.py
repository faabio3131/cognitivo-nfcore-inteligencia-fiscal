"""Governed staging commercial ingress on the existing NFCore GSM secret authority.

This opt-in only composes the *existing* signed trial/acquisition routers. It never
turns a development key into a staging credential, exposes a signing key to a
browser, creates a tenant, approves prices or starts a public trial by itself.
The API's already approved GSM workload identity is reused, but signing
bindings/resources are separate from the fiscal webhook pilot.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime

from kordena_fiscal.persistence.postgres import PostgresFiscalDatabase
from kordena_fiscal.security.s2s import WebhookSecurity
from kordena_fiscal.security.secrets import SecretReference, SecretResolver, SecretScope
from kordena_fiscal.vault.google_secret_manager import (
    DurableGsmReader,
    GoogleSignatureSecretBackend,
)

from .api_staging_gsm_probe import _credentials, _timestamp
from .config import RuntimeConfigurationError
from .gsm_staging_identity_policy import (
    PROJECT_NUMBERS,
    build_staging_workload_gsm_access,
)

_MODE = "scoped-staging-gsm-v1"
_GSM_API_MODE = "scoped-staging-sa-v1"
_RESOURCE = re.compile(
    r"projects/fm-nfcore-staging/secrets/[A-Za-z0-9_-]{1,255}\Z"
)
_CHANNELS = {
    "TRIAL": ("commercial_trial_security", "commercial-trial-ingress"),
    "ACQUISITION": ("commercial_acquisition_security", "commercial-acquisition-ingress"),
}
_PROVIDER = "google-secret-manager"
_PLATFORM_TENANT = "nfcore-platform"
_WORKLOAD = "nfcore-api"


class _CommercialSigningKeys:
    """Resolve only the pinned channel reference through the canonical vault."""

    def __init__(
        self, resolver: SecretResolver, reference: SecretReference, scope: SecretScope
    ) -> None:
        self._resolver = resolver
        self._reference = reference
        self._scope = scope

    def resolve(self, key_id: str) -> bytes | None:
        if key_id != self._reference.reference_id:
            return None
        with self._resolver.resolve(self._reference, scope=self._scope) as material:
            return material.reveal()


def staging_commercial_ingress(
    database: PostgresFiscalDatabase,
    environ: Mapping[str, str] | None = None,
) -> dict[str, WebhookSecurity]:
    """Explicit signed S2S channels; missing opt-in leaves routes disabled.

    The existing trial/account/tenant/price/activation service remains the
    *only* business authority. Never derive channel, secret scope or tenant from
    an HTTP payload, never resolve any fiscal webhook pilot secret as a trial key.
    """
    source = os.environ if environ is None else environ
    mode = source.get("NFCORE_STAGING_COMMERCIAL_INGRESS_MODE", "").strip()
    if not mode:
        return {}
    if (
        mode != _MODE
        or source.get("NFCORE_ENVIRONMENT") != "staging"
        or source.get("NFCORE_API_GSM_MODE") != _GSM_API_MODE
    ):
        raise RuntimeConfigurationError("staging commercial ingress identity denied")

    enabled = [
        channel
        for channel in _CHANNELS
        if any(
            source.get(f"NFCORE_STAGING_COMMERCIAL_{channel}_{field}", "")
            for field in ("REFERENCE", "VERSION", "RESOURCE")
        )
    ]
    if not enabled:
        raise RuntimeConfigurationError("staging commercial ingress has no approved channels")

    phase = "CHANNEL_BINDING"
    try:
        declared: dict[str, tuple[SecretReference, SecretScope, str]] = {}
        for channel in enabled:
            prefix = f"NFCORE_STAGING_COMMERCIAL_{channel}_"
            reference = SecretReference(\n                source[prefix + "REFERENCE"], int(source[prefix + "VERSION"])\n            )
            resource = source[prefix + "RESOURCE"]
            if not _RESOURCE.fullmatch(resource):
                raise ValueError("invalid staging resource")
            purpose = _CHANNELS[channel][1]
            scope = SecretScope(_PLATFORM_TENANT, None, purpose)
            with database() as uow:
                binding = uow.secret_bindings.get(reference.reference_id)
            if (
                binding is None
                or binding.tenant_id != scope.tenant_id
                or binding.unit_id is not None
                or binding.purpose != scope.purpose
                or binding.runtime_environment != "staging"
                or binding.fiscal_environment is not None
                or binding.workload_id != _WORKLOAD
                or binding.kind != "signature"
                or binding.canonical_version != reference.version
                or binding.provider_id != _PROVIDER
                or binding.resource != resource
                or binding.state != "active"
                or (binding.not_after is not None and binding.not_after <= datetime.now(UTC))
            ):
                raise ValueError("binding scope unavailable")
            declared[channel] = (reference, scope, resource)
        if len({ref.reference_id for ref, _scope, _resource in declared.values()}) != len(declared):
            raise ValueError("commercial channels must have distinct signing references")
        if len({resource for _ref, _scope, resource in declared.values()}) != len(declared):
            raise ValueError("commercial channels must have distinct signing resources")

        phase = "SERVICE_IDENTITY"
        credentials = _credentials(
            source["NFCORE_API_GSM_CREDENTIAL_JSON"],
            source["NFCORE_API_GSM_KEY_ID"],
        )
        access = build_staging_workload_gsm_access(
            credentials=credentials,
            workload_id=_WORKLOAD,
            environment="staging",
            key_created_at=_timestamp(source["NFCORE_API_GSM_KEY_CREATED_AT"]),
            key_not_after=_timestamp(source["NFCORE_API_GSM_KEY_NOT_AFTER"]),
        )
        phase = "SECRET_RESOLUTION"
        reader = DurableGsmReader(
            uow_factory=database,
            access=access,
            environment="staging",
            workload_id=_WORKLOAD,
            allowed_resources=frozenset(resource for _, _, resource in declared.values()),
            project_numbers=PROJECT_NUMBERS,
        )
        resolver = SecretResolver(
            GoogleSignatureSecretBackend(reader, provider_id=_PROVIDER),
            environment="staging",
        )
        result: dict[str, WebhookSecurity] = {}
        for channel, (reference, scope, _resource) in declared.items():
            # Fail closed on absent permission, wrong envelope, revoked binding
            # or weak signing material before announcing the route as ready.
            with resolver.resolve(reference, scope=scope) as material:
                if len(material.reveal()) < 32:
                    raise ValueError("weak signing material")
            result[_CHANNELS[channel][0]] = WebhookSecurity(
                key_resolver=_CommercialSigningKeys(resolver, reference, scope),
                signing_key_id=reference.reference_id,
            )
        return result
    except Exception:
        # No secret, identity, reference, tenant, provider payload or raw
        # provider exception is ever copied to the public error/log boundary.
        raise RuntimeConfigurationError(
            f"staging commercial ingress unavailable [{phase}]"
        ) from None
