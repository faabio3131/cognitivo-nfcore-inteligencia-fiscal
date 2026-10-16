"""Deterministic internal alert candidates over the existing metrics authority.

No notifications, credentials, tenant identifiers or external side effects. Missing
series are unknown, never interpreted as healthy. Thresholds are reviewable policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from kordena_fiscal.runtime.observability import MetricSample


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


# Candidate operational policy; delivery/routing and final thresholds are separate gates.
DEFAULT_RULES: tuple[AlertRule, ...] = (
    AlertRule("http_5xx", "nfcore_http_requests_total", "critical", 0, (("status_class", "5xx"),)),
    AlertRule("provider_errors", "nfcore_provider_errors_total", "warning", 0),
    AlertRule("worker_backlog", "nfcore_worker_backlog_jobs", "warning", 0),
    AlertRule(
        "worker_dead_letter", "nfcore_worker_jobs_total", "critical", 0,
        (("outcome", "dead_letter"),),
    ),
    AlertRule("fiscal_rejection", "nfcore_fiscal_rejections_total", "warning", 0),
    AlertRule("worker_cycle_failure", "nfcore_worker_cycle_failures_total", "warning", 0),
)


def evaluate_alert_candidates(
    samples: tuple[MetricSample, ...],
    rules: tuple[AlertRule, ...] = DEFAULT_RULES,
) -> tuple[AlertCandidate, ...]:
    """Evaluate bounded facts without assuming absent instrumentation means zero."""
    observed: list[AlertCandidate] = []
    for rule in rules:
        values = [
            sample.value
            for sample in samples
            if sample.name == rule.metric
            and all(pair in sample.labels for pair in rule.labels)
        ]
        if not values:
            continue
        value = sum(values)
        if value > rule.threshold:
            observed.append(
                AlertCandidate(rule.code, rule.severity, rule.metric, value, rule.threshold)
            )
    return tuple(observed)
