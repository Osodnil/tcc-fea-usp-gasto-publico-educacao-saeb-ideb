"""Monta uma CÓPIA do rascunho do TCC II com o conteúdo técnico produzido no projeto.

Uso (na raiz do repositório):  python Montar_Copia_Rascunho.py <pasta_descompactada> <saida.docx> <pasta_das_telas> [--final]

Com --final, gera a versão de entrega: sem as notas amarelas, com a lista das marcações que ainda restam. Depois, rodar
src/Exportacao/Atualizar_Campos.ps1 na saída, para o Word preencher o sumário e as listas com as páginas.

Não toca no original. Insere, depois das lacunas do rascunho: notas de rascunho (caixa amarela, como as do documento),
texto técnico dos capítulos 4 e 5, quadros, tabelas e figuras, e notas de ATENÇÃO onde o rascunho diverge do que foi
feito. Não escreve revisão de literatura, discussão nem conclusões.
"""
import shutil
import unicodedata
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import polars as pl

sys.path.insert(0, "src/Analise")
import Material_Texto as MT  # noqa: E402  (formatação brasileira e leitura das saídas)
import Modelo_Principal as M  # noqa: E402

PASTA, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
FINAL = "--final" in sys.argv[4:]
DOC = PASTA / "word" / "document.xml"
FONTE = ('<w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" w:eastAsia="Times New Roman" '
         'w:hAnsi="Times New Roman"/>')
BORDA = "".join(f'<w:{l} w:color="ffc000" w:space="2" w:sz="8" w:val="single"/>' for l in ("top", "left", "bottom", "right"))


def run(texto: str, tam: int = 24, negrito: bool = False, italico: bool = False) -> str:
    extra = ("<w:b/><w:bCs/>" if negrito else "") + ("<w:i/><w:iCs/>" if italico else "")
    return (f'<w:r><w:rPr>{FONTE}{extra}<w:color w:val="000000"/><w:sz w:val="{tam}"/><w:szCs w:val="{tam}"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(texto)}</w:t></w:r>')


def corpo(texto: str) -> str:
    return ('<w:p><w:pPr><w:spacing w:after="120" w:before="0" w:line="360" w:lineRule="auto"/>'
            '<w:ind w:left="0" w:right="0" w:firstLine="707"/><w:jc w:val="both"/></w:pPr>' + run(texto) + "</w:p>")


def item(texto: str) -> str:
    return ('<w:p><w:pPr><w:spacing w:after="60" w:before="0" w:line="360" w:lineRule="auto"/>'
            '<w:ind w:left="707" w:right="0" w:hanging="283"/><w:jc w:val="both"/></w:pPr>' + run("– " + texto) + "</w:p>")


def nota(texto: str) -> str:
    """Caixa amarela, igual às lacunas do rascunho."""
    return (f'<w:p><w:pPr><w:pBdr>{BORDA}</w:pBdr><w:spacing w:after="120" w:before="120" w:line="276" w:lineRule="auto"/>'
            '<w:ind w:left="113" w:right="113" w:firstLine="0"/><w:jc w:val="both"/></w:pPr>' + run(texto) + "</w:p>")


def titulo(nivel: int, texto: str) -> str:
    """Título de seção com a mesma numeração automática dos títulos do rascunho (lista 3: nível 1 = 5.2, nível 2 = 5.2.1)."""
    rec = {2: (1, 362, 360, 140, 280), 3: (2, 542, 540, 120, 240)}[nivel]
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{nivel}"/><w:keepNext w:val="1"/><w:numPr><w:ilvl w:val="{rec[0]}"/>'
            f'<w:numId w:val="3"/></w:numPr><w:tabs><w:tab w:val="left" w:leader="none" w:pos="{rec[1]}"/></w:tabs>'
            f'<w:spacing w:after="{rec[3]}" w:before="{rec[4]}" w:lineRule="auto"/><w:ind w:left="{rec[1]}" '
            f'w:hanging="{rec[2]}"/></w:pPr>' + run(texto, negrito=True) + "</w:p>")


def legenda(texto: str) -> str:
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:after="120" w:before="240" w:line="240" w:lineRule="auto"/>'
            '<w:jc w:val="left"/></w:pPr>' + run(texto, negrito=True) + "</w:p>")


def fonte(texto: str) -> str:
    """Fonte da ilustração ou tabela; a "Nota:", se houver, vai em linha própria (ABNT). Com endereço, alinha à esquerda,
    para a linha não esticar."""
    jc = "left" if "http" in texto else "both"
    antes, sep, nota = texto.partition(" Nota: ")
    # o espaço antes da quebra preserva " Nota: " quando o texto é relido (ilustracoes() relê o parágrafo pronto)
    corpo_xml = run(antes + (" " if sep else ""), tam=20) + ('<w:r><w:br/></w:r>' + run("Nota: " + nota, tam=20) if sep else "")
    return (f'<w:p><w:pPr><w:spacing w:after="240" w:before="60" w:line="240" w:lineRule="auto"/><w:jc w:val="{jc}"/></w:pPr>'
            + corpo_xml + "</w:p>")


def tabela(cab: list[str], linhas: list[list[str]], larguras: list[int]) -> str:
    assert sum(larguras) == 9075 and len(larguras) == len(cab), (sum(larguras), len(cab))
    bordas = "".join(f'<w:{l} w:color="000000" w:space="0" w:sz="4" w:val="single"/>'
                     for l in ("top", "left", "bottom", "right", "insideH", "insideV"))
    x = (f'<w:tbl><w:tblPr><w:tblW w:w="9075" w:type="dxa"/><w:jc w:val="left"/><w:tblBorders>{bordas}</w:tblBorders>'
         '<w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in larguras)
         + "</w:tblGrid>")

    def celula(txt: str, w: int, cabecalho: bool) -> str:
        pars = "".join('<w:p><w:pPr><w:spacing w:after="20" w:before="20" w:line="240" w:lineRule="auto"/>'
                       '<w:jc w:val="left"/></w:pPr>' + run(t, tam=18, negrito=cabecalho) + "</w:p>"
                       for t in str(txt).split("\n"))
        sombra = '<w:shd w:fill="d9d9d9" w:val="clear"/>' if cabecalho else ""
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{sombra}</w:tcPr>{pars}</w:tc>'

    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(celula(c, w, True) for c, w in zip(cab, larguras)) + "</w:tr>"
    for l in linhas:
        assert len(l) == len(cab), l
        x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(celula(c, w, False) for c, w in zip(l, larguras)) + "</w:tr>"
    return x + "</w:tbl>"


def figura(rid: str, n: int, larg_cm: float, alt_cm: float, nome: str) -> str:
    cx, cy = int(larg_cm * 360000), int(alt_cm * 360000)
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:after="60" w:before="120"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{9000 + n}" name="{nome}"/>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{9000 + n}" name="{nome}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            "</wp:inline></w:drawing></w:r></w:p>")


# ───────────────────────── dados das tabelas ─────────────────────────
D = MT.DIAG
coefs = pl.read_csv(D / "modelo_principal_coeficientes.csv")
comp = pl.read_csv(D / "modelo_principal_defasagens_mesma_amostra.csv")
het = pl.read_csv(D / "heterogeneidade_coeficientes.csv", schema_overrides={"GRUPO": pl.Utf8})
sens = pl.read_csv(D / "sensibilidade_modelo.csv")
est = pl.read_csv(D / "modelo_estadual_coeficientes.csv")
painel = M.base()
clu = pl.read_parquet(M.PROCESSED_DIR / "powerbi" / "dim_cluster.parquet").sort("CLUSTER")
br, ce = MT.br, MT.coef_ep
ETAPAS = [("AI", "MT"), ("AI", "LP"), ("AF", "MT"), ("AF", "LP")]
CAB4 = ["AI Matemática", "AI Português", "AF Matemática", "AF Português"]
NOTA_COEF = ("Coeficiente do log do gasto por aluno, com erro-padrão agrupado entre parênteses. *** p < 0,01; ** p < 0,05; "
             "* p < 0,10. Associação, não efeito causal.")
# ABNT/IBGE: toda tabela tem "Fonte:" logo abaixo; notas explicativas vêm depois, como "Nota:"
FONTE_MUN = "Fonte: elaborado pelos autores, com dados do SIOPE, do Censo Escolar, do Saeb, do IBGE e do Radar IDHM. Nota: "
FONTE_EST = "Fonte: elaborado pelos autores, com dados do SICONFI, do Censo Escolar e do Saeb. Nota: "


def linha(df: pl.DataFrame, **f) -> dict:
    for k, v in f.items():
        df = df.filter(pl.col(k) == v)
    assert df.height == 1, (f, df.height)
    return df.row(0, named=True)


gasto0 = coefs.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO") & (pl.col("DEFASAGEM") == 0))

t_amostra = []
for etapa in ["AI", "AF"]:
    for ano in [2017, 2019, 2021, 2023, 2025]:
        d = painel.filter((pl.col("ETAPA") == etapa) & (pl.col("ANO") == ano) & pl.col("NOTA_MT").is_not_null())
        t_amostra.append([MT.ETAPAS[etapa], str(ano), br(d.height, 0), "R$ " + br(d["GASTO_ALUNO_R2025_L0"].median(), 0),
                          br(d["NOTA_MT"].mean(), 1), br(d["NOTA_LP"].mean(), 1)])

t_rho = []
for ano in [2017, 2019, 2021, 2023, 2025]:
    cel = [str(ano)]
    for k in M.DEFASAGENS:
        d = painel.filter((pl.col("ETAPA") == "AI") & (pl.col("ANO") == ano)).drop_nulls(["NOTA_MT", f"GASTO_ALUNO_R2025_L{k}"])
        cel.append(br(d.select(pl.corr(f"GASTO_ALUNO_R2025_L{k}", "NOTA_MT", method="spearman")).item()) if d.height >= 30 else "—")
    t_rho.append(cel)

t_modelo = []
for e, rot in [("MQO agrupado", "MQO agrupado, 2017–2023"), ("EF de município", "EF de município e de edição, 2017–2023"),
               ("EF de município e UF × edição", "EF de município e de UF × edição, 2017–2025 (referência)")]:
    cel = [rot]
    for et, di in ETAPAS:
        r = linha(gasto0, ESPECIFICACAO=e, ETAPA=et, DISCIPLINA=di)
        cel.append(f"{ce(r['COEF'], r['EP'], r['P'])}\nN = {br(r['N'], 0)}")
    t_modelo.append(cel)

t_defas = []
for et, di in ETAPAS:
    cel = [f"{MT.ETAPAS[et]}, {MT.DISCS[di]}"]
    for k in [0, 1, 2]:
        r = linha(comp, JANELA="2019-2025, UF × edição", ETAPA=et, DISCIPLINA=di, DEFASAGEM=k)
        cel.append(ce(r["COEF"], r["EP"], r["P"]))
    t_defas.append(cel)

NOMES_CLUSTER = {str(r["CLUSTER"]): f"{r['CLUSTER']} · {r['CLUSTER_ROTULO'].rsplit(' · ', 1)[0]}" for r in clu.iter_rows(named=True)}
t_het = []
for dim, grupos in MT.ORDEM_GRUPOS.items():
    for g in grupos:
        rm = linha(het, ETAPA="AI", DIMENSAO=dim, GRUPO=g, DISCIPLINA="MT")
        rl = linha(het, ETAPA="AI", DIMENSAO=dim, GRUPO=g, DISCIPLINA="LP")
        rot = NOMES_CLUSTER[g] if dim == "Cluster" else g
        t_het.append([dim, rot, ce(rm["COEF"], rm["EP"], rm["P"]), ce(rl["COEF"], rl["EP"], rl["P"]), br(rm["MUN_GRUPO"], 0)])

sm = sens.filter(pl.col("CAMADA") == "Municipal")
t_sens = []
for t in sm.filter((pl.col("ETAPA") == "AI") & (pl.col("DISCIPLINA") == "MT"))["TESTE"].to_list():
    cel = [t]
    for et, di in ETAPAS:
        r = linha(sm, TESTE=t, ETAPA=et, DISCIPLINA=di)
        cel.append(ce(r["COEF"], r["EP"], r["P"]))
    t_sens.append(cel)

ge = est.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO") & (pl.col("DEFASAGEM") == 0))
t_est = []
for e, rot in [("MQO agrupado", "MQO agrupado, 2017–2023"), ("EF de UF", "EF de UF, 2017–2023 (referência)"),
               ("EF de UF, com 2025", "EF de UF, 2017–2025, sem IDHM")]:
    cel = [rot]
    for et in ["AF", "EM"]:
        for di in ["MT", "LP"]:
            r = linha(ge, ESPECIFICACAO=e, ETAPA=et, DISCIPLINA=di)
            cel.append(f"{ce(r['COEF'], r['EP'], r['P'])}\nIC 95%: {br(r['IC95_INF'], 1)} a {br(r['IC95_SUP'], 1)}")
    t_est.append(cel)
for t, rot in [("Versão B do gasto", "Versão B do gasto (EF de UF, 2017–2023)"),
               ("Soma das subfunções da educação básica", "Soma das subfunções da educação básica (EF de UF, 2017–2023)")]:
    cel = [rot]
    for et in ["AF", "EM"]:
        for di in ["MT", "LP"]:
            r = linha(sens, CAMADA="Estadual", TESTE=t, ETAPA=et, DISCIPLINA=di)
            cel.append(f"{ce(r['COEF'], r['EP'], r['P'])}\nIC 95%: {br(r['IC95_INF'], 1)} a {br(r['IC95_SUP'], 1)}")
    t_est.append(cel)

t_clu = [[f"{r['CLUSTER']} · {r['CLUSTER_ROTULO']}", br(r["MUNICIPIOS"], 0), br(r["POP_MEDIANA"], 0),
          br(100 * r["ALFAB_MEDIA"], 1) + "%", br(r["IDHM_RENDA_MEDIO"], 3), br(r["INFRA_MEDIA"], 2),
          f"{r['REGIAO_PREDOMINANTE']} ({br(100 * r['PARCELA_REGIAO_PREDOMINANTE'], 0)}%)"] for r in clu.iter_rows(named=True)]

# ───────────────────────── conteúdo ─────────────────────────
AVISO = ("[RASCUNHO TÉCNICO – vale para todo este capítulo. Texto montado em 2026-11-12, com apoio de IA, a partir dos "
         "registros do projeto. Serve de base factual: os autores devem reescrever com as próprias palavras, conferir os "
         "números e acrescentar as citações. Uso de IA permitido pela orientadora, desde que os autores conheçam todas as "
         "etapas e informações do projeto (Manual, item 2.3).]")
TELAS = [  # (arquivo, legenda) das capturas do painel, na ordem das páginas
    ("01_boas_vindas", "Página Boas-vindas: para que serve o painel, como usar e as perguntas de entrada"),
    ("02_visao_geral", "Página Visão geral: gasto, proficiência, cobertura do Saeb e redes que melhoraram"),
    ("03_eficiencia", "Página Desempenho: gasto por aluno e resultado em relação ao esperado, com o ranking das redes"),
    ("04_ficha", "Página Ficha do município: série da rede contra o cluster, a UF e o Brasil"),
    ("05_pares", "Página Pares: redes de contexto e gasto parecidos e comparação de duas redes"),
    ("06_mapa", "Página Mapa: resultado em relação ao esperado por município (exemplo: Bahia)"),
    ("07_defasagens", "Página Defasagens: correlação entre gasto e proficiência por edição e defasagem"),
    ("08_contexto", "Página Contexto e clusters: perfil dos grupos e composição por região"),
    ("09_estados", "Página Estados: redes estaduais das 27 UFs"),
    ("10_sobre", "Página Sobre os dados: fontes, indicadores, limitações e correção pela inflação"),
]
# numeração (texto enxugado em 2026-11-17, A22): no texto ficam o fluxo, três telas, a heterogeneidade, Ceará e Bahia
# e a tela de Pares de um caso; as outras telas, os clusters, duas tabelas e as fichas dos casos vão para o Apêndice B
TELAS_TEXTO = ["03_eficiencia", "04_ficha", "05_pares"]
LEG_TELA = dict(TELAS)
IDX_TELA = {a: k for k, (a, _) in enumerate(TELAS)}
F_FLUXO, F_TELA0 = 1, 2
F_QR = F_TELA0 + len(TELAS_TEXTO)   # QR Code de acesso (etapa 5, 2026-11-18)
F_HET = F_QR + 1
REPO = "https://github.com/Osodnil/tcc-fea-usp-gasto-publico-educacao-saeb-ideb"

CAP4_ABERTURA = [
    nota(AVISO),
    corpo("Este capítulo descreve o método do trabalho, um estudo quantitativo com dados públicos. A seção 3.1 apresenta as "
          "fontes e a arquitetura dos dados, da extração nas bases públicas aos painéis de dados; a seção 3.2, as regras de "
          "tratamento; a seção 3.3, o painel em Power BI e o indicador que ele usa; e a seção 3.4, o uso de inteligência "
          "artificial no trabalho. O instrumento construído tem duas "
          "partes: os painéis de dados, montados em Python a partir de oito bases públicas, e o painel interativo, "
          "organizado em torno de três perguntas de quem gere uma rede de ensino. O código, os dados tratados e o registro "
          f"datado de cada decisão de método estão em repositório público ({REPO}), o que permite refazer cada número a "
          "partir das fontes."),
]

CAP4_1 = [
    corpo("O trabalho parte de bases públicas de oito origens, reunidas no Quadro 2. Com o auxílio de inteligência "
          "artificial generativa (seção 3.4), foram desenvolvidos em Python, com a biblioteca Polars, os scripts de extração, "
          "tratamento e integração dessas bases, versionados no repositório do projeto; as regras de tratamento foram "
          "definidas pelos autores, e as saídas de cada etapa foram conferidas. Um "
          "comando único executa todas as etapas na ordem certa, do dado bruto às tabelas lidas pelo painel, o que permite "
          "refazer todo o processo a partir das fontes. A Figura 1 resume esse fluxo."),
    figura("rIdFluxo", 50, 16.0, 7.64, "Figura fluxo"),
    fonte(f"Figura {F_FLUXO} – Fluxo de dados do projeto, das fontes públicas ao painel. Fonte: elaborado pelos autores."),
    legenda("Quadro 2 – Fontes de dados, origem e uso no trabalho"),
    tabela(["Base", "Origem", "Período", "Uso"], [
        ["SIOPE", "FNDE, API de dados abertos", "2017–2025", "Gasto municipal: despesa paga na subfunção 361 (Ensino Fundamental)"],
        ["SICONFI", "Tesouro Nacional, DCA Anexo I-E", "2014–2025", "Gasto estadual: função 12 (Educação) menos a subfunção 364 (Ensino Superior)"],
        ["Saeb e IDEB", "Inep, planilhas de divulgação do IDEB 2025", "Edições de 2017 a 2025", "Proficiência em Matemática e Português por rede, etapa e edição"],
        ["Censo Escolar", "Inep, microdados", "2015–2025", "Matrículas por rede e etapa; infraestrutura das escolas"],
        ["Censo Demográfico 2022", "IBGE", "2022", "População e taxa de alfabetização de 15 anos ou mais"],
        ["IDHM por UF", "Atlas Brasil / Radar IDHM (PNUD, FJP, IBGE)", "2015–2024", "IDHM Renda e IDHM Longevidade da UF, como controles de contexto"],
        ["IPCA", "IBGE/SIDRA, tabela 1737", "2017–2025", "Correção dos valores para reais de 2025"],
        ["Malha Municipal 2025", "IBGE", "2025", "Contornos dos municípios para o mapa"],
    ], [1300, 2300, 1500, 3975]),
    fonte("Fonte: elaborado pelos autores, com base em FNDE (2026), Secretaria do Tesouro Nacional (2026), Inep (2026a, "
          "2026b), IBGE (2023, 2024, 2026a, 2026b) e PNUD et al. (2026)."),
    corpo("A análise tem duas camadas, que não se misturam, porque o gasto e o desempenho precisam ser da mesma rede. Na "
          "camada municipal, a unidade é a rede municipal de cada município: o gasto é a despesa paga no Ensino Fundamental "
          "dividida pelas matrículas do Ensino Fundamental da rede municipal, e o desempenho é a proficiência no Saeb dos "
          "Anos Iniciais (principal) e dos Anos Finais. Na camada estadual, a unidade é a rede estadual de cada uma das 27 "
          "unidades da Federação: o gasto é a despesa em educação menos o Ensino Superior, dividida pelas matrículas da "
          "educação básica da rede estadual, e o desempenho é a proficiência nos Anos Finais e no Ensino Médio."),
    corpo("As bases são ligadas pelo código de sete dígitos do município (IBGE), pela sigla da UF, pela rede e pelo ano. "
          "Todos os valores monetários foram corrigidos para reais de 2025 pelo IPCA médio anual; a correção foi conferida "
          "de ponta a ponta, do valor nominal ao gasto por aluno usado no painel."),
    corpo("O resultado da integração são dois painéis de dados. O painel municipal tem uma linha por município, etapa e "
          f"edição do Saeb ({br(painel.height, 0)} linhas), com as notas, as matrículas, o gasto por aluno do mesmo ano e de "
          "1, 2 e 4 anos antes, e os controles de contexto. O painel estadual tem uma linha por UF, etapa e edição (270 "
          "linhas). Para o painel de Business Intelligence, esses dados foram organizados num modelo em estrela, com 13 "
          "tabelas (dimensões de município, UF, cluster, ano, etapa e disciplina, e tabelas de fatos de desempenho, de "
          "gasto e de oferta por rede) e 85 medidas."),
]

