import polars as pl
from pathlib import Path
import unicodedata

BASE_DIR = Path(__file__).resolve().parent
RAW_ROOT = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

LINHA_CABECALHO = 7  # confirmado via inspeção manual das primeiras 15 linhas

COLUNAS_DESEJADAS = [
    "SG_UF",
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "REDE",
    "VL_OBSERVADO_2017",
    "VL_OBSERVADO_2019",
    "VL_OBSERVADO_2021",
    "VL_OBSERVADO_2023",
    "VL_OBSERVADO_2025",
]

REDES_A_MANTER = ["Estadual", "Federal", "Municipal", "Privada"]  # exclui 'Pública', que é agregado


def normalizar(texto: str) -> str:
    sem_acento = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return sem_acento.upper()


def localizar_pasta_ideb() -> Path:
    candidatos = [
        p for p in RAW_ROOT.iterdir()
        if p.is_dir() and "IDEB" in normalizar(p.name)
    ]
    if not candidatos:
        raise FileNotFoundError(f"Nenhuma subpasta contendo 'IDEB' encontrada em {RAW_ROOT}.")
    return candidatos[0]


def localizar_arquivo_municipios(pasta_ideb: Path) -> Path:
    candidatos = [
        f for f in pasta_ideb.rglob("*.xlsx")
        if "MUNICIP" in normalizar(f.stem)
        and "ensino_medio" in f.stem.lower()
        and not f.stem.lower().startswith("md5")
    ]
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum arquivo de Ensino Médio por município (.xlsx) encontrado em {pasta_ideb}."
        )
    if len(candidatos) > 1:
        print(f"[AVISO] Mais de um arquivo candidato: {[c.name for c in candidatos]}")
    return candidatos[0]


def extrair_ideb_municipios(caminho: Path) -> pl.DataFrame:
    # Lê tudo cru, sem interpretar cabeçalho — abordagem já validada no
    # script de reconhecimento, evitando depender de 'header_row' do Polars.
    df_raw = pl.read_excel(caminho, read_options={"header_row": None})

    valores_cabecalho = df_raw.row(LINHA_CABECALHO)

    mapa_nomes = {
        coluna_atual: (str(nome) if nome is not None else coluna_atual)
        for coluna_atual, nome in zip(df_raw.columns, valores_cabecalho)
    }

    df = df_raw.slice(LINHA_CABECALHO + 1).rename(mapa_nomes)

    colunas_disponiveis = df.columns
    colunas_faltantes = set(COLUNAS_DESEJADAS) - set(colunas_disponiveis)
    if colunas_faltantes:
        print(f"[AVISO] Colunas esperadas ausentes -> {sorted(colunas_faltantes)}")
        print(f"[INFO] Colunas disponíveis -> {colunas_disponiveis}")

    colunas_a_ler = [c for c in COLUNAS_DESEJADAS if c in colunas_disponiveis]
    df = df.select(colunas_a_ler)

    colunas_valor = [c for c in colunas_a_ler if c.startswith("VL_OBSERVADO")]
    df = df.with_columns(
        [pl.col(c).cast(pl.Float64, strict=False) for c in colunas_valor]
    )

    return df


if __name__ == "__main__":
    pasta_ideb = localizar_pasta_ideb()
    print(f"Pasta IDEB: {pasta_ideb}")

    arquivo = localizar_arquivo_municipios(pasta_ideb)
    print(f"[PROCESSANDO] {arquivo.relative_to(pasta_ideb)}")

    df = extrair_ideb_municipios(arquivo)

    print(f"\n[INFO] {df.height} linhas, {df.width} colunas")

    if "REDE" in df.columns:
        redes_encontradas = df["REDE"].unique().to_list()
        print(f"[INFO] Valores únicos em REDE (antes do filtro) -> {redes_encontradas}")

        df = df.filter(pl.col("REDE").is_in(REDES_A_MANTER))
        print(f"[INFO] Linhas após excluir 'Pública' (agregado) -> {df.height}")

    destino = INTERIM_DIR / "ideb_ensino_medio_municipios_extraido.parquet"
    df.write_parquet(destino)

    print(f"[OK] IDEB salvo em {destino}")
    print(df.head())