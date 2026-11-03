"""Import the UTF-8/CP437-mangled RTC research ZIP into safe offline staging.

Collection integrity is not normative authenticity and never updates RegulatoryBaseline.
Run through the thin scripts/rtc_import_external_collection.py entrypoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = "NFCORE_RTC_OFFICIAL_NORMATIVE_PACKAGE/"
MANIFEST = ROOT + "09_MANIFESTOS_E_HASHES/manifesto_artefatos.json"
REPORT = ROOT + "09_MANIFESTOS_E_HASHES/relatorio_integridade_importacao.json"
MAX_FILE = 75 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024


class RtcCollectionImportError(ValueError):
    """Untrusted evidence bundle is malformed or inconsistent."""


def _decode_member(name: str) -> str:
    try:
        return name.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def _safe_member(name: str) -> None:
    if (
        not name.startswith(ROOT)
        or PurePosixPath(name).is_absolute()
        or "\\" in name
        or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))
    ):
        raise RtcCollectionImportError("Unsafe archive member path")


def _signature(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"PK\x03\x04"):
        return "zip_container"
    head = data[:512].lstrip().lower()
    if b"<html" in head or b"<!doctype html" in head:
        return "html"
    return "other"


def normalize_rtc_collection(source: Path, destination: Path) -> dict[str, object]:
    """Check all supplier SHA/size pairs, normalize paths and preserve bytes.

    No publication dates, official versions, applicability or legal provenance are
    inferred. Returned collection is strictly NOT approved for fiscal execution.
    """
    if not isinstance(source, Path) or not source.is_file():
        raise RtcCollectionImportError("Source ZIP does not exist")
    if source.resolve() == destination.resolve():
        raise RtcCollectionImportError("Output must not replace original collection")
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) > 3000 or sum(i.file_size for i in infos) > MAX_TOTAL:
            raise RtcCollectionImportError("Collection exceeds resource limits")
        by_name: dict[str, zipfile.ZipInfo] = {}
        changed_names: list[dict[str, str]] = []
        for info in infos:
            if info.flag_bits & 1:
                raise RtcCollectionImportError("Encrypted file forbidden")
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise RtcCollectionImportError("Symlinks forbidden")
            if info.file_size > MAX_FILE:
                raise RtcCollectionImportError("Oversized document")
            name = _decode_member(info.filename)
            _safe_member(name)
            if name in by_name:
                raise RtcCollectionImportError("Duplicate normalized ZIP path")
            by_name[name] = info
            if name != info.filename:
                changed_names.append({"old": info.filename, "new": name})
        if MANIFEST not in by_name:
            raise RtcCollectionImportError("Supplier manifest missing")
        raw_manifest = archive.read(by_name[MANIFEST])
        if len(raw_manifest) > 5 * 1024 * 1024:
            raise RtcCollectionImportError("Supplier manifest too large")
        try:
            manifest = json.loads(raw_manifest)
        except (ValueError, UnicodeError) as exc:
            raise RtcCollectionImportError("Supplier manifest is not valid JSON") from exc
        records = manifest.get("arquivos") if isinstance(manifest, dict) else None
        if not isinstance(records, list) or not records:
            raise RtcCollectionImportError("Supplier manifest has no documents")
        examined: set[str] = set()
        checked: list[dict[str, object]] = []
        for entry in records:
            if not isinstance(entry, dict):
                raise RtcCollectionImportError("Invalid document manifest entry")
            folder, filename = entry.get("pasta"), entry.get("arquivo")
            if not isinstance(folder, str) or not isinstance(filename, str):
                raise RtcCollectionImportError("Supplier filename missing")
            name = ROOT + folder + "/" + filename
            _safe_member(name)
            info = by_name.get(name)
            if info is None or name in examined:
                raise RtcCollectionImportError("Missing or duplicated document")
            examined.add(name)
            payload = archive.read(info)
            digest = hashlib.sha256(payload).hexdigest()
            if digest != entry.get("sha256") or len(payload) != entry.get("tamanho"):
                raise RtcCollectionImportError("Document SHA-256 or size mismatch")
            suffix = PurePosixPath(filename).suffix.lower()
            signature = _signature(payload)
            if (
                (suffix == ".pdf" and signature != "pdf")
                or (suffix in (".zip", ".xlsx") and signature != "zip_container")
                or (suffix == ".html" and signature != "html")
            ):
                raise RtcCollectionImportError("Document signature mismatch")
            checked.append({
                "relative_path": folder + "/" + filename,
                "sha256": digest,
                "bytes": len(payload),
                "signature": signature,
                "status": "INTEGRITY_ONLY_SOURCE_AND_EFFECTIVE_DATE_UNVERIFIED",
            })
        uncollected = manifest.get("nao_obtidos")
        report: dict[str, object] = {
            "schema_version": 1,
            "state": "INTEGRITY_VERIFIED_NOT_NORMATIVELY_APPROVED",
            "verified_documents": len(checked),
            "normalized_zip_names": len(changed_names),
            "name_reconciliation": changed_names,
            "supplier_uncollected_count": (
                len(uncollected) if isinstance(uncollected, list) else None
            ),
            "documents": checked,
            "limitations": [
                "SHA-256 was compared to the supplier manifest, not to an independent source",
                "Portal date is not a legally verified publication or effective date",
                "No changes to RegulatoryBaseline, rates, tax rules, XML or production",
            ],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=4, allowZip64=True) as output:
            for name, info in by_name.items():
                output.writestr(name, b"" if info.is_dir() else archive.read(info))
            output.writestr(
                REPORT, json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
            )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("destination_zip", type=Path)
    args = parser.parse_args()
    report = normalize_rtc_collection(args.source_zip, args.destination_zip)
    print(json.dumps({
        "status": report["state"],
        "verified": report["verified_documents"],
        "names_fixed": report["normalized_zip_names"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
