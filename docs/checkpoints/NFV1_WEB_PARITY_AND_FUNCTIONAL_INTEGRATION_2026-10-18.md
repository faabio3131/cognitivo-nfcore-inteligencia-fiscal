# FM NFCORE V1 — Paridade funcional código × API × Web, com correções reais
Data: 2026-10-18. Base de auditoria: main `59fcd2e7d482b3d7be334b63aba195675319f107`.

## Fontes atuais, não checkpoints presumidos
Código de `portal/app.js`, `portal/index.html`, `web/portal_api.py`, `web/portal_runtime.py`, `runtime/api.py` e `runtime/fiscal_runtime.py`. Perfil público obtido por GET efetivo no endpoint Railway `/runtime/profile` em 18/10; configuração dos serviços Railway lida por connector. Testes/CI anteriores são evidências internas, não prova automática de disponibilidade Web.

Railway: projeto `FM NFCORE Staging`, embora seu ambiente Railway seja denominado `production`, `NFCORE_ENVIRONMENT=staging`. API e Worker executavam commit `19cf767de1be75009783054356ffcb7c14d2e975`; o Portal acompanhava `main`. Portal, API, Worker, PostgreSQL online, 1/1 na consulta. A paridade de SHA não estava satisfeita e não deve ser apresentada como encerrada.

Perfil real: `persistence_backend=postgres`, `human_identity_configured=true`, `portal_executor_configured=true`, `fiscal_operation_handlers_configured=["queryArchiveReference"]`, `fiscal_provider_transport_real_configured=false`, `fiscal_runtime_external_execution_ready=false`, `pricing_catalog_published=false`, `commercial_release_status=unavailable`, `commercial_checkout_provider_configured=null`, `commercial_first_party_acquisition_configured=false`, `commercial_trial_configured=false`, `commercial_checkout_processing_configured=false`, `commercial_delivery_path_ready=true`, `fiscal_production_activated=false`.

## Inventário completo das áreas do Portal V1

Critério: **INTEGRADO** = caminho UI→API/serviço codificado (não significa cenário real homologado); **CORRIGIDO NESTA PR** = integração Web funcional alterada; **BLOQUEADO NA CONFIGURAÇÃO** = serviço implementado, mas capacidade indisponível no runtime; **EXTERNO DIFERIDO** = provedor oficial/gateway/homologação por executar na fase final autorizada.

