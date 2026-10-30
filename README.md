# Gasto público em educação e desempenho no Saeb

Trabalho de Conclusão de Curso em Administração (FEA/USP, EAD 600/601), no formato de consultoria. Autores: Henrique Lindoso e Guilherme.

**Pergunta central:** o gasto público por aluno em educação, deflacionado, se associa ao desempenho no Saeb/IDEB? Com que defasagem? Quais municípios e estados entregam mais ou menos do que o esperado, dado o gasto e o contexto?

**Usuário-alvo:** gestor de secretaria de educação.

**Fluxo:** Dados → ETL → Análise → Indicadores → Insights → Dashboard → Avaliação.

> Os resultados são de **associação e eficiência relativa**, não de causalidade.

## Desenho

A análise tem duas camadas, que nunca são misturadas:

| | Camada municipal | Camada estadual |
|---|---|---|
| Gasto | SIOPE, subfunção 361 (Ensino Fundamental), despesa paga | SICONFI (DCA Anexo I-E), função 12 paga − 12.364 (Ensino Superior) |
| Denominador | Matrículas do Fundamental, rede municipal | Matrículas da educação básica, rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais, rede municipal | Saeb Anos Finais e Ensino Médio, rede estadual |
| Unidades | ~5.500 municípios | 27 UFs |

- **Janela:** 2017–2025, com as edições bienais do Saeb (2017, 2019, 2021, 2023 e 2025).
- **Valores:** reais de 2025, corrigidos pelo IPCA médio anual.
- **Decisões:** todas as decisões de método, com os problemas encontrados em cada base, estão em [`docs/decisoes_metodo.md`](docs/decisoes_metodo.md). A versão curta para as reuniões está em [`docs/resumo_reuniao_orientadora.md`](docs/resumo_reuniao_orientadora.md).

## Estrutura do repositório

```
data/
  raw/          brutos baixados manualmente (fora do Git)
  interim/      saídas intermediárias em Parquet (fora do Git)
    diagnosticos/   saídas de testes e conferências
  processed/    painéis finais (versionados)
docs/           registro de decisões e resumo para a orientadora
  historico/    dossiê das conversas anteriores ao repositório (desatualizado; só registro)
relatorios/     dashboard HTML de conferência (versionado)
src/
  Extract/      extração de cada fonte → data/interim
  Transform/    tratamento de cada base e montagem dos painéis
  Visualizacao/ gerador do dashboard HTML
  Exportacao/   gerador do pacote ZIP para envio (dashboard, documentos em HTML, dados em Excel e código)
  Testes/       scripts de reconhecimento e diagnóstico (não fazem parte do pipeline)
  Legado/       scripts da fase ENEM e do IDEB antigo, substituídos (não rodar)
run_pipeline.py executa o pipeline na ordem certa
requirements.txt
```

Os scripts localizam a raiz do projeto subindo até a pasta `.git`, então podem ser executados de qualquer diretório.

## Fontes de dados

