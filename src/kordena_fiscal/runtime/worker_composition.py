"""Composition root for the canonical durable NFCORE background worker.

CL-02 deliberately wires the already-certified outbox, retry, delivery-audit and
observability primitives. It does not introduce a second queue or invent background
operations. Concrete handlers remain explicit dependencies so missing external
integrations fail closed instead of consuming jobs with placeholder behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from kordena_fiscal.application.webhook_delivery import SignedWebhookOutboxHandler
    from kordena_fiscal.security import WebhookSecurity

from kordena_fiscal.application import (
    BackgroundCycleResult,
    BackgroundWorkerRuntime,
    DurableFiscalOutboxWorker,
    RoutedOutboxHandler,
)
from kordena_fiscal.application.webhook_delivery import (
    WebhookDeliveryRequest,
    WebhookDeliveryResponse,
    WebhookTransport,
)
from kordena_fiscal.contingency import (
    FiscalDispatchResult,
    FiscalOutboxEntry,
    FiscalOutboxHandler,
    FiscalOutboxStatus,
    FiscalRetryPolicy,
)
from kordena_fiscal.contingency.outbox import OutboxClaimSelection
from kordena_fiscal.observability.alerts import AlertRegistry
from kordena_fiscal.observability.events import ObservabilityContext
from kordena_fiscal.persistence.ports import FiscalUnitOfWorkFactory

from .alert_rules import (
    InternalAlertMonitor,
    StructuredLogAlertSink,
    publish_alert_candidates,
)
from .config import RuntimeConfigurationError
from .observability import (
    MetricsRegistry,
    RequestTimer,
    SafeTracer,
    StructuredLogger,
    TraceContext,
    WorkerHealth,
    WorkerObservability,
)
from .otel_trace_sink import build_trace_sink


def _new_trace_context(
    *, correlation_id: str | None = None, causation_id: str | None = None
) -> TraceContext:
    return TraceContext(
        trace_id=uuid4().hex,
        correlation_id=correlation_id or uuid4().hex,
        causation_id=causation_id,
    )


class _TracedOutboxHandler:
    """Observe canonical dispatch without interpreting scope, payload or fiscal outcomes."""

    def __init__(
        self, delegate: FiscalOutboxHandler, tracer: SafeTracer,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._delegate = delegate
        self._tracer = tracer
        self._metrics = metrics

    def _metric(self, seconds: float, outcome: str) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.increment("nfcore_dispatch_total", outcome=outcome)
            self._metrics.observe_seconds("nfcore_dispatch", seconds, outcome=outcome)
        except Exception:
            pass  # Telemetry cannot change fiscal dispatch.

    def dispatch(self, entry: FiscalOutboxEntry) -> FiscalDispatchResult:
        timer = RequestTimer()
        started = datetime.now(UTC)
        context = _new_trace_context(
            correlation_id=entry.scope.correlation_id, causation_id=entry.entry_id
        )
        try:
            result = self._delegate.dispatch(entry)
        except Exception:
            self._metric(timer.elapsed(), "error")
            self._tracer.record(
                operation="worker.dispatch", context=context, started_at=started,
                elapsed_seconds=timer.elapsed(), outcome="error",
            )
            raise
        # Do not validate the domain result in the tracing adapter; the canonical
        # outbox worker remains the only authority for invalid handler responses.
        outcome = result.status.value if isinstance(result, FiscalDispatchResult) else "invalid"
        metric_outcome = (
            outcome if outcome in {"succeeded", "retry_wait", "dead_letter"} else "other"
        )
        self._metric(timer.elapsed(), metric_outcome)
        self._tracer.record(
            operation="worker.dispatch", context=context, started_at=started,
            elapsed_seconds=timer.elapsed(), outcome=outcome,
        )
        return result


class _TracingWorkerObserver:
    """Preserve the certified P04 observer while recording worker cycles."""

    def __init__(
        self, observer: WorkerObservability, tracer: SafeTracer,
        alerts: InternalAlertMonitor | None = None,
        alert_registry: AlertRegistry | None = None,
        alert_context: ObservabilityContext | None = None,
    ) -> None:
        self._observer = observer
        self._tracer = tracer
        self._alerts = alerts
        self._alert_registry = alert_registry
        self._alert_context = alert_context
        self._active_alert_keys: dict[str, str] = {}

    def worker_started(self) -> None:
        self._observer.worker_started()

    def worker_stopped(self) -> None:
        self._observer.worker_stopped()

    def cycle_completed(self, result: BackgroundCycleResult) -> None:
        self._observer.cycle_completed(result)
        self._record(result.elapsed_seconds, "ok")
        self._poll_alerts()

    def cycle_failed(self, *, error_type: str, elapsed_seconds: float) -> None:
        self._observer.cycle_failed(error_type=error_type, elapsed_seconds=elapsed_seconds)
        self._record(elapsed_seconds, "error")
        self._poll_alerts()

    def _poll_alerts(self) -> None:
        if self._alerts is not None:
            try:
                candidates = self._alerts.poll()
                if self._alert_registry is not None and self._alert_context is not None:
                    publish_alert_candidates(
                        candidates, registry=self._alert_registry,
                        context=self._alert_context, active_keys=self._active_alert_keys,
                    )
            except Exception:
                # Internal candidate evaluation can never stop the durable worker.
                pass

    def _record(self, elapsed_seconds: float, outcome: str) -> None:
        self._tracer.record(
            operation="worker.cycle",
            context=_new_trace_context(),
            started_at=datetime.now(UTC) - timedelta(seconds=elapsed_seconds),
            elapsed_seconds=elapsed_seconds, outcome=outcome,
        )


class _TracedWebhookTransport:
    """Trace the actual signed transport port, never URL/body/signature/headers."""

    def __init__(
        self, delegate: WebhookTransport, tracer: SafeTracer,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._delegate = delegate
        self._tracer = tracer
        self._metrics = metrics

    def _metric(self, duration: float, outcome: str) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.increment("nfcore_webhook_delivery_total", outcome=outcome)
            self._metrics.observe_seconds("nfcore_webhook_delivery", duration, outcome=outcome)
        except Exception:
            pass  # Telemetry cannot change the governed webhook transport result.

    def deliver(self, request: WebhookDeliveryRequest) -> WebhookDeliveryResponse:
        timer = RequestTimer()
        started = datetime.now(UTC)
        context = _new_trace_context(
            correlation_id=(request.scope.correlation_id if request.scope else None),
            causation_id=request.outbox_entry_id,
        )
        try:
            response = self._delegate.deliver(request)
        except Exception:
            self._metric(timer.elapsed(), "error")
            self._tracer.record(
                operation="external.webhook", context=context, started_at=started,
                elapsed_seconds=timer.elapsed(), outcome="error",
            )
            raise
        # The signed delivery handler validates response types. Tracing must not
        # replace that validation with AttributeError or reinterpret the result.
        status = response.status_code if isinstance(response, WebhookDeliveryResponse) else None
        outcome = "ok" if status is not None and 200 <= status <= 299 else "error"
        self._metric(timer.elapsed(), outcome)
        self._tracer.record(
            operation="external.webhook", context=context, started_at=started,
            elapsed_seconds=timer.elapsed(),
            outcome="ok" if status is not None and 200 <= status <= 299 else "error",
            attributes={} if status is None else {"status_class": f"{status // 100}xx"},
        )
        return response


DELIVER_WEBHOOK_OPERATION = "deliver_webhook"


@dataclass(frozen=True, slots=True)
class ScopedWorkerHandlerComposition:
    """Carry trusted claim authority alongside concrete handlers to the entrypoint."""

    handlers: Mapping[str, FiscalOutboxHandler]
    claim_selection: OutboxClaimSelection

    def __post_init__(self) -> None:
        if (
            not isinstance(self.claim_selection, OutboxClaimSelection)
            or frozenset(self.handlers) != self.claim_selection.operations
        ):
            raise RuntimeConfigurationError("worker handlers and claim selection disagree")
        object.__setattr__(self, "handlers", MappingProxyType(dict(self.handlers)))


@dataclass(frozen=True, slots=True)
class WorkerWebhookDependencies:
    """Explicit platform dependencies; no URL, raw key or tenant authority here.

    Security must be supplied by the governed signing boundary. Destination URLs
    and approvals are resolved durably for each entry's scope at dispatch time.
    This dependency object does not certify an external secret backend.
    """

    security: WebhookSecurity = field(repr=False)
    destination_id: str

    def __post_init__(self) -> None:
        from kordena_fiscal.security import WebhookSecurity

        if not isinstance(self.security, WebhookSecurity):
            raise RuntimeConfigurationError("worker webhook signing dependency is invalid")
        if (
            not isinstance(self.destination_id, str)
            or not self.destination_id.strip()
            or len(self.destination_id) > 256
            or any(ord(char) < 32 or ord(char) == 127 for char in self.destination_id)
        ):
            raise RuntimeConfigurationError("worker webhook destination reference is invalid")
        object.__setattr__(self, "destination_id", self.destination_id.strip())


def build_canonical_worker_handlers(
    *,
    uow_factory: FiscalUnitOfWorkFactory,
    webhook: WorkerWebhookDependencies | None,
    tracer: SafeTracer | None = None,
) -> Mapping[str, FiscalOutboxHandler]:
    """Register existing concrete handlers only, over the canonical outbox.

    No implicit fiscal provider, inbox replay or commercial provisioning handler
    exists. Missing dependencies fail before claiming jobs. The immutable map has
    one canonical operation, never tenant-selected aliases or dynamic imports.
    """
    if not isinstance(webhook, WorkerWebhookDependencies):
        raise RuntimeConfigurationError(
            "continuous worker requires an explicitly configured handler factory "
            "or canonical webhook signing dependencies"
        )
    return MappingProxyType(
        {
            DELIVER_WEBHOOK_OPERATION: build_customer_webhook_handler(
                uow_factory=uow_factory,
                security=webhook.security,
                destination_id=webhook.destination_id,
                tracer=tracer,
            )
        }
    )


@dataclass(frozen=True, slots=True)
class ProductionWorkerComposition:
    """Process-local worker composition; authoritative job state stays durable."""

    runtime: BackgroundWorkerRuntime
    operations: frozenset[str]
    metrics: MetricsRegistry
    observer: WorkerObservability
    alert_monitor: InternalAlertMonitor | None = None

    def health(self) -> WorkerHealth:
        return self.observer.health()


def build_production_worker_runtime(
    *,
    uow_factory: FiscalUnitOfWorkFactory,
    handlers: Mapping[str, FiscalOutboxHandler],
    environment: str,
    retry_policy: FiscalRetryPolicy | None = None,
    batch_size: int = 10,
    lease_duration: timedelta = timedelta(seconds=60),
    idle_wait_seconds: float = 1.0,
    failure_wait_seconds: float = 2.0,
    heartbeat_timeout_seconds: float = 60.0,
    tracer: SafeTracer | None = None,
    claim_selection: OutboxClaimSelection | None = None,
) -> ProductionWorkerComposition:
    """Compose one durable worker over the canonical outbox and observer boundaries.

    ``RoutedOutboxHandler`` intentionally rejects an empty handler map. That keeps a
    staging/production worker from appearing healthy while no authorized operation can
    actually be executed.
    """

    if claim_selection is not None and (
        not isinstance(claim_selection, OutboxClaimSelection)
        or claim_selection.operations != frozenset(handlers)
    ):
        raise RuntimeConfigurationError("worker handlers and claim selection disagree")
    runtime_tracer = tracer if tracer is not None else SafeTracer(
        build_trace_sink(
            StructuredLogger(service="nfcore-worker", environment=environment),
            service="nfcore-worker",
        )
    )
    metrics = MetricsRegistry()
    alert_monitor = InternalAlertMonitor(metrics)
    # Only the certified scoped Worker may emit tenant-bound alerts. Unscoped
    # workers expose candidates but cannot invent a tenant/unit authority.
    alert_registry = None
    alert_context = None
    if claim_selection is not None:
        alert_registry = AlertRegistry(sink=StructuredLogAlertSink(
            StructuredLogger(service="nfcore-worker", environment=environment)
        ))
        alert_context = ObservabilityContext(scope=claim_selection.scope)
    traced_handlers = {
        operation: _TracedOutboxHandler(handler, runtime_tracer, metrics)
        for operation, handler in handlers.items()
    }
    routed = RoutedOutboxHandler(traced_handlers)

    def queue_counts() -> Mapping[FiscalOutboxStatus, int]:
        timer = RequestTimer()
        started = datetime.now(UTC)
        context = _new_trace_context()
        try:
            with uow_factory() as uow:
                counts = (
                    uow.outbox.counts_by_status()
                    if claim_selection is None
                    else uow.outbox.counts_by_status(selection=claim_selection)
                )
        except Exception:
            runtime_tracer.record(
                operation="db.outbox_counts", context=context, started_at=started,
                elapsed_seconds=timer.elapsed(), outcome="error",
            )
            raise
        runtime_tracer.record(
            operation="db.outbox_counts", context=context, started_at=started,
            elapsed_seconds=timer.elapsed(), outcome="ok",
        )
        return counts

    observer = WorkerObservability(
        metrics=metrics,
        queue_counts=queue_counts,
        heartbeat_timeout_seconds=heartbeat_timeout_seconds,
        logger=StructuredLogger(service="nfcore-worker", environment=environment),
    )
    worker = DurableFiscalOutboxWorker(
        uow_factory=uow_factory,
        handler=routed,
        retry_policy=retry_policy,
        claim_selection=claim_selection,
    )
    runtime = BackgroundWorkerRuntime(
        worker=worker,
        observer=_TracingWorkerObserver(
            observer, runtime_tracer, alert_monitor, alert_registry, alert_context,
        ),
        batch_size=batch_size,
        lease_duration=lease_duration,
        idle_wait_seconds=idle_wait_seconds,
        failure_wait_seconds=failure_wait_seconds,
    )
    return ProductionWorkerComposition(
        runtime=runtime,
        operations=routed.operations,
        metrics=metrics,
        observer=observer,
        alert_monitor=alert_monitor,
    )


def build_customer_webhook_handler(
    *,
    uow_factory: FiscalUnitOfWorkFactory,
    security: WebhookSecurity,
    destination_id: str,
    tracer: SafeTracer | None = None,
    metrics: MetricsRegistry | None = None,
) -> SignedWebhookOutboxHandler:
    """Compose the approved adapter without activating any worker operation/deploy."""
    from kordena_fiscal.application.webhook_delivery import SignedWebhookOutboxHandler
    from kordena_fiscal.control_plane.webhook_policy import DurableWebhookEgressPolicy
    from kordena_fiscal.gateway.webhook_transport import PinnedWebhookTransport
    from kordena_fiscal.runtime.webhook_destination import DurableWebhookDestinationResolver

    policy = DurableWebhookEgressPolicy(uow_factory)
    return SignedWebhookOutboxHandler(
        security=security,
        policy=policy,
        destination_resolver=DurableWebhookDestinationResolver(uow_factory, destination_id),
        transport=_TracedWebhookTransport(
            PinnedWebhookTransport(policy),
            tracer if tracer is not None else SafeTracer(
                build_trace_sink(
                    StructuredLogger(service="nfcore-worker", environment="unspecified"),
                    service="nfcore-worker",
                )
            ),
            metrics=metrics,
        ),
    )
