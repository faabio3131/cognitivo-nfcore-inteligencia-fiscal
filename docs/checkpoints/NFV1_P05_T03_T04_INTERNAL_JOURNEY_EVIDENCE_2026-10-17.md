# NFV1-P05 — T03 controles internos e T04 cobertura integrada inicial

**Data:** 2026-10-17
**Repositório:** `faabio3131/kordena-fiscal-engine-v2`
**Base CURRENT verificada:** `main=0497f3df36faf8894c94364a413e90ca8351be20`; PR #213 MERGED; CI pós-merge #1016 SUCCESS e Governança #437 SUCCESS no mesmo SHA.
**Branch:** `test/nfv1-p05-t03-t04-internal-http-matrix-20261017`.

## Current → Target e escopo congelado

O código existente já possui recuperação de senha, login/logout por cookie, validação CSRF, autoridade canônica de tenant/unidade, onboarding de trial, Portal Web e Worker/outbox PostgreSQL. O script de smoke aprovado na PR #213 já cobre `GET /v1/portal/bootstrap` sem sessão (esperado 401). Não criar segunda autenticação, persistência ou runtime.

**T03 — extensão integrada interna:** adicionado teste sobre a composição **PostgreSQL canônica** com trial assinado sintético, provisionamento, ativação por token de recuperação, login, `/v1/auth/me`, bootstrap autenticado, recusa de logout sem CSRF, logout com CSRF e revogação de sessão. Reutiliza fixtures e serviços existentes.

**T04 — próximo trabalho interno iniciado:** adicionado teste sobre a **mesma jornada comercial PostgreSQL**: perfil do proprietário provisionado, confirmação de que trial não cria unidade por efeito implícito, onboarding explícito de unidade pela operação HTTP canônica, consulta à superfície de unidades do Portal, bloqueio de operação sem CSRF (403), rejeição de tenant forjado na requisição (400) e bloqueio de unidade não cadastrada pelo registro canônico (409), com `fiscal_production_activated=false`. Nenhuma operação fiscal nem pagamento real é acionado.

O recorte modifica somente `tests/runtime/test_nfv1_p05_internal_postgres_closure.py`, mais este checkpoint. O teste existente da mesma suíte já percorre trial → autenticação → Portal → Worker/outbox e Command assinado → claim → ativação; a CI principal já executa frontend, navegador e containers. A execução das jornadas externas permanece diferida conforme decisão humana.

## Gates e evidências

- CI pós-merge #1016 e Governança #437 **SUCCESS** sobre a main anterior à nova candidata.
- **Execução local confirmada:** PostgreSQL 18 descartável em `127.0.0.1:65432`, schema/migrations de teste da fixture canônica: `pytest tests/runtime/test_nfv1_p05_internal_postgres_closure.py` **4 PASS / 0 FAIL**, incluindo dois testes novos T03/T04 e os dois cenários anteriores. `Ruff check` e `ruff format --check` PASS; `scripts/check_nfcore_plan.py` PASS (59 IDs, próxima P05-T03). O banco local foi encerrado e removido após a execução. Nenhuma instância ou dado da Railway foi acessado.
- A CI da PR deve repetir a suíte completa em Linux/PostgreSQL 16 e comprovar os novos casos no HEAD exato; não contar apenas checks históricos.

## Classificação e riscos

**Não marcar P05-T03 ou P05-T04 como DONE_CERTIFIED por estes testes internos.** O cronograma exige smoke completo e E2E real no staging publicado; o Web runtime Railway continua na revisão anterior `eef54e7`, embora a main esteja em `0497f3d`. Testes e homologações fiscais/comerciais externos ficam para a fase final, mas segurança interna não é dispensada.

Não executar novo deploy, merge, migration, backup, DNS, billing, certificados ou segredos produtivos neste recorte. O ambiente Railway possui o nome técnico `production`, mas a finalidade aprovada do projeto é staging, sem produção comercial homologada.

**Próxima ação depois dos gates:** revisão e aprovação humana específica para integrar a candidata; continuar P05-T03/T04 apenas quanto aos requisitos internos ainda não comprovados. P05-T05 rollback rehearsal permanece uma etapa distinta e não concluída.
