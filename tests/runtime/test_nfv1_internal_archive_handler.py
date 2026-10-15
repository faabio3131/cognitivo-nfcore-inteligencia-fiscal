"""Internal fiscal archive query over the existing durable canonical store."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from kordena_fiscal.archive import (
    FiscalArchiveEntry,
    FiscalArchiveKind,
    RetentionPolicyMetadata,
)
from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment, FiscalValidationError
from kordena_fiscal.persistence import SqliteFiscalDatabase
from kordena_fiscal.runtime.internal_archive_handler import (
    build_archive_reference_handler,
)


def _scope(unit: str) -> ExecutionScope:
    return ExecutionScope(
        tenant_id="tenant-dev",
        unit_id=unit,
        environment=FiscalEnvironment.HOMOLOGATION,
        correlation_id="corr-archive-read",
    )


def test_archive_reference_handler_reads_only_authorized_unit_records(tmp_path: Path) -> None:
    database = SqliteFiscalDatabase(tmp_path / "archive-query.sqlite3")
    database.initialize()
    now = datetime(2026, 10, 15, tzinfo=UTC)
    with database() as uow:
        uow.archive.append(
            FiscalArchiveEntry.build(
                scope=_scope("unit-a"),
                document_reference="document-1",
                kind=FiscalArchiveKind.AUTHORIZED_XML,
                content=b"<synthetic-test-only />",
                media_type="application/xml",
                archived_at=now,
                retention=RetentionPolicyMetadata(
                    policy_id="internal-test",
                    policy_version=1,
                    retain_until=now + timedelta(days=10),
                ),
            )
        )
        uow.commit()

    handler = build_archive_reference_handler(database)
    own = handler(_scope("unit-a"), {"document_reference": "document-1"}, None)
    other = handler(_scope("unit-b"), {"document_reference": "document-1"}, None)
    assert own["found"] is True
    assert len(own["entries"]) == 1
    assert own["entries"][0]["document_reference"] == "document-1"
    assert "content" not in own["entries"][0]
    assert other == {
        "document_reference": "document-1",
        "found": False,
        "entries": [],
    }


def test_archive_reference_handler_fails_closed_on_invalid_reference(tmp_path: Path) -> None:
    database = SqliteFiscalDatabase(tmp_path / "archive-query-invalid.sqlite3")
    database.initialize()
    handler = build_archive_reference_handler(database)
    with pytest.raises(FiscalValidationError):
        handler(_scope("unit-a"), {"document_reference": ""}, None)
