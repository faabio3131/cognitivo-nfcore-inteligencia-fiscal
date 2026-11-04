"""Offline normative sentinel: checksum is not proof of official authenticity.

Delegates integrity to the canonical RTC evidence verifier. No HTTP polling,
automatic baseline promotion or approval of fiscal rules is performed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .rtc import RegulatoryArtifactPin
from .rtc_evidence import verify_regulatory_artifact_bytes


@dataclass(frozen=True, slots=True)
class NormativeIntegrityAssessment:
    sha256: str
    integrity_verified: bool
    official_provenance_verified: bool = False
    fiscal_production_approved: bool = False


def assess_pinned_normative_bytes(
    artifact: RegulatoryArtifactPin,
    payload: bytes,
) -> NormativeIntegrityAssessment:
    digest = verify_regulatory_artifact_bytes(artifact, payload)
    return NormativeIntegrityAssessment(digest, integrity_verified=True)
