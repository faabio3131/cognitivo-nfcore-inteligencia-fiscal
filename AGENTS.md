# AGENTS.md — FM Fiscal Core V2

## Autoridade

Este repositório implementa a evolução independente e multiproduto do motor fiscal brasileiro da FM Tecnologia.

O Fiscal Core não é autoridade do domínio de negócio de Kordena, Iron Fit, Vendedor IA, CampaIA ou qualquer consumidor. Ele recebe contratos fiscais neutros, executa regras e lifecycle fiscais e devolve resultados/eventos auditáveis.

## Estratégia de transição

1. O repositório `faabio3131/kordena-fiscal-engine` permanece baseline congelado durante a transição.
2. O baseline certificado de origem é `b336def47ad4f5188307102203f4e04b98406014`.
3. O V2 deve provar equivalência antes de refatoração multiproduto.
4. O fork é temporário. Depois do cutover certificado, o V2 vira a única arquitetura fiscal ativa e o original é preservado como histórico/auditoria.

## Regras obrigatórias

1. Nunca adicionar segredo, certificado real, senha, CSC, token, credencial, endpoint privado ou dado real de cliente.
2. Todo dado de exemplo deve ser sintético.
3. Alterações fiscais relevantes exigem teste correspondente.
4. Emissão deve ser idempotente por construção.
5. Numeração fiscal não pode usar estratégia concorrencialmente insegura como `MAX + 1`.
6. Regras tributárias devem possuir versão/vigência e ficar atrás do Tax Rule Engine.
7. Documento autorizado deve preservar snapshot histórico; cadastro atual não reescreve passado.
8. Adapters externos não podem inventar regra de negócio.
9. IA pode sugerir classificação, nunca alterar silenciosamente configuração fiscal de alto impacto.
10. Falhas de escopo, assinatura, schema, autorização, capability ou segredo são fail-closed.
11. Core não importa domínios privados dos SaaS consumidores.
12. Integração multiproduto exige `host_system_id`/namespace e binding governado de tenant/unidade.
13. Nenhum merge, deploy, promoção para produção ou cutover é automático.

## Disciplina de entrega

Para cada bloco V2:

- confirmar escopo em `docs/EXECUTION_TRACKER_V2.md`;
- implementar somente o bloco ativo e dependências mínimas;
- executar testes dirigidos;
- executar Ruff, Mypy strict e Pytest;
- revisar diff;
- registrar SHA, PR e CI;
- registrar riscos residuais;
- somente então alterar o estado para `CONCLUÍDO`.

Nenhuma etapa é concluída por declaração sem evidência.


## NFCore Commercial Launch — execução governada por plano mestre

Esta seção rege o trabalho do **FM NFCORE V1 — Commercial Launch** e complementa as regras históricas acima.

### Arquivos obrigatórios

Antes de executar qualquer bloco, leia integralmente:

1. `docs/NFCORE_V1_COMPLETION_MASTER_EXECUTION_SCHEDULE_2026-10-05.md`;
2. `docs/NFCORE_V1_EXECUTION_LEDGER.md`;
3. `docs/standards/FM_AI_MASTER_PLAN_EXECUTION_STANDARD.md`;
4. este `AGENTS.md`.

Git/GitHub, CI e runtime continuam sendo as fontes superiores para determinar o CURRENT técnico. O cronograma governa escopo/ordem/gates; o ledger governa estado/prova; o chat não substitui a persistência do plano.

### Disciplina obrigatória

1. Antes de qualquer coisa, reconfirmar `main`, HEAD, PRs abertas, CI e o ambiente afetado.
2. O plano precisa estar `APROVADO` ou `EM EXECUCAO`.
3. Executar somente a primeira tarefa não concluída do ledger, uma por vez.
4. Releia a tarefa no cronograma imediatamente antes de executá-la; não use memória do chat como substituto.
5. Uma PR de execução corresponde a uma única tarefa `NFV1-Pxx-Tyy`, exceto a PR inicial de bootstrap documental.
6. Concluído significa critério de aceite provado. Rode os testes, confira o resultado, obtenha CI/evidência e só então marque `[x]`.
7. O campo **Prova** de tarefa concluída deve registrar PR, CI e commit/SHA; integrações externas também exigem evidência de runtime.
8. Falha deve ser corrigida pela causa; nunca pular, apagar ou enfraquecer teste válido.
9. O que não foi provado é **não confirmado**. Fake/synthetic/mock não prova integração real.
10. Qualquer pendência descoberta deve ser resolvida, receber ID no cronograma/ledger, virar blocker ou ser rejeitada explicitamente com justificativa.
11. Alteração de escopo exige atualizar cronograma e ledger antes da execução.
12. Rode `python3 scripts/check_nfcore_plan.py` antes de abrir/atualizar a PR e antes de declarar o item certificável.