CAP4_2 = [
    corpo("As regras de tratamento foram registradas à medida que as decisões eram tomadas, com a evidência que as motivou. "
          "As principais são as seguintes."),
    item("Dado ausente não é zero. Traços e marcas de dado não disponível nas planilhas viram valor ausente, e a rede fica "
         "fora do cálculo correspondente."),
    item("Só entram as redes com nota divulgada pelo Inep. As redes pequenas, que não têm resultado divulgado, ficam "
         "sub-representadas, sobretudo nos Anos Finais e na edição de 2021."),
    item("A medida de desempenho é a proficiência em pontos da escala do Saeb, com Matemática e Português separadas. A nota "
         "padronizada do Inep e o IDEB ficam como medidas secundárias."),
    item("O controle socioeconômico é o IDHM da UF no mesmo ano da edição do Saeb, só nas dimensões Renda e Longevidade. A "
         "dimensão Educação e o índice total ficam de fora, para não controlar o resultado pelo próprio resultado. Como a "
         "série do IDHM termina em 2024, a edição de 2025 não tem esse controle."),
    item("Os valores extremos de gasto por aluno não são removidos, por decisão da orientadora. Ficam apenas marcados os "
         "valores fora do intervalo entre os percentis 0,5 e 99,5 de cada ano: 174 das 25.658 observações com nota nos Anos "
         "Iniciais (0,7%)."),
    item("No gasto estadual, quando a linha do Ensino Superior não existe para a UF e o ano, nada é descontado (versão A). A "
         "versão que deixa esses casos de fora (versão B) é usada como teste de sensibilidade."),
    item("Saltos atípicos de proficiência são marcados, e não excluídos: é atípica a variação em relação à última "
         "edição com nota que se afasta mais de três desvios-padrão da média das variações da mesma etapa e disciplina. As "
         "variações de dois anos (edições seguidas) e de quatro anos (quando falta a nota da edição do meio) têm cada uma a "
         "própria média e o próprio desvio, porque em quatro anos a nota varia naturalmente mais. São 647 resultados "
         "marcados, cerca de 0,8% do total."),
    item("Redes municipais parciais são marcadas: aquelas em que a prefeitura atende menos de 50% dos alunos públicos da "
         "etapa, e o restante está na rede estadual. Em 2023, eram 2,7% das redes com nota nos Anos Iniciais e 16% nos Anos "
         "Finais."),
    corpo("A lista completa das limitações que decorrem dessas regras está no Capítulo 5."),
]

CAP4_3 = [
    # remanejado do antigo Capítulo 3 (Diagnóstico), item 3.3 e perfis de 3.2 (decisão D1, A23)
    corpo("O painel usa uma ferramenta de Business Intelligence porque ela transforma bases volumosas e heterogêneas em "
          "indicadores com filtros e comparações, sem exigir do usuário o domínio técnico dos microdados (Davenport & "
          "Harris, 2007; Few, 2006). O público-alvo são analistas e técnicos de secretarias de educação, que cruzam dados e "
          "apoiam pareceres e o planejamento orçamentário, e gestores que precisam comparar a própria rede com redes "
          "parecidas. Esses perfis são premissas de projeto definidas pelos autores, e não resultado de levantamento com "
          "usuários."),
    corpo("Com o auxílio da IA, foram desenvolvidos os scripts que geram o modelo de dados, as medidas e as páginas do "
          "painel; o conteúdo, o público e o desenho de cada página foram definidos pelos autores. "
          "O protótipo foi construído no Power BI, como projeto versionável (formato .pbip), e tem dez páginas, descritas no "
          "Quadro 3. Os filtros ficam numa faixa no topo, e cada página mostra só os filtros que alteram o seu conteúdo. A "
          "escolha de UF, etapa, disciplina e edição vale para todas as páginas."),
    legenda("Quadro 3 – Páginas do painel e pergunta que cada uma responde"),
    tabela(["Página", "O que mostra", "Pergunta do gestor"], [
        ["Boas-vindas", "Para que serve, como usar e três perguntas que levam às páginas", "Por onde começo?"],
        ["Visão geral", "Gasto, proficiência, cobertura do Saeb e redes que melhoraram desde a edição anterior", "Como está o conjunto das redes?"],
        ["Desempenho", "Dispersão do gasto contra o resultado em relação ao esperado; ranking das redes", "Quem entrega acima do esperado?"],
        ["Ficha do município", "Série de proficiência contra o cluster, a UF e o Brasil; gasto por ano; situação da rede", "Como está a minha rede?"],
        ["Pares", "Redes de contexto e gasto parecidos; comparação de duas redes, uma a uma", "Com quem conversar?"],
        ["Mapa", "Resultado em relação ao esperado por município, numa UF", "Onde estão as redes acima e abaixo do esperado?"],
        ["Defasagens", "Correlação entre gasto e proficiência, por edição e defasagem do gasto", "Gastar mais se associa a notas maiores?"],
        ["Contexto e clusters", "Perfil dos sete grupos de municípios; gasto e proficiência por porte", "Quais redes são comparáveis?"],
        ["Estados", "Redes estaduais das 27 UFs, Anos Finais e Ensino Médio", "Como estão as redes estaduais?"],
        ["Sobre os dados", "Fontes, indicadores, limitações e correção pela inflação", "De onde vêm os números?"],
    ], [1700, 4375, 3000]),
    fonte("Fonte: elaborado pelos autores."),
    corpo("O indicador central do painel é o desempenho em relação ao esperado (no painel, \"vs. esperado\"): a diferença "
          "entre a proficiência média da rede no Saeb e a proficiência esperada para redes com o mesmo gasto por aluno e o "
          "mesmo contexto, em percentual da esperada. A esperada vem de uma regressão da proficiência contra o gasto por "
          "aluno (em logaritmo) e variáveis de contexto: população, alfabetização, infraestrutura das escolas, tamanho da "
          "rede e IDHM Renda e Longevidade da UF. Assim, +5% significa que a nota ficou 5% acima da esperada, e 0% significa "
          "que a rede entregou exatamente o esperado. Há duas comparações: a nacional, que usa o IDHM e cobre as edições de "
          "2017 a 2023, e a do mesmo estado, que troca o IDHM por um efeito de cada UF e cobre também 2025."),
    corpo("O indicador não se chama eficiência por dois motivos. Primeiro, no modelo nacional, o gasto quase não altera a "
          "nota esperada (0,92 ponto por log do gasto, sem significância estatística): o indicador mostra a distância até "
          "redes de gasto e contexto parecidos, e não o resultado obtido por real gasto. Segundo, nos métodos de fronteira, "
          "como a análise envoltória de dados, eficiência tem sentido próprio, em que 100% é o melhor resultado possível, o "
          "que não se aplica aqui. Como é um resíduo de regressão, o indicador também capta fatores não medidos, como "
          "gestão, contexto familiar e qualidade do registro."),
    corpo("Os alertas do painel aparecem numa coluna única, chamada Atenção, que marca os saltos atípicos e as redes "
          "municipais parciais. Os números do painel foram conferidos com os cálculos feitos em Python, e as páginas são "
          "validadas contra os esquemas oficiais do formato do Power BI. As Figuras "
          f"{F_TELA0} a {F_TELA0 + len(TELAS_TEXTO) - 1} mostram as três páginas que respondem às perguntas centrais "
          "(Desempenho, Ficha do município e Pares), com os filtros em Anos Iniciais, Matemática e edição de 2023; as "
          "outras sete páginas estão no Apêndice B (Figuras B.1 a B.7)."),
    *[b for k, arq in enumerate(TELAS_TEXTO) for b in (
        figura(f"rIdTela{IDX_TELA[arq]}", 60 + IDX_TELA[arq], 16.0, 9.0, f"Tela {IDX_TELA[arq] + 1}"),
        fonte(f"Figura {F_TELA0 + k} – {LEG_TELA[arq]}. Fonte: painel elaborado pelos autores."))],
    corpo(f"O painel pode ser acessado pelo QR Code da Figura {F_QR}, que leva à página do projeto no repositório "
          f"público ({REPO}). A página traz o link do painel publicado na web, que abre sem login, além do código, dos "
          "dados tratados e do registro das decisões de método."),
    figura("rIdQR", 49, 4.0, 4.0, "QR Code de acesso"),
    fonte(f"Figura {F_QR} – QR Code de acesso ao painel e ao repositório do projeto. Fonte: elaborado pelos autores. "
          f"Nota: para acessar pelo computador, use o endereço {REPO}, que traz o link do painel publicado."),
    nota("[Decisões de 2026-11-17 (registro D1, D2 e A21): o indicador passou a se chamar desempenho em relação ao esperado, "
         "e o item 2.1.4 foi reescrito com essa definição. Simulação de cenários e monitoramento do "
         "VAAR passaram a trabalhos futuros (5.4). O QR Code (etapa 5) aponta para o README do repositório, que traz o "
         "link do painel publicado.]"),
    titulo(2, "Uso de inteligência artificial"),
    corpo("O trabalho usou inteligência artificial (IA) generativa com autorização da orientadora, como prevê o Manual de "
          "TCC (Departamento de Administração FEA/USP, 2025). A ferramenta foi o Claude, modelo de linguagem da Anthropic "
          "(Anthropic, 2026), usado em conversas e, a partir de outubro de 2026, pelo Claude Code, que lê e escreve arquivos "
          "no repositório do projeto e executa os scripts. Ao longo do texto, cada etapa feita com o auxílio da IA é indicada "
          "no próprio parágrafo. As etapas foram as seguintes."),
    item("Coleta e tratamento dos dados: com o auxílio da IA, foram desenvolvidos os scripts em Python que extraem, tratam e "
         "integram as bases públicas. As regras de tratamento, como o que entra na análise e como tratar valores ausentes e "
         "extremos, foram definidas pelos autores, que executaram os scripts e conferiram as saídas."),
    item("Análises: com o auxílio da IA, foram escritos os scripts dos modelos de regressão, do agrupamento por contexto e "
         "dos testes de sensibilidade. A especificação de cada modelo foi decidida pelos autores, e os resultados foram conferidos "
         "nas saídas dos scripts e no painel."),
    item("Painel: com o auxílio da IA, foram desenvolvidos os scripts que geram o modelo de dados, as medidas e as páginas "
         "do painel em Power BI. O conteúdo, o público e o desenho de cada página foram definidos pelos autores."),
    item("Levantamento bibliográfico: com o auxílio da IA, foi feito um levantamento inicial de referências, com a "
         "conferência dos dados bibliográficos de cada uma. A leitura das obras, a escolha do que citar e a redação da revisão "
         "couberam aos autores."),
    item("Redação: com o auxílio da IA, foram redigidas versões iniciais das seções técnicas, e o texto foi reorganizado no "
         "formato de método científico. Os autores revisaram e reescreveram essas versões."),
    corpo("A IA não tomou decisões de pesquisa: a pergunta, o recorte e cada escolha de método foram decididos pelos autores ou "
          "pela orientadora e estão registrados, com data, no repositório do projeto. A IA também não produziu dados: todos "
          "os números vêm de bases públicas e podem ser refeitos a partir dos scripts. Os erros encontrados na conferência, "
          "inclusive os cometidos pela IA, estão documentados no mesmo registro."),
]

CAP5_CLUSTER = [
    nota(AVISO + " A interpretação e a discussão com a literatura ficam com os autores; aqui estão o método e os números."),
    corpo("Para comparar redes em condições parecidas, os municípios foram agrupados pelo contexto em que a rede municipal "
          "atua, e não pelo gasto nem pela nota. Se o agrupamento usasse essas variáveis, a comparação dentro do grupo "
          "deixaria de mostrar quem gasta mais, ou entrega mais, do que redes parecidas. Foram usadas cinco variáveis: o "
          "logaritmo da população e a taxa de alfabetização das pessoas de 15 anos ou mais, ambas do Censo Demográfico "
          "2022; o IDHM Renda e o IDHM Longevidade da UF, na média de 2017 a 2023; e um índice de infraestrutura das escolas "
          "da rede municipal, a média, de 2017 a 2025, das proporções de escolas com oito itens. A população entra em "
          "logaritmo porque sua distribuição é muito assimétrica: sem isso, as poucas cidades muito grandes dominariam o "
          "agrupamento. A dimensão Educação do IDHM ficou de fora, porque mede escolaridade, que é parte do próprio "
          "resultado que se quer comparar. As cinco variáveis foram padronizadas (média zero e desvio-padrão um), para que "
          "nenhuma pese mais por causa da unidade de medida."),
    corpo("O script do agrupamento foi desenvolvido com o auxílio da IA; a escolha das variáveis e do número de grupos coube "
          "aos autores. O agrupamento usou o método das k-médias (MacQueen, 1967), que divide os municípios em k grupos de modo a "
          "minimizar a distância de cada município ao centro do seu grupo. O algoritmo foi rodado com 50 pontos de partida "
          "diferentes e semente fixa, o que torna o resultado reprodutível. Entraram 5.568 municípios; ficaram de fora "
          "Fernando de Noronha, Boa Esperança do Norte e Brasília, por falta de alguma variável. Um único agrupamento vale "
          "para todo o período e para as duas etapas."),
    corpo(f"O número de grupos foi escolhido comparando os valores de k de 3 a 10 por dois critérios (Figura B.8, no Apêndice B). O "
          "primeiro é o coeficiente de silhueta (Rousseeuw, 1987), que vai de −1 a 1 e mede o quanto cada município está "
          "mais próximo do próprio grupo do que do grupo vizinho. O segundo é a inércia, a soma das distâncias de cada "
          "município ao centro do seu grupo. A silhueta é maior com três grupos (0,32) e fica perto de 0,23 de cinco a dez "
          "grupos; a inércia cai de forma contínua, sem um ponto de inflexão claro. Com três grupos, o menor teria 1.053 "
          "municípios, o que é largo demais para formar pares de comparação. Entre os valores de silhueta parecida, foi "
          "escolhido k = 7: a silhueta é praticamente igual à de seis grupos (0,233 contra 0,229), e o sétimo grupo separa "
          "os municípios grandes do Norte e do Nordeste (população mediana de 101,7 mil), que de outro modo ficariam com "
          "municípios muito menores."),
    corpo(f"O Quadro 4 mostra o perfil de cada grupo; a Figura B.9, no Apêndice B, mostra o mesmo perfil em desvios-padrão e a composição por região. Os grupos 1 e 2 reúnem municípios com "
          "alfabetização e IDHM Renda abaixo da média, quase todos do Nordeste e do Norte; os grupos 6 e 7, os de "
          "alfabetização, IDHM e infraestrutura mais altos, quase todos do Sul e do Sudeste. O grupo 5 se distingue pelo "
          "porte: a média do logaritmo da população fica 1,9 desvio-padrão acima da dos municípios. O nome de cada grupo "
          "traz a região da maioria dos municípios, o porte e a faixa de alfabetização; nenhum grupo é formado por uma "
          "região só."),
    legenda("Quadro 4 – Perfil dos sete clusters de contexto"),
    tabela(["Cluster", "Municí-\npios", "População\nmediana", "Alfabeti-\nzação", "IDHM\nRenda", "Infraes-\ntrutura",
            "Região\nprincipal"], t_clu, [2875, 900, 1100, 1050, 800, 1000, 1350]),
    fonte("Fonte: elaborado pelos autores. Infraestrutura: média das proporções de escolas com oito itens (biblioteca, "
          "laboratórios, internet, banheiro, água potável, energia e quadra)."),
    corpo("A separação entre os grupos é fraca (coeficiente de silhueta de cerca de 0,23): eles são uma partição útil para "
          "formar pares de comparação, e não tipos naturalmente distintos. Os grupos também acompanham a região, porque o "
          "IDHM só existe por UF. No painel, os pares de uma rede são as redes do mesmo cluster com gasto por aluno entre "
          "0,8 e 1,25 vez o dela; na comparação dentro do estado, também da mesma UF."),
    corpo("O percentual de redes acima do esperado, na comparação nacional, varia entre os clusters: de 40% no grupo de "
          "municípios pequenos do Nordeste a 59% no de municípios pequenos do Sul e do Sudeste (Anos Iniciais, Matemática, "
          "2023). O indicador não é neutro em relação ao contexto, o que reforça a comparação dentro do cluster."),
]

CAP5_MODELOS = [
    titulo(2, "Associação entre gasto e desempenho"),
    corpo("Esta seção examina a associação entre o gasto por aluno e a proficiência. Os resultados descrevem associação, e "
          "não efeito causal do gasto."),
    titulo(3, "Descrição da amostra e associação simples"),
    corpo("A Tabela 1 mostra o número de redes municipais com nota, o gasto mediano por aluno e a proficiência média em cada "
          "edição. O gasto mediano por aluno nos Anos Iniciais passou de R$ 9.202, em 2017, para R$ 15.859, em 2025, em "
          "reais de 2025. A proficiência caiu em 2021, na edição afetada pela pandemia, e subiu nas duas edições seguintes."),
    legenda("Tabela 1 – Redes municipais com nota, gasto por aluno e proficiência média, por edição"),
    tabela(["Etapa", "Edição", "Redes com nota", "Gasto por aluno (mediana, R$ de 2025)", "Matemática (média)", "Português (média)"],
           t_amostra, [1500, 900, 1400, 2475, 1400, 1400]),
    fonte("Fonte: elaborado pelos autores, com dados do SIOPE, do Censo Escolar e do Saeb."),
    corpo("A correlação de Spearman entre o gasto por aluno e a proficiência, sem controles, é positiva e vem caindo: de "
          "0,46 em 2017 para 0,16 em 2025, com o gasto do mesmo ano (Tabela 2). A correlação é maior com o gasto de anos "
          "anteriores. Dentro de cada UF, ela é bem menor: em 2023, a mediana entre as UFs é de 0,08, contra 0,26 no Brasil."),
    legenda("Tabela 2 – Correlação de Spearman entre gasto por aluno e proficiência (Anos Iniciais, Matemática)"),
    tabela(["Edição", "Gasto do mesmo ano", "1 ano antes", "2 anos antes", "4 anos antes"], t_rho, [1475, 1900, 1900, 1900, 1900]),
    fonte("Fonte: elaborado pelos autores. Vazio: sem gasto daquele ano (a série de gasto começa em 2017)."),
    titulo(3, "Modelo principal: entre municípios e dentro do mesmo município"),
    corpo(f"O modelo principal estima a proficiência em função do logaritmo do gasto por aluno, com controles e efeitos de "
          "edição, em três especificações (Tabela 3). A primeira compara os municípios entre si. A segunda inclui "
          "um efeito fixo de município, isto é, compara cada município com ele mesmo ao longo do tempo. A terceira, adotada "
          "como referência, acrescenta um efeito de UF e edição, de modo que a comparação é feita entre municípios do mesmo "
          "estado na mesma edição. Os erros-padrão são agrupados por município. Os modelos foram estimados em Python, em "
          "scripts desenvolvidos com o auxílio da IA a partir das especificações definidas pelos autores."),
    legenda("Tabela 3 – Gasto do mesmo ano e proficiência: três especificações"),
    tabela(["Especificação", *CAB4], t_modelo, [2475, 1650, 1650, 1650, 1650]),
    fonte(FONTE_MUN + NOTA_COEF + " EF: efeito fixo. Controles: infraestrutura e log das matrículas; no MQO, também log da população e "
          "alfabetização; nas especificações de 2017–2023, IDHM Renda e Longevidade da UF."),
    corpo("Entre os municípios, com os controles de contexto, o gasto quase não se associa à nota: o coeficiente é de 0,92 "
          "ponto por log do gasto nos Anos Iniciais, em Matemática, e não se distingue de zero. Dentro do mesmo município, a "
          "associação é positiva e estatisticamente significativa nas duas etapas e nas duas disciplinas. Na especificação "
          "de referência, um aumento de 10% no gasto por aluno acompanha um aumento de cerca de 0,22 ponto em Matemática nos "
          "Anos Iniciais; dobrar o gasto acompanha cerca de 1,6 ponto. Para dar a escala: o desvio-padrão da proficiência "
          "entre as redes municipais é de 24,2 pontos (Anos Iniciais, Matemática, 2017–2023), de modo que dobrar o gasto "
          "se associa a menos de 7% de um desvio-padrão. Para comparação, a média das redes municipais em Matemática vai "
          "de 220,2 pontos no 5º ano a 249,3 pontos no 9º ano (2023)."),
    corpo("A especificação de referência foi escolhida depois de uma investigação sobre a edição de 2025. Sem o efeito de UF "
          "e edição, incluir 2025 dobrava o coeficiente. Verificou-se que, de 2023 a 2025, as redes do Nordeste e do Norte "
          "tiveram ao mesmo tempo o maior aumento médio de gasto por aluno (cerca de 26% e 21%, contra 8% no Sudeste) e o maior ganho de nota. Com o "
          "efeito de UF e edição, o coeficiente fica estável, com ou sem 2025. O padrão é compatível com a complementação "
          "VAAT do Novo Fundeb, mas essa explicação não foi testada, porque o painel de dados não identifica as redes que "
          "receberam a complementação."),
    titulo(3, "Defasagem do gasto"),
    corpo(f"A Tabela 4 compara o gasto do ano da prova com o de um e dois anos antes, sempre nas mesmas redes. "
          "Dentro do município, a associação vem do gasto do ano da prova e do ano anterior, os dois anos do ciclo bienal do "
          "Saeb; o gasto de dois anos antes não se associa de forma significativa. O gasto de quatro anos antes, na janela em "
          "que existe (2021 a 2025), também não. O resultado difere do da correlação simples, que cresce com a defasagem."),
    legenda("Tabela 4 – Defasagem do gasto na especificação de referência, mesma amostra (2019–2025)"),
    tabela(["Etapa e disciplina", "Gasto do mesmo ano", "1 ano antes", "2 anos antes"], t_defas, [2775, 2100, 2100, 2100]),
    fonte(FONTE_MUN + NOTA_COEF),
    titulo(3, "Heterogeneidade por porte, região, cluster e nível de gasto"),
    corpo(f"A associação dentro do município não é igual em todos os grupos (Figura {F_HET}; os coeficientes estão na Tabela B.1, no Apêndice B). O teste de igualdade das "
          "inclinações é rejeitado nas quatro dimensões (p ≤ 0,02). A associação é maior nos municípios de até 50 mil "
          "habitantes e no Nordeste e no Norte. Nas cidades de 50 a 100 mil habitantes, ela não se distingue de zero, e "
          "nas de mais de 100 mil, é negativa. No Sudeste e no Sul, não se distingue de zero."),
    figura("rIdFig3", 3, 16.0, 11.02, "Figura 3"),
    fonte(f"Figura {F_HET} – Associação dentro do município por porte, região, cluster e faixa de gasto médio (Anos Iniciais, "
          "Matemática). Fonte: elaborado pelos autores."),
    corpo("Três cuidados valem para essa leitura. As dimensões se sobrepõem: 614 dos 1.063 municípios do quintil de maior "
          "gasto por aluno têm até 5 mil habitantes, de modo que a faixa de gasto e o porte contam, em boa parte, a mesma "
          "história. A associação negativa nas cidades grandes não tem explicação testada; são hipóteses a composição do "
          "gasto da subfunção 361 nessas redes, a variação das matrículas e a regressão à média. E, como são muitas "
          "comparações, nenhum grupo deve ser lido isoladamente."),
    titulo(3, "Testes de sensibilidade"),
    corpo(f"A Tabela 5 mostra a associação dentro do município quando se altera uma escolha de cada vez: sem a "
          "edição de 2021, só com os municípios que têm nota nas cinco edições, com o gasto médio do biênio, sem as redes "
          "municipais parciais, sem os saltos atípicos e com outras formas de controlar o IDHM. Em todos os testes, o "
          "coeficiente fica positivo e significativo, entre 1,4 e 5,5 pontos por log do gasto. Com o gasto médio do biênio, "
          "o coeficiente é cerca de 60% maior que o da referência na mesma janela."),
    legenda("Tabela 5 – Testes de sensibilidade (camada municipal, gasto do mesmo ano)"),
    tabela(["Teste", *CAB4], t_sens, [2875, 1550, 1550, 1550, 1550]),
    fonte(FONTE_MUN + NOTA_COEF + " Cada teste muda uma escolha da especificação de referência. As três últimas linhas usam efeito de "
          "edição e 2017–2023, porque o efeito de UF e edição absorve o IDHM."),
    titulo(3, "Camada estadual"),
    corpo("Na camada estadual, o mesmo modelo foi estimado com a UF no lugar do município (Tabela B.2, no Apêndice B). Nenhum coeficiente se "
          "distingue de zero, nos Anos Finais e no Ensino Médio, em nenhuma especificação, nem com a versão B do gasto, nem com o gasto medido pela soma das subfunções da educação básica, que deixa de fora o que a função 12 não detalha em subfunção. Com 27 "
          "unidades, a estimativa é imprecisa: os intervalos de 95% vão de cerca de −6 a +9 pontos por log do gasto e "
          "incluem tanto zero quanto valores maiores que o da camada municipal. A leitura correta é que a associação não é "
          "detectável com 27 unidades, e não que ela não exista."),
]

