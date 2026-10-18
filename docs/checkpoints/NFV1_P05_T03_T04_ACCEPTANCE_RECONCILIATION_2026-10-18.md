# NFV1-P05 — reconciliação de aceite T03 e preparação T04 (18/10/2026)

## Autoridade e escopo

- Repositório CURRENT: `faabio3131/nf-core-v001` (caminho anterior redirecionado).
- Base desta candidata: `main 59ae95a43b0cddc42ad9b044feed3dc7fb67aca3`; CI pós-merge #1028 SUCCESS, Governança #449 SUCCESS.
- Fontes persistentes: `docs/NFCORE_V1_COMPLETION_MASTER_EXECUTION_SCHEDULE_2026-10-05.md`, `docs/NFCORE_V1_EXECUTION_LEDGER.md`, `docs/checkpoints/NFV1_P05_T01_T02_VERIFIED_CLOSEOUT_2026-10-17.md` e Issue operacional #181.
- Sem alteração de código, serviço, segredo, banco, migração, autenticação, hostname ou política. Não confundir execução interna com homologação fiscal ou produção comercial.
- Decisão do proprietário: deixar processamento real dependente de integrações externas para o encerramento comercial; manter esse gate explicitamente pendente, sem falsificar evidência.

## Evidências verificadas; NÃO repetir sem regressão

| Escopo | Evidência objetiva | Classificação |
| --- | --- | --- |
| T01 / T02 | Checkpoint certificado; backup/migration e deploy governados | DONE_CERTIFIED, não reabrir |
| Smoke anônimo | Script canônico `scripts/ci/staging_smoke.sh`, PASS exit 0; HTTPS, live/ready/profile, Portal raiz, bootstrap anônimo 401; registrado na Issue #181 em 17/10 | PASS para revisão implantada no ensaio |
| Sessão Web | Logout 204, login 200, bootstrap autenticado 200 em sequência na API, 18/10 01:24 UTC; Issue #181 | PASS |
| Unidade Web | Capturas do operador + GET `/v1/portal/surfaces/units` 200, consulta PG read-only no tenant de teste `nfcore-staging-e2e` confirmou unidade preexistente `pilot-gsm-staging` | PASS existência, persistência e leitura; não provar POST novo |
| Recuperação de senha | Operador recebeu e-mail do NFCore; Railway API: `POST /v1/auth/password-reset/request` 202 em 16:57:09 UTC, `/complete` 204 em 16:58:19 UTC e `/login` 200 em 16:58:35 UTC, 18/10 | STAGING_PASSWORD_RECOVERY_END_TO_END_PROVEN |
| PostgreSQL / isolamento | PR #214 CI #1017 e pós-merge #1018, 2.375 Pytest PASS e 28 E2E Playwright PASS; incluem criação da unidade por `onboardUnit`, CSRF, tenant estrangeiro negado e recuperação | CERTIFIED_INTERNAL_TEST |
| Worker / outbox | Railway 1/1; 100 ciclos `claimed=0`, `succeeded=0`. SQL `SELECT COUNT(*) FROM fm_fiscal_outbox` em transação read-only retornou 0; tabelas `fm_fiscal_outbox` e `fm_fiscal_outbox_ordering` existem | WORKER_RUNNING; EXTERNAL_DISPATCH_NOT_PROVEN |
| Disponibilidade atual | Portal/API/Worker/Postgres 1/1 ONLINE, sem alertas; GitHub main CI #1028 e Governance #449 SUCCESS | OPERATIONAL_HEALTH_PASS |

## T03 — decisão de aceite disciplinada

**Comprovados**: liveness/readiness, proteção de bootstrap, login/logout, recuperação de senha real e leitura/persistência de unidade; Worker rodando com PostgreSQL, sem fila pendente.

**Não demonstrados**: uma execução de `onboardUnit` em staging na versão publicada e uma entrega/dispatch real de Worker a destino externo governado. A segunda foi diferida expressamente pelo proprietário; não bloquear a construção interna das fases seguintes, mas manter o gate final de P05 em aberto.

**Status P05-T03:** `PARTIAL_OPERATIONAL_CERTIFIED`; **NÃO** marcar DONE no ledger enquanto o critério integral do cronograma não estiver satisfeito. A consulta de unidade existente não equivale à sua criação.

## T04 — matriz de trabalho sem duplicação

| Jornada requerida | Prova existente / próximo trabalho | Classificação |
| --- | --- | --- |
| Login, unidade, recuperação | HTTP staging + banco + captura, acima | PARTIAL_LIVE_VERIFIED |
| Configuração e RBAC | Testes do codebase e gates remotos já aprovados; não equivalem a operação autenticada de configuração em staging | INTERNAL_CERTIFIED / LIVE_PENDING |
| Isolamento tenant/unidade e CSRF | Teste real de integração em PostgreSQL descartável, PR #214; sem tenant estrangeiro real em staging | INTERNAL_CERTIFIED / LIVE_PENDING |
| Jornada fiscal controlada | Sem homologação oficial, provider real ou autorização de emissão externa | DEFERRED_EXTERNAL |
| Jornadas comerciais | Fluxos internos PostgreSQL/Command/trial/Worker certificados anteriormente; prova de pagamento/provider real ainda depende de insumo externo | INTERNAL_CERTIFIED / DEFERRED_EXTERNAL |
| Recuperação operacional | Recuperação de senha comprovada; rollback real continua T05 separado | PARTIAL_LIVE_VERIFIED |

Não criar segunda API/UI/autenticação, conta, unidade ou outbox só para elevar status. A preparação documental de T04 é permitida, mas a task T04 depende de T03 formalmente concluída. Trabalho interno adicional só pode avançar sem marcar gate ou task prematuramente.

## Gate P05 geral — impede declaração de conclusão

1. `API SHA == Portal SHA == Worker SHA == SHA certificado`: **NOT MET** na leitura corrente. API e Worker `19cf767de1be75009783054356ffcb7c14d2e975`; Portal `59ae95a43b0cddc42ad9b044feed3dc7fb67aca3`. A diferença isolada não comprova regressão, mas exige reconciliação/rollout governado posteriormente.
2. Worker running > 0: **MET**, 1/1.
3. E2E no runtime alvo atual: **NOT FULLY MET**.
4. Rollback provado: **NOT MET**, baselines anteriores não são rehearsal.
5. Evidências persistidas: **PARTIAL**.

**Próxima atividade interna sem retrabalho:** revisar e reutilizar os testes já existentes da matriz T04, detectar lacunas que possam ser demonstradas de forma sintética em CI sem mudar contratos. Deixar as operações reais de provider, pagamento e fiscal para autorização na etapa final e o rehearsal T05 para operação governada própria. Nenhum merge, deploy ou avanço do checkbox `NFV1-P05-T03` apenas por esta documentação.
