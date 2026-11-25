"""Aplica as correções da conferência das referências no Crossref (docs/conferencia_referencias.md, A33, 2026-11-24).

As trocas são feitas dentro dos runs, para preservar o itálico de revistas e volumes.
Uso (na raiz do repositório): python src/Exportacao/Corrigir_Referencias.py <entrada.docx> <saida.docx>
"""
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

TROCAS = [
    ("Crozatti, J.", [("Serpa, A. M.", "Rinaldi, A. M. S."),
                      (", (61). https://doi.org/10.38116/ppp61art5", ", (61), 143–171. https://doi.org/10.38116/ppp61art5")]),
    ("Alves, P. J. H.", [(", (61). https://doi.org/10.38116/ppp61art10",
                          ", (61), 285–312. https://doi.org/10.38116/ppp61art10")]),
    ("Mazzon, J. A.", [("(5), 747–770.", "(5), 747–770. https://doi.org/10.5585/bjm.v17i5.4175")]),
    ("Sasso, M.", [(", e260071.", ", e260071. https://doi.org/10.1590/S1413-24782021260071")]),
    ("Soares, J. F., & Xavier", [("https://www.scielo.br/pdf/es/v34n124/13.pdf",
                                  "https://doi.org/10.1590/S0101-73302013000300013")]),
    # número conforme o registro oficial do repositório do Insper (dc.identifier.issue = "BEWP 065/2009"), A34
    ("Menezes-Filho, N., & Amaral", [(" (Insper Working Paper). Insper. https://ideas.repec.org/p/aap/wpaper/064.html "
                                      "[CONFERIR o número do texto]",
                                      " (Insper Working Paper BEWP 065/2009). Insper. "
                                      "https://repositorio.insper.edu.br/handle/11224/5748")]),
    # A34: ementas conforme o Diário Oficial do Ceará (19/12/2007) e o texto da ALMG
    ("Ceará. (2007)", [("que define critérios para distribuição da parcela de receita do produto da arrecadação do ICMS "
                        "pertencente aos municípios.",
                        "que define critérios para distribuição da parcela de receita do produto e arrecadação do "
                        "Imposto sobre Operações Relativas à Circulação de Mercadorias e sobre Prestações de Serviços de "
                        "Transporte Interestadual e Intermunicipal e de Comunicação – ICMS, pertencente aos municípios e "
                        "dá outras providências.")]),
    ("Minas Gerais. (1995)", [("pertencente aos municípios.",
                               "pertencente aos Municípios, de que trata o inciso II do parágrafo único do artigo 158 "
                               "da Constituição Federal, e dá outras providências.")]),
    # A34: o Radar IDHM 2026 é do PNUD, da Fundação João Pinheiro e do IBGE (não do Ipea)
    ("Programa das Nações Unidas", [("Instituto de Pesquisa Econômica Aplicada", "Instituto Brasileiro de Geografia e Estatística"),
                                    ("Radar IDHM: Atlas do Desenvolvimento Humano no Brasil",
                                     "Radar IDHM: Evolução do IDHM e de seus componentes – período de 2012 a 2024"),
                                    (" [Conjunto de dados]. http://www.atlasbrasil.org.br [CONFERIR a autoria da edição usada]",
                                     " [Conjunto de dados]. PNUD. https://atlasbrasil.org.br/consulta")]),
]

tmp, x = E.abrir(Path(sys.argv[1]))
for inicio, pares in TROCAS:
    m = E.achar(x, inicio)
    p = m.group(0)
    for antigo, novo in pares:
        a, n = escape(antigo), escape(novo)
        assert p.count(a) == 1, (inicio, antigo)
        p = p.replace(a, n)
    if inicio.startswith(("Menezes-Filho", "Programa das Nações")):
        p = re.sub(r"<w:highlight [^>]*/>", "", p)  # a marca amarela saiu junto com o [CONFERIR]
    x = x[:m.start()] + p + x[m.end():]

E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
