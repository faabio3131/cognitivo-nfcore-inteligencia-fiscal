# FM NFCORE V1 — Ledger da trilha BUILD-ONLY

**Estado:** EM_EXECUCAO (trilha subordinada ao cronograma mestre de 59 IDs).  
**Decisão:** autorização explícita do proprietário em 18/10/2026 para construir/corrigir autonomamente e **mergear PRs BUILD-ONLY 100% verdes**, preservando decisões humanas para credenciais, custos, preço, segurança nova, deploy, produção e atos irreversíveis.  
**Cronograma de escopo:** `docs/NFCORE_V1_BUILD_INTEGRATION_EXECUTION_2026-10-18.md` — anexo, **não substitui** `docs/NFCORE_V1_EXECUTION_LEDGER.md`.  
**Próximo bloco executável:** `NFV1-BLD-01`.  
**Última reconciliação:** main `74089d694b50f4809810e34e9fed6899a68c37e1`; BLD-00 PR #226 com CI #1063/Gov #484 SUCCESS, fechamento PR #227 com CI #1066/Gov #487 SUCCESS; BLD-01 em execução, PR #228 mergeada (CI #1067/Gov #488 SUCCESS), Governança pós-merge #489 SUCCESS, CI pós-merge #1068 ainda em execução nesta verificação. BUILD-01 não declarado DONE.

## Semântica de estado e prova

- `PENDING`: não iniciada/sem prova completa.
- `IN_PROGRESS`: existe PR ativa ou trabalho de auditoria efetivo, no máximo 1 bloco principal simultâneo.
- `BLOCKED_HUMAN_ACTION`: falta sessão/decisão específica; continua aberta e pode permitir **somente** tarefas internas independentes explicitadas.
- `BLOCKED_EXTERNAL`: depende de infraestrutura/terceiro, não pode virar PASS sem evidência.
- `DONE`: somente após PR(s) mergidas, `CI+Gov SUCCESS` no SHA exato, CI/Gov pós-merge SUCCESS, verificação de delta funcional e aceite definido no anexo; refs obrigatórias.
- `ALREADY_INTEGRATED`: implementação já existente e aceita com **PR/SHA/CI reais do CURRENT**; encerra bloco sem repetição de código, com evidência específica.
- `CONSTRUCTION_AND_WEB_INTEGRATION_COMPLETE` só é permitido após todos os blocos terminados e execução Web na revisão liberada. Merge de código não equivale a deploy.

Cada `Evidência` abaixo é levantamento de baseline, **não certificação do bloco**. Registrar PR, SHA e CI por item concluído. Alterações de site devem citar PR em `fm-site-novo`. Se uma PR falhar, consertar a causa no mesmo bloco. Nenhum avanço por checkpoint inventado.

## Blocos (ordem de execução)

