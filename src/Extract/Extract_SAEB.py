import re
import unicodedata
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
RAW_ROOT = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

METRICAS = ["VL_NOTA_MATEMATICA", "VL_NOTA_PORTUGUES", "VL_NOTA_MEDIA", "VL_INDICADOR_REND", "VL_OBSERVADO"]
TECNICO = re.compile(r"^[A-Z]{2,3}_[A-Z0-9_]+$")
COM_ANO = re.compile(r"^(VL_[A-Z_]+?)_((?:19|20)\d{2})$")
ETAPAS_MUN = {"anos_iniciais": "AI", "anos_finais": "AF", "ensino_medio": "EM"}
REGIOES = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]

MAPA_UF = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR",
    "Pará": "PA", "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA",
    "Piauí": "PI", "Ceará": "CE", "Rio Grande do Norte": "RN", "Paraíba": "PB",
    "Pernambuco": "PE", "Alagoas": "AL", "Sergipe": "SE", "Bahia": "BA",
    "Minas Gerais": "MG", "Espírito Santo": "ES", "Rio de Janeiro": "RJ",
    "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
    # a planilha de regiões/UFs abrevia estes três nomes
    "M. G. do Sul": "MS", "R. G. do Norte": "RN", "R. G. do Sul": "RS",
}


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").upper()


def pasta_ideb() -> Path:
    candidatas = [p for p in RAW_ROOT.iterdir() if p.is_dir() and "IDEB" in normalizar(p.name)]
    if not candidatas:
        raise FileNotFoundError(f"Nenhuma pasta com 'IDEB' em {RAW_ROOT}")
    return candidatas[0]


def achar_cabecalho(bruto: pl.DataFrame) -> int:
    """Linha com mais nomes técnicos de coluna (SG_UF, VL_NOTA_MEDIA_2017...)."""
    melhor, n_melhor = None, 0
    for i in range(min(40, bruto.height)):
        n = sum(1 for c in bruto.row(i) if c is not None and TECNICO.match(str(c).strip()))
        if n > n_melhor:
            melhor, n_melhor = i, n
    if melhor is None or n_melhor < 5:
        raise ValueError("Cabeçalho técnico não encontrado nas 40 primeiras linhas.")
    return melhor


def tabela_da_aba(caminho: Path, aba: str, ids_posicionais: dict | None = None) -> pl.DataFrame:
    bruto = pl.read_excel(caminho, sheet_name=aba, read_options={"header_row": None})
    i = achar_cabecalho(bruto)
    cab = [str(c).strip() if c is not None else "" for c in bruto.row(i)]

    nomes, vistos = [], {}
    for j, c in enumerate(cab):
        nome = (ids_posicionais or {}).get(j) or c or f"_COL{j}"
        vistos[nome] = vistos.get(nome, 0) + 1
        nomes.append(nome if vistos[nome] == 1 else f"{nome}__dup{vistos[nome]}")

    dados = bruto.slice(i + 1)
    dados.columns = nomes
    return dados


def para_longo(dados: pl.DataFrame, ids: list[str]) -> pl.DataFrame:
    cols = [c for c in dados.columns if (m := COM_ANO.match(c)) and m.group(1) in METRICAS]
    if not cols:
        raise ValueError("Nenhuma coluna de métrica com ano encontrada.")

    longo = (
        dados.select(ids + [pl.col(c).cast(pl.Utf8) for c in cols])
        .unpivot(index=ids, on=cols, variable_name="_col", value_name="_valor")
        .with_columns(
            pl.col("_col").str.extract(r"^(VL_[A-Z_]+?)_(?:19|20)\d{2}$", 1).alias("_metrica"),
            pl.col("_col").str.extract(r"_((?:19|20)\d{2})$", 1).cast(pl.Int64).alias("ANO"),
            # '-' e 'ND' (sem resultado divulgado) viram nulo
            pl.col("_valor").cast(pl.Float64, strict=False),
        )
    )
    return (
        longo.pivot(on="_metrica", index=ids + ["ANO"], values="_valor", aggregate_function="first")
        .sort(ids + ["ANO"])
    )


