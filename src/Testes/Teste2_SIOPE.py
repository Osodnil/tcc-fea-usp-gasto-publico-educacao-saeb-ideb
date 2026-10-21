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
RAW = BASE_DIR / "data" / "raw" / "Microdados Censo Escolar"
ANOS = ["2019", "2023", "2025"]
ALVO = {"QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED"}


if __name__ == "__main__":
    dicionarios = [
        f for f in RAW.rglob("*.xlsx")
        if "icion" in f.name.lower()
        and not f.name.startswith("~$")
        and f.relative_to(RAW).parts[0] in ANOS
    ]

    for caminho in sorted(dicionarios):
        ano = caminho.relative_to(RAW).parts[0]
        print(f"\n{'=' * 70}\n{ano}: {caminho.name}\n{'=' * 70}")

        abas = pl.read_excel(caminho, sheet_id=0)  # dict: nome da aba -> DataFrame
        print(f"Abas: {list(abas.keys())}")

        achou_algo = False
        for nome, df in abas.items():
            achados = []
            for row in df.iter_rows():
                celulas = [str(c).strip() for c in row if c is not None]
                if any(c.startswith("QT_MAT") for c in celulas):
                    achados.append(celulas)
            if not achados:
                continue

            achou_algo = True
            variaveis = [next(c for c in cel if c.startswith("QT_MAT")) for cel in achados]
            print(f"\n[Aba '{nome}'] {len(variaveis)} variáveis QT_MAT*")
            print("  ", variaveis[:40])
            for cel in achados:
                var = next(c for c in cel if c.startswith("QT_MAT"))
                if var in ALVO:
                    print("  ", cel[:4])

        if not achou_algo:
            print("  Nenhuma variável QT_MAT* encontrada neste dicionário.")