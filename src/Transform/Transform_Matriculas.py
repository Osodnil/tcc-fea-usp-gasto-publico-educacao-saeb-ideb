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
MATRICULAS = ["QT_MAT_BAS", "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED"]

UF_COD = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def carregar() -> pl.DataFrame:
    df = pl.concat(
        [pl.read_parquet(INTERIM_DIR / f"censo_matriculas_{a}.parquet") for a in ANOS], how="diagonal_relaxed"
    )
    # Em 2025 uma escola veio sem SG_UF e virou uma segunda linha do município; a UF sai dos
    # dois primeiros dígitos do código, e a soma é refeita por município x rede x ano
    return (
        df.with_columns(pl.col("CO_MUNICIPIO").str.slice(0, 2).replace_strict(UF_COD).alias("SG_UF"),
                        pl.col("ANO").cast(pl.Int32))
        .group_by("CO_MUNICIPIO", "SG_UF", "REDE", "ANO")
        .agg([pl.col(c).sum() for c in MATRICULAS])
    )


def municipal(df: pl.DataFrame) -> pl.DataFrame:
    # Denominador municipal: Fundamental da rede municipal (decisão M1); AI e AF para os recortes por etapa
    return (
        df.filter(pl.col("REDE") == "Municipal")
        .select("CO_MUNICIPIO", "SG_UF", "ANO", "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF")
        .sort("CO_MUNICIPIO", "ANO")
    )


def estadual(df: pl.DataFrame) -> pl.DataFrame:
    # Denominador estadual: educação básica da rede estadual, somada por UF (decisão M1)
    return (
        df.filter(pl.col("REDE") == "Estadual")
        .group_by("SG_UF", "ANO")
        .agg([pl.col(c).sum() for c in MATRICULAS])
        .sort("SG_UF", "ANO")
    )


if __name__ == "__main__":
    df = carregar()

    mun = municipal(df)
    mun.write_parquet(INTERIM_DIR / "matriculas_municipal_transformado.parquet")
    duplicadas = mun.height - mun.select("CO_MUNICIPIO", "ANO").unique().height
    print(f"[OK] matriculas_municipal_transformado: {mun.height} linhas | chave única: "
          f"{'sim' if duplicadas == 0 else f'NÃO ({duplicadas} duplicadas)'}")
    print(f"[INFO] Municípios com rede municipal mas zero matrícula no Fundamental (gasto por aluno indefinido): "
          f"{(mun['QT_MAT_FUND'] == 0).sum()} linhas")
    print(mun.group_by("ANO").agg(pl.len().alias("municipios"), (pl.col("QT_MAT_FUND").sum() / 1e6).round(2).alias("fund_mi"))
          .sort("ANO"))

    est = estadual(df)
    est.write_parquet(INTERIM_DIR / "matriculas_estadual_transformado.parquet")
    print(f"\n[OK] matriculas_estadual_transformado: {est.height} linhas | UFs por ano: "
          f"{sorted(set(est.group_by('ANO').agg(pl.col('SG_UF').n_unique())['SG_UF'].to_list()))}")
    print(
        est.group_by("ANO").agg((pl.col("QT_MAT_BAS").sum() / 1e6).round(2).alias("basica_mi"),
                                (pl.col("QT_MAT_MED").sum() / 1e6).round(2).alias("medio_mi"))
        .sort("ANO").with_columns((pl.col("basica_mi").pct_change() * 100).round(1).alias("var_basica_pct"))
    )
