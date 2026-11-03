"""RTC-01 supplier collection intake regression tests (synthetic inputs only)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.rtc_import_external_collection import (
    ROOT,
    RtcCollectionImportError,
    normalize_rtc_collection,
)

FOLDER = "02_NOTAS_TECNICAS_NFE_NFCE"
DOCUMENT = "NT de Emissão.pdf"
BYTES = b"%PDF-1.7\nSynthetic fixture, not official normative evidence\n"


def _create_collection(
    source: Path, *, content: bytes = BYTES, sha: str | None = None,
    filename: str = DOCUMENT, duplicate: bool = False,
) -> None:
    entry = {
        "pasta": FOLDER,
        "arquivo": filename,
        "sha256": sha or hashlib.sha256(BYTES).hexdigest(),
        "tamanho": len(content),
    }
    manifest = {"arquivos": [entry, dict(entry)] if duplicate else [entry], "nao_obtidos": []}
    mangled_name = (ROOT + FOLDER + "/" + filename).encode("utf-8").decode("cp437")
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr(mangled_name, content)
        zf.writestr(
            ROOT + "09_MANIFESTOS_E_HASHES/manifesto_artefatos.json",
            json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
        )


def test_import_repairs_zip_encoding_without_touching_pdf_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    target = tmp_path / "reconciled.zip"
    _create_collection(source)
    report = normalize_rtc_collection(source, target)
    assert report["verified_documents"] == 1
    assert report["normalized_zip_names"] == 1
    assert report["state"] == "INTEGRITY_VERIFIED_NOT_NORMATIVELY_APPROVED"
    with zipfile.ZipFile(target) as zf:
        assert zf.read(ROOT + FOLDER + "/" + DOCUMENT) == BYTES
        assert (
            ROOT + "09_MANIFESTOS_E_HASHES/relatorio_integridade_importacao.json"
        ) in zf.namelist()


def test_import_rejects_changed_pdf(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    _create_collection(source, content=BYTES + b"tampering")
    with pytest.raises(RtcCollectionImportError, match="SHA-256 or size mismatch"):
        normalize_rtc_collection(source, tmp_path / "output.zip")


def test_import_rejects_mislabeled_html_login(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    data = b"<html><title>Login required</title></html>"
    _create_collection(source, content=data, sha=hashlib.sha256(data).hexdigest())
    with pytest.raises(RtcCollectionImportError, match="SHA-256 or size mismatch"):
        normalize_rtc_collection(source, tmp_path / "output.zip")


def test_import_rejects_duplicate_inventory_record(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    _create_collection(source, duplicate=True)
    with pytest.raises(RtcCollectionImportError, match="Missing or duplicated"):
        normalize_rtc_collection(source, tmp_path / "output.zip")


def test_import_rejects_escape_path(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr(ROOT + "../evil.txt", b"bad")
    with pytest.raises(RtcCollectionImportError, match="Unsafe"):
        normalize_rtc_collection(source, tmp_path / "output.zip")


def test_import_rejects_overwrite_source(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    _create_collection(source)
    with pytest.raises(RtcCollectionImportError, match="replace original"):
        normalize_rtc_collection(source, source)