### Parada obrigatória para decisão humana

Parar e solicitar autorização específica antes de:

- decisão de produto/preço;
- mudança de segurança sensível;
- tratamento novo de dado pessoal;
- gasto ou conta real;
- segredo/certificado/credencial real;
- alteração de outro repositório;
- mudança de visibilidade;
- merge quando não autorizado;
- deploy;
- migration produtiva;
- DNS;
- produção fiscal;
- transação real não previamente aprovada;
- operação irreversível.

### Regra de continuidade

Ao retomar o projeto, nunca continue apenas do chat. Reabra o cronograma, o ledger e o último checkpoint persistente; depois reconfirme GitHub/CI/runtime e execute exatamente a próxima tarefa permitida.

### Continuidade NFCore Web — wiring de desenvolvimento, gate interno (2026-10-15)

- CURRENT base: `main=4f7d520ef66831edb56d8d68c60ca24cc17b51f4`; API, Portal e Worker sincronizados na Railway nessa revisão, com `live`/`ready` e controles 401 básicos comprovados.
- Diagnóstico real de `/runtime/profile`: `fiscal_operation_handlers_configured=[]`, checkout/acquisition/trial/receivers não compostos; domínio/portal/fulfillment/ativação preexistentes. NÃO reconstruir motor nem adicionar adapter sintético silenciosamente a staging.
- Branch de correção `feat/nfv1-web-dev-wiring-contract-gates`: `scripts/ci/check_nfv1_web_functional_profile.py` classifica separadamente shell pronto e caminhos de negócio conectados, a partir do perfil existente; testes sintéticos garantem regressão sem invocar fiscal/serviço externo. Usar `--require-all-paths` apenas para gate de paridade total e não confundir com health genérico.
- PENDENTE: composição efetiva de handlers fiscais de desenvolvimento e de ingressos comerciais governados, sem usar fake como homologação; E2E autenticado Portal→API→DB/Worker e prova de todas as superfícies na revisão publicada. Código deste branch não foi implantado nem incorporado à main.
- Ao retomar: verificar CI/Governança da branch e resolver falhas; auditar contratos de `CanonicalFiscalOperationPath` e `create_runtime_app` para conectar somente serviços existentes. Separar construção/testes internos de homologação externa futura; nenhuma alteração de credenciais, migrations ou novo deploy sem autorização específica.

### Atualização de execução segura — 2026-10-15

- A PR #190 revelou falha no Ruff, tratada com correção cirúrgica; novo HEAD deve passar CI e Governança próprios.
- O gate `check_nfv1_web_functional_profile.py` foi ajustado para não exigir simultaneamente os dois receivers de provedores comerciais opcionais (Cakto e Command). Conclusão de wiring exige pelo menos um ingresso de aquisição ou trial, checkout configurado e handlers fiscais, além do núcleo Web. Não transformar contrato do gate em evidência de jornada E2E.
- **Bloqueio factual de wiring fiscal Web:** `runtime.api::app` é composto sem `fiscal_operation_handlers`, ao passo que `CanonicalFiscalOperationPath` é fail-closed e `FakeFiscalOperationsGateway` está apenas nos testes. Não promover adapter sintético a staging/produção, nem criar handler fiscal fictício para pintar flag verde.
- **Bloqueio factual de wiring comercial:** `create_runtime_app` recebe security/receivers e starter explícitos; o entrypoint atual não os constrói automaticamente. Corrigir por composição governada e segredo configurável, não endpoint inseguro ou negócio duplicado.
- **PENDENTE:** instrumentar integração fiscal real de desenvolvimento (sem operação externa), comercial e E2E autenticado; sem credenciais/sessão de teste autorizadas para browser autenticado nesta etapa. Não alegar conclusão da construção ou dos fluxos.

### Implementação efetiva de ingressos comerciais de desenvolvimento — 2026-10-15

