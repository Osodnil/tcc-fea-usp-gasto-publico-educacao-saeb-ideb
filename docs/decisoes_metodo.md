# Registro de decisões de método

Panorama do que foi desenvolvido até agora, dos problemas encontrados em cada base e das decisões tomadas para contorná-los. Serve de base para a seção de Método e para as reuniões com a orientadora.

- **Última atualização:** 2026-10-30 (decisões de 30/10, Manual de TCC, clusters, indicador de eficiência, marca de saltos atípicos e especificação do Power BI)
- **Fontes deste registro:** código e dados do repositório, os testes em `src/Testes`, os diagnósticos em `data/interim/diagnosticos`, as instruções do projeto e o dossiê das conversas anteriores (`docs/historico/`). Os números marcados com † foram recalculados a partir dos parquets em `data/interim`; os marcados "(dossiê)" vêm das conversas anteriores; os demais vêm dos testes ou das instruções. Esses dois últimos grupos não foram reverificados.
- **Status:** ✅ fechada · 🟡 provisória (validar com a orientadora) · ⚠️ problema em aberto. As pendências estão na seção 9 e as limitações consolidadas na seção 10.

---

## 1. Panorama

**Pergunta.** O gasto público por aluno em educação (deflacionado) se associa ao desempenho no Saeb/IDEB? Com que defasagem? Quais municípios e estados entregam mais ou menos do que o esperado, dado o gasto e o contexto? O usuário-alvo é o gestor de secretaria de educação.

**Fluxo.** Dados → ETL → Análise → Indicadores → Insights → Dashboard → Avaliação. Formato de consultoria: o TCC precisa produzir conhecimento a partir dos dados, não só a ferramenta.

**Duas camadas, analisadas separadamente:**

| | Camada municipal | Camada estadual |
|---|---|---|
| Gasto | SIOPE, subfunção 361 (Ensino Fundamental), despesa paga | SICONFI (DCA Anexo I-E), função 12 paga − 12.364 (Ensino Superior) |
| Denominador | Matrículas do Fundamental, rede municipal | Matrículas da educação básica, rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais, rede Municipal | Saeb Anos Finais e Ensino Médio, rede Estadual |
| Unidades | ~5.500 municípios | 27 UFs |
| Janela | 2017–2025 (Saeb bienal: 2017, 2019, 2021, 2023, 2025) | idem; gasto disponível desde 2014 |

**Estado do pipeline:**

| Base | Extract | Transform | Saída |
|---|---|---|---|
| SIOPE (geral + subfunção) | ✅ `Extract_SIOPE.py`, `Extract_SIOPE_Funcao.py` (ver T1) | ✅ `Transform_SIOPE.py` | `siope_municipal_transformado` |
| SICONFI estados | ✅ `Extract_SICONFI_Estados.py` | ✅ `Transform_SICONFI.py` | `siconfi_estadual_transformado` |
| Censo Escolar, matrículas | ✅ `Extract_Censo_Matriculas.py` | ✅ `Transform_Matriculas.py` | `matriculas_{municipal,estadual}_transformado` |
| Censo Escolar, infraestrutura | ✅ | ✅ `Transform_Infraestrutura.py` (ver T4) | `censo_escolar_transformado` |
| **Painéis** | — | ✅ `Montar_Paineis.py` (ver P1) | `data/processed/painel_{municipal,estadual}` |
| **Tabelas de apoio** | — | ✅ `Montar_Paineis.py` (ver P4) | `data/processed/dim_{municipio,uf}`, `gasto_{municipal,estadual}_anual` |
| **Clusters e eficiência** | — | ✅ `src/Analise/Analise_Clusters.py`, `Eficiencia.py` (ver A6, A8, S11) | `data/processed/cluster_*`, `eficiencia_municipal` |
| **Dashboard (ferramenta de análise)** | — | ✅ `src/Visualizacao/Gerar_Dashboard_HTML.py` (ver P5) | `relatorios/dashboard_conferencia.html` |
| **Dashboard oficial (Power BI)** | — | ✅ modelo `src/Visualizacao/Preparar_PowerBI.py`; especificação em `powerbi/` (ver P7) · `.pbix` a construir | `data/processed/powerbi/` |
| Saeb/IDEB | ✅ `Extract_SAEB.py` | ✅ `Transform_SAEB.py` | `saeb_{municipal,estadual}_transformado` |
| IDHM por UF | ✅ | ✅ (mesmo ano do Saeb; 2025 sem IDHM, ver C1) | `idhm_transformado` |
| IBGE, Censo 2022 (alfabetização) | ✅ | ✅ | `ibge_transformado` |
| IPCA | ✅ `Extract_IPCA.py` | não precisa | `ipca_deflator_anual` |

O dashboard é um HTML autocontido, que abre offline, gerado a partir dos painéis e das tabelas de apoio. É só descritivo (medianas, médias simples, correlação de Spearman), sem modelo estimado, e não muda nenhum resultado.

A validação de 2026-10-21 concluiu que os Extracts estão completos para a pergunta. Em 2026-10-22, todas as bases foram tratadas e cruzadas nos painéis municipal e estadual. Em 2026-10-30 saíram os clusters, o indicador de eficiência e a especificação do dashboard oficial. O próximo passo é construir o `.pbix` e, em paralelo, os testes de sensibilidade (A4).

---

## 2. Escopo

### E1. Prova de desempenho: Saeb/IDEB ✅
- **Problema:** era preciso escolher a medida de desempenho.
- **Decisão:** usar o Saeb/IDEB. O ENEM e o PISA foram descartados.
- **Por quê:**
  - No ENEM há auto-seleção: só 15% a 27% dos inscritos têm escola vinculada (`diagnosticos/enem_preenchimento_por_ano.csv`).
  - O PISA é amostral e não tem resultado por município.
  - O Saeb é censitário na rede pública e tem resultado por município e por rede.
- **Resíduo:** os scripts e parquets do ENEM (`Extract_ENEM.py`, `Diagnostico_ENEM.py`, `enem_*_extraido`) ficaram como histórico e não entram na análise.

### E2. Janela 2017–2025 ✅
- **Problema:** o SIOPE só tem dados a partir de 2017; a sondagem da API confirmou 2017 como o primeiro ano.
- **Decisão:** a janela vai de 2017 a 2025 e contém cinco edições do Saeb.
- **Consequência:** as defasagens possíveis ficam limitadas. Com gasto desde 2017, a defasagem de 2 anos só vale para o Saeb de 2019 em diante, e a de 4 anos só a partir de 2021. Na camada estadual, o SICONFI começa em 2014, o que permite defasagens maiores.
- **Literatura (dossiê):** os estudos brasileiros de gasto municipal × IDEB (SciELO, ANPEC, ENAP) costumam encontrar efeito defasado, de cerca de quatro anos, e relação heterogênea entre estados. Isso torna a defasagem L4 relevante, apesar de ela só existir para 2021, 2023 e 2025. Cada artigo precisa ser verificado antes de ser citado.

### E3. Recorte geográfico: Brasil inteiro ✅ (Henrique, 2026-10-30)
- **Decisão:** sem foco em SP. O produto é uma ferramenta nacional, com a mesma perspectiva para todos os estados. O pipeline já cobre o Brasil inteiro, e nada precisa ser refeito.
- **Histórico:** a orientadora tinha sugerido SP em 02/10, na fase do ENEM; a sugestão não se manteve depois do pivô.

### E4. Usuário-alvo ✅ (Henrique, 2026-10-30)
- **Decisão:** um agente de secretaria de educação, ou perfil semelhante (analista da educação pública em geral), de qualquer estado ou município. Isso fecha o item D3.
- **Consequência para o dashboard:** linguagem para quem não é estatístico, visão nacional com leitura por UF e por município, e as duas camadas (municipal e estadual) lado a lado.

---

## 3. Gasto

### G1. Fonte do gasto municipal: SIOPE ✅
- **Problema:** SIOPE e SICONFI informam o gasto municipal com educação, mas os valores divergem.
- **Evidência:** razão SICONFI/SIOPE da subfunção 361, despesa paga.
  - Amostra de 40 municípios de 825 a 197 mil habitantes (`reconciliacao_municipal.csv`): mediana de 1,08, com 72% dos casos dentro de ±20% e 28% dentro de ±5%.
  - 30 maiores municípios (`reconciliacao_grandes_municipios.csv`): mediana de 0,91, com 79% dos casos dentro de ±20%. Há casos extremos: São Paulo em 2017 (0,004), São Luís em 2017 (5,36), Jaboatão em 2017 (0,26), e Rio de Janeiro e Porto Alegre sistematicamente entre 0,52 e 0,71.
- **Decisão:** usar o SIOPE na camada municipal.
- **Por quê:** é o sistema específico da educação, cobre de 5.541 a 5.563 municípios com gasto em 361 por ano† e classifica a despesa por subfunção de forma homogênea.
- **Para o Método:** a escolha da fonte afeta o nível do gasto, sobretudo nas capitais. Isso é uma limitação.

### G2. Fonte do gasto estadual: SICONFI ✅
- **Problema:** o SIOPE estadual tem lacunas. MG não declara as subfunções 361/362 em 8 dos 9 anos (só 2024), e RS falta em 2018–2019†.
- **Decisão:** usar o SICONFI (DCA Anexo I-E) na camada estadual. Ele tem as 27 UFs de 2014 a 2025, sem erro de API, e o total da função 12 vem diretamente da conta "12 - Educação" em todos os 243 pares UF/ano de 2017 a 2025 (`siconfi_estados_funcao12.csv`).

### G3. Nunca misturar fontes de gasto dentro da mesma camada ✅
- **Problema:** as fontes discordam inclusive para o mesmo ente. Exemplo: Ensino Médio pago de SP em 2023, com 9,67 bi no SIOPE contra 7,18 bi no SICONFI.
- **Decisão:** cada camada usa uma única fonte. Nenhuma lacuna de uma fonte é preenchida com a outra.

### G4. Gasto estadual = função 12 − subfunção 12.364 ✅ · versão A (2026-10-30)
- **Problema:** a função 12 dos estados inclui o Ensino Superior (universidades estaduais), que não se relaciona com o Saeb.
- **Decisão:** usar a função 12 paga menos a 12.364 paga.
- **Problema em aberto:** em alguns pares UF/ano, a linha 12.364 não aparece†. Entre 2014 e 2025:
  - **RO:** a linha não aparece em nenhum ano (12 de 12).
  - **AC e SE:** a linha só existe em 2025 (falta em 11 de 12).
  - **RS:** falta de 2018 a 2023 (6 anos).
  - **MS** (2015) e **RN** (2016): falta só em um ano anterior a 2017, sem efeito na janela de análise.
