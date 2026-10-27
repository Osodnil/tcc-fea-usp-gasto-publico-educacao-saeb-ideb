# 02 — Fontes de dados, estruturas e achados

Cada seção traz: o que é, como acessar, estrutura, achados e limitações. As limitações marcadas com **[Método]** devem aparecer na seção de Método do TCC.

## 1. SIOPE (FNDE), gasto em educação

**Acesso (API OData "Olinda", sem chave):**
`https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/`

Padrão de chamada (o parâmetro de UF vai entre aspas simples):
`{BASE}{Entidade}(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta=2023&@Num_Peri=6&@Sig_UF='SP'&$format=json`

- Uma chamada por ano, bimestre e UF. A API não devolve o Brasil inteiro de uma vez. Paginação por `@odata.nextLink`.
- `Num_Peri` vai de 1 a 6. O **bimestre 6 é o acumulado do ano** (confirmado pelos valores: a despesa de educação de um município pequeno fecha em cerca de 22% da despesa total, compatível com o mínimo constitucional).
- Entidades que funcionam com esses três parâmetros: `Dados_Gerais_Siope`, `Despesas_Funcao_Educacao_Siope`, `Despesas_Siope`, `Indicadores_Siope`, `Receita_Siope`, `Informacoes_Complementares_Siope`, `Dados_Gerais_Siope_Dados_Responsaveis`. As entidades com `_` na frente dão erro 400; `Remuneracao_Siope` exige outro parâmetro.
- Camadas: `TIPO` = "Municipal" ou "Estadual". `COD_MUNI` tem **6 dígitos** e é nulo na camada estadual.
- **Disponibilidade:** de 2017 a 2025. De 2008 a 2016 a API devolve vazio.

**Entidade `Dados_Gerais_Siope`** (`siope_{ano}_extraido.parquet`, só `TIPO == "Municipal"`): colunas `NUM_ANO`, `COD_UF`, `SIG_UF`, `COD_MUNI`, `NOM_MUNI`, `NUM_POPU`, `VL_DESP_DOTA_ATUA_EDU`, `VL_DESP_EMPE_EDU`, `VL_DESP_LIQU_EDU`, `VL_DESP_PAGA_EDU`, `VAL_DESP_PAGA` (despesa total do município). Cobertura de 5.559 a 5.567 municípios por ano.

**Entidade `Despesas_Funcao_Educacao_Siope`** (`siope_funcao_{ano}_extraido.parquet`): uma linha por subfunção, com `DES_SUBF` (rótulo), `VAL_DESP_EMPE`, `VAL_DESP_LIQU` e `VAL_DESP_PAGA`. Colunas derivadas pelo script: `COD_SUBF` (primeiro número de 3 dígitos do rótulo) e `EH_TOTAL` (rótulo começa com "TOTAL").

