"""Fail-closed logical fiscal routing for the SP accountant pilot.

No credentials, endpoint selection, authorization or provider I/O occurs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from kordena_fiscal.domain import BrazilianJurisdiction, FiscalValidationError
from kordena_fiscal.domain.profile import TaxRegimeCode

PilotDocument = Literal["nfe", "nfce", "nfse"]
PilotChannel = Literal["sefaz-sp-nfe", "sefaz-sp-nfce", "nfse-national"]
_SP_IBGE = frozenset({"3509205", "3548708", "3550308"})
_NFSE_CUTOVER = date(2026, 11, 1)


@dataclass(frozen=True, slots=True)
class SpPilotRoute:
    """Routing intent, NEVER proof of authorization to emit."""

    municipality_ibge_code: str
    document: PilotDocument
    channel: PilotChannel
    requires_external_homologation: bool = True


def resolve_sp_pilot_route(
    *,
    jurisdiction: BrazilianJurisdiction,
    document: PilotDocument,
    tax_regime: TaxRegimeCode,
    competence_date: date,
) -> SpPilotRoute:
    """Classify SP pilot documents; deny unknown regimes/historical NFS-e."""
    if (
        not isinstance(jurisdiction, BrazilianJurisdiction)
        or jurisdiction.state_code != "SP"
        or jurisdiction.municipality_ibge_code not in _SP_IBGE
        or type(tax_regime) is not TaxRegimeCode
        or type(competence_date) is not date
        or document not in ("nfe", "nfce", "nfse")
    ):
        raise FiscalValidationError("unsupported SP pilot fiscal context")
    if document == "nfe":
        channel: PilotChannel = "sefaz-sp-nfe"
    elif document == "nfce":
        channel = "sefaz-sp-nfce"
    elif (
        competence_date >= _NFSE_CUTOVER
        and tax_regime in (
            TaxRegimeCode.SIMPLES_NACIONAL,
            TaxRegimeCode.SIMPLES_NACIONAL_EXCESS_SUBLIMIT,
            TaxRegimeCode.MEI,
        )
    ):
        channel = "nfse-national"
    else:
        raise FiscalValidationError(
            "NFS-e municipality and competence need explicit official eligibility"
        )
    return SpPilotRoute(
        municipality_ibge_code=jurisdiction.municipality_ibge_code,
        document=document,
        channel=channel,
    )