### NFV1-BLD-00 — Inventário integral de paridade
- **Estado:** DONE
- **Depende de:** docs/NFCORE_V1_BUILD_INTEGRATION_EXECUTION_2026-10-18.md §4 BLD-00
- **CURRENT:** main 44cddbabb4e91b55dcc730e6976fcc2ce7f00d75 CI #1054/Gov #475 SUCCESS; checkpoint NFV1_WEB_PARITY_AND_FUNCTIONAL_INTEGRATION_2026-10-18.md histórico. Falta auditoria **completa de todas as ações** no CURRENT e matriz de gaps.
- **Target e aceite:** seção `NFV1-BLD-00` do anexo de execução.
- **Evidência final:** PR #226, HEAD `f42bc2f0916c0385b752d240028023979f9fa182`, CI #1062 SUCCESS / Gov #483 SUCCESS; merge SHA `b15527e725213c3c1cb848692306a95dd7c240df`, CI #1063 SUCCESS / Gov #484 SUCCESS (mesmo SHA); matriz `docs/checkpoints/NFV1_BLD00_CURRENT_FUNCTIONAL_PARITY_2026-10-19.md`, 26 áreas navegacionais, 2 ações especiais, gaps e limites de evidência explícitos. Sem deploy/produção/homologação.
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-01 — Identidade, onboarding e Portal operacional
- **Estado:** IN_PROGRESS
- **Depende de:** BLD-00 concluído; exceto coleta de dados não destrutiva paralela
- **CURRENT:** Login/logout/recovery/onboardUnit/UserAdmin já têm código, testes e evidências. PR #228 corrigiu a confirmação visível após refresh de usuários (merge `74089d694b50f4809810e34e9fed6899a68c37e1`; CI #1067/Gov #488 SUCCESS antes do merge; Gov #489 SUCCESS pós-merge, CI #1068 pendente de conclusão). Prosseguir somente com deltas funcionais, sem reabrir P02 DONE nem considerar a Web publicada por merge.
- **Target e aceite:** seção `NFV1-BLD-01` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-02 — Paridade fiscal Web e executores internos
- **Estado:** PENDING
- **Depende de:** BLD-00 e BLD-01
- **CURRENT:** queryArchiveReference é handler interno existente; outros handlers fiscais dependem de composição determinística e transportes corretos; PR #189 auditar sem copiar.
- **Target e aceite:** seção `NFV1-BLD-02` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-03 — Trial first-party no NFCore e site estático
- **Estado:** PENDING
- **Depende de:** BLD-00 e interfaces de identidade BLD-01; código interno pode avançar se sessão admin/config comercial bloquearem operações
- **CURRENT:** GovernedTrialService, binding admin Web e segredo comercial GSM já construídos/criados. Registro admin não provado; /runtime/profile commercial_trial_configured=false; site fm-site-novo ainda não tem cadastro de trial.
- **Target e aceite:** seção `NFV1-BLD-03` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-04 — Comercial interno e integração Command
- **Estado:** PENDING
- **Depende de:** BLD-03 contratos, ou interfaces canônicas já verificadas; não ativar pagamentos
- **CURRENT:** Pricing/release e aquisição/fulfillment internos existentes; catálogo/release/checkout de runtime sem readiness. Backend multi-tenant é autoridade; simular somente entrada de provedor em testes.
- **Target e aceite:** seção `NFV1-BLD-04` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-05 — Fiscal adapter/contratos para homologação futura
- **Estado:** PENDING
- **Depende de:** BLD-02 + scope de adapter revisado
- **CURRENT:** Provider transport real não está configurado. Não criar fake em runtime. Aprovação humana necessária para provedor/jurisdição específicos, porém infraestrutura neutra pode avançar.
- **Target e aceite:** seção `NFV1-BLD-05` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-06 — Persistência e Worker das jornadas Web
- **Estado:** PENDING
- **Depende de:** BLD-02/BLD-04/BLD-05 contratos relevantes
- **CURRENT:** Worker staging online e DB existem, mas prova de outbox externo não é construção interna. Reusar Worker, idempotência e recovery existentes; corrigir somente wiring faltante.
- **Target e aceite:** seção `NFV1-BLD-06` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-07 — Conectar site novo e jornada NFCore
- **Estado:** PENDING
- **Depende de:** BLD-03 ingresso seguro e catálogo quando aprovado; separar canal interno de liberação pública
- **CURRENT:** Site novo faabio3131/fm-site-novo PR #10 integrou acesso Portal. Trial Web comercial ainda não disponível; Next.js PR #33 legada fechada SEM merge.
- **Target e aceite:** seção `NFV1-BLD-07` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

### NFV1-BLD-08 — Aceite de construção e entrega demonstrável na Web
- **Estado:** PENDING
- **Depende de:** BLD-00 a BLD-07 sem lacunas de código/wiring não resolvidas
- **CURRENT:** Sem prova de CONSTRUCTION_AND_WEB_INTEGRATION_COMPLETE. CI green isolada não prova todas as superfícies disponíveis.
- **Target e aceite:** seção `NFV1-BLD-08` do anexo de execução.
- **Evidência final:** PENDENTE (registrar PR + HEAD + merge SHA + CI/Gov PR e main + prova funcional apropriada).
- **Pendência / decisão humana:** se surgir, registrar o bloqueio exato com decisão necessária, sem gerar novo serviço, preço ou credencial.

## Checkpoint permanente de execução

Para cada PR BUILD usar este registro, preenchido **depois** das provas:

```text
Data UTC:
Bloco:
Base main / SHA:
Autoridade reutilizada:
Current -> Target (delta concreto):
Branch / HEAD:
PR:
Testes dirigidos e resultado:
CI PR / Governança PR (mesmo SHA):
Aprovação automática de merge aplicável? [sim/não + motivo]:
Merge SHA:
CI main / Governança main:
Estado no staging (se houve deploy autorizado):
Evidência Web/API/PostgreSQL:
Pendências internas / externas / decisões humanas:
Próximo bloco:
```

## Backlog de homologação e produção: preservado, não confundido

P05-T03/T04/T05 **provas operacionais adicionais**, P08 canal de pagamento real, P09-T04 rotina periódica/retention/RPO/RTO de produção, P09-T05 runbooks finais, P10 homologação oficial, P11 infra definitiva, P12 certificação/Go-No-Go. Backup/restauração isolados **já realizados** em 12/10/2026; não reexecutar só para satisfazer checklist. Nenhum cliente real ou produção comercial ativa neste estágio.
