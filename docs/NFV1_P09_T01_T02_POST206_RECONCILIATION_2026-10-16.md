# FM NFCORE V1 — Reconciliação pós-PR #206, P09-T01/T02

Data: 2026-10-16. Fonte de verdade: `main` GitHub após merge `904587334bdd830a41c260e0f545f3d6083e8bfc`, cronograma mestre e `docs/NFCORE_V1_EXECUTION_LEDGER.md`.

## Estado confirmado

- PR #206 integrada na main, contendo adaptador OTLP opcional sobre `SafeTracer`, composição API/Worker, teste de SDK real e transporte HTTP local, logs estruturados seguros, `db.readiness`, e métrica de reconciliação comercial Cakto.
- Governança pós-merge na main: execução `38937043756` SUCCESS. CI pós-merge `38937043499` estava IN_PROGRESS na primeira verificação; atualizar somente com evidência conclusiva. Não reutilizar CI pré-merge como certificação pós-merge.
- Railway API/Worker tinham tracing nativo ativo e edge spans provados antes do merge; nenhum novo deploy autorizado nesta retomada. O código OTLP da PR #206 **não foi comprovado implantado**. P09-T01 segue `[ ]` por ausência de prova de spans de serviço API/DB/externos/Worker no staging.
- `check_nfcore_plan.py`: 59 IDs, próximo item P09-T01. A dependência formal P09-T01 → P09-T02 impede marcar T02 concluída ou antecipar a próxima fase.

## Matriz da P09-T02 — CURRENT por produtor, não apenas declaração de nome

| Requisito do cronograma | Evidência no código CURRENT | Estado / lacuna de certificação |
| --- | --- | --- |
| HTTP/error/latency | `runtime/api.py`: `nfcore_http_requests_total`, `nfcore_http_request` com classe HTTP e duração; `web/app.py` tem observação HTTP adicional | Implementação existente; requer prova integrada e coleta |
| Commercial events | `runtime/commercial_observability.py`: `nfcore_commercial_events_total` | Implementação existente; validar todos os outcomes relevantes |
| Fulfillment | Não identificado contador específico de fulfillment nesta auditoria dirigida | **GAP A INVESTIGAR** na autoridade canônica de fulfillment antes de codificar |
| Worker backlog | `runtime/observability.py`: `nfcore_worker_backlog_jobs` | Implementação existente; aferir gauges no ciclo real |
| Retries e dead-letter | `runtime/observability.py`: `nfcore_worker_jobs_total` por outcome; `runtime/worker_composition.py`: `nfcore_dispatch_total` | Implementação existente; reconciliar denominadores e alarme |
| Provider errors | Não identificado produtor dedicado nesta auditoria dirigida | **GAP A INVESTIGAR** por adaptadores de provedores canônicos; não simular provedor real |
| Fiscal rejection | Não identificado produtor dedicado nesta auditoria dirigida | **GAP A INVESTIGAR** sobre resultado determinístico fiscal; sem emitir documento real |
| Reconciliation | `product/cakto.py`: `nfcore_cakto_reconciliation_total` com outcome drift/aligned | **Somente comercial Cakto**; não equivale a reconciliação fiscal |
| Activation | `runtime/api.py`: `nfcore_commercial_activation_attempts_total`; `runtime/commercial_observability.py` inclui categoria activation | Implementação existente; provar fluxo de ativação e labels |

## Critérios e segurança

Manter `MetricsRegistry` como autoridade canônica, baixa cardinalidade, sem tenant/user/URL/token em labels e sem substituir o resultado fiscal. Não duplicar HTTP ou métricas de reconciliação com nomes paralelos. Priorizar auditoria de produtores reais de fulfillment, provider error, fiscal rejection e reconciliação fiscal, depois testes determinísticos e gates.

## Gates restantes

Confirmar CI/Governança pós-merge de `9045873`; obter prova de spans internos no staging apenas quando o deploy for autorizado; P09-T01 ainda não certificada. P09-T02 preparada por matriz, sem promoção de status. Não reiniciar P05, nem pedir contabilidade externa para fechar desenvolvimento interno. Próxima alteração em branch isolada com testes e AGENTS.md atualizados.

## Auditoria dirigida de produtores — 2026-10-16

- **Fulfillment comercial:** `application/commercial_fulfillment.py` implementa `CommercialFulfillmentService.process`, com caminhos de sucesso, replay e exceções, mas não injeta `MetricsRegistry` e não registra contador próprio. `runtime/commercial_observability.py` disponibiliza `CommercialTelemetryEvent.PROVISIONING`, porém a busca em `src/` não encontrou uso explícito `CommercialTelemetryEvent.PROVISIONING`; **nome de enum não comprova emissão real**.
- **Provider errors:** `CommercialTelemetryEvent.PROVIDER_DRIFT` e `FAILURE` são contratos existentes; busca de produção em `src/` não encontrou chamadas diretas desses membros. Um nome `nfcore_provider_errors_total` aparece em `tests/test_nfv1_p09_t02_metric_sample_integrity.py` como amostra sintética do `MetricsRegistry`, não como produtor. Classificação: lacuna ainda não resolvida.
- **Fiscal rejection:** busca de produtores `nfcore_*reject*` em `src/` não encontrou registro dedicado; validar o ponto determinístico de normalização de rejeições e evitar emitir métricas em um serviço paralelo.
- **Fiscal reconciliation:** `nfcore_cakto_reconciliation_total` é reconciliação *comercial*, não fiscal; nenhum `nfcore_*reconcil*` fiscal localizado em `src/` nesta auditoria dirigida.
- **Decisão:** instrumentar somente após localizar o contrato determinístico e o ponto autoritativo para cada resultado. Status T02 `IMPLEMENTED_NOT_CERTIFIED`, com quatro grupos ainda abertos; P09-T01 ainda precisa prova de spans no staging.
