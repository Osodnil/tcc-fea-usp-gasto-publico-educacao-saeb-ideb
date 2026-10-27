# 03 — Estado do pipeline (fonte da verdade)

Atualizado em 25/10/2026. Se algo nas instruções do projeto divergir deste arquivo, vale este.

## 1. Onde estamos

- **Etapa:** Extract quase concluído. O Transform das bases novas (gasto e Saeb) ainda não começou.
- **Pergunta central:** o gasto público por aluno em educação (SIOPE/SICONFI, em reais de 2025) se associa ao desempenho no Saeb/IDEB? Com que defasagem? Quais municípios e estados entregam mais ou menos do que o esperado, dado o gasto e o contexto?
- **Janela:** 2017–2025 (o SIOPE só tem dado a partir de 2017; o Saeb é bienal: 2017, 2019, 2021, 2023, 2025).
- **Bloqueios imediatos:**
  1. As planilhas municipais do IDEB de Anos Iniciais e Anos Finais ainda não foram baixadas.
  2. O `Extract_Saeb.py` corrigido (com o mapa de nomes de UF abreviados) ainda não foi rodado.
- **Decisão de escopo em aberto:** recorte geográfico (Brasil inteiro × São Paulo). A orientadora sugeriu SP; o resultado da reunião de 02/10 não foi registrado.

## 2. Extract por fonte

| Fonte | Uso no projeto | Cobertura | Arquivos em `data/interim/` | Status |
|---|---|---|---|---|
| SIOPE, entidade `Dados_Gerais_Siope` (municipal) | População (`NUM_POPU`) e gasto total em educação | 2017–2025, 5.559 a 5.567 municípios por ano | `siope_{ano}_extraido.parquet` | Extraído |
| SIOPE, entidade `Despesas_Funcao_Educacao_Siope` | **Numerador da camada municipal** (subfunção 361, paga) | 2017–2025, camadas Municipal e Estadual | `siope_funcao_{ano}_extraido.parquet` | Extraído |
| SICONFI, DCA Anexo I-E (estados) | **Numerador da camada estadual** (função 12 menos 12.364, paga) | 27 UFs × 2014–2025, formato longo | `siconfi_estados_funcao12.parquet` | Extraído (324 de 324 UF-anos) |
| Censo Escolar (matrículas) | **Denominadores** | 2017–2025, município × rede | `censo_matriculas_{ano}.parquet` | Extraído; 2015–2016 opcional, não rodado |
| IPCA (SIDRA, tabela 1737, variável 2266) | Deflator para reais de 2025 | 2013–2025 | `ipca_deflator_anual.parquet` | Extraído e conferido |
| Saeb/IDEB municipal, Ensino Médio | Desfecho (uso secundário) | 2017–2025, 5.563 municípios | `saeb_municipios_EM.parquet` | Extraído |
| Saeb/IDEB municipal, **Anos Iniciais** | **Desfecho principal da camada municipal** | A definir | `saeb_municipios_AI.parquet` | **Pendente: planilha não baixada** |
| Saeb/IDEB municipal, **Anos Finais** | Desfecho da camada municipal | A definir | `saeb_municipios_AF.parquet` | **Pendente: planilha não baixada** |
| Saeb/IDEB por UF (abas AI, AF, EM) | **Desfecho da camada estadual** | 2005–2025 | `saeb_ufs_{AI,AF,EM}.parquet` | Extraído **com erro**: só 24 UFs (faltam MS, RN, RS). Correção no script, falta rodar |

Fontes herdadas da fase ENEM (não são essenciais para a pergunta atual, mas continuam em disco e podem servir de controle):

