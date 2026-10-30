# Roteiro de construção do dashboard (projeto `.pbip`)

*Passo a passo para montar o dashboard descrito em `especificacao_dashboard.md`. Siga as fases em ordem: cada uma termina com uma conferência, e só vale avançar quando ela passar. Os nomes dos menus seguem o Power BI Desktop em português.*

*O modelo de dados (tabelas, parâmetro, relações, ordenações e medidas) é gerado por script, `src/Visualizacao/Gerar_Modelo_PowerBI.py`. O relatório (páginas e visuais) é feito no Power BI. O caminho manual (`carregar_dados.pq` e `medidas.dax` colados à mão) fica como plano B, no fim deste roteiro.*

## Fase 0. Preparar o Power BI (10 min)

1. Atualize o Power BI Desktop.
2. **Arquivo > Opções e configurações > Opções > Global > Recursos em versão prévia:** marque **Visual de mapa de formas**. Se aparecerem, marque também **Salvar como projeto do Power BI (.pbip)** e **Armazenar modelo semântico no formato TMDL** (nas versões mais novas, esses dois já vêm ativos). Reinicie o Power BI.
3. **Opções > Global > Carregamento de dados:** desmarque **Data/hora automática para novos arquivos**.

## Fase 1. Criar o projeto e gerar o modelo (10 min)

