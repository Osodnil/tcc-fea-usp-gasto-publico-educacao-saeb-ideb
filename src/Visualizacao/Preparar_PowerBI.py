"""Monta o modelo em estrela do dashboard oficial (Power BI) a partir de data/processed.

Grava data/processed/powerbi/*.parquet, que o arquivo .pbix lê sem transformações no Power Query:
- dimensões: dim_municipio (com cluster), dim_uf, dim_cluster, dim_ano, dim_etapa, dim_disciplina,
  dim_defasagem e dim_modelo (as duas últimas são parâmetros, sem relacionamento);
- fatos: fato_desempenho_municipal e fato_desempenho_estadual (formato longo: uma linha por rede,
  etapa, disciplina e edição, com a proficiência em pontos, decisão S9), fato_gasto_municipal e
  fato_gasto_estadual (gasto anual, 2017-2025).

Nada é recalculado aqui: o script só junta, renomeia e empilha as tabelas já validadas.
A especificação do dashboard está em powerbi/especificacao_dashboard.md.
"""
from pathlib import Path

import polars as pl


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DESTINO = PROCESSED_DIR / "powerbi"

DISCIPLINAS = {"MT": "NOTA_MT", "LP": "NOTA_LP"}
INFRA = ["PROP_IN_BIBLIOTECA", "PROP_IN_LABORATORIO_INFORMATICA", "PROP_IN_LABORATORIO_CIENCIAS", "PROP_IN_INTERNET",
         "PROP_IN_BANHEIRO", "PROP_IN_AGUA_POTAVEL", "PROP_IN_ENERGIA_REDE_PUBLICA", "PROP_IN_QUADRA_ESPORTES"]
EDICOES = [2017, 2019, 2021, 2023, 2025]
EDICOES_OFICIAL = [2017, 2019, 2021, 2023]  # modelo nacional com IDHM (decisão A8)


def longo(painel: pl.DataFrame, chave: list[str], comuns: list[str]) -> pl.DataFrame:
    """Empilha NOTA_MT e NOTA_LP numa coluna PROFICIENCIA, com a coluna DISCIPLINA."""
    return pl.concat([
        painel.select(*chave, pl.lit(disc).alias("DISCIPLINA"), pl.col(nota).alias("PROFICIENCIA"), *comuns)
        for disc, nota in DISCIPLINAS.items()
    ])


def dimensoes(uf: pl.DataFrame) -> dict[str, pl.DataFrame]:
    clusters = pl.read_parquet(PROCESSED_DIR / "cluster_municipio.parquet").select("CO_MUNICIPIO", "CLUSTER", "CLUSTER_ROTULO")
    municipio = (
        pl.read_parquet(PROCESSED_DIR / "dim_municipio.parquet")
        .join(uf.select("SG_UF", "NM_UF"), on="SG_UF", how="left")
        .join(clusters, on="CO_MUNICIPIO", how="left")
        .with_columns(
            (pl.col("NO_MUNICIPIO") + " (" + pl.col("SG_UF") + ")").alias("MUNICIPIO_UF"),
            pl.col("CLUSTER_ROTULO").fill_null("Sem cluster"),
            # rótulo curto para legendas (o completo era cortado nas dispersões, 2026-11-09): número, região e porte
            pl.when(pl.col("CLUSTER").is_null()).then(pl.lit("Sem cluster"))
            .otherwise(pl.col("CLUSTER").cast(pl.Utf8) + " · "
                       + pl.col("CLUSTER_ROTULO").str.split(" · ").list.slice(0, 2).list.join(" · "))
            .alias("CLUSTER_CURTO"),
        )
        .select("CO_MUNICIPIO", "NO_MUNICIPIO", "MUNICIPIO_UF", "SG_UF", "NM_UF", "NM_REGIAO", "POPULACAO_TOTAL_CENSO",
                "TAXA_ALFABETIZACAO_15MAIS", "PORTE", "PORTE_ORDEM", "FAIXA_ALFABETIZACAO", "CLUSTER", "CLUSTER_ROTULO",
                "CLUSTER_CURTO")
        .sort("CO_MUNICIPIO")
    )
    anos = list(range(2017, 2026))
    return {
        "dim_municipio": municipio,
        "dim_uf": uf,
        "dim_cluster": pl.read_parquet(PROCESSED_DIR / "cluster_resumo.parquet"),
        "dim_ano": pl.DataFrame({
            "ANO": anos,
            "EDICAO_SAEB": [a in EDICOES for a in anos],
            "TEM_IDHM": [a <= 2024 for a in anos],
            "EFICIENCIA_OFICIAL": [a in EDICOES_OFICIAL for a in anos],
        }, schema_overrides={"ANO": pl.Int32}),
        "dim_etapa": pl.DataFrame({
            "ETAPA": ["AI", "AF", "EM"],
            "NOME_ETAPA": ["Anos Iniciais (5º ano)", "Anos Finais (9º ano)", "Ensino Médio (3ª série)"],
            "ORDEM": [1, 2, 3],
            "CAMADA": ["Municipal", "Municipal e estadual", "Estadual"],
        }),
        "dim_disciplina": pl.DataFrame({"DISCIPLINA": ["MT", "LP"], "NOME_DISCIPLINA": ["Matemática", "Língua Portuguesa"], "ORDEM": [1, 2]}),
        "dim_defasagem": pl.DataFrame({
            "DEFASAGEM": [0, 1, 2, 4],
            "ROTULO_DEFASAGEM": ["Mesmo ano", "1 ano antes", "2 anos antes", "4 anos antes"],
        }),
        # rótulos revistos na reunião de 2026-11-06: o modelo de UF não filtra a UF, muda a régua da comparação
        "dim_modelo": pl.DataFrame({
            "MODELO": ["Oficial", "Robustez"],
            "ROTULO_MODELO": ["Comparação nacional (2017–2023)", "Comparação no próprio estado (2017–2025)"],
            "ORDEM": [1, 2],
        }),
    }


