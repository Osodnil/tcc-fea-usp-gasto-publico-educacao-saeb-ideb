import re
import sys
from datetime import date, datetime
from pathlib import Path

import polars as pl


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
SAIDA_DIR = BASE_DIR / "docs" / "migracao"
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

# pastas que não entram no pacote de código
PASTAS_IGNORADAS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", ".vscode", ".ipynb_checkpoints", "data", "docs"}
LIMITE_CARACTERES_CODIGO = 350_000  # divide o código em partes para não pesar no projeto
PADRAO_CREDENCIAL = re.compile(r"(?i)(password|senha|secret|api[_-]?key|token|bearer)\s*[=:]\s*['\"]\w")


def tamanho_mb(caminho: Path) -> float:
    return caminho.stat().st_size / 1e6


# ---------------------------------------------------------------- inventário de dados
def inventario_parquets() -> list[str]:
    linhas: list[str] = []
    for pasta in (BASE_DIR / "data" / "interim", BASE_DIR / "data" / "processed"):
        arquivos = sorted(pasta.rglob("*.parquet")) if pasta.exists() else []
        linhas.append(f"## {pasta.relative_to(BASE_DIR).as_posix()}: {len(arquivos)} arquivo(s) parquet")
        linhas.append("")
        for arq in arquivos:
            linhas.append(f"### {arq.relative_to(BASE_DIR).as_posix()}")
            try:
                lf = pl.scan_parquet(arq)
                esquema = lf.collect_schema()
                n = lf.select(pl.len()).collect().item()
                extra = ""
                for col in ("ANO", "NUM_ANO"):
                    if col in esquema.names():
                        mn, mx = lf.select(
                            pl.col(col).cast(pl.Int64, strict=False).min().alias("mn"),
                            pl.col(col).cast(pl.Int64, strict=False).max().alias("mx"),
                        ).collect().row(0)
                        extra = f" | {col}: {mn} a {mx}"
                        break
                linhas.append(f"- {n:,} linhas | {len(esquema)} colunas | {tamanho_mb(arq):.1f} MB{extra}".replace(",", "."))
                linhas.append("- Colunas: " + ", ".join(f"`{nome}` ({tipo})" for nome, tipo in esquema.items()))
            except Exception as e:
                linhas.append(f"- [ERRO ao ler] {type(e).__name__}: {e}")
            linhas.append("")
    return linhas


def lista_diagnosticos() -> list[str]:
    pasta = BASE_DIR / "data" / "interim" / "diagnosticos"
    linhas = ["## data/interim/diagnosticos", ""]
    arquivos = sorted(pasta.glob("*")) if pasta.exists() else []
    if not arquivos:
        linhas.append("- (vazia)")
    for a in arquivos:
        if a.is_file():
            linhas.append(f"- {a.name} ({tamanho_mb(a):.2f} MB)")
    linhas.append("")
    return linhas