- **Correção do registro (2026-10-22):** a versão anterior deste item dizia que RN e MS não tinham a linha em 11 de 12 anos, e AC e SE em 1. A leitura estava invertida: aquele diagnóstico contava os anos em que a linha existe. Além disso, RO tinha ficado de fora porque não tem a linha em ano nenhum.
- **Ordem de grandeza:** onde a linha existe, o Ensino Superior pesa de 0% a 23% da função 12 (mediana de 2,2%; em 2023, PR 19%, SC 15%, BA, SP e CE perto de 10%)†.
- **Duas leituras possíveis:**
  - **(a) Ausência = sem gasto com Ensino Superior nessa subfunção,** e a dedução é zero.
  - **(b) Ausência = dado faltante,** e o par UF/ano sai da amostra ou é imputado.
- **Riscos:** a regra geral do projeto ("ausência não é zero") aponta para (b), mas no DCA é comum que uma conta sem movimento simplesmente não seja publicada, o que favorece (a). Para AC, RO e SE, a hipótese de que o estado não mantém universidade estadual nesses anos favoreceria (a), mas ainda não foi verificada. No RS, a linha existe antes e depois da lacuna de 2018–2023, o que sugere dado faltante ou classificação em outra conta.
- **Implementação provisória:** `Transform_SICONFI.py` gera as duas versões, `GASTO_BASICA_A_*` e `GASTO_BASICA_B_*`, além da marca `SUP364_AUSENTE`. A escolha fica para depois da reunião, sem refazer nada.
- **Dossiê da conta anterior:** a especificação original do Transform estadual já previa tratar a ausência como zero (versão A). O dossiê também registra que o RS tem universidade estadual, e por isso o zero no RS seria provavelmente uma classificação diferente, de efeito pequeno diante do total. Isso não foi verificado.
- **Decisão (Henrique, 2026-10-30):** usar a **versão A**: a ausência da linha 12.364 é tratada como "nada a descontar", para não deixar UF/anos sem informação. A versão B continua calculada nos painéis, só para teste de sensibilidade. O dashboard oficial usa a A.
- **Limitação que permanece (L2):** no RS de 2018 a 2023, se o Ensino Superior estiver lançado em outra subfunção, o gasto da educação básica fica superestimado nesses anos. A conferência no DCA do RS continua recomendada, mas não bloqueia nada.

### G4b. Total da função 12 maior que a soma das subfunções listadas ⚠️ (achado de 2026-10-22)
- **Evidência:** no SICONFI, a soma das subfunções publicadas (12.122, 12.361, …, 12.999) fica abaixo do total "12 - Educação" em vários pares UF/ano. A razão vai de 0,61 a 1,00, com mediana de 0,994; no AC, por exemplo, fica entre 0,67 e 0,75†.
- **Leitura provável:** a função 12 inclui despesas em subfunções de outras funções, como previdência de inativos, que o Anexo I-E não detalha dentro da função 12. Isso não foi verificado.
- **Efeito:** o gasto estadual usado (total da função 12 menos 12.364) pode incluir gastos que não chegam à sala de aula, com peso diferente entre os estados.
- **Encaminhamento:** registrar como limitação. Se houver tempo, testar a variante "soma das subfunções da educação básica" (361 + 362 + 365 + 366 + 367 + 368 + 122) como sensibilidade.

### G5. Subfunção 361 do SIOPE: rótulos que começam com "361" ✅ (revisada em 2026-10-26)
- **Problema:** o rótulo muda ao longo do tempo†. Até 2023 ele é "361 - Ensino Fundamental"; em 2024 e 2025, só "361". Também há linhas "TOTAL …" (de 2017 a 2023), que somariam o mesmo gasto duas vezes, e rótulos fora do padrão. São 117 rótulos distintos de subfunção, segundo o dossiê; um exemplo é "SubFunção 361 - Fonte 01 - Aplic. 110", com uma linha em Louveira-SP 2017 e R$ 146 mil.
- **Decisão (2026-10-26):** filtrar `TIPO == "Municipal"`, `EH_TOTAL == False` e rótulo `DES_SUBF` que **começa** com 361 (expressão `^\s*361\s*(-|$)`). A expressão cobre os dois formatos ("361 - …" e "361") e deixa de fora os rótulos atípicos.
- **Histórico:** de 2026-10-22 a 2026-10-26 o filtro foi `COD_SUBF == "361"` (primeiro número de 3 dígitos do rótulo), que incluía a linha atípica de Louveira. A regra foi alinhada com a do dossiê da conta anterior, que é mais rigorosa.
- **Efeito da troca†:** muda só o gasto de Louveira em 2017 (R$ 146 mil a menos, nominais). No painel, isso afeta 3 linhas: AI 2017 no L0, e as edições de 2019 e 2021 nas defasagens que usam 2017. Nada mais muda.
- **Teste de consistência:** a participação da 361 no gasto total em educação fica estável entre 0,59 e 0,63 de 2017 a 2025†. Ou seja, não há quebra de classificação, e o crescimento nominal do gasto municipal em 361 (95 → 223 bi de 2017 a 2025†) acompanha o gasto total, puxado pela expansão do FUNDEB a partir de 2021.

### G6. O SIOPE por subfunção traz também linhas estaduais ✅
- **Problema:** os arquivos `siope_funcao_*` têm linhas `TIPO = Estadual` de 26 estados†.
- **Decisão:** filtrar `TIPO == "Municipal"` na camada municipal. As linhas estaduais do SIOPE não são usadas (ver G2).

### G7. Despesa paga, acumulada no ano ✅
- **Decisão:** usar a despesa paga (não a empenhada nem a liquidada) do 6º bimestre do SIOPE (`Num_Peri = 6`), que é o acumulado do ano, e a coluna "Despesas Pagas" do SICONFI.
- **Por quê:** a despesa paga mede o recurso que efetivamente saiu.
- **Limitação:** restos a pagar inscritos no ano ficam de fora.

### G12. O gasto por aluno é anual; o Saeb é bienal ✅ · 🟡 sensibilidade (pergunta da orientadora, 2026-10-23)
- **Pergunta:** o gasto por aluno é anual ou bianual?
- **Resposta:** é **anual**. O SIOPE e o SICONFI informam o gasto acumulado de cada ano (2017 a 2025), e o gasto de cada ano é dividido pelas matrículas do mesmo ano†. O que é bienal é o Saeb.
- **Como os dois se encontram:** cada edição do Saeb usa o gasto do mesmo ano (`_L0`). Os anos sem Saeb, como 2018, entram pelas defasagens (`_L1` para a edição de 2019).
- **Evidência:** o gasto por aluno de um ano e o do ano anterior têm correlação de 0,80 entre os municípios (AI, com nota)†. A escolha importa pouco, mas importa.
- **Proposta:** manter o gasto anual como medida principal e testar como sensibilidade a **média do biênio** (ano do Saeb e ano anterior), que capta o investimento acumulado entre duas provas (A4).

### G8. Valores em reais de 2025 ✅
- **Decisão:** deflacionar pelo IPCA médio anual (SIDRA, tabela 1737), com base 2025 = 1.
- **Verificação:** o deflator tem os 12 meses de todos os anos de 2013 a 2025†.

### G9. Código de município com 7 dígitos ✅ (revisada em 2026-10-22)
- **Problema:** o SIOPE usa 6 dígitos, e as demais bases usam os 7 do IBGE.
- **Decisão original:** converter pelo dígito verificador (pesos 1,2,1,2,1,2; somar os algarismos de cada produto; verificador = (10 − soma mod 10) mod 10).
- **Problema encontrado no Transform:** 9 municípios têm código oficial do IBGE que não segue essa regra†: Bom Princípio do Piauí, Brejo do Piauí e Canavieira (PI), Quixaba (PE), Cônego Marinho e Ponto Chique (MG), Coronel Barros (RS), Buriti de Goiás e Buritinópolis (GO). Exemplo: para Brejo do Piauí, a fórmula daria 2201986, mas o código oficial é 2201988. Pela fórmula, esses 9 municípios se perderiam no cruzamento com o Saeb e o Censo, sem nenhum aviso.
- **Decisão revisada:** converter por consulta à tabela de códigos oficiais (Censo 2022 mais Censo Escolar 2017–2025), pelos 6 primeiros dígitos, que são únicos. A fórmula fica só como último recurso, com a marca `CODIGO_POR_FORMULA`. Hoje nenhum código precisa dela, e todos os códigos convertidos existem no IBGE com a mesma UF† (`Transform_SIOPE.py`).

### G11. Gasto 361 igual a zero ⚠️
- **Evidência:** Rio Grande da Serra (SP) declara gasto 361 igual a zero em 2018 e 2020, embora o gasto total em educação seja de ~R$ 15 milhões nesses anos†. Provavelmente o gasto foi classificado em outra subfunção.
- **Encaminhamento:** no painel, tratar o gasto por aluno desses dois pares município/ano como faltante, e não como zero. Registrar o caso.

### G10. O Distrito Federal não existe como município no SIOPE ✅
- **Evidência:** há zero linhas municipais para o DF no SIOPE (2017 e 2025)†, conforme a sondagem em `Sondagem_SIOPE.py`.
- **Decisão:** o DF fica fora da camada municipal e entra só na estadual.

---

## 4. Matrículas (denominador)

### M1. Denominadores por camada ✅
- **Decisão:**
  - Municipal: `QT_MAT_FUND` da rede municipal.
  - Estadual: `QT_MAT_BAS` da rede estadual, somado por UF.
- **Por quê:** é a etapa que cada gasto financia. O 361 é o Ensino Fundamental; a função 12 menos o Ensino Superior é a educação básica.

### M2. Mudança de layout do Censo Escolar em 2025 ✅
- **Problema:** até 2024, as matrículas vêm num arquivo único (`microdados_ed_basica`). Em 2025 elas passaram a vir separadas, em `tabela_escola` e `tabela_matricula`.
- **Decisão:** o extrator trata os dois layouts e, em 2025, junta as tabelas por `CO_ENTIDADE` (`Teste5_SIOPE.py` / `Extract_Censo_Matriculas.py`).
- **Escolas sem matrícula (dossiê):** em 2025, 35.426 das 214.192 escolas (16,5%) não têm linha na Tabela de Matrícula. A proporção é a mesma das escolas sem matrícula em 2024 (12% nas estaduais, 17% nas municipais, 19% nas privadas), então tratá-las como zero matrícula é coerente. Segundo o dossiê, o `QT_MAT_MED` de 2025 mantém a mesma definição dos anos anteriores (soma de propedêutico, magistério e técnico), então a queda do M3 não é mudança de definição.

