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

MAPA_REDE = {"1": "Federal", "2": "Estadual", "3": "Municipal", "4": "Privada"}
UF_COD = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}


def transformar_infraestrutura() -> pl.DataFrame:
    """Proporção de escolas com cada item de infraestrutura, por município x rede x ano.

    Recria o censo_escolar_transformado (cujo script original não estava no repositório; regra
    conferida contra o arquivo antigo). TOTAL_ESCOLAS conta todas as escolas; as proporções
    ignoram escolas sem a informação (indicadores nulos).
    """
    escolas = pl.concat(
        [pl.read_parquet(f) for f in sorted(INTERIM_DIR.glob("censo_escolar_*_extraido.parquet"))],
        how="diagonal_relaxed",
    )
    indicadores = [c for c in escolas.columns if c.startswith("IN_")]
    return (
        escolas.with_columns(
            # UF pelo código do município: em 2025 uma escola veio sem SG_UF (decisão M4)
            pl.col("CO_MUNICIPIO").str.slice(0, 2).replace_strict(UF_COD).alias("SG_UF"),
            pl.col("TP_DEPENDENCIA").replace_strict(MAPA_REDE).alias("REDE"),
            pl.col("ANO").cast(pl.Int32),
        )
        .group_by("CO_MUNICIPIO", "SG_UF", "ANO", "REDE")
        .agg(pl.len().cast(pl.UInt32).alias("TOTAL_ESCOLAS"),
             *[pl.col(c).cast(pl.Float64).mean().alias(f"PROP_{c}") for c in indicadores])
        .sort("CO_MUNICIPIO", "ANO", "REDE")
    )


if __name__ == "__main__":
    df = transformar_infraestrutura()
    destino = INTERIM_DIR / "censo_escolar_transformado.parquet"
    df.write_parquet(destino)
    duplicadas = df.height - df.select("CO_MUNICIPIO", "ANO", "REDE").unique().height
    print(f"[OK] {destino.name}: {df.height} linhas | anos {df['ANO'].min()}-{df['ANO'].max()} | "
          f"chave única: {'sim' if duplicadas == 0 else f'NÃO ({duplicadas})'}")
    print(df.group_by("ANO").agg(pl.col("CO_MUNICIPIO").n_unique().alias("municipios"),
                                 pl.col("TOTAL_ESCOLAS").sum().alias("escolas")).sort("ANO"))
