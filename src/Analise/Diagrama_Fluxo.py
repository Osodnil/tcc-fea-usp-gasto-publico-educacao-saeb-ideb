"""Diagrama do fluxo de dados do projeto, para o texto do TCC (docs/resultados/figuras/fig0_fluxo_dados.png).

Fontes públicas → extração → tratamento → painéis de dados → análise e modelo em estrela → painel em Power BI.
Figura estática para impressão: caixas neutras, texto em tinta escura, uma cor só para o produto final.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

RAIZ = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SAIDA = RAIZ / "docs" / "resultados" / "figuras" / "fig0_fluxo_dados.png"
TINTA, TINTA_2, BORDA, FUNDO, AZUL, AZUL_CLARO = "#0b0b0b", "#52514e", "#b9b8b1", "#f4f4f1", "#2a78d6", "#e3eefb"


def caixa(ax, x, y, w, h, titulo, linhas, destaque=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", linewidth=1.2,
                                edgecolor=AZUL if destaque else BORDA, facecolor=AZUL_CLARO if destaque else FUNDO))
    ax.text(x + w / 2, y + h - 0.22, titulo, ha="center", va="top", fontsize=9.5, fontweight="bold", color=TINTA)
    ax.text(x + w / 2, y + h - 0.60, "\n".join(linhas), ha="center", va="top", fontsize=7.6, color=TINTA_2, linespacing=1.35)


def seta(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=11, linewidth=1.1, color=TINTA_2))


def main() -> None:
    fig, ax = plt.subplots(figsize=(9, 4.3))
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 6)
    ax.axis("off")
    caixa(ax, 0.1, 1.2, 2.3, 3.6, "Fontes públicas",
          ["SIOPE (FNDE)", "SICONFI (Tesouro)", "Saeb e IDEB (Inep)", "Censo Escolar (Inep)", "Censo 2022 (IBGE)",
           "IDHM por UF (Atlas)", "IPCA (IBGE)", "Malha Municipal (IBGE)"])
    caixa(ax, 2.9, 2.0, 2.0, 2.0, "Extração", ["um script por fonte", "APIs e planilhas", "→ arquivos Parquet"])
    caixa(ax, 5.4, 2.0, 2.0, 2.0, "Tratamento", ["limpeza e validação", "valores em R$ de 2025", "gasto por aluno"])
    caixa(ax, 7.9, 2.0, 2.0, 2.0, "Painéis de dados", ["municipal: município ×", "etapa × edição", "estadual: UF × etapa ×", "edição"])
    caixa(ax, 10.4, 3.5, 2.1, 1.9, "Análise", ["clusters", "nota esperada", "modelos e testes"])
    caixa(ax, 10.4, 0.6, 2.1, 1.9, "Painel em Power BI", ["modelo em estrela", "(13 tabelas, 85 medidas)", "10 páginas"], destaque=True)
    for x in (2.4, 4.9, 7.4):
        seta(ax, x + 0.03, 3.0, x + 0.47, 3.0)
    seta(ax, 9.93, 3.4, 10.37, 4.2)
    seta(ax, 9.93, 2.6, 10.37, 1.8)
    seta(ax, 11.45, 3.47, 11.45, 2.53)
    ax.text(6.3, 0.75, "Tudo em Python (Polars), em scripts versionados; um comando refaz o fluxo inteiro.",
            ha="center", fontsize=8, color=TINTA_2, style="italic")
    fig.patch.set_facecolor("white")
    fig.tight_layout()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAIDA, dpi=200, facecolor="white")
    print(f"[OK] {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
