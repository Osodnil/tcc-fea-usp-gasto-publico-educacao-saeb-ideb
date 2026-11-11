"""Modelo da camada estadual: o gasto estadual por aluno se associa à proficiência das redes estaduais?

Responde à pergunta analítica 4 (decisões A1, A2): para cada etapa (AF e EM), disciplina (MT, LP, em pontos do
Saeb; S9) e defasagem do gasto (0, 1, 2 e 4 anos; G12), estima

    proficiência = b·log(gasto estadual por aluno, versão A, R$ de 2025) + controles + efeitos de edição [+ efeito de UF]

em três especificações:

- "MQO agrupado": controles fixos (log da população e alfabetização, Censo 2022), infraestrutura das escolas
  estaduais, log das matrículas da educação básica estadual e IDHM Renda e Longevidade da UF; edições 2017-2023.
- "EF de UF" (referência): a mesma, com efeito fixo de UF (que absorve os controles fixos); 2017-2023. Mede se,
  quando o gasto de uma UF sobe em relação à média dela, a nota da rede estadual também sobe.
- "EF de UF, com 2025": sem o IDHM, que não existe em 2025 (C1); 2017-2025. As matrículas estaduais caem 5,1%
  em 2025 (M3), o que pode inflar o gasto por aluno desse ano: ler com cautela.

O gasto é o mesmo nas duas etapas (toda a educação básica estadual, G4). Só 27 UFs: erros-padrão agrupados por UF
com valores-p pela distribuição t com 26 graus de liberdade (correção para poucos grupos); a leitura é cautelosa e
a camada é descritiva no painel. A versão B do gasto entra nos testes de sensibilidade (A4). Associação, não
efeito causal (A1).

Saída: data/interim/diagnosticos/modelo_estadual_coeficientes.csv (formato longo, uma linha por variável).
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
FIXOS = ["LOG_POP", "ALFAB"]
NO_TEMPO = ["INFRA", "LOG_MAT"]
IDHM = ["IDHM_RENDA", "IDHM_LONGEVIDADE"]
ESPECIFICACOES = {
    "MQO agrupado": {"ef": False, "controles": FIXOS + NO_TEMPO + IDHM, "anos": [2017, 2019, 2021, 2023]},
    "EF de UF": {"ef": True, "controles": NO_TEMPO + IDHM, "anos": [2017, 2019, 2021, 2023]},
    "EF de UF, com 2025": {"ef": True, "controles": NO_TEMPO, "anos": [2017, 2019, 2021, 2023, 2025]},
}
REFERENCIA = "EF de UF"


def base() -> pl.DataFrame:
    d = pl.read_parquet(PROCESSED_DIR / "painel_estadual.parquet").with_columns(
        pl.col("POPULACAO_TOTAL_CENSO").log10().alias("LOG_POP"),
        (pl.col("TAXA_ALFABETIZACAO_15MAIS") * 100).alias("ALFAB"),
        pl.mean_horizontal(INFRA).alias("INFRA"),
        pl.when(pl.col("QT_MAT_BAS") > 0).then(pl.col("QT_MAT_BAS").log10()).alias("LOG_MAT"),
        *[pl.when(pl.col(f"GASTO_ALUNO_A_R2025_L{k}") > 0).then(pl.col(f"GASTO_ALUNO_A_R2025_L{k}").log())
          .alias(f"LOG_GASTO_L{k}") for k in DEFASAGENS],
    )
    assert d.select(pl.struct("SG_UF", "ETAPA", "ANO").is_unique().all()).item(), "painel com chave repetida"
    return d


def estimar(d: pl.DataFrame, nota: str, k: int, op: dict) -> tuple[list[dict], dict] | None:
    x_cols = [f"LOG_GASTO_L{k}", *op["controles"]]
    d = d.filter(pl.col("ANO").is_in(op["anos"])).drop_nulls([nota, *x_cols])
    if op["ef"]:
        d = d.filter(pl.len().over("SG_UF") > 1)
    anos = sorted(d["ANO"].unique().to_list())
    if d.height == 0 or len(anos) < 2:
        return None
    d = d.with_columns([(pl.col("ANO") == a).cast(pl.Float64).alias(f"ANO_{a}") for a in anos[1:]])
    cols = [*x_cols, *[f"ANO_{a}" for a in anos[1:]]]
    if op["ef"]:  # transformação "dentro" da UF
        d = d.with_columns([(pl.col(c) - pl.col(c).mean().over("SG_UF")).alias(c) for c in [nota, *cols]])
        X = np.column_stack([d[c].cast(pl.Float64).to_numpy() for c in cols])
        nomes = cols
    else:
        X = np.column_stack([np.ones(d.height), *[d[c].cast(pl.Float64).to_numpy() for c in cols]])
        nomes = ["const", *cols]
    y = d[nota].to_numpy()
    grupos = d["SG_UF"].rank("dense").cast(pl.Int64).to_numpy()
    # poucos grupos: valores-p e intervalos pela t com G-1 graus de liberdade
    res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": grupos, "df_correction": True}, use_t=True)
    ic = res.conf_int()
    coefs = [{"VARIAVEL": v, "COEF": res.params[i], "EP": res.bse[i], "P": res.pvalues[i],
              "IC95_INF": ic[i][0], "IC95_SUP": ic[i][1]}
             for i, v in enumerate(nomes) if not v.startswith("ANO_")]
    ajuste = {"N": int(res.nobs), "UFS": len(set(grupos)), "EDICOES": "-".join(map(str, anos)), "R2": res.rsquared}
    return coefs, ajuste


def main() -> None:
    painel = base()
    linhas = []
    for etapa in ["AF", "EM"]:
        for disc, nota in DISCIPLINAS.items():
            d_etapa = painel.filter(pl.col("ETAPA") == etapa)
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
        pl.when(pl.col("VARIAVEL").str.starts_with("LOG_GASTO")).then(pl.col("COEF") * np.log(1.1))
        .alias("PONTOS_POR_10PCT"),
    ).with_columns((pl.col("PONTOS_POR_10PCT") / pl.col("DP_NOTA")).alias("DP_POR_10PCT"),
                   (pl.col("ESPECIFICACAO") == REFERENCIA).alias("REFERENCIA"))
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    arquivo = DIAG_DIR / "modelo_estadual_coeficientes.csv"
    saida.write_csv(arquivo)
    gasto = saida.filter(pl.col("VARIAVEL").str.starts_with("LOG_GASTO")).sort("ETAPA", "DISCIPLINA", "DEFASAGEM")
    with pl.Config(tbl_rows=100, tbl_cols=20, tbl_width_chars=220, float_precision=3):
        print(gasto.select("ETAPA", "DISCIPLINA", "DEFASAGEM", "ESPECIFICACAO", "COEF", "EP", "P",
                           "PONTOS_POR_10PCT", "N", "UFS", "EDICOES", "R2"))
    print(f"[OK] {saida.height} linhas em {arquivo.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
