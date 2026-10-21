import polars as pl
from pathlib import Path
import unicodedata

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw" / "IDHM"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FUNÇÕES
# ============================================================

def localizar_arquivo_idhm() -> Path:
    """Busca recursiva — cobre o caso de o arquivo estar em subpastas
    como 'Região/data.xlsx', criadas pela exportação do Atlas Brasil."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"A pasta {RAW_DIR} não existe. Baixe a planilha do Atlas Brasil "
            f"(atlasbrasil.org.br ou idhm.org.br/consulta/planilha) e coloque-a aqui."
        )

    candidatos = (
        list(RAW_DIR.rglob("*.xlsx"))
        + list(RAW_DIR.rglob("*.xls"))
        + list(RAW_DIR.rglob("*.csv"))
    )

    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum arquivo .xlsx/.xls/.csv encontrado em {RAW_DIR} (nem em subpastas)."
        )

    if len(candidatos) > 1:
        print(f"[AVISO] Mais de um arquivo encontrado: {[str(c) for c in candidatos]}")
        print(f"[INFO] Usando o primeiro: {candidatos[0]}")

    return candidatos[0]


def normalizar_nome_coluna(nome: str) -> str:
    """Remove acentos, espaços e caracteres especiais dos nomes de coluna,
    deixando-os seguros para uso posterior (ex: 'IDHM Educação' -> 'idhm_educacao')."""
    nome_sem_acento = (
        unicodedata.normalize("NFKD", nome)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return (
        nome_sem_acento.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
    )


def carregar_planilha(caminho: Path) -> pl.DataFrame:
    """Como o arquivo é pequeno (UF+Brasil ou municípios, ambos cabem
    tranquilamente em memória), carregamos tudo — diferente do ENEM,
    aqui não há necessidade de leitura lazy/streaming."""
    if caminho.suffix == ".csv":
        df = pl.read_csv(caminho, encoding="utf8-lossy")
    else:
        df = pl.read_excel(caminho)
    return df


def processar_idhm() -> None:
    arquivo = localizar_arquivo_idhm()
    print(f"[PROCESSANDO] {arquivo}")

    df = carregar_planilha(arquivo)

    print(f"[INFO] {df.height} linhas, {df.width} colunas")
    print(f"[INFO] Colunas originais -> {df.columns}")

    # Renomeia colunas para um formato seguro (sem acentos/espaços),
    # preservando o nome original como referência no print acima.
    mapa_nomes = {c: normalizar_nome_coluna(c) for c in df.columns}
    df = df.rename(mapa_nomes)

    print(f"[INFO] Colunas normalizadas -> {df.columns}")

    destino = INTERIM_DIR / "idhm_extraido.parquet"
    df.write_parquet(destino)

    print(f"[OK] IDHM salvo em {destino}")
    print(df.head())


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    processar_idhm()