# ───────────────────────── estudos de caso e validação (src/Analise/Estudos_Caso.py) ─────────────────────────
cs = pl.read_csv(D / "estudos_caso_resumo.csv").sort("CASO")
cserie = pl.read_csv(D / "estudos_caso.csv")
C = {r["CASO"]: r for r in cs.iter_rows(named=True)}


def br(x: float | None, casas: int = 2) -> str:  # noqa: F811  arredonda meio para cima, como o painel (336,45 → 336,5)
    from decimal import ROUND_HALF_UP, Decimal
    if x is None:
        return MT.br(x)
    return MT.br(float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)), casas)


def pct(x: float | None) -> str:
    return "—" if x is None else ("+" if x > 0 else "") + br(100 * x, 1) + "%"


def reais(x: float) -> str:
    return "R$ " + br(x, 0)


def mun(k: str) -> str:
    return C[k]["MUNICIPIO"]


T_CEBA = 6   # as Tabelas 1 a 5 estão na seção de associação (a heterogeneidade e a camada estadual foram ao Apêndice B)
T_CASOS = 7
TELAS_CASO = [  # (arquivo em docs/resultados/telas, legenda); entram só se a captura existir
    ("caso_a_ficha", f"Página Ficha do município com {mun('A')}"),
    ("caso_a_pares", f"Página Pares com {mun('A')} como referência"),
    ("caso_b_ficha", f"Página Ficha do município com {mun('B')}"),
    ("caso_c_ficha", f"Página Ficha do município com {mun('C')}"),
]
TELAS_DIR = Path(sys.argv[3])
TELAS_CASO = [t for t in TELAS_CASO if (TELAS_DIR / f"{t[0]}.png").exists()]
F_CEBA = F_HET + 1
F_CASO = F_HET + 2


def fig_caso(arq: str, numero) -> list[str]:
    k = next(i for i, t in enumerate(TELAS_CASO) if t[0] == arq) if any(t[0] == arq for t in TELAS_CASO) else None
    if k is None:
        return [nota(f"[Tela a capturar: {arq.replace('_', ' ')}.]")]
    return [figura(f"rIdCaso{k}", 80 + k, 16.0, 9.0, f"Caso {k + 1}"),
            fonte(f"Figura {numero} – {TELAS_CASO[k][1]} (Anos Iniciais, Matemática, 2023). Fonte: painel elaborado "
                  "pelos autores.")]


def alerta(salto: bool, part: float) -> str:
    a = (["salto atípico"] if salto else []) + (["rede parcial"] if part < 0.5 else [])
    return ", ".join(a) if a else "nenhum"


t_casos = [
    ["Critério de escolha", "Maior resultado acima do esperado entre as redes de mais de 50 mil habitantes, sem alerta",
     "Município mais populoso entre as redes municipais parciais",
     "Maior resultado acima do esperado entre as redes de mais de 50 mil habitantes com salto atípico"],
    ["População (2022)", *[br(C[k]["POPULACAO"], 0) for k in "ABC"]],
    ["Cluster", *[C[k]["CLUSTER"] for k in "ABC"]],
    ["Gasto por aluno (R$ de 2025)", *[reais(C[k]["GASTO_2023"]) for k in "ABC"]],
    ["Proficiência observada", *[br(C[k]["PROF_2023"], 1) for k in "ABC"]],
    ["Proficiência esperada", *[br(C[k]["ESPERADA_2023"], 1) for k in "ABC"]],
    ["Em relação ao esperado", *[pct(C[k]["VS_ESPERADO_2023"]) for k in "ABC"]],
    ["Percentil entre as redes", *[br(C[k]["PERCENTIL_2023"], 1) for k in "ABC"]],
    ["Alunos públicos dos Anos Iniciais na rede municipal", *[br(100 * C[k]["PART_MUN_2023"], 0) + "%" for k in "ABC"]],
    ["Alerta do painel", *[alerta(C[k]["SALTO_2023"], C[k]["PART_MUN_2023"]) for k in "ABC"]],
    ["Pares / pares que entregam mais", *[f"{C[k]['PARES']} / {C[k]['PARES_ACIMA']}" for k in "ABC"]],
    ["Par com maior resultado", *[f"{C[k]['MELHOR_PAR']} ({pct(C[k]['MELHOR_PAR_VS'])}"
                                  + (", com salto)" if C[k]["MELHOR_PAR_SALTO"] else ")") for k in "ABC"]],
]
t_serie = [[r["MUNICIPIO"], str(r["ANO"]), reais(r["GASTO_ALUNO_R2025_L0"]), br(r["PROFICIENCIA"], 1),
            br(r["NOTA_ESPERADA"], 1), pct(r["EFIC_PCT"]), alerta(r["SALTO_ATIPICO"], r["PART_MUN"])]
           for r in cserie.sort(["CASO", "ANO"]).iter_rows(named=True)]


def s(k: str, ano: int, col: str) -> float:
    return cserie.filter((pl.col("CASO") == k) & (pl.col("ANO") == ano))[col][0]

# ───────────────────────── Ceará × Bahia (src/Analise/Comparacao_CE_BA.py; decisão A19) ─────────────────────────
cb = pl.read_csv(D / "comparacao_ce_ba.csv")


def cbv(corte: str, uf: str, col: str, **f) -> float:
    d = cb.filter((pl.col("CORTE") == corte) & (pl.col("SG_UF") == uf))
    for k, v in f.items():
        d = d.filter(pl.col(k) == v)
    assert d.height == 1, (corte, uf, f, d.height)
    return d[col][0]


def et(uf: str, etapa: str, disc: str, col: str) -> float:
    return cbv("2023 por etapa", uf, col, ETAPA=etapa, DISCIPLINA=disc)


def pc(x: float) -> str:
    return br(100 * x, 0) + "%"


t_ceba = [
    ["Redes municipais com nota (AI, 2023)", *[f"{int(et(u, 'AI', 'MT', 'REDES'))}" for u in ("CE", "BA")]],
    ["Gasto mediano por aluno (AI, 2023)", *[reais(et(u, "AI", "MT", "GASTO_MEDIANO")) for u in ("CE", "BA")]],
    *[[f"Proficiência média: {ETQ}", *[br(et(u, e, dd, "PROFICIENCIA_MEDIA"), 1) for u in ("CE", "BA")]]
      for ETQ, e, dd in [("AI Matemática", "AI", "MT"), ("AI Português", "AI", "LP"), ("AF Matemática", "AF", "MT"),
                         ("AF Português", "AF", "LP")]],
    ["Redes acima do esperado (AI Matemática)", *[pc(et(u, "AI", "MT", "PARC_ACIMA")) for u in ("CE", "BA")]],
    ["Redes acima do esperado no cluster 1 (AI Matemática)",
     *[pc(cbv("AI MT 2023 por cluster", u, "PARC_ACIMA", CLUSTER=1)) for u in ("CE", "BA")]],
    ["Redes acima do esperado sem as de salto atípico (AI Matemática)",
     *[pc(cbv("AI MT 2023 sem saltos", u, "PARC_ACIMA")) for u in ("CE", "BA")]],
    ["Redes com salto atípico (AI Matemática)", *[f"{int(et(u, 'AI', 'MT', 'SALTOS'))}" for u in ("CE", "BA")]],
    ["Alfabetização média dos municípios (Censo 2022)", "79,5%", "82,0%"],
    ["IDHM Renda da UF (2023)", "0,674", "0,673"],
    ["Ensino Médio estadual: proficiência em Matemática", "265,6", "251,0"],
    ["Ensino Médio estadual: gasto por aluno", "R$ 15.966", "R$ 16.988"],
]
dce = et("CE", "AI", "MT", "PROFICIENCIA_MEDIA") - et("BA", "AI", "MT", "PROFICIENCIA_MEDIA")

CAP5_CEBA = [
    titulo(2, "Mesmo gasto, resultados diferentes: Ceará e Bahia"),
    nota("[Análise proposta por Guilherme Menezes, com os números preparados por Henrique Lindoso (2026-11-16). A "
         "interpretação fica com os autores.]"),
    corpo("Comparar redes com gasto parecido é o uso central do painel. O contraste mais forte aparece entre dois estados "
          "do Nordeste. Em 2023, o gasto mediano por aluno das redes municipais foi praticamente o mesmo no Ceará "
          f"({reais(et('CE', 'AI', 'MT', 'GASTO_MEDIANO'))}) e na Bahia ({reais(et('BA', 'AI', 'MT', 'GASTO_MEDIANO'))}), "
          "mas a proficiência média em Matemática nos Anos Iniciais foi de "
          f"{br(et('CE', 'AI', 'MT', 'PROFICIENCIA_MEDIA'), 1)} pontos no Ceará e de "
          f"{br(et('BA', 'AI', 'MT', 'PROFICIENCIA_MEDIA'), 1)} na Bahia: {br(dce, 0)} pontos de diferença, mais que o "
          "desvio-padrão entre as redes do país (25,0 pontos). No Ceará, "
          f"{pc(et('CE', 'AI', 'MT', 'PARC_ACIMA'))} das redes ficaram acima do esperado para o seu gasto e contexto; na "
          f"Bahia, {pc(et('BA', 'AI', 'MT', 'PARC_ACIMA'))} (Tabela {T_CEBA}). Os números desta seção foram calculados com o auxílio da IA, "
          "a partir dos mesmos painéis de dados."),
    corpo("A diferença não se limita a uma etapa ou disciplina: aparece nos Anos Iniciais e nos Anos Finais, em Matemática "
          f"e em Português, e em todas as edições de 2017 a 2025 (Figura {F_CEBA}). Também não se explica pelo contexto "
          "medido no trabalho: o Ceará tem alfabetização média um pouco menor que a da Bahia (79,5% contra 82,0%) e o mesmo "
          "IDHM Renda (0,674 e 0,673). Dentro do mesmo cluster, a diferença se mantém: no cluster 1, de municípios pequenos "
          f"com alfabetização mais baixa, {pc(cbv('AI MT 2023 por cluster', 'CE', 'PARC_ACIMA', CLUSTER=1))} das redes do "
          f"Ceará e {pc(cbv('AI MT 2023 por cluster', 'BA', 'PARC_ACIMA', CLUSTER=1))} das da Bahia ficaram acima do "
          "esperado. Sem as redes com salto atípico, o resultado é o mesmo."),
    legenda(f"Tabela {T_CEBA} – Redes municipais do Ceará e da Bahia em 2023"),
    tabela(["", "Ceará", "Bahia"], t_ceba, [5075, 2000, 2000]),
    fonte("Fonte: elaborado pelos autores, com dados do SIOPE, do Censo Escolar, do Saeb, do IBGE e do Radar IDHM. Acima "
          "do esperado: na comparação nacional. Cluster 1: municípios pequenos, de maioria nordestina e alfabetização mais "
          "baixa."),
    figura("rIdCeba", 72, 16.0, 6.40, "Figura Ceará e Bahia"),
    fonte(f"Figura {F_CEBA} – Ceará e Bahia: proficiência média das redes municipais por edição, e gasto e proficiência "
          "de cada rede em 2023 (Anos Iniciais, Matemática). Uma rede da Bahia, com gasto marcado como extremo (R$ 1.206 "
          "por aluno), fica fora da escala. Fonte: elaborado pelos autores."),
    corpo("Na camada estadual, a comparação só faz sentido no Ensino Médio. Nos Anos Finais, a rede estadual do Ceará "
          "atende só 2% dos alunos públicos da etapa (13% na Bahia), e a nota estadual retrata um grupo pequeno. No Ensino "
          "Médio, a direção é a mesma, com diferença menor: 265,6 pontos em Matemática no Ceará e 251,0 na Bahia, com "
          "gasto estadual por aluno de R$ 15.966 e R$ 16.988."),
    corpo("Três cuidados valem para essa leitura. A comparação é de associação: mostra que o gasto, sozinho, não explica a "
          "diferença, mas não diz o que a explica. O Ceará distribui parte do ICMS aos municípios segundo resultados "
          "educacionais e presta assistência técnica às redes, e a literatura associa essas políticas a ganhos de nota "
          "(Lautharte et al., 2021); ligar o resultado a elas cabe à discussão. Em segundo lugar, o Ceará "
          f"concentra mais saltos atípicos ({int(et('CE', 'AI', 'MT', 'SALTOS'))} das "
          f"{int(et('CE', 'AI', 'MT', 'REDES'))} redes em 2023, contra {int(et('BA', 'AI', 'MT', 'SALTOS'))} das "
          f"{int(et('BA', 'AI', 'MT', 'REDES'))} na Bahia), embora tirá-los não mude a comparação. Por fim, a diferença é "
          "entre médias: há redes da Bahia acima de muitas do Ceará, e a página Pares permite localizá-las."),
]


CAP5_CASOS = [
    nota(AVISO + " A análise gerencial dos casos fica com os autores; aqui estão a escolha e os números."),
    corpo("Esta seção mostra como o painel apoia a comparação entre redes, com três casos. Os casos foram escolhidos por "
          "regras objetivas, propostas com o auxílio da IA e aprovadas pelos autores, aplicadas ao recorte padrão do painel (Anos Iniciais, Matemática, edição de 2023, comparação "
          "nacional), para ilustrar três situações de leitura: uma rede acima do esperado sem alerta, uma rede abaixo do "
          "esperado com alerta de rede parcial e uma rede acima do esperado com alerta de salto atípico. Eles ilustram o "
          "uso do painel e não formam uma amostra representativa. Os pares de cada rede são as redes do mesmo cluster "
          "com gasto por aluno entre 0,8 e 1,25 vez o dela, a mesma regra da página Pares. A Tabela "
          f"{T_CASOS} resume os três casos em 2023, e a Tabela {T_CASOS + 1} traz a série de cada um. A Figura {F_CASO} "
          "mostra a página Pares com o primeiro caso; as fichas dos três municípios no painel estão no Apêndice B "
          "(Figuras B.10 a B.12)."),
    legenda(f"Tabela {T_CASOS} – Os três casos em 2023 (Anos Iniciais, Matemática, comparação nacional)"),
    tabela(["", mun("A"), mun("B"), mun("C")], t_casos, [2475, 2200, 2200, 2200]),
    fonte("Fonte: elaborado pelos autores, com dados do SIOPE, do Censo Escolar, do Saeb e do IBGE. Em relação ao "
          "esperado: diferença entre a proficiência observada e a esperada, em % da esperada. Pares: mesmo cluster e gasto "
          "por aluno entre 0,8 e 1,25 vez o da rede."),
    titulo(3, f"Rede acima do esperado sem alerta: {mun('A')}"),
    corpo(f"{mun('A')} tem {br(C['A']['POPULACAO'], 0)} habitantes e está no cluster {C['A']['CLUSTER']}. Em 2023, a rede "
          f"municipal gastou {reais(C['A']['GASTO_2023'])} por aluno e teve proficiência de {br(C['A']['PROF_2023'], 1)} "
          f"pontos, contra {br(C['A']['ESPERADA_2023'], 1)} esperados para o seu gasto e contexto: "
          f"{pct(C['A']['VS_ESPERADO_2023'])}, acima de {br(C['A']['PERCENTIL_2023'], 0)}% das redes do país. A rede "
          "atende todos os alunos públicos dos Anos Iniciais do município e não tem salto atípico em nenhuma edição."),
    corpo(f"A série mostra uma melhora contínua em relação ao esperado: {pct(s('A', 2017, 'EFIC_PCT'))} em 2017, "
          f"{pct(s('A', 2019, 'EFIC_PCT'))} em 2019, {pct(s('A', 2021, 'EFIC_PCT'))} em 2021 e "
          f"{pct(s('A', 2023, 'EFIC_PCT'))} em 2023. A proficiência passou de {br(s('A', 2017, 'PROFICIENCIA'), 1)} para "
          f"{br(s('A', 2023, 'PROFICIENCIA'), 1)} pontos, e o gasto por aluno, de {reais(s('A', 2017, 'GASTO_ALUNO_R2025_L0'))} "
          f"para {reais(s('A', 2023, 'GASTO_ALUNO_R2025_L0'))}, em reais de 2025. Em 2025, a proficiência foi de "
          f"{br(s('A', 2025, 'PROFICIENCIA'), 1)}; a comparação nacional não cobre essa edição, porque o IDHM termina em 2024."),
    corpo(f"Entre os {C['A']['PARES']} pares, só um entrega mais: {C['A']['MELHOR_PAR']}, com "
          f"{pct(C['A']['MELHOR_PAR_VS'])}, mas com salto atípico em 2023. O primeiro par sem alerta, "
          f"{C['A']['MELHOR_PAR_SEM_SALTO']}, fica logo abaixo de {mun('A')}. Os cinco primeiros pares da lista são do "
          "Ceará. Para esta rede, o painel indica que ela já está no topo do seu grupo: em vez de procurar referências, a "
          "pergunta gerencial passa a ser o que explica o resultado e se ele se mantém."),
    *fig_caso("caso_a_pares", F_CASO),
    titulo(3, f"Rede abaixo do esperado com rede parcial: {mun('B')}"),
    corpo(f"{mun('B')} é o município mais populoso entre as redes municipais parciais: em 2023, a prefeitura atendia "
          f"{br(100 * C['B']['PART_MUN_2023'], 0)}% dos alunos públicos dos Anos Iniciais, e o restante estava na rede "
          f"estadual. A rede municipal gastou {reais(C['B']['GASTO_2023'])} por aluno, teve proficiência de "
          f"{br(C['B']['PROF_2023'], 1)} pontos, contra {br(C['B']['ESPERADA_2023'], 1)} esperados "
          f"({pct(C['B']['VS_ESPERADO_2023'])}), e ficou no percentil {br(C['B']['PERCENTIL_2023'], 0)}. O resultado em "
          f"relação ao esperado foi negativo em todas as edições, de {pct(s('B', 2017, 'EFIC_PCT'))} em 2017 a "
          f"{pct(s('B', 2023, 'EFIC_PCT'))} em 2023."),
    corpo(f"Dos {C['B']['PARES']} pares, {C['B']['PARES_ACIMA']} entregam mais; o primeiro é {C['B']['MELHOR_PAR']}, com "
          f"{pct(C['B']['MELHOR_PAR_VS'])}. O caso mostra três limites da comparação. Primeiro, o alerta de rede parcial: "
          "o gasto por aluno e a nota se referem só à parte municipal da rede pública, e a comparação com redes que "
          "atendem todos os alunos é imperfeita. Segundo, os pares são cidades muito menores (a maior entre as cinco "
          "primeiras tem 256 mil habitantes), porque a população é só uma das cinco variáveis do agrupamento. Terceiro, "
          "o nível do gasto das capitais depende da fonte: nos 30 maiores municípios, o gasto informado ao SICONFI e ao "
          "SIOPE diverge mais do que nos demais."),
    titulo(3, f"Rede acima do esperado com salto atípico: {mun('C')}"),
    corpo(f"{mun('C')} tem o maior resultado em relação ao esperado entre as redes de mais de 50 mil habitantes com salto "
          f"atípico: proficiência de {br(C['C']['PROF_2023'], 1)} pontos em 2023, contra {br(C['C']['ESPERADA_2023'], 1)} "
          f"esperados ({pct(C['C']['VS_ESPERADO_2023'])}). A média das redes municipais do país, no mesmo recorte, foi de "
          "220,2 pontos. A série tem dois saltos marcados: a queda para "
          f"{br(s('C', 2021, 'PROFICIENCIA'), 1)} pontos em 2021 e a alta para {br(s('C', 2023, 'PROFICIENCIA'), 1)} em 2023. "
          f"O gasto por aluno também oscila: {reais(s('C', 2019, 'GASTO_ALUNO_R2025_L0'))} em 2019, "
          f"{reais(s('C', 2021, 'GASTO_ALUNO_R2025_L0'))} em 2021 e {reais(s('C', 2023, 'GASTO_ALUNO_R2025_L0'))} em 2023."),
    corpo(f"Dos {C['C']['PARES']} pares, só {C['C']['PARES_ACIMA']} entregam mais, ambos de Alagoas: "
          f"{C['C']['MELHOR_PAR']} ({pct(C['C']['MELHOR_PAR_VS'])}, também com salto) e {C['C']['MELHOR_PAR_SEM_SALTO']}. "
          "O padrão não é isolado: das 53 redes no 1% superior do país em 2023, 13 são de Alagoas, que tem 1,9% das redes "
          "com cálculo (100 de 5.240), e 17 têm salto atípico. Nesses casos, o alerta do painel sugere conferir o resultado "
          "antes de tomar a rede como referência; a marca indica uma variação fora do padrão, e não um erro."),
    nota("[Para os autores: o levantamento bibliográfico (docs/levantamento_bibliografico.md, seção 8) registrou que "
         "Alagoas distribui parte do ICMS aos municípios segundo indicadores de qualidade da educação. É contexto a "
         "considerar na interpretação, e não explicação testada; nenhum trabalho localizado aponta irregularidade nas notas. "
         "CITAR, se for usado.]"),
    legenda(f"Tabela {T_CASOS + 1} – Série dos três casos por edição (Anos Iniciais, Matemática, comparação nacional)"),
    tabela(["Município", "Edição", "Gasto por aluno (R$ de 2025)", "Proficiência", "Esperada", "Em relação ao esperado",
            "Alerta"], t_serie, [1800, 800, 1500, 1300, 1300, 1375, 1000]),
    fonte("Fonte: elaborado pelos autores. Em 2025, a comparação nacional não tem cálculo, porque a série do IDHM termina "
          "em 2024; a comparação com o mesmo estado cobre essa edição."),
    titulo(3, "O que os casos mostram sobre o uso do painel"),
    corpo("Nos três casos, a leitura combina três informações do painel: o resultado em relação ao esperado, os alertas e "
          "os pares. O resultado sozinho levaria a conclusões apressadas: tomar Coruripe como modelo sem olhar o salto, ou "
          "comparar São Paulo com cidades pequenas sem considerar que a rede municipal atende menos da metade dos alunos. "
          "Os casos também ilustram por que o indicador se chama desempenho em relação ao esperado, e não eficiência (Capítulo "
          "3): na comparação nacional, o gasto quase não altera a proficiência esperada, de modo que o indicador mostra a "
          "distância até redes de gasto e contexto parecidos, e não o rendimento de cada real gasto."),
]

