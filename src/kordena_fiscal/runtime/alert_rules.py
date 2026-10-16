"""Bounded alert candidates over canonical in-process metrics; no external delivery."""

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
