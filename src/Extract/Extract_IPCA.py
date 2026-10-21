import re
import requests
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
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all?formato=json"
BASE_ANO = 2025
ANO_MIN, ANO_MAX = 2013, 2025


def baixar_mensal() -> pl.DataFrame:
    r = requests.get(URL, timeout=120)
    r.raise_for_status()
    dados = r.json()
    cab, linhas = dados[0], dados[1:]
    print(f"[INFO] {len(linhas)} meses retornados")

    chaves_c = [k for k in cab if k.startswith("D") and k.endswith("C")]
    # a ordem das dimensões (D1, D2, D3) varia: acha o mês e a variável pelo cabeçalho
    chave_mes = next((k for k in chaves_c if "mês" in str(cab[k]).lower()), None)
    if chave_mes is None:
        chave_mes = next(
            (k for k in chaves_c if re.fullmatch(r"(19|20)\d{4}", str(linhas[0][k]))), None
        )
    if chave_mes is None:
        raise ValueError(f"Não achei a coluna do mês. Cabeçalho: {cab}")

    chave_var = next((k for k in chaves_c if "variável" in str(cab[k]).lower()), None)
    if chave_var:
        print(f"[INFO] Variável: {linhas[0].get(chave_var[:-1] + 'N')} (código {linhas[0].get(chave_var)})")

    mensal = (
        pl.DataFrame({"PERIODO": [l[chave_mes] for l in linhas], "INDICE": [l["V"] for l in linhas]})
        .with_columns(
            pl.col("PERIODO").cast(pl.Int64, strict=False),
            pl.col("INDICE").cast(pl.Float64, strict=False),
        )
        .drop_nulls()
        .with_columns((pl.col("PERIODO") // 100).alias("ANO"), (pl.col("PERIODO") % 100).alias("MES"))
        .sort("PERIODO")
    )
    print(f"[INFO] Período: {mensal['PERIODO'].min()} a {mensal['PERIODO'].max()}")
    return mensal


if __name__ == "__main__":
    mensal = baixar_mensal()

    anual = (
        mensal.group_by("ANO")
        .agg(
            pl.len().alias("MESES"),
            pl.col("INDICE").mean().alias("INDICE_MEDIO"),
            pl.col("INDICE").filter(pl.col("MES") == 12).first().alias("INDICE_DEZ"),
        )
        .sort("ANO")
        .with_columns(
            ((pl.col("INDICE_DEZ") / pl.col("INDICE_DEZ").shift(1) - 1) * 100).round(2).alias("IPCA_DEZ_DEZ_PCT")
        )
    )

    base = anual.filter(pl.col("ANO") == BASE_ANO)
    if base.is_empty() or base["MESES"][0] < 12:
        raise ValueError(f"O ano-base {BASE_ANO} não tem os 12 meses na série.")

    saida = (
        anual.with_columns((base["INDICE_MEDIO"][0] / pl.col("INDICE_MEDIO")).round(4).alias("FATOR_PARA_BASE"))
        .filter(pl.col("ANO").is_between(ANO_MIN, ANO_MAX))
    )

    incompletos = saida.filter(pl.col("MESES") != 12)
    if incompletos.height:
        print(f"[AVISO] Anos sem 12 meses: {incompletos['ANO'].to_list()}")

    destino = INTERIM_DIR / "ipca_deflator_anual.parquet"
    saida.write_parquet(destino)
    print(f"\n[OK] Deflator salvo em {destino}")
    print(f"Valor em reais de {BASE_ANO} = valor nominal x FATOR_PARA_BASE\n")
    with pl.Config(tbl_rows=20):
        print(saida)