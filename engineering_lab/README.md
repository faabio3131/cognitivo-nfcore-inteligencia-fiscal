# FM Engineering Governance Fabric — NFCore V2 laboratory

**Status: experimental foundation only; no production certification.**

This separate engineering-agent governance pilot does not modify the NFCore fiscal runtime, NFCore V1, or any existing AGENTS.md, execution tracker or master plan. Existing policies retain authority. No merge, deployment, sensitive operation, official fiscal emission or real credentials are authorized.

## Runbook

From the experimental branch:

- python3 scripts/fm_agent_governance.py audit
- python3 scripts/fm_agent_governance.py resume
- python3 scripts/fm_agent_governance.py preflight --actor claude-code
- python3 scripts/fm_agent_governance.py checkpoint --task LAB-01 --actor claude-code --status IN_PROGRESS --summary "Started"
- python3 scripts/fm_agent_governance.py verify --task LAB-01 --evidence engineering_lab/evidence/LAB-01.json

The deterministic preflight binds a mission to required authority hashes, the exact Git HEAD and branch. Tasks unlock only when dependencies are VERIFIED. Events and status are persisted; agents cannot mark their own mission VERIFIED. Checkpoints and evidence are not secrets stores. Keep only infrastructure inventory, runbooks and credential *references*, never private keys or passwords.

## EGM integration

EGM is the independent design-review component, **not** the policy engine. Install its upstream package only in an isolated compatible agent runtime after reviewing and pinning its version. Attach independent reviewer artifacts and evidence to the laboratory mission. This PR does not claim EGM is installed or that multi-provider handoff has been tested.

## Current limitations and next stages

The JSON mission state is a single-writer lab prototype, not an atomic multi-tenant DB. The engineering tenant here is a namespace, not enforced authentication isolation. Providers are not yet routed through a common execution API. The verify command only checks local evidence structure; remote CI, commit signatures and runtime evidence must be validated by a separate trustworthy verifier before any VERIFIED promotion. Production-grade implementation needs tenant RBAC, transactional mission locking, signed events, remote CI verifier, plugin adapters and cross-model interruption tests.

## Pilot validation

- Rule violation or wrong branch must be denied.
- Unverified dependencies must remain locked.
- False completion without evidence must be denied.
- Interrupted work must be recoverable via resume.
- EGM independent design critic and structural review must be tested against code.
- Handoff Claude/Code to Codex/Gemini must be demonstrated without duplicated operations.

Do not confuse successful unit tests with real remote or fiscal homologation.


## EGM — instalação REAL no executor (não no motor fiscal)

O arquivo ZIP original contém as sete skills em `skills/egm-*/SKILL.md`, personas em `agents/`, recursos em `resources/` e manifests de plugins. Estes arquivos NÃO estão instalados pelo motor `fm_agent_governance.py`; ele apenas controla missões. Não declare qualquer skill EGM executada apenas por ter gerado um relatório manual.

**Claude Code (ambiente de desenvolvimento autenticado):**

```sh
claude plugin marketplace add google/elephant-goldfish-model
claude plugin install egm@egm
claude plugin enable egm@egm
```

Iniciar uma nova sessão e invocar os comandos de skill publicados pelo plugin, por exemplo `/egm:egm-brainstorm`, `/egm:egm-draft` e `/egm:egm-review`. Confirmar que o runtime suporta subagentes independentes e suas permissões de leitura. Seguir `docs/claude.md` do próprio EGM, inclusive seu requisito de versão e isolamento de contexto.

**Codex CLI (ambiente autenticado):**

```sh
codex plugin marketplace add google/elephant-goldfish-model
codex plugin add egm@egm
```

Iniciar nova sessão e descobrir as sete skills do plugin. Seguir `docs/codex.md` do EGM. Os revisores Goldfish precisam de contexto fresco e leitura de seus arquivos de persona e standards. Se o host não suportar isolamento, a revisão deve ser marcada INCOMPLETE, não PASSED.

**Critério de teste obrigatório:** registrar versão do EGM, runtime, skill invocada, persona lida, artefato produzido, identidades/resultados de revisores e evidência do isolamento de contexto. O usuário deve distinguir EGM nativo executado de inspeção manual. Nenhum desses comandos foi executado na branch pelo simples ato de documentá-los. Não instalar scripts arbitrários nem copiar uma distribuição para o repositório fiscal.

**Separação de responsabilidades:** o EGM é o revisor; FM Governance guarda tarefas, políticas, evidências e estados. Não desenvolver clones improvisados das sete skills.
