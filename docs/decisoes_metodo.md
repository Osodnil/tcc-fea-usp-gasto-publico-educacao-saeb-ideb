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
- **Painel (2026-11-09):** só a versão A aparece. A comparação com a B fica para o texto, como robustez (ver P7).
- **Decisão (Henrique, 2026-10-30):** usar a **versão A**: a ausência da linha 12.364 é tratada como "nada a descontar", para não deixar UF/anos sem informação. A versão B continua calculada nos painéis, só para teste de sensibilidade. O dashboard oficial usa a A.
- **Como as versões diferem na prática (conferido em 2026-11-09):** onde a linha 12.364 existe, A e B são iguais. A versão B só deixa vazios os pares UF/ano sem a linha (em 2023, AC, RO, RS e SE). Logo, a sensibilidade à versão B é uma sensibilidade à **amostra**, e não ao valor do gasto de cada UF.
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

### A4. Testes de sensibilidade ✅ (rodados em 2026-11-11; G4b não feito)
1. Sem 2021 (S5).
2. Sem 2025 na camada estadual (M3).
3. IDHM Renda no lugar do IDHM total, e vice-versa (C1b).
4. Tratamento alternativo da 12.364 (G4) e gasto estadual pela soma das subfunções da educação básica (G4b).
5. Painel balanceado: só municípios com nota nas cinco edições (S8).
6. Gasto médio do biênio (ano do Saeb e ano anterior) no lugar do gasto anual (G12).

*(Revisão de 2026-10-23: saiu o teste "com e sem os gastos extremos", porque a orientadora decidiu não removê-los (A5). Saiu também o teste "IDHM do mesmo ano", porque ele passou a ser a especificação principal (C1).)*

- **Rodados em 2026-11-11 (`src/Analise/Sensibilidade_Modelo.py`; saída `data/interim/diagnosticos/sensibilidade_modelo.csv`)†.** Cada teste muda uma coisa na especificação de referência (A11 na camada municipal, A12 na estadual). Além da lista acima, entraram: o limite de 80% para a rede parcial (proposto na pauta para a orientadora), a exclusão das redes parciais (A9) e a dos saltos atípicos (S11).

  | Teste (camada municipal, gasto do mesmo ano) | AI MT | AI LP | AF MT | AF LP |
  |---|---|---|---|---|
  | Referência (2017–2025) | 2,34 | 1,98 | 2,73 | 2,00 |
  | Sem 2021 | 2,84 | 2,46 | 2,97 | 2,22 |
  | Painel balanceado (nota nas 5 edições) | 2,51 | 2,06 | 2,99 | 2,52 |
  | Referência em 2019–2025 | 2,33 | 2,00 | 3,20 | 2,49 |
  | Gasto médio do biênio (2019–2025) | 3,74 | 3,12 | 5,46 | 4,32 |
  | Sem redes parciais (< 50%) | 2,42 | 2,16 | 2,96 | 2,21 |
  | Sem redes abaixo de 80% | 2,66 | 2,31 | 3,68 | 2,85 |
  | Sem saltos atípicos | 2,11 | 1,99 | 2,34 | 1,97 |
  | EF de município + edição, IDHM Renda e Longevidade (2017–2023) | 2,47 | 2,23 | 2,23 | 1,65 |
  | Idem, IDHM total | 1,85 | 1,65 | 1,74 | 1,41 |
  | Idem, sem IDHM | 2,81 | 2,48 | 2,40 | 1,78 |

  - **Leitura:** todos os coeficientes municipais são positivos e significativos (p ≤ 0,02), entre 1,4 e 5,5. A conclusão de A11 se sustenta: associação dentro do município positiva e pequena.
  - **Gasto médio do biênio:** o coeficiente sobe cerca de 60% em relação à referência na mesma janela (AI MT: 3,74 contra 2,33). Isso combina com o achado de A11 de que contam o gasto do ano da prova e o do anterior: a média dos dois mede melhor o gasto do ciclo (e tem menos ruído de um ano isolado).
  - **IDHM total:** reduz o coeficiente (AI MT: 1,85 contra 2,47), como esperado de um controle que contém a dimensão Educação (C1b); a escolha de Renda e Longevidade fica mantida.
  - **Camada estadual:** com 2025 (sem IDHM) e com a versão B do gasto, nenhum coeficiente se distingue de zero (p ≥ 0,18), como na referência (A12).
  - **Não feito:** o gasto estadual pela soma das subfunções da educação básica (G4b), que pede as subfunções brutas do SICONFI, fora dos dados processados. A extensão das matrículas para 2015–2016 (P3) segue opcional.

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

### A9. Rede municipal parcial: quando a prefeitura não atende todos os alunos da etapa ✅ (2026-11-09)
- **Origem:** reunião de 2026-11-06. Os Anos Iniciais são responsabilidade das prefeituras, mas há exceções que os dados de nota sozinhos não mostram.
- **Medida:** `PART_MUN` = matrículas da etapa na rede municipal ÷ (municipal + estadual), por município, etapa e ano, a partir do Censo Escolar (tabela `fato_oferta_municipal`). "Rede parcial" é a rede com nota e `PART_MUN` < 50%.
- **Tamanho, entre as redes com nota†:**
  - **Anos Iniciais:** 140 de 5.243 em 2023 (2,7%), e de 2,5% a 4,4% conforme a edição. As UFs com mais redes parciais são RR (23%), AC (14%), RS (12%), SC (7%) e MG (6%).
  - **Anos Finais:** 525 de 3.196 em 2023 (16%), e de 16% a 22% conforme a edição. As UFs com mais são GO (54%) e MG (45%).
  - **Contagem anterior:** a de 266 municípios em AI incluía os municípios sem nota.
- **Sensibilidade** (`src/Analise/Sensibilidade_Rede_Municipal.py`; saídas `diagnosticos/sensibilidade_rede_municipal_*.csv`):
  - **Coeficiente do gasto:** quase não muda. AI MT, modelo nacional: +0,92 (p = 0,20) com todas as redes e +1,13 (p = 0,12) sem as parciais. Modelo no próprio estado: +4,33 e +4,40. Em AF, sobe um pouco (AF MT nacional: +1,57 → +2,06, p = 0,06), e continua não significativo a 5% no modelo nacional.
  - **Ordenação das redes que ficam:** praticamente a mesma. A correlação entre as eficiências com e sem as parciais é de 0,998 em AI e 0,995 em AF. Mudam de quintil 6% das redes em AI e 9% a 11% em AF.
  - **ρ de Spearman gasto × nota:** igual, com diferença menor que 0,02 em todas as edições.
  - **Achado:** as redes parciais têm eficiência média bem menor que as demais. Em 2023, na comparação nacional, AI MT fica em −13,5 contra +0,4; AF MT, em −3,5 contra +0,7. Uma hipótese é que a rede municipal, nesses casos, atenda as escolas de áreas mais vulneráveis, mas **isso não foi verificado**.
- **Decisão:** manter as redes parciais na análise (as conclusões agregadas não mudam) e **marcá-las** no painel. A marca aparece:
  - na coluna "Rede atende" do ranking de Eficiência, com ⚠ abaixo de 50%;
  - na dica do Mapa;
  - no cartão "Situação da rede" da Ficha, que avisa que a eficiência é a da rede municipal, não a da cidade.
- **No texto:** citar a sensibilidade como robustez e a limitação L19.

### A10. Eficiência em % do esperado como medida principal do painel ✅ (Henrique, 2026-11-09)
- **Origem:** reunião de 2026-11-06. Em pontos, a escala muda entre etapas: o esperado gira em torno de 220 em Anos Iniciais e de 249 em Anos Finais.
- **Definição:** eficiência = (proficiência − esperada) ÷ esperada, rede a rede (colunas `EFIC_PCT` e `EFIC_PCT_ALT`). No agregado, é a média entre as redes.
- **O que fica como referência:** os pontos e o percentil continuam no painel, em colunas e dicas.
- **Limite:** a escala do Saeb não tem zero verdadeiro, então o % é uma convenção de leitura, e não uma razão no sentido estrito. O percentil é a alternativa mais robusta.
- **O que não muda:** o sinal (acima ou abaixo do esperado), o "% acima do esperado" e os modelos. A ordem das redes muda pouco, porque o esperado varia de ~180 a ~260.
- **Ordem de grandeza (AI MT 2023):**
  - **intervalo:** 90% das redes ficam entre −13,8% e +16,1% na comparação nacional, e entre −12,1% e +13,8% no mesmo estado;
  - **exemplos:** Campinas −10,5%; São Paulo −9,3%; Ibateguara +71,1%.
- **Mapa:** passou a comparar cada rede com as do mesmo estado (a "mesma régua" pedida na reunião). A escala de cor fica saturada em ±12%, que cobre de 88% a 96% das redes. Os cartões do Mapa seguem a mesma comparação. O resumo por UF fica na comparação nacional, porque na comparação dentro do estado a média de cada UF é zero no período (efeito fixo de UF). Depois, o mapa ganhou a opção nacional, com o mesmo estado como padrão (ver P7).
- **Exemplo do Ceará (2023):** na comparação nacional, 90% das redes ficam acima do esperado (média de +16,1%); no mesmo estado, 45% (+1,7%).
- **Rótulo "vs. esperado" e escala centrada em 0% (Henrique, 2026-11-09):**
  - **Pergunta:** escrito ao lado da palavra "Eficiência", o 0% (rede que entregou exatamente o esperado) podia ser lido como ineficiência total. A alternativa seria a razão proficiência ÷ esperada, com o esperado valendo 100%.
  - **Por que a razão não foi adotada:**
    - nos métodos de fronteira (DEA), 100% quer dizer "eficiente", o melhor possível: uma rede mediana pareceria ótima, e 105% pareceria "acima do máximo";
    - a escala do Saeb não tem zero verdadeiro: "entregou 89,5% do esperado" (Campinas) sugere uma proporção de aprendizagem que não existe.
  - **Decisão:** manter a distância até o esperado, centrada em 0%, e trocar o rótulo dos valores. Colunas, cartões, eixos e dicas passam de "Eficiência" para "vs. esperado"; os cartões de média, para "Média vs. esperado". O nome do indicador e das páginas continua "eficiência".
  - **Explicação nos glossários (Henrique pediu menos ambiguidade, 2026-11-09):** "nota acima (+) ou abaixo (−) da esperada, em %; 0% = igual a ela", com a linha "Pontos: a mesma diferença, em pontos do Saeb" à parte. Sobre os dados traz a versão longa, com o exemplo "+5% = 5% acima".
  - **Sinal do zero:** as medidas passaram a ser arredondadas na precisão exibida (0,1% e 0,1 ponto). Antes, Abadia de Goiás (AI, MT, 2023: −0,007 ponto, −0,003%) aparecia como "−0,0%"; agora aparece como "0,0%".
  - **No texto do TCC:** explicar por que o painel não usa a escala em que o esperado vale 100%.

