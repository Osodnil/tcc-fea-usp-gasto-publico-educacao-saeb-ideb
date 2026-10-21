import polars as pl
from pathlib import Path
import re


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
RAW_DIR = BASE_DIR / "data" / "raw" / "Microdados ENEM"
INTERIM_DIR = BASE_DIR / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

ANO_INICIO = 2013
ANO_FIM = 2023
FORCAR_ANOS: set[int] = set()  # ex.: {2016} para reprocessar só 2016, mesmo já existindo e válido

SEPARADORES = [";", ",", "|"]  # ";" primeiro: é o padrão que funcionou em todos os anos

# CO_ESCOLA removida: excluída permanentemente dos microdados públicos (LGPD).
COLUNAS_DESEJADAS = [
    "NU_INSCRICAO",
    "TP_SEXO",
    "TP_COR_RACA",
    "TP_ESTADO_CIVIL",
    "TP_FAIXA_ETARIA",
    "IN_TREINEIRO",
    "CO_MUNICIPIO_ESC",
    "SG_UF_ESC",
    "TP_DEPENDENCIA_ADM_ESC",
    "TP_LOCALIZACAO_ESC",
    "TP_PRESENCA_CN",
    "TP_PRESENCA_CH",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    "TP_STATUS_REDACAO",
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_COMP1",
    "NU_NOTA_COMP2",
    "NU_NOTA_COMP3",
    "NU_NOTA_COMP4",
    "NU_NOTA_COMP5",
    "NU_NOTA_REDACAO",
    "Q001",
    "Q002",
    "Q006",
]

# IN_TREINEIRO: confirmado ausente em 2013/2014 (só existe a partir de 2015); a regra
# de treineiros ainda será decidida, mas a coluna continua sendo extraída quando existe.
COLUNAS_OPCIONAIS = {
    "TP_ESTADO_CIVIL", "TP_FAIXA_ETARIA", "TP_LOCALIZACAO_ESC",
    "Q001", "Q002", "IN_TREINEIRO",
}
COLUNAS_CRITICAS = [c for c in COLUNAS_DESEJADAS if c not in COLUNAS_OPCIONAIS]

COLUNAS_NOTA = [
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT",
    "NU_NOTA_COMP1", "NU_NOTA_COMP2", "NU_NOTA_COMP3",
    "NU_NOTA_COMP4", "NU_NOTA_COMP5", "NU_NOTA_REDACAO",
]


def extrair_ano_do_nome(caminho: Path) -> int:
    match = re.search(r"(20\d{2})", caminho.stem)
    if not match:
        raise ValueError(f"Não foi possível identificar o ano em {caminho.name}")
    return int(match.group(1))


def localizar_arquivos() -> list[Path]:
    """Busca sem diferenciar maiúsculas/minúsculas, mantém só a faixa
    ANO_INICIO-ANO_FIM e trava se houver mais de um arquivo por ano
    (proteção contra sobrescrita silenciosa)."""
    candidatos = [
        f for f in RAW_DIR.rglob("*")
        if f.is_file()
        and f.suffix.lower() == ".csv"
        and f.stem.lower().startswith("microdados_enem")
    ]

    por_ano: dict[int, list[Path]] = {}
    for f in candidatos:
        por_ano.setdefault(extrair_ano_do_nome(f), []).append(f)

    duplicados = {ano: fs for ano, fs in por_ano.items() if len(fs) > 1}
    if duplicados:
        raise ValueError(
            "Mais de um arquivo por ano encontrado: "
            + str({ano: [f.name for f in fs] for ano, fs in duplicados.items()})
        )

    fora_da_faixa = sorted(a for a in por_ano if not (ANO_INICIO <= a <= ANO_FIM))
    if fora_da_faixa:
        print(f"[INFO] Ignorando anos fora da faixa {ANO_INICIO}-{ANO_FIM}: {fora_da_faixa}")

    ausentes = [a for a in range(ANO_INICIO, ANO_FIM + 1) if a not in por_ano]
    if ausentes:
        print(f"[AVISO] Anos da faixa SEM arquivo em {RAW_DIR}: {ausentes}")

    return [por_ano[a][0] for a in sorted(por_ano) if ANO_INICIO <= a <= ANO_FIM]


def detectar_separador(caminho_csv: Path) -> str:
    for sep in SEPARADORES:
        colunas = (
            pl.scan_csv(caminho_csv, separator=sep, encoding="utf8-lossy", n_rows=0)
            .collect_schema()
            .names()
        )
        if len(colunas) > 1:
            return sep
    raise ValueError(f"Não foi possível detectar o separador de {caminho_csv.name}")


def sugerir_colunas_parecidas(faltantes: list[str], disponiveis: list[str]) -> None:
    for coluna in faltantes:
        prefixo = "Q" if re.fullmatch(r"Q\d+", coluna) else coluna.split("_")[0] + "_"
        parecidas = [c for c in disponiveis if c.startswith(prefixo)]
        print(f"    {coluna}: colunas com prefixo '{prefixo}' -> {parecidas[:25]}")


