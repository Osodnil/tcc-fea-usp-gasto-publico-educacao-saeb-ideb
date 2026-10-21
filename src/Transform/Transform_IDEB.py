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

REDES_VALIDAS = ["Estadual", "Federal", "Municipal"]


def transformar_ideb() -> pl.DataFrame:
    caminho = INTERIM_DIR / "ideb_ensino_medio_municipios_extraido.parquet"
    df = pl.read_parquet(caminho)

    # --- Limpeza: remove linhas com REDE ausente (pendência da extração) ---
    linhas_sem_rede = df.filter(pl.col("REDE").is_null())
    if linhas_sem_rede.height > 0:
        print(f"[INFO] Removendo {linhas_sem_rede.height} linha(s) com REDE nula (~{linhas_sem_rede.height / df.height:.1%} do total)")

    df = df.filter(pl.col("REDE").is_in(REDES_VALIDAS))

    # --- Reshape: wide (VL_OBSERVADO_AAAA) -> long, com coluna ANO ---
    colunas_valor = [c for c in df.columns if c.startswith("VL_OBSERVADO_")]
    colunas_id = [c for c in df.columns if c not in colunas_valor]

    df_longo = (
        df.unpivot(
            index=colunas_id,
            on=colunas_valor,
            variable_name="coluna_origem",
            value_name="IDEB",
        )
        .with_columns(
            pl.col("coluna_origem").str.extract(r"(\d{4})$").cast(pl.Int64).alias("ANO"),
            pl.col("IDEB").cast(pl.Float64, strict=False),
        )
        .drop("coluna_origem")
    )

    return df_longo


if __name__ == "__main__":
    df = transformar_ideb()

    destino = INTERIM_DIR / "ideb_transformado.parquet"
    df.write_parquet(destino)

    print(f"\n[OK] IDEB transformado salvo em {destino}")
    print(f"[INFO] {df.height} linhas, {df.width} colunas")
    print(df.schema)

    anos_presentes = sorted(df["ANO"].unique().to_list())
    print(f"\n[INFO] Anos presentes (edições bienais): {anos_presentes}")
    print("[INFO] 2015-2016 e os anos pares (2018/2020/2022/2024) do ENEM não têm edição correspondente do IDEB "
          "— a regra de correspondência (ex.: usar a edição anterior mais próxima) fica para a etapa de merge, não aqui.")

    print(f"[INFO] Valores únicos em REDE (pós-filtro): {df['REDE'].unique().to_list()}")
    
    print("\n[INFO] Proporção de IDEB nulo, por REDE:")
    
    print(
        df.group_by("REDE")
        .agg(
            pl.col("IDEB").null_count().alias("nulos"),
            pl.len().alias("total"),
        )
        .with_columns((pl.col("nulos") / pl.col("total")).alias("proporcao_nula"))
        .sort("proporcao_nula", descending=True)
    )

    taxa_nulos = df["IDEB"].null_count() / df.height
    print(f"[INFO] Proporção de IDEB nulo (sem cálculo divulgado para o município/rede/ano): {taxa_nulos:.1%}")

    print(df.sort(["CO_MUNICIPIO", "REDE", "ANO"]).head(15))