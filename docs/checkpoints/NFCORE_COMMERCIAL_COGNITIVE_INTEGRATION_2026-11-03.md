# NFCore — Integração interna das três frentes — 03/11/2026

**Branch:** feat/nfcore-four-plan-multi-ai-sentinel-20261103
**Base de construção:** main@d810dca6f3b4ab7ca0ffd7d1a8c1b81cee9a3183
**Escopo:** aprimorar PR #340; não habilitar operação comercial, IA paga ou fiscal sem gates.

## 1. Comercial

- Quatro planos versionados `config/commercial/plans.json` e adaptados ao catálogo **canônico** de preços, planos, cotas e cadência; preços em Decimal.
- A rota `GET /v1/admin/pricing/candidate` mostra ao `platform_admin` o catálogo candidato e versão corrente, exigindo a autenticação de sessão canônica. Não cria um segundo Pricing Admin, não altera `CommercialPricingAdministrationService.publish` e não autoriza checkout.
- O catálogo candidato mantém `enabled=False`, e os valores publicados só podem ser aplicados prospectivamente depois de aprovação administrativa, migração governada e aceitação de contratos existentes.
- **Não implementados como fato:** emissão de fatura real, enforcement concorrente de todas as quotas comerciais e billing externo; requerem integração adicional no ledger/assinatura canônico. Um cálculo de estimativa não é uma invoice.

## 2. Roteamento multi-IA

- `TierRoutedAdvisoryClient` seleciona clientes `FAST_ECONOMIC` e `DEEP_REASONING` pela capacidade autenticada e presença de fatos confiáveis, não por keywords de texto do usuário.
- Reusa **exatamente** os providers `OpenAICompatibleAdvisoryClient`, fallback `FallbackAdvisoryClient`, timeout compartilhado, quotas, audit e ledger já instalados em `composition.py`.
- Opt-in exclusivamente com `NFCORE_COGNITIVE_AI_TIER_ROUTING_ENABLED=true` e tiers `NFCORE_COGNITIVE_AI_{PRIMARY,SECONDARY}_TIER` explícitos; dois providers válidos obrigatórios. Flag não habilita IA sem `NFCORE_COGNITIVE_ENABLED`, aprovação de IA durável, audit e quotas em staging/produção.
- Fallback registra `ProviderAnswer` real do cliente de destino; nenhuma execução `SUCCESS` inventada.

## 3. Sentinela Normativo

- `normative_watch.py` observa quatro URLs de portais públicos fixas (NF-e, SVRS, NFS-e, DOU) via HTTPS, com redirects proibidos, timeout e limite 2 MiB; compara SHA-256 das páginas e conserva checkpoint atômico, bloqueia concorrência por lock O_EXCL.
- Eventos de primeiro contato e alteração indicam somente `REVIEW_REQUIRED`. Mudança de HTML **não** comprova alteração normativa; a baseline fiscal e os artefatos oficiais pinados permanecem fontes separadas.
- Entrypoint `scripts/nfcore_normative_watch_once.py` exige `NFCORE_NORMATIVE_WATCH_ENABLED=true`, `--acknowledge-network` e um `--state-file` em diretório persistente pré-criado. É executável por timer/cron após autorização; **não há agendamento instalado na Contabo**.
- Templates systemd de exemplo ficam em `deploy/contabo/nfcore-normative-watch.*.example`; requerem conferência de paths, usuário, egress e aprovação de instalação. Não foram ativados.
- Nenhuma coleta externa real, polling produtivo, ativação de regra ou alteração de banco foi realizada.

## Gates ainda necessários

Pytest local dirigido, Ruff, Mypy, GitHub CI/Gov, revisão de diff, integração na main com autorização, CI pós-merge, testes E2E comercial/IA e preflight Contabo. Para produção real: release/go-no-go, migração aplicável, aprovação de deploy, credenciais autorizadas e homologação fiscal. Expor UI premium/comercial não implica billing habilitado.

**Correção de semântica de quotas:** franquia incluída e RPM NÃO foram inseridos em CommercialPlan.periodic_quotas, pois isso bloquearia excedentes e interpretaria requisições/minuto como uso mensal. Permanecem especificações aprovadas dependentes dos medidores/limitadores canônicos; não publicar sem integração de enforcement.
