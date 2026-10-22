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

# Nome por extenso -> sigla, para compatibilizar com SG_UF_ESC do ENEM
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

# Territorialidades válidas: as 26 UFs + DF (chaves do MAPA_UF) mais "Brasil"
# (o benchmark nacional, que não tem sigla). Qualquer outra coisa na coluna
# original (notas de rodapé, linhas de fonte/elaboração) é lixo de planilha.
TERRITORIALIDADES_VALIDAS = set(MAPA_UF.keys()) | {"Brasil"}

# Prefixos ordenados do mais específico para o mais genérico — importante
# porque "idhm_" também "casaria" por engano com "idhm_educacao_2015" se
# processado primeiro.
METRICAS = [
    ("idhm_educacao_", "IDHM_EDUCACAO"),
    ("idhm_longevidade_", "IDHM_LONGEVIDADE"),
    ("idhm_renda_", "IDHM_RENDA"),
    ("idhm_", "IDHM"),
]


def transformar_idhm() -> pl.DataFrame:
    caminho = INTERIM_DIR / "idhm_extraido.parquet"
    df = pl.read_parquet(caminho)

    # --- Limpeza: remove linhas de rodapé/nota da planilha original ---
    linhas_removidas = df.filter(~pl.col("territorialidades").is_in(TERRITORIALIDADES_VALIDAS))
    if linhas_removidas.height > 0:
        print(f"[INFO] Removendo {linhas_removidas.height} linha(s) de rodapé/lixo:")
        print(linhas_removidas["territorialidades"].unique().to_list())

    df = df.filter(pl.col("territorialidades").is_in(TERRITORIALIDADES_VALIDAS))

    # --- Reshape: wide -> long, uma métrica por vez ---
    tabelas_longas = []
    colunas_ja_usadas: set[str] = set()

    for prefixo, nome_metrica in METRICAS:
        colunas_da_metrica = [
            c for c in df.columns
            if c.startswith(prefixo) and c not in colunas_ja_usadas
        ]
        colunas_ja_usadas.update(colunas_da_metrica)

        tabela_longa = (
            df.select(["territorialidades", *colunas_da_metrica])
            .unpivot(
                index="territorialidades",
                on=colunas_da_metrica,
                variable_name="coluna_origem",
                value_name=nome_metrica,
            )
            .with_columns(
                pl.col("coluna_origem").str.extract(r"(\d{4})$").cast(pl.Int64).alias("ANO")
            )
            .drop("coluna_origem")
            .with_columns(
                pl.col(nome_metrica).cast(pl.Float64, strict=False)
            )
        )
        tabelas_longas.append(tabela_longa)

    # As quatro métricas compartilham exatamente o mesmo conjunto de
    # (territorialidade, ano) — inner join é seguro aqui.
    resultado = tabelas_longas[0]
    for tabela in tabelas_longas[1:]:
        resultado = resultado.join(tabela, on=["territorialidades", "ANO"], how="inner")

    # --- Sigla da UF, para compatibilizar com o ENEM ---
    resultado = resultado.with_columns(
        pl.col("territorialidades").replace_strict(MAPA_UF, default=None).alias("SG_UF")
    )
    # A linha "Brasil" fica com SG_UF nulo de propósito — não é uma UF,
    # é o benchmark nacional; mantemos a linha para comparações futuras.

    # --- Defasagem t-1: o IDHM do ano t controla o Saeb do ano t+1 ---
    # A série do PNUD termina em 2024, então o Saeb 2025 só tem controle
    # com defasagem; aplicamos a mesma regra a todas as edições. O merge
    # usa ANO_REF_SAEB (Int32, como o ANO do saeb_*_transformado).
    resultado = resultado.with_columns((pl.col("ANO") + 1).cast(pl.Int32).alias("ANO_REF_SAEB"))

    return resultado


if __name__ == "__main__":
    df = transformar_idhm()

    destino = INTERIM_DIR / "idhm_transformado.parquet"
    df.write_parquet(destino)

    print(f"\n[OK] IDHM transformado salvo em {destino}")
    print(f"[INFO] {df.height} linhas, {df.width} colunas (esperado: 28 territorialidades x 10 anos = 280 linhas)")
    print(df.schema)

    sem_sigla = df.filter(pl.col("SG_UF").is_null())
    print(f"\n[INFO] Linhas sem SG_UF (esperado: só 'Brasil') -> {sem_sigla['territorialidades'].unique().to_list()}")

    print(df.sort(["territorialidades", "ANO"]).head(15))

    # Cada edição do Saeb precisa do IDHM do ano anterior para as 27 UFs
    edicoes_saeb = [2017, 2019, 2021, 2023, 2025]
    cobertura = (
        df.filter(pl.col("SG_UF").is_not_null() & pl.col("ANO_REF_SAEB").is_in(edicoes_saeb))
        .group_by("ANO_REF_SAEB")
        .agg(pl.col("SG_UF").filter(pl.col("IDHM").is_not_null()).n_unique().alias("ufs_com_idhm"))
    )
    faltando = sorted(set(edicoes_saeb) - set(cobertura.filter(pl.col("ufs_com_idhm") == 27)["ANO_REF_SAEB"].to_list()))
    print(f"\n[INFO] UFs com IDHM t-1 por edição do Saeb:\n{cobertura.sort('ANO_REF_SAEB')}")
    print(f"[INFO] Edições sem as 27 UFs: {faltando or 'nenhuma'}")