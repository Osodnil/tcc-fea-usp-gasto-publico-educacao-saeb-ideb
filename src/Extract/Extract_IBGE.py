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
RAW_ROOT = BASE_DIR / "data" / "raw" / "Censo" / "Dados"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)


def extrair_municipios() -> pl.DataFrame:
    caminho = RAW_ROOT / "Municípios.xlsx"
    df = pl.read_excel(caminho, sheet_name="Agregados_por_municipios_basico")

    colunas_desejadas = ["CD_MUN", "NM_MUN", "CD_UF", "NM_UF", "CD_REGIAO", "NM_REGIAO", "AREA_KM2", "v0001"]
    colunas_disponiveis = [c for c in colunas_desejadas if c in df.columns]
    df = df.select(colunas_disponiveis)

    if "v0001" in df.columns:
        df = df.rename({"v0001": "POPULACAO_TOTAL_CENSO"})

    exprs = [pl.col("CD_MUN").cast(pl.Utf8), pl.col("AREA_KM2").cast(pl.Float64, strict=False)]
    if "POPULACAO_TOTAL_CENSO" in df.columns:
        exprs.append(pl.col("POPULACAO_TOTAL_CENSO").cast(pl.Float64, strict=False))

    return df.with_columns(exprs)


def extrair_alfabetizacao() -> pl.DataFrame:
    caminho = RAW_ROOT / "Alfabetização.xlsx"
    df = pl.read_excel(caminho, sheet_name="Agregados_por_municipios_alfabe")

    df = df.select(["CD_MUN", "V00900", "V00901"]).with_columns([
        pl.col("CD_MUN").cast(pl.Utf8),
        pl.col("V00900").cast(pl.Float64, strict=False),
        pl.col("V00901").cast(pl.Float64, strict=False),
    ])

    df = df.with_columns(
        (pl.col("V00900") / (pl.col("V00900") + pl.col("V00901"))).alias("TAXA_ALFABETIZACAO_15MAIS")
    ).rename({
        "V00900": "POP_ALFABETIZADA_15MAIS",
        "V00901": "POP_NAO_ALFABETIZADA_15MAIS",
    })

    return df


if __name__ == "__main__":
    municipios = extrair_municipios()
    alfabetizacao = extrair_alfabetizacao()

    base_ibge = municipios.join(alfabetizacao, on="CD_MUN", how="left")

    destino = INTERIM_DIR / "ibge_censo_municipios_extraido.parquet"
    base_ibge.write_parquet(destino)

    print(f"[OK] Base IBGE (Municípios + Alfabetização) salva em {destino}")
    print(f"[INFO] {base_ibge.height} linhas, {base_ibge.width} colunas")
    print(base_ibge.columns)
    print(base_ibge.head())