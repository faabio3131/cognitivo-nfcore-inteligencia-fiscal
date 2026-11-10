# EGM original — teste nativo de sete funções no NFCore V2

**Fase atual: executar upstream sem alterações, antes de incorporar FM Governance Fabric.**

## Fonte e instalação
- Repositório EGM original: google/elephant-goldfish-model
- Revisão fixada (git submodule): `6d2af49f635515a472ce0dbba375c62b73dace26`
- Não editar skills, personas, adapters ou padrões do EGM.
- Clone com `git clone --recurse-submodules` ou, em checkout existente, `git submodule update --init --recursive`.
- EGM não funciona sozinho apenas porque seus arquivos estão no GitHub. É necessário um runtime Claude Code/Codex/Antigravity com subagentes isolados. O GitHub Action de packaging valida a integridade do pacote, **não** executa modelos.

### Claude Code (exemplo, no runtime autenticado)
```sh
claude plugin marketplace add google/elephant-goldfish-model
claude plugin install egm@egm
claude plugin enable egm@egm
```
Usar Claude Code 2.1.271+ e reiniciar a sessão. Os comandos disponibilizados incluem `/egm:egm-bootstrap`, `/egm:egm-brainstorm`, `/egm:egm-draft` e `/egm:egm-review`. Para review-loop e resolve, seguir diretamente o SKILL.md conforme docs/claude.md: não invocar via ferramenta Skill quando ela não suporta as skills com disable-model-invocation.
Para revisão Goldfish confirmar `omitClaudeMd: true`, contextos frescos e permissão de leitura das personas. Se a ferramenta não criar subagente isolado, registrar INCOMPLETE.

### Codex CLI
```sh
codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```
Usar as sete skills a partir do plugin instalado, com subagentes `fork_context: false` / `fork_turns: "none"` quando disponíveis, verificando exclusão de histórico e instruções do host; veja `third_party/elephant-goldfish-model/docs/codex.md`.

## Bateria original 1–7 (executar uma skill por vez, sem modificar o produto)
1. **egm-bootstrap:** inventário e documentação do subtree `src/kordena_fiscal/cognitive/`. Gerar relatórios somente no diretório experimental ou branch de execução, sem sobrepor README em main.
2. **egm-brainstorm:** identificar lacunas na arquitetura do core cognitivo com base no código e `docs/NFCORE_COGNITIVE_CORE_ARCHITECTURE.md`.
3. **egm-draft:** redigir proposta de melhorias em documento separado, sem implementação.
4. **egm-review:** acionar Goldfish frescos para revisar o documento do passo 3.
5. **egm-review-loop:** executar os estágios nativos na ordem e registrar cada revisor, achados e revisões.
6. **egm-resolve:** reconciliar os achados com evidência, sem promover mudanças na arquitetura fiscal.
7. **egm-drift-report:** comparar a arquitetura documentada com código `src/kordena_fiscal/cognitive/`, diferenciar alegação documental de implementação e registrar diffs.

### Evidência obrigatória para CADA execução
Registre runtime/version, SHA do EGM, skill invocada, artefato de saída, revisores reais utilizados, resultado (PASS / FAIL / INCOMPLETE), logs/referências do runtime e limites. **Nunca inventar execução**. O EGM nativo deve operar seguindo sua própria sequência de revisão; a ordem acima é da bateria de teste, não substitui dependências internas de seus workflows.

### Exclusão das camadas FM
Os arquivos `engineering_lab/` são experimentos anteriores separados e não devem ser passados como políticas adicionais aos revisores EGM neste primeiro experimento, exceto limites obrigatórios de segurança e isolamento do próprio ambiente. O AGENTS.md existente continua sendo autoridade de segurança para o executor; não conceder write ou deploy a subagentes de revisão. Não alterar, executar nem aprovar produção, fiscal real ou V1. Nenhum merge automático.

## Critérios
O pacote fica READY quando checkout/submódulo, 7 skills e 10 personas são validados no GitHub Actions. **TESTED** só após sete execuções nativas demonstradas. O teste multiagente é obrigatório para considerar Review e Review Loop aprovados.
