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
