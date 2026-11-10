# Resumo para a reunião com a orientadora

*Versão curta de `decisoes_metodo.md` (os códigos entre colchetes remetem ao registro completo). Atualizado em 2026-11-09, com o dashboard em Power BI concluído.*

## 1. Onde estamos

- **Dados prontos.** Todas as bases foram extraídas, tratadas, validadas e cruzadas em dois painéis (municípios e estados, 2017–2025), com gasto por aluno em reais de 2025, notas do Saeb e controles.
- **Desenho fechado.** As decisões de método estão tomadas (seção 2).
- **Clusters e eficiência calculados:** 7 grupos de municípios por contexto e indicador de eficiência por município, etapa e disciplina.
- **Dashboard oficial construído em Power BI [P7]:** 9 páginas:
  - Início;
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
- **A eficiência não é neutra entre os clusters:**
  - O % de redes acima do esperado vai de 40% (Nordeste, municípios pequenos) a 59% (Sul e Sudeste, pequenos).
  - O modelo oficial inclui as variáveis de contexto, mas de forma linear e sem efeito de região.
  - Por isso, a comparação dentro do cluster (página Pares) é a mais justa.
- **Rede municipal parcial [A9, L19]:**
  - **Tamanho:** em 2,7% das redes com nota em Anos Iniciais e em 16% em Anos Finais (2023), a prefeitura atende menos da metade dos alunos públicos da etapa; o restante está na rede estadual.
  - **Sensibilidade:** tirar essas redes não muda as conclusões. O coeficiente do gasto, a ordenação das demais e a correlação ficam praticamente iguais.
  - **O que muda:** essas redes têm eficiência média bem menor (−13,5 contra +0,4 pontos em AI MT). Por isso ficam marcadas no painel.
- **Gasto estadual, versões A e B [G4]:** onde a linha do Ensino Superior existe, as duas versões são iguais. A versão B só deixa de fora as UF/anos sem a linha (em 2023, AC, RO, RS e SE). O teste de sensibilidade é, portanto, de amostra.

## 4. Pontos ainda abertos (não bloqueiam o desenvolvimento)

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
- **Uso de IA [D5]:** como você prefere que seja documentado no Método? A página "Sobre os dados" do painel traz hoje a mesma declaração do README, a ajustar conforme a sua orientação.
- **Faixa dos pares [P7]:**
  - **Regra atual:** pares são as redes do mesmo cluster com gasto entre 0,8 e 1,25 vez o do município.
  - **Problema:** nos clusters grandes, a faixa fica larga demais; Ibateguara-AL, por exemplo, tem 690 pares.
  - **Pergunta:** estreitar a faixa ou limitar aos N pares de gasto mais próximo?
- **Endereço do QR Code [A7]:**
  - **Requisito:** o QR precisa abrir sem login, e o repositório é privado.
  - **Opções:**
    - publicar o Power BI na web pela conta da USP, se o administrador permitir;
    - publicar o HTML de conferência no GitHub Pages;
    - tornar o repositório público.
  - **Pergunta:** qual você prefere?

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

O Manual exige informar e discutir previamente o uso de IA. Usamos assistente de IA no desenvolvimento do código de tratamento dos dados e na organização dos registros. Todas as decisões são nossas e verificáveis no código e nos diagnósticos.
