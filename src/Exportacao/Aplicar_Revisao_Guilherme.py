"""Aplica, na versão revisada pelo Guilherme (2026-11-19), as respostas aos comentários dele (registro A29).

A partir desta revisão, o documento principal é o arquivo editado pelos autores, e não mais a saída do montador
(Montar_Copia_Rascunho.py): este script edita o .docx deles diretamente, parágrafo a parágrafo, e retira os comentários
já respondidos. Depois, rodar Atualizar_Campos.ps1 na saída, para refazer o sumário e as listas.

Uso: python src/Exportacao/Aplicar_Revisao_Guilherme.py <entrada.docx> <saida.docx>
"""
import html
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ENTRADA, SAIDA = Path(sys.argv[1]), Path(sys.argv[2])
tmp = Path(tempfile.mkdtemp())
with zipfile.ZipFile(ENTRADA) as z:
    z.extractall(tmp)
DOC = tmp / "word" / "document.xml"
x = DOC.read_text(encoding="utf-8")


def texto_de(par: str) -> str:
    return html.unescape("".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", par, flags=re.S)))


def pars(xml: str):
    tbs = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S)]
    return [m for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, flags=re.S) if not any(a <= m.start() < b for a, b in tbs)]


def achar(xml: str, inicio: str, n: int = 1, depois_de: int = 0) -> re.Match:
    ach = [m for m in pars(xml) if m.start() >= depois_de and texto_de(m.group(0)).strip().startswith(inicio)]
    assert len(ach) == n, f"esperava {n}, achei {len(ach)}: {inicio[:60]}"
    return ach[-1]


def intro(xml: str) -> int:
    return [m.start() for m in pars(xml) if "Ttulo1" in m.group(0) or "Heading1" in m.group(0)
            if texto_de(m.group(0)).strip() == "INTRODUÇÃO"][-1]


def partes(par: str):
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", par, flags=re.S)
    ppr = ppr.group(0) if ppr else ""
    rpr = re.search(r"<w:r[ >](?:(?!</w:r>).)*?(<w:rPr>.*?</w:rPr>)", par, flags=re.S)
    rpr = rpr.group(1) if rpr else ""
    rpr = re.sub(r"<w:highlight [^>]*/>|<w:b/>|<w:bCs/>|<w:b w:val=\"[^\"]*\"/>|<w:bCs w:val=\"[^\"]*\"/>|<w:i/>|<w:iCs/>"
                 r"|<w:rStyle [^>]*/>", "", rpr)
    return ppr, rpr


def runs(texto: str, rpr: str) -> str:
    """Texto em runs; **trecho** em negrito, *trecho* em itálico, [MARCA...] em realce amarelo."""
    out = ""
    for k, s in enumerate(texto.split("**")):
        for j, s2 in enumerate(s.split("*")):
            for p in re.split(r"(\[[A-ZÇÃÉÍ]{5,}[^\]]*\])", s2):
                if not p:
                    continue
                r = rpr or "<w:rPr></w:rPr>"
                if k % 2:
                    r = r.replace("<w:rPr>", "<w:rPr><w:b/><w:bCs/>", 1)
                if j % 2:
                    r = r.replace("<w:rPr>", "<w:rPr><w:i/><w:iCs/>", 1)
                if p.startswith("["):
                    r = r.replace("</w:rPr>", '<w:highlight w:val="yellow"/></w:rPr>')
                out += f'<w:r>{r}<w:t xml:space="preserve">{escape(p)}</w:t></w:r>'
    return out


def novo_par(modelo: str, texto: str) -> str:
    ppr, rpr = partes(modelo)
    ppr = re.sub(r"<w:sectPr.*?</w:sectPr>", "", ppr, flags=re.S)
    return "<w:p>" + ppr + runs(texto, rpr) + "</w:p>"


def reescrever(xml: str, inicio: str, texto: str, n: int = 1) -> str:
    m = achar(xml, inicio, n)
    return xml[:m.start()] + novo_par(m.group(0), texto) + xml[m.end():]


def inserir_depois(xml: str, inicio: str, blocos: list[str], n: int = 1) -> str:
    m = achar(xml, inicio, n)
    return xml[:m.end()] + "".join(blocos) + xml[m.end():]


def corpo_como(xml: str, inicio: str, texto: str) -> str:
    return novo_par(achar(xml, inicio).group(0), texto)


