// Power Query (M): carregamento das tabelas de data/processed/powerbi.
// 1) Página Inicial > Transformar dados > Gerenciar parâmetros > Novo parâmetro:
//    Nome = PastaDados, Tipo = Texto, Valor atual = caminho completo da pasta data\processed\powerbi
//    (ex.: C:\Users\...\tcc-fea-usp-gasto-publico-educacao-saeb-ideb\data\processed\powerbi).
//    Quem abrir o .pbix em outra máquina só troca esse parâmetro.
// 2) Para cada tabela: Nova fonte > Consulta nula > Editor avançado, colar o bloco abaixo e trocar o nome do arquivo.
//    O nome da consulta deve ser igual ao do arquivo (dim_municipio, fato_desempenho_municipal, ...).

let
    Fonte = Parquet.Document ( File.Contents ( PastaDados & "\dim_municipio.parquet" ) )
in
    Fonte

// Tabelas (12): dim_municipio, dim_uf, dim_cluster, dim_ano, dim_etapa, dim_disciplina, dim_defasagem,
// dim_modelo, fato_desempenho_municipal, fato_gasto_municipal, fato_desempenho_estadual, fato_gasto_estadual.
// Nenhuma transformação é feita no Power Query: tudo vem pronto de src/Visualizacao/Preparar_PowerBI.py.
// Conferir só os tipos: códigos (CO_MUNICIPIO, SG_UF, ETAPA, DISCIPLINA) como Texto; ANO, CLUSTER e
// DEFASAGEM como Número inteiro; marcas (SALTO_ATIPICO, GASTO_EXTREMO...) como Verdadeiro/Falso.
