"""Real authority metadata creates alert inputs without reading secrets or cloud keys."""

from datetime import UTC, datetime, timedelta

import pytest

from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment, FiscalValidationError
from kordena_fiscal.runtime.alert_rules import (
    certificate_expiry_signal,
    railway_deployment_signal,
    secret_audit_signal,
)
from kordena_fiscal.security.secrets import SecretAuditEvent
from kordena_fiscal.security.signing import CertificateReference, FiscalSignerKind

NOW = datetime(2026, 10, 16, tzinfo=UTC)


def test_certificate_metadata_is_scoped_and_no_material_used() -> None:
    scope = ExecutionScope(
        host_namespace="fm.nfcore", tenant_id="tenant-one", unit_id="unit-one",
        environment=FiscalEnvironment.HOMOLOGATION, correlation_id="corr-one",
    )
    reference = CertificateReference(
        tenant_id="tenant-one", unit_id="unit-one", reference_id="ref-1",
        signer_kind=FiscalSignerKind.A1_PFX,
        not_before=NOW - timedelta(days=2),
        expires_at=NOW + timedelta(days=5),
    )
    assert certificate_expiry_signal(reference, scope, NOW).certificate_days_remaining == 5
    other_scope = ExecutionScope(
        host_namespace="fm.nfcore", tenant_id="tenant-other", unit_id="unit-one",
        environment=FiscalEnvironment.HOMOLOGATION, correlation_id="corr-two",
    )
    with pytest.raises(FiscalValidationError, match="scope mismatch"):
        certificate_expiry_signal(reference, other_scope, NOW)


def test_secret_audit_and_deployment_status_never_infer_unknown_as_healthy() -> None:
    audit = SecretAuditEvent(
        reference_id="opaque-ref", version=1, tenant_id="tenant-one", unit_id="unit-one",
        purpose="signature", outcome="denied", occurred_at=NOW,
    )
    assert secret_audit_signal(audit).secret_resolution_ok is False
    assert railway_deployment_signal("FAILED").deployment_healthy is False
    assert railway_deployment_signal("SUCCESS").deployment_healthy is True
    assert railway_deployment_signal("DEPLOYING").deployment_healthy is None
    assert railway_deployment_signal("unexpected").deployment_healthy is None