### M4. Escola sem UF no Censo Escolar 2025 ✅ (2026-10-22)
- **Problema:** uma escola de Uruguaiana (RS, 4319901), com 28 matrículas, veio sem `SG_UF` em 2025. Ela criava uma segunda linha para o município e também ficava de fora da soma estadual.
- **Decisão:** a UF passa a sair dos dois primeiros dígitos do código do município, e as matrículas são somadas de novo por município × rede × ano (`Transform_Matriculas.py`).

### M5. Rede municipal sem matrícula no Fundamental ✅ (2026-10-22)
- **Evidência:** há 88 pares município/ano com rede municipal, mas zero matrícula no Fundamental† (por exemplo, municípios que só oferecem Educação Infantil).
- **Decisão:** nesses casos, o gasto por aluno fica indefinido (faltante), sem divisão por zero.

### M3. Queda das matrículas estaduais do Ensino Médio em 2025 🟡
- **Problema:** `QT_MAT_MED` estadual cai 6,6% em 2025 (instruções do projeto; investigado em `Teste7_SINCOFI.py`). No total, a educação básica estadual cai de 14,05 para 13,33 milhões entre 2024 e 2025 (−5,1%)†.
- **Encaminhamento:** não se sabe se a queda é real ou efeito do novo layout. Tratar 2025 com cautela na camada estadual e testar a sensibilidade sem esse ano.

---

## 5. Desempenho

### S1. Fonte do Saeb: planilhas de divulgação do IDEB ✅
- **Problema:** os microdados do Saeb são por aluno, pesados (GB por edição) e exigem pesos amostrais.
- **Decisão:** usar as planilhas de divulgação do IDEB do Inep, que já trazem as notas do Saeb agregadas por município/UF e por rede. São elas: `VL_NOTA_MATEMATICA`, `VL_NOTA_PORTUGUES` (em pontos), `VL_NOTA_MEDIA` (nota padronizada N, de 0 a 10), `VL_INDICADOR_REND` e `VL_OBSERVADO` (IDEB).
- **Verificação:** o MD5 dos arquivos confere com o publicado pelo Inep, e o número de municípios com IDEB 2025 na rede pública bate exatamente com a nota informativa (AI 5.478, AF 5.491, EM 5.428)†.
- **Extensão possível:** os microdados ficam para depois, se a orientadora pedir controles por questionário.

### S2. Medida principal: nota do Saeb ✅
- **Decisão:** a medida principal é a nota do Saeb (`NOTA_MT`, `NOTA_LP`, `NOTA_N`). O IDEB e o rendimento são medidas secundárias.
- **Por quê:** o IDEB mistura nota e fluxo escolar, e o fluxo responde a políticas de aprovação, não só a aprendizado.

### S3. Rede analisada em cada camada ✅
- **Decisão:** a camada municipal usa só a rede Municipal (AI e AF); a estadual, só a rede Estadual (AF e EM). As redes "Pública" (agregada) e Federal ficam de fora (`Transform_SAEB.py`).
- **Por quê:** o desempenho comparado é o da rede que o gasto financia.

### S4. Anos Iniciais como desfecho principal; Anos Finais com amostra selecionada 🟡
- **Problema:** só 3.913 municípios têm rede municipal de Anos Finais, e de 2.630 a 3.315 deles têm nota, conforme o ano†. Em Anos Iniciais, são de 4.754 a 5.320 municípios com nota†. A amostra de AF é selecionada: são os municípios que assumiram essa etapa, o que pode estar associado a porte e capacidade fiscal.
- **Decisão:** AI é o desfecho principal da camada municipal; AF entra como complementar, e a seleção vai para as limitações.
- **Pergunta para a orientadora:** manter AF na camada municipal ou deixá-lo só na estadual?

### S5. Edição de 2021 (pandemia) 🟡
- **Problema:** em 2021, o número de linhas município × rede com nota cai em relação a 2017: −11% em AI, −17% em AF e −37% em EM (todas as redes somadas)†.
- **Decisão:** manter 2021 e rodar um teste de sensibilidade sem esse ano.

### S6. Roraima sem nota de Anos Iniciais na rede estadual ✅
- **Evidência:** RR não tem nota de AI na rede estadual em nenhum ano de 2017 a 2025†.
- **Por que não afeta:** AI não entra na camada estadual (S3). AF e EM estão completos nas 27 UFs.

### S7. Nomes de UF abreviados na planilha de regiões/UFs ✅ (erro corrigido)
- **Problema:** a planilha escreve "M. G. do Sul", "R. G. do Norte" e "R. G. do Sul", e o extrator descartava MS, RN e RS, deixando a camada estadual com 24 UFs.
- **Decisão:** mapear as abreviações em `Extract_SAEB.py` (commit `e3153de`). Agora são 27 UFs.

### S8. Seleção da amostra pela divulgação do Saeb 🟡 (2026-10-22)
- **Problema:** o Inep só divulga a nota das redes que atingem critérios mínimos de participação. Segundo o dossiê da conta anterior, a escola precisa de pelo menos 10 estudantes e 80% de participação, e o município, de 10 estudantes e 50%. O critério municipal teria mudado entre 2021 e 2022. Esses números não foram conferidos aqui na nota técnica do Inep, e é preciso conferi-los antes de citá-los no TCC. Entre os municípios com rede municipal, ficam sem nota†:
  - **Anos Iniciais:** de 2,4% (2025) a 12,8% (2021).
  - **Anos Finais:** de 15,3% (2017) a 32,8% (2021). Em 2023, 157 dos 717 municípios sem nota de AF não tinham matrícula municipal nessa etapa naquele ano.
  - **Gasto ausente:** é irrelevante, no máximo 18 municípios por edição.
- **A ausência não é aleatória.** Em Anos Iniciais 2023, comparando as redes sem nota com as que têm nota†:

  | | Com nota | Sem nota |
  |---|---|---|
  | Matrículas AI (mediana) | 721 | 182 |
  | População (mediana) | 11,9 mil | 4,5 mil |
  | Gasto por aluno (mediana) | R$ 13,5 mil | R$ 16,6 mil |

  Em Anos Finais o padrão é o mesmo: 98 contra 690 matrículas de AF, e R$ 14,9 mil contra R$ 12,5 mil de gasto por aluno.
- **Efeito:** os resultados valem para as redes com nota divulgada. Ficam sub-representados os municípios pequenos, que têm gasto por aluno mais alto, provavelmente por falta de escala. Isso pode distorcer a relação gasto × nota justamente nos gastos mais altos. É mais um motivo para Anos Iniciais ser o desfecho principal (S4).
- **Decisão provisória:**
  1. Não imputar notas (A3).
  2. Descrever a cobertura e a comparação entre incluídos e excluídos no Método.
  3. Controlar o porte da rede (matrículas) ou a população nos modelos.
  4. Testar a sensibilidade com um painel balanceado (municípios com nota nas cinco edições).
- **No dashboard:** as notas de rodapé explicam a ausência e a tabela de cobertura mostra a parcela por edição.

### S9. Medida de desempenho no dashboard ✅ (2026-10-22)
- **Problema:** a primeira versão do dashboard mostrava só Matemática, uma simplificação que não havia sido registrada.
- **Decisão:** o dashboard passou a ter um seletor com Matemática, Português, nota padronizada N (0 a 10, que combina as duas provas) e IDEB, e a tabela mostra as quatro medidas.
- **Evidência:** em AI 2023, a correlação entre municípios é de 0,96 entre Matemática e Português e de 0,99 entre Matemática e N†.
- **Medida principal, 1ª versão (2026-10-30):** a nota padronizada N seria a medida padrão, desde que o cálculo da padronização ficasse claro (S10). **Substituída no mesmo dia** pela decisão abaixo.
- **Medida principal, decisão final (Henrique, 2026-10-30) ✅:** usar as **proficiências do Saeb em pontos**, Matemática e Língua Portuguesa, analisadas separadamente. A nota N fica só como medida secundária, ao lado do IDEB, por causa das limitações vistas em S10:
  - **Saturação no teto:** a N corta a proficiência nos limites de 1997. Isso já acontece nos dados: 43 redes municipais de Anos Iniciais têm Matemática acima de 322 pontos e ficam presas em 10, e 6 têm Português acima de 324†. A proficiência em pontos preserva essa informação.
  - **Comparação entre etapas:** a escala do Saeb em pontos é comum às etapas, então um 5º ano com 220 e um 9º ano com 250 estão na mesma régua. A N não é: cada etapa tem limites próprios.
  - **Duas disciplinas:** a N mistura Matemática e Português. Em pontos, as duas podem ser analisadas em separado.
  - **Igualdade dentro da etapa:** fora do corte, a N é uma transformação linear das proficiências. Por isso, dentro de uma etapa, a troca não muda o sinal das associações.
- **"Dados brutos" aqui significa a proficiência média da rede em pontos**, que vem nas planilhas do Inep (`VL_NOTA_MATEMATICA` e `VL_NOTA_PORTUGUES`). Não são os microdados do Saeb por aluno, que continuam fora do escopo (S1).
- **Efeito no dashboard e no Power BI:** a medida padrão passa a ser Matemática em pontos, com Português ao lado. O seletor do dashboard HTML já abre em Matemática.

### S10. Como a nota padronizada N é calculada ✅ (verificado em 2026-10-30)
- **Quem calcula:** o **Inep**. A N vem pronta nas planilhas de divulgação (`VL_NOTA_MEDIA`). O projeto não padroniza nada, só usa o valor publicado.
- **Fórmula:** para cada disciplina, a proficiência do Saeb é levada a uma escala de 0 a 10 entre um limite inferior e um superior fixos. Valores fora dos limites são cortados no limite. A N é a média simples das duas disciplinas:
  - N_disciplina = 10 × (proficiência − limite inferior) ÷ (limite superior − limite inferior)
  - N = (N_Matemática + N_Português) ÷ 2
- **Limites por etapa:**

  | Etapa | Matemática | Língua Portuguesa |
  |---|---|---|
  | Anos Iniciais (5º ano) | 60 a 322 | 49 a 324 |
  | Anos Finais (9º ano) | 100 a 400 | 100 a 400 |
  | Ensino Médio | 111 a 467 | 117 a 451 |

