"""Indicador de eficiência municipal: desempenho observado × desempenho esperado dado gasto e contexto.

Para cada etapa (AI, AF) e disciplina (Matemática, Português, em pontos do Saeb; decisão S9),
estima por MQO:
    proficiência = a + b·log(gasto por aluno do ano) + contexto + efeitos de edição + erro
com erros-padrão agrupados por município. O indicador é o resíduo: quantos pontos o município
ficou acima (+) ou abaixo (−) do esperado para o seu gasto e o seu contexto.

Contexto: log da população e alfabetização (Censo 2022), índice de infraestrutura da rede
municipal no ano, log das matrículas do Fundamental (tamanho da rede) e IDHM Renda e
Longevidade da UF no ano (sem a dimensão Educação, decisão C1b).

- Modelo principal: com IDHM, edições 2017-2023 (o IDHM 2025 não existe, decisão C1).
- Modelo alternativo: troca o IDHM por efeitos fixos de UF e cobre também 2025.
Também grava a comparação descritiva com os pares do mesmo cluster (decisão A6).

Saídas: data/processed/eficiencia_municipal.parquet; coeficientes em
data/interim/diagnosticos/eficiencia_coeficientes.csv.
"""
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DIAG_DIR = BASE_DIR / "data" / "interim" / "diagnosticos"

DISCIPLINAS = {"MT": "NOTA_MT", "LP": "NOTA_LP"}
INFRA = ["PROP_IN_BIBLIOTECA", "PROP_IN_LABORATORIO_INFORMATICA", "PROP_IN_LABORATORIO_CIENCIAS", "PROP_IN_INTERNET",
         "PROP_IN_BANHEIRO", "PROP_IN_AGUA_POTAVEL", "PROP_IN_ENERGIA_REDE_PUBLICA", "PROP_IN_QUADRA_ESPORTES"]
CONTEXTO = ["LOG_POP", "ALFAB", "INFRA", "LOG_MAT"]
MODELOS = {
    "principal": {"idhm": True, "uf": False, "anos": [2017, 2019, 2021, 2023]},
    "alternativo_uf": {"idhm": False, "uf": True, "anos": [2017, 2019, 2021, 2023, 2025]},
}


def base() -> pl.DataFrame:
    clusters = pl.read_parquet(PROCESSED_DIR / "cluster_municipio.parquet").select("CO_MUNICIPIO", "CLUSTER", "CLUSTER_ROTULO")
    return (
        pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet")
        .with_columns(
            pl.col("GASTO_ALUNO_R2025_L0").log().alias("LOG_GASTO"),
            pl.col("POPULACAO_TOTAL_CENSO").log10().alias("LOG_POP"),
            (pl.col("TAXA_ALFABETIZACAO_15MAIS") * 100).alias("ALFAB"),
            pl.mean_horizontal(INFRA).alias("INFRA"),
            pl.when(pl.col("QT_MAT_FUND") > 0).then(pl.col("QT_MAT_FUND").log10()).alias("LOG_MAT"),
        )
        .join(clusters, on="CO_MUNICIPIO", how="left")
    )


def ajustar(df: pl.DataFrame, nota: str, op: dict) -> tuple[pl.DataFrame, list[dict], dict]:
    x_cols = ["LOG_GASTO", *CONTEXTO] + (["IDHM_RENDA", "IDHM_LONGEVIDADE"] if op["idhm"] else [])
    d = df.filter(pl.col("ANO").is_in(op["anos"])).drop_nulls([nota, *x_cols])
    # matriz em NumPy puro (sem pandas/pyarrow), com os nomes guardados à parte
    nomes = ["const", *x_cols]
    colunas = [np.ones(d.height), *[d[c].cast(pl.Float64).to_numpy() for c in x_cols]]
    for a in op["anos"][1:]:  # efeitos de edição (2017 é a referência)
        nomes.append(f"ANO_{a}"); colunas.append((d["ANO"] == a).cast(pl.Float64).to_numpy())
    if op["uf"]:
        for uf in sorted(d["SG_UF"].unique().to_list())[1:]:
            nomes.append(f"UF_{uf}"); colunas.append((d["SG_UF"] == uf).cast(pl.Float64).to_numpy())
    X = np.column_stack(colunas)
    y = d[nota].to_numpy()
    grupos = d["CO_MUNICIPIO"].cast(pl.Int64).to_numpy()
    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": grupos})
    coefs = [{"VARIAVEL": v, "COEF": res.params[i], "EP": res.bse[i], "P": res.pvalues[i]}
             for i, v in enumerate(nomes) if not v.startswith(("ANO_", "UF_"))]
    pred = np.asarray(res.fittedvalues)
    saida = d.select("CO_MUNICIPIO", "ETAPA", "ANO").with_columns(
        pl.Series("NOTA", y), pl.Series("NOTA_ESPERADA", pred), pl.Series("RESIDUO", y - pred))
    ajuste = {"N": int(res.nobs), "R2": res.rsquared, "MUNICIPIOS": len(set(grupos))}
    return saida, coefs, ajuste


