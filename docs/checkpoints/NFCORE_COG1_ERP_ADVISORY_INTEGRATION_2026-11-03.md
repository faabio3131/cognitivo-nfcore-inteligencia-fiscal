# NFCore COG-1 — integração governada do pacote de evolução — 03/11/2026

Base auditada: `main@d810dca6f3b4ab7ca0ffd7d1a8c1b81cee9a3183`.
Origem: `EVOLUCAO_FASE1_CONECTORES_E_COGNITIVO.zip` fornecido pelo Diretor.
Estado: **IMPLEMENTED_CANDIDATE / NOT_DEPLOYED / NOT_FISCALLY_AUTHORITATIVE**.

## Escopo incorporado

- Pré-normalização estrita para exemplos de pedidos Bling v3 e Tiny, sem endpoint de rede, sem transporte externo e sem emissão.
- Matriz cruzada apenas consultiva: valida dimensões estruturais, retorna `REVIEW_REQUIRED`, sem inventar CST/cClassTrib.
- Testes adversariais para campos críticos ausentes, valores inválidos e inexistência de determinação tributária genérica.

## Limites do pacote original que não são aprovados como produção

O original atribui automaticamente CST/cClassTrib e base legal a exportação,
Simples Nacional e regime normal a partir de CFOP/CRT genéricos, sem vincular
catálogo completo pinado, versão, vigência, situação do contribuinte,
operações especiais e evidência documental. Essa segunda autoridade fiscal
é rejeitada pelo princípio constitucional do NFCore.

O original também declara suporte a Omie/ContaAzul sem implementação,
aceita NCM/CFOP e quantidades default e contém um verificador HMAC sem
contrato de autenticação específico por provedor. Estes elementos não foram
promovidos para rotas produtivas.

## Dependências para ativação futura

Contrato canônico do ingresso, autenticação do provedor, assinatura verificada
conforme documentação de cada plataforma, proteção replay, idempotência
persistente, mapeamento tenant/unidade por credencial governada, rate limits,
auditoria e consentimento. Catálogos oficiais RTC-01 completos e regras
verificadas para a classificação. Homologação de campos, documentos e API
reais requer evidência externa. Metas de latência e alegações de ganho
operacional do roadmap são **TARGET**, sem medição.

Não são alterados: `TaxRuleEngine`, catálogo RTC, autenticação,
roteador HTTP, Worker, banco produtivo, Contabo ou branch `production`.