### A11. Modelo principal da camada municipal ✅ (implementado e com especificação de referência decidida em 2026-11-10)
- **Pergunta (perguntas analíticas 1 e 2):** o gasto por aluno se associa à proficiência? E, dentro do mesmo município, aumentos de gasto acompanham melhora da nota?
- **Especificação (proposta da IA, aceita por Henrique ao aprovar o plano da fase de análise):**
  - proficiência = b·log(gasto por aluno, R$ de 2025) + controles + efeitos de edição [+ efeito fixo de município]; erros-padrão agrupados por município (A2); gastos extremos mantidos (A5);
  - por etapa (AI principal, AF complementar), disciplina (MT, LP) e defasagem do gasto (0, 1, 2 e 4 anos);
  - **MQO agrupado:** com os controles fixos (log da população e alfabetização) e os que variam no tempo (infraestrutura, log das matrículas, IDHM Renda e Longevidade da UF), edições 2017–2023. É a mesma especificação da eficiência (conferido: coeficiente, N e R² iguais aos de `eficiencia_coeficientes.csv`);
  - **EF de município:** com efeito fixo de município, que absorve os controles fixos no tempo; 2017–2023;
  - **EF de município, com 2025:** sem o IDHM, que não existe em 2025 (C1); 2017–2025.
  - **Implementação:** `src/Analise/Modelo_Principal.py`, sem pacotes novos: efeito fixo pela transformação "dentro" (como o `xtreg, fe vce(cluster)` do Stata), sem os municípios com uma só observação. Saídas em `data/interim/diagnosticos/modelo_principal_coeficientes.csv` e `modelo_principal_defasagens_mesma_amostra.csv`.
- **Resultados (AI, Matemática, gasto do mesmo ano)†:**

  | Especificação | b (EP) | +10% no gasto | N |
  |---|---|---|---|
  | MQO agrupado (entre e dentro) | 0,92 (0,72), p = 0,20 | +0,09 ponto | 20.315 |
  | EF de município, 2017–2023 | 2,47 (0,50), p < 0,001 | +0,24 ponto (0,01 DP) | 20.256 |
  | EF de município, 2017–2025 | 5,06 (0,47), p < 0,001 | +0,48 ponto (0,02 DP) | 25.591 |

  - **Leitura:** com os controles de contexto, as diferenças de gasto **entre** municípios quase não se associam à nota. **Dentro** do mesmo município, a associação é positiva e estatisticamente clara, mas pequena: dobrar o gasto por aluno se associa a cerca de 1,7 ponto a mais (2017–2023), quando um ano de escola vale cerca de 25 pontos na escala do Saeb. Português e Anos Finais seguem o mesmo padrão (EF, mesmo ano: AI LP 2,23; AF MT 2,23; AF LP 1,65).
  - **Por que 2025 dobra o coeficiente:** tirar o IDHM muda pouco (2,48 → 2,81, mesma amostra); somar 2025 leva a 5,05. Investigado em 2026-11-10 (`src/Analise/Investigar_2025.py`; saídas `investigar_2025_testes.csv` e `investigar_2025_descricao.csv`)†:
    - **Primeiras diferenças por biênio (AI MT):** 1,63 (2017→19), 4,28 (2019→21), 0,87 (2021→23, não significativo) e 3,99 (2023→25). O biênio de 2023→25 não é o único alto: o da pandemia também é. A inclinação varia muito entre biênios.
    - **O que explica 2023→25: mudanças comuns ao estado.** Com efeito de UF, o coeficiente cai pela metade (3,99 → 1,96). Os municípios do Nordeste e do Norte tiveram ao mesmo tempo o gasto que mais subiu (+23% e +19%, contra +7% no Sudeste) e as notas que mais subiram (+12,1 e +13,6 pontos, contra +7,4).
    - **Não é convergência:** controlar a nota e o gasto de 2023 não reduz o coeficiente (5,38). O gasto subiu muito mais nas redes que gastavam menos (+31% no quintil mais baixo de 2023, −1% no mais alto), mas a nota subiu quase igual em todos os quintis (de +8,8 a +10,8 pontos em MT).
    - **Compatível com o novo Fundeb, sem prova:** a complementação VAAT vai para redes de menor receita, concentradas no Nordeste e no Norte, o que combina com o padrão acima. Não há no painel dado de quem recebeu VAAT para testar.
    - **Efeito fixo de município com UF × edição, 2017–2025:** 2,34 (EP 0,43) em MT e 1,98 (0,40) em LP, praticamente iguais aos de 2017–2023 com IDHM (2,48 e 2,23). Com o efeito de UF × edição, a associação dentro do município fica estável, e 2025 deixa de puxar o resultado.
    - **Consequência para o IDHM:** como o IDHM é da UF e do ano, o efeito de UF × edição o absorve inteiro. Essa especificação dispensa o IDHM e, por isso, cobre 2025 sem violar a decisão C1.
  - **Decisão (Henrique, 2026-11-10): especificação de referência = efeito fixo de município com efeito de UF × edição, 2017–2025.** Ela compara municípios do mesmo estado na mesma edição, a mesma lógica da comparação "no mesmo estado" da eficiência (A8). A especificação com IDHM, 2017–2023, e o MQO agrupado ficam como comparação. No script, a coluna `REFERENCIA` marca essa especificação.
  - **Resultados na referência (gasto do mesmo ano)†:**

    | Etapa | Matemática | Português |
    |---|---|---|
    | AI | 2,34 (EP 0,43): +10% no gasto → +0,22 ponto | 1,98 (0,40): +0,19 ponto |
    | AF | 2,73: +0,26 ponto | 2,00: +0,19 ponto |

  - **Defasagens na referência, mesma amostra (2019–2025):** a associação vem do gasto do **ano da prova e do ano anterior**, os dois anos do ciclo bienal do Saeb. O gasto de 2 anos antes não se associa (AI MT: 2,26 no mesmo ano, 2,35 com 1 ano, 0,85 com 2 anos, p = 0,10; AI LP: 1,97, 1,83, 0,47). Na janela 2021–2025, o de 4 anos antes também não (AI MT: 0,10, p = 0,87). AF segue o mesmo padrão.
  - **Para o texto:** dentro do mesmo município e descontados os choques do estado, a associação é positiva e estável, mas pequena, e concentrada no gasto do próprio ciclo de avaliação. O ρ simples cresce com a defasagem porque o gasto antigo carrega diferenças persistentes entre municípios, que o efeito fixo retira.
  - **Defasagens na mesma amostra (EF):** em AI, a associação é mais forte com o gasto do **mesmo ano** e não cresce com a defasagem (MT, 2019–2023: 2,16 no mesmo ano; 0,99 com 1 ano; 1,85 com 2 anos. 2021–2025: 3,29; 2,74; 1,07; 0,97 com 4 anos). Em AF, o padrão é menos nítido (MT, 2019–2023: 1,51; 2,25; 2,08). É o contrário do ρ simples, que cresce com a defasagem (P7): lá, o gasto antigo carrega diferenças persistentes entre municípios, que o efeito fixo retira.
  - **Cuidado na comparação entre defasagens na tabela principal:** as defasagens de 1 e 2 anos só existem a partir de 2019, e a de 4 anos a partir de 2021 (só duas edições com IDHM). Por isso a comparação válida é a da mesma amostra.
- **Para o texto:** associação, não efeito causal (A1). O efeito fixo de município retira o que é fixo no município, mas não o que muda junto com o gasto (por exemplo, uma troca de gestão ou um programa novo).

### A12. Modelo da camada estadual ✅ (2026-11-10)
- **Pergunta (pergunta analítica 4):** o gasto estadual por aluno se associa à proficiência das redes estaduais (Anos Finais e Ensino Médio)?
- **Especificação (plano da fase de análise, aprovado por Henrique):** a mesma estrutura de A11, com a UF no lugar do município:
  - proficiência = b·log(gasto estadual por aluno, versão A, R$ de 2025) + controles + efeitos de edição [+ efeito fixo de UF]; defasagens de 0, 1, 2 e 4 anos;
  - **MQO agrupado**, 2017–2023 com IDHM; **EF de UF** (referência), 2017–2023 com IDHM; **EF de UF, com 2025**, sem IDHM (cautela com 2025: as matrículas estaduais caem 5,1%, M3);
  - o efeito de UF × edição, usado na camada municipal, não cabe aqui, porque absorveria toda a variação;
  - **poucos grupos:** erros-padrão agrupados por UF (27 grupos), com valores-p e intervalos pela t com 26 graus de liberdade;
  - `src/Analise/Modelo_Estadual.py`; saída `data/interim/diagnosticos/modelo_estadual_coeficientes.csv`. A versão B do gasto fica para os testes de sensibilidade (A4).
