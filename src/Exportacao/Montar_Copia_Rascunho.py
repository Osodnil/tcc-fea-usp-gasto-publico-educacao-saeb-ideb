"""Monta uma CÓPIA do rascunho do TCC II com o conteúdo técnico produzido no projeto.

Uso (na raiz do repositório):  python Montar_Copia_Rascunho.py <pasta_descompactada> <saida.docx> <pasta_das_telas>

Não toca no original. Insere, depois das lacunas do rascunho: notas de rascunho (caixa amarela, como as do documento),
texto técnico dos capítulos 4 e 5, quadros, tabelas e figuras, e notas de ATENÇÃO onde o rascunho diverge do que foi
feito. Não escreve revisão de literatura, discussão nem conclusões.
"""
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import polars as pl

sys.path.insert(0, "src/Analise")
import Material_Texto as MT  # noqa: E402  (formatação brasileira e leitura das saídas)
import Modelo_Principal as M  # noqa: E402

PASTA, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
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
    return f'<w:p><w:pPr><w:pStyle w:val="Heading{nivel}"/></w:pPr>' + run(texto, negrito=True) + "</w:p>"


def legenda(texto: str) -> str:
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:after="120" w:before="240" w:line="240" w:lineRule="auto"/>'
            '<w:jc w:val="left"/></w:pPr>' + run(texto, negrito=True) + "</w:p>")


def fonte(texto: str) -> str:
    return ('<w:p><w:pPr><w:spacing w:after="240" w:before="60" w:line="240" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>'
            + run(texto, tam=20) + "</w:p>")


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
             "* p < 0,10. Associação, não efeito causal. Fonte: elaborado pelos autores.")


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
         "números e acrescentar as citações. O uso de IA precisa ser aprovado pela orientadora (Manual, item 2.3).]")
TELAS = [  # (arquivo, legenda) das capturas do painel, na ordem das páginas
    ("01_boas_vindas", "Página Boas-vindas: para que serve o painel, como usar e as perguntas de entrada"),
    ("02_visao_geral", "Página Visão geral: gasto, proficiência, cobertura do Saeb e redes que melhoraram"),
    ("03_eficiencia", "Página Eficiência: gasto por aluno e resultado em relação ao esperado, com o ranking das redes"),
    ("04_ficha", "Página Ficha do município: série da rede contra o cluster, a UF e o Brasil"),
    ("05_pares", "Página Pares: redes de contexto e gasto parecidos e comparação de duas redes"),
    ("06_mapa", "Página Mapa: resultado em relação ao esperado por município (exemplo: Bahia)"),
    ("07_defasagens", "Página Defasagens: correlação entre gasto e proficiência por edição e defasagem"),
    ("08_contexto", "Página Contexto e clusters: perfil dos grupos e composição por região"),
    ("09_estados", "Página Estados: redes estaduais das 27 UFs"),
    ("10_sobre", "Página Sobre os dados: fontes, indicadores, limitações e correção pela inflação"),
]
F_FLUXO, F_TELA0, F_AN = 1, 2, 2 + len(TELAS)   # numeração: fluxo, telas e figuras da análise

CAP4_1 = [
    nota(AVISO),
    corpo("O produto analítico parte de bases públicas de oito origens, reunidas no Quadro 3. A extração, o tratamento e a "
          "integração foram feitos em Python, com a biblioteca Polars, em scripts versionados no repositório do projeto. Um "
          "comando único executa todas as etapas na ordem certa, do dado bruto às tabelas lidas pelo painel, o que permite "
          "refazer todo o processo a partir das fontes. A Figura 1 resume esse fluxo."),
    figura("rIdFluxo", 50, 16.0, 7.64, "Figura fluxo"),
    fonte(f"Figura {F_FLUXO} – Fluxo de dados do projeto, das fontes públicas ao painel. Fonte: elaborado pelos autores."),
    legenda("Quadro 3 – Fontes de dados, origem e uso no trabalho"),
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
    fonte("Fonte: elaborado pelos autores."),
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
    item("Saltos atípicos de proficiência são marcados, e não excluídos: é atípica a variação entre duas edições "
         "consecutivas que se afasta mais de três desvios-padrão da média das variações da mesma etapa e disciplina. São 633 "
         "resultados marcados, cerca de 0,8% do total."),
    item("Redes municipais parciais são marcadas: aquelas em que a prefeitura atende menos de 50% dos alunos públicos da "
         "etapa, e o restante está na rede estadual. Em 2023, eram 2,7% das redes com nota nos Anos Iniciais e 16% nos Anos "
         "Finais."),
    corpo("A lista completa das limitações que decorrem dessas regras está no Capítulo 6."),
]

