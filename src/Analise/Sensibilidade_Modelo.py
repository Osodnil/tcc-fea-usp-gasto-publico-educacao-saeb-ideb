"""Testes de sensibilidade dos modelos principais (decisão A4): os resultados de A11 e A12 se sustentam?

Camada municipal: especificação de referência de A11 (efeito fixo de município e UF × edição, 2017-2025, gasto do
mesmo ano), AI e AF, MT e LP. Cada teste muda uma coisa:
- sem 2021 (pandemia; S5);
- painel balanceado: só municípios com nota nas cinco edições (S8);
- gasto médio do biênio (ano da prova e ano anterior) no lugar do gasto do ano (G12); como o ano anterior só existe
  a partir de 2019, a comparação é com a referência em 2019-2025;
- sem as redes parciais: a rede municipal atende menos de 50% dos alunos públicos da etapa (A9), e o limite de 80%
  proposto como sensibilidade;
- sem os resultados marcados como salto atípico na disciplina (S11);
- IDHM (C1b), no modelo com efeito fixo de município e efeito de edição, 2017-2023 (na referência, o efeito de
  UF × edição absorve o IDHM): Renda e Longevidade (a escolha) × IDHM total × sem IDHM.

Camada estadual: referência de A12 (efeito fixo de UF, 2017-2023, versão A do gasto): com 2025 (M3) e versão B do
gasto (G4) e gasto pela soma das subfunções da educação básica (G4b: 122, 361, 362, 365, 366, 367 e 368, lidas do
SICONFI intermediário), que tira da função 12 o que o Anexo I-E não detalha em subfunção.

Associação, não causalidade (A1). Saída: data/interim/diagnosticos/sensibilidade_modelo.csv.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Modelo_Estadual as E  # noqa: E402
import Modelo_Principal as M  # noqa: E402

TODOS = [2017, 2019, 2021, 2023, 2025]
REF = {"ef": True, "controles": M.NO_TEMPO, "anos": TODOS, "uf_ano": True}


def base_municipal() -> pl.DataFrame:
    pbi = M.PROCESSED_DIR / "powerbi"
    parcela = pl.read_parquet(pbi / "fato_oferta_municipal.parquet").select("CO_MUNICIPIO", "ETAPA", "ANO", "PART_MUN")
    saltos = (pl.read_parquet(pbi / "fato_desempenho_municipal.parquet")
              .select("CO_MUNICIPIO", "ETAPA", "ANO", "DISCIPLINA", "SALTO_ATIPICO")
              .pivot(on="DISCIPLINA", index=["CO_MUNICIPIO", "ETAPA", "ANO"], values="SALTO_ATIPICO")
              .rename({"MT": "SALTO_MT", "LP": "SALTO_LP"}))
    return (M.base()
            .join(parcela, on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
            .join(saltos, on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
            .with_columns(
                # gasto médio do biênio: média do ano da prova (L0) e do ano anterior (L1), em log
                ((pl.col("GASTO_ALUNO_R2025_L0") + pl.col("GASTO_ALUNO_R2025_L1")) / 2).log().alias("LOG_GASTO_BIENIO")))


def gasto(r: tuple | None) -> dict:
    if r is None:
        return {}
    g = next(c for c in r[0] if c["VARIAVEL"].startswith("LOG_GASTO"))
    return {"COEF": g["COEF"], "EP": g["EP"], "P": g["P"], "IC95_INF": g["IC95_INF"], "IC95_SUP": g["IC95_SUP"],
            "N": r[1]["N"], "UNIDADES": r[1].get("MUNICIPIOS", r[1].get("UFS"))}


def testes_municipais(p: pl.DataFrame, etapa: str, disc: str, nota: str) -> list[dict]:
    d = p.filter(pl.col("ETAPA") == etapa)
    com_nota = d.filter(pl.col("ANO").is_in(TODOS) & pl.col(nota).is_not_null())
    balanceados = com_nota.group_by("CO_MUNICIPIO").len().filter(pl.col("len") == len(TODOS))["CO_MUNICIPIO"]
    salto = f"SALTO_{disc}"
    bienio = d.with_columns(pl.col("LOG_GASTO_BIENIO").alias("LOG_GASTO_L0"))
    casos = [
        ("Referência (2017–2025)", d, REF),
        ("Sem 2021", d, {**REF, "anos": [2017, 2019, 2023, 2025]}),
        ("Painel balanceado", d.filter(pl.col("CO_MUNICIPIO").is_in(balanceados.implode())), REF),
        ("Referência em 2019–2025", d, {**REF, "anos": TODOS[1:]}),
        ("Gasto médio do biênio (2019–2025)", bienio, {**REF, "anos": TODOS[1:]}),
        ("Sem redes parciais (< 50%)", d.filter(~(pl.col("PART_MUN") < 0.5).fill_null(False)), REF),
        ("Sem redes abaixo de 80%", d.filter(~(pl.col("PART_MUN") < 0.8).fill_null(False)), REF),
        ("Sem saltos atípicos", d.filter(~pl.col(salto).fill_null(False)), REF),
        ("EF de município, IDHM Renda e Longevidade (2017–2023)", d,
         {"ef": True, "controles": M.NO_TEMPO + M.IDHM, "anos": TODOS[:-1]}),
        ("EF de município, IDHM total (2017–2023)", d, {"ef": True, "controles": M.NO_TEMPO + ["IDHM"], "anos": TODOS[:-1]}),
        ("EF de município, sem IDHM (2017–2023)", d, {"ef": True, "controles": M.NO_TEMPO, "anos": TODOS[:-1]}),
    ]
    return [{"CAMADA": "Municipal", "ETAPA": etapa, "DISCIPLINA": disc, "TESTE": nome, **gasto(M.estimar(dd, nota, 0, op))}
            for nome, dd, op in casos]


SUBF_BASICA = ["122", "361", "362", "365", "366", "367", "368"]  # G4b: sem 363 (profissional) e 364 (superior)


def razao_subfuncoes() -> pl.DataFrame:
    """Razão, por UF e ano, entre a soma das subfunções da educação básica e a versão A (função 12 − 12.364, com a
    12.364 ausente = zero), ambas pagas e nominais. Multiplicada pelo gasto por aluno da versão A, dá o gasto por aluno
    pela soma das subfunções com o mesmo denominador (matrículas da educação básica estadual) e o mesmo deflator."""
    d = pl.read_parquet(M.BASE_DIR / "data" / "interim" / "siconfi_estados_funcao12.parquet").filter(
        pl.col("COLUNA") == "Despesas Pagas")
    return (d.group_by("UF", "ANO")
            .agg(pl.col("VALOR").filter(pl.col("SUBF").is_null()).first().alias("F12"),
                 pl.col("VALOR").filter(pl.col("SUBF") == "364").sum().alias("S364"),
                 pl.col("VALOR").filter(pl.col("SUBF").is_in(SUBF_BASICA)).sum().alias("SOMA"))
            .select(pl.col("UF").alias("SG_UF"), pl.col("ANO").cast(pl.Int32),
                    (pl.col("SOMA") / (pl.col("F12") - pl.col("S364"))).alias("RAZAO_SUBF")))


def testes_estaduais(etapa: str, disc: str, nota: str) -> list[dict]:
    d = E.base().filter(pl.col("ETAPA") == etapa)
    versao_b = d.with_columns(
        pl.when(pl.col("GASTO_ALUNO_B_R2025_L0") > 0).then(pl.col("GASTO_ALUNO_B_R2025_L0").log()).alias("LOG_GASTO_L0"))
    subf = (d.with_columns(pl.col("ANO").cast(pl.Int32)).join(razao_subfuncoes(), on=["SG_UF", "ANO"], how="left")
            .with_columns((pl.col("GASTO_ALUNO_A_R2025_L0") * pl.col("RAZAO_SUBF")).alias("G"))
            .with_columns(pl.when(pl.col("G") > 0).then(pl.col("G").log()).alias("LOG_GASTO_L0")))
    ref = E.ESPECIFICACOES[E.REFERENCIA]
    casos = [("Referência (EF de UF, 2017–2023, versão A)", d, ref),
             ("Com 2025, sem IDHM", d, E.ESPECIFICACOES["EF de UF, com 2025"]),
             ("Versão B do gasto", versao_b, ref),
             ("Soma das subfunções da educação básica", subf, ref)]
    return [{"CAMADA": "Estadual", "ETAPA": etapa, "DISCIPLINA": disc, "TESTE": nome, **gasto(E.estimar(dd, nota, 0, op))}
            for nome, dd, op in casos]


def main() -> None:
    p = base_municipal()
    linhas = []
    for disc, nota in M.DISCIPLINAS.items():
        for etapa in ["AI", "AF"]:
            linhas += testes_municipais(p, etapa, disc, nota)
        for etapa in ["AF", "EM"]:
            linhas += testes_estaduais(etapa, disc, nota)
    saida = pl.DataFrame(linhas).with_columns((pl.col("COEF") * np.log(1.1)).alias("PONTOS_POR_10PCT"))
    arquivo = M.DIAG_DIR / "sensibilidade_modelo.csv"
    saida.write_csv(arquivo)
    with pl.Config(tbl_rows=200, tbl_cols=20, tbl_width_chars=220, float_precision=2, fmt_str_lengths=60):
        print(saida.select("CAMADA", "ETAPA", "DISCIPLINA", "TESTE", "COEF", "EP", "P", "N", "UNIDADES"))
    print(f"[OK] {saida.height} linhas em {arquivo.relative_to(M.BASE_DIR)}")


if __name__ == "__main__":
    main()
