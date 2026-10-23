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
RAW_DIR = BASE_DIR / "data" / "raw" / "Microdados ENEM"
INTERIM_DIR = BASE_DIR / "data" / "interim"
SAIDA_DIR = INTERIM_DIR / "diagnosticos"
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

ANOS = range(2013, 2024)
ANOS_DETALHE = [2013, 2014, 2015]  # 2015 entra como referência de um ano "normal"


def parquet_do_ano(ano: int) -> Path:
    return INTERIM_DIR / f"enem_{ano}_extraido.parquet"


def matriz_preenchimento() -> None:
    """Proporção de valores não nulos de cada coluna, por ano. Detecta colunas
    que existem mas vêm vazias (ex.: campo suprimido por LGPD)."""
    por_ano: dict[int, dict] = {}
    total_linhas: dict[int, int] = {}

    for ano in ANOS:
        caminho = parquet_do_ano(ano)
        if not caminho.exists():
            print(f"[AVISO] Sem parquet para {ano}: {caminho.name}")
            continue
        lf = pl.scan_parquet(caminho)
        colunas = [c for c in lf.collect_schema().names() if c not in ("NU_INSCRICAO", "ANO")]
        resultado = lf.select(
            [pl.len().alias("__linhas__")]
            + [pl.col(c).is_not_null().mean().alias(c) for c in colunas]
        ).collect().to_dicts()[0]
        total_linhas[ano] = resultado.pop("__linhas__")
        por_ano[ano] = resultado

    todas = list(dict.fromkeys(c for d in por_ano.values() for c in d))
    tabela = {"coluna": todas}
    for ano, d in por_ano.items():
        tabela[str(ano)] = [round(d[c], 3) if c in d else None for c in todas]
    df = pl.DataFrame(tabela)

    df.write_csv(SAIDA_DIR / "enem_preenchimento_por_ano.csv")
    print("\n[1] PROPORÇÃO DE VALORES NÃO NULOS, POR COLUNA E ANO")
    print(f"    Linhas por ano: {total_linhas}")
    with pl.Config(tbl_rows=60, tbl_cols=15, tbl_width_chars=220):
        print(df)


def diagnostico_ausencia_e_notas() -> None:
    """Quem faltou tem nota vazia (null) ou nota 0? Valores reais, sem recodificar."""
    for ano in ANOS_DETALHE:
        caminho = parquet_do_ano(ano)
        if not caminho.exists():
            continue
        lf = pl.scan_parquet(caminho)
        print(f"\n[2] ANO {ano}")

        for coluna in ["TP_PRESENCA_LC", "TP_STATUS_REDACAO"]:
            valores = lf.select(coluna).collect()[coluna].value_counts().sort(coluna)
            print(f"  Valores de {coluna}:")
            print(valores)

        for presenca, nota in [("TP_PRESENCA_LC", "NU_NOTA_REDACAO"), ("TP_PRESENCA_MT", "NU_NOTA_MT")]:
            resumo = (
                lf.group_by(presenca)
                .agg(
                    pl.len().alias("linhas"),
                    pl.col(nota).is_not_null().sum().alias("nota_nao_nula"),
                    (pl.col(nota) == 0).sum().alias("nota_zero"),
                    pl.col(nota).mean().alias("nota_media"),
                )
                .sort(presenca)
                .collect()
            )
            print(f"  {nota} segundo {presenca}:")
            print(resumo)


def diagnostico_treineiro() -> None:
    """Peso dos treineiros nos anos em que IN_TREINEIRO existe (2015-2023)."""
    linhas = []
    for ano in range(2015, 2024):
        caminho = parquet_do_ano(ano)
        if not caminho.exists():
            continue
        r = pl.scan_parquet(caminho).select(
            pl.len().alias("linhas"),
            (pl.col("IN_TREINEIRO") == "1").sum().alias("treineiros"),
            pl.col("CO_MUNICIPIO_ESC").is_not_null().sum().alias("com_escola"),
            ((pl.col("IN_TREINEIRO") == "1") & pl.col("CO_MUNICIPIO_ESC").is_not_null())
            .sum()
            .alias("treineiros_com_escola"),
        ).collect().to_dicts()[0]
        linhas.append({
            "ANO": ano,
            "pct_treineiros_geral": round(r["treineiros"] / r["linhas"], 4),
            "pct_com_escola": round(r["com_escola"] / r["linhas"], 4),
            "pct_treineiros_entre_com_escola": (
                round(r["treineiros_com_escola"] / r["com_escola"], 4) if r["com_escola"] else None
            ),
        })
    df = pl.DataFrame(linhas)
    df.write_csv(SAIDA_DIR / "enem_treineiros_por_ano.csv")
    print("\n[3] PESO DOS TREINEIROS (2015-2023)")
    print(df)


def colunas_raw(ano: int) -> list[str]:
    arquivo = next(
        f for f in RAW_DIR.rglob("*.csv")
        if f.stem.lower().startswith("microdados_enem") and str(ano) in f.stem
    )
    return pl.scan_csv(arquivo, separator=";", encoding="utf8-lossy", n_rows=0).collect_schema().names()


def diferencas_de_schema() -> None:
    """Colunas TP_* e IN_* que existem em 2015 e não em 2013 (e vice-versa),
    para ver se algum outro campo pode substituir IN_TREINEIRO."""
    c13, c15 = set(colunas_raw(2013)), set(colunas_raw(2015))

    def filtra(conjunto):
        return sorted(c for c in conjunto if c.startswith(("TP_", "IN_")))

    print("\n[4] DIFERENÇAS DE SCHEMA (só colunas TP_* e IN_*)")
    print(f"  Só em 2015: {filtra(c15 - c13)}")
    print(f"  Só em 2013: {filtra(c13 - c15)}")
    print(f"  TP_ST_CONCLUSAO em 2013? {'TP_ST_CONCLUSAO' in c13} | em 2015? {'TP_ST_CONCLUSAO' in c15}")


if __name__ == "__main__":
    matriz_preenchimento()
    diagnostico_ausencia_e_notas()
    diagnostico_treineiro()
    diferencas_de_schema()
    print(f"\n[OK] Tabelas completas salvas em {SAIDA_DIR}")