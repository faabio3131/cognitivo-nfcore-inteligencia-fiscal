# NFCore V1 — 4 planos por consumo + Multi-IA + Sentinela — 03/11/2026

**Base auditada:** `faabio3131/nf-core-v001@d810dca6f3b4ab7ca0ffd7d1a8c1b81cee9a3183`.
**Estado:** `IMPLEMENTED_CANDIDATE / NOT_PUBLISHED / NOT_DEPLOYED`.
**Aprovação de produto:** nova decisão explícita do Diretor de 03/11/2026, **posterior** à aprovação documental de 01/11 na PR #299, arquivada e preservada na PR #339. A presente decisão substitui os números anteriores **quando aprovada no catálogo governado**; não equivale a publicar preços, quotas, trial, checkout ou cobrança.
**Fonte:** comando fornecido pelo Diretor em 03/11/2026, reconciliado contra as autoridades do código atual.

## Escopo de configuração aprovado para evolução interna

- Starter: R$ 99 mensal / R$ 79 mensal-equivalente em contrato anual; 300 documentos/mês, excedente R$ 0,25, 2 CNPJs, 120 req/min.
- Pro (Growth): R$ 249 / R$ 199; 1.500 documentos/mês, excedente R$ 0,15, 5 CNPJs, 600 req/min.
- Business (Scale): R$ 590 / R$ 490; 6.000 documentos/mês, excedente R$ 0,08, 20 CNPJs, 2.400 req/min.
- Enterprise (Hub): R$ 1.490 / R$ 1.190; 25.000 documentos/mês, excedente R$ 0,04, CNPJs/rate-limit sem teto numérico **proposto**, sujeitos a rate limit de proteção operacional e contrato aprovado.
- Paridade funcional, com distinção por consumo.
- Trial: 14 dias; sem cartão; 50 documentos de produção como limite de **produto**, não permissão de emissão. Homologação não tem franquia numérica proposta, mas exige ambiente, provider, credencial, tenant e gates oficiais. Não há autorização automática de emissão ou garantia de ilimitado sem recursos/rate-limit.

## Mapa de autoridades (sem duplicação)

- `config/commercial/plans.json`: proposta versionada em estado `APPROVED_PRODUCT_PROPOSAL_NOT_PUBLISHED` e preços monetários como decimal string.
- `product/commercial_plan_candidate.py`: validação fail-closed, adaptação às entidades existentes `CommercialPricingConfiguration`, `PlanDefinition`, `PriceDefinition`, `UsageQuota`, cálculo **não vinculante** de estimativa de excedentes. Não cria `BillingEngine` paralelo, fatura, evento de pagamento ou persistência independente.
- `cognitive/routing_policy.py`: escolha consultiva `FAST_ECONOMIC`/`DEEP_REASONING` baseada apenas em metadados confiáveis de risco e integridade da evidência. Não usa keywords arbitrárias do prompt para decidir segurança. `FallbackAdvisoryClient` existente continua autoridade para execução real e tratamento de falhas.
- `compliance/normative_sentinel.py`: usa `verify_regulatory_artifact_bytes` canônico; hash igual comprova somente integridade relativa ao pin, **não** proveniência governamental, vigência, interpretação fiscal, homologação nem permissão de produção.

## NÃO implementado / dependências

- Publicação dos quatro planos no Pricing Admin, migração de clientes/assinaturas atuais, parametrização dos contratos anuais, cálculo durável da fatura no ledger canônico, cobrança e checkout reais.
- Hard quotas concorrentes, contador persistido de documentos, antifraude, eventuais sobreconsumos retroativos, trial público, monitoramento de usage e cobrança de excedentes.
- Roteador efetivamente ligado ao runtime de IA com seleção multimodelo por tenant/capability/custo/SLA; o adaptador atual de fallback permanece sem modificação.
- Sentinela com coleta periódica de documentos oficiais, pinagem de fontes, rastreamento de publicação e aprovação humana. O verificador offline não é prova de oficialidade.
- Homologação fiscal externa, RTC baseline autoritativa, certificado, provedor, ativação real, Contabo, production e deploy.
- Sem novas APIs, credenciais, migrations, DNS, alterações irreversíveis ou deploy.

## Gates e aceitação

Condição para promoção à main: PR revisada, testes dirigidos e regressão, Ruff, Mypy strict, CI e Governança `SUCCESS` no SHA exato; merge condicionado à autorização aplicável. Publicação de catálogo e deploy Contabo têm aprovação específica independente. A decisão de produto não derroga o fail-closed fiscal e o RBAC.

**Risco principal:** a configuração de 14 dias/50 documentos contradiz os valores históricos 30 dias/100 documentos e a precificação de 01/11. A nova proposta deve ser versionada e aplicada apenas prospectivamente com regras para clientes já existentes; sem migração implícita de contratos.
