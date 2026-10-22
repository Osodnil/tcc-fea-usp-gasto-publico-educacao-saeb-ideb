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

ANOS = [2017, 2019, 2021, 2023, 2025]  # edições do Saeb dentro da janela do SIOPE

# Cada camada usa só a rede que o seu gasto financia (decisão 3)
CAMADAS = {
    "municipal": {"nivel": "municipios", "etapas": ["AI", "AF"], "rede": "Municipal",
                  "chave": ["CO_MUNICIPIO", "ETAPA", "ANO"]},
    "estadual": {"nivel": "ufs", "etapas": ["AF", "EM"], "rede": "Estadual",
                 "chave": ["SG_UF", "ETAPA", "ANO"]},
}

RENOMEAR = {
    "VL_NOTA_MATEMATICA": "NOTA_MT",      # proficiência em pontos (escala Saeb)
    "VL_NOTA_PORTUGUES": "NOTA_LP",
    "VL_NOTA_MEDIA": "NOTA_N",            # nota padronizada N, 0 a 10
    "VL_INDICADOR_REND": "IND_REND",      # rendimento (P), 0 a 1
    "VL_OBSERVADO": "IDEB",
}

# Faixas de plausibilidade só para alertar; valores fora delas não são removidos
FAIXAS = {"NOTA_MT": (100, 450), "NOTA_LP": (100, 450), "NOTA_N": (0, 10), "IND_REND": (0, 1), "IDEB": (0, 10)}


def transformar(camada: str) -> pl.DataFrame:
    cfg = CAMADAS[camada]
    partes = [pl.read_parquet(INTERIM_DIR / f"saeb_{cfg['nivel']}_{e}.parquet") for e in cfg["etapas"]]
    df = pl.concat(partes, how="vertical_relaxed")

    if camada == "estadual":
        df = df.filter(pl.col("NIVEL") == "UF").drop("NIVEL", "REGIAO_UF")

    df = (
        df.filter((pl.col("REDE") == cfg["rede"]) & pl.col("ANO").is_in(ANOS))
        .rename(RENOMEAR)
        # ANO em Int32 para casar com censo_matriculas (as bases de gasto seguem o mesmo padrão no merge)
        .with_columns(pl.col("ANO").cast(pl.Int32))
        .with_columns(pl.col("NOTA_MT").is_not_null().alias("TEM_NOTA"))
    )
    ids = cfg["chave"][:1] + [c for c in ("SG_UF", "NO_MUNICIPIO") if c in df.columns and c not in cfg["chave"]]
    return df.select(ids + ["REDE", "ETAPA", "ANO", *RENOMEAR.values(), "TEM_NOTA"]).sort(cfg["chave"])


def validar(df: pl.DataFrame, camada: str) -> None:
    cfg = CAMADAS[camada]
    print(f"\n[{camada.upper()}] {df.height} linhas | rede {cfg['rede']} | etapas {cfg['etapas']}")

    duplicadas = df.height - df.select(cfg["chave"]).unique().height
    print(f"  Chave {cfg['chave']} única: {'sim' if duplicadas == 0 else f'NÃO ({duplicadas} duplicadas)'}")

    unidade = cfg["chave"][0]
    print("  Unidades com nota, por etapa e ano:")
    print(
        df.group_by("ETAPA", "ANO")
        .agg(pl.col(unidade).filter(pl.col("TEM_NOTA")).n_unique().alias("com_nota"),
             pl.col(unidade).n_unique().alias("total"))
        .pivot(on="ETAPA", index="ANO", values=["com_nota", "total"])
        .sort("ANO")
    )

    for col, (lo, hi) in FAIXAS.items():
        fora = df.filter(pl.col(col).is_not_null() & ~pl.col(col).is_between(lo, hi)).height
        if fora:
            print(f"  [AVISO] {col}: {fora} valor(es) fora de [{lo}, {hi}]")

    # nota sem IDEB é esperado (IDEB exige rendimento); IDEB sem nota indicaria erro de leitura
    ideb_sem_nota = df.filter(pl.col("IDEB").is_not_null() & ~pl.col("TEM_NOTA")).height
    print(f"  Linhas com IDEB e sem nota (esperado 0): {ideb_sem_nota}")

    print("  Média de NOTA_MT por etapa e ano:")
    print(df.group_by("ETAPA", "ANO").agg(pl.col("NOTA_MT").mean().round(1))
          .pivot(on="ETAPA", index="ANO", values="NOTA_MT").sort("ANO"))


def conferir_codigos(df: pl.DataFrame) -> None:
    ibge = set(pl.read_parquet(INTERIM_DIR / "ibge_transformado.parquet")["CO_MUNICIPIO"].to_list())
    fora = sorted(set(df["CO_MUNICIPIO"].to_list()) - ibge)
    print(f"  Códigos de município fora da base do IBGE (Censo 2022): {len(fora)} {fora[:10]}")


def conferir_ufs(df: pl.DataFrame) -> None:
    faltam = df.filter(pl.col("TEM_NOTA")).group_by("ETAPA", "ANO").agg(pl.col("SG_UF").n_unique().alias("n")).filter(pl.col("n") < 27)
    print(f"  Etapa/ano com menos de 27 UFs com nota: {faltam.sort('ETAPA', 'ANO').rows() or 'nenhum'}")


if __name__ == "__main__":
    for camada in CAMADAS:
        df = transformar(camada)
        destino = INTERIM_DIR / f"saeb_{camada}_transformado.parquet"
        df.write_parquet(destino)
        validar(df, camada)
        conferir_codigos(df) if camada == "municipal" else conferir_ufs(df)
        print(f"  [OK] {destino.name}")
