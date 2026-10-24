"""Gera um pacote ZIP para enviar a quem não vai rodar o código (ex.: a orientadora).

Conteúdo: dashboard HTML, documentos convertidos para HTML (abrem no navegador e podem
ser impressos em PDF), painéis em Excel com dicionário de colunas e uma cópia do código.
Saída: exportacao/TCC_Gasto_Saeb_<data>.zip (pasta fora do Git).
"""
import html
import re
import shutil
import subprocess
import zipfile
from datetime import date
from pathlib import Path

import markdown
import polars as pl
import xlsxwriter


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
HOJE = date.today()
NOME = f"TCC_Gasto_Saeb_{HOJE.isoformat()}"
SAIDA_DIR = BASE_DIR / "exportacao"
PACOTE = SAIDA_DIR / NOME

DOCUMENTOS = [  # (origem, nome no pacote, título)
    ("docs/resumo_reuniao_orientadora.md", "1_Resumo_para_a_orientadora.html", "Resumo para a orientadora"),
    ("docs/decisoes_metodo.md", "2_Registro_de_decisoes_de_metodo.html", "Registro de decisões de método"),
    ("README.md", "3_Visao_geral_do_projeto.html", "Visão geral do projeto"),
]

CSS = """
body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color: #0b0b0b; background: #fcfcfb;
  max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; line-height: 1.55; font-size: 15px; }
h1 { font-size: 26px; line-height: 1.2; } h2 { font-size: 20px; margin-top: 2em; border-bottom: 1px solid #e1e0d9; padding-bottom: 4px; }
h3 { font-size: 16px; margin-top: 1.6em; }
table { border-collapse: collapse; margin: 12px 0; font-size: 13.5px; display: block; overflow-x: auto; }
th, td { border: 1px solid #e1e0d9; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f0efec; }
code { background: #f0efec; padding: 1px 5px; border-radius: 4px; font-size: 0.92em; }
pre { background: #f0efec; padding: 12px; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { border-left: 3px solid #c3c2b7; margin: 12px 0; padding: 2px 14px; color: #52514e; }
.meta { color: #52514e; font-size: 13px; border-bottom: 1px solid #e1e0d9; padding-bottom: 10px; margin-bottom: 20px; }
@media print { body { max-width: none; font-size: 11pt; } a { color: inherit; } }
"""


def pagina(titulo: str, corpo: str, versao: str) -> str:
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(titulo)}</title><style>{CSS}</style></head><body>"
            f'<p class="meta">TCC FEA/USP · Gasto público em educação e desempenho no Saeb · '
            f"versão de {HOJE.strftime('%d/%m/%Y')} (código {versao}). "
            f"Para salvar em PDF: Ctrl+P → Salvar como PDF.</p>{corpo}</body></html>")


