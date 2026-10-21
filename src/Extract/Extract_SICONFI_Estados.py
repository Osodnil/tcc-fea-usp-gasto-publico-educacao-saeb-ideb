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
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
ANEXO = "DCA-Anexo I-E"
ANO_INICIO, ANO_FIM = 2014, 2025

UF_COD = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29", "MG": "31", "ES": "32", "RJ": "33", "SP": "35", "PR": "41",
    "SC": "42", "RS": "43", "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}

# "12 - Educação" (total da função) ou "12.361 - Ensino Fundamental" (subfunção)
PADRAO_CONTA = re.compile(r"^12(\s*-|\.\d{3})")


def buscar(ano: int, id_ente: str):
    """Lista de itens; None se a API falhar (para não confundir com 'sem dados')."""
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


def extrair():
    linhas, status = [], []
    for uf, cod in UF_COD.items():
        for ano in range(ANO_INICIO, ANO_FIM + 1):
            itens = buscar(ano, cod)
            if itens is None:
                status.append({"UF": uf, "ANO": ano, "STATUS": "erro_api"})
            else:
                sel = [it for it in itens if PADRAO_CONTA.match(it.get("conta") or "")]
                estado = "ok" if sel else ("sem_dados" if not itens else "sem_funcao_12")
                status.append({"UF": uf, "ANO": ano, "STATUS": estado})
                for it in sel:
                    linhas.append({
                        "UF": uf, "ANO": ano, "CONTA": it.get("conta"),
                        "COLUNA": it.get("coluna"), "VALOR": it.get("valor"),
                    })
            time.sleep(0.15)
        print(f"  {uf} concluído")
    return pl.DataFrame(linhas, infer_schema_length=None), pl.DataFrame(status)


if __name__ == "__main__":
    df, status = extrair()
    df = df.with_columns(
        pl.col("VALOR").cast(pl.Float64, strict=False),
        pl.col("CONTA").str.extract(r"^12\.(\d{3})", 1).alias("SUBF"),  # nulo = total da função 12
    )
    destino = INTERIM_DIR / "siconfi_estados_funcao12.parquet"
    df.write_parquet(destino)
    print(f"\n[OK] {df.height} linhas salvas em {destino}")

    print("\n[1] STATUS DA EXTRAÇÃO (UF-anos)")
    print(status.group_by("STATUS").agg(pl.len().alias("uf_anos")))
    problemas = status.filter(pl.col("STATUS") != "ok")
    if problemas.height:
        with pl.Config(tbl_rows=40):
            print(problemas.group_by(["UF", "STATUS"]).agg(pl.col("ANO").sort().alias("anos")).sort("UF"))

    pagas = df.filter(pl.col("COLUNA") == "Despesas Pagas")

    def anos_com(cond: pl.Expr, de: int, ate: int) -> pl.Expr:
        return pl.col("ANO").filter(cond & pl.col("ANO").is_between(de, ate)).n_unique()

    print("\n[2] ANOS COM DADO POR UF (despesa paga)")
    with pl.Config(tbl_rows=30):
        print(
            pagas.group_by("UF")
            .agg(
                anos_com(pl.col("SUBF").is_null(), 2017, 2025).alias("total12_2017_25"),
                anos_com(pl.col("SUBF") == "364", 2017, 2025).alias("sup364_2017_25"),
                anos_com(pl.col("SUBF").is_null(), 2014, 2016).alias("total12_2014_16"),
            )
            .sort("UF")
        )

    t = pagas.filter(pl.col("ANO") == 2023)
    tot = t.filter(pl.col("SUBF").is_null()).select("UF", pl.col("VALOR").alias("TOTAL"))
    sup = t.filter(pl.col("SUBF") == "364").select("UF", pl.col("VALOR").alias("SUP"))
    print("\n[3] PESO DO ENSINO SUPERIOR (12.364) NO TOTAL DA FUNÇÃO 12, 2023")
    with pl.Config(tbl_rows=30):
        print(
            tot.join(sup, on="UF", how="left")
            .with_columns(
                (pl.col("TOTAL") / 1e9).round(2).alias("TOTAL_BI"),
                (pl.col("SUP").fill_null(0) / pl.col("TOTAL")).round(3).alias("PCT_SUPERIOR"),
            )
            .select("UF", "TOTAL_BI", "PCT_SUPERIOR")
            .sort("PCT_SUPERIOR", descending=True)
        )