def saltos(df: pl.DataFrame, nota: str) -> pl.DataFrame:
    """Marca (não exclui) variação atípica de proficiência em relação à edição anterior (decisão S11, proposta).

    Atípica = a variação entre duas edições consecutivas (2 anos) se afasta mais de 3 desvios-padrão
    da média das variações da mesma etapa e disciplina, para cima ou para baixo.
    """
    d = (df.drop_nulls(nota).sort("CO_MUNICIPIO", "ANO")
         .with_columns((pl.col(nota) - pl.col(nota).shift(1).over("CO_MUNICIPIO")).alias("VARIACAO"),
                       (pl.col("ANO") - pl.col("ANO").shift(1).over("CO_MUNICIPIO")).alias("INTERVALO")))
    v = d.filter(pl.col("INTERVALO") == 2)["VARIACAO"]
    m, dp = v.mean(), v.std()
    return d.select(
        "CO_MUNICIPIO", "ETAPA", "ANO",
        pl.when(pl.col("INTERVALO") == 2).then(pl.col("VARIACAO")).alias("VARIACAO_EDICAO_ANTERIOR"),
        pl.when(pl.col("INTERVALO") == 2).then((pl.col("VARIACAO") - m).abs() > 3 * dp).otherwise(False).alias("SALTO_ATIPICO"),
    )


def pares_cluster(df: pl.DataFrame, nota: str) -> pl.DataFrame:
    """Comparação descritiva com o cluster: nota − mediana do cluster e gasto ÷ mediana do cluster, por edição."""
    d = df.drop_nulls([nota, "GASTO_ALUNO_R2025_L0", "CLUSTER"])
    return d.select(
        "CO_MUNICIPIO", "ETAPA", "ANO",
        (pl.col(nota) - pl.col(nota).median().over("ETAPA", "ANO", "CLUSTER")).alias("NOTA_VS_CLUSTER"),
        (pl.col("GASTO_ALUNO_R2025_L0") / pl.col("GASTO_ALUNO_R2025_L0").median().over("ETAPA", "ANO", "CLUSTER")).alias("GASTO_VS_CLUSTER"),
    )


