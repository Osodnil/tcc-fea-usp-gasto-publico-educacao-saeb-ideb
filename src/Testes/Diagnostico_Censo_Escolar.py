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
RAW_CENSO = BASE_DIR / "data" / "raw" / "Microdados Censo Escolar"
INTERIM_DIR = BASE_DIR / "data" / "interim"

VARIAVEIS_ALVO = ["IN_BANHEIRO", "IN_AGUA_POTAVEL"]

COLUNAS_INFRA = [
    "IN_BIBLIOTECA", "IN_LABORATORIO_INFORMATICA", "IN_LABORATORIO_CIENCIAS",
    "IN_INTERNET", "IN_BANHEIRO", "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA", "IN_QUADRA_ESPORTES",
]


def localizar_dicionario() -> Path:
    candidatos = list(RAW_CENSO.rglob("*[Dd]icion*[dD]ados*.xlsx"))
    if not candidatos:
        raise FileNotFoundError(f"Nenhum dicionário encontrado em {RAW_CENSO}")
    print(f"[INFO] Dicionário(s) candidato(s): {[c.relative_to(RAW_CENSO) for c in candidatos]}")
    return candidatos[0]


def inspecionar_dicionario() -> None:
    caminho = localizar_dicionario()
    print(f"\n[DICIONÁRIO] Usando: {caminho}\n")

    abas = list(pl.read_excel(caminho, sheet_id=0).keys())
    print(f"[DICIONÁRIO] Abas encontradas: {abas}\n")

    for aba in abas:
        df = pl.read_excel(caminho, sheet_name=aba)
        print(f"[DICIONÁRIO] Aba '{aba}' — colunas: {df.columns}")

        colunas_texto = [c for c, t in zip(df.columns, df.dtypes) if t == pl.Utf8]
        if not colunas_texto:
            print("  (nenhuma coluna de texto nesta aba, pulando)\n")
            continue

        mascara = pl.any_horizontal([pl.col(c).is_in(VARIAVEIS_ALVO) for c in colunas_texto])
        encontrados = df.filter(mascara)

        if encontrados.height > 0:
            print(f"  -> Encontrado(s) {encontrados.height} registro(s) nesta aba:")
            for row in encontrados.iter_rows(named=True):
                print(f"     {row}")
        print()


def diagnosticar_media_nacional() -> None:
    arquivos = sorted(INTERIM_DIR.glob("censo_escolar_*_extraido.parquet"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo censo_escolar_*_extraido.parquet em {INTERIM_DIR}")

    df_bruto = pl.concat([pl.read_parquet(a) for a in arquivos], how="diagonal_relaxed")
    colunas_presentes = [c for c in COLUNAS_INFRA if c in df_bruto.columns]

    print("[MÉDIA NACIONAL] Proporção de escolas com cada indicador — Brasil, todos os anos:")
    print(df_bruto.select([pl.col(c).cast(pl.Float64).mean().alias(c) for c in colunas_presentes]))

    print("\n[MÉDIA NACIONAL] Mesma coisa, só 2025 (para checar se mudou ao longo do tempo):")
    print(
        df_bruto.filter(pl.col("ANO") == 2025)
        .select([pl.col(c).cast(pl.Float64).mean().alias(c) for c in colunas_presentes])
    )


if __name__ == "__main__":
    print("=" * 70)
    print("ETAPA 1 — Verificando definição oficial das variáveis no dicionário")
    print("=" * 70)
    try:
        inspecionar_dicionario()
    except Exception as e:
        print(f"[ERRO na etapa 1] {e}")

    print("=" * 70)
    print("ETAPA 2 — Verificando se o padrão é nacional ou específico de um município")
    print("=" * 70)
    diagnosticar_media_nacional()