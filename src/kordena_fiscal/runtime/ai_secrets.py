"""Explicit, non-fiscal AI API key access through the EXISTING GSM transport.

OpenAI's previously provisioned v1 is a raw credential, not a fiscal
SecretBinding envelope. Never reinterpret it as a fiscal signature/CSC.
The exact pinned resource and version plus API workload IAM are mandatory.
No ADC, implicit credentials, latest aliases, cloud writes or secret logs.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

import google_crc32c
from google.cloud import secretmanager_v1

from kordena_fiscal.vault.google_secret_manager import (
    GoogleSdkSecretAccess,
    GsmAccess,
    same_secret_version,
)

from .config import RuntimeConfigurationError
from .production_gsm import ProductionWorkloadIdentity, production_credentials

_PROJECT = "fm-nfcore-prod"
_PROJECT_NUMBER = "646230745113"
_RESOURCE = f"projects/{_PROJECT}/secrets/nfcore-openai-api-key"
_PROVIDER = "openai"
_KEY_SHAPE = re.compile(r"sk-[A-Za-z0-9_-]{20,512}\Z", re.ASCII)
_MODE = "pinned-gsm-openai-v1"


def pinned_openai_key_reader(
    *,
    access: GsmAccess,
    resource: str,
    version: str,
    project_number: str = _PROJECT_NUMBER,
) -> Callable[[], str | None]:
    """Return a lazy, non-caching reader; no access during construction."""
    if (
        resource != _RESOURCE
        or project_number != _PROJECT_NUMBER
        or not re.fullmatch(r"[1-9][0-9]{0,18}", version)
    ):
        raise RuntimeConfigurationError("AI GSM resource/version not approved")
    target = f"{resource}/versions/{version}"

    def read() -> str | None:
        try:
            payload = access.access(target)
            if (
                not same_secret_version(payload.name, target, {_PROJECT: _PROJECT_NUMBER})
                or type(payload.data) is not bytes
                or not 25 <= len(payload.data) <= 520
                or type(payload.crc32c) is not int
                or google_crc32c.value(payload.data) != payload.crc32c
            ):
                raise ValueError
            key = payload.data.decode("ascii")
            if not _KEY_SHAPE.fullmatch(key):
                raise ValueError
            return key
        except Exception:
            # Caller treats unavailable material as ModelProviderDenied.
            # Never leak provider payload, credentials, or internal exception.
            return None

    return read


def build_production_openai_key_readers(
    environ: Mapping[str, str],
    *,
    access: GsmAccess | None = None,
) -> dict[str, Callable[[], str | None]]:
    """Explicit opt-in in production only, same API workload identity path.

    Cloud access is never attempted during setup; all material reads are lazy.
    """
    mode = environ.get("NFCORE_COGNITIVE_AI_SECRET_MODE", "")
    if not mode:
        return {}
    if mode != _MODE or environ.get("NFCORE_ENVIRONMENT") != "production":
        raise RuntimeConfigurationError("AI GSM mode denied")
    if (
        environ.get("NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL") != "https://api.openai.com/v1"
        or not re.fullmatch(
            r"[A-Za-z0-9._-]{1,128}", environ.get("NFCORE_COGNITIVE_AI_SECONDARY_MODEL", "")
        )
        or environ.get("NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER") != _PROVIDER
        or environ.get("NFCORE_COGNITIVE_AI_SECONDARY_API_KEY")
        or environ.get("NFCORE_GSM_PROJECT_ID") != _PROJECT
        or environ.get("NFCORE_GSM_PROJECT_NUMBER") != _PROJECT_NUMBER
    ):
        raise RuntimeConfigurationError("AI GSM identity/provider configuration denied")
    version = environ.get("NFCORE_COGNITIVE_AI_SECONDARY_GSM_VERSION", "")
    if access is None:
        sa = environ.get("NFCORE_GSM_API_SERVICE_ACCOUNT", "")
        if sa != f"nfcore-api@{_PROJECT}.iam.gserviceaccount.com":
            raise RuntimeConfigurationError("AI GSM API identity not pinned")
        identity = ProductionWorkloadIdentity(role="API", project=_PROJECT, service_account=sa)
        credentials, expires_at = production_credentials(environ, identity)
        try:
            client = secretmanager_v1.SecretManagerServiceClient(
                credentials=credentials,
                client_options={
                    "api_endpoint": "secretmanager.googleapis.com",
                    "universe_domain": "googleapis.com",
                },
            )
        except Exception:
            raise RuntimeConfigurationError("AI GSM SDK identity unavailable") from None
        access = GoogleSdkSecretAccess(client, bootstrap_not_after=expires_at)
    return {
        "NFCORE_COGNITIVE_AI_SECONDARY_API_KEY": pinned_openai_key_reader(
            access=access, resource=_RESOURCE, version=version
        )
    }