CAP5_VALIDACAO = [
    nota(AVISO + " Cabe aos autores e à orientadora decidir se esta seção mantém o nome de validação conceitual."),
    corpo("A ferramenta não foi testada com usuários, o que fica registrado como limitação. A validação feita tem duas "
          "partes: cenários de uso, em que cada uma das três perguntas de entrada do painel é percorrida com os casos da "
          "seção anterior, e a conferência técnica dos números. O Quadro 5 resume os cenários."),
    legenda("Quadro 5 – Cenários de uso: as perguntas de entrada do painel percorridas com dados reais"),
    tabela(["Pergunta de entrada", "Página", "O que o painel responde (Anos Iniciais, Matemática, 2023)", "Coerência com a análise"], [
        ["Gastar mais se associa a aprender mais?", "Defasagens",
         "Correlação de 0,26 no Brasil com o gasto do mesmo ano, e mediana de 0,08 entre as UFs",
         "Coerente com as Tabelas 2 e 3: a associação simples é fraca e se explica em boa parte pelo contexto. A "
         "associação dentro do município não está no painel; fica no texto"],
        ["Minha rede entrega o esperado?", "Ficha do município",
         f"{mun('A')}: {pct(C['A']['VS_ESPERADO_2023'])}, sem alerta. {mun('B')}: {pct(C['B']['VS_ESPERADO_2023'])}, com "
         f"alerta de rede parcial. {mun('C')}: {pct(C['C']['VS_ESPERADO_2023'])}, com alerta de salto",
         "Os alertas aparecem nos dois casos em que a leitura pede cuidado"],
        ["Com quem conversar?", "Pares",
         f"{mun('A')}: {C['A']['PARES_ACIMA']} de {C['A']['PARES']} pares entrega mais. {mun('B')}: "
         f"{C['B']['PARES_ACIMA']} de {C['B']['PARES']}. {mun('C')}: {C['C']['PARES_ACIMA']} de {C['C']['PARES']}",
         "A regra devolve listas ordenadas e úteis para redes médias. Para metrópoles, os pares são cidades muito menores; "
         "nos clusters grandes, a faixa de gasto inclui boa parte do grupo"],
    ], [1900, 1300, 3175, 2700]),
    fonte("Fonte: elaborado pelos autores."),
    corpo("A conferência técnica, feita com o auxílio da IA, comparou os números do painel com os cálculos feitos em "
          "Python no recorte padrão "
          "(Brasil, Anos Iniciais, Matemática, 2023): bateram o gasto mediano por aluno (R$ 13.721), a proficiência média "
          "(220,2 pontos), a parcela de redes acima do esperado (46,3%), o número de redes com nota (5.243) e a cobertura do "
          "Saeb (94,1%), além das correlações da página Defasagens e dos números dos três casos. A conferência encontrou e "
          "corrigiu dois erros nas medidas do painel: a mediana do gasto contava como zero três redes sem gasto, e a contagem "
          "de pares que entregam mais incluía dois pares sem resultado calculado. As páginas do painel são conferidas contra "
          "os esquemas oficiais do formato do Power BI, a correção pela inflação foi conferida de ponta a ponta, e um comando "
          "único refaz o tratamento e os painéis de dados a partir das fontes. Os resultados dos modelos passaram pelos testes "
          "de sensibilidade da Tabela 5."),
]

FUTURO = [nota(
    "[Base factual para este item (Henrique), revista em 2026-11-17 (registro A21). Escolher quais entram e redigir como "
    "alíneas. DEIXADO DE FORA NESTA VERSÃO, com o motivo: (a) simulação de cenários de gasto: a associação entre gasto e "
    "nota dentro do município é pequena e não é causal, e um simulador sugeriria um efeito que o trabalho não mede; (b) "
    "monitoramento das condicionalidades e dos indicadores do VAAR: pede os dados de habilitação das redes, que não foram "
    "integrados; (c) gasto separado por etapa e Educação Infantil: o SIOPE informa a subfunção 361 para todo o Ensino "
    "Fundamental, sem separar Anos Iniciais e Finais; (d) avaliação com usuários: entrevistar gestores exige termo de "
    "consentimento e, possivelmente, comitê de ética (Manual de TCC), e a validação ficou nos cenários de uso da seção "
    "4.5. EXTENSÕES SUGERIDAS: (e) identificar as redes que recebem a complementação VAAT, para testar a hipótese "
    "levantada para 2023–2025; (f) usar o gasto médio do biênio na nota esperada, que no modelo acompanha melhor o ciclo "
    "do Saeb (coeficiente cerca de 60% maior); (g) estender a comparação nacional a 2025 quando o IDHM desse ano for "
    "publicado; (h) comparar o indicador com uma medida de fronteira, como a análise envoltória de dados ou a fronteira "
    "estocástica; (i) estudar o efeito de incentivos estaduais, como o ICMS educacional do Ceará e de Alagoas, sobre as "
    "redes acima do esperado e os saltos atípicos; (j) se o uso mostrar listas de pares longas demais nos grupos grandes, "
    "limitar os pares às redes de gasto mais próximo. A publicação do painel com QR Code não é trabalho futuro: é a etapa "
    "final desta versão.]")]
AUTOMACAO = [nota(
    "[Base factual para este item: hoje, um comando único (run_pipeline.py) refaz o tratamento e os painéis de dados a "
    "partir das bases baixadas. A extração tem scripts próprios, disparados à mão. O SIOPE, o SICONFI e o IPCA vêm "
    "direto das APIs oficiais, e as demais bases são baixadas manualmente: as planilhas do Ideb e os microdados do Censo "
    "Escolar, do Inep; o IDHM, do Atlas Brasil; e a alfabetização do Censo 2022 e a malha municipal, do IBGE. O painel em "
    "Power BI lê os arquivos de uma pasta local e é atualizado pelo botão Atualizar. Melhorias possíveis: automatizar o "
    "download das bases do Inep, por exemplo com o pacote educabR, para a linguagem R (Bissoli, 2026), que baixa e "
    "organiza o Censo Escolar, o Saeb e o Ideb, mas não os dados de gasto do SIOPE e do SICONFI; agendar a extração e o "
    "tratamento; publicar o "
    "painel no serviço do Power BI, com atualização programada; e trocar a pasta local por um armazenamento "
    "compartilhado, o que dispensaria ajustar o caminho dos dados em cada computador.]")]
def ordem_apa(r: str) -> str:
    """Ordem alfabética da APA: sem acentos e sem itálico; "&" não conta (Jackson, Johnson vem antes de Jackson & M.)."""
    s = unicodedata.normalize("NFKD", r.replace("*", "").replace("& ", "")).encode("ascii", "ignore").decode().lower()
    return s


def ref(texto: str) -> str:
    """Referência em APA: recuo deslocado de 1,25 cm, espaço simples e uma linha em branco depois; *trecho* em itálico."""
    partes = texto.split("*")
    runs = "".join(run(s, italico=bool(k % 2)) for k, s in enumerate(partes) if s)
    return ('<w:p><w:pPr><w:spacing w:after="240" w:before="0" w:line="240" w:lineRule="auto"/>'
            '<w:ind w:left="709" w:hanging="709"/><w:jc w:val="left"/></w:pPr>' + runs + "</w:p>")


# Lista final (2026-11-17, registro D4): as referências do rascunho e as dos capítulos 4 e 5, numa só lista em APA 7,
# em ordem alfabética. Entra só o que é citado no texto; as candidatas do levantamento bibliográfico entram quando forem
# citadas. Substitui a nota de norma e a lista antiga do rascunho (ver montagem).
REFERENCIAS = [nota(
    "[Lista final de referências, montada em 2026-11-17: une as do rascunho e as dos capítulos 3 e 4, em APA 7 (o Manual "
    "de TCC torna a APA obrigatória a partir de 2026; a formatação do trabalho segue a ABNT). Entram só as obras citadas. "
    "Desde 2026-11-17, inclui as obras citadas na revisão bibliográfica (2.1.4 e 2.2). Mudanças "
    "em relação ao rascunho: DOIs acrescentados; o Inep (2026) do rascunho passa a Inep (2026b), e as citações no texto "
    "devem ser ajustadas. CONFERIR as datas de acesso e os itens marcados antes da versão final.]"),
    *[ref(r) for r in sorted([
        "Alves, M. T. G., & Soares, J. F. (2013). Contexto escolar e indicadores educacionais: Condições desiguais para a "
        "efetivação de uma política de avaliação educacional. *Educação e Pesquisa, 39*(1), 177–194. "
        "https://doi.org/10.1590/S1517-97022013000100012",
        "Alves, P. J. H., & Frio, G. S. (2022). Uma análise dos resultados educacionais dos municípios brasileiros. "
        "*Planejamento e Políticas Públicas*, (61). https://doi.org/10.38116/ppp61art10",
        "Cruz, G. F., & Rocha, R. (2018). Efeitos do FUNDEF/B sobre frequência escolar, fluxo escolar e trabalho infantil: "
        "Uma análise com base nos Censos de 2000 e 2010. *Estudos Econômicos, 48*(1), 39–75. "
        "https://doi.org/10.1590/0101-4161481239gcr",
        "Faria, F. P., Jannuzzi, P. M., & Silva, S. J. (2008). Eficiência dos gastos municipais em saúde e educação: Uma "
        "investigação através da análise envoltória no estado do Rio de Janeiro. *Revista de Administração Pública, 42*(1), "
        "155–177. https://doi.org/10.1590/S0034-76122008000100008",
        "Hanushek, E. A. (2003). The failure of input-based schooling policies. *The Economic Journal, 113*(485), F64–F98. "
        "https://doi.org/10.1111/1468-0297.00099",
        "Hirata, G., Melo, L., & Oliveira, J. B. (2022). O Fundeb e a questão da equidade. *Revista Brasileira de Economia, "
        "76*(2). https://doi.org/10.5935/0034-7140.20220009",
        "Jackson, C. K., & Mackevicius, C. L. (2024). What impacts can we expect from school spending policy? Evidence from "
        "evaluations in the United States. *American Economic Journal: Applied Economics, 16*(1), 412–446. "
        "https://doi.org/10.1257/app.20220279",
        "Menezes-Filho, N., & Amaral, L. F. L. E. (2009). *A relação entre gastos educacionais e desempenho escolar* "
        "(Insper Working Paper). Insper. https://ideas.repec.org/p/aap/wpaper/064.html [CONFERIR o número do texto]",
        "Menezes-Filho, N., & Pazello, E. (2007). Do teachers' wages matter for proficiency? Evidence from a funding reform "
        "in Brazil. *Economics of Education Review, 26*(6), 660–672. https://doi.org/10.1016/j.econedurev.2007.08.003",
        "Oliveira, V. E., Menezes Filho, N. A., & Komatsu, B. K. (2022). A relação entre a qualidade da gestão municipal e o "
        "desempenho educacional no Brasil. *Economia Aplicada, 26*(1), 81–100. https://doi.org/10.11606/1980-5330/ea148736",
        "Silva Júnior, J. A., Miranda, R. L. P., & Coelho, R. P. S. (2025). Nem bom como dizem, nem ruim como pensam: O "
        "Fundeb e a desigualdade educacional regional brasileira. *FINEDUCA – Revista de Financiamento da Educação, 15*. "
        "https://doi.org/10.22491/2236-5907135670",
        "Soares, J. F., & Xavier, F. P. (2013). Pressupostos educacionais e estatísticos do Ideb. *Educação & Sociedade, "
        "34*(124), 903–923. https://www.scielo.br/pdf/es/v34n124/13.pdf",
        "Anthropic. (2026). *Claude* [Modelo de linguagem de grande escala, usado por meio do aplicativo e do Claude "
        "Code]. https://claude.ai",
        "Bissoli, S. S. P. (2026). *educabR: Download and process Brazilian education data from INEP* (Versão 2.0.0) "
        "[Pacote de software R]. CRAN. https://doi.org/10.32614/CRAN.package.educabR",
        "Brasil. (1988). *Constituição da República Federativa do Brasil de 1988*. Presidência da República.",
        "Brasil. (1996). *Lei nº 9.394, de 20 de dezembro de 1996*. Estabelece as diretrizes e bases da educação nacional. "
        "Diário Oficial da União.",
        "Brasil. (2000). *Lei Complementar nº 101, de 4 de maio de 2000*. Lei de Responsabilidade Fiscal. Diário Oficial "
        "da União.",
        "Brasil. (2011). *Lei nº 12.527, de 18 de novembro de 2011*. Lei de Acesso à Informação. Diário Oficial da União.",
        "Brasil. (2016). *Decreto nº 8.777, de 11 de maio de 2016*. Institui a Política de Dados Abertos do Poder Executivo "
        "federal. Diário Oficial da União.",
        "Brasil. (2020a). *Emenda Constitucional nº 108, de 26 de agosto de 2020*. Diário Oficial da União.",
        "Brasil. (2020b). *Lei nº 14.113, de 25 de dezembro de 2020*. Regulamenta o Fundo de Manutenção e Desenvolvimento "
        "da Educação Básica e de Valorização dos Profissionais da Educação (Fundeb). Diário Oficial da União.",
        "Brasil. (2021). *Lei nº 14.276, de 27 de dezembro de 2021*. Altera a Lei nº 14.113, de 25 de dezembro de 2020, "
        "que regulamenta o Fundeb. Diário Oficial da União.",
        "Brasil. (2025). *Portaria Interministerial MEC/MF nº 4, de 30 de abril de 2025*. Diário Oficial da União.",
        "Cairney, P. (2016). *The politics of evidence-based policy making*. Palgrave Macmillan. "
        "https://doi.org/10.1057/978-1-137-51781-4",
        "Davenport, T. H., & Harris, J. G. (2007). *Competing on analytics: The new science of winning*. Harvard Business "
        "School Press.",
        "Departamento de Administração FEA/USP. (2025). *Manual de Trabalho de Conclusão de Curso: Curso de Graduação em "
        "Administração*. Universidade de São Paulo.",
        "Few, S. (2006). *Information dashboard design: The effective visual communication of data*. O’Reilly Media.",
        "Fundo Nacional de Desenvolvimento da Educação. (2026). *SIOPE: Sistema de Informações sobre Orçamentos Públicos "
        "em Educação – dados abertos* [Conjunto de dados]. "
        "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/",
        "Hanushek, E. A. (1997). Assessing the effects of school resources on student performance: An update. "
        "*Educational Evaluation and Policy Analysis, 19*(2), 141–164. https://doi.org/10.3102/01623737019002141",
        "Heald, D. (2006). Varieties of transparency. In C. Hood & D. Heald (Eds.), *Transparency: The key to better "
        "governance?* (pp. 25–43). Oxford University Press.",
        "Instituto Brasileiro de Geografia e Estatística. (2023). *Censo Demográfico 2022: População e domicílios – "
        "primeiros resultados*. IBGE.",
        "Instituto Brasileiro de Geografia e Estatística. (2024). *Censo Demográfico 2022: Alfabetização – resultados do "
        "universo*. IBGE.",
        "Instituto Brasileiro de Geografia e Estatística. (2026a). *Índice Nacional de Preços ao Consumidor Amplo (IPCA): "
        "Tabela 1737* [Conjunto de dados]. SIDRA. https://sidra.ibge.gov.br/tabela/1737",
        "Instituto Brasileiro de Geografia e Estatística. (2026b). *Malha municipal 2025* [Conjunto de dados]. IBGE. "
        "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais.html",
        "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira. (2026a). *Censo Escolar da Educação "
        "Básica: Microdados 2015–2025* [Conjunto de dados]. Inep. "
        "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar",
        "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira. (2026b). *Índice de Desenvolvimento da "
        "Educação Básica (Ideb) 2025: Resultados* [Conjunto de dados]. Inep. "
        "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados",
        "Jackson, C. K., Johnson, R. C., & Persico, C. (2016). The effects of school spending on educational and economic "
        "outcomes: Evidence from school finance reforms. *The Quarterly Journal of Economics, 131*(1), 157–218. "
        "https://doi.org/10.1093/qje/qjv036",
        "Janssen, M., Charalabidis, Y., & Zuiderwijk, A. (2012). Benefits, adoption barriers and myths of open data and "
        "open government. *Information Systems Management, 29*(4), 258–268. https://doi.org/10.1080/10580530.2012.716740",
        "Lautharte, I., Oliveira, V. H., & Loureiro, A. (2021). *Incentives for mayors to improve learning: Evidence from "
        "state reforms in Ceará, Brazil* (Policy Research Working Paper No. 9509). World Bank. "
        "https://doi.org/10.1596/1813-9450-9509",
        "MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. In L. M. Le Cam "
        "& J. Neyman (Eds.), *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability* "
        "(Vol. 1, pp. 281–297). University of California Press.",
        "Moore, M. H. (1995). *Creating public value: Strategic management in government*. Harvard University Press.",
        "Programa das Nações Unidas para o Desenvolvimento, Fundação João Pinheiro, & Instituto de Pesquisa Econômica "
        "Aplicada. (2026). *Radar IDHM: Atlas do Desenvolvimento Humano no Brasil* [Conjunto de dados]. "
        "http://www.atlasbrasil.org.br [CONFERIR a autoria da edição usada]",
        "Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. "
        "*Journal of Computational and Applied Mathematics, 20*, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7",
        "Sackett, D. L., Rosenberg, W. M. C., Gray, J. A. M., Haynes, R. B., & Richardson, W. S. (1996). Evidence based "
        "medicine: What it is and what it isn’t. *BMJ, 312*(7023), 71–72. https://doi.org/10.1136/bmj.312.7023.71",
        "Secretaria do Tesouro Nacional. (2026). *Siconfi: Declaração de Contas Anuais (DCA), Anexo I-E* [Conjunto de "
        "dados]. https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca",
    ], key=ordem_apa)]]

