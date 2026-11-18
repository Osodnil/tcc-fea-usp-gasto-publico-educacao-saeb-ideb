"""Gera o QR Code de acesso ao projeto, impresso no TCC (decisão A7; etapa 5 do plano final, 2026-11-18).

O QR aponta para a página do repositório no GitHub, e não direto para o painel: o README traz no topo o link do
painel publicado no Power BI ("Publicar na Web", sem login), o código e o registro das decisões. Se o link do painel
mudar, só o README muda, e o QR impresso continua valendo.

Saída: docs/resultados/figuras/qrcode_acesso.png (usada pela cópia do rascunho, Figura 5).
Uso (na raiz do repositório): python src/Exportacao/Gerar_QRCode.py
"""
from pathlib import Path

import segno

URL = "https://github.com/Osodnil/tcc-fea-usp-gasto-publico-educacao-saeb-ideb"
SAIDA = Path(__file__).resolve().parents[2] / "docs" / "resultados" / "figuras" / "qrcode_acesso.png"

if __name__ == "__main__":
    qr = segno.make(URL, error="m")  # correção de erro média: continua legível se a impressão borrar um pouco
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    qr.save(SAIDA, scale=12, border=4, dark="#000000", light="#ffffff")
    print(f"[OK] {SAIDA.relative_to(SAIDA.parents[3])} (versão {qr.designator}) -> {URL}")
