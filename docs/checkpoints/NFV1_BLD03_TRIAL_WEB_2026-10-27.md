# NFV1-BLD-03 — cadastro de trial no Portal

Base: main e751ffb368828ea3387b0f49eeab5e467e2ce4ba (#259). Construção interna em andamento; não certificar Web publicada ou oferta comercial.

Delta: página trial.html na aplicação existente, catálogo governado, criação anônima sem cookies/HMAC/tenant fornecido pelo browser, recuperação com mesma chave após falha/reload e mensagens honestas de indisponibilidade. Origin é repassado intacto pelo proxy; consulta POST ao catálogo preserva a allowlist existente e permite Origin no browser same-origin. Sem novo serviço, migração, preço/duração definidos em runtime ou transporte de e-mail real.

Reuso: GovernedTrialService, pricing administration, provisioning, HumanIdentity, PasswordRecovery, subscription e PostgresPublicTrialAbuseGate. Testes browser incluem cenário real PostgreSQL em schema descartável único e mailbox sintética exclusivamente no harness loopback; criação canônica de tenant/OWNER/subscription, perda de resposta após commit, replay, ativação e login. Harness de teste nunca é composição de staging.

Validação local inicial: 19 testes dirigidos API/proxy/governança PASS; frontend 18 PASS, lint/typecheck/build PASS. Browser local bloqueado por download incompleto do Chromium e ausência de PostgreSQL; CI remota deve provar cenários completos antes de aceite. Não classificar falha de infraestrutura como teste aprovado.

PR #237 auditada: teste concorrente de admission gate ainda não integrado; exige remover dependência de contagem histórica das migrations e isolar schema antes de aproveitar. Será tratado neste bloco sem merge cego.

Pendências externas preservadas: binding administrativo GSM, catálogo/duração/origens aprovados e publicação explícita. Portal acompanha main e auto-deploy permanece habilitado; a autorização pontual da #259 não altera a regra permanente. Site fm-site-novo não foi alterado. BLD-03 não está DONE.