- **Verificação†:** com esses limites, a fórmula reproduz **exatamente** a N publicada em todas as 41.465 linhas de município e UF com as duas notas (diferença máxima de 0,0000). A relação IDEB = N × indicador de rendimento também confere, com diferença máxima de 0,05 (arredondamento do Inep).
- **Interpretação:** como os limites são fixos, a N é comparável entre edições dentro da mesma etapa. Ela **não** é comparável entre etapas: um 5,0 em Anos Iniciais não equivale a um 5,0 em Anos Finais. Por isso o dashboard sempre filtra uma etapa por vez.
- **Fonte formal, conferida em 2026-10-30:** Inep, *Nota Técnica – Índice de Desenvolvimento da Educação Básica (Ideb)*, a "Nota Técnica nº 1, concepção do Ideb", com cópia em `docs/referencias/Inep_Nota_Tecnica_n1_concepcao_IDEB.pdf`, baixada de download.inep.gov.br. A nota confirma:
  - a fórmula (equação 2);
  - o corte nos limites: abaixo do inferior, fixa no inferior; acima do superior, fixa no superior;
  - os limites da Tabela 2, iguais aos usados acima;
  - a origem dos limites: média ± 3 desvios-padrão das proficiências do Saeb de 1997, o ano em que a escala foi definida (Tabela 1);
  - o IDEB = N × P, sendo P o indicador de rendimento (equações 1 e 3).

  A nota usa a nomenclatura antiga (4ª e 8ª séries), que corresponde ao 5º e ao 9º ano atuais.

---

## 6. Controles

### C1. IDHM por UF do mesmo ano da edição do Saeb ✅ (orientadora, 2026-10-23)
*(antes registrada como D1)*

- **Decisão final:** cada edição do Saeb usa o IDHM da UF do mesmo ano (Saeb 2017 ← IDHM 2017, …, Saeb 2023 ← IDHM 2023). **A edição de 2025 fica sem IDHM**, porque a série anual do PNUD (Radar IDHM, PNUD/FJP/IBGE, base PNAD Contínua, divulgada em 26/05/2026) termina em 2024. Isso é uma limitação, documentada em L4.
- **Consequência prática:** os modelos que usam o IDHM cobrem 2017–2023. A edição de 2025 entra nas análises descritivas e nos modelos sem IDHM. No painel, o IDHM é nulo em todas as linhas de 2025 e só nelas† (8.612 linhas com nota no municipal, 54 no estadual).
- **Histórico:** em 2026-10-21 tínhamos adotado provisoriamente o IDHM do ano anterior (t−1) em todas as edições, para não deixar 2025 sem controle. A orientadora preferiu comparar com o IDHM do ano respectivo e tratar 2025 como limitação.
- **Implementação (2026-10-26):** `Transform_IDHM.py` deixou de criar `ANO_REF_SAEB`, e `Montar_Paineis.py` casa o IDHM pelo próprio `ANO`. A coluna `ANO_IDHM` saiu dos painéis, porque agora é igual a `ANO`. As demais colunas ficaram idênticas às da versão anterior (conferido).
- **Para o Método:** "O controle socioeconômico é o IDHM da UF no mesmo ano da aplicação do Saeb. Como a série do PNUD termina em 2024, a edição de 2025 não tem esse controle."
- **Observação:** o rodapé da planilha diz "Atlas … 2022", embora a série vá até 2024. Registrar a data em que o arquivo foi baixado na citação da fonte.

### C1b. O IDHM impacta ou é impactado pela educação? ✅ (decidido em 2026-10-30)
- **Problema:** o IDHM tem uma dimensão de Educação, que mede a escolaridade da população adulta e o fluxo escolar de crianças e jovens. Controlar pelo IDHM total pode significar controlar, em parte, pelo próprio resultado educacional (circularidade, ou "mau controle").
- **Evidência inicial (estados, Anos Finais, IDHM do mesmo ano, 2017–2023)†:** correlação com a nota padronizada N de 0,49 para o IDHM total, 0,48 para o IDHM Educação e 0,45 para o IDHM Renda. Educação e Renda têm 0,77 entre si.
- **Decisão (Henrique, 2026-10-30):** **excluir da análise os índices que medem escolaridade**, para evitar circularidade. Saem o IDHM Educação e o IDHM total, que contém a dimensão de Educação. Os controles de contexto socioeconômico passam a ser o **IDHM Renda** e o **IDHM Longevidade**.
- **Implementação:** as colunas continuam nos painéis, para registro e transparência, mas os modelos, os clusters e o dashboard oficial usam só Renda e Longevidade.
- **A taxa de alfabetização (C2) continua sendo usada?** Ela também mede escolaridade, só que da população de 15 anos ou mais. A diferença é que se refere à população adulta e é uma foto fixa de 2022, que não varia com o desempenho das edições do Saeb. Por isso, o risco de circularidade é menor. Ela é usada para formar os grupos de pares (P5). Se a orientadora entender que ela também deve sair, os grupos passam a usar só porte e IDHM Renda.

### C2. Alfabetização: Censo 2022, estática ✅
- **Decisão:** usar a taxa de alfabetização de 15 anos ou mais do Censo Demográfico 2022, por município, como controle fixo no tempo. Com efeitos fixos de município, ela só entra em análises sem efeito fixo, como a comparação entre municípios.
- **Problema:** o município `5101837`, Boa Esperança do Norte-MT (nome que vem do Saeb), aparece no Censo Escolar e no Saeb a partir de 2025 e não existe no Censo 2022†. Provavelmente foi instalado depois de 2022 (não confirmado). Ele fica sem esse controle e também não aparece no SIOPE até 2025. É uma única linha do painel.

### C3. Infraestrutura: Censo Escolar ✅
- **Decisão:** usar as proporções de escolas com biblioteca, laboratórios, internet, água potável etc., por município × rede × ano, de 2015 a 2025 (`censo_escolar_transformado`).

---

## 7. Regras de análise

### A1. Associação, não causalidade ✅
Falar sempre em associação e eficiência relativa.

### A2. Efeitos fixos e erros-padrão ✅
- **Camada municipal:** efeitos fixos de município.
- **Camada estadual:** só 27 unidades, com erros-padrão agrupados por UF. O baixo número de clusters é uma limitação.

### A3. Ausência nunca é zero ✅
`-` e `ND` nas planilhas viram nulo, nunca 0. As exceções precisam ser justificadas caso a caso (ver G4).

### A4. Testes de sensibilidade previstos 🟡
1. Sem 2021 (S5).
2. Sem 2025 na camada estadual (M3).
3. IDHM Renda no lugar do IDHM total, e vice-versa (C1b).
4. Tratamento alternativo da 12.364 (G4) e gasto estadual pela soma das subfunções da educação básica (G4b).
5. Painel balanceado: só municípios com nota nas cinco edições (S8).
6. Gasto médio do biênio (ano do Saeb e ano anterior) no lugar do gasto anual (G12).

*(Revisão de 2026-10-23: saiu o teste "com e sem os gastos extremos", porque a orientadora decidiu não removê-los (A5). Saiu também o teste "IDHM do mesmo ano", porque ele passou a ser a especificação principal (C1).)*

### A6. Análise de clusters ✅ desenvolver · 🟡 desenho técnico (2026-10-30)
- **Decisão da orientadora:** incluir uma análise de clusters.
- **Decisão (Henrique, 2026-10-30):** os clusters **devem ser desenvolvidos**, aproveitando a riqueza da distribuição já disponível (o histograma de gasto e notas por município). O desenho técnico abaixo é a proposta de trabalho e foi mantido, porque não houve objeção. Fica sujeito a ajuste quando os primeiros grupos forem vistos.
- **Proposta de desenho (a validar):** agrupar os municípios **só pelo contexto** (porte da rede, população, alfabetização, IDHM Renda, infraestrutura) e depois comparar gasto por aluno e nota dentro de cada grupo. Assim se identifica quem entrega mais ou menos do que os pares comparáveis, que é o centro da pergunta do TCC e é fácil de explicar a um gestor.
- **Alternativa:** agrupar por tudo junto (gasto, nota e contexto), para descrever perfis como "alto gasto e baixo desempenho". É mais descritiva e responde menos à pergunta de eficiência.
- **Implementação (2026-10-30, `src/Analise/Analise_Clusters.py`) ✅:**
  - **Unidade:** o município, num agrupamento único para todo o período. As variáveis de contexto são médias de 2017–2025, e os mesmos grupos servem a todas as etapas e edições. Ficam de fora só os 3 municípios sem variáveis completas: Fernando de Noronha, Boa Esperança do Norte e Brasília. No total, são 5.568 municípios.
  - **Variáveis (padronizadas), sem gasto nem nota:**
    - log10 da população (Censo 2022);
    - taxa de alfabetização de 15 anos ou mais (Censo 2022);
    - IDHM Renda e IDHM Longevidade da UF, média de 2017–2023, sem a dimensão Educação (C1b);
    - índice de infraestrutura da rede municipal: média das 8 proporções do Censo Escolar, de 2017–2025.
  - **Método:** k-médias com 50 inicializações e semente fixa (42).
  - **Escolha de k (diagnóstico em `diagnosticos/clusters_escolha_k.csv`)†:** a silhueta é de 0,32 com k=3 e fica em torno de 0,23 de k=5 a k=10. Foi escolhido **k = 7**: a silhueta é praticamente igual à de k=6 (0,233 contra 0,229), e o 7º grupo separa os municípios grandes do Norte e do Nordeste, cuja mediana é de 101 mil habitantes, para que grandes cidades sejam comparadas entre si. Com k=3, os grupos seriam amplos demais para servir de pares.
  - **Os 7 grupos†**, ordenados pela alfabetização média:

    | Grupo | Rótulo | Municípios | População mediana | Alfabetização média |
    |---|---|---|---|---|
    | 1 | Nordeste · pequenos · alfabetização mais baixa | 952 | 7,4 mil | 78,3% |
    | 2 | Nordeste · médios · alfabetização mais baixa | 1.037 | 18,3 mil | 81,2% |
    | 3 | Sudeste · pequenos · alfabetização intermediária | 844 | 6,8 mil | 90,5% |
    | 4 | Centro-Oeste · pequenos · alfabetização intermediária | 578 | 9,5 mil | 90,9% |
    | 5 | Nordeste e Norte · grandes · alfabetização intermediária | 272 | 101,7 mil | 92,3% |
    | 6 | Sul e Sudeste · pequenos · alfabetização mais alta | 1.166 | 5,4 mil | 93,8% |
    | 7 | Sudeste · médios · alfabetização mais alta | 719 | 44,8 mil | 96,1% |

  - **Rótulos:** são automáticos. A região é a predominante, ou as duas principais quando a primeira tem menos de 60% dos municípios. O porte segue a população mediana (pequenos, abaixo de 10 mil; médios, até 50 mil; grandes, acima). A alfabetização usa os terços nacionais dos municípios (85,3% e 93,4%).
  - **Leitura honesta:** a silhueta baixa indica que o contexto varia de forma contínua. Os grupos são uma **partição útil para formar pares**, e não "tipos" naturalmente separados (L16). Eles também saem muito ligados à região, porque o IDHM só existe por UF.
  - **Saídas:** `data/processed/cluster_municipio.parquet` (grupo de cada município) e `cluster_resumo.parquet` (perfil de cada grupo).
  - **Versão estadual:** não haverá. Com 27 UFs, não há como formar grupos com pares suficientes.

