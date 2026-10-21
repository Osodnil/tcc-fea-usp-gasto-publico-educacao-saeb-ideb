import re
import time
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
SAIDA_DIR = INTERIM_DIR / "diagnosticos"
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
ANEXO = "DCA-Anexo I-E"
ANOS_AMOSTRA = [2017, 2021, 2024]
N_AMOSTRA = 40
ANOS_ESTADOS = range(2017, 2026)

UF_COD = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41",
    "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}


def ibge7(cod6) -> str:
    """Código de município de 6 dígitos (SIOPE) -> 7 dígitos (IBGE), pelo dígito verificador."""
    s = f"{int(cod6):06d}"
    soma = 0
    for i, ch in enumerate(s):
        p = int(ch) * (1 if i % 2 == 0 else 2)
        soma += p // 10 + p % 10
    return s + str((10 - soma % 10) % 10)


def buscar(ano: int, id_ente: str):
    """Devolve lista de itens; None se a API falhar (para não confundir com 'sem dados')."""
    itens, offset = [], 0
    while True:
        params = {"an_exercicio": ano, "id_ente": id_ente, "no_anexo": ANEXO, "offset": offset}
        r = None
        for tentativa in range(3):
            try:
                r = requests.get(API, params=params, timeout=90)
                r.raise_for_status()
                break
            except requests.RequestException:
                r = None
                time.sleep(2 * (tentativa + 1))
        if r is None:
            return None
        dados = r.json()
        pagina = dados.get("items", [])
        itens.extend(pagina)
        if not dados.get("hasMore") or not pagina:
            break
        offset += len(pagina)
        time.sleep(0.15)
    return itens


def valor_dca(itens, regex_conta: str, coluna: str = "Despesas Pagas"):
    soma, achou = 0.0, False
    for it in itens or []:
        if it.get("coluna") == coluna and re.search(regex_conta, it.get("conta") or ""):
            v = it.get("valor")
            if v is not None:
                soma += float(v)
                achou = True
    return soma if achou else None