### Achados
- **Subfunção 361 (Ensino Fundamental)** aparece em 5.541 a 5.563 municípios por ano e pesa entre 58,8% e 62,7% do gasto municipal em educação, sem quebra em 2021. A 362 (Ensino Médio) aparece em só 474 a 891 municípios por ano: prefeitura gasta pouco com Médio. Em SP 2023, 119 municípios declararam algo no Médio, R$ 165 milhões, contra R$ 9,7 bilhões do estado.
- **A despesa total em educação mistura etapas:** na camada municipal a Educação Infantil (365) pesa quase tanto quanto o Fundamental (SP 2023: R$ 30,1 bi contra R$ 32,2 bi). O Saeb não mede creche, por isso o numerador é a 361.
- **A linha "TOTAL 365" repete creche + pré-escola.** Somar tudo conta a Educação Infantil duas vezes.
- **Rótulos fora do padrão** ("Inativos", "SubFunção 361 - Fonte 01 ...", "SubFunção (122 + 361 + ...)", nomes sem código). Há 117 rótulos distintos de subfunção. Em SP 2017, um rótulo "SubFunção 361 - Fonte 01 - Aplic. 110" (R$ 146 mil) foi classificado como 361. Regra: usar só rótulos que comecem com o código. "Inativos" soma R$ 40,4 bi na camada estadual (38 linhas) e R$ 2,1 bi na municipal, acumulado em 2017–2025, valores nominais.
- **O SIOPE inclui previdência dentro do gasto em educação** (SP 2023, estadual: 361 = R$ 13,5 bi, subfunção 272 "Previdência do Regime Estatutário" = R$ 13,5 bi, 362 = R$ 9,7 bi).
- **O layout mudou em 2021.** Até 2020 aparecem linhas de programas e transferências (116 a 120: PDDE, PNAE, PNATE, convênios), a 098 e linhas sem código; merenda (306), transporte escolar (782) e administração (122) só aparecem como linhas próprias a partir de 2021. A participação da 361 não deu salto, então não há evidência de reclassificação.
- **Valores em reais correntes:** o gasto municipal na 361 vai de R$ 94,9 bi (2017) a R$ 223,1 bi (2025), com salto de 34% entre 2021 e 2022 (R$ 120,7 bi para R$ 161,2 bi). Deflacionar antes de comparar anos.
- **Valores marcados como provisórios:** o campo traz o texto "Valores sujeito alterações" em colunas fora das que usamos. Ao montar DataFrame de dicionários, usar `infer_schema_length=None`.
- **[Método] 41 linhas com despesa total zerada** (3 em 2017, 8 em 2018, 11 em 2019, 19 em 2020; nenhuma depois), tratadas como ausentes.
- **[Método] DF:** não existe como município no SIOPE (é `TIPO = "Estadual"`, sem `COD_MUNI`). Na entidade `Dados_Gerais_Siope`, o DF estadual falta em 2021, 2022, 2023 e 2025; na de subfunção aparece em todos os anos.
- **[Método] Camada estadual no SIOPE:** Minas Gerais só aparece em 2024 (em nenhum bimestre dos outros anos, nas duas entidades testadas). O Rio Grande do Sul declarou só os bimestres 1 e 2 em 2018 e nada em 2019; na `Dados_Gerais` só aparece em 2017, 2020 e 2024. Por isso a camada estadual usa o SICONFI.
- **[Método] Gasto estadual pelo SIOPE e pelo SICONFI diverge** (ver seção 2).

## 2. SICONFI / DCA (Tesouro Nacional), gasto estadual

**Acesso (API, sem chave):** `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca`
Parâmetros: `an_exercicio`, `id_ente` (UF com 2 dígitos, município com 7 dígitos do IBGE), `no_anexo = "DCA-Anexo I-E"` (despesas por função e subfunção). Paginação com `offset` e `hasMore` (até 5.000 itens por página).

Campos devolvidos: `exercicio`, `instituicao`, `cod_ibge`, `uf`, `anexo`, `rotulo`, `coluna`, `cod_conta`, `conta`, `valor`, `populacao`. `conta` vem como "12 - Educação" (total da função) ou "12.361 - Ensino Fundamental" (subfunção). `coluna` assume: Despesas Empenhadas, Despesas Liquidadas, **Despesas Pagas**, Inscrição de Restos a Pagar Processados e Não Processados. O `rotulo` é sempre "Total Geral da Despesa por Função".

**Arquivo:** `siconfi_estados_funcao12.parquet`, formato longo (`UF`, `ANO`, `CONTA`, `COLUNA`, `VALOR`, `SUBF`), 12.342 linhas, 27 UFs × 2014–2025. A DCA de SP existe a partir de 2014 (2013 vem vazia).