APENDICE = [
    nota(AVISO.replace("vale para todo este capítulo", "vale para este apêndice")),
    corpo("O modelo de dados do painel segue o formato estrela: tabelas de dimensões, que descrevem municípios, UFs, anos, "
          "etapas, disciplinas e clusters, ligadas a tabelas de fatos, que guardam os valores. O Quadro A.1 lista as "
          "tabelas, e o Quadro A.2, os principais indicadores. O dicionário completo das colunas acompanha o pacote de "
          f"exportação do projeto (planilha, aba Dicionário), e o código está em {REPO}."),
    legenda("Quadro A.1 – Tabelas do modelo de dados do painel"),
    tabela(["Tabela", "Conteúdo", "Linhas"], [
        ["dim_ano", "Anos de 2017 a 2025, com a marca das edições do Saeb e o fator de correção pelo IPCA", "9"],
        ["dim_cluster", "Os sete clusters de contexto e o perfil de cada um", "7"],
        ["dim_defasagem", "Defasagem do gasto: mesmo ano e 1, 2 e 4 anos antes", "4"],
        ["dim_disciplina", "Matemática e Língua Portuguesa", "2"],
        ["dim_etapa", "Anos Iniciais, Anos Finais e Ensino Médio", "3"],
        ["dim_modelo", "As duas comparações do indicador: nacional e com o mesmo estado", "2"],
        ["dim_municipio", "Municípios, com UF, região, população, alfabetização, porte e cluster", "5.571"],
        ["dim_uf", "Unidades da Federação", "27"],
        ["fato_desempenho_municipal", "Por município, etapa, disciplina e edição: proficiência, gasto por aluno (do ano e "
         "defasado), controles, proficiência esperada, resíduo, percentil e alertas", "93.630"],
        ["fato_desempenho_estadual", "O mesmo por UF, para a rede estadual (Anos Finais e Ensino Médio), com as versões A "
         "e B do gasto", "540"],
        ["fato_gasto_municipal", "Gasto anual da rede municipal na subfunção 361, matrículas e gasto por aluno, 2017–2025",
         "50.113"],
        ["fato_gasto_estadual", "Gasto anual da rede estadual (versões A e B) e matrículas, 2017–2025", "243"],
        ["fato_oferta_municipal", "Matrículas das redes municipal e estadual por etapa, parcela da rede municipal e "
         "situação da nota", "100.278"],
        ["ref_municipio e cmp_municipio", "Listas de municípios calculadas no Power BI, para escolher a referência e o "
         "município comparado na página Pares", "—"],
        ["_Medidas", "As 85 medidas em DAX usadas pelos visuais", "—"],
    ], [2575, 5500, 1000]),
    fonte("Fonte: elaborado pelos autores."),
    legenda("Quadro A.2 – Principais indicadores do painel"),
    tabela(["Indicador", "Definição", "Unidade"], [
        ["Gasto por aluno", "Despesa paga da rede municipal na subfunção 361 (Ensino Fundamental), dividida pelas "
         "matrículas do Ensino Fundamental da rede municipal; na camada estadual, função 12 menos a subfunção 364, "
         "dividida pelas matrículas da educação básica da rede estadual", "R$ de 2025"],
        ["Proficiência", "Média da rede no Saeb, por etapa e disciplina", "Pontos"],
        ["Proficiência esperada", "Valor previsto por regressão com o gasto por aluno (em logaritmo) e o contexto da rede",
         "Pontos"],
        ["Desempenho vs. esperado", "Diferença entre a proficiência e a esperada, em percentual da esperada; no painel, \"vs. esperado\"", "%"],
        ["Percentil", "Posição da rede entre as da mesma etapa, disciplina e edição, pelo resultado em relação ao esperado",
         "0 a 100"],
        ["Faixa", "O percentil em cinco grupos, de bem abaixo a bem acima do esperado", "Categoria"],
        ["Pares", "Redes do mesmo cluster com gasto por aluno entre 0,8 e 1,25 vez o da rede de referência", "Contagem"],
        ["Atenção", "Alerta de salto atípico (variação entre edições mais de três desvios-padrão fora da média) ou de rede "
         "parcial (a rede municipal atende menos de 50% dos alunos públicos da etapa)", "Marca"],
        ["Cobertura do Saeb", "Parcela das redes municipais com nota divulgada pelo Inep", "%"],
        ["ρ de Spearman", "Correlação de postos entre o gasto por aluno e a proficiência, por edição e defasagem", "−1 a 1"],
    ], [1900, 5875, 1300]),
    fonte("Fonte: elaborado pelos autores."),
]

def titulo_apendice(texto: str) -> str:
    """Título de apêndice como o do rascunho: sem número, centralizado, em página nova."""
    return ('<w:p><w:pPr><w:pStyle w:val="Heading1"/><w:keepNext w:val="1"/><w:pageBreakBefore w:val="1"/>'
            '<w:spacing w:after="360" w:before="0" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="0"/>'
            '<w:jc w:val="center"/></w:pPr>' + run(texto, negrito=True) + "</w:p>")


# Apêndice B (2026-11-17, A22): o que saiu do corpo do texto para enxugá-lo, sem perder resultado
TELAS_AP = [(arq, leg) for arq, leg in TELAS if arq not in TELAS_TEXTO]
APENDICE_B = [
    titulo_apendice("APÊNDICE B – TELAS DO PAINEL E RESULTADOS COMPLEMENTARES"),
    corpo("Este apêndice reúne as telas do painel que não entram no texto (Figuras B.1 a B.7), o detalhe do agrupamento "
          "por contexto (Figuras B.8 e B.9), os coeficientes da heterogeneidade e da camada estadual (Tabelas B.1 e B.2) e "
          "as fichas dos três estudos de caso (Figuras B.10 a B.12)."),
    *[b for k, (arq, leg) in enumerate(TELAS_AP) for b in (
        figura(f"rIdTela{IDX_TELA[arq]}", 60 + IDX_TELA[arq], 16.0, 9.0, f"Tela {IDX_TELA[arq] + 1}"),
        fonte(f"Figura B.{k + 1} – {leg}. Fonte: painel elaborado pelos autores."))],
    figura("rIdClu1", 70, 16.0, 6.04, "Figura escolha de k"),
    fonte(f"Figura B.8 – Escolha do número de clusters: silhueta e inércia para k de 3 a 10. Fonte: elaborado pelos "
          "autores."),
    figura("rIdClu2", 71, 16.0, 6.70, "Figura perfil dos clusters"),
    fonte(f"Figura B.9 – Perfil dos clusters: média de cada variável de contexto, em desvios-padrão da média dos "
          "municípios, e composição por região. Fonte: elaborado pelos autores."),
    legenda("Tabela B.1 – Associação dentro do município, por grupo (Anos Iniciais)"),
    tabela(["Dimensão", "Grupo", "Matemática", "Português", "Municípios"], t_het, [1700, 3075, 1600, 1600, 1100]),
    fonte(FONTE_MUN + NOTA_COEF + " Especificação de referência, com uma inclinação por grupo. Faixa de gasto: quintil do gasto médio "
          "por aluno do município em 2017–2025 (Q1 = menor)."),
    legenda("Tabela B.2 – Camada estadual: gasto estadual por aluno e proficiência das redes estaduais"),
    tabela(["Especificação", "AF Matemática", "AF Português", "EM Matemática", "EM Português"], t_est, [2475, 1650, 1650, 1650, 1650]),
    fonte(FONTE_EST + NOTA_COEF + " 27 UFs (23 na versão B, que deixa de fora as UFs e anos sem a linha do Ensino Superior). Soma das subfunções: 122, 361, 362, 365, 366, 367 e 368. Erros agrupados por UF; valores-p e intervalos pela distribuição t com 26 graus de "
          "liberdade."),
    *[b for j, arq in enumerate(["caso_a_ficha", "caso_b_ficha", "caso_c_ficha"]) for b in fig_caso(arq, f"B.{10 + j}")],
]
APENDICE = APENDICE + APENDICE_B

SUBSTITUICOES = [  # (trecho do parágrafo do rascunho, blocos que o substituem)
    ("[CAPÍTULO RESERVADO. Redação sob responsabilidade de Henrique Lindoso", CAP4_ABERTURA),
    ("[A ser detalhado por Henrique Lindoso: ingestão, limpeza", CAP4_1),
    ("[A ser detalhado por Henrique Lindoso.]", CAP4_2),
    ("[A ser detalhado por Henrique Lindoso: telas interativas", CAP4_3),
    ("[INSERIR os apêndices (documentos elaborados pelos autores", APENDICE),
]

PAUSAS = [  # (trecho do parágrafo de pausa do rascunho, texto novo da nota)
    ("[CAPÍTULO EM PAUSA até a finalização do dashboard",
     "[Pausa retirada na cópia de 2026-11-13: o painel está concluído e as quatro seções deste capítulo têm material "
     "técnico. Divisão mantida: metodologia e números por Henrique Lindoso; interpretação e análise gerencial por "
     "Guilherme Menezes.]"),
    ("[Em pausa. Metodologia e gráficos por Henrique Lindoso",
     "[Metodologia e gráficos por Henrique Lindoso; interpretação por Guilherme Menezes.]"),
    ("[Em pausa. Análise gerencial por Guilherme Menezes.]", "[Análise gerencial por Guilherme Menezes.]"),
    ("[Em pausa. Análise por Guilherme Menezes.]", "[Análise por Guilherme Menezes.]"),
]

INSERCOES = [  # (trecho que identifica o parágrafo do rascunho, blocos a inserir depois dele)
    ("[INSERIR funcionalidades do dashboard deliberadamente deixadas de fora", FUTURO),
    ("[INSERIR melhorias de automação e atualização periódica de dados", AUTOMACAO),
    ("[Metodologia e gráficos por Henrique Lindoso; interpretação por Guilherme Menezes.]", CAP5_CLUSTER + CAP5_MODELOS + CAP5_CEBA),
    ("[Análise gerencial por Guilherme Menezes.]", CAP5_CASOS),
    ("[Análise por Guilherme Menezes.]", CAP5_VALIDACAO),
    ("AVISO. Como o Capítulo 5 está em pausa", [nota(
        "[ATENÇÃO: na cópia de 2026-11-13, o capítulo de resultados (hoje Capítulo 4) saiu da pausa e tem material técnico em todas as seções. Este aviso "
        "pode sair quando as lacunas abaixo forem preenchidas pelos autores.]")]),
    ("Ausência do IDH 2025.", [nota(
        "[Base factual: foi usado o IDHM por UF (dimensões Renda e Longevidade), do mesmo ano de cada edição do Saeb. A "
        "série termina em 2024, e por isso a edição de 2025 não tem esse controle. O índice só existe por UF, e não por "
        "município. Decisões C1 e C1b; limitação L4.]")]),
    ("Premissa de não correção inflacionária.", [nota(
        "[ATENÇÃO – divergência com o que foi feito: esta limitação NÃO se aplica. Todos os valores monetários foram "
        "corrigidos para reais de 2025 pelo IPCA médio anual, e a correção foi conferida de ponta a ponta "
        "(src/Testes/Conferir_Inflacao.py). Retirar este item e o item correspondente das perspectivas futuras.]")]),
    ("Outras limitações a avaliar.", [nota(
        "[Limitações registradas no projeto (docs/decisoes_metodo.md, seção 10), a selecionar pelos autores: o nível do "
        "gasto depende da fonte (L1); só entram redes com nota divulgada (L3); IDHM só por UF e até 2024 (L4); edição de "
        "2021 afetada pela pandemia (L5); valores extremos de gasto mantidos (L7); só 27 unidades na camada estadual (L8); "
        "defasagem de 4 anos só a partir de 2021 (L9); a despesa paga não inclui restos a pagar (L11); associação, e não "
        "causalidade (L12); o gasto municipal não separa Anos Iniciais e Finais e exclui a Educação Infantil (L13, L14); o "
        "indicador de desempenho em relação ao esperado é um resíduo e capta também gestão e contexto (L17); saltos atípicos de proficiência "
        "(L18); redes municipais parciais (L19).]")]),
    ("[INSERIR 2 a 4 conclusões gerenciais principais", [nota(
        "[Achados disponíveis para apoiar as conclusões (docs/nota_resultados.md): (1) a correlação simples entre gasto e "
        "nota existe, vem caindo e se explica em grande parte pelo contexto; (2) dentro do mesmo município, a associação é "
        "positiva, estável e pequena (+10% no gasto acompanha cerca de +0,2 ponto); (3) ela vem do gasto dos dois anos do "
        "ciclo do Saeb; (4) ela se concentra nos municípios pequenos e no Nordeste e no Norte; (5) na camada estadual, não é "
        "detectável com 27 UFs. Não escrever como efeito causal.]")]),
    ("[INSERIR: evidências sobre desigualdade regional de desempenho e de gasto por aluno", [nota(
        "[Números do projeto que podem servir aqui (redes municipais, Anos Iniciais, Matemática): o gasto mediano por aluno "
        "foi de R$ 9.202 (2017) a R$ 15.859 (2025), em reais de 2025; a proficiência média foi de 218,2 (2017) a 230,1 "
        "(2025), com queda para 211,8 em 2021. De 2023 a 2025, o gasto por aluno subiu, em média, cerca de 26% no Nordeste e 8% no Sudeste. Ver "
        "a Tabela 1, no Capítulo 4.]")]),
]

# ───────────────────────── montagem ─────────────────────────
x = DOC.read_text(encoding="utf-8")
import re
from xml.sax.saxutils import unescape