- Na PR #190: `runtime/development_commercial_ingress.py` fornece `WebhookSecurity` canônico para aquisição e trial SOMENTE quando `NFCORE_ENVIRONMENT=development|test`, com IDs e segredos HMAC explícitos via configuração (nenhum segredo padrão). Configuração incompleta falha fechada; staging/production não ativam essa composição. O entrypoint `runtime/api.py` injeta tais dependências existentes explicitamente, sem nova API, autenticação ou persistência.
- Testes `tests/runtime/test_nfv1_development_commercial_ingress.py` abrangem ausência de configuração, configuração incompleta, injeção explícita e isolamento de staging. **Isso NÃO ativa automaticamente checkout/acquisition nem trial em staging;** outras dependências existentes (PostgreSQL/composição, checkout e delivery) permanecem necessárias.
- Operações fiscais: `CanonicalFiscalOperationPath` só executa handlers explicitamente injetados; não ligar adapter sintético em staging nem declarar fiscal pronto. Falta integrar handler canônico com adapter aprovado para desenvolvimento e executar E2E autenticado com UOW/tenant/unidade.
- Sem merge, deploy, credenciais reais ou migrations nesta etapa. CI do HEAD mais recente deve ser inspecionada antes de qualquer certificação.

### Execução de código fiscal canônico — archive query (2026-10-15)

- Implementado `runtime/internal_archive_handler.py`: handler real `queryArchiveReference` consulta `FiscalArchiveStore.list_for_document(scope, reference)` com a `FiscalUnitOfWorkFactory` existente, retornando apenas metadados/digest e nenhuma peça de XML/conteúdo. Não chama SEFAZ, não simula autorização e não altera registros fiscais.
- `build_postgres_runtime_composition` registra o handler read-only no mesmo `CanonicalFiscalOperationPath` existente, preservando handlers explícitos e fail-closed dos demais comandos. `web/portal_api.py` habilita a operação com `DOCUMENT_QUERY`; `CanonicalPortalOperationExecutor` continua validando tenant/unidade/ambiente antes do lookup.
- Testes: SQLite durável com isolamento por unidade e entrada inválida `tests/runtime/test_nfv1_internal_archive_handler.py`; API de Portal com sessão AUDITOR e 403 para outra unidade `tests/web/test_portal_api.py`.
- Isto é integração interna real e parcial: emissão/cancelamento/inutilização e fluxo comercial final ainda dependem dos handlers/adapters de execução e checkout aprovados. CI do HEAD exige verificação; PR #190 Draft sem merge ou deploy.


## Protocolo de reconciliação antirretrabalho — obrigatório (2026-10-16)

**LER ANTES DE QUALQUER EXECUÇÃO:** `docs/checkpoints/NFV1_CURRENT_RECONCILIATION_ANTI_REWORK_2026-10-16.md`. É uma fotografia datada; GitHub e runtime atuais prevalecem. Este protocolo aplica-se a TODOS os agentes `.md`, revisores e executores do FM NFCORE V1.

1. Consultar ao vivo `main`/HEAD, PRs, CI+Governança do SHA exato, cronograma, ledger, checkpoints e ambiente de destino; se não for possível, declarar `CURRENT_NAO_VERIFICADO` e não alterar código nem checkbox.
2. Reconstruir a matriz por tarefa `ID → requisito de aceite → código/diff → testes → PR/merge SHA → CI pós-merge → runtime (quando aplicável)`. Sem elo obrigatório, resultado `EVIDENCIA_INSUFICIENTE`, não `DONE`.
3. Fazer busca antirretrabalho em `main` e PRs já mergeadas **antes** de programar; apenas delta faltante é elegível. Não repetir T07/P02 nem as métricas já incorporadas.
4. Distinguir `IMPLEMENTED_NOT_CERTIFIED`, `DONE_CERTIFIED_INTERNAL`, `DONE_CERTIFIED_OPERATIONAL`, `PENDING`, `BLOCKED_EXTERNAL` e `SUPERSEDED`. Não promover checkbox do ledger com CI verde isoladamente.
5. Quando ledger e código divergem, reconciliar uma única vez no checkpoint e registrar evidências; a próxima implementação fica condicionada à resolução da divergência. Nunca tratar nota histórica do AGENTS.md como CURRENT.
6. P09-T01/T02 e P05 são gates separados: tracing/métricas em código não homologam staging; deployment SUCCESS não comprova jornada do cliente. A prioridade comercial Web não autoriza deploy, migration, segredo real ou fiscal real.
7. Fechar cada PR com HEAD, gates PR e pós-merge, alterações, blockers e **próxima tarefa permitida** no repositório. A análise apenas no chat não vale como continuidade.
8. Executar `python3 scripts/check_nfcore_plan.py` e CI. **O validador verifica estrutura; não autentica GitHub ou Railway**. Os dois níveis de prova são obrigatórios.