### A8. Indicador de eficiência municipal ✅ (implementado e escolhido em 2026-10-30)
- **Definição:** o indicador mostra **quantos pontos do Saeb o município ficou acima (+) ou abaixo (−) do esperado para o seu gasto por aluno e o seu contexto**. É o resíduo de um modelo de regressão, estimado por etapa (AI e AF) e por disciplina (Matemática e Português, em pontos; S9). Script: `src/Analise/Eficiencia.py`.
- **Modelo:** proficiência = a + b·log(gasto por aluno do ano) + contexto + efeitos de edição + erro, estimado por MQO com erros-padrão agrupados por município. O contexto é:
  - log da população e alfabetização (Censo 2022);
  - infraestrutura da rede municipal no ano;
  - log das matrículas do Fundamental, que mede o tamanho da rede;
  - IDHM Renda e Longevidade da UF no ano (só no modelo principal).
- **Duas versões, ambas gravadas em `data/processed/eficiencia_municipal.parquet`:**
  - **Principal (com IDHM), de 2017 a 2023:** compara os municípios **em escala nacional**. Não cobre 2025, porque não há IDHM 2025 (C1).
  - **Alternativo (efeitos fixos de UF), de 2017 a 2025:** compara cada município **com os do mesmo estado**. Cobre 2025.
- **Resultados (associação, não causa)†:**

  | Etapa e disciplina | log(gasto), modelo principal | log(gasto), modelo alternativo | R² principal / alternativo |
  |---|---|---|---|
  | AI Matemática | +0,92 (EP 0,72; p = 0,20) | +4,33 (EP 0,60; p < 0,001) | 0,39 / 0,52 |
  | AI Português | +0,89 (EP 0,62; p = 0,15) | +4,15 (EP 0,52; p < 0,001) | 0,41 / 0,52 |
  | AF Matemática | +1,57 (EP 0,94; p = 0,10) | +5,20 (EP 0,82; p < 0,001) | 0,28 / 0,35 |
  | AF Português | +1,18 (EP 0,81; p = 0,15) | +3,19 (EP 0,68; p < 0,001) | 0,28 / 0,37 |

  - **Leitura:** dentro do mesmo estado, 10% a mais de gasto por aluno se associa a cerca de 0,3 a 0,5 ponto a mais no Saeb. Na comparação nacional com o IDHM, a associação é menor e não significativa. Coeficientes completos em `diagnosticos/eficiencia_coeficientes.csv`.
- **Robustez do ranking†:**
  - os resíduos dos dois modelos têm correlação de 0,87 (AI) a 0,92 (AF), então a ordem dos municípios muda pouco;
  - o indicador é persistente: o resíduo de 2019 tem correlação de 0,61 com o de 2023, e o de 2023 tem 0,70 com o de 2025 (AI Matemática). Quem fica acima do esperado tende a continuar acima.
- **Diferença que importa para o dashboard:** o modelo principal capta diferenças entre estados. Por exemplo, 90% dos municípios do Ceará ficam acima do esperado em AI Matemática 2023. O alternativo, por construção, coloca cerca de metade de cada estado acima e metade abaixo (CE: 45%).
- **Decisão (Henrique, 2026-10-30): o indicador oficial é a versão nacional, com IDHM.** Ela é coerente com a ferramenta nacional, que usa a mesma régua para todos os estados (E3), e preserva as diferenças entre estados, que interessam a um analista da educação pública.
  - **Consequência:** o indicador de eficiência existe para as edições de **2017, 2019, 2021 e 2023**. Em 2025, o dashboard mostra gasto e proficiência, mas não a eficiência, por falta do IDHM 2025 (C1, L4).
  - **A versão dentro do estado fica como teste de robustez:** a correlação entre os rankings é de 0,87 a 0,92. As colunas `*_ALT` continuam no arquivo.
- **Também gravado:** a comparação descritiva com os pares do cluster (nota − mediana do cluster; gasto ÷ mediana do cluster), por edição, e o percentil do resíduo dentro de cada etapa, disciplina e edição.

### S11. Saltos atípicos de proficiência ⚠️ (achado de 2026-10-30)
- **Evidência†:** os municípios com os maiores resíduos em AI Matemática 2023 têm proficiências de 330 a 357 pontos, mais altas que as das redes de capitais ricas, em municípios pequenos. Alguns sobem mais de 130 pontos em 6 anos: Ibateguara-AL foi de 195 (2017) para 345 (2025), e Santana do Mundaú-AL de 200 para 357 (2023). Como referência, a escala do Saeb avança cerca de 25 pontos por ano de escolaridade.
- **Concentração:** as redes de AI com mais de 300 pontos em Matemática estão quase todas no Ceará e em Alagoas (2025: 30 no CE e 10 em AL). A média de AL subiu de 200 (2017) para 238 (2025).
- **Leitura:** pode ser melhoria real, artefato de participação ou distorção ligada a incentivos. Por exemplo, a distribuição do ICMS educacional pelo IDEB em alguns estados é citada nesse debate. **Nenhuma dessas hipóteses foi verificada aqui.**
- **Encaminhamento:** marcar esses casos no dashboard como "salto atípico" e não interpretá-los como eficiência sem checagem. Vale procurar notas do Inep e literatura sobre o tema antes de escrever os resultados.
- **Regra proposta (implementada em `Eficiencia.py`, 2026-10-30; a confirmar) 🟡:**
  - variação = proficiência da edição − proficiência da edição anterior da mesma rede, etapa e disciplina, só entre edições consecutivas (2 anos);
  - atípica quando a variação se afasta **mais de 3 desvios-padrão** da média das variações da mesma etapa e disciplina, para cima ou para baixo;
  - colunas `VARIACAO_EDICAO_ANTERIOR` e `SALTO_ATIPICO` em `eficiencia_municipal.parquet`. A marca **não exclui** ninguém (coerente com A5); o dashboard mostra um aviso na ficha e um ícone no ranking.
- **Resultado†:** 633 linhas marcadas (0,8% das 82.260), 434 altas e 199 quedas. As quedas também entram, porque costumam ser o "outro lado" de uma alta isolada.
- **Alternativas consideradas:** limite fixo em pontos (por exemplo, 50 pontos em dois anos, cerca de dois anos de aprendizado), mais fácil de explicar, mas que não se ajusta às diferenças de dispersão entre etapas e disciplinas; e regra pela distância à tendência da própria rede, que exige mais edições do que a série tem.

### A7. Forma simples de acessar o projeto 🟡 (pedido da orientadora, 2026-10-23)
- **Decisão da orientadora:** ao final, oferecer um acesso simples ao projeto, como um QR Code.
- **Requisito:** o QR Code precisa apontar para um endereço que a pessoa consiga abrir sem login. Hoje o repositório no GitHub é privado.
- **Opções:** publicar o dashboard como página na web (link do claude.ai, GitHub Pages com o repositório público, ou Power BI publicado) e gerar o QR Code por script a partir desse link.
- **Quando:** na etapa final, depois do dashboard definitivo.

### A5. Valores extremos de gasto por aluno: manter na análise ✅ (orientadora, 2026-10-23)
- **Decisão final:** a orientadora decidiu que **não é preciso remover os outliers**. Todos os valores entram na análise. A marca `GASTO_EXTREMO_L{k}` continua no painel só como informação, por exemplo para comentar casos no texto.
- **Evidência:** a distribuição do gasto municipal por aluno (L0, linhas com nota de AI) tem mediana de R$ 11,2 mil e intervalo de 1% a 99% entre R$ 5,3 mil e R$ 25,6 mil†. Nas pontas, porém, aparecem valores implausíveis:
  - **Muito baixos:** Cáceres-MT 2021 (R$ 210), Carlópolis-PR 2023 (R$ 305), São Luís-MA 2017 (R$ 1,8 mil). São Luís 2017 já tinha aparecido como caso extremo na reconciliação com o SICONFI (G1).
  - **Muito altos:** redes com poucas matrículas, como Queluzito-MG 2023 (73 alunos, R$ 64,5 mil).
  - 131 dos 50 mil pares município/ano têm o gasto 361 multiplicado por mais de 3 ou dividido por mais de 3 de um ano para o outro†.
- **Marcação:** o painel marca com `GASTO_EXTREMO_L{k}` os valores fora do intervalo de 0,5% a 99,5% do ano (225 linhas de AI, 174 delas com nota), cerca de 0,7% da amostra com nota (lista em `diagnosticos/gasto_aluno_extremos_municipal.csv`).
- **Ainda a definir na análise:** usar o logaritmo do gasto por aluno, que reduz o peso das pontas sem remover ninguém, é compatível com a decisão e continua sendo a sugestão para a especificação principal.

---

## 7b. Painéis (cruzamento das bases)

### P1. Estrutura dos painéis ✅ (2026-10-22)
- **Script:** `src/Transform/Montar_Paineis.py`. As saídas ficam em `data/processed/`.
- **Painel municipal (`painel_municipal.parquet`):** uma linha por município × etapa (AI, AF) × edição do Saeb. São 46.815 linhas e 39 colunas, com chave única†.
  - **Base:** a lista de municípios com rede municipal no Saeb.
  - **Colunas:** notas e IDEB, matrículas, gasto 361, gasto por aluno nas defasagens 0, 1, 2 e 4 anos, a marca de valor extremo, alfabetização e população (Censo 2022), região, IDHM da UF do mesmo ano (C1; nulo em 2025) e a infraestrutura da rede municipal no mesmo ano.
- **Painel estadual (`painel_estadual.parquet`):** uma linha por UF × etapa (AF, EM) × edição. São 270 linhas e 36 colunas, com chave única†.
  - **Colunas:** gasto por aluno nas versões A e B (G4) e nas mesmas defasagens, alfabetização da UF (soma dos municípios), IDHM do mesmo ano (nulo em 2025) e infraestrutura da rede estadual (média municipal ponderada pelo número de escolas).
- **Atualização de 2026-10-26:** com a troca do IDHM para o mesmo ano (C1), a coluna `ANO_IDHM` saiu dos dois painéis (antes eram 40 e 37 colunas).
- **Regras do gasto por aluno:**
  - O gasto do ano t−k é dividido pelas matrículas do próprio ano t−k.
  - Gasto 361 igual a zero (G11) ou matrícula igual a zero (M5) viram nulo.
  - Fora o IDHM de 2025 (C1), os controles só ficam nulos para Boa Esperança do Norte-MT (5101837), que está fora do Censo 2022, ver C2.