SEM_REDE, SEM_DIVULGACAO, COM_NOTA = "Sem rede municipal na etapa", "Sem nota divulgada pelo Inep", "Com nota"


def fato_oferta(municipio: pl.DataFrame, painel: pl.DataFrame) -> pl.DataFrame:
    """Matrículas da etapa por rede (Censo Escolar) para cada município, etapa (AI, AF) e ano, e a situação da
    rede municipal nas edições do Saeb: com nota, sem nota divulgada (há alunos na rede) ou sem rede na etapa.
    PART_MUN = parcela das matrículas públicas (municipal + estadual) da etapa que está na rede municipal."""
    blocos = []
    for ano in range(2017, 2026):
        c = pl.read_parquet(BASE_DIR / "data" / "interim" / f"censo_matriculas_{ano}.parquet")
        for etapa, col in (("AI", "QT_MAT_FUND_AI"), ("AF", "QT_MAT_FUND_AF")):
            blocos.append(c.filter(pl.col("REDE").is_in(["Municipal", "Estadual"]))
                          .group_by("CO_MUNICIPIO").agg(
                              pl.col(col).filter(pl.col("REDE") == "Municipal").sum().alias("QT_MAT_MUN"),
                              pl.col(col).filter(pl.col("REDE") == "Estadual").sum().alias("QT_MAT_EST"))
                          .with_columns(pl.lit(etapa).alias("ETAPA"), pl.lit(ano, dtype=pl.Int32).alias("ANO")))
    mat = pl.concat(blocos)
    grade = municipio.select("CO_MUNICIPIO").join(
        pl.DataFrame({"ETAPA": ["AI", "AF"]}), how="cross").join(
        pl.DataFrame({"ANO": list(range(2017, 2026))}, schema={"ANO": pl.Int32}), how="cross")
    nota = painel.filter(pl.col("TEM_NOTA")).select("CO_MUNICIPIO", "ETAPA", "ANO").with_columns(pl.lit(True).alias("_NOTA"))
    return (
        grade.join(mat, on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
        .join(nota, on=["CO_MUNICIPIO", "ETAPA", "ANO"], how="left")
        .with_columns(pl.col("QT_MAT_MUN", "QT_MAT_EST").fill_null(0.0))
        .with_columns(
            pl.when(pl.col("QT_MAT_MUN") + pl.col("QT_MAT_EST") > 0)
            .then(pl.col("QT_MAT_MUN") / (pl.col("QT_MAT_MUN") + pl.col("QT_MAT_EST"))).alias("PART_MUN"),
            pl.when(~pl.col("ANO").is_in(EDICOES)).then(None)
            .when(pl.col("_NOTA").fill_null(False)).then(pl.lit(COM_NOTA))
            .when(pl.col("QT_MAT_MUN") == 0).then(pl.lit(SEM_REDE))
            .otherwise(pl.lit(SEM_DIVULGACAO)).alias("SITUACAO"))
        .drop("_NOTA")
        .sort("CO_MUNICIPIO", "ETAPA", "ANO")
    )


def fatos_municipais() -> dict[str, pl.DataFrame]:
    painel = pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet").with_columns(pl.mean_horizontal(INFRA).alias("INFRA"))
    comuns = ["NOTA_N", "IND_REND", "IDEB",
              *[f"GASTO_ALUNO_R2025_L{k}" for k in (0, 1, 2, 4)], "GASTO_EXTREMO_L0",
              "QT_MAT_FUND", "IDHM_RENDA", "IDHM_LONGEVIDADE", "INFRA"]
    efic = pl.read_parquet(PROCESSED_DIR / "eficiencia_municipal.parquet").drop("CLUSTER", "CLUSTER_ROTULO", "NOTA")
    desempenho = (
        longo(painel, ["CO_MUNICIPIO", "ETAPA", "ANO"], comuns)
        .join(efic, on=["CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO"], how="left")
        .with_columns(pl.col("SALTO_ATIPICO").fill_null(False))
        .sort("CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO")
    )
    # conferência: a proficiência da eficiência tem de ser a mesma do painel
    conf = pl.read_parquet(PROCESSED_DIR / "eficiencia_municipal.parquet").join(
        desempenho.select("CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO", "PROFICIENCIA"),
        on=["CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO"], how="left")
    assert conf.filter((pl.col("NOTA") - pl.col("PROFICIENCIA")).abs() > 1e-9).height == 0, "proficiência divergente"
    assert conf["PROFICIENCIA"].null_count() == 0, "linha de eficiência sem par no painel"
    gasto = pl.read_parquet(PROCESSED_DIR / "gasto_municipal_anual.parquet")
    return {"fato_desempenho_municipal": desempenho, "fato_gasto_municipal": gasto}


def fatos_estaduais() -> dict[str, pl.DataFrame]:
    painel = pl.read_parquet(PROCESSED_DIR / "painel_estadual.parquet").with_columns(pl.mean_horizontal(INFRA).alias("INFRA"))
    comuns = ["NOTA_N", "IND_REND", "IDEB", "SUP364_AUSENTE",
              *[f"GASTO_ALUNO_{v}_R2025_L{k}" for k in (0, 1, 2, 4) for v in ("A", "B")],
              "QT_MAT_BAS", "IDHM_RENDA", "IDHM_LONGEVIDADE", "INFRA"]
    desempenho = longo(painel, ["SG_UF", "ETAPA", "ANO"], comuns).sort("SG_UF", "ETAPA", "DISCIPLINA", "ANO")
    gasto = pl.read_parquet(PROCESSED_DIR / "gasto_estadual_anual.parquet")
    return {"fato_desempenho_estadual": desempenho, "fato_gasto_estadual": gasto}


if __name__ == "__main__":
    DESTINO.mkdir(parents=True, exist_ok=True)
    uf = pl.read_parquet(PROCESSED_DIR / "dim_uf.parquet")
    tabelas = {**dimensoes(uf), **fatos_municipais(), **fatos_estaduais()}
    tabelas["fato_oferta_municipal"] = fato_oferta(tabelas["dim_municipio"], pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet"))

    chaves = {
        "dim_municipio": ["CO_MUNICIPIO"], "dim_uf": ["SG_UF"], "dim_cluster": ["CLUSTER"], "dim_ano": ["ANO"],
        "dim_etapa": ["ETAPA"], "dim_disciplina": ["DISCIPLINA"], "dim_defasagem": ["DEFASAGEM"], "dim_modelo": ["MODELO"],
        "fato_desempenho_municipal": ["CO_MUNICIPIO", "ETAPA", "DISCIPLINA", "ANO"], "fato_gasto_municipal": ["CO_MUNICIPIO", "ANO"],
        "fato_desempenho_estadual": ["SG_UF", "ETAPA", "DISCIPLINA", "ANO"], "fato_gasto_estadual": ["SG_UF", "ANO"],
        "fato_oferta_municipal": ["CO_MUNICIPIO", "ETAPA", "ANO"],
    }
    for nome, df in tabelas.items():
        dup = df.height - df.select(chaves[nome]).unique().height
        assert dup == 0, f"{nome}: chave {chaves[nome]} repetida em {dup} linhas"
        df.write_parquet(DESTINO / f"{nome}.parquet")
        print(f"[OK] {nome:28s} {df.height:>7} linhas × {df.width:>2} colunas (chave: {', '.join(chaves[nome])})")

    # integridade referencial: toda chave dos fatos existe na dimensão
    mun = set(tabelas["dim_municipio"]["CO_MUNICIPIO"])
    for f in ("fato_desempenho_municipal", "fato_gasto_municipal"):
        orfaos = set(tabelas[f]["CO_MUNICIPIO"]) - mun
        print(f"[INFO] {f}: municípios fora de dim_municipio = {len(orfaos)}")
    d = tabelas["fato_desempenho_municipal"]
    print(f"[INFO] Linhas com proficiência: {d['PROFICIENCIA'].is_not_null().sum()} | com eficiência oficial: "
          f"{d['RESIDUO'].is_not_null().sum()} | com eficiência de robustez: {d['RESIDUO_ALT'].is_not_null().sum()} | "
          f"saltos atípicos: {d['SALTO_ATIPICO'].sum()}")

    # oferta: a situação "com nota" tem de bater com o painel, e as matrículas municipais com as do painel
    o = tabelas["fato_oferta_municipal"]
    painel = pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet")
    assert o.filter(pl.col("SITUACAO") == COM_NOTA).height == painel.filter(pl.col("TEM_NOTA")).height, "situação ≠ painel"
    dif = painel.filter(pl.col("ETAPA") == "AI").join(o.filter(pl.col("ETAPA") == "AI"), on=["CO_MUNICIPIO", "ETAPA", "ANO"]) \
        .filter((pl.col("QT_MAT_FUND_AI").fill_null(0) - pl.col("QT_MAT_MUN")).abs() > 0.5).height
    print(f"[INFO] fato_oferta_municipal: linhas de AI com matrícula municipal diferente do painel = {dif}")
    print("[INFO] Situação da rede nas edições:", o.filter(pl.col("SITUACAO").is_not_null())
          .group_by("ETAPA", "SITUACAO").len().sort("ETAPA", "SITUACAO").rows())