def extrair_enem(caminho_csv: Path) -> tuple[pl.LazyFrame, list[str]]:
    ano = extrair_ano_do_nome(caminho_csv)
    separador = detectar_separador(caminho_csv)
    if separador != ";":
        print(f"[INFO] Ano {ano}: separador detectado = '{separador}'")

    colunas_disponiveis = (
        pl.scan_csv(caminho_csv, separator=separador, encoding="utf8-lossy", n_rows=0)
        .collect_schema()
        .names()
    )

    faltantes = [c for c in COLUNAS_DESEJADAS if c not in colunas_disponiveis]
    criticas_faltantes = [c for c in faltantes if c in COLUNAS_CRITICAS]
    opcionais_faltantes = [c for c in faltantes if c in COLUNAS_OPCIONAIS]

    if opcionais_faltantes:
        print(f"[AVISO] Ano {ano}: colunas opcionais ausentes -> {opcionais_faltantes}")
    if criticas_faltantes:
        print(f"[ERRO CRÍTICO] Ano {ano}: colunas críticas ausentes -> {criticas_faltantes}")
        sugerir_colunas_parecidas(criticas_faltantes, colunas_disponiveis)

    colunas_a_ler = [c for c in COLUNAS_DESEJADAS if c in colunas_disponiveis]

    lf = (
        pl.scan_csv(
            caminho_csv,
            separator=separador,
            encoding="utf8-lossy",
            infer_schema_length=0,  # tudo como texto; os casts vêm depois, de forma explícita
        )
        .select(colunas_a_ler)
        .with_columns(pl.lit(ano).alias("ANO"))
    )
    return lf, criticas_faltantes


def converter_tipos(lf: pl.LazyFrame) -> pl.LazyFrame:
    colunas = lf.collect_schema().names()
    exprs = [
        # vírgula decimal -> ponto ANTES do cast: sem isso, "580,5" viraria null
        # silenciosamente com strict=False
        pl.col(c).str.replace(",", ".", literal=True).cast(pl.Float64, strict=False)
        for c in COLUNAS_NOTA
        if c in colunas
    ]
    return lf.with_columns(exprs)


def parquet_valido(destino: Path) -> bool:
    """True se o parquet abre (rodapé íntegro) e tem linhas. Um arquivo truncado
    por uma gravação interrompida (ex.: disco cheio) falha aqui."""
    try:
        return pl.scan_parquet(destino).select(pl.len()).collect().item() > 0
    except Exception:
        return False


def verificar_ano(destino: Path, ano: int) -> None:
    lf = pl.scan_parquet(destino)
    colunas = lf.collect_schema().names()
    notas_presentes = [c for c in ["NU_NOTA_CN", "NU_NOTA_MT", "NU_NOTA_REDACAO"] if c in colunas]

    resumo = lf.select(
        [pl.len().alias("linhas")]
        + [pl.col(c).is_not_null().mean().alias(c) for c in notas_presentes]
    ).collect()

    print(f"    [VERIFICAÇÃO {ano}] {resumo.to_dicts()[0]}")
    for c in notas_presentes:
        if resumo[c][0] == 0:
            print(f"    [ALERTA] {c} está 100% nula em {ano} — provável falha de leitura.")


def processar_ano(caminho_csv: Path) -> tuple[int, list[str], str]:
    ano = extrair_ano_do_nome(caminho_csv)
    destino = INTERIM_DIR / f"enem_{ano}_extraido.parquet"

    if destino.exists() and ano not in FORCAR_ANOS:
        if parquet_valido(destino):
            print(f"\n[PULANDO] {ano} — parquet já existe e é legível: {destino.name}")
            verificar_ano(destino, ano)
            return ano, [], "pulado"
        print(f"\n[AVISO] {ano}: parquet existente está ilegível ou vazio (gravação interrompida?); reprocessando.")

    print(f"\n[PROCESSANDO] {ano} — {caminho_csv}")

    lf, criticas_faltantes = extrair_enem(caminho_csv)
    lf = converter_tipos(lf)

    # Grava em arquivo temporário e só renomeia ao terminar: se algo falhar no meio
    # (ex.: disco cheio), nenhum arquivo incompleto fica com o nome final.
    tmp = destino.with_name(destino.name + ".tmp")
    try:
        lf.sink_parquet(tmp)
        tmp.replace(destino)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    print(f"[OK] Ano {ano} salvo em {destino}")

    verificar_ano(destino, ano)
    return ano, criticas_faltantes, "processado"


if __name__ == "__main__":
    print(f"Raiz do projeto: {BASE_DIR}")
    print(f"Diretório RAW: {RAW_DIR}\n")

    if not RAW_DIR.exists():
        raise FileNotFoundError(f"A pasta não existe:\n{RAW_DIR}")

    arquivos = localizar_arquivos()
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo MICRODADOS_ENEM_*.csv na faixa {ANO_INICIO}-{ANO_FIM} em:\n{RAW_DIR}")

    print(f"Anos na faixa ({len(arquivos)}):")
    for a in arquivos:
        print(f"  - {a.relative_to(RAW_DIR)}")

    resultados = [processar_ano(a) for a in arquivos]

    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)

    processados = [ano for ano, _, status in resultados if status == "processado"]
    pulados = [ano for ano, _, status in resultados if status == "pulado"]
    print(f"  Processados agora: {processados}")
    print(f"  Pulados (parquet já existente e válido): {pulados}")

    problemas = {ano: faltantes for ano, faltantes, _ in resultados if faltantes}
    if problemas:
        for ano, faltantes in problemas.items():
            print(f"  {ano}: colunas críticas ausentes -> {faltantes}")
        print("\n[ATENÇÃO] Os anos acima foram gravados, mas INCOMPLETOS. Não seguir para o Transform sem resolver.")
    else:
        print("  Nenhum ano processado agora tem colunas críticas ausentes.")