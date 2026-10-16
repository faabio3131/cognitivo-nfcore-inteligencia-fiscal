# NFV1-P05-T01/T02 — Reconciliação de fechamento, evidências e bloqueios

**Data:** 2026-10-16. **Método:** leitura de GitHub main/ledger/cronograma e Railway FM NFCORE Staging. **Sem execução de deploy, migration, segredo ou restore.** Este checkpoint prevalece sobre descrições antigas de Worker 0/1 somente no assunto recuperado; não altera o escopo das tarefas.

## T01 — Pré-deploy: critérios do cronograma

| Critério | Evidência | Classificação |
|---|---|---|
| Main CI verde | PRs posteriores com CI/Governança aprovadas, incluindo #200; main `e425f7a797be62e3496401fa0a658c8cf33b016d`, CI pós-merge #38842226036 ainda executando na leitura | CI do HEAD atual **aguarda confirmação**, não certificar |
| SHA imutável | Railway aponta `2f3689838cfbec1c6d2ffac614cb0eb364d91633` em API/Portal/Worker | **COMPROVADO** para versão publicada |
| Backup/restore | Checkpoint T01 de 12/10 registra backup `*.dump.age` e SHA256 `58ae2d97cc40f26c89900e7f349211f89770255f57427231d38ac5f8bafeded6`; restore isolado PG18 exit 0 / 34 tabelas | **EVIDÊNCIA HISTÓRICA**; não repetir, mas não presumir prova atual de recuperação operacional pós-migration |
| Migrations governadas | Histórico posterior informa migration 17 aplicada em staging; snapshot antigo registra versão 12. Não houve nesta auditoria leitura autenticada da tabela de migrations | **HISTÓRICO DE EXECUÇÃO, conferência SQL atual não comprovada** |
| Rollback baseline | Scripts e política de rollback/degraded Worker documentados em checkpoints P05; prova real de rehearsal pertence T05 | **IMPLEMENTAÇÃO/REFERÊNCIA EXISTENTE**, gate de baseline completo não revalidado nesta rodada |
| Segredos fora do Git | GSM/Worker sealed via código/PRs #176–#185 e relato de ativação. Não ler conteúdo de segredos | **CONFIGURAÇÃO RECUPERADA**, não repetir; revisão de consistência sem exposição se necessária |
| PostgreSQL saudável | Railway service Postgres ONLINE, 1/1; sem alertas no status | **COMPROVADO no plano Railway**, não equivale a SQL preflight/migrations |

**T01 conclusão formal:** `EVIDENCIA_PARCIAL_SEM_PROMOCAO`. O bloqueio antigo de Worker 0/1 **está resolvido**; o status genérico “bloqueado externo” carece qualificação. Não reabrir GSM, migration 17, backup/restore sintético ou conexão do Worker sem regressão comprovada.

## T02 — Deploy reconciliado: mesmo SHA nos três serviços

**Aceite exigido:** API, Portal e Worker publicados na mesma revisão imutável.

Leitura Railway do projeto `b84b290d-f3b4-46a1-9023-0b761cb96b0d`, ambiente `c9878b9b-62b2-4a97-b8ba-743c8a3e99ec` (nome interno `production`, projeto é staging):

- `nfcore-api`: deployment SUCCESS no SHA `2f3689838cfbec1c6d2ffac614cb0eb364d91633`; ONLINE 1/1.
- `nfcore-portal`: deployment SUCCESS no mesmo SHA; ONLINE 1/1.
- `nfcore-worker`: deployment SUCCESS no mesmo SHA; ONLINE 1/1.
- `Postgres`: ONLINE 1/1.
- Railway environment_status: zero serviços com problemas, zero failures e zero alertas ativos no intervalo consultado.

**T02 critério técnico específico: `PROVADO_NO_STAGING`**. Não refazer deploy para comprovar a mesma coisa. Entretanto **T02 não pode receber checkbox `[x]` até T01 ser formalmente certificada e o encadeamento do ledger permitir essa promoção**. É um bloqueio de governança/documentação, não de serviço offline. Smoke autenticado e jornadas Web pertencem T03/T04; não confundir.

## Rastreabilidade e retomada

- `main` na leitura: `e425f7a797be62e3496401fa0a658c8cf33b016d`; Plan Governance pós-merge #38842225832 SUCCESS; CI pós-merge #38842226036 ainda IN_PROGRESS.
- O ledger mantém 59 IDs e 27 [x] porque o validador vigente exige estado concluído como prefixo contínuo; P09-T01/T02 ainda estão abertos antes de P05. **Não inserir conclusão posterior que faça a CI falhar, nem falsificar a ordem.**
- **Próxima ação concreta:** verificar conclusão da CI main, obter somente as provas faltantes de T01 (SQL/migrations atuais, baseline e backup pós-migration quando requerido), sem recriar infraestrutura; registrar closeout quando comprovado; então promover T01/T02 na sequência autorizada pelo cronograma e ajustar validador caso a ordem aprovada permita certificações independentes.
- Estão fora deste fechamento: T03 smoke completo, T04 E2E autenticado, T05 rollback real; não marcar essas tarefas [x] por status SUCCESS.

**Regra de continuidade:** `P05_WORKER_RECOVERED = TRUE`, `P05_T02_DEPLOY_SAME_SHA = VERIFIED`, `P05_T01_ALL_GATES = NOT_YET_PROVEN`, `P05_T01_T02_CHECKBOX = NOT_PROMOTED`. Estes campos são classificação de evidência, não novos estados oficiais do validador.
