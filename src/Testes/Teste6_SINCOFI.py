import time
import requests
import polars as pl

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
ANEXO = "DCA-Anexo I-E"

ENTES = {"MG": "31", "RS": "43", "SP": "35"}

# Etapa identificada pelo código da subfunção OU pelo nome (não sei qual dos dois a API traz)
FUND = r"(?i)(\b361\b|ensino fundamental)"
MED = r"(?i)(\b362\b|ensino m[eé]dio)"

# Referência do SIOPE (camada estadual, SP 2023, despesa paga), em R$ bilhões
REF_SIOPE_SP_2023 = {"361 Fundamental": 13.504, "362 Médio": 9.667}


def buscar(ano: int, id_ente: str) -> list[dict]:
    itens, offset = [], 0
    while True:
        params = {"an_exercicio": ano, "id_ente": id_ente, "no_anexo": ANEXO, "offset": offset}
        for tentativa in range(3):
            try:
                r = requests.get(BASE, params=params, timeout=90)
                r.raise_for_status()
                break
            except requests.RequestException:
                if tentativa == 2:
                    raise
                time.sleep(2 * (tentativa + 1))
        dados = r.json()
        pagina = dados.get("items", [])
        itens.extend(pagina)
        if not dados.get("hasMore") or not pagina:
            break
        offset += len(pagina)
        time.sleep(0.2)
    return itens


def tabela(itens: list[dict]) -> pl.DataFrame | None:
    if not itens:
        return None
    df = pl.DataFrame(itens, infer_schema_length=None)
    if "valor" in df.columns:
        df = df.with_columns(pl.col("valor").cast(pl.Float64, strict=False))
    partes = [pl.col(c).cast(pl.Utf8).fill_null("") for c in ("conta", "rotulo") if c in df.columns]
    return df.with_columns(pl.concat_str(partes or [pl.lit("")], separator=" | ").alias("_texto"))


def etapa(df: pl.DataFrame, regex: str) -> pl.DataFrame:
    return df.filter(pl.col("_texto").str.contains(regex))


def mostrar(df: pl.DataFrame) -> None:
    campos = [c for c in ("conta", "rotulo", "coluna", "valor") if c in df.columns]
    saida = df.select(campos)
    if "valor" in saida.columns:
        saida = saida.with_columns((pl.col("valor") / 1e9).round(3).alias("valor_bi")).drop("valor")
    with pl.Config(tbl_rows=60, fmt_str_lengths=60, tbl_width_chars=220):
        print(saida)


def passo1_estrutura() -> None:
    print("=" * 70 + "\n[1] ESTRUTURA DO ANEXO I-E — MG, 2023\n" + "=" * 70)
    df = tabela(buscar(2023, ENTES["MG"]))
    if df is None:
        print("  Nada retornado para MG 2023.")
        return
    print(f"{df.height} itens | campos: {df.columns}")
    for campo in ("coluna", "rotulo"):
        if campo in df.columns:
            print(f"\nValores distintos de '{campo}': {df[campo].unique().sort().to_list()[:40]}")
    print("\nLinhas de Ensino Fundamental e Médio:")
    mostrar(pl.concat([etapa(df, FUND), etapa(df, MED)]))


def passo2_conferencia() -> None:
    print("\n" + "=" * 70 + "\n[2] CONFERÊNCIA COM O SIOPE — SP estadual, 2023\n" + "=" * 70)
    print(f"Referência SIOPE (paga): {REF_SIOPE_SP_2023}")
    df = tabela(buscar(2023, ENTES["SP"]))
    if df is None:
        print("  Nada retornado para SP 2023.")
        return
    for nome, regex in (("361 Fundamental", FUND), ("362 Médio", MED)):
        print(f"\n{nome}:")
        mostrar(etapa(df, regex))


def passo3_lacunas() -> None:
    print("\n" + "=" * 70 + "\n[3] MG e RS NO SICONFI, 2017-2025\n" + "=" * 70)
    for uf in ("MG", "RS"):
        for ano in range(2017, 2026):
            df = tabela(buscar(ano, ENTES[uf]))
            if df is None:
                print(f"  {uf} {ano}: SEM DADOS")
                continue
            soma = (
                etapa(df, FUND).group_by("coluna").agg((pl.col("valor").sum() / 1e9).round(2).alias("bi"))
                if "coluna" in df.columns else None
            )
            resumo = dict(zip(soma["coluna"].to_list(), soma["bi"].to_list())) if soma is not None else {}
            print(f"  {uf} {ano}: {df.height} itens | FUND={etapa(df, FUND).height} | MED={etapa(df, MED).height} | soma FUND por coluna (bi): {resumo}")
            time.sleep(0.2)


def passo4_sondagens() -> None:
    print("\n" + "=" * 70 + "\n[4] SP ESTADUAL ANTES DE 2017 (itens retornados)\n" + "=" * 70)
    for ano in range(2013, 2017):
        itens = buscar(ano, ENTES["SP"])
        print(f"  SP {ano}: {len(itens)} itens")
        time.sleep(0.2)

    print("\n" + "=" * 70 + "\n[5] MUNICÍPIO — Belo Horizonte (3106200), 2023\n" + "=" * 70)
    df = tabela(buscar(2023, "3106200"))
    if df is None:
        print("  Nada retornado.")
    else:
        print(f"{df.height} itens")
        mostrar(pl.concat([etapa(df, FUND), etapa(df, MED)]))


if __name__ == "__main__":
    for passo in (passo1_estrutura, passo2_conferencia, passo3_lacunas, passo4_sondagens):
        try:
            passo()
        except Exception as e:
            print(f"\n[ERRO em {passo.__name__}] {type(e).__name__}: {e}")