1. No Power BI, **Arquivo > Novo** (relatório em branco) e **Arquivo > Salvar como**. No campo **Tipo** da janela de salvar, troque "Arquivos do Power BI (\*.pbix)" por **Arquivos de projeto do Power BI (\*.pbip)**. Escolha a pasta `powerbi\` do repositório e o nome `tcc_gasto_saeb`. O Power BI cria `tcc_gasto_saeb.pbip`, `tcc_gasto_saeb.Report\` e `tcc_gasto_saeb.SemanticModel\`. Se o tipo `.pbip` não aparecer, ative "Salvar como projeto do Power BI (.pbip)" em Recursos em versão prévia (Fase 0) e reinicie o Power BI.
2. **Feche o Power BI.**
3. No PowerShell, na raiz do repositório, rode o gerador com o Python do Anaconda (o `&` é obrigatório no PowerShell quando o caminho do programa vem entre aspas):

   ```powershell
   & "$env:USERPROFILE\anaconda3\python.exe" src\Visualizacao\Gerar_Modelo_PowerBI.py
   ```

   Ele confere as fórmulas antes de gravar, e a saída esperada é: *14 tabelas (12 importadas e 2 calculadas), 14 relações, 35 medidas, 7 ordenações*. O parâmetro `PastaDados` já sai apontando para `data\processed\powerbi` desta máquina.
4. Abra `powerbi\tcc_gasto_saeb.pbip`. Se aparecer uma faixa sobre alterações externas, aceite. Depois, **Página Inicial > Atualizar**: o modelo chega sem dados e é aí que o Power BI lê os Parquet.
5. **Se der erro ao abrir:** a mensagem diz o arquivo e a linha (por exemplo, `tables/_Medidas.tmdl`, linha 120). Me mande o texto exato do erro: eu corrijo o gerador, você roda de novo com `--forcar` e reabre.

**Conferência 1:** na exibição de Dados, o número de linhas no rodapé de cada tabela:

| Tabela | Linhas |
|---|---|
| dim_municipio | 5.571 |
| dim_uf | 27 |
| dim_cluster | 7 |
| dim_ano | 9 |
| dim_etapa | 3 |
| dim_disciplina | 2 |
| dim_defasagem | 4 |
| dim_modelo | 2 |
| fato_desempenho_municipal | 93.630 |
| fato_gasto_municipal | 50.113 |
| fato_desempenho_estadual | 540 |
| fato_gasto_estadual | 243 |

## Fase 2. Conferir o modelo e completar à mão (20 min)

1. **Exibição de modelo:** confira as 14 relações, todas **1:\*** e com filtro numa só direção:
   - `dim_uf[SG_UF]` → `dim_municipio`, `fato_desempenho_estadual`, `fato_gasto_estadual`
   - `dim_cluster[CLUSTER]` → `dim_municipio[CLUSTER]`
   - `dim_municipio[CO_MUNICIPIO]` → `fato_desempenho_municipal`, `fato_gasto_municipal`
   - `dim_ano[ANO]` → os quatro fatos
   - `dim_etapa[ETAPA]` e `dim_disciplina[DISCIPLINA]` → os dois fatos de desempenho
   - `dim_defasagem`, `dim_modelo`, `ref_municipio` e `_Medidas` ficam **sem relação**.
2. **O que já vem pronto (só conferir):**
   - medidas na tabela `_Medidas`, em pastas (`0 Parâmetros`, `1 Gasto` etc.), com formato e descrição;
   - rótulos ordenados (etapa, disciplina, defasagem, modelo, porte e cluster);
   - nenhuma coluna com soma automática;
   - chaves dos fatos ocultas.
3. **Parâmetro de campo para o mapa** (não dá para gerar por script com segurança): Modelagem > Novo parâmetro > Campos, com `Eficiência (pontos)`, `Proficiência média` e `Gasto das redes avaliadas (mediana)`. Nome: `Métrica do mapa`.
4. **Tema:** Exibir > Temas > Procurar temas > `powerbi/tema_tcc.json`.
5. **Salve.** A partir daqui, o Power BI é a fonte do modelo. Não rode o gerador de novo sem `--forcar`, que apagaria o que foi feito no Power BI (o próprio script recusa).

**Conferência 2 (a mais importante):** abra a **Exibição de consulta DAX** (ícone "DAX" na barra da esquerda), cole `powerbi/conferencia_modelo.dax` e execute. Cada bloco vira uma aba de resultado, com o valor esperado no comentário. A consulta também refaz a Conferência 1. Os valores têm de bater com os calculados no Python a partir das mesmas tabelas:

| Recorte | Medida | Esperado |
|---|---|---|
| Brasil, AI, MT, 2023 | Redes avaliadas | 5.243 |
| | Proficiência média | 220,21 |
| | Gasto das redes avaliadas (mediana), defasagem 0 | R$ 13.526 |
| | % acima do esperado (Oficial) | 46,3% |
| | Eficiência (pontos), Oficial | 0,0 |
| | IDEB médio | 5,79 |
| | Redes com salto atípico | 43 |
| | ρ de Spearman, defasagens 0 / 1 / 2 / 4 | 0,26 / 0,26 / 0,32 / 0,38 |
| Brasil, AF, MT, 2023 | Redes avaliadas | 3.196 |
| | Proficiência média | 249,28 |
| | Gasto das redes avaliadas (mediana) | R$ 12.540 |
| | ρ, defasagens 0 / 1 / 2 / 4 | 0,17 / 0,17 / 0,24 / 0,27 |
| AL, AI, MT, 2023 | Redes avaliadas | 100 |
| | Proficiência média | 222,41 |
| | % acima do esperado (Oficial) | 87,0% |
| | Eficiência (pontos), Oficial | +27,2 |
| Brasil, 2023 | Gasto por aluno (mediana anual) | R$ 13.721 |

Ibateguara (AL), AI, MT, para testar a ficha:

| Edição | Proficiência | Esperada | Eficiência | Percentil | Salto atípico |
|---|---|---|---|---|---|
| 2017 | 194,9 | 186,4 | +8,6 | 72 | não |
| 2019 | 202,8 | 193,9 | +8,9 | 71 | não |
| 2021 | 284,3 | 191,1 | +93,2 | 100 | **sim** |
| 2023 | 331,2 | 193,6 | +137,6 | 100 | não |
| 2025 | 345,1 | — (sem IDHM) | — | — | não |

Se algum valor não bater, pare e investigue antes de desenhar as páginas: quase sempre é uma relação faltando, com a direção errada ou com tipo de coluna diferente.

## Fase 3. Página-modelo (30 min)

1. **Formatar página > Tela:** 16:9, 1280 × 720.
2. Faixa do topo: título à esquerda e, numa linha, as segmentações **UF** (lista suspensa), **Etapa** (`NOME_ETAPA`, seleção única), **Disciplina** (`NOME_DISCIPLINA`, seleção única, padrão Matemática) e **Edição** (`dim_ano[ANO]`, filtrada para `EDICAO_SAEB = Verdadeiro`).
3. Um cartão de texto com a medida `Aviso de seleção` e outro com `Aviso do modelo`, em tinta discreta.
4. Duplique essa página para criar as demais. Depois, em **Exibir > Sincronizar segmentações**, sincronize as quatro segmentações em todas as páginas.

## Fase 4. Páginas, nesta ordem (1 a 2 dias)

**As páginas são geradas por script** (`src/Visualizacao/Gerar_Relatorio_PowerBI.py`), como o modelo. O fluxo para cada página nova:

1. Salvar e **fechar o Power BI**.
2. Se a página usar medidas novas, acrescentá-las ao modelo, que só adiciona e não altera nada:

   ```powershell
   & "$env:USERPROFILE\anaconda3\python.exe" src\Visualizacao\Gerar_Modelo_PowerBI.py --adicionar-medidas
   ```

3. Gerar as páginas. As que já existem não são tocadas; para regravar uma, use `--refazer <nome>`:

   ```powershell
   & "$env:USERPROFILE\anaconda3\python.exe" src\Visualizacao\Gerar_Relatorio_PowerBI.py
   ```

4. Abrir o `.pbip`, conferir e fazer os ajustes finos no próprio Power BI (cores condicionais, larguras de coluna).

As descrições abaixo continuam valendo como especificação de cada página e como plano B manual. A ordem prioriza o que responde à pergunta do TCC; cada página está descrita na seção 5 da especificação.

1. **Eficiência.** Seletor de `dim_modelo[ROTULO_MODELO]`; dispersão `Proficiência esperada` × `Proficiência média` com `dim_municipio[MUNICIPIO_UF]` em Valores e `CLUSTER_ROTULO` em Legenda; tabela-ranking com nome, cluster, proficiência, esperada, eficiência, percentil e salto atípico (ícone por formatação condicional).
2. **Ficha do município.** Em **Detalhamento**, arraste `dim_municipio[MUNICIPIO_UF]`. Gráfico de linhas por `ANO` com `Proficiência média`, `Proficiência mediana do cluster`, `Proficiência mediana da UF` e `Proficiência mediana do Brasil`; colunas com o gasto anual (`fato_gasto_municipal`); cartões com cluster, porte, `Faixa de eficiência` e `Aviso de salto atípico`. Teste com Ibateguara (AL).
3. **Pares.** Segmentação de `ref_municipio[REF_MUNICIPIO_UF]` (seleção única, com pesquisa); tabela de `dim_municipio[MUNICIPIO_UF]` com o filtro de visual `É par = 1`, mostrando gasto, proficiência e eficiência, ordenada pela eficiência. Deixe a Edição numa só (por exemplo, 2023).
4. **Início.** Os quatro cartões, a linha da proficiência por edição e o botão para a ficha.
5. **Mapa.** Visual **Mapa de formas**: em Local, `dim_municipio[CO_MUNICIPIO]`; em Saturação de cor, o parâmetro `Métrica do mapa`. Em Formatar > Configurações de mapa > Mapa personalizado, carregue `data/processed/malha_municipios.topojson`. Em "Exibir chaves do mapa", confira que as chaves são os códigos de 7 dígitos. Cores: divergente com centro 0 para eficiência e sequencial para as outras. Ative o zoom automático.
6. **Defasagens.** Colunas com `dim_defasagem[ROTULO_DEFASAGEM]` no eixo e `Correlação gasto × proficiência (Spearman)` como valor; pequenos múltiplos por `ANO`. Cartão com `Redes na correlação`.
7. **Contexto e clusters.** Tabela de `dim_cluster`; colunas de proficiência e gasto por `CLUSTER_ROTULO` e por `PORTE`.
8. **Estados.** Mesma lógica, com `fato_desempenho_estadual` e `fato_gasto_estadual`. As medidas estaduais além das três de `medidas.dax` entram conforme a necessidade.
9. **Sobre os dados.** Caixas de texto com fontes, indicadores (seção 4 da especificação), limitações e o QR Code (A7), que entra por último.

**Conferência 3:** repetir a tabela da Conferência 2 nas páginas finais e os três municípios de teste da especificação (seção 8). Depois, apagar a página provisória.

## Fase 5. Acabamento (meio dia)

- **Dicas de ferramenta:** em cada visual, adicione `Redes avaliadas` e, nas páginas de eficiência, `Percentil de eficiência`.
- **Títulos que dizem o achado**, por exemplo "Redes que gastam mais tendem a ter notas maiores, e a associação cresce com a defasagem", em vez de "Correlação por defasagem".
- **Formatação condicional** do salto atípico com ícone de aviso. A cor nunca deve ser a única pista.
- **Ordem de tabulação e texto alternativo** nos visuais principais (Formatar > Geral > Texto alternativo).
- **Teste de desempenho:** Exibir > Analisador de desempenho. Se a página de Defasagens passar de cerca de 2 s, aplicar o plano B da seção 7 da especificação.

## Fase 6. Publicar e gerar o acesso (A7)

1. **Publicar** no serviço com a conta USP.
2. Testar **Arquivo > Inserir > Publicar na Web**. Se a opção estiver bloqueada pelo administrador, seguir o plano B da especificação: HTML no GitHub Pages e o `.pbix` para download.
3. Gerar o QR Code apontando para o endereço público e incluí-lo na página "Sobre os dados".

## Fase 7. Versionar

- O projeto `.pbip` guarda o modelo em texto (TMDL) e o relatório em JSON (PBIR). Assim, o Git mostra o que mudou em cada medida ou página, o que conversa com o registro de decisões.
- Os dados em cache (`.pbi/cache.abf`) e as preferências locais (`.pbi/localSettings.json`) ficam fora do Git: os dados se refazem com Atualizar.
- Toda mudança de medida, filtro ou regra visual que altere um número entra em `docs/decisoes_metodo.md`.
- Para entregar um arquivo único (por exemplo, à orientadora), use **Arquivo > Salvar como > .pbix**: é uma cópia, e a fonte continua sendo o projeto.

## Plano B: modelo à mão

Se o modelo gerado não abrir e a correção demorar, monte o modelo à mão num relatório novo:

1. Crie o parâmetro `PastaDados` e as 12 consultas com o bloco de `carregar_dados.pq`.
2. Crie as relações da Fase 2.
3. Crie a tabela `_Medidas` (Inserir dados) e a tabela calculada `ref_municipio`, cuja fórmula está no comentário de `medidas.dax`.
4. Cole as medidas de `medidas.dax`. Os formatos estão na lista `FORMATOS` do gerador.
5. Ajuste as ordenações (lista `ORDENAR` do gerador), marque "Não resumir" e oculte as chaves dos fatos.