| Fonte | Arquivos | Observação |
|---|---|---|
| ENEM 2013–2023 | `enem_{ano}_extraido.parquet` | Escopo descartado como desfecho (ver arquivo 01) |
| IDHM por UF (Radar IDHM) | `idhm_extraido.parquet`, `idhm_transformado.parquet` | Anual 2015–2024, formato longo, 280 linhas |
| IDEB Ensino Médio (só `VL_OBSERVADO`) | `ideb_ensino_medio_municipios_extraido.parquet`, `ideb_transformado.parquet` | Substituído pelo `saeb_municipios_EM.parquet`, que tem as notas |
| Censo Escolar, infraestrutura | `censo_escolar_{ano}_extraido.parquet`, `censo_escolar_transformado.parquet` | 2015–2025; 168.759 linhas agregadas por município × rede × ano |
| IBGE, Censo 2022 | `ibge_censo_municipios_extraido.parquet`, `ibge_transformado.parquet` | Taxa de alfabetização de 15 anos ou mais, estática, 5.570 municípios |
| Dicionário do Censo 2022 | `censo_dicionario_variaveis.parquet` e `.csv` | 1.411 variáveis |

Diagnósticos ficam em `data/interim/diagnosticos/`.

## 3. Pendências do Extract (em ordem)

1. **Baixar o IDEB municipal de Anos Iniciais e Anos Finais** no portal do Inep (https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb), seção "Municípios". Nomes esperados: `divulgacao_anos_iniciais_municipios_2025` e `divulgacao_anos_finais_municipios_2025`. Salvar em `data/raw/IDEB - Índice de Desenvolvimento da Educação Básica/Municípios/` e registrar URL, data de acesso e nome do arquivo no `Fonte.txt` da pasta.
2. **Rodar o `Extract_Saeb.py` corrigido** (inclui `ALIAS_UF` para "M. G. do Sul", "R. G. do Norte" e "R. G. do Sul"). Validar: 27 UFs por etapa; municípios com IDEB 2025 na rede Pública perto de 5.478 (AI) e 5.491 (AF), como na nota informativa do Inep de 2025 (no Médio deu exatamente 5.428).
3. **Opcional:** estender as matrículas para 2015–2016 (`ANO_INICIO = 2015` no `Extract_Censo_Matriculas.py`), útil para defasagens na camada estadual. Os arquivos brutos já estão em disco; ver avisos de coluna ausente.

## 4. Transform a fazer (especificação)

### 4.1 Camada municipal

- **Numerador:** `siope_funcao_{ano}_extraido.parquet`, `TIPO == "Municipal"`, linhas cujo rótulo `DES_SUBF` começa com "361" (regex `^\s*361\s*(-|$)`), somando `VAL_DESP_PAGA` por município e ano. Não usar `COD_SUBF` sozinho: o código de 3 dígitos é extraído do primeiro número do rótulo e erra em rótulos como "SubFunção (122 + 361 + 365 ...)". Ignorar linhas "TOTAL ...".
- **Código do município:** `COD_MUNI` vem com 6 dígitos; converter para 7 pelo dígito verificador do IBGE (ver arquivo 02, seção 8).
- **Denominador:** `censo_matriculas_{ano}.parquet`, `REDE == "Municipal"`, `QT_MAT_FUND`.
- **Deflação:** multiplicar o valor nominal por `FATOR_PARA_BASE` do ano (reais de 2025).
- **Gasto por aluno real** = `VAL_DESP_PAGA × FATOR_PARA_BASE ÷ QT_MAT_FUND`.
- **Sinalizar, sem corrigir:** matrícula zero ou muito baixa; gasto zero; saltos de um ano para o outro; 2017 (as fontes mais divergem nesse ano); municípios pequenos (razão SICONFI/SIOPE instável).
- **Desfecho:** `saeb_municipios_AI` (principal) e `saeb_municipios_AF`, `REDE == "Municipal"`. Métricas: `VL_NOTA_MEDIA` (nota padronizada N, de 0 a 10), `VL_NOTA_MATEMATICA` e `VL_NOTA_PORTUGUES` (pontos da escala Saeb); IDEB e rendimento como secundárias. Ausência é `null`, nunca zero.
- **Junção:** (`CO_MUNICIPIO` de 7 dígitos, `ANO`), com gasto defasado em t, t−1 e t−2. Defasagem de 4 anos só para IDEB de 2021 em diante.
- **Controles:** `TAXA_ALFABETIZACAO_15MAIS` (Censo 2022, estática); proporções de infraestrutura do Censo Escolar; população.
- **DF:** não existe como município no SIOPE; fica de fora desta camada.

