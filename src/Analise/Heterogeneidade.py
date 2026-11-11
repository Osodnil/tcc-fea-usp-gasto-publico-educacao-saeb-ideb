"""A associação gasto × proficiência dentro do município muda por porte, região, cluster ou nível de gasto?

Responde à pergunta analítica 5. Usa a especificação de referência do modelo principal (decisão A11): efeito fixo
de município e efeito de UF × edição, 2017-2025, gasto do mesmo ano, controles de infraestrutura e log das
matrículas, erros-padrão agrupados por município. No lugar de uma inclinação única do log do gasto, o modelo tem uma
inclinação por grupo (log do gasto × indicador do grupo), e o teste de Wald diz se as inclinações são iguais.

Dimensões (todas fixas no município, então o efeito fixo de município absorve o nível de cada grupo):
- porte (faixas de população do Censo 2022, as mesmas do painel; as duas maiores juntas, por terem poucas redes);
- região;
- cluster de contexto (A6);
- faixa de gasto: quintil do gasto por aluno médio do município em 2017-2025 (gastar mais vale mais para quem gasta
  pouco?).

Associação, não causalidade (A1). Saída: data/interim/diagnosticos/heterogeneidade_coeficientes.csv.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Modelo_Principal as M  # noqa: E402

PORTES = [(5_000, "Até 5 mil"), (10_000, "5 a 10 mil"), (20_000, "10 a 20 mil"), (50_000, "20 a 50 mil"),
          (100_000, "50 a 100 mil"), (float("inf"), "Mais de 100 mil")]
ANOS = [2017, 2019, 2021, 2023, 2025]


def grupos(p: pl.DataFrame) -> pl.DataFrame:
    porte = pl.lit(None, dtype=pl.Utf8)
    for limite, rotulo in reversed(PORTES):
        porte = pl.when(pl.col("POPULACAO_TOTAL_CENSO") <= limite).then(pl.lit(rotulo)).otherwise(porte)
    clusters = pl.read_parquet(M.PROCESSED_DIR / "cluster_municipio.parquet").select(
        "CO_MUNICIPIO", pl.col("CLUSTER").cast(pl.Utf8).alias("CLUSTER"))
    gasto_medio = (p.filter(pl.col("ETAPA") == "AI").group_by("CO_MUNICIPIO")
                   .agg(pl.col("GASTO_ALUNO_R2025_L0").mean().alias("GASTO_MEDIO"))
                   .with_columns(pl.col("GASTO_MEDIO").qcut(5, labels=[f"Q{i}" for i in range(1, 6)])
                                 .cast(pl.Utf8).alias("FAIXA_GASTO")))
    return (p.with_columns(porte.alias("PORTE"))
            .join(clusters, on="CO_MUNICIPIO", how="left")
            .join(gasto_medio.select("CO_MUNICIPIO", "FAIXA_GASTO"), on="CO_MUNICIPIO", how="left"))


def estimar(d: pl.DataFrame, nota: str, dim: str) -> list[dict]:
    x_base = ["LOG_GASTO_L0", *M.NO_TEMPO]
    d = (d.filter(pl.col("ANO").is_in(ANOS)).drop_nulls([nota, *x_base, dim])
         .filter(pl.len().over("CO_MUNICIPIO") > 1)
         .with_columns((pl.col("SG_UF") + "_" + pl.col("ANO").cast(pl.Utf8)).alias("UF_ANO")))
    niveis = sorted(d[dim].unique().to_list())
    inter = [f"G_{g}" for g in niveis]
    uf_ano = sorted(d["UF_ANO"].unique().to_list())[1:]
    d = d.with_columns(
        *[(pl.col("LOG_GASTO_L0") * (pl.col(dim) == g).cast(pl.Float64)).alias(f"G_{g}") for g in niveis],
        *[(pl.col("UF_ANO") == v).cast(pl.Float64).alias(f"UA_{v}") for v in uf_ano])
    cols = [*inter, *M.NO_TEMPO, *[f"UA_{v}" for v in uf_ano]]
    contagem = d.group_by(dim).agg(pl.len().alias("N_GRUPO"), pl.col("CO_MUNICIPIO").n_unique().alias("MUN_GRUPO"))
    dw = d.with_columns([(pl.col(c) - pl.col(c).mean().over("CO_MUNICIPIO")).alias(c) for c in [nota, *cols]])
    X = np.column_stack([dw[c].cast(pl.Float64).to_numpy() for c in cols])
    res = sm.OLS(dw[nota].to_numpy(), X).fit(
        cov_type="cluster", cov_kwds={"groups": dw["CO_MUNICIPIO"].cast(pl.Int64).to_numpy()})
    # H0: todas as inclinações iguais (b_g − b_1 = 0 para g > 1)
    R = np.zeros((len(niveis) - 1, X.shape[1]))
    for i in range(1, len(niveis)):
        R[i - 1, 0], R[i - 1, i] = -1.0, 1.0
    p_igual = float(res.f_test(R).pvalue)
    ic = res.conf_int()
    linhas = []
    for i, g in enumerate(niveis):
        c = contagem.filter(pl.col(dim) == g)
        linhas.append({"GRUPO": g, "COEF": res.params[i], "EP": res.bse[i], "P": res.pvalues[i],
                       "IC95_INF": ic[i][0], "IC95_SUP": ic[i][1], "PONTOS_POR_10PCT": res.params[i] * np.log(1.1),
                       "N_GRUPO": c["N_GRUPO"].item(), "MUN_GRUPO": c["MUN_GRUPO"].item(),
                       "P_IGUALDADE": p_igual, "N": int(res.nobs)})
    return linhas


def main() -> None:
    p = grupos(M.base())
    saida = []
    for etapa in ["AI", "AF"]:
        for disc, nota in M.DISCIPLINAS.items():
            d = p.filter(pl.col("ETAPA") == etapa)
            for dim, nome in [("PORTE", "Porte"), ("NM_REGIAO", "Região"), ("CLUSTER", "Cluster"),
                              ("FAIXA_GASTO", "Faixa de gasto médio")]:
                for linha in estimar(d, nota, dim):
                    saida.append({"ETAPA": etapa, "DISCIPLINA": disc, "DIMENSAO": nome, **linha})
    saida = pl.DataFrame(saida)
    arquivo = M.DIAG_DIR / "heterogeneidade_coeficientes.csv"
    saida.write_csv(arquivo)
    with pl.Config(tbl_rows=200, tbl_cols=20, tbl_width_chars=220, float_precision=2):
        print(saida.filter(pl.col("ETAPA") == "AI").select(
            "DISCIPLINA", "DIMENSAO", "GRUPO", "COEF", "EP", "P", "PONTOS_POR_10PCT", "N_GRUPO", "MUN_GRUPO",
            "P_IGUALDADE"))
        print(saida.filter(pl.col("ETAPA") == "AF").group_by("DISCIPLINA", "DIMENSAO")
              .agg(pl.col("P_IGUALDADE").first(), pl.col("COEF").min().alias("MIN"), pl.col("COEF").max().alias("MAX"))
              .sort("DISCIPLINA", "DIMENSAO"))
    print(f"[OK] {saida.height} linhas em {arquivo.relative_to(M.BASE_DIR)}")


if __name__ == "__main__":
    main()