### Achados
- **Total da função 12 completo:** 27 UFs em todos os anos, sem erro de API.
- **Subfunções 361 e 362 incompletas:** só 18 UFs têm as duas em todos os 9 anos (2017–2025). Anos com 361: AC 9, AL 5, GO 7, MT 4, PI 8, PR 5, RS 1, SP 4, TO 2. Anos com 362: AC 6, AL 5, GO 8, MT 3, PI 8, RS 1, TO 2. Por isso a camada estadual usa o total da função, não as subfunções.
- **A função 12 inclui o Ensino Superior (12.364)**, que não entra no denominador nem no que o Saeb mede. Peso em 2023: PR 19,1%, SC 14,9%, BA 9,8%, SP 9,5%, CE 9,3%, PB 7,5%, MS 5,8%, RJ 4,6%, MG 4,3%, PE 3,6%; os demais ficam abaixo de 3%. Anos com 12.364 em 2017–2025: RO 0, AC 1, SE 1, RS 3, os outros 9. (RS tem universidade estadual; o zero provavelmente é classificação diferente, efeito pequeno diante do total.)
- **[Método] SICONFI e SIOPE não são intercambiáveis.** SP 2023, Médio pago: R$ 7,18 bi (SICONFI) contra R$ 9,67 bi (SIOPE). MG 2024, Fundamental: R$ 5,48 bi contra R$ 8,49 bi. Totais: RS 2024, R$ 6,35 bi contra R$ 11,65 bi; MG 2024, R$ 17,16 bi contra R$ 19,43 bi. Explicação plausível, não verificada: o SIOPE segue a contabilidade de gasto em educação (inclui, por exemplo, previdência de servidores) e o SICONFI segue só a função orçamentária 12.
- **[Método] Reconciliação no município, subfunção 361 paga, razão SICONFI/SIOPE:**
  - 40 municípios de 825 a 197.663 habitantes (2017, 2021, 2024): mediana 1,076; quartis 0,985 e 1,184; 28% dentro de ±5% e 72% dentro de ±20%. Mediana por ano: 1,12 (2017), 1,04 (2021), 1,05 (2024).
  - 30 maiores municípios: mediana 0,91; quartis 0,83 e 0,97; 79% dentro de ±20%. Mediana por ano: 0,87, 0,93, 0,90.
  - A razão é estável dentro de cada cidade (Belo Horizonte 0,86, 0,89, 0,90; Curitiba 0,92, 0,91, 0,95; Fortaleza 0,82, 0,79, 0,80), o que um efeito fixo de município absorve. Discordâncias persistentes: Rio de Janeiro (cerca de 0,65) e Porto Alegre (cerca de 0,55).
  - Anomalias em 2017: SICONFI de São Paulo igual a zero; São Luís 5,36; Salvador 0,42; Jaboatão dos Guararapes 0,26; Duque de Caxias 1,68. Não se sabe qual fonte está mais perto do gasto real.
- **Séries nominais a validar:** BA 6,05 → 10,72 bi e MG 10,83 → 14,60 bi de 2021 para 2022; quedas isoladas (DF 2023, PB e RR 2025). Parte é inflação e FUNDEB novo; não verificado.

## 3. Matrículas (Censo Escolar, INEP)

**Acesso:** microdados do Censo da Educação Básica, no portal do INEP, um pacote por ano. De 2015 a 2024, um arquivo `microdados_ed_basica_AAAA.csv` (separador `;`, uma linha por escola). **Em 2025** o INEP separou em tabelas (`Tabela_Escola`, `Tabela_Matricula`, `Tabela_Docente`, `Tabela_Turma`, `Tabela_Gestor_Escolar`, `Tabela_Curso_Tecnico`); as matrículas passam a vir na Tabela de Matrícula e a rede, na Tabela de Escola, ligadas por `CO_ENTIDADE`.

**Arquivo:** `censo_matriculas_{ano}.parquet` (2017–2025): `CO_MUNICIPIO` (7 dígitos), `SG_UF`, `REDE` (Federal, Estadual, Municipal, Privada, a partir de `TP_DEPENDENCIA` 1 a 4), `N_LINHAS`, `QT_MAT_BAS`, `QT_MAT_FUND`, `QT_MAT_FUND_AI`, `QT_MAT_FUND_AF`, `QT_MAT_MED`, `ANO`.

Matrículas nacionais por rede (milhões):

| Ano | BAS Est. | BAS Mun. | FUND Est. | FUND Mun. | AI Est. | AI Mun. | AF Est. | AF Mun. | MED Est. |
|---|---|---|---|---|---|---|---|---|---|
| 2017 | 16,22 | 23,10 | 7,17 | 15,56 | 2,09 | 10,42 | 5,08 | 5,13 | 6,72 |
| 2018 | 15,95 | 23,10 | 7,06 | 15,43 | 2,03 | 10,28 | 5,03 | 5,14 | 6,53 |
| 2019 | 15,31 | 23,03 | 6,92 | 15,26 | 1,97 | 10,16 | 4,95 | 5,10 | 6,27 |
| 2020 | 15,20 | 22,90 | 6,84 | 15,21 | 1,89 | 10,08 | 4,94 | 5,13 | 6,35 |
| 2021 | 15,02 | 23,14 | 6,61 | 15,47 | 1,80 | 10,11 | 4,80 | 5,36 | 6,56 |
| 2022 | 14,76 | 23,24 | 6,46 | 15,37 | 1,71 | 10,08 | 4,75 | 5,29 | 6,62 |
| 2023 | 14,18 | 23,32 | 6,22 | 15,17 | 1,61 | 10,03 | 4,61 | 5,14 | 6,42 |
| 2024 | 14,05 | 23,13 | 6,05 | 15,13 | 1,54 | 10,11 | 4,52 | 5,02 | 6,48 |
| 2025 | 13,33 | 23,06 | 5,87 | 15,15 | 1,48 | 10,21 | 4,39 | 4,94 | 6,05 |

