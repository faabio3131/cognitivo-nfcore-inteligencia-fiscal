# NFV1-BLD-00 — Auditoria reconciliada de construção e integração Web

**Data da verificação:** 19/10/2026 UTC.  
**Classificação:** AUDITORIA READ-ONLY / CANDIDATA PARA ACEITE BLD-00, não homologação e não autorização de deploy.  
**Repositório canônico:** faabio3131/nf-core-v001. **CURRENT main auditado:** f7ae59cb6fee448c9aebb96f3cb5da39dc7d2119.  
**Gates dessa main:** CI #1059 SUCCESS; Governança #480 SUCCESS.  
**Site institucional correto:** faabio3131/fm-site-novo main f2f995bed15cc371fcfb4ccb09d1e321ff209f8a, site CI #4 SUCCESS.

## 1. Reconciliação — auditoria anterior NÃO perdida

- A PR #189, OPEN/DRAFT, commit 2b512b0b975e567839a0f883b0bbf0c8474d0b40, contém `docs/checkpoints/NFV1_FULL_WEB_CODE_RUNTIME_PARITY_2026-10-15.md`: matriz interna valiosa, **mas não mergeada**. Não mergear seu AGENTS.md histórico por conveniência: conflitante com o CURRENT.
- O checkpoint **já integrado** `docs/checkpoints/NFV1_WEB_PARITY_AND_FUNCTIONAL_INTEGRATION_2026-10-18.md` revisou unidades adicionais, consulta archive e detalhes de projeções comerciais. As correções descritas constam no Portal da main auditada. **Não implementar novamente**.
- PR #225 (merge f7ae59cb6fee448c9aebb96f3cb5da39dc7d2119) aprovou anexo BUILD-ONLY, `AGENTS.md`, ledger e validador; só governa construção, não publica funcionalidades nem encerra homologação.
- PR #182 (alternância visual de senha), #188 (instrumentação anterior), #201 (proteção counters), #204/#205 e #165 continuam DRAFT, não mergeadas. Antes de usar qualquer uma: diff atual versus main, testes e delta restante. Nenhuma é automaticamente predecessora de BLD-01/02.
- Últimos checkpoints certificados P05-T01/T02: deploy e recuperação prévia; backup/restauração isolados já comprovados. **Não repetir e não bloquear BUILD com P09-T04**.
- A matriz abaixo é uma reconciliação de **código + contrato + configuração runtime + evidência anterior**. Não houve login com sessão administrativa nesta auditoria; ausência de E2E autenticado CURRENT é lacuna de prova, não prova de falha.

## 2. CURRENT real do staging: código != serviço operacional

Projeto Railway: FM NFCORE Staging, project b84b290d-f3b4-46a1-9023-0b761cb96b0d, environment c9878b9b-62b2-4a97-b8ba-743c8a3e99ec (nome da Railway `production`, **NFCORE_ENVIRONMENT=staging**). Serviço nfcore-api, nfcore-portal, nfcore-worker e Postgres: ONLINE 1/1 cada. Isso é disponibilidade de infraestrutura, não capacidade comercial/fiscal.

