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
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Defasagens do gasto em relação à edição do Saeb. Sem dado do ano t-k, a coluna fica nula
# (ex.: L2 só existe a partir do Saeb 2019 e L4 a partir de 2021, pois o gasto começa em 2017)
DEFASAGENS = [0, 1, 2, 4]
INFRA = ["PROP_IN_BIBLIOTECA", "PROP_IN_LABORATORIO_INFORMATICA", "PROP_IN_LABORATORIO_CIENCIAS", "PROP_IN_INTERNET",
         "PROP_IN_BANHEIRO", "PROP_IN_AGUA_POTAVEL", "PROP_IN_ENERGIA_REDE_PUBLICA", "PROP_IN_QUADRA_ESPORTES"]


def ler(nome: str) -> pl.DataFrame:
    return pl.read_parquet(INTERIM_DIR / f"{nome}.parquet")


def com_defasagens(painel: pl.DataFrame, gasto: pl.DataFrame, chave: list[str], colunas: list[str]) -> pl.DataFrame:
    """Junta o gasto por aluno do ano ANO-k para cada k em DEFASAGENS, com sufixo _L{k}."""
    for k in DEFASAGENS:
        defasado = gasto.select(
            *chave, (pl.col("ANO") + k).cast(pl.Int32).alias("ANO"), *[pl.col(c).alias(f"{c}_L{k}") for c in colunas]
        )
        painel = painel.join(defasado, on=[*chave, "ANO"], how="left")
    return painel


def idhm_uf() -> pl.DataFrame:
    # IDHM da UF no mesmo ano da edição do Saeb (decisão C1); o Saeb 2025 fica sem IDHM
    return ler("idhm_transformado").filter(pl.col("SG_UF").is_not_null()).select(
        "SG_UF", pl.col("ANO").cast(pl.Int32), "IDHM", "IDHM_EDUCACAO", "IDHM_RENDA", "IDHM_LONGEVIDADE",
    )


