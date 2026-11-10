"""Modelo principal da camada municipal: o gasto por aluno se associa à proficiência? E dentro do mesmo município?

Responde às perguntas analíticas 1 e 2 (decisões A1, A2): para cada etapa (AI principal, AF complementar),
disciplina (MT, LP, em pontos do Saeb; S9) e defasagem do gasto (0, 1, 2 e 4 anos; G12), estima

    proficiência = b·log(gasto por aluno, R$ de 2025) + controles + efeitos de edição [+ efeito fixo de município] + erro

em quatro especificações, todas com erros-padrão agrupados por município:

- "MQO agrupado" (entre e dentro dos municípios): controles de contexto fixos (log da população e alfabetização,
  Censo 2022) e variáveis no tempo (infraestrutura, log das matrículas do Fundamental, IDHM Renda e Longevidade
  da UF); edições 2017-2023 (sem IDHM em 2025; C1). É a especificação do indicador de eficiência.
- "EF de município" (só dentro do município): a mesma, com efeito fixo de município; os controles fixos no tempo
  saem, porque o efeito fixo os absorve. b mede se, quando o gasto de um município sobe em relação à média dele,
  a nota também sobe, descontada a tendência comum de cada edição. Edições 2017-2023.
- "EF de município, com 2025": sem o IDHM (que não existe em 2025), edições 2017-2025.
- "EF de município e UF × edição" (REFERÊNCIA desde 2026-11-10, decisão A11): efeito fixo de município e efeito de
  UF × edição no lugar do efeito de edição; edições 2017-2025. Compara municípios do mesmo estado na mesma edição
  e absorve o IDHM inteiro (que é da UF e do ano), por isso cobre 2025 sem contrariar a decisão C1. Retira os
  choques comuns ao estado, que faziam 2025 dobrar o coeficiente (src/Analise/Investigar_2025.py).

A comparação entre a primeira e a segunda mostra quanto da associação vem das diferenças entre municípios.
Associação, não efeito causal (A1). Os gastos extremos ficam (A5).

Efeito fixo pela transformação "dentro" (desvio em relação à média do município, inclusive das dummies de edição),
equivalente ao xtreg, fe vce(cluster) do Stata; os municípios com uma só observação (singletons) saem, porque não
informam nada sobre a variação dentro do município.

Saídas (data/interim/diagnosticos):
- modelo_principal_coeficientes.csv: formato longo, uma linha por variável;
- modelo_principal_defasagens_mesma_amostra.csv: as defasagens comparadas nas mesmas linhas (EF de município,
  na especificação de referência e na com IDHM).
"""
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DIAG_DIR = BASE_DIR / "data" / "interim" / "diagnosticos"

DISCIPLINAS = {"MT": "NOTA_MT", "LP": "NOTA_LP"}
DEFASAGENS = [0, 1, 2, 4]
INFRA = ["PROP_IN_BIBLIOTECA", "PROP_IN_LABORATORIO_INFORMATICA", "PROP_IN_LABORATORIO_CIENCIAS", "PROP_IN_INTERNET",
         "PROP_IN_BANHEIRO", "PROP_IN_AGUA_POTAVEL", "PROP_IN_ENERGIA_REDE_PUBLICA", "PROP_IN_QUADRA_ESPORTES"]
FIXOS = ["LOG_POP", "ALFAB"]               # Censo 2022: não variam no tempo
NO_TEMPO = ["INFRA", "LOG_MAT"]
IDHM = ["IDHM_RENDA", "IDHM_LONGEVIDADE"]  # por UF e ano (C1, C1b)
ESPECIFICACOES = {
    "MQO agrupado": {"ef": False, "controles": FIXOS + NO_TEMPO + IDHM, "anos": [2017, 2019, 2021, 2023]},
    "EF de município": {"ef": True, "controles": NO_TEMPO + IDHM, "anos": [2017, 2019, 2021, 2023]},
    "EF de município, com 2025": {"ef": True, "controles": NO_TEMPO, "anos": [2017, 2019, 2021, 2023, 2025]},
    "EF de município e UF × edição": {"ef": True, "controles": NO_TEMPO, "anos": [2017, 2019, 2021, 2023, 2025],
                                      "uf_ano": True},
}
REFERENCIA = "EF de município e UF × edição"


