# FM Tecnologia — Política de separação de fases (laboratório)

**Regra vinculante para os futuros executores do laboratório:** construir 100%, certificar internamente 100%, somente depois configurar, certificar/homologar externamente e obter aprovação de liberação comercial.

## A fronteira é obrigatória

- INTERNAL_BUILD: implementar toda a engenharia interna configurável, inclusive adapters e tratamento das integrações externas, sem exigir clientes, contas ou certificados reais.
- INTERNAL_CERTIFICATION: confirmar o funcionamento interno por testes reais da aplicação em ambientes controlados, testes de integração simulada, segurança, regressão e critérios de aceite. Não alegar homologação externa.
- EXTERNAL_CONFIGURATION: inserir, fora do repositório, credenciais/contas/certificados e configurar ambientes oficiais quando houver autorização.
- EXTERNAL_HOMOLOGATION: comprovar operações reais e aprovadas junto a provedores, órgãos ou ambientes externos.
- COMMERCIAL_RELEASE: decisão comercial separada com aprovação humana e comprovação dos gates aplicáveis.

**Regra anti-bloqueio:** a falta de certificado A1, CSC, conta do provedor, cliente piloto, webhook real ou credenciais oficiais nunca justifica deixar um componente interno incompleto. A falta é registrada como pendência da etapa externa, enquanto as tarefas internas independentes continuam. Uma dependência de requisito técnico legítimo, mesmo associado a um provedor, pode ser registrada como bloqueio interno se não houver especificação suficiente para construir com segurança; nesse caso, implementar contratos neutros e testes possíveis e sinalizar a lacuna, sem inventar APIs.

**Regra anti-falsa-homologação:** passar testes com mock, simulador, sandbox ou transporte falso não equivale a emissão fiscal real, liquidação bancária, integração homologada ou certificação comercial.

O módulo `scripts/fm_phase_gates.py` e o manifesto `engineering_lab/phases.json` implementam validação de classificação, fluxo de fases, dependências e permissão de avanço. O código é uma fundação testável, ainda não uma barreira vinculada a toda PR nem um certificador de produção. A integração desses gates à autoridade externa de merge e ao motor durável de missões permanece pendente.
