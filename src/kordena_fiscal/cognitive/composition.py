"""Composition of the cognitive advisory route for the runtime. Disabled unless explicitly on.

With no central FM model configured the route serves only the deterministic baseline
(``aiEnabled: false``): useful, free of AI cost and requiring no credential. Connecting the
central model is a separate, owner-authorized configuration step (Vault Secret Reference).
"""

from __future__ import annotations

from collections.abc import Mapping

from fastapi import APIRouter

from kordena_fiscal.security.human_identity import HumanIdentityService

from .api import create_cognitive_router
from .knowledge.official import OfficialTablesError, cached_official_catalog
from .portal_evidence import PortalSurfaceEvidenceProvider, SurfaceReader
from .registry import default_baselines
from .service import CognitiveAdviceService

ENABLE_FLAG = "NFCORE_COGNITIVE_ENABLED"


def build_cognitive_router(
    identity: HumanIdentityService | None,
    portal_executor: SurfaceReader | None,
    environ: Mapping[str, str],
) -> APIRouter | None:
    if environ.get(ENABLE_FLAG, "").strip().lower() != "true":
        return None
    if identity is None or portal_executor is None:
        return None
    try:
        catalog = cached_official_catalog()
    except OfficialTablesError:
        # Fail-open: without the official tables the advice says "não verificado".
        catalog = None
    service = CognitiveAdviceService(
        baselines=default_baselines(classification_catalog=catalog), model=None
    )
    return create_cognitive_router(
        identity,
        service,
        PortalSurfaceEvidenceProvider(portal_executor),
        ai_enabled=False,
    )
