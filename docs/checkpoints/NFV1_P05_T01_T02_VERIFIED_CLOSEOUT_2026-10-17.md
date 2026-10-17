# NFV1-P05 — fechamento verificável T01 (pré-deploy) e T02 (deploy reconciliado)

**Data:** 17/10/2026.  
**Autoridade:** `faabio3131/kordena-fiscal-engine-v2`, branch `main` no commit `eef54e79310ef813a5ef62633f8dbbc5b0c68774`.  
**Escopo deste documento:** encerramento **somente** das tarefas NFV1-P05-T01 e NFV1-P05-T02 com provas previamente produzidas. Não executa novo deploy, merge, migration, backup ou homologação. O checklist global P05 continua incompleto.

## Fontes CURRENT confirmadas

- [PR #211](https://github.com/faabio3131/kordena-fiscal-engine-v2/pull/211): MERGED. Commit de merge `eef54e79310ef813a5ef62633f8dbbc5b0c68774`.
- [CI pós-merge #1012](https://github.com/faabio3131/kordena-fiscal-engine-v2/actions/runs/39059174217): SUCCESS no mesmo commit; Governança pós-merge #433: SUCCESS.
- [Issue operacional #181](https://github.com/faabio3131/kordena-fiscal-engine-v2/issues/181#issuecomment-6239191416): inventário dos deployments imutáveis, configuração staged não destrutiva, runtime/smoke básicos e ausência de migration.
- O nome **`production`** é o rótulo Railway do ambiente `c9878b9b-62b2-4a97-b8ba-743c8a3e99ec` no projeto **FM NFCORE Staging** `b84b290d-f3b4-46a1-9023-0b761cb96b0d`. **Não significa produção fiscal/comercial homologada.**

## T01 — predeploy: DONE_CERTIFIED (evidência acumulada, sem repetição)

| Critério do cronograma | Evidência |
| --- | --- |
| Main CI verde e SHA imutável | Merge PR #211, CI #1012 e Governance #433 SUCCESS no SHA `eef54e79310ef813a5ef62633f8dbbc5b0c68774` |
| Backup verificável | Backup lógico criptografado `nfcore-staging-20261017T144302Z-0437e86a.dump.age` (93522 bytes), SHA256 `b0db53883d892018b60e5de10173756084e7ec13fd5e3ef0192ae6649a12859a`; hash validado, cabeçalho PGDMP validado em memória; operador confirmou custódia externa da chave privada |
| Restauração conhecida | Ensaio isolado PostgreSQL 18 datado de 12/10: `PG_RESTORE_EXIT_CODE=0` e 34 tabelas; **não** houve ensaio independente do backup de 17/10. Não transformar a prova histórica em prova de restauração atual |
| Migrations governadas | Preflight SQL read-only fiscal versões 1–17; migrations comerciais Cakto 1 e 2 aplicadas pelo orquestrador externo, transação commitada, consulta SQL independente retornou 1 e 2; sem migration no deploy de 17/10 |
| Rollback baseline | Capturado antes da publicação com deployment IDs imutáveis e marcados `canRollback=true`; registros abaixo. **Baseline capturado não é rollback rehearsal** |
| Segredos fora do código | Secret scan/policy da CI #1012 SUCCESS; credenciais de backend e GSM já governadas e não impressas na auditoria. Não inferir homologação do provider fiscal/comercial a partir disso |
| Banco saudável | PostgreSQL Railway `Postgres` ONLINE 1/1 antes e depois do rollout, sem alteração de deployment, sem alerta crítico |

**Classificação T01:** `DONE_CERTIFIED_INTERNAL_PREDEPLOY`. Os checkpoints de 09–16/10 permanecem históricos; afirmações de que Cakto 1–2 está ausente, Worker 0/1 ou segredo GSM não configurado **não representam o CURRENT**.

## T02 — aplicação Web no mesmo SHA: DONE_CERTIFIED

| Serviço | Deployment anterior (baseline de rollback) | Deployment atual confirmado |
| --- | --- | --- |
| API | `273731b9-00e2-44dd-b10e-99b058fec7d6` | `f26d2a5e-700b-41bb-9d23-03b65d07d400` |
| Worker | `a4f48d68-3fe5-449a-9bac-37df6869b77a` | `cea783c9-b924-4565-8611-adc155f0764c` |
| Portal | `1a8f5202-0b43-4397-bcaa-ca739188f208` | `dfd82c7e-a927-4c2f-a493-f6c51df1eb2f` |

**Todos os três deployments atuais**: `SUCCESS`, 1/1 réplica, zero alertas e `meta.commitHash=eef54e79310ef813a5ef62633f8dbbc5b0c68774`.

A Railway confirmou o pacote `f2ad0040-1f5f-46b4-a75a-9b50a19b2b50` como não destrutivo, limitado aos `source.*` dos três serviços. `Postgres` manteve deployment `ce9b66e7-6de7-4c70-9852-8ca1936a719b`, ONLINE 1/1. Nenhuma variable, volume, DNS, TLS ou migration de banco foi modificada no rollout.

O CLI estava autenticado, mas `RAILWAY_API_TOKEN` não estava disponível no executor local. Portanto, a publicação utilizou o mecanismo nativo de stage/apply da Railway, **não** o wrapper `run_staging_deploy.sh`, cuja sequência incluiria `migration_guard.py --apply`. Não houve bypass de teste: os gates de CI pós-merge foram concluídos previamente e a revisão do SHA foi verificada após o rollout.

**Classificação T02:** `DONE_CERTIFIED_STAGING_SAME_SHA`.

## T03–T05 — pendências preservadas (não ocultar)

- **T03 Smoke:** evidência parcial: API `/health/live` 200, `/health/ready` 200, `/runtime/profile` 200; Portal `/` 200; `GET /v1/portal/bootstrap` anônimo 401 (fail-closed). O `/health` do host do Portal retornou 404 e **não foi provado contrato de readiness nesse caminho**. Faltam login, recovery, bootstrap autenticado e onboarding contra a versão publicada; smoke API+Portal parcial não prova toda a tarefa.
- **T04 E2E real:** não certificado no staging Web publicado. A CI #1012 passou testes internos de PostgreSQL, autenticação, RBAC/tenant e Playwright, **mas isso não substitui a homologação/certificação externa**. O proprietário determinou que testes/homologações externas fiquem para a fase final de construção.
- **T05 Rollback rehearsal:** os três IDs de rollback e a capacidade `canRollback=true` foram verificados, mas **não foi executado rollback real**. Exige procedimento governado e aprovação quando cabível; não repetir deploy como substituto de rehearsal.
- **Gate P05 global:** ainda NÃO certificado; não registrar `P05 DONE`, `PRODUCTION_APPROVED` ou `COMMERCIAL_LIVE`.

## Governança e próxima ação

1. O ledger avança de **30/59 para 32/59 tarefas concluídas**, preservando os 59 IDs e a ordem canônica. Próxima tarefa formal: **NFV1-P05-T03**.
2. A decisão de priorizar conclusão interna do produto permanece em vigor; não executar homologação fiscal, faturamento externo ou operações reais apenas para completar checkbox.
3. Não reabrir T01/T02 sem evidência de regressão. [PR #204](https://github.com/faabio3131/kordena-fiscal-engine-v2/pull/204) contém registros pré-migration Cakto superados e não deve ser integrada sem reconciliação.
4. Este fechamento documental precisa de validação do cronograma, revisão e CI da própria PR antes de ser incorporado à `main`. Não fazer merge automático sem autorização do proprietário.