CAP4_3 = [
    corpo("O protótipo foi construído no Power BI, como projeto versionável (formato .pbip), e tem dez páginas, descritas no "
          "Quadro 4. Os filtros ficam numa faixa no topo, e cada página mostra só os filtros que alteram o seu conteúdo. A "
          "escolha de UF, etapa, disciplina e edição vale para todas as páginas."),
    legenda("Quadro 4 – Páginas do painel e pergunta que cada uma responde"),
    tabela(["Página", "O que mostra", "Pergunta do gestor"], [
        ["Boas-vindas", "Para que serve, como usar e três perguntas que levam às páginas", "Por onde começo?"],
        ["Visão geral", "Gasto, proficiência, cobertura do Saeb e redes que melhoraram desde a edição anterior", "Como está o conjunto das redes?"],
        ["Eficiência", "Dispersão do gasto contra o resultado em relação ao esperado; ranking das redes", "Quem entrega acima do esperado?"],
        ["Ficha do município", "Série de proficiência contra o cluster, a UF e o Brasil; gasto por ano; situação da rede", "Como está a minha rede?"],
        ["Pares", "Redes de contexto e gasto parecidos; comparação de duas redes, uma a uma", "Com quem conversar?"],
        ["Mapa", "Resultado em relação ao esperado por município, numa UF", "Onde estão as redes acima e abaixo do esperado?"],
        ["Defasagens", "Correlação entre gasto e proficiência, por edição e defasagem do gasto", "Gastar mais se associa a notas maiores?"],
        ["Contexto e clusters", "Perfil dos sete grupos de municípios; gasto e proficiência por porte", "Quais redes são comparáveis?"],
        ["Estados", "Redes estaduais das 27 UFs, Anos Finais e Ensino Médio", "Como estão as redes estaduais?"],
        ["Sobre os dados", "Fontes, indicadores, limitações e correção pela inflação", "De onde vêm os números?"],
    ], [1700, 4375, 3000]),
    fonte("Fonte: elaborado pelos autores."),
    corpo("O indicador central do painel compara a proficiência de cada rede com a proficiência esperada. A esperada vem de "
          "uma regressão da proficiência contra o gasto por aluno (em logaritmo) e variáveis de contexto: população, "
          "alfabetização, infraestrutura das escolas, tamanho da rede e IDHM Renda e Longevidade da UF. O painel mostra a "
          "diferença em percentual da esperada: +5% significa que a nota ficou 5% acima da esperada, e 0% significa que a "
          "rede entregou exatamente o esperado. Há duas comparações: a nacional, que usa o IDHM e cobre as edições de 2017 a "
          "2023, e a do mesmo estado, que troca o IDHM por um efeito de cada UF e cobre também 2025."),
    corpo("Os alertas do painel aparecem numa coluna única, chamada Atenção, que marca os saltos atípicos e as redes "
          "municipais parciais. Os números do painel foram conferidos com os cálculos feitos em Python, e as páginas são "
          "validadas contra os esquemas oficiais do formato do Power BI. As Figuras "
          f"{F_TELA0} a {F_TELA0 + len(TELAS) - 1} mostram as dez páginas, com os filtros em Anos Iniciais, Matemática e "
          "edição de 2023."),
    *[b for k, (arq, leg) in enumerate(TELAS) for b in (
        figura(f"rIdTela{k}", 60 + k, 16.0, 9.0, f"Tela {k + 1}"),
        fonte(f"Figura {F_TELA0 + k} – {leg}. Fonte: painel elaborado pelos autores."))],
    nota("[Pontos deste capítulo que dependem de decisão dos autores e da orientadora: (i) no modelo nacional, o gasto quase "
         "não altera a nota esperada (0,92 ponto por log do gasto, não significativo), então o indicador mede, na prática, o "
         "desempenho em relação ao esperado para o contexto: isso afeta o nome do indicador e a definição do item 2.1.4; "
         "(ii) o painel não tem simulação de cenários nem monitoramento do VAAR, citados no resumo, nos objetivos e no "
         "Capítulo 3; (iii) a regra dos saltos atípicos ainda precisa ser confirmada; (iv) falta o endereço público do "
         "painel para o QR Code.]"),
]

