# Especificação do dashboard oficial (Power BI)

*Versão 2, 2026-11-11 (a versão 1 era de 2026-10-30; as seções 4 e 5 foram reescritas na revisão geral, para descrever o painel como ele ficou). Base: decisões E3, E4, S9, S11, C1, C1b, G4, A5, A6, A8 e A7 de `docs/decisoes_metodo.md`. O HTML em `relatorios/` continua como ferramenta de conferência; o produto entregue é o projeto `.pbip` desta pasta.*

## 1. Para quem e para quê

- **Usuário-alvo (E4):** técnico de secretaria de educação (municipal ou estadual) ou analista da educação pública. Conhece o Saeb e o orçamento da rede, mas não precisa conhecer regressão.
- **Perguntas que o painel responde, nesta ordem:**
  1. Quanto a minha rede gasta por aluno e quanto ela tira no Saeb, comparada ao Brasil, à UF e a redes parecidas?
  2. Considerando o gasto e o contexto, a minha rede entrega mais ou menos do que o esperado? Isso se repete entre edições?
  3. Quem são as redes parecidas que entregam mais com gasto semelhante (pares para conversar)?
  4. No agregado, gastar mais se associa a notas maiores? Com que defasagem?
- **O que o painel não diz:** que gastar mais *causa* nota maior, nem a nota de cada escola ou aluno. Isso aparece na página "Sobre os dados" e nos avisos das páginas.

## 2. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `src/Visualizacao/Preparar_PowerBI.py` | Monta as 13 tabelas do modelo em `data/processed/powerbi/` (roda no `run_pipeline.py`) |
| `powerbi/carregar_dados.pq` | Consulta M de carregamento e o parâmetro `PastaDados` |
| `powerbi/medidas.dax` | Todas as medidas, por pasta |
| `powerbi/tema_tcc.json` | Tema (mesma paleta do HTML de conferência) |
| `powerbi/roteiro_construcao.md` | Passo a passo da construção, com os valores de conferência |
| `data/processed/malha_municipios.topojson` | Malha para o visual "Mapa de formas" (id de cada área = "Nome (UF)"; `CD_MUN` nas propriedades) |
| `src/Visualizacao/Gerar_Modelo_PowerBI.py` | Escreve o modelo semântico (TMDL) no projeto, uma vez |
| `src/Visualizacao/Gerar_Relatorio_PowerBI.py` | Grava e valida as 10 páginas (formato PBIR) |
| `powerbi/tcc_gasto_saeb.pbip` | O dashboard, como projeto do Power BI |

## 3. Modelo de dados (estrela)

```
                   dim_uf ──┐
                            ▼
 dim_cluster ──► dim_municipio ──► fato_desempenho_municipal ◄── dim_etapa
                            │                ▲   ▲                    │
                            └──► fato_gasto_municipal              dim_disciplina
 dim_ano ──► (os quatro fatos)                                        │
 dim_uf ──► fato_desempenho_estadual ◄────────────────────────────────┘
 dim_uf ──► fato_gasto_estadual
 dim_defasagem, dim_modelo: tabelas de parâmetro, sem relacionamento
```

| Tabela | Grão (chave) | Linhas | Observação |
|---|---|---|---|
| `dim_municipio` | município (`CO_MUNICIPIO`) | 5.571 | nome, "Nome (UF)", região, porte, faixa de alfabetização, cluster (3 municípios sem cluster: Fernando de Noronha, Boa Esperança do Norte, Brasília) |
| `dim_uf` | UF | 27 | |
| `dim_cluster` | cluster | 7 | rótulo e perfil médio do grupo (A6) |
| `dim_ano` | ano 2017–2025 | 9 | marcas `EDICAO_SAEB`, `TEM_IDHM`, `EFICIENCIA_OFICIAL` |
| `dim_etapa` | AI, AF, EM | 3 | nome legível e ordem |
| `dim_disciplina` | MT, LP | 2 | |
| `dim_defasagem` | 0, 1, 2, 4 | 4 | parâmetro: gasto do mesmo ano ou de 1, 2, 4 anos antes |
| `dim_modelo` | Oficial, Robustez | 2 | parâmetro: eficiência nacional com IDHM (oficial) ou dentro da UF |
| `fato_desempenho_municipal` | município × etapa × disciplina × edição | 93.630 | proficiência, N, IDEB, gasto L0–L4, contexto, eficiência (2 modelos), posição no cluster, salto atípico |
| `fato_gasto_municipal` | município × ano | 50.113 | gasto anual 2017–2025 |
| `fato_desempenho_estadual` | UF × etapa × disciplina × edição | 540 | camada estadual (AF e EM), gasto versões A e B |
| `fato_gasto_estadual` | UF × ano | 243 | |
| `fato_oferta_municipal` | município × etapa × ano | 100.278 | matrículas municipais e estaduais, parcela da rede municipal e situação (com nota, sem rede, sem nota divulgada); decisão A9 |
| `ref_municipio`, `cmp_municipio` | município | 5.571 | tabelas calculadas, sem relacionamento: município de referência e município comparado da página Pares |

