"""Ajusta o documento principal ao Modelo de TCC Científico EAD FEA 2025 (registro A30, 2026-11-23).

1. Títulos dos capítulos como no modelo; "Estrutura do trabalho" acompanha.
2. Delimitação do estudo na Introdução (método, bases e análise em poucas linhas).
3. Item 3.5: técnicas de análise e matriz de amarração metodológica (Mazzon, 2018), com um quadro novo.
4. Item 4.6: discussão dos resultados e implicações.
5. Abstract com a mesma formatação do resumo.

Uso (na raiz do repositório): python src/Exportacao/Aplicar_Modelo_Cientifico.py <entrada.docx> <saida.docx>
Depois: src/Exportacao/Atualizar_Campos.ps1 na saída (sumário e listas).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

tmp, x = E.abrir(Path(sys.argv[1]))

# ── 1. títulos dos capítulos (só o título no corpo; o sumário é refeito pelo Word)
for antigo, novo in [("REVISÃO BIBLIOGRÁFICA", "REVISÃO DA LITERATURA"), ("MÉTODO", "PROCEDIMENTOS METODOLÓGICOS"),
                     ("RESULTADOS E DISCUSSÃO", "ANÁLISES E RESULTADOS"),
                     ("CONCLUSÕES, LIMITAÇÕES E SUGESTÕES DE PESQUISA FUTURA", "CONSIDERAÇÕES FINAIS")]:
    x = E.reescrever(x, antigo, novo, exato=True)
x = E.reescrever(x, "O trabalho organiza-se em cinco capítulos.",
    "O trabalho organiza-se em cinco capítulos. Este primeiro capítulo apresenta o contexto, o problema, a pergunta, os "
    "objetivos e a delimitação do estudo. O Capítulo 2 reúne a revisão da literatura e a caracterização das bases "
    "oficiais. O Capítulo 3 descreve os procedimentos metodológicos: as fontes e a integração dos dados, as regras de "
    "tratamento, o painel, o uso de inteligência artificial e as técnicas de análise. O Capítulo 4 apresenta as análises "
    "e os resultados (o agrupamento dos municípios por contexto, a associação entre gasto e desempenho, a comparação "
    "entre Ceará e Bahia, os estudos de caso e a validação do painel) e os discute à luz da literatura. O Capítulo 5 traz "
    "as considerações finais: as conclusões, as contribuições, as limitações e as sugestões de pesquisa futura.")

# ── 2. delimitação do estudo, como item da Introdução, antes das contribuições
h2 = E.achar(x, "Objetivos", exato=True).group(0)
corpo_intro = E.achar(x, "No formato de método científico, os objetivos são de descoberta").group(0)
x = E.antes_de(x, "Contribuições teóricas e práticas", [
    E.novo_par(h2, "Delimitação do estudo"),
    E.novo_par(corpo_intro,
        "Trata-se de um estudo quantitativo, com dados secundários e públicos. A base reúne o gasto por aluno das redes "
        "municipais e estaduais (SIOPE e Siconfi), a proficiência no Saeb, as matrículas e a infraestrutura do Censo "
        "Escolar e o contexto socioeconômico (IBGE e IDHM), nas edições de 2017 a 2025, para cerca de 5.500 redes "
        "municipais e as 27 redes estaduais. A análise combina correlação, regressões que comparam cada município com ele "
        "mesmo ao longo do tempo, o agrupamento dos municípios por contexto e um painel de Business Intelligence; os "
        "procedimentos estão detalhados no Capítulo 3. O estudo cobre o Ensino Fundamental das redes municipais e os Anos "
        "Finais e o Ensino Médio das redes estaduais, e os resultados indicam associação, e não efeito causal."),
], exato=True)

# ── 3. item 3.5: técnicas de análise e matriz de amarração
# os quadros dos Capítulos 4 sobem um número, porque o quadro novo entra antes deles (texto visível e entradas TC)
x = x.replace("Quadro 6", "Quadro 7").replace("Quadro 5", "Quadro 6")
x = E.trocar_trecho(x, "Este capítulo descreve o método", "; e a seção 3.4, o uso de inteligência artificial no trabalho.",
                    "; a seção 3.4, o uso de inteligência artificial no trabalho; e a seção 3.5, as técnicas de análise e a "
                    "matriz que liga cada objetivo aos dados e às técnicas.")
x = E.trocar_trecho(x, "Este capítulo descreve o método", "Este capítulo descreve o método do trabalho",
                    "Este capítulo descreve os procedimentos metodológicos do trabalho")
h_ia = E.achar(x, "Uso de inteligência artificial", exato=True).group(0)
corpo_ia = E.achar(x, "A IA não tomou decisões de pesquisa").group(0)
# a lista de quadros repete o título; a legenda é a última ocorrência
leg_q1 = E.achar(x, "Quadro 1 – Trabalhos e ferramentas semelhantes", n=2).group(0)
fonte_q1 = [m for m in E.pars(x) if E.texto_de(m.group(0)).strip() == "Fonte: elaborado pelos autores."][0].group(0)
tab_q1 = next(m.group(0) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", x, flags=re.S)
              if E.texto_de(m.group(0)).startswith("Trabalho ou ferramenta"))
linhas = re.findall(r"<w:tr[ >].*?</w:tr>", tab_q1, flags=re.S)


def linha_nova(modelo: str, valores: list[str]) -> str:
    out = modelo
    for c, v in zip(re.findall(r"<w:tc>.*?</w:tc>", modelo, flags=re.S), valores):
        p0 = re.search(r"<w:p[ >].*?</w:p>", c, flags=re.S).group(0)
        cel = c[:c.index(p0)] + E.novo_par(p0, v) + "</w:tc>"
        out = out.replace(c, cel, 1)
    return out


MATRIZ = [
    ["a) Integrar as bases de gasto, desempenho, oferta e contexto", "SIOPE, Siconfi, Saeb, Censo Escolar, IBGE, IDHM e "
     "IPCA", "Extração, tratamento e integração em Python; correção pelo IPCA", "Seções 3.1 e 3.2"],
    ["b) Estimar a associação entre gasto por aluno e proficiência", "Painéis municipal e estadual, 2017–2025",
     "Correlação de Spearman; regressões com efeito fixo de município e de UF e edição; testes de sensibilidade",
     "Seção 4.2"],
    ["c) Construir o indicador e o painel", "Painel municipal e grupos de contexto",
     "Regressão da proficiência esperada; k-médias; Power BI", "Seções 3.3 e 4.1"],
    ["d) Aplicar o painel a redes de estados diferentes e a estudos de caso", "Redes municipais, 2023",
     "Comparação descritiva (Ceará e Bahia); casos escolhidos por regras objetivas; cenários de uso",
     "Seções 4.3, 4.4 e 4.5"],
]
tab = tab_q1.replace(linhas[0], linha_nova(linhas[0], ["Objetivo específico", "Dados", "Técnica", "Resultados"]), 1)
tab = tab.replace("".join(linhas[1:]), "".join(linha_nova(linhas[1], v) for v in MATRIZ), 1)
titulo_q = "Quadro 5 – Matriz de amarração metodológica"
leg = E.novo_par(leg_q1, titulo_q, negrito=True)
leg = leg[:-len("</w:p>")] + E.campo_tc(titulo_q, "Q") + "</w:p>"
x = E.depois_de(x, "A IA não tomou decisões de pesquisa", [
    E.novo_par(h_ia, "Técnicas de análise e matriz de amarração metodológica"),
    E.novo_par(corpo_ia,
        "O trabalho é um estudo quantitativo, com dados secundários de bases públicas que cobrem todas as redes "
        "municipais com nota divulgada no Saeb e as 27 redes estaduais (seções 3.1 e 3.2). Quatro técnicas foram usadas. "
        "A correlação de postos de Spearman mede a associação simples entre o gasto por aluno e a proficiência em cada "
        "edição. Regressões por mínimos quadrados ordinários, com erros-padrão agrupados por município, estimam essa "
        "associação controlando o contexto, em três especificações: entre municípios; com efeito fixo de município, que "
        "compara cada município com ele mesmo ao longo do tempo; e com efeito de UF e edição, que compara municípios do "
        "mesmo estado na mesma edição. O agrupamento por k-médias forma os grupos de contexto usados para comparar redes "
        "parecidas. Por fim, o resíduo da regressão nacional dá o desempenho em relação ao esperado, mostrado no painel "
        "(seção 3.3)."),
    E.novo_par(corpo_ia,
        "O Quadro 5 resume a matriz de amarração metodológica (Mazzon, 2018): para cada objetivo específico, os dados, a "
        "técnica e a seção em que os resultados são apresentados."),
    leg, tab, fonte_q1,
])
ref_m = E.achar(x, "Menezes-Filho, N., & Amaral").group(0)
x = x.replace(ref_m, E.novo_par(ref_m, "Mazzon, J. A. (2018). Using the methodological association matrix in marketing "
                                "studies. *Revista Brasileira de Marketing, 17*(5), 747–770.") + ref_m, 1)

# ── 4. item 4.6: discussão dos resultados e implicações (fim do capítulo de resultados)
h_val = E.achar(x, "Validação conceitual da ferramenta", exato=True).group(0)
corpo_val = E.achar(x, "A conferência técnica, feita com o auxílio da IA").group(0)
x = E.depois_de(x, "A conferência técnica, feita com o auxílio da IA", [
    E.novo_par(h_val, "Discussão dos resultados e implicações"),
    E.novo_par(corpo_val,
        "Os resultados dialogam com a literatura em três pontos. Primeiro, a associação pequena entre gasto e desempenho "
        "entre municípios, que quase desaparece quando se controla o contexto, está em linha com Hanushek (1997, 2003) e "
        "com Menezes-Filho e Amaral (2009). A associação positiva quando cada município é comparado com ele mesmo, maior "
        "nos municípios pequenos e nas regiões mais pobres, aproxima-se dos estudos que encontram efeitos do gasto "
        "sobretudo para populações mais pobres (Jackson et al., 2016; Jackson & Mackevicius, 2024); o tamanho, porém, é "
        "menor que o desses estudos, que isolam variações do gasto externas às redes, o que o desenho deste trabalho não "
        "faz."),
    E.novo_par(corpo_val,
        "Segundo, a distância entre Ceará e Bahia, com gasto praticamente igual, reforça a leitura de que a gestão e os "
        "incentivos pesam mais do que o volume de recursos (Oliveira et al., 2022) e é compatível com os efeitos "
        "atribuídos às políticas do Ceará (Lautharte et al., 2021), explicação que o trabalho não testa. Terceiro, a "
        "comparação dentro de grupos de contexto confirma o argumento de Alves e Soares (2013): sem considerar o contexto, "
        "redes que atendem populações mais vulneráveis ficariam sistematicamente abaixo, e o percentual de redes acima do "
        "esperado varia de 40% a 59% entre os grupos."),
    E.novo_par(corpo_val,
        "As implicações são de três tipos. Para a teoria, o trabalho mostra, com dados de 2017 a 2025 e já sob o Novo "
        "Fundeb, que a pergunta relevante é menos quanto se gasta e mais como o recurso é usado. Para a prática, o painel "
        "permite ao gestor localizar redes parecidas que entregam mais e investigar o que elas fazem, em vez de tomar o "
        "volume de gasto como medida de qualidade. Para a política pública, a combinação de fundos redistributivos, como "
        "o Fundeb, com incentivos a resultados, como a cota do ICMS (seção 2.1.3), indica que o desenho dos repasses pode "
        "pesar tanto quanto o seu valor; os alertas do painel lembram, porém, que incentivos ligados a indicadores pedem "
        "cautela na leitura de saltos de nota."),
])

# ── 5. abstract com a formatação do resumo (justificado, espaçamento 1,5)
m = E.achar(x, "The financing of Brazilian public basic education")
p = m.group(0)
ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, flags=re.S).group(0)
novo = ppr.replace('<w:spacing w:before="1"/>', '<w:spacing w:before="1" w:line="360" w:lineRule="auto"/>', 1)
if '<w:jc ' not in novo:
    novo = novo.replace("<w:rPr>", '<w:jc w:val="both"/><w:rPr>', 1)
assert novo != ppr, "abstract com formato inesperado"
x = x[:m.start()] + p.replace(ppr, novo, 1) + x[m.end():]

E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