(MED Mun. fica em 0,04 a 0,05 milhão em todos os anos.)

### Achados
- **O Médio municipal é irrelevante** (0,04 milhão de alunos). A rede municipal concentra os Anos Iniciais (cerca de 87% da rede pública em 2025) e divide os Anos Finais com a estadual.
- **[Método] `QT_MAT_MED` continua sendo o total em 2025:** na rede estadual, 4,720 (propedêutico) + 0,027 (magistério) + 0,901 + 0,399 (formação técnica) = 6,047 milhões, mesma identidade de 2023 e 2024. A queda de 6,48 para 6,05 milhões (−6,6%) não é mudança de definição, mas é a maior de toda a série; tratar com cautela.
- **[Método] Em 2025, 35.426 de 214.192 escolas (16,5%) não têm linha na Tabela de Matrícula.** Proporção igual à das escolas sem matrícula em 2024 (12% estaduais, 17% municipais, 19% privadas, nos dois anos), então tratar como zero é coerente.
- Nos dicionários, `QT_MAT_BAS`, `QT_MAT_FUND`, `QT_MAT_FUND_AI`, `QT_MAT_FUND_AF` e `QT_MAT_MED` existem em 2019, 2023 e 2025.

## 4. Saeb / IDEB (INEP), desfecho

**Acesso:** portal do Ideb no Inep, https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb, seção de resultados 2025. Nomes dos arquivos: `divulgacao_ensino_medio_municipios_2025`, `divulgacao_anos_iniciais_municipios_2025`, `divulgacao_anos_finais_municipios_2025`, `divulgacao_regioes_ufs_ideb_2025` (abas AI, AF e EM). Há ainda `divulgacao_brasil_Ensino_Medio_integrado_ideb_2025`, que não serve (só Ensino Médio integrado, nacional). A nota informativa do Ideb 2025 está em https://download.inep.gov.br/ideb/resultados/nota_informativa_ideb_2025.pdf.

**Estrutura dos arquivos municipais:** uma aba; linhas 0 a 6 são títulos e cabeçalhos descritivos; a **linha de índice 7 traz os nomes técnicos**; os dados começam na linha 8. Identificadores: `SG_UF`, `CO_MUNICIPIO` (7 dígitos), `NO_MUNICIPIO`, `REDE` (Estadual, Federal, Municipal, **Pública**, que é o agregado). Métricas com sufixo de ano: `VL_NOTA_MATEMATICA`, `VL_NOTA_PORTUGUES` (pontos da escala Saeb), `VL_NOTA_MEDIA` (nota média padronizada N, escala 0 a 10, que entra no IDEB = N × P), `VL_INDICADOR_REND` (P, rendimento), `VL_OBSERVADO` (IDEB), `VL_APROVACAO_*` (por série), `VL_PROJECAO`. '-' e 'ND' significam resultado não divulgado e viram nulo. No Médio municipal os anos são 2017, 2019, 2021, 2023 e 2025. Os arquivos de Anos Iniciais e Finais devem ter a mesma estrutura, mas ainda não foram abertos.

**Estrutura do arquivo de UFs:** abas "UF e Regiões (AI)", "(AF)" e "(EM)", série 2005–2025 (11 edições). Cabeçalho técnico também na linha de índice 7. As **duas primeiras colunas (Região/UF e Rede) não têm nome técnico**, e os rótulos trazem notas de rodapé, como "Privada (1)" e "Total (3)(4)". Três UFs aparecem abreviadas: "M. G. do Sul", "R. G. do Norte" e "R. G. do Sul". Não há linha do Brasil nem rede Municipal; redes presentes: Total, Pública, Privada, Estadual (AI e AF) e Total, Privada, Estadual (EM). Na aba AI, `VL_INDICADOR_REND` só vai até 2023.