def achar_fim(xml: str, trecho: str) -> int:
    """Fim do último parágrafo cujo texto (somando os trechos <w:t>) contém o trecho; o texto pode estar partido."""
    achado = None
    for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        txt = unescape("".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", m.group(0), flags=re.S)))
        if trecho in txt:
            achado = m.end()
    assert achado is not None, f"trecho não encontrado: {trecho[:60]}"
    return achado


def texto_de(par: str) -> str:
    return unescape("".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", par, flags=re.S)))


def ilustracoes(blocos: list[str]) -> list[str]:
    """ABNT (NBR 14724): a identificação da figura vai acima dela, e a fonte (com eventual nota) abaixo. Os blocos são
    escritos como figura + "Figura N – título. [nota.] Fonte: ..."; aqui o título sobe e o resto fica embaixo."""
    out, i = [], 0
    while i < len(blocos):
        b = blocos[i]
        prox = texto_de(blocos[i + 1]) if i + 1 < len(blocos) else ""
        if "<w:drawing>" in b and prox.startswith("Figura "):
            tit, _, resto = prox.partition(". ")
            resto = resto if resto.startswith("Fonte:") else "Nota: " + resto
            # título e imagem no mesmo parágrafo, separados por quebra de linha: com parágrafos separados, o Word deixava
            # o título sozinho no pé da página mesmo com "manter com o próximo" (a imagem tem a largura do texto, 16 cm)
            tit_run = run(tit.rstrip("."), negrito=True) + "<w:r><w:br/></w:r>"
            b = b.replace('<w:spacing w:after="60" w:before="120"/><w:jc w:val="center"/></w:pPr>',
                          '<w:keepLines/><w:spacing w:after="60" w:before="240"/><w:jc w:val="left"/></w:pPr>' + tit_run, 1)
            assert tit_run in b, "parágrafo da figura com formato inesperado"
            out += [b, fonte(resto)]
            i += 2
            continue
        out.append(b)
        i += 1
    return out


SUBSTITUICOES = [(a, ilustracoes(b)) for a, b in SUBSTITUICOES]
INSERCOES = [(a, ilustracoes(b)) for a, b in INSERCOES]

for trecho, blocos in SUBSTITUICOES:  # troca o parágrafo-marcador do rascunho pelo conteúdo
    fim = achar_fim(x, trecho)
    ini = max(x.rfind("<w:p>", 0, fim), x.rfind("<w:p ", 0, fim))
    x = x[:ini] + "".join(blocos) + x[fim:]
assert x.count("[INSERIR TÍTULO DO APÊNDICE]") >= 1, "título do apêndice não encontrado num trecho só"
x = x.replace("[INSERIR TÍTULO DO APÊNDICE]", "DICIONÁRIO DE DADOS DO PAINEL")
# o marcador tinha realce amarelo: tira o realce só dos trechos (runs) com o título novo
x = re.sub(r"<w:r[ >](?:(?!</w:r>).)*?DICIONÁRIO DE DADOS DO PAINEL(?:(?!</w:r>).)*?</w:r>",
           lambda m: re.sub(r"<w:highlight [^>]*/>", "", m.group(0)), x, flags=re.S)

# referências: a nota de norma e a lista antiga do rascunho dão lugar à lista final, até o título do apêndice
fim_norma = achar_fim(x, "[NORMA DE REFERÊNCIAS:")
ini_norma = max(x.rfind("<w:p>", 0, fim_norma), x.rfind("<w:p ", 0, fim_norma))
ap = x.index("DICIONÁRIO DE DADOS DO PAINEL", ini_norma)
ini_ap = max(x.rfind("<w:p>", 0, ap), x.rfind("<w:p ", 0, ap))
assert x.count("Sackett", ini_norma, ini_ap) == 1 and "Heading1" in x[ini_ap:ap], "lista antiga não encontrada"
x = x[:ini_norma] + "".join(REFERENCIAS) + x[ini_ap:]

for trecho, novo in PAUSAS:  # troca o parágrafo de pausa inteiro por uma nota com o texto novo
    fim = achar_fim(x, trecho)
    ini = max(x.rfind("<w:p>", 0, fim), x.rfind("<w:p ", 0, fim))
    x = x[:ini] + nota(novo) + x[fim:]

for trecho, blocos in INSERCOES:
    fim = achar_fim(x, trecho)
    x = x[:fim] + "".join(blocos) + x[fim:]

for ns, uri in [("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
                ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")]:
    cab = x[:x.index(">", x.index("<w:document")) + 1]
    if f"xmlns:{ns}=" not in cab:
        x = x.replace("<w:document ", f'<w:document xmlns:{ns}="{uri}" ', 1)
# ───────────────────────── formato científico (decisão D1, 2026-11-17) ─────────────────────────
TITULOS_D1 = [  # (título do rascunho, título no formato de método científico); vale no texto e no sumário digitado
    ("FUNDAMENTAÇÃO TEÓRICA E INSTRUMENTOS", "REVISÃO BIBLIOGRÁFICA"),
    ("SOLUÇÃO (PRODUTO ANALÍTICO E DESENVOLVIMENTO)", "MÉTODO"),
    ("ANÁLISE E DISCUSSÃO DOS RESULTADOS", "RESULTADOS E DISCUSSÃO"),
    ("CONCLUSÕES E LIMITAÇÕES", "CONCLUSÕES, LIMITAÇÕES E SUGESTÕES DE PESQUISA FUTURA"),
    ("Aplicação prática por análise de cluster", "Agrupamento dos municípios por contexto"),
    ("Protótipo do dashboard de Business Intelligence", "Painel de Business Intelligence"),
    ("Perspectivas futuras e trabalhos futuros", "Sugestões de pesquisa futura"),
    ("Eficiência alocativa", "Eficiência do gasto e desempenho em relação ao esperado"),
]
for antigo, novo in TITULOS_D1:
    x, n = re.subn(r"(<w:t(?: [^>]*)?>)" + re.escape(antigo) + r"(</w:t>)", lambda m: m.group(1) + novo + m.group(2), x)
    assert n >= 1, f"título não encontrado: {antigo}"


# ───────────────────────── revisão bibliográfica (A24, 2026-11-17) ─────────────────────────
NOTA_REVISAO = nota(
    "[REVISÃO BIBLIOGRÁFICA escrita com o auxílio da IA em 2026-11-17 (registro A24), a partir do levantamento em "
    "docs/levantamento_bibliografico.md. Os achados de cada obra foram resumidos a partir dos resumos e registros "
    "conferidos; antes da versão final, os autores devem ler os textos e confirmar cada paráfrase, como diz a seção 3.4. "
    "Os dispositivos legais de 2.1 foram conferidos no texto da Lei nº 14.113/2020 e da EC nº 108/2020.]")
REV_214 = [
    corpo("Em sentido econômico, eficiência é a relação entre os resultados obtidos e os recursos empregados: uma unidade "
          "é eficiente quando não consegue obter mais resultado com os mesmos recursos, ou o mesmo resultado com menos. Na "
          "educação, os estudos de eficiência do gasto municipal costumam usar métodos de fronteira, como a análise "
          "envoltória de dados, que comparam cada município com os de melhor desempenho para o mesmo insumo e atribuem 100% "
          "aos que estão na fronteira (Faria et al., 2008)."),
    corpo("Este trabalho usa um conceito mais restrito, o desempenho em relação ao esperado: a diferença entre a "
          "proficiência de uma rede e a proficiência esperada para redes com o mesmo gasto por aluno e o mesmo contexto, "
          "estimada por regressão. A ideia se aproxima da defesa de indicadores que levam em conta o contexto escolar, já "
          "que o perfil dos alunos e as condições das escolas se associam ao Ideb e não podem ser ignorados na sua leitura "
          "(Alves & Soares, 2013). O indicador não mede eficiência no sentido estrito, porque o gasto pesa pouco na "
          "proficiência esperada (Capítulo 3), e não permite afirmar que o gasto cause o resultado: ele aponta redes que se "
          "afastam do padrão de redes comparáveis, cujos motivos precisam ser investigados."),
]
REV_22 = [
    NOTA_REVISAO,
    corpo("Esta seção reúne a literatura com que os resultados do trabalho dialogam, em quatro frentes: a relação entre "
          "gasto e desempenho escolar, os efeitos dos fundos de financiamento da educação básica, as medidas de desempenho "
          "e o papel do contexto, e as políticas de incentivo a resultados. A última parte resume a lacuna em que o "
          "trabalho se posiciona."),
    titulo(3, "Gasto e desempenho escolar"),
    corpo("A relação entre recursos e resultados escolares é um dos debates mais antigos da economia da educação. Revisões "
          "da evidência norte-americana e internacional concluíram que políticas baseadas apenas no aumento de insumos, "
          "como mais recursos por aluno ou turmas menores, têm efeitos pequenos e pouco consistentes sobre o desempenho, e "
          "que os incentivos e a forma de uso dos recursos importam mais (Hanushek, 1997, 2003)."),
    corpo("Estudos mais recentes, que aproveitam mudanças nas regras de financiamento como fonte de variação do gasto "
          "externa às decisões das redes, encontraram efeitos positivos. Nos Estados Unidos, aumentos do gasto por aluno "
          "decorrentes de reformas do financiamento escolar elevaram a escolaridade e os salários futuros, sobretudo de "
          "crianças de baixa renda (Jackson et al., 2016). Uma meta-análise de 31 avaliações estimou que US$ 1.000 a mais "
          "por aluno, durante quatro anos, elevam as notas em cerca de 0,03 desvio-padrão, com efeitos maiores para "
          "populações mais pobres (Jackson & Mackevicius, 2024)."),
    corpo("No Brasil, a evidência entre municípios aponta associação pequena. Com dados do gasto municipal no Ensino "
          "Fundamental e das notas da Prova Brasil, Menezes-Filho e Amaral (2009) encontraram efeito muito pequeno e, na "
          "maioria das especificações, não significativo, presente apenas entre os municípios de notas mais altas. Oliveira "
          "et al. (2022) mostraram que indicadores de qualidade da gestão municipal se associam às notas mesmo depois de "
          "controlar o gasto e as características fixas de cada município, o que sugere que a gestão explica parte das "
          "diferenças que o gasto não explica. Já Alves e Frio (2022), com um painel de municípios de 2011 a 2017 e um "
          "modelo de fronteira estocástica, encontraram associação positiva entre o Ideb e o gasto por aluno de quatro anos "
          "antes."),
    corpo("Esses estudos ajudam a ler os resultados do Capítulo 4. A associação entre municípios é quase nula quando se "
          "controla o contexto, mas aparece, pequena, quando cada município é comparado com ele mesmo ao longo do tempo. A "
          "diferença em relação a Alves e Frio (2022) quanto ao gasto defasado decorre, ao menos em parte, do método: o "
          "modelo deste trabalho compara cada município com ele mesmo, o que o modelo de fronteira daquele estudo não faz."),
    titulo(3, "Financiamento e equidade: Fundef e Fundeb"),
    corpo("O Fundef, antecessor do Fundeb, elevou o salário relativo dos professores da rede pública, com efeito positivo "
          "sobre a proficiência dos alunos (Menezes-Filho & Pazello, 2007), e aumentou a frequência escolar e reduziu a "
          "distorção idade-série, sobretudo entre as crianças de nível socioeconômico mais baixo (Cruz & Rocha, 2018). Os "
          "efeitos sobre o fluxo escolar não aparecem numa medida de proficiência como a usada neste trabalho."),
    corpo("Quanto ao Fundeb, simulações contrafactuais indicam que o fundo reduz muito a desigualdade de gasto por aluno "
          "entre municípios, mas muda pouco os indicadores de qualidade (Hirata et al., 2022). Com dados de 2008 a 2019 do "
          "Censo Escolar, do SIOPE e do Siconfi, as mesmas fontes de gasto deste trabalho, Silva Júnior et al. (2025) "
          "concluíram que o Fundeb não aprofundou nem reduziu a desigualdade educacional entre as regiões, e que o gasto por "
          "aluno foi o fator positivo mais consistente. O Novo Fundeb, com a complementação-VAAT, passou a dirigir "
          "recursos às redes de menor capacidade de financiamento. Não foi localizada avaliação com dados observados que "
          "isole esse efeito; o Capítulo 4 descreve um padrão de 2023 a 2025 compatível com ele, sem testá-lo."),
    titulo(3, "Medidas de desempenho e contexto"),
    corpo("O Ideb combina a proficiência no Saeb com a taxa de aprovação. Soares e Xavier (2013) examinaram os pressupostos "
          "educacionais e estatísticos do índice e a forma como ele define qualidade, e propuseram aperfeiçoamentos. Por "
          "isso, este trabalho usa como medida principal a proficiência em pontos, por etapa e disciplina, e não o Ideb "
          "(Capítulo 3)."),
    corpo("Alves e Soares (2013) mostraram que o perfil socioeconômico dos alunos, a infraestrutura e a complexidade das "
          "escolas se associam ao Ideb, de modo que comparar redes sem considerar o contexto penaliza as que atendem "
          "populações mais vulneráveis. Esse argumento sustenta os controles de contexto do indicador e a comparação entre "
          "redes de um mesmo grupo de contexto. Na literatura de eficiência, Faria et al. (2008) aplicaram a análise "
          "envoltória de dados aos municípios do Rio de Janeiro, com o gasto per capita em saúde e educação como insumo; "
          "como discutido em 2.1.4, esse tipo de método mede a distância até a fronteira de melhores práticas, e não até o "
          "resultado esperado para redes comparáveis."),
    titulo(3, "Incentivos a resultados: o caso do Ceará"),
    corpo("Uma explicação documentada para as diferenças entre estados com gasto semelhante vem das políticas de "
          "incentivo. O Ceará distribui parte da cota municipal do ICMS segundo resultados educacionais e oferece "
          "assistência técnica às redes municipais; Lautharte et al. (2021) estimaram que essa política elevou as notas do "
          "9º ano em cerca de 0,15 desvio-padrão, e que o efeito dobra com a assistência técnica."),
    corpo("A Emenda Constitucional nº 108/2020 estendeu esse desenho ao país, ao determinar que parte da cota municipal do "
          "ICMS seja distribuída com base em indicadores de melhoria nos resultados de aprendizagem e de aumento da equidade "
          "(Brasil, 2020a). Incentivos ligados a indicadores podem, porém, produzir variações bruscas de resultado, o que "
          "justifica tratá-las com cautela, como faz a marca de saltos atípicos do painel, sem supor irregularidade."),
    titulo(3, "Síntese e lacuna"),
    corpo("Em síntese, a literatura indica que o gasto, sozinho, explica pouco do desempenho entre redes; que o efeito "
          "aparece quando se isola a variação do gasto, é maior para populações mais pobres e depende de como os recursos "
          "são usados; e que comparações justas entre redes precisam considerar o contexto. Do lado da gestão, a "
          "disponibilidade de dados públicos não garante o seu uso para decisão (Heald, 2006; Janssen et al., 2012), e "
          "painéis de apoio à decisão precisam reunir as informações mais importantes de forma que possam ser lidas de "
          "relance (Few, 2006)."),
    corpo("A lacuna em que o trabalho se posiciona é a combinação dessas duas frentes: uma ferramenta pública, de "
          "abrangência nacional, que estime a associação entre gasto e desempenho com dados recentes, de 2017 a 2025, e que "
          "permita ao gestor comparar a própria rede com redes de contexto e gasto parecidos, identificando as que entregam "
          "mais ou menos do que o esperado."),
]
REV_23 = [
    corpo("As bases públicas usadas no trabalho estão resumidas no Quadro 1; o Quadro 2, no Capítulo 3, detalha o período "
          "e o uso de cada uma."),
    legenda("Quadro 1 – Bases oficiais utilizadas"),
    tabela(["Base", "Órgão responsável", "O que é"], [
        ["SIOPE", "FNDE/MEC", "Sistema em que estados e municípios declaram receitas e despesas em educação; base do "
         "acompanhamento da MDE e do Fundeb"],
        ["Siconfi", "Secretaria do Tesouro Nacional", "Sistema das declarações contábeis e fiscais dos entes federados, "
         "como a Declaração de Contas Anuais"],
        ["Saeb", "Inep/MEC", "Avaliação bienal da proficiência em Língua Portuguesa e Matemática, aplicada às escolas "
         "públicas com número mínimo de estudantes nas etapas avaliadas"],
        ["Ideb", "Inep/MEC", "Indicador que combina a proficiência no Saeb e a taxa de aprovação"],
        ["Censo Escolar", "Inep/MEC", "Levantamento anual de matrículas, docentes e infraestrutura das escolas"],
        ["Censo Demográfico, IPCA e malha municipal", "IBGE", "População e alfabetização (2022), índice de preços usado "
         "na correção monetária e contornos dos municípios"],
        ["IDHM", "PNUD, Ipea e Fundação João Pinheiro", "Índice de desenvolvimento humano nas dimensões renda, "
         "longevidade e educação, usado por UF"],
    ], [2000, 2275, 4800]),
    fonte("Fonte: elaborado pelos autores, com base em Fundo Nacional de Desenvolvimento da Educação [FNDE] (2026), "
          "Secretaria do Tesouro Nacional (2026), Inep (2026a, 2026b), Instituto Brasileiro de Geografia e Estatística "
          "[IBGE] (2023, 2024, 2026a, 2026b) e Programa das Nações Unidas para o Desenvolvimento [PNUD] et al. (2026)."),
    corpo("O Exame Nacional do Ensino Médio (ENEM) e o Programa Internacional de Avaliação de Estudantes (PISA) foram "
          "descartados como medida de desempenho. O ENEM é de adesão voluntária e inclui alunos de escolas privadas; nos "
          "microdados públicos analisados pelos autores, só de 15,6% a 27,4% dos inscritos têm escola e município "
          "identificados. O PISA é amostral e não produz resultados por município. O Saeb, por sua vez, é aplicado às "
          "escolas públicas e tem resultados por município e por rede."),
]
LEI_21 = [  # parágrafos de 2.1 com os dispositivos conferidos na lei (marcas [CONFERIR] resolvidas)
    ("A vinculação constitucional de receitas à educação",
     "A vinculação constitucional de receitas à educação determina que a União aplique anualmente, no mínimo, 18%, e que "
     "estados, Distrito Federal e municípios apliquem, no mínimo, 25% da receita de impostos, compreendidas as "
     "transferências, na manutenção e desenvolvimento do ensino (Brasil, 1988, art. 212). A Lei de Diretrizes e Bases da "
     "Educação Nacional define o que se considera e o que não se considera despesa de MDE (Brasil, 1996, arts. 70 e 71), o "
     "que condiciona a margem de discricionariedade do gestor."),
    ("O Fundeb é um fundo de natureza contábil",
     "O Fundeb é um fundo de natureza contábil, de âmbito estadual (um por estado e um no Distrito Federal), composto por "
     "parcela das receitas de impostos e transferências de estados e municípios. Foi tornado permanente pela Emenda "
     "Constitucional nº 108/2020, regulamentada pela Lei nº 14.113/2020 e alterada pela Lei nº 14.276/2021 (Brasil, "
     "2020a, 2020b, 2021)."),
    ("A União complementa o fundo com",
     "A União complementa o fundo com, no mínimo, 23% do total de recursos, em implantação gradual de 2021 a 2026, de 12% "
     "no primeiro ano a 23% no sexto, distribuídos em três modalidades (Brasil, 2020b, arts. 5º e 41):"),
    ("o VAAT (Valor Anual Total por Aluno)",
     "o VAAT (Valor Anual Total por Aluno) corresponde a, no mínimo, 10,5 pontos percentuais e é distribuído por rede de "
     "ensino, com base na capacidade total de financiamento por aluno, considerando outras receitas vinculadas à educação, "
     "o que aprofunda a equalização entre redes, inclusive dentro de um mesmo estado. Metade desses recursos vai à educação "
     "infantil, e ao menos 15% devem ser aplicados em despesas de capital (Brasil, 2020b, arts. 27 e 28);"),
    ("o VAAR (Valor Anual por Aluno por Resultado)",
     "o VAAR (Valor Anual por Aluno por Resultado) corresponde a 2,5 pontos percentuais e é distribuído às redes que "
     "cumprirem condicionalidades de gestão e apresentarem melhoria de indicadores de atendimento e de aprendizagem, com "
     "redução das desigualdades. As condicionalidades incluem a escolha de diretores por critérios de mérito e desempenho "
     "ou com participação da comunidade, a participação de ao menos 80% dos estudantes nas avaliações nacionais, a redução "
     "das desigualdades educacionais socioeconômicas e raciais, o regime de colaboração entre estado e municípios e "
     "referenciais curriculares alinhados à Base Nacional Comum Curricular (Brasil, 2020b, art. 14)."),
    ("Quanto à aplicação, no mínimo 70%",
     "Quanto à aplicação, no mínimo 70% dos recursos anuais totais do Fundeb, excluída a complementação-VAAR, devem ser "
     "destinados à remuneração dos profissionais da educação básica em efetivo exercício (Brasil, 2020b, art. 26). O "
     "restante pode ser aplicado em outras ações de MDE na educação básica pública, observadas as vinculações da "
     "complementação-VAAT. É essa fração, por vezes chamada de “30% flexível”, que concentra a maior parte da margem de "
     "decisão alocativa associada ao fundo, embora continue sujeita às regras de MDE."),
    ("A Emenda Constitucional nº 108/2020 também inscreveu",
     "A Emenda Constitucional nº 108/2020 também inscreveu na Constituição o Custo Aluno-Qualidade (CAQ) como referência "
     "do padrão mínimo de qualidade, a ser pactuado em regime de colaboração na forma de lei complementar (Brasil, 2020a; "
     "Brasil, 1988, art. 211, § 7º). O trabalho não usa o CAQ, porque compara o gasto observado das redes, e não um padrão "
     "de custo."),
]


# ───────────────────────── antigo Capítulo 3 remanejado (D1, A23, 2026-11-17) ─────────────────────────
def paragrafos(xml: str):
    tbs = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S)]
    return [m for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, flags=re.S) if not any(a <= m.start() < b for a, b in tbs)]


def achar_par(xml: str, inicio: str, h1: bool = False, pre: bool = False) -> re.Match:
    pars = paragrafos(xml)
    intro = [m.start() for m in pars if '"Heading1"' in m.group(0) and texto_de(m.group(0)).strip() == "INTRODUÇÃO"][-1]
    achados = [m for m in pars if texto_de(m.group(0)).strip().startswith(inicio)
               and (not h1 or '"Heading1"' in m.group(0)) and (h1 or (m.start() < intro if pre else m.start() > intro))]  # corpo do texto, ou pré-textuais
    achados = achados[-1:] if h1 else achados  # o sumário digitado repete os títulos; vale o último
    assert len(achados) == 1, f"parágrafo não encontrado ou repetido: {inicio[:50]} ({len(achados)})"
    return achados[0]


def reescrever(xml: str, inicio: str, novo: str, pre: bool = False) -> str:
    """Troca o texto de um parágrafo do rascunho, mantendo o formato dele; **trecho** sai em negrito."""
    m = achar_par(xml, inicio, pre=pre)
    par = m.group(0)
    ppr = (re.search(r"<w:pPr>.*?</w:pPr>", par, flags=re.S) or [""])[0] if "<w:pPr>" in par else ""
    rpr = re.search(r"<w:r[ >].*?(<w:rPr>.*?</w:rPr>)", par, flags=re.S)
    rpr = re.sub(r"<w:highlight [^>]*/>|<w:b(?:Cs)? [^>]*/>|<w:b(?:Cs)?/>|<w:i(?:Cs)? [^>]*/>|<w:i(?:Cs)?/>", "",
                 rpr.group(1)) if rpr else ""
    runs = ""
    for k, s in enumerate(novo.split("**")):
        for pedaco in re.split(r"(\[[^\]]*\])", s):
            if not pedaco:
                continue
            r = rpr.replace("<w:rPr>", "<w:rPr><w:b/><w:bCs/>", 1) if k % 2 and rpr else rpr
            if re.match(r"\[[A-ZÇÃÉÍ]{5,}", pedaco) and r:  # marcação ([CONFERIR...]); siglas como [Inep] não
                r = r.replace("</w:rPr>", '<w:highlight w:val="yellow"/></w:rPr>')
            runs += f'<w:r>{r}<w:t xml:space="preserve">{escape(pedaco)}</w:t></w:r>'
    return xml[:m.start()] + "<w:p>" + ppr + runs + "</w:p>" + xml[m.end():]


def inserir_depois(xml: str, inicio: str, blocos: list[str]) -> str:
    m = achar_par(xml, inicio)
    return xml[:m.end()] + "".join(blocos) + xml[m.end():]


def apagar_trecho(xml: str, ini_h: str, fim_h: str, nivel: str) -> str:
    """Apaga do título ini_h (inclusive) até o título fim_h (exclusive)."""
    a = [m for m in paragrafos(xml) if f'"{nivel}"' in m.group(0) and texto_de(m.group(0)).strip() == ini_h][-1]
    b = [m for m in paragrafos(xml) if '"Heading' in m.group(0) and texto_de(m.group(0)).strip() == fim_h
         and m.start() > a.start()][0]
    assert "<w:sectPr" not in xml[a.start():b.start()], "quebra de seção dentro do trecho apagado"
    return xml[:a.start()] + xml[b.start():]


x = apagar_trecho(x, "DIAGNÓSTICO DA SITUAÇÃO ATUAL", "MÉTODO", "Heading1")
x = apagar_trecho(x, "Instrumentos e estruturas de diagnóstico", "Trabalhos semelhantes e literatura correlata", "Heading2")


def substituir_intervalo(xml: str, inicio: str, ultimo: str, blocos: list[str]) -> str:
    """Troca, no corpo do texto, do parágrafo que começa com `inicio` até o que começa com `ultimo` (inclusive)."""
    a, b = achar_par(xml, inicio), achar_par(xml, ultimo)
    assert a.start() <= b.start()
    return xml[:a.start()] + "".join(blocos) + xml[b.end():]


x = substituir_intervalo(x, "[DEFINIR o conceito operacional", "[DEFINIR o conceito operacional", REV_214)
x = substituir_intervalo(x, "AVISO – SEÇÃO PENDENTE DE PESQUISA", "[SÍNTESE E LACUNA", REV_22)
x = substituir_intervalo(x, "O trabalho utiliza bases públicas de cinco origens", "[INSERIR parágrafo explicando por que o ENEM", REV_23)
for inicio, novo in LEI_21:
    x = reescrever(x, inicio, novo)
# o sumário digitado (com o antigo Capítulo 3) será refeito no Word: ver docs/revisao_formatacao.md

x = reescrever(x, "Os dados necessários para conectar essas duas agendas",
    "Os dados necessários para conectar essas duas agendas estão publicados em sistemas distintos, mantidos por órgãos "
    "diferentes e com lógicas próprias. Os dados orçamentários e contábeis estão no Sistema de Informações sobre "
    "Orçamentos Públicos em Educação (SIOPE) e no Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro "
    "(SICONFI), do Tesouro Nacional. Os dados de proficiência e fluxo estão no Sistema de Avaliação da Educação Básica "
    "(Saeb) e no Índice de Desenvolvimento da Educação Básica (Ideb), e os de infraestrutura, matrículas e docentes, no "
    "Censo Escolar, todos do Inep. A fragmentação entre dados financeiros e dados pedagógicos e estruturais dificulta a "
    "visão sistêmica do gestor e a identificação de redes que precisam de apoio.")
x = inserir_depois(x, "Os dados necessários para conectar essas duas agendas", [
    corpo("O país dispõe de uma infraestrutura relevante de transparência e de dados abertos, amparada pela Lei de "
          "Responsabilidade Fiscal (Brasil, 2000), pela Lei de Acesso à Informação (Brasil, 2011) e pela política de dados "
          "abertos do Poder Executivo federal (Brasil, 2016). Divulgar os dados, porém, não equivale a torná-los úteis "
          "para a decisão (Heald, 2006; Janssen et al., 2012). Na educação, os portais orçamentários, como o Tesouro "
          "Transparente e a consulta pública do SIOPE, orientam-se à prestação de contas e ao cumprimento de limites "
          "legais, enquanto os painéis do Inep apresentam resultados de aprendizagem, fluxo e infraestrutura. São escassos os "
          "portais que permitem comparar, rede a rede, o gasto por aluno com o desempenho, e mais raros ainda os que levam "
          "em conta o contexto em que cada rede atua."),
    corpo("A integração feita neste trabalho ilustra as barreiras práticas a esse cruzamento. As bases vêm em formatos "
          "diferentes, de interfaces de programação (SIOPE e SICONFI) a planilhas (resultados do Ideb) e microdados (Censo "
          "Escolar); têm periodicidades distintas, com gasto anual e avaliação bienal; e são publicadas com defasagens "
          "diferentes, como o IDHM, cuja série disponível termina em 2024. O Capítulo 3 descreve como essas diferenças "
          "foram tratadas."),
    corpo("Daí decorre a lacuna que motiva o trabalho: os dados para avaliar se o gasto se converte em aprendizagem "
          "existem e são públicos, mas não estão integrados de forma que o gestor possa comparar a própria rede com redes "
          "em condições parecidas, nem há consenso sobre o quanto o gasto, por si só, se associa ao desempenho."),
])
x = inserir_depois(x, "Quanto à aplicação, no mínimo 70% dos recursos", [
    corpo("Essa margem é onde o gestor tem mais espaço para alocar recursos com foco na aprendizagem e na equidade entre "
          "escolas e regiões da rede. Ao mesmo tempo, a complementação-VAAR liga parte dos repasses à melhoria de "
          "indicadores de atendimento e de aprendizagem (Brasil, 2020b), o que torna relevante acompanhar, ao longo do "
          "tempo, a posição da rede em relação a redes comparáveis. Este trabalho não monitora as condicionalidades do "
          "VAAR, mas o indicador de desempenho em relação ao esperado, descrito no Capítulo 3, informa essa posição relativa."),
])
x = reescrever(x, "De que maneira a integração de dados orçamentários",
    "O gasto público por aluno se associa ao desempenho das redes públicas de ensino no Saeb e, considerando o gasto e o "
    "contexto de cada rede, quais redes entregam mais ou menos do que o esperado?")
x = reescrever(x, "O Manual de TCC da FEA/USP estabelece que trabalhos de consultoria",
    "No formato de método científico, os objetivos são de descoberta: buscam reduzir uma lacuna de conhecimento, e não "
    "alterar uma realidade administrativa específica (Departamento de Administração FEA/USP, 2025). Assim, definem-se os "
    "objetivos a seguir.")
x = reescrever(x, "Objetivo geral: estruturar",
    "**Objetivo geral:** analisar a associação entre o gasto público por aluno e o desempenho das redes públicas de ensino no "
    "Saeb, de 2017 a 2025, e identificar as redes que entregam mais ou menos do que o esperado para o seu gasto e o seu "
    "contexto.")
for antigo, novo in [
    ("diagnosticar a fragmentação informacional", "integrar, em painéis de dados municipal e estadual, bases públicas de "
     "gasto (SIOPE e SICONFI), de desempenho (Saeb), de oferta (Censo Escolar) e de contexto (IBGE e IDHM);"),
    ("integrar, em uma única camada analítica", "estimar a associação entre o gasto por aluno e a proficiência, entre "
     "municípios e dentro do mesmo município, com o gasto do ano da prova e de anos anteriores;"),
    ("projetar visualizações interativas", "construir um indicador de desempenho em relação ao esperado e um painel de "
     "Business Intelligence que permita comparar redes de contexto e gasto parecidos;"),
    ("demonstrar, por simulação de cenários", "aplicar o painel à comparação entre as redes municipais do Ceará e da "
     "Bahia e a três estudos de caso.")]:
    x = reescrever(x, antigo, novo)
x = reescrever(x, "Contribuição prática.",
    "**Contribuição prática.** O trabalho entrega um painel que reúne, numa só interface, o que hoje o gestor precisa "
    "consultar em portais separados, e que compara cada rede com redes de contexto e gasto parecidos. Diferencia-se dos "
    "portais existentes, que tendem a apresentar o cumprimento de limites fiscais ou os resultados de aprendizagem de "
    "forma isolada (ver 1.2).")
x = reescrever(x, "O trabalho organiza-se em seis capítulos.",
    "O trabalho organiza-se em cinco capítulos. Este primeiro capítulo apresenta o contexto, o problema, a pergunta e os "
    "objetivos. O Capítulo 2 reúne a revisão bibliográfica e a caracterização das bases oficiais. O Capítulo 3 descreve o "
    "método: as fontes e a integração dos dados, as regras de tratamento, o painel e o uso de inteligência artificial. O "
    "Capítulo 4 apresenta e discute os resultados: o agrupamento dos municípios por contexto, a associação entre gasto e "
    "desempenho, a comparação entre Ceará e Bahia, os estudos de caso e a validação do painel. O Capítulo 5 traz as "
    "conclusões, as limitações e as sugestões de pesquisa futura.")
# remissões que mudam com a saída do antigo Capítulo 3 (e do item 2.2) em marcações do rascunho
x = reescrever(x, "Contribuição teórica.",
    "**Contribuição teórica.** O trabalho aproxima as literaturas de gestão pública baseada em evidências, de dados "
    "abertos e de análise de dados para decisão (analytics) de um problema concreto de administração pública "
    "educacional, descrevendo um modelo replicável de integração entre bases públicas. [REFINAR após a revisão "
    "bibliográfica adicional do item 2.2: a contribuição teórica só deve ser afirmada com base em lacuna efetivamente "
    "demonstrada.]")
x = reescrever(x, "AVISO. Como o Capítulo 5 está em pausa",
    "AVISO. As conclusões abaixo estão estruturadas como lacunas, a preencher com os resultados do Capítulo 4. Nenhum "
    "resultado foi presumido.")
x = reescrever(x, "O trabalho partiu da pergunta:",
    "O trabalho partiu da pergunta: o gasto público por aluno se associa ao desempenho das redes públicas de ensino no "
    "Saeb e, considerando o gasto e o contexto de cada rede, quais redes entregam mais ou menos do que o esperado? "
    "[RESPONDER DIRETAMENTE, em um parágrafo, com base em: (i) a associação entre gasto e desempenho (seção 4.2); (ii) as "
    "redes acima e abaixo do esperado, com Ceará e Bahia e os estudos de caso (seções 4.3 e 4.4); (iii) o que o painel "
    "entrega e como foi validado (seções 3.3 e 4.5).]")
x = reescrever(x, "[INSERIR 2 a 4 conclusões gerenciais principais",
    "[INSERIR 2 a 4 conclusões principais, com base nos resultados do Capítulo 4.]")
x = reescrever(x, "Teóricas. [DETALHAR",
    "**Teóricas.** [DETALHAR: contribuição à literatura de administração pública e gestão baseada em evidências, "
    "vinculada à lacuna demonstrada no item 2.2. Evitar contribuições não sustentadas pela revisão da literatura.]")
x = reescrever(x, "Natureza declaratória dos dados orçamentários.",
    "**Natureza declaratória dos dados orçamentários.** Os dados do SIOPE e de sistemas correlatos são informados pelos "
    "próprios entes federados, o que sujeita as informações a inconsistências, atrasos, erros de classificação e eventuais "
    "revisões posteriores [CONFERIR nas normas do FNDE o grau de validação e conferência aplicado aos dados]. [DESCREVER o "
    "tratamento adotado, em coerência com o Capítulo 3.]")


def depois_do_titulo(xml: str, titulo_h1: str, blocos: list[str]) -> str:
    for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        if '"Heading1"' in m.group(0) and texto_de(m.group(0)) == titulo_h1:
            return xml[:m.end()] + "".join(blocos) + xml[m.end():]
    raise AssertionError(f"capítulo não encontrado: {titulo_h1}")


x = depois_do_titulo(x, "INTRODUÇÃO", [nota(
    "[REORGANIZAÇÃO PARA O FORMATO CIENTÍFICO (2026-11-17, decisões D1 e A23), feita com o auxílio da IA. O antigo Capítulo "
    "3 (Diagnóstico) foi remanejado: a fragmentação da informação e as barreiras ao cruzamento dos dados entraram em 1.2; "
    "a margem de decisão do gestor e o VAAR, em 2.1.2; a justificativa do Business Intelligence e o público-alvo, em 3.3. "
    "Saíram a oportunidade de consultoria, o Quadro 2 (portais, que estava vazio), o antigo item 2.2 (instrumentos de "
    "diagnóstico) e o escopo que incluía a Educação Infantil. Foram reescritos a pergunta, os objetivos, a contribuição "
    "prática e a estrutura do trabalho. Guilherme: revisar e ajustar à sua redação.]")])

# ───────────────────────── conclusões, resumo e abstract (A25, 2026-11-18) ─────────────────────────
def alinea(letra: str, texto: str) -> str:
    """Alínea no padrão da ABNT: letra minúscula seguida de parêntese, recuo deslocado."""
    return ('<w:p><w:pPr><w:spacing w:after="60" w:before="0" w:line="360" w:lineRule="auto"/>'
            '<w:ind w:left="1134" w:right="0" w:hanging="425"/><w:jc w:val="both"/></w:pPr>'
            + run(f"{letra}) " + texto) + "</w:p>")


def alineas(textos: list[str]) -> list[str]:
    return [alinea("abcdefghij"[k], s) for k, s in enumerate(textos)]


CAP_CONCLUSOES = [
    nota("[CONCLUSÕES escritas com o auxílio da IA em 2026-11-18 (registro A25), a partir dos resultados do Capítulo 4 e "
         "das notas de base factual do rascunho. Os autores devem revisá-las e reescrevê-las com as próprias palavras.]"),
    titulo(2, "Conclusões"),
    corpo("O trabalho partiu da pergunta: o gasto público por aluno se associa ao desempenho das redes públicas de ensino "
          "no Saeb e, considerando o gasto e o contexto de cada rede, quais redes entregam mais ou menos do que o "
          "esperado? A resposta tem duas partes. Primeiro, a associação existe, mas é pequena: a correlação simples entre "
          "gasto e proficiência caiu de 0,46 em 2017 para 0,16 em 2025 e se explica, em grande parte, pelo contexto dos "
          "municípios; quando cada município é comparado com ele mesmo ao longo do tempo, 10% a mais de gasto por aluno "
          "acompanham cerca de 0,2 ponto a mais no Saeb, e dobrar o gasto se associa a menos de 7% de um desvio-padrão da "
          "proficiência entre as redes. Segundo, redes com gasto e contexto parecidos têm resultados muito diferentes, e "
          "são essas diferenças, mais do que o volume de gasto, que distinguem as redes acima e abaixo do esperado."),
    corpo("Quatro conclusões se destacam:"),
    *alineas([
        "o volume de gasto, sozinho, diz pouco sobre o resultado: a associação dentro do município é estável e "
        "estatisticamente clara, mas pequena, e se concentra no gasto do próprio ciclo do Saeb, isto é, no ano da prova "
        "e no anterior; o gasto de dois ou quatro anos antes não se associa à nota;",
        "a associação não é igual em todo o país: concentra-se nos municípios de até 50 mil habitantes e no Nordeste e "
        "no Norte, e não aparece nas cidades com mais de 100 mil habitantes nem no Sudeste e no Sul; na camada estadual, "
        "com 27 unidades, não é possível detectá-la;",
        "redes com o mesmo gasto podem ter resultados muito diferentes: as redes municipais do Ceará e da Bahia gastaram, "
        "em mediana, praticamente o mesmo por aluno em 2023 (R$ 11.391 e R$ 11.231), mas a proficiência média em "
        "Matemática nos Anos Iniciais foi de 242,4 pontos no Ceará e de 200,1 na Bahia, e 90% das redes cearenses "
        "ficaram acima do esperado, contra 38% das baianas; a diferença se mantém entre municípios de contexto parecido e "
        "é compatível com as políticas de incentivo e de assistência técnica do Ceará descritas na literatura, explicação "
        "que este trabalho não testa;",
        "o resultado em relação ao esperado só é útil acompanhado dos alertas: os estudos de caso mostram que uma rede "
        "muito acima do esperado pode ter um salto atípico de nota (Coruripe, +69,6%) e que uma rede abaixo do esperado "
        "pode atender menos da metade dos alunos da etapa (São Paulo, −9,3%, com 42% dos alunos públicos dos Anos "
        "Iniciais na rede municipal); sem os alertas, a leitura levaria a conclusões apressadas.",
    ]),
    corpo("O objetivo geral foi atingido: o trabalho estimou a associação entre o gasto por aluno e o desempenho de 2017 "
          "a 2025 e identificou, para cada rede, a distância até o resultado esperado. Os objetivos específicos foram "
          "atendidos da seguinte forma: a integração das bases está descrita nas seções 3.1 e 3.2; a associação entre "
          "municípios e dentro do mesmo município, na seção 4.2; o indicador e o painel, na seção 3.3; e a aplicação ao "
          "Ceará e à Bahia e aos estudos de caso, nas seções 4.3 e 4.4."),
    titulo(2, "Contribuições práticas e teóricas"),
    corpo("Do ponto de vista prático, o painel reúne numa só interface o que hoje está em portais separados e responde a "
          "três perguntas de quem gere uma rede de ensino: se gastar mais se associa a aprender mais, se a própria rede "
          "entrega o esperado e com quem conversar, isto é, que redes de contexto e gasto parecidos obtêm resultados "
          "melhores. Isso desloca a pergunta gerencial do volume de recursos para o uso dos recursos, o que é coerente com "
          "a margem de decisão que o Fundeb deixa ao gestor. O código, os dados tratados e o registro de cada decisão "
          "estão em repositório público, o que permite reproduzir e atualizar o painel."),
    corpo("Do ponto de vista teórico, o trabalho acrescenta evidência recente, de 2017 a 2025 e já no período do Novo "
          "Fundeb, à literatura brasileira sobre gasto e desempenho, com um desenho que separa a comparação entre "
          "municípios da comparação de cada município com ele mesmo. O resultado reforça a leitura de que o gasto, "
          "sozinho, explica pouco das diferenças entre redes (Hanushek, 2003; Menezes-Filho & Amaral, 2009), e mostra que "
          "a associação existente é maior nos municípios pequenos e nas regiões mais pobres, em linha com os efeitos "
          "maiores para populações mais pobres encontrados na literatura internacional (Jackson & Mackevicius, 2024). O "
          "trabalho também propõe, para o uso gerencial, um indicador de desempenho em relação ao esperado que considera o "
          "contexto, como defendem Alves e Soares (2013)."),
    titulo(2, "Limitações"),
    corpo("As principais limitações do trabalho são as seguintes:"),
    *alineas([
        "associação, e não causalidade: os modelos não isolam uma variação do gasto externa às decisões das redes, e o "
        "desempenho em relação ao esperado é um resíduo de regressão, que capta também gestão, contexto familiar e "
        "qualidade do registro;",
        "controle socioeconômico por UF: o IDHM só existe por unidade da Federação, e a série disponível termina em 2024, "
        "de modo que a edição de 2025 não tem a comparação nacional;",
        "natureza declaratória dos dados de gasto: os dados do SIOPE são informados pelos próprios entes, e o nível do "
        "gasto depende da fonte, com divergência maior entre o SIOPE e o Siconfi nas maiores cidades; os valores extremos "
        "foram mantidos e marcados, e não excluídos;",
        "cobertura do Saeb: só entram as redes com nota divulgada pelo Inep, o que sub-representa as redes pequenas, "
        "sobretudo nos Anos Finais, e a edição de 2021 foi afetada pela pandemia;",
        "gasto agregado: o gasto municipal da subfunção 361 cobre todo o Ensino Fundamental, sem separar Anos Iniciais e "
        "Finais, deixa de fora a Educação Infantil e, por ser despesa paga, não inclui restos a pagar;",
        "redes parciais e saltos atípicos: em parte dos municípios, a rede municipal atende menos da metade dos alunos "
        "públicos da etapa, e algumas redes têm variações de nota fora do padrão; os dois casos foram marcados, e os "
        "testes sem eles não mudam as conclusões;",
        "camada estadual: com 27 unidades, a associação nas redes estaduais não pode ser detectada, e essa camada fica "
        "descritiva;",
        "validação sem usuários: o painel foi validado por cenários de uso e pela conferência técnica dos números, e não "
        "por testes com gestores, que exigiriam termo de consentimento e, possivelmente, aprovação em comitê de ética.",
    ]),
    titulo(2, "Sugestões de pesquisa futura"),
    corpo("Ficaram fora desta versão, por decisão dos autores, a simulação de cenários de gasto, porque a associação "
          "encontrada é pequena e não causal, e um simulador sugeriria um efeito que o trabalho não mede, e o "
          "monitoramento das condicionalidades do VAAR, que exige dados de habilitação das redes que não foram "
          "integrados. Como continuidade, sugere-se:"),
    *alineas([
        "avaliar o painel com gestores e analistas de secretarias de educação, com os cuidados éticos exigidos;",
        "identificar as redes que recebem a complementação-VAAT, para testar se ela explica o padrão observado de 2023 a "
        "2025;",
        "separar o gasto por etapa e incluir a Educação Infantil, quando as bases permitirem;",
        "estender a comparação nacional a 2025, quando o IDHM desse ano for publicado, e usar na nota esperada o gasto "
        "médio do biênio, que acompanha melhor o ciclo do Saeb;",
        "comparar o indicador com medidas de fronteira, como a análise envoltória de dados e a fronteira estocástica;",
        "estudar o efeito dos incentivos estaduais ligados a resultados, como o ICMS educacional, sobre as redes acima do "
        "esperado e sobre os saltos atípicos;",
        "automatizar a coleta das bases do Inep, por exemplo com o pacote educabR (Bissoli, 2026), e publicar o painel "
        "com atualização programada;",
        "derivar do trabalho um artigo científico.",
    ]),
]

RESUMO = (
    "O financiamento da educação básica pública brasileira mobiliza um volume expressivo de recursos, mas os dados que "
    "permitem relacionar o gasto aos resultados educacionais estão publicados em sistemas distintos. Este trabalho, um "
    "estudo quantitativo, investigou se o gasto público por aluno se associa ao desempenho das redes públicas de ensino "
    "no Saeb e quais redes entregam mais ou menos do que o esperado para o seu gasto e o seu contexto. Foram integradas "
    "bases públicas de gasto (SIOPE e Siconfi), de desempenho (Saeb), de oferta (Censo Escolar) e de contexto (IBGE e "
    "IDHM), de 2017 a 2025, em painéis de dados municipal e estadual. A associação foi estimada por regressões entre "
    "municípios e dentro do mesmo município, os municípios foram agrupados por contexto, e os resultados foram "
    "organizados num painel de Business Intelligence, com um indicador de desempenho em relação ao esperado. A "
    "correlação simples entre gasto e proficiência caiu de 0,46 em 2017 para 0,16 em 2025 e se explica, em grande parte, "
    "pelo contexto. Dentro do mesmo município, 10% a mais de gasto por aluno acompanham cerca de 0,2 ponto a mais no "
    "Saeb, associação concentrada no gasto do próprio ciclo de avaliação, nos municípios pequenos e no Nordeste e no "
    "Norte. Redes com gasto semelhante têm resultados muito diferentes: as redes municipais do Ceará e da Bahia gastam "
    "praticamente o mesmo por aluno, mas 90% das cearenses ficaram acima do esperado em 2023, contra 38% das baianas. "
    "Conclui-se que o volume de gasto, sozinho, explica pouco das diferenças de desempenho, e que comparar cada rede com "
    "redes de contexto e gasto parecidos ajuda o gestor a identificar referências e a orientar a investigação sobre o "
    "uso dos recursos. Os resultados indicam associação, e não efeito causal.")
ABSTRACT = (
    "The financing of Brazilian public basic education involves a significant volume of resources, but the data needed "
    "to relate spending to educational outcomes are published in separate systems. This quantitative study investigated "
    "whether public spending per student is associated with the performance of public school networks in Saeb, the "
    "national assessment of basic education, and which networks deliver more or less than expected given their spending "
    "and context. Public data on spending (SIOPE and Siconfi), performance (Saeb), provision (School Census) and context "
    "(IBGE and HDI) from 2017 to 2025 were integrated into municipal and state panels. The association was estimated "
    "with regressions across municipalities and within each municipality, municipalities were grouped by context, and "
    "the results were organized in a Business Intelligence dashboard with an indicator of performance relative to the "
    "expected level. The simple correlation between spending and proficiency fell from 0.46 in 2017 to 0.16 in 2025 and "
    "is largely explained by context. Within the same municipality, 10% more spending per student is associated with "
    "about 0.2 additional Saeb points, an association concentrated in spending during the assessment cycle itself, in "
    "small municipalities and in the Northeast and North regions. Networks with similar spending show very different "
    "results: municipal networks in Ceará and Bahia spend almost the same per student, but 90% of those in Ceará were "
    "above the expected level in 2023, against 38% in Bahia. The study concludes that the volume of spending alone "
    "explains little of the differences in performance, and that comparing each network with networks of similar "
    "context and spending helps managers identify benchmarks and guide the investigation of how resources are used. "
    "The results indicate association, not causal effect.")


def substituir_capitulo(xml: str, h1: str, proximo_h1: str, blocos: list[str]) -> str:
    """Troca todo o conteúdo do capítulo h1 (depois do título e até o título seguinte) pelos blocos."""
    a = achar_par(xml, h1, h1=True)
    b = [m for m in paragrafos(xml) if '"Heading1"' in m.group(0) and texto_de(m.group(0)).strip() == proximo_h1
         and m.start() > a.start()][0]
    assert "<w:sectPr" not in xml[a.end():b.start()]
    return xml[:a.end()] + "".join(blocos) + xml[b.start():]


x = substituir_capitulo(x, "CONCLUSÕES, LIMITAÇÕES E SUGESTÕES DE PESQUISA FUTURA", "REFERÊNCIAS", CAP_CONCLUSOES)
x = reescrever(x, "O financiamento da educação básica pública brasileira mobiliza", RESUMO, pre=True)
x = reescrever(x, "Palavras-chave:", "**Palavras-chave:** Gasto público em educação. Desempenho educacional. Saeb. Fundeb. "
               "Business Intelligence.", pre=True)
x = reescrever(x, "The financing of Brazilian public basic education", ABSTRACT, pre=True)
x = reescrever(x, "Keywords:", "**Keywords:** Public education spending. Educational performance. Saeb. Fundeb. Business "
               "Intelligence.", pre=True)
print(f"[INFO] Resumo: {len(RESUMO.split())} palavras; abstract: {len(ABSTRACT.split())} palavras")

# ───────────────────────── acabamento da etapa 4 (A26, 2026-11-18) ─────────────────────────
TITULO = ("Gasto público por aluno e desempenho no Saeb: uma análise das redes públicas brasileiras com apoio de "
          "Business Intelligence")


def apagar_pars(xml: str, inicios: list[str], pre: bool = True) -> str:
    for inicio in inicios:
        m = achar_par(xml, inicio, pre=pre)
        assert "<w:sectPr" not in m.group(0), inicio
        xml = xml[:m.start()] + xml[m.end():]
    return xml


def tirar_realce(xml: str, inicio: str, pre: bool = True) -> str:
    m = achar_par(xml, inicio, pre=pre)
    novo = re.sub(r"<w:highlight [^>]*/>", "", m.group(0))
    return xml[:m.start()] + novo + xml[m.end():]


def tirar_marca(xml: str, inicio: str, marca: str) -> str:
    """Tira de um parágrafo do corpo o trecho realçado que começa com `marca` (e o espaço antes dele)."""
    m = achar_par(xml, inicio)
    par = m.group(0)
    runs = re.findall(r"<w:r[ >](?:(?!</w:r>).)*?</w:r>", par, flags=re.S)
    alvo = [r for r in runs if texto_de(r).strip().startswith(marca)]
    assert alvo, (inicio[:40], marca)
    for r in alvo:
        par = par.replace(r, "", 1)
    par = re.sub(r"(<w:t(?: [^>]*)?>[^<]*?) +(</w:t>)(?=(?:(?!<w:t).)*</w:p>$)", r"\1\2", par, flags=re.S)
    return xml[:m.start()] + par + xml[m.end():]


# capa, página das opções de título e folha de rosto
x = reescrever(x, "Eficiência do Gasto Público e Qualidade Educacional: Proposição", TITULO, pre=True)
x = apagar_pars(x, ["Opção 1 (Focada", "&quot;Eficiência do Gasto Público e Qualidade Educacional: Um Produto", "Opção 2 (Focada",
                    "&quot;: Proposição de um Modelo", "Opção 3 (Mais", "&quot;Integração de Dados Orçamentários"])
x = reescrever(x, "[REVISAR] BUSINESS INTELLIGENCE PARA A GESTÃO", TITULO.upper(), pre=True)
# nome completo do autor na capa e na folha de rosto (pedido do Henrique, 2026-11-18)
i_intro = x.index("INTRODUÇÃO", x.index('"Heading1"'))
nomes = [m for m in paragrafos(x[:i_intro]) if texto_de(m.group(0)).strip() == "Henrique Lindoso"]
assert len(nomes) == 2, len(nomes)
for m in reversed(nomes):
    par = re.sub(r"(<w:t(?: [^>]*)?>)[^<]*(</w:t>)", lambda k: k.group(1) + k.group(2), m.group(0))
    par = re.sub(r"(<w:t(?: [^>]*)?>)(</w:t>)", lambda k: k.group(1) + "Henrique Nogueira Pedro Lindoso" + k.group(2), par, count=1)
    x = x[:m.start()] + par + x[m.end():]
# autoridades: reitor conferido; a FEA tem novo diretor (site da FEA, 2026-11-18); a chefia do departamento fica a conferir
x = tirar_realce(x, "Prof. Dr. Aluisio Augusto Cotrim Segurado")
x = reescrever(x, "Profa. Dra. Maria Dolores Montoya Diaz", "Prof. Dr. João Maurício Gama Boaventura", pre=True)
x = reescrever(x, "Diretora da Faculdade de Economia", "Diretor da Faculdade de Economia, Administração, Contabilidade e "
               "Atuária", pre=True)
# dedicatória (opcional) sai: a página inteira, até a quebra de seção da folha de rosto
pars_pre = [m for m in paragrafos(x) if m.start() < x.index("INTRODUÇÃO", x.index('"Heading1"'))]
k = next(i for i, m in enumerate(pars_pre) if texto_de(m.group(0)).strip().startswith("[Dedicatória"))
j = k
while j > 0 and not texto_de(pars_pre[j - 1].group(0)).strip() and "<w:sectPr" not in pars_pre[j - 1].group(0):
    j -= 1
assert "<w:sectPr" in pars_pre[j - 1].group(0) and texto_de(pars_pre[j - 1].group(0)).strip() == "São Paulo 2026"
x = x[:pars_pre[j].start()] + x[pars_pre[k].end():]
# agradecimentos: base para os autores personalizarem
x = reescrever(x, "[Escrever os agradecimentos", "Agradecemos à Profa. Adriana Backx Noronha Viana, pela orientação, pela "
               "confiança e pelo incentivo ao longo do trabalho; ao Departamento de Administração e à Faculdade de Economia, "
               "Administração, Contabilidade e Atuária da Universidade de São Paulo, pela formação; e às nossas famílias e "
               "aos colegas, pelo apoio durante a graduação. [PERSONALIZAR: acrescentar os agradecimentos de cada autor.]",
               pre=True)

# Introdução: marcações resolvidas com dados oficiais
x = reescrever(x, "A educação básica pública brasileira é financiada por um arranjo federativo complexo.",
    "A educação básica pública brasileira é financiada por um arranjo federativo complexo. A Constituição Federal obriga "
    "estados, Distrito Federal e municípios a aplicarem, no mínimo, 25% da receita resultante de impostos e "
    "transferências na manutenção e desenvolvimento do ensino (MDE) (Brasil, 1988, art. 212). Desde a Emenda "
    "Constitucional nº 108/2020, o Fundo de Manutenção e Desenvolvimento da Educação Básica e de Valorização dos "
    "Profissionais da Educação (Fundeb) tornou-se instrumento permanente de financiamento, com complementação da União de, "
    "no mínimo, 23% do total de recursos do fundo, distribuída nas modalidades VAAF, VAAT e VAAR (Brasil, 2020a, 2020b). "
    "Trata-se de um volume expressivo de recursos públicos: para 2025, a receita do Fundeb foi estimada em R$ 339 "
    "bilhões, dos quais R$ 58,8 bilhões de complementação da União (Brasil, 2025).")
x = reescrever(x, "Em paralelo, os resultados de aprendizagem seguem como desafio central.",
    "Em paralelo, os resultados de aprendizagem seguem como desafio central. Segundo a divulgação do Ideb 2025, a rede "
    "pública alcançou 6,1 nos anos iniciais do ensino fundamental, 5,0 nos anos finais e 4,3 no ensino médio (Instituto "
    "Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira [Inep], 2026b). Os resultados também são desiguais entre "
    "redes com recursos parecidos: em 2023, as redes municipais do Ceará e da Bahia gastaram praticamente o mesmo por "
    "aluno, mas a proficiência média em Matemática nos Anos Iniciais foi de 242,4 pontos no Ceará e de 200,1 na Bahia "
    "(Capítulo 4).")
x = tirar_marca(x, "Esse cenário revela uma questão de gestão", "[CONFERIR")
x = tirar_marca(x, "Esse cenário revela uma questão de gestão", "[DESENVOLVER")
x = reescrever(x, "Contribuição teórica.",
    "**Contribuição teórica.** O trabalho acrescenta evidência recente, de 2017 a 2025, à literatura brasileira sobre "
    "gasto e desempenho, separando a comparação entre municípios da comparação de cada município com ele mesmo, e "
    "aproxima essa literatura da de gestão pública baseada em evidências, ao propor um indicador de desempenho em relação "
    "ao esperado para uso gerencial (seção 2.2).")
x = tirar_marca(x, "A ideia de decisão baseada em evidências", "[CONFERIR")
x = tirar_marca(x, "No campo da transparência, a literatura distingue", "[CONFERIR")

# listas de figuras, tabelas e quadros: os campos do modelo buscavam títulos; passam a buscar as entradas TC das legendas
CAMPO_MODELO = "TOC \\h \\u \\z \\t &quot;Heading 1,1,Heading 2,2,Heading 3,3,Heading 4,4,Heading 5,5,Heading 6,6,&quot;"
assert x.count(CAMPO_MODELO) == 3, x.count(CAMPO_MODELO)
for letra in "FTQ":
    x = x.replace(CAMPO_MODELO, f"TOC \\h \\z \\f {letra}", 1)


def com_tc(m: re.Match) -> str:
    par = m.group(0)
    if "Heading" in par or "ffc000" in par:
        return par
    txt = texto_de(par).strip()
    tipo = re.match(r"(Figura|Tabela|Quadro) [A-Z]?\.?\d+ – ", txt)
    if not tipo or m.start() < x.index("INTRODUÇÃO", x.index('"Heading1"')):
        return par
    letra = {"Figura": "F", "Tabela": "T", "Quadro": "Q"}[tipo.group(1)]
    tc = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TC "'
          + escape(txt.replace('"', "”")) + f'" \\f {letra} \\l 1 </w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')
    if "<w:r><w:br/></w:r>" in par:
        return par.replace("<w:r><w:br/></w:r>", tc + "<w:r><w:br/></w:r>", 1)
    return par[:-len("</w:p>")] + tc + "</w:p>"


