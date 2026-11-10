"""Por que incluir 2025 dobra a associação gasto × proficiência dentro do município (decisão A11)?

Testes, para Anos Iniciais (MT e LP), sempre com erros-padrão agrupados por município:

1. Primeiras diferenças por biênio (2017→19, 19→21, 21→23, 23→25): Δnota ~ Δlog(gasto) + Δinfraestrutura
   + Δlog(matrículas). Mostra se a inclinação de 2023→25 é diferente das outras.
2. No biênio 2023→25, controles extras, um de cada vez e juntos:
   - efeito de UF (mudanças comuns ao estado: programas estaduais, ICMS educacional, recomposição);
   - nota e log do gasto de 2023 (convergência: redes de nota e gasto baixos sobem mais nas duas coisas,
     o que cria associação sem que uma dependa da outra).
3. Modelo de efeito fixo de município 2017–2025 com efeito de UF × edição no lugar do efeito de edição.
4. Descrição do biênio 2023→25: crescimento do gasto e da nota por quintil do gasto de 2023 e por região,
   e a parcela de redes com variação extrema do gasto (|Δlog| > 0,5) em cada biênio (qualidade dos dados).

Associação, não causalidade (A1). Saídas em data/interim/diagnosticos/investigar_2025_*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Modelo_Principal as M  # noqa: E402  (mesma base e mesmas variáveis do modelo principal)

DIAG_DIR = M.DIAG_DIR
BIENIOS = [(2017, 2019), (2019, 2021), (2021, 2023), (2023, 2025)]


def mqo(d: pl.DataFrame, y: str, xs: list[str], dummies: list[str] | None = None) -> dict:
    d = d.drop_nulls([y, *xs, *(dummies or [])])
    cols = [np.ones(d.height), *[d[c].cast(pl.Float64).to_numpy() for c in xs]]
    for dm in dummies or []:
        for v in sorted(d[dm].unique().to_list())[1:]:
            cols.append((d[dm] == v).cast(pl.Float64).to_numpy())
    res = sm.OLS(d[y].to_numpy(), np.column_stack(cols)).fit(
        cov_type="cluster", cov_kwds={"groups": d["CO_MUNICIPIO"].cast(pl.Int64).to_numpy()})
    return {"COEF": res.params[1], "EP": res.bse[1], "P": res.pvalues[1], "N": int(res.nobs)}


def diferencas(p: pl.DataFrame, nota: str, a0: int, a1: int) -> pl.DataFrame:
    """Uma linha por município com as variações entre as edições a0 e a1 e os níveis de a0."""
    cols = ["CO_MUNICIPIO", "SG_UF", "NM_REGIAO", nota, "LOG_GASTO_L0", "INFRA", "LOG_MAT"]
    ini = p.filter(pl.col("ANO") == a0).select(cols)
    fim = p.filter(pl.col("ANO") == a1).select(cols[0], *cols[3:])
    return ini.join(fim, on="CO_MUNICIPIO", suffix="_FIM").with_columns(
        (pl.col(f"{nota}_FIM") - pl.col(nota)).alias("D_NOTA"),
        (pl.col("LOG_GASTO_L0_FIM") - pl.col("LOG_GASTO_L0")).alias("D_LOG_GASTO"),
        (pl.col("INFRA_FIM") - pl.col("INFRA")).alias("D_INFRA"),
        (pl.col("LOG_MAT_FIM") - pl.col("LOG_MAT")).alias("D_LOG_MAT"),
        pl.col(nota).alias("NOTA_INI"), pl.col("LOG_GASTO_L0").alias("LOG_GASTO_INI"),
    ).drop_nulls(["D_NOTA", "D_LOG_GASTO", "D_INFRA", "D_LOG_MAT"])


def ef_uf_edicao(p: pl.DataFrame, nota: str) -> dict:
    """EF de município 2017–2025 com efeito de UF × edição (todas as variáveis tiradas da média do município)."""
    d = (p.filter(pl.col("ANO").is_in([2017, 2019, 2021, 2023, 2025]))
         .drop_nulls([nota, "LOG_GASTO_L0", *M.NO_TEMPO])
         .filter(pl.len().over("CO_MUNICIPIO") > 1)
         .with_columns((pl.col("SG_UF") + "_" + pl.col("ANO").cast(pl.Utf8)).alias("UF_ANO")))
    niveis = sorted(d["UF_ANO"].unique().to_list())[1:]
    d = d.with_columns([(pl.col("UF_ANO") == v).cast(pl.Float64).alias(f"D_{v}") for v in niveis])
    cols = ["LOG_GASTO_L0", *M.NO_TEMPO, *[f"D_{v}" for v in niveis]]
    d = d.with_columns([(pl.col(c) - pl.col(c).mean().over("CO_MUNICIPIO")).alias(c) for c in [nota, *cols]])
    X = np.column_stack([d[c].cast(pl.Float64).to_numpy() for c in cols])
    res = sm.OLS(d[nota].to_numpy(), X).fit(cov_type="cluster",
                                            cov_kwds={"groups": d["CO_MUNICIPIO"].cast(pl.Int64).to_numpy()})
    return {"COEF": res.params[0], "EP": res.bse[0], "P": res.pvalues[0], "N": int(res.nobs)}


def main() -> None:
    p = M.base().filter(pl.col("ETAPA") == "AI")
    testes, descr = [], []
    for disc, nota in M.DISCIPLINAS.items():
        # 1. primeiras diferenças por biênio
        for a0, a1 in BIENIOS:
            d = diferencas(p, nota, a0, a1)
            r = mqo(d, "D_NOTA", ["D_LOG_GASTO", "D_INFRA", "D_LOG_MAT"])
            testes.append({"DISCIPLINA": disc, "TESTE": "1. Primeiras diferenças", "BIENIO": f"{a0}→{a1}",
                           "ESPECIFICACAO": "Δ gasto, Δ infraestrutura, Δ matrículas", **r,
                           "MEDIA_D_LOG_GASTO": d["D_LOG_GASTO"].mean(), "DP_D_LOG_GASTO": d["D_LOG_GASTO"].std(),
                           "MEDIA_D_NOTA": d["D_NOTA"].mean(),
                           "PCT_D_GASTO_EXTREMO": (d["D_LOG_GASTO"].abs() > 0.5).mean()})
        # 2. biênio 2023→25 com controles extras (e o de 2021→23 para comparar)
        for a0, a1 in [(2021, 2023), (2023, 2025)]:
            d = diferencas(p, nota, a0, a1)
            base_x = ["D_LOG_GASTO", "D_INFRA", "D_LOG_MAT"]
            for nome, xs, dm in [("sem extras", base_x, None),
                                 ("+ efeito de UF", base_x, ["SG_UF"]),
                                 ("+ nota e gasto iniciais", [*base_x, "NOTA_INI", "LOG_GASTO_INI"], None),
                                 ("+ UF, nota e gasto iniciais", [*base_x, "NOTA_INI", "LOG_GASTO_INI"], ["SG_UF"])]:
                testes.append({"DISCIPLINA": disc, "TESTE": "2. Controles extras", "BIENIO": f"{a0}→{a1}",
                               "ESPECIFICACAO": nome, **mqo(d, "D_NOTA", xs, dm)})
        # 3. EF de município com UF × edição
        testes.append({"DISCIPLINA": disc, "TESTE": "3. EF de município", "BIENIO": "2017–2025",
                       "ESPECIFICACAO": "efeito de UF × edição", **ef_uf_edicao(p, nota)})
        # 4. descrição do biênio 2023→25 por quintil do gasto inicial e por região
        d = diferencas(p, nota, 2023, 2025).with_columns(
            pl.col("LOG_GASTO_INI").qcut(5, labels=[f"Q{i}" for i in range(1, 6)]).alias("QUINTIL_GASTO_2023"))
        for grupo in ["QUINTIL_GASTO_2023", "NM_REGIAO"]:
            descr.append(d.group_by(grupo).agg(
                pl.len().alias("REDES"),
                pl.col("LOG_GASTO_INI").exp().median().alias("GASTO_2023_MEDIANO"),
                pl.col("D_LOG_GASTO").mean().alias("MEDIA_D_LOG_GASTO"),
                pl.col("NOTA_INI").mean().alias("NOTA_2023"),
                pl.col("D_NOTA").mean().alias("MEDIA_D_NOTA"),
            ).rename({grupo: "GRUPO"}).with_columns(pl.lit(disc).alias("DISCIPLINA"), pl.lit(grupo).alias("POR"))
                .sort("GRUPO"))
    testes = pl.DataFrame(testes)
    descr = pl.concat(descr, how="vertical_relaxed")
    testes.write_csv(DIAG_DIR / "investigar_2025_testes.csv")
    descr.write_csv(DIAG_DIR / "investigar_2025_descricao.csv")
    with pl.Config(tbl_rows=100, tbl_cols=20, tbl_width_chars=220, float_precision=3):
        print(testes)
        print(descr)
    print("[OK] investigar_2025_testes.csv e investigar_2025_descricao.csv em data/interim/diagnosticos")


if __name__ == "__main__":
    main()