### P2. Cobertura das defasagens ✅
- **Municípios:** o gasto começa em 2017. Por isso, L1 e L2 só existem a partir do Saeb 2019 e L4 a partir de 2021. Com nota e gasto L0, o painel tem de 4.750 a 5.306 municípios em AI e de 2.629 a 3.310 em AF, conforme o ano†.
- **Estados:** o gasto do SICONFI começa em 2014, mas as matrículas extraídas começam em 2017. Na prática, as defasagens estaduais têm a mesma limitação das municipais.

### P3. Matrículas de 2015–2016 para estender as defasagens estaduais 🟡
- **Situação:** com as matrículas de 2015 e 2016, o Saeb 2017 ganharia L1 e L2 na camada estadual, e o de 2019 ganharia L4. Os microdados do Censo de 2015 e 2016 já estão na pasta de brutos do repositório antigo. Não existe Censo de 2014 na pasta, então o L4 de 2017 não tem como ser calculado.
- **Custo:** rodar o `Extract_Censo_Matriculas.py` para 2015 e 2016, depois de copiar os brutos.
- **Decisão:** pendente. Vale a pena só se a análise estadual usar defasagens.

### P4. Tabelas de apoio para análise e Power BI ✅ (2026-10-27)
- **Decisão:** o `Montar_Paineis.py` passou a gravar também quatro tabelas de apoio em `data/processed/`. São a base comum do dashboard HTML e do futuro Power BI.
  - `dim_municipio`: 5.571 municípios, com nome, UF, região, população, porte e faixa de alfabetização.
  - `dim_uf`: 27 UFs.
  - `gasto_municipal_anual`: gasto por aluno de todos os anos de 2017 a 2025, não só os de Saeb.
  - `gasto_estadual_anual`: o mesmo para as UFs, nas versões A e B.
- **Porte:** classes de população do IBGE, pelo Censo 2022 (até 5 mil; 5 a 10 mil; 10 a 20 mil; 20 a 50 mil; 50 a 100 mil; 100 a 500 mil; mais de 500 mil). São 1.324, 1.170, 1.367, 1.052, 338, 278 e 41 municípios, nessa ordem, mais 1 sem informação (Boa Esperança do Norte)†.
- **Faixa de alfabetização:** terços nacionais da taxa de alfabetização de 15 anos ou mais (Censo 2022), com 1.856 a 1.857 municípios cada†. Serve para formar grupos de pares por contexto.
- **Verificação:** a refatoração (o cálculo do gasto anual virou função própria) manteve os painéis idênticos, linha a linha.
- **Correção de escala (2026-10-27):** a taxa de alfabetização do painel estadual estava multiplicada por 100 (91,2), enquanto a municipal vinha como proporção do IBGE (0,87). As duas agora estão como **proporção de 0 a 1**. O dashboard mostra em porcentagem.

### P6. Malha municipal simplificada para o mapa ✅ (2026-10-27)
- **Fonte:** Malha Municipal do IBGE, versão 2025 (`BR_Municipios_2025.shp`, SIRGAS 2000, 5.573 polígonos, cerca de 20 milhões de pontos, 320 MB). Foi copiada do repositório antigo para `data/raw/Malha Municipal/`, que fica fora do Git.
- **Simplificação (`src/Visualizacao/Gerar_Malha.py`):**
  - projeção equiretangular, com a longitude multiplicada por cos 15°, a latitude média do Brasil;
  - encaixe dos vértices numa grade de 0,005° (cerca de 550 m). As fronteiras compartilhadas encaixam no mesmo ponto, o que evita buracos entre vizinhos;
  - Douglas-Peucker em cada anel, com tolerância de cerca de 1,6 km.
- **Resultado:** 117 mil pontos e 0,74 MB, com todos os 5.571 municípios da dimensão. Os contornos são aproximados, servem para visualização e não para cálculo de área.
- **Descartados:** os polígonos 4300001 e 4300002, que são as áreas operacionais da Lagoa Mirim e da Lagoa dos Patos (RS), e não municípios.
- **Dependência nova:** `pyshp` (leitura do shapefile), instalada no Anaconda em 2026-10-27 com autorização do Henrique.
- **TopoJSON para o Power BI (2026-10-30):** o mesmo script grava também `malha_municipios.topojson` (5.571 geometrias, 1,5 MB), para o visual "Mapa de formas". Coordenadas inteiras da grade, com transformação de volta para graus; chave `CD_MUN` (também em `id`), igual a `CO_MUNICIPIO`.
  - **Orientação dos anéis:** o Power BI desenha com o d3, que exige anel externo no sentido horário e buraco no anti-horário. A marca externo/buraco vem do anel original do shapefile, e o anel simplificado é forçado a essa orientação.
  - **Ilhas degeneradas:** em 3 municípios com ilhas minúsculas, a simplificação deixava anéis de área quase zero, que o d3 lê como "o globo inteiro". Esses anéis saem quando o município tem outro anel maior (o maior sempre fica). Isso também muda um pouco o JSON do HTML (116.311 pontos).
  - **Conferência:** o TopoJSON foi desenhado com o d3 numa página de teste. Nenhuma geometria virou globo invertido, e o mapa ficou igual ao do HTML.

### P7. Modelo de dados e especificação do dashboard oficial ✅ (2026-10-30)
- **Script:** `src/Visualizacao/Preparar_PowerBI.py` grava 12 tabelas em `data/processed/powerbi/`, num modelo em estrela: 8 dimensões (município com cluster, UF, cluster, ano, etapa, disciplina e os parâmetros defasagem e modelo) e 4 fatos (desempenho e gasto, municipal e estadual).
- **Formato longo:** os fatos de desempenho têm uma linha por rede × etapa × **disciplina** × edição, com a proficiência numa coluna só. Assim, um filtro de disciplina serve para todas as páginas.
- **Nada é recalculado:** o script só junta e empilha tabelas já validadas. Ele confere chaves únicas, ausência de órfãos e que a proficiência da eficiência é a mesma do painel.
- **Contagens†:** 93.630 linhas no fato municipal; 82.390 com proficiência; 65.084 com eficiência oficial; 82.260 com eficiência de robustez. **130 redes com nota ficam sem eficiência**, porque falta o gasto ou algum controle.
- **Especificação (`powerbi/especificacao_dashboard.md`):** público, perguntas, modelo, relacionamentos, indicadores formais (proposta para D2), 9 páginas, regras visuais, riscos e critérios de aceite. Medidas em `powerbi/medidas.dax`, carregamento em `powerbi/carregar_dados.pq` e tema em `powerbi/tema_tcc.json`, com a mesma paleta do HTML.
- **Agregações iguais às do HTML:** gasto = mediana entre as redes; nota = média simples; associação = ρ de Spearman. As proficiências só aparecem com uma etapa e uma disciplina selecionadas.
- **Proposta a confirmar:** faixas de eficiência por quintil do percentil (bem abaixo, abaixo, próximo, acima e bem acima do esperado).
- **Correção (2026-10-30, antes de qualquer uso):** a medida "Gasto das redes avaliadas" contava também as linhas sem proficiência. No caso de Brasil, AI, MT, 2023, a mediana saía R$ 13.643, e o correto é R$ 13.526. A medida passou a filtrar as redes com nota, como no HTML.
- **Pares no Power BI:** o município de referência é escolhido numa tabela à parte, sem relação com o modelo (`ref_municipio`), e a medida `É par` marca as redes do mesmo cluster com gasto entre 0,8 e 1,25 vez o dele. Essa faixa é uma escolha de apresentação, a mesma ideia da aba Pares do HTML.
- **Roteiro de construção (`powerbi/roteiro_construcao.md`):** 7 fases, cada uma com uma conferência. A principal compara as medidas com valores calculados em Python a partir das mesmas tabelas (Brasil AI e AF, AL e Ibateguara-AL).
- **Modelo gerado por script (Henrique, 2026-10-30):** o dashboard é um projeto `.pbip`, e não um `.pbix`. O modelo semântico (tabelas, parâmetro, relações, ordenações, formatos e medidas) é escrito em TMDL por `src/Visualizacao/Gerar_Modelo_PowerBI.py`; as páginas são feitas no Power BI.
  - **Divisão do trabalho:** o Power BI cria o projeto em branco e escreve o relatório, cujo formato é mais sensível. O script só escreve o modelo, que tem sintaxe documentada.
  - **Conferência antes de gravar:** o script confere que toda coluna e toda medida citadas nas fórmulas existem, que as ordenações são 1:1 e que o lado "um" das relações tem chave única. Um teste com uma coluna e uma medida inventadas confirmou que os dois erros são pegos.
  - **Limitação:** o modelo gerado não pôde ser aberto no Power BI durante o desenvolvimento. A primeira abertura é o teste real.
  - **Depois da criação, o Power BI é a fonte:** o script recusa sobrescrever um modelo com tabelas, salvo com `--forcar`. Cache e preferências locais ficam fora do Git.
  - **Feito à mão:** o parâmetro de campo do mapa e o tema.
- **Primeira abertura (2026-10-30):** o modelo gerado abriu no Power BI e carregou as 13 tabelas com o número de linhas esperado. Ao salvar, o Power BI só reformatou os arquivos (indentação e ordem de propriedades).
- **Conferência 2 (`powerbi/conferencia_modelo.dax`):** bateram com o Python:
  - redes avaliadas, proficiência média, % acima do esperado, eficiência média (zero), IDEB médio e saltos (Brasil AI e AF);
  - os 8 ρ de Spearman e os respectivos números de redes;
  - Alagoas, o gasto anual de 2023 e a série de Ibateguara-AL, inclusive a marca de salto em 2021 e a falta de eficiência em 2025.
- **Erro encontrado e corrigido:** o gasto mediano das redes avaliadas saía R$ 13.524,86, e não R$ 13.525,81 (AI), e R$ 12.536 em vez de R$ 12.540 (AF).
  - **Causa:** no `MEDIANX`, as 3 redes com nota e sem gasto entravam como zero, em vez de serem ignoradas. Recalculado em Python com os vazios como zero, o valor é idêntico ao do Power BI.
  - **Correção:** a medida passou a tirar as redes sem gasto antes da mediana. Corrigida no Power BI e conferida de novo: R$ 13.525,81 (AI) e R$ 12.539,72 (AF), iguais ao Python. **Conferência 2 concluída.**

### P5. Dashboard como ferramenta de análise ✅ (2026-10-27)
- **Decisão (Henrique, 2026-10-27):** usar o dashboard HTML como ferramenta de exploração para a análise, ampliado em abas. O Power BI fica para a apresentação final, alimentado pelas mesmas tabelas.
- **Abas:**
  - **Visão geral:** indicadores, dispersão gasto × nota, evolução, ranking por UF, cobertura e tabela.
  - **Defasagens:** gasto do mesmo ano e de 1, 2 e 4 anos antes × nota, com a correlação de Spearman (ρ) por edição e defasagem.
  - **Porte, região e contexto:** mapa de calor da nota média por grupo e quintil de gasto, e resumo por grupo.
  - **Ficha:** série anual de gasto e notas de um município ou UF, comparada com os pares e com o Brasil.
  - **Pares (exploratória):** gasto e nota de cada município em relação à mediana do seu grupo de contexto.
  - **Mapa (2026-10-27):** municípios coloridos por gasto, desempenho, nota em relação aos pares ou gasto em relação aos pares. Na camada estadual, cada município recebe o valor da sua UF. Há zoom pela UF em destaque, e o clique abre a ficha.