def trocar_trecho(xml: str, inicio: str, antigo: str, novo: str) -> str:
    m = achar(xml, inicio)
    t = texto_de(m.group(0)).strip()
    assert antigo in t, (inicio[:40], antigo)
    return xml[:m.start()] + novo_par(m.group(0), t.replace(antigo, novo)) + xml[m.end():]


# ── 0. comentários: todos respondidos (ver o registro A29); saem as marcas do texto e o conteúdo dos arquivos
x = re.sub(r'<w:commentRangeStart w:id="\d+"/>|<w:commentRangeEnd w:id="\d+"/>', "", x)
x = re.sub(r"<w:r(?: [^>]*)?>(?:<w:rPr>(?:(?!</w:r>).)*?</w:rPr>)?<w:commentReference w:id=\"\d+\"/></w:r>", "", x, flags=re.S)
assert "commentReference" not in x
for nome, raiz in [("comments.xml", "w:comments"), ("commentsExtended.xml", "w15:commentsEx"),
                   ("commentsIds.xml", "w16cid:commentsIds"), ("commentsExtensible.xml", "w16cex:commentsExtensible")]:
    f = tmp / "word" / nome
    if f.exists():
        c = f.read_text(encoding="utf-8")
        m = re.search(rf"<{raiz}[^>]*>", c)
        f.write_text(c[:m.end()] + f"</{raiz}>", encoding="utf-8")

# ── 1. resumo e abstract: periodicidade das bases [comentário 1]
x = trocar_trecho(x, "O financiamento da educação básica pública brasileira mobiliza",
                  "de 2017 a 2025, em painéis de dados municipal e estadual",
                  "de 2017 a 2025, em painéis de dados municipal e estadual (o gasto é anual, e o Saeb, bienal)")
x = trocar_trecho(x, "The financing of Brazilian public basic education", "from 2017 to 2025 were integrated into municipal "
                  "and state panels", "from 2017 to 2025 were integrated into municipal and state panels (spending is "
                  "annual; Saeb is biennial)")

# ── 2. Introdução: composição do Fundeb [4], Ideb e pontos do Saeb [5, 6], pergunta [9], objetivos [11, 12], contribuição [14]
x = reescrever(x, "A educação básica pública brasileira é financiada por um arranjo federativo complexo.",
    "A educação básica pública brasileira é financiada por um arranjo federativo complexo. A Constituição Federal obriga "
    "estados, Distrito Federal e municípios a aplicarem, no mínimo, 25% da receita resultante de impostos e "
    "transferências na manutenção e desenvolvimento do ensino (MDE) (Brasil, 1988, art. 212). Desde a Emenda "
    "Constitucional nº 108/2020, o Fundo de Manutenção e Desenvolvimento da Educação Básica e de Valorização dos "
    "Profissionais da Educação (Fundeb) é instrumento permanente de financiamento. Em cada estado, o fundo é formado por "
    "20% de um conjunto de impostos e transferências de estados e municípios, como o ICMS, o IPVA e as cotas dos fundos "
    "de participação, e é repartido entre a rede estadual e as redes municipais segundo as matrículas; a União "
    "complementa esses recursos com, no mínimo, 23% do total, nas modalidades VAAF, VAAT e VAAR (Brasil, 2020a, 2020b). "
    "Trata-se de um volume expressivo de recursos públicos: para 2025, a receita do Fundeb foi estimada em R$ 339 "
    "bilhões, dos quais R$ 58,8 bilhões de complementação da União (Brasil, 2025).")
x = reescrever(x, "Em paralelo, os resultados de aprendizagem seguem como desafio central.",
    "Em paralelo, os resultados de aprendizagem seguem como desafio central. O Índice de Desenvolvimento da Educação "
    "Básica (Ideb), numa escala de 0 a 10, combina a nota padronizada dos alunos no Sistema de Avaliação da Educação "
    "Básica (Saeb) com a taxa de aprovação. Segundo a divulgação do Ideb 2025, a rede pública alcançou 6,1 nos anos "
    "iniciais do ensino fundamental, 5,0 nos anos finais e 4,3 no ensino médio (Instituto Nacional de Estudos e Pesquisas "
    "Educacionais Anísio Teixeira [Inep], 2026b). Os resultados também são desiguais entre redes com recursos parecidos: "
    "em 2023, as redes municipais do Ceará e da Bahia gastaram praticamente o mesmo por aluno, mas a proficiência média em "
    "Matemática nos Anos Iniciais foi de 242,4 pontos no Ceará e de 200,1 na Bahia (Capítulo 4). Esses pontos são a média "
    "dos alunos de cada rede na escala de proficiência do Saeb, que é a mesma em todas as edições; para comparação, a "
    "média das redes municipais do país foi de 220,2 pontos, e oito em cada dez redes ficaram entre 188 e 251 pontos.")