## Checkpoint de execucao P09-T02 — 2026-10-16 (continuar, nao reiniciar)

- Fonte de verdade no inicio deste recorte: `main=95cd0a852aea001c7bde0a84e5e0c2b4ac111be6`; rever GitHub e CI antes de cada merge. PR #201 ainda aberta (correcao de overflow em `MetricsRegistry`), com CI #952 e Governance #373 SUCCESS no HEAD `d76e538e84db93315c0960a4835fd51d986c29e0`; PR #205 Draft documenta a matriz de aceite, nao certifica T01/T02.
- Worktree isolado no PC: `C:\nfcore-p09-t02-current`, branch `feat/nfv1-p09-t02-remaining-instrumentation-20261016`, baseada em main citada. Checkout historico `C:\nfcore-p05-migrations` em detached HEAD `65c58b6` permanece preservado.
- **Armadilha de ambiente confirmada:** `py -3 -m pytest` sem `PYTHONPATH` carregava `kordena_fiscal` de `C:\Users\faabi\nfcore-t04-work\src`, causando `ImportError` em `test_nfv1_p09_t02_http_metrics.py`. Reexecutar com `PYTHONPATH=C:\nfcore-p09-t02-current\src` resolveu: tres arquivos direcionados, 16 testes PASS. Nao alterar codigo para mascarar contaminacao de import.
- Uma alteracao inesperada em `.github/PULL_REQUEST_TEMPLATE.md` surgiu no worktree durante o checkout. Nao incorporar, descartar ou sobrescrever sem identificar origem; `git add` deve selecionar somente caminhos revisados.
- Instrumentacao CURRENT ja identificada em `runtime/observability.py` (Worker/queue), `runtime/api.py` (HTTP/dependency/activation), `web/app.py` (HTTP), `web/commercial_release.py` (offer), `runtime/commercial_observability.py` (eventos) e `product/cakto.py` (webhook/processing). Antes de adicionar counters, localizar producer + caminho de runtime + testes.
- Ausencias ainda nao certificadas: metricas de fulfillment, reconciliation, provider errors e fiscal rejection; diferenciar metric name presente apenas em teste de evento produtivo realmente instrumentado. P09-T01 tracing/exporter continua separadamente pendente; nenhuma checkbox promovida.
- P05 Worker/GSM e migration17 recuperados; T02 same-SHA staging documentado na PR #203. **Nao repetir deploy, credenciais, migrations, backup/restore ou bootstrap**. T01/T03/T04/T05 ainda possuem gates de prova distintos.
- Nao declarar T02 DONE sem testes/CI e evidencia para cada item do cronograma; sem merge em main, deploy ou operacoes externas sem aprovacao especifica.

- **Causa raiz adicional do template no Windows:** Git rastreia simultaneamente `.github/PULL_REQUEST_TEMPLATE.md` e `.github/pull_request_template.md`. NTFS case-insensitive faz colisao; restaurar um pode deixar outro como modificado. Diff inicial preservado em `C:\Users\faabi\Documents\nfcore-p09-template-unexpected-20261016.patch` (4385 bytes). Nao usar `git add -A`, nao renomear/excluir arquivos do repositorio neste gate; saneamento de conflito case-only exige PR propria e revisao de impacto.

### P09-T02 delta real de reconciliacao comercial — 2026-10-16

- Em `product/cakto.py`, `CaktoCommercialProcessor.reconcile()` passa a emitir `nfcore_cakto_reconciliation_total{outcome=drift|aligned}` somente apos retorno do bridge canonico, sem tenant/customer ID como label. Nao cria segunda autoridade comercial ou fiscal. Teste atualizado em `tests/product/test_web11_cakto.py` valida a amostra drift no caminho real SQLite/bridge.
- Reexecucao dirigida com `PYTHONPATH` do worktree correto: `tests/product/test_web11_cakto.py` mais tres suites P09-T02 = 25 PASS; Ruff dos dois arquivos PASS. Provas apenas locais, CI remoto e demais gates ainda necessarios. Nao confundir reconciliacao comercial Cakto com reconciliacao FISCAL, que segue aberta no cronograma.
- Aviso no Windows: `git diff --check` global inclui modificacao espuria do template case-only; fazer `git diff --check -- AGENTS.md src/kordena_fiscal/product/cakto.py tests/product/test_web11_cakto.py` e stage somente os tres caminhos. Conflito dos templates permanece pendente de saneamento separado.

