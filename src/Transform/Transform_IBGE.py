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

# Mesmo mapa usado no Transform do IDHM — reaproveitado para consistência
MAPA_UF = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR",
    "Pará": "PA", "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA",
    "Piauí": "PI", "Ceará": "CE", "Rio Grande do Norte": "RN", "Paraíba": "PB",
    "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espírito Santo": "ES", "Rio de Janeiro": "RJ",
    "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}


def transformar_ibge() -> pl.DataFrame:
    caminho = INTERIM_DIR / "ibge_censo_municipios_extraido.parquet"
    df = pl.read_parquet(caminho)

    print(f"[INFO] Schema original: {df.schema}")
    print(f"[INFO] {df.height} linhas")

    # --- Padronização de nomes, para bater com ENEM/IDEB/Censo Escolar ---
    df = df.rename({"CD_MUN": "CO_MUNICIPIO"}).with_columns(
        pl.col("CO_MUNICIPIO").cast(pl.Utf8)
    )

    # --- Sigla da UF (de-para do nome por extenso) ---
    if "NM_UF" in df.columns:
        df = df.with_columns(
            pl.col("NM_UF").replace_strict(MAPA_UF, default=None).alias("SG_UF")
        )
        nao_mapeados = df.filter(pl.col("SG_UF").is_null())
        if nao_mapeados.height > 0:
            print(f"[AVISO] {nao_mapeados.height} linha(s) sem SG_UF mapeada -> "
                  f"{nao_mapeados['NM_UF'].unique().to_list()}")

    # --- Checagem do join feito na Extração ---
    if "TAXA_ALFABETIZACAO_15MAIS" in df.columns:
        nulos_alfab = df["TAXA_ALFABETIZACAO_15MAIS"].null_count()
        print(f"[INFO] Municípios sem taxa de alfabetização (join Municípios x Alfabetização): "
              f"{nulos_alfab} de {df.height}")

    return df


if __name__ == "__main__":
    df = transformar_ibge()

    destino = INTERIM_DIR / "ibge_transformado.parquet"
    df.write_parquet(destino)

    print(f"\n[OK] IBGE transformado salvo em {destino}")
    print(f"[INFO] {df.height} linhas, {df.width} colunas")
    print(df.schema)
    print(df.select(["CO_MUNICIPIO", "NM_MUN", "SG_UF", "TAXA_ALFABETIZACAO_15MAIS"]).head(10))

    print("\n[NOTA] Esta base é uma fotografia estática do Censo 2022 — não tem coluna ANO. "
          "No merge final, deve ser unida por CO_MUNICIPIO apenas (não por ano), aplicando-se "
          "o mesmo valor a todas as edições do ENEM — igual à decisão já tomada para o IDHM municipal.")