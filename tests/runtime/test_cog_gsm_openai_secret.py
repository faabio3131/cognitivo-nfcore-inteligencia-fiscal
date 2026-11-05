"""GSM-backed OpenAI credential: read-only, pinned and never logged."""

from __future__ import annotations

import google_crc32c
import pytest

from kordena_fiscal.runtime.ai_secrets import (
    build_production_openai_key_readers,
    pinned_openai_key_reader,
)
from kordena_fiscal.runtime.config import RuntimeConfigurationError
from kordena_fiscal.vault.google_secret_manager import GsmPayload

RESOURCE = "projects/fm-nfcore-prod/secrets/nfcore-openai-api-key"
NUMBER = "646230745113"
VALID = b"sk-proj-fake-synthetic-0123456789abcdefghijklmnop"


class Access:
    def __init__(
        self, *, data: bytes = VALID, name: str | None = None, corrupt_crc: bool = False
    ) -> None:
        self.data = data
        self.name = name or f"projects/{NUMBER}/secrets/nfcore-openai-api-key/versions/1"
        self.corrupt_crc = corrupt_crc
        self.calls: list[str] = []

    def access(self, name: str) -> GsmPayload:
        self.calls.append(name)
        return GsmPayload(
            self.name,
            self.data,
            google_crc32c.value(self.data) + int(self.corrupt_crc),
        )


def test_secret_is_lazy_and_version_and_identity_pinned() -> None:
    backend = Access()
    reader = pinned_openai_key_reader(access=backend, resource=RESOURCE, version="1")
    assert backend.calls == []
    assert reader() == VALID.decode()
    assert backend.calls == [RESOURCE + "/versions/1"]
    assert "sk-proj-" not in repr(reader)


@pytest.mark.parametrize(
    "resource,version,number",
    [
        (RESOURCE, "latest", NUMBER),
        (RESOURCE, "0", NUMBER),
        (RESOURCE, "01", NUMBER),
        ("projects/fm-nfcore-staging/secrets/nfcore-openai-api-key", "1", NUMBER),
        (RESOURCE, "1", "999999999999"),
    ],
)
def test_unapproved_reference_fails_before_cloud_io(
    resource: str,
    version: str,
    number: str,
) -> None:
    access = Access()
    with pytest.raises(RuntimeConfigurationError):
        pinned_openai_key_reader(
            access=access,
            resource=resource,
            version=version,
            project_number=number,
        )
    assert access.calls == []


@pytest.mark.parametrize(
    "backend",
    [
        Access(data=b"garbage"),
        Access(corrupt_crc=True),
        Access(name=f"projects/{NUMBER}/secrets/other-secret/versions/1"),
        Access(name=f"projects/{NUMBER}/secrets/nfcore-openai-api-key/versions/2"),
        Access(name="projects/999999999999/secrets/nfcore-openai-api-key/versions/1"),
    ],
)
def test_invalid_or_foreign_payload_denied_without_material(backend: Access) -> None:
    reader = pinned_openai_key_reader(access=backend, resource=RESOURCE, version="1")
    assert reader() is None


def test_transport_failure_denied_without_exception_material() -> None:
    class Broken:
        def access(self, name: str) -> GsmPayload:
            raise RuntimeError("sk-proj-secret-should-never-escape")

    reader = pinned_openai_key_reader(access=Broken(), resource=RESOURCE, version="1")
    assert reader() is None


def test_mode_off_does_not_touch_cloud() -> None:
    assert build_production_openai_key_readers({}) == {}