CAP5_CLUSTER = [
    nota(AVISO + " A interpretação e a discussão com a literatura ficam com os autores; aqui estão o método e os números."),
    corpo("Para comparar redes em condições parecidas, os municípios foram agrupados pelo contexto, sem usar o gasto nem a "
          "nota. O agrupamento usou o método das k-médias com cinco variáveis padronizadas: população, taxa de "
          "alfabetização, IDHM Renda e IDHM Longevidade da UF e infraestrutura das escolas. Foram formados sete grupos, com "
          "5.568 municípios; três municípios ficaram de fora por falta de alguma variável. O Quadro 5 traz o perfil de cada "
          "grupo."),
    legenda("Quadro 5 – Perfil dos sete clusters de contexto"),
    tabela(["Cluster", "Municípios", "População mediana", "Alfabetização", "IDHM Renda", "Infraestrutura", "Região principal"],
           t_clu, [2675, 950, 1100, 1100, 900, 1050, 1300]),
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
          "edição, em três especificações (Tabela 3 e Figura {F_AN}). A primeira compara os municípios entre si. A segunda inclui "
          "um efeito fixo de município, isto é, compara cada município com ele mesmo ao longo do tempo. A terceira, adotada "
          "como referência, acrescenta um efeito de UF e edição, de modo que a comparação é feita entre municípios do mesmo "
          "estado na mesma edição. Os erros-padrão são agrupados por município."),
    legenda("Tabela 3 – Gasto do mesmo ano e proficiência: três especificações"),
    tabela(["Especificação", *CAB4], t_modelo, [2475, 1650, 1650, 1650, 1650]),
    fonte(NOTA_COEF + " EF: efeito fixo. Controles: infraestrutura e log das matrículas; no MQO, também log da população e "
          "alfabetização; nas especificações de 2017–2023, IDHM Renda e Longevidade da UF."),
    figura("rIdFig1", 1, 16.0, 6.04, "Figura 1"),
    fonte(f"Figura {F_AN + 0} – Coeficiente do log do gasto por aluno, entre municípios e dentro do município, com intervalo de 95%. "
          "Fonte: elaborado pelos autores."),
    corpo("Entre os municípios, com os controles de contexto, o gasto quase não se associa à nota: o coeficiente é de 0,92 "
          "ponto por log do gasto nos Anos Iniciais, em Matemática, e não se distingue de zero. Dentro do mesmo município, a "
          "associação é positiva e estatisticamente significativa nas duas etapas e nas duas disciplinas. Na especificação "
          "de referência, um aumento de 10% no gasto por aluno acompanha um aumento de cerca de 0,22 ponto em Matemática nos "
          "Anos Iniciais; dobrar o gasto acompanha cerca de 1,6 ponto. Como referência de escala, um ano de escolaridade "
          "corresponde a cerca de 25 pontos no Saeb. [CITAR a fonte dessa equivalência.]"),
    corpo("A especificação de referência foi escolhida depois de uma investigação sobre a edição de 2025. Sem o efeito de UF "
          "e edição, incluir 2025 dobrava o coeficiente. Verificou-se que, de 2023 a 2025, as redes do Nordeste e do Norte "
          "tiveram ao mesmo tempo o maior aumento médio de gasto por aluno (cerca de 26% e 21%, contra 8% no Sudeste) e o maior ganho de nota. Com o "
          "efeito de UF e edição, o coeficiente fica estável, com ou sem 2025. O padrão é compatível com a complementação "
          "VAAT do Novo Fundeb, mas essa explicação não foi testada, porque o painel de dados não identifica as redes que "
          "receberam a complementação."),
    titulo(3, "Defasagem do gasto"),
    corpo(f"A Tabela 4 e a Figura {F_AN + 1} comparam o gasto do ano da prova com o de um e dois anos antes, sempre nas mesmas redes. "
          "Dentro do município, a associação vem do gasto do ano da prova e do ano anterior, os dois anos do ciclo bienal do "
          "Saeb; o gasto de dois anos antes não se associa de forma significativa. O gasto de quatro anos antes, na janela em "
          "que existe (2021 a 2025), também não. O resultado difere do da correlação simples, que cresce com a defasagem."),
    legenda("Tabela 4 – Defasagem do gasto na especificação de referência, mesma amostra (2019–2025)"),
    tabela(["Etapa e disciplina", "Gasto do mesmo ano", "1 ano antes", "2 anos antes"], t_defas, [2775, 2100, 2100, 2100]),
    fonte(NOTA_COEF),
    figura("rIdFig2", 2, 16.0, 5.16, "Figura 2"),
    fonte(f"Figura {F_AN + 1} – Associação dentro do município por defasagem do gasto, mesma amostra (2019–2025). Fonte: elaborado "
          "pelos autores."),
    titulo(3, "Heterogeneidade por porte, região, cluster e nível de gasto"),
    corpo(f"A associação dentro do município não é igual em todos os grupos (Tabela 5 e Figura {F_AN + 2}). O teste de igualdade das "
          "inclinações é rejeitado nas quatro dimensões (p ≤ 0,02). A associação é maior nos municípios de até 50 mil "
          "habitantes e no Nordeste e no Norte. Nas cidades de 50 a 100 mil habitantes, ela não se distingue de zero, e "
          "nas de mais de 100 mil, é negativa. No Sudeste e no Sul, não se distingue de zero."),
    legenda("Tabela 5 – Associação dentro do município, por grupo (Anos Iniciais)"),
    tabela(["Dimensão", "Grupo", "Matemática", "Português", "Municípios"], t_het, [1700, 3075, 1600, 1600, 1100]),
    fonte(NOTA_COEF + " Especificação de referência, com uma inclinação por grupo. Faixa de gasto: quintil do gasto médio "
          "por aluno do município em 2017–2025 (Q1 = menor)."),
    figura("rIdFig3", 3, 16.0, 11.02, "Figura 3"),
    fonte(f"Figura {F_AN + 2} – Associação dentro do município por porte, região, cluster e faixa de gasto médio (Anos Iniciais, "
          "Matemática). Fonte: elaborado pelos autores."),
    corpo("Três cuidados valem para essa leitura. As dimensões se sobrepõem: 614 dos 1.063 municípios do quintil de maior "
          "gasto por aluno têm até 5 mil habitantes, de modo que a faixa de gasto e o porte contam, em boa parte, a mesma "
          "história. A associação negativa nas cidades grandes não tem explicação testada; são hipóteses a composição do "
          "gasto da subfunção 361 nessas redes, a variação das matrículas e a regressão à média. E, como são muitas "
          "comparações, nenhum grupo deve ser lido isoladamente."),
    titulo(3, "Testes de sensibilidade"),
    corpo(f"A Tabela 6 e a Figura {F_AN + 3} mostram a associação dentro do município quando se altera uma escolha de cada vez: sem a "
          "edição de 2021, só com os municípios que têm nota nas cinco edições, com o gasto médio do biênio, sem as redes "
          "municipais parciais, sem os saltos atípicos e com outras formas de controlar o IDHM. Em todos os testes, o "
          "coeficiente fica positivo e significativo, entre 1,4 e 5,5 pontos por log do gasto. Com o gasto médio do biênio, "
          "o coeficiente é cerca de 60% maior que o da referência na mesma janela."),
    legenda("Tabela 6 – Testes de sensibilidade (camada municipal, gasto do mesmo ano)"),
    tabela(["Teste", *CAB4], t_sens, [2875, 1550, 1550, 1550, 1550]),
    fonte(NOTA_COEF + " Cada teste muda uma escolha da especificação de referência. As três últimas linhas usam efeito de "
          "edição e 2017–2023, porque o efeito de UF e edição absorve o IDHM."),
    figura("rIdFig4", 4, 16.0, 7.82, "Figura 4"),
    fonte(f"Figura {F_AN + 3} – Testes de sensibilidade (Anos Iniciais, Matemática); o tracejado marca a referência. Fonte: "
          "elaborado pelos autores."),
    titulo(3, "Camada estadual"),
    corpo("Na camada estadual, o mesmo modelo foi estimado com a UF no lugar do município (Tabela 7). Nenhum coeficiente se "
          "distingue de zero, nos Anos Finais e no Ensino Médio, em nenhuma especificação, nem com a versão B do gasto, nem com o gasto medido pela soma das subfunções da educação básica, que deixa de fora o que a função 12 não detalha em subfunção. Com 27 "
          "unidades, a estimativa é imprecisa: os intervalos de 95% vão de cerca de −6 a +9 pontos por log do gasto e "
          "incluem tanto zero quanto valores maiores que o da camada municipal. A leitura correta é que a associação não é "
          "detectável com 27 unidades, e não que ela não exista."),
    legenda("Tabela 7 – Camada estadual: gasto estadual por aluno e proficiência das redes estaduais"),
    tabela(["Especificação", "AF Matemática", "AF Português", "EM Matemática", "EM Português"], t_est, [2475, 1650, 1650, 1650, 1650]),
    fonte(NOTA_COEF + " 27 UFs (23 na versão B, que deixa de fora as UFs e anos sem a linha do Ensino Superior). Soma das subfunções: 122, 361, 362, 365, 366, 367 e 368. Erros agrupados por UF; valores-p e intervalos pela distribuição t com 26 graus de "
          "liberdade."),
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


