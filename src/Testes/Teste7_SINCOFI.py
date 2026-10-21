import re
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


def varrer(caminho: Path) -> pl.LazyFrame:
    return pl.scan_csv(caminho, separator=";", encoding="utf8-lossy", infer_schema_length=0)


def colunas(caminho: Path) -> list[str]:
    return varrer(caminho).head(0).collect_schema().names()


def colunas_med_agregadas(cols: list[str]) -> list[str]:
    # QT_MAT_MED e derivadas, sem os cortes por série (_1.._4, _NS)
    return [c for c in cols if c.startswith("QT_MAT_MED") and not re.search(r"_(\d|NS)$", c)]


def totais_estadual_med(ano: int) -> dict[str, float]:
    arquivos = csvs_do_ano(ano)
    if ano <= 2024:
        caminho = escolher(arquivos, "microdados_ed_basica")
        med = colunas_med_agregadas(colunas(caminho))
        df = varrer(caminho).select(["TP_DEPENDENCIA"] + med).filter(pl.col("TP_DEPENDENCIA") == "2").collect()
    else:
        escola = varrer(escolher(arquivos, "tabela_escola")).select(["CO_ENTIDADE", "TP_DEPENDENCIA"]).collect()
        mat_caminho = escolher(arquivos, "tabela_matricula")
        med = colunas_med_agregadas(colunas(mat_caminho))
        mat = varrer(mat_caminho).select(["CO_ENTIDADE"] + med).collect()
        df = mat.join(escola, on="CO_ENTIDADE", how="inner").filter(pl.col("TP_DEPENDENCIA") == "2")
    return {c: round(df[c].cast(pl.Float64, strict=False).sum() / 1e6, 3) for c in med}


def escolas_sem_matricula(ano: int) -> pl.DataFrame:
    arquivos = csvs_do_ano(ano)
    if ano == 2024:
        df = (
            varrer(escolher(arquivos, "microdados_ed_basica"))
            .select(["TP_DEPENDENCIA", "QT_MAT_BAS"]).collect()
            .with_columns(pl.col("QT_MAT_BAS").cast(pl.Float64, strict=False))
        )
        sem = pl.col("QT_MAT_BAS").is_null() | (pl.col("QT_MAT_BAS") == 0)
        return df.group_by("TP_DEPENDENCIA").agg(pl.len().alias("escolas"), sem.sum().alias("sem_matricula"))
    escola = varrer(escolher(arquivos, "tabela_escola")).select(["CO_ENTIDADE", "TP_DEPENDENCIA"]).collect()
    mat = varrer(escolher(arquivos, "tabela_matricula")).select(["CO_ENTIDADE"]).collect()
    sem_linha = escola.join(mat, on="CO_ENTIDADE", how="anti")
    return (
        escola.group_by("TP_DEPENDENCIA").agg(pl.len().alias("escolas"))
        .join(sem_linha.group_by("TP_DEPENDENCIA").agg(pl.len().alias("sem_matricula")), on="TP_DEPENDENCIA", how="left")
    )


if __name__ == "__main__":
    print("[1] REDE ESTADUAL — TOTAIS NACIONAIS POR COLUNA QT_MAT_MED* (milhões de matrículas)")
    resultados = {ano: totais_estadual_med(ano) for ano in (2023, 2024, 2025)}
    todas = sorted({c for d in resultados.values() for c in d})
    tabela = pl.DataFrame({"coluna": todas, **{str(a): [resultados[a].get(c) for c in todas] for a in resultados}})
    with pl.Config(tbl_rows=40, tbl_width_chars=160):
        print(tabela)

    print("\n[2] ESCOLAS SEM MATRÍCULA (2024: QT_MAT_BAS nulo ou zero | 2025: sem linha na Tabela de Matrícula)")
    for ano in (2024, 2025):
        df = escolas_sem_matricula(ano).with_columns(
            pl.col("sem_matricula").fill_null(0),
        ).with_columns((pl.col("sem_matricula") / pl.col("escolas")).round(3).alias("proporcao")).sort("TP_DEPENDENCIA")
        print(f"\n{ano} (TP_DEPENDENCIA: 1 Federal, 2 Estadual, 3 Municipal, 4 Privada)")
        print(df)