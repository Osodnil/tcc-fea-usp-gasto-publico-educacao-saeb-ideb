# Registro de decisões de método

Panorama do que foi desenvolvido até agora, dos problemas encontrados em cada base e das decisões tomadas para contorná-los. Serve de base para a seção de Método e para as reuniões com a orientadora.

- **Última atualização:** 2026-10-22
- **Fontes deste registro:** código e dados do repositório, os testes em `src/Testes`, os diagnósticos em `data/interim/diagnosticos` e as instruções do projeto. Os números marcados com † foram recalculados nesta data a partir dos parquets em `data/interim`; os demais vêm dos testes ou das instruções, e não foram reverificados.
- **Status:** ✅ fechada · 🟡 provisória (validar com a orientadora) · ⚠️ problema em aberto

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
| **Dashboard de conferência** | — | ✅ `src/Visualizacao/Gerar_Dashboard_HTML.py` | `relatorios/dashboard_conferencia.html` |

O dashboard de conferência (2026-10-22) é um HTML autocontido, que abre offline, gerado a partir dos painéis. Ele é só descritivo: gasto por aluno do mesmo ano do Saeb, mediana do gasto e média simples das notas entre as unidades, sem nenhum modelo estimado. Ele não muda nenhum resultado.
| Saeb/IDEB | ✅ `Extract_SAEB.py` | ✅ `Transform_SAEB.py` | `saeb_{municipal,estadual}_transformado` |
| IDHM por UF | ✅ | ✅ (com t−1, ver C1) | `idhm_transformado` |
| IBGE, Censo 2022 (alfabetização) | ✅ | ✅ | `ibge_transformado` |
| IPCA | ✅ `Extract_IPCA.py` | não precisa | `ipca_deflator_anual` |

A validação de 2026-10-21 concluiu que os Extracts estão completos para a pergunta. Em 2026-10-22, todas as bases foram tratadas e cruzadas nos painéis municipal e estadual. O próximo passo é a análise exploratória e, depois, as estimações.

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

### E3. Recorte geográfico ⚠️ (depende da orientadora)
- A orientadora sugeriu SP, mas o resultado da reunião não foi registrado. O pipeline atual cobre o Brasil inteiro, então um recorte pode ser aplicado depois, na análise, sem refazer o ETL.

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

### G4. Gasto estadual = função 12 − subfunção 12.364 ✅ · ⚠️ ausência da 12.364
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
- **Encaminhamento:** levar à orientadora. Antes disso, conferir no DCA de RS (2018–2023) se o Ensino Superior foi lançado em outra subfunção.

### G4b. Total da função 12 maior que a soma das subfunções listadas ⚠️ (achado de 2026-10-22)
- **Evidência:** no SICONFI, a soma das subfunções publicadas (12.122, 12.361, …, 12.999) fica abaixo do total "12 - Educação" em vários pares UF/ano. A razão vai de 0,61 a 1,00, com mediana de 0,994; no AC, por exemplo, fica entre 0,67 e 0,75†.
- **Leitura provável:** a função 12 inclui despesas em subfunções de outras funções, como previdência de inativos, que o Anexo I-E não detalha dentro da função 12. Isso não foi verificado.
- **Efeito:** o gasto estadual usado (total da função 12 menos 12.364) pode incluir gastos que não chegam à sala de aula, com peso diferente entre os estados.
- **Encaminhamento:** registrar como limitação. Se houver tempo, testar a variante "soma das subfunções da educação básica" (361 + 362 + 365 + 366 + 367 + 368 + 122) como sensibilidade.

### G5. Subfunção 361 do SIOPE: identificar pelo código, não pelo texto ✅
- **Problema:** o rótulo muda ao longo do tempo†. Até 2023 ele é "361 - Ensino Fundamental"; em 2024 e 2025, só "361". Também há linhas "TOTAL …" (de 2017 a 2023), que somariam o mesmo gasto duas vezes, e um rótulo atípico ("SubFunção 361 - Fonte 01 - Aplic. 110": uma linha, SP 2017, R$ 146 mil).
- **Decisão:**
  - filtrar `COD_SUBF == "361"` e `EH_TOTAL == False` e `TIPO == "Municipal"`;
  - não filtrar pelo texto "361 - …", porque isso apagaria 2024 e 2025;
  - a linha atípica de 2017 fica, porque o valor é irrelevante.
- **Teste de consistência:** a participação da 361 no gasto total em educação fica estável entre 0,59 e 0,63 de 2017 a 2025†. Ou seja, não há quebra de classificação, e o crescimento nominal do gasto municipal em 361 (95 → 223 bi de 2017 a 2025†) acompanha o gasto total, puxado pela expansão do FUNDEB a partir de 2021.

