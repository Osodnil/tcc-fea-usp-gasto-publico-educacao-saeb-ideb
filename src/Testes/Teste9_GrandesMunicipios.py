import time
import polars as pl
from Teste8_Reconciliacao import buscar, ibge7, valor_dca, INTERIM_DIR, SAIDA_DIR

ANOS = [2017, 2021, 2024]
N = 30


def resumo(df: pl.DataFrame, titulo: str) -> None:
    ok = df.filter(pl.col("RAZAO").is_not_null())
    quantis = [round(ok["RAZAO"].quantile(p), 3) for p in (0.1, 0.25, 0.5, 0.75, 0.9)]
    print(
        f"\n{titulo}: {ok.height} comparações | quantis 10/25/50/75/90: {quantis} | "
        f"±5%: {ok['RAZAO'].is_between(0.95, 1.05).mean():.0%} | "
        f"±20%: {ok['RAZAO'].is_between(0.8, 1.2).mean():.0%}"
    )
    print(ok.group_by("NUM_ANO").agg(pl.col("RAZAO").median().round(3).alias("mediana_razao")).sort("NUM_ANO"))


if __name__ == "__main__":
    anterior = SAIDA_DIR / "reconciliacao_municipal.csv"
    if anterior.exists():
        resumo(pl.read_csv(anterior), "AMOSTRA ANTERIOR (40 municípios de 825 a 197 mil hab.)")

    func = pl.concat(
        [pl.read_parquet(INTERIM_DIR / f"siope_funcao_{a}_extraido.parquet") for a in ANOS],
        how="diagonal_relaxed",
    )
    siope = (
        func.filter((pl.col("TIPO") == "Municipal") & (pl.col("COD_SUBF") == "361") & ~pl.col("EH_TOTAL"))
        .group_by(["NUM_ANO", "COD_MUNI"])
        .agg(pl.col("VAL_DESP_PAGA").sum().alias("SIOPE_361"))
    )
    grandes = (
        pl.read_parquet(INTERIM_DIR / "siope_2024_extraido.parquet")
        .select([pl.col("COD_MUNI").cast(pl.Int64, strict=False), "NOM_MUNI", "NUM_POPU"])
        .drop_nulls(["COD_MUNI", "NUM_POPU"])
        .unique("COD_MUNI")
        .sort("NUM_POPU", descending=True)
        .head(N)
    )

    linhas = []
    for row in grandes.iter_rows(named=True):
        for ano in ANOS:
            itens = buscar(ano, ibge7(row["COD_MUNI"]))
            linhas.append({
                "COD_MUNI": row["COD_MUNI"], "NOM_MUNI": row["NOM_MUNI"], "NUM_POPU": row["NUM_POPU"],
                "NUM_ANO": ano,
                "SICONFI_361": valor_dca(itens, r"^12\.361") if itens is not None else None,
            })
            time.sleep(0.15)

    comp = (
        pl.DataFrame(linhas)
        .join(siope, on=["COD_MUNI", "NUM_ANO"], how="left")
        .with_columns(
            pl.when(pl.col("SIOPE_361") > 0)
            .then(pl.col("SICONFI_361") / pl.col("SIOPE_361"))
            .otherwise(None)
            .alias("RAZAO")
        )
    )
    comp.write_csv(SAIDA_DIR / "reconciliacao_grandes_municipios.csv")
    resumo(comp, f"{N} MAIORES MUNICÍPIOS")
    print(f"Linhas sem razão calculável: {comp.filter(pl.col('RAZAO').is_null()).height}")

    with pl.Config(tbl_rows=40, tbl_width_chars=140):
        print(
            comp.with_columns(pl.col("RAZAO").round(2))
            .pivot(on="NUM_ANO", index=["NOM_MUNI", "NUM_POPU"], values="RAZAO")
            .sort("NUM_POPU", descending=True)
        )