## FM NFCORE V1 — Evidência obrigatória de entrega

> Antes de preencher, ler `AGENTS.md`, `docs/NFCORE_V1_EXECUTION_LEDGER.md` e `docs/checkpoints/NFV1_CURRENT_RECONCILIATION_ANTI_REWORK_2026-10-16.md`. Este modelo não substitui a leitura ao vivo do GitHub/Railway.

- **Tarefa canônica (NFV1-Pxx-Tyy):**
- **HEAD main auditado (SHA + data):**
- **CURRENT → TARGET / escopo congelado:**
- **Autoridade canônica reutilizada (API/tenant/RBAC/persistência):**
- **Código e PRs anteriores consultados — prova de não duplicação:**
- **Critérios de aceite do cronograma e evidências por critério:**
- **Testes executados e resultado (Ruff/Mypy/Pytest/PG/Web/segurança conforme escopo):**
- **CI + Governança no HEAD exato (IDs, conclusão; preencher após execução):**
- **Impacto em staging / versão publicada e provas E2E (ou NÃO COMPROVADO):**
- **Segredos, migration, deploy, DNS ou ação irreversível? autorização humana específica:**
- **Classificação:** IMPLEMENTED_NOT_CERTIFIED / DONE_CERTIFIED_INTERNAL / DONE_CERTIFIED_OPERATIONAL / BLOCKED_EXTERNAL
- **Blockers e riscos residuais:**
- **Próxima tarefa autorizada — nenhuma fase pulada:**

### Gate de merge

Não marcar tarefa `[x]` por PR aberta, testes locais ou CI da PR isoladamente. Confirmar HEAD, autorização, merges, CI/Governança pós-merge e runtime (se aplicável). Só depois registrar checkpoint e atualizar ledger. Divergência entre GitHub e ledger obriga reconciliação anterior a novo código. Proibido completar campos com evidências presumidas.