- **Escolhas do mapa (descritivas):**
  - gasto e desempenho em 7 faixas com o mesmo número de unidades, por quantis nacionais (na camada estadual, quantis das 27 UFs), para comparar regiões com a mesma régua;
  - as variáveis relativas aos pares usam escala divergente simétrica em torno do neutro (0 para nota, 1 para gasto, este em escala logarítmica), com cinza perto da mediana do grupo;
  - "sem dado" aparece hachurado;
  - o gasto do mapa é o do ano da edição selecionada, para todos os municípios com rede, mesmo sem nota.
- **Escolhas descritivas, que não alteram nenhum resultado:**
  - correlação de **Spearman**, que não é puxada por valores extremos;
  - quintis de gasto calculados dentro da edição e do recorte selecionados;
  - células do mapa de calor com menos de 10 municípios ficam em branco.
- **Pares, uma prévia do A6:** porte × faixa de alfabetização, o que dá 21 grupos. Gasto relativo = gasto ÷ mediana do grupo; nota relativa = nota − mediana do grupo. **Ainda não é o indicador de eficiência final**, que depende do desenho validado com a orientadora e do modelo.
- **Primeiros sinais vistos na ferramenta (descritivos, a confirmar na análise):**
  - nos Anos Finais de 2023, o ρ entre gasto e nota de Matemática sobe com a defasagem (0,17 no mesmo ano, 0,24 com 2 anos e 0,27 com 4 anos);
  - em Anos Iniciais 2023, dentro de cada porte, a nota média sobe do quintil de menor gasto para o de maior gasto;
  - quase todos os municípios do Ceará ficam acima da mediana de nota dos seus pares.

---

## 8. Problemas técnicos do pipeline

### T1. Script que gerou `siope_funcao_*` ✅ (reescrito em 2026-10-21)
- **Problema:** os arquivos `siope_funcao_{2017..2025}_extraido.parquet` são a base do numerador municipal, mas o script que os produziu não estava no repositório. Sem ele, não era possível reproduzir a extração nem auditar como as colunas `COD_SUBF` e `EH_TOTAL` foram derivadas.
- **Regras recuperadas a partir dos dados**, sem nenhuma divergência em ~469 mil linhas:
  - `COD_SUBF` é a primeira sequência de 3 dígitos do rótulo `DES_SUBF`. Rótulos sem código ficam nulos, como "98 - Contribuição Social do Salário-Educação".
  - `EH_TOTAL` é verdadeiro quando o rótulo começa com "TOTAL". Na prática, só aparece "TOTAL 365 - Educação Infantil".
- **Decisão:** reescrever o extrator como `src/Extract/Extract_SIOPE_Funcao.py`. Ele usa a entidade `Despesas_Funcao_Educacao_Siope`, o 6º bimestre e as 27 UFs, e mantém as camadas Municipal e Estadual.
- **Verificação:** a nova extração reproduz exatamente os parquets atuais nos 9 anos: mesmo número de linhas, mesmo schema, nenhuma linha só de um lado e nenhum valor empenhado, liquidado ou pago diferente. O total municipal da 361 é idêntico ano a ano (94,9 bi em 2017; 223,1 bi em 2025).

### T2. Brutos fora do repositório ✅ (contornado)
- **Situação:** os brutos (~35 GB) estão em `ENEM_Microdata_Analysis/data/raw`. Neste repositório, só a pasta do IDEB foi copiada.
- **Consequência:** os Transforms leem `data/interim` e funcionam. Para rodar de novo os outros Extracts, é preciso copiar a pasta bruta correspondente.
- **Decisão sobre o Git:** `data/raw` e `data/interim` ficam fora do Git (`.gitignore` na raiz, commit `e3153de`). Os painéis em `data/processed` são versionados (decisão de 2026-10-22). São pequenos (~2,4 MB), e assim podem ser abertos no Power BI sem rodar o pipeline.

### T4. Script que gerou `censo_escolar_transformado` ✅ (recriado em 2026-10-22)
- **Problema:** nenhum script do repositório gerava a base de infraestrutura. O `Transform_Censo_Escolar.py` só faz diagnóstico do dicionário de variáveis. Além disso, a base tinha uma linha duplicada: Uruguaiana-RS 2025, por causa da escola sem UF (M4).
- **Regra recuperada:** número de escolas e média dos indicadores `IN_*` por município × rede × ano. Os nulos ficam fora da média; cerca de 150 mil registros escola/ano têm todos os indicadores nulos.
- **Verificação:** a regra reproduz o arquivo antigo em todas as 168.759 linhas, exceto as 2 duplicadas.
- **Decisão:** novo script `src/Transform/Transform_Infraestrutura.py`, com a UF derivada do código do município. A saída tem 168.758 linhas, com chave única.

### T3. Scripts obsoletos ✅
- `Extract_IDEB.py` foi substituído pelo `Extract_SAEB.py`. Ele procura `data/raw` dentro de `src/Extract`, então não roda.
- `Transform_IDEB.py` e `ideb_transformado` se referem só ao Ensino Médio da fase ENEM.
- Nenhum dos três deve entrar no merge.
- **2026-10-22:** esses scripts e os da fase ENEM (`Extract_ENEM.py`, `Diagnostico_ENEM.py`) foram movidos para `src/Legado/`. O `Transform_Censo_Escolar.py`, que só fazia diagnóstico, virou `src/Testes/Diagnostico_Censo_Escolar.py`.

### T5. Reprodutibilidade ✅ (2026-10-22)
- **`run_pipeline.py` na raiz:** executa os scripts na ordem certa e para no primeiro erro.
  - Sem argumentos, faz o tratamento, os painéis e o dashboard.
  - Com `--com-extracao`, inclui a extração, depois de conferir se os brutos estão em `data/raw`.
  - Força saída em UTF-8, para os acentos não quebrarem o console do Windows.
- **Teste:** a execução completa do tratamento recriou os dois painéis idênticos aos versionados (comparação quadro a quadro).
- **`requirements.txt`:** versões usadas no desenvolvimento.
- **Limpeza do repositório:**
  - o `.gitattributes` saiu da pasta `git/` para a raiz, onde o Git o aplica;
  - o `__pycache__` saiu do índice;
  - `.claude/` (configuração local) entrou no `.gitignore`.
- **Pendente:** os brutos continuam só na máquina do Henrique (T2). O README documenta a organização esperada em `data/raw/`.
- **Pacote de exportação (2026-10-23):** o repositório no GitHub é privado, e os painéis em Parquet e os documentos em Markdown não abrem bem para quem não programa. Por isso, `src/Exportacao/Gerar_Pacote_Exportacao.py` gera um ZIP com:
  - o dashboard;
  - os documentos em HTML;
  - os painéis em Excel, com a aba "Dicionário", e em CSV;
  - o código.

  O Excel foi conferido contra os Parquet (mesmas linhas, colunas e somas).

### T6. Ambiente Python da máquina do Henrique ⚠️ (achado de 2026-10-30)
- **Situação:** há um polars 2.1.0 e um pyarrow 26.0 na pasta de pacotes do usuário (`AppData\Roaming\Python\Python312`), instalados em 2026-10-30 fora deste trabalho. Essa pasta tem prioridade sobre o Anaconda, que tem o polars 1.44.2 do `requirements.txt`. Além disso, o comando `python` do terminal aponta para o Python da Microsoft Store, e não para o Anaconda.
- **Efeito:** o pyarrow 26 exige NumPy 2, e o Anaconda tem NumPy 1.26. Qualquer conversão para pandas falha.
- **Contorno:** o código ficou livre de pandas (a matriz do modelo em `Eficiencia.py` é montada em NumPy). As tabelas foram conferidas e saíram iguais. Os scripts devem ser rodados com o Python do Anaconda (`%USERPROFILE%\anaconda3\python.exe`).
- **Pendente:** decidir se o pacote da pasta do usuário fica (e o `requirements.txt` sobe para o polars 2.1) ou sai. Rodar com `python -s` ignora essa pasta.

---

## 9. Reuniões com a orientadora

### Reunião de 2026-10-23
Anotações do Henrique, registradas como vieram:

| Ponto | Decisão ou pedido | Onde está registrado |
|---|---|---|
| Análise de clusters | Incluir uma análise de clusters | A6 (desenho a validar) |
| Outliers | Não é preciso remover | A5 ✅ |
| Gasto anual ou bianual | Entender a periodicidade | G12 (é anual; média do biênio como sensibilidade) |
| IDHM | Usar o IDHM do ano respectivo, sem t−1; 2025 é uma limitação, desde que documentada | C1 ✅, L4 |
| IDHM e educação | Entender se o IDHM impacta ou é impactado pela educação | C1b (proposta: IDHM Renda) |
| Acesso ao projeto | Ao final, uma forma simples de acesso, como QR Code | A7 |
| Registro | Manter anotada toda e qualquer decisão e limitação | Este documento e a seção 10 |

### Decisões de 2026-10-30 (Henrique, com base nas reuniões já feitas)
| Item | Decisão |
|---|---|
| A6 Clusters | Desenvolver; desenho de trabalho = agrupar por contexto e comparar gasto e nota dentro dos grupos |
| S9 Medida principal | Proficiências em pontos (Matemática e Português); nota N do Inep só como secundária (S10) |
| C1b IDHM | Excluir os índices de escolaridade (IDHM Educação e IDHM total); usar IDHM Renda e Longevidade |
| G4 Ensino Superior | Versão A (ausência = nada a descontar) |
| E3 Recorte | Brasil inteiro, ferramenta nacional, mesma perspectiva para todos os estados |
| E4/D3 Usuário-alvo | Agente de secretaria de educação ou analista da educação pública |
| Power BI | Instalado e funcionando na máquina do Henrique |

