"""Versão enxuta da seção 4.2: o corpo fala a língua do gestor, e o detalhe estatístico vai para o Apêndice B (A32, 2026-11-24).

- 4.2.2: dois parágrafos em linguagem simples e a Tabela 3 só com "entre municípios" e "dentro do mesmo município";
  a tabela completa (três especificações) e a investigação da edição de 2025 vão para o apêndice (Tabela B.3).
- 4.2.3: duas frases; a tabela de defasagens vira a Tabela B.4.
- 4.2.5: um parágrafo curto; a tabela de sensibilidade fica no corpo, como Tabela 4 (pedido do Henrique).
- As Tabelas 6, 7 e 8 passam a 5, 6 e 7; as chamadas no texto acompanham.

Uso (na raiz do repositório): python src/Exportacao/Enxugar_Secao_4_2.py <entrada.docx> <saida.docx>
Depois: src/Exportacao/Atualizar_Campos.ps1 na saída (sumário e listas).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

tmp, x = E.abrir(Path(sys.argv[1]))


def bloco(xml: str, titulo: str) -> tuple[int, int, str, str, str]:
    """Legenda + tabela + fonte, contíguas no corpo do texto. Devolve início, fim e as três partes."""
    leg = E.achar(xml, titulo, n=2)  # a lista de tabelas repete o título; a legenda é a última
    resto = xml[leg.end():]
    tb = re.match(r"\s*<w:tbl>.*?</w:tbl>", resto, flags=re.S)
    fo = re.match(r"\s*<w:p[ >].*?</w:p>", resto[tb.end():], flags=re.S)
    assert tb and fo and E.texto_de(fo.group(0)).startswith("Fonte:"), titulo
    fim = leg.end() + tb.end() + fo.end()
    return leg.start(), fim, leg.group(0), tb.group(0).strip(), fo.group(0).strip()


def renomear(leg: str, antigo: str, novo: str) -> str:
    assert leg.count(antigo) == 2, (antigo, leg.count(antigo))  # texto visível e entrada TC
    return leg.replace(antigo, novo)


# ── blocos que vão para o apêndice (lidos antes de mexer no corpo)
_, _, leg3, tab3, fonte3 = bloco(x, "Tabela 3 – Gasto do mesmo ano e proficiência")
_, _, leg4, tab4, fonte4 = bloco(x, "Tabela 4 – Defasagem do gasto")
_, _, leg5, tab5, fonte5 = bloco(x, "Tabela 5 – Testes de sensibilidade")
inv_2025 = E.achar(x, "A especificação de referência foi escolhida depois de uma investigação").group(0)
modelo_ap = E.achar(x, "Este apêndice reúne").group(0)

ap = [
    E.novo_par(modelo_ap, "A Tabela B.3 traz as três especificações do modelo principal da seção 4.2.2. "
               + E.texto_de(inv_2025).strip()),
    renomear(leg3, "Tabela 3 – Gasto do mesmo ano e proficiência: três especificações",
             "Tabela B.3 – Modelo principal: gasto do mesmo ano e proficiência, três especificações"), tab3, fonte3,
    renomear(leg4, "Tabela 4 – Defasagem", "Tabela B.4 – Defasagem"), tab4, fonte4,
]
# a tabela de sensibilidade fica no corpo (pedido do Henrique): passa de Tabela 5 a Tabela 4

# ── corpo: Tabela 3 enxuta (sem a especificação intermediária)
linhas = re.findall(r"<w:tr[ >].*?</w:tr>", tab3, flags=re.S)
assert len(linhas) == 4
t3 = tab3.replace(linhas[2], "", 1)
for antigo, novo in [("MQO agrupado, 2017–2023", "Entre municípios (2017–2023)"),
                     ("EF de município e de UF × edição, 2017–2025 (referência)",
                      "Dentro do mesmo município (referência, 2017–2025)")]:
    assert antigo in t3, antigo
    t3 = t3.replace(antigo, novo, 1)
f3 = fonte3.replace(
    "EF: efeito fixo. Controles: infraestrutura e log das matrículas; no MQO, também log da população e alfabetização; "
    "nas especificações de 2017–2023, IDHM Renda e Longevidade da UF.",
    "Controles: infraestrutura e log das matrículas; entre municípios, também log da população e alfabetização. "
    "A especificação intermediária e o detalhe dos controles estão na Tabela B.3, no Apêndice B.")
assert f3 != fonte3
titulo3 = "Tabela 3 – Gasto do mesmo ano e proficiência: entre municípios e dentro do mesmo município"
leg3_novo = E.novo_par(leg3, titulo3, negrito=True)
leg3_novo = leg3_novo[:-len("</w:p>")] + E.campo_tc(titulo3, "T") + "</w:p>"

i, f, *_ = bloco(x, "Tabela 3 – Gasto do mesmo ano e proficiência")
x = x[:i] + leg3_novo + t3 + f3 + x[f:]
i, f, *_ = bloco(x, "Tabela 4 – Defasagem do gasto")
x = x[:i] + x[f:]
i, f, *_ = bloco(x, "Tabela 5 – Testes de sensibilidade")
x = x[:i] + renomear(leg5, "Tabela 5 – Testes", "Tabela 4 – Testes") + x[i + len(leg5):]

# ── textos do corpo
x = E.reescrever(x, "O modelo principal estima a proficiência",
    "O modelo principal relaciona a proficiência ao gasto por aluno, levando em conta o contexto de cada rede, de duas "
    "maneiras (Tabela 3). A primeira compara municípios diferentes entre si. A segunda compara cada município com ele "
    "mesmo ao longo do tempo, e só com municípios do mesmo estado na mesma edição; é a especificação de referência do "
    "trabalho. Os modelos foram estimados em Python, em scripts desenvolvidos com o auxílio da IA a partir das "
    "especificações definidas pelos autores; o detalhe das especificações está na Tabela B.3, no Apêndice B.")
x = E.reescrever(x, "Entre os municípios, com os controles de contexto",
    "Entre municípios diferentes, o gasto quase não se associa à nota: o coeficiente não se distingue de zero. Quando "
    "cada município é comparado com ele mesmo, a associação é positiva nas duas etapas e nas duas disciplinas, mas "
    "pequena: 10% a mais de gasto por aluno acompanham cerca de 0,2 ponto a mais em Matemática nos Anos Iniciais, e "
    "dobrar o gasto acompanha cerca de 1,6 ponto, menos de 7% da diferença típica entre as redes (desvio-padrão de 24,2 "
    "pontos). Para comparação, a média das redes municipais em Matemática vai de 220,2 pontos no 5º ano a 249,3 pontos "
    "no 9º ano (2023).")
x = E.reescrever(x, "A especificação de referência foi escolhida depois de uma investigação",
    "A comparação dentro do mesmo estado e da mesma edição foi adotada porque, de 2023 a 2025, as redes do Nordeste e "
    "do Norte tiveram ao mesmo tempo o maior aumento de gasto e o maior ganho de nota, o que inflava a associação; com "
    "ela, o resultado fica estável, com ou sem 2025 (Apêndice B).")
x = E.reescrever(x, "A Tabela 4 compara o gasto do ano da prova",
    "O Saeb é aplicado a cada dois anos. Dentro do município, o que acompanha a nota é o gasto dos dois anos do ciclo "
    "da prova, o do ano da prova e o do ano anterior; o gasto de antes do ciclo não se associa de forma significativa "
    "(Tabela B.4, no Apêndice B).")
x = E.reescrever(x, "A Tabela 5 mostra a associação dentro do município",
    "Para verificar se o resultado depende de alguma escolha do método, a estimativa foi refeita mudando uma escolha de "
    "cada vez: sem a edição de 2021, da pandemia; só com os municípios com nota em todas as edições; com o gasto médio "
    "dos dois anos do ciclo; sem as redes municipais parciais; sem os saltos atípicos de nota; e com outras formas de "
    "controlar o contexto. Em todos os testes, a associação dentro do município continua positiva e significativa, "
    "entre 1,4 e 5,5 pontos por log do gasto (Tabela 4). Com o gasto médio dos dois anos do ciclo, o coeficiente é "
    "cerca de 60% maior que o da referência no mesmo período.")
x = E.trocar_trecho(x, "A conferência técnica, feita com o auxílio da IA",
                    "passaram pelos testes de sensibilidade da Tabela 5.",
                    "passaram pelos testes de sensibilidade da Tabela 4.")

# ── tabelas seguintes sobem um número (texto visível e entradas TC); em sequência, sem colisão
for a, b in [("6", "5"), ("7", "6"), ("8", "7")]:
    x = re.sub(rf"Tabela {a}(?!\d)", f"Tabela {b}", x)

# ── apêndice: depois da Tabela B.2
x = E.trocar_trecho(x, "Este apêndice reúne", "(Tabelas B.1 e B.2)",
                    "(Tabelas B.1 e B.2), o detalhe do modelo principal e da defasagem do gasto (Tabelas B.3 e B.4)")
_, fim_b2, *_ = bloco(x, "Tabela B.2 – Camada estadual")
x = x[:fim_b2] + "".join(ap) + x[fim_b2:]

E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
