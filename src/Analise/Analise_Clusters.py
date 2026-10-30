"""Clusters de municípios por contexto (decisão A6).

Agrupa os municípios só por variáveis de contexto, sem gasto nem nota, para depois comparar
gasto e desempenho dentro de cada grupo de pares. Variáveis (padronizadas):
- log10 da população (Censo 2022);
- taxa de alfabetização de 15 anos ou mais (Censo 2022);
- IDHM Renda e IDHM Longevidade da UF, média 2017-2023 (sem a dimensão Educação, decisão C1b);
- índice de infraestrutura da rede municipal: média das 8 proporções do Censo Escolar, 2017-2025.
Método: k-médias com k = 7 (escolha registrada em A6), semente fixa.
Saídas: data/processed/cluster_municipio.parquet e cluster_resumo.parquet;
diagnóstico da escolha de k em data/interim/diagnosticos/clusters_escolha_k.csv.
"""
import os
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")  # evita aviso do joblib no Windows

import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
INTERIM_DIR = BASE_DIR / "data" / "interim"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DIAG_DIR = INTERIM_DIR / "diagnosticos"

K = 7
SEMENTE = 42
VARIAVEIS = ["LOG_POP", "TAXA_ALFABETIZACAO_15MAIS", "IDHM_RENDA", "IDHM_LONGEVIDADE", "INFRA"]
INFRA = ["PROP_IN_BIBLIOTECA", "PROP_IN_LABORATORIO_INFORMATICA", "PROP_IN_LABORATORIO_CIENCIAS", "PROP_IN_INTERNET",
         "PROP_IN_BANHEIRO", "PROP_IN_AGUA_POTAVEL", "PROP_IN_ENERGIA_REDE_PUBLICA", "PROP_IN_QUADRA_ESPORTES"]


def contexto() -> pl.DataFrame:
    dim = pl.read_parquet(PROCESSED_DIR / "dim_municipio.parquet")
    infra = (
        pl.read_parquet(INTERIM_DIR / "censo_escolar_transformado.parquet")
        .filter((pl.col("REDE") == "Municipal") & pl.col("ANO").is_between(2017, 2025))
        .group_by("CO_MUNICIPIO").agg(pl.mean_horizontal(INFRA).mean().alias("INFRA"))
    )
    idhm = (
        pl.read_parquet(INTERIM_DIR / "idhm_transformado.parquet")
        .filter(pl.col("SG_UF").is_not_null() & pl.col("ANO").is_between(2017, 2023))
        .group_by("SG_UF").agg(pl.col("IDHM_RENDA").mean(), pl.col("IDHM_LONGEVIDADE").mean())
    )
    return (
        dim.join(infra, on="CO_MUNICIPIO", how="left").join(idhm, on="SG_UF", how="left")
        .with_columns(pl.col("POPULACAO_TOTAL_CENSO").log10().alias("LOG_POP"))
    )


def rotular(resumo: pl.DataFrame, alfab_municipios: pl.Series) -> pl.DataFrame:
    """Rótulo descritivo a partir do perfil médio do grupo (região predominante, porte, alfabetização).

    A alfabetização é classificada pelos terços nacionais dos municípios (mesmo critério da faixa
    de alfabetização da dimensão), e não pela posição entre os grupos.
    """
    def porte(p: float) -> str:
        return "pequenos" if p < 10_000 else "médios" if p < 50_000 else "grandes"
    t1, t2 = alfab_municipios.quantile(1 / 3), alfab_municipios.quantile(2 / 3)
    # região: a predominante, ou as duas principais quando a primeira tem menos de 60% dos municípios
    regiao = lambda r: r["REGIAO_PREDOMINANTE"] if r["PARCELA_REGIAO_PREDOMINANTE"] >= 0.6 else r["DUAS_REGIOES"]
    rot = [f"{regiao(r)} · {porte(r['POP_MEDIANA'])} · alfabetização "
           f"{'mais baixa' if r['ALFAB_MEDIA'] <= t1 else 'intermediária' if r['ALFAB_MEDIA'] <= t2 else 'mais alta'}"
           for r in resumo.iter_rows(named=True)]
    # se dois grupos ganharem o mesmo rótulo, a infraestrutura desempata
    vistos = {}
    for i, r in enumerate(rot):
        vistos.setdefault(r, []).append(i)
    for r, idx in vistos.items():
        if len(idx) > 1:
            for i in idx:
                rot[i] += f" · infraestrutura {resumo['INFRA_MEDIA'][i]:.2f}".replace(".", ",")
    return resumo.with_columns(pl.Series("CLUSTER_ROTULO", rot))


