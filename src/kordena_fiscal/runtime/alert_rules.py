"""Bounded alert candidates over canonical in-process metrics; no external delivery."""

from __future__ import annotations

from dataclasses import dataclass

from kordena_fiscal.observability.alerts import AlertRegistry
from kordena_fiscal.observability.events import ObservabilityContext
from kordena_fiscal.runtime.observability import MetricSample, MetricsRegistry


@dataclass(frozen=True, slots=True)
class AlertCandidate:
    code: str
    severity: str
    metric: str
    observed: float
    threshold: float


@dataclass(frozen=True, slots=True)
class AlertRule:
    code: str
    metric: str
    severity: str
    threshold: float
    labels: tuple[tuple[str, str], ...] = ()
    kind: str = "counter"


# Threshold zero is a conservative *candidate*, not a production paging policy.
DEFAULT_RULES: tuple[AlertRule, ...] = (
    AlertRule("http_5xx", "nfcore_http_requests_total", "critical", 0,
              (("status_class", "5xx"),)),
    AlertRule("provider_errors", "nfcore_provider_errors_total", "warning", 0),
    AlertRule("worker_backlog", "nfcore_worker_backlog_jobs", "warning", 0,
              kind="gauge"),
    AlertRule("worker_dead_letter", "nfcore_worker_jobs_total", "critical", 0,
              (("outcome", "dead_letter"),)),
    AlertRule("fiscal_rejection", "nfcore_fiscal_rejections_total", "warning", 0),
    AlertRule("worker_cycle_failure", "nfcore_worker_cycle_failures_total", "warning", 0),
)


def evaluate_alert_candidates(
    samples: tuple[MetricSample, ...],
    rules: tuple[AlertRule, ...] = DEFAULT_RULES,
    *,
    previous: tuple[MetricSample, ...] | None = None,
) -> tuple[AlertCandidate, ...]:
    """Counter alerts require two snapshots; missing series is unknown, not healthy.

    Counter resets are not counted as incidents; gauge rules use present value.
    The evaluator never emits notifications or changes fiscal authority.
    """
    observed: list[AlertCandidate] = []
    for rule in rules:
        if rule.kind not in {"counter", "gauge"}:
            raise ValueError("unsupported alert rule kind")
        current = {
            sample.labels: sample.value for sample in samples
            if sample.name == rule.metric and all(pair in sample.labels for pair in rule.labels)
        }
        if not current:
            continue
        if rule.kind == "counter":
            if previous is None:
                continue
            baseline = {
                sample.labels: sample.value for sample in previous
                if sample.name == rule.metric and all(pair in sample.labels for pair in rule.labels)
            }
            # New or reset series do not have a trusted delta until next sample.
            value = sum(
                max(0.0, amount - baseline[labels])
                for labels, amount in current.items()
                if labels in baseline and amount >= baseline[labels]
            )
        else:
            value = sum(current.values())
        if value > rule.threshold:
            observed.append(AlertCandidate(
                rule.code, rule.severity, rule.metric, value, rule.threshold
            ))
    return tuple(observed)


@dataclass(frozen=True, slots=True)
class OperationalSignals:
    """Trusted, pre-validated observations; None means not observed, not healthy."""

    certificate_days_remaining: float | None = None
    secret_resolution_ok: bool | None = None
    database_ready: bool | None = None
    deployment_healthy: bool | None = None


def evaluate_operational_signals(signals: OperationalSignals) -> tuple[AlertCandidate, ...]:
    """Only explicit observations may create alerts; no network or secret access."""
    import math

    alerts: list[AlertCandidate] = []
    days = signals.certificate_days_remaining
    if days is not None:
        if not math.isfinite(days):
            raise ValueError("certificate expiry observation must be finite")
        if days <= 30:
            alerts.append(AlertCandidate("certificate_expiry", "warning",
                                         "certificate_days_remaining", days, 30))
    for code, ok in (
        ("secret_failure", signals.secret_resolution_ok),
        ("db_unavailable", signals.database_ready),
        ("deployment_unhealthy", signals.deployment_healthy),
    ):
        if ok is False:
            alerts.append(AlertCandidate(code, "critical", code, 1.0, 0.0))
    return tuple(alerts)