def test_mode_enabled_routes_only_openai_and_keeps_material_out_of_env() -> None:
    backend = Access()
    cfg = {
        "NFCORE_COGNITIVE_AI_SECRET_MODE": "pinned-gsm-openai-v1",
        "NFCORE_ENVIRONMENT": "production",
        "NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER": "openai",
        "NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL": "https://api.openai.com/v1",
        "NFCORE_COGNITIVE_AI_SECONDARY_MODEL": "gpt-synthetic",
        "NFCORE_GSM_PROJECT_ID": "fm-nfcore-prod",
        "NFCORE_GSM_PROJECT_NUMBER": NUMBER,
        "NFCORE_COGNITIVE_AI_SECONDARY_GSM_VERSION": "1",
    }
    readers = build_production_openai_key_readers(cfg, access=backend)
    assert len(readers) == 1
    assert readers["NFCORE_COGNITIVE_AI_SECONDARY_API_KEY"]() == VALID.decode()
    assert backend.calls == [RESOURCE + "/versions/1"]
    assert "sk-" not in str(cfg)


@pytest.mark.parametrize(
    "changed",
    [
        {"NFCORE_ENVIRONMENT": "staging"},
        {"NFCORE_GSM_PROJECT_ID": "fm-nfcore-staging"},
        {"NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER": "gemini"},
        {"NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL": "https://attacker.example/v1"},
        {"NFCORE_COGNITIVE_AI_SECONDARY_MODEL": ""},
        {"NFCORE_COGNITIVE_AI_SECONDARY_API_KEY": "sk-forbidden"},
        {"NFCORE_COGNITIVE_AI_SECONDARY_GSM_VERSION": "latest"},
    ],
)
def test_invalid_configuration_fails_closed(changed: dict[str, str]) -> None:
    cfg = {
        "NFCORE_COGNITIVE_AI_SECRET_MODE": "pinned-gsm-openai-v1",
        "NFCORE_ENVIRONMENT": "production",
        "NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER": "openai",
        "NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL": "https://api.openai.com/v1",
        "NFCORE_COGNITIVE_AI_SECONDARY_MODEL": "gpt-synthetic",
        "NFCORE_GSM_PROJECT_ID": "fm-nfcore-prod",
        "NFCORE_GSM_PROJECT_NUMBER": NUMBER,
        "NFCORE_COGNITIVE_AI_SECONDARY_GSM_VERSION": "1",
    }
    cfg.update(changed)
    with pytest.raises(RuntimeConfigurationError):
        build_production_openai_key_readers(cfg, access=Access())


def test_gemini_existing_environment_key_compatible_with_gsm_openai() -> None:
    from kordena_fiscal.cognitive.adapters.openai_compatible import (
        TierRoutedAdvisoryClient,
        build_model_from_environ,
    )

    env = {
        "NFCORE_COGNITIVE_AI_PRIMARY_PROVIDER": "gemini",
        "NFCORE_COGNITIVE_AI_PRIMARY_BASE_URL": "https://gemini.example.test/v1",
        "NFCORE_COGNITIVE_AI_PRIMARY_MODEL": "gemini-test",
        "NFCORE_COGNITIVE_AI_PRIMARY_API_KEY": "synthetic-gemini-test",
        "NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER": "openai",
        "NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL": "https://api.openai.com/v1",
        "NFCORE_COGNITIVE_AI_SECONDARY_MODEL": "gpt-synthetic",
        "NFCORE_COGNITIVE_AI_PRIMARY_TIER": "FAST_ECONOMIC",
        "NFCORE_COGNITIVE_AI_SECONDARY_TIER": "DEEP_REASONING",
        "NFCORE_COGNITIVE_AI_TIER_ROUTING_ENABLED": "true",
    }
    model = build_model_from_environ(
        env, key_readers={"NFCORE_COGNITIVE_AI_SECONDARY_API_KEY": lambda: "sk-proj-synthetic"}
    )
    assert isinstance(model, TierRoutedAdvisoryClient)
    env["NFCORE_COGNITIVE_AI_SECONDARY_API_KEY"] = "collision"
    assert (
        build_model_from_environ(
            env, key_readers={"NFCORE_COGNITIVE_AI_SECONDARY_API_KEY": lambda: "synthetic"}
        )
        is None
    )
