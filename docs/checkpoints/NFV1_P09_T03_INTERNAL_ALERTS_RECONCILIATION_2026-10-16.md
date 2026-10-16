# NFV1-P09-T03 — Reconciliação de alertas internos (2026-10-16)

## Fonte de verdade e escopo

- Repositório: `faabio3131/kordena-fiscal-engine-v2`.
- PR #208 **MERGED** na `main`, merge SHA `1edf0107f47c5ce0277ed1a65c5cbfa3e506af5f`. CI pós-merge `38969810567` ainda em execução no momento deste registro.
- PR #209: branch `feat/nfv1-p09-t03-internal-alert-rules-20261016`, com `main` reconciliada no commit `64f4476`. Nova conexão de auditoria GSM `8d30ea1` e teste de falha do bootstrap `d63d6cc`; a certificação deste HEAD depende da CI Linux.
- A tarefa P09-T03 antecipada no cronograma refere-se à **construção interna controlada** dos alertas. Alertas operacionais reais e painéis/roteamento em ambientes externos ainda dependem dos gates P05/P09-T04/T05. Homologação fiscal real (SEFAZ/contabilidade) é etapa posterior, não um bloqueio de integração do código interno.

## Implementado / testes internos

- Avaliador de HTTP 5xx, erro de provider, backlog, dead-letter, falha do Worker, rejeição fiscal e taxa de rejeição NFC-e; contadores via delta, gauges por valor atual, séries ausentes/resetadas desconhecidas.
- Ciclos de API (`/health/ready`, `/internal/metrics`) e Worker (`cycle_completed`, `cycle_failed`) acoplados às autoridades canônicas de métricas; sem segunda API ou segundo Worker.
- `AlertRegistry` preexistente conserva a identidade, o escopo tenant/unidade e a deduplicação; testes dirigidos comprovam isolamento de tenants e rejeição de códigos não suportados.
- `nfcore_fiscal_authorizations_finalized_total` incrementa após NFC-e `mark_authorized`/`mark_rejected`, fornecendo denominador real; não estender automaticamente a NF-e/NFS-e.
- Expiração de certificado projetada exclusivamente de `CertificateReference` com escopo validado; limiares de 30 e 7 dias. Sem abertura de material de assinatura.
- `SecretAuditEvent` canônico já alimenta candidato `secret_failure` no bootstrap/uso do resolver GSM do Worker, sem material secreto; teste adicional no bootstrap real aguarda CI Linux com dependência Google.
- Para deploy Railway, há adapter de estados explícitos `SUCCESS`/`FAILED`/`CRASHED` com `unknown` para qualquer estado não reconhecido. **Ainda não existe coleta periódica autenticada desse status dentro do runtime**. A conexão do monitoramento do deploy a uma fonte operacional autorizada pertence ao fechamento de operação P09-T04/T05; não declarar esse alerta ativo em staging antes de provas.
- A inexistência de certificado fiscal real, de endpoint externo de cobrança ou de webhook de provider homologado não impede o fechamento da **construção interna**; não confundir com `PRODUCTION_APPROVED`.

## CURRENT Railway — somente leitura em 2026-10-16

Projeto lógico FM NFCORE **Staging** `b84b290d-f3b4-46a1-9023-0b761cb96b0d`, ambiente denominado `production` internamente no Railway, mas sem equivalência a produção fiscal.

| Serviço | Status | Réplicas | SHA deploy ativo |
| --- | --- | --- | --- |
| API | SUCCESS / online | 1/1 | `e4ffd584c4bc66632e80d1ab1448cdb67cd914ea` |
| Worker | SUCCESS / online | 1/1 | `e4ffd584c4bc66632e80d1ab1448cdb67cd914ea` |
| Portal | SUCCESS / online | 1/1 | `2f3689838cfbec1c6d2ffac614cb0eb364d91633` |
| PostgreSQL | SUCCESS / online | 1/1 | imagem de banco, não SHA Git de aplicação |

Zero alerts/warnings ativos e zero deploys com falhas na janela verificada. A diferença de SHA do Portal é **drift de paridade para P05**; não marcar jornada Web integrada no mesmo SHA sem deploy governado. Nenhum deploy/migration/credencial real executado nesta reconciliação.

## Gates ainda obrigatórios

1. CI e Governança da PR #209 no HEAD final; nunca copiar PASS de um SHA anterior.
2. Prova pós-merge da `main` no merge SHA exato.
3. Aceite de código P09-T03 separado da operação real do serviço de alertas; fontes Railway, certificados reais e integração externa fiscal só passam a `ACTIVE/EXTERNAL_CERTIFIED` com evidência de campo.
4. Antes de P05, consultar o cronograma/ledger e reconciliar T01/T02 com o drift atual (sem repetir GSM/migrations já resolvidos, nem inferir autorização de deploy).

**Autorizações:** o dono autorizou integrar PR #208 e #209 após gates; não autorizou implicitamente deploy, migração produtiva, DNS, novas credenciais ou ativação fiscal real.

## Complemento — Emissão real na autoridade de alertas do Worker

No escopo pré-claim certificado (`OutboxClaimSelection.scope`), o `build_production_worker_runtime` conecta o `InternalAlertMonitor` à `AlertRegistry` V2-13 existente por `StructuredLogAlertSink`. O sink registra apenas código e severidade, sem tenant/unidade/segredo nos logs. O observer usa as métricas reais do ciclo, publica o candidato, mantém deduplicação enquanto incidente persiste e resolve a chave quando o sinal desaparece; recorrência gera novo alerta. Workers sem escopo canônico **não** fabricam tenant para publicar alertas. O caminho fiscal/outbox permanece determinístico, sem mutação pela telemetria. Evidência: `tests/runtime/test_nfv1_p09_t03_worker_canonical_alert_delivery.py`, 2 PASS, integrado à matriz de 6 PASS, Ruff e Mypy direcionados PASS.

**Limite:** API com métricas agregadas e deploy Railway exigem destino/autoridade operacional externa para notificações ativas; o conjunto interno de regras e a interface de projeção não constituem monitoramento externo contínuo. Etapas P05/P09-T04/T05 continuam donas dessa ativação. Nenhum deploy, certificado real ou migração ocorreu.