| Área de produto | Autoridade canônica já construída | Web antes desta candidata | Estado / entrega |
| --- | --- | --- | --- |
| Login/sessão/logout/RBAC | HumanIdentity, cookies e CSRF, rotas `/v1/auth` | Formulário de login e sessão; logout | INTEGRADO; login real e controles de tenant confirmados em evidências prévias |
| Recuperação de senha/ativação | PasswordRecovery + delivery de e-mail | Fluxo completo de redefinição | INTEGRADO; 202→204→login 200 e e-mail recebido no staging |
| Visão geral/readiness | Bootstrap + projeções autorizadas | Painel e estado de bloqueio visível | INTEGRADO; readiness fiscal real não autorizado |
| Organização/empresas | Control Plane e organização do tenant | Superfície de leitura por tenant | INTEGRADO |
| Primeiro onboarding da unidade | `onboardUnit` com audit, CSRF, RBAC, idempotência e PostgreSQL | Formulário apenas se `unit_setup_required` | INTEGRADO; primeira unidade já persistida em staging |
| **Unidades adicionais** | Mesmo `onboardUnit`, suporta múltiplas unidades | Formulário desaparecia depois da primeira; tela Unidades só leitura | **CORRIGIDO NESTA PR:** adicionar unidade pelo menu Unidades com idempotency key estável no retry; depois exibir listagem canônica; autoridade no backend |
| Ambientes por unidade | FiscalUnitRegistration e filtros de scope | Visualização, seleção de homologação/produção autorizada | INTEGRADO; habilitação de produção não autorizada pela UI |
| Usuários/perfis/escopos | HumanAdministrationService | Criar/editar usuários, unidade/papel | INTEGRADO; permissões efetivas impostas no servidor |
| Certificados | Referências de configuração governadas | Cadastro/edição de referências | INTEGRADO como cadastro, não como segredo/certificado homologado |
| Providers/bindings | Control Plane de configurações | Cadastro/edição por jurisdição/operação | INTEGRADO como configuração, sem transporte fiscal real |
| Webhooks/egress | Configuração durável + política aprovada pelo platform_admin | Formulários de solicitação/decisão | INTEGRADO internamente, entrega real EXTERNA DIFERIDA |
| Integrações e políticas | Configuração existente com versionamento | Cadastros por tenant, unidade, ambiente | INTEGRADO; não ativa provider fiscal sozinho |
| Documentos e emissão | Superfícies duráveis, CanonicalFiscalOperationPath | Documentos, emissão, fluxo de intents, bloqueio visível | CONSULTA INTERNA INTEGRADA; operações fiscais externas bloqueadas |
| **Arquivo fiscal por referência** | Handler **já ativo** `queryArchiveReference`, read-only, usa FiscalArchiveStore | Nenhum botão/formulário acessível apesar de handler no runtime | **CORRIGIDO NESTA PR:** formulário na tela Documentos, escopo via sessão/unidade/ambiente, exibe metadados reais ou ausência, sem novo serviço |
| Cancelamento/inutilização | Domínio, recuperação, idempotência, API | Ações e páginas sob permissões | SUPERFÍCIES INTEGRADAS; envio fiscal externo NÃO PRONTO |
| Reconciliação, erros e capacidades | Projeções/readiness persistentes e rotas governadas | Páginas, filtros, bloqueios, estado | INTEGRADO para dados internos; confirmação oficial EXTERNA DIFERIDA |
| Billing, planos e uso | CommercialPortalReadService, persistência canônica | Listagem abreviada ocultava demais colunas devolvidas | **CORRIGIDO NESTA PR:** detalhes completos do registro autorizado, sem novo endpoint |
| Catálogo comercial/preços | PricingAdministrationService + versão/histórico | Tela `pricing-admin` para autoridade de plataforma | INTEGRADO; `pricing_catalog_published=false`: não inventar preços |
| Release comercial | CommercialReleaseAdministrationService | Administração de decisão humana versionada | INTEGRADO; status real `unavailable` exige decisão aprovada |
| Checkout Cakto | Adapters e administrador condicional | Tela presente, exposta somente se provider configurado | `commercial_checkout_provider_configured=null`: BLOQUEADO NA CONFIGURAÇÃO |
| Aquisição, assinatura e trial | CommercialFulfillment, provisioning, trial, receivers existentes | API/entradas condicionais; nenhuma jornada de compra/trial público ativo | SERVIÇOS INTERNOS INTEGRADOS; `commercial_first_party_acquisition_configured=false` e `commercial_trial_configured=false`: FALTA CONFIGURAÇÃO/WIRING seguro e oferta/preço |
| Worker/outbox | Serviço durável único em Railway; handler real governado | Sem tela obrigatória do Worker | RUNNING; outbox zero registros no staging; processamento externo DIFERIDO |
| Suporte/auditoria | Projeções e RBAC do portal | Páginas com estado operacional | INTEGRADO para leitura; SLA e operação comercial real não homologados |
| Produção fiscal real | Autoridade humana, signer, certificados e transportes oficiais | UI indica bloqueio real | **NÃO HABILITADA**; proibir simulação como emissão real |

## Escopo da correção funcional desta candidata

1. Não reconstruir o Portal. Reutilizar `onboardUnit` em **Onboarding e Unidades** após a primeira unidade, somente com `configuration.write` e escopo de todas as unidades; proteger retries de rede mantendo a mesma idempotency key para conteúdo idêntico.
2. Expor a consulta ao arquivo persistido que o API runtime já suporta via `queryArchiveReference`, usando `document.query`, seleção de unidade/ambiente e retornando apenas metadados autorizados.
3. Exibir os campos completos que as autoridades existentes devolvem em Billing, Planos, Uso, Auditoria, Usuários, Empresa, Onboarding, Ambientes e Unidades; nenhuma regra de cobrança, preço, permissão ou status foi movida para a UI.

## Pendências verdadeiras para produto vendável — ordem por impacto

1. **Publicação Web desta integração** no Portal que acompanha a `main`; verificar o commit implantado e o fluxo Web autenticado sem alterar a API desnecessariamente.
2. **Paridade da mesma revisão** API/Portal/Worker em staging, com gate de rollback/smoke governado; exige autorização operacional específica antes de deploy deliberado.
3. **Ativação comercial interna governada** (catálogo de preços reais e decisão humana de release). Não inventar preço/plano, nem falsificar `commercial_approved`.
4. **Conectar acquisition/trial/checkout ao runtime existente** apenas quando dependências/identidade confiável e provider estiverem definidos; não inventar chaves, ativar endpoint público sem security, nem abrir pagamentos reais sem autorização.
5. **Operação fiscal real e webhooks externos**: registrar como DIFERIDOS pelo proprietário para o fechamento comercial, sem impedir evolução das funcionalidades internas.

## GATE
Esta alteração é entrega de **funcionalidade Web**, não de cobertura de testes isolados. Não declarar P05/P12 ou NFCORE V1 100% prontos por passar CI. Exigir CI/Gov verdes, merge governado, deploy efetivamente observado e fluxo interativo em staging. Nenhuma migration, segredo real, segunda API/autenticação/persistência nem mudança de segurança foi criada.
