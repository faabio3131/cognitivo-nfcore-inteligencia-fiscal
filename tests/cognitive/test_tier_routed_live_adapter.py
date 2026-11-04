"""Real provider dispatch/fallback through the canonical model ports."""

from __future__ import annotations

from unittest.mock import Mock

from kordena_fiscal.cognitive.adapters.openai_compatible import (
    TierRoutedAdvisoryClient,
    build_model_from_environ,
)
from kordena_fiscal.cognitive.contracts import Capability, ModelUsage
from kordena_fiscal.cognitive.ports import (
    ModelPrompt,
    ModelProviderUnavailable,
    ProviderAnswer,
)


def _prompt(capability: Capability, facts: str = "trusted evidence") -> ModelPrompt:
    return ModelPrompt(
        capability=capability,
        system="test-only",
        trusted_facts=facts,
        untrusted_data="exportacao imunidade lc 214",  # MUST NOT control selection
        boundary="untrusted",
        context_hash="hash",
        tenant_id="tenant-test",
        unit_id="unit-test",
        request_id="request-test",
        correlation_id="correlation-test",
    )


def _result(provider: str) -> ProviderAnswer:
    return ProviderAnswer(
        sections=(),
        provider_id=provider,
        model=provider,
        model_version="test-v1",
        usage=ModelUsage(input_tokens=12, output_tokens=7),
    )


def test_fast_route_executes_fast_model_not_keyword_prompt() -> None:
    fast = Mock()
    deep = Mock()
    fast.advise.return_value = _result("fast")
    router = TierRoutedAdvisoryClient(fast=fast, deep=deep)
    result = router.advise(_prompt(Capability.EXPLAIN_REJECTION), deadline_seconds=3)
    assert result.provider_id == "fast"
    assert result.usage.input_tokens == 12
    fast.advise.assert_called_once()
    deep.advise.assert_not_called()


def test_high_risk_route_executes_deep_model() -> None:
    fast = Mock()
    deep = Mock()
    deep.advise.return_value = _result("deep")
    router = TierRoutedAdvisoryClient(fast=fast, deep=deep)
    result = router.advise(_prompt(Capability.ANSWER_ACCOUNTANT_QUESTION), deadline_seconds=3)
    assert result.provider_id == "deep"
    deep.advise.assert_called_once()
    fast.advise.assert_not_called()


def test_provider_error_falls_back_and_tracks_actual_model() -> None:
    fast = Mock()
    deep = Mock()
    deep.advise.side_effect = ModelProviderUnavailable("provider down")
    fast.advise.return_value = _result("fast")
    router = TierRoutedAdvisoryClient(fast=fast, deep=deep)
    result = router.advise(_prompt(Capability.SUGGEST_CLASSIFICATION), deadline_seconds=3)
    assert result.provider_id == "fast"
    assert result.usage.output_tokens == 7
    deep.advise.assert_called_once()
    fast.advise.assert_called_once()


def test_missing_trusted_evidence_prefers_deep() -> None:
    fast = Mock()
    deep = Mock()
    deep.advise.return_value = _result("deep")
    router = TierRoutedAdvisoryClient(fast=fast, deep=deep)
    assert (
        router.advise(
            _prompt(Capability.EXPLAIN_REJECTION, facts=""), deadline_seconds=3
        ).provider_id
        == "deep"
    )


def test_misconfigured_two_tier_opt_in_fails_closed() -> None:
    base = {
        "NFCORE_COGNITIVE_AI_TIER_ROUTING_ENABLED": "true",
        "NFCORE_COGNITIVE_AI_PRIMARY_BASE_URL": "https://ai.example.test/v1",
        "NFCORE_COGNITIVE_AI_PRIMARY_MODEL": "model",
    }
    assert build_model_from_environ(base) is None
    second = {
        **base,
        "NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL": "https://ai2.example.test/v1",
        "NFCORE_COGNITIVE_AI_SECONDARY_MODEL": "model2",
        "NFCORE_COGNITIVE_AI_PRIMARY_TIER": "FAST_ECONOMIC",
        "NFCORE_COGNITIVE_AI_SECONDARY_TIER": "DEEP_REASONING",
    }
    assert isinstance(build_model_from_environ(second), TierRoutedAdvisoryClient)
    assert (
        build_model_from_environ({**second, "NFCORE_COGNITIVE_AI_SECONDARY_TIER": "FAST_ECONOMIC"})
        is None
    )