GET público real de `/runtime/profile` e `/v1/commercial/offer`, em 19/10:
- Configurado: `persistence_backend=postgres`, `human_identity_configured=true`, `portal_executor_configured=true`, `bridge_security_configured=true`, `bridge_executor_configured=true`, `password_recovery_configured=true`, `password_reset_delivery_configured=true`, `commercial_fulfillment_configured=true`, `commercial_provisioning_configured=true`, `commercial_activation_configured=true`, `commercial_delivery_path_ready=true`.
- Fiscal: `fiscal_operation_handlers_configured=["queryArchiveReference"]`; `fiscal_provider_transport_real_configured=false`, `fiscal_runtime_external_execution_ready=false`, `fiscal_production_activated=false`.
- Comercial: `commercial_trial_configured=false`, `commercial_first_party_acquisition_configured=false`, `commercial_checkout_processing_configured=false`, `commercial_checkout_provider_configured=null`, `pricing_catalog_published=false`, `commercial_release_status=unavailable`.
- Oferta externa: `trial_enabled=false`, `purchase_enabled=false`.
- **Drift de revisão:** Railway API `config.source.commitSha=44cddbabb4e91b55dcc730e6976fcc2ce7f00d75`; Worker `config.source.commitSha=19cf767de1be75009783054356ffcb7c14d2e975`; Portal último deployment SUCCESS mas sem SHA fonte imutável retornado. Não declarar API/Worker/Portal sincronizados no SHA da main, nem reimplantar sem autorização.
- Railway possui **patch staged não aplicado** ID c8222d45-669d-436c-893c-eb6c5a2648ad, **somente para API**, com source e referências GSM/opt-in comercial. NÃO aplicar patch automaticamente nesta auditoria; o modo comercial deve permanecer fail-closed até binding administrativo autenticado comprovado.
- No relatório anterior o perfil fiscal não tinha handlers; agora `queryArchiveReference` está configurado. Esse delta já está em código e **não deve ser reproduzido**.

## 3. Matriz exaustiva de navegação: 26 áreas, código → UI → API → autoridade → estado

Legenda: **WIRED_CODE** = ligação codificada, não prova de jornada autenticada atual; **READ_ONLY** = projeção consultiva deliberada; **BLOCKED_RUNTIME** = UI/serviço implementados, dependência não disponível; **DEFERRED_EXTERNAL** = emissão, provider/pagamento/homologação reais; **GAP_CODE** = funcionalidade V1 necessária sem ingresso Web seguro implementado.

Autoridade de acesso: `web/portal_api.py` mapeia 22 superfícies em `_SURFACE_PERMISSIONS` e 14 comandos `_OPERATION_PERMISSIONS`; a UI contém 26 entradas agrupadas (6 Operação, 8 Configuração e 12 Plataforma). As quatro superfícies especiais — `pricing-admin`, `commercial-release`, `checkout-admin`, `webhook-egress` — usam routers próprios. `_authenticated`, `_authorized`, `_csrf`, `_reject_browser_authority` e exigência de idempotência pertencem **ao servidor**, nunca à UI. A navegação consulta `/v1/portal/bootstrap` e `/v1/portal/surfaces/{surface_id}`.

