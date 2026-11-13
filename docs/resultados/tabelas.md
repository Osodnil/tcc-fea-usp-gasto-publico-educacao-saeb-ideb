# Tabelas dos resultados

*Gerado por `src/Analise/Material_Texto.py` a partir das saídas dos scripts de análise. Não editar à mão: rodar o script de novo. Decisões e leitura em `docs/decisoes_metodo.md` (A4, A11, A12, A13) e em `docs/nota_resultados.md`.*

### Tabela 1. Redes municipais com nota, gasto e proficiência por edição

| Etapa | Edição | Redes com nota | Gasto por aluno (mediana, R$ de 2025) | Matemática (média) | Português (média) |
|---|---|---|---|---|---|
| Anos Iniciais | 2017 | 5.201 | R$ 9.202 | 218,2 | 207,5 |
| Anos Iniciais | 2019 | 5.140 | R$ 9.524 | 222,7 | 208,4 |
| Anos Iniciais | 2021 | 4.754 | R$ 9.961 | 211,8 | 201,7 |
| Anos Iniciais | 2023 | 5.243 | R$ 13.526 | 220,2 | 208,2 |
| Anos Iniciais | 2025 | 5.320 | R$ 15.859 | 230,1 | 215,9 |
| Anos Finais | 2017 | 3.315 | R$ 8.106 | 247,7 | 248,5 |
| Anos Finais | 2019 | 3.104 | R$ 8.340 | 254,8 | 251,6 |
| Anos Finais | 2021 | 2.630 | R$ 9.080 | 249,1 | 249,8 |
| Anos Finais | 2023 | 3.196 | R$ 12.540 | 249,3 | 250,2 |
| Anos Finais | 2025 | 3.292 | R$ 15.164 | 255,1 | 254,3 |

*Gasto do Ensino Fundamental da rede municipal (SIOPE) ÷ matrículas, corrigido pelo IPCA. Proficiência em pontos do Saeb, média simples entre as redes.*

### Tabela 2. Correlação de Spearman entre gasto por aluno e proficiência (AI, Matemática)

| Edição | Gasto do mesmo ano | 1 ano antes | 2 anos antes | 4 anos antes |
|---|---|---|---|---|
| 2017 | 0,46 | — | — | — |
| 2019 | 0,41 | 0,40 | 0,44 | — |
| 2021 | 0,33 | 0,37 | 0,41 | 0,45 |
| 2023 | 0,26 | 0,26 | 0,32 | 0,38 |
| 2025 | 0,16 | 0,17 | 0,25 | 0,30 |

*Sem controles. Vazio: sem gasto daquele ano (a série começa em 2017).*

### Tabela 3. Modelo principal: gasto do mesmo ano e proficiência

| Especificação | AI Matemática | AI Português | AF Matemática | AF Português |
|---|---|---|---|---|
| MQO agrupado, 2017–2023 | 0,92 (0,72)<br>N = 20.315 | 0,89 (0,62)<br>N = 20.315 | 1,57* (0,94)<br>N = 12.227 | 1,18 (0,81)<br>N = 12.227 |
| EF de município + edição, 2017–2023 | 2,47*** (0,50)<br>N = 20.256 | 2,23*** (0,47)<br>N = 20.256 | 2,23*** (0,65)<br>N = 12.056 | 1,65*** (0,62)<br>N = 12.056 |
| EF de município + UF × edição, 2017–2025 (referência) | 2,34*** (0,43)<br>N = 25.591 | 1,98*** (0,40)<br>N = 25.591 | 2,73*** (0,61)<br>N = 15.390 | 2,00*** (0,54)<br>N = 15.390 |

*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \*\*\* p < 0,01; \*\* p < 0,05; \* p < 0,10. Associação, não efeito causal.* *Controles: infraestrutura e log das matrículas; no MQO, também log da população e alfabetização; nas especificações de 2017–2023, IDHM Renda e Longevidade da UF. +10% no gasto = coeficiente × 0,095 ponto.*

### Tabela 4. Defasagem do gasto na mesma amostra (referência, 2019–2025)