**Relacionamentos** (todos 1:\*, filtro em direção única, da dimensão para o fato):

- `dim_uf[SG_UF]` → `dim_municipio[SG_UF]`, `fato_desempenho_estadual[SG_UF]`, `fato_gasto_estadual[SG_UF]`
- `dim_cluster[CLUSTER]` → `dim_municipio[CLUSTER]`
- `dim_municipio[CO_MUNICIPIO]` → `fato_desempenho_municipal[CO_MUNICIPIO]`, `fato_gasto_municipal[CO_MUNICIPIO]`
- `dim_ano[ANO]` → `ANO` dos quatro fatos
- `dim_etapa[ETAPA]` e `dim_disciplina[DISCIPLINA]` → os dois fatos de desempenho

**Cuidados do formato longo:** IDEB, nota N, gasto e contexto se repetem nas duas linhas de disciplina. As medidas que usam essas colunas resumem antes por rede e edição (`SUMMARIZE`), para não contar duas vezes. Proficiências só são mostradas com **uma etapa e uma disciplina** selecionadas (a medida devolve vazio e aparece o aviso "Escolha uma etapa e uma disciplina").

**Contagens de conferência** (saída do `Preparar_PowerBI.py`): 82.390 linhas com proficiência; 65.084 com eficiência oficial (2017–2023); 82.260 com eficiência de robustez; 130 redes com nota ficam sem eficiência porque falta gasto ou algum controle; 633 linhas com salto atípico.

## 4. Indicadores formais (proposta para D2)

| # | Indicador | Fórmula | Unidade | Como ler | Cuidados |
|---|---|---|---|---|---|
| I1 | Gasto por aluno, rede municipal | despesa paga na subfunção 361 (SIOPE) ÷ matrículas do Fundamental na rede municipal (Censo Escolar), corrigida pelo IPCA | R$ de 2025 por aluno/ano | quanto a rede gasta, por aluno do Fundamental | não separa Anos Iniciais e Finais; exclui Educação Infantil (L13, L14); mediana entre redes |
| I2 | Gasto por aluno, rede estadual | (função 12 − subfunção 364, SICONFI) ÷ matrículas da educação básica na rede estadual, IPCA | R$ de 2025 por aluno/ano | idem, para o estado | versão A (G4): onde a 364 não existe, nada é descontado |
| I3 | Proficiência média | média simples, entre as redes do recorte, da proficiência do Saeb | pontos da escala Saeb | quanto os alunos da rede sabem na etapa e disciplina | não comparar etapas nem disciplinas entre si (S9) |
| I4 | Nota padronizada N (secundária) | 10·(S − limite inferior)/(limite superior − limite inferior), média de MT e LP | 0 a 10 | componente de aprendizado do IDEB | satura nos limites de 1997 (S10) |
| I5 | IDEB | N × indicador de rendimento (Inep) | 0 a 10 | referência oficial | mistura aprendizado e fluxo |
| I6 | Proficiência esperada | previsão do modelo de MQO: log do gasto, população, alfabetização, infraestrutura, tamanho da rede, IDHM Renda e Longevidade da UF, edição | pontos | o que redes com o mesmo gasto e contexto tiraram, em média | modelo oficial só 2017–2023 (C1) |
| I7 | **Eficiência ("vs. esperado")** | (proficiência observada − esperada) ÷ esperada (A10); em pontos como referência | % do esperado | +5% = nota 5% acima da esperada; 0% = igual à esperada | associação, não efeito do gasto; no modelo nacional o gasto pesa pouco na esperada (revisão geral, item 2.1); a escala do Saeb não tem zero verdadeiro; ver saltos (I10) |
| I8 | Percentil de eficiência | posição do resíduo entre as redes da mesma etapa, disciplina e edição | 0 a 100 | 80 = melhor que 80% das redes | faixas por quintil (proposta): bem abaixo, abaixo, próximo, acima, bem acima do esperado |
| I9 | Posição no cluster | nota − mediana do cluster; gasto ÷ mediana do cluster | pontos; razão | comparação descritiva com redes de contexto parecido (A6) | não controla o gasto; é descritiva |
| I10 | Salto atípico | variação desde a edição anterior afastada mais de 3 desvios-padrão da média das variações | marca (sim/não) | resultado que mudou demais em dois anos | marca, não exclui (A5); regra em S11, a confirmar |
| I11 | Cobertura do Saeb | redes com nota ÷ municípios do recorte | % | quanto do recorte está representado | redes pequenas ficam sub-representadas |
| I12 | Associação gasto × desempenho | ρ de Spearman entre o gasto (defasagem k) e a proficiência, entre as redes | −1 a 1 | se redes que gastam mais tendem a ter nota maior | só com ≥ 30 redes; não é efeito causal |

## 5. Páginas

O registro detalhado de cada página está em P7 de `docs/decisoes_metodo.md`. As páginas são gravadas por `src/Visualizacao/Gerar_Relatorio_PowerBI.py`.

