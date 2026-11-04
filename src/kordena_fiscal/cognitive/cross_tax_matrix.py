"""Matriz cruzada de evidências, exclusivamente consultiva e fail-closed.

Não mapeia CFOP ou CRT diretamente para CST/cClassTrib, nem substitui
TaxRuleEngine/ClassificationBaseline. Sem tabelas oficiais pinadas, não decide.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrossTaxAssessment:
    status: str
    authoritative: bool
    cclasstrib: None
    cst: None
    findings: tuple[str, ...]
    approval_required: bool = True


def review_cross_tax_dimensions(
    *,
    cnae: str,
    ncm: str,
    cfop: str,
    crt: int,
    uf_origem: str,
    uf_destino: str,
    nbs: str | None = None,
) -> CrossTaxAssessment:
    """Verifica integridade estrutural, sem inferir enquadramento jurídico."""
    findings: list[str] = []
    if not re.fullmatch(r"\d{7}", str(cnae)):
        findings.append("CNAE inválido ou ausente")
    if not re.fullmatch(r"\d{8}", str(ncm)):
        findings.append("NCM inválido ou ausente")
    if not re.fullmatch(r"[1-7]\d{3}", str(cfop)):
        findings.append("CFOP inválido ou ausente")
    if crt not in (1, 2, 3, 4):
        findings.append("CRT inválido")
    valid_ufs = frozenset(
        "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI "
        "RJ RN RS RO RR SC SP SE TO EX".split()
    )
    if uf_origem not in valid_ufs - {"EX"} or uf_destino not in valid_ufs:
        findings.append("UF inválida")
    if nbs is not None and not re.fullmatch(r"\d{9}", str(nbs)):
        findings.append("NBS inválido")
    findings.append(
        "CST/cClassTrib dependem da decisão fiscal canônica e de catálogo oficial verificado"
    )
    return CrossTaxAssessment(
        status="INVALID_INPUT" if len(findings) > 1 else "REVIEW_REQUIRED",
        authoritative=False,
        cclasstrib=None,
        cst=None,
        findings=tuple(findings),
    )