### Retomada pela ordem do cronograma mestre — P09-T01 antes de T02 (2026-10-16)

- O `docs/NFCORE_V1_EXECUTION_LEDGER.md` marca P09-T01 `[ ] em execucao` e P09-T02 `[ ] pendente`, com dependencia explicita de T02 em T01; NAO promover T02 enquanto T01 nao estiver certificada. O delta Cakto da PR #206 e apenas candidata isolada, sem merge.
- P09-T01 ja possui `SafeTracer` e chamadas em `runtime/api.py`, `runtime/worker_composition.py`, `runtime/observability.py`; nao reconstruir. Executado no worktree `PYTHONPATH=C:\nfcore-p09-t02-current\src py -3 -m pytest -q tests/test_nfv1_p09_t01_runtime_trace_sink.py tests/runtime/test_p04_t03_worker_observability.py` com exit code 0 (alguns testes SKIP por dependencias/opcionais; nao converter SKIP em PASS).
- Gate faltante T01: demonstrar cobertura de spans de DB e dependencias externas e prova do sink/exporter real no staging, com correlacao segura e sem vazamento. Traces escritos em stdout nos testes locais nao bastam para certificacao de exporter remoto. Nao deployar apenas para produzir evidencia sem autorizacao.
- PR #206 HEAD `690a284718a84a2c7f3b4a2f4fb8a4c764f8043a`: Governance #385 SUCCESS e CI #964 ainda `in_progress` na ultima consulta. Verificar gates novamente antes de merge; nenhum merge autorizado por este registro.

### P09-T01 delta de tracing DB — 2026-10-16

- Achado reproduzivel: `runtime/api.py` emite operacao `db.readiness`, mas `StructuredLogTraceSink._ALLOWED_OPERATIONS` a omitia e serializava como `other`. Corrigida somente a allowlist fixa de operacoes, sem ampliar atributos livres, IDs, direitos ou dependencias.
- Teste novo `tests/test_nfv1_p09_t01_db_readiness_export.py` verifica que `db.readiness`/`error` e latencia permanecem visiveis no sink estruturado e que contexto/segredo nao aparecem. Suite nova + `tests/test_nfv1_p09_t01_runtime_trace_sink.py` passou, junto de Ruff dos arquivos alterados (exit 0).
- **Nao declarar P09-T01 concluida:** exporter real/staging, traces DB alem de readiness e chamadas externas permanecem sem prova operacional autenticada. Verificar CI/Governanca do HEAD remoto, manter T01 [ ] e T02 [ ]; nao fazer deploy para obter prova sem aprovacao.

### P09-T01 — Railway observability audit read-only (2026-10-16)

- Read-only Railway project `FM NFCORE Staging`, environment named `production` **within staging project**: API/Portal/Worker deployments SUCCESS at same source `2f3689838cfbec1c6d2ffac614cb0eb364d91633`. This does NOT mean commercial production.
- Railway `describe_service` API (`nfcore-api`) and Worker (`nfcore-worker`): `tracingEnabled=false`, `autoInstrumentationEnabled=false`, `autoInstrumentationActive=false`; no configured environment-variable names matching OTEL/TRACE/OBSERV/EXPORT/LOG identified. Railway native OpenTelemetry exporter is **not enabled**. Existing structured-log `SafeTracer` is separate from native Railway tracing, so native switch OFF does not prove application tracing ABSENT.
- Railway deploy logs search `runtime.trace` for both services yielded 0 entries; broad read displayed HTTP readiness/startup and Worker mostly empty log lines. Neither result certifies real span collection or lack of implementation. No authenticated end-to-end trace evidence with DB, external webhook, Worker and API in a configured destination.
- **Gate:** P09-T01 remains `[ ] EVIDENCIA_INSUFICIENTE` for staging exporter. Enabling Railway tracing on API requires redeploy; DO NOT call `set_service_tracing`, change variables, restart, migrate or deploy without specific approval. Preserve P05 runtime. First choose approved observability sink with retention/access/PII policy, confirm scope, and obtain explicit deploy permission when required.
- Corrections to P09-T01 and P09-T02 remain in PR #206 Draft, not deployed. Never use deployed SHA `2f368983` as evidence of corrections at branch HEAD. Verify exact PR CI and governance before integration.