**Arquivos:** `saeb_municipios_EM.parquet` (58.760 linhas, 5.563 municípios, 2017–2025) e `saeb_ufs_{AI,AF,EM}.parquet` (formato longo, uma linha por entidade × rede × ano; 1.276 linhas em AI e AF com 29 entidades; 957 no EM). **A versão atual dos parquets de UF tem só 24 UFs** (o mapa de nomes não reconhecia as três abreviadas); o `Extract_Saeb.py` corrigido ainda não foi rodado.

### Achados
- **Validação:** no Médio, 5.428 municípios têm IDEB 2025 na rede Pública, exatamente o número da nota informativa do Inep. Para AI e AF os números esperados são 5.478 e 5.491.
- **[Método] 2021 tem muito menos observações com nota:** 6.827 linhas município × rede contra 9.742 (2019) e 10.314 (2023), cerca de 30% a 34% a menos no Médio. É compatível com o critério de participação mais rígido daquele ano, mas a causa não foi verificada. O rendimento tem 11 mil linhas em todos os anos porque vem do Censo Escolar.
- **[Método] Critérios de divulgação:** a escola precisa de pelo menos 10 estudantes e 80% de participação; o município, 10 estudantes e 50% (o critério municipal mudou entre 2021 e 2022). Municípios pequenos ou com baixa participação ficam sem resultado; isso não é aleatório.
- **[Método] O IDEB nulo concentra-se onde a rede é rara:** no IDEB do Médio, 68% dos valores da rede Federal, 53% da Municipal e 14% da Estadual são nulos, o que reflete a divisão constitucional (estados oferecem o Ensino Médio). Nulo significa ausência de dado, não desempenho zero.
- **Cobertura:** IDEB da rede pública em 2025: 5.478 municípios (AI), 5.491 (AF) e 5.428 (EM).

## 5. IPCA (IBGE, SIDRA), deflator

**Acesso:** `https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all?formato=json` (tabela 1737, variável 2266: IPCA número-índice, base dezembro de 1993 = 100). A resposta traz uma linha de cabeçalho e uma por mês; a ordem das dimensões varia, então o script acha a coluna do mês pelo cabeçalho.

**Arquivo:** `ipca_deflator_anual.parquet`, 2013–2025. Deflator usa a **média anual do índice** (o gasto é um fluxo ao longo do ano) e a base é a média de 2025: `valor em reais de 2025 = valor nominal × FATOR_PARA_BASE`.

| Ano | Fator | IPCA dez/dez (%) |
|---|---|---|
| 2013 | 1,9637 | 5,91 |
| 2014 | 1,8468 | 6,41 |
| 2015 | 1,6939 | 10,67 |
| 2016 | 1,5577 | 6,29 |
| 2017 | 1,5059 | 2,95 |
| 2018 | 1,4526 | 3,75 |
| 2019 | 1,4003 | 4,31 |
| 2020 | 1,3568 | 4,52 |
| 2021 | 1,2528 | 10,06 |
| 2022 | 1,1464 | 5,79 |
| 2023 | 1,0960 | 4,62 |
| 2024 | 1,0502 | 4,83 |
| 2025 | 1,0000 | 4,26 |

## 6. Fontes de contexto e controles

- **Alfabetização municipal (IBGE, Censo 2022, "Agregados por Municípios"):** `ibge_transformado.parquet`, 5.570 municípios, sem nulos. `TAXA_ALFABETIZACAO_15MAIS = V00900 / (V00900 + V00901)` ("15 anos ou mais, sabe ler e escrever" e "não sabe"). Foto estática de 2022 (sem coluna de ano). Os arquivos de renda não foram baixados.
- **IDHM por UF (Radar IDHM, PNUD/Ipea/FJP):** série anual 2015–2024 (IDHM e componentes Educação, Longevidade e Renda), calculada com a PNAD Contínua; só existe por UF, porque a amostra não permite município. O IDHM municipal clássico é decenal (Censo, 2010). `idhm_transformado.parquet`: 280 linhas (28 territórios × 10 anos).
- **Infraestrutura escolar (Censo Escolar):** `censo_escolar_transformado.parquet`, proporção de escolas com biblioteca, laboratórios, internet, banheiro, água potável, energia e quadra, por município × rede × ano. A cobertura básica quase dobrou na década (banheiro e água potável: 52% na média 2015–2025 e 97% em 2025; internet: 68% para 95%).