- **Resultados na referência (EF de UF, gasto do mesmo ano, 108 observações)†:**

  | Etapa | Matemática | Português |
  |---|---|---|
  | AF | 1,51 (IC 95%: −6,0 a 9,1), p = 0,68 | 1,06 (−6,4 a 8,5), p = 0,78 |
  | EM | 5,25 (−2,6 a 13,1), p = 0,18 | 2,47 (−5,2 a 10,1), p = 0,51 |

  Nenhuma defasagem nem especificação dá associação distinguível de zero, e os sinais variam.
- **Leitura:** com 27 UFs, a camada estadual não tem poder para detectar uma associação do tamanho da municipal (2 a 3 pontos por log do gasto): os intervalos vão de cerca de −6 a +9 pontos e incluem tanto zero quanto valores maiores que o municipal. O resultado é "não detectável", e não "ausência de associação". Isso confirma a decisão de tratar a camada estadual como descritiva no painel e reforça a limitação L8 sobre o número de unidades.

### A13. Heterogeneidade da associação dentro do município ✅ implementado · 🟡 interpretação (2026-11-11)
- **Pergunta (pergunta analítica 5):** a associação gasto × proficiência dentro do município muda por porte, região, cluster ou nível de gasto?
- **Método (plano da fase de análise, aprovado por Henrique):**
  - especificação de referência de A11 (efeito fixo de município e UF × edição, 2017–2025, gasto do mesmo ano), com uma inclinação do log do gasto por grupo e teste de Wald de igualdade entre as inclinações;
  - **dimensões**, todas fixas no município:
    - porte (faixas do painel, com as duas maiores juntas, porque têm poucas redes);
    - região;
    - cluster;
    - faixa de gasto: quintil do gasto médio de 2017–2025, acrescentada para a pergunta "gastar mais vale mais para quem gasta pouco?";
  - `src/Analise/Heterogeneidade.py`; saída `data/interim/diagnosticos/heterogeneidade_coeficientes.csv`.
- **Resultados (AI, Matemática; Português segue o mesmo padrão)†:** a igualdade das inclinações é rejeitada nas quatro dimensões (p ≤ 0,02).

  | Dimensão | Onde a associação é maior | Onde é nula ou negativa |
  |---|---|---|
  | Porte | até 50 mil habitantes: 2,4 a 3,0 | 50 a 100 mil: −0,5 (não signif.); mais de 100 mil: **−2,65** (p = 0,01) |
  | Região | Nordeste 4,3; Norte 3,6; Centro-Oeste 1,8 | Sudeste 1,1 e Sul 0,9 (não signif.) |
  | Cluster | 1 e 2 (Nordeste, pequenos e médios): 4,3 e 5,0 | 5 (Nordeste e Norte, grandes): −0,1; 7 (Sudeste, médios): **−3,2** (p < 0,001) |
  | Faixa de gasto médio | Q4 e Q5: 4,0 e 3,7 | Q1 (quem gasta menos): −1,1 (não signif.) |

- **Sem 2025 (2017–2023, efeito de UF × edição):** mesmo desenho, mais fraco. Porte: 1,4 a 2,1 até 50 mil e cerca de −1,0 acima (não signif.). Faixa de gasto: −1,5 em Q1 e 2,3 a 2,8 em Q4–Q5.
- **Cuidados de leitura:**
  - **As dimensões se sobrepõem:** o quintil de maior gasto por aluno é dominado por municípios de até 5 mil habitantes (614 dos 1.063 municípios de Q5), e os clusters seguem a região e o porte. O padrão por faixa de gasto pode ser, em boa parte, o do porte. Não há evidência de "retornos maiores para quem gasta pouco"; se algo, o contrário.
  - **A associação negativa nas cidades grandes não foi explicada.** Hipóteses, nenhuma testada: (a) o gasto da subfunção 361 nas cidades grandes mistura itens que não chegam à sala de aula (L1: a fonte diverge sobretudo nas capitais); (b) nessas redes, o gasto por aluno varia mais com a entrada e a saída de alunos do que com o investimento; (c) regressão à média.
  - **Comparações múltiplas:** são 4 dimensões e 2 disciplinas; os testes de igualdade passam com folga, mas os coeficientes de cada grupo não devem ser lidos isoladamente.
- **Para o texto:** a associação dentro do município está concentrada nos municípios pequenos e no Nordeste e Norte; nas cidades grandes e no Sudeste e Sul, não aparece. Associação, não efeito do gasto.

### A14. Material dos resultados para o texto ✅ (2026-11-11)
- **O que é:** tabelas e figuras dos modelos (A4, A11, A12, A13) e uma nota de resultados para a redação, que fecham o plano da fase de análise.
- **Onde:**
  - `docs/resultados/tabelas.md`: sete tabelas (amostra, ρ de Spearman, modelo principal, defasagens, heterogeneidade, sensibilidade, camada estadual), com coeficiente, erro-padrão agrupado e significância;
  - `docs/resultados/figuras/`: quatro figuras de coeficientes com intervalo de 95% (entre × dentro, defasagens, heterogeneidade, sensibilidade), em PNG para impressão;
  - `docs/nota_resultados.md`: o que cada pergunta analítica respondeu, com os números, o que dizer e o que não dizer, e a ordem para reproduzir.
- **Geração:** `src/Analise/Material_Texto.py`, a partir das saídas dos scripts de análise; as tabelas não devem ser editadas à mão.
- **Pendentes de interpretação, a levar à orientadora:** a associação negativa nas cidades com mais de 100 mil habitantes (A13) e a hipótese do Fundeb/VAAT para 2023→2025 (A11), nenhuma testada.

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
- **Requisito:** o QR Code precisa apontar para um endereço que a pessoa consiga abrir sem login.
- **Repositório público (Henrique, 2026-11-11):** o repositório no GitHub está público, para que a dupla o acesse. Os registros anteriores o tratavam como privado. Consequências:
  - o QR Code já pode apontar para o próprio repositório, ou para uma página do GitHub Pages com o HTML de conferência, sem depender do Power BI Service;
  - tudo o que está versionado fica visível a qualquer pessoa: código, painéis de dados (todos de bases públicas e agregadas), registros de decisão, pauta para a orientadora e o rascunho da declaração de uso de IA; o caminho da pasta de Henrique aparece no parâmetro `PastaDados` do modelo;
  - a descrição do repositório no GitHub ainda fala do ENEM e precisa ser atualizada lá;
  - alternativa, se a exposição incomodar: repositório privado com o Guilherme como colaborador.
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
- **Página de Eficiência, revisão do desenho (2026-10-30):**
  - **Dispersão:** a esperada × observada virou gasto por aluno (eixo log) × eficiência, com linha em zero. O Power BI não desenha a diagonal y = x, e o resíduo do MQO é, por construção, não correlacionado com o log do gasto na amostra conjunta das edições (dentro de uma edição, a correlação fica perto de zero). Assim, o gráfico mostra que há redes acima e abaixo do esperado em qualquer nível de gasto.
  - **Histograma:** o do percentil (uniforme por construção) virou barras com a % de redes acima do esperado por UF, que mostram a concentração regional (por exemplo, o CE).
  - **Medida nova:** `Marca de salto`, a versão curta do aviso, para a coluna do ranking.
- **Páginas também geradas por script (Henrique, 2026-10-30):** montar cada página à mão levaria tempo demais. Por isso, `src/Visualizacao/Gerar_Relatorio_PowerBI.py` escreve as páginas no formato PBIR, que é público e tem esquemas JSON oficiais.
  - **Como funciona:** cada página é descrita em poucas linhas (posição, tipo de visual e campos), e o cabeçalho com as cinco segmentações é comum a todas.
  - **Conferência:** com `--validar`, cada arquivo é conferido contra os esquemas oficiais da Microsoft. Um teste com quatro erros inventados mostrou que todos são recusados.
  - **Limite da conferência:** o esquema não confere os nomes dos papéis (X, Y, Values...) nem as propriedades de formatação. Esses seguem a convenção do Power BI e só se confirmam ao abrir.
  - **Páginas existentes não são tocadas**, salvo com `--refazer`. As medidas novas entram no modelo com `Gerar_Modelo_PowerBI.py --adicionar-medidas`, que só acrescenta.
  - **Primeira página gerada:** Eficiência, com 15 visuais. Abriu no Power BI com os números esperados (46,3% acima do esperado no Brasil, AI, MT, 2023).
  - **Revisão após o primeiro print (2026-10-30):**
    - segmentações com rótulo em português no próprio campo;
    - cartões mais baixos;
    - sem o subtítulo automático;
    - cabeçalhos legíveis no ranking e sem linha de total;
    - mais altura para o ranking.
  - **Medidas ajustadas:**
    - `Eficiência (pontos)` passou a ser arredondada em 4 casas: a média nacional aparecia como "-0,0" por um resíduo numérico de −3×10⁻¹³;
    - `Aviso do modelo` passou a sempre dizer qual comparação está em uso, porque um cartão vazio mostrava "(Em branco)".
  - **Nova opção:** `Gerar_Modelo_PowerBI.py --atualizar-medidas` troca só as medidas indicadas e preserva o identificador interno de cada uma.
  - **Escala log da dispersão:** não pegou pelo arquivo. Foi ligada uma vez no Power BI, e o arquivo salvo mostrou o nome certo da propriedade (`logAxisScale: true`, e não `axisScale: 'log'`). Agora o gerador grava assim.
    - **Método para o resto do relatório:** quando uma formatação não pegar, ela é feita uma vez no Power BI, e o gerador copia o que o Desktop gravou.
    - **Ao salvar, o Desktop só reordenou campos e marcou `active: true` nos campos de categoria;** o gerador passou a fazer o mesmo.
  - **Segundo print:**
    - os rótulos dos cartões sumiram por falta de altura (passaram de 64 para 72 px, com o número em 18 pt);
    - o aviso do modelo, que ficava cortado, foi encurtado para caber em uma linha.
  - **Erro de renderização corrigido (2026-10-30):** o Power BI acusou "Erro ao renderizar o relatório" no módulo de tabelas (`Cannot read properties of undefined (reading 'isMeasure')`).
    - **Causa:** a marca `active: true`, que o gerador passou a pôr nas colunas de todos os visuais. O Desktop só grava essa marca em gráficos e segmentações, nunca na tabela.
    - **Correção:** a tabela ficou sem a marca.
    - **Lição:** copiar do Desktop só o que ele grava no mesmo tipo de visual.
