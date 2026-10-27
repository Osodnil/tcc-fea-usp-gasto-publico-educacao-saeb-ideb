# 04 — Orientações da orientadora e regras do Manual de TCC

Este arquivo registra só o que foi confirmado. O que depende do texto completo do Manual está marcado como **conferir no PDF** (o PDF do Manual deve estar no conhecimento do projeto).

## 1. E-mail da orientadora (reunião de sexta-feira, 02/10, às 20h, no Zoom)

**Mensagem central.** A proposta é interessante e tem potencial, por integrar análise de dados, indicadores educacionais e dashboard. Mas é preciso delimitar a pesquisa para o TCC não ficar concentrado apenas no desenvolvimento tecnológico da ferramenta. O dashboard é o produto que permite visualizar e explorar os resultados; o TCC precisa também produzir conhecimento a partir dos dados: padrões, diferenças de desempenho, desigualdades socioeconômicas e territoriais, resultados relevantes para a gestão educacional.

**Pedido.** Um documento curto, de 3 a 5 páginas, ainda que preliminar, com os nove pontos abaixo. As sugestões dela são ponto de partida e não precisam ser adotadas como estão.

| # | Ponto | Sugestão dela |
|---|---|---|
| 1 | Pergunta de pesquisa | "Como dados do ENEM, associados a variáveis socioeconômicas e educacionais, podem ser estruturados em indicadores capazes de identificar padrões e desigualdades de desempenho relevantes para a gestão educacional?" Segunda questão, aplicada: como organizar esses indicadores em um dashboard que facilite a interpretação por gestores. |
| 2 | Usuário-alvo | Gestores públicos da área de educação. Definir se é Secretaria Estadual, Secretarias Municipais ou outro perfil. |
| 3 | Recorte geográfico e temporal | Estado de São Paulo, com análise por município e, se possível, por escola. Em vez de 2011–2025, um período mais curto, como 2019–2024, ou anos específicos. Equilibrar riqueza e viabilidade. |
| 4 | Unidade de análise | Município como principal, escola como complemento; ou escola como principal, se as bases permitirem integração consistente. Precisa estar claramente definida. |
| 5 | Variáveis | Notas por área, redação, renda familiar, escolaridade dos responsáveis, localização, sexo, raça/cor, tipo de escola, dependência administrativa, infraestrutura, características do município. Não é preciso usar todas. |
| 6 | Perguntas analíticas | De 5 a 8, que orientem análises e dashboard (variação entre municípios, relação com nível socioeconômico, desigualdade, evolução temporal, características de escolas e municípios associadas ao desempenho). |
| 7 | Indicadores | Para cada um: nome, fórmula ou forma de cálculo, unidade de análise, variáveis, interpretação. |
| 8 | Integração entre bases | ENEM, Censo Escolar e IBGE, ligados por códigos de município e, quando possível, de escola. **Verificar desde já quais chaves existem em cada base**, pois isso determina o nível de análise possível. |
| 9 | Fluxo metodológico | Dados → ETL → Análise → Indicadores → Insights → Dashboard → Avaliação (clareza, usabilidade e utilidade junto a usuários). |

**O que já foi respondido.** Preparamos o documento `Delimitacao_TCC_Reuniao.docx` (4 páginas). Os achados que mais pesaram: o código da escola não existe nos microdados públicos do ENEM (então a escola não serve de unidade de análise a partir do ENEM), e só 15,6% a 27,4% dos inscritos têm município vinculado. Para o ponto 3, o documento apresentou duas opções (Brasil inteiro ou SP) e apontou que o ENEM 2024 é tecnicamente inviável.

**O que mudou depois.** Segundo o Henrique, na conversa com a orientadora decidiu-se pivotar o projeto para gasto público em educação x desempenho em prova nacional (ver arquivo 01). O resultado do ponto 3 (recorte geográfico) **não foi registrado**.

**O que ainda precisa ser respondido nos termos dela** (pós-pivô): pergunta de pesquisa; usuário-alvo; recorte geográfico; unidade de análise (município na camada municipal, UF na estadual); perguntas analíticas; indicadores formais com nome, fórmula, unidade, variáveis e interpretação; chaves de integração (município de 7 dígitos, UF, rede e ano; ver arquivo 02, seção 8).

## 2. Manual de TCC do Departamento de Administração (2025)

### Confirmado
- **Três formatos aceitos:** método científico, consultoria e empreendedor.
- **Uso de IA (item 2.3):** qualquer uso de ferramentas de IA na elaboração do TCC deve ser informado e discutido previamente com o orientador; o uso indevido ou não autorizado pode levar à reprovação, com a mesma gravidade do plágio.
- **Citações e referências:** APA obrigatório a partir de 2026.
- **Plágio:** tratado com gravidade máxima (ver item 2.3; conferir no PDF a consequência exata).

### Conferir no PDF (não confirmado aqui)
- Estrutura mínima de TCC I e de TCC II em cada formato.
- Critérios de avaliação (rubrica) e a composição da nota, inclusive qualquer vídeo de apresentação.
- Prazos, número máximo de autores por trabalho e forma de entrega.
- Pré-requisitos e frequência de reuniões com o orientador.

### Ponto a decidir com a orientadora: qual formato
O projeto vem sendo chamado de "estilo consultoria". Mas a pergunta central ("o gasto se associa ao desempenho? com que defasagem?") é uma questão de descoberta, típica de estudo quantitativo (método científico), com o dashboard como produto aplicado. Isso é uma leitura do assistente, não uma conclusão do Manual. A escolha muda a estrutura e os critérios de avaliação (por exemplo: o formato de consultoria costuma pedir objetivo gerencial e plano de ação; o científico, fundamentação teórica, método, resultados e discussão). Confirmar com a orientadora e conferir as exigências de cada formato no PDF.

## 3. Uso de IA: o que registrar

Para cumprir o item 2.3, vale manter um registro simples, a ser conversado e aprovado pela orientadora:
- Quais ferramentas de IA foram usadas (por exemplo, Claude) e para quê: apoio na escrita de código de extração e tratamento de dados, revisão de achados, estruturação de documentos.
- O que a IA não fez: não definiu sozinha a pergunta de pesquisa nem as decisões de escopo, e os resultados foram conferidos pelos autores com saídas reais dos scripts.
- Onde o uso aparece no TCC (por exemplo, na seção de Método ou em nota metodológica), conforme a orientadora aprovar.
- Texto do TCC: antes de pedir redação de trechos à IA, alinhar com a orientadora.

## 4. Referências já conhecidas

- Séries do Leonardo Sales no Medium sobre o ENEM (desempenho x perfil socioeconômico, ICP, gap racial controlado, ENEM 2022): literatura cinzenta, a citar formalmente.
- Literatura de gasto público x IDEB: levantamento inicial em SciELO, ANPEC e ENAP; verificar cada artigo antes de citar.
- A bibliografia do documento original do TCC contém itens não verificados (ver arquivo 01, seção 7).
- Fontes oficiais de dados: ver arquivo 02.
