"""RTC-01 offline staging tests: synthetic bytes, never official homologation."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from kordena_fiscal.compliance.rtc import RegulatoryBaselineError
from kordena_fiscal.compliance.rtc_package_evidence import verify_staged_rtc_package

_DATA = b"synthetic test-only normative bytes"


def _stage(tmp_path: Path, *, payload: bytes = _DATA) -> tuple[Path, dict[str, object]]:
    (tmp_path / "01_LEGISLACAO").mkdir()
    (tmp_path / "01_LEGISLACAO" / "lc-test.pdf").write_bytes(payload)
    entry = {
        "artifact_id": "LC-TEST",
        "kind": "other",
        "version": "synthetic-v1",
        "published_on": "2026-10-30",
        "source_reference": "https://www.gov.br/receitafederal/",
        "checksum_sha256": sha256(_DATA).hexdigest(),
        "relative_path": "01_LEGISLACAO/lc-test.pdf",
    }
    manifest: dict[str, object] = {"schema_version": 1, "artifacts": [entry]}
    _write_manifest(tmp_path, manifest)
    return tmp_path, manifest


def _write_manifest(root: Path, manifest: dict[str, object]) -> None:
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _verify(root: Path) -> dict[str, str]:
    return verify_staged_rtc_package(root, "manifest.json")


def test_staged_package_validates_synthetic_bytes_without_approval(tmp_path: Path) -> None:
    root, _ = _stage(tmp_path)
    assert _verify(root) == {"LC-TEST": sha256(_DATA).hexdigest()}


def test_staged_package_rejects_modified_bytes(tmp_path: Path) -> None:
    root, _ = _stage(tmp_path, payload=b"tampered")
    with pytest.raises(RegulatoryBaselineError, match="digest mismatch"):
        _verify(root)


@pytest.mark.parametrize("relative", [
    "../outside.pdf", "/etc/passwd", "01_LEGISLACAO/../../outside.pdf",
    "01_LEGISLACAO//lc-test.pdf", r"01_LEGISLACAO\\lc-test.pdf",
])
def test_staged_package_rejects_unsafe_paths(tmp_path: Path, relative: str) -> None:
    root, manifest = _stage(tmp_path)
    records = manifest["artifacts"]
    assert isinstance(records, list)
    records[0]["relative_path"] = relative
    _write_manifest(root, manifest)
    with pytest.raises(RegulatoryBaselineError):
        _verify(root)


def test_staged_package_rejects_symlink(tmp_path: Path) -> None:
    root, _ = _stage(tmp_path)
    target = root / "01_LEGISLACAO" / "lc-test.pdf"
    target.unlink()
    target.symlink_to(root / "manifest.json")
    with pytest.raises(RegulatoryBaselineError, match="symlink"):
        _verify(root)


def test_staged_package_rejects_duplicate_artifact(tmp_path: Path) -> None:
    root, manifest = _stage(tmp_path)
    records = manifest["artifacts"]
    assert isinstance(records, list)
    records.append(dict(records[0]))
    _write_manifest(root, manifest)
    with pytest.raises(RegulatoryBaselineError, match="duplicate"):
        _verify(root)


def test_staged_package_rejects_manifest_with_duplicate_json_key(tmp_path: Path) -> None:
    root, _ = _stage(tmp_path)
    (root / "manifest.json").write_text(
        '{"schema_version":1,"schema_version":1,"artifacts":[]}', encoding="utf-8"
    )
    with pytest.raises(RegulatoryBaselineError, match="duplicate JSON"):
        _verify(root)


def test_staged_package_rejects_unverified_source(tmp_path: Path) -> None:
    root, manifest = _stage(tmp_path)
    records = manifest["artifacts"]
    assert isinstance(records, list)
    records[0]["source_reference"] = "http://example.org/test"
    _write_manifest(root, manifest)
    with pytest.raises(RegulatoryBaselineError, match="public HTTPS"):
        _verify(root)


def test_staged_package_rejects_missing_checksum(tmp_path: Path) -> None:
    root, manifest = _stage(tmp_path)
    records = manifest["artifacts"]
    assert isinstance(records, list)
    records[0].pop("checksum_sha256")
    _write_manifest(root, manifest)
    with pytest.raises(RegulatoryBaselineError, match="checksum_sha256"):
        _verify(root)


def test_staged_package_rejects_missing_file(tmp_path: Path) -> None:
    root, _ = _stage(tmp_path)
    (root / "01_LEGISLACAO" / "lc-test.pdf").unlink()
    with pytest.raises(RegulatoryBaselineError, match="missing"):
        _verify(root)