### G6. O SIOPE por subfunção traz também linhas estaduais ✅
- **Problema:** os arquivos `siope_funcao_*` têm linhas `TIPO = Estadual` de 26 estados†.
- **Decisão:** filtrar `TIPO == "Municipal"` na camada municipal. As linhas estaduais do SIOPE não são usadas (ver G2).

### G7. Despesa paga, acumulada no ano ✅
- **Decisão:** usar a despesa paga (não a empenhada nem a liquidada) do 6º bimestre do SIOPE (`Num_Peri = 6`), que é o acumulado do ano, e a coluna "Despesas Pagas" do SICONFI.
- **Por quê:** a despesa paga mede o recurso que efetivamente saiu.
- **Limitação:** restos a pagar inscritos no ano ficam de fora.

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
- **Problema:** o Inep só divulga a nota das redes que atingem critérios mínimos de participação (os números exatos dos critérios não foram verificados). Entre os municípios com rede municipal, ficam sem nota†:
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
- **Pendente:** a medida principal da análise continua sendo a definida em S2 (notas do Saeb). Qual delas é a principal fica para a análise, e a nota padronizada N é a candidata natural a medida-resumo.

---

## 6. Controles

### C1. IDHM por UF com defasagem de um ano (t−1) 🟡 — pendente de validação com a orientadora
*(antes registrada como D1)*

- **Data:** 2026-10-21
- **Decisão:** o controle socioeconômico de cada edição do Saeb é o IDHM da UF do ano anterior (Saeb 2017 ← IDHM 2016, …, Saeb 2025 ← IDHM 2024).
- **Por quê:** a série anual do IDHM por UF (Radar IDHM, PNUD/FJP/IBGE, base PNAD Contínua, divulgada em 26/05/2026) termina em 2024, e não há IDHM 2025. Usar t−1 em todas as edições evita imputar valores e trata as cinco edições da mesma forma.
- **Alternativas consideradas:**
  - Repetir o IDHM 2024 em 2025, marcado como imputado: mexe só em 2025, mas trata uma edição de forma diferente das outras. **Sugerida como teste de sensibilidade.**
  - Projetar 2025 pela tendência: descartada, porque o valor seria inventado.
  - Excluir 2025 das estimações com IDHM: descartada, porque perde a edição de maior cobertura.
- **Implementação:** `src/Transform/Transform_IDHM.py`, coluna `ANO_REF_SAEB = ANO + 1` (Int32). O merge casa `saeb_*_transformado.ANO` com `idhm_transformado.ANO_REF_SAEB`. As cinco edições têm as 27 UFs†.
- **Como reverter:** no merge, casar com `ANO` em vez de `ANO_REF_SAEB` e decidir o tratamento de 2025. Nada mais precisa mudar.
- **Para o Método:** "O controle socioeconômico é o IDHM da UF no ano anterior à aplicação do Saeb (t−1), pois a série do PNUD termina em 2024."
- **Observação:** o rodapé da planilha diz "Atlas … 2022", embora a série vá até 2024. Registrar a data em que o arquivo foi baixado na citação da fonte.

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
3. IDHM do mesmo ano, com 2024 repetido em 2025 (C1).
4. Tratamento alternativo da 12.364 (G4) e gasto estadual pela soma das subfunções da educação básica (G4b).
5. Com e sem os valores extremos de gasto por aluno (A5).
6. Painel balanceado: só municípios com nota nas cinco edições (S8).

### A5. Valores extremos de gasto por aluno: marcar, não excluir 🟡 (2026-10-22)
- **Evidência:** a distribuição do gasto municipal por aluno (L0, linhas com nota de AI) tem mediana de R$ 11,2 mil e intervalo de 1% a 99% entre R$ 5,3 mil e R$ 25,6 mil†. Nas pontas, porém, aparecem valores implausíveis:
  - **Muito baixos:** Cáceres-MT 2021 (R$ 210), Carlópolis-PR 2023 (R$ 305), São Luís-MA 2017 (R$ 1,8 mil). São Luís 2017 já tinha aparecido como caso extremo na reconciliação com o SICONFI (G1).
  - **Muito altos:** redes com poucas matrículas, como Queluzito-MG 2023 (73 alunos, R$ 64,5 mil).
  - 131 dos 50 mil pares município/ano têm o gasto 361 multiplicado por mais de 3 ou dividido por mais de 3 de um ano para o outro†.
