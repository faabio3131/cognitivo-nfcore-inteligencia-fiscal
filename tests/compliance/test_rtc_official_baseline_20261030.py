"""Regression contract for the RTC regulatory reference baseline.

Metadata only: this test does not certify tax rates, XML layouts or issuance.
"""

from datetime import date, datetime
from json import loads
from pathlib import Path

from kordena_fiscal.compliance import (
    RegulatoryArtifactKind,
    RegulatoryArtifactPin,
    RegulatoryBaseline,
)

_MANIFEST = Path(__file__).resolve().parents[2] / "config/rtc/official-baseline-2026-10-30.json"


def _baseline() -> RegulatoryBaseline:
    manifest = loads(_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["status"] == "REFERENCE_ONLY_NOT_PRODUCTION_APPROVED"
    assert manifest["source_policy"] == "official_published_sources_only"
    assert len(manifest["artifacts"]) >= 3
    captured_at = datetime.fromisoformat(manifest["captured_at"].replace("Z", "+00:00"))
    artifacts = tuple(
        RegulatoryArtifactPin(
            artifact_id=item["artifact_id"],
            kind=RegulatoryArtifactKind(item["kind"]),
            version=item["version"],
            published_on=date.fromisoformat(item["published_on"]),
            source_reference=item["source_reference"],
        )
        for item in manifest["artifacts"]
    )
    assert all(item.published_on <= captured_at.date() for item in artifacts)
    assert all(item.source_reference.startswith("https://") for item in artifacts)
    return RegulatoryBaseline(
        baseline_id=manifest["baseline_id"],
        version=manifest["version"],
        captured_at=captured_at,
        artifacts=artifacts,
    )


def test_rtc_official_reference_manifest_uses_existing_compliance_authority() -> None:
    baseline = _baseline()
    assert baseline.artifact("NT-2025.002").version == "1.53"
    assert baseline.version == 5
    assert baseline.artifact("NT-2025.002").published_on == date(2026, 10, 30)
    assert baseline.artifact("NT-2026.005").version == "1.00"
    assert baseline.artifact("NT-2026.005").published_on == date(2026, 10, 30)
    assert baseline.artifact("IT-2025.002").version == "1.71"
    assert baseline.artifact("IBSCBS-CCLASSTRIB").version == "IT-2025.002-v1.71"
    assert baseline.artifact("IBSCBS-CCREDPRES").version == "IT-2025.002-v1.70"
    assert baseline.artifact("LC-214-2025").version == "214/2025"
    assert baseline.artifact("LC-227-2026").version == "227/2026"


def test_rtc_reference_baseline_never_implicitly_approves_fiscal_production() -> None:
    manifest = loads(_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] != "PRODUCTION_APPROVED"
    assert "provider homologation" in manifest["excluded_until_verified"]
    assert "production rates and fiscal formulas" in manifest["excluded_until_verified"]


def test_new_simplified_rtc_note_is_reference_only_not_calculation_authority() -> None:
    manifest = loads(_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["status"] == "REFERENCE_ONLY_NOT_PRODUCTION_APPROVED"
    note = next(
        item for item in manifest["artifacts"] if item["artifact_id"] == "NT-2026.005"
    )
    table = next(
        item for item in manifest["artifacts"] if item["artifact_id"] == "IBSCBS-CCLASSTRIB"
    )
    assert note["version"] == "1.00"
    assert table["version"] == "IT-2025.002-v1.71"
    assert "checksum_sha256" not in note
    assert "checksum_sha256" not in table
    assert all(item["kind"] != "rate_table" for item in manifest["artifacts"])
    assert any("NT 2026.005 SN official PDF/XSD" in v for v in manifest["excluded_until_verified"])


def test_rtc_v5_retains_production_blockers_and_official_document_pin() -> None:
    manifest = loads(_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["version"] == 5
    assert manifest["status"] == "REFERENCE_ONLY_NOT_PRODUCTION_APPROVED"
    assert "provider homologation" in manifest["excluded_until_verified"]
    assert "production rates and fiscal formulas" in manifest["excluded_until_verified"]
    refs = {item["artifact_id"]: item for item in manifest["artifacts"]}
    assert refs["IT-2025.002"]["version"] == "1.71"
    assert refs["IT-2025.002"]["checksum_sha256"] == (
        "96fb4d462e5973096534e7c3cfef77b2ca1054bff5a4237a2c2a74726e162da1"
    )
    assert refs["NT-2026.008"]["version"] == "1.01"
    assert refs["IT-2023.002"]["version"] == "2.10"
    assert "governance" not in manifest
