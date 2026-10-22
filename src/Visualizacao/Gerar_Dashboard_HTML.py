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


def arredondar(serie: pl.Series, casas: int) -> list:
    return [None if v is None else round(v, casas) for v in serie.to_list()]


def dados_municipais() -> dict:
    """Painel municipal em formato colunar, com os nomes guardados uma vez por município."""
    p = pl.read_parquet(PROCESSED_DIR / "painel_municipal.parquet")
    municipios = (
        p.select("CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF", "NM_REGIAO").unique("CO_MUNICIPIO").sort("CO_MUNICIPIO")
        .with_row_index("IDX")
    )
    p = p.join(municipios.select("CO_MUNICIPIO", "IDX"), on="CO_MUNICIPIO").sort("IDX", "ETAPA", "ANO")
    return {
        "municipios": {
            "cod": municipios["CO_MUNICIPIO"].to_list(),
            "nome": municipios["NO_MUNICIPIO"].to_list(),
            "uf": municipios["SG_UF"].to_list(),
            "regiao": municipios["NM_REGIAO"].to_list(),
        },
        "linhas": {
            "m": p["IDX"].to_list(),
            "etapa": p["ETAPA"].to_list(),
            "ano": p["ANO"].to_list(),
            "mt": arredondar(p["NOTA_MT"], 1),
            "lp": arredondar(p["NOTA_LP"], 1),
            "ideb": arredondar(p["IDEB"], 1),
            "gasto": arredondar(p["GASTO_ALUNO_R2025_L0"], 0),
            "extremo": [bool(v) for v in p["GASTO_EXTREMO_L0"].fill_null(False).to_list()],
            "mat": arredondar(p["QT_MAT_FUND"], 0),
        },
    }


def dados_estaduais() -> dict:
    p = pl.read_parquet(PROCESSED_DIR / "painel_estadual.parquet").sort("SG_UF", "ETAPA", "ANO")
    return {
        "uf": p["SG_UF"].to_list(),
        "regiao": p["NM_REGIAO"].to_list(),
        "etapa": p["ETAPA"].to_list(),
        "ano": p["ANO"].to_list(),
        "mt": arredondar(p["NOTA_MT"], 1),
        "lp": arredondar(p["NOTA_LP"], 1),
        "ideb": arredondar(p["IDEB"], 1),
        "gastoA": arredondar(p["GASTO_ALUNO_A_R2025_L0"], 0),
        "gastoB": arredondar(p["GASTO_ALUNO_B_R2025_L0"], 0),
        "supAusente": [bool(v) for v in p["SUP364_AUSENTE"].fill_null(False).to_list()],
        "mat": arredondar(p["QT_MAT_BAS"], 0),
    }


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
    }
    # "</" escapado para o JSON não fechar a tag <script> por acidente
    carga = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DADOS__", carga)
    DESTINO.write_text(html, encoding="utf-8")
    print(f"[OK] {DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB)")
    print(f"[INFO] {len(dados['mun']['municipios']['cod'])} municípios, "
          f"{len(dados['mun']['linhas']['m'])} linhas municipais, {len(dados['est']['uf'])} linhas estaduais")
