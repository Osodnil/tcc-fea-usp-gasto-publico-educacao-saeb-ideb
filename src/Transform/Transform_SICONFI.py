import polars as pl
from pathlib import Path


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
INTERIM_DIR = BASE_DIR / "data" / "interim"


def transformar_siconfi() -> pl.DataFrame:
    pagas = pl.read_parquet(INTERIM_DIR / "siconfi_estados_funcao12.parquet").filter(
        pl.col("COLUNA") == "Despesas Pagas"
    )
    por_uf = pagas.group_by("UF", "ANO").agg(
        pl.col("VALOR").filter(pl.col("SUBF").is_null()).first().alias("F12_NOMINAL"),
        pl.col("VALOR").filter(pl.col("SUBF") == "364").first().alias("SUP364_NOMINAL"),
    )

    deflator = pl.read_parquet(INTERIM_DIR / "ipca_deflator_anual.parquet").select(
        pl.col("ANO").cast(pl.Int32), "FATOR_PARA_BASE"
    )

    return (
        por_uf.with_columns(pl.col("ANO").cast(pl.Int32))
        .join(deflator, on="ANO", how="left")
        .with_columns(
            pl.col("SUP364_NOMINAL").is_null().alias("SUP364_AUSENTE"),
            # Decisão G4 ainda pendente com a orientadora: as duas versões ficam disponíveis.
            # (a) linha 12.364 ausente = nada a descontar
            (pl.col("F12_NOMINAL") - pl.col("SUP364_NOMINAL").fill_null(0)).alias("GASTO_BASICA_A_NOMINAL"),
            # (b) linha 12.364 ausente = dado faltante
            (pl.col("F12_NOMINAL") - pl.col("SUP364_NOMINAL")).alias("GASTO_BASICA_B_NOMINAL"),
        )
        .with_columns(
            [(pl.col(f"{c}_NOMINAL") * pl.col("FATOR_PARA_BASE")).alias(f"{c}_R2025")
             for c in ("F12", "GASTO_BASICA_A", "GASTO_BASICA_B")]
        )
        .select(pl.col("UF").alias("SG_UF"), "ANO", "F12_NOMINAL", "SUP364_NOMINAL", "SUP364_AUSENTE",
                "GASTO_BASICA_A_NOMINAL", "GASTO_BASICA_B_NOMINAL",
                "F12_R2025", "GASTO_BASICA_A_R2025", "GASTO_BASICA_B_R2025")
        .sort("SG_UF", "ANO")
    )


if __name__ == "__main__":
    df = transformar_siconfi()
    destino = INTERIM_DIR / "siconfi_estadual_transformado.parquet"
    df.write_parquet(destino)
    print(f"[OK] {destino.name}: {df.height} linhas | anos {df['ANO'].min()}-{df['ANO'].max()}")

    duplicadas = df.height - df.select("SG_UF", "ANO").unique().height
    print(f"[INFO] Chave SG_UF + ANO única: {'sim' if duplicadas == 0 else f'NÃO ({duplicadas})'} | "
          f"UFs por ano: {sorted(set(df.group_by('ANO').agg(pl.col('SG_UF').n_unique())['SG_UF'].to_list()))}")
    print(f"[INFO] Sem total da função 12: {df['F12_NOMINAL'].null_count()} | sem deflator: {df['F12_R2025'].null_count()}")

    print("\n[INFO] UF-anos sem a linha 12.364 (decisão G4), 2017-2025:")
    print(df.filter(pl.col("SUP364_AUSENTE") & (pl.col("ANO") >= 2017)).group_by("SG_UF")
          .agg(pl.col("ANO").sort().alias("anos")).sort("SG_UF"))

    print("\n[INFO] Peso do Ensino Superior na função 12 (onde a linha existe), 2017-2025:")
    print(df.filter(~pl.col("SUP364_AUSENTE") & (pl.col("ANO") >= 2017))
          .select((pl.col("SUP364_NOMINAL") / pl.col("F12_NOMINAL")).alias("p"))
          .select(pl.col("p").min().round(3).alias("min"), pl.col("p").median().round(3).alias("mediana"),
                  pl.col("p").max().round(3).alias("max")))

    print("\n[INFO] Gasto com educação básica (versão a), R$ bi de 2025:")
    print(df.group_by("ANO").agg((pl.col("GASTO_BASICA_A_R2025").sum() / 1e9).round(1).alias("bi")).sort("ANO"))