x = reescrever(x, "O gasto público por aluno se associa ao desempenho das redes públicas de ensino no Saeb e,",
    "O gasto público por aluno se associa ao desempenho das redes públicas de ensino no Saeb? Considerando o gasto e o "
    "contexto de cada rede, quais redes entregam mais ou menos do que o esperado?")
x = reescrever(x, "estimar a associação entre o gasto por aluno e a proficiência, entre municípios e dentro do mesmo",
    "estimar a associação entre o gasto por aluno e a proficiência, comparando os municípios entre si e cada município "
    "com ele mesmo ao longo do tempo, com o gasto do ano da prova e de anos anteriores;")
x = reescrever(x, "aplicar o painel à comparação entre as redes municipais do Ceará e da Bahia",
    "aplicar o painel à comparação entre redes municipais de estados diferentes, o que levou à análise do Ceará e da "
    "Bahia, e a três estudos de caso.")
x = reescrever(x, "Contribuição teórica.",
    "**Contribuição teórica.** O trabalho acrescenta evidência recente, de 2017 a 2025, à literatura brasileira sobre "
    "gasto e desempenho. Ele usa dois tipos de comparação: entre municípios diferentes, que mostra se os que gastam mais "
    "têm notas maiores, e de cada município com ele mesmo ao longo do tempo, que mostra se a nota acompanha as variações "
    "do gasto. Também aproxima essa literatura da de gestão pública baseada em evidências, ao propor um indicador de "
    "desempenho em relação ao esperado para uso gerencial (seção 2.2).")

# ── 3. Revisão: composição e repartição do Fundeb [21]; nova 2.1.3 sobre a cota do ICMS [3, 31]
x = reescrever(x, "O Fundeb é um fundo de natureza contábil",
    "O Fundeb é um fundo de natureza contábil, de âmbito estadual: há um por estado e um no Distrito Federal. Cada fundo "
    "é formado por 20% de um conjunto de receitas de estados e municípios: o ICMS, o IPVA, o ITCMD, as cotas do Fundo de "
    "Participação dos Estados e do Fundo de Participação dos Municípios, a parcela do ITR devida aos municípios, a "
    "parcela do IPI-Exportação e a dívida ativa desses tributos (Brasil, 2020b, art. 3º). Os recursos de cada fundo são "
    "repartidos entre o governo estadual e os municípios segundo o número de matrículas presenciais na educação básica "
    "pública, ponderadas por etapa, modalidade, jornada e tipo de estabelecimento (Brasil, 2020b, arts. 7º, 8º e 11). "
    "A maior parte do dinheiro vem, portanto, dos próprios estados e municípios: dos R$ 339 bilhões estimados para 2025, "
    "cerca de 83% vinham dessas receitas, e R$ 58,8 bilhões da complementação da União (Brasil, 2025). O fundo foi "
    "tornado permanente pela Emenda Constitucional nº 108/2020, regulamentada pela Lei nº 14.113/2020 e alterada pela Lei "
    "nº 14.276/2021 (Brasil, 2020a, 2020b, 2021).")
