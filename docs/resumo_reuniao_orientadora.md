# Resumo para a reunião com a orientadora

*Versão curta de `decisoes_metodo.md` (os códigos entre colchetes remetem ao registro completo). Atualizado em 2026-11-10, com o dashboard em Power BI concluído e a pauta da próxima reunião (seção 4).*

## 1. Onde estamos

- **Dados prontos.** Todas as bases foram extraídas, tratadas, validadas e cruzadas em dois painéis (municípios e estados, 2017–2025), com gasto por aluno em reais de 2025, notas do Saeb e controles.
- **Desenho fechado.** As decisões de método estão tomadas (seção 2).
- **Clusters e eficiência calculados:** 7 grupos de municípios por contexto e indicador de eficiência por município, etapa e disciplina.
- **Dashboard oficial construído em Power BI [P7]:** 10 páginas:
  - Boas-vindas (para que serve e por onde começar);
  - Visão geral;
  - Eficiência;
  - Ficha do município;
  - Pares;
  - Mapa;
  - Defasagens;
  - Contexto e clusters;
  - Estados;
  - Sobre os dados.

  Os números foram conferidos contra os cálculos em Python. O dashboard HTML continua como ferramenta de conferência.
- **Próxima etapa:** fechar os pontos abertos (seção 4), publicar o painel para o QR Code e escrever a análise.

| | Municípios | Estados |
|---|---|---|
| Gasto por aluno | SIOPE: gasto com Ensino Fundamental ÷ matrículas do Fundamental na rede municipal | SICONFI: gasto em educação menos o Ensino Superior ÷ matrículas da educação básica na rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais | Saeb Anos Finais e Ensino Médio |
| Tamanho | ~5.500 municípios | 27 UFs |

## 2. Decisões tomadas

| Ponto | Decisão |
|---|---|
| IDHM no tempo [C1] | IDHM do mesmo ano do Saeb; a edição de 2025 fica sem IDHM, o que vai como limitação |
| IDHM e educação [C1b] | Excluir os índices de escolaridade (IDHM Educação e IDHM total), para evitar circularidade; usar IDHM Renda e Longevidade |
| Outliers [A5] | Não remover; os casos implausíveis só ficam marcados |
| Gasto anual ou bianual [G12] | O gasto é anual; o Saeb é bienal. Cada edição usa o gasto do mesmo ano, e os anos intermediários entram pelas defasagens |
| Clusters [A6] | Desenvolver: agrupar os municípios por contexto e comparar gasto e nota dentro de cada grupo |
| Medida principal [S9, S10] | Proficiência do Saeb em pontos, Matemática e Português separadas. A nota padronizada N do Inep fica como secundária, porque satura nos limites de 1997 (43 redes de Anos Iniciais presas no teto) e não é comparável entre etapas. O cálculo da N foi conferido na Nota Técnica do Inep e reproduzido nos dados |
| Ensino Superior no gasto estadual [G4] | Versão A: quando a linha não existe, nada é descontado, para não perder UF/anos |
| Recorte [E3] | Brasil inteiro: ferramenta nacional, mesma perspectiva para todos os estados |
| Usuário-alvo [E4] | Agente de secretaria de educação ou analista da educação pública |
| Indicador de eficiência [A8] | Pontos do Saeb acima ou abaixo do esperado para o gasto e o contexto. Versão oficial: **nacional, com IDHM** (edições 2017–2023); a versão dentro do estado, que inclui 2025, fica como teste de robustez |
| Eficiência no painel [A10] | Em % do esperado ((nota − esperada) ÷ esperada), para pôr etapas e disciplinas na mesma escala; pontos e percentil ficam como referência. Os valores aparecem como "vs. esperado", com 0% = entregou o esperado. A escala em que o esperado vale 100% não foi usada, porque em DEA 100% quer dizer "eficiente" e porque a escala do Saeb não tem zero verdadeiro. O mapa abre na comparação no mesmo estado, com opção nacional. Na comparação no mesmo estado, os pares (página Pares) também são da mesma UF, para não misturar réguas. No Brasil inteiro, a eficiência média é zero por construção, e o painel diz isso |
| Rede municipal parcial [A9] | Manter na análise e marcar no painel; a sensibilidade sem essas redes não muda as conclusões |
| Acesso [A7] | QR Code ao final, apontando para o dashboard publicado |
| Registro [seção 10] | Toda decisão e limitação anotada |

## 3. Primeiros achados (para discutir)

Leitura descritiva, de associação, para Anos Iniciais e Matemática, salvo indicação [P7].

- **No Brasil, gastar mais se associa a notas um pouco maiores, cada vez menos:**
  - **Medida:** correlação simples (ρ de Spearman, sem controles) entre o gasto por aluno do mesmo ano e a proficiência.
  - **Tendência:** cai de 0,46 em 2017 para 0,16 em 2025.
  - **Defasagem:** com o gasto de anos antes, a correlação é maior. Em 2023, vai de 0,26 com o gasto do mesmo ano a 0,38 com o de 4 anos antes.
