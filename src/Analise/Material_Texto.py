"""Tabelas e figuras dos resultados, para o texto do TCC (passo 5 da fase de análise).

Lê as saídas dos scripts de análise (rodar antes, nesta ordem: Modelo_Principal.py, Modelo_Estadual.py,
Heterogeneidade.py, Sensibilidade_Modelo.py) e o painel municipal, e grava em docs/resultados/:
- tabelas.md: sete tabelas em Markdown (amostra, ρ de Spearman, modelo principal, defasagens, heterogeneidade,
  sensibilidade, camada estadual), com números no formato brasileiro;
- figuras/fig1_entre_dentro.png, fig2_defasagens.png, fig3_heterogeneidade.png, fig4_sensibilidade.png:
  coeficientes do log do gasto com intervalo de 95%.

Leitura sempre de associação, não de efeito causal (A1). Paleta: dois primeiros tons da paleta de referência do
painel (azul e laranja), texto em tinta neutra, linha do zero em cinza.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import polars as pl

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Modelo_Principal as M  # noqa: E402

DIAG = M.DIAG_DIR
SAIDA = M.BASE_DIR / "docs" / "resultados"
FIG = SAIDA / "figuras"
AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, GRADE = "#0b0b0b", "#52514e", "#d9d8d2"
ETAPAS = {"AI": "Anos Iniciais", "AF": "Anos Finais", "EM": "Ensino Médio"}
DISCS = {"MT": "Matemática", "LP": "Português"}


def br(x: float | None, casas: int = 2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    s = f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.replace("-", "−")  # sinal de menos tipográfico


def estrelas(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def coef_ep(c: float, ep: float, p: float) -> str:
    return f"{br(c)}{estrelas(p)} ({br(ep)})"


def tabela_md(cab: list[str], linhas: list[list[str]]) -> str:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(l) + " |" for l in linhas]
    return "\n".join(out)


NOTA_EST = "*Coeficiente do log do gasto por aluno (erro-padrão agrupado entre parênteses). \\*\\*\\* p < 0,01; \\*\\* p < 0,05; \\* p < 0,10. Associação, não efeito causal.*"


# ───────────────────────── tabelas ─────────────────────────

def t1_amostra(p: pl.DataFrame) -> str:
    linhas = []
    for etapa in ["AI", "AF"]:
        for ano in [2017, 2019, 2021, 2023, 2025]:
            d = p.filter((pl.col("ETAPA") == etapa) & (pl.col("ANO") == ano) & pl.col("NOTA_MT").is_not_null())
            linhas.append([ETAPAS[etapa], str(ano), br(d.height, 0), "R$ " + br(d["GASTO_ALUNO_R2025_L0"].median(), 0),
                           br(d["NOTA_MT"].mean(), 1), br(d["NOTA_LP"].mean(), 1)])
    return ("### Tabela 1. Redes municipais com nota, gasto e proficiência por edição\n\n"
            + tabela_md(["Etapa", "Edição", "Redes com nota", "Gasto por aluno (mediana, R$ de 2025)",
                         "Matemática (média)", "Português (média)"], linhas)
            + "\n\n*Gasto do Ensino Fundamental da rede municipal (SIOPE) ÷ matrículas, corrigido pelo IPCA. "
              "Proficiência em pontos do Saeb, média simples entre as redes.*")


def t2_spearman(p: pl.DataFrame) -> str:
    linhas = []
    for ano in [2017, 2019, 2021, 2023, 2025]:
        cel = [str(ano)]
        for k in M.DEFASAGENS:
            d = p.filter((pl.col("ETAPA") == "AI") & (pl.col("ANO") == ano)).drop_nulls(["NOTA_MT", f"GASTO_ALUNO_R2025_L{k}"])
            cel.append(br(d.select(pl.corr(f"GASTO_ALUNO_R2025_L{k}", "NOTA_MT", method="spearman")).item())
                       if d.height >= 30 else "—")
        linhas.append(cel)
    return ("### Tabela 2. Correlação de Spearman entre gasto por aluno e proficiência (AI, Matemática)\n\n"
            + tabela_md(["Edição", "Gasto do mesmo ano", "1 ano antes", "2 anos antes", "4 anos antes"], linhas)
            + "\n\n*Sem controles. Vazio: sem gasto daquele ano (a série começa em 2017).*")


def t3_modelo(coefs: pl.DataFrame) -> str:
    esp = [("MQO agrupado", "MQO agrupado, 2017–2023"), ("EF de município", "EF de município + edição, 2017–2023"),
           ("EF de município e UF × edição", "EF de município + UF × edição, 2017–2025 (referência)")]
    g = coefs.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO") & (pl.col("DEFASAGEM") == 0))
    linhas = []
    for e, rot in esp:
        cel = [rot]
        for etapa in ["AI", "AF"]:
            for disc in ["MT", "LP"]:
                r = g.filter((pl.col("ESPECIFICACAO") == e) & (pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc)).row(0, named=True)
                cel.append(f"{coef_ep(r['COEF'], r['EP'], r['P'])}<br>N = {br(r['N'], 0)}")
        linhas.append(cel)
    return ("### Tabela 3. Modelo principal: gasto do mesmo ano e proficiência\n\n"
            + tabela_md(["Especificação", "AI Matemática", "AI Português", "AF Matemática", "AF Português"], linhas)
            + "\n\n" + NOTA_EST + " *Controles: infraestrutura e log das matrículas; no MQO, também log da população "
              "e alfabetização; nas especificações de 2017–2023, IDHM Renda e Longevidade da UF. +10% no gasto = "
              "coeficiente × 0,095 ponto.*")


def t4_defasagens(comp: pl.DataFrame) -> str:
    d = comp.filter(pl.col("JANELA") == "2019-2025, UF × edição")
    linhas = []
    for etapa in ["AI", "AF"]:
        for disc in ["MT", "LP"]:
            cel = [f"{ETAPAS[etapa]}, {DISCS[disc]}"]
            for k in [0, 1, 2]:
                r = d.filter((pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc) & (pl.col("DEFASAGEM") == k)).row(0, named=True)
                cel.append(coef_ep(r["COEF"], r["EP"], r["P"]))
            linhas.append(cel)
    return ("### Tabela 4. Defasagem do gasto na mesma amostra (referência, 2019–2025)\n\n"
            + tabela_md(["Etapa e disciplina", "Gasto do mesmo ano", "1 ano antes", "2 anos antes"], linhas)
            + "\n\n" + NOTA_EST + " *Mesmas linhas em todas as colunas (redes com os três gastos).*")


ORDEM_GRUPOS = {"Porte": ["Até 5 mil", "5 a 10 mil", "10 a 20 mil", "20 a 50 mil", "50 a 100 mil", "Mais de 100 mil"],
                "Região": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
                "Cluster": [str(i) for i in range(1, 8)],
                "Faixa de gasto médio": ["Q1", "Q2", "Q3", "Q4", "Q5"]}


def rotulos_cluster() -> dict[str, str]:
    """Rótulo de cada cluster, lido da tabela do painel (Analise_Clusters.py gera; "Predomínio do …" desde 2026-11-12)."""
    c = pl.read_parquet(M.PROCESSED_DIR / "powerbi" / "dim_cluster.parquet").sort("CLUSTER")
    return {str(r["CLUSTER"]): r["CLUSTER_ROTULO"] for r in c.iter_rows(named=True)}


def t5_heterogeneidade(het: pl.DataFrame) -> str:
    d = het.filter(pl.col("ETAPA") == "AI")
    linhas = []
    for dim, grupos in ORDEM_GRUPOS.items():
        for g in grupos:
            cel = [dim, g]
            for disc in ["MT", "LP"]:
                r = d.filter((pl.col("DIMENSAO") == dim) & (pl.col("GRUPO") == g) & (pl.col("DISCIPLINA") == disc)).row(0, named=True)
                cel.append(coef_ep(r["COEF"], r["EP"], r["P"]))
            cel.append(br(r["MUN_GRUPO"], 0))
            linhas.append(cel)
    return ("### Tabela 5. Heterogeneidade da associação dentro do município (AI)\n\n"
            + tabela_md(["Dimensão", "Grupo", "Matemática", "Português", "Municípios"], linhas)
            + "\n\n" + NOTA_EST + " *Especificação de referência com uma inclinação por grupo. A igualdade das "
              "inclinações é rejeitada nas quatro dimensões (p ≤ 0,02). Clusters: " + "; ".join(
                f"{n} = {r}" for n, r in rotulos_cluster().items())
            + ". O k-médias não usa a região: ela só nomeia o grupo pela maioria dos municípios. Faixa de gasto: "
              "quintil do gasto médio de 2017–2025.*")


def t6_sensibilidade(sens: pl.DataFrame) -> str:
    d = sens.filter(pl.col("CAMADA") == "Municipal")
    testes = d.filter((pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))["TESTE"].to_list()
    linhas = []
    for t in testes:
        cel = [t]
        for etapa in ["AI", "AF"]:
            for disc in ["MT", "LP"]:
                r = d.filter((pl.col("TESTE") == t) & (pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc)).row(0, named=True)
                cel.append(coef_ep(r["COEF"], r["EP"], r["P"]))
        linhas.append(cel)
    return ("### Tabela 6. Testes de sensibilidade (camada municipal, gasto do mesmo ano)\n\n"
            + tabela_md(["Teste", "AI Matemática", "AI Português", "AF Matemática", "AF Português"], linhas)
            + "\n\n" + NOTA_EST + " *Cada teste muda uma coisa na referência (EF de município + UF × edição, "
              "2017–2025). As três últimas linhas usam efeito de edição e 2017–2023, porque o efeito de UF × edição "
              "absorve o IDHM.*")


def t7_estadual(est: pl.DataFrame, sens: pl.DataFrame) -> str:
    g = est.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO") & (pl.col("DEFASAGEM") == 0))
    vb = sens.filter((pl.col("CAMADA") == "Estadual") & (pl.col("TESTE") == "Versão B do gasto"))
    linhas = []
    for e, rot in [("MQO agrupado", "MQO agrupado, 2017–2023"), ("EF de UF", "EF de UF, 2017–2023 (referência)"),
                   ("EF de UF, com 2025", "EF de UF, 2017–2025, sem IDHM")]:
        cel = [rot]
        for etapa in ["AF", "EM"]:
            for disc in ["MT", "LP"]:
                r = g.filter((pl.col("ESPECIFICACAO") == e) & (pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc)).row(0, named=True)
                cel.append(f"{coef_ep(r['COEF'], r['EP'], r['P'])}<br>IC: {br(r['IC95_INF'], 1)} a {br(r['IC95_SUP'], 1)}")
        linhas.append(cel)
    cel = ["Versão B do gasto (referência)"]
    for etapa in ["AF", "EM"]:
        for disc in ["MT", "LP"]:
            r = vb.filter((pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc)).row(0, named=True)
            cel.append(coef_ep(r["COEF"], r["EP"], r["P"]))
    linhas.append(cel)
    return ("### Tabela 7. Camada estadual: gasto estadual por aluno e proficiência das redes estaduais\n\n"
            + tabela_md(["Especificação", "AF Matemática", "AF Português", "EM Matemática", "EM Português"], linhas)
            + "\n\n" + NOTA_EST + " *27 UFs (23 na versão B). Erros agrupados por UF; valores-p e intervalos de 95% "
              "pela t com 26 graus de liberdade.*")


# ───────────────────────── figuras ─────────────────────────

def estilo(ax, titulo: str | None = None) -> None:
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRADE)
    ax.tick_params(colors=TINTA_2, labelsize=9, length=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 0) if float(v).is_integer() else br(v, 1)))
    ax.grid(axis="x", color=GRADE, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.axvline(0, color=TINTA_2, linewidth=1)
    if titulo:
        ax.set_title(titulo, fontsize=10, color=TINTA, loc="left", fontweight="bold")


def pontos(ax, ys, c, lo, hi, cor) -> None:
    ax.hlines(ys, lo, hi, color=cor, linewidth=2)
    ax.plot(c, ys, "o", color=cor, markersize=7, markeredgecolor="white", markeredgewidth=1.5, zorder=3)


def legenda_disciplinas(fig) -> None:
    """Legenda no alto da figura, fora das áreas de dados (dentro do painel, cobria marcas)."""
    fig.legend(handles=[plt.Line2D([], [], color=AZUL, marker="o", linewidth=2, label="Matemática"),
                        plt.Line2D([], [], color=LARANJA, marker="o", linewidth=2, label="Português")],
               frameon=False, fontsize=9, loc="upper right", ncol=2, labelcolor=TINTA_2)
    fig._tem_legenda = True


def salvar(fig, nome: str, legenda_x: str) -> None:
    fig.supxlabel(legenda_x, fontsize=9, color=TINTA_2)
    fig.patch.set_facecolor("white")
    fig.tight_layout(rect=(0, 0, 1, 0.93) if getattr(fig, "_tem_legenda", False) else None)
    fig.savefig(FIG / nome, dpi=200, facecolor="white")
    plt.close(fig)


ROTULO_X = "Pontos do Saeb por log do gasto por aluno (intervalo de 95%)"


def f1_entre_dentro(coefs: pl.DataFrame) -> None:
    esp = [("MQO agrupado", "Entre e dentro\n(MQO, 2017–23)"), ("EF de município", "Dentro do município\n(2017–23, IDHM)"),
           ("EF de município e UF × edição", "Dentro, mesmo estado\n(2017–25, referência)")]
    g = coefs.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO") & (pl.col("DEFASAGEM") == 0))
    fig, eixos = plt.subplots(1, 2, figsize=(9, 3.4), sharex=True, sharey=True)
    for ax, etapa in zip(eixos, ["AI", "AF"]):
        for j, (disc, cor) in enumerate([("MT", AZUL), ("LP", LARANJA)]):
            ys = np.arange(len(esp))[::-1] + (0.12 if j == 0 else -0.12)
            rs = [g.filter((pl.col("ESPECIFICACAO") == e) & (pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc)).row(0, named=True) for e, _ in esp]
            pontos(ax, ys, [r["COEF"] for r in rs], [r["IC95_INF"] for r in rs], [r["IC95_SUP"] for r in rs], cor)
        ax.set_yticks(np.arange(len(esp))[::-1], [r for _, r in esp])
        estilo(ax, ETAPAS[etapa])
    legenda_disciplinas(fig)
    salvar(fig, "fig1_entre_dentro.png", ROTULO_X)


def f2_defasagens(comp: pl.DataFrame) -> None:
    d = comp.filter(pl.col("JANELA") == "2019-2025, UF × edição")
    rot = ["Mesmo ano", "1 ano antes", "2 anos antes"]
    fig, eixos = plt.subplots(1, 2, figsize=(9, 2.9), sharex=True, sharey=True)
    for ax, etapa in zip(eixos, ["AI", "AF"]):
        for j, (disc, cor) in enumerate([("MT", AZUL), ("LP", LARANJA)]):
            rs = [d.filter((pl.col("ETAPA") == etapa) & (pl.col("DISCIPLINA") == disc) & (pl.col("DEFASAGEM") == k)).row(0, named=True) for k in [0, 1, 2]]
            ys = np.arange(3)[::-1] + (0.12 if j == 0 else -0.12)
            pontos(ax, ys, [r["COEF"] for r in rs], [r["COEF"] - 1.96 * r["EP"] for r in rs],
                   [r["COEF"] + 1.96 * r["EP"] for r in rs], cor)
        ax.set_yticks(np.arange(3)[::-1], rot)
        estilo(ax, ETAPAS[etapa])
    legenda_disciplinas(fig)
    salvar(fig, "fig2_defasagens.png", ROTULO_X + "; mesma amostra, 2019–2025")


def f3_heterogeneidade(het: pl.DataFrame) -> None:
    d = het.filter((pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))
    ordem = ORDEM_GRUPOS
    # rótulo curto do eixo: número, região predominante e porte (o painel usa o mesmo, CLUSTER_CURTO)
    curto = pl.read_parquet(M.PROCESSED_DIR / "powerbi" / "dim_municipio.parquet").select("CLUSTER", "CLUSTER_CURTO").unique()
    nomes_cluster = {str(r["CLUSTER"]): r["CLUSTER_CURTO"] for r in curto.drop_nulls("CLUSTER").iter_rows(named=True)}
    fig, eixos = plt.subplots(2, 2, figsize=(9, 6.2), sharex=True)
    for ax, (dim, grupos) in zip(eixos.flat, ordem.items()):
        rs = [d.filter((pl.col("DIMENSAO") == dim) & (pl.col("GRUPO") == g)).row(0, named=True) for g in grupos]
        ys = np.arange(len(grupos))[::-1]
        pontos(ax, ys, [r["COEF"] for r in rs], [r["IC95_INF"] for r in rs], [r["IC95_SUP"] for r in rs], AZUL)
        rotulos = [nomes_cluster[g] for g in grupos] if dim == "Cluster" else (
            ["Q1 (menor)", "Q2", "Q3", "Q4", "Q5 (maior)"] if dim == "Faixa de gasto médio" else grupos)
        ax.set_yticks(ys, rotulos)
        estilo(ax, dim)
    salvar(fig, "fig3_heterogeneidade.png", ROTULO_X + "; AI, Matemática")


def f4_sensibilidade(sens: pl.DataFrame) -> None:
    d = sens.filter((pl.col("CAMADA") == "Municipal") & (pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))
    ref = d.filter(pl.col("TESTE").str.starts_with("Referência (2017"))["COEF"].item()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ys = np.arange(d.height)[::-1]
    pontos(ax, ys, d["COEF"].to_list(), d["IC95_INF"].to_list(), d["IC95_SUP"].to_list(), AZUL)
    ax.axvline(ref, color=AZUL, linewidth=1, linestyle=(0, (3, 3)), alpha=0.6)
    ax.set_yticks(ys, d["TESTE"].to_list())
    estilo(ax)
    salvar(fig, "fig4_sensibilidade.png", ROTULO_X + "; AI, Matemática (tracejado: referência)")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    p = M.base()
    coefs = pl.read_csv(DIAG / "modelo_principal_coeficientes.csv")
    comp = pl.read_csv(DIAG / "modelo_principal_defasagens_mesma_amostra.csv")
    het = pl.read_csv(DIAG / "heterogeneidade_coeficientes.csv", schema_overrides={"GRUPO": pl.Utf8})
    sens = pl.read_csv(DIAG / "sensibilidade_modelo.csv")
    est = pl.read_csv(DIAG / "modelo_estadual_coeficientes.csv")
    partes = ["# Tabelas dos resultados",
              "*Gerado por `src/Analise/Material_Texto.py` a partir das saídas dos scripts de análise. "
              "Não editar à mão: rodar o script de novo. Decisões e leitura em `docs/decisoes_metodo.md` "
              "(A4, A11, A12, A13) e em `docs/nota_resultados.md`.*",
              t1_amostra(p), t2_spearman(p), t3_modelo(coefs), t4_defasagens(comp), t5_heterogeneidade(het),
              t6_sensibilidade(sens), t7_estadual(est, sens)]
    (SAIDA / "tabelas.md").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    f1_entre_dentro(coefs)
    f2_defasagens(comp)
    f3_heterogeneidade(het)
    f4_sensibilidade(sens)
    print(f"[OK] tabelas.md e 4 figuras em {SAIDA.relative_to(M.BASE_DIR)}")


if __name__ == "__main__":
    main()
