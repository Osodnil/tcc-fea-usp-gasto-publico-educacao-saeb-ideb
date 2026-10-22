# Registro de decisões de método

Panorama do que foi desenvolvido até agora, dos problemas encontrados em cada base e das decisões tomadas para contorná-los. Serve de base para a seção de Método e para as reuniões com a orientadora.

- **Última atualização:** 2026-10-21
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
| SIOPE, dados gerais | ✅ `Extract_SIOPE.py` | pendente | `siope_{ano}_extraido` |
| SIOPE, por subfunção | ✅ (⚠️ script fora do repositório, ver T1) | pendente | `siope_funcao_{ano}_extraido` |
| SICONFI estados | ✅ `Extract_SICONFI_Estados.py` | pendente | `siconfi_estados_funcao12` |
| Censo Escolar, matrículas | ✅ `Extract_Censo_Matriculas.py` | pendente | `censo_matriculas_{ano}` |
| Censo Escolar, infraestrutura | ✅ | ✅ | `censo_escolar_transformado` |
| Saeb/IDEB | ✅ `Extract_SAEB.py` | ✅ `Transform_SAEB.py` | `saeb_{municipal,estadual}_transformado` |
| IDHM por UF | ✅ | ✅ (com t−1, ver C1) | `idhm_transformado` |
| IBGE, Censo 2022 (alfabetização) | ✅ | ✅ | `ibge_transformado` |
| IPCA | ✅ `Extract_IPCA.py` | não precisa | `ipca_deflator_anual` |

A validação de 2026-10-21 concluiu que os Extracts estão completos para a pergunta. O próximo passo é o Transform das bases de gasto e das matrículas, seguido do merge.

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
- **Problema em aberto:** em alguns pares UF/ano, a linha 12.364 não aparece†. RN e MS não a têm em 11 dos 12 anos, RS em 6, e AC e SE em 1. Há duas leituras possíveis:
  - **(a) Ausência = sem gasto com Ensino Superior nessa subfunção,** e a dedução é zero.
  - **(b) Ausência = dado faltante,** e o par UF/ano sai da amostra ou é imputado.
- **Riscos:** a regra geral do projeto ("ausência não é zero") aponta para (b), mas no DCA é comum que uma conta sem movimento simplesmente não seja publicada, o que favorece (a). E se o estado registra o Ensino Superior em outra subfunção, nenhuma das duas leituras corrige o problema.
- **Encaminhamento:** levar à orientadora. Antes disso, conferir no DCA original de RN e MS se existe gasto com Ensino Superior em outra subfunção.

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

### G9. Código de município com 7 dígitos ✅
- **Problema:** o SIOPE usa 6 dígitos, e as demais bases usam os 7 do IBGE.
- **Decisão:** converter pelo dígito verificador (pesos 1,2,1,2,1,2; somar os algarismos de cada produto; verificador = (10 − soma mod 10) mod 10). A função `ibge7()` já está implementada em `Teste8_Reconciliacao.py` e deve ir para o Transform do SIOPE.

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
- **Problema:** o município `5101837` aparece no Censo Escolar e no Saeb a partir de 2025 e não existe no Censo 2022†. Provavelmente é um município instalado depois de 2022 (não confirmado), e ficará sem esse controle.

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
4. Tratamento alternativo da 12.364 (G4).

---

## 8. Problemas técnicos do pipeline

### T1. Falta no repositório o script que gerou `siope_funcao_*` ⚠️
- **Problema:** os arquivos `siope_funcao_{2017..2025}_extraido.parquet` existem e são usados pelos testes, mas o script que os produziu não está no repositório. O `Extract_SIOPE.py` só gera os dados gerais. Pelos testes, a fonte é a entidade `Despesas_Funcao_Educacao_Siope` da mesma API do SIOPE, e as colunas `COD_SUBF` e `EH_TOTAL` foram derivadas por esse código ausente.
- **Por que importa:** é a base do numerador municipal. Sem o script, não dá para reproduzir a extração nem auditar como `COD_SUBF` e `EH_TOTAL` foram derivadas.
- **Encaminhamento:** recuperar o script (outra máquina? Guilherme?) ou reescrever um `Extract_SIOPE_Funcao.py` e conferir se reproduz os parquets atuais.

### T2. Brutos fora do repositório ✅ (contornado)
- **Situação:** os brutos (~35 GB) estão em `ENEM_Microdata_Analysis/data/raw`. Neste repositório, só a pasta do IDEB foi copiada.
- **Consequência:** os Transforms leem `data/interim` e funcionam. Para rodar de novo os outros Extracts, é preciso copiar a pasta bruta correspondente.
- **Decisão sobre o Git:** `data/raw` e `data/interim` ficam fora do Git (`.gitignore` na raiz, commit `e3153de`).

### T3. Scripts obsoletos ✅
- `Extract_IDEB.py` foi substituído pelo `Extract_SAEB.py`. Ele procura `data/raw` dentro de `src/Extract`, então não roda.
- `Transform_IDEB.py` e `ideb_transformado` se referem só ao Ensino Médio da fase ENEM.
- Nenhum dos três deve entrar no merge.

---

## 9. Para levar à orientadora

1. **C1:** IDHM com defasagem t−1.
2. **G4:** tratamento da ausência da 12.364 (RN e MS em 11 de 12 anos).
3. **S4:** manter Anos Finais na camada municipal, com a amostra selecionada?
4. **E3:** recorte geográfico (Brasil ou SP).
5. **M3 e S5:** confirmar os testes de sensibilidade (sem 2021, sem 2025 estadual).
6. **Integridade acadêmica:** o Manual exige informar e discutir previamente o uso de IA. Este registro e parte do código foram produzidos com apoio de IA, o que deve ser comunicado e documentado no Método.
