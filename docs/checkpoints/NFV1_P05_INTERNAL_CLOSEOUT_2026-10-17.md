# NFV1-P05 — Gate de fechamento interno e candidata Web unificada

**Data:** 2026-10-17
**Fonte canônica:** repositório `faabio3131/kordena-fiscal-engine-v2`
**Base auditada:** `main=976ae4e223accd603af710d083b18ca47b95b614`, CI #1007 SUCCESS, Governança #428 SUCCESS.
**Branch candidata:** `feat/nfv1-p05-controlled-development-wiring-20261017` (PR #211).
**Ambiente-alvo posterior:** projeto Railway `b84b290d-f3b4-46a1-9023-0b761cb96b0d`, ambiente `c9878b9b-62b2-4a97-b8ba-743c8a3e99ec`, uso governado **staging** apesar do nome Railway `production`.

## Escopo deste fechamento — sem alteração de dados reais

Não criar outro runtime, outro provedor comercial, outra autoridade de sessão/tenant/unidade, outra infraestrutura de migrations nem frontend paralelo. Unificar as evidências já existentes e acrescentar testes integrados que exercem os contratos atuais:

1. **Trial/Portal/Worker, PostgreSQL descartável:** assinatura S2S de trial, trial provisionado, replay idempotente, reset e login humano, portal bootstrap, enfileiramento de outbox e dispatch por Worker canônico de operação sintética sem I/O externo. Verificar persistência única e estado final sem alterar a autorização fiscal.
2. **Command/Portal, PostgreSQL descartável:** aquisição comercial assinada, evento Command autenticado, recibo/idempotência, claim governado, ativação e entrega sintética, reset/login e Portal bootstrap. Confirmar unicidade do cliente, assinatura e purchase.
3. **Frontend/API/Worker:** manter `npm run lint:frontend`, `typecheck:frontend`, `test:frontend`, `build:frontend`, `test:e2e`; Python lint, mypy e pytest no Linux com PostgreSQL real; builds/smoke de imagens API/Worker/Portal sem credenciais reais. São executados pelo **workflow CI existente**, sem segundo workflow.

O teste de integração é sintético **somente no canal de ingresso**; o PostgreSQL, as tabelas canônicas, a autenticação, os contratos HTTP e o Worker são reais no runtime de teste. Não equivale a emissão fiscal oficial, pagamento real ou homologação externa.

## Candidate release (não publicar automaticamente)

- Revisão de referência: **HEAD imutável da PR #211 após aprovação da CI remota e revisão humana**.
- API, Worker e Portal devem ser construídos e implantados do **mesmo SHA**. A imagem do Portal pode ter delta de código zero em `portal/`, mas a revisão de release ainda precisa coincidir.
- O driver canônico `scripts/deploy/drivers/railway.sh` já captura baseline imutável de rollback, valida SHA do checkout e verifica o Worker por deployment/revision/réplicas. **Não duplicar essas rotinas.**
- Após deploy autorizado, verificar `/health/live`, `/health/ready`, `/runtime/profile`, `/v1/portal/bootstrap` com sessão de teste e Worker running. Testes externos e homologação real ficam para a fase final aprovada.
- Provas de banco anteriores: schema fiscal 1..17 e Cakto 1..2 conferidos por SQL independente, backup criptografado de 17/10 e restore histórico de 12/10. Não repetir restore apenas para atualizar papelada; manter plano de proteção proporcional a operações mutáveis.

## Estados separados (não converter Target em Current)

| Critério | Estado até CI desta candidata |
| --- | --- |
| Wiring fiscal read-only sintético e Command dev/test | IMPLEMENTED_BRANCH #211 |
| Testes locais Web sessão/RBAC/CSRF/tenant | PASS 21 + regressão de Portal; CI #1009 SUCCESS na revisão anterior |
| Novos cenários comerciais PostgreSQL + Worker | IMPLEMENTED_TEST_PENDING_CI na revisão nova |
| Gates integrais CI e governança no novo HEAD | PENDING_RECHECK |
| API/Worker/Portal publicados com mesmo SHA | PENDING_DEPLOY_APPROVAL |
| T03/T04 Web staging e T05 rollback rehearsal | PENDING_DEPLOY / fases de certificação |
| Homologações fiscais, cobrança e integrações externas | DEFERRED_BY_OWNER; obrigatórias antes de Go/No-Go |

**Condição de encerramento da construção interna desta candidata:** CI Linux/PostgreSQL completa SUCCESS + Governança SUCCESS no mesmo commit + ausência de blockers funcionais internos descobertos. Isso **não** certifica o estado implantado nem altera as 59 marcações do cronograma automaticamente.
