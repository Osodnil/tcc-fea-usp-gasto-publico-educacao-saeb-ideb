import polars as pl
from pathlib import Path
import re
import unicodedata

# ============================================================
# CONFIGURAÇÃO
# ============================================================

def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    """Sobe na árvore de diretórios a partir deste arquivo até encontrar
    a raiz do projeto (identificada pela presença de '.git'). Funciona
    independentemente de o script estar na raiz, em src/, ou em
    src/Extract/ — remove a fragilidade de contar '.parent' manualmente."""
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(
        f"Não foi possível localizar a raiz do projeto (procurando por '{marcador}')."
    )


BASE_DIR = encontrar_raiz_projeto()
RAW_ROOT = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

# Padrões de nome de arquivo que identificam a tabela de nível ESCOLA em
# cada ano — cobre tanto o formato antigo (microdados_ed_basica_AAAA)
# quanto o formato normalizado introduzido em 2025 (Tabela_Escola_AAAA).
PADROES_VALIDOS = ["microdados_ed_basica", "tabela_escola"]

# Excluídos explicitamente: suplementos e as demais tabelas normalizadas de
# 2025 (docente, turma, matrícula, gestor, curso técnico), que não são a
# tabela de escola e não devem ser confundidas com ela.
PADROES_EXCLUIDOS = ["suplemento", "docente", "turma", "matricula", "gestor", "curso_tecnico"]

# Colunas candidatas — nomes historicamente estáveis (CO_ENTIDADE, CO_MUNICIPIO,
# TP_DEPENDENCIA) têm alta confiança; os indicadores de infraestrutura (IN_*)
# podem ter mudado de nome entre reformas do Censo Escolar, por isso a lista é
# ampla e o script avisa o que não existir em cada ano, em vez de presumir.
COLUNAS_DESEJADAS = [
    "CO_ENTIDADE",          # código INEP da escola
    "NO_ENTIDADE",          # nome da escola (referência/depuração)
    "CO_MUNICIPIO",         # chave de junção com CO_MUNICIPIO_ESC do ENEM
    "SG_UF",
    "TP_DEPENDENCIA",       # 1=Federal, 2=Estadual, 3=Municipal, 4=Privada
    "TP_LOCALIZACAO",       # urbano/rural
    "IN_BIBLIOTECA",
    "IN_LABORATORIO_INFORMATICA",
    "IN_LABORATORIO_CIENCIAS",
    "IN_INTERNET",
    "IN_BANHEIRO",
    "IN_AGUA_POTAVEL",
    "IN_ENERGIA_REDE_PUBLICA",
    "IN_QUADRA_ESPORTES",
]


# ============================================================
# FUNÇÕES
# ============================================================

def normalizar(texto: str) -> str:
    sem_acento = (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return sem_acento.upper()


def extrair_ano_do_nome(caminho: Path) -> int:
    match = re.search(r"(\d{4})", caminho.stem)
    if not match:
        raise ValueError(f"Não foi possível identificar o ano em {caminho.name}")
    return int(match.group(1))


def localizar_pasta_censo() -> Path:
    candidatos = [
        p for p in RAW_ROOT.iterdir()
        if p.is_dir() and "CENSO ESCOLAR" in normalizar(p.name)
    ]
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhuma subpasta contendo 'CENSO ESCOLAR' encontrada em {RAW_ROOT}. "
            f"Pastas disponíveis: {[p.name for p in RAW_ROOT.iterdir() if p.is_dir()]}"
        )
    return candidatos[0]