def base() -> pl.DataFrame:
    d = pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet").with_columns(
        pl.col("POPULACAO_TOTAL_CENSO").log10().alias("LOG_POP"),
        (pl.col("TAXA_ALFABETIZACAO_15MAIS") * 100).alias("ALFAB"),
        pl.mean_horizontal(INFRA).alias("INFRA"),
        pl.when(pl.col("QT_MAT_FUND") > 0).then(pl.col("QT_MAT_FUND").log10()).alias("LOG_MAT"),
        *[pl.when(pl.col(f"GASTO_ALUNO_R2025_L{k}") > 0).then(pl.col(f"GASTO_ALUNO_R2025_L{k}").log())
          .alias(f"LOG_GASTO_L{k}") for k in DEFASAGENS],
    )
    assert d.select(pl.struct("CO_MUNICIPIO", "ETAPA", "ANO").is_unique().all()).item(), "painel com chave repetida"
    return d


def estimar(d: pl.DataFrame, nota: str, k: int, op: dict) -> tuple[list[dict], dict] | None:
    x_cols = [f"LOG_GASTO_L{k}", *op["controles"]]
    d = d.filter(pl.col("ANO").is_in(op["anos"])).drop_nulls([nota, *x_cols])
    if op["ef"]:  # singletons não informam a variação dentro do município
        d = d.filter(pl.len().over("CO_MUNICIPIO") > 1)
    anos = sorted(d["ANO"].unique().to_list())
    if d.height == 0 or len(anos) < 2:
        return None
    if op.get("uf_ano"):  # efeito de UF × edição no lugar do efeito de edição (contém o de edição)
        d = d.with_columns((pl.col("SG_UF") + "_" + pl.col("ANO").cast(pl.Utf8)).alias("UF_ANO"))
        niveis = sorted(d["UF_ANO"].unique().to_list())[1:]
        d = d.with_columns([(pl.col("UF_ANO") == v).cast(pl.Float64).alias(f"ANO_UF_{v}") for v in niveis])
        cols = [*x_cols, *[f"ANO_UF_{v}" for v in niveis]]
    else:
        d = d.with_columns([(pl.col("ANO") == a).cast(pl.Float64).alias(f"ANO_{a}") for a in anos[1:]])
        cols = [*x_cols, *[f"ANO_{a}" for a in anos[1:]]]
    if op["ef"]:  # transformação "dentro": tira a média do município de y e de todas as colunas de X
        d = d.with_columns([(pl.col(c) - pl.col(c).mean().over("CO_MUNICIPIO")).alias(c) for c in [nota, *cols]])
        X = np.column_stack([d[c].cast(pl.Float64).to_numpy() for c in cols])
        nomes = cols
    else:
        X = np.column_stack([np.ones(d.height), *[d[c].cast(pl.Float64).to_numpy() for c in cols]])
        nomes = ["const", *cols]
    y = d[nota].to_numpy()
    grupos = d["CO_MUNICIPIO"].cast(pl.Int64).to_numpy()
    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": grupos})
    ic = res.conf_int()
    coefs = [{"VARIAVEL": v, "COEF": res.params[i], "EP": res.bse[i], "P": res.pvalues[i],
              "IC95_INF": ic[i][0], "IC95_SUP": ic[i][1]}
             for i, v in enumerate(nomes) if not v.startswith("ANO_")]
    ajuste = {"N": int(res.nobs), "MUNICIPIOS": len(set(grupos)), "EDICOES": "-".join(map(str, anos)),
              "R2": res.rsquared}  # no EF, R² "dentro" (da variação em torno da média do município)
    return coefs, ajuste


