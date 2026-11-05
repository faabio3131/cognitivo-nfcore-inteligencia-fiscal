# NAT-03/04 — continuidade e autorização NF-e MG

Data: 05/11/2026. Escopo: construção interna parcial; não homologação oficial.

## CURRENT confirmado antes da alteração

Repositório atual: faabio3131/nf-core-v001 (renomeado do histórico).
main: 3f56084041fc9cd441af9a61dcc9532ba6090a85.
PR #356 integrada; #359 integrada; #358 aberta para production, sem execução nesta entrega.
PR #360 Draft: feedf8b41085914b831c9585bec1b34675742008.
Governança #1120 SUCCESS; CI #1689 ainda em execução na consulta inicial.
A base desta branch é exatamente o HEAD da #360; preservar sua revisão separada.

## CURRENT → TARGET e impacto congelado

CURRENT: catálogo MG 55/65 com dez operações; transporte de autorização fixo SP.
TARGET deste incremento: mesma implementação SOAP de autorização com alvo MG NF-e 55,
selecionado exclusivamente por configuração de engenharia, com validação estrita
da identidade fiscal. Não cria novo router, persistência, API, auth ou regra tributária.

Arquivo comum evoluído: gateway/nfe_sp_homologation.py. O nome histórico é preservado
para compatibilidade de imports; SefazSpHomologationGateway permanece wrapper SP.
SefazHomologationAuthorizationGateway implementa o transporte compartilhado.
Fonte de endpoint MG: mg_official_homologation_catalog.py da #360.
ProviderRegistry e DurableProviderBindingResolver continuam autoridades da aplicação.
A configuração deste adapter não cria nem aprova binding e não altera readiness.

Mapa de impacto: autorização SOAP/mTLS e metadados de provider; wrapper SP,
métodos auxiliares e formato AuthorizationResult preservados. Redirecionamento HTTP
é bloqueado também em SP para impedir mudança de destino de comunicação mTLS.
Sem alteração de DB/migrations, Portal, DNS, credenciais, production ou Contabo.

## Critérios de aceite e controles

- Alvo MG exige chave UF 31/modelo 55, XML único com Id, cUF/mod/tpAmb e CNPJ coerentes.
- Rejeição de escopo antes de consultar Vault; nenhuma seleção implícita de SP.
- Assinatura MG pertence ao Vault: XML previamente assinado é recusado enquanto
  não existir validação criptográfica explícita para esse caminho.
- Callback XSD confiável obrigatório na construção MG e executado sobre XML assinado
  antes do transporte. Deve lançar exceção em schema inválido.
- A1 continua validado por emitente/escopo; SOAP, TLS e respostas reutilizam código atual.
- Resposta deve identificar MG, homologação, chave/protocolo e digest do XML assinado.
- Sem replay automático de mutação fiscal e sem redirecionamento HTTP.
- Endpoint não vem do navegador, tenant, inventário municipal ou URL livre.

## Fontes oficiais reconferidas

- https://portalsped.fazenda.mg.gov.br/spedmg/nfe/webservices/
- https://portalsped.fazenda.mg.gov.br/spedmg/nfce/web-services/

As páginas sustentam os endereços de referência; não constituem XSD/WSDL congelado,
aprovação do contribuinte ou prova de homologação. Fonte não foi artificialmente
marcada com hash de bytes não capturados.

## Evidência e limitações

Testes usam certificado RSA PKCS#12 sintético, namespace SOAP e respostas locais.
O validador XSD é um spy nos testes de transporte: estes testes NÃO certificam
schema oficial. O endpoint HTTPS é exercitado com opener local, sem chamada fiscal.
Asserções incluem assinatura real, protocolo/nfeProc, UF/modelo/ambiente/emitente,
schema rejeitado, resposta inconsistente, redirect e compatibilidade de URL SP.

Gates finais e SHA: registrar no ledger e na PR após execução.
Esta entrega não integra automaticamente à main; merge exige autorização específica.
A PR #358 pode acionar deploy automático em production e não foi mesclada.

## Pendências e próximo bloco

NAT-03/04 e NAT-UF-MG permanecem IMPLEMENTING, nunca INTERNAL_COMPLETE.
Ainda faltam congelar e verificar XSD/WSDL oficiais, compor o validador real com
proveniência, ligar adapter ao registro canônico governado, consulta/cancelamento/
inutilização/status/recibo, NFC-e CSC/QR, NFS-e BH, Web, carga e certificação completa.
Ausência de XSD real é lacuna interna de construção; A1/credenciamento/transmissão
oficial e homologação permanecem dependências externas distintas.

Sequência preservada: MG → RJ → PR → MT → MS. Nenhum município ou UF homologado.
