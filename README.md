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

**3. Painéis e dashboard**

| Script | Saída |
|---|---|
| `Transform/Montar_Paineis.py` | `data/processed/painel_municipal.parquet` e `painel_estadual.parquet` |
| `Visualizacao/Gerar_Dashboard_HTML.py` | `relatorios/dashboard_conferencia.html` |

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
- **`dashboard_conferencia.html`:** página única que abre offline em qualquer navegador. Mostra a dispersão gasto × nota, a evolução 2017–2025, o ranking por UF, a cobertura e uma tabela detalhada. É apenas descritiva.

## Situação atual

- ✅ Extração, tratamento e painéis concluídos e validados.
- ✅ Dashboard HTML de conferência.
- ✅ Decisões da reunião de 23/10/2026 aplicadas: IDHM do mesmo ano (2025 sem IDHM, como limitação) e outliers mantidos.
- 🟡 Pendentes com a orientadora (seção 9 de `docs/decisoes_metodo.md`): desenho dos clusters, IDHM Renda × IDHM total, medida principal de desempenho, seleção da amostra, ausência da 12.364, escopo e testes de sensibilidade.
- ⏳ Análise exploratória, análise de clusters, estimações, dashboard final em Power BI e acesso simples ao projeto (QR Code).

As limitações do trabalho estão consolidadas na seção 10 de `docs/decisoes_metodo.md`.

## Uso de IA

Parte do código e da documentação foi desenvolvida com apoio de um assistente de IA (Claude, da Anthropic). Conforme o Manual de TCC, esse uso deve ser informado e discutido previamente com a orientadora e documentado na seção de Método. As decisões de método são dos autores e estão registradas em `docs/decisoes_metodo.md`.