- **Identidade visual (Henrique, 2026-10-30):** faixa azul institucional e o nome **Painel de Eficiência Educacional**.
  - **Faixa azul-escura (`#0d366b`) no topo de todas as páginas:** traz o nome do painel, o título da página e o subtítulo, com as segmentações por cima, em caixas brancas.
  - **Fundo da página cinza-claro (`#f4f5f7`):** cartões e gráficos ficam em caixas brancas com cantos arredondados (8 px), borda fina e sombra leve; números e títulos em azul-escuro.
  - **Alternativas consideradas:** "clara e editorial" (melhor para imprimir, menos cara de produto) e "escura" (cansa em leitura longa, imprime mal e exigiria revalidar a paleta para fundo escuro).
  - **Onde fica:** o estilo é gravado em cada visual e em cada página, partes que o esquema oficial cobre.
- **Página Ficha do município (2026-11-02):**
  - **Escolha do município:** por um filtro com busca na própria faixa, e não por detalhamento (clique direito). É mais simples para o técnico da secretaria, que digita o nome da cidade, e mais robusto para gerar. O detalhamento pode ser acrescentado depois.
  - **Conteúdo:**
    - cartões com o nome do município, o perfil (porte e cluster), o gasto do ano, a proficiência, a eficiência, o percentil e a faixa;
    - linhas da proficiência por edição, contra as medianas do cluster, da UF e do Brasil;
    - colunas com o gasto por aluno ano a ano;
    - tabela de eficiência por edição, com a marca de salto;
    - quadro "Como ler esta ficha", escrito para o usuário-alvo.
  - **O filtro de Edição vale só para os cartões:** gráficos e tabela mostram todas as edições (interação "sem filtro" gravada na página).
  - **Medidas novas:** `Município selecionado` e `Perfil do município`. Como o modelo desestimula agregações implícitas, os textos dos cartões vêm de medidas.
  - **Conferida no Power BI com Ibateguara-AL:** 331,2 pontos, +137,6, percentil 100 e salto em 2021, iguais à conferência em Python.
- **Cartões cortados (2026-11-02):**
  - **Causa:** o cartão do Power BI reserva espaço interno acima e abaixo do conteúdo, e o rótulo saía cortado.
  - **Correção:** espaço interno reduzido (2 px na vertical), cartões de 84 px de altura e o cartão da faixa de eficiência mais largo.
  - **Gasto sem abreviação:** os cartões mostram "R$ 12.000", e não "R$ 12 Mil".
- **Página Pares (2026-11-02):** o técnico escolhe um município de referência e vê as redes do mesmo cluster com gasto por aluno (mesmo ano da edição) entre 0,8 e 1,25 vez o dele, ordenadas pela eficiência.
  - **Sem filtro de visual sobre medida:** a parte mais frágil do formato fica de fora. As colunas da tabela são medidas `Par: …`, vazias quando a rede não é par, e o Power BI esconde essas linhas sozinho.
  - **Topo da página:** o nome da referência, a regra já com os valores ("Mesmo cluster, gasto entre R$ … e R$ …"), o gasto, a proficiência e a eficiência da referência, o número de pares e quantos deles entregam mais.
  - **Medidas novas (12):** `Município de referência`, `Proficiência do município de referência`, `Eficiência do município de referência`, `Regra dos pares`, `Pares encontrados`, `Pares que entregam mais` e as seis colunas `Par: …`.
  - **Conferência em Python (AI, MT, 2023, modelo oficial):**
    - Campinas-SP: 34 pares, 30 entregam mais; o primeiro é Guararema-SP (+34,3);
    - Ibateguara-AL: 690 pares, 2 entregam mais (Santana do Mundaú-AL e Coruripe-AL, ambos com salto atípico);
    - Sobral-CE: 175 pares, nenhum entrega mais.
  - **Conferida no Power BI com Campinas-SP:** 34 pares, a regra com os valores certos e Guararema-SP em primeiro, iguais ao Python.
  - **Erro encontrado e corrigido:** o cartão "Pares que entregam mais" mostrava 32, e o certo é 30. Dois pares sem eficiência calculada entravam na conta, porque na comparação `eficiência do par > eficiência da referência` o DAX trata o vazio como zero, e 0 > −25,0. A medida passou a exigir eficiência não vazia.
  - **Margem interna:** a faixa do topo e os quadros "Como ler" e "Como usar" ganharam margem interna, porque o texto encostava na borda.
  - **Ponto a avaliar:** nos clusters grandes, a faixa de 0,8 a 1,25 vez o gasto pega quase todo o grupo (690 dos 1.037 municípios do cluster de Ibateguara). Opções: estreitar a faixa ou exigir também o mesmo porte. A lista ordenada já põe os mais relevantes no topo.
- **Página Início (2026-11-02):** é a primeira do relatório e funciona como porta de entrada.
  - **Cartões:** gasto mediano, proficiência média, % acima do esperado, redes com nota e cobertura do Saeb.
  - **Séries:** proficiência por edição e gasto por ano, sempre do recorte escolhido contra o Brasil.
  - **Guia:** as três perguntas do painel e a página que responde cada uma, mais um navegador de páginas.
  - **Filtro de Edição:** vale só para os cartões, como na Ficha.
  - **Medidas novas:** `Proficiência média do Brasil` e `Gasto por aluno do Brasil (mediana anual)`.
  - **Valores esperados (Brasil, AI, MT, 2023):** R$ 13.721, 220,2 pontos, 46,3% acima do esperado, 5.243 redes e cobertura de 94,1%. Todos conferidos no Power BI.
  - **Navegador de páginas:** no Power BI Desktop, botões e navegadores só respondem com Ctrl + clique, porque o clique simples seleciona o visual para edição. No modo de leitura e no relatório publicado, basta um clique. O título do bloco avisa isso.
  - **Faixa:** a margem vertical voltou a 2 px, porque 6 px cortavam o subtítulo. O navegador ganhou margem interna.
- **Página Mapa (2026-11-05):** a eficiência de cada município aparece no "Mapa de formas" com a malha TopoJSON (P6), ao lado de um resumo por UF.
  - **Cores divergentes com centro fixo em 0:** vermelho abaixo, cinza perto de 0 e azul acima do esperado. Na primeira montagem manual, o Power BI pôs o meio da escala na média (43,7 pontos), o que puxava o mapa para o vermelho.
  - **Formato aprendido do Desktop:** o mapa foi inserido uma vez à mão e o gerador copiou o que o Power BI gravou: tipo `shapeMap`, papéis `Category` e `Value`, a malha como recurso `ShapeMap` do relatório e as cores numa regra de gradiente de três pontos. A cada execução, o gerador copia a malha atual do pipeline para esse recurso.
  - **Limite do visual (decisão de Henrique: mapa por UF):** o Mapa de formas desenha no máximo cerca de 1.500 áreas por vez; o limite vem de relatos da comunidade, sem documentação oficial. Com o Brasil inteiro (5.571 municípios), ele mostra só uma amostra e avisa "Excesso de valores".
    - Por UF, todos cabem: a maior, MG, tem 853.
    - Acima do mapa, a medida `Aviso do mapa` pede para escolher uma UF quando o recorte passa de 1.500 municípios.
    - A visão nacional fica no "Resumo por UF".
  - **Escala de cor saturada em ±30 pontos (2026-11-05):** com o gradiente indo do mínimo ao máximo do país (−77 a +165), quase todo o mapa ficava cinza-claro. Em 2023, ±30 pontos cobrem de 88% a 94% das redes, conforme a etapa e a disciplina (p5 entre −25 e −30; p95 entre +26 e +35). Acima disso, a cor fica no máximo. O texto acima do mapa informa o limite.
  - **Navegação:** zoom automático ao filtrar a UF, pela roda do mouse e ao selecionar; mapa mais largo (924 px) e tabela por UF mais estreita. As propriedades de zoom foram deduzidas, sem cópia do Desktop; se não pegarem, valem o mesmo método de ajustar uma vez e copiar.
  - **Aviso encurtado** para caber em uma linha.
  - **Alternativas descartadas:**
    - um segundo mapa só com as 27 UFs, que exigiria gerar a malha das UFs e caberia pior na página;
    - um visual de terceiros sem limite, que depende de componente externo, pode exigir licença e pode não funcionar no "Publicar na Web" (A7).
