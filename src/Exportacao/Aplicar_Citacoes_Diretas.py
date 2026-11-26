"""Transforma em citação direta os trechos que reproduziam o texto da lei quase literalmente (A36, 2026-11-26).

Apontados no teste do Turnitin: os 70% do Fundeb (Lei nº 14.113/2020, art. 26), o VAAR e as condicionalidades
(art. 14) e a cota do ICMS por resultados (Constituição, art. 158, § 1º, II, redação da EC nº 108/2020).
O texto entre aspas foi conferido, palavra por palavra, no site do Planalto em 2026-11-26.

Uso (na raiz do repositório): python src/Exportacao/Aplicar_Citacoes_Diretas.py <entrada.docx> <saida.docx>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

A, F = "“", "”"  # aspas curvas, como no restante do texto
ART26 = (f"{A}proporção não inferior a 70% (setenta por cento) dos recursos anuais totais dos Fundos [...] será destinada "
         f"ao pagamento, em cada rede de ensino, da remuneração dos profissionais da educação básica em efetivo exercício{F}")

TROCAS = [
    # 1.2 Situação-problema
    ("O gestor público de educação responde",
     "entre elas a destinação mínima de 70% dos recursos do fundo (excluída a complementação-VAAR) à remuneração dos "
     "profissionais da educação básica em efetivo exercício (Brasil, 2020b).",
     f"entre elas a de destinar à remuneração dos profissionais {A}proporção não inferior a 70% (setenta por cento) dos "
     f"recursos anuais totais dos Fundos{F}, excluída a complementação-VAAR (Brasil, 2020b, art. 26)."),
    # 2.1.2, alínea do VAAR
    ("o VAAR (Valor Anual por Aluno por Resultado)",
     "corresponde a 2,5 pontos percentuais e é distribuído às redes que cumprirem condicionalidades de gestão e "
     "apresentarem melhoria de indicadores de atendimento e de aprendizagem, com redução das desigualdades. As "
     "condicionalidades incluem a escolha de diretores por critérios de mérito e desempenho ou com participação da "
     "comunidade, a participação de ao menos 80% dos estudantes nas avaliações nacionais, a redução das desigualdades "
     "educacionais socioeconômicas e raciais, o regime de colaboração entre estado e municípios e referenciais "
     "curriculares alinhados à Base Nacional Comum Curricular (Brasil, 2020b, art. 14).",
     f"corresponde a 2,5 pontos percentuais. Pela lei, {A}a complementação-VAAR será distribuída às redes públicas de "
     f"ensino que cumprirem as condicionalidades e apresentarem melhoria dos indicadores referidos no inciso III do caput "
     f"do art. 5º desta Lei{F} (Brasil, 2020b, art. 14), ou seja, indicadores de atendimento e de aprendizagem, com "
     f"redução das desigualdades. As condicionalidades são cinco: a escolha dos diretores por mérito e desempenho ou com "
     f"a participação da comunidade escolar; a participação de {A}pelo menos 80% (oitenta por cento) dos estudantes{F} "
     f"nas avaliações nacionais; a {A}redução das desigualdades educacionais socioeconômicas e raciais{F}; o regime de "
     f"colaboração entre estado e municípios; e {A}referenciais curriculares alinhados à Base Nacional Comum "
     f"Curricular{F} (Brasil, 2020b, art. 14, § 1º)."),
    # 2.1.2, aplicação dos recursos
    ("Quanto à aplicação, no mínimo 70%",
     "Quanto à aplicação, no mínimo 70% dos recursos anuais totais do Fundeb, excluída a complementação-VAAR, devem ser "
     "destinados à remuneração dos profissionais da educação básica em efetivo exercício (Brasil, 2020b, art. 26).",
     f"Quanto à aplicação, excluída a complementação-VAAR, {ART26} (Brasil, 2020b, art. 26)."),
    # 2.1.3, cota do ICMS
    ("Além do Fundeb, os municípios recebem",
     "e até 35% segundo lei estadual, dos quais ao menos 10 pontos percentuais com base em indicadores de melhoria nos "
     "resultados de aprendizagem e de aumento da equidade, considerado o nível socioeconômico dos educandos (Brasil, 2020a).",
     f"e até 35% segundo lei estadual, {A}observada, obrigatoriamente, a distribuição de, no mínimo, 10 (dez) pontos "
     f"percentuais com base em indicadores de melhoria nos resultados de aprendizagem e de aumento da equidade, "
     f"considerado o nível socioeconômico dos educandos{F} (Brasil, 1988, art. 158, § 1º, II; Brasil, 2020a)."),
]

tmp, x = E.abrir(Path(sys.argv[1]))
for inicio, antigo, novo in TROCAS:
    x = E.trocar_trecho(x, inicio, antigo, novo)
E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
