# Declaração de uso de inteligência artificial (rascunho)

*Atualização de 2026-11-13: a orientadora permitiu e incentivou o uso de IA, desde que os autores conheçam todas as etapas do desenvolvimento e todas as informações necessárias para a apresentação final (relato de Henrique). Seguem em aberto as perguntas 2 e 4 da seção 5.*

*Rascunho de 2026-11-10 para discutir com a orientadora, como pede o Manual de TCC ADM 2025 (item 2.3): o uso de IA deve ser informado e discutido previamente, e a orientadora decide o que é permitido. Os trechos entre colchetes dependem dos autores ou da orientadora. Depois de aprovado, o texto vai para o Método (ou para uma nota metodológica) e substitui a declaração curta do README e da página "Sobre os dados" do painel.*

## 1. Ferramenta

- **Qual:** Claude, assistente de IA da Anthropic.
- **Como foi usado:**
  - em conversas no aplicativo, de setembro a outubro de 2026;
  - a partir de outubro, pelo Claude Code, que lê e escreve arquivos no repositório do projeto e executa os scripts na máquina de Henrique.
- **Quem usou:** Henrique, na parte de dados e do painel. [Guilherme: informar se usou IA e em quê.]

## 2. Uso por etapa do trabalho

| Etapa | O que a IA fez | O que os autores fizeram |
|---|---|---|
| **Delimitação da pesquisa** | Discutiu alternativas de base de desempenho (ENEM, PISA, Saeb), apontou limites de cada uma e redigiu um rascunho de perguntas analíticas | Escolheram a pergunta, o pivô do ENEM para gasto × Saeb, o desenho em duas camadas (municipal e estadual) e o recorte nacional. As perguntas analíticas ainda dependem da orientadora |
| **Escolhas de método** | Propôs várias escolhas, com prós e contras: janela 2017–2025, fontes do gasto por camada, proficiência como medida principal, correção pelo IPCA, clusters, indicador de eficiência | Decidiram cada ponto. Alguns foram decididos pela orientadora (IDHM do mesmo ano, outliers, clusters). Outros foram aceitos sem objeção e estão marcados assim no registro (`docs/decisoes_metodo.md`) |
| **Coleta e tratamento dos dados** | Escreveu a maior parte dos scripts em Python (Polars): extração (SIOPE, SICONFI, Censo Escolar, Saeb, IBGE, PNUD, IPCA), tratamento, validação e montagem dos painéis | Definiram as regras (o que entra, o que sai, como tratar ausências), rodaram os scripts e conferiram as saídas |
| **Análises** | Escreveu e rodou os scripts de correlação, regressão da nota esperada, clusters e testes de sensibilidade, e relatou os resultados | Conferiram os números nas saídas dos scripts e no painel. A interpretação dos resultados no texto é dos autores |
| **Painel em Power BI** | Escreveu os geradores do modelo e das páginas, as medidas em DAX e os textos explicativos das páginas | Definiram o conteúdo, o público, o desenho e o que entra em cada página. Conferiram os valores no Power BI e pediram as correções |
| **Registro e documentação** | Redigiu o registro de decisões, a nota de método, o resumo para as reuniões e o README, a partir das decisões tomadas | Revisaram e corrigiram os registros |
| **Revisão bibliográfica** | Buscou referências do tema e conferiu os dados bibliográficos e os resumos (`docs/levantamento_bibliografico.md`); não leu os textos completos nem escreveu a revisão | Leem os trabalhos, decidem o que citar e escrevem a revisão |
| **Texto do TCC** | Montou uma cópia do rascunho com texto técnico dos capítulos 4 e 5, tabelas, figuras e notas de divergência, tudo marcado como rascunho a reescrever (2026-11-12). Em 2026-11-13, escolheu três estudos de caso por regras objetivas e montou o material factual do estudo de casos e da validação por cenários, também como rascunho. Ainda em 2026-11-13, montou a base factual das partes de Henrique que faltavam (abertura do capítulo 4, método e gráficos dos clusters, citações das bases, perspectivas futuras e apêndice) e, ao buscar a fonte de uma afirmação, achou e corrigiu um erro seu ("um ano de escola vale cerca de 25 pontos"). Não escreveu revisão de literatura, discussão nem conclusões. Uso permitido pela orientadora (2026-11-13), com os autores cientes de cada etapa. | Escrevem o texto |

## 3. O que a IA não fez

- Não escolheu sozinha a pergunta de pesquisa, o recorte nem as decisões de método: toda decisão foi dos autores ou da orientadora e está datada no registro.
- Não produziu dados: todos os números vêm de bases públicas e dos scripts do repositório, que qualquer pessoa pode rodar de novo.
- Não teve acesso a dados pessoais: as bases são públicas e agregadas por rede, município ou UF.

## 4. Como o uso pode ser verificado

- **Código:** os scripts estão no repositório, com histórico de versões (Git), e reproduzem as tabelas a partir das bases públicas.
- **Decisões:** `docs/decisoes_metodo.md` registra cada decisão com data, autor (autores, orientadora ou proposta da IA aceita) e evidência.
- **Erros corrigidos:** o registro também traz os erros encontrados e como foram corrigidos, inclusive os que a IA cometeu (por exemplo, o formato da eficiência na página Pares e uma explicação imprecisa sobre a média da eficiência por estado, corrigidos em 2026-11-09).
- **Conferência:** os valores do painel foram conferidos com os cálculos em Python (`src/Testes/`).

## 5. Perguntas para a orientadora

1. O uso descrito acima é permitido para o TCC? **Respondida (2026-11-13): sim, e incentivado, desde que os autores conheçam todas as etapas do desenvolvimento e todas as informações necessárias para a apresentação final.**
2. Onde a declaração deve ficar: no Método, numa nota metodológica ou num apêndice?
3. A IA pode ser usada na redação do texto? Se puder, em quê? **Respondida (2026-11-13): sim, com a mesma condição.**
4. Basta este nível de detalhe, ou é preciso anexar algo (por exemplo, exemplos de interações)?