- **Página Defasagens (2026-11-06):** responde à pergunta 4 do painel (gastar mais se associa a notas maiores, e com que defasagem?).
  - **Conteúdo:**
    - colunas e matriz com o ρ de Spearman por edição e defasagem, com todas as edições e defasagens ao mesmo tempo;
    - cartões e uma dispersão gasto × proficiência para a edição e a defasagem escolhidas na faixa.
  - **Filtros:**
    - a segmentação de defasagem é nova e não é sincronizada, porque vale só nesta página;
    - as segmentações de edição e de defasagem não filtram as colunas nem a matriz, pois a defasagem é a própria série desses dois visuais;
    - Modelo de eficiência não entra, porque a página não usa a eficiência.
  - **Matriz sem totais:** um ρ de várias edições juntas misturaria anos diferentes.
  - **Leitura do ρ:** a medida `Leitura da correlação` descreve a força pela convenção usual: |ρ| < 0,1 praticamente nula, < 0,3 fraca, < 0,5 moderada e ≥ 0,5 forte. Ela também explica as lacunas da série (P2): 2017 só tem o mesmo ano, e 4 anos antes só existe a partir de 2021.
  - **Valores de conferência (Brasil, Matemática, postos com empate no menor, como o RANKX):** a grade completa está em `data/interim/diagnosticos/conferencia_defasagens.csv`.

    | Etapa | Edição | Mesmo ano | 1 ano antes | 2 anos antes | 4 anos antes |
    |---|---|---|---|---|---|
    | AI | 2017 | 0,46 | | | |
    | AI | 2019 | 0,41 | 0,40 | 0,44 | |
    | AI | 2021 | 0,33 | 0,37 | 0,41 | 0,45 |
    | AI | 2023 | 0,26 | 0,26 | 0,32 | 0,38 |
    | AI | 2025 | 0,16 | 0,17 | 0,25 | 0,31 |
    | AF | 2023 | 0,17 | 0,17 | 0,24 | 0,28 |

  - **Achado para o texto:**
    - **No Brasil:** a associação é fraca a moderada, cresce com a defasagem e cai de uma edição para a outra.
    - **Dentro de cada UF:** ela é bem menor. Em AI, Matemática, 2023, com o gasto do mesmo ano, o ρ mediano entre as 23 UFs com 30 redes ou mais é 0,08 (de −0,13 no RN a +0,32 no RJ), contra 0,26 no Brasil. No CE, fica entre −0,08 e +0,29, conforme a edição.
    - **Leitura:** boa parte da correlação nacional vem das diferenças entre estados, o que reforça os efeitos fixos de UF (A2). O quadro "Como ler" da página avisa isso.
  - **Desempenho:** o ρ é calculado em DAX, com RANKX, para cada célula. Se a página demorar mais de ~2 s, a alternativa registrada na especificação é calcular a grade no Python e carregá-la como tabela.
- **Página Contexto e clusters (2026-11-06):**
  - **Conteúdo:**
    - **Tabela-perfil dos 7 clusters (A6):** as colunas de `dim_cluster` (municípios, população mediana, alfabetização, IDHM Renda e Longevidade, infraestrutura, região principal) vêm ao lado de redes com nota, gasto mediano, proficiência mediana e % acima do esperado.
    - **Dispersão gasto × proficiência**, colorida por cluster.
    - **Barras por porte:** gasto mediano e proficiência mediana. "Sem informação" fica fora, por ser um só município, sem nota.
  - **Filtros:** o perfil é nacional e fixo, pois as colunas de `dim_cluster` não mudam com os filtros. As medidas seguem UF, etapa, disciplina, edição e modelo.
  - **Formato das colunas:** o gerador do modelo ganhou `FORMATOS_COLUNA` e a opção `--formatar-colunas`, que acrescenta `formatString` às colunas exibidas direto, como percentual, milhar e três casas no IDHM, sem recriar o modelo.
  - **Valores de conferência (Brasil, AI, MT, 2023, gasto do mesmo ano, modelo oficial):** o arquivo é `data/interim/diagnosticos/conferencia_contexto.csv`.

    | Cluster | Redes com nota | Gasto (mediana) | Proficiência (mediana) | Acima do esperado |
    |---|---|---|---|---|
    | 1 Nordeste · pequenos | 925 | R$ 13.007 | 204,9 | 40,0% |
    | 2 Nordeste · médios | 1.021 | R$ 11.302 | 196,2 | 43,4% |
    | 3 Sudeste · pequenos | 722 | R$ 14.865 | 224,9 | 40,2% |
    | 4 Centro-Oeste · pequenos | 557 | R$ 16.306 | 221,9 | 42,2% |
    | 5 Nordeste e Norte · grandes | 272 | R$ 11.690 | 209,1 | 41,3% |
    | 6 Sul e Sudeste · pequenos | 1.032 | R$ 15.602 | 237,2 | 58,7% |
    | 7 Sudeste · médios | 714 | R$ 13.461 | 232,5 | 51,7% |

    - **Por porte:** o gasto mediano cai de R$ 16.669 (até 5 mil habitantes) para R$ 11.987 (100 a 500 mil) e volta a R$ 14.093 acima de 500 mil. A proficiência mediana vai de 226,7 a 212,2 (mais de 500 mil).
  - **Achado (página Contexto e clusters):** o % acima do esperado vai de 40% (cluster 1) a 59% (cluster 6). O modelo oficial (A8) já inclui as variáveis de contexto usadas nos clusters, mas de forma linear e sem efeito de região. Por isso parte da diferença entre os grupos, provavelmente regional, ainda aparece na eficiência, e a comparação dentro do cluster (página Pares) é a mais justa. Isso fica para avaliar com o Guilherme se cabe na seção de Método.
- **Página Estados (2026-11-09):** camada estadual, com 27 UFs, Anos Finais e Ensino Médio. A leitura é descritiva (L8): com 27 unidades, a página não mostra correlação (mínimo de 30, I12) nem eficiência.
  - **Conteúdo:**
    - cartões com UFs com nota, proficiência média, gasto mediano nas versões A e B e UFs sem a linha do Ensino Superior;
    - dispersão gasto × proficiência por UF, colorida por região;
    - proficiência por edição e por região;
    - tabela das UFs;
    - linha do gasto mediano por ano nas versões A e B.
  - **Filtros:**
    - **Etapa:** a segmentação é própria (AF e EM) e não sincronizada, porque o Ensino Médio não existe nas páginas municipais.
    - **Edição:** vale para os cartões, a dispersão e a tabela, mas não para as duas linhas.
    - **Gasto:** é o do mesmo ano da edição.
  - **Mudança em relação à especificação:**
    - **Previsto:** um seletor de versão A ou B.
    - **Por que mudou:** a conferência mostrou que A e B são iguais onde a linha 12.364 existe (G4).
    - **Como ficou:** a versão B aparece como segunda linha no gráfico de gasto e num cartão. A tabela marca com "⚠ sem a linha" as UFs que ela deixaria de fora, e não há seletor.
    - **Vantagem:** mostra a sensibilidade sem esconder a versão oficial.
  - **Medidas novas:** `UFs avaliadas`, `UFs sem a linha do Ensino Superior` e `Marca do Ensino Superior`.
  - **Ajustes depois da primeira conferência (2026-11-09):**
    - **Clique num ponto:** filtrava a página toda para aquela UF. Com MT selecionado, os cartões mostravam 1 UF, 243,2 e R$ 14.898, valores corretos para MT, e isso pareceu erro. O título da dispersão agora explica o clique.
    - **Cartão "UFs sem a linha":** mostrava "(Em branco)" quando nenhuma UF do recorte estava sem a linha. Como zero UFs é um zero de fato, e não um dado ausente (A3), a medida agora devolve 0.
    - **Rótulos dos cartões de gasto:** encurtados, porque não cabiam.
- **Página Sobre os dados (2026-11-09):** quadros de texto com:
  - fontes e recorte;
  - indicadores, em versão curta da seção 4 da especificação;
  - limitações principais, em versão curta da seção 10 deste registro;
  - autoria e data de atualização;
  - acesso ao projeto.
  - **Data dos dados:** é a do `.parquet` mais recente de `data/processed/powerbi`, gravada quando a página é gerada. Depois de rodar o pipeline de novo, é preciso regravar a página (`--refazer tcc_sobre`).
  - **Uso de IA:** a página repete a declaração do README (apoio do Claude no código e na documentação; decisões de método dos autores). A redação final deve seguir o que for combinado com a orientadora (Manual do TCC).
  - **QR Code (A7):** por enquanto, é um espaço reservado.
- **Etapa 1 do plano da reunião de 2026-11-06 (2026-11-09):**
  - **Nova tabela `fato_oferta_municipal`:** uma linha por município, etapa (AI, AF) e ano de 2017 a 2025.
    - **Conteúdo:** matrículas da etapa na rede municipal e na estadual (Censo Escolar), a parcela municipal `PART_MUN` e a situação nas edições do Saeb ("Com nota", "Sem nota divulgada pelo Inep" ou "Sem rede municipal na etapa").
    - **Conferência:** "Com nota" bate com o painel, e as matrículas municipais de AI batem linha a linha.
    - **Ligação com o modelo:** a tabela se liga a `dim_municipio`, `dim_ano` e `dim_etapa`. O gerador do modelo ganhou `--adicionar-tabelas`.
  - **Medidas novas:** `Situação da rede` (cartão na Ficha), `Municípios sem rede municipal na etapa` e `Municípios sem nota divulgada` (no aviso do Mapa).
  - **`Marca de salto`:** mostra "⚠ salto", "não" ou "sem edição anterior", e só onde há nota, para não criar linhas nas tabelas.
  - **Rótulos dos modelos:** "Comparação nacional (2017–2023)" e "Comparação no próprio estado (2017–2025)". O filtro passou a se chamar "Comparação da eficiência", e `Aviso do modelo` explica o que cada comparação faz e o caso de 2025.
  - **Página Eficiência:** a tabela de ranking ficou mais estreita para dar lugar a um quadro "Como ler", com proficiência, esperada, eficiência, clusters e o achado de que mais gasto não garante eficiência.
  - **Páginas regravadas:** Início, Eficiência, Ficha, Pares, Mapa e Contexto, porque o padrão do filtro de comparação mudou.