x = re.sub(r"<w:p[ >].*?</w:p>", com_tc, x, flags=re.S)


def titulo_pre(texto: str, quebra: bool = False) -> str:
    return ('<w:p><w:pPr>' + ('<w:pageBreakBefore/>' if quebra else '') + '<w:spacing w:after="360" w:before="0" '
            'w:line="360" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>' + run(texto, negrito=True) + "</w:p>")


def antes_do_campo(xml: str, campo: str, blocos: list[str]) -> str:
    i = xml.index(campo)
    b = xml.rfind('w:fldCharType="begin"', 0, i)
    a = max(xml.rfind("<w:p>", 0, b), xml.rfind("<w:p ", 0, b))
    return xml[:a] + "".join(blocos) + xml[a:]


SIGLAS = [("AF", "Anos Finais do Ensino Fundamental"), ("AI", "Anos Iniciais do Ensino Fundamental"),
          ("BI", "Business Intelligence"), ("BNCC", "Base Nacional Comum Curricular"), ("CAQ", "Custo Aluno-Qualidade"),
          ("DEA", "Análise envoltória de dados (Data Envelopment Analysis)"), ("EF", "Efeito fixo"),
          ("EM", "Ensino Médio"), ("ENEM", "Exame Nacional do Ensino Médio"),
          ("FEA", "Faculdade de Economia, Administração, Contabilidade e Atuária"), ("FJP", "Fundação João Pinheiro"),
          ("FNDE", "Fundo Nacional de Desenvolvimento da Educação"),
          ("Fundeb", "Fundo de Manutenção e Desenvolvimento da Educação Básica e de Valorização dos Profissionais da Educação"),
          ("Fundef", "Fundo de Manutenção e Desenvolvimento do Ensino Fundamental e de Valorização do Magistério"),
          ("IA", "Inteligência artificial"), ("IBGE", "Instituto Brasileiro de Geografia e Estatística"),
          ("ICMS", "Imposto sobre Operações Relativas à Circulação de Mercadorias e sobre Prestações de Serviços de "
                   "Transporte Interestadual e Intermunicipal e de Comunicação"),
          ("Ideb", "Índice de Desenvolvimento da Educação Básica"), ("IDHM", "Índice de Desenvolvimento Humano Municipal"),
          ("Inep", "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira"),
          ("IPCA", "Índice Nacional de Preços ao Consumidor Amplo"), ("Ipea", "Instituto de Pesquisa Econômica Aplicada"),
          ("LDB", "Lei de Diretrizes e Bases da Educação Nacional"), ("LP", "Língua Portuguesa"),
          ("MDE", "Manutenção e desenvolvimento do ensino"), ("MEC", "Ministério da Educação"),
          ("MQO", "Mínimos quadrados ordinários"), ("MT", "Matemática"),
          ("PISA", "Programa Internacional de Avaliação de Estudantes"),
          ("PNUD", "Programa das Nações Unidas para o Desenvolvimento"),
          ("Saeb", "Sistema de Avaliação da Educação Básica"),
          ("Siconfi", "Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro"),
          ("SIOPE", "Sistema de Informações sobre Orçamentos Públicos em Educação"),
          ("TCC", "Trabalho de Conclusão de Curso"), ("UF", "Unidade da Federação"), ("USP", "Universidade de São Paulo"),
          ("VAAF", "Valor Anual por Aluno do Fundeb"), ("VAAR", "Valor Anual por Aluno por Resultado"),
          ("VAAT", "Valor Anual Total por Aluno")]