### 4.2 Camada estadual

- **Numerador:** `siconfi_estados_funcao12.parquet`, `COLUNA == "Despesas Pagas"`; total da função 12 (`SUBF` nulo) menos a subfunção 364 (Ensino Superior; tratar como zero quando ausente).
- **Denominador:** `censo_matriculas`, `REDE == "Estadual"`, `QT_MAT_BAS` somado por UF.
- **Deflação:** igual à camada municipal.
- **Desfecho:** `saeb_ufs_AF` e `saeb_ufs_EM`, `NIVEL == "UF"`, `REDE == "Estadual"`.
- **Janela:** o gasto existe desde 2014 e as matrículas, por ora, desde 2017. O arquivo de UFs do Saeb tem 2005–2025; a comparabilidade do Médio antes de 2017 não foi verificada.
- **Escala:** 27 unidades. Erros-padrão agrupados por UF.

### 4.3 Painel e análise

- Efeitos fixos de município (e de UF na camada estadual) e de ano; erros agrupados.
- Testes de sensibilidade: sem 2021 (o Saeb de 2021 tem cerca de 30% menos observações com nota); troca de fonte de gasto numa amostra; exclusão de MG e RS na camada estadual, se necessário.
- Linguagem: associação e eficiência, nunca causalidade.
- Eficiência: resíduo da nota esperada dado gasto e contexto, por município.

## 5. Decisões pendentes

1. Recorte geográfico: Brasil inteiro ou São Paulo (sugestão da orientadora). Resultado da reunião de 02/10 não registrado.
2. Confirmação formal da divisão de fontes por camada: municipal com SIOPE 361; estadual com SICONFI função 12 menos 12.364. O usuário rodou os testes sem objeção, mas não confirmou por escrito.
3. Formato do TCC no Manual: método científico (estudo quantitativo) ou consultoria. Ver arquivo 04.
4. Reescrita das perguntas analíticas e dos indicadores formais pós-pivô, para validar com a orientadora.
5. Registro do uso de IA no TCC e alinhamento com a orientadora (exigência do Manual).

## 6. Como reproduzir (ordem dos scripts)

1. Extract: `Extract_SIOPE.py` (Dados_Gerais), `Extract_SIOPE_Funcao.py` (subfunções), `Extract_SICONFI_Estados.py`, `Extract_Censo_Matriculas.py`, `Extract_IPCA.py`, `Extract_Saeb.py`.
2. Fontes herdadas: `Extract_ENEM.py`, `Extract_IDHM.py`, `Extract_IDEB.py`, `Extract_Censo_Escolar.py`, `Extract_IBGE.py`.
3. Transform herdado (já rodado): `Transform_IDHM.py`, `Transform_IDEB.py`, `Transform_Censo_Escolar.py`, `Transform_IBGE.py`.
4. Transform novo: a escrever (seções 4.1 e 4.2).

## 7. Nomes de arquivos reais x sugeridos

Alguns scripts foram salvos com nomes diferentes dos sugeridos, e vários testes de diagnóstico estão soltos. Exemplos: o código de matrículas rodou como `Teste5_SIOPE.py`, a extração por subfunção como `Teste_SIOPE.py`, os testes do SICONFI como `Teste6_SINCOFI.py` e `Teste7_SINCOFI.py`. O `Teste9_GrandesMunicipios.py` importa funções do `Teste8_Reconciliacao.py` e precisa ficar na mesma pasta. O inventário de código (`CODIGO_PIPELINE.md`) mostra os nomes reais.
