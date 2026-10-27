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

ANOS = range(2017, 2026)


def ibge7(cod6: pl.Expr) -> pl.Expr:
    """Código de 6 dígitos (SIOPE) -> 7 dígitos (IBGE), pelo dígito verificador (decisão G9).

    Pesos 1,2,1,2,1,2; soma dos algarismos de cada produto; verificador = (10 - soma mod 10) mod 10.
    """
    s = cod6.cast(pl.Int64).cast(pl.Utf8).str.zfill(6)
    soma = pl.lit(0)
    for i in range(6):
        p = s.str.slice(i, 1).cast(pl.Int64) * (1 if i % 2 == 0 else 2)
        soma = soma + p // 10 + p % 10
    return s + ((10 - soma % 10) % 10).cast(pl.Utf8)


def tabela_codigos() -> pl.DataFrame:
    """Prefixo de 6 dígitos -> código IBGE de 7, a partir dos códigos oficiais.

    Nove municípios têm código IBGE que não segue o dígito verificador (ex.: Brejo do Piauí,
    2201988; a fórmula daria 2201986), por isso a conversão é por consulta e a fórmula só cobre
    o que não estiver na tabela. Usa o Censo 2022 mais o Censo Escolar, que já traz municípios
    instalados depois de 2022.
    """
    codigos = pl.concat([
        pl.read_parquet(INTERIM_DIR / "ibge_transformado.parquet").select("CO_MUNICIPIO"),
        *[pl.read_parquet(INTERIM_DIR / f"censo_matriculas_{a}.parquet").select("CO_MUNICIPIO") for a in ANOS],
    ]).unique()
    tabela = codigos.with_columns(pl.col("CO_MUNICIPIO").str.slice(0, 6).alias("C6"))
    if tabela["C6"].n_unique() != tabela.height:
        raise ValueError("Prefixos de 6 dígitos repetidos na tabela de códigos; a consulta seria ambígua.")
    return tabela.rename({"CO_MUNICIPIO": "CO_TABELA"})


def carregar(padrao: str) -> pl.DataFrame:
    return pl.concat([pl.read_parquet(INTERIM_DIR / padrao.format(ano=a)) for a in ANOS], how="diagonal_relaxed")


def transformar_siope() -> pl.DataFrame:
    # Numerador: subfunção 361 paga, camada municipal, sem linhas TOTAL (decisões G5 e G6).
    # Só rótulos que COMEÇAM com 361: "361 - Ensino Fundamental" (até 2023) e "361" (2024-2025).
    # Rótulos atípicos como "SubFunção 361 - Fonte 01 ..." ficam de fora.
    gasto_361 = (
        carregar("siope_funcao_{ano}_extraido.parquet")
        .filter((pl.col("TIPO") == "Municipal") & pl.col("DES_SUBF").str.contains(r"^\s*361\s*(-|$)")
                & ~pl.col("EH_TOTAL"))
        .group_by("NUM_ANO", "COD_MUNI")
        .agg(pl.col("VAL_DESP_PAGA").sum().alias("GASTO_361_NOMINAL"))
    )

    # Gasto total em educação: contexto (participação da 361), não entra no indicador principal
    geral = (
        carregar("siope_{ano}_extraido.parquet")
        .select("NUM_ANO", pl.col("COD_MUNI").cast(pl.Int64, strict=False), "SIG_UF", "NOM_MUNI",
                pl.col("VL_DESP_PAGA_EDU").alias("GASTO_EDU_NOMINAL"))
        .unique(["NUM_ANO", "COD_MUNI"])
    )

    deflator = pl.read_parquet(INTERIM_DIR / "ipca_deflator_anual.parquet").select(
        pl.col("ANO").cast(pl.Int32), "FATOR_PARA_BASE"
    )

    return (
        gasto_361.join(geral, on=["NUM_ANO", "COD_MUNI"], how="left")
        .with_columns(pl.col("COD_MUNI").cast(pl.Utf8).str.zfill(6).alias("C6"))
        .join(tabela_codigos(), on="C6", how="left")
        .with_columns(
            pl.coalesce("CO_TABELA", ibge7(pl.col("COD_MUNI"))).alias("CO_MUNICIPIO"),
            pl.col("CO_TABELA").is_null().alias("CODIGO_POR_FORMULA"),
            pl.col("NUM_ANO").cast(pl.Int32).alias("ANO"),
        )
        .join(deflator, on="ANO", how="left")
        .with_columns(
            # Reais de 2025 pelo IPCA médio anual (decisão G8)
            (pl.col("GASTO_361_NOMINAL") * pl.col("FATOR_PARA_BASE")).alias("GASTO_361_R2025"),
            (pl.col("GASTO_EDU_NOMINAL") * pl.col("FATOR_PARA_BASE")).alias("GASTO_EDU_R2025"),
        )
        .select("CO_MUNICIPIO", pl.col("SIG_UF").alias("SG_UF"), pl.col("NOM_MUNI").alias("NO_MUNICIPIO"), "ANO",
                "GASTO_361_NOMINAL", "GASTO_361_R2025", "GASTO_EDU_NOMINAL", "GASTO_EDU_R2025", "CODIGO_POR_FORMULA")
        .sort("CO_MUNICIPIO", "ANO")
    )


if __name__ == "__main__":
    df = transformar_siope()
    destino = INTERIM_DIR / "siope_municipal_transformado.parquet"
    df.write_parquet(destino)
    print(f"[OK] {destino.name}: {df.height} linhas")

    duplicadas = df.height - df.select("CO_MUNICIPIO", "ANO").unique().height
    print(f"[INFO] Chave CO_MUNICIPIO + ANO única: {'sim' if duplicadas == 0 else f'NÃO ({duplicadas})'}")

    # Teste da conversão de código: todo código precisa existir no IBGE ou no Censo Escolar, com a mesma UF
    por_formula = df.filter(pl.col("CODIGO_POR_FORMULA"))["CO_MUNICIPIO"].unique().to_list()
    print(f"[INFO] Códigos que precisaram da fórmula (fora da tabela oficial): {len(por_formula)} {sorted(por_formula)[:10]}")
    ibge = pl.read_parquet(INTERIM_DIR / "ibge_transformado.parquet").select("CO_MUNICIPIO", pl.col("SG_UF").alias("UF_IBGE"))
    conf = df.join(ibge, on="CO_MUNICIPIO", how="left")
    fora = conf.filter(pl.col("UF_IBGE").is_null())["CO_MUNICIPIO"].unique().to_list()
    uf_trocada = conf.filter(pl.col("UF_IBGE").is_not_null() & (pl.col("UF_IBGE") != pl.col("SG_UF"))).height
    print(f"[INFO] Códigos fora do Censo 2022: {len(fora)} {sorted(fora)[:10]} | UF divergente do IBGE: {uf_trocada}")

    print(f"[INFO] Linhas sem deflator: {df['GASTO_361_R2025'].null_count()} | sem gasto total em educação: "
          f"{df['GASTO_EDU_NOMINAL'].null_count()} | gasto 361 <= 0: {(df['GASTO_361_NOMINAL'] <= 0).sum()}")
    print("\n[INFO] Por ano (R$ bi de 2025):")
    print(
        df.group_by("ANO").agg(
            pl.len().alias("municipios"),
            (pl.col("GASTO_361_R2025").sum() / 1e9).round(1).alias("gasto_361_bi"),
            (pl.col("GASTO_361_NOMINAL").sum() / pl.col("GASTO_EDU_NOMINAL").sum()).round(3).alias("part_361"),
        ).sort("ANO")
    )
