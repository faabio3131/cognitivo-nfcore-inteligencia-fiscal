"""P05 closure: Postgres-backed commercial Web journey and canonical Worker in one DB.

Only synthetic, signed, in-process ingress. No external fiscal/payment calls or staging data.
The existing Postgres fixture owns migrations and an isolated disposable schema in CI.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from test_p03_t01_acquisition import acquisition
from test_p03_t01_acquisition import settings as postgres_settings
from test_p03_t02_trial import BODY, Delivery
from test_p03_t02_trial import options as trial_options
from test_p03_t02_trial import post as post_trial
from test_p03_t02_trial import publish as publish_trial
from test_p03_t03_command import begin as begin_command
from test_p03_t03_command import post as post_command
from test_p03_t03_command import setup as setup_command

from kordena_fiscal.contingency import (
    FiscalDispatchResult,
    FiscalDispatchStatus,
    FiscalOutboxService,
    FiscalOutboxStatus,
)
from kordena_fiscal.control_plane import FiscalOrganization, FiscalUnitRegistration
from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment
from kordena_fiscal.runtime import api as runtime_api
from kordena_fiscal.runtime.worker_composition import build_production_worker_runtime
from kordena_fiscal.web.human_auth import CSRF_COOKIE, CSRF_HEADER

settings = postgres_settings


class _LocalOnlyHandler:
    def dispatch(self, entry: object) -> FiscalDispatchResult:
        del entry
        return FiscalDispatchResult(
            status=FiscalDispatchStatus.SUCCEEDED,
            reference="internal-test-only",
        )


def _activate_and_login(client: TestClient, *, email: str, reset_token: str) -> None:
    password = "Synthetic-Internal-Portal-2026"
    completed = client.post(
        "/v1/auth/password-reset/complete",
        json={"reset_token": reset_token, "new_password": password},
    )
    assert completed.status_code == 204
    login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    bootstrap = client.get("/v1/portal/bootstrap")
    assert bootstrap.status_code == 200


def test_postgres_trial_portal_and_worker_share_canonical_state(settings) -> None:
    delivery = Delivery()
    app = runtime_api.create_runtime_app(settings, **trial_options(delivery))
    publish_trial(app)
    with TestClient(app, base_url="https://testserver") as client:
        profile = client.get("/runtime/profile").json()
        assert profile["commercial_trial_configured"] is True
        assert profile["portal_executor_configured"] is True
        assert profile["fiscal_runtime_external_execution_ready"] is False

        created = post_trial(client)
        assert created.status_code == 201
        assert post_trial(client).status_code == 200
        # Trial replay may legitimately resend a fresh activation link. It must
        # not create a second purchase, subscription, tenant or owner.
        assert len(delivery.calls) == 2
        assert all(email == BODY["buyer_email"] for email, _ in delivery.calls)

        _activate_and_login(
            client,
            email=BODY["buyer_email"],
            reset_token=delivery.calls[-1][1].reset_token,
        )
        database = app.state.nfcore_runtime.database
        with database.connection() as connection:
            counts = {
                name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in (
                    "fm_commercial_purchases",
                    "fm_commercial_subscriptions",
                    "fm_human_accounts",
                    "fm_control_plane_organizations",
                )
            }
            tenant = connection.execute(
                "SELECT tenant_id FROM fm_control_plane_organizations LIMIT 1"
            ).fetchone()[0]
        assert all(value == 1 for value in counts.values())

        scope = ExecutionScope(
            host_namespace="nfcore",
            tenant_id=tenant,
            unit_id="local-only-worker-unit",
            environment=FiscalEnvironment.HOMOLOGATION,
            correlation_id="p05-test-worker",
        )
        with database.unit_of_work() as uow:
            entry = (
                FiscalOutboxService(uow.outbox)
                .enqueue(
                    scope=scope,
                    operation="deliver_webhook",
                    deduplication_key="p05-internal-worker-1",
                    payload=b'{"synthetic":true}',
                    created_at=datetime.now(UTC),
                )
                .entry
            )
            uow.commit()
        worker = build_production_worker_runtime(
            uow_factory=database,
            handlers={"deliver_webhook": _LocalOnlyHandler()},
            environment="test",
        )
        cycle = worker.runtime.run_cycle()
        assert cycle.claimed == cycle.succeeded == 1
        with database.unit_of_work() as uow:
            durable = uow.outbox.get(entry.entry_id)
        assert durable is not None
        assert durable.status is FiscalOutboxStatus.SUCCEEDED
        assert worker.runtime.run_cycle().claimed == 0

        # Fiscal and commercial provider activities are still guarded.
        assert client.get("/runtime/profile").json()["fiscal_production_activated"] is False


def test_postgres_signed_command_claim_activation_login_and_replay(settings) -> None:
    app, _, _, delivery = setup_command(settings)
    with TestClient(app, base_url="https://testserver") as client:
        received = begin_command(client)
        accepted = post_command(client, received)
        assert accepted.status_code == 202
        assert post_command(client, received).status_code == 200
        purchase_id = accepted.json()["purchase_id"]

        claim_service = app.state.nfcore_runtime_composition.commercial_claim
        now = datetime.now(UTC)
        claim = claim_service.issue(purchase_id=purchase_id, now=now)
        claim_service.complete(
            claim_token=claim.claim_token,
            legal_name=json.loads(acquisition.acquisition_body())["legal_name"],
            now=now,
        )
        activated = {
            **received,
            "event_id": "evt-p05-internal-activation",
            "event_type": "subscription_activated",
            "occurred_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        }
        assert post_command(client, activated).status_code == 202
        assert post_command(client, activated).status_code == 200
        assert len(delivery.calls) == 1

        _activate_and_login(
            client,
            email=delivery.calls[0][0],
            reset_token=delivery.calls[0][1].reset_token,
        )
        with app.state.nfcore_runtime.database.connection() as connection:
            assert (
                connection.execute("SELECT COUNT(*) FROM fm_commercial_purchases").fetchone()[0]
                == 1
            )
            assert connection.execute("SELECT COUNT(*) FROM fm_human_accounts").fetchone()[0] == 1
            assert (
                connection.execute("SELECT COUNT(*) FROM fm_commercial_subscriptions").fetchone()[0]
                == 1
            )


def test_p05_t03_postgres_trial_activation_and_session_revocation(settings) -> None:
    """Internal smoke: recovery-driven activation and session lifecycle on the real DB."""
    delivery = Delivery()
    app = runtime_api.create_runtime_app(settings, **trial_options(delivery))
    publish_trial(app)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.get("/v1/auth/me").status_code == 401
        assert client.get("/v1/portal/bootstrap").status_code == 401

        assert post_trial(client).status_code == 201
        assert len(delivery.calls) == 1
        _activate_and_login(
            client,
            email=BODY["buyer_email"],
            reset_token=delivery.calls[0][1].reset_token,
        )

        current = client.get("/v1/auth/me")
        assert current.status_code == 200
        assert current.json()["account"]["email"] == BODY["buyer_email"]
        assert current.json()["account"]["tenant_id"]
        csrf = client.cookies.get(CSRF_COOKIE)
        assert csrf

        # A session may not be terminated by a third-party site without CSRF proof.
        missing_csrf = client.post("/v1/auth/logout")
        assert missing_csrf.status_code == 403
        assert client.get("/v1/portal/bootstrap").status_code == 200

        logout = client.post("/v1/auth/logout", headers={CSRF_HEADER: csrf})
        assert logout.status_code == 204
        assert client.get("/v1/auth/me").status_code == 401
        assert client.get("/v1/portal/bootstrap").status_code == 401


def test_p05_t04_postgres_trial_owner_cannot_spoof_tenant_unit_or_csrf(settings) -> None:
    """Internal E2E: tenant/unit are backend authority even after commercial onboarding."""
    delivery = Delivery()
    app = runtime_api.create_runtime_app(settings, **trial_options(delivery))
    publish_trial(app)
    with TestClient(app, base_url="https://testserver") as client:
        assert post_trial(client).status_code == 201
        _activate_and_login(
            client,
            email=BODY["buyer_email"],
            reset_token=delivery.calls[0][1].reset_token,
        )
        csrf = client.cookies.get(CSRF_COOKIE)
        assert csrf
        # Trial only provisions the organization and owner; unit setup is its
        # own canonical onboarding action, not a hidden side-effect of signup.
        units_before = client.get("/v1/portal/surfaces/units")
        assert units_before.status_code == 200
        assert units_before.json()["rows"] == []
        onboard = client.post(
            "/v1/portal/operations/onboardUnit",
            json={"unit_id": "test-unit", "display_name": "Synthetic test unit"},
            headers={CSRF_HEADER: csrf, "Idempotency-Key": "p05-t04-unit-setup"},
        )
        assert onboard.status_code == 200, onboard.text
        units = client.get("/v1/portal/surfaces/units")
        assert units.status_code == 200
        unit_rows = units.json()["rows"]
        assert len(unit_rows) == 1
        own_unit = unit_rows[0]["unit_id"]
        assert own_unit == "test-unit"

        # Register a real foreign tenant/unit in the same PostgreSQL test
        # database: isolation must hold even when the unit actually exists.
        database = app.state.nfcore_runtime.database
        with database.unit_of_work() as uow:
            uow.control_plane.add_organization(
                FiscalOrganization(
                    tenant_id="foreign-tenant",
                    legal_name="Synthetic Foreign Tenant Ltda",
                )
            )
            uow.control_plane.add_unit(
                FiscalUnitRegistration(
                    tenant_id="foreign-tenant",
                    unit_id="foreign-unit",
                    display_name="Synthetic Foreign Unit",
                    enabled_environments=frozenset({FiscalEnvironment.HOMOLOGATION}),
                )
            )
            uow.commit()
        scoped_units = client.get("/v1/portal/surfaces/units")
        assert scoped_units.status_code == 200
        assert [row["unit_id"] for row in scoped_units.json()["rows"]] == [own_unit]

        route = "/v1/portal/operations/queryFiscalDocument"
        payload = {"unit_id": own_unit, "document_id": "synthetic-local-document"}
        assert client.post(route, json=payload).status_code == 403

        tenant_spoof = client.post(
            route,
            json={**payload, "tenant_id": "other-tenant"},
            headers={CSRF_HEADER: csrf},
        )
        assert tenant_spoof.status_code == 400
        assert tenant_spoof.json()["detail"]["code"] == "BROWSER_AUTHORITY_REJECTED"

        unit_spoof = client.post(
            route,
            json={**payload, "unit_id": "foreign-unit"},
            headers={CSRF_HEADER: csrf},
        )
        # Even a registered unit of another tenant fails closed (409),
        # without reaching an unconfigured fiscal provider.
        assert unit_spoof.status_code == 409

        # Access to one client's UI cannot activate unconfigured fiscal providers.
        assert client.get("/runtime/profile").json()["fiscal_production_activated"] is False
