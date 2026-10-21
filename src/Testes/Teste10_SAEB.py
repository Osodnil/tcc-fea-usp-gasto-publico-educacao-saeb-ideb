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
MARCADORES = {"SG_UF", "CO_MUNICIPIO", "CO_UF"}


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").upper()


def pasta_ideb() -> Path:
    candidatas = [p for p in RAW_ROOT.iterdir() if p.is_dir() and "IDEB" in normalizar(p.name)]
    if not candidatas:
        raise FileNotFoundError(f"Nenhuma pasta com 'IDEB' em {RAW_ROOT}")
    return candidatas[0]


def linha_cabecalho(df: pl.DataFrame):
    for i in range(min(40, df.height)):
        celulas = {str(c).strip() for c in df.row(i) if c is not None}
        if celulas & MARCADORES:
            return i
    return None


def inspecionar_aba(caminho: Path, aba: str) -> None:
    bruto = pl.read_excel(caminho, sheet_name=aba, read_options={"header_row": None})
    print(f"\n  [ABA '{aba}'] {bruto.height} linhas x {bruto.width} colunas")

    i = linha_cabecalho(bruto)
    if i is None:
        print("    Cabeçalho (SG_UF / CO_MUNICIPIO / CO_UF) não encontrado nas 40 primeiras linhas.")
        return

    cab = [str(c).strip() if c is not None else "" for c in bruto.row(i)]
    dados = bruto.slice(i + 1)
    print(f"    Cabeçalho na linha {i} (índice a partir de 0) | linhas de dados: {dados.height}")

    familias: dict[str, set[int]] = {}
    outros = []
    for c in cab:
        m = re.fullmatch(r"(.+?)_((?:19|20)\d{2})(?:_.*)?", c)
        if m:
            familias.setdefault(m.group(1), set()).add(int(m.group(2)))
        elif c:
            outros.append(c)

    print(f"    Colunas sem ano: {outros[:15]}")
    print("    Colunas por ano:")
    for fam, anos in familias.items():
        print(f"      {fam}: {sorted(anos)}")

    for nome in ("REDE", "SG_UF", "CO_UF", "CO_MUNICIPIO"):
        if nome in cab:
            serie = dados[:, cab.index(nome)]
            valores = sorted({str(v) for v in serie.to_list() if v is not None})
            amostra = valores[:12] if nome == "REDE" else f"{len(valores)} valores distintos"
            print(f"    {nome}: {amostra}")


if __name__ == "__main__":
    pasta = pasta_ideb()
    print(f"Pasta: {pasta}")
    arquivos = sorted(
        f for f in pasta.rglob("*.xlsx")
        if not f.name.startswith("~$") and not f.stem.lower().startswith("md5")
    )
    print(f"{len(arquivos)} arquivo(s) .xlsx:")
    for f in arquivos:
        print("  -", f.relative_to(pasta))

    for f in arquivos:
        print("\n" + "=" * 70 + f"\n{f.relative_to(pasta)}\n" + "=" * 70)
        try:
            abas = list(pl.read_excel(f, sheet_id=0).keys())
        except Exception as e:
            print(f"  [ERRO ao listar abas] {type(e).__name__}: {e}")
            continue
        print(f"  Abas: {abas}")
        for aba in abas:
            try:
                inspecionar_aba(f, aba)
            except Exception as e:
                print(f"  [ERRO na aba '{aba}'] {type(e).__name__}: {e}")