| # | Superfície/ação V1 | Caminho / autoridade única | Estado BUILD no CURRENT |
|---|---|---|---|
| 01 | Visão geral/readiness | Portal overview → `/v1/portal/bootstrap` → `DurableHumanPortalExecutor.snapshot`; `portal.read` | WIRED_CODE, readiness não certifica operações externas |
| 02 | Documentos/listagem | Portal documents → `GET /v1/portal/surfaces/documents` → lifecycle/archive por tenant/unidade | READ_ONLY/WIRED_CODE |
| 03 | Arquivo por referência | Mesmo Portal → `POST /v1/portal/operations/queryArchiveReference` → `FiscalArchiveStore`/handler configurado | WIRED_CODE interno; NÃO refazer correção já integrada |
| 04 | Emissões | Portal issuances e fiscal intents → `issueFiscalDocument`/CanonicalFiscalOperationPath; `document.issue` | UI/intent WIRED_CODE; handler indisponível em staging; operação oficial DEFERRED_EXTERNAL |
| 05 | Inutilização | Portal inutilizations + form/intent/outbox → `inutilizeFiscalRange`; `document.inutilize` | UI/intent WIRED_CODE; handler externo BLOCKED_RUNTIME |
| 06 | Erros | Portal errors → superfície lifecycle ERROR/REJECTED | READ_ONLY/WIRED_CODE, sem invocar provider |
| 07 | Reconciliação | Portal reconciliation → projeção + `reconcileFiscalOperation` com permissão server-side | READ_ONLY; execução fiscal BLOCKED_RUNTIME |
| 08 | Onboarding | Portal onboarding + `onboardUnit` → Control Plane/PG, escopo de sessão | WIRED_CODE e provas anteriores de onboarding; não reconstruir |
| 09 | Empresas | Portal companies → projeção de organização do tenant no PG | READ_ONLY conforme UI; não declarar CRUD de empresas implementado sem escopo |
| 10 | Unidades | Portal units + `onboardUnit` para unidades adicionais → Control Plane, CSRF/idempotência | WIRED_CODE; melhoria 18/10 já na main |
| 11 | Ambientes | Portal environments → registros escopados da unidade | READ_ONLY/configuração governada; seleção na UI não promove produção |
| 12 | Capacidades | Portal capabilities → CapabilityReadinessService/consulta escopada | READ_ONLY; provider real diferido |
| 13 | Certificados | Portal certificates + `configureCertificates` → CommercialConfigurationService/refs | WIRED_CODE cadastro de referência, não material fiscal |
| 14 | Providers | Portal providers + `configureProviders` → bindings governados | WIRED_CODE cadastro, adapter real desligado |
| 15 | Usuários | Portal users + `createUser`/`updateUser` → HumanAdministrationService | WIRED_CODE; auth/RBAC/tenant servidor, evidência interna anterior |
| 16 | Webhooks | Portal webhooks + `configureWebhooks` → configuração durável/outbox | WIRED_CODE configuração; despacho externo DEFERRED_EXTERNAL |
| 17 | Aprovação de egress | Portal webhook-egress → `/v1/portal/egress/{tenant_id}/{unit_id}/{environment}/{destination_id}` → platform authority | WIRED_CODE; admin humano autentica/autoriza, tenant não autoaprova |
| 18 | Integrações | Portal integrations + `configureIntegrations` → configuração governada e bindings | WIRED_CODE cadastro; não indica webhook externo ativo |
| 19 | Uso | Portal usage → CommercialPortalReadService/PG | READ_ONLY/WIRED_CODE |
| 20 | Billing | Portal billing → CommercialPortalReadService/PG | READ_ONLY/WIRED_CODE; operação real de gateway diferida |
| 21 | Planos do cliente | Portal plans → CommercialPortalReadService/PG | READ_ONLY/WIRED_CODE |
| 22 | Catálogo/preços da plataforma | Portal pricing-admin → `GET/POST /v1/admin/pricing` → PricingAdministrationService (platform_admin/CSRF) | WIRED_CODE admin; `pricing_catalog_published=false` depende decisão de preço |
| 23 | Segredo trial admin | Botão na pricing-admin → `POST /internal/staging/commercial-trial-binding` → SecretBindingAdministration | WIRED_CODE; binding efetivo ainda **não certificado**, depende da sessão humana |
| 24 | Liberação comercial | Portal commercial-release → `GET/POST /v1/admin/commercial-release` → ReleaseAdministrationService | WIRED_CODE; `commercial_release_status=unavailable` decisão comercial humana |
| 25 | Checkout canais | Portal checkout-admin → `/v1/admin/checkout/cakto` → administração condicional | UI/serviço parcial; provider null, checkout processing false; BLOCKED_RUNTIME |
| 26 | Auditoria | Portal audit → control-plane events escopados | READ_ONLY/WIRED_CODE |
| 27 | Suporte | Portal support → projeção de suporte/escopo e aviso de SLA ainda não certificado | READ_ONLY; **não** alegar ticketing/SLA/suporte comercial ativo |
| 28 | Configurações | Portal settings + `configureSettings` → política versionada | WIRED_CODE, não ativa transporte fiscal real |

