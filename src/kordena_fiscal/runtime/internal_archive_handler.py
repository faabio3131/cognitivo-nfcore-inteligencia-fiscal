"""Canonical read-only archive reference fiscal handler.

Uses the existing durable FiscalArchiveStore and never fabricates provider results.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kordena_fiscal.domain import ExecutionScope, FiscalValidationError
from kordena_fiscal.persistence.ports import FiscalUnitOfWorkFactory


def build_archive_reference_handler(
    unit_of_work_factory: FiscalUnitOfWorkFactory,
):
    """Adapt the existing archive store to queryArchiveReference without a new API."""

    def query_archive_reference(
        scope: ExecutionScope,
        payload: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        del idempotency_key  # read-only operation
        reference = payload.get("document_reference")
        if not isinstance(reference, str) or not reference.strip():
            raise FiscalValidationError("document_reference is required")
        reference = reference.strip()
        if len(reference) > 256:
            raise FiscalValidationError("document_reference exceeds max length 256")
        with unit_of_work_factory() as uow:
            rows = uow.archive.list_for_document(scope, reference)
        return {
            "document_reference": reference,
            "found": bool(rows),
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "document_reference": entry.document_reference,
                    "kind": entry.kind.value,
                    "content_sha256": entry.content_sha256,
                    "media_type": entry.media_type,
                    "archived_at": entry.archived_at.isoformat(),
                }
                for entry in rows
            ],
        }

    return query_archive_reference