| Etapa e disciplina | Gasto do mesmo ano | 1 ano antes | 2 anos antes |
|---|---|---|---|
| Anos Iniciais, Matemática | 2,26*** (0,47) | 2,35*** (0,54) | 0,85 (0,52) |
| Anos Iniciais, Português | 1,97*** (0,44) | 1,83*** (0,50) | 0,47 (0,47) |
| Anos Finais, Matemática | 3,22*** (0,69) | 3,88*** (0,73) | 1,30* (0,69) |
| Anos Finais, Português | 2,56*** (0,63) | 3,05*** (0,68) | 0,83 (0,66) |

*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \*\*\* p < 0,01; \*\* p < 0,05; \* p < 0,10. Associação, não efeito causal.* *Mesmas linhas em todas as colunas (redes com os três gastos).*

### Tabela 5. Heterogeneidade da associação dentro do município (AI)

| Dimensão | Grupo | Matemática | Português | Municípios |
|---|---|---|---|---|
| Porte | Até 5 mil | 3,01*** (0,79) | 2,68*** (0,75) | 1.184 |
| Porte | 5 a 10 mil | 3,04*** (0,75) | 2,76*** (0,68) | 1.106 |
| Porte | 10 a 20 mil | 2,87*** (0,65) | 2,38*** (0,60) | 1.350 |
| Porte | 20 a 50 mil | 2,41*** (0,78) | 1,92*** (0,68) | 1.048 |
| Porte | 50 a 100 mil | −0,54 (1,04) | −0,68 (0,99) | 338 |
| Porte | Mais de 100 mil | −2,65*** (1,00) | −2,47*** (0,95) | 318 |
| Região | Norte | 3,60** (1,51) | 3,68*** (1,31) | 446 |
| Região | Nordeste | 4,29*** (0,85) | 3,73*** (0,76) | 1.788 |
| Região | Centro-Oeste | 1,84** (0,90) | 2,25** (0,93) | 451 |
| Região | Sudeste | 1,07 (0,69) | 0,47 (0,66) | 1.591 |
| Região | Sul | 0,86 (0,96) | 0,50 (0,96) | 1.068 |
| Cluster | 1 | 4,25*** (1,06) | 4,58*** (0,97) | 942 |
| Cluster | 2 | 4,96*** (0,91) | 4,26*** (0,80) | 1.035 |
| Cluster | 3 | 2,32*** (0,90) | 2,04** (0,88) | 752 |
| Cluster | 4 | 3,03*** (0,87) | 2,85*** (0,79) | 562 |
| Cluster | 5 | −0,09 (0,96) | −0,64 (0,86) | 272 |
| Cluster | 6 | 1,55* (0,88) | 0,78 (0,84) | 1.063 |
| Cluster | 7 | −3,20*** (0,80) | −3,46*** (0,78) | 718 |
| Faixa de gasto médio | Q1 | −1,10 (0,82) | −1,26* (0,74) | 1.089 |
| Faixa de gasto médio | Q2 | 1,97** (0,79) | 1,61** (0,73) | 1.088 |
| Faixa de gasto médio | Q3 | 1,80** (0,74) | 1,64** (0,68) | 1.077 |
| Faixa de gasto médio | Q4 | 4,01*** (0,73) | 3,40*** (0,66) | 1.072 |
| Faixa de gasto médio | Q5 | 3,71*** (0,80) | 3,24*** (0,73) | 1.018 |

*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \*\*\* p < 0,01; \*\* p < 0,05; \* p < 0,10. Associação, não efeito causal.* *Especificação de referência com uma inclinação por grupo. A igualdade das inclinações é rejeitada nas quatro dimensões (p ≤ 0,02). Clusters: 1 = Predomínio do Nordeste · pequenos · alfabetização mais baixa; 2 = Predomínio do Nordeste · médios · alfabetização mais baixa; 3 = Predomínio do Sudeste · pequenos · alfabetização intermediária; 4 = Predomínio do Centro-Oeste · pequenos · alfabetização intermediária; 5 = Predomínio do Nordeste e do Norte · grandes · alfabetização intermediária; 6 = Predomínio do Sul e do Sudeste · pequenos · alfabetização mais alta; 7 = Predomínio do Sudeste · médios · alfabetização mais alta. O k-médias não usa a região: ela só nomeia o grupo pela maioria dos municípios. Faixa de gasto: quintil do gasto médio de 2017–2025.*

