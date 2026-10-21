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
TECNICO = re.compile(r"^[A-Za-z]{2,3}_[A-Za-z0-9_]+$")
COM_ANO = re.compile(r"^(.+?)_((?:19|20)\d{2})(?:_.*)?$")


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").upper()


def pasta_ideb() -> Path:
    candidatas = [p for p in RAW_ROOT.iterdir() if p.is_dir() and "IDEB" in normalizar(p.name)]
    if not candidatas:
        raise FileNotFoundError(f"Nenhuma pasta com 'IDEB' em {RAW_ROOT}")
    return candidatas[0]


def celulas(linha) -> list[str]:
    return [str(c).strip() for c in linha if c is not None and str(c).strip() != ""]


def inspecionar(caminho: Path, aba: str) -> None:
    bruto = pl.read_excel(caminho, sheet_name=aba, read_options={"header_row": None})
    print(f"\n[ABA '{aba}'] {bruto.height} linhas x {bruto.width} colunas")

    print("  Primeiras linhas (até 8 células de cada):")
    for i in range(min(12, bruto.height)):
        c = celulas(bruto.row(i))
        print(f"   {i:>2}: {len(c):>3} células | {[x[:26] for x in c[:8]]}")

    melhor, n_melhor = None, 0
    for i in range(min(40, bruto.height)):
        n = sum(1 for x in celulas(bruto.row(i)) if TECNICO.match(x))
        if n > n_melhor:
            melhor, n_melhor = i, n
    if melhor is None or n_melhor < 5:
        print("  Sem linha de nomes técnicos (cabeçalho só descritivo).")
        return

    cab = [str(c).strip() if c is not None else "" for c in bruto.row(melhor)]
    dados = bruto.slice(melhor + 1)
    ids_idx = [j for j, c in enumerate(cab) if c and not COM_ANO.match(c)]
    print(f"  Cabeçalho técnico na linha {melhor} | {dados.height} linhas de dados")
    print(f"  Colunas sem ano: {[cab[j] for j in ids_idx][:20]}")

    familias: dict[str, set[int]] = {}
    for c in cab:
        m = COM_ANO.match(c)
        if m:
            familias.setdefault(m.group(1), set()).add(int(m.group(2)))
    print("  Colunas por ano:")
    for fam, anos in familias.items():
        a = sorted(anos)
        print(f"    {fam}: {a[0]}-{a[-1]} ({len(a)} anos)")

    for j in ids_idx:
        nome = cab[j]
        if re.search(r"REDE|UF|REGIAO|NO_|SG_|CO_", nome.upper()):
            vals = sorted({str(v) for v in dados[:, j].to_list() if v is not None})
            print(f"    {nome}: {len(vals)} valores distintos | amostra: {vals[:8]}")


if __name__ == "__main__":
    pasta = pasta_ideb()
    achados = [f for f in pasta.rglob("*.xlsx") if "regioes_ufs" in f.name.lower() and not f.name.startswith("~$")]
    if len(achados) != 1:
        raise FileNotFoundError(f"Esperava 1 arquivo de regiões/UFs, achei {[f.name for f in achados]}")
    arquivo = achados[0]
    print(f"Arquivo: {arquivo.relative_to(pasta)}")
    for aba in pl.read_excel(arquivo, sheet_id=0).keys():
        try:
            inspecionar(arquivo, aba)
        except Exception as e:
            print(f"  [ERRO na aba '{aba}'] {type(e).__name__}: {e}")