def fiscal_rejection_rate(
    current: tuple[MetricSample, ...],
    previous: tuple[MetricSample, ...],
    *,
    threshold: float = 0.1,
) -> AlertCandidate | None:
    """Ratio of observed rejected authorizations to all finished authorizations.

    Requires both counter families and a valid prior sample. Missing denominator
    or reset counters are not interpreted as safe nor as a real rejection rate.
    """
    import math

    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("invalid rejection rate threshold")

    def amount(samples: tuple[MetricSample, ...], name: str) -> float | None:
        matches = [item.value for item in samples if item.name == name]
        return sum(matches) if matches else None

    rejected_now = amount(current, "nfcore_fiscal_rejections_total")
    rejected_before = amount(previous, "nfcore_fiscal_rejections_total")
    finalized_now = amount(current, "nfcore_fiscal_authorizations_finalized_total")
    finalized_before = amount(previous, "nfcore_fiscal_authorizations_finalized_total")
    if None in (rejected_now, rejected_before, finalized_now, finalized_before):
        return None
    assert rejected_now is not None and rejected_before is not None
    assert finalized_now is not None and finalized_before is not None
    if rejected_now < rejected_before or finalized_now < finalized_before:
        return None
    rejected = rejected_now - rejected_before
    total = finalized_now - finalized_before
    if total <= 0 or rejected > total:
        return None
    rate = rejected / total
    return (AlertCandidate("fiscal_rejection_rate", "warning", "ratio", rate, threshold)
            if rate > threshold else None)


class InternalAlertMonitor:
    """Poll existing registry; expose candidates to a caller without auto-sending."""

    def __init__(self, metrics: MetricsRegistry) -> None:
        self._metrics = metrics
        self._previous: tuple[MetricSample, ...] | None = None

    def poll(self, *, signals: OperationalSignals | None = None) -> tuple[AlertCandidate, ...]:
        current = self._metrics.snapshot()
        candidates = list(evaluate_alert_candidates(current, previous=self._previous))
        if self._previous is not None:
            ratio = fiscal_rejection_rate(current, self._previous)
            if ratio is not None:
                candidates.append(ratio)
        if signals is not None:
            candidates.extend(evaluate_operational_signals(signals))
        self._previous = current
        return tuple(candidates)


# The existing V2-13 AlertRegistry remains the single owner of alert identity,
# deduplication, sanitization, sinks and lifecycle. The metrics evaluator only
# projects bounded candidates and never constructs tenant authority itself.
_ALERT_KIND = {
    "http_5xx": "http-5xx",
    "provider_errors": "provider-error",
    "worker_backlog": "queue-backlog",
    "worker_dead_letter": "dead-letter",
    "fiscal_rejection": "fiscal-rejection",
    "fiscal_rejection_rate": "rejection-rate",
    "worker_cycle_failure": "worker-cycle-failure",
    "certificate_expiry": "certificate-expiry",
    "secret_failure": "secret-failure",
    "db_unavailable": "db-unavailable",
    "deployment_unhealthy": "deployment-unhealthy",
}


def publish_alert_candidates(
    candidates: tuple[AlertCandidate, ...],
    *,
    registry: AlertRegistry,
    context: ObservabilityContext,
) -> int:
    """Delegate all alert persistence/deduplication to canonical AlertRegistry.

    A caller must provide an already-authorized context, never user-supplied
    tenant fields. No external delivery or credential resolution occurs here.
    """
    from kordena_fiscal.observability.alerts import AlertKind, AlertSeverity

    published = 0
    for candidate in candidates:
        kind = _ALERT_KIND.get(candidate.code)
        if kind is None:
            continue
        alert = registry.emit(
            kind=AlertKind(kind),
            severity=AlertSeverity(candidate.severity),
            context=context,
            message_code=f"runtime.{candidate.code}",
            dimension="runtime",
            attributes={"observed": candidate.observed,
                        "threshold": candidate.threshold},
        )
        if alert is not None:
            published += 1
    return published