def descricao_coluna(c: str) -> str:
    """Dicionário de colunas dos painéis, por nome ou padrão de nome."""
    fixas = {
        "CO_MUNICIPIO": "Código IBGE do município (7 dígitos)",
        "NO_MUNICIPIO": "Nome do município",
        "SG_UF": "Sigla da UF",
        "NM_REGIAO": "Região do país",
        "ETAPA": "Etapa do Saeb: AI = Anos Iniciais (5º ano), AF = Anos Finais (9º ano), EM = Ensino Médio",
        "ANO": "Edição do Saeb (2017, 2019, 2021, 2023, 2025)",
        "NOTA_MT": "Nota de Matemática no Saeb (pontos da escala Saeb)",
        "NOTA_LP": "Nota de Língua Portuguesa no Saeb (pontos da escala Saeb)",
        "NOTA_N": "Nota padronizada N (0 a 10), combina Matemática e Português",
        "IND_REND": "Indicador de rendimento (aprovação), 0 a 1",
        "IDEB": "IDEB = nota padronizada N × indicador de rendimento",
        "TEM_NOTA": "Verdadeiro se o Inep divulgou nota para a rede nessa edição",
        "QT_MAT_FUND": "Matrículas no Ensino Fundamental da rede municipal (Censo Escolar)",
        "QT_MAT_FUND_AI": "Matrículas nos Anos Iniciais da rede municipal",
        "QT_MAT_FUND_AF": "Matrículas nos Anos Finais da rede municipal",
        "QT_MAT_BAS": "Matrículas na educação básica da rede estadual",
        "QT_MAT_MED": "Matrículas no Ensino Médio da rede estadual",
        "GASTO_361_R2025": "Despesa paga na subfunção 361 (Ensino Fundamental), SIOPE, em R$ de 2025",
        "SUP364_AUSENTE": "Verdadeiro se o estado não tem a linha 12.364 (Ensino Superior) no SICONFI nesse ano",
        "POPULACAO_TOTAL_CENSO": "População total (Censo Demográfico 2022)",
        "TAXA_ALFABETIZACAO_15MAIS": "Taxa de alfabetização de 15 anos ou mais, % (Censo Demográfico 2022)",
        "ANO_IDHM": "Ano do IDHM usado (ano anterior à edição do Saeb)",
        "IDHM": "IDHM da UF no ano anterior à edição do Saeb",
        "IDHM_EDUCACAO": "IDHM Educação da UF no ano anterior",
        "IDHM_RENDA": "IDHM Renda da UF no ano anterior",
        "IDHM_LONGEVIDADE": "IDHM Longevidade da UF no ano anterior",
        "ESCOLAS_MUNICIPAIS": "Número de escolas da rede municipal no ano (Censo Escolar)",
        "ESCOLAS_ESTADUAIS": "Número de escolas da rede estadual na UF no ano (Censo Escolar)",
    }
    if c in fixas:
        return fixas[c]
    defas = {"L0": "do mesmo ano do Saeb", "L1": "de 1 ano antes", "L2": "de 2 anos antes", "L4": "de 4 anos antes"}
    sufixo = c.rsplit("_", 1)[-1]
    if c.startswith("GASTO_ALUNO_R2025_"):
        return f"Gasto por aluno {defas[sufixo]}, R$ de 2025: subfunção 361 paga ÷ matrículas do Fundamental"
    if c.startswith("GASTO_ALUNO_A_R2025_"):
        return f"Gasto por aluno {defas[sufixo]}, R$ de 2025, versão A (Ensino Superior ausente = 0)"
    if c.startswith("GASTO_ALUNO_B_R2025_"):
        return f"Gasto por aluno {defas[sufixo]}, R$ de 2025, versão B (Ensino Superior ausente = dado faltante)"
    if c.startswith("GASTO_EXTREMO_"):
        return f"Verdadeiro se o gasto por aluno {defas[sufixo]} está fora de 0,5%–99,5% do ano (só marcado, não excluído)"
    if c.startswith("PROP_IN_"):
        item = c.removeprefix("PROP_IN_").replace("_", " ").lower()
        return f"Proporção das escolas da rede com {item} (Censo Escolar, mesmo ano)"
    return ""


def exportar_dados(destino: Path) -> None:
    mun = pl.read_parquet(BASE_DIR / "data/processed/painel_municipal.parquet")
    est = pl.read_parquet(BASE_DIR / "data/processed/painel_estadual.parquet")
    dicionario = pl.DataFrame(
        [{"Painel": painel, "Coluna": c, "Descrição": descricao_coluna(c)}
         for painel, df in (("Municipal", mun), ("Estadual", est)) for c in df.columns]
    )
    sem_descricao = dicionario.filter(pl.col("Descrição") == "")["Coluna"].to_list()
    if sem_descricao:
        raise ValueError(f"Colunas sem descrição no dicionário: {sem_descricao}")

    destino.mkdir(parents=True, exist_ok=True)
    for nome, df in (("Painel_municipal", mun), ("Painel_estadual", est)):
        caminho = destino / f"{nome}.xlsx"
        with xlsxwriter.Workbook(caminho) as wb:
            df.write_excel(wb, worksheet="Dados", autofit=True, freeze_panes=(1, 0))
            dicionario.filter(pl.col("Painel") == nome.split("_")[1].capitalize()).drop("Painel").write_excel(
                wb, worksheet="Dicionário", autofit=True)
        df.write_csv(destino / f"{nome}.csv")  # CSV para quem usa R, Stata ou Power BI


def recuo_de_4(texto: str) -> str:
    """Os documentos usam recuo de 2 espaços em listas aninhadas (padrão do GitHub); o Python-Markdown
    exige 4. Dobra o recuo das linhas recuadas fora de blocos de código. Também separa com uma linha
    em branco o item de lista que vem logo após um parágrafo recuado, que o Python-Markdown
    juntaria ao parágrafo anterior."""
    marcador = re.compile(r"^\s*(?:[-*]|\d+\.)\s")
    saida, em_codigo, anterior = [], False, ""
    for linha in texto.splitlines():
        if linha.lstrip().startswith("```"):
            em_codigo = not em_codigo
        recuo = len(linha) - len(linha.lstrip(" "))
        if (not em_codigo and recuo == 0 and marcador.match(linha) and anterior.startswith(" ")
                and anterior.strip() and not marcador.match(anterior)):
            saida.append("")
        saida.append(" " * recuo + linha if recuo and not em_codigo else linha)
        anterior = linha
    return "\n".join(saida)