T_CASOS = 8  # as Tabelas 1 a 7 estão na seção de associação
TELAS_CASO = [  # (arquivo em docs/resultados/telas, legenda); entram só se a captura existir
    ("caso_a_ficha", f"Página Ficha do município com {mun('A')}"),
    ("caso_a_pares", f"Página Pares com {mun('A')} como referência"),
    ("caso_b_ficha", f"Página Ficha do município com {mun('B')}"),
    ("caso_c_ficha", f"Página Ficha do município com {mun('C')}"),
]
TELAS_DIR = Path(sys.argv[3])
TELAS_CASO = [t for t in TELAS_CASO if (TELAS_DIR / f"{t[0]}.png").exists()]
F_CASO = F_AN + 4


def fig_caso(arq: str) -> list[str]:
    k = next(i for i, t in enumerate(TELAS_CASO) if t[0] == arq) if any(t[0] == arq for t in TELAS_CASO) else None
    if k is None:
        return [nota(f"[Tela a capturar: {arq.replace('_', ' ')}.]")]
    return [figura(f"rIdCaso{k}", 80 + k, 16.0, 9.0, f"Caso {k + 1}"),
            fonte(f"Figura {F_CASO + k} – {TELAS_CASO[k][1]} (Anos Iniciais, Matemática, 2023). Fonte: painel elaborado "
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


CAP5_CASOS = [
    nota(AVISO + " A análise gerencial dos casos fica com os autores; aqui estão a escolha e os números."),
    corpo("Esta seção mostra como o painel apoia a comparação entre redes, com três casos. Os casos foram escolhidos por "
          "regras objetivas, aplicadas ao recorte padrão do painel (Anos Iniciais, Matemática, edição de 2023, comparação "
          "nacional), para ilustrar três situações de leitura: uma rede acima do esperado sem alerta, uma rede abaixo do "
          "esperado com alerta de rede parcial e uma rede acima do esperado com alerta de salto atípico. Eles ilustram o "
          "uso do painel e não formam uma amostra representativa. Os pares de cada rede são as redes do mesmo cluster "
          "com gasto por aluno entre 0,8 e 1,25 vez o dela, a mesma regra da página Pares. A Tabela "
          f"{T_CASOS} resume os três casos em 2023, e a Tabela {T_CASOS + 1} traz a série de cada um."),
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
    *fig_caso("caso_a_ficha"),
    *fig_caso("caso_a_pares"),
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
    *fig_caso("caso_b_ficha"),
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
          "com cálculo (100 de 5.240), e 16 têm salto atípico. Nesses casos, o alerta do painel sugere conferir o resultado "
          "antes de tomar a rede como referência; a marca indica uma variação fora do padrão, e não um erro."),
    nota("[Para os autores: o levantamento bibliográfico (docs/levantamento_bibliografico.md, seção 8) registrou que "
         "Alagoas distribui parte do ICMS aos municípios segundo indicadores de qualidade da educação. É contexto a "
         "considerar na interpretação, e não explicação testada; nenhum trabalho localizado aponta irregularidade nas notas. "
         "CITAR, se for usado.]"),
    *fig_caso("caso_c_ficha"),
    legenda(f"Tabela {T_CASOS + 1} – Série dos três casos por edição (Anos Iniciais, Matemática, comparação nacional)"),
    tabela(["Município", "Edição", "Gasto por aluno (R$ de 2025)", "Proficiência", "Esperada", "Em relação ao esperado",
            "Alerta"], t_serie, [1800, 800, 1500, 1300, 1300, 1375, 1000]),
    fonte("Fonte: elaborado pelos autores. Em 2025, a comparação nacional não tem cálculo, porque a série do IDHM termina "
          "em 2024; a comparação com o mesmo estado cobre essa edição."),
    titulo(3, "O que os casos mostram sobre o uso do painel"),
    corpo("Nos três casos, a leitura combina três informações do painel: o resultado em relação ao esperado, os alertas e "
          "os pares. O resultado sozinho levaria a conclusões apressadas: tomar Coruripe como modelo sem olhar o salto, ou "
          "comparar São Paulo com cidades pequenas sem considerar que a rede municipal atende menos da metade dos alunos. "
          "Os casos também ilustram um limite do indicador já apontado no Capítulo 4: na comparação nacional, o gasto quase "
          "não altera a proficiência esperada, de modo que o indicador mede, na prática, o desempenho em relação ao esperado "
          "para o contexto, e não o rendimento de cada real gasto."),
]

CAP5_VALIDACAO = [
    nota(AVISO + " Cabe aos autores e à orientadora decidir se esta seção mantém o nome de validação conceitual."),
    corpo("A ferramenta não foi testada com usuários, o que fica registrado como limitação. A validação feita tem duas "
          "partes: cenários de uso, em que cada uma das três perguntas de entrada do painel é percorrida com os casos da "
          "seção anterior, e a conferência técnica dos números. O Quadro 6 resume os cenários."),
    legenda("Quadro 6 – Cenários de uso: as perguntas de entrada do painel percorridas com dados reais"),
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
    corpo("A conferência técnica cobriu os pontos a seguir."),
    item("Números do painel contra os cálculos em Python. No recorte padrão (Brasil, Anos Iniciais, Matemática, 2023), "
         "bateram o gasto mediano por aluno (R$ 13.721), a proficiência média (220,2 pontos), a parcela de redes acima do "
         "esperado (46,3%), o número de redes com nota (5.243) e a cobertura do Saeb (94,1%), além das oito correlações da "
         "página Defasagens, da série de um município e da lista de pares de outro."),
    item("A conferência encontrou e corrigiu dois erros nas medidas do painel: a mediana do gasto contava como zero as três "
         "redes com nota e sem gasto (R$ 13.524,86 em vez de R$ 13.525,81), e a contagem de pares que entregam mais incluía "
         "dois pares sem resultado calculado (32 em vez de 30)."),
    item("As páginas do painel são geradas por script e conferidas contra os esquemas oficiais do formato do Power BI. Um "
         "teste com quatro erros inventados mostrou que todos são recusados. O esquema não confere as propriedades de "
         "formatação, que só se confirmam ao abrir o painel."),
    item("A correção pela inflação foi conferida de ponta a ponta, do valor nominal ao gasto por aluno usado no painel."),
    item("O processo é reprodutível: um comando único refaz o tratamento e os painéis de dados, e a execução completa "
         "recriou painéis idênticos aos versionados."),
    item("Os resultados dos modelos passaram pelos testes de sensibilidade da Tabela 6."),
    item("Os números dos três casos foram calculados em Python e conferidos no painel"
         + (f" (Figuras {F_CASO} a {F_CASO + len(TELAS_CASO) - 1})." if TELAS_CASO else ".")
         if len(TELAS_CASO) == 4 else "Os números dos três casos foram calculados em Python; falta conferi-los no painel."),
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
    ("[A ser detalhado por Henrique Lindoso: ingestão, limpeza", CAP4_1),
    ("[A ser detalhado por Henrique Lindoso.]", CAP4_2),
    ("[A ser detalhado por Henrique Lindoso: telas interativas", CAP4_3),
    ("[Metodologia e gráficos por Henrique Lindoso; interpretação por Guilherme Menezes.]", CAP5_CLUSTER + CAP5_MODELOS),
    ("[Análise gerencial por Guilherme Menezes.]", CAP5_CASOS),
    ("[Análise por Guilherme Menezes.]", CAP5_VALIDACAO),
    ("AVISO. Como o Capítulo 5 está em pausa", [nota(
        "[ATENÇÃO: na cópia de 2026-11-13, o Capítulo 5 saiu da pausa e tem material técnico em todas as seções. Este aviso "
        "pode sair quando as lacunas abaixo forem preenchidas pelos autores.]")]),
    ("[DEFINIR o conceito operacional de “eficiência do gasto”", [nota(
        "[Base factual para esta definição: no painel, o indicador é a diferença entre a proficiência observada e a "
        "esperada, em % da esperada. A esperada vem de uma regressão com o gasto por aluno e o contexto (ver 4.3). Não é uma "
        "medida de fronteira, como a análise envoltória de dados, em que 100% significa eficiente. O registro (decisão A10) "
        "explica por que a escala de 100% não foi usada. Ver também a nota de atenção em 4.3 sobre o peso do gasto no "
        "indicador.]")]),
    ("AVISO – SEÇÃO PENDENTE DE PESQUISA BIBLIOGRÁFICA ADICIONAL", [nota(
        "[Levantamento disponível em docs/levantamento_bibliografico.md (2026-11-11), com registros e resumos conferidos, "
        "mas textos NÃO lidos. Bloco A: Menezes-Filho e Amaral (2009); Diaz (2012); Monteiro (2015); Oliveira, Menezes Filho "
        "e Komatsu (2022); Alves e Frio (2022); Hanushek (2003); Jackson, Johnson e Persico (2016); Jackson e Mackevicius "
        "(2024). Bloco B: Menezes-Filho e Pazello (2007); Cruz e Rocha (2018); Hirata, Melo e Oliveira (2022); Silva Júnior, "
        "Miranda e Coelho (2025); Lautharte, Oliveira e Loureiro (2021). Blocos C e D: nenhuma referência conferida. Este "
        "rascunho cita Hanushek (1997); o levantamento localizou Hanushek (2003): conferir qual será usado.]")]),
    ("[INSERIR parágrafo explicando por que o ENEM e o PISA foram descartados", [nota(
        "[Base factual, do histórico do projeto: o ENEM é de adesão voluntária e inclui escolas privadas; nos microdados "
        "públicos, só de 15,6% a 27,4% dos inscritos têm escola e município identificados, e o código da escola não é "
        "divulgado. O PISA é amostral e só dá resultado nacional e por grandes regiões. O Saeb é censitário nas escolas "
        "públicas e sai por município e rede. Faltam as referências que sustentem essas afirmações.]")]),
    ("demonstrar, por simulação de cenários decisórios com dados reais", [nota(
        "[ATENÇÃO – divergência com o que foi feito: o painel não tem simulação de cenários decisórios. O que existe são as "
        "análises do Capítulo 5 (associação entre gasto e desempenho, heterogeneidade e sensibilidade) e a comparação entre "
        "redes. Ajustar este objetivo, o resumo e o Capítulo 5.]")]),
    ("Fonte: elaborado pelos autores [CONFERIR e citar a documentação oficial de cada base", [nota(
        "[ATENÇÃO – divergências do Quadro 1 com o que foi feito: (i) nenhuma base chamada SINCOP foi usada: retirar a "
        "linha; (ii) o indicador socioeconômico usado é o IDHM por UF, nas dimensões Renda e Longevidade (Atlas Brasil / "
        "Radar IDHM, de PNUD, FJP e IBGE), e não o IDH municipal nem o PIB per capita; do IBGE vêm a população e a "
        "alfabetização (Censo 2022) e o IPCA; (iii) faltam no quadro o IPCA e a Malha Municipal. O Quadro 3, no Capítulo 4, "
        "traz a lista completa.]")]),
    ("[INSERIR: levantamento dos indicadores e condicionalidades do VAAR", [nota(
        "[ATENÇÃO – divergência com o que foi feito: o painel não monitora as condicionalidades nem os indicadores do VAAR. "
        "Retirar a promessa deste capítulo, do item 1.5 e do Capítulo 6, ou tratá-la como trabalho futuro.]")]),
    ("O escopo é a educação básica pública, da educação infantil ao ensino médio", [nota(
        "[ATENÇÃO – divergência com o que foi feito: o trabalho cobre o Ensino Fundamental das redes municipais (Anos "
        "Iniciais e Finais) e os Anos Finais e o Ensino Médio das redes estaduais. A Educação Infantil está fora: o gasto "
        "municipal usado é só o da subfunção 361 (Ensino Fundamental).]")]),
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
        "indicador de eficiência é um resíduo e capta também gestão e contexto (L17); saltos atípicos de proficiência "
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
        "a Tabela 1, no Capítulo 5.]")]),
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
DOC.write_text(x, encoding="utf-8")

rels = PASTA / "word" / "_rels" / "document.xml.rels"
r = rels.read_text(encoding="utf-8")
figs = {"rIdFig1": "fig1_entre_dentro.png", "rIdFig2": "fig2_defasagens.png", "rIdFig3": "fig3_heterogeneidade.png",
        "rIdFig4": "fig4_sensibilidade.png"}
figs["rIdFluxo"] = "fig0_fluxo_dados.png"
novos = ""
for k, (arq, _) in enumerate(TELAS_CASO):
    shutil.copy(TELAS_DIR / f"{arq}.png", PASTA / "word" / "media" / f"tela_{arq}.png")
    novos += (f'<Relationship Id="rIdCaso{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/tela_{arq}.png"/>')
for k, (arq, _) in enumerate(TELAS):
    shutil.copy(TELAS_DIR / f"{arq}.png", PASTA / "word" / "media" / f"tela_{arq}.png")
    novos += (f'<Relationship Id="rIdTela{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
              f'Target="media/tela_{arq}.png"/>')
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