- **Filtros:** ficam numa faixa azul no topo, e cada página mostra só os que mudam algum visual dela. UF, Etapa, Disciplina, Edição e Comparação da eficiência são sincronizados entre as páginas. São próprios de uma página: Município (Ficha), Município de referência e Comparar com (Pares), Comparação do mapa (Mapa), Gasto de quando (Defasagens) e Etapa da rede estadual (Estados).
- **Comparações:** "Nacional (até 2023)", com IDHM, e "Mesmo estado (até 2025)", com efeito fixo de UF (A8).

| # | Página | O que mostra |
|---|---|---|
| 1 | **Boas-vindas** | para que serve, como usar e três perguntas que levam às páginas (Defasagens, Ficha, Pares) |
| 2 | **Visão geral** | cartões (gasto, proficiência, % acima do esperado, cobertura); proficiência por edição; redes que melhoraram desde a edição anterior; gasto do recorte × Brasil |
| 3 | **Eficiência** | cartões; dispersão gasto × resultado em relação ao esperado, por cluster; % acima do esperado por UF; ranking (município, gasto, proficiência, esperada, vs. esperado, atenção) |
| 4 | **Ficha do município** | cartões; proficiência por edição contra cluster, UF e Brasil; gasto por ano; situação da rede; tabela por edição |
| 5 | **Pares** | redes do mesmo cluster com gasto entre 0,8 e 1,25 vez o da referência (e da mesma UF, na comparação no mesmo estado); comparação 1 a 1 com um par clicado ou escolhido |
| 6 | **Mapa** | eficiência por município numa UF (o visual desenha até ~1.500 áreas), na comparação escolhida, com cor saturada em ±12%; resumo por UF na comparação nacional |
| 7 | **Defasagens** | ρ de Spearman por edição e defasagem, em colunas e em mapa de calor |
| 8 | **Contexto e clusters** | perfil dos 7 clusters; composição de cada cluster por região; gasto e proficiência por porte |
| 9 | **Estados** | 27 UFs, AF e EM, gasto na versão A: dispersão, séries por região e tabela; leitura descritiva |
| 10 | **Sobre os dados** | fontes, indicadores, limitações, inflação (fator do IPCA), autoria e espaço do QR Code (A7) |

**O que o painel não traz:** os modelos com efeito fixo, a heterogeneidade e os testes de sensibilidade (A4, A11 a A13) estão em `docs/nota_resultados.md` e `docs/resultados/`. O painel é descritivo.

## 6. Regras visuais

- Tema `tema_tcc.json`: mesma paleta do HTML. Clusters usam as 7 primeiras cores categóricas, **na ordem fixa do número do cluster** (a cor segue o grupo, não a posição no gráfico).
- Eficiência: escala divergente com centro cinza em 0 (vermelho = abaixo, azul = acima). Gasto e proficiência: escala sequencial de um só azul.
- Nada de dois eixos verticais no mesmo gráfico; gasto e nota em gráficos lado a lado.
- Valores e rótulos em tinta neutra; a cor marca só a série. Legenda sempre que houver duas séries ou mais.
- Formatos: gasto `R$ #.##0`; proficiência `0,0`; eficiência `+0,0%;−0,0%;0,0%` (em pontos: `+0,0;−0,0;0,0`); percentuais `0%`; ρ `0,00`.
- Toda página com indicador de eficiência mostra o aviso de associação; toda página com 2025 mostra o aviso do IDHM.

## 7. Riscos técnicos e alternativas

| Risco | Plano |
|---|---|
| "Mapa de formas" é recurso em versão prévia (Arquivo > Opções > Recursos em versão prévia) e pode ficar lento com 5.571 polígonos | malha já simplificada (1,5 MB); se ficar lento, mostrar o mapa só com UF filtrada, ou usar o visual Azure Maps com a mesma malha. **Ocorreu (2026-11-05):** o visual desenha só ~1.500 áreas; adotado o mapa por UF |
| "Publicar na Web" (para o QR Code, A7) depende de conta corporativa e da permissão do administrador do locatário | testar com a conta USP; se não houver permissão, publicar o HTML de conferência (GitHub Pages) e o `.pbix` para download |
| ρ de Spearman em DAX com ~10 mil redes pode demorar | se passar de ~2 s, calcular no Python (tabela pronta por edição, etapa, disciplina e defasagem) |
| Atualização dos dados | rodar `run_pipeline.py` e depois "Atualizar" no Power BI; o caminho fica no parâmetro `PastaDados` |

## 8. Critérios de aceite

- Os números do Power BI batem com os do HTML de conferência para Brasil, AI, MT, 2023: gasto mediano, proficiência média, número de redes e ρ (tolerância: 3ª casa decimal no ρ).
- A ficha de 3 municípios de teste (um pequeno do Nordeste, uma capital, um com salto atípico, por exemplo Ibateguara-AL) mostra os mesmos valores do HTML.
- Nenhuma página mostra proficiência média misturando etapas ou disciplinas.
- O `.pbix` abre em outra máquina trocando só o parâmetro `PastaDados`.
