import json
import subprocess
from datetime import date
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
TEMPLATE = Path(__file__).resolve().parent / "template_dashboard.html"
SAIDA_DIR = BASE_DIR / "relatorios"
SAIDA_DIR.mkdir(parents=True, exist_ok=True)
DESTINO = SAIDA_DIR / "dashboard_conferencia.html"

FAIXAS_ALF = {"Baixa": 0, "Média": 1, "Alta": 2}


def ler(nome: str) -> pl.DataFrame:
    return pl.read_parquet(PROCESSED_DIR / f"{nome}.parquet")


def arredondar(serie: pl.Series, casas: int) -> list:
    return [None if v is None else round(v, casas) for v in serie.to_list()]


def booleanos(serie: pl.Series) -> list:
    return [1 if v else 0 for v in serie.fill_null(False).to_list()]


def dados_municipais() -> dict:
    """Dados municipais em formato colunar; cada linha aponta para o município pelo índice m."""
    dim = ler("dim_municipio").sort("CO_MUNICIPIO").with_row_index("IDX")
    portes = dim.select("PORTE_ORDEM", "PORTE").unique().sort("PORTE_ORDEM")["PORTE"].to_list()
    idx = dim.select("CO_MUNICIPIO", "IDX")

    p = ler("painel_municipal").join(idx, on="CO_MUNICIPIO").sort("IDX", "ETAPA", "ANO")
    a = ler("gasto_municipal_anual").join(idx, on="CO_MUNICIPIO").sort("IDX", "ANO")
    return {
        "portes": portes,
        "municipios": {
            "cod": dim["CO_MUNICIPIO"].to_list(),
            "nome": dim["NO_MUNICIPIO"].to_list(),
            "uf": dim["SG_UF"].to_list(),
            "regiao": dim["NM_REGIAO"].to_list(),
            "pop": arredondar(dim["POPULACAO_TOTAL_CENSO"], 0),
            "porte": dim["PORTE_ORDEM"].to_list(),
            "alf": arredondar(dim["TAXA_ALFABETIZACAO_15MAIS"] * 100, 1),  # proporção 0-1 -> %
            "faixaAlf": [FAIXAS_ALF.get(v, -1) for v in dim["FAIXA_ALFABETIZACAO"].to_list()],
        },
        "linhas": {
            "m": p["IDX"].to_list(),
            "etapa": p["ETAPA"].to_list(),
            "ano": p["ANO"].to_list(),
            "mt": arredondar(p["NOTA_MT"], 1),
            "lp": arredondar(p["NOTA_LP"], 1),
            "n": arredondar(p["NOTA_N"], 2),
            "ideb": arredondar(p["IDEB"], 1),
            **{f"g{k}": arredondar(p[f"GASTO_ALUNO_R2025_L{k}"], 0) for k in (0, 1, 2, 4)},
            "extremo": booleanos(p["GASTO_EXTREMO_L0"]),
            "mat": arredondar(p["QT_MAT_FUND"], 0),
        },
        "anual": {
            "m": a["IDX"].to_list(),
            "ano": a["ANO"].to_list(),
            "gasto": arredondar(a["GASTO_ALUNO_R2025"], 0),
            "extremo": booleanos(a["GASTO_EXTREMO"]),
            "mat": arredondar(a["QT_MAT_FUND"], 0),
        },
    }


def dados_estaduais() -> dict:
    ufs = ler("dim_uf")
    p = ler("painel_estadual").sort("SG_UF", "ETAPA", "ANO")
    a = ler("gasto_estadual_anual").sort("SG_UF", "ANO")
    return {
        "ufs": {"uf": ufs["SG_UF"].to_list(), "nome": ufs["NM_UF"].to_list(), "regiao": ufs["NM_REGIAO"].to_list(),
                "pop": arredondar(ufs["POPULACAO_TOTAL_CENSO"], 0)},
        "linhas": {
            "uf": p["SG_UF"].to_list(),
            "etapa": p["ETAPA"].to_list(),
            "ano": p["ANO"].to_list(),
            "mt": arredondar(p["NOTA_MT"], 1),
            "lp": arredondar(p["NOTA_LP"], 1),
            "n": arredondar(p["NOTA_N"], 2),
            "ideb": arredondar(p["IDEB"], 1),
            **{f"gA{k}": arredondar(p[f"GASTO_ALUNO_A_R2025_L{k}"], 0) for k in (0, 1, 2, 4)},
            **{f"gB{k}": arredondar(p[f"GASTO_ALUNO_B_R2025_L{k}"], 0) for k in (0, 1, 2, 4)},
            "supAusente": booleanos(p["SUP364_AUSENTE"]),
            "mat": arredondar(p["QT_MAT_BAS"], 0),
        },
        "anual": {
            "uf": a["SG_UF"].to_list(),
            "ano": a["ANO"].to_list(),
            "gastoA": arredondar(a["GASTO_ALUNO_A_R2025"], 0),
            "gastoB": arredondar(a["GASTO_ALUNO_B_R2025"], 0),
            "supAusente": booleanos(a["SUP364_AUSENTE"]),
            "mat": arredondar(a["QT_MAT_BAS"], 0),
        },
    }


def dados_malha() -> dict:
    """Caminhos SVG dos municípios, na mesma ordem da dimensão (índice m); None se faltar polígono."""
    malha = json.loads((PROCESSED_DIR / "malha_municipios.json").read_text(encoding="utf-8"))
    cods = ler("dim_municipio").sort("CO_MUNICIPIO")["CO_MUNICIPIO"].to_list()
    return {"caminhos": [malha["municipios"].get(c) for c in cods], "bboxBrasil": malha["bbox_brasil"], "bboxUF": malha["bbox_uf"]}


def commit_atual() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconhecido"


if __name__ == "__main__":
    dados = {
        "meta": {"gerado_em": date.today().isoformat(), "commit": commit_atual()},
        "mun": dados_municipais(),
        "est": dados_estaduais(),
        "malha": dados_malha(),
    }
    # "</" escapado para o JSON não fechar a tag <script> por acidente
    carga = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DADOS__", carga)
    DESTINO.write_text(html, encoding="utf-8")
    print(f"[OK] {DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB)")
    print(f"[INFO] {len(dados['mun']['municipios']['cod'])} municípios, {len(dados['mun']['linhas']['m'])} linhas "
          f"municipais, {len(dados['mun']['anual']['m'])} município-anos de gasto, {len(dados['est']['linhas']['uf'])} "
          f"linhas estaduais")
