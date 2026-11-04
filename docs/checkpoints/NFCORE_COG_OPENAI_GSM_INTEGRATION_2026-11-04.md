# NFCore — OpenAI API via Google Secret Manager (04/11/2026)

## CURRENT / escopo
- Repositório: faabio3131/nf-core-v001; base main: `7f1e17303505934aa6081b4a9146cccb236ee008`.
- Google Secret Manager de **produção**: projeto `fm-nfcore-prod` (número `646230745113`); segredo `nfcore-openai-api-key`, versão 1 habilitada; existência confirmada **somente por metadados**.
- Provedor cognitivo canônico: `cognitive/adapters/openai_compatible.py` e composição `cognitive/composition.py`.
- Chave OpenAI é payload bruto, **não** envelope de `SecretBinding` fiscal; nunca simular assinatura, CSC ou binding fiscal.

## Entrega interna
- Adaptador `runtime/ai_secrets.py` reutiliza `GoogleSdkSecretAccess` e `same_secret_version` da infraestrutura GSM canônica. Exige projeto, número, ID e versão exatos, CRC32C, formato de chave e endpoint **https://api.openai.com/v1**.
- Credenciais de workload são carregadas **somente** via `production_credentials` já existente: conta de serviço canônica `nfcore-api@fm-nfcore-prod.iam.gserviceaccount.com`, arquivo com permissão restrita, validade controlada, sem ADC.
- O segredo é lido somente quando houver chamada real elegível (lazy); ausência, falha de IAM, resposta adulterada ou versão incorreta são tratadas como indisponibilidade da chave, sem exibir material.
- Ligação ao mesmo `build_model_from_environ`, preservando `TierRoutedAdvisoryClient`, `QuotaGovernedAdvisoryClient`, auditoria e bloqueios existentes. Não foi criada outra API, provider duplicado ou segundo cofre.
- `NFCORE_COGNITIVE_AI_SECRET_MODE=pinned-gsm-openai-v1` é **opt-in** e, sem demais gates de IA durável, não libera chamadas reais.

## Configuração FUTURA para preflight (NÃO ativada)
- `NFCORE_COGNITIVE_AI_SECONDARY_PROVIDER=openai`
- `NFCORE_COGNITIVE_AI_SECONDARY_BASE_URL=https://api.openai.com/v1`
- `NFCORE_COGNITIVE_AI_SECONDARY_MODEL=<modelo aprovado e compatível>`
- `NFCORE_COGNITIVE_AI_SECONDARY_GSM_VERSION=1`
- `NFCORE_COGNITIVE_AI_SECRET_MODE=pinned-gsm-openai-v1`
- `NFCORE_GSM_PROJECT_ID=fm-nfcore-prod`, `NFCORE_GSM_PROJECT_NUMBER=646230745113`
- `NFCORE_GSM_API_SERVICE_ACCOUNT=nfcore-api@fm-nfcore-prod.iam.gserviceaccount.com`
- Identidade no arquivo canônico `NFCORE_API_GSM_CREDENTIAL_FILE` com metadados de versão e validade exigidos por `production_credentials`.
- Flags `NFCORE_COGNITIVE_ENABLED` e `NFCORE_COGNITIVE_DURABLE_AI_ENABLED` **OFF** até aprovação específica e quotas duráveis, auditoria, domínio, RBAC, custo e testes em ambiente controlado.
- A permissão `roles/secretmanager.secretAccessor` deve ser estudada e, depois de autorização, concedida **apenas no recurso exato** à identidade API; confirmar ausência de grants amplos. Nenhum IAM foi modificado.

## Gates e limites
- Rodar Ruff, Mypy strict, Pytest dirigido, CI/Governança remotos e revisar SHA real antes de merge.
- Esta entrega **não** testa se o token funciona na OpenAI, não acessa valor real no Google Cloud e não habilita cobranças de API.
- **Não autorizado:** merge em main sem ordem específica, promoção `production`, deploy Contabo, alterações IAM produtivas, migrations ou ativação fiscal/comercial/IA.