def sigla(s: str, sig: str) -> str:
    return ('<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="1418"/></w:tabs><w:spacing w:after="0" w:before="0" '
            'w:line="360" w:lineRule="auto"/><w:ind w:left="1418" w:hanging="1418"/><w:jc w:val="left"/></w:pPr>'
            + run(s) + "<w:r><w:tab/></w:r>" + run(sig) + "</w:p>")


x = antes_do_campo(x, "TOC \\h \\z \\f F", [titulo_pre("LISTA DE FIGURAS")])
x = antes_do_campo(x, "TOC \\h \\z \\f T", [titulo_pre("LISTA DE TABELAS")])
x = antes_do_campo(x, "TOC \\h \\z \\f Q", [titulo_pre("LISTA DE QUADROS")])
x = antes_do_campo(x, "TOC \\h \\u \\z \\t &quot;Heading 1,1,Heading 2,2,Heading 3,3,&quot;",
                   [titulo_pre("LISTA DE ABREVIATURAS E SIGLAS"), *[sigla(a, b) for a, b in SIGLAS],
                    titulo_pre("SUMÁRIO", quebra=True)])
# o campo do sumário buscava os estilos pelo nome em inglês ("Heading 1"), que o Word em português não reconhece:
# passa a usar os níveis de estrutura de tópicos, que valem em qualquer idioma
x = x.replace(r"TOC \h \u \z \t &quot;Heading 1,1,Heading 2,2,Heading 3,3,&quot;", r"TOC \o &quot;1-3&quot; \h \z \u", 1)
# os títulos das listas e do sumário estavam no cabeçalho da página (resto da conversão do modelo): saem de lá
for cab in (PASTA / "word").glob("header*.xml"):
    c = cab.read_text(encoding="utf-8")
    if texto_de(c).strip() in ("LISTA DE FIGURAS", "LISTA DE TABELAS", "LISTA DE QUADROS", "SUMÁRIO"):
        cab.write_text(re.sub(r"(<w:t(?: [^>]*)?>)[^<]*(</w:t>)", r"\1\2", c), encoding="utf-8")

# versão final: sem as notas amarelas; as marcações que restarem são listadas
if FINAL:
    x = re.sub(r"<w:p[ >](?:(?!</w:p>).)*?ffc000(?:(?!</w:p>).)*?</w:p>", "", x, flags=re.S)
    restam = [texto_de(r).strip() for r in re.findall(r"<w:r[ >](?:(?!</w:r>).)*?<w:highlight [^>]*/>(?:(?!</w:r>).)*?</w:r>", x,
                                                         flags=re.S) if texto_de(r).strip()]
    restam += re.findall(r"\[(?:CONFERIR|INSERIR|REVISAR|PERSONALIZAR|DEFINIR|DETALHAR)[^\]]*\]", texto_de(x))
    print(f"[INFO] Versão final: {len(set(restam))} marcações restantes")
    for r in dict.fromkeys(restam):
        print("   -", r[:110])

# ───────────────────────── formatação (ABNT NBR 14724; diretrizes da USP) ─────────────────────────
# margens de 3 cm (superior e esquerda) e 2 cm (inferior e direita) em todas as seções; número da página a 2 cm da borda
x = re.sub(r"<w:pgMar [^>]*/>", '<w:pgMar w:top="1701" w:right="1134" w:bottom="1134" w:left="1701" w:header="1134" '
           'w:footer="709" w:gutter="0"/>', x)
# capa e folha de rosto: o modelo posiciona "São Paulo 2026" no pé da página com linhas em branco; com a margem
# inferior de 2 cm (era 0,5 cm), a cidade e o ano passavam para uma página nova. Saem 5 linhas em branco antes de cada um.
i_intro = x.index("INTRODUÇÃO", x.index('"Heading1"'))
pars = list(re.finditer(r"<w:p[ >].*?</w:p>", x[:i_intro], flags=re.S))
cortes = []
for k, m in enumerate(pars):
    if texto_de(m.group(0)).strip() == "São Paulo 2026":
        j = k - 1
        while j >= 0 and len([c for c in cortes if c[2] == k]) < 5:
            q = pars[j].group(0)
            if texto_de(q).strip() or "<w:sectPr" in q or "<w:drawing>" in q:
                break
            cortes.append((pars[j].start(), pars[j].end(), k))
            j -= 1
assert len(cortes) >= 8, f"linhas em branco da capa e da folha de rosto: {len(cortes)}"
for a, b, _ in sorted(cortes, reverse=True):
    x = x[:a] + x[b:]

# tabelas (não quadros) abertas nas laterais, como pede a ABNT pelas normas de apresentação tabular do IBGE: só os
# traços de cima e de baixo e o que separa o cabeçalho, sem grade interna e sem sombreado
def abrir_tabela(m: re.Match) -> str:
    tb = m.group(0)
    antes = [p for p in re.findall(r"<w:p[ >].*?</w:p>", x[max(0, m.start() - 3000):m.start()], flags=re.S)]
    if not antes or not texto_de(antes[-1]).startswith("Tabela "):
        return tb
    tb = re.sub(r"<w:tblBorders>.*?</w:tblBorders>", '<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
                '<w:left w:val="nil"/><w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/><w:right w:val="nil"/>'
                '<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>', tb, count=1, flags=re.S)
    cab = re.search(r"<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>.*?</w:tr>", tb, flags=re.S)
    if cab:
        novo = cab.group(0).replace('<w:shd w:fill="d9d9d9" w:val="clear"/>',
                                    '<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tcBorders>')
        tb = tb.replace(cab.group(0), novo, 1)
    return tb


x = re.sub(r"<w:tbl>.*?</w:tbl>", abrir_tabela, x, flags=re.S)

# texto do corpo (da Introdução às Referências, fora de tabelas, títulos, notas, legendas e fontes): espaçamento 1,5,
# justificado e recuo de 1,25 cm na primeira linha
i0 = next(m.start() for m in re.finditer(r"<w:p[ >].*?</w:p>", x, flags=re.S)
          if '"Heading1"' in m.group(0) and texto_de(m.group(0)) == "INTRODUÇÃO")
i1 = next(m.start() for m in re.finditer(r"<w:p[ >].*?</w:p>", x, flags=re.S)
          if '"Heading1"' in m.group(0) and texto_de(m.group(0)) == "REFERÊNCIAS")
tabelas = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", x, flags=re.S)]
ajustados = 0


def ajustar(m: re.Match) -> str:
    global ajustados
    par = m.group(0)
    if not (i0 < m.start() < i1) or any(a <= m.start() < b for a, b in tabelas):
        return par
    txt = texto_de(par).strip()
    if (not txt or "Heading" in par or "ffc000" in par or "<w:drawing>" in par or "<w:pPr>" not in par
            or re.match(r"(Quadro|Tabela|Figura|Fonte|Nota)\b", txt)):
        return par
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", par, flags=re.S).group(0)
    novo = re.sub(r'w:line="\d+"', 'w:line="360"', ppr) if 'w:line="' in ppr else ppr
    if 'w:line="' not in novo:
        novo = (re.sub(r"<w:spacing ", '<w:spacing w:line="360" w:lineRule="auto" ', novo, count=1) if "<w:spacing " in novo
                else novo.replace("</w:pPr>", '<w:spacing w:line="360" w:lineRule="auto"/></w:pPr>'))
    novo = re.sub(r'<w:jc w:val="(left|start)"/>', '<w:jc w:val="both"/>', novo)
    lista = "numPr" in novo or "w:hanging" in novo or re.search(r'w:left="[1-9]', novo)
    if not lista:
        novo = re.sub(r'w:firstLine="0"', 'w:firstLine="709"', novo)
    if novo != ppr:
        ajustados += 1
    return par.replace(ppr, novo, 1)


x = re.sub(r"<w:p[ >].*?</w:p>", ajustar, x, flags=re.S)
print(f"[INFO] Formatação: {ajustados} parágrafos do corpo ajustados (1,5, justificado, recuo); margens 3/2 cm")
# número da página: no rascunho, o cabeçalho do texto traz o número "10" digitado (resto da conversão do modelo);
# aqui vira o campo PAGE, no canto superior direito, em tamanho 10
rels_doc = (PASTA / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
rid_corpo = re.findall(r'<w:headerReference r:id="(rId\d+)"', x)[-1]
arq_cab = PASTA / "word" / re.search(rf'Id="{rid_corpo}"[^>]*Target="([^"]+)"', rels_doc).group(1)
cab = arq_cab.read_text(encoding="utf-8")
assert texto_de(cab).strip() == "10", f"cabeçalho inesperado: {texto_de(cab)[:40]}"
rpr = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="20"/></w:rPr>'
campo = ('<w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
         f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rpr}<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
         f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rpr}<w:t>10</w:t></w:r>'
         f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r></w:p>')
arq_cab.write_text(re.sub(r"<w:p[ >].*</w:p>", lambda m: campo, cab, count=1, flags=re.S), encoding="utf-8")
estilos = PASTA / "word" / "styles.xml"
st = estilos.read_text(encoding="utf-8")
estilos.write_text(st.replace('<w:lang w:val="pt_PT"/>', '<w:lang w:val="pt-BR" w:eastAsia="pt-BR" w:bidi="ar-SA"/>'),
                   encoding="utf-8")
# endereço do repositório como link clicável (para quem lê o PDF ou o .docx no computador; etapa 5, 2026-11-18)
def com_link(m: re.Match) -> str:
    r = m.group(0)
    rpr = (re.search(r"<w:rPr>.*?</w:rPr>", r, flags=re.S) or [""])[0] if "<w:rPr>" in r else "<w:rPr></w:rPr>"
    rpr_link = rpr.replace("</w:rPr>", '<w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>')
    rpr_link = re.sub(r'<w:color w:val="000000"/>', "", rpr_link, count=1)
    antes, _, depois = texto_de(r).partition(REPO)
    pedaco = lambda s, pr: f'<w:r>{pr}<w:t xml:space="preserve">{escape(s)}</w:t></w:r>' if s else ""
    return (pedaco(antes, rpr) + f'<w:hyperlink r:id="rIdRepo" w:history="1"><w:r>{rpr_link}<w:t>{REPO}</w:t></w:r>'
            "</w:hyperlink>" + pedaco(depois, rpr))


i_intro = x.index("INTRODUÇÃO", x.index('"Heading1"'))
x = x[:i_intro] + re.sub(r"<w:r>(?:(?!</w:r>).)*?" + re.escape(REPO) + r"(?:(?!</w:r>).)*?</w:r>", com_link, x[i_intro:],
                         flags=re.S)
DOC.write_text(x, encoding="utf-8")

rels = PASTA / "word" / "_rels" / "document.xml.rels"
r = rels.read_text(encoding="utf-8")
figs = {"rIdFig3": "fig3_heterogeneidade.png"}  # as Figuras 1, 2 e 4 da análise repetiam as Tabelas 3, 4 e 5 (A22)
figs["rIdFluxo"] = "fig0_fluxo_dados.png"
figs["rIdClu1"], figs["rIdClu2"] = "fig5_escolha_k.png", "fig6_perfil_clusters.png"
figs["rIdCeba"] = "fig7_ce_ba.png"
figs["rIdQR"] = "qrcode_acesso.png"  # src/Exportacao/Gerar_QRCode.py
novos = ""
for k, (arq, _) in enumerate(TELAS_CASO):
    shutil.copy(TELAS_DIR / f"{arq}.png", PASTA / "word" / "media" / f"tela_{arq}.png")
    novos += (f'<Relationship Id="rIdCaso{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/tela_{arq}.png"/>')
for k, (arq, _) in enumerate(TELAS):
    shutil.copy(TELAS_DIR / f"{arq}.png", PASTA / "word" / "media" / f"tela_{arq}.png")
    novos += (f'<Relationship Id="rIdTela{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/tela_{arq}.png"/>')
novos += (f'<Relationship Id="rIdRepo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
          f'Target="{REPO}" TargetMode="External"/>')
for rid, arq in figs.items():
    shutil.copy(MT.FIG / arq, PASTA / "word" / "media" / arq)
    novos += (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/{arq}"/>')
rels.write_text(r.replace("</Relationships>", novos + "</Relationships>"), encoding="utf-8")

SAIDA.parent.mkdir(parents=True, exist_ok=True)
if SAIDA.exists():
    SAIDA.unlink()
with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_DEFLATED) as z:
    ct = PASTA / "[Content_Types].xml"
    z.write(ct, "[Content_Types].xml")
    for f in sorted(PASTA.rglob("*")):
        if f.is_file() and f != ct:
            z.write(f, f.relative_to(PASTA).as_posix())
print(f"[OK] {SAIDA} ({SAIDA.stat().st_size // 1024} KB), {len(INSERCOES)} pontos de inserção")
