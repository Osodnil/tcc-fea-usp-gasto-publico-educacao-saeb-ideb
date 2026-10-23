"""Executa o pipeline do TCC na ordem certa.

Uso (a partir de qualquer pasta):
    python run_pipeline.py                     # tratamento, painéis e dashboard (lê data/interim)
    python run_pipeline.py --com-extracao      # tudo, incluindo extração (precisa de data/raw e internet)
    python run_pipeline.py --a-partir-de Montar_Paineis
    python run_pipeline.py --listar            # só mostra a ordem
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

EXTRACAO = [
    "Extract/Extract_IPCA.py",
    "Extract/Extract_IBGE.py",
    "Extract/Extract_IDHM.py",
    "Extract/Extract_SIOPE.py",
    "Extract/Extract_SIOPE_Funcao.py",
    "Extract/Extract_SICONFI_Estados.py",
    "Extract/Extract_Censo_Escolar.py",
    "Extract/Extract_Censo_Matriculas.py",
    "Extract/Extract_SAEB.py",
]
TRATAMENTO = [
    "Transform/Transform_IBGE.py",
    "Transform/Transform_IDHM.py",
    "Transform/Transform_SAEB.py",
    "Transform/Transform_Matriculas.py",
    "Transform/Transform_Infraestrutura.py",
    "Transform/Transform_SIOPE.py",  # depende de IBGE, matrículas e IPCA
    "Transform/Transform_SICONFI.py",
    "Transform/Montar_Paineis.py",
    "Visualizacao/Gerar_Dashboard_HTML.py",
]

# Brutos baixados manualmente que a extração espera encontrar em data/raw
BRUTOS = [
    "Censo/Dados/Municípios.xlsx",
    "Censo/Dados/Alfabetização.xlsx",
    "IDHM",
    "Microdados Censo Escolar",
    "IDEB - Índice de Desenvolvimento da Educação Básica",
]


def main() -> int:
    p = argparse.ArgumentParser(description="Executa o pipeline do TCC.")
    p.add_argument("--com-extracao", action="store_true", help="inclui a extração (lenta; usa APIs e data/raw)")
    p.add_argument("--a-partir-de", metavar="NOME", help="começa no script cujo nome contém NOME")
    p.add_argument("--listar", action="store_true", help="mostra a ordem e sai")
    args = p.parse_args()

    etapas = (EXTRACAO if args.com_extracao else []) + TRATAMENTO
    if args.a_partir_de:
        idx = next((i for i, s in enumerate(etapas) if args.a_partir_de.lower() in s.lower()), None)
        if idx is None:
            print(f"[ERRO] Nenhum script com '{args.a_partir_de}' no nome.")
            return 1
        etapas = etapas[idx:]

    if args.listar:
        print("\n".join(f"{i:2d}. src/{s}" for i, s in enumerate(etapas, 1)))
        return 0

    if any(s.startswith("Extract/") for s in etapas):
        faltam = [b for b in BRUTOS if not (RAIZ / "data" / "raw" / b).exists()]
        if faltam:
            print("[ERRO] Brutos ausentes em data/raw (veja o README, seção Fontes de dados):")
            print("\n".join(f"  - {b}" for b in faltam))
            return 1

    # UTF-8 na saída: os scripts imprimem acentos e tabelas que o console cp1252 do Windows não codifica
    ambiente = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    inicio = time.time()
    for i, script in enumerate(etapas, 1):
        print(f"\n{'=' * 70}\n[{i}/{len(etapas)}] src/{script}\n{'=' * 70}", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, str(RAIZ / "src" / script)], cwd=RAIZ, env=ambiente)
        if r.returncode != 0:
            print(f"\n[FALHOU] src/{script} (código {r.returncode}). Corrija e retome com: "
                  f"python run_pipeline.py --a-partir-de {Path(script).stem}")
            return r.returncode
        print(f"[ok em {time.time() - t0:.0f}s]")
    print(f"\n[CONCLUÍDO] {len(etapas)} scripts em {time.time() - inicio:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
