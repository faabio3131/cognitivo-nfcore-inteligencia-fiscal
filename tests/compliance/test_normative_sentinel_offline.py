from __future__ import annotations

import hashlib
from datetime import date

import pytest

from kordena_fiscal.compliance.normative_sentinel import assess_pinned_normative_bytes
from kordena_fiscal.compliance.rtc import (
    RegulatoryArtifactKind,
    RegulatoryArtifactPin,
    RegulatoryBaselineError,
)


def _pin(payload: bytes) -> RegulatoryArtifactPin:
    return RegulatoryArtifactPin(
        artifact_id="SYNTHETIC-TEST",
        kind=RegulatoryArtifactKind.CLASSIFICATION_TABLE,
        version="test-only",
        published_on=date(2026, 11, 3),
        source_reference="https://example.org/fixture",
        checksum_sha256=hashlib.sha256(payload).hexdigest(),
    )


def test_hash_match_is_integrity_only_not_authenticity() -> None:
    result = assess_pinned_normative_bytes(_pin(b"synthetic"), b"synthetic")
    assert result.integrity_verified
    assert not result.official_provenance_verified
    assert not result.fiscal_production_approved


def test_digest_mismatch_fails_closed() -> None:
    with pytest.raises(RegulatoryBaselineError):
        assess_pinned_normative_bytes(_pin(b"synthetic"), b"tampered")


def test_missing_pin_denied() -> None:
    with pytest.raises(RegulatoryBaselineError):
        assess_pinned_normative_bytes(None, b"synthetic")  # type: ignore[arg-type]
