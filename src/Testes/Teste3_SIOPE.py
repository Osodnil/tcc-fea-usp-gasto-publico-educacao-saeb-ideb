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


def carregar(padrao: str) -> pl.DataFrame:
    arquivos = sorted(INTERIM_DIR.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo {padrao} em {INTERIM_DIR}")
    return pl.concat([pl.read_parquet(a) for a in arquivos], how="diagonal_relaxed")


if __name__ == "__main__":
    func = carregar("siope_funcao_*_extraido.parquet").with_columns(
        pl.col("DES_SUBF").fill_null("")
    )
    est = func.filter(pl.col("TIPO") == "Estadual")

    with pl.Config(tbl_rows=70, fmt_str_lengths=70):
        print("[1] O QUE MG E RS DECLARAM NA CAMADA ESTADUAL, POR ANO")
        print(
            est.filter(pl.col("SIG_UF").is_in(["MG", "RS"]))
            .group_by(["SIG_UF", "NUM_ANO"])
            .agg(
                pl.len().alias("linhas"),
                (pl.col("VAL_DESP_PAGA").sum() / 1e9).round(2).alias("pago_bi"),
                pl.col("DES_SUBF").n_unique().alias("rotulos"),
            )
            .sort(["SIG_UF", "NUM_ANO"])
        )

        for ano in (2023, 2024):
            print(f"\n[2] MG EM {ano}: TODAS AS LINHAS DECLARADAS")
            print(
                est.filter((pl.col("SIG_UF") == "MG") & (pl.col("NUM_ANO") == ano))
                .select(["DES_SUBF", "COD_SUBF", "VAL_DESP_PAGA"])
                .sort("VAL_DESP_PAGA", descending=True)
            )

        # rótulos que NÃO seguem o formato "NNN - Nome" (ou "TOTAL NNN - Nome")
        padrao = r"^\s*(?:TOTAL\s+)?\d{2,3}\s*(?:-|–|$)"
        fora = func.filter(~pl.col("DES_SUBF").str.contains(padrao))

        print("\n[3] LINHAS COM RÓTULO FORA DO PADRÃO, POR CAMADA")
        print(
            fora.group_by("TIPO").agg(
                pl.len().alias("linhas"),
                (pl.col("VAL_DESP_PAGA").sum() / 1e9).round(2).alias("pago_bi"),
            )
        )

        print("\n[4] MAIORES RÓTULOS FORA DO PADRÃO (por valor pago)")
        print(
            fora.group_by(["TIPO", "DES_SUBF"])
            .agg(
                pl.len().alias("linhas"),
                (pl.col("VAL_DESP_PAGA").sum() / 1e9).round(3).alias("pago_bi"),
            )
            .sort("pago_bi", descending=True)
            .head(25)
        )

        print("\n[5] LINHAS FORA DO PADRÃO QUE O MEU CÓDIGO CLASSIFICOU COMO 361/362 (risco de erro)")
        print(
            fora.filter(pl.col("COD_SUBF").is_in(["361", "362"]))
            .select(["TIPO", "NUM_ANO", "SIG_UF", "DES_SUBF", "VAL_DESP_PAGA"])
            .sort("VAL_DESP_PAGA", descending=True)
            .head(25)
        )