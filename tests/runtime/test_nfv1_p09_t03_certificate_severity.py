"""Certificate expiry severity follows the existing 30/7-day operational policy."""

from kordena_fiscal.runtime.alert_rules import OperationalSignals, evaluate_operational_signals


def test_certificate_expiry_severity_and_unknown_state() -> None:
    assert evaluate_operational_signals(OperationalSignals()) == ()
    assert evaluate_operational_signals(OperationalSignals(certificate_days_remaining=31)) == ()
    warning = evaluate_operational_signals(OperationalSignals(certificate_days_remaining=20))
    critical = evaluate_operational_signals(OperationalSignals(certificate_days_remaining=7))
    expired = evaluate_operational_signals(OperationalSignals(certificate_days_remaining=-1))
    assert warning[0].severity == "warning"
    assert critical[0].severity == "critical"
    assert expired[0].severity == "critical"
