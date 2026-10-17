# NFV1-P05 — Wiring interno fiscal/comercial controlado (candidata)

**Data:** 2026-10-17
**Base auditada:** main `976ae4e223accd603af710d083b18ca47b95b614`, CI #1007 e Governance #428 SUCCESS.
**Branch de execução:** `feat/nfv1-p05-controlled-development-wiring-20261017`.

## Objetivo e limites

Completar um primeiro elo de desenvolvimento/teste para operações internas, reutilizando o runtime canônico e mantendo testes/homologação externas para a fase final. **Esta candidata não implanta staging, não altera PostgreSQL/segredos reais e não certifica lançamento comercial ou efeitos fiscais.**

A composição fiscal existente já recebe `fiscal_operation_handlers` e protege o caminho através de `CanonicalFiscalOperationPath`, RBAC e tenant/unidade. O ingress comercial existente já recebe `command_secret_resolver`, `commercial_acquisition_security` e `commercial_trial_security`. Não introduzir novo Core, API, banco de dados, RBAC ou frontend.

## Implementado — opt-in estrito

1. `development_fiscal_ingress`: somente `NFCORE_ENVIRONMENT=development|test` e `NFCORE_DEV_FISCAL_QUERY_MODE=synthetic_pending`. Usa **o FakeFiscalOperationsGateway já existente** através de `FiscalOperationsClient` e `build_provider_query_handler`, registrando somente `queryFiscalDocument`. Resultado rotulado `simulation=true`, `official_fiscal_evidence=false`, `provider_origin=synthetic_local_only`, status `pending`, sem protocolo. Não configura emissão, cancelamento, inutilização, reconciliação ou homologação; nenhum write/transport fiscal real.
2. `development_command_resolver`: somente `development|test`, opt-in por conjunto completo de metadados e segredo efêmero local. Reutiliza `CommandBinding.scope`, `InMemorySecretBackend` e `SecretResolver` já existentes. **Não cria binding persistido**, contrato comercial, checkout ou cliente. Uma operação real de webhook continua exigindo binding aprovado/configurado na persistência canônica, assinatura válida e restante das dependências de checkout/entrega/readiness. Um grupo incompleto/segredo curto/ref inválida impede o bootstrap local.
3. O entrypoint `runtime/api.py` passa apenas os resultados dessas factories ao `create_runtime_app` existente. Para `staging|production`, os helpers retornam `{}`/`None`; não há criação ou leitura de segredo cloud por este código.

### Configuração de execução local — somente nomes, não valores

- `NFCORE_DEV_FISCAL_QUERY_MODE` — valor exato `synthetic_pending` para ligar consulta simulada;
- `NFCORE_DEV_COMMAND_BINDING_ID`, `NFCORE_DEV_COMMAND_KEY_ID`, `NFCORE_DEV_COMMAND_SECRET_REFERENCE`, `NFCORE_DEV_COMMAND_HMAC_SECRET` — **todos** obrigatórios para usar o resolver local; mínimo 32 bytes do segredo, referência opaca canônica, versão 1; binding persistido da mesma identidade obrigatório para processamento real;
- `NFCORE_DEV_ACQUISITION_KEY_ID`/`NFCORE_DEV_ACQUISITION_HMAC_SECRET` e `NFCORE_DEV_TRIAL_KEY_ID`/`NFCORE_DEV_TRIAL_HMAC_SECRET` já existiam; este trabalho não altera suas políticas.

**Importante:** com persistência default SQLite, o runtime `create_runtime_app` não cria a composição durável PostgreSQL. Para testar jornadas autenticadas e comerciais completas, usar o PostgreSQL descartável/local com o schema e dados de teste governados, sem conectá-lo ao staging. Nunca usar Cakto real, conta de cliente, token fiscal real ou conta Command produtiva nesses testes.

## Current → Target e gates

| Bloco | Current antes da mudança | Target desta candidata | Fora do escopo |
| --- | --- | --- | --- |
| Fiscal query | adapter de consulta já pronto mas não injetado no entrypoint | consulta de status sintético identificável local | emissão/cancelamento fiscal e homologação externa |
| Command webhook | `SecretResolver` aceito por `create_runtime_app` mas não ligado pelo entrypoint de dev | resolver de HMAC local sob escopo canônico | binding automático, checkout real, ativação de billing |
| Portal | UI premium e contratos existentes | sem alteração visual, mesmo frontend canônico | reconstrução de frontend |
| Segurança | autenticação e tenant/unidade no caminho canônico | sem bypass, testes negativos e fail-closed por ambiente | credencial de terceiros ou incremento de permissões |

**Gates locais deste bloco:** testes dirigidos de helpers e provider query; `ruff check`; `ruff format --check`; `mypy` quando disponível; `npm run test:frontend`; `python scripts/check_nfcore_plan.py`; CI/Governança da PR em HEAD exato. Registre resultados somente depois de executar.

**Pendente de prova:** runtime API completo sob PostgreSQL Linux de teste, autenticação e operações Portal E2E, integração real/contratos de billing Command, infraestrutura Web unificada e deploy governado. A integração externa é diferida, mas a segurança interna não.

**Governança:** PR Draft, sem merge até autorização específica. Testes sintéticos não são homologação fiscal nem pagamento real. Não marcar tarefas P05-T01..T05 como DONE_CERTIFIED por este recorte.