| Base | Origem | Como obter |
|---|---|---|
| SIOPE (gasto municipal) | FNDE, API OData `DADOS_ABERTOS_SIOPE` (`Dados_Gerais_Siope` e `Despesas_Funcao_Educacao_Siope`) | Automático pelos scripts |
| SICONFI (gasto estadual) | Tesouro Nacional, API `apidatalake.tesouro.gov.br`, DCA Anexo I-E | Automático pelos scripts |
| IPCA | IBGE/SIDRA, tabela 1737 | Automático pelos scripts |
| Saeb/IDEB | Inep, planilhas de divulgação do IDEB 2025 (municípios: AI, AF e EM; regiões e UFs) — [página de resultados](https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados) | Manual, em `data/raw/IDEB - Índice de Desenvolvimento da Educação Básica/` |
| Censo Escolar | Inep, microdados 2015–2025 — [dados abertos](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar) | Manual, em `data/raw/Microdados Censo Escolar/<ano>/` |
| Censo Demográfico 2022 | IBGE, planilhas `Municípios.xlsx` e `Alfabetização.xlsx` | Manual, em `data/raw/Censo/Dados/` |
| Malha Municipal 2025 | IBGE, shapefile `BR_Municipios_2025` — [malhas territoriais](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html) | Manual, em `data/raw/Malha Municipal/` |
| IDHM por UF | Atlas Brasil / Radar IDHM (PNUD, FJP, IBGE), série 2015–2024 — [consulta](https://atlasbrasil.org.br/consulta) | Manual, em `data/raw/IDHM/` |

As fontes manuais somam cerca de 35 GB, quase tudo dos microdados do Censo Escolar. Os extratores esperam esta organização em `data/raw/`:

```
data/raw/
  Censo/Dados/Municípios.xlsx
  Censo/Dados/Alfabetização.xlsx
  IDHM/<planilha do Atlas Brasil>.xlsx
  Microdados Censo Escolar/<ano>/.../dados/*.csv          (2015 a 2025, como vêm do Inep)
  IDEB - Índice de Desenvolvimento da Educação Básica/
    Municípios/divulgacao_{anos_iniciais,anos_finais,ensino_medio}_municipios_2025/*.xlsx
    Regiões/divulgacao_regioes_ufs_ideb_2025/*.xlsx
```

> Hoje os brutos completos estão só na máquina do Henrique, no repositório anterior (`ENEM_Microdata_Analysis/data/raw`). Neste repositório há apenas a pasta do IDEB. Para rodar de novo a extração, copie as pastas acima para `data/raw/`.

## Ambiente

- Python 3.12 (Anaconda). O desenvolvimento foi feito em Windows e PowerShell.
- Pacotes usados: `polars` (≥ 1.44), `requests`, `fastexcel` (leitura de `.xlsx` pelo Polars) e `xlsxwriter` (só em um script de teste).

```bash
python -m pip install -r requirements.txt
```

## Como reproduzir

O `run_pipeline.py` roda os scripts na ordem certa, para no primeiro erro e diz de onde retomar:

```bash
python run_pipeline.py
```

Sem argumentos, ele faz o tratamento, os painéis e o dashboard a partir de `data/interim` (alguns segundos). As outras opções:

| Opção | O que faz |
|---|---|
| `--com-extracao` | Inclui a extração. Precisa dos brutos em `data/raw` e de internet; leva vários minutos. O script confere os brutos antes de começar. |
| `--a-partir-de Montar_Paineis` | Retoma a partir de um script. |
| `--listar` | Só mostra a ordem. |

Para rodar um script isolado, chame-o diretamente, por exemplo `python src/Transform/Transform_SIOPE.py`. A ordem completa é esta:

**1. Extração** (`src/Extract/` → `data/interim/`)

| Script | Saída |
|---|---|
| `Extract_IPCA.py` | `ipca_deflator_anual` |
| `Extract_IBGE.py` | `ibge_censo_municipios_extraido` |
| `Extract_IDHM.py` | `idhm_extraido` |
| `Extract_SIOPE.py` | `siope_{ano}_extraido` (dados gerais, 2017–2025) |
| `Extract_SIOPE_Funcao.py` | `siope_funcao_{ano}_extraido` (gasto por subfunção) |
| `Extract_SICONFI_Estados.py` | `siconfi_estados_funcao12` (2014–2025) |
| `Extract_Censo_Escolar.py` | `censo_escolar_{ano}_extraido` (infraestrutura por escola) |
| `Extract_Censo_Matriculas.py` | `censo_matriculas_{ano}` (2017–2025) |
| `Extract_SAEB.py` | `saeb_municipios_{AI,AF,EM}`, `saeb_ufs_{AI,AF,EM}` |

**2. Tratamento** (`src/Transform/`)

| Script | Saída |
|---|---|
| `Transform_IBGE.py` | `ibge_transformado` |
| `Transform_IDHM.py` | `idhm_transformado` (série 2015–2024) |
| `Transform_SAEB.py` | `saeb_{municipal,estadual}_transformado` |
| `Transform_Matriculas.py` | `matriculas_{municipal,estadual}_transformado` |
| `Transform_Infraestrutura.py` | `censo_escolar_transformado` |
| `Transform_SIOPE.py` | `siope_municipal_transformado` (precisa de IBGE, matrículas e IPCA) |
| `Transform_SICONFI.py` | `siconfi_estadual_transformado` (versões A e B do gasto) |

**3. Painéis, análise e dashboards**

| Script | Saída |
|---|---|
| `Transform/Montar_Paineis.py` | `data/processed/painel_municipal.parquet` e `painel_estadual.parquet`, mais as tabelas de apoio |
| `Analise/Analise_Clusters.py` | `data/processed/cluster_municipio.parquet` e `cluster_resumo.parquet` (7 grupos por contexto) |
| `Analise/Eficiencia.py` | `data/processed/eficiencia_municipal.parquet` (indicador de eficiência e marca de salto atípico) |
| `Visualizacao/Preparar_PowerBI.py` | `data/processed/powerbi/` (modelo em estrela do dashboard oficial) |
| `Visualizacao/Gerar_Dashboard_HTML.py` | `relatorios/dashboard_conferencia.html` |

O modelo do dashboard em Power BI é criado uma única vez por `src/Visualizacao/Gerar_Modelo_PowerBI.py`, dentro do projeto `powerbi/tcc_gasto_saeb.pbip`; o passo a passo está em `powerbi/roteiro_construcao.md`.

Use o Python do Anaconda (`%USERPROFILE%\anaconda3\python.exe`); na máquina de desenvolvimento, o `python` do terminal aponta para outra instalação (ver T6 no registro).

Cada script imprime um resumo com contagens e validações, como chave única, cobertura por ano e valores fora do esperado. Saídas maiores vão para `data/interim/diagnosticos/`.

**Quem só vai usar os resultados**, por exemplo no Power BI, não precisa rodar nada: os painéis em `data/processed/` e o dashboard em `relatorios/` estão versionados.

**Para enviar o projeto a quem não programa** (por exemplo, a orientadora), gere o pacote:

```bash
python src/Exportacao/Gerar_Pacote_Exportacao.py
```

Ele cria `exportacao/TCC_Gasto_Saeb_<data>.zip` (~13 MB) com o dashboard, os documentos convertidos para HTML (imprimíveis em PDF), os painéis em Excel com dicionário de colunas e em CSV, e uma cópia do código. A pasta `exportacao/` fica fora do Git.

## Saídas principais

- **`painel_municipal.parquet`:** uma linha por município × etapa (AI/AF) × edição do Saeb. Traz notas, IDEB, matrículas, gasto por aluno em R$ de 2025 no mesmo ano e com 1, 2 e 4 anos de defasagem (`_L0`, `_L1`, `_L2`, `_L4`), marca de gasto extremo e controles (alfabetização, população, região, IDHM da UF do mesmo ano, vazio em 2025, e infraestrutura).
- **`painel_estadual.parquet`:** uma linha por UF × etapa (AF/EM) × edição. Traz o gasto por aluno nas versões A e B (tratamento da ausência da subfunção 12.364), com as mesmas defasagens, e os controles por UF.
- **Tabelas de apoio** (`dim_municipio`, `dim_uf`, `gasto_municipal_anual`, `gasto_estadual_anual`): dimensões com porte e faixa de alfabetização, e gasto por aluno de todos os anos de 2017 a 2025. São a base comum do dashboard e do Power BI.
- **Clusters e eficiência:** `cluster_municipio` (grupo de contexto de cada município), `cluster_resumo` (perfil dos 7 grupos) e `eficiencia_municipal` (proficiência observada × esperada para o gasto e o contexto, por município, etapa, disciplina e edição; versão oficial nacional com IDHM, 2017–2023, e versão de robustez dentro da UF).
- **`powerbi/`:** as 12 tabelas do modelo em estrela que o `.pbix` lê (8 dimensões e 4 fatos). A especificação do dashboard, as medidas DAX, a consulta de carregamento e o tema estão na pasta `powerbi/` da raiz.
- **`malha_municipios.json` e `malha_municipios.topojson`:** contornos dos municípios (Malha Municipal do IBGE 2025) simplificados, com cerca de 0,7 MB (caminhos SVG, para o HTML) e 1,5 MB (TopoJSON, para o "Mapa de formas" do Power BI, chave `CD_MUN`). São gerados por `src/Visualizacao/Gerar_Malha.py` a partir do shapefile bruto (`data/raw/Malha Municipal/`) e só são refeitos com `run_pipeline.py --com-extracao`.
- **`dashboard_conferencia.html`:** ferramenta de análise numa página única, que abre offline em qualquer navegador. Tem seis abas:
  - **Visão geral:** dispersão gasto × nota, evolução, ranking por UF, cobertura e tabela.
  - **Defasagens:** gasto de 0, 1, 2 e 4 anos antes × nota, com a correlação de Spearman.
  - **Porte, região e contexto:** mapa de calor da nota por grupo e faixa de gasto.
  - **Mapa:** municípios (ou UFs) coloridos por gasto, desempenho ou posição em relação aos pares, com zoom por UF.
  - **Ficha:** de cada município ou UF, comparada com pares e com o Brasil.
  - **Pares (exploratória):** gasto e nota em relação ao grupo de contexto.

  Os filtros valem para todas as abas (camada, etapa, edição, medida de desempenho e UF). É apenas descritiva.

## Situação atual

- ✅ Extração, tratamento e painéis concluídos e validados.
- ✅ Dashboard HTML de conferência.
- ✅ Decisões de 23/10 e 30/10/2026 aplicadas: IDHM do mesmo ano, só Renda e Longevidade (2025 sem IDHM); outliers mantidos; proficiência em pontos como medida principal; versão A do gasto estadual; Brasil inteiro.
- ✅ Dashboard HTML ampliado como ferramenta de análise (6 abas, incluindo mapa).
- ✅ Clusters por contexto (7 grupos) e indicador de eficiência municipal (versão oficial nacional, com IDHM).
- ✅ Modelo de dados e especificação do dashboard oficial em Power BI (`powerbi/`).
- ⏳ Construção do `.pbix`, testes de sensibilidade e acesso simples ao projeto (QR Code).
- 🟡 Abertos (seção 9 de `docs/decisoes_metodo.md`): regra dos saltos atípicos, indicadores formais, formato do TCC, lista de sensibilidade e forma de documentar o uso de IA.

As limitações do trabalho estão consolidadas na seção 10 de `docs/decisoes_metodo.md`.

## Uso de IA

Parte do código e da documentação foi desenvolvida com apoio de um assistente de IA (Claude, da Anthropic). Conforme o Manual de TCC, esse uso deve ser informado e discutido previamente com a orientadora e documentado na seção de Método. As decisões de método são dos autores e estão registradas em `docs/decisoes_metodo.md`.