**Contagem de navegação:** há **26 botões** e **28 linhas nesta tabela**, porque a consulta ao archive (#03) e o registro de segredo do trial (#23) são **ações dentro de páginas**, não páginas extras. Não usar 28 como contagem de áreas.

Ações sem página própria:
- Login/logout, redefinição por e-mail e ativação: `/v1/auth/*`, HumanIdentityService/PasswordRecovery; Web/P05 já possuem evidências reais de login e reset; **não refazer**.
- Consulta fiscal (`queryFiscalDocument`) e cancelamento (`cancelFiscalDocument`) compartilham módulo fiscal/intent; handlers não configurados em runtime. Nenhum resultado fiscal oficial pode ser inventado.
- `createUser`/`updateUser`, onboardUnit, configurações, fiscal-intent prepare/resume e plataforma comercial têm autenticação e grants próprios; não criar autenticação duplicada.

## 4. Cadeia não navegacional — site público → ingresso → serviço → persistência/Worker

| Jornada | Autoridade já construída | O que funciona em CURRENT | Delta demonstrável |
|---|---|---|---|
| Acesso Portal | `fm-site-novo` /entrar → Portal Railway → auth humano NFCore | Link do site após PR #10, site CI #4; runtime identity true | Sem alteração de código comprovadamente necessária; não certificar cada papel por GET anônimo |
| Trial / avaliação | `GovernedTrialService`, `web/commercial_trial.py` (`POST /v1/commercial/trials` **S2S assinado**), tenant/OWNER/subscription/activation PostgreSQL; patch GSM | Código interno + binding admin GUI na main; staging `commercial_trial_configured=false`, oferta `trial_enabled=false` | **GAP-WEB-01:** site estático `fm-site-novo` tem `signupUrl=null`, não tem jornada de cadastro. Construir ingresso público protegido usando **APIs/sessão existentes** ou canal Command S2S aprovado; assinatura nunca no browser. Configurar binding com admin legítimo, sem SQL bypass. Catálogo/trial_days decisão humana |
| Aquisição first-party | `CommercialAcquisitionService`, `POST /v1/commercial/acquisitions`, fulfillment/provisioning/PG | Serviços internos true, ingress `commercial_first_party_acquisition_configured=false` | **GAP-COM-01:** compor canal autorizado sem segundo checkout, preservando assinatura/idempotência; pagamento externo diferido |
| Checkout / purchase | Pricing + Release + checkout projector/adapter Cakto + purchase canonical | UI admin, serviço condicional; checkout provider null, processing false, `purchase_enabled=false` | **GAP-COM-02:** vincular projeção e rotas somente à autoridade comercial; sem criar preço/provider real nem fingir compra efetuada |
| Command signed event | `CommandCommercialReceiver`, `POST /v1/commercial/command/events` com resolver explícito | Código e contrato existem, receiver depende de segredo resolvido/composição | **GAP-COM-03:** provar ligação interna assinada Command → canonical fulfillment/activation/PG, diferir credenciais reais |
| Fiscal engine | `FiscalApplicationService`, `CanonicalFiscalOperationPath`, lifecycle, numbering, archive, signing, gateways | `queryArchiveReference` conectado; emissão/cancelamento/inutilização/query/reconciliation externos sem handlers | **GAP-FISC-01:** fechar wiring/adapter determinístico compatível com contratos de provider; **sem** FakeFiscalOperationsGateway em runtime. Seleção/credenciais oficiais e homologação pertencem fase posterior |
| Outbox/Worker | Persistência única e Worker/PG canônicos; retries, idempotência | Worker 1/1, sem prova atual de efeito de negócio externo; historicamente outbox 0 | **GAP-WRK-01:** verificar e corrigir somente event handlers internos/cadeia Web→API→PG→Worker onde faltarem, sem segundo Worker/queue |
| Site institucional | `faabio3131/fm-site-novo`, HTML/CSS/JS estático | Landing NFCore e /entrar apontam ao Portal Railway de staging | **GAP-SITE-01:** CTA trial automático **não presente**; não copiar Next.js PR #33 do repo histórico |
| Operação de suporte | `support` e `audit` read projections | Informação e auditoria, não workflow completo de tickets no Portal | **GAP-DEC-01:** confirmar se ticketing é requisito **do próprio NFCore V1**; não criar sistema extra por suposição |

## 5. Delta priorizado e seu bloco **sem repetir o que já existe**

1. **BLD-01**: apenas confrontar mutações e telas já presentes contra aceites (onboardUnit após primeira unidade, create/updateUser, config e RBAC); não há evidência de `MISSING_CODE` que autorize reconstrução imediata. Reutilizar provas P02/P05 e completar somente o delta real.
2. **BLD-02**: `GAP-FISC-01`: mapear handlers faltantes por operação. `queryArchiveReference` já resolvido; demais operations devem ter caminho interno e erros corretos, produção fiscal fail-closed.
3. **BLD-03**: `GAP-WEB-01` e `GAP-SITE-01`: **maior lacuna pública**. Browser não possui credencial HMAC; site estático não comporta um BFF Next.js. Usar entrada segura no NFCore/Command existente, sem segunda API/autenticação. Binding comercial/staging exige plataforma autenticada; `trial_days` e preços dependem da decisão do proprietário.
4. **BLD-04**: `GAP-COM-01/02/03`: conectar serviços canônicos com eventos assinados internos de teste e PostgreSQL de teste. Provider e pagamento real ficam de fora.
5. **BLD-05**: complementar adapter fiscal/capabilities/normalização/request+response/unknown outcome de produção **no código**, com transporte substituível; homologação oficial deferida.
6. **BLD-06**: `GAP-WRK-01` e consistência API/Worker/persistência sem recriar schema/worker.
7. **BLD-07**: fechar links/CTA do **site correto** com a entrada segura criada em BLD-03; não usar o site Next.js histórico.
8. **BLD-08**: demonstrar jornadas internas no Portal/staging **somente com aprovação de deploy**; não confundir testes internos com homologação externa.

**Outros bloqueios / condições de governança:**
- **GAP-REL-01**: pin/versionar e publicar revisão sincronizada API/Worker/Portal em staging, com autorização explícita; **não é argumento para refazer código funcional**.
- **HUMAN-01**: executar botão de binding de trial com `platform_admin` real; sem spoof ou SQL direto. Não considerar segredo criado = binding registrado.
- **HUMAN-02**: preço/plano/trial_days e release comercial somente se aprovado; ausência não impede construir formulário paramétrico, mas impede ofertar trial como disponível.
- **HUMAN-03**: seleção de provider/jurisdição de estreia para adapter concreto se ainda não aprovado; infra neutra pode avançar sem inventar escolha.
- `P09-T04`, `P05-T05`, P08/P10/P11/P12 externos: **fora de BUILD**. Nenhum cliente real em operação comercial. Backup e restauração isolada já foram ensaiados.

## 6. Aceite BLD-00 e limites da prova

**Comprovado nesta auditoria:** CURRENT GitHub/PR/CI, revisão de 26 páginas e autoridades de permissão, código do Portal e serviços de composição, status e flags da API em staging, publicação do site estático, estado Railway dos quatro serviços e patch staged. Comparado com dois levantamentos anteriores, sem copiar correções de PRs antigas.

**Não comprovado:** navegação autenticada integral na revisão atual para cada papel, mutações reais dos 26 módulos, associação de cada deployment a um SHA verificado do Container Worker/Portal, binding de segredo gravado no PG, cadastro trial público, cobrança externa, emissão fiscal oficial. São tarefas seguintes ou provas que exigem ator autorizado/decisão.

**Critério de saída:** esta matriz gera backlog de delta concreto e não inventa que UI=integração operacional. PR/CI/Governança verdes e closeout no ledger subordinado serão registrados antes de marcar BLD-00 DONE. Sem novo deploy, migration, credencial, preço ou segunda regra de domínio nesta auditoria.
