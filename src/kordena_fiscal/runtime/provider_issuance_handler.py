"""Opt-in adapter from the canonical fiscal path to durable prepared issuance.

The resolver is supplied by trusted composition and loads a prepared, validated
request from the existing preparation/signing authority. Browser payloads never
supply signed XML, provider selection, certificate material or final outcomes.
"""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.domain import ExecutionScope, FiscalValidationError
from kordena_fiscal.gateway import AuthorizationRequest, FiscalGatewayClient
from kordena_fiscal.issuance.nfe_nfse import NfseAuthorizationRequest, NfseGatewayClient

from .fiscal_runtime import FiscalOperationHandler

PreparedIssuanceResolver = Callable[
    [ExecutionScope, str], AuthorizationRequest | NfseAuthorizationRequest
]


def build_provider_issuance_handler(
    application: FiscalApplicationService,
    *,
    resolve_prepared: PreparedIssuanceResolver,
    gateway: FiscalGatewayClient | NfseGatewayClient,
) -> FiscalOperationHandler:
    """Bind one explicitly configured document family; never enable a default provider."""

    def issue(
        scope: ExecutionScope,
        payload: Mapping[str, Any],
        idempotency_key: str | None,
    ) -> Mapping[str, Any]:
        if set(payload) - {"document_id", "unit_id", "environment"}:
            raise FiscalValidationError("issuance accepts only a prepared document reference")
        document_id = payload.get("document_id")
        if not isinstance(document_id, str) or not document_id.strip():
            raise FiscalValidationError("document_id is required")
        request = resolve_prepared(scope, document_id)
        request_scope = (
            request.scope if isinstance(request, AuthorizationRequest) else request.document.scope
        )
        if request_scope.identity_partition_key != scope.identity_partition_key:
            raise FiscalValidationError("prepared issuance does not match execution scope")
        # HTTP intent identity and canonical issuance identity are distinct.
        # Portal already binds its UUID to the payload; the domain request key
        # protects the same fiscal document even across different HTTP attempts.
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise FiscalValidationError("HTTP idempotency key is required")
        outcome = application.authorize_prepared_document(
            document_id=document_id,
            request=request,
            gateway=gateway,
            occurred_at=datetime.now(UTC),
        )
        return {
            "document_id": outcome.attempt.document_id,
            "status": outcome.lifecycle.state.value,
            "replay": outcome.replay,
            "recovery_required": outcome.recovery_required,
            "result_reference": outcome.attempt.result_reference,
            "rejection_reason": outcome.attempt.rejection_reason,
        }

    return issue