if __name__ == "__main__":
    df = base()
    blocos, coef_linhas = [], []
    for etapa in ("AI", "AF"):
        de = df.filter(pl.col("ETAPA") == etapa)
        for disc, nota in DISCIPLINAS.items():
            pares = pares_cluster(de, nota)
            por_modelo = {}
            for nome, op in MODELOS.items():
                saida, coefs, ajuste = ajustar(de, nota, op)
                por_modelo[nome] = saida
                for c in coefs:
                    coef_linhas.append({"ETAPA": etapa, "DISCIPLINA": disc, "MODELO": nome, **c, **ajuste})
                b = next(c for c in coefs if c["VARIAVEL"] == "LOG_GASTO")
                print(f"[{etapa} {disc} {nome:15s}] N={ajuste['N']:>6} R²={ajuste['R2']:.3f}  log(gasto): "
                      f"{b['COEF']:+.2f} (EP {b['EP']:.2f}, p={b['P']:.3f}) -> +10% de gasto ~ {b['COEF'] * np.log(1.1):+.2f} pontos")
            juntos = (
                por_modelo["alternativo_uf"].rename({"NOTA_ESPERADA": "NOTA_ESPERADA_ALT", "RESIDUO": "RESIDUO_ALT"})
                .join(por_modelo["principal"].select("CO_MUNICIPIO", "ANO", "NOTA_ESPERADA", "RESIDUO"), on=["CO_MUNICIPIO", "ANO"], how="left")
                .join(pares, on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
                .join(saltos(de, nota), on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
                .with_columns(pl.lit(disc).alias("DISCIPLINA"), pl.col("SALTO_ATIPICO").fill_null(False))
            )
            r = juntos.drop_nulls(["RESIDUO", "RESIDUO_ALT"])
            print(f"    correlação entre os resíduos dos dois modelos: {np.corrcoef(r['RESIDUO'], r['RESIDUO_ALT'])[0, 1]:.3f}")
            blocos.append(juntos)

    efic = (
        pl.concat(blocos)
        .join(df.select("CO_MUNICIPIO", "ETAPA", "ANO", "CLUSTER", "CLUSTER_ROTULO").unique(), on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
        # posição relativa (0 a 100) no resíduo principal, dentro de etapa, disciplina e edição
        .with_columns(
            (pl.col("RESIDUO").rank().over("ETAPA", "DISCIPLINA", "ANO") / pl.col("RESIDUO").count().over("ETAPA", "DISCIPLINA", "ANO") * 100)
            .alias("PERCENTIL_RESIDUO"),
            (pl.col("RESIDUO_ALT").rank().over("ETAPA", "DISCIPLINA", "ANO") / pl.col("RESIDUO_ALT").count().over("ETAPA", "DISCIPLINA", "ANO") * 100)
            .alias("PERCENTIL_RESIDUO_ALT"),
        )
        .select("CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO", "CLUSTER", "CLUSTER_ROTULO", "NOTA",
                "NOTA_ESPERADA", "RESIDUO", "PERCENTIL_RESIDUO", "NOTA_ESPERADA_ALT", "RESIDUO_ALT", "PERCENTIL_RESIDUO_ALT",
                "NOTA_VS_CLUSTER", "GASTO_VS_CLUSTER", "VARIACAO_EDICAO_ANTERIOR", "SALTO_ATIPICO")
        .sort("CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO")
    )
    efic.write_parquet(PROCESSED_DIR / "eficiencia_municipal.parquet")
    pl.DataFrame(coef_linhas).write_csv(DIAG_DIR / "eficiencia_coeficientes.csv")

    dup = efic.height - efic.select("CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO").unique().height
    print(f"\n[OK] eficiencia_municipal.parquet: {efic.height} linhas | chave única: {'sim' if dup == 0 else f'NÃO ({dup})'}")
    print("[INFO] Linhas por edição (resíduo principal / alternativo):")
    print(efic.group_by("ETAPA", "ANO").agg(pl.col("RESIDUO").is_not_null().sum().alias("principal"),
                                            pl.col("RESIDUO_ALT").is_not_null().sum().alias("alternativo")).sort("ETAPA", "ANO"))
    s = efic.filter(pl.col("SALTO_ATIPICO"))
    print(f"[INFO] Saltos atípicos marcados: {s.height} linhas ({s.height / efic.height:.1%}); "
          f"altas: {(s['VARIACAO_EDICAO_ANTERIOR'] > 0).sum()}, quedas: {(s['VARIACAO_EDICAO_ANTERIOR'] < 0).sum()}")
    # persistência: o mesmo município tende a ficar acima/abaixo do esperado entre edições?
    w = (efic.filter((pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))
         .pivot(on="ANO", index="CO_MUNICIPIO", values="RESIDUO_ALT"))
    print(f"[INFO] Persistência (AI, MT, modelo alternativo): correlação do resíduo 2019 × 2023 = "
          f"{w.select(pl.corr('2019', '2023')).item():.3f}; 2023 × 2025 = {w.select(pl.corr('2023', '2025')).item():.3f}")