- **Dentro de cada estado, a associação quase some:**
  - Em 2023, a mediana entre as UFs é de 0,08, contra 0,26 no Brasil, com variação de −0,13 (RN) a +0,32 (RJ).
  - Boa parte da correlação nacional vem das diferenças entre estados, já que os que gastam mais também têm notas maiores.
  - Isso reforça os efeitos fixos de UF [A2] e o modelo de robustez da eficiência [A8].
- **Modelo principal, com efeito fixo de município [A11]:**
  - **Entre municípios**, com os controles de contexto, o gasto quase não se associa à nota (0,92 ponto por log do gasto, não significativo).
  - **Dentro do mesmo município**, a associação é positiva e clara, mas pequena: +10% no gasto por aluno se associa a +0,24 ponto (2017–2023); dobrar o gasto, a cerca de 1,7 ponto, quando um ano de escola vale ~25.
  - **Especificação de referência (decidida em 2026-11-10):** efeito fixo de município com efeito de UF × edição, 2017–2025: compara municípios do mesmo estado na mesma edição. +10% no gasto → +0,22 ponto em AI Matemática e +0,19 em Português.
  - **Defasagem:** na mesma amostra, a associação dentro do município vem do gasto do ano da prova e do ano anterior (o ciclo bienal do Saeb). O de 2 e 4 anos antes não se associa, ao contrário do ρ simples, que cresce com a defasagem.
  - **2025:** incluir 2025 dobra o coeficiente (5,1). A investigação mostrou que isso vem de mudanças comuns a cada estado: de 2023 a 2025, o Nordeste e o Norte tiveram ao mesmo tempo o maior aumento de gasto e o maior ganho de nota (compatível com a complementação VAAT do novo Fundeb, sem prova). Com efeito de UF × edição, o coeficiente com 2025 volta a 2,3, igual ao de 2017–2023. Essa especificação dispensa o IDHM, que é da UF e do ano, e por isso cobre 2025.
- **Heterogeneidade [A13]:** a associação dentro do município está concentrada nos municípios pequenos (até 50 mil habitantes) e no Nordeste e Norte; nas cidades com mais de 100 mil habitantes, ela é negativa (−2,7), e no Sudeste e Sul não aparece. As dimensões se sobrepõem: os municípios que mais gastam por aluno são, em geral, os menores. A associação negativa nas cidades grandes ainda não tem explicação.
- **Camada estadual [A12]:** com efeito fixo de UF, nenhuma associação entre gasto e nota é distinguível de zero, em AF e EM. Com 27 UFs, os intervalos são largos (de cerca de −6 a +9 pontos por log do gasto) e não excluem uma associação do tamanho da municipal. A leitura é "não detectável", e a camada segue descritiva.
- **A eficiência não é neutra entre os clusters:**
  - O % de redes acima do esperado vai de 40% (Nordeste, municípios pequenos) a 59% (Sul e Sudeste, pequenos).
  - O modelo oficial inclui as variáveis de contexto, mas de forma linear e sem efeito de região.
  - Por isso, a comparação dentro do cluster (página Pares) é a mais justa.
- **Rede municipal parcial [A9, L19]:**
  - **Tamanho:** em 2,7% das redes com nota em Anos Iniciais e em 16% em Anos Finais (2023), a prefeitura atende menos da metade dos alunos públicos da etapa; o restante está na rede estadual.
  - **Sensibilidade:** tirar essas redes não muda as conclusões. O coeficiente do gasto, a ordenação das demais e a correlação ficam praticamente iguais.
  - **O que muda:** essas redes têm eficiência média bem menor (−13,5 contra +0,4 pontos em AI MT). Por isso ficam marcadas no painel.
- **Gasto estadual, versões A e B [G4]:** onde a linha do Ensino Superior existe, as duas versões são iguais. A versão B só deixa de fora as UF/anos sem a linha (em 2023, AC, RO, RS e SE). O teste de sensibilidade é, portanto, de amostra.

## 4. Pauta da próxima reunião

### 4.1 Para decidir nesta reunião

As quatro primeiras perguntas vêm da reunião de 06/11 entre os autores; as respostas podem mudar o painel ou o texto.

- **Uso de IA [D5]:** trazemos um rascunho de declaração completa, por etapa do trabalho (`docs/declaracao_uso_ia.md`).
  - **Perguntas:** o uso descrito é permitido? Onde a declaração deve ficar (Método, nota ou apêndice)? A IA pode ser usada na redação do texto e, se puder, em quê?