def extrair_municipal(caminho: Path, etapa: str) -> pl.DataFrame:
    abas = list(pl.read_excel(caminho, sheet_id=0).keys())
    if len(abas) > 1:
        print(f"  [AVISO] {caminho.name} tem {len(abas)} abas {abas}; usando a primeira.")
    dados = tabela_da_aba(caminho, abas[0])

    ids = [c for c in ("SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO", "REDE") if c in dados.columns]
    if not {"CO_MUNICIPIO", "REDE"} <= set(ids):
        raise ValueError(f"Colunas-chave ausentes em {caminho.name}. Colunas: {dados.columns[:12]}")

    dados = dados.with_columns(
        pl.col("CO_MUNICIPIO").cast(pl.Utf8).str.strip_chars().str.replace(r"\.0$", "")
    ).filter(
        # descarta rodapés e linhas de nota (sem código de 7 dígitos ou sem rede)
        pl.col("CO_MUNICIPIO").str.contains(r"^\d{7}$") & pl.col("REDE").is_not_null()
    )
    return para_longo(dados, ids).with_columns(pl.lit(etapa).alias("ETAPA"))


def extrair_uf(caminho: Path) -> dict[str, tuple[pl.DataFrame, list[str]]]:
    saidas = {}
    for aba in pl.read_excel(caminho, sheet_id=0).keys():
        m = re.search(r"\((AI|AF|EM)\)", aba)
        if not m:
            print(f"  [AVISO] Aba '{aba}' ignorada (não é AI/AF/EM).")
            continue
        etapa = m.group(1)
        dados = tabela_da_aba(caminho, aba, ids_posicionais={0: "REGIAO_UF_BRUTO", 1: "REDE_BRUTA"})

        def limpar(col: str) -> pl.Expr:
            # tira marcas de rodapé "(1)", "(3)(4)" e espaços/quebras de linha
            txt = pl.col(col).cast(pl.Utf8).str.replace_all(r"\s*\(\d+\)", "").str.replace_all(r"\s+", " ").str.strip_chars()
            return pl.when(txt == "").then(None).otherwise(txt)

        dados = dados.with_columns(
            limpar("REGIAO_UF_BRUTO").alias("REGIAO_UF"),
            limpar("REDE_BRUTA").alias("REDE"),
        ).with_columns(pl.col("REGIAO_UF").fill_null(strategy="forward"))

        dados = dados.filter(pl.col("REDE").is_not_null() & pl.col("REGIAO_UF").is_not_null())
        dados = dados.with_columns(
            pl.when(pl.col("REGIAO_UF") == "Brasil").then(pl.lit("Brasil"))
            .when(pl.col("REGIAO_UF").is_in(REGIOES)).then(pl.lit("Região"))
            .when(pl.col("REGIAO_UF").is_in(list(MAPA_UF))).then(pl.lit("UF"))
            .otherwise(pl.lit("Outro")).alias("NIVEL"),
            pl.col("REGIAO_UF").replace_strict(MAPA_UF, default=None).alias("SG_UF"),
        )
        outros = sorted(dados.filter(pl.col("NIVEL") == "Outro")["REGIAO_UF"].unique().to_list())
        dados = dados.filter(pl.col("NIVEL") != "Outro")

        longo = para_longo(dados, ["REGIAO_UF", "SG_UF", "NIVEL", "REDE"]).with_columns(pl.lit(etapa).alias("ETAPA"))
        saidas[etapa] = (longo, outros)
    return saidas


