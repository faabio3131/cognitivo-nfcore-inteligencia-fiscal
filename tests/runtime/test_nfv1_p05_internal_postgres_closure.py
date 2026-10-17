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
from kordena_fiscal.domain import ExecutionScope, FiscalEnvironment
from kordena_fiscal.runtime import api as runtime_api
from kordena_fiscal.runtime.worker_composition import build_production_worker_runtime

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
        assert len(delivery.calls) == 1
        assert delivery.calls[0][0] == BODY["buyer_email"]

        _activate_and_login(
            client,
            email=BODY["buyer_email"],
            reset_token=delivery.calls[0][1].reset_token,
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
