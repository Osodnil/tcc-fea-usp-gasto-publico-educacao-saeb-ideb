import sys
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
# Pasta de saída opcional como 1º argumento (usada para conferir contra os parquets já existentes)
INTERIM_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"
ENTIDADE = "Despesas_Funcao_Educacao_Siope"

ANO_INICIO, ANO_FIM = 2017, 2025
PERIODO = 6  # bimestre 6 = acumulado do ano, como no Extract_SIOPE.py

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]

# Mantém as duas camadas (TIPO Municipal e Estadual); o filtro fica para o Transform
COLUNAS = [
    "TIPO", "NUM_ANO", "SIG_UF", "COD_MUNI", "NOM_MUNI", "DES_SUBF",
    "VAL_DESP_EMPE", "VAL_DESP_LIQU", "VAL_DESP_PAGA",
]
COLUNAS_VALOR = ["VAL_DESP_EMPE", "VAL_DESP_LIQU", "VAL_DESP_PAGA"]


def buscar_pagina(url: str, params: dict | None = None) -> dict:
    for tentativa in range(3):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if tentativa == 2:
                raise
            time.sleep(2 * (tentativa + 1))


def buscar_tudo(ano: int, uf: str) -> list[dict]:
    """Busca uma UF/ano, seguindo a paginação OData (@odata.nextLink) caso exista."""
    url = f"{API_BASE}{ENTIDADE}(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    params = {"@Ano_Consulta": ano, "@Num_Peri": PERIODO, "@Sig_UF": f"'{uf}'", "$format": "json"}

    registros, proxima_url, proximos_params = [], url, params
    while proxima_url:
        dados = buscar_pagina(proxima_url, proximos_params)
        registros.extend(dados.get("value", []))
        proxima_url = dados.get("@odata.nextLink")
        proximos_params = None  # o nextLink já vem com os parâmetros embutidos
    return registros


def extrair_ano(ano: int) -> pl.DataFrame | None:
    todos = []
    for uf in UFS:
        registros = buscar_tudo(ano, uf)
        if not registros:
            print(f"  [AVISO] {ano}/{uf}: 0 registros retornados")
        todos.extend(registros)
        time.sleep(0.2)

    if not todos:
        print(f"[AVISO] {ano}: nenhum registro em nenhuma UF — pulando este ano.")
        return None

    # infer_schema_length=None: valores de texto no meio das colunas numéricas
    # (mesmo problema visto no Extract_SIOPE.py em 2018)
    df = pl.DataFrame(todos, infer_schema_length=None).select(COLUNAS)

    for c in COLUNAS_VALOR:
        nao_numerico = df.filter(pl.col(c).is_not_null() & pl.col(c).cast(pl.Float64, strict=False).is_null())
        if nao_numerico.height > 0:
            print(f"  [AVISO] {ano}/{c}: {nao_numerico.height} valor(es) não numérico(s) -> {nao_numerico[c].unique().to_list()}")

    return df.with_columns(
        [pl.col(c).cast(pl.Float64, strict=False) for c in COLUNAS_VALOR]
        + [
            pl.col("NUM_ANO").cast(pl.Int64),
            pl.col("COD_MUNI").cast(pl.Int64, strict=False),  # 6 dígitos; a conversão para 7 fica no Transform
            # Código = primeira sequência de 3 dígitos do rótulo. Cobre "361 - Ensino Fundamental"
            # (até 2023), "361" (2024-2025) e "SubFunção 361 - Fonte 01"; rótulos sem código ficam nulos.
            pl.col("DES_SUBF").str.extract(r"(\d{3})", 1).alias("COD_SUBF"),
            # Linhas "TOTAL 365 - ..." repetem o valor das linhas de detalhe e não podem ser somadas
            pl.col("DES_SUBF").str.strip_chars().str.to_uppercase().str.starts_with("TOTAL").alias("EH_TOTAL"),
        ]
    )


if __name__ == "__main__":
    print(f"Saída: {INTERIM_DIR}")
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n[PROCESSANDO] {ano}")
        df = extrair_ano(ano)
        if df is None:
            continue
        destino = INTERIM_DIR / f"siope_funcao_{ano}_extraido.parquet"
        df.write_parquet(destino)
        print(f"[OK] {ano}: {df.height} linhas | {df.filter(pl.col('TIPO') == 'Municipal')['COD_MUNI'].n_unique()} "
              f"municípios | {df.filter(pl.col('TIPO') == 'Estadual')['SIG_UF'].n_unique()} UFs com linha estadual")