def cobertura(df: pl.DataFrame, ano_min: int = 2017) -> pl.DataFrame:
    metricas = [m for m in METRICAS if m in df.columns]
    return (
        df.filter(pl.col("ANO") >= ano_min)
        .group_by("ANO")
        .agg([pl.col(m).is_not_null().sum().alias(m.replace("VL_", "")) for m in metricas])
        .sort("ANO")
    )


def resumo_municipal(df: pl.DataFrame, etapa: str) -> None:
    print(f"\n[MUNICIPAL {etapa}] {df.height} linhas | {df['CO_MUNICIPIO'].n_unique()} municípios | "
          f"anos {df['ANO'].min()}-{df['ANO'].max()}")
    print(f"  Redes: {sorted(df['REDE'].unique().to_list())}")
    publica = df.filter((pl.col("REDE") == "Pública") & (pl.col("ANO") == 2025) & pl.col("VL_OBSERVADO").is_not_null())
    print(f"  Municípios com IDEB 2025 na rede Pública: {publica['CO_MUNICIPIO'].n_unique()} "
          f"(nota informativa do Inep: AI 5.478 | AF 5.491 | EM 5.428)")
    print("  Valores não nulos por métrica e ano (2017 em diante):")
    print(cobertura(df))


def resumo_uf(df: pl.DataFrame, etapa: str, outros: list[str]) -> None:
    print(f"\n[UF {etapa}] {df.height} linhas | anos {df['ANO'].min()}-{df['ANO'].max()}")
    print(f"  Entidades por nível: {df.group_by('NIVEL').agg(pl.col('REGIAO_UF').n_unique().alias('n')).sort('NIVEL').to_dicts()}")
    print(f"  Redes: {sorted(df['REDE'].unique().to_list())}")
    if outros:
        print(f"  [AVISO] Nomes fora do padrão descartados: {outros}")
    est = df.filter(
        (pl.col("NIVEL") == "UF") & (pl.col("REDE") == "Estadual") & pl.col("VL_NOTA_MEDIA").is_not_null()
    )
    print("  UFs com nota média (N) da rede Estadual, por ano:")
    print(est.group_by("ANO").agg(pl.col("SG_UF").n_unique().alias("n_ufs")).sort("ANO").tail(6))


if __name__ == "__main__":
    pasta = pasta_ideb()
    xlsx = [
        f for f in pasta.rglob("*.xlsx")
        if not f.name.startswith("~$") and not f.stem.lower().startswith("md5")
    ]
    print(f"Pasta: {pasta}\n{len(xlsx)} arquivo(s) .xlsx")

    for chave, etapa in ETAPAS_MUN.items():
        achados = [f for f in xlsx if chave in f.name.lower() and "municipios" in f.name.lower()]
        if not achados:
            print(f"\n[FALTA] Municipal {etapa}: nenhum arquivo com '{chave}' e 'municipios' no nome.")
            continue
        if len(achados) > 1:
            raise ValueError(f"Mais de um arquivo para {etapa}: {[f.name for f in achados]}")
        print(f"\n[LENDO] Municipal {etapa}: {achados[0].name}")
        df = extrair_municipal(achados[0], etapa)
        df.write_parquet(INTERIM_DIR / f"saeb_municipios_{etapa}.parquet")
        resumo_municipal(df, etapa)

    uf_arquivos = [f for f in xlsx if "regioes_ufs" in f.name.lower()]
    if len(uf_arquivos) != 1:
        print(f"\n[FALTA] Esperava 1 arquivo de regiões/UFs, achei {[f.name for f in uf_arquivos]}")
    else:
        print(f"\n[LENDO] UFs e regiões: {uf_arquivos[0].name}")
        for etapa, (df, outros) in extrair_uf(uf_arquivos[0]).items():
            df.write_parquet(INTERIM_DIR / f"saeb_ufs_{etapa}.parquet")
            resumo_uf(df, etapa, outros)

    print("\n[FIM] Arquivos em data/interim: saeb_municipios_{AI,AF,EM}.parquet e saeb_ufs_{AI,AF,EM}.parquet")