### Pendências restantes (nenhuma bloqueia o desenvolvimento)
0. **S11 (2026-10-30):** confirmar a regra proposta para marcar os saltos atípicos (mais de 3 desvios-padrão da variação média; 633 linhas marcadas, nenhuma excluída). (A8 foi decidido: versão nacional.)
1. **S8 e S4:** as propostas (não imputar notas, controlar o porte, painel balanceado; Anos Finais como complementar) seguem como padrão de trabalho, sem objeção registrada.
2. **A4 e P3:** lista de testes de sensibilidade; extensão das matrículas para 2015–2016 é opcional.
3. **D1:** formato do TCC (científico ou consultoria). Afeta o texto, não o dashboard.
4. **D2:** indicadores formais. Proposta escrita em 2026-10-30 (12 indicadores, seção 4 de `powerbi/especificacao_dashboard.md`), com as faixas de eficiência por quintil; falta confirmar.
5. **D4:** referências e APA; **D5/IA:** forma de documentar o uso de IA no Método.
6. **A7:** endereço público para o QR Code (Power BI Service com "Publicar na Web", ou o HTML), a verificar na publicação.

### Dossiê da conta anterior (incorporado em 2026-10-26)
O dossiê das conversas anteriores (arquivos 01 a 05, guardados em `docs/historico/`) foi comparado com o estado atual. Os achados de dados entraram nos itens G4, G5, M2, S8 e E2 e nas limitações L13 e L14. Abaixo ficam as pendências que só apareciam no dossiê.

- **D1. Formato do TCC 🟡 (Manual lido em 2026-10-30):** o projeto vem sendo chamado de consultoria, mas pelo Manual o enquadramento mais natural é **método científico, estudo quantitativo**. A decisão é da dupla com a orientadora. O que o Manual de TCC ADM 2025 (Depto. de Administração, FEA/USP, atualizado em abril de 2025) diz:
  - **Formatos (4.2):**
    - **Método científico, com estudos quantitativos** (longitudinais, multivariados, levantamentos populacionais): o objetivo é "de descobrimento" e busca diminuir uma lacuna de conhecimento, não alterar a realidade. É o caso de "o gasto se associa ao desempenho? com que defasagem?".
    - **Consultoria:** é um plano para uma organização (objetivo gerencial, que altera a realidade administrativa, com diagnóstico da empresa e plano de ação) ou um relato técnico de uma situação-problema numa organização específica. Exige acesso a uma organização. Hoje não temos uma organização-cliente; o produto serve a qualquer secretaria.
    - **Empreendedor:** plano de negócio para uma nova organização. Não se aplica.
  - **Conteúdo mínimo, método científico (4.4):**
    - **TCC I:** Introdução (questão de pesquisa, objetivos, contexto), Revisão bibliográfica, Método (definido, justificado e planejado, com coleta e análise), Cronograma do TCC II e Referências.
    - **TCC II:** o TCC I revisado, mais Resultados, Análise e discussão, e Conclusões, limitações e sugestões de pesquisa futura.
  - **Avaliação (5.2 e 5.3):**
    - **TCC II:** 80% trabalho escrito, avaliado pelo orientador e por um 2º professor (um 3º entra se a diferença passar de 2 pontos), e 20% vídeo.
    - **Vídeo:** de cerca de 5 minutos, no máximo 7. Cada integrante grava o seu, com o rosto numa janela menor e os slides na maior. O link do YouTube vai no 1º slide, e o PPT nomeado com os nomes completos é postado no Moodle.
    - **Rubrica do método científico:** pesa fundamentação teórica (autores relevantes e atuais), referências de artigos nacionais e internacionais, método compatível com os objetivos e detalhado com citação de autores, profundidade da análise conectada à teoria, e conclusões coerentes com as evidências.
  - **Formatação:** diretriz USP para teses e dissertações, com **APA obrigatório a partir de 2026**. Recomenda-se submeter ao Turnitin (pela Biblioteca da FEA) e enviar o relatório ao orientador. Plágio dá nota zero.
  - **IA (item 2.3, p. 9):** qualquer uso de IA deve ser **informado e discutido previamente com o orientador**, que decide se será permitido. O uso não autorizado pode levar à reprovação, como o plágio.
  - **Pesquisa com seres humanos (4.2 e Apêndices 6 a 8):** trabalhos com método científico que envolvem pessoas podem precisar de aprovação de comitê de ética. Há modelos de Termo de Consentimento (TCLE). **Isso afeta a etapa de "Avaliação com usuários" do fluxo:** entrevistar ou aplicar questionário a gestores exige TCLE e deve ser alinhado com a orientadora.
  - **Outros pontos:** dupla é permitida (até 3 alunos); mínimo de 2 reuniões com o orientador por semestre; prazos sem exceção. O Prêmio Ruy Leme exige uma versão em formato de artigo do SemeAd.
- **D2. Os pontos do e-mail de 02/10 ainda sem resposta depois do pivô 🟡:** a orientadora pediu um documento de 3 a 5 páginas com nove pontos. O documento entregue (`Delimitacao_TCC_Reuniao.docx`) era anterior ao pivô. Falta responder, nos termos do projeto atual:
  - **pergunta de pesquisa;**
  - **perguntas analíticas:** de 5 a 8. Há 6 em rascunho no arquivo 01: associação gasto × nota com defasagem; efeito dentro do município; quem está acima ou abaixo do esperado; camada estadual; heterogeneidade por porte e região; robustez à fonte e a 2021;
  - **indicadores formais:** nome, fórmula, unidade, variáveis e interpretação de cada um (por exemplo, gasto por aluno real, nota padronizada N, resíduo de eficiência);
  - **unidade de análise e chaves de integração:** já definidas (município na camada municipal, UF na estadual; chave de 7 dígitos, UF, rede e ano). Falta só escrevê-las no formato pedido.
- **D3. Usuário-alvo ✅ (2026-10-30):** decidido em E4: agente de secretaria de educação ou analista da educação pública, de qualquer estado ou município.
- **D4. Referências 🟡:** vários itens da bibliografia do documento original (por exemplo, Benjamin e Kim 2018, Dehghan et al. 2020 e Franco et al. 2015) nunca foram verificados. Confirmar a existência de cada um antes de citar. O formato APA é obrigatório a partir de 2026. A série de Leonardo Sales no Medium sobre o ENEM entra como literatura cinzenta.
- **D5. Roteiro para o registro do uso de IA:**
  - quais ferramentas foram usadas e para quê: apoio na escrita do código de extração e tratamento, revisão de achados e estruturação de documentos;
  - o que a IA não fez: não definiu sozinha a pergunta de pesquisa nem as decisões de escopo, e os resultados foram conferidos pelos autores com as saídas reais dos scripts;
  - onde o uso aparece no TCC (Método ou nota metodológica), conforme a orientadora aprovar;
  - qualquer redação de trechos do TCC com apoio de IA precisa ser alinhada antes com a orientadora.

---

## 10. Limitações (para a seção de Método)

Lista consolidada, conforme o pedido da orientadora de manter anotada toda limitação. Cada item remete à decisão que o originou.

- **L1. Fonte do gasto [G1–G3]:** o nível do gasto depende da fonte. O SIOPE e o SICONFI divergem para o mesmo ente, sobretudo nas capitais. Cada camada usa uma única fonte.
- **L2. Composição do gasto estadual [G4, G4b]:** a linha do Ensino Superior falta para alguns estados e anos e, nesses casos, nada é descontado (versão A). Se no RS (2018–2023) o Ensino Superior estiver em outra subfunção, o gasto da educação básica fica superestimado. Além disso, o total da função 12 inclui despesas fora das subfunções detalhadas (provavelmente inativos).
- **L3. Seleção da amostra [S4, S8]:** só entram as redes com nota divulgada pelo Inep. As redes pequenas, que gastam mais por aluno, ficam sub-representadas, sobretudo em Anos Finais e em 2021.
- **L4. IDHM [C1, C1b]:** o IDHM só existe por UF, não por município, e a série termina em 2024. Por isso, a edição de 2025 não tem esse controle. Para evitar circularidade com o desempenho, a análise usa só as dimensões Renda e Longevidade, e deixa de fora a Educação e o índice total.
- **L15. Medida de desempenho [S9, S10]:** a análise usa a proficiência média da rede (Matemática e Português, em pontos), e não o desempenho de cada aluno. A nota padronizada N, usada só como medida secundária, satura nos limites fixados em 1997 e não é comparável entre etapas.
- **L16. Clusters [A6]:** a separação entre os grupos é fraca (silhueta de cerca de 0,23). Os grupos são uma partição útil para formar pares, e não tipos naturalmente distintos. Eles saem ligados à região, porque o IDHM só existe por UF.
- **L17. Indicador de eficiência [A8]:** é o resíduo de um modelo de associação. Ele reflete tudo o que o modelo não mede (gestão, contexto familiar, qualidade do registro), e não só eficiência no uso do gasto. O indicador oficial (versão nacional) não cobre a edição de 2025.
- **L18. Saltos atípicos de proficiência [S11]:** algumas redes, sobretudo no Ceará e em Alagoas, têm crescimentos de proficiência muito acima do usual. Se não forem reais, inflam o indicador de eficiência desses municípios.
- **L5. Pandemia [S5]:** a edição de 2021 tem menos resultados com nota e condições atípicas de aplicação.
- **L6. Matrículas de 2025 [M3]:** as matrículas estaduais caem cerca de 5% em 2025, e não se sabe se é efeito real ou da mudança de layout do Censo Escolar.
- **L7. Valores extremos [A5, G11]:** cerca de 0,7% dos municípios com nota têm gasto por aluno implausível (provável erro de registro ou rede muito pequena). Eles ficam na análise, conforme a decisão da orientadora.
- **L8. Camada estadual [A2]:** são só 27 unidades, o que limita a precisão das estimativas e o uso de clusters.
- **L9. Defasagens [E2, P2]:** com o gasto desde 2017, a defasagem de 2 anos só existe a partir do Saeb 2019, e a de 4 anos a partir de 2021.
- **L10. Alfabetização estática [C2]:** vem do Censo 2022 e não varia no tempo. Um município instalado depois de 2022 fica sem esse controle.
- **L11. Restos a pagar [G7]:** a despesa paga não inclui os restos a pagar inscritos no ano.
- **L12. Associação, não causalidade [A1]:** os resultados descrevem associação e eficiência relativa, não efeito causal do gasto. A relação pode até se inverter, por exemplo se o FUNDEB e a complementação da União direcionam mais recursos às redes com pior desempenho.
- **L13. Mesmo numerador para duas etapas [G5]:** a subfunção 361 cobre todo o Ensino Fundamental e não separa Anos Iniciais de Anos Finais. O mesmo gasto por aluno serve aos dois desfechos da camada municipal.
- **L14. Gasto municipal só no Fundamental [G5]:** a Educação Infantil (subfunção 365) pesa quase tanto quanto o Fundamental no gasto municipal (SP 2023: R$ 30,1 bi contra R$ 32,2 bi, segundo o dossiê) e fica fora do numerador, porque o Saeb não a avalia. O gasto em educação do município é, portanto, bem maior do que o gasto usado.