### P09-T01 — Autorizacao e ativacao Railway Native Tracing (2026-10-16)

- Dono autorizou expressamente ativar tracing nativo da API e Worker no projeto `FM NFCORE Staging`; nenhuma autorizacao concedida para migration, credenciais fiscais, production commercial release ou merge.
- Auditoria preflight Railway: projeto `b84b290d-f3b4-46a1-9023-0b761cb96b0d`, environment interno Railway com nome `production` e ID `c9878b9b-62b2-4a97-b8ba-743c8a3e99ec` (o PROJETO e staging). Ambos servicos LIVE, sem patch staged, baseline source SHA `2f3689838cfbec1c6d2ffac614cb0eb364d91633`, tracing e autoinstrumentacao OFF.
- Acao autorizada executada: `set_service_tracing(tracingEnabled=true,autoInstrumentationEnabled=true)` na API `705bd719-f77b-4ade-a47c-4e6af63737d5` e no Worker `b3bde804-fa29-4c67-841d-7cda050c40e7`; ambas retornaram `tracingEnabled=true,autoInstrumentationEnabled=true,autoInstrumentationActive=true`.
- Railway iniciou deployments resultantes, API ID `8832e77c-70fc-41f9-bfec-25177342e3bd` e Worker ID `3634c897-8ce6-4f37-8b5f-98cd9b107adc`. Na primeira rechecagem ambos BUILDING. **Nao declarar sucesso de deploy, E2E, traces DB/externos ou T01 DONE ate confirmar deploy SUCCESS, health e traces reais no destino.**
- Revalidar estado do projeto e services; nao repetir a acao `set_service_tracing` se ja TRUE, nem criar credenciais, migrations ou novos deploys. Registrar SHA final, logs filtrados e limites de retencao/privacidade antes de promover checkbox.

### P09-T01 — Verificacao pos-ativacao Railway Native Tracing (2026-10-16)

- Apos ativacao autorizada, API deployment `8832e77c-70fc-41f9-bfec-25177342e3bd` **SUCCESS** e Worker deployment `3634c897-8ce6-4f37-8b5f-98cd9b107adc` **SUCCESS**, ambos no source SHA `95cd0a852aea001c7bde0a84e5e0c2b4ac111be6` de main. Portal preservado em SUCCESS com `2f3689838cfbec1c6d2ffac614cb0eb364d91633`, logo nao afirmar paridade same-SHA dos tres servicos depois da mudanca autorizada.
- Smoke real `GET https://nfcore-api-production.up.railway.app/health/ready` respondeu HTTP 200 e body `status=ready,reason=ready`, incluiu header `x-railway-trace-id`. Isso prova a resposta de readiness e correlacao do Railway edge, NAO garante todos os spans OTel de API/DB/external/Worker.
- Consulta `runtime.trace` nos novos deployments API e Worker retornou zero eventos no stream deploy; nao inferir ausencia de spans nativos em backend de tracing a partir de busca de logs estruturados. Destino, filtros, retencao e captura real em tracing UI ainda nao atestados.
- Estado formal P09-T01 = `IMPLEMENTED_NOT_CERTIFIED`/`EVIDENCIA_INSUFICIENTE` para end-to-end operacional; nao promover `[x]`. Nao executar outro deploy ou reconfiguracao apenas para perseguir log ausente. Proximo passo: prova de spans representativos API, DB, external e Worker no destino aprovado, e permissao humana para outros testes que provoquem efeitos reais.

### P09-T01 — Prova real do trace backend Railway (2026-10-16)

