# NFV1-P05-T03 — Segurança do smoke Web (execução interna controlada)

**Data:** 2026-10-17
**Base auditada:** `main=339d186c3b317e6706be8beb0979477f3d03edc4`, merge PR #212; CI PR #1013 SUCCESS, Governança PR #434 SUCCESS; CI/Governança pós-merge aguardadas nesta abertura.
**Branch:** `feat/nfv1-p05-t03-internal-smoke-guard-20261017`.

## Objetivo estritamente delimitado

Incrementar o script canônico `scripts/ci/staging_smoke.sh`, já usado pelo driver de deploy, com um teste **fail-closed de autenticação** da API: `GET /v1/portal/bootstrap` sem sessão deve retornar exatamente `401`.

O script continua exigindo HTTPS e validando `/health/live`, `/health/ready`, `/runtime/profile` (environment staging, postgres, secret backend external, HTTPS e produção fiscal inativa) e o Portal raiz. Não introduzir segunda API, novo provedor, nova autenticação, alteração da UI ou banco adicional.

A nova sonda usa `curl --disable` para ignorar `~/.curlrc`, evitando que configurações locais adicionem inadvertidamente credenciais à solicitação que deve ser anônima. Status diferente de 401 ou falha de transporte é rejeitado.

## Matriz de testes sem recursos externos

Arquivo `tests/ci/test_nfv1_p05_staging_smoke_contract.py` substitui `curl` por executável local controlado, sem qualquer chamada de rede. No CI POSIX, comprova:
- cenário nominal: profile correto, API pronta, Portal disponível e bootstrap anônimo 401;
- falha se bootstrap anônimo for 200 (bypass da sessão) ou 403 (resultado fora do contrato de login exigido);
- falha para timeout/transporte do bootstrap;
- falha para runtime profile incorreto ou readiness indisponível;
- falha para URL API ou Portal não HTTPS.

Nos testes Windows a suíte POSIX não é considerada certificada localmente; validação final será no Linux da CI. A sintaxe shell e o Ruff são validados no checkout local.

## Limites de certificação

**IMPLEMENTAÇÃO INTERNA APENAS**: não executar este smoke contra serviços externos/provedores, não usar conta real ou tokens, não refazer deploy/migrations/backups. Os testes unitários e de integração já executados anteriormente para login, RBAC, tenant/unidade, recuperação e PostgreSQL continuam preservados.

**NFV1-P05-T03 NÃO é promovida a DONE_CERTIFIED com esta PR isolada.** O cronograma exige liveness, readiness, login, recovery, bootstrap autenticado, onboarding, Worker e DB contra o ambiente alvo. Evidências anteriores de health HTTP e Worker online são parciais; jornadas externas/homologação ficaram para o fim da construção por decisão explícita do proprietário.

**Próxima etapa técnica:** obter CI/Governança verdes na PR, integrar somente mediante autorização específica e preservar as pendências T03/T04/T05 no ledger até provas que atendam aos critérios completos. O staging publicado permanecerá no SHA anterior até um novo deploy autorizado, se necessário.