- **Medida principal da eficiência: % do esperado ou percentil [A10]:**
  - **Hoje:** o painel mostra a eficiência em % do esperado ("vs. esperado": +5% = nota 5% acima da esperada); o percentil aparece na Ficha e na comparação 1 a 1.
  - **% do esperado:** mostra o tamanho da diferença e põe etapas na mesma escala. Contras: a escala do Saeb não tem zero verdadeiro, e casos extremos pesam (Ibateguara-AL: +71%).
  - **Percentil:** robusto a extremos e fácil de ler ("melhor que 80% das redes"). Contra: não mostra o tamanho da diferença, e redes muito próximas podem ficar a vários pontos de percentil de distância.
  - **Nossa proposta:** manter o % como medida principal e o percentil como complemento. Serve?
- **Edição de 2025 [C1]:**
  - **Hoje:** como decidido, o modelo nacional, que usa o IDHM, vai até 2023. A eficiência de 2025 só aparece na comparação dentro do estado: ela usa efeito fixo de UF, que absorve o IDHM (que só existe por UF). O painel avisa isso sempre que a edição de 2025 é escolhida.
  - **Pergunta:** podemos apresentar a eficiência de 2025 por essa comparação, como resultado complementar, ou 2025 deve ficar só nas análises descritivas?
- **Rede municipal parcial: limite de 50% [A9]:**
  - **Hoje:** a rede fica marcada quando a prefeitura atende menos de 50% dos alunos públicos da etapa. Em Anos Iniciais (2023), isso acontece em 266 municípios; com limite de 80%, seriam 923. Tirar as redes abaixo de 50% não muda as conclusões.
  - **Proposta:** manter os 50% na marca e usar 80% como teste de sensibilidade. Serve?
- **Endereço do QR Code [A7]:**
  - **Requisito:** o QR precisa abrir sem login, e o repositório é privado.
  - **Opções:**
    - publicar o Power BI na web pela conta da USP, se o administrador permitir;
    - publicar o HTML de conferência no GitHub Pages;
    - tornar o repositório público.
  - **Pergunta:** qual você prefere?

### 4.2 Outros pontos abertos (não bloqueiam o desenvolvimento)

- **Saltos atípicos [S11]:** algumas redes, sobretudo no CE e em AL, sobem mais de 100 pontos em poucos anos (por exemplo, Ibateguara-AL, de 195 para 345). Proposta: marcar, sem excluir, a variação entre edições que se afasta mais de 3 desvios-padrão da média (633 de 82 mil resultados), com aviso no dashboard. A regra serve?

- **Formato do TCC [D1]:** pelo Manual de 2025, o enquadramento mais natural é **método científico (estudo quantitativo)**: a pergunta é de descoberta, e não há uma organização-cliente para um plano de consultoria. Confirmar. Muda a estrutura do texto, não o dashboard.
- **Avaliação com usuários:** o Manual prevê TCLE (e possivelmente comitê de ética) para pesquisa com pessoas. Como fazer a avaliação com gestores?
- **Indicadores formais [D2]:** 12 indicadores propostos, com nome, fórmula, unidade e interpretação (seção 4 da especificação do dashboard), incluindo faixas de eficiência por quintil (de "bem abaixo" a "bem acima do esperado"). Confirmar.
- **Testes de sensibilidade [A4]:**
  - sem 2021;
  - sem 2025 na camada estadual;
  - IDHM Renda × IDHM total;
  - versão B do gasto estadual;
  - painel balanceado;
  - gasto médio do biênio.

  A lista está suficiente?
- **Faixa dos pares [P7]:**
  - **Regra atual:** pares são as redes do mesmo cluster com gasto entre 0,8 e 1,25 vez o do município. Na comparação dentro do estado, também da mesma UF.
  - **Problema:** na comparação nacional, nos clusters grandes, a faixa fica larga demais: a mediana é de 401 pares por rede em Anos Iniciais (2023), e Ibateguara-AL tem 690. Dentro do estado, a mediana cai para 78.
  - **Pergunta:** estreitar a faixa ou limitar aos N pares de gasto mais próximo?

## 5. Principais limitações (lista completa na seção 10 do registro)

- O nível do gasto depende da fonte, sobretudo nas capitais.
- Só entram redes com nota divulgada; redes pequenas ficam sub-representadas.
- O IDHM existe só por UF e só até 2024: a edição de 2025 fica sem esse controle.
- O desempenho é a proficiência média da rede, não a de cada aluno.
- A edição de 2021 foi afetada pela pandemia.
- A camada estadual tem só 27 unidades.
- O gasto municipal usado (Ensino Fundamental) não separa Anos Iniciais de Finais e exclui a Educação Infantil.
- Os resultados são de associação, não de causalidade.

## 6. Uso de IA

O Manual exige informar e discutir previamente o uso de IA. Usamos um assistente de IA (Claude, da Anthropic) na delimitação da pesquisa, na proposta de escolhas de método, no código de tratamento dos dados e das análises, no painel e na redação dos registros. As decisões são nossas ou suas, e estão datadas e verificáveis no registro, no código e nos diagnósticos. O detalhe por etapa está no rascunho `docs/declaracao_uso_ia.md` (seção 4.1).
