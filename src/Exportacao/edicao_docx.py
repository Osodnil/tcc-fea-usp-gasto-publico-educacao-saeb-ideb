"""Funções para editar, parágrafo a parágrafo, o .docx editado pelos autores (documento principal desde 2026-11-23).

Cada parágrafo novo copia o formato (pPr e rPr) de um parágrafo existente do próprio documento, para manter o
padrão do texto. Usado por Aplicar_Modelo_Cientifico.py e pelos próximos ajustes.
"""
import html
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def abrir(entrada: Path) -> tuple[Path, str]:
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(entrada) as z:
        z.extractall(tmp)
    return tmp, (tmp / "word" / "document.xml").read_text(encoding="utf-8")


def salvar(tmp: Path, x: str, saida: Path) -> None:
    (tmp / "word" / "document.xml").write_text(x, encoding="utf-8")
    saida.parent.mkdir(parents=True, exist_ok=True)
    if saida.exists():
        saida.unlink()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(tmp / "[Content_Types].xml", "[Content_Types].xml")
        for f in sorted(tmp.rglob("*")):
            if f.is_file() and f.name != "[Content_Types].xml":
                z.write(f, f.relative_to(tmp).as_posix())
    shutil.rmtree(tmp, ignore_errors=True)


def texto_de(par: str) -> str:
    return html.unescape("".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", par, flags=re.S)))


def pars(xml: str):
    tbs = [(m.start(), m.end()) for m in re.finditer(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S)]
    return [m for m in re.finditer(r"<w:p[ >].*?</w:p>", xml, flags=re.S) if not any(a <= m.start() < b for a, b in tbs)]


def achar(xml: str, inicio: str, n: int = 1, exato: bool = False) -> re.Match:
    ach = [m for m in pars(xml) if (texto_de(m.group(0)).strip() == inicio if exato
                                    else texto_de(m.group(0)).strip().startswith(inicio))]
    assert len(ach) == n, f"esperava {n}, achei {len(ach)}: {inicio[:60]}"
    return ach[-1]


def partes(par: str) -> tuple[str, str]:
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", par, flags=re.S)
    ppr = ppr.group(0) if ppr else ""
    rpr = re.search(r"<w:r[ >](?:(?!</w:r>).)*?(<w:rPr>.*?</w:rPr>)", par, flags=re.S)
    rpr = rpr.group(1) if rpr else ""
    rpr = re.sub(r"<w:highlight [^>]*/>|<w:b/>|<w:bCs/>|<w:b w:val=\"[^\"]*\"/>|<w:bCs w:val=\"[^\"]*\"/>|<w:i/>|<w:iCs/>"
                 r"|<w:rStyle [^>]*/>", "", rpr)
    return ppr, rpr


def runs(texto: str, rpr: str, negrito: bool = False) -> str:
    """Texto em runs; **trecho** em negrito, *trecho* em itálico, [MARCA...] em realce amarelo."""
    out = ""
    for k, s in enumerate(texto.split("**")):
        for j, s2 in enumerate(s.split("*")):
            for p in re.split(r"(\[[A-ZÇÃÉÍ]{5,}[^\]]*\])", s2):
                if not p:
                    continue
                r = rpr or "<w:rPr></w:rPr>"
                if k % 2 or negrito:
                    r = r.replace("<w:rPr>", "<w:rPr><w:b/><w:bCs/>", 1)
                if j % 2:
                    r = r.replace("<w:rPr>", "<w:rPr><w:i/><w:iCs/>", 1)
                if p.startswith("["):
                    r = r.replace("</w:rPr>", '<w:highlight w:val="yellow"/></w:rPr>')
                out += f'<w:r>{r}<w:t xml:space="preserve">{escape(p)}</w:t></w:r>'
    return out


def novo_par(modelo: str, texto: str, negrito: bool = False) -> str:
    ppr, rpr = partes(modelo)
    ppr = re.sub(r"<w:sectPr.*?</w:sectPr>", "", ppr, flags=re.S)
    ppr = ppr.replace("<w:pageBreakBefore/>", "").replace('<w:pageBreakBefore w:val="1"/>', "")
    return "<w:p>" + ppr + runs(texto, rpr, negrito) + "</w:p>"


def reescrever(xml: str, inicio: str, texto: str, exato: bool = False) -> str:
    m = achar(xml, inicio, exato=exato)
    return xml[:m.start()] + novo_par(m.group(0), texto) + xml[m.end():]


def trocar_trecho(xml: str, inicio: str, antigo: str, novo: str) -> str:
    m = achar(xml, inicio)
    t = texto_de(m.group(0)).strip()
    assert antigo in t, (inicio[:40], antigo)
    return xml[:m.start()] + novo_par(m.group(0), t.replace(antigo, novo)) + xml[m.end():]


def antes_de(xml: str, inicio: str, blocos: list[str], exato: bool = False) -> str:
    m = achar(xml, inicio, exato=exato)
    return xml[:m.start()] + "".join(blocos) + xml[m.start():]


def depois_de(xml: str, inicio: str, blocos: list[str], exato: bool = False) -> str:
    m = achar(xml, inicio, exato=exato)
    return xml[:m.end()] + "".join(blocos) + xml[m.end():]


def campo_tc(texto: str, letra: str) -> str:
    """Entrada oculta para as listas automáticas de figuras (F), tabelas (T) e quadros (Q)."""
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TC "'
            + escape(texto.replace('"', "”")) + f'" \\f {letra} \\l 1 </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')
