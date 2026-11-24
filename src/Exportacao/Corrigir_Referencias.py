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
    ("Menezes-Filho, N., & Amaral", [(" (Insper Working Paper). Insper. https://ideas.repec.org/p/aap/wpaper/064.html "
                                      "[CONFERIR o número do texto]",
                                      " (Insper Working Paper No. WPE 164). Insper. "
                                      "https://repositorio.insper.edu.br/handle/11224/5748")]),
]

tmp, x = E.abrir(Path(sys.argv[1]))
for inicio, pares in TROCAS:
    m = E.achar(x, inicio)
    p = m.group(0)
    for antigo, novo in pares:
        a, n = escape(antigo), escape(novo)
        assert p.count(a) == 1, (inicio, antigo)
        p = p.replace(a, n)
    if inicio.startswith("Menezes-Filho"):
        p = re.sub(r"<w:highlight [^>]*/>", "", p)  # a marca amarela saiu junto com o [CONFERIR]
    x = x[:m.start()] + p + x[m.end():]

E.salvar(tmp, x, Path(sys.argv[2]))
print(f"[OK] {sys.argv[2]}")
