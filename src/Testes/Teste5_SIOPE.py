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
RAW_CENSO = BASE_DIR / "data" / "raw" / "Microdados Censo Escolar"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

ANO_INICIO, ANO_FIM = 2017, 2025
COLUNAS_MAT = ["QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED"]
CHAVES = ["CO_ENTIDADE", "CO_MUNICIPIO", "SG_UF", "TP_DEPENDENCIA"]
MAPA_REDE = {"1": "Federal", "2": "Estadual", "3": "Municipal", "4": "Privada"}


def csvs_do_ano(ano: int) -> list[Path]:
    return [
        f for f in RAW_CENSO.rglob("*")
        if f.is_file() and f.suffix.lower() == ".csv"
        and f.parent.name.lower() == "dados"
        and f.relative_to(RAW_CENSO).parts[0] == str(ano)
        and not f.stem.lower().startswith("md5")
    ]


def escolher(arquivos: list[Path], termo: str) -> Path:
    achados = [f for f in arquivos if termo in f.stem.lower() and "suplemento" not in f.stem.lower()]
    if len(achados) != 1:
        raise ValueError(f"Esperava 1 arquivo com '{termo}', achei {[f.name for f in achados]}")
    return achados[0]


def colunas(caminho: Path) -> list[str]:
    return pl.scan_csv(caminho, separator=";", encoding="utf8-lossy", n_rows=0).collect_schema().names()


def ler(caminho: Path, desejadas: list[str], ano: int) -> pl.DataFrame:
    disponiveis = colunas(caminho)
    faltam = [c for c in desejadas if c not in disponiveis]
    if faltam:
        print(f"  [AVISO] {ano} / {caminho.name}: colunas ausentes -> {faltam}")
    usar = [c for c in desejadas if c in disponiveis]
    return (
        pl.scan_csv(caminho, separator=";", encoding="utf8-lossy", infer_schema_length=0)
        .select(usar)
        .collect()
    )


def carregar_ano(ano: int) -> pl.DataFrame:
    arquivos = csvs_do_ano(ano)
    if ano <= 2024:
        df = ler(escolher(arquivos, "microdados_ed_basica"), CHAVES + COLUNAS_MAT, ano)
    else:
        escola = ler(escolher(arquivos, "tabela_escola"), CHAVES, ano)
        mat_path = escolher(arquivos, "tabela_matricula")
        print(f"  [INFO] {ano}: colunas da Tabela de Matrícula que contêm 'CO_': "
              f"{[c for c in colunas(mat_path) if c.startswith('CO_')][:10]}")
        mat = ler(mat_path, ["CO_ENTIDADE"] + COLUNAS_MAT, ano)
        mat = mat.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in COLUNAS_MAT if c in mat.columns])
        print(f"  [INFO] {ano}: Tabela de Matrícula tem {mat.height} linhas e "
              f"{mat['CO_ENTIDADE'].n_unique()} escolas distintas")
        mat = mat.group_by("CO_ENTIDADE").agg([pl.col(c).sum() for c in COLUNAS_MAT if c in mat.columns])
        df = escola.join(mat, on="CO_ENTIDADE", how="left")
        sem_mat = df.filter(pl.col(COLUNAS_MAT[0]).is_null()).height
        print(f"  [INFO] {ano}: {sem_mat} de {df.height} escolas sem linha na Tabela de Matrícula")

    print(f"  [INFO] {ano}: {df.height} linhas, {df['CO_ENTIDADE'].n_unique()} CO_ENTIDADE distintos")

    return df.with_columns(
        [pl.col(c).cast(pl.Float64, strict=False) for c in COLUNAS_MAT if c in df.columns]
        + [pl.col("TP_DEPENDENCIA").replace_strict(MAPA_REDE, default=None).alias("REDE")]
    )


def agregar(df: pl.DataFrame, ano: int) -> pl.DataFrame:
    mat = [c for c in COLUNAS_MAT if c in df.columns]
    return (
        df.group_by(["CO_MUNICIPIO", "SG_UF", "REDE"])
        .agg([pl.len().alias("N_LINHAS")] + [pl.col(c).sum() for c in mat])
        .with_columns(pl.lit(ano).alias("ANO"))
    )


if __name__ == "__main__":
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n[PROCESSANDO] {ano}")
        agg = agregar(carregar_ano(ano), ano)
        agg.write_parquet(INTERIM_DIR / f"censo_matriculas_{ano}.parquet")
        print(f"[OK] {ano}: {agg.height} combinações município x rede")

    todos = pl.concat(
        [pl.read_parquet(INTERIM_DIR / f"censo_matriculas_{a}.parquet") for a in range(ANO_INICIO, ANO_FIM + 1)],
        how="diagonal_relaxed",
    )
    print("\n[CONTINUIDADE] Matrículas nacionais (milhões) por ano — Municipal e Estadual")
    for col in [c for c in COLUNAS_MAT if c in todos.columns]:
        print(f"\n{col}")
        print(
            todos.filter(pl.col("REDE").is_in(["Municipal", "Estadual"]))
            .group_by(["ANO", "REDE"]).agg((pl.col(col).sum() / 1e6).round(2).alias("milhoes"))
            .pivot(on="REDE", index="ANO", values="milhoes").sort("ANO")
        )