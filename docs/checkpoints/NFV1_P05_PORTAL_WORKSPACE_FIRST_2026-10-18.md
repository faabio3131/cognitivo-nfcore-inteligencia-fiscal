# NFV1-P05 — Workspace-first portal layout — 2026-10-18

**Estado:** implementação e testes locais; CI remota da PR pendente até sua conclusão.
**Repositório canônico CURRENT:** `faabio3131/nf-core-v001` (renomeado do caminho histórico `faabio3131/kordena-fiscal-engine-v2`, mantendo o mesmo repositório).
**Base auditada:** `main 84bde1429fe50f2f3eeb20c61448ee8692e4886e` (PR #215 de identidade premium já integrada); CI #1022 e Governança #443 SUCCESS na base.
**Branch:** `fix/nfv1-portal-workspace-first-20261018`.

## Problema comprovado e Current → Target

Capturas reais do operador demonstraram que os blocos institucionais fixos do `portal/index.html` — banner de marca e faixa EMIT/CONTROL/TRACE/SCALE — reapareciam antes das ferramentas em Documentos, Emissões, Onboarding, Unidades e outras superfícies, exigindo rolagem e confundindo navegação. O backend e a sessão estavam funcionando (P05), não sendo necessário recriar funcionalidades.

**Target aprovado pelo proprietário:** preservar banner institucional completo somente em `Visão geral`; mostrar imediatamente conteúdo funcional em todas as demais páginas; conservar proteção e avisos de readiness em todas as rotas.

## Mudança única e reversível

- `portal/app.js`: aplica/remover a classe `is-operational-view` no mesmo `app-shell` ao mudar a rota já existente, reposiciona rolagem do documento no início apenas ao trocar de módulo, e restaura layout de overview ao reconstruir a sessão. Sem alteração de contratos API, autenticação, autorização/RBAC, escopo tenant/unidade, fiscal ou persistência.
- `portal/styles.css`: oculta somente `.product-banner` e `.mission-strip` nas rotas operacionais; mantém `#critical-state` exibido e em formato compacto para preservar avisos `BLOCKED_EXTERNAL` e `HUMAN_APPROVAL_REQUIRED`. Mantém logo/branding aprovado no overview.
- `tests/e2e/portal.spec.js`: regressão automatizada de navegação nas resoluções 320/390/1280 px; testa overview visível, 5 módulos funcionais sem hero, conteúdo acima da dobra, readiness persistente e retorno ao overview. Fixture é explicitamente sintética, não homologação fiscal nem login real.

## Gates e critérios de aceite

- Local: `npm run lint:frontend` PASS; `npm run typecheck:frontend` PASS; `npm run test:frontend` 14 PASS; `npm run build:frontend` PASS; `python scripts/check_nfcore_plan.py` PASS (59 tarefas, próxima P05-T03), `git diff --check` PASS.
- E2E local: Google Chrome via Playwright e servidor HTTP exclusivamente loopback, com respostas sintéticas (sem fornecedor externo): **3 PASS / 0 FAIL** nas resoluções **320px, 390px e 1280px**, cobrindo cinco módulos, segurança visível, painel acima da dobra e retorno ao overview. Executado sem cookies reais nem contato com staging.
- Gates obrigatórios da candidata: CI Linux/PostgreSQL, lint/typecheck/build frontend, E2E navegador, segurança, containers e Governança no SHA exato. Não reutilizar CI #1022 da base como prova da nova alteração.

## Limites e decisões

Sem criar outro frontend, outra API ou autoridade de segurança. Aviso de bloqueio nunca pode ser escondido por CSS. Sem migração, deploy, segredo, alteração no staging, homologação externa ou merge não aprovado. P05-T03/T04/T05 permanecem pendentes quanto às provas funcionais/externas documentadas, independente da aprovação deste refinamento de UI.

**Próxima ação:** registrar commit, abrir PR Draft e executar CI/Governança; solicitar autorização específica para merge. Após merge autorizado, exigir CI/Governança pós-merge e autorização de deploy antes de alterar Web público.