def exportar_documentos(destino: Path, versao: str) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    for origem, nome, titulo in DOCUMENTOS:
        texto = recuo_de_4((BASE_DIR / origem).read_text(encoding="utf-8"))
        corpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
        (destino / nome).write_text(pagina(titulo, corpo, versao), encoding="utf-8")


def exportar_codigo(destino: Path) -> None:
    ignorar = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(BASE_DIR / "src", destino / "src", ignore=ignorar)
    for f in ("README.md", "requirements.txt", "run_pipeline.py"):
        shutil.copy2(BASE_DIR / f, destino / f)


def leia_me(versao: str) -> str:
    corpo = f"""
<h1>Gasto público em educação e desempenho no Saeb</h1>
<p>Pacote do TCC de Administração (FEA/USP), autores Henrique Lindoso e Guilherme.
Tudo abre sem instalar nada: os arquivos <b>.html</b> abrem no navegador, e os <b>.xlsx</b>, no Excel.</p>
<h2>O que tem em cada pasta</h2>
<table>
<tr><th>Pasta</th><th>Conteúdo</th><th>Como abrir</th></tr>
<tr><td><b>1_Dashboard</b></td><td>Painel interativo de conferência: gasto por aluno × desempenho no Saeb, evolução 2017–2025, ranking por UF, cobertura dos dados e tabela por município. É descritivo: ainda não há modelo estimado.</td><td>Duplo clique; abre no navegador, também sem internet.</td></tr>
<tr><td><b>2_Documentos</b></td><td>(1) Resumo para a orientadora, com os pontos que dependem de decisão; (2) registro completo das decisões de método, com os problemas de cada base e como foram tratados; (3) visão geral técnica do projeto.</td><td>Navegador. Para PDF: Ctrl+P → Salvar como PDF.</td></tr>
<tr><td><b>3_Dados</b></td><td>Os dois painéis finais (municípios e estados), cada um em Excel, com uma aba "Dicionário" explicando as colunas, e em CSV.</td><td>Excel, R, Stata, Power BI.</td></tr>
<tr><td><b>4_Codigo</b></td><td>Código Python completo do pipeline (extração, tratamento, painéis e dashboard).</td><td>Só para reproduzir; veja o README.md da pasta.</td></tr>
</table>
<h2>Observações</h2>
<ul>
<li>Valores de gasto em reais de 2025 (IPCA). Resultados são de associação, não de causalidade.</li>
<li>Itens marcados com 🟡 nos documentos são decisões provisórias, que dependem da validação da orientadora.</li>
<li>Os dados brutos (~35 GB, sobretudo os microdados do Censo Escolar) não vão no pacote. As fontes e a forma de obtê-los estão na visão geral do projeto.</li>
<li>Parte do código e da documentação foi desenvolvida com apoio de assistente de IA (Claude, da Anthropic). As decisões de método são dos autores.</li>
</ul>
"""
    return pagina("Leia-me", corpo, versao)


def commit_atual() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconhecido"


if __name__ == "__main__":
    versao = commit_atual()
    if PACOTE.exists():
        shutil.rmtree(PACOTE)
    PACOTE.mkdir(parents=True)

    (PACOTE / "LEIA-ME.html").write_text(leia_me(versao), encoding="utf-8")
    (PACOTE / "1_Dashboard").mkdir()
    shutil.copy2(BASE_DIR / "relatorios/dashboard_conferencia.html", PACOTE / "1_Dashboard/dashboard_conferencia.html")
    exportar_documentos(PACOTE / "2_Documentos", versao)
    exportar_dados(PACOTE / "3_Dados")
    exportar_codigo(PACOTE / "4_Codigo")

    zip_path = SAIDA_DIR / f"{NOME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PACOTE.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(SAIDA_DIR))

    arquivos = [f for f in PACOTE.rglob("*") if f.is_file()]
    print(f"[OK] {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB, {len(arquivos)} arquivos, código {versao})")
    for pasta in sorted(p for p in PACOTE.iterdir()):
        tamanho = sum(f.stat().st_size for f in ([pasta] if pasta.is_file() else pasta.rglob("*")) if f.is_file())
        print(f"  {pasta.name:<22} {tamanho / 1e6:6.1f} MB")