h_fundeb = achar(x, "O Novo Fundeb").group(0)
ppr_h, rpr_h = partes(h_fundeb)
TITULO_ICMS = "<w:p>" + ppr_h + runs("A cota municipal do ICMS e os resultados educacionais", rpr_h) + "</w:p>"
ICMS = [TITULO_ICMS] + [corpo_como(x, "A União complementa o fundo com", t) for t in [
    "Além do Fundeb, os municípios recebem dos estados 25% da arrecadação do ICMS, a chamada cota-parte municipal "
    "(Brasil, 1988, art. 158). Pela regra em vigor desde a Emenda Constitucional nº 108/2020, no mínimo 65% dessa cota é "
    "distribuída na proporção do valor adicionado em cada município, e até 35% segundo lei estadual, dos quais ao menos 10 "
    "pontos percentuais com base em indicadores de melhoria nos resultados de aprendizagem e de aumento da equidade, "
    "considerado o nível socioeconômico dos educandos (Brasil, 2020a). Os estados tiveram dois anos, até agosto de 2022, "
    "para aprovar essas leis.",
    "O mecanismo segue uma lógica diferente da dos fundos redistributivos. Enquanto o Fundeb e a complementação-VAAT "
    "dirigem mais recursos às redes de menor capacidade de financiamento, a cota do ICMS premia os municípios que melhoram "
    "os resultados: quem entrega mais recebe mais, embora a exigência de considerar o nível socioeconômico atenue essa "
    "diferença. Além disso, o valor recebido não é vinculado à educação: entra no caixa geral do município, e só a parcela "
    "exigida pela vinculação constitucional vai obrigatoriamente para a MDE. A Lei nº 14.113/2020 reforçou esse desenho "
    "ao incluir, entre as condicionalidades do VAAR, o regime de colaboração entre o estado e os municípios previsto na "
    "mesma emenda (Brasil, 2020b, art. 14).",
    "O modelo foi inspirado no Ceará, que distribui parte da cota do ICMS segundo resultados educacionais desde 2007 "
    "(Sasso et al., 2021). O efeito dessa política sobre a aprendizagem é discutido em 2.2.4.",
]]
m_caq = achar(x, "A Emenda Constitucional nº 108/2020 também inscreveu")
x = x[:m_caq.end()] + "".join(ICMS) + x[m_caq.end():]
x = trocar_trecho(x, "Alves e Soares (2013) mostraram", "como discutido em 2.1.4", "como discutido em 2.1.5")
# eficiência técnica [24]
x = trocar_trecho(x, "Em sentido econômico, eficiência é a relação", "uma unidade é eficiente quando",
                  "uma unidade é tecnicamente eficiente quando")
# Fundef: o estudo usa variação externa [28]
x = trocar_trecho(x, "O Fundef, antecessor do Fundeb,", "(Menezes-Filho & Pazello, 2007),",
                  "(Menezes-Filho & Pazello, 2007), resultado obtido com a reforma do financiamento como fonte de variação "
                  "externa, e não por simples correlação,")
# 2.2.4: o mecanismo passou a 2.1.3; efeito ainda pouco visível nos dados [31]
x = reescrever(x, "A Emenda Constitucional nº 108/2020 estendeu esse desenho ao país",
    "Com a Emenda Constitucional nº 108/2020, esse desenho passou a valer para todos os estados (ver 2.1.3). Como as leis "
    "estaduais tinham até 2022 para ser aprovadas, as edições do Saeb usadas neste trabalho ainda captam pouco do seu "
    "efeito, que fica como sugestão de pesquisa futura. Incentivos ligados a indicadores podem, porém, produzir variações "
    "bruscas de resultado, o que justifica tratá-las com cautela, como faz a marca de saltos atípicos do painel, sem supor "
    "irregularidade.")
# 2.2.5: o pacote sugerido pela orientadora [33]
x = trocar_trecho(x, "No Brasil, a plataforma QEdu Gestão", "(Edunomics Lab, s.d.).",
                  "(Edunomics Lab, s.d.). Para o acesso aos dados, o pacote educabR, para a linguagem R, baixa e organiza "
                  "dados públicos do Inep, como o Censo Escolar, o Saeb e o Ideb (Bissoli, 2026).")
m_tab = next((m for m in re.finditer(r"<w:tr[ >].*?</w:tr>", x, flags=re.S)
              if texto_de(m.group(0)).startswith("NERD$ (Edunomics Lab)")), None)
assert m_tab, "linha do NERD$ no Quadro 1 não encontrada"
linha = m_tab.group(0)
celulas = re.findall(r"<w:tc>.*?</w:tc>", linha, flags=re.S)
valores = ["educabR (Bissoli, 2026)", "Pacote em R que baixa e organiza dados públicos do Inep",
           "Bases públicas do Inep", "Gasto por aluno (SIOPE e Siconfi), indicador e painel"]
nova = linha
for c, v in zip(celulas, valores):
    p0 = re.search(r"<w:p[ >].*?</w:p>", c, flags=re.S).group(0)
    nova = nova.replace(c, re.sub(r"<w:p[ >].*?</w:p>", lambda _: novo_par(p0, v), c, count=1, flags=re.S), 1)
x = x[:m_tab.end()] + nova + x[m_tab.end():]

