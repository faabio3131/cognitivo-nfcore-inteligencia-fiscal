"""P05: internal Web journey through the canonical authenticated fiscal path.

The provider response is intentionally synthetic and can never prove fiscal homologation.
"""

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.control_plane import FiscalOrganization, FiscalUnitRegistration
from kordena_fiscal.domain import Cnpj, ElectronicInvoiceModel, FiscalEnvironment
from kordena_fiscal.persistence import SqliteFiscalDatabase
from kordena_fiscal.runtime.config import RuntimeSettings
from kordena_fiscal.runtime.development_fiscal_ingress import development_fiscal_ingress
from kordena_fiscal.runtime.fiscal_runtime import (
    CanonicalFiscalOperationPath,
    CanonicalPortalOperationExecutor,
)
from kordena_fiscal.security.human_identity import (
    HumanAccount,
    HumanIdentityService,
    InMemoryHumanAccountRepository,
    InMemoryWebSessionRepository,
    PortalRole,
    ScryptPasswordHasher,
)
from kordena_fiscal.web import create_app
from kordena_fiscal.web.human_auth import CSRF_COOKIE, CSRF_HEADER
from kordena_fiscal.web.portal_runtime import DurableHumanPortalExecutor
from kordena_fiscal.xml import AccessKeyInput, build_access_key


def _access_key() -> str:
    return build_access_key(
        AccessKeyInput(
            state_ibge_code="35",
            issued_at=datetime(2026, 9, 11, tzinfo=UTC),
            issuer_cnpj=Cnpj("12.345.678/0001-95"),
            model=ElectronicInvoiceModel.NFCE,
            series=3,
            invoice_number=10,
            emission_type=1,
            numeric_code=12345678,
        )
    ).value


def test_signed_in_portal_local_query_respects_tenant_unit_and_csrf(tmp_path: Path) -> None:
    database = SqliteFiscalDatabase(tmp_path / "fiscal-local-query.sqlite3")
    database.initialize()
    with database() as uow:
        uow.control_plane.add_organization(
            FiscalOrganization(tenant_id="tenant-a", legal_name="Example Synthetic Ltda")
        )
        for unit_id in ("unit-a", "unit-b"):
            uow.control_plane.add_unit(
                FiscalUnitRegistration(
                    tenant_id="tenant-a",
                    unit_id=unit_id,
                    display_name=unit_id,
                    enabled_environments=frozenset({FiscalEnvironment.HOMOLOGATION}),
                )
            )
        uow.commit()

    settings = RuntimeSettings.from_mapping({"NFCORE_ENVIRONMENT": "test"})
    handlers = development_fiscal_ingress(
        settings, {"NFCORE_DEV_FISCAL_QUERY_MODE": "synthetic_pending"}
    )
    path = CanonicalFiscalOperationPath(FiscalApplicationService(database), handlers=handlers)
    portal_executor = DurableHumanPortalExecutor(
        database,
        operation_executor=CanonicalPortalOperationExecutor(
            unit_of_work_factory=database, path=path
        ),
    )
    password = "synthetic-local-only-portal-password"
    hasher = ScryptPasswordHasher()
    identity = HumanIdentityService(
        accounts=InMemoryHumanAccountRepository(
            (
                HumanAccount(
                    account_id="operator-local",
                    email="local-operator@example.com",
                    password_hash=hasher.hash(password),
                    tenant_id="tenant-a",
                    role=PortalRole.OPERATOR,
                    unit_ids=frozenset({"unit-a"}),
                ),
            )
        ),
        sessions=InMemoryWebSessionRepository(),
        password_hasher=hasher,
    )
    client = TestClient(
        create_app(human_identity=identity, portal_executor=portal_executor),
        base_url="https://nfcore.test",
    )
    route = "/v1/portal/operations/queryFiscalDocument"
    payload = {"unit_id": "unit-a", "access_key": _access_key()}
    assert client.post(route, json=payload).status_code == 401

    response = client.post(
        "/v1/auth/login", json={"email": "local-operator@example.com", "password": password}
    )
    assert response.status_code == 200
    csrf = client.cookies.get(CSRF_COOKIE)
    assert csrf
    assert client.post(route, json=payload).status_code == 403

    forbidden = client.post(
        route, json={**payload, "unit_id": "unit-b"}, headers={CSRF_HEADER: csrf}
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "PORTAL_FORBIDDEN"

    successful = client.post(route, json=payload, headers={CSRF_HEADER: csrf})
    assert successful.status_code == 200
    assert successful.json()["status"] == "pending"
    assert successful.json()["simulation"] is True
    assert successful.json()["official_fiscal_evidence"] is False

    assert "issueFiscalDocument" not in handlers
