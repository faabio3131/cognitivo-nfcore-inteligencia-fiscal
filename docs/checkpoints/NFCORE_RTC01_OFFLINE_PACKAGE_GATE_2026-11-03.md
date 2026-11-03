# RTC-01 — Gate offline de integridade do pacote normativo (03/11/2026)

**CURRENT conferido:** `main@40d072df6608b8febb0e157c6a36d67c17ec0073` com CI pós-merge #1512 SUCCESS e Governança #943 SUCCESS. A RTC-04 B13 PR #331 está DRAFT, não integrada; B10–B12 estão certificadas. Esta entrega RTC-01 é independente, sem alterar calculadora, catálogo, baseline ou produção.

## Escopo estritamente interno

A agente externa recolherá documentos oficiais; o NFCore recebe arquivos em uma pasta de staging local. O módulo existente `compliance/rtc_evidence.py` continua sendo a **única função de comparação dos bytes com o SHA-256 do pin**. O novo `compliance/rtc_package_evidence.py` apenas lê o inventário de staging, cria `RegulatoryArtifactPin` do contrato canônico e delega a comparação, com guardas de caminho e duplicação.

**Exemplo de `manifest.json` sintético (NÃO oficial):**

```json
{
  "schema_version": 1,
  "artifacts": [
    {
      "artifact_id": "NT-EXEMPLO",
      "kind": "technical_note",
      "version": "synthetic-v1",
      "published_on": "2026-11-01",
      "source_reference": "https://www.nfe.fazenda.gov.br/",
      "checksum_sha256": "SUBSTITUIR_PELO_SHA256_REAL_DO_ARQUIVO",
      "relative_path": "02_NOTAS_TECNICAS_NFE_NFCE/arquivo.pdf"
    }
  ]
}
```

O usuário/conector responsável pelo download deve fornecer os **bytes originais**, seu URL oficial direto, evidência de publicação e vigência, além do checksum; não basta apontar para um URL ou entregar resumo textual.

**Uso programático somente leitura:**

```python
from pathlib import Path
from kordena_fiscal.compliance.rtc_package_evidence import verify_staged_rtc_package

digests = verify_staged_rtc_package(
    Path("NFCORE_RTC_OFFICIAL_NORMATIVE_PACKAGE"),
    "09_MANIFESTOS_E_HASHES/manifest.json",
)
```

O verificador falha fechado para JSON inválido/chaves duplicadas, falta de SHA, divergência dos bytes, ausência de arquivos, caminhos fora da pasta, symlinks, artefatos duplicados e fontes sem HTTPS. Limites: 512 artefatos, 1 MiB de manifesto, 50 MiB por artefato.

**Limites de evidência:** HTTPS e SHA-256 não provam publicação por autoridade oficial. O manifesto é entrada **não confiável** até revisão de origem. Este gate não faz download, não aprova documento, não escolhe vigência, não atualiza `config/rtc/official-baseline-2026-10-30.json` e não ativa emissão, alíquota, XML, homologação ou produção.

**Gate da entrega:** Ruff, Mypy, Pytest, CI e Governança no HEAD exato, PR sem merge antes da autorização aplicável; após integração, repetir os gates pós-merge. RTC-01/03/04 globais seguem `IMPLEMENTED_PARTIAL/BLOCKED_NORMATIVE` até auditoria dos originais, tabelas, XSD e golden cases.
