# NFV1-BLD-03 — Provisionamento governado do ingresso público de trial

**Estado de construção:** rota pública, catálogo de ofertas, ativação por e-mail e limitador PostgreSQL implementados na PR #234. A integração com a página do site está na PR #12 de `faabio3131/fm-site-novo`. A ativação Web e a homologação externa **não estão certificadas**.

## Autoridade única

- API: `/v1/public/trial-plans` (leitura estrita do catálogo FM publicado) e `/v1/public/trials` (chama `GovernedTrialService.begin`).
- Trial, customer, identidade, owner, subscription, tenant e plano continuam sob o mesmo núcleo transacional. O formulário não fornece nem escolhe identidades de tenant.
- Ingresso S2S pré-existente `/v1/commercial/trials` permanece autenticado por HMAC, **independente** do ingresso browser.
- O cadastro público é habilitado somente quando o operador configura `NFCORE_PUBLIC_TRIAL_ALLOWED_ORIGINS` com as origens HTTPS exatas, separadas por vírgulas (por exemplo `https://fmtecnologiaia.com.br`), e a entrega de ativação está operacional. A variável não deve ser ativada antes da revisão do runtime e do schema.
- URL de API comprovadamente alocada no Railway staging: `https://nfcore-api-production.up.railway.app`. Não significa que a rota de trial já esteja publicada.

## Persistência antiabuso necessária (SQL preparado — NÃO APLICADO)

A operação precisa de uma tabela durável, compartilhada por todas as réplicas PostgreSQL. O algoritmo no módulo `runtime/public_trial_abuse.py` faz um incremento atômico por chave hash + janela, por meio de `INSERT ... ON CONFLICT DO UPDATE ... WHERE hits < limite RETURNING hits`. Uma resposta inexistente ou falha de banco **nega** a admissão. O IP remoto vem da conexão ASGI, não de headers forjáveis.

SQL a governar como migração aditiva, sob aprovação específica para ambiente e banco:

```sql
CREATE TABLE fm_public_trial_rate_windows (
    scope_key TEXT NOT NULL,
    window_start BIGINT NOT NULL,
    hits INTEGER NOT NULL CHECK (hits >= 1),
    PRIMARY KEY (scope_key, window_start)
);
```

Este SQL está **preparado, mas não foi aplicado nem integrado ao registry de migrations**. Até essa etapa, requests públicos falham em modo seguro. Registrar também limpeza governada de janelas antigas, métrica 429, limites por origem/rede e proteção de borda (WAF/CAPTCHA quando aplicável) antes da disponibilidade pública.

## Ordem do gate de lançamento

1. CI/Gov verde no SHA exato da PR #234, merge autorizado BUILD-ONLY e CI pós-merge.
2. Homologar o schema como migration controlada e aplicar somente após aprovação específica. Nunca executar DDL no boot da API.
3. Publicar um catálogo habilitado de planos, preços e períodos de trial por autoridade FM (decisão humana de comercialização).
4. Configurar a entrega de ativação, `NFCORE_PUBLIC_TRIAL_ALLOWED_ORIGINS=https://fmtecnologiaia.com.br`, e atestar isolamento de tenant/RBAC; autenticar/travar acesso de borda, observabilidade e quotas.
5. Deploy de staging sob autorização específica, navegador contra API, corrida/idempotência, email real, rate-limit entre réplicas, teste de indisponibilidade de DB, sem chave HMAC browser.
6. Liberar site PR #12 e produção somente após revisão de disponibilidade, DNS/TLS e autorização específica.

**Não confundir BUILD interno integrado com trial comercial ativo.**