### Tabela 6. Testes de sensibilidade (camada municipal, gasto do mesmo ano)

| Teste | AI Matemática | AI Português | AF Matemática | AF Português |
|---|---|---|---|---|
| Referência (2017–2025) | 2,34*** (0,43) | 1,98*** (0,40) | 2,73*** (0,61) | 2,00*** (0,54) |
| Sem 2021 | 2,84*** (0,50) | 2,46*** (0,47) | 2,97*** (0,74) | 2,22*** (0,65) |
| Painel balanceado | 2,51*** (0,46) | 2,06*** (0,43) | 2,99*** (0,73) | 2,52*** (0,63) |
| Referência em 2019–2025 | 2,33*** (0,47) | 2,00*** (0,44) | 3,20*** (0,69) | 2,49*** (0,63) |
| Gasto médio do biênio (2019–2025) | 3,74*** (0,66) | 3,12*** (0,61) | 5,46*** (0,93) | 4,32*** (0,86) |
| Sem redes parciais (< 50%) | 2,42*** (0,44) | 2,16*** (0,41) | 2,96*** (0,71) | 2,21*** (0,62) |
| Sem redes abaixo de 80% | 2,66*** (0,50) | 2,31*** (0,46) | 3,68*** (0,85) | 2,85*** (0,73) |
| Sem saltos atípicos | 2,11*** (0,41) | 1,99*** (0,39) | 2,34*** (0,58) | 1,97*** (0,52) |
| EF de município, IDHM Renda e Longevidade (2017–2023) | 2,47*** (0,50) | 2,23*** (0,47) | 2,23*** (0,65) | 1,65*** (0,62) |
| EF de município, IDHM total (2017–2023) | 1,85*** (0,49) | 1,65*** (0,46) | 1,74*** (0,65) | 1,41** (0,62) |
| EF de município, sem IDHM (2017–2023) | 2,81*** (0,50) | 2,48*** (0,47) | 2,40*** (0,66) | 1,78*** (0,62) |

*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \*\*\* p < 0,01; \*\* p < 0,05; \* p < 0,10. Associação, não efeito causal.* *Cada teste muda uma coisa na referência (EF de município + UF × edição, 2017–2025). As três últimas linhas usam efeito de edição e 2017–2023, porque o efeito de UF × edição absorve o IDHM.*

### Tabela 7. Camada estadual: gasto estadual por aluno e proficiência das redes estaduais

| Especificação | AF Matemática | AF Português | EM Matemática | EM Português |
|---|---|---|---|---|
| MQO agrupado, 2017–2023 | 0,55 (5,18)<br>IC: −10,1 a 11,2 | 2,07 (5,76)<br>IC: −9,8 a 13,9 | −2,70 (5,90)<br>IC: −14,8 a 9,4 | −0,77 (5,44)<br>IC: −11,9 a 10,4 |
| EF de UF, 2017–2023 (referência) | 1,51 (3,67)<br>IC: −6,0 a 9,1 | 1,06 (3,61)<br>IC: −6,4 a 8,5 | 5,25 (3,82)<br>IC: −2,6 a 13,1 | 2,47 (3,71)<br>IC: −5,2 a 10,1 |
| EF de UF, 2017–2025, sem IDHM | 0,38 (4,44)<br>IC: −8,8 a 9,5 | 0,28 (3,73)<br>IC: −7,4 a 7,9 | 6,35 (4,77)<br>IC: −3,5 a 16,2 | 3,63 (4,01)<br>IC: −4,6 a 11,9 |
| Versão B do gasto (referência) | 0,86 (3,51) | 0,73 (3,52) | 5,22 (3,95) | 2,66 (3,89) |

*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \*\*\* p < 0,01; \*\* p < 0,05; \* p < 0,10. Associação, não efeito causal.* *27 UFs (23 na versão B). Erros agrupados por UF; valores-p e intervalos de 95% pela t com 26 graus de liberdade.*