def main() -> None:
    painel = base()
    linhas = []
    for etapa in ["AI", "AF"]:
        for disc, nota in DISCIPLINAS.items():
            d_etapa = painel.filter(pl.col("ETAPA") == etapa)
            # desvio-padrão da nota entre as redes (2017-2023), para ler o efeito em desvios-padrão
            dp_nota = d_etapa.filter(pl.col("ANO") <= 2023)[nota].drop_nulls().std()
            for k in DEFASAGENS:
                for esp, op in ESPECIFICACOES.items():
                    r = estimar(d_etapa, nota, k, op)
                    if r is None:
                        continue
                    coefs, ajuste = r
                    for c in coefs:
                        linhas.append({"ETAPA": etapa, "DISCIPLINA": disc, "DEFASAGEM": k, "ESPECIFICACAO": esp,
                                       **c, **ajuste, "DP_NOTA": dp_nota})
    saida = pl.DataFrame(linhas).with_columns(
        # efeito associado a +10% no gasto por aluno: b·ln(1,1) pontos, e o mesmo em desvios-padrão da nota
        pl.when(pl.col("VARIAVEL").str.starts_with("LOG_GASTO")).then(pl.col("COEF") * np.log(1.1))
        .alias("PONTOS_POR_10PCT"),
    ).with_columns((pl.col("PONTOS_POR_10PCT") / pl.col("DP_NOTA")).alias("DP_POR_10PCT"),
                   (pl.col("ESPECIFICACAO") == REFERENCIA).alias("REFERENCIA"))
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    arquivo = DIAG_DIR / "modelo_principal_coeficientes.csv"
    saida.write_csv(arquivo)

    # Defasagens comparadas na mesma amostra (EF de município): a defasagem de 1 e 2 anos só existe a partir de 2019,
    # e a de 4 anos a partir de 2021, então as estimativas acima vêm de amostras diferentes. Aqui todas as defasagens
    # usam as mesmas linhas (as que têm todos os gastos daquela janela).
    janelas = {"2019-2023, com IDHM": ([2019, 2021, 2023], [0, 1, 2], NO_TEMPO + IDHM, False),
               "2019-2025, UF × edição": ([2019, 2021, 2023, 2025], [0, 1, 2], NO_TEMPO, True),
               "2021-2025, UF × edição": ([2021, 2023, 2025], [0, 1, 2, 4], NO_TEMPO, True)}
    comp = []
    for etapa in ["AI", "AF"]:
        for disc, nota in DISCIPLINAS.items():
            for janela, (anos, ks, controles, uf_ano) in janelas.items():
                d = painel.filter(pl.col("ETAPA") == etapa).drop_nulls([f"LOG_GASTO_L{k}" for k in ks])
                for k in ks:
                    r = estimar(d, nota, k, {"ef": True, "controles": controles, "anos": anos, "uf_ano": uf_ano})
                    if r is None:
                        continue
                    g = next(c for c in r[0] if c["VARIAVEL"].startswith("LOG_GASTO"))
                    comp.append({"ETAPA": etapa, "DISCIPLINA": disc, "JANELA": janela, "DEFASAGEM": k,
                                 **{c: g[c] for c in ("COEF", "EP", "P")}, "N": r[1]["N"]})
    comp = pl.DataFrame(comp)
    arquivo_comp = DIAG_DIR / "modelo_principal_defasagens_mesma_amostra.csv"
    comp.write_csv(arquivo_comp)

    gasto = saida.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO")).sort("ETAPA", "DISCIPLINA", "DEFASAGEM")
    with pl.Config(tbl_rows=100, tbl_cols=20, tbl_width_chars=220, float_precision=3):
        print(gasto.select("ETAPA", "DISCIPLINA", "DEFASAGEM", "ESPECIFICACAO", "COEF", "EP", "P",
                           "PONTOS_POR_10PCT", "DP_POR_10PCT", "N", "MUNICIPIOS", "EDICOES", "R2"))
        print(comp.sort("ETAPA", "DISCIPLINA", "JANELA", "DEFASAGEM"))
    print(f"[OK] {saida.height} linhas em {arquivo.relative_to(BASE_DIR)}; "
          f"{comp.height} em {arquivo_comp.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
