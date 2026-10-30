"""Escreve as páginas do dashboard oficial no projeto Power BI (formato PBIR, um JSON por página e por visual).

Cada página é descrita de forma declarativa em PAGINAS (posição, tipo de visual e campos); o script grava
powerbi/tcc_gasto_saeb.Report/definition/pages/<pagina>/page.json e visuals/<visual>/visual.json, e põe as
páginas na ordem de PAGINAS em pages.json.

Regras:
- Feche o Power BI antes de rodar (o Desktop sobrescreveria os arquivos ao salvar).
- Uma página já existente não é tocada, porque pode ter sido ajustada no Desktop; para refazê-la, use
  --refazer <pagina>. A página em branco criada pelo Desktop ("Página 1") é removida se não tiver visuais.
- Com --validar <pasta>, confere cada JSON contra os esquemas oficiais da Microsoft baixados nessa pasta.
  O esquema garante a estrutura; os nomes dos papéis (X, Y, Values...) seguem a convenção do Power BI.

As medidas usadas precisam existir no modelo (Gerar_Modelo_PowerBI.py --adicionar-medidas).
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")


BASE_DIR = encontrar_raiz_projeto()
RELATORIO = BASE_DIR / "powerbi" / "tcc_gasto_saeb.Report"
ESQ = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
ESQ_VISUAL = f"{ESQ}/visualContainer/2.13.0/schema.json"
ESQ_PAGINA = f"{ESQ}/page/2.1.0/schema.json"
ESQ_PAGINAS = f"{ESQ}/pagesMetadata/1.1.0/schema.json"
MEDIDAS = "_Medidas"
LARGURA, ALTURA = 1280, 720

# cores do tema (powerbi/tema_tcc.json)
COR_TEXTO_2, COR_GRADE, VERMELHO, NEUTRO, AZUL = "#52514e", "#c3c2b7", "#b52a2a", "#f0efec", "#184f95"
# identidade visual (Henrique, 2026-10-30): faixa azul institucional, cartões brancos sobre fundo cinza-claro
NOME_PAINEL = "PAINEL DE EFICIÊNCIA EDUCACIONAL"
AZUL_FAIXA, AZUL_CLARO, AZUL_MEDIO = "#0d366b", "#cde2fb", "#9ec5f4"
FUNDO_PAGINA, FUNDO_CARTAO, BORDA_CARTAO = "#f4f5f7", "#ffffff", "#e3e4e0"


# ───────────────────────── campos e expressões ─────────────────────────

def coluna(tabela: str, col: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": col}}


def medida(nome: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": MEDIDAS}}, "Property": nome}}


def campo(ref: str) -> dict:
    """'tabela.COLUNA' é coluna; qualquer outro texto é medida de _Medidas."""
    if re.fullmatch(r"(dim|fato|ref)_\w+\.\w+", ref):
        return coluna(*ref.split(".", 1))
    return medida(ref)


def query_ref(ref: str) -> str:
    return ref if re.fullmatch(r"(dim|fato|ref)_\w+\.\w+", ref) else f"{MEDIDAS}.{ref}"


def literal(valor) -> dict:
    if isinstance(valor, bool):
        v = "true" if valor else "false"
    elif isinstance(valor, int):
        v = f"{valor}L"
    elif isinstance(valor, float):
        v = f"{valor}D"
    else:
        v = "'" + str(valor).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": v}}}


def cor(hexa: str) -> dict:
    return {"solid": {"color": literal(hexa)}}


def filtro_in(tabela: str, col: str, valores: list) -> dict:
    """Definição de filtro 'col IN (valores)', no formato de consulta do Power BI."""
    return {
        "Version": 2,
        "From": [{"Name": "t", "Entity": tabela, "Type": 0}],
        "Where": [{"Condition": {"In": {
            "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}],
            "Values": [[{"Literal": literal(v)["expr"]["Literal"]}] for v in valores],
        }}}],
    }


def filtro_visual(nome: str, tabela: str, col: str, valores: list) -> dict:
    return {"name": nome, "field": coluna(tabela, col), "type": "Categorical",
            "filter": filtro_in(tabela, col, valores), "howCreated": "User", "isHiddenInViewMode": True}


# ───────────────────────── visuais ─────────────────────────

def estilo_container(estilo: str) -> dict:
    """'cartao': branco, cantos arredondados e sombra leve; 'faixa': azul, sem borda; 'nenhum': transparente."""
    if estilo == "cartao":
        return {"background": [{"properties": {"show": literal(True), "color": cor(FUNDO_CARTAO), "transparency": literal(0.0)}}],
                "border": [{"properties": {"show": literal(True), "color": cor(BORDA_CARTAO), "radius": literal(8.0)}}],
                "dropShadow": [{"properties": {"show": literal(True), "color": cor("#000000"), "transparency": literal(90.0)}}]}
    if estilo == "faixa":
        return {"background": [{"properties": {"show": literal(True), "color": cor(AZUL_FAIXA), "transparency": literal(0.0)}}],
                "border": [{"properties": {"show": literal(False)}}],
                "dropShadow": [{"properties": {"show": literal(False)}}]}
    return {"background": [{"properties": {"show": literal(False)}}],
            "border": [{"properties": {"show": literal(False)}}],
            "dropShadow": [{"properties": {"show": literal(False)}}]}


def container(nome: str, pos: tuple, visual: dict, z: int, filtros: list | None = None, titulo: str | None = None,
              estilo: str = "cartao") -> dict:
    x, y, w, h = pos
    objs = visual.setdefault("visualContainerObjects", {})
    objs.update(estilo_container(estilo))
    if titulo is not None:
        objs["title"] = [{"properties": {"show": literal(True), "text": literal(titulo), "fontSize": literal(11.0),
                                         "fontColor": cor(AZUL_FAIXA), "bold": literal(True)}}]
        # sem o subtítulo automático ("Medida por Coluna") que o Power BI acrescenta
        objs["subTitle"] = [{"properties": {"show": literal(False)}}]
    c = {"$schema": ESQ_VISUAL, "name": nome,
         "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}, "visual": visual}
    if filtros:
        c["filterConfig"] = {"filters": filtros}
    return c


def projecoes(papeis: dict, ativo: bool = True) -> dict:
    """Cada campo é 'ref' ou ('ref', 'Rótulo exibido no visual').
    ativo: marca 'active' nas colunas, como o Desktop grava em gráficos e segmentações. Na tabela (tableEx)
    o Desktop não marca, e a marca quebra a renderização ("reading 'isMeasure'", 2026-10-30)."""
    saida = {}
    for papel, refs in papeis.items():
        projs = []
        for r in refs:
            ref, rotulo = r if isinstance(r, tuple) else (r, None)
            p = {"field": campo(ref), "queryRef": query_ref(ref), "nativeQueryRef": ref.split(".")[-1]}
            if ativo and "Column" in p["field"]:
                p["active"] = True
            if rotulo:
                p["displayName"] = rotulo
            projs.append(p)
        saida[papel] = {"projections": projs}
    return saida


def grafico(tipo: str, papeis: dict, ordenar: str | None = None, decrescente: bool = True, objetos: dict | None = None) -> dict:
    q = {"queryState": projecoes(papeis, ativo=tipo not in ("tableEx", "pivotTable"))}
    if ordenar:
        q["sortDefinition"] = {"sort": [{"field": campo(ordenar), "direction": "Descending" if decrescente else "Ascending"}],
                               "isDefaultSort": False}
    v = {"visualType": tipo, "query": q, "drillFilterOtherVisuals": True}
    if objetos:
        v["objects"] = objetos
    return v


def texto(paragrafos: list[tuple[str, dict]]) -> dict:
    """paragrafos: [(texto, estilo)], estilo como {'fontWeight': 'bold', 'fontSize': '16pt', 'color': '#...'}"""
    return {"visualType": "textbox", "drillFilterOtherVisuals": True, "objects": {"general": [{"properties": {
        "paragraphs": [{"textRuns": [{"value": t, "textStyle": est}]} for t, est in paragrafos]}}]}}


def segmentacao(ref: str, rotulo: str, padrao: list | None = None, unica: bool = True) -> dict:
    """Lista suspensa; o rótulo vai no cabeçalho da própria segmentação (sem título de contêiner)."""
    tabela, col = ref.split(".", 1)
    objetos = {"data": [{"properties": {"mode": literal("Dropdown")}}],
               "selection": [{"properties": {"strictSingleSelect": literal(unica), "selectAllCheckboxEnabled": literal(not unica)}}],
               # sobre a faixa azul: cabeçalho azul-claro e caixa de seleção branca
               "header": [{"properties": {"show": literal(True), "fontColor": cor(AZUL_CLARO), "textSize": literal(9.0)}}],
               "items": [{"properties": {"textSize": literal(10.0), "fontColor": cor(AZUL_FAIXA), "background": cor(FUNDO_CARTAO)}}]}
    if padrao:
        objetos["general"] = [{"properties": {"filter": {"filter": filtro_in(tabela, col, padrao)}}}]
    return {"visualType": "slicer", "query": {"queryState": projecoes({"Values": [(ref, rotulo)]})},
            "objects": objetos, "drillFilterOtherVisuals": True}


def cartao(medida_nome: str, rotulo: str, tamanho: float = 18.0) -> dict:
    return grafico("card", {"Values": [(medida_nome, rotulo)]}, objetos={
        "labels": [{"properties": {"fontSize": literal(tamanho), "color": cor(AZUL_FAIXA)}}],
        "categoryLabels": [{"properties": {"show": literal(True), "fontSize": literal(9.0), "color": cor(COR_TEXTO_2)}}]})


def cartao_texto(medida_nome: str) -> dict:
    """Cartão para medida de texto longo: fonte pequena, com quebra de linha e sem rótulo."""
    return grafico("card", {"Values": [medida_nome]}, objetos={
        "labels": [{"properties": {"fontSize": literal(10.0), "color": cor(COR_TEXTO_2)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}],
        "wordWrap": [{"properties": {"show": literal(True)}}]})


def linha_constante(objeto: str, valor: float, cor_hexa: str = COR_GRADE) -> dict:
    return {objeto: [{"properties": {"show": literal(True), "value": literal(float(valor)),
                                     "lineColor": cor(cor_hexa), "style": literal("dashed"), "transparency": literal(0.0)},
                      "selector": {"id": "1"}}]}


# ───────────────────────── páginas ─────────────────────────

def cabecalho(prefixo: str, titulo: str, subtitulo: str, z0: int = 0) -> list[dict]:
    """Faixa azul com o nome do painel, o título da página e as cinco segmentações comuns às páginas municipais."""
    estilo_nome = {"fontWeight": "bold", "fontSize": "8pt", "color": AZUL_MEDIO}
    estilo_tit = {"fontWeight": "bold", "fontSize": "16pt", "color": "#ffffff"}
    estilo_sub = {"fontSize": "9pt", "color": AZUL_CLARO}
    seg = [
        ("uf", "dim_uf.SG_UF", "UF (vazio = Brasil)", None, False, None),
        ("etapa", "dim_etapa.NOME_ETAPA", "Etapa", ["Anos Iniciais (5º ano)"], True,
         [filtro_visual(f"{prefixo}_f_etapa", "dim_etapa", "ETAPA", ["AI", "AF"])]),
        ("disciplina", "dim_disciplina.NOME_DISCIPLINA", "Disciplina", ["Matemática"], True, None),
        ("edicao", "dim_ano.ANO", "Edição do Saeb", [2023], True,
         [filtro_visual(f"{prefixo}_f_edicao", "dim_ano", "EDICAO_SAEB", [True])]),
        ("modelo", "dim_modelo.ROTULO_MODELO", "Modelo de eficiência", ["Nacional, com IDHM (2017–2023)"], True, None),
    ]
    # a faixa é a própria caixa de texto do título, de ponta a ponta; as segmentações ficam por cima, à direita
    vis = [container(f"{prefixo}_titulo", (0, 0, LARGURA, 72),
                     texto([(NOME_PAINEL, estilo_nome), (titulo, estilo_tit), (subtitulo, estilo_sub)]), z0, estilo="faixa")]
    for i, (nome, ref, rot, padrao, unica, filtros) in enumerate(seg):
        vis.append(container(f"{prefixo}_seg_{nome}", (456 + i * 164, 8, 156, 56), segmentacao(ref, rot, padrao, unica),
                             z0 + 1 + i, filtros, estilo="nenhum"))
    return vis


def pagina(nome: str, titulo: str) -> dict:
    """page.json com o fundo cinza-claro da identidade (também na área fora da tela)."""
    return {"$schema": ESQ_PAGINA, "name": nome, "displayName": titulo, "displayOption": "FitToPage",
            "height": ALTURA, "width": LARGURA,
            "objects": {"background": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}],
                        "outspace": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}]}}


# grade da página (1280 × 720): faixa 0–72, cartões 80–152, gráficos 160–404, tabela 412–684, rodapé 690–714
def pagina_eficiencia() -> tuple[dict, list[dict]]:
    p = "efic"
    vis = cabecalho(p, "Quem entrega mais do que o esperado?",
                    "Pontos acima (+) ou abaixo (−) do esperado, dado o gasto e o contexto")
    cartoes = [("redes", "Redes com eficiência calculada", "Redes comparadas"),
               ("acima", "% acima do esperado", "Acima do esperado"),
               ("media", "Eficiência (pontos)", "Eficiência média (pontos)"),
               ("saltos", "Redes com salto atípico", "Redes com salto atípico")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 72), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_aviso", (672, 80, 592, 72), cartao_texto("Aviso do modelo"), 14))
    vis.append(container(
        f"{p}_dispersao", (16, 160, 760, 244),
        grafico("scatterChart",
                {"Category": [("dim_municipio.MUNICIPIO_UF", "Município")], "Series": [("dim_municipio.CLUSTER_ROTULO", "Cluster")],
                 "X": [("Gasto das redes avaliadas (mediana)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Eficiência (pontos)", "Eficiência (pontos)")]},
                # propriedade copiada do que o Desktop grava ao ligar a escala logarítmica
                objetos={"categoryAxis": [{"properties": {"logAxisScale": literal(True)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Right"), "fontSize": literal(8.0)}}],
                         **linha_constante("y1AxisReferenceLine", 0)}),
        20, titulo="Gasto por aluno × eficiência: há redes acima e abaixo do esperado em todo nível de gasto"))
    vis.append(container(
        f"{p}_barras_uf", (788, 160, 476, 244),
        grafico("clusteredBarChart", {"Category": [("dim_uf.SG_UF", "UF")], "Y": [("% acima do esperado", "Acima do esperado")]},
                ordenar="% acima do esperado",
                objetos={"labels": [{"properties": {"show": literal(True)}}],
                         "categoryAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                         "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                         **linha_constante("y1AxisReferenceLine", 0.5)}),
        21, titulo="% das redes acima do esperado, por UF (linha = metade)"))
    vis.append(container(
        f"{p}_ranking", (16, 412, 1248, 272),
        grafico("tableEx", {"Values": [("dim_municipio.MUNICIPIO_UF", "Município"), ("dim_municipio.CLUSTER_ROTULO", "Cluster"),
                                       ("Gasto das redes avaliadas (mediana)", "Gasto por aluno"),
                                       ("Proficiência média", "Proficiência"), ("Proficiência esperada", "Esperada"),
                                       ("Eficiência (pontos)", "Eficiência"), ("Percentil de eficiência", "Percentil"),
                                       ("Marca de salto", "Salto")]},
                ordenar="Eficiência (pontos)",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        22, titulo="Ranking de eficiência (clique no cabeçalho para reordenar)"))
    vis.append(container(f"{p}_rodape", (16, 690, 1248, 24), texto([(
        "Eficiência = pontos acima (+) ou abaixo (−) do que redes com gasto e contexto parecidos alcançaram. "
        "Indica associação, não efeito do gasto. ⚠ salto = variação atípica desde a edição anterior: conferir antes de interpretar.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), 30, estilo="nenhum"))
    return pagina("tcc_eficiencia", "Eficiência"), vis


PAGINAS = [pagina_eficiencia]


# ───────────────────────── gravação e validação ─────────────────────────

def validador(pasta: Path):
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource
    recursos = []
    for arq in pasta.rglob("*.json"):
        s = json.loads(arq.read_text(encoding="utf-8"))
        # cada esquema fica registrado pelo endereço do arquivo (é assim que os outros o referenciam)
        # e pelo $id, que nos esquemas "embedded" é diferente do endereço
        url = f"{ESQ}/{arq.relative_to(pasta).as_posix()}"
        recursos.append((url, Resource.from_contents(s)))
        if s.get("$id") and s["$id"] != url:
            recursos.append((s["$id"], Resource.from_contents(s)))
    registro = Registry().with_resources(recursos)
    cache = {}

    def validar(doc: dict) -> list[str]:
        url = doc["$schema"]
        if url not in cache:
            cache[url] = Draft7Validator(registro[url].contents, registry=registro)
        return [f"{'/'.join(map(str, e.absolute_path))}: {e.message[:200]}" for e in cache[url].iter_errors(doc)]
    return validar


def gravar(caminho: Path, doc: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refazer", nargs="*", default=[], help="páginas a refazer (apaga e grava de novo)")
    ap.add_argument("--validar", type=Path, help="pasta com os esquemas PBIR baixados")
    ap.add_argument("--pasta", type=Path, help="outra pasta .Report (para testes)")
    args = ap.parse_args()
    raiz = (args.pasta or RELATORIO).resolve()
    paginas_dir = raiz / "definition" / "pages"
    if not (paginas_dir / "pages.json").exists():
        sys.exit(f"[ERRO] Não achei {paginas_dir / 'pages.json'}: o projeto .pbip foi criado (roteiro, Fase 1)?")
    validar = validador(args.validar) if args.validar else None

    meta = json.loads((paginas_dir / "pages.json").read_text(encoding="utf-8"))
    ordem = list(meta.get("pageOrder", []))
    # página vazia (sem visuais) criada no Desktop: sai se for a "Página 1" ou se tiver o nome de uma página gerada
    nomes_gerados = {"Página 1"} | {m()[0]["displayName"] for m in PAGINAS}
    for nome in list(ordem):
        pasta = paginas_dir / nome
        pj = pasta / "page.json"
        if (pj.exists() and not (pasta / "visuals").exists() and not nome.startswith("tcc_")
                and json.loads(pj.read_text(encoding="utf-8")).get("displayName") in nomes_gerados):
            shutil.rmtree(pasta)
            ordem.remove(nome)
            print(f"[INFO] Página em branco removida: {nome}")

    erros, gravadas = [], []
    for montar in PAGINAS:
        pag, visuais = montar()
        nome = pag["name"]
        pasta = paginas_dir / nome
        if pasta.exists() and nome not in args.refazer:
            print(f"[INFO] {nome} já existe; mantida (use --refazer {nome} para gravar de novo)")
            continue
        docs = [(pasta / "page.json", pag)] + [(pasta / "visuals" / v["name"] / "visual.json", v) for v in visuais]
        if validar:
            for caminho, doc in docs:
                erros += [f"{caminho.relative_to(paginas_dir)} → {e}" for e in validar(doc)]
        if erros:
            continue
        shutil.rmtree(pasta, ignore_errors=True)
        for caminho, doc in docs:
            gravar(caminho, doc)
        gravadas.append(f"{pag['displayName']} ({len(visuais)} visuais)")
        if nome not in ordem:
            ordem.append(nome)
    if erros:
        sys.exit("[ERRO] Arquivos fora do esquema (nada foi gravado para essas páginas):\n  " + "\n  ".join(erros))

    meta["pageOrder"] = [n for n in [m()[0]["name"] for m in PAGINAS] if n in ordem] + \
                        [n for n in ordem if n not in [m()[0]["name"] for m in PAGINAS]]
    meta["activePageName"] = meta["pageOrder"][0]
    meta["$schema"] = meta.get("$schema", ESQ_PAGINAS)
    if validar:
        problemas = validar(meta)
        if problemas:
            sys.exit("[ERRO] pages.json fora do esquema: " + "; ".join(problemas))
    gravar(paginas_dir / "pages.json", meta)
    print(f"[OK] Páginas gravadas: {', '.join(gravadas) if gravadas else 'nenhuma'}"
          f"{' | validadas contra os esquemas oficiais' if validar else ''}")
    print(f"     Ordem: {', '.join(meta['pageOrder'])}")