- **Correções depois da conferência da etapa 1 (2026-11-09):**
  - **Erro nos cartões de aviso (Eficiência e Mapa):**
    - **Causa:** `Aviso do modelo` usava `\"` para aspas dentro do texto, o que não existe em DAX, e a medida inteira ficou inválida.
    - **Correção:** as aspas viraram tipográficas. O gerador do modelo agora recusa `\"` em qualquer medida.
  - **Página Boas-vindas** (primeira do relatório, pedido da reunião):
    - à esquerda, para que serve o painel e como usá-lo;
    - à direita, um botão para cada página, com uma frase sobre o que ela responde.
    - O botão é do tipo `actionButton`, com a navegação em `visualLink` (`type` = `PageNavigation`, `navigationSection` = nome interno da página); as propriedades foram conferidas no esquema oficial.
    - Ela substitui o navegador de páginas da antiga Início, que cortava os nomes.
  - **Início → "Visão geral":** o nome exibido mudou; o nome interno `tcc_inicio` ficou, para os botões e o histórico. Sem o navegador, o guia de leitura ocupa a coluna inteira.
  - **Pares, comparação 1 a 1:**
    - **Como escolher o segundo município:** pelo filtro "Comparar com", da tabela calculada `cmp_municipio`, sem relação com o modelo, ou, com esse filtro vazio, clicando num par da tabela.
    - **O que aparece:** cartões lado a lado da referência e do comparado (gasto, proficiência, esperada, eficiência e percentil) e a frase `Comparação 1 a 1`, com a diferença de eficiência e de gasto e se o cluster é o mesmo.
    - **Medidas novas:** `Município comparado`, `Comparado: …` (5), `Esperada do município de referência`, `Percentil do município de referência` e `Comparação 1 a 1`.
    - O quadro "Como usar" virou o título da tabela e o rodapé.
  - **Textos cortados:**
    - **Nova conferência:** o gerador ganhou `--conferir-textos`, que estima, pela largura média das letras, se cada quadro de texto, título de visual e rótulo de cartão cabe no espaço.
    - **Resultado da primeira execução:** 29 casos, entre eles o rodapé de todas as páginas, que quebrava em duas linhas numa faixa de uma.
    - **Correção:** textos encurtados, rótulos trocados (por exemplo, "Eficiência média" e "Saltos atípicos") e alturas ajustadas, até zerar os avisos.
    - **Limite:** a estimativa não mede a fonte de fato. O que ela não pegar é corrigido pelo print.
  - **Páginas regravadas:** todas.
  - **Segunda rodada de textos cortados, a partir dos prints:**
    - **Botões da Boas-vindas:** o texto já estava no arquivo, mas não aparecia no Desktop.
      - **Causa:** comparando o botão salvo pelo Desktop com o gerado, o Desktop grava no objeto `text` duas entradas: o texto, no estado `default`, e um `show` sem estado, que é o que liga a exibição.
      - **Correção:** o gerador passou a gravar as duas entradas.
    - **Legenda das dispersões por cluster (Eficiência e Contexto):** o rótulo completo era cortado. Agora a legenda fica à direita e usa a coluna nova `CLUSTER_CURTO` de `dim_municipio`, com número, região e porte (por exemplo, "1 · Nordeste · pequenos"). Para levar a coluna ao modelo, o gerador do modelo ganhou `--recriar-tabelas`, que regrava uma tabela importada a partir do Parquet com as mesmas lineageTags.
    - **Perfil na Ficha:** o cartão ganhou altura para duas linhas, porque o cluster era cortado.
    - **Faixa:** a conferência de textos passou a checar se o título e o subtítulo da faixa cabem antes da primeira segmentação. O subtítulo de Defasagens passava por baixo dos filtros; ele e os de Eficiência e Contexto foram encurtados.
    - **Calibragem:** a largura média das letras foi medida nos prints: ~0,48 da altura da letra no texto comum e ~0,50 no negrito.
  - **Boas-vindas redesenhada (2026-11-09):** a primeira versão cumpria a função, mas era pouco visual, e Henrique pediu outra forma de apresentar o mesmo conteúdo, sem tirar nada. A página passou a ter quatro faixas:
    1. **Para que serve e o painel em números:** 4 cartões fixados por filtros ocultos em Brasil, Anos Iniciais, Matemática e Saeb 2023 (redes com nota, gasto mediano, proficiência média e % acima do esperado).
    2. **As três perguntas do painel:** cada uma em faixa azul, com explicação e botão para a página que a responde (Defasagens, Ficha do município e Pares).
    3. **Como usar, em seis passos:** blocos numerados lado a lado.
    4. **Todas as páginas:** grade de 3 × 3, com botão e frase de cada uma.
    - O rodapé de fontes saiu desta página e continua nas demais.
  - **Boas-vindas, terceira versão (2026-11-09):** a segunda ficou poluída ("quantidade não quer dizer qualidade"). Entre três arranjos mostrados, Henrique escolheu duas colunas.
    - **À esquerda:** um único quadro com "Para que serve" e "Como usar", com os seis passos numerados e espaço entre eles.
    - **À direita:**
      - "Comece por uma pergunta": as três perguntas como botões grandes;
      - "Outras páginas": as seis páginas restantes como botões azul-claros.
    - **O que saiu e o que ficou:**
      - saíram os cartões de números;
      - as frases sobre cada página passaram para a dica do botão, que aparece ao passar o mouse (propriedade `tooltip` do `visualLink`);
      - o conteúdo das instruções ficou inteiro.
  - **Terceira rodada de ajustes, a partir dos prints da Ficha (2026-11-09):**
    - **Filtros da faixa com valor cortado:**
      - os rótulos das comparações ficaram curtos: "Nacional (até 2023)" e "Mesmo estado (até 2025)";
      - o filtro de Etapa passou a 192 px e o de comparação a 196 px; UF e defasagem ficaram mais estreitos;
      - os títulos de Eficiência ("Quem entrega acima do esperado?") e de Pares ("Com quem conversar") foram encurtados para caber;
      - a conferência de textos passou a medir, em cada filtro, o maior valor da coluna (lido do Parquet).
    - **"Como ler" sem todas as colunas:** os quadros da Eficiência e da Ficha viraram glossários, com cada coluna da tabela em negrito e a definição ao lado. Na Eficiência entram cluster, gasto, proficiência, esperada, eficiência, percentil, salto e "Rede atende". Na Ficha entram as linhas, todas as colunas e o caso de 2025.
    - **2025 sem eficiência na Ficha (Campinas):** com a comparação nacional, que não cobre 2025 (C1), a faixa mostrava "Sem cálculo". Agora diz "Só na comparação com o mesmo estado". O glossário e o rodapé da Eficiência explicam o motivo.
    - **Perfil cortado:** a medida usa o rótulo curto do cluster (`CLUSTER_CURTO`), e o cartão ganhou altura.
    - O ranking da Eficiência também passou a usar o rótulo curto do cluster.
  - **Etapa 3 do plano da reunião (2026-11-09):**
    - **Eficiência em % do esperado (A10):**
      - colunas `EFIC_PCT` e `EFIC_PCT_ALT` em `fato_desempenho_municipal`, calculadas no `Preparar_PowerBI.py` a partir do resíduo e da esperada;
      - medida principal `Eficiência (% do esperado)`, usada nos cartões, na dispersão e na ordenação do ranking (Eficiência), na Ficha, nos Pares (tabela, "Pares que entregam mais", comparação 1 a 1 e diferença em pontos percentuais) e no Mapa;
      - os pontos ficam como coluna "Pontos" e na dica do Mapa.
    - **Mapa:** a página não tem mais o filtro de comparação. O mapa e os cartões têm um filtro oculto, "Mesmo estado"; o resumo por UF tem outro, "Nacional".
    - **Visão geral:**
      - novo gráfico com a parcela de redes que melhoraram desde a edição anterior;
      - a linha de gasto ganhou o "valor da época" (R$ 2025 ÷ fator do IPCA, coluna `FATOR_IPCA` de `dim_ano`);
      - o glossário explica os dois.
    - **Valores de conferência (Brasil, AI, MT, 2023):**
      - eficiência média +0,0% (nacional);
      - redes que melhoraram 79,9% (2019: 66,0%; 2021: 14,9%; 2025: 79,2%);
      - gasto mediano R$ 13.721 de 2025, que equivale a R$ 12.520 da época (2017: R$ 9.391 e R$ 6.236);
      - Campinas −10,5%;
      - Mapa com CE: 184 redes, 44,6% acima, +1,7%.
  - **Correção do Mapa (2026-11-09):**
    - **Problema:** na conferência, os cartões e as cores do Mapa saíram na comparação nacional (CE: 90,2% acima, +16,1%), apesar dos filtros ocultos de visual sobre `dim_modelo`.
    - **Correção:** a comparação "mesmo estado" foi fixada dentro de medidas próprias (`Mapa: eficiência (%)`, `Mapa: eficiência (pontos)`, `Mapa: % acima do esperado`, `Mapa: redes comparadas`, com `CALCULATE` + `TREATAS`), e os filtros de visual saíram.
    - **Lição:** para fixar um parâmetro num visual, a medida é mais confiável que o filtro oculto.
  - **Mapa com as duas comparações (Henrique, 2026-11-09):**
    - **Filtro "Comparação do mapa":** a página ganhou um filtro próprio, sem sincronização, que vem em "Mesmo estado (até 2025)" e permite trocar para "Nacional". As medidas `Mapa: …` leem esse filtro com `REMOVEFILTERS` + `TREATAS`.
    - **Resumo por UF:** fica sempre na comparação nacional, com as medidas `UF: …`.
    - **Dica do mouse:** mostrava "CO_MUNICIPIO 2304400". Agora as áreas da malha registrada no relatório usam "Nome (UF)" como id (o código fica em `properties.CD_MUN`), o local do mapa é `dim_municipio.MUNICIPIO_UF`, e a dica mostra o nome.
  - **Inflação explicada em um só lugar (Henrique, 2026-11-09):**
    - **O que saiu:** a linha "valor da época" saiu da Visão geral, porque sugeria que só aquele gasto dependia da inflação.
    - **Onde ficou:** em Sobre os dados, um gráfico mostra quanto vale R$ 1 de cada ano em R$ de 2025 (medida `Fator do IPCA`), e o texto de fontes traz o exemplo de 2017 (1,51).
    - **Resto do painel:** o glossário da Visão geral diz que todo valor em reais está corrigido.
  - **Estados só com a versão A (Henrique, 2026-11-09):**
    - **O que saiu:** o cartão e a linha da versão B. Onde a linha 12.364 existe, A = B (G4), e a mediana muda no máximo ~1% (2023: R$ 13.343 contra R$ 13.467).
    - **O que ficou:** a marca ⚠ na tabela.
    - **No texto:** a comparação A × B vai como teste de robustez.
  - **Revisão dos filtros por página (Henrique, 2026-11-09):** cada página fica só com os filtros que mudam algum visual dela.

    | Página | Filtros | O que mudou |
    |---|---|---|
    | Boas-vindas, Sobre os dados | nenhum | — |
    | Visão geral | UF, etapa, disciplina, edição | saiu "Comparação da eficiência", que só mudava o cartão de % acima |
    | Eficiência, Ficha, Pares | os de antes, com a comparação | todos mudam algum visual |
    | Mapa | UF, etapa, disciplina, edição, comparação do mapa | — |
    | Defasagens | UF, etapa, disciplina, edição, gasto de quando | — |
    | Contexto e clusters | UF, etapa, disciplina, edição | saiu "Comparação da eficiência", que só mudava a coluna de % acima |
    | Estados | etapa (rede estadual), disciplina, edição | — |

    - **% acima nas páginas sem o filtro:** a Visão geral e o Contexto usam a medida `% acima do esperado (padrão)`. Ela fica na comparação nacional e, em 2025, que a nacional não cobre, passa para a comparação no mesmo estado. Os glossários avisam.
  - **Conferência da inflação** (`src/Testes/Conferir_Inflacao.py`, 2026-11-09). Pergunta da conferência: os outros valores do painel também estão corrigidos? Todos os itens passaram:
    - SIOPE e SICONFI: R$ 2025 = nominal × fator do IPCA em todas as linhas;
    - gasto por aluno = R$ 2025 ÷ matrículas;
    - defasagens: o gasto de k anos antes é o gasto real daquele ano, corrigido pelo próprio fator;
    - as 16 colunas de gasto do painel e as 9 citadas nas medidas estão todas em R$ 2025.
    - O que não é dinheiro (notas, eficiência, percentis, contagens) não depende da inflação. No modelo, o gasto entra em log e há efeito de edição, então um fator comum a todas as redes do ano não muda a eficiência.
  - **Eficiência em "0,0%" e pares de vários estados (Henrique, 2026-11-09):** a consulta direta ao modelo deu os valores certos (Campinas, AI, MT, 2023: −10,5%). Havia três causas:
    - **Erro de formato em Pares:** a regra de formato em pontos vinha antes da regra em % no gerador, e `Par: eficiência (%)` saía sem o ×100 ("+0,2" em vez de "+20%"). A ordem foi corrigida.
    - **Média zero por construção:** os resíduos da regressão somam zero no Brasil a cada edição (comparação nacional). Na comparação no mesmo estado, o modelo junta as edições com efeito fixo de UF: a média é zero em cada UF no período, não em cada edição (diferença típica de 1,9 ponto por UF e edição, máx. 14,6), e no Brasil fica em até 0,06%. Correção de uma explicação anterior, que dizia "zero em qualquer UF, edição a edição".
      - **Decisão:** o cartão "Eficiência média" de Eficiência e Mapa mostra "≈ 0" quando o recorte é o Brasil inteiro (sem UF, cluster nem município), e o aviso ao lado diz o porquê. Com uma UF, mostra o valor (CE: +16,1% nacional; +1,7% no mesmo estado, que compara a edição com a média do estado no período).
    - **Coincidência:** Abadia de Goiás, que abre selecionada na Ficha e em Pares, tem em 2023 proficiência igual à esperada (223,1): o −0,0% é real.
  - **Pares na comparação no mesmo estado (Henrique, 2026-11-09):** antes, o filtro só trocava a régua da eficiência, e os pares vinham do cluster no país todo. Como nessa comparação cada rede é medida contra o próprio estado, pares de estados diferentes misturavam réguas.
    - **Decisão:** na comparação no mesmo estado, os pares são do mesmo cluster **e da mesma UF** (medida `É par`). A regra no cartão, o rodapé, Sobre os dados e a comparação 1 a 1 (que avisa quando o comparado é de outro estado) dizem isso.
    - **Quantos pares sobram (AI, MT, 2023):** mediana de 78 por rede (eram 401 no país); AF, 60 (eram 282). Sem nenhum par na UF: 0,9% das redes; com menos de 5: 3,7% (AI) e 5,5% (AF). Campinas: 34 pares no país, 18 em SP.
  - **"Comparar com" podia ficar vazio só no papel:** a segmentação tinha seleção única obrigatória, e o Power BI marcava sempre o primeiro município, então a comparação com o par clicado nunca era usada. Agora ela aceita ficar vazia (opção `permite_vazio` do gerador).
  - **Revisão das tabelas e das dispersões (Henrique, 2026-11-09):** as tabelas traziam informação demais, e duas dispersões pareciam a mesma.
    - **Regra:** cada tabela fica com o que responde à pergunta da página; o detalhe de cada rede fica na Ficha.
    - **Coluna "Atenção":** junta o salto atípico (S11) e a rede municipal parcial (A9) numa coluna só. Mostra "⚠ salto", "⚠ rede parcial (x%)" ou os dois, e fica vazia sem alerta.

    | Página | Antes | Depois | O que saiu |
    |---|---|---|---|
    | Eficiência (ranking) | 10 colunas | Município, Gasto, Proficiência, Esperada, vs. esperado, Atenção | Cluster (é a cor do gráfico), Pontos e Percentil (na Ficha) |
    | Ficha (por edição) | 8 | Edição, Proficiência, Esperada, vs. esperado, Faixa, Atenção | Pontos (diferença das colunas ao lado), Percentil (no cartão) |
    | Pares | 7 | Município, Gasto, Proficiência, vs. esperado, Atenção | Diferença (p.p.) (o cartão traz a referência), Percentil (na comparação 1 a 1) |
    | Contexto (perfil) | 13 | Cluster, Municípios, População, Alfabetização, IDHM Renda, Infraestrutura, Gasto, Proficiência | IDHM Longevidade (a nota lista as variáveis), Região e % na região (gráfico novo), Redes com nota e % acima (na Eficiência) |
    | Estados | 5 | UF, Gasto, Proficiência, Ensino Superior ⚠ | Região (é a cor dos gráficos) |
    | Mapa (resumo por UF) | 4 | sem mudança | — |

    - **Dispersões:** a de gasto × proficiência fica em Defasagens, e a de gasto × vs. esperado fica em Eficiência. A do Contexto, que repetia a de Defasagens colorida por cluster, deu lugar a um gráfico com **a composição de cada cluster por região** (medida `Municípios do cluster (Brasil)`, sem os 3 municípios fora dos clusters).
    - **Defasagens:** a matriz de ρ e redes saiu nesta revisão, por repetir os rótulos do gráfico de colunas, e a dispersão de gasto × proficiência ocupou o lugar.
      - **Revertido (Henrique, 2026-11-10):** a matriz é o resultado central da página, e a dispersão parecia a de Eficiência. A matriz voltou no lugar da dispersão como **mapa de calor do ρ**: só o ρ, sem o número de redes (que está no cartão), com cor numa escala fixa de 0 a 0,5 para comparar edições e defasagens. O gráfico de colunas passou a ocupar a largura toda.
      - **Formato da cor:** regra `FillRule` com `linearGradient2` e valores mínimo e máximo explícitos, gerada pelo script e aceita pelo Desktop na primeira tentativa.
      - **Proporção (Henrique, 2026-11-10):** em 10 pt a matriz ocupava metade do bloco. Passou a 12 pt (células e cabeçalhos: `values`, `columnHeaders` e `rowHeaders` com `fontSize`), e o bloco dela e o do glossário ficaram com a mesma largura (620 px).
  - **Revisão geral (Henrique, 2026-11-11; relatório em `docs/revisao_geral.md`):** ajustes que não dependiam da orientadora.
    - **Frase retirada:** "Gastar mais não garante eficiência (correlação de 0,01)" saiu do glossário da página Eficiência e da nota de método. O resíduo de uma regressão que inclui o log do gasto não se correlaciona com ele: o 0,01 é zero por construção, e não um achado. No lugar entrou o resultado de A11 (dentro do mesmo município, +10% no gasto acompanha +0,2 ponto). O título da dispersão passou a "Gasto por aluno × resultado em relação ao esperado".
    - **Defasagens:** o glossário não diz mais que "o aluno acumula anos de escola"; a linha "Gasto antigo" explica que o ρ maior com gasto de anos antes reflete diferenças duradouras entre municípios (A11).
    - **Sobre os dados:** "modelo oficial" virou "comparação nacional", como no resto do painel.
    - **Medidas:** 12 que sobraram das revisões saíram do modelo e de `medidas.dax` (opção nova `--remover-medidas` do gerador), de 97 para 85. Ficam 5 indicadores formais sem visual, à espera de D2.
    - **Pipeline:** opção `--com-analise` no `run_pipeline.py`.
    - **A decidir com a orientadora:** a régua principal (A8 × A11), o nome do indicador de eficiência (no modelo nacional, o gasto quase não muda a nota esperada: 0,92, p = 0,20) e se os modelos entram no painel.
  - **Padrão de glossário (Henrique, 2026-11-09):** o desenho do "Como ler esta ficha" vira o padrão dos quadros explicativos: termo em negrito azul, definição ao lado e uma nota final em itálico. Ele foi aplicado também em Visão geral, Defasagens e no quadro das 27 unidades de Estados (sem título, por ser pequeno). A função `glossario` do gerador monta esses quadros.

  - **Valores de conferência (AF, MT, 2023):**
    - 27 UFs, proficiência média de 247,5 (EM: 263,3);
    - gasto mediano de R$ 13.343 na versão A e de R$ 13.467 na versão B; as 4 UFs sem a linha são AC, RO, RS e SE;
    - maior proficiência em GO (266,8, R$ 13.301) e menor na BA (226,7, R$ 16.988);
    - médias por região: Sul 258,2, Centro-Oeste 250,4, Sudeste 249,6, Nordeste 244,6 e Norte 243,7.
