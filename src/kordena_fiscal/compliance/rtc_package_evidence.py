"""Offline integrity gate for an untrusted, staged RTC normative download package.

This gate only checks internal metadata and byte integrity against the supplied
manifest. It NEVER certifies official provenance, approves rates or alters the
canonical RegulatoryBaseline. The manifest itself requires independent review.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .rtc import RegulatoryArtifactKind, RegulatoryArtifactPin, RegulatoryBaselineError
from .rtc_evidence import verify_regulatory_artifact_bytes

_MAX_ARTIFACT_SIZE = 50 * 1024 * 1024


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RegulatoryBaselineError("RTC package manifest duplicate JSON key")
        result[key] = value
    return result


def _required_string(entry: dict[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegulatoryBaselineError(f"RTC package missing string {key}")
    return value


def _package_path(root: Path, relative: str) -> Path:
    if "\\" in relative:
        raise RegulatoryBaselineError("RTC package file path must use POSIX separators")
    parts = PurePosixPath(relative)
    if (
        parts.is_absolute()
        or not parts.parts
        or any(part in (".", "..") for part in relative.split("/"))
        or any(not part for part in relative.split("/"))
    ):
        raise RegulatoryBaselineError("RTC package file path is unsafe")
    target = root.joinpath(*parts.parts)
    # Symlink denial also covers links to targets inside the staging root.
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise RegulatoryBaselineError("RTC package symlink is forbidden")
    if not target.resolve().is_relative_to(root.resolve()) or not target.is_file():
        raise RegulatoryBaselineError("RTC package file missing or outside staging root")
    return target


def verify_staged_rtc_package(
    package_root: Path, manifest_relative_path: str
) -> dict[str, str]:
    """Verify staged official-source candidates without promoting any fiscal authority.

    Manifest schema: {"schema_version": 1, "artifacts": [
      {"artifact_id", "kind", "version", "published_on", "source_reference",
       "checksum_sha256", "relative_path", optional "effective_from"}]}.
    Paths are relative to package_root; returns artifact IDs mapped to digests.
    Duplicate artifact IDs are denied even when versions differ: one manifest
    must describe an unambiguous pin set, not competing legal versions.
    """
    if not isinstance(package_root, Path) or not package_root.is_dir():
        raise RegulatoryBaselineError("RTC package root directory is required")
    manifest_path = _package_path(package_root, manifest_relative_path)
    if manifest_path.stat().st_size > 1024 * 1024:
        raise RegulatoryBaselineError("RTC package manifest exceeds size limit")
    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs
        )
    except (ValueError, UnicodeError) as exc:
        raise RegulatoryBaselineError("RTC package manifest must be valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise RegulatoryBaselineError("RTC package requires schema_version 1")
    records = manifest.get("artifacts")
    if not isinstance(records, list) or not records or len(records) > 512:
        raise RegulatoryBaselineError("RTC package requires 1-512 artifact entries")
    digests: dict[str, str] = {}
    seen_paths: set[str] = set()
    for raw in records:
        if not isinstance(raw, dict):
            raise RegulatoryBaselineError("RTC package artifact must be an object")
        artifact_id = _required_string(raw, "artifact_id")
        relative = _required_string(raw, "relative_path")
        reference = _required_string(raw, "source_reference")
        url = urlsplit(reference)
        if (
            url.scheme != "https" or not url.hostname
            or url.username is not None or url.password is not None
        ):
            raise RegulatoryBaselineError("RTC package source must be public HTTPS")
        if artifact_id in digests or relative in seen_paths:
            raise RegulatoryBaselineError("RTC package duplicate artifact or path")
        try:
            effective = raw.get("effective_from")
            if effective is not None and not isinstance(effective, str):
                raise ValueError("effective_from is not a string")
            pin = RegulatoryArtifactPin(
                artifact_id=artifact_id,
                kind=RegulatoryArtifactKind(_required_string(raw, "kind")),
                version=_required_string(raw, "version"),
                published_on=date.fromisoformat(_required_string(raw, "published_on")),
                effective_from=date.fromisoformat(effective) if effective else None,
                source_reference=reference,
                checksum_sha256=_required_string(raw, "checksum_sha256"),
            )
        except (TypeError, ValueError) as exc:
            raise RegulatoryBaselineError("RTC package artifact metadata invalid") from exc
        target = _package_path(package_root, relative)
        if target.stat().st_size > _MAX_ARTIFACT_SIZE:
            raise RegulatoryBaselineError("RTC package artifact exceeds size limit")
        digests[artifact_id] = verify_regulatory_artifact_bytes(pin, target.read_bytes())
        seen_paths.add(relative)
    return digests
