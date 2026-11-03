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

## Reconciliação do lote externo entregue em 03/11/2026

**Origem recebida:** `nfcore_rtc_pacote_normativo_2026-11-03.zip`, sem atestado independente de autenticidade jurídica. Manifesto do fornecedor: `09_MANIFESTOS_E_HASHES/manifesto_artefatos.json` com chaves `arquivos`, `pasta`, `arquivo`, `tamanho`, `sha256`, `url_pagina`, `url_direta`, `data_portal`, `estado` e `nao_obtidos`. **Esse formato de inventário NÃO é o contrato do `RegulatoryArtifactPin` canônico:** `data_portal` não prova `published_on`; `estado` frequentemente é indeterminado. Proibido inventar versão/vigência ou promover todos os registros a pins operacionais.

**Reconciliação técnica reproduzível:** `scripts/rtc_import_external_collection.py` corrige nomes de membros ZIP cujo conteúdo UTF-8 foi interpretado como CP437, sem mudar bytes de PDF, XLSX ou ZIP. Para cada item confere nome, tamanho, SHA-256 declarado e assinatura do formato; falha fechado em divergência, duplicação, travessia de diretório, symlink e HTML disfarçado de PDF/ZIP. Grava o relatório `09_MANIFESTOS_E_HASHES/relatorio_integridade_importacao.json` no pacote de saída. Não altera `config/rtc/official-baseline-2026-10-30.json`.

**Resultado do lote original medido:** 156 registros de arquivos, **156 hashes/tamanhos conferidos**, 20 caminhos ZIP normalizados, 109 PDF, 46 contêineres ZIP (incluindo XLSX) e 1 HTML explicitamente nomeado `.html` (captura da página DOU LC 227, NÃO texto normativo consolidado). O fornecedor declara 9 `nao_obtidos`. Os 156 bytes são consistentes com o **manifesto recebido**, não constituem prova jurídica independente de vigência, fonte ou homologação.

**Execução em staging:** `python scripts/rtc_import_external_collection.py pacote_original.zip pacote_normalizado.zip`. Preservar o original; não versionar 90 MB de downloads no repositório sem avaliação específica de licenciamento, retenção e estratégia de artefatos. Após exame da origem, um responsável pode **produzir pins canônicos individualmente** com datas oficiais comprovadas, para verificação por `verify_regulatory_artifact_bytes`; jamais derivar automaticamente `published_on` de `data_portal`.

**Gates:** testes unitários sintéticos do adaptador + CI/Governança no HEAD exato. A conformidade completa RTC-01/03/04 continua PENDENTE até revisão normativa, pacote NFS-e RTC válido, legislação consolidada, golden cases e decisões de vigência. O merge desta PR só ocorrerá com autorização específica.
