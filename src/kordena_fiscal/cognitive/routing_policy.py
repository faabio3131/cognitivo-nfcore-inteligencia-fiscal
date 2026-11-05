"""Advisory model tier selection; never claims successful provider execution.

The existing FallbackAdvisoryClient owns actual execution and typed fallback.
The input is trusted task metadata, not keywords from untrusted fiscal text.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .contracts import Capability


class AdvisoryTier(StrEnum):
    FAST_ECONOMIC = "fast_economic"
    DEEP_REASONING = "deep_reasoning"


class RoutingPolicyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AdvisoryRoutingDecision:
    tier: AdvisoryTier
    status: str = "SUGGESTED_ONLY"
    authoritative: bool = False


def suggest_advisory_tier(
    *,
    capability: Capability,
    risk: str,
    evidence_complete: bool,
) -> AdvisoryRoutingDecision:
    """Return a suggestion, not provider ID, permission or fiscal determination."""
    if not isinstance(capability, Capability):
        raise RoutingPolicyError("capability must be verified")
    if risk not in ("low", "high"):
        raise RoutingPolicyError("risk must come from trusted structured policy")
    if not isinstance(evidence_complete, bool):
        raise RoutingPolicyError("evidence status must be boolean")
    return AdvisoryRoutingDecision(
        AdvisoryTier.DEEP_REASONING
        if risk == "high" or not evidence_complete
        else AdvisoryTier.FAST_ECONOMIC
    )