- **Filtros sincronizados:** Etapa, Disciplina, Edição, Modelo e UF passaram a ter grupo de sincronização. A escolha feita numa página vale nas outras.
- **Conferências do gerador de páginas:**
  - os esquemas oficiais são baixados pelo próprio script para `data/interim/esquemas_pbir` (fora do Git), e `--validar` funciona em qualquer máquina;
  - toda medida usada num visual tem de existir em `medidas.dax`. O tema (`tema_tcc.json` e a cópia registrada no relatório) recebeu os mesmos ajustes, para que visuais criados à mão saiam no mesmo estilo.

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
- **Pacote de exportação (2026-10-23):** na época o repositório no GitHub era privado (hoje é público, ver A7), e os painéis em Parquet e os documentos em Markdown não abrem bem para quem não programa. Por isso, `src/Exportacao/Gerar_Pacote_Exportacao.py` gera um ZIP com:
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

### Reunião de 2026-11-06 (Henrique e Guilherme)
Pontos levantados sobre o painel, com diagnóstico nos dados em 2026-11-09 e plano de ação em cinco etapas.

| Ponto | Diagnóstico | Encaminhamento |
|---|---|---|
| Entender a nota esperada, a proficiência, a eficiência e os clusters | Explicação faltava no painel | ✅ Quadro "Como ler" na página Eficiência e `docs/nota_metodo_eficiencia.md` (etapa 1) |
| 2025 sem eficiência | Decisão C1: sem IDHM 2025, o modelo nacional vai até 2023 | ✅ Aviso explícito quando a edição é 2025 (etapa 1); mudar sozinho de comparação fica para decisão |
| Muitos municípios sem dados | Falta a nota, não o gasto. 2023: AI 5.243 com nota, 319 sem divulgação, 9 sem rede; AF 3.196, 723 e 1.652 | ✅ Tabela `fato_oferta_municipal`, "Situação da rede" na Ficha e contagem no aviso do Mapa (etapa 1) |
| Exceções na rede dos Anos Iniciais | Em 923 municípios a rede municipal atende < 80% do AI público; em 266, < 50% (Campinas: 22%) | ✅ Etapa 2 (A9, L19): marca no painel; sem as redes parciais, as conclusões agregadas não mudam |
| Coluna "Salto" dos pares vazia | Correta, mas ambígua: só 10 dos 690 pares de Ibateguara têm salto | ✅ Mostra "não", "⚠ salto" ou "sem edição anterior" (etapa 1) |
| Modelo "dentro da UF" não filtra a UF, "mas tira alguma coisa" | Muda a régua: tira a diferença média entre estados (CE: +33,6 → +4,0) | ✅ Rótulos "Comparação nacional" e "Comparação no próprio estado" e aviso explicativo (etapa 1) |
| Selecionar um par não o compara com a referência; comparar dois municípios 1 para 1 | Função inexistente | Etapa 4: bloco de comparação na página Pares |
| Mais gasto não significa mais eficiência | Confirmado: correlação de 0,01 entre eficiência e gasto; coeficiente do gasto não significativo no modelo nacional | ✅ No quadro "Como ler" e na nota de método |
| IA na FEA | Pergunta para a orientadora | ✅ Etapa 5 preparada (2026-11-10): rascunho em `docs/declaracao_uso_ia.md` e pauta na seção 4.1 do resumo para a orientadora, com as perguntas sobre IA, % do esperado × percentil, 2025, limite de 50% e QR Code |
| Inflação na Início ou VPL | IPCA já está na base (fator 1,51 para 2017); o VPL não se aplica, porque desconta fluxos futuros por uma taxa de juros, e aqui a questão é poder de compra | ✅ Etapa 3: linha "valor da época" ao lado do gasto em R$ de 2025 na Visão geral (mediana do Brasil: R$ 6.236 da época em 2017 = R$ 9.391 de 2025) |
| Eficiência em % do esperado; mesma base no mapa | Escala diferente entre etapas (esperado ~220 em AI e ~249 em AF); a "base" do mapa era a régua nacional | ✅ Etapa 3 (A10): % do esperado como medida principal; mapa sempre na comparação com o mesmo estado, com cor saturada em ±12% |
| O desempenho melhora a cada edição? | AI MT: 218,2 → 222,7 → 211,8 (2021) → 220,2 → 230,1. Redes que melhoraram: 66% (2019), 15% (2021), 80% (2023), 79% (2025) | ✅ Etapa 3: gráfico "Redes que melhoraram" na Visão geral, com a ressalva de que melhorar não prova bom uso do gasto |

