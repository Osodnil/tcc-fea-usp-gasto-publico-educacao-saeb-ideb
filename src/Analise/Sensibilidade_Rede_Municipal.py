"""Sensibilidade à parcela atendida pela rede municipal (etapa 2 do plano da reunião de 2026-11-06).

Em parte dos municípios, a rede estadual atende boa parte dos alunos da etapa. O indicador continua coerente
(gasto e nota são da mesma rede municipal), mas a rede municipal deixa de representar as crianças da cidade.
Este script:
1. descreve a parcela municipal das matrículas públicas (PART_MUN) nas redes com nota, por etapa e edição;
2. reestima os dois modelos de eficiência (src/Analise/Eficiencia.py) sem as redes com PART_MUN < LIMITE
   e compara o coeficiente do gasto, o ajuste e a ordenação das redes que ficam;
3. compara a eficiência média das redes parciais com a das demais;
4. recalcula o ρ de Spearman gasto × proficiência (gasto do mesmo ano) com e sem as redes parciais.

Entrada: data/processed/painel_municipal.parquet e data/processed/powerbi/fato_oferta_municipal.parquet
(gerado por src/Visualizacao/Preparar_PowerBI.py). Saídas em data/interim/diagnosticos/:
sensibilidade_rede_municipal_parcela.csv, _coeficientes.csv e _ordenacao.csv.
Nada aqui altera os indicadores oficiais.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Eficiencia as ef  # noqa: E402

LIMITE = 0.5  # rede municipal com menos da metade das matrículas públicas da etapa
DIAG = ef.DIAG_DIR


def com_parcela(df: pl.DataFrame) -> pl.DataFrame:
    oferta = pl.read_parquet(ef.BASE_DIR / "data" / "processed" / "powerbi" / "fato_oferta_municipal.parquet")
    return df.join(oferta.select("CO_MUNICIPIO", "ETAPA", "ANO", "PART_MUN", "QT_MAT_MUN", "QT_MAT_EST"),
                   on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")


def descrever(df: pl.DataFrame) -> pl.DataFrame:
    nota = df.filter(pl.col("NOTA_MT").is_not_null() | pl.col("NOTA_LP").is_not_null())
    return (nota.group_by("ETAPA", "ANO").agg(
        pl.len().alias("REDES_COM_NOTA"),
        (pl.col("PART_MUN") < 0.5).sum().alias("PARCELA_MENOR_50"),
        (pl.col("PART_MUN") < 0.8).sum().alias("PARCELA_MENOR_80"),
        pl.col("PART_MUN").median().alias("PARCELA_MEDIANA"),
    ).with_columns((pl.col("PARCELA_MENOR_50") / pl.col("REDES_COM_NOTA")).alias("PCT_MENOR_50"))
     .sort("ETAPA", "ANO"))


def rho(x: pl.Series, y: pl.Series) -> float:
    return float(np.corrcoef(x.rank("average").to_numpy(), y.rank("average").to_numpy())[0, 1])


if __name__ == "__main__":
    pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_tbl_cols(20)
    df = com_parcela(ef.base())
    parcela = descrever(df)
    parcela.write_csv(DIAG / "sensibilidade_rede_municipal_parcela.csv")
    print("== 1. Parcela municipal das matrículas públicas, nas redes com nota")
    print(parcela.with_columns(pl.col("PARCELA_MEDIANA").round(3), pl.col("PCT_MENOR_50").round(3)))
    ufs = (df.filter(pl.col("NOTA_MT").is_not_null() & (pl.col("ANO") == 2023))
           .group_by("ETAPA", "SG_UF").agg((pl.col("PART_MUN") < LIMITE).mean().round(3).alias("PCT_PARCIAIS"), pl.len())
           .sort("ETAPA", "PCT_PARCIAIS", descending=[False, True]))
    print("UFs com mais redes parciais em 2023 (nota de MT):")
    for etapa in ("AI", "AF"):
        print(etapa, ufs.filter(pl.col("ETAPA") == etapa).head(6).select("SG_UF", "PCT_PARCIAIS", "len").rows())

    print(f"\n== 2. Modelos de eficiência com e sem as redes com parcela municipal < {LIMITE:.0%}")
    coefs, ordem = [], []
    for etapa in ("AI", "AF"):
        de = df.filter(pl.col("ETAPA") == etapa)
        so_integrais = de.filter(pl.col("PART_MUN") >= LIMITE)
        for disc, nota in ef.DISCIPLINAS.items():
            for nome, op in ef.MODELOS.items():
                todos, c_todos, a_todos = ef.ajustar(de, nota, op)
                parte, c_parte, a_parte = ef.ajustar(so_integrais, nota, op)
                b0 = next(c for c in c_todos if c["VARIAVEL"] == "LOG_GASTO")
                b1 = next(c for c in c_parte if c["VARIAVEL"] == "LOG_GASTO")
                coefs.append({"ETAPA": etapa, "DISCIPLINA": disc, "MODELO": nome,
                              "N_TODAS": a_todos["N"], "N_SEM_PARCIAIS": a_parte["N"],
                              "COEF_GASTO_TODAS": b0["COEF"], "EP_TODAS": b0["EP"], "P_TODAS": b0["P"],
                              "COEF_GASTO_SEM_PARCIAIS": b1["COEF"], "EP_SEM_PARCIAIS": b1["EP"], "P_SEM_PARCIAIS": b1["P"],
                              "R2_TODAS": a_todos["R2"], "R2_SEM_PARCIAIS": a_parte["R2"]})
                # ordenação das redes que ficam: a eficiência delas muda quando as parciais saem do modelo?
                j = todos.join(parte, on=["CO_MUNICIPIO", "ETAPA", "ANO"], suffix="_SEM")
                j = j.join(de.select("CO_MUNICIPIO", "ANO", "PART_MUN"), on=["CO_MUNICIPIO", "ANO"], how="left")
                parciais = todos.join(de.select("CO_MUNICIPIO", "ANO", "PART_MUN"), on=["CO_MUNICIPIO", "ANO"], how="left")
                for ano in op["anos"]:
                    ja = j.filter(pl.col("ANO") == ano)
                    pa = parciais.filter(pl.col("ANO") == ano)
                    q = lambda s: (s.rank("ordinal") / s.len() * 5).ceil()
                    ordem.append({"ETAPA": etapa, "DISCIPLINA": disc, "MODELO": nome, "ANO": ano, "REDES": ja.height,
                                  "RHO_ORDEM": rho(ja["RESIDUO"], ja["RESIDUO_SEM"]),
                                  "MUDA_QUINTIL": float((q(ja["RESIDUO"]) != q(ja["RESIDUO_SEM"])).mean()),
                                  "EFIC_MEDIA_PARCIAIS": pa.filter(pl.col("PART_MUN") < LIMITE)["RESIDUO"].mean(),
                                  "EFIC_MEDIA_DEMAIS": pa.filter(pl.col("PART_MUN") >= LIMITE)["RESIDUO"].mean(),
                                  "N_PARCIAIS": pa.filter(pl.col("PART_MUN") < LIMITE).height})
    tc = pl.DataFrame(coefs)
    to = pl.DataFrame(ordem)
    tc.write_csv(DIAG / "sensibilidade_rede_municipal_coeficientes.csv")
    to.write_csv(DIAG / "sensibilidade_rede_municipal_ordenacao.csv")
    print(tc.select("ETAPA", "DISCIPLINA", "MODELO", "N_TODAS", "N_SEM_PARCIAIS",
                    pl.col("COEF_GASTO_TODAS").round(2), pl.col("P_TODAS").round(3),
                    pl.col("COEF_GASTO_SEM_PARCIAIS").round(2), pl.col("P_SEM_PARCIAIS").round(3),
                    pl.col("R2_TODAS").round(3), pl.col("R2_SEM_PARCIAIS").round(3)))
    print("\nOrdenação das redes que ficam e eficiência média das parciais (2023):")
    print(to.filter(pl.col("ANO") == 2023).select(
        "ETAPA", "DISCIPLINA", "MODELO", "REDES", pl.col("RHO_ORDEM").round(3), pl.col("MUDA_QUINTIL").round(3),
        "N_PARCIAIS", pl.col("EFIC_MEDIA_PARCIAIS").round(1), pl.col("EFIC_MEDIA_DEMAIS").round(1)))

    print("\n== 3. ρ de Spearman gasto (mesmo ano) × proficiência, com e sem as redes parciais (MT)")
    for etapa in ("AI", "AF"):
        for ano in (2017, 2019, 2021, 2023, 2025):
            d = df.filter((pl.col("ETAPA") == etapa) & (pl.col("ANO") == ano)).drop_nulls(["NOTA_MT", "GASTO_ALUNO_R2025_L0"])
            s = d.filter(pl.col("PART_MUN") >= LIMITE)
            print(f"  {etapa} {ano}: todas {rho(d['GASTO_ALUNO_R2025_L0'], d['NOTA_MT']):.3f} (n={d.height}) | "
                  f"sem parciais {rho(s['GASTO_ALUNO_R2025_L0'], s['NOTA_MT']):.3f} (n={s.height})")
