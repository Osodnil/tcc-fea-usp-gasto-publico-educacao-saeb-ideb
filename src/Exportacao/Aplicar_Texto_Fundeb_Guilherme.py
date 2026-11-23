"""Incorpora ao 2.1 o texto do Guilherme sobre MDE, Fundeb e ICMS Educacional (registro A31, 2026-11-23).

O texto dele ("Fundeb e como são feitos os repasses para a educação") responde aos tópicos 2 e 3 da revisão (A29).
O 2.1.2 já tinha quase tudo; entram aqui só os pontos que faltavam:
- 2.1.1: as duas camadas da MDE (parcela compartilhada no Fundeb e aplicação direta) e os programas federais;
- 2.1.2: a redistribuição dentro do estado (contribuidores e recebedores líquidos);
- 2.1.3: Minas Gerais como pioneiro, a lei cearense de 2007 (18% da cota, IQE), a divisão 25%/75% e o DF.

Uso (na raiz do repositório): python src/Exportacao/Aplicar_Texto_Fundeb_Guilherme.py <entrada.docx> <saida.docx>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

tmp, x = E.abrir(Path(sys.argv[1]))

# ── 2.1.1: as duas camadas
mde = E.achar(x, "A vinculação constitucional de receitas à educação determina").group(0)
x = E.depois_de(x, "A vinculação constitucional de receitas à educação determina", [E.novo_par(mde,
    "Nos estados, no Distrito Federal e nos municípios, esse piso se divide em duas camadas. Na camada compartilhada, "
    "20% das principais receitas de impostos e transferências são retidos automaticamente para compor o Fundeb, "
    "descrito a seguir. Na camada de aplicação direta, ficam no caixa do próprio ente os 5% restantes dessas receitas e "
    "25% dos impostos que não entram no fundo, como o IPTU, o ISS e o ITBI nos municípios e o imposto de renda retido "
    "na fonte pelos próprios entes. A rede conta ainda com programas federais que não entram no cômputo do mínimo de "
    "MDE, como o salário-educação, o Programa Nacional de Alimentação Escolar (PNAE), o Programa Nacional de Apoio ao "
    "Transporte do Escolar (PNATE) e o Programa Dinheiro Direto na Escola (PDDE). Como a despesa por subfunção é "
    "classificada pela finalidade, e não pela fonte, o gasto por aluno usado neste trabalho reúne recursos das duas "
    "camadas e desses programas, desde que a despesa esteja classificada no Ensino Fundamental (seção 3.1).")])

# ── 2.1.2: redistribuição dentro do estado
x = E.trocar_trecho(x, "O Fundeb é um fundo de natureza contábil",
    "(Brasil, 2020b, arts. 7º, 8º e 11).",
    "(Brasil, 2020b, arts. 7º, 8º e 11). Esse mecanismo redistribui recursos dentro de cada estado: os municípios com "
    "arrecadação por habitante alta e proporcionalmente poucos alunos contribuem mais do que recebem, e os de base "
    "tributária menor e mais alunos recebem mais do que contribuem.")

# ── 2.1.3: Distrito Federal, divisão 25%/75% e a origem em Minas Gerais e no Ceará
x = E.trocar_trecho(x, "Além do Fundeb, os municípios recebem dos estados 25%",
    "Os estados tiveram dois anos, até agosto de 2022, para aprovar essas leis.",
    "A regra vale para todos os estados; o Distrito Federal fica de fora, porque não tem municípios. Os estados "
    "tiveram dois anos, até agosto de 2022, para aprovar essas leis.")
x = E.trocar_trecho(x, "O mecanismo segue uma lógica diferente",
    "entra no caixa geral do município, e só a parcela exigida pela vinculação constitucional vai obrigatoriamente "
    "para a MDE.",
    "entra no caixa do município como transferência constitucional comum. Desse valor, 25% seguem vinculados à "
    "educação, pela "
    "retenção do Fundeb e pela aplicação mínima em MDE, e os outros 75% são receita livre, que o município pode "
    "aplicar em outras políticas ou reinvestir na própria rede.")
x = E.reescrever(x, "O modelo foi inspirado no Ceará",
    "Minas Gerais foi o primeiro estado a incluir critérios educacionais na repartição da cota, na década de 1990 "
    "(Minas Gerais, 1995). Foi o Ceará, porém, que deu ao mecanismo a escala que inspirou a Emenda Constitucional "
    "nº 108/2020: a Lei Estadual nº 14.023/2007 passou a distribuir 18% da cota-parte municipal, o equivalente a 4,5% "
    "de toda a arrecadação do ICMS no estado, segundo o Índice Municipal de Qualidade Educacional (IQE) (Ceará, 2007; "
    "Sasso et al., 2021). O incentivo é recorrente e chega ao gestor municipal junto com a assistência técnica do "
    "estado, sem depender de aumentos salariais permanentes. O efeito dessa política sobre a aprendizagem é discutido "
    "em 2.2.4, e o mecanismo ajuda a contextualizar a comparação entre Ceará e Bahia da seção 4.3.")

# ── referências, em ordem alfabética
ps = E.pars(x)
i_ref = [k for k, m in enumerate(ps) if E.texto_de(m.group(0)).strip() == "REFERÊNCIAS"][-1]
refs = []
for m in ps[i_ref + 1:]:
    t = E.texto_de(m.group(0)).strip()
    if t.startswith("APÊNDICE"):
        break
    if t:
        refs.append((t, m.group(0)))
for nova in ["Ceará. (2007). Lei nº 14.023, de 17 de dezembro de 2007. Modifica dispositivos da Lei nº 12.612, de 7 de "
             "agosto de 1996, que define critérios para distribuição da parcela de receita do produto da arrecadação do "
             "ICMS pertencente aos municípios. *Diário Oficial do Estado do Ceará*.",
             "Minas Gerais. (1995). Lei nº 12.040, de 28 de dezembro de 1995. Dispõe sobre a distribuição da parcela de "
             "receita do produto da arrecadação do ICMS pertencente aos municípios. *Diário Oficial do Estado de Minas "
             "Gerais*."]:
    seguinte = next(p for t, p in refs if t.lower() > nova.lower())
    modelo = next(p for t, p in refs if t.startswith("Brasil. (2021)"))
    x = x.replace(seguinte, E.novo_par(modelo, nova) + seguinte, 1)

E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