## 7. Fontes herdadas do ENEM (descartado como desfecho)

- Microdados do ENEM 2013–2023, `enem_{ano}_extraido.parquet`; linhas por ano: 2013 7.173.563; 2014 8.722.248; 2015 7.746.427; 2016 8.627.179; 2017 6.731.278; 2018 5.513.733; 2019 5.095.171; 2020 5.783.109; 2021 3.389.832; 2022 3.476.105; 2023 3.933.955.
- **[Método] `CO_ESCOLA` não existe nos microdados públicos** (decisão permanente do INEP, LGPD).
- **[Método] Só 15,6% a 27,4% dos inscritos têm escola vinculada** (2013: 22,8%; 2014: 20,2%; 2015: 21,3%; 2016: 21,8%; 2017: 26,5%; 2018: 26,3%; 2019: 22,5%; 2020: 15,6%; 2021: 24,0%; 2022: 27,4%; 2023: 24,4%). Indicadores por escola ou município descrevem essa subpopulação.
- **[Método] 2024 e 2025:** arquivos de participantes e resultados sem chave em comum.
- **Redação:** em 2013–2015, quem faltou tem nota 0 (nos demais anos, vazio). `IN_TREINEIRO` só existe a partir de 2015; treineiros pesam de 7,7% a 15,8% dos inscritos e nunca têm escola vinculada.
- Série do Medium de Leonardo Sales (ENEM 2022): citar como literatura cinzenta.

## 8. Chaves de integração

- **Município:** código do IBGE com 7 dígitos (`CO_MUNICIPIO`). O SIOPE usa 6 (`COD_MUNI`).
- **Conversão 6 → 7 dígitos:** pesos 1, 2, 1, 2, 1, 2 nos seis dígitos; somar os algarismos de cada produto; verificador = (10 − soma mod 10) mod 10; anexar ao final. Conferido: 310620 → 3106200 (Belo Horizonte); 355030 → 3550308 (São Paulo); 352950 → 3529500.
- **UF:** sigla de 2 letras. Mapa de nome por extenso para sigla em `Transform_IDHM.py` e `Extract_Saeb.py`. Códigos numéricos de UF: RO 11, AC 12, AM 13, RR 14, PA 15, AP 16, TO 17, MA 21, PI 22, CE 23, RN 24, PB 25, PE 26, AL 27, SE 28, BA 29, MG 31, ES 32, RJ 33, SP 35, PR 41, SC 42, RS 43, MS 50, MT 51, GO 52, DF 53.
- **Rede:** `TP_DEPENDENCIA` do Censo (1 Federal, 2 Estadual, 3 Municipal, 4 Privada) e `REDE` do IDEB (Estadual, Federal, Municipal, Pública). Não somar linhas "Pública" com as redes específicas.
- **Ano:** gasto anual (2017–2025, SICONFI estadual desde 2014) e Saeb bienal (2017, 2019, 2021, 2023, 2025).

## 9. Limitações para o Método (resumo)

1. SIOPE sem MG (exceto 2024) e com RS parcial na camada estadual; por isso a camada estadual usa o SICONFI.
2. SIOPE e SICONFI discordam; cada camada usa uma única fonte.
3. Gasto em reais correntes; deflacionado para 2025 pela média anual do IPCA.
4. SIOPE só desde 2017: defasagens longas limitadas (4 anos só para IDEB de 2021 em diante).
5. Saeb: 2021 com muito menos observações; municípios pequenos ou com baixa participação ficam sem resultado.
6. Camada estadual com 27 unidades: poucas observações independentes.
7. Subfunção 361 não separa Anos Iniciais de Finais; o mesmo numerador serve aos dois desfechos.
8. DF fora da camada municipal.
9. Matrículas do Médio estadual caem 6,6% em 2025 (não é mudança de definição).
10. Associação, não causalidade (efeitos de FUNDEB e complementação da União podem inverter a relação).