def painel_municipal() -> pl.DataFrame:
    # Gasto por aluno: 361 pago (R$ 2025) / matrículas do Fundamental da rede municipal.
    # Gasto 361 = 0 com gasto em educação positivo é erro de classificação (G11) e matrícula 0
    # deixa a razão indefinida (M5): os dois viram nulo, nunca zero ou infinito.
    gasto = (
        ler("matriculas_municipal_transformado")
        .join(ler("siope_municipal_transformado").select("CO_MUNICIPIO", "ANO", "GASTO_361_R2025"),
              on=["CO_MUNICIPIO", "ANO"], how="full", coalesce=True)
        .with_columns(
            pl.when((pl.col("GASTO_361_R2025") > 0) & (pl.col("QT_MAT_FUND") > 0))
            .then(pl.col("GASTO_361_R2025") / pl.col("QT_MAT_FUND"))
            .alias("GASTO_ALUNO_R2025")
        )
        # Marca (não exclui) valores fora de 0,5%-99,5% do ano: a regra de corte é decisão de análise (A5)
        .with_columns(
            (~pl.col("GASTO_ALUNO_R2025").is_between(
                pl.col("GASTO_ALUNO_R2025").quantile(0.005).over("ANO"),
                pl.col("GASTO_ALUNO_R2025").quantile(0.995).over("ANO"),
            )).alias("GASTO_EXTREMO")
        )
    )

    ibge = ler("ibge_transformado").select(
        "CO_MUNICIPIO", "NM_REGIAO", "POPULACAO_TOTAL_CENSO", "TAXA_ALFABETIZACAO_15MAIS"
    )
    infra = ler("censo_escolar_transformado").filter(pl.col("REDE") == "Municipal").select(
        "CO_MUNICIPIO", "ANO", pl.col("TOTAL_ESCOLAS").alias("ESCOLAS_MUNICIPAIS"), *INFRA
    )

    painel = (
        ler("saeb_municipal_transformado").drop("REDE")
        .join(gasto.select("CO_MUNICIPIO", "ANO", "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "GASTO_361_R2025"),
              on=["CO_MUNICIPIO", "ANO"], how="left")
    )
    painel = com_defasagens(painel, gasto, ["CO_MUNICIPIO"], ["GASTO_ALUNO_R2025", "GASTO_EXTREMO"])
    return (
        painel.join(ibge, on="CO_MUNICIPIO", how="left")
        .join(idhm_uf(), on=["SG_UF", "ANO"], how="left")
        .join(infra, on=["CO_MUNICIPIO", "ANO"], how="left")
        .sort("CO_MUNICIPIO", "ETAPA", "ANO")
    )


def painel_estadual() -> pl.DataFrame:
    # Gasto por aluno: função 12 - 12.364 paga (R$ 2025) / matrículas da educação básica da rede estadual.
    # Versões A e B enquanto a decisão G4 está pendente.
    gasto = (
        ler("matriculas_estadual_transformado")
        .join(ler("siconfi_estadual_transformado"), on=["SG_UF", "ANO"], how="left")
        .with_columns(
            [pl.when(pl.col("QT_MAT_BAS") > 0).then(pl.col(f"GASTO_BASICA_{v}_R2025") / pl.col("QT_MAT_BAS"))
             .alias(f"GASTO_ALUNO_{v}_R2025") for v in ("A", "B")]
        )
    )

    # Alfabetização da UF a partir dos municípios (Censo 2022, estática)
    alfab = ler("ibge_transformado").group_by("SG_UF").agg(
        (pl.col("POP_ALFABETIZADA_15MAIS").sum()
         / (pl.col("POP_ALFABETIZADA_15MAIS").sum() + pl.col("POP_NAO_ALFABETIZADA_15MAIS").sum()) * 100)
        .alias("TAXA_ALFABETIZACAO_15MAIS"),
        pl.col("POPULACAO_TOTAL_CENSO").sum(),
        pl.col("NM_REGIAO").first(),
    )
    # Infraestrutura da rede estadual na UF: média das proporções municipais ponderada pelo número de escolas
    infra = (
        ler("censo_escolar_transformado").filter(pl.col("REDE") == "Estadual")
        .group_by("SG_UF", "ANO")
        .agg(pl.col("TOTAL_ESCOLAS").sum().alias("ESCOLAS_ESTADUAIS"),
             *[((pl.col(c) * pl.col("TOTAL_ESCOLAS")).sum() / pl.col("TOTAL_ESCOLAS").sum()).alias(c) for c in INFRA])
    )

    painel = (
        ler("saeb_estadual_transformado").drop("REDE")
        .join(gasto.select("SG_UF", "ANO", "QT_MAT_BAS", "QT_MAT_MED", "SUP364_AUSENTE"), on=["SG_UF", "ANO"], how="left")
    )
    painel = com_defasagens(painel, gasto, ["SG_UF"], ["GASTO_ALUNO_A_R2025", "GASTO_ALUNO_B_R2025"])
    return (
        painel.join(alfab, on="SG_UF", how="left")
        .join(idhm_uf(), on=["SG_UF", "ANO"], how="left")
        .join(infra, on=["SG_UF", "ANO"], how="left")
        .sort("SG_UF", "ETAPA", "ANO")
    )


def validar(df: pl.DataFrame, nome: str, chave: list[str], unidade: str, col_gasto: str) -> None:
    print(f"\n[{nome.upper()}] {df.height} linhas | {df.width} colunas")
    duplicadas = df.height - df.select(chave).unique().height
    print(f"  Chave {chave} única: {'sim' if duplicadas == 0 else f'NÃO ({duplicadas} duplicadas)'}")

    cols_l = [f"{col_gasto}_L{k}" for k in DEFASAGENS]
    print("  Unidades com nota e com gasto por aluno, por etapa e ano:")
    print(
        df.filter(pl.col("TEM_NOTA")).group_by("ETAPA", "ANO")
        .agg(pl.len().alias("com_nota"), *[pl.col(c).is_not_null().sum().alias(c.split("_")[-1]) for c in cols_l])
        .sort("ETAPA", "ANO")
    )

    controles = ["IDHM", "TAXA_ALFABETIZACAO_15MAIS", "PROP_IN_INTERNET"]
    print("  Nulos nos controles (linhas com nota):",
          {c: df.filter(pl.col("TEM_NOTA"))[c].null_count() for c in controles})
    # IDHM do mesmo ano: só a edição de 2025 deve ficar sem (série do PNUD termina em 2024)
    print("  Edições com IDHM nulo (esperado: só 2025):",
          sorted(df.filter(pl.col("TEM_NOTA") & pl.col("IDHM").is_null())["ANO"].unique().to_list()))

    g = df.filter(pl.col("TEM_NOTA")).select(pl.col(f"{col_gasto}_L0").drop_nulls())
    q = [round(g.to_series().quantile(p)) for p in (0.0, 0.01, 0.25, 0.5, 0.75, 0.99, 1.0)]
    print(f"  Gasto por aluno L0 (R$ 2025), quantis 0/1/25/50/75/99/100%: {q}")


def extremos_municipais(df: pl.DataFrame) -> None:
    fora = (df.filter((pl.col("ETAPA") == "AI") & pl.col("GASTO_EXTREMO_L0"))
            .select("CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF", "ANO", "TEM_NOTA", "QT_MAT_FUND", "GASTO_ALUNO_R2025_L0")
            .sort("ANO", "GASTO_ALUNO_R2025_L0"))
    destino = INTERIM_DIR / "diagnosticos" / "gasto_aluno_extremos_municipal.csv"
    fora.write_csv(destino)
    print(f"  Gasto por aluno marcado como extremo (L0, AI): {fora.height} linhas, "
          f"{fora.filter(pl.col('TEM_NOTA')).height} com nota -> {destino.name}")


if __name__ == "__main__":
    mun = painel_municipal()
    mun.write_parquet(PROCESSED_DIR / "painel_municipal.parquet")
    validar(mun, "municipal", ["CO_MUNICIPIO", "ETAPA", "ANO"], "CO_MUNICIPIO", "GASTO_ALUNO_R2025")
    extremos_municipais(mun)

    est = painel_estadual()
    est.write_parquet(PROCESSED_DIR / "painel_estadual.parquet")
    validar(est, "estadual", ["SG_UF", "ETAPA", "ANO"], "SG_UF", "GASTO_ALUNO_A_R2025")
    print(f"  Linhas com 12.364 ausente no ano (versão B nula): {est['SUP364_AUSENTE'].sum()}")

    print(f"\n[OK] painel_municipal.parquet e painel_estadual.parquet em {PROCESSED_DIR}")