def arvore_raw(profundidade: int = 4) -> list[str]:
    raiz = BASE_DIR / "data" / "raw"
    linhas = ["## data/raw (estrutura; só nomes e contagens, nenhum conteúdo)", ""]
    if not raiz.exists():
        linhas.append("- (pasta não encontrada)")
        return linhas

    def visitar(pasta: Path, nivel: int) -> None:
        filhos = sorted(pasta.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        arquivos = [p for p in filhos if p.is_file()]
        pastas = [p for p in filhos if p.is_dir()]
        recuo = "  " * nivel
        if arquivos:
            if len(arquivos) <= 8:
                resumo = ", ".join(f"`{a.name}`" for a in arquivos)
            else:
                por_ext: dict[str, int] = {}
                for a in arquivos:
                    por_ext[a.suffix.lower() or "(sem extensão)"] = por_ext.get(a.suffix.lower() or "(sem extensão)", 0) + 1
                resumo = ", ".join(f"{n} arquivo(s) {ext}" for ext, n in sorted(por_ext.items()))
            total = sum(a.stat().st_size for a in arquivos) / 1e6
            linhas.append(f"{recuo}- arquivos: {resumo} ({total:.1f} MB)")
        for d in pastas:
            linhas.append(f"{recuo}- **{d.name}/**")
            if nivel + 1 < profundidade:
                visitar(d, nivel + 1)

    visitar(raiz, 0)
    linhas.append("")
    return linhas


def gerar_inventario() -> Path:
    cab = [
        "# Inventário dos dados (gerado automaticamente)",
        "",
        f"- Gerado em {date.today():%d/%m/%Y} a partir do computador do Henrique.",
        f"- Python {sys.version.split()[0]} | Polars {pl.__version__}",
        f"- Raiz do projeto: {BASE_DIR}",
        "- Este arquivo descreve o que existe em disco (esquemas, linhas, anos). O significado das fontes está no arquivo 02 e o estado do pipeline, no 03.",
        "",
    ]
    corpo = inventario_parquets() + lista_diagnosticos() + arvore_raw()
    destino = SAIDA_DIR / "INVENTARIO_DADOS.md"
    destino.write_text("\n".join(cab + corpo), encoding="utf-8")
    return destino


# ---------------------------------------------------------------- pacote de código
def coletar_scripts() -> list[Path]:
    achados = []
    for p in BASE_DIR.rglob("*.py"):
        partes = set(p.relative_to(BASE_DIR).parts[:-1])
        if partes & PASTAS_IGNORADAS:
            continue
        achados.append(p)
    return sorted(achados, key=lambda p: p.relative_to(BASE_DIR).as_posix().lower())


def gerar_codigo() -> list[Path]:
    scripts = coletar_scripts()
    tabela = ["| Arquivo | Linhas | Modificado em |", "|---|---|---|"]
    blocos: list[tuple[str, str]] = []
    alertas = []

    for p in scripts:
        rel = p.relative_to(BASE_DIR).as_posix()
        texto = p.read_text(encoding="utf-8", errors="replace")
        n_linhas = texto.count("\n") + 1
        data_mod = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        tabela.append(f"| `{rel}` | {n_linhas} | {data_mod} |")
        aviso = ""
        if PADRAO_CREDENCIAL.search(texto):
            aviso = "  (ATENÇÃO: possível credencial no texto; conferir antes de subir)"
            alertas.append(rel)
        blocos.append((rel, f"\n\n## {rel}{aviso}\n\n- {n_linhas} linhas | modificado em {data_mod}\n\n````python\n{texto.rstrip()}\n````\n"))

    partes: list[list[str]] = []
    atual: list[str] = []
    tamanho = 0
    for _, bloco in blocos:
        if atual and tamanho + len(bloco) > LIMITE_CARACTERES_CODIGO:
            partes.append(atual)
            atual, tamanho = [], 0
        atual.append(bloco)
        tamanho += len(bloco)
    if atual:
        partes.append(atual)

    gerados = []
    for i, conteudo in enumerate(partes, 1):
        nome = "CODIGO_PIPELINE.md" if len(partes) == 1 else f"CODIGO_PIPELINE_{i}.md"
        cab = [f"# Código do pipeline (parte {i} de {len(partes)})", "",
               f"Gerado em {date.today():%d/%m/%Y}. Lista de todos os scripts do repositório:", ""]
        if i == 1:
            cab += tabela + [""]
        destino = SAIDA_DIR / nome
        destino.write_text("\n".join(cab) + "".join(conteudo), encoding="utf-8")
        gerados.append(destino)

    if alertas:
        print(f"[ATENÇÃO] Possível credencial em: {alertas}. Revise antes de subir.")
    print(f"[INFO] {len(scripts)} script(s) .py coletado(s).")
    return gerados


if __name__ == "__main__":
    print(f"Raiz do projeto: {BASE_DIR}")
    inv = gerar_inventario()
    cod = gerar_codigo()
    print("\n[OK] Arquivos gerados em", SAIDA_DIR)
    for f in [inv] + cod:
        print(f"  - {f.name} ({tamanho_mb(f):.2f} MB)")
    print("\nRevise os arquivos antes de subir para o projeto no Claude (nomes, caminhos e qualquer dado sensível).")