def parte_a_municipal() -> None:
    print("=" * 70 + "\n[A] MUNICÍPIOS: SIOPE x SICONFI, subfunção 361, despesa paga\n" + "=" * 70)
    func = pl.concat(
        [pl.read_parquet(INTERIM_DIR / f"siope_funcao_{a}_extraido.parquet") for a in ANOS_AMOSTRA],
        how="diagonal_relaxed",
    )
    siope = (
        func.filter((pl.col("TIPO") == "Municipal") & (pl.col("COD_SUBF") == "361") & ~pl.col("EH_TOTAL"))
        .group_by(["NUM_ANO", "COD_MUNI"])
        .agg(pl.col("VAL_DESP_PAGA").sum().alias("SIOPE_361"))
    )
    pop = (
        pl.read_parquet(INTERIM_DIR / "siope_2024_extraido.parquet")
        .select([pl.col("COD_MUNI").cast(pl.Int64, strict=False), "NUM_POPU"])
        .drop_nulls()
        .unique("COD_MUNI")
        .sort("NUM_POPU")
    )
    amostra = pop.gather_every(max(1, pop.height // N_AMOSTRA)).head(N_AMOSTRA)

    linhas = []
    for row in amostra.iter_rows(named=True):
        for ano in ANOS_AMOSTRA:
            itens = buscar(ano, ibge7(row["COD_MUNI"]))
            linhas.append({
                "COD_MUNI": row["COD_MUNI"],
                "NUM_POPU": row["NUM_POPU"],
                "NUM_ANO": ano,
                "SICONFI_361": valor_dca(itens, r"^12\.361") if itens is not None else None,
                "ERRO_API": itens is None,
            })
            time.sleep(0.15)

    comp = (
        pl.DataFrame(linhas)
        .join(siope, on=["COD_MUNI", "NUM_ANO"], how="left")
        .with_columns(
            pl.when(pl.col("SIOPE_361") > 0)
            .then(pl.col("SICONFI_361") / pl.col("SIOPE_361"))
            .otherwise(None)
            .alias("RAZAO")
        )
    )
    comp.write_csv(SAIDA_DIR / "reconciliacao_municipal.csv")

    ok = comp.filter(pl.col("RAZAO").is_not_null())
    print(f"Comparações: {comp.height} | com razão calculável: {ok.height} | "
          f"sem valor no SICONFI: {comp['SICONFI_361'].is_null().sum()} | erros de API: {comp['ERRO_API'].sum()}")
    if ok.height:
        quantis = [round(ok["RAZAO"].quantile(p), 3) for p in (0.1, 0.25, 0.5, 0.75, 0.9)]
        print(f"Razão SICONFI/SIOPE — quantis 10/25/50/75/90: {quantis}")
        print(f"Dentro de ±5%: {ok['RAZAO'].is_between(0.95, 1.05).mean():.0%} | "
              f"dentro de ±20%: {ok['RAZAO'].is_between(0.8, 1.2).mean():.0%}")

    with pl.Config(tbl_rows=50, tbl_width_chars=160):
        print("\nTabela de 2024 (todas as linhas de 2017/2021 estão no CSV):")
        print(
            comp.filter(pl.col("NUM_ANO") == 2024)
            .with_columns((pl.col("SIOPE_361") / 1e6).round(1).alias("SIOPE_mi"),
                          (pl.col("SICONFI_361") / 1e6).round(1).alias("SICONFI_mi"),
                          pl.col("RAZAO").round(3))
            .select(["COD_MUNI", "NUM_POPU", "SIOPE_mi", "SICONFI_mi", "RAZAO"])
            .sort("NUM_POPU")
        )


def parte_b_estados() -> None:
    print("\n" + "=" * 70 + "\n[B] ESTADOS NO SICONFI: função 12 e subfunções 361/362 (paga, R$ bi)\n" + "=" * 70)
    linhas = []
    for uf, cod in UF_COD.items():
        for ano in ANOS_ESTADOS:
            itens = buscar(ano, cod)
            total = valor_dca(itens, r"^12\s*-")
            origem = "funcao" if total is not None else None
            if total is None:
                total = valor_dca(itens, r"^12\.\d{3}")
                origem = "soma_subfuncoes" if total is not None else None
            fund = valor_dca(itens, r"^12\.361")
            med = valor_dca(itens, r"^12\.362")
            linhas.append({
                "UF": uf, "ANO": ano, "ORIGEM": origem, "ERRO_API": itens is None,
                "TOTAL_12_BI": round(total / 1e9, 2) if total is not None else None,
                "FUND_BI": round(fund / 1e9, 2) if fund is not None else None,
                "MED_BI": round(med / 1e9, 2) if med is not None else None,
            })
            time.sleep(0.15)

    df = pl.DataFrame(linhas)
    df.write_csv(SAIDA_DIR / "siconfi_estados_funcao12.csv")

    print(f"Erros de API: {df['ERRO_API'].sum()} | origem do total: {df['ORIGEM'].value_counts().to_dicts()}")
    with pl.Config(tbl_rows=40, tbl_cols=12, tbl_width_chars=160):
        print("\nTotal da função 12 (R$ bi, pago), por UF e ano:")
        print(df.pivot(on="ANO", index="UF", values="TOTAL_12_BI").sort("UF"))
        print("\nAnos com dado, por UF (máximo 9):")
        print(
            df.group_by("UF")
            .agg(
                pl.col("TOTAL_12_BI").is_not_null().sum().alias("anos_total12"),
                pl.col("FUND_BI").is_not_null().sum().alias("anos_361"),
                pl.col("MED_BI").is_not_null().sum().alias("anos_362"),
            )
            .sort("UF")
        )


if __name__ == "__main__":
    for parte in (parte_a_municipal, parte_b_estados):
        try:
            parte()
        except Exception as e:
            print(f"\n[ERRO em {parte.__name__}] {type(e).__name__}: {e}")