if __name__ == "__main__":
    ctx = contexto()
    base = ctx.drop_nulls(VARIAVEIS)
    print(f"[INFO] {base.height} municípios com todas as variáveis de contexto; "
          f"fora: {ctx.join(base, on='CO_MUNICIPIO', how='anti')['NO_MUNICIPIO'].to_list()}")
    X = StandardScaler().fit_transform(base.select(VARIAVEIS).to_numpy())

    # diagnóstico da escolha de k
    linhas = []
    for k in range(3, 11):
        km = KMeans(k, n_init=50, random_state=SEMENTE).fit(X)
        linhas.append({"K": k, "INERCIA": km.inertia_, "SILHUETA": silhouette_score(X, km.labels_, sample_size=3000, random_state=0),
                       "MENOR_GRUPO": int(np.bincount(km.labels_).min())})
    escolha = pl.DataFrame(linhas)
    escolha.write_csv(DIAG_DIR / "clusters_escolha_k.csv")
    print(escolha.with_columns(pl.col("INERCIA").round(0), pl.col("SILHUETA").round(3)))

    km = KMeans(K, n_init=50, random_state=SEMENTE).fit(X)
    mun = base.with_columns(pl.Series("CLUSTER_ID", km.labels_.astype(np.int8)))

    resumo = (
        mun.group_by("CLUSTER_ID").agg(
            pl.len().alias("MUNICIPIOS"),
            pl.col("POPULACAO_TOTAL_CENSO").median().alias("POP_MEDIANA"),
            pl.col("TAXA_ALFABETIZACAO_15MAIS").mean().alias("ALFAB_MEDIA"),
            pl.col("IDHM_RENDA").mean().alias("IDHM_RENDA_MEDIO"),
            pl.col("IDHM_LONGEVIDADE").mean().alias("IDHM_LONGEVIDADE_MEDIO"),
            pl.col("INFRA").mean().alias("INFRA_MEDIA"),
            pl.col("NM_REGIAO").mode().first().alias("REGIAO_PREDOMINANTE"),
            (pl.col("NM_REGIAO") == pl.col("NM_REGIAO").mode().first()).mean().alias("PARCELA_REGIAO_PREDOMINANTE"),
            pl.col("NM_REGIAO").value_counts(sort=True).head(2).struct.field("NM_REGIAO").str.join(" e ").alias("DUAS_REGIOES"),
        )
        # ordem estável e legível: do menor para o maior perfil socioeconômico
        .sort("ALFAB_MEDIA").with_row_index("CLUSTER", offset=1).with_columns(pl.col("CLUSTER").cast(pl.Int8))
    )
    resumo = rotular(resumo, base["TAXA_ALFABETIZACAO_15MAIS"])
    mapa = resumo.select("CLUSTER_ID", "CLUSTER", "CLUSTER_ROTULO")
    mun = mun.join(mapa, on="CLUSTER_ID").select("CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF", "NM_REGIAO", "CLUSTER", "CLUSTER_ROTULO", *VARIAVEIS)
    resumo = resumo.drop("CLUSTER_ID").sort("CLUSTER")

    mun.write_parquet(PROCESSED_DIR / "cluster_municipio.parquet")
    resumo.write_parquet(PROCESSED_DIR / "cluster_resumo.parquet")
    print(f"\n[OK] cluster_municipio.parquet ({mun.height} municípios) e cluster_resumo.parquet ({resumo.height} grupos), k = {K}")
    print(resumo.select("CLUSTER", "CLUSTER_ROTULO", "MUNICIPIOS", pl.col("POP_MEDIANA").round(0),
                        (pl.col("ALFAB_MEDIA") * 100).round(1), pl.col("IDHM_RENDA_MEDIO").round(3), pl.col("INFRA_MEDIA").round(2),
                        (pl.col("PARCELA_REGIAO_PREDOMINANTE") * 100).round(0).alias("PCT_REGIAO")))