### Pendências restantes (nenhuma bloqueia o desenvolvimento)
0. **S11 (2026-10-30):** confirmar a regra proposta para marcar os saltos atípicos (mais de 3 desvios-padrão da variação média; 633 linhas marcadas, nenhuma excluída). (A8 foi decidido: versão nacional.)
1. **S8 e S4:** as propostas (não imputar notas, controlar o porte, painel balanceado; Anos Finais como complementar) seguem como padrão de trabalho, sem objeção registrada.
2. **A4 e P3:** testes de sensibilidade rodados em 2026-11-11 (falta só o G4b, que pede dados brutos); a extensão das matrículas para 2015–2016 é opcional.
3. **D1:** formato do TCC (científico ou consultoria). Afeta o texto, não o dashboard.
4. **D2:** indicadores formais. Proposta escrita em 2026-10-30 (12 indicadores, seção 4 de `powerbi/especificacao_dashboard.md`), com as faixas de eficiência por quintil; falta confirmar.
5. **D4:** referências e APA; **D5/IA:** forma de documentar o uso de IA no Método. Rascunho da declaração por etapa do trabalho em `docs/declaracao_uso_ia.md` (2026-11-10), para aprovar com a orientadora.
6. **A7:** endereço público para o QR Code (Power BI Service com "Publicar na Web", ou o HTML), a verificar na publicação.
7. **Revisão geral de 2026-11-11 (`docs/revisao_geral.md`):** a decidir com a orientadora: qual é a régua principal (nacional, A8, ou mesmo estado, usada em A11), o nome do indicador de eficiência (que quase não depende do gasto) e se os resultados dos modelos entram no painel. Também faltam a revisão bibliográfica e o registro das respostas da orientadora na reunião já feita.

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
  - **Levantamento de 2026-11-11 (`docs/levantamento_bibliografico.md`):** 17 referências do tema atual localizadas e com os dados bibliográficos conferidos, em sete eixos (gasto × desempenho no Brasil e no exterior, Fundef/Fundeb, eficiência com DEA, incentivos no Ceará, Saeb/IDEB e método), cada uma ligada a um resultado do trabalho. Só os registros e os resumos foram conferidos: falta ler os textos. A bibliografia da fase do ENEM não trata do tema e não deve ser usada. O levantamento foi feito com apoio de IA, uso a aprovar com a orientadora (D5). Segunda rodada no mesmo dia: localizado o estudo do efeito defasado de quatro anos (Alves e Frio, 2022, fronteira estocástica sem efeito fixo de município, o que explica a diferença para A11), dois trabalhos sobre a equidade do Fundeb e o contexto do ICMS educacional de Alagoas (o incentivo existe; nenhum trabalho aponta irregularidade nas notas). Municipalização e uso de dados por gestores ficaram sem referência conferida.
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
- **L19. Rede municipal parcial [A9]:** em parte dos municípios, a rede estadual atende boa parte dos alunos da etapa: 2,7% das redes com nota em Anos Iniciais e 16% em Anos Finais, em 2023, têm menos da metade dos alunos públicos. Nesses casos, o indicador descreve a rede municipal, e não a educação pública da cidade. Essas redes têm eficiência média menor, mas tirá-las não muda as conclusões agregadas.
- **L5. Pandemia [S5]:** a edição de 2021 tem menos resultados com nota e condições atípicas de aplicação.
- **L6. Matrículas de 2025 [M3]:** as matrículas estaduais caem cerca de 5% em 2025, e não se sabe se é efeito real ou da mudança de layout do Censo Escolar.
- **L7. Valores extremos [A5, G11]:** cerca de 0,7% dos municípios com nota têm gasto por aluno implausível (provável erro de registro ou rede muito pequena). Eles ficam na análise, conforme a decisão da orientadora.
- **L8. Camada estadual [A2, A12]:** são só 27 unidades, o que limita a precisão das estimativas e o uso de clusters. No modelo com efeito fixo de UF, os intervalos de 95% do coeficiente do gasto vão de cerca de −6 a +9 pontos por log do gasto: não dá para detectar uma associação do tamanho da municipal.
- **L9. Defasagens [E2, P2]:** com o gasto desde 2017, a defasagem de 2 anos só existe a partir do Saeb 2019, e a de 4 anos a partir de 2021.
- **L10. Alfabetização estática [C2]:** vem do Censo 2022 e não varia no tempo. Um município instalado depois de 2022 fica sem esse controle.
- **L11. Restos a pagar [G7]:** a despesa paga não inclui os restos a pagar inscritos no ano.
- **L12. Associação, não causalidade [A1]:** os resultados descrevem associação e eficiência relativa, não efeito causal do gasto. A relação pode até se inverter, por exemplo se o FUNDEB e a complementação da União direcionam mais recursos às redes com pior desempenho.
- **L13. Mesmo numerador para duas etapas [G5]:** a subfunção 361 cobre todo o Ensino Fundamental e não separa Anos Iniciais de Anos Finais. O mesmo gasto por aluno serve aos dois desfechos da camada municipal.
- **L14. Gasto municipal só no Fundamental [G5]:** a Educação Infantil (subfunção 365) pesa quase tanto quanto o Fundamental no gasto municipal (SP 2023: R$ 30,1 bi contra R$ 32,2 bi, segundo o dossiê) e fica fora do numerador, porque o Saeb não a avalia. O gasto em educação do município é, portanto, bem maior do que o gasto usado.
