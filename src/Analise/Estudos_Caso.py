"""Estudos de caso do capítulo 5: escolha dos municípios por critério objetivo e os números de cada um.

Recorte: Anos Iniciais, Matemática, edição de 2023, comparação nacional (padrão do painel). Critérios:
- caso A, "acima do esperado sem alerta": entre as redes de municípios com mais de 50 mil habitantes, sem salto atípico
  e com rede municipal completa (parcela ≥ 50%), a de maior "vs. esperado";
- caso B, "abaixo do esperado com rede parcial": entre as redes com rede municipal parcial (parcela < 50%), a do
  município mais populoso (é onde o alerta mais pesa na leitura);
- caso C, "salto atípico": entre as redes com salto atípico em 2023, a de maior "vs. esperado" entre os municípios com
  mais de 50 mil habitantes (cidades em que o salto é menos provável de ser efeito de rede pequena).
Para cada caso: série por edição, gasto, cluster, pares (mesmo cluster, gasto entre 0,8 e 1,25 vez; comparação
nacional) e o par de maior "vs. esperado".

Saída: data/interim/diagnosticos/estudos_caso.csv (série) e estudos_caso_resumo.csv; imprime o resumo.
"""
from pathlib import Path

import polars as pl

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PBI = RAIZ / "data" / "processed" / "powerbi"
DIAG = RAIZ / "data" / "interim" / "diagnosticos"
ETAPA, DISC, ANO = "AI", "MT", 2023


def base() -> pl.DataFrame:
    f = pl.read_parquet(PBI / "fato_desempenho_municipal.parquet").filter(
        (pl.col("ETAPA") == ETAPA) & (pl.col("DISCIPLINA") == DISC))
    o = pl.read_parquet(PBI / "fato_oferta_municipal.parquet").filter(pl.col("ETAPA") == ETAPA).select(
        "CO_MUNICIPIO", "ANO", "PART_MUN")
    m = pl.read_parquet(PBI / "dim_municipio.parquet").select(
        "CO_MUNICIPIO", "MUNICIPIO_UF", "POPULACAO_TOTAL_CENSO", "CLUSTER", "CLUSTER_ROTULO")
    return f.join(o, on=["CO_MUNICIPIO", "ANO"], how="left").join(m, on="CO_MUNICIPIO", how="left")


def pares(b: pl.DataFrame, co: str) -> pl.DataFrame:
    d = b.filter((pl.col("ANO") == ANO) & pl.col("EFIC_PCT").is_not_null())
    ref = d.filter(pl.col("CO_MUNICIPIO") == co).row(0, named=True)
    g = ref["GASTO_ALUNO_R2025_L0"]
    return (d.filter((pl.col("CLUSTER") == ref["CLUSTER"]) & (pl.col("CO_MUNICIPIO") != co)
                     & pl.col("GASTO_ALUNO_R2025_L0").is_between(0.8 * g, 1.25 * g))
            .sort("EFIC_PCT", descending=True))


def main() -> None:
    b = base()
    a23 = b.filter((pl.col("ANO") == ANO) & pl.col("EFIC_PCT").is_not_null())
    grande = pl.col("POPULACAO_TOTAL_CENSO") > 50_000
    completa = pl.col("PART_MUN") >= 0.5
    casos = {
        "A": a23.filter(grande & ~pl.col("SALTO_ATIPICO") & completa).sort("EFIC_PCT", descending=True).row(0, named=True),
        "B": a23.filter(pl.col("PART_MUN") < 0.5).sort("POPULACAO_TOTAL_CENSO", descending=True).row(0, named=True),
        "C": a23.filter(grande & pl.col("SALTO_ATIPICO")).sort("EFIC_PCT", descending=True).row(0, named=True),
    }
    serie, resumo = [], []
    for k, r in casos.items():
        co = r["CO_MUNICIPIO"]
        s = b.filter(pl.col("CO_MUNICIPIO") == co).sort("ANO").select(
            "ANO", "PROFICIENCIA", "NOTA_ESPERADA", "EFIC_PCT", "PERCENTIL_RESIDUO", "GASTO_ALUNO_R2025_L0",
            "SALTO_ATIPICO", "PART_MUN").with_columns(pl.lit(k).alias("CASO"), pl.lit(r["MUNICIPIO_UF"]).alias("MUNICIPIO"))
        serie.append(s)
        p = pares(b, co)
        topo = p.row(0, named=True) if p.height else None
        resumo.append({
            "CASO": k, "MUNICIPIO": r["MUNICIPIO_UF"], "POPULACAO": r["POPULACAO_TOTAL_CENSO"],
            "CLUSTER": f"{r['CLUSTER']} · {r['CLUSTER_ROTULO']}", "GASTO_2023": r["GASTO_ALUNO_R2025_L0"],
            "PROF_2023": r["PROFICIENCIA"], "ESPERADA_2023": r["NOTA_ESPERADA"], "VS_ESPERADO_2023": r["EFIC_PCT"],
            "PERCENTIL_2023": r["PERCENTIL_RESIDUO"], "PART_MUN_2023": r["PART_MUN"], "SALTO_2023": r["SALTO_ATIPICO"],
            "PARES": p.height, "PARES_ACIMA": p.filter(pl.col("EFIC_PCT") > r["EFIC_PCT"]).height,
            "MELHOR_PAR": None if topo is None else topo["MUNICIPIO_UF"],
            "MELHOR_PAR_GASTO": None if topo is None else topo["GASTO_ALUNO_R2025_L0"],
            "MELHOR_PAR_VS": None if topo is None else topo["EFIC_PCT"],
            "MELHOR_PAR_SALTO": None if topo is None else topo["SALTO_ATIPICO"],
            "MELHOR_PAR_SEM_SALTO": (p.filter(~pl.col("SALTO_ATIPICO") & (pl.col("PART_MUN") >= 0.5)).row(0, named=True)["MUNICIPIO_UF"]
                                     if p.filter(~pl.col("SALTO_ATIPICO") & (pl.col("PART_MUN") >= 0.5)).height else None),
        })
    DIAG.mkdir(parents=True, exist_ok=True)
    pl.concat(serie).write_csv(DIAG / "estudos_caso.csv")
    res = pl.DataFrame(resumo)
    res.write_csv(DIAG / "estudos_caso_resumo.csv")
    with pl.Config(tbl_cols=30, tbl_width_chars=250, fmt_str_lengths=70, tbl_rows=60, float_precision=3):
        print(res.transpose(include_header=True, column_names="CASO"))
        print(pl.concat(serie))


if __name__ == "__main__":
    main()
