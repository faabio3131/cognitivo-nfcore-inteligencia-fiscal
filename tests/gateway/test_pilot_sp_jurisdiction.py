"""Pure pilot routing tests. No calls to fiscal services."""

from datetime import date

import pytest

from kordena_fiscal.domain import BrazilianJurisdiction, FiscalValidationError
from kordena_fiscal.domain.profile import TaxRegimeCode
from kordena_fiscal.gateway.pilot_sp_jurisdiction import resolve_sp_pilot_route

CITIES = ("3509205", "3548708", "3550308")


@pytest.mark.parametrize("city", CITIES)
@pytest.mark.parametrize("document,channel", [
    ("nfe", "sefaz-sp-nfe"),
    ("nfce", "sefaz-sp-nfce"),
    ("nfse", "nfse-national"),
])
def test_all_pilot_documents(city: str, document: str, channel: str) -> None:
    route = resolve_sp_pilot_route(
        jurisdiction=BrazilianJurisdiction("SP", city),
        document=document,
        tax_regime=TaxRegimeCode.SIMPLES_NACIONAL,
        competence_date=date(2026, 11, 4),
    )
    assert route.channel == channel
    assert route.municipality_ibge_code == city
    assert route.requires_external_homologation


@pytest.mark.parametrize("regime", [
    TaxRegimeCode.SIMPLES_NACIONAL_EXCESS_SUBLIMIT,
    TaxRegimeCode.MEI,
])
def test_other_simples_variants_route_national(regime: TaxRegimeCode) -> None:
    assert resolve_sp_pilot_route(
        jurisdiction=BrazilianJurisdiction("SP", "3550308"),
        document="nfse",
        tax_regime=regime,
        competence_date=date(2026, 11, 4),
    ).channel == "nfse-national"


@pytest.mark.parametrize("city", CITIES)
def test_historical_service_competence_denied(city: str) -> None:
    with pytest.raises(FiscalValidationError):
        resolve_sp_pilot_route(
            jurisdiction=BrazilianJurisdiction("SP", city),
            document="nfse",
            tax_regime=TaxRegimeCode.SIMPLES_NACIONAL,
            competence_date=date(2026, 10, 31),
        )


def test_normal_regime_service_denied_without_evidence() -> None:
    with pytest.raises(FiscalValidationError):
        resolve_sp_pilot_route(
            jurisdiction=BrazilianJurisdiction("SP", "3550308"),
            document="nfse",
            tax_regime=TaxRegimeCode.NORMAL,
            competence_date=date(2026, 11, 4),
        )


@pytest.mark.parametrize("jurisdiction", [
    BrazilianJurisdiction("RJ", "3304557"),
    BrazilianJurisdiction("SP", "3509502"),
    BrazilianJurisdiction("SP"),
])
def test_not_approved_pilot_location_denied(jurisdiction: BrazilianJurisdiction) -> None:
    with pytest.raises(FiscalValidationError):
        resolve_sp_pilot_route(
            jurisdiction=jurisdiction, document="nfe",
            tax_regime=TaxRegimeCode.NORMAL, competence_date=date(2026, 11, 4),
        )
