from __future__ import annotations

import pytest

from kordena_fiscal.cognitive.contracts import Capability
from kordena_fiscal.cognitive.routing_policy import (
    AdvisoryTier,
    RoutingPolicyError,
    suggest_advisory_tier,
)


def test_fast_route_is_only_advisory() -> None:
    decision = suggest_advisory_tier(
        capability=Capability.EXPLAIN_REJECTION, risk="low", evidence_complete=True
    )
    assert decision.tier == AdvisoryTier.FAST_ECONOMIC
    assert decision.status == "SUGGESTED_ONLY"
    assert decision.authoritative is False


def test_risky_or_incomplete_evidence_prefers_deep_reasoning() -> None:
    for risk, complete in (("high", True), ("low", False)):
        decision = suggest_advisory_tier(
            capability=Capability.ANSWER_ACCOUNTANT_QUESTION, risk=risk, evidence_complete=complete
        )
        assert decision.tier == AdvisoryTier.DEEP_REASONING


def test_untrusted_prompt_is_not_routing_authority() -> None:
    with pytest.raises(RoutingPolicyError):
        suggest_advisory_tier(
            capability=Capability.EXPLAIN_REJECTION,
            risk="exportacao lc214",
            evidence_complete=True,
        )
