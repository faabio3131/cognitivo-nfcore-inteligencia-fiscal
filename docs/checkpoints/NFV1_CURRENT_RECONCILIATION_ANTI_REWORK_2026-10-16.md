# NFCORE V1 — CURRENT reconciliado e protocolo antirretrabalho

**Data da observação:** 2026-10-16 (UTC). **Tipo:** auditoria read-only de GitHub/Railway; esta PR somente documenta e governa execução. **Produto:** FM NFCORE V1. **Repositório:** `faabio3131/kordena-fiscal-engine-v2`.

## 1. Fatos observados, não extrapolações

- **GitHub main no início desta reconciliação:** `d46cc517ae8a3a201e3e915a6d4fe00dd178306d`; CI pós-merge #38836914869 **SUCCESS**; NFCore Plan Governance #38836914884 **SUCCESS**. Qualquer avanço após esta data exige nova leitura, não presunção deste SHA.
- **Ledger canônico em main:** **59 IDs**, **27 [x]**, **32 [ ]**; P00 (3), P01 (4), P02 (7), P03 (5), P04 (4), P06 (4) certificados **internamente**, não em produção/staging por consequência.
- **P02-T07** está registrada como concluída internamente em 2026-10-08: PR #131, CI PR #676/main #677, Governance #97/#98; **não é a mesma T02 da P09**. Não reiniciar.
- **P09-T01** segue `[ ] em execução` no ledger: PRs #172 e #187 *foram integradas* (verificar a evidência atual), mas falta reconciliar integralmente aceite de tracing e prova operacional de exporter/staging. A nota antiga que chama #172 de DRAFT é histórica, não CURRENT.
- **P09-T02** segue `[ ] pendente` no ledger, mas há IMPLEMENTAÇÃO PARCIAL INTEGRADA nas PRs **#193, #194, #195, #196, #197, #198, #199, #200**. Cobertura observada: dispatch Worker, HTTP/error/latência, oferta comercial, validação de telemetry, tentativas de ativação, webhook, integridade das amostras. Isso **não** certifica a tarefa: ainda exigir matriz de critérios (fulfillment, reconciliação, rejeições fiscais, erros provider, provas operacionais) e predecessora T01. NÃO reproduzir código já integrado.
- **PR #201** está OPEN/DRAFT (overflow counter), com CI e Governança SUCCESS no HEAD `d76e538e84db93315c0960a4835fd51d986c29e0` quando consultada; **sem merge** na leitura. Avaliar necessidade/impacto antes de integrar, reconsultando mergeability/gates.
- **Outras PRs abertas** em 16/10: #165 (GSM P05), #182 (Portal senha), #188 (métricas HTTP antigas; potencial duplicação), #189 (paridade Web). Não declarar seu conteúdo integrado. Auditar diff contra main antes de qualquer decisão.
- **Railway, projeto FM NFCORE Staging** `b84b290d-f3b4-46a1-9023-0b761cb96b0d`: API, Portal, Worker e PostgreSQL têm deployment **SUCCESS**, 1 réplica cada na leitura; API/Portal/Worker estão no SHA **`2f3689838cfbec1c6d2ffac614cb0eb364d91633`**, **não** no HEAD main acima. Ambiente Railway chama-se `production`, porém o projeto é de **staging**. Deployment SUCCESS não prova saúde operacional nem E2E.
- **P05-T01** permanece `[ ] bloqueado externo` no ledger. Confirmar novamente runtime, binding GSM/IAM, schema/migrations, backup, Worker readiness, smoke/E2E e autorizacões antes de qualquer operação externa. Não apagar evidência prévia do backup lógico/restore nem repeti-la sem regressão.
- **PRODUCTION_APPROVED = NO; COMMERCIAL_LIVE = NO** até provas e Go/No-Go humano.

## 2. Diagnóstico da divergência

O arquivo `AGENTS.md` inclui anotações históricas de PRs e branches e o ledger não recebeu a reconciliação das PRs #172/#187/#193–#200. O script `scripts/check_nfcore_plan.py` valida IDs, ordem, campos, checkbox e formatos textuais de PR/CI/SHA, **não consulta o GitHub/Railway e não autentica resultados reais**. É incorreto interpretar seu PASS como certificação de entrega, runtime ou comercialização.

