import polars as pl
from pathlib import Path
import xlsxwriter


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
INTERIM_DIR = BASE_DIR / "data" / "interim"
SAIDA = INTERIM_DIR / "diagnosticos" / "visualizacao_siope_ideb.xlsx"
SAIDA.parent.mkdir(parents=True, exist_ok=True)


def carregar_siope() -> pl.DataFrame:
    arquivos = sorted(INTERIM_DIR.glob("siope_*_extraido.parquet"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo siope_*_extraido.parquet em {INTERIM_DIR}")
    return pl.concat([pl.read_parquet(a) for a in arquivos], how="diagonal_relaxed")


def carregar_ideb() -> pl.DataFrame:
    caminho = INTERIM_DIR / "ideb_transformado.parquet"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não encontrado — rode o Transform do IDEB primeiro.")
    return pl.read_parquet(caminho)


def resumo_siope(df: pl.DataFrame) -> pl.DataFrame:
    total_zerado = df.filter(
        (pl.col("VAL_DESP_PAGA") == 0) | pl.col("VAL_DESP_PAGA").is_null()
    )
    if total_zerado.height > 0:
        print(f"[AVISO] {total_zerado.height} linha(s) com despesa total (VAL_DESP_PAGA) zerada ou nula:")
        print(
            total_zerado.group_by("NUM_ANO")
            .agg(pl.len().alias("municipios_afetados"))
            .sort("NUM_ANO")
        )

    df = df.with_columns(
        # pl.when evita a divisão por zero virar inf/NaN: vira null, que o
        # Excel aceita tranquilamente (célula em branco, não um erro).
        pl.when(pl.col("VAL_DESP_PAGA") > 0)
        .then(pl.col("VL_DESP_PAGA_EDU") / pl.col("VAL_DESP_PAGA"))
        .otherwise(None)
        .alias("PCT_GASTO_EM_EDUCACAO")
    )

    return (
        df.group_by("NUM_ANO")
        .agg(
            pl.len().alias("MUNICIPIOS"),
            pl.col("VL_DESP_PAGA_EDU").mean().round(0).alias("DESPESA_EDU_MEDIA"),
            pl.col("VL_DESP_PAGA_EDU").median().round(0).alias("DESPESA_EDU_MEDIANA"),
            pl.col("PCT_GASTO_EM_EDUCACAO").mean().round(4).alias("PCT_MEDIO_EM_EDUCACAO"),
        )
        .sort("NUM_ANO")
        .rename({"NUM_ANO": "ANO"})
    )


def resumo_ideb(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by(["ANO", "REDE"])
        .agg(
            pl.len().alias("LINHAS"),
            pl.col("IDEB").is_not_null().sum().alias("COM_IDEB"),
            pl.col("IDEB").mean().round(2).alias("IDEB_MEDIO"),
        )
        .sort(["ANO", "REDE"])
    )


def amostra_cruzada(siope: pl.DataFrame, ideb: pl.DataFrame, n_municipios: int = 20) -> pl.DataFrame:
    """Prévia visual, NÃO o merge definitivo. Usa REDE='Municipal' do IDEB de
    propósito: o SIOPE declara o gasto do GOVERNO MUNICIPAL, então o cruzamento
    metodologicamente mais direto é com a rede municipal de ensino — escolas
    estaduais são financiadas pelo orçamento do estado, não capturado aqui.

    ATENÇÃO: COD_MUNI do SIOPE tem 6 dígitos; CO_MUNICIPIO das demais bases
    tem 7 (dígito verificador no final). Aqui truncamos para 6 só para esta
    prévia — a forma definitiva de tratar isso fica para o Transform/merge.
    """
    siope_fmt = siope.rename({"NUM_ANO": "ANO"}).with_columns(
        pl.col("COD_MUNI").cast(pl.Utf8).alias("COD_MUNI_6D")
    )

    ideb_municipal = ideb.filter(pl.col("REDE") == "Municipal").with_columns(
        pl.col("CO_MUNICIPIO").str.slice(0, 6).alias("COD_MUNI_6D")
    )

    maiores = (
        siope_fmt.filter(pl.col("ANO") == siope_fmt["ANO"].max())
        .sort("NUM_POPU", descending=True)
        .head(n_municipios)
        .select(["COD_MUNI_6D"])
    )

    return (
        maiores.join(siope_fmt, on="COD_MUNI_6D", how="left")
        .join(ideb_municipal.select(["COD_MUNI_6D", "ANO", "IDEB"]), on=["COD_MUNI_6D", "ANO"], how="left")
        .select(["NOM_MUNI", "SIG_UF", "ANO", "NUM_POPU", "VL_DESP_PAGA_EDU", "IDEB"])
        .sort(["NOM_MUNI", "ANO"])
    )


if __name__ == "__main__":
    siope = carregar_siope()
    ideb = carregar_ideb()

    print(f"SIOPE: {siope.height} linhas, {siope['NUM_ANO'].n_unique()} anos")
    print(f"IDEB: {ideb.height} linhas, {ideb['ANO'].n_unique()} anos")

    wb = xlsxwriter.Workbook(str(SAIDA))

    resumo_siope(siope).write_excel(workbook=wb, worksheet="SIOPE - Resumo por Ano", autofit=True, table_style="Table Style Medium 2")
    resumo_ideb(ideb).write_excel(workbook=wb, worksheet="IDEB - Resumo Ano-Rede", autofit=True, table_style="Table Style Medium 2")
    amostra_cruzada(siope, ideb).write_excel(workbook=wb, worksheet="Prévia Cruzamento (20 maiores)", autofit=True, table_style="Table Style Medium 6")
    siope.head(200).write_excel(workbook=wb, worksheet="SIOPE - Amostra Bruta", autofit=True)
    ideb.head(200).write_excel(workbook=wb, worksheet="IDEB - Amostra Bruta", autofit=True)

    wb.close()
    print(f"\n[OK] Planilha gerada em {SAIDA}")