# ── 4. Método 3.4: acordo com a orientadora [50]; Gemini também usado [51]
x = reescrever(x, "O trabalho usou inteligência artificial (IA) generativa",
    "Em acordo com a orientadora, e como prevê o Manual de TCC (Departamento de Administração FEA/USP, 2025), o trabalho "
    "usou inteligência artificial (IA) generativa. A principal ferramenta foi o Claude, modelo de linguagem da Anthropic "
    "(Anthropic, 2026), usado em conversas e, a partir de outubro de 2026, pelo Claude Code, que lê e escreve arquivos no "
    "repositório do projeto e executa os scripts. O Gemini, do Google (Google, 2026), também foi usado, sobretudo em "
    "pesquisas, no levantamento bibliográfico, em algumas análises e na redação. Ao longo do texto, cada etapa feita com o "
    "auxílio da IA é indicada no próprio parágrafo. As etapas foram as seguintes.")

# ── 5. Resultados: leitura em termos práticos (item 6), Spearman [58], "respectivamente" [75]
x = inserir_depois(x, "O percentual de redes acima do esperado, na comparação nacional, varia entre os", [corpo_como(x,
    "O percentual de redes acima do esperado, na comparação nacional, varia entre os",
    "Em termos práticos, o agrupamento separa os municípios em sete grupos de realidades parecidas, como os municípios "
    "pequenos do Nordeste com alfabetização mais baixa ou as cidades médias do Sudeste. É dentro desses grupos que o painel "
    "procura os pares de cada rede, para que ela seja comparada com redes em condições semelhantes, e não com o país "
    "inteiro.")])
x = inserir_depois(x, "Esta seção examina a associação entre o gasto por aluno e a proficiência.", [corpo_como(x,
    "Esta seção examina a associação entre o gasto por aluno e a proficiência.",
    "Em termos práticos, a seção responde a três perguntas. A primeira é se os municípios que gastam mais por aluno têm "
    "notas maiores: têm um pouco, mas a diferença se explica quase toda pelo contexto, porque os municípios mais ricos e "
    "mais escolarizados gastam mais e também têm notas maiores. A segunda é se, quando um mesmo município aumenta o gasto, "
    "a nota acompanha: acompanha, mas pouco, cerca de 0,2 ponto a cada 10% a mais de gasto. A terceira é se isso vale "
    "para todos: vale mais para os municípios pequenos e para o Nordeste e o Norte.")])
x = trocar_trecho(x, "A correlação de Spearman entre o gasto por aluno e a proficiência", "de 0,46 em 2017 para 0,16 em 2025",
                  "de 0,46 em 2017, uma correlação moderada, para 0,16 em 2025, uma correlação fraca")
x = trocar_trecho(x, "Na camada estadual, a comparação só faz sentido no Ensino Médio.", "de R$ 15.966 e R$ 16.988.",
                  "de R$ 15.966 e R$ 16.988, respectivamente.")

# ── 6. Conclusões: pergunta [88] e objetivos [89]
x = trocar_trecho(x, "O trabalho partiu da pergunta:", "no Saeb e, considerando o gasto e o contexto de cada rede, quais",
                  "no Saeb? Considerando o gasto e o contexto de cada rede, quais")
x = trocar_trecho(x, "O objetivo geral foi atingido:", "e a aplicação ao Ceará e à Bahia e aos estudos de caso, nas seções "
                  "4.3 e 4.4.", "e a aplicação do painel, na comparação entre redes de estados diferentes (seção 4.3) e "
                  "nos estudos de caso (seção 4.4).")

# ── 7. agradecimentos do Henrique ainda a escrever
x = reescrever(x, "De Henrique:", "De Henrique: [PERSONALIZAR: agradecimentos do Henrique.]")

# ── 8. referências novas (Google) em ordem alfabética: antes de Hanushek
ref_modelo = achar(x, "Hanushek, E. A. (1997)").group(0)
x = x.replace(ref_modelo, novo_par(ref_modelo, "Google. (2026). *Gemini* [Modelo de linguagem de grande escala]. "
                                   "https://gemini.google.com") + ref_modelo, 1)

DOC.write_text(x, encoding="utf-8")
SAIDA.parent.mkdir(parents=True, exist_ok=True)
if SAIDA.exists():
    SAIDA.unlink()
with zipfile.ZipFile(SAIDA, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(tmp / "[Content_Types].xml", "[Content_Types].xml")
    for f in sorted(tmp.rglob("*")):
        if f.is_file() and f.name != "[Content_Types].xml":
            z.write(f, f.relative_to(tmp).as_posix())
shutil.rmtree(tmp, ignore_errors=True)
print(f"[OK] {SAIDA}")