## 3. Protocolo obrigatório: CERTIFICAR ANTES DE PROMOVER

1. **READ-ONLY CURRENT**: consultar GitHub `main`/HEAD, PRs OPEN/MERGED, CI no *exato* SHA e Railway/runtime do ambiente. Data e fonte registradas no checkpoint, nunca somente no chat.
2. **RECONCILIAR**: confrontar cronograma (escopo/ordem), ledger (estado), checkpoints (histórico) e código/testes CURRENT (implementado). Identificar lacunas e código cumulativo. Se divergem, bloquear implementação até classificar.
3. **CLASSIFICAR** cada item: `DONE_CERTIFIED_INTERNAL`, `IMPLEMENTED_NOT_CERTIFIED`, `BLOCKED_EXTERNAL`, `PENDING`, `DONE_CERTIFIED_OPERATIONAL` ou `SUPERSEDED` com evidência. Preservar os estados oficiais/checkboxes existentes até validação; classificação detalhada fica no checkpoint.
4. **MATRIZ DE ACEITE**: cada requisito da tarefa do cronograma recebe evidência de arquivo/código, teste determinístico, PR+merge SHA, CI exata e, se externo, runtime/ambiente/observação. **Faltando evidência => NÃO PROMOVER [x]**. PR verde não equivale a tarefa concluída; teste sintético não equivale a integração real.
5. **ANTI-DUPLICAÇÃO**: antes de escrever, buscar código e PRs anteriores, identificar autoridade canônica e provar delta Current → Target. Não criar PR corretiva repetida ou duplicar service/API/auth/tenant/persistência.
6. **APROVAÇÃO**: mudanças sensíveis, credenciais reais, migrations, deploy, billing/fiscal real, DNS e produção exigem autorização humana específica. Merge apenas quando autorizado, HEAD mergeable e CI+Governança 100% verdes no mesmo SHA.
7. **CLOSEOUT DURÁVEL**: após PR/merge, verificar CI/Governança pós-merge, atualizar ledger/checkpoint com resultados reais, SHA e pendências. Nunca fazer atualização otimista baseada em workflow em execução.
8. **SEQUÊNCIA**: não avançar para fase nova com predecessor não certificado, salvo exceção explícita já aprovada e registrada no cronograma. Se bloqueado, registrar o blocker e trabalhar somente em construção interna autorizada, sem mascará-lo.
9. **CONTINUIDADE**: próxima sessão reexecuta itens 1–2; esta página é snapshot **datado**, não fonte mais nova que HEAD/runtime. Caso divergência, abrir uma única PR de reconciliação documental antes de refatorar.
10. **HOMOLOGAÇÃO**: separar conclusão interna, release em staging, jornadas E2E, fiscalização oficial, produção e comercialização. Nenhuma equivalência automática.

## 4. Próximo passo seguro e não duplicado

1. Certificar status pós-merge de #200 (comprovado verde nesta auditoria).
2. Resolver #201 e as PRs legadas #165/#182/#188/#189 por comparação de diff, sem merge cego.
3. Montar matriz requisito×evidência de P09-T01/T02 e preencher apenas o que estiver comprovado; **não** reimplementar métricas existentes.
4. Retomar o caminho crítico P05 com verificação Railway/GSM/migrations e as autorizações específicas necessárias para staging; evitar mais micro-PRs de métricas sem vínculo ao aceite.
5. Somente depois de aceite auditado avançar para P09-T03 e demais fases na sequência efetivamente aprovada.

## 5. Regra para agentes e revisores

Qualquer agente ou executor que não tenha consultado HEAD/CI/PR/runtime **deve declarar `CURRENT_NAO_VERIFICADO` e parar**. Qualquer conclusão sem os quatro vínculos (ID → aceite → PR/merge+CI → prova operacional quando aplicável) deve ser devolvida como `EVIDENCIA_INSUFICIENTE`. Alterações desta PR documental não comprovam funcionalidade nem encerram T01/T02/P05.
