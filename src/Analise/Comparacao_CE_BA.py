"""Mesmo gasto, resultados diferentes: as redes municipais do Ceará e da Bahia (análise 2 do capítulo 5; decisão A19).

Compara as redes municipais dos dois estados, que gastam praticamente o mesmo por aluno, em quatro cortes:
- por etapa e disciplina, em 2023 (redes com nota, gasto mediano, proficiência média, % acima do esperado na comparação
  nacional, mediana do "vs. esperado" e saltos atípicos);
- por edição, de 2017 a 2025 (Anos Iniciais, Matemática);
- dentro dos mesmos clusters de contexto (2023), para ver se a diferença é de contexto;
- sem as redes com salto atípico (2023).
Também traz o contexto dos dois estados (alfabetização e população dos municípios; IDHM da UF) e a camada estadual do
Ensino Médio, onde as redes estaduais atendem quase todos os alunos. Associação, não efeito causal (A1).

Saídas: data/interim/diagnosticos/comparacao_ce_ba.csv (formato longo, com a coluna CORTE) e
docs/resultados/figuras/fig7_ce_ba.png.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import polars as pl

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Material_Texto as MT  # noqa: E402

PBI = MT.M.PROCESSED_DIR / "powerbi"
UFS = ["CE", "BA"]
CORES = {"CE": MT.AZUL, "BA": MT.LARANJA}


def base() -> pl.DataFrame:
    f = pl.read_parquet(PBI / "fato_desempenho_municipal.parquet")
    m = pl.read_parquet(PBI / "dim_municipio.parquet").select("CO_MUNICIPIO", "SG_UF", "CLUSTER")
    return f.join(m, on="CO_MUNICIPIO", how="left")


def resumo(d: pl.DataFrame) -> list[pl.Expr]:
    com_nota = pl.col("PROFICIENCIA").is_not_null()
    return [com_nota.sum().alias("REDES"),
            pl.col("GASTO_ALUNO_R2025_L0").filter(com_nota).median().alias("GASTO_MEDIANO"),
            pl.col("PROFICIENCIA").mean().alias("PROFICIENCIA_MEDIA"),
            (pl.col("EFIC_PCT").drop_nulls() > 0).mean().alias("PARC_ACIMA"),
            pl.col("EFIC_PCT").median().alias("VS_ESPERADO_MEDIANO"),
            pl.col("SALTO_ATIPICO").filter(com_nota).sum().alias("SALTOS")]


def main() -> None:
    b = base()
    uf = b.filter(pl.col("SG_UF").is_in(UFS))
    ai_mt = (pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT")
    partes = [
        uf.filter(pl.col("ANO") == 2023).group_by("ETAPA", "DISCIPLINA", "SG_UF").agg(resumo(uf))
        .with_columns(pl.lit("2023 por etapa").alias("CORTE")),
        uf.filter(ai_mt).group_by("ANO", "SG_UF").agg(resumo(uf)).with_columns(pl.lit("AI MT por edição").alias("CORTE")),
        uf.filter(ai_mt & (pl.col("ANO") == 2023)).group_by("CLUSTER", "SG_UF").agg(resumo(uf))
        .with_columns(pl.lit("AI MT 2023 por cluster").alias("CORTE")),
        uf.filter(ai_mt & (pl.col("ANO") == 2023) & ~pl.col("SALTO_ATIPICO")).group_by("SG_UF").agg(resumo(uf))
        .with_columns(pl.lit("AI MT 2023 sem saltos").alias("CORTE")),
        b.filter(ai_mt).group_by("ANO").agg(resumo(b)).with_columns(pl.lit("BR").alias("SG_UF"),
                                                                    pl.lit("AI MT por edição").alias("CORTE")),
    ]
    saida = pl.concat(partes, how="diagonal_relaxed")
    MT.DIAG.mkdir(parents=True, exist_ok=True)
    saida.write_csv(MT.DIAG / "comparacao_ce_ba.csv")

    # contexto dos dois estados
    m = pl.read_parquet(PBI / "dim_municipio.parquet").filter(pl.col("SG_UF").is_in(UFS))
    idhm = pl.read_parquet(MT.M.BASE_DIR / "data" / "interim" / "idhm_transformado.parquet").filter(
        pl.col("SG_UF").is_in(UFS) & (pl.col("ANO") == 2023)).select("SG_UF", "IDHM_RENDA", "IDHM_LONGEVIDADE")
    ctx = m.group_by("SG_UF").agg(pl.col("TAXA_ALFABETIZACAO_15MAIS").mean().alias("ALFAB_MEDIA"),
                                  pl.col("POPULACAO_TOTAL_CENSO").median().alias("POP_MEDIANA")).join(idhm, on="SG_UF")
    # camada estadual, Ensino Médio (as redes estaduais atendem quase todos os alunos dessa etapa)
    est = (pl.read_parquet(PBI / "fato_desempenho_estadual.parquet")
           .filter(pl.col("SG_UF").is_in(UFS) & (pl.col("ANO") == 2023) & (pl.col("ETAPA") == "EM"))
           .select("SG_UF", "DISCIPLINA", "PROFICIENCIA", "GASTO_ALUNO_A_R2025_L0"))
    with pl.Config(tbl_rows=80, tbl_cols=20, tbl_width_chars=220, float_precision=3):
        for c in saida["CORTE"].unique(maintain_order=True):
            print(f"\n== {c}")
            print(saida.filter(pl.col("CORTE") == c).drop("CORTE").drop(
                [k for k in ("ETAPA", "DISCIPLINA", "ANO", "CLUSTER") if saida.filter(pl.col("CORTE") == c)[k].null_count()
                 == saida.filter(pl.col("CORTE") == c).height]).sort(pl.all().exclude(pl.Float64, pl.UInt32)))
        print("\n== contexto"), print(ctx)
        print("\n== camada estadual, EM 2023"), print(est.sort("DISCIPLINA", "SG_UF"))

    figura(b)
    print(f"[OK] {(MT.DIAG / 'comparacao_ce_ba.csv').relative_to(MT.M.BASE_DIR)} e fig7_ce_ba.png")


def figura(b: pl.DataFrame) -> None:
    ai_mt = b.filter((pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.0), gridspec_kw={"width_ratios": [1, 1.2]})
    # (a) proficiência média por edição
    serie = (ai_mt.with_columns(pl.when(pl.col("SG_UF").is_in(UFS)).then(pl.col("SG_UF")).otherwise(pl.lit("BR")).alias("G"))
             .pipe(lambda d: pl.concat([d.filter(pl.col("G") != "BR"), d.with_columns(pl.lit("BR").alias("G"))]))
             .group_by("G", "ANO").agg(pl.col("PROFICIENCIA").mean()).sort("ANO"))
    for g, cor, rot in [("CE", CORES["CE"], "Ceará"), ("BA", CORES["BA"], "Bahia"), ("BR", MT.TINTA_2, "Brasil")]:
        s = serie.filter(pl.col("G") == g)
        a1.plot(s["ANO"], s["PROFICIENCIA"], marker="o", color=cor, linewidth=2, markersize=5, label=rot,
                linestyle="--" if g == "BR" else "-")
    a1.set_xticks([2017, 2019, 2021, 2023, 2025])
    a1.set_title("Proficiência média das redes municipais", fontsize=10, color=MT.TINTA, loc="left", fontweight="bold")
    a1.legend(frameon=False, fontsize=8, labelcolor=MT.TINTA_2)
    # (b) gasto × proficiência em 2023
    d = ai_mt.filter((pl.col("ANO") == 2023) & pl.col("SG_UF").is_in(UFS)).drop_nulls(["PROFICIENCIA", "GASTO_ALUNO_R2025_L0"])
    for g, rot in [("BA", "Bahia"), ("CE", "Ceará")]:
        s = d.filter(pl.col("SG_UF") == g)
        a2.scatter(s["GASTO_ALUNO_R2025_L0"] / 1000, s["PROFICIENCIA"], s=12, alpha=0.6, color=CORES[g], label=rot,
                   edgecolors="none")
        med = s["GASTO_ALUNO_R2025_L0"].median() / 1000
        a2.axvline(med, color=CORES[g], linewidth=1, linestyle=":")
    a2.set_xscale("log")
    a2.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    a2.set_xticks([5, 8, 10, 15, 20, 30], ["5", "8", "10", "15", "20", "30"])
    a2.set_xlim(4, 32)
    fora = d.filter((pl.col("GASTO_ALUNO_R2025_L0") < 4000) | (pl.col("GASTO_ALUNO_R2025_L0") > 32000))
    print(f"[INFO] fora da escala do gráfico (gasto < R$ 4 mil ou > R$ 32 mil): "
          f"{fora.select('CO_MUNICIPIO', 'SG_UF', 'GASTO_ALUNO_R2025_L0', 'GASTO_EXTREMO_L0').to_dicts()}")
    a2.set_xlabel("Gasto por aluno, R$ mil de 2025 (escala log; pontilhado: mediana)", fontsize=8, color=MT.TINTA_2)
    a2.set_title("Gasto e proficiência por rede, 2023", fontsize=10, color=MT.TINTA, loc="left", fontweight="bold")
    a2.legend(frameon=False, fontsize=8, labelcolor=MT.TINTA_2, loc="upper right")
    for ax in (a1, a2):
        for lado in ["top", "right"]:
            ax.spines[lado].set_visible(False)
        ax.spines["left"].set_color(MT.GRADE)
        ax.spines["bottom"].set_color(MT.GRADE)
        ax.tick_params(colors=MT.TINTA_2, labelsize=8, length=0)
        ax.grid(axis="y", color=MT.GRADE, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: MT.br(v, 0)))
    fig.supylabel("Pontos do Saeb (AI, Matemática)", fontsize=8, color=MT.TINTA_2)
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    fig.savefig(MT.FIG / "fig7_ce_ba.png", dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
