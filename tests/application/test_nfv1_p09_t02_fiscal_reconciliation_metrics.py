"""Fiscal reconciliation metrics are emitted after commit and never mutate authority."""

from functools import partial
from types import SimpleNamespace
from unittest.mock import Mock

from kordena_fiscal.application.service import FiscalApplicationService
from kordena_fiscal.reconciliation import ReconciliationStatus
from kordena_fiscal.runtime.observability import MetricsRegistry


class _UnitOfWork:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self.reconciliations = SimpleNamespace(save=lambda _: calls.append("save"))

    def __enter__(self) -> "_UnitOfWork":
        return self

    def __exit__(self, *_args: object) -> None:
        return

    def commit(self) -> None:
        self.calls.append("commit")


class _ObservedMetrics(MetricsRegistry):
    def __init__(self, calls: list[str], fail: bool = False) -> None:
        super().__init__()
        self.calls = calls
        self.fail = fail

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        self.calls.append("metric")
        if self.fail:
            raise RuntimeError("telemetry unavailable")
        super().increment(name, value, **labels)


def test_fiscal_metric_only_after_commit_and_failure_is_non_authoritative() -> None:
    for fail in (False, True):
        calls: list[str] = []
        metrics = _ObservedMetrics(calls, fail=fail)
        result = SimpleNamespace(status=ReconciliationStatus.MATCHED)
        engine = Mock()
        engine.reconcile_operation.return_value = result
        service = FiscalApplicationService(
            partial(_UnitOfWork, calls), reconciliation=engine, metrics=metrics
        )
        assert service.reconcile_operation(Mock(), ()) is result
        assert calls == ["save", "commit", "metric"]
        samples = [
            s for s in metrics.as_dicts()
            if s["name"] == "nfcore_fiscal_reconciliation_total"
        ]
        if fail:
            assert samples == []
        else:
            assert samples == [{
                "name": "nfcore_fiscal_reconciliation_total",
                "value": 1.0,
                "labels": {"outcome": "matched"},
            }]
