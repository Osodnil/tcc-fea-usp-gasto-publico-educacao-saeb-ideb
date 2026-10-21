import requests
import polars as pl
from pathlib import Path
import time


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

API_BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"
ENTIDADE = "Dados_Gerais_Siope"

ANO_INICIO = 2017  # confirmado via sondagem: primeiro ano com dado na API
ANO_FIM = 2025      # confirmado via sondagem: já disponível
PERIODO = 6          # bimestre 6 (nov-dez) = acumulado do ano, confirmado pelos valores reais

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]

COLUNAS_DESEJADAS = [
    "TIPO", "NUM_ANO", "COD_UF", "SIG_UF", "COD_MUNI", "NOM_MUNI", "NUM_POPU",
    "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU", "VL_DESP_LIQU_EDU", "VL_DESP_PAGA_EDU",
    "VAL_DESP_PAGA",  # total do município (todas as funções) — referência para % em educação
]


def buscar_pagina(url: str, params: dict | None = None) -> dict:
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def buscar_tudo(ano: int, uf: str) -> list[dict]:
    """Busca uma UF/ano, seguindo paginação OData (@odata.nextLink) caso exista."""
    url = f"{API_BASE}{ENTIDADE}(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    params = {
        "@Ano_Consulta": ano,
        "@Num_Peri": PERIODO,
        "@Sig_UF": f"'{uf}'",
        "$format": "json",
    }

    registros = []
    proxima_url = url
    proximos_params = params

    while proxima_url:
        dados = buscar_pagina(proxima_url, proximos_params)
        registros.extend(dados.get("value", []))
        proxima_url = dados.get("@odata.nextLink")
        proximos_params = None  # o nextLink já vem com os parâmetros embutidos

    return registros


def checar_schema(ano_a: int, ano_b: int, uf_amostra: str = "SP") -> None:
    print(f"[DIAGNÓSTICO] Comparando schema entre {ano_a} e {ano_b} ({uf_amostra})")
    dados_a = buscar_tudo(ano_a, uf_amostra)
    dados_b = buscar_tudo(ano_b, uf_amostra)

    if not dados_a or not dados_b:
        print("  [AVISO] Um dos anos não retornou dados — verificar manualmente.")
        return

    colunas_a, colunas_b = set(dados_a[0].keys()), set(dados_b[0].keys())
    faltam_em_b = colunas_a - colunas_b
    faltam_em_a = colunas_b - colunas_a

    if faltam_em_b or faltam_em_a:
        print(f"  [AVISO] Diferença de schema entre {ano_a} e {ano_b}:")
        print(f"    Só em {ano_a}: {sorted(faltam_em_b)}")
        print(f"    Só em {ano_b}: {sorted(faltam_em_a)}")
    else:
        print("  Schema idêntico entre os dois anos.")

    faltantes = [c for c in COLUNAS_DESEJADAS if c not in colunas_a or c not in colunas_b]
    if faltantes:
        print(f"  [ERRO] Colunas desejadas ausentes em algum dos anos: {faltantes}")
    else:
        print("  Todas as colunas desejadas presentes nos dois anos.")


def extrair_ano(ano: int) -> pl.DataFrame | None:
    todos_registros = []
    for uf in UFS:
        registros = buscar_tudo(ano, uf)
        if not registros:
            print(f"  [AVISO] {ano}/{uf}: 0 registros retornados")
        todos_registros.extend(registros)
        time.sleep(0.2)

    if not todos_registros:
        print(f"[AVISO] {ano}: nenhum registro em nenhuma UF — pulando este ano.")
        return None

    # infer_schema_length=None força o Polars a olhar TODAS as linhas antes de
    # decidir o tipo de cada coluna — sem isso, um valor de texto como
    # "Valores sujeito alterações" que só aparece depois da amostra inicial
    # derruba a leitura (foi o que aconteceu em 2018).
    df = pl.DataFrame(todos_registros, infer_schema_length=None)

    df = df.filter(pl.col("TIPO") == "Municipal")

    colunas_disponiveis = [c for c in COLUNAS_DESEJADAS if c in df.columns]
    df = df.select(colunas_disponiveis)

    colunas_valor = [c for c in colunas_disponiveis if c.startswith(("VL_", "VAL_"))]

    # Diagnóstico: quantos valores em cada coluna NÃO eram número antes do cast
    # (captura o marcador "Valores sujeito alterações" e qualquer outro texto
    # inesperado, sem precisar prever o texto exato de antemão)
    for c in colunas_valor:
        nao_numerico = df.filter(
            pl.col(c).is_not_null() & pl.col(c).cast(pl.Float64, strict=False).is_null()
        )
        if nao_numerico.height > 0:
            valores_unicos = nao_numerico[c].unique().to_list()
            print(f"  [AVISO] {ano}/{c}: {nao_numerico.height} valor(es) não numérico(s) -> {valores_unicos}")

    df = df.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in colunas_valor])

    return df


if __name__ == "__main__":
    checar_schema(ANO_INICIO, ANO_FIM)

    print(f"\n{'=' * 70}\nEXTRAINDO {ANO_INICIO}-{ANO_FIM}\n{'=' * 70}")

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n[PROCESSANDO] {ano}")
        df = extrair_ano(ano)

        if df is None:
            continue

        destino = INTERIM_DIR / f"siope_{ano}_extraido.parquet"
        df.write_parquet(destino)
        print(f"[OK] {ano}: {df.height} municípios salvos em {destino}")