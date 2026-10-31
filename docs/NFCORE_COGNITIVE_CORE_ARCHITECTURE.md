# NFCore — Core Cognitivo Fiscal V1: arquitetura

**Estado:** `PENDING_IMPLEMENTATION` → fundação em construção (PR de fundação).
**Repositório:** `faabio3131/cognitivo-nfcore-inteligencia-fiscal` (cópia de `nf-core-v001@207fbf2`).
**Regra-mestre:** *o Core coordena e raciocina; os serviços determinísticos validam e executam.*
**Pacote:** `src/kordena_fiscal/cognitive/`.

## 1. Objetivo

Dar ao NFCore a maior capacidade cognitiva possível **sem** dar autoridade fiscal à IA.
O core entende rejeições, classificação tributária, conciliação e dúvidas do contador, sempre
com evidência e proveniência, e continua útil mesmo com a IA desligada.

## 2. Princípios (invariantes testados)

1. **Fatos são determinísticos.** Seções `FACT` e `SOURCE` nascem do catálogo e das evidências
   autorizadas. O modelo **nunca** escreve fatos; só hipóteses e ações sugeridas.
2. **Consultivo.** Nenhum caminho de escrita: a IA não emite, assina, transmite, cancela,
   inutiliza, altera imposto nem salva classificação. O resultado é `advisory_only`.
3. **Fail-open da operação, fail-closed da segurança.** Falha, timeout, circuito aberto, quota
   ou ausência de provedor => resposta **determinística** (baseline). Falha de autorização,
   escopo ou tenant => `DENIED`, sem dados.
4. **Tenant/unidade isolados.** Toda evidência carrega `tenant_id`/`unit_id`; divergência do
   escopo da requisição aborta antes de qualquer chamada ao modelo.
5. **Minimização e redação.** CNPJ, CPF, chave de acesso, e-mail, telefone, PEM, tokens e PAN
   são mascarados antes de sair do processo e também na saída (defesa em profundidade).
6. **Dado não confiável é dado.** Texto de XML, retorno de provedor e a pergunta do usuário
   entram em blocos cercados por *nonce*, nunca em instruções.
7. **Resposta do modelo é validada.** Cada seção precisa citar evidências existentes; números e
   códigos não presentes na evidência são descartados; alegações de execução e vazamento são
   barradas. Se nada sobra, volta ao baseline.
8. **Sem inventar norma.** O catálogo declara `review_status`. Entradas sem revisão normativa
   humana são apresentadas como tal. Código desconhecido => `INSUFFICIENT_BASIS`.
9. **Sem segredo, sem credencial de IA do cliente.** A credencial é da FM, central, via
   Vault/Secret Reference. Nenhuma chave de modelo neste repositório.
10. **Auditável.** Cada uso gera evento de auditoria (ids e hashes, nunca prompt integral) e
    registro de uso/custo idempotente por `request_id`.

## 3. Camadas

```
Portal/API (sessão, RBAC, tenant/unidade)            [T04, fora da fundação]
        │
        ▼
CognitiveAdviceService  ── orquestra e nunca levanta por falha de IA
  1 autorização de capability (fail-closed)
  2 isolamento de escopo das evidências (fail-closed)
  3 redação + ContextPack (fatos confiáveis × blocos não confiáveis)
  4 baseline determinístico (catálogo + evidências)   ← sempre calculado
  5 entitlement/quota (nega só a IA)
  6 auditoria de início (sem ela, sem IA)
  7 chamada ao modelo: bulkhead + circuit breaker + deadline
  8 OutputGuard (grounding, ações proibidas, vazamento)
  9 fusão: FACT/SOURCE do baseline + HYPOTHESIS/ACTION validadas
 10 ledger de uso + auditoria final
        │
        ▼
Portas (Protocols): AdvisoryModelPort · EntitlementPort · UsageLedgerPort · AuditSinkPort
        │
        ▼
Adaptadores: Null (padrão, IA desligada) · Central FM S2S (T01/T03, após contrato aprovado)
```

## 4. Capacidades

| Capability | Jornada | Evidência determinística |
|---|---|---|
| `cognitive.explain_rejection` | T04 | código/status de rejeição, estado do documento, catálogo |
| `cognitive.suggest_classification` | T05 | `TaxRuleOutcome`, catálogo CST/cClassTrib/NCM vigente, regime |
| `cognitive.explain_reconciliation` | T06 | `ReconciliationIssueCode`, estados e divergências |
| `cognitive.answer_accountant_question` | T06 | evidências fornecidas; sem base => incerteza explícita |

A fundação implementa contratos, segurança e a jornada de **rejeição** de ponta a ponta
(baseline + modelo). As demais entram em PRs seguintes, reutilizando a mesma base.

## 5. Contrato de resposta

`AdviceResult`: `status`, `sections[]` (`FACT` / `HYPOTHESIS` / `ACTION` / `SOURCE`, cada uma
com `evidence_ids`), `provenance` (correlationId, requestId, schemaVersion, hash do contexto,
evidências, provedor/modelo/versão, achados do guard, motivo de degradação, latência, uso),
`advisory_only=True`, `requires_human_approval=True`.

Status: `ADVISED` (modelo validado) · `BASELINE_ONLY` (determinístico; IA indisponível/negada)
· `INSUFFICIENT_BASIS` (sem evidência para responder) · `DENIED` (sem autorização/escopo).

## 6. O que fica fora desta fundação (com dono)

| Item | Depende de |
|---|---|
| Contrato S2S NFCore↔Command (T01) e adaptador real (T03) | contrato aprovado pelo mantenedor do Command |
| Credencial central de IA | **Fábio** coloca no cofre; eu nunca digito segredo |
| Cota/plano `cognitive.advice` (T07) | política de preço aprovada por Fábio |
| Rota de API e superfície no Portal (T04–T06) | PRs seguintes |
| Catálogos oficiais (rejeição, CST, cClassTrib, NCM) | curadoria/revisão humana e artefatos oficiais com SHA-256 |

## 7. Evolução (PRs pequenos, cada um testado)

1. **Fundação** — contratos, redação, ContextPack, guard, resiliência, serviço, rejeição.
2. **Classificação (T05)** — sugestão CST/cClassTrib/NCM com catálogo vigente, sem write path.
3. **Conciliação e contador (T06)**.
4. **Adaptador central FM (T03)** — HTTP S2S assinado, após contrato T01.
5. **Entitlement, custo e auditoria persistente (T07)**.
6. **API + Portal (T04–T06 UI)** e certificação integrada (T08).

## 8. Não objetivos

Emitir, assinar, transmitir, decidir imposto, substituir contador, fazer homologação externa,
deploy, migration. Nada aqui altera o motor fiscal determinístico existente.
