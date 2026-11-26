"""Gera a versão anônima do TCC para o Moodle (sem autores nem orientadora), como pede a Coordenação (A35, 2026-11-26).

O que sai:
- os nomes dos autores na capa e na folha de rosto e a linha da orientadora;
- a seção de agradecimentos inteira (cita autores, orientadora e famílias);
- o endereço do repositório no GitHub (o usuário identifica um dos autores), no texto e nos hyperlinks;
- o QR Code da Figura 5 (leva ao repositório), trocado por um aviso;
- o quadro "Autoria e atualização" da tela Sobre os dados (Figura B.7), coberto por um aviso;
- o autor nos metadados do arquivo.
No fim, confere que nenhum nome dos autores ou da orientadora sobrou em nenhuma parte do .docx.

Uso (na raiz do repositório): python src/Exportacao/Gerar_Versao_Anonima.py <entrada.docx> <saida.docx>
Depois: src/Exportacao/Atualizar_Campos.ps1 -Arquivo <saida.docx> -Pdf <saida.pdf> (sumário, listas e PDF).
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edicao_docx as E  # noqa: E402

NOMES = ["Guilherme", "Henrique", "Lindoso", "Menezes Araújo", "Nogueira Pedro", "Adriana", "Backx", "Osodnil"]
AVISO = "endereço omitido na versão anônima"
ent, sai = Path(sys.argv[1]), Path(sys.argv[2])
tmp, x = E.abrir(ent)


def fonte(tam: int):
    for f in ["C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(f).exists():
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default()


# ── capa e folha de rosto: os parágrafos ficam (para não mudar o leiaute), só o texto sai
for nome in ["Guilherme Menezes Araújo", "Henrique Nogueira Pedro Lindoso"]:
    for m in reversed(E.pars(x)):
        if E.texto_de(m.group(0)).strip() == nome:
            x = x[:m.start()] + E.novo_par(m.group(0), "") + x[m.end():]
m = E.achar(x, "Orientadora: Profa.")
x = x[:m.start()] + E.novo_par(m.group(0), "") + x[m.end():]

# ── agradecimentos: a seção inteira, do título ao parágrafo que fecha a seção
ps = list(re.finditer(r"<w:p[ >].*?</w:p>", x, flags=re.S))
i0 = next(i for i, m in enumerate(ps) if E.texto_de(m.group(0)).strip() == "AGRADECIMENTOS")
i1 = next(i for i in range(i0, len(ps)) if "<w:sectPr" in ps[i].group(0))
assert E.texto_de(ps[i1 + 1].group(0)).strip() == "RESUMO", "estrutura inesperada depois dos agradecimentos"
x = x[:ps[i0].start()] + x[ps[i1].end():]

# ── endereço do GitHub: hyperlinks viram texto simples com o aviso; o endereço solto também
url = re.compile(r"https?://github\.com/Osodnil/[\w\-./]*")
rels_p = tmp / "word" / "_rels" / "document.xml.rels"
rels = rels_p.read_text(encoding="utf-8")
ids = re.findall(r'<Relationship Id="([^"]+)"[^>]*Target="https?://github\.com/Osodnil[^"]*"[^>]*/>', rels)
for rid in ids:
    for h in re.findall(rf'<w:hyperlink [^>]*r:id="{rid}"[^>]*>.*?</w:hyperlink>', x, flags=re.S):
        rpr = re.search(r"<w:rPr>.*?</w:rPr>", h, flags=re.S)
        rpr = re.sub(r'<w:rStyle [^>]*/>|<w:color [^>]*/>|<w:u [^>]*/>', "", rpr.group(0)) if rpr else ""
        x = x.replace(h, f'<w:r>{rpr}<w:t xml:space="preserve">{AVISO}</w:t></w:r>', 1)
rels = re.sub(r'<Relationship Id="[^"]+"[^>]*Target="https?://github\.com/Osodnil[^"]*"[^>]*/>', "", rels)
rels_p.write_text(rels, encoding="utf-8")
x = url.sub(AVISO, x)
for m in reversed(E.pars(x)):  # onde o texto já dizia "o endereço", o aviso fica só entre parênteses
    if "endereço " + AVISO in E.texto_de(m.group(0)):
        p = m.group(0).replace(f">{AVISO}</w:t>", ">(omitido na versão anônima)</w:t>", 1)
        x = x[:m.start()] + p + x[m.end():]

# ── QR Code (Figura 5) e quadro de autoria da tela Sobre os dados (Figura B.7)
relmap = dict(re.findall(r'<Relationship Id="([^"]+)"[^>]*Target="(media/[^"]+)"', rels))
def imagem_da_legenda(legenda: str) -> Path:
    m = E.achar(x, legenda, n=2)  # a lista de figuras repete o título; a legenda é a última
    rid = re.search(r'r:embed="([^"]+)"', m.group(0)).group(1)
    return tmp / "word" / relmap[rid]

qr = imagem_da_legenda("Figura 5 –")
w, h = Image.open(qr).size
img = Image.new("RGB", (w, h), (238, 243, 249))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, w - 1, h - 1], outline=(150, 160, 175), width=max(1, w // 120))
f = fonte(max(10, w // 14))
for k, linha in enumerate(["QR Code omitido", "na versão anônima"]):
    tw = d.textlength(linha, font=f)
    d.text(((w - tw) / 2, h / 2 - f.size * (1.2 - k * 1.4)), linha, fill=(60, 70, 85), font=f)
img.save(qr)

sobre = imagem_da_legenda("Figura B.7 –")
img = Image.open(sobre).convert("RGB")
W, H = img.size
cx = lambda v: round(v * W / 1426); cy = lambda v: round(v * H / 802)  # coordenadas medidas na captura 1426 × 802
d = ImageDraw.Draw(img)
d.rounded_rectangle([cx(20), cy(506), cx(466), cy(758)], radius=cx(8), fill=(255, 255, 255), outline=(220, 225, 232))
f = fonte(cy(17))
d.text((cx(38), cy(522)), "Autoria e atualização", fill=(23, 55, 94), font=fonte(cy(19)))
d.text((cx(38), cy(560)), "Omitidas na versão anônima.", fill=(60, 70, 85), font=f)
img.save(sobre)

# ── metadados
core_p = tmp / "docProps" / "core.xml"
core = core_p.read_text(encoding="utf-8")
core = re.sub(r"<dc:creator>[^<]*</dc:creator>", "<dc:creator></dc:creator>", core)
core = re.sub(r"<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>", "<cp:lastModifiedBy></cp:lastModifiedBy>", core)
core_p.write_text(core, encoding="utf-8")

# ── conferência: nenhum nome em nenhuma parte de texto do pacote
(tmp / "word" / "document.xml").write_text(x, encoding="utf-8")
sobras = [(p.relative_to(tmp).as_posix(), n) for p in tmp.rglob("*") if p.suffix in (".xml", ".rels")
          for n in NOMES if n in p.read_text(encoding="utf-8", errors="ignore")]
assert not sobras, f"ainda há nomes: {sobras}"
E.salvar(tmp, x, sai)
print(f"[OK] {sai}")
