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

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]


def carregar(padrao: str) -> pl.DataFrame:
    arquivos = sorted(INTERIM_DIR.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo {padrao} em {INTERIM_DIR}")
    return pl.concat([pl.read_parquet(a) for a in arquivos], how="diagonal_relaxed")


def total_por_subfuncao(func: pl.DataFrame) -> None:
    mun = func.filter((pl.col("TIPO") == "Municipal") & ~pl.col("EH_TOTAL"))
    alvo = mun.filter(pl.col("COD_SUBF").is_in(["361", "362", "306", "782", "122"]))
    resumo = alvo.group_by(["NUM_ANO", "COD_SUBF"]).agg(
        (pl.col("VAL_DESP_PAGA").sum() / 1e9).round(2).alias("pago_bi"),
        (pl.col("VAL_DESP_PAGA") > 0).sum().alias("n_positivo"),
    )
    with pl.Config(tbl_rows=20, tbl_cols=10):
        print("\n[1] GASTO PAGO (R$ bilhões) POR SUBFUNÇÃO — camada Municipal")
        print(resumo.pivot(on="COD_SUBF", index="NUM_ANO", values="pago_bi").sort("NUM_ANO"))
        print("\n[1b] MUNICÍPIOS COM GASTO POSITIVO (não só com linha existente)")
        print(resumo.pivot(on="COD_SUBF", index="NUM_ANO", values="n_positivo").sort("NUM_ANO"))


def participacao_361(func: pl.DataFrame) -> None:
    geral = (
        carregar("siope_20*_extraido.parquet")
        .filter(pl.col("TIPO") == "Municipal")
        .select([
            pl.col("NUM_ANO"),
            pl.col("COD_MUNI").cast(pl.Int64, strict=False),
            pl.col("VL_DESP_PAGA_EDU"),
        ])
    )
    f361 = (
        func.filter(
            (pl.col("TIPO") == "Municipal") & (pl.col("COD_SUBF") == "361") & ~pl.col("EH_TOTAL")
        )
        .group_by(["NUM_ANO", "COD_MUNI"])
        .agg(pl.col("VAL_DESP_PAGA").sum().alias("PAGO_361"))
    )
    j = f361.join(geral, on=["NUM_ANO", "COD_MUNI"], how="inner").filter(pl.col("VL_DESP_PAGA_EDU") > 0)

    print("\n[2] PARTICIPAÇÃO DA SUBFUNÇÃO 361 NO GASTO TOTAL EM EDUCAÇÃO (a quebra de 2021 apareceria aqui)")
    print(
        j.group_by("NUM_ANO")
        .agg(
            pl.len().alias("municipios"),
            (pl.col("PAGO_361").sum() / pl.col("VL_DESP_PAGA_EDU").sum()).round(3).alias("share_agregado"),
            (pl.col("PAGO_361") / pl.col("VL_DESP_PAGA_EDU")).median().round(3).alias("share_mediana"),
        )
        .sort("NUM_ANO")
    )


def ufs_faltantes(func: pl.DataFrame) -> None:
    est = func.filter((pl.col("TIPO") == "Estadual") & pl.col("COD_SUBF").is_in(["361", "362"]))
    print("\n[3] UFs SEM gasto declarado em 361/362 (camada Estadual), por ano")
    for ano in sorted(func["NUM_ANO"].unique().to_list()):
        presentes = set(est.filter(pl.col("NUM_ANO") == ano)["SIG_UF"].unique().to_list())
        print(f"  {ano}: {sorted(set(UFS) - presentes)}")


if __name__ == "__main__":
    func = carregar("siope_funcao_*_extraido.parquet")
    total_por_subfuncao(func)
    participacao_361(func)
    ufs_faltantes(func)