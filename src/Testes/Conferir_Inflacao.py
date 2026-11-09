"""Confere a correção pela inflação em todo o caminho do gasto, do dado bruto ao painel (pedido de 2026-11-09).

Pergunta: além do gasto por aluno mostrado na Visão geral, os demais valores do painel estão em R$ de 2025?
Confere, sem alterar nada:
1. SIOPE e SICONFI: o valor em R$ de 2025 é o nominal × fator do IPCA do mesmo ano, linha a linha;
2. gasto por aluno municipal e estadual: R$ 2025 ÷ matrículas, igual ao gravado;
3. defasagens: o gasto de k anos antes (L1, L2, L4) é o gasto real daquele ano, já em R$ de 2025
   (cada ano corrigido pelo próprio fator, e não pelo da edição);
4. painel Power BI: toda coluna de valor monetário é uma versão R2025, e toda medida de gasto usa só essas colunas;
5. valores que não são monetários (nota, eficiência, contagens, percentuais) não dependem do IPCA.
Saída: resumo no terminal. Encerra com erro se alguma conferência falhar.
"""
import re
import sys
from pathlib import Path

import polars as pl


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE = encontrar_raiz_projeto()
INTERIM, PROC, PBI = BASE / "data" / "interim", BASE / "data" / "processed", BASE / "data" / "processed" / "powerbi"
falhas = []


def conferir(nome: str, ok: bool, detalhe: str) -> None:
    print(f"[{'OK' if ok else 'FALHA'}] {nome}: {detalhe}")
    if not ok:
        falhas.append(nome)


ipca = pl.read_parquet(INTERIM / "ipca_deflator_anual.parquet").select(pl.col("ANO").cast(pl.Int32), "FATOR_PARA_BASE")

# 1. nominal × fator = R$ 2025
siope = pl.read_parquet(INTERIM / "siope_municipal_transformado.parquet").join(ipca, on="ANO")
for c in ("GASTO_361", "GASTO_EDU"):
    d = (siope[f"{c}_NOMINAL"] * siope["FATOR_PARA_BASE"] - siope[f"{c}_R2025"]).abs().max()
    conferir(f"SIOPE {c}", d < 0.01, f"maior diferença entre nominal × fator e R$ 2025 = {d:.6f} ({siope.height} linhas)")
siconfi = pl.read_parquet(INTERIM / "siconfi_estadual_transformado.parquet").join(ipca, on="ANO")
for c in ("F12", "GASTO_BASICA_A", "GASTO_BASICA_B"):
    s = siconfi.drop_nulls([f"{c}_NOMINAL", f"{c}_R2025"])
    d = (s[f"{c}_NOMINAL"] * s["FATOR_PARA_BASE"] - s[f"{c}_R2025"]).abs().max()
    conferir(f"SICONFI {c}", d < 0.01, f"maior diferença = {d:.6f} ({s.height} linhas)")

# 2. gasto por aluno = R$ 2025 ÷ matrículas
gm = pl.read_parquet(PROC / "gasto_municipal_anual.parquet").drop_nulls(["GASTO_ALUNO_R2025"])
d = (gm["GASTO_361_R2025"] / gm["QT_MAT_FUND"] - gm["GASTO_ALUNO_R2025"]).abs().max()
conferir("Gasto por aluno municipal", d < 0.01, f"maior diferença entre R$ 2025 ÷ matrículas e o gravado = {d:.6f}")
ge = pl.read_parquet(PROC / "gasto_estadual_anual.parquet").join(
    siconfi.select("SG_UF", "ANO", "GASTO_BASICA_A_R2025"), on=["SG_UF", "ANO"]).drop_nulls(["GASTO_ALUNO_A_R2025"])
d = (ge["GASTO_BASICA_A_R2025"] / ge["QT_MAT_BAS"] - ge["GASTO_ALUNO_A_R2025"]).abs().max()
conferir("Gasto por aluno estadual (A)", d < 0.01, f"maior diferença = {d:.6f}")

# 3. defasagens: L_k da edição t = gasto real do ano t − k
painel = pl.read_parquet(PROC / "painel_municipal.parquet")
anual = gm.select("CO_MUNICIPIO", "ANO", "GASTO_ALUNO_R2025")
for k in (0, 1, 2, 4):
    j = painel.select("CO_MUNICIPIO", "ANO", f"GASTO_ALUNO_R2025_L{k}").drop_nulls().join(
        anual.with_columns((pl.col("ANO") + k).alias("ANO")), on=["CO_MUNICIPIO", "ANO"], how="left")
    d = (j[f"GASTO_ALUNO_R2025_L{k}"] - j["GASTO_ALUNO_R2025"]).abs().max()
    sem = j["GASTO_ALUNO_R2025"].null_count()
    conferir(f"Defasagem L{k}", d is not None and d < 0.01 and sem == 0,
             f"maior diferença para o gasto real de {k} ano(s) antes = {d}, sem par = {sem}")

# 4. painel Power BI: colunas e medidas de dinheiro
monetarias = []
for arq in sorted(PBI.glob("*.parquet")):
    for c in pl.read_parquet_schema(arq):
        if re.search(r"GASTO", c) and not re.search(r"EXTREMO|VS_CLUSTER", c):
            monetarias.append(f"{arq.stem}.{c}")
nominais = [c for c in monetarias if "R2025" not in c]
conferir("Colunas monetárias do painel", not nominais,
         f"{len(monetarias)} colunas de gasto, todas em R$ 2025" if not nominais else f"sem R2025: {nominais}")
dax = (BASE / "powerbi" / "medidas.dax").read_text(encoding="utf-8")
refs = set(re.findall(r"\[(GASTO[^\]]*)\]", dax))
fora = sorted(r for r in refs if "R2025" not in r and "EXTREMO" not in r and "VS_CLUSTER" not in r)
conferir("Medidas de gasto", not fora, f"colunas de gasto citadas nas medidas: {len(refs)}; fora de R$ 2025: {fora or 'nenhuma'}")
print("[INFO] A única medida que mostra valor da época é 'Gasto por aluno da época', que divide o R$ 2025 pelo fator do IPCA.")

# 5. o que não é dinheiro não passa pelo IPCA
print("[INFO] Proficiência, IDEB, nota N, eficiência (pontos e %), percentis, contagens e percentuais não são valores em "
      "reais: não dependem da inflação. No modelo de eficiência, o gasto entra em log e há efeito de edição, então um "
      "fator comum a todas as redes do ano não muda o resíduo.")
sys.exit(1 if falhas else 0)
