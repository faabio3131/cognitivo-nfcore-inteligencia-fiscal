"""Fail-closed validation of RTC codes against a pinned, normalized catalog.

The payload is a reviewed JSON normalization of an official source. Its hash
protects the reviewed payload's integrity, but does NOT attest that the
normalization itself was faithful to the published government spreadsheet.
No rates or implicit classifications are provided by this module.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime

from kordena_fiscal.compliance.rtc import (
    ReformTaxClassificationSnapshot,
    RegulatoryArtifactKind,
    RegulatoryBaseline,
    RegulatoryBaselineError,
)
from kordena_fiscal.compliance.rtc_evidence import verify_regulatory_artifact_bytes
from kordena_fiscal.domain import TaxRegimeCode
from kordena_fiscal.tax import TaxDecision, TaxRule, TaxRuleContext, TaxRuleEngine

# Local construction witness: a catalog object is not verified merely by its type.
# This protects the canonical code path against accidental unpinned synthetic data.
_VERIFIED_CATALOG_WITNESS = object()


@dataclass(frozen=True, slots=True)
class VerifiedRtcClassificationCatalog:
    artifact_version: str
    allowed_pairs: frozenset[tuple[str, str]]
    published_on: date | None = None
    effective_from: date | None = None
    artifact_id: str | None = None
    checksum_sha256: str | None = None
    source_reference: str | None = None
    _verification_witness: (
        tuple[object, str, frozenset[tuple[str, str]], date | None, date | None,
              str | None, str | None, str | None] | None
    ) = field(default=None, repr=False, compare=False)

    def _is_verified(self) -> bool:
        # Replacing a verified dataclass with different codes or version
        # must invalidate its verification provenance.
        return self._verification_witness == (
            _VERIFIED_CATALOG_WITNESS, self.artifact_version, self.allowed_pairs,
            self.published_on, self.effective_from,
            self.artifact_id, self.checksum_sha256, self.source_reference,
        )

    def require_same_baseline(self, baseline: RegulatoryBaseline) -> None:
        """Reject mixing classification and rate artifacts from unrelated pins.

        The normalized table digest and full metadata must be exactly the same
        as the classification pin in the rate baseline. This is an integrity
        check, not evidence that a government publication is authentic.
        """
        if not self._is_verified():
            raise RegulatoryBaselineError("RTC catalog requires pinned artifact verification")
        if not isinstance(baseline, RegulatoryBaseline):
            raise RegulatoryBaselineError("RTC preview requires canonical baseline")
        if self.artifact_id is None or self.checksum_sha256 is None:
            raise RegulatoryBaselineError("RTC catalog lacks baseline pin identity")
        artifact = baseline.artifact(self.artifact_id)
        if (
            artifact.kind is not RegulatoryArtifactKind.CLASSIFICATION_TABLE
            or artifact.version != self.artifact_version
            or artifact.published_on != self.published_on
            or artifact.effective_from != self.effective_from
            or artifact.checksum_sha256 != self.checksum_sha256
            or artifact.source_reference != self.source_reference
        ):
            raise RegulatoryBaselineError("RTC classification catalog baseline pin mismatch")

    def require_published_at(self, instant: datetime) -> None:
        """Deny retrospective/future catalog use before official publication.

        Publication is only a lower bound, not proof of legal effectiveness.
        Any explicit effective_from is an additional lower bound. This preview
        does not confer XML emission or calculation authority.
        """
        if not self._is_verified():
            raise RegulatoryBaselineError("RTC catalog requires pinned artifact verification")
        if not isinstance(instant, datetime) or instant.tzinfo is None or (
            instant.utcoffset() is None
        ):
            raise RegulatoryBaselineError("RTC catalog instant must be timezone-aware")
        if not isinstance(self.published_on, date):
            raise RegulatoryBaselineError("RTC catalog publication is not pinned")
        if instant.date() < self.published_on:
            raise RegulatoryBaselineError("RTC catalog was not published at fiscal instant")
        if self.effective_from is not None and instant.date() < self.effective_from:
            raise RegulatoryBaselineError("RTC catalog not effective at fiscal instant")

    def require_classification(self, snapshot: ReformTaxClassificationSnapshot) -> None:
        """Deny unknown codes, including missing classification on nonempty catalogs."""
        if not self._is_verified():
            raise RegulatoryBaselineError("RTC catalog requires pinned artifact verification")
        if not isinstance(snapshot, ReformTaxClassificationSnapshot):
            raise RegulatoryBaselineError("RTC classification snapshot required")
        if snapshot.classification_table_version != self.artifact_version:
            raise RegulatoryBaselineError("RTC classification table version mismatch")
        key = (snapshot.cst_code, snapshot.classification_code or "")
        if key not in self.allowed_pairs:
            raise RegulatoryBaselineError("unrecognized RTC CST/cClassTrib combination")
        if snapshot.presumed_credit_code is not None:
            raise RegulatoryBaselineError(
                "RTC cCredPres requires an independently verified credit catalog"
            )


def _unique_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject JSON key collisions rather than silently accepting last-write wins."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RegulatoryBaselineError("duplicate RTC normalized catalog JSON key")
        result[key] = value
    return result


def load_verified_rtc_classification_catalog(
    baseline: RegulatoryBaseline,
    artifact_payload: bytes,
    *,
    artifact_id: str = "IBSCBS-CCLASSTRIB",
) -> VerifiedRtcClassificationCatalog:
    """Load reviewed normalized rows after exact digest and baseline pin validation.

    The caller remains responsible for independent official-source validation
    and human approval of the normalized mapping before production use.
    """
    if not isinstance(baseline, RegulatoryBaseline):
        raise RegulatoryBaselineError("regulatory baseline is required")
    artifact = baseline.artifact(artifact_id)
    if artifact.kind is not RegulatoryArtifactKind.CLASSIFICATION_TABLE:
        raise RegulatoryBaselineError("RTC artifact must be a classification table")
    verify_regulatory_artifact_bytes(artifact, artifact_payload)
    try:
        raw = json.loads(artifact_payload, object_pairs_hook=_unique_json_keys)
    except (ValueError, UnicodeDecodeError) as exc:
        raise RegulatoryBaselineError("RTC normalized catalog must be JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "artifact_id", "artifact_version", "records",
    }:
        raise RegulatoryBaselineError("invalid RTC normalized catalog schema")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise RegulatoryBaselineError("RTC normalized catalog schema version mismatch")
    if raw["artifact_id"] != artifact.artifact_id:
        raise RegulatoryBaselineError("RTC normalized catalog identity mismatch")
    if raw["artifact_version"] != artifact.version:
        raise RegulatoryBaselineError("RTC normalized catalog version mismatch")
    rows = raw["records"]
    if not isinstance(rows, list) or not rows:
        raise RegulatoryBaselineError("RTC normalized catalog requires records")
    pairs: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"cst", "cclass_trib"}:
            raise RegulatoryBaselineError("invalid RTC classification row shape")
        cst, classification = row["cst"], row["cclass_trib"]
        if (
            not isinstance(cst, str)
            or len(cst) != 3
            or not cst.isascii()
            or not cst.isdigit()
            or not isinstance(classification, str)
            or len(classification) != 6
            or not classification.isascii()
            or not classification.isdigit()
        ):
            raise RegulatoryBaselineError("invalid RTC CST/cClassTrib code format")
        pairs.append((cst, classification))
    if len(set(pairs)) != len(pairs):
        raise RegulatoryBaselineError("duplicate RTC CST/cClassTrib pair")
    reviewed_pairs = frozenset(pairs)
    if artifact.published_on > baseline.captured_at.date():
        raise RegulatoryBaselineError("RTC catalog published after pinned baseline capture")
    return VerifiedRtcClassificationCatalog(
        artifact.version,
        reviewed_pairs,
        published_on=artifact.published_on,
        effective_from=artifact.effective_from,
        artifact_id=artifact.artifact_id,
        checksum_sha256=artifact.checksum_sha256,
        source_reference=artifact.source_reference,
        _verification_witness=(
            _VERIFIED_CATALOG_WITNESS, artifact.version, reviewed_pairs,
            artifact.published_on, artifact.effective_from,
            artifact.artifact_id, artifact.checksum_sha256,
            artifact.source_reference,
        ),
    )


def resolve_rule_with_verified_rtc_catalog(
    *,
    engine: TaxRuleEngine,
    context: TaxRuleContext,
    rules: Iterable[TaxRule],
    catalog: VerifiedRtcClassificationCatalog,
) -> tuple[TaxDecision, ReformTaxClassificationSnapshot]:
    """Bind the existing deterministic rule winner to a version-pinned RTC pair.

    No fallback classification, rate, or fiscal emission is inferred. Callers must
    supply a catalog verified from a reviewed normative artifact via the loader.
    """
    if (
        not isinstance(catalog, VerifiedRtcClassificationCatalog)
        or not catalog._is_verified()
    ):
        raise RegulatoryBaselineError("verified RTC classification catalog required")
    if not isinstance(context, TaxRuleContext):
        raise RegulatoryBaselineError("canonical RTC tax context required")
    catalog.require_published_at(context.instant)
    decision = engine.resolve(context, rules)
    outcome = decision.outcome
    if (
        outcome.ibs_cbs_cst_code is None
        or outcome.ibs_cbs_classification_code is None
        or outcome.ibs_cbs_classification_table_version is None
    ):
        raise RegulatoryBaselineError("RTC rule requires explicit CST, cClassTrib and version")
    if outcome.ibs_cbs_classification_table_version != catalog.artifact_version:
        raise RegulatoryBaselineError("RTC tax-rule classification version mismatch")
    snapshot = ReformTaxClassificationSnapshot(
        cst_code=outcome.ibs_cbs_cst_code,
        classification_code=outcome.ibs_cbs_classification_code,
        classification_table_version=outcome.ibs_cbs_classification_table_version,
    )
    catalog.require_classification(snapshot)
    return decision, snapshot


def resolve_strict_rtc_2026_incidence_candidate(
    *,
    engine: TaxRuleEngine,
    context: TaxRuleContext,
    rules: Iterable[TaxRule],
    catalog: VerifiedRtcClassificationCatalog,
) -> tuple[TaxDecision, ReformTaxClassificationSnapshot]:
    """Require a contextual, effective and versioned rule for RTC-04 analysis.

    A catalog only validates a CST/cClassTrib pair; it does not prove that the
    pair has correct legal incidence. This internal candidate is non-issuable.
    In particular a wildcard tax rule cannot justify a 2026 IBS/CBS preview.
    """
    if not isinstance(context, TaxRuleContext) or not isinstance(engine, TaxRuleEngine):
        raise RegulatoryBaselineError("canonical tax context and engine required")
    if context.instant.year != 2026:
        raise RegulatoryBaselineError("incidence candidate supports only 2026")
    if context.tax_regime is not TaxRegimeCode.NORMAL:
        raise RegulatoryBaselineError("2026 incidence candidate excludes Simples Nacional")
    # Freeze the iterable so the canonical engine and the later audit see the
    # exact same rule set, including one-shot iterators.
    candidates = tuple(rules)
    decision, snapshot = resolve_rule_with_verified_rtc_catalog(
        engine=engine, context=context, rules=candidates, catalog=catalog,
    )
    winners = [
        rule for rule in candidates
        if rule.rule_id == decision.rule_id and rule.version == decision.rule_version
    ]
    if len(winners) != 1:
        raise RegulatoryBaselineError("winning RTC rule identity must be unique")
    selector = winners[0].selector
    if (
        selector.state_code is None
        or selector.tax_regime is None
        or selector.document_kind is None
        or selector.operation_type is None
        or selector.recipient_profile is None
        or selector.ncm_prefix is None
    ):
        raise RegulatoryBaselineError(
            "RTC incidence candidate requires explicit contextual selectors"
        )
    # The selector is already evaluated by TaxRuleEngine; never independently
    # override its winning rule or its classifications with caller data.
    return decision, snapshot
