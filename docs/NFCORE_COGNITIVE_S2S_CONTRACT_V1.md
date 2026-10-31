# Contrato S2S NFCore → Core Cognitivo Central FM — v1 (PROPOSTA)

**Estado:** `PROPOSED`. Nada aqui foi homologado com o Command. O endpoint abaixo é um
**caminho proposto**, não o `/api/core/query` do Command (interface interna, outro contexto
de autenticação). O mantenedor do Command precisa aprovar, ajustar e publicar este contrato
antes de qualquer chamada real. Classificação até lá: `INTEGRATED_NOT_EXTERNALLY_CERTIFIED`.

Implementação cliente: `src/kordena_fiscal/cognitive/adapters/central_fm.py`
(testes de contrato em `tests/cognitive/test_central_fm_adapter.py`).

## 1. Princípios

- A credencial de IA (Gemini/OpenAI/Anthropic) é da FM e vive só no backend central. O NFCore
  **nunca** recebe nem envia chave de modelo, token de usuário ou senha.
- Autenticação workload-to-workload por **assinatura HMAC-SHA256** (mesmo esquema do
  `WebhookSecurity`): `t=<unix>,kid=<id>,v1=<hex>` sobre `"<t>." + corpo`. A chave é resolvida
  do Vault por **Secret Reference**; rotação por `kid`.
- Janela anti-replay: 300 s (passado) e 30 s (futuro). Idempotência por `Idempotency-Key`
  (= `requestId`): repetir o mesmo `requestId` não pode cobrar duas vezes.
- Isolamento: `tenantId`/`unitId` no corpo; o Command mapeia para o tenant dele e **rejeita**
  se o par produto+tenant não estiver vinculado à chave (`kid`).
- O NFCore já envia o contexto **redigido** (CNPJ, CPF, chave de acesso, e-mail, telefone,
  PEM, tokens, cartão mascarados) e separa dado não confiável por marcador com nonce.

## 2. Requisição

`POST {endpoint}` — `Content-Type: application/json`

Cabeçalhos: `X-FM-Contract-Version: nfcore.cognitive.s2s/v1`, `X-FM-Product: nfcore`,
`X-FM-Correlation-Id`, `X-FM-Signature`, `Idempotency-Key`.

```json
{
  "contractVersion": "nfcore.cognitive.s2s/v1",
  "productId": "nfcore",
  "tenantId": "…", "unitId": "…",
  "requestId": "…", "correlationId": "…",
  "capability": "cognitive.explain_rejection",
  "contextHash": "sha256…",
  "system": "instruções fixas",
  "trustedFacts": "[id] kind (origem): chave=valor; …",
  "untrustedData": "<<DADOS-nonce>> … <</DADOS-nonce>>",
  "boundary": "DADOS-nonce"
}
```

Capabilities: `cognitive.explain_rejection`, `cognitive.suggest_classification`,
`cognitive.explain_reconciliation`, `cognitive.answer_accountant_question`.

## 3. Resposta (200)

```json
{
  "contractVersion": "nfcore.cognitive.s2s/v1",
  "requestId": "<igual ao enviado>",
  "sections": [{"kind": "hypothesis|action", "text": "…", "evidenceIds": ["…"]}],
  "provider": "…", "model": "…", "modelVersion": "…",
  "usage": {"inputTokens": 0, "outputTokens": 0, "costMicroBrl": 0}
}
```

O NFCore valida de forma estrita (versão, `requestId`, tipos, no máximo 12 seções, 64 KB) e
**descarta** qualquer seção `fact`/`source`, sem citação válida, com código ou valor fora da
evidência, com alegação de execução ou com dado sensível.

## 4. Erros

| HTTP | Significado no NFCore |
|---|---|
| 401/403 | `provider_denied` — IA indisponível, operação fiscal segue |
| 429 | `provider_rate_limited` (cota/limite do plano) |
| 5xx / timeout / sem conexão | `provider_unavailable` (circuit breaker abre após falhas) |
| outros 4xx, 3xx, corpo inválido | `provider_malformed` (redirecionamento nunca é seguido) |

Qualquer falha degrada para a resposta determinística; nenhum erro bloqueia emissão,
consulta, cancelamento, conciliação, login ou Portal.

## 5. Decisões que dependem de pessoas

| Decisão | Dono |
|---|---|
| Caminho/host do endpoint, versão e publicação do contrato | mantenedor do Command |
| Mapeamento tenant NFCore ↔ tenant Command e vínculo por `kid` | Command + Fábio |
| Provisionar a chave HMAC no cofre (Secret Reference) | **Fábio** |
| Modelos, orçamento, cotas por plano, preço | **Fábio** |
| Política de dados/LGPD e DPA do fornecedor de IA | Fábio + jurídico |