def localizar_arquivos_por_ano(pasta_censo: Path) -> list[Path]:
    """Busca recursiva por CSVs dentro de qualquer subpasta 'dados', mantendo
    apenas o arquivo de nível ESCOLA por ano — descarta suplementos e as
    demais tabelas normalizadas introduzidas em 2025 (docente, turma,
    matrícula, gestor, curso técnico)."""

    todos = [
        f for f in pasta_censo.rglob("*.csv")
        if f.parent.name.lower() == "dados"
        and not f.stem.lower().startswith("md5")
    ]

    candidatos = [
        f for f in todos
        if any(p in f.stem.lower() for p in PADROES_VALIDOS)
        and not any(p in f.stem.lower() for p in PADROES_EXCLUIDOS)
    ]

    # Trava de segurança: nunca deixar mais de um arquivo "válido" por ano
    # seguir adiante silenciosamente — preferimos parar com erro explícito
    # a repetir uma sobrescrita silenciosa como a que já ocorreu.
    por_ano: dict[int, list[Path]] = {}
    for f in candidatos:
        ano = extrair_ano_do_nome(f)
        por_ano.setdefault(ano, []).append(f)

    for ano, arquivos_do_ano in por_ano.items():
        if len(arquivos_do_ano) > 1:
            raise ValueError(
                f"Mais de um arquivo válido encontrado para {ano}: "
                f"{[a.name for a in arquivos_do_ano]}. Ajuste PADROES_VALIDOS/EXCLUIDOS."
            )

    return sorted(candidatos)


def obter_colunas_disponiveis(caminho_csv: Path) -> list[str]:
    return (
        pl.scan_csv(caminho_csv, separator=";", encoding="utf8-lossy", n_rows=0)
        .collect_schema()
        .names()
    )


def extrair_censo(caminho_csv: Path) -> pl.LazyFrame:
    ano = extrair_ano_do_nome(caminho_csv)
    colunas_disponiveis = obter_colunas_disponiveis(caminho_csv)

    # Alerta de segurança: se o separador estiver errado, o arquivo inteiro
    # vira UMA coluna só — detectamos isso antes de seguir.
    if len(colunas_disponiveis) <= 1:
        raise ValueError(
            f"Ano {ano}: apenas {len(colunas_disponiveis)} coluna(s) detectada(s) — "
            f"o separador provavelmente não é ';'. Verifique o arquivo manualmente."
        )

    colunas_faltantes = set(COLUNAS_DESEJADAS) - set(colunas_disponiveis)
    if colunas_faltantes:
        print(f"[AVISO] Ano {ano}: colunas ausentes -> {sorted(colunas_faltantes)}")

    colunas_a_ler = [c for c in COLUNAS_DESEJADAS if c in colunas_disponiveis]

    lf = (
        pl.scan_csv(caminho_csv, separator=";", encoding="utf8-lossy", infer_schema_length=0)
        .select(colunas_a_ler)
        .with_columns(pl.lit(ano).alias("ANO"))
    )
    return lf


def converter_tipos(lf: pl.LazyFrame) -> pl.LazyFrame:
    colunas_disponiveis = lf.collect_schema().names()
    colunas_indicadoras = [c for c in colunas_disponiveis if c.startswith("IN_")]
    exprs = [pl.col(c).cast(pl.Int8, strict=False) for c in colunas_indicadoras]
    return lf.with_columns(exprs)


def processar_ano(caminho_csv: Path) -> None:
    ano = extrair_ano_do_nome(caminho_csv)
    print(f"[PROCESSANDO] {ano} — {caminho_csv.name}")

    lf = extrair_censo(caminho_csv)
    lf = converter_tipos(lf)

    destino = INTERIM_DIR / f"censo_escolar_{ano}_extraido.parquet"
    lf.sink_parquet(destino)

    print(f"[OK] Ano {ano} salvo em {destino}")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    print(f"Raiz do projeto: {BASE_DIR}")

    pasta_censo = localizar_pasta_censo()
    print(f"Pasta Censo Escolar: {pasta_censo}\n")

    arquivos = localizar_arquivos_por_ano(pasta_censo)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo de dados encontrado em {pasta_censo}.")

    print(f"Encontrados {len(arquivos)} arquivo(s) válido(s) (um por ano):")
    for a in arquivos:
        print(f"  - {a.relative_to(pasta_censo)}")
    print()

    for arquivo in arquivos:
        processar_ano(arquivo)