- **Decisão provisória:** o painel mantém todos os valores e marca com `GASTO_EXTREMO_L{k}` os que ficam fora do intervalo de 0,5% a 99,5% do ano (225 linhas de AI, 174 delas com nota). Isso é cerca de 0,7% da amostra com nota (lista em `diagnosticos/gasto_aluno_extremos_municipal.csv`).
- **A decidir na análise:** excluir os marcados, winsorizar ou usar o logaritmo do gasto. A sugestão é usar o logaritmo do gasto por aluno na especificação principal e rodar a análise com e sem os marcados como sensibilidade.

---

## 7b. Painéis (cruzamento das bases)

### P1. Estrutura dos painéis ✅ (2026-10-22)
- **Script:** `src/Transform/Montar_Paineis.py`. As saídas ficam em `data/processed/`.
- **Painel municipal (`painel_municipal.parquet`):** uma linha por município × etapa (AI, AF) × edição do Saeb. São 46.815 linhas e 40 colunas, com chave única†.
  - **Base:** a lista de municípios com rede municipal no Saeb.
  - **Colunas:** notas e IDEB, matrículas, gasto 361, gasto por aluno nas defasagens 0, 1, 2 e 4 anos, a marca de valor extremo, alfabetização e população (Censo 2022), região, IDHM da UF defasado (C1) e a infraestrutura da rede municipal no mesmo ano.
- **Painel estadual (`painel_estadual.parquet`):** uma linha por UF × etapa (AF, EM) × edição. São 270 linhas e 37 colunas, com chave única†.
  - **Colunas:** gasto por aluno nas versões A e B (G4) e nas mesmas defasagens, alfabetização da UF (soma dos municípios), IDHM defasado e infraestrutura da rede estadual (média municipal ponderada pelo número de escolas).
- **Regras do gasto por aluno:**
  - O gasto do ano t−k é dividido pelas matrículas do próprio ano t−k.
  - Gasto 361 igual a zero (G11) ou matrícula igual a zero (M5) viram nulo.
  - Os controles só ficam nulos para Boa Esperança do Norte-MT (5101837), que está fora do Censo 2022, ver C2.

### P2. Cobertura das defasagens ✅
- **Municípios:** o gasto começa em 2017. Por isso, L1 e L2 só existem a partir do Saeb 2019 e L4 a partir de 2021. Com nota e gasto L0, o painel tem de 4.750 a 5.306 municípios em AI e de 2.629 a 3.310 em AF, conforme o ano†.
- **Estados:** o gasto do SICONFI começa em 2014, mas as matrículas extraídas começam em 2017. Na prática, as defasagens estaduais têm a mesma limitação das municipais.

### P3. Matrículas de 2015–2016 para estender as defasagens estaduais 🟡
- **Situação:** com as matrículas de 2015 e 2016, o Saeb 2017 ganharia L1 e L2 na camada estadual, e o de 2019 ganharia L4. Os microdados do Censo de 2015 e 2016 já estão na pasta de brutos do repositório antigo. Não existe Censo de 2014 na pasta, então o L4 de 2017 não tem como ser calculado.
- **Custo:** rodar o `Extract_Censo_Matriculas.py` para 2015 e 2016, depois de copiar os brutos.
- **Decisão:** pendente. Vale a pena só se a análise estadual usar defasagens.

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

---

## 9. Para levar à orientadora

1. **C1:** IDHM com defasagem t−1.
2. **G4:** tratamento da ausência da 12.364 (RO em todos os anos, AC e SE até 2024, RS em 2018–2023). **G4b:** o total da função 12 inclui gastos fora das subfunções listadas.
3. **S4:** manter Anos Finais na camada municipal, com a amostra selecionada?
4. **E3:** recorte geográfico (Brasil ou SP).
5. **M3, S5 e A5:** confirmar os testes de sensibilidade (sem 2021, sem 2025 estadual, com e sem os gastos extremos) e o tratamento dos valores extremos.
6. **P3:** vale estender as matrículas para 2015–2016 para ter defasagens na camada estadual?
7. **S8:** a amostra é selecionada pela divulgação do Saeb (redes pequenas ficam sem nota). A proposta é descrever a seleção, controlar o porte e testar com um painel balanceado, sem imputar notas. A orientadora está de acordo?
8. **S9:** qual medida de desempenho será a principal (Matemática, Português ou nota padronizada N)?
9. **Integridade acadêmica:** o Manual exige informar e discutir previamente o uso de IA. Este registro e parte do código foram produzidos com apoio de IA, o que deve ser comunicado e documentado no Método.
