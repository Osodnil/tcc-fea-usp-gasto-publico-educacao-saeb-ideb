"""Simplifica a Malha Municipal do IBGE (2025) para o mapa do dashboard.

Lê data/raw/Malha Municipal/BR_Municipios_2025.shp (320 MB, 20 milhões de pontos) e grava
data/processed/malha_municipios.json com um caminho SVG por município (~1 MB).
Passos: projeção equiretangular (longitude × cos 15°), encaixe dos vértices numa grade fina
(fronteiras compartilhadas encaixam no mesmo ponto) e Douglas-Peucker em cada anel.
"""
import json
import math
from pathlib import Path

import numpy as np
import polars as pl
import shapefile


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
SHP = BASE_DIR / "data" / "raw" / "Malha Municipal" / "BR_Municipios_2025.shp"
DESTINO = BASE_DIR / "data" / "processed" / "malha_municipios.json"

PASSO = 0.005            # grade de encaixe, em graus (~550 m); é a unidade das coordenadas gravadas
TOLERANCIA = 3           # Douglas-Peucker, em unidades da grade (~1,6 km)
FATOR_X = math.cos(math.radians(15))  # corrige a largura na latitude média do Brasil


def douglas_peucker(p: np.ndarray, tol: float) -> np.ndarray:
    """Simplifica uma linha aberta; mantém o primeiro e o último ponto."""
    if len(p) < 3:
        return p
    manter = np.zeros(len(p), dtype=bool)
    manter[[0, -1]] = True
    pilha = [(0, len(p) - 1)]
    while pilha:
        a, b = pilha.pop()
        if b - a < 2:
            continue
        seg = p[b] - p[a]
        meio = p[a + 1:b] - p[a]
        norma = math.hypot(*seg)
        d = np.abs(seg[0] * meio[:, 1] - seg[1] * meio[:, 0]) / norma if norma else np.hypot(meio[:, 0], meio[:, 1])
        i = int(np.argmax(d))
        if d[i] > tol:
            k = a + 1 + i
            manter[k] = True
            pilha += [(a, k), (k, b)]
    return p[manter]


def simplificar_anel(pontos: np.ndarray) -> np.ndarray | None:
    q = np.round(np.c_[pontos[:, 0] * FATOR_X, -pontos[:, 1]] / PASSO).astype(np.int64)
    q = q[np.r_[True, np.any(q[1:] != q[:-1], axis=1)]]
    if len(q) < 4:
        return None
    # anel fechado: divide no ponto mais distante do início para o Douglas-Peucker não colapsar
    j = int(np.argmax(np.hypot(*(q - q[0]).T)))
    s = np.vstack([douglas_peucker(q[:j + 1].astype(float), TOLERANCIA)[:-1], douglas_peucker(q[j:].astype(float), TOLERANCIA)])
    s = np.round(s).astype(np.int64)
    return s if len(s) >= 4 else q[[0, len(q) // 3, 2 * len(q) // 3, -1]]


def caminho(aneis: list[np.ndarray]) -> str:
    """Caminho SVG com coordenadas relativas (inteiras), o formato mais compacto."""
    partes = []
    for a in aneis:
        d = np.diff(a[:-1], axis=0)
        partes.append(f"M{a[0, 0]} {a[0, 1]}l" + " ".join(f"{x} {y}" for x, y in d) + "z")
    return "".join(partes)


if __name__ == "__main__":
    validos = set(pl.read_parquet(BASE_DIR / "data/processed/dim_municipio.parquet")["CO_MUNICIPIO"].to_list())
    r = shapefile.Reader(str(SHP))
    malha, bbox, fora, pontos = {}, {}, [], 0
    for sr in r.iterShapeRecords(fields=["CD_MUN", "SIGLA_UF"]):
        cod, uf = sr.record["CD_MUN"], sr.record["SIGLA_UF"]
        if cod not in validos:
            fora.append(cod)  # áreas operacionais de lagoas no RS, que não são municípios
            continue
        pts = np.asarray(sr.shape.points)
        partes = list(sr.shape.parts) + [len(pts)]
        aneis = [a for a in (simplificar_anel(pts[i:j]) for i, j in zip(partes[:-1], partes[1:])) if a is not None]
        if not aneis:
            continue
        malha[cod] = caminho(aneis)
        pontos += sum(len(a) for a in aneis)
        xy = np.vstack(aneis)
        b = bbox.setdefault(uf, [math.inf, math.inf, -math.inf, -math.inf])
        bbox[uf] = [min(b[0], xy[:, 0].min()), min(b[1], xy[:, 1].min()), max(b[2], xy[:, 0].max()), max(b[3], xy[:, 1].max())]

    todos = np.array(list(bbox.values()))
    saida = {"passo_graus": PASSO, "fonte": "IBGE, Malha Municipal 2025",
             "bbox_brasil": [int(todos[:, 0].min()), int(todos[:, 1].min()), int(todos[:, 2].max()), int(todos[:, 3].max())],
             "bbox_uf": {uf: [int(v) for v in b] for uf, b in bbox.items()}, "municipios": malha}
    DESTINO.write_text(json.dumps(saida, separators=(",", ":")), encoding="utf-8")
    sem_malha = sorted(validos - set(malha))
    print(f"[OK] {DESTINO.name}: {len(malha)} municípios, {pontos:,} pontos, {DESTINO.stat().st_size / 1e6:.2f} MB".replace(",", "."))
    print(f"[INFO] Polígonos fora da dimensão de municípios (descartados): {fora}")
    print(f"[INFO] Municípios da dimensão sem polígono: {sem_malha}")