- Inspecao do destino nativo com `Railway.list_traces` (janela ~14:25–15:25Z) encontrou **2 traces reais** `/health/ready` no projeto FM NFCORE Staging, com 4 spans cada e 0 erros. Trace auditado `1a2648690b15179af77322a0bd2ede2c`: `edge.request` (SERVER), `edge_rules.evaluate` (INTERNAL), `upstream.request` (CLIENT), `origin_proxy.request` (SERVER). Componentes SOMENTE `edge`/`proxy`, nenhum span `service`.
- `Railway.get_tracing_coverage`: API `nfcore-api` = `spanCount=0`, Worker `nfcore-worker` = `spanCount=0`, sistemas/scopes vazios na janela. Tracing Railway e autoInstrumentation Active nos dois, mas isto NAO comprova instrumentacao interna.
- Auditoria CURRENT main `95cd0a852aea001c7bde0a84e5e0c2b4ac111be6`: `SafeTracer` usa `StructuredLogTraceSink` (logs de evento `runtime.trace`, sem OTLP) ou `NullTraceSink`; `pyproject.toml` nao declarou dependencias OpenTelemetry. PR #206 Draft contem uma allowlist corretiva DB ainda nao mergeada/deployada. **Causa provavel:** falta ligacao real do adapter de spans da aplicacao ao exporter OTLP, nao simples opcao de tracings do Railway; essa classificacao e HIPOTESE ate validacao via deploy governado.
- **P09-T01 EVIDENCIA_PARCIAL, NAO CERTIFICADA:** edge/proxy confirmados; API/DB/external/Worker spans internos ausentes na janela medida. Proxima implementacao aprovada somente apos mapa de impacto: adaptador OTel seguro sobre `SafeTracer` existente, export de spans tipados de baixa cardinalidade, falha nao autoritativa, teste de export e retencao, sem segunda autoridade nem credenciais hardcoded; validar por CI e solicitar autorizacao antes de integrar/deployar. Nao repetir ativacao Railway.

### Decisao do dono — priorizar fechamento interno antes de homologacao externa (2026-10-16)

- Nao exigir contador, cliente piloto, credenciais/certificados oficiais, SEFAZ, prefeitura ou provider fiscal REAL para continuar a construcao do NFCore V1. Homologacoes de terceiros ficam classificadas `BLOCKED_EXTERNAL` ate que o produto esteja internamente completo e pronto para apresentacao/teste real.
- Seguir `docs/NFCORE_V1_COMPLETION_MASTER_EXECUTION_SCHEDULE_2026-10-05.md` e ledger na ordem, executando integralmente codigo, APIs, composicao, PostgreSQL, Worker, Web/UI, RBAC/tenant, seguranca, testes locais/CI e operabilidade possiveis sem dependencia externa; nao mascarar criterios internos como externos.
- P09-T01: concluir adaptador OTLP e instrumentacao interna existente por testes controlados locais/de staging sem dados reais de terceiros; nao bloquear desenvolvimento por ausencia de piloto fiscal. A prova de homologacao fiscal externa nao faz parte deste gate de construcao. Nao declarar spans end-to-end certificados onde nao houver evidencias.
- Manter aprovacao humana especifica para merge, deploy, migrations reais, credenciais reais e operacoes irreversiveis. Atualizar AGENTS.md, checkpoint e ledger com evidencias, bloqueios e proximo bloco em cada marco.

### P09-T01 — reconciliacao/implementacao interna API tracing (2026-10-16)

- CURRENT conferido: main `95cd0a852aea001c7bde0a84e5e0c2b4ac111be6`, branch da PR #206 baseada em main, `SafeTracer`/`StructuredLogTraceSink` canônicos; Worker usa sink estruturado, mas API criava por padrao `SafeTracer()` com `NullTraceSink`. Corrigido apenas `runtime/api.py`: criar `runtime_logger` primeiro e usar `SafeTracer(StructuredLogTraceSink(runtime_logger))` se tracer nao for injetado; dependencia/injecao explicita continua prevalecendo, sem segunda autoridade.
- Teste novo `tests/test_nfv1_p09_t01_api_default_trace_sink.py` verifica evento `runtime.trace` e ausencia de token no sink quando dependencias canônicas estao instaladas. Na maquina Windows atual a coleta foi `SKIP` declarado (ausente `google.cloud.secretmanager_v1`), NAO PASS. Suite anterior de tracing/DB passou 7 testes, Ruff dos arquivos editados PASS; testes E2E da API em CI completo precisam confirmar funcionalidade. Nao mascarar o SKIP nem substituir GSM.
- Esta alteracao produz log estruturado seguro da API; NAO constitui exporter OTLP e NAO prova spans da aplicacao no Railway. O adaptador OpenTelemetry, cobertura API/DB/external/Worker, CI do HEAD, staging e gates P09-T01 continuam pendentes. Nao promover ledger/checkbox. Conflito case-only de templates no Windows permanece protegido/nao incluido.
