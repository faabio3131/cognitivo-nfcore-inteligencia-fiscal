# NFCore V1 — Trial comercial conectado à autoridade de segredos do staging
Data: 2026-10-18. **Candidata técnica de wiring — não ativação comercial real.**

## Diagnóstico CURRENT confirmado
- `GovernedTrialService` e `POST /v1/commercial/trials` já existem, usam o PostgreSQL e o fluxo canônico de ativação por e-mail. O endpoint é **S2S assinado**; o browser não pode fabricar `X-NFCore-Signature`.
- O entrypoint anterior só compunha `commercial_trial_security` a partir de `NFCORE_DEV_*` em development/test. Em staging, a rota estava ausente por falta de signer verificador governado, não por inexistência do domínio.
- A API já utiliza uma identidade GSM de `nfcore-api` para prova fiscal piloto. **A mesma identidade de execução pode acessar novas referências comerciais SOMENTE depois de concessão IAM e binding canônico separados**. Nunca reutilizar o segredo do webhook fiscal para trial.
- GET /runtime/profile (Railway): `commercial_trial_configured=false`, `pricing_catalog_published=false`, `commercial_first_party_acquisition_configured=false`, `commercial_checkout_provider_configured=null`; GET /v1/commercial/offer: `trial_enabled=false`, `purchase_enabled=false`. Isto continua REAL mesmo com código de composição publicado, até que inputs externos sejam configurados.

## Target implementado nesta candidata
Novo adaptador de composição em `runtime/staging_commercial_ingress.py`, acionado pelo mesmo `create_runtime_app`, não por nova API ou lógica comercial:
- Opt-in por `NFCORE_STAGING_COMMERCIAL_INGRESS_MODE=scoped-staging-gsm-v1`, somente com `NFCORE_ENVIRONMENT=staging` e a identidade API GSM existente `NFCORE_API_GSM_MODE=scoped-staging-sa-v1`.
- Um ou ambos os canais podem ser habilitados separadamente: `TRIAL`, `ACQUISITION`, respectivamente às dependências já existentes `commercial_trial_security` e `commercial_acquisition_security`.
- Cada canal exige binding **durável** ativo do `nfcore-api` com assinatura externa, project pinned `fm-nfcore-staging`, scope separado `tenant_id=nfcore-platform`, `unit_id=null` e `purpose=commercial-trial-ingress` ou `commercial-acquisition-ingress`, com referência, versão, recurso e provider registrados. Distinção de recurso e referência entre canais obrigatória.
- `DurableGsmReader`/ `GoogleSignatureSecretBackend`/ `SecretResolver` e `WebhookSecurity` existentes fazem resolução, verificação de envelope, rotação/revogação e HMAC; validação de material real no bootstrap. Se env, IAM, binding, material ou janela de validade estiver incorreta, falha fechada — sem fallback para secrets dev e sem vazar segredo em erro.
- `GovernedTrialService` conserva domínio, antifraude por e-mail, idempotência, assinatura canônica, provisioning e ativação; não há segunda persistência/tenancy/autorização.

## Inputs operacionais necessários para ligar o trial seguro
Estes itens exigem execução por autoridade de segredos apropriada; **não foram criados nem alterados** nesta PR:
1. Criar (ou localizar) uma versão da assinatura comercial no Google Secret Manager do projeto de staging, com material suficiente, envelope do `SecretBinding` canônico e recurso separado do piloto webhook.
2. Vincular metadata `SecretBinding` à autoridade de plataforma no banco, com revisão governada, escopo `nfcore-platform`/sem unidade, propósito `commercial-trial-ingress`, `workload_id=nfcore-api`, `kind=signature`, `provider_id=google-secret-manager`, versão, estado e validade.
3. Conceder a identidade `nfcore-api` acesso **somente** ao recurso comercial explicitamente aprovado, com auditoria IAM; não criar outra service account por conveniência.
4. Configurar no Railway (sem imprimir valores secretos) `NFCORE_STAGING_COMMERCIAL_INGRESS_MODE` e as três referências por canal: `NFCORE_STAGING_COMMERCIAL_TRIAL_REFERENCE`, `NFCORE_STAGING_COMMERCIAL_TRIAL_VERSION`, `NFCORE_STAGING_COMMERCIAL_TRIAL_RESOURCE`. A API GSM existente deve estar saudável.
5. Apresentar caller S2S autorizado (por exemplo FM Command) para assinar e enviar o trial. A rota S2S não deve ser chamada diretamente pelo navegador nem fornecer a assinatura ao cliente.
6. Publicar **preços e planos efetivamente aprovados pelo proprietário** com `trial_days > 0`; sem eles `GovernedTrialService.begin` rejeita. Não inventar preços/planos nem converter `trial_enabled` público automaticamente com base somente na configuração do signer.
7. Fazer Web/landing gerenciar a solicitação de teste via fluxo governado do Command ou futuro ingresso público protegido e expressamente aprovado. Endpoint assinado no backend != formulário aberto e pronto ao usuário.

## Gates de construção × homologação (separados)
- **Implementação interna de integração**: modulo/composition + CI e testes negativos/positivos.
- **Ativação no staging**: metadados reais governados, canal autenticado, pricing aprovado, reset real, UI e uma jornada controlada com provas; autorização específica antes de mudar secrets/IAM e deployments.
- **Homologação final/produção**: checkout real, antispam, conformidade comercial, observabilidade, aprovação humana, fiscal real e lançamento; não bloquear a construção antes disto.

**Proibições:** reusar `NFCORE_DEV_*` no staging, reutilizar assinatura fiscal do piloto, criar segunda API/registro de tenant, desbloquear o checkout ou publicar preço fictício só para deixar estado verde. Nunca anunciar `trial_enabled=true` sem uma jornada de inscrição Web real com canal seguro e política aprovada.
