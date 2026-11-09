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
    q = {"queryState": projecoes(papeis, ativo=tipo not in ("tableEx", "pivotTable", "shapeMap"))}
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


def segmentacao(ref: str, rotulo: str, padrao: list | None = None, unica: bool = True,
                grupo: str | None = None, busca: bool = False) -> dict:
    """Lista suspensa; o rótulo vai no cabeçalho da própria segmentação (sem título de contêiner).
    grupo: nome do grupo de sincronização (a mesma escolha vale em todas as páginas do grupo).
    busca: caixa de pesquisa na lista (para listas longas, como a de municípios)."""
    tabela, col = ref.split(".", 1)
    objetos = {"data": [{"properties": {"mode": literal("Dropdown")}}],
               "selection": [{"properties": {"strictSingleSelect": literal(unica), "selectAllCheckboxEnabled": literal(not unica)}}],
               # sobre a faixa azul: cabeçalho azul-claro e caixa de seleção branca
               "header": [{"properties": {"show": literal(True), "fontColor": cor(AZUL_CLARO), "textSize": literal(9.0)}}],
               "items": [{"properties": {"textSize": literal(10.0), "fontColor": cor(AZUL_FAIXA), "background": cor(FUNDO_CARTAO)}}]}
    geral = {}
    if padrao:
        geral["filter"] = {"filter": filtro_in(tabela, col, padrao)}
    if busca:
        geral["selfFilterEnabled"] = literal(True)
    if geral:
        objetos["general"] = [{"properties": geral}]
    v = {"visualType": "slicer", "query": {"queryState": projecoes({"Values": [(ref, rotulo)]})},
         "objects": objetos, "drillFilterOtherVisuals": True}
    if grupo:
        v["syncGroup"] = {"groupName": grupo, "fieldChanges": True, "filterChanges": True}
    return v


def com_padding(visual: dict, vertical: float = 2.0, horizontal: float = 8.0) -> dict:
    """Espaço interno pequeno: o cartão do Power BI reserva tanto espaço acima e abaixo que cortava o rótulo."""
    visual.setdefault("visualContainerObjects", {})["padding"] = [{"properties": {
        "top": literal(vertical), "bottom": literal(vertical), "left": literal(horizontal), "right": literal(horizontal)}}]
    return visual


def quadro_texto(paragrafos: list[tuple[str, dict]]) -> dict:
    """Caixa de texto em cartão (Como ler, Como usar), com margem interna para o texto não encostar na borda."""
    return com_padding(texto(paragrafos), vertical=12.0, horizontal=16.0)


def cartao(medida_nome: str, rotulo: str, tamanho: float = 18.0) -> dict:
    # labelDisplayUnits 1 = sem abreviação ("R$ 12.000", e não "R$ 12 Mil")
    return com_padding(grafico("card", {"Values": [(medida_nome, rotulo)]}, objetos={
        "labels": [{"properties": {"fontSize": literal(tamanho), "color": cor(AZUL_FAIXA), "labelDisplayUnits": literal(1.0)}}],
        "categoryLabels": [{"properties": {"show": literal(True), "fontSize": literal(9.0), "color": cor(COR_TEXTO_2)}}]}))


def cartao_texto(medida_nome: str) -> dict:
    """Cartão para medida de texto longo: fonte pequena, com quebra de linha e sem rótulo."""
    return com_padding(grafico("card", {"Values": [medida_nome]}, objetos={
        "labels": [{"properties": {"fontSize": literal(10.0), "color": cor(COR_TEXTO_2)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}],
        "wordWrap": [{"properties": {"show": literal(True)}}]}))


MALHA = BASE_DIR / "data" / "processed" / "malha_municipios.topojson"
RECURSO_MALHA = "malha_municipios.topojson"  # trocado no início da execução pelo nome registrado no relatório


def registrar_malha(raiz: Path) -> str:
    """Garante a malha TopoJSON como recurso do relatório (tipo ShapeMap) e copia a versão atual do pipeline.
    Reaproveita o nome que o Desktop deu ao recurso, se já existir. Devolve o nome do recurso."""
    rel = raiz / "definition" / "report.json"
    rep = json.loads(rel.read_text(encoding="utf-8"))
    pacotes = rep.setdefault("resourcePackages", [])
    reg = next((p for p in pacotes if p.get("type") == "RegisteredResources"), None)
    if reg is None:
        reg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        pacotes.append(reg)
    item = next((i for i in reg["items"] if i.get("type") == "ShapeMap"), None)
    if item is None:
        item = {"name": "malha_municipios.topojson", "path": "malha_municipios.topojson", "type": "ShapeMap"}
        reg["items"].append(item)
        rel.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destino = raiz / "StaticResources" / "RegisteredResources" / item["path"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MALHA, destino)
    return item["name"]


LIMITE_COR_MAPA = 30  # pontos: ±30 cobre 88% a 94% das redes em 2023 (p5 ≈ −25 a −30; p95 ≈ +26 a +35)


def mapa_formas(recurso: str, local: str, valor: tuple, dicas: list) -> dict:
    """Mapa de formas com a malha municipal (formato copiado do que o Desktop grava, 2026-11-05).
    Cor divergente com centro fixo em 0 e saturada em ±LIMITE_COR_MAPA pontos: vermelho abaixo, cinza perto de 0,
    azul acima do esperado. Sem os limites, a escala ia do mínimo ao máximo do país (−77 a +165) e quase todo o mapa
    ficava cinza-claro. Zoom: automático ao filtrar a UF, pela roda do mouse e ao selecionar."""
    ponto = lambda hexa, v: {"color": literal(hexa), "value": literal(float(v))}
    return grafico("shapeMap", {"Category": [local], "Value": [valor], "Tooltips": dicas}, objetos={
        "shape": [{"properties": {
            "datasourceType": literal("file_upload"),
            "map": {"geoJson": {"type": literal("packaged"), "name": literal("malha_municipios.topojson"),
                                "content": {"expr": {"ResourcePackageItem": {
                                    "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": recurso}}}}},
            "projectionEnum": literal("mercator")}}],
        "zoom": [{"properties": {"autoZoom": literal(True), "manualZoom": literal(True), "selectionZoom": literal(True)}}],
        "dataPoint": [{"properties": {"fillRule": {"linearGradient3": {
            "min": ponto(VERMELHO, -LIMITE_COR_MAPA), "mid": ponto(NEUTRO, 0), "max": ponto(AZUL, LIMITE_COR_MAPA),
            "nullColoringStrategy": {"strategy": literal("asZero")}}}}}]})


def linha_constante(objeto: str, valor: float, cor_hexa: str = COR_GRADE) -> dict:
    return {objeto: [{"properties": {"show": literal(True), "value": literal(float(valor)),
                                     "lineColor": cor(cor_hexa), "style": literal("dashed"), "transparency": literal(0.0)},
                      "selector": {"id": "1"}}]}


# ───────────────────────── páginas ─────────────────────────

def segmentacoes_padrao(prefixo: str) -> dict:
    """Segmentações disponíveis para a faixa: (campo, rótulo, seleção padrão, seleção única, filtros do visual,
    grupo de sincronização, caixa de busca, largura)."""
    return {
        "uf": ("dim_uf.SG_UF", "UF (vazio = Brasil)", None, False, None, "uf", False, 156),
        "municipio": ("dim_municipio.MUNICIPIO_UF", "Município (digite para buscar)", None, True, None, None, True, 252),
        # tabela sem relação com o modelo: escolher a referência não filtra a lista de pares
        "referencia": ("ref_municipio.REF_MUNICIPIO_UF", "Município de referência (busque)", None, True, None, None, True, 252),
        "etapa": ("dim_etapa.NOME_ETAPA", "Etapa", ["Anos Iniciais (5º ano)"], True,
                  [filtro_visual(f"{prefixo}_f_etapa", "dim_etapa", "ETAPA", ["AI", "AF"])], "etapa", False, 156),
        "disciplina": ("dim_disciplina.NOME_DISCIPLINA", "Disciplina", ["Matemática"], True, None, "disciplina", False, 156),
        "edicao": ("dim_ano.ANO", "Edição do Saeb", [2023], True,
                   [filtro_visual(f"{prefixo}_f_edicao", "dim_ano", "EDICAO_SAEB", [True])], "edicao", False, 156),
        "modelo": ("dim_modelo.ROTULO_MODELO", "Modelo de eficiência", ["Nacional, com IDHM (2017–2023)"], True, None,
                   "modelo", False, 156),
        # parâmetro sem relação com o modelo e sem sincronização: vale só na página Defasagens
        "defasagem": ("dim_defasagem.ROTULO_DEFASAGEM", "Gasto de quando", ["Mesmo ano"], True, None, None, False, 156),
    }


def cabecalho(prefixo: str, titulo: str, subtitulo: str, z0: int = 0,
              segs: tuple = ("uf", "etapa", "disciplina", "edicao", "modelo")) -> list[dict]:
    """Faixa azul com o nome do painel, o título da página e as segmentações escolhidas, alinhadas à direita.
    As segmentações comuns são sincronizadas entre as páginas (mesmo grupo = mesma escolha)."""
    estilo_nome = {"fontWeight": "bold", "fontSize": "8pt", "color": AZUL_MEDIO}
    estilo_tit = {"fontWeight": "bold", "fontSize": "16pt", "color": "#ffffff"}
    estilo_sub = {"fontSize": "9pt", "color": AZUL_CLARO}
    disponiveis = segmentacoes_padrao(prefixo)
    # a faixa é a própria caixa de texto do título, de ponta a ponta; as segmentações ficam por cima, à direita
    faixa = com_padding(texto([(NOME_PAINEL, estilo_nome), (titulo, estilo_tit), (subtitulo, estilo_sub)]),
                        vertical=2.0, horizontal=16.0)  # margem lateral; na vertical, mais que 2 px cortava o subtítulo
    vis = [container(f"{prefixo}_titulo", (0, 0, LARGURA, 72), faixa, z0, estilo="faixa")]
    x = LARGURA - 16 - sum(disponiveis[s][7] + 8 for s in segs) + 8
    for i, nome in enumerate(segs):
        ref, rot, padrao, unica, filtros, grupo, busca, largura = disponiveis[nome]
        vis.append(container(f"{prefixo}_seg_{nome}", (x, 8, largura, 56),
                             segmentacao(ref, rot, padrao, unica, grupo, busca), z0 + 1 + i, filtros, estilo="nenhum"))
        x += largura + 8
    return vis


def pagina(nome: str, titulo: str, sem_filtro: list[tuple[str, str]] | None = None) -> dict:
    """page.json com o fundo cinza-claro da identidade (também na área fora da tela).
    sem_filtro: pares (visual de origem, visual de destino) em que a origem NÃO filtra o destino."""
    p = {"$schema": ESQ_PAGINA, "name": nome, "displayName": titulo, "displayOption": "FitToPage",
         "height": ALTURA, "width": LARGURA,
         "objects": {"background": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}],
                     "outspace": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}]}}
    if sem_filtro:
        p["visualInteractions"] = [{"source": a, "target": b, "type": "NoFilter"} for a, b in sem_filtro]
    return p


def cartao_destaque(medida_nome: str, tamanho: float = 14.0) -> dict:
    """Cartão de texto em destaque (nome do município), sem rótulo."""
    return com_padding(grafico("card", {"Values": [medida_nome]}, objetos={
        "labels": [{"properties": {"fontSize": literal(tamanho), "color": cor(AZUL_FAIXA)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}]}))


def rodape_fontes(prefixo: str, z: int) -> dict:
    return container(f"{prefixo}_rodape", (16, 690, 1248, 24), texto([(
        "Fontes: SIOPE (gasto), Censo Escolar (matrículas e infraestrutura), Saeb/Inep (proficiência), IBGE e PNUD "
        "(contexto). Valores em R$ de 2025, corrigidos pelo IPCA. Resultados de associação, não de causalidade.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), z, estilo="nenhum")


# grade da página (1280 × 720): faixa 0–72, cartões 80–164, gráficos 172–404, tabela 412–684, rodapé 690–714
def pagina_eficiencia() -> tuple[dict, list[dict]]:
    p = "efic"
    vis = cabecalho(p, "Quem entrega mais do que o esperado?",
                    "Pontos acima (+) ou abaixo (−) do esperado, dado o gasto e o contexto")
    cartoes = [("redes", "Redes com eficiência calculada", "Redes comparadas"),
               ("acima", "% acima do esperado", "Acima do esperado"),
               ("media", "Eficiência (pontos)", "Eficiência média (pontos)"),
               ("saltos", "Redes com salto atípico", "Redes com salto atípico")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_aviso", (672, 80, 592, 84), cartao_texto("Aviso do modelo"), 14))
    vis.append(container(
        f"{p}_dispersao", (16, 172, 760, 232),
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
        f"{p}_barras_uf", (788, 172, 476, 232),
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


def pagina_ficha() -> tuple[dict, list[dict]]:
    """Ficha de um município: série por edição contra cluster, UF e Brasil; gasto anual; eficiência por edição.
    O filtro de Edição vale só para os cartões (as séries mostram todas as edições)."""
    p = "fic"
    vis = cabecalho(p, "Ficha do município", "Um município ao longo das edições do Saeb",
                    segs=("municipio", "etapa", "disciplina", "edicao", "modelo"))
    vis.append(container(f"{p}_card_nome", (16, 80, 344, 44), cartao_destaque("Município selecionado"), 10))
    vis.append(container(f"{p}_card_perfil", (16, 124, 344, 40), cartao_texto("Perfil do município"), 11))
    cartoes = [("gasto", "Gasto por aluno (mediana anual)", "Gasto por aluno no ano"),
               ("prof", "Proficiência média", "Proficiência"),
               ("efic", "Eficiência (pontos)", "Eficiência (pontos)"),
               ("pct", "Percentil de eficiência", "Percentil")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (368 + i * 158, 80, 150, 84), cartao(m, rot), 12 + i))
    vis.append(container(f"{p}_card_faixa", (1000, 80, 264, 84), cartao_destaque("Faixa de eficiência", 12.0), 16))
    so_edicoes = lambda nome: [filtro_visual(f"{p}_f_{nome}", "dim_ano", "EDICAO_SAEB", [True])]
    eixo_ano = {"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}]}
    vis.append(container(
        f"{p}_linhas", (16, 172, 760, 232),
        grafico("lineChart",
                {"Category": [("dim_ano.ANO", "Edição")],
                 "Y": [("Proficiência média", "Município"), ("Proficiência mediana do cluster", "Mediana do cluster"),
                       ("Proficiência mediana da UF", "Mediana da UF"), ("Proficiência mediana do Brasil", "Mediana do Brasil")]},
                objetos={**eixo_ano, "legend": [{"properties": {"show": literal(True), "position": literal("Top")}}]}),
        20, so_edicoes("linhas"), titulo="Proficiência por edição: o município contra o cluster, a UF e o Brasil"))
    vis.append(container(
        f"{p}_gasto", (788, 172, 476, 232),
        grafico("clusteredColumnChart", {"Category": [("dim_ano.ANO", "Ano")], "Y": [("Gasto por aluno (mediana anual)", "Gasto por aluno")]},
                objetos={**eixo_ano, "labels": [{"properties": {"show": literal(True)}}],
                         "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}]}),
        21, titulo="Gasto por aluno por ano (R$ de 2025)"))
    vis.append(container(
        f"{p}_tabela", (16, 412, 760, 272),
        grafico("tableEx", {"Values": [("dim_ano.ANO", "Edição"), ("Proficiência média", "Proficiência"),
                                       ("Proficiência esperada", "Esperada"), ("Eficiência (pontos)", "Eficiência"),
                                       ("Percentil de eficiência", "Percentil"), ("Faixa de eficiência", "Faixa"),
                                       ("Marca de salto", "Salto")]},
                ordenar="dim_ano.ANO", decrescente=False,
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        22, so_edicoes("tabela"), titulo="Eficiência por edição"))
    titulo_ler = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    vis.append(container(f"{p}_como_ler", (788, 412, 476, 272), quadro_texto([
        ("Como ler esta ficha", titulo_ler),
        ("• Linhas: a proficiência do município em cada edição do Saeb, contra as medianas das redes do mesmo "
         "cluster (contexto parecido), da UF e do Brasil.", corpo),
        ("• Eficiência: pontos acima (+) ou abaixo (−) do que redes com gasto e contexto parecidos alcançaram. "
         "Percentil 80 = resultado melhor que o de 80% das redes.", corpo),
        ("• ⚠ salto: o resultado mudou demais desde a edição anterior. Conferir antes de tirar conclusões.", corpo),
        ("• O filtro de edição muda só os cartões; gráficos e tabela mostram todas as edições.", corpo),
        ("• O indicador descreve associação, não efeito do gasto: ele também capta gestão, contexto familiar e "
         "qualidade do registro.", corpo),
    ]), 23))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_edicao", f"{p}_{alvo}") for alvo in ("linhas", "gasto", "tabela")]
    return pagina("tcc_ficha", "Ficha do município", sem_filtro), vis


def pagina_pares() -> tuple[dict, list[dict]]:
    """Pares: redes do mesmo cluster do município de referência, com gasto entre 0,8 e 1,25 vez o dele,
    ordenadas pela eficiência. As colunas são medidas 'Par: ...', vazias fora dos pares (a linha some sozinha)."""
    p = "par"
    vis = cabecalho(p, "Pares: com quem conversar", "Redes de contexto e gasto parecidos, ordenadas pela eficiência",
                    segs=("referencia", "etapa", "disciplina", "edicao", "modelo"))
    vis.append(container(f"{p}_card_nome", (16, 80, 344, 44), cartao_destaque("Município de referência"), 10))
    vis.append(container(f"{p}_card_regra", (16, 124, 344, 40), cartao_texto("Regra dos pares"), 11))
    cartoes = [("gasto", "Gasto do município de referência", "Gasto por aluno"),
               ("prof", "Proficiência do município de referência", "Proficiência"),
               ("efic", "Eficiência do município de referência", "Eficiência (pontos)"),
               ("pares", "Pares encontrados", "Pares encontrados"),
               ("acima", "Pares que entregam mais", "Pares que entregam mais")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (368 + i * 180, 80, 172, 84), cartao(m, rot), 12 + i))
    vis.append(container(
        f"{p}_tabela", (16, 172, 860, 512),
        grafico("tableEx", {"Values": [("dim_municipio.MUNICIPIO_UF", "Município"),
                                       ("Par: gasto por aluno", "Gasto por aluno"), ("Par: proficiência", "Proficiência"),
                                       ("Par: eficiência", "Eficiência"),
                                       ("Par: diferença para a referência", "Diferença para a referência"),
                                       ("Par: percentil", "Percentil"), ("Par: salto", "Salto")]},
                ordenar="Par: eficiência",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        20, titulo="Pares do município de referência, do mais ao menos eficiente"))
    titulo_ler = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    vis.append(container(f"{p}_como_usar", (884, 172, 380, 512), quadro_texto([
        ("Como usar", titulo_ler),
        ("1. Escolha o município de referência no filtro da faixa (digite o nome).", corpo),
        ("2. A tabela lista as redes do mesmo cluster (contexto parecido) que gastam entre 0,8 e 1,25 vez o "
         "gasto por aluno da referência na edição escolhida.", corpo),
        ("3. No topo da tabela ficam as redes que mais entregam acima do esperado com gasto semelhante: são as "
         "candidatas a uma conversa sobre práticas de gestão.", corpo),
        ("4. Diferença para a referência: quantos pontos de eficiência o par tem a mais (+) ou a menos (−) que o "
         "município escolhido.", corpo),
        ("Cuidados", titulo_ler),
        ("• ⚠ salto: o resultado do par mudou demais desde a edição anterior. Conferir antes de tomá-lo como exemplo.", corpo),
        ("• Pares parecidos em contexto e gasto não são iguais em tudo: a eficiência descreve associação e também "
         "capta gestão, contexto familiar e qualidade do registro.", corpo),
        ("• A edição de 2025 só tem eficiência no modelo de robustez.", corpo),
    ]), 21))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_pares", "Pares"), vis


def pagina_inicio() -> tuple[dict, list[dict]]:
    """Porta de entrada: números do recorte, séries de proficiência e gasto (recorte × Brasil), guia das perguntas
    e navegador de páginas. O filtro de Edição vale só para os cartões."""
    p = "ini"
    vis = cabecalho(p, "Gasto e aprendizado nas redes municipais", "Visão geral do recorte escolhido nos filtros")
    cartoes = [("gasto", "Gasto por aluno (mediana anual)", "Gasto por aluno (mediana)"),
               ("prof", "Proficiência média", "Proficiência média"),
               ("acima", "% acima do esperado", "Redes acima do esperado"),
               ("redes", "Redes avaliadas", "Redes com nota no Saeb"),
               ("cobertura", "Cobertura do Saeb", "Cobertura do Saeb")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 251, 80, 242, 84), cartao(m, rot), 10 + i))
    titulo_ler = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    vis.append(container(f"{p}_guia", (16, 172, 400, 400), quadro_texto([
        ("O que este painel responde", titulo_ler),
        ("1. Gastar mais por aluno se associa a aprender mais? Veja os números e as séries desta página e a "
         "dispersão da página Eficiência.", corpo),
        ("2. Minha rede entrega o que se espera para o seu gasto e o seu contexto? Veja a Ficha do município.", corpo),
        ("3. Com quem conversar? A página Pares lista redes parecidas que entregam mais com gasto semelhante.", corpo),
        ("Como ler", titulo_ler),
        ("• Proficiência: pontos do Saeb, na escala de cada etapa (não compare etapas nem disciplinas).", corpo),
        ("• Gasto por aluno: Ensino Fundamental da rede municipal, em R$ de 2025.", corpo),
        ("• Eficiência: pontos acima (+) ou abaixo (−) do esperado para redes com gasto e contexto parecidos.", corpo),
        ("• Os filtros da faixa (UF vazia = Brasil) valem em todas as páginas.", corpo),
    ]), 20))
    # no Desktop, botões e navegadores só respondem com Ctrl + clique; no modo de leitura e publicado, clique simples
    vis.append(container(f"{p}_navegador", (16, 580, 400, 104),
                         com_padding({"visualType": "pageNavigator", "drillFilterOtherVisuals": True}, vertical=6.0, horizontal=12.0),
                         21, titulo="Ir para (no Power BI Desktop: Ctrl + clique)"))
    so_edicoes = [filtro_visual(f"{p}_f_linhas_prof", "dim_ano", "EDICAO_SAEB", [True])]
    eixo_ano = {"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}],
                "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                "legend": [{"properties": {"show": literal(True), "position": literal("Top")}}]}
    vis.append(container(
        f"{p}_linhas_prof", (424, 172, 840, 252),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Edição")],
                              "Y": [("Proficiência média", "Recorte escolhido"), ("Proficiência média do Brasil", "Brasil")]},
                objetos=eixo_ano),
        22, so_edicoes, titulo="Proficiência média por edição do Saeb: recorte escolhido × Brasil"))
    vis.append(container(
        f"{p}_linhas_gasto", (424, 432, 840, 252),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Ano")],
                              "Y": [("Gasto por aluno (mediana anual)", "Recorte escolhido"),
                                    ("Gasto por aluno do Brasil (mediana anual)", "Brasil")]},
                objetos=eixo_ano),
        23, titulo="Gasto por aluno por ano (mediana, R$ de 2025): recorte escolhido × Brasil"))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_edicao", f"{p}_{alvo}") for alvo in ("linhas_prof", "linhas_gasto")]
    return pagina("tcc_inicio", "Início", sem_filtro), vis


def pagina_mapa() -> tuple[dict, list[dict]]:
    """Mapa da eficiência por município, com resumo por UF ao lado.
    O Mapa de formas desenha no máximo ~1.500 áreas: o mapa municipal completo pede uma UF escolhida
    (decisão de 2026-11-05); a visão nacional fica no Resumo por UF."""
    p = "map"
    vis = cabecalho(p, "Mapa da eficiência", "Onde as redes entregam mais ou menos do que o esperado")
    cartoes = [("redes", "Redes com eficiência calculada", "Redes comparadas"),
               ("acima", "% acima do esperado", "Acima do esperado"),
               ("media", "Eficiência (pontos)", "Eficiência média (pontos)"),
               ("saltos", "Redes com salto atípico", "Redes com salto atípico")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_aviso", (672, 80, 592, 84), cartao_texto("Aviso do modelo"), 14))
    # mapa mais largo (924 px) e tabela mais estreita: os municípios ficavam pequenos demais
    vis.append(container(f"{p}_aviso_mapa", (16, 172, 924, 40), cartao_texto("Aviso do mapa"), 19))
    vis.append(container(
        f"{p}_mapa", (16, 220, 924, 464),
        mapa_formas(RECURSO_MALHA, "dim_municipio.CO_MUNICIPIO", ("Eficiência (pontos)", "Eficiência (pontos)"),
                    [("Município selecionado", "Município"), ("Proficiência média", "Proficiência"),
                     ("Gasto das redes avaliadas (mediana)", "Gasto por aluno")]),
        20, titulo="Eficiência por município (pontos acima ou abaixo do esperado)"))
    vis.append(container(
        f"{p}_tabela_uf", (948, 172, 316, 512),
        grafico("tableEx", {"Values": [("dim_uf.SG_UF", "UF"), ("% acima do esperado", "Acima"),
                                       ("Eficiência (pontos)", "Eficiência"),
                                       ("Redes com eficiência calculada", "Redes")]},
                ordenar="% acima do esperado",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        21, titulo="Resumo por UF"))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_mapa", "Mapa"), vis


def pagina_defasagens() -> tuple[dict, list[dict]]:
    """Associação gasto × proficiência (ρ de Spearman) por edição e defasagem do gasto.
    As segmentações de edição e de defasagem valem para os cartões e a dispersão; o gráfico de colunas e a matriz
    mostram todas as edições e defasagens (a defasagem é a própria série/coluna, sem relação com o modelo)."""
    p = "def"
    vis = cabecalho(p, "Gastar mais se associa a notas maiores?",
                    "Correlação entre o gasto por aluno e a proficiência, com o gasto do mesmo ano ou de anos antes",
                    segs=("uf", "etapa", "disciplina", "edicao", "defasagem"))
    cartoes = [("rho", "Correlação gasto × proficiência (Spearman)", "ρ de Spearman"),
               ("redes", "Redes na correlação", "Redes na correlação"),
               ("gasto", "Gasto das redes avaliadas (mediana)", "Gasto por aluno (mediana)"),
               ("prof", "Proficiência média", "Proficiência média")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_leitura", (672, 80, 592, 84), cartao_texto("Leitura da correlação"), 14))
    so_edicoes = lambda nome: [filtro_visual(f"{p}_f_{nome}", "dim_ano", "EDICAO_SAEB", [True])]
    rho = "Correlação gasto × proficiência (Spearman)"
    vis.append(container(
        f"{p}_colunas", (16, 172, 760, 232),
        grafico("clusteredColumnChart",
                {"Category": [("dim_ano.ANO", "Edição")], "Series": [("dim_defasagem.ROTULO_DEFASAGEM", "Gasto de quando")],
                 "Y": [(rho, "ρ de Spearman")]},
                ordenar="dim_ano.ANO", decrescente=False,
                objetos={"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}],
                         "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Top")}}],
                         "labels": [{"properties": {"show": literal(True), "fontSize": literal(8.0)}}]}),
        20, so_edicoes("colunas"), titulo="ρ de Spearman por edição, com o gasto do mesmo ano ou de 1, 2 e 4 anos antes"))
    vis.append(container(
        f"{p}_dispersao", (788, 172, 476, 232),
        grafico("scatterChart",
                {"Category": [("dim_municipio.MUNICIPIO_UF", "Município")],
                 "X": [("Gasto das redes avaliadas (mediana)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Proficiência média", "Proficiência")]},
                objetos={"categoryAxis": [{"properties": {"logAxisScale": literal(True)}}]}),
        21, titulo="Cada ponto é uma rede (edição e defasagem escolhidas)"))
    vis.append(container(
        f"{p}_matriz", (16, 412, 760, 272),
        grafico("pivotTable",
                {"Rows": [("dim_ano.ANO", "Edição")], "Columns": [("dim_defasagem.ROTULO_DEFASAGEM", "Gasto de quando")],
                 "Values": [(rho, "ρ"), ("Redes na correlação", "Redes")]},
                # sem totais: o ρ de várias edições juntas misturaria anos diferentes
                objetos={"subTotals": [{"properties": {"rowSubtotals": literal(False), "columnSubtotals": literal(False)}}]}),
        22, so_edicoes("matriz"), titulo="ρ e número de redes por edição e defasagem (vazio = sem gasto daquele ano)"))
    titulo_ler = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    vis.append(container(f"{p}_como_ler", (788, 412, 476, 272), quadro_texto([
        ("Como ler", titulo_ler),
        ("• ρ de Spearman (−1 a 1): compara a ordem das redes no gasto com a ordem na nota. 0 = sem relação; "
         "perto de 1 = quem gasta mais quase sempre tem nota maior. Só com 30 redes ou mais.", corpo),
        ("• Defasagem: gasto do mesmo ano da prova ou de 1, 2 ou 4 anos antes, porque o aluno acumula anos de escola. "
         "A série de gasto começa em 2017: 2017 só tem o mesmo ano, e 4 anos antes só a partir de 2021.", corpo),
        ("• No Brasil, parte da associação vem das diferenças entre estados (os que gastam mais também têm notas "
         "maiores). Escolha uma UF para comparar redes do mesmo estado: a correlação costuma cair muito.", corpo),
        ("• Associação não é efeito do gasto: contexto, gestão e qualidade do registro também entram.", corpo),
    ]), 23))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_{seg}", f"{p}_{alvo}") for seg in ("edicao", "defasagem") for alvo in ("colunas", "matriz")]
    return pagina("tcc_defasagens", "Defasagens", sem_filtro), vis


PORTES = ["Até 5 mil", "5 a 10 mil", "10 a 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Mais de 500 mil"]


def pagina_contexto() -> tuple[dict, list[dict]]:
    """Perfil dos 7 clusters de contexto (A6) com gasto, nota e eficiência de cada um; gasto e nota por porte;
    dispersão gasto × proficiência colorida por cluster. O perfil (colunas de dim_cluster) é nacional e fixo;
    as medidas seguem os filtros da faixa."""
    p = "ctx"
    vis = cabecalho(p, "Contexto e clusters", "Grupos de municípios com contexto parecido, usados para comparar pares")
    vis.append(container(
        f"{p}_perfil", (16, 80, 1248, 220),
        grafico("tableEx", {"Values": [
            ("dim_cluster.CLUSTER_ROTULO", "Cluster"), ("dim_cluster.MUNICIPIOS", "Municípios"),
            ("dim_cluster.POP_MEDIANA", "População mediana"), ("dim_cluster.ALFAB_MEDIA", "Alfabetização"),
            ("dim_cluster.IDHM_RENDA_MEDIO", "IDHM Renda"), ("dim_cluster.IDHM_LONGEVIDADE_MEDIO", "IDHM Longev."),
            ("dim_cluster.INFRA_MEDIA", "Infraestrutura"), ("dim_cluster.REGIAO_PREDOMINANTE", "Região principal"),
            ("dim_cluster.PARCELA_REGIAO_PREDOMINANTE", "% na região"),
            ("Redes avaliadas", "Redes com nota"), ("Gasto das redes avaliadas (mediana)", "Gasto (mediana)"),
            ("Proficiência mediana", "Proficiência (mediana)"), ("% acima do esperado", "Acima do esperado")]},
            ordenar="dim_cluster.CLUSTER_ROTULO", decrescente=False,
            objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        10, titulo="Perfil dos 7 clusters (contexto nacional e fixo) e resultados no recorte escolhido"))
    vis.append(container(
        f"{p}_dispersao", (16, 308, 620, 332),
        grafico("scatterChart",
                {"Category": [("dim_municipio.MUNICIPIO_UF", "Município")], "Series": [("dim_municipio.CLUSTER_ROTULO", "Cluster")],
                 "X": [("Gasto das redes avaliadas (mediana)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Proficiência média", "Proficiência")]},
                objetos={"categoryAxis": [{"properties": {"logAxisScale": literal(True)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Bottom"), "fontSize": literal(8.0)}}]}),
        20, titulo="Gasto por aluno × proficiência, por cluster (cada ponto é uma rede)"))
    so_portes = lambda nome: [filtro_visual(f"{p}_f_{nome}", "dim_municipio", "PORTE", PORTES)]
    barras = lambda medida_nome, rotulo: grafico(
        "clusteredBarChart", {"Category": [("dim_municipio.PORTE", "Porte")], "Y": [(medida_nome, rotulo)]},
        ordenar="dim_municipio.PORTE", decrescente=False,
        objetos={"labels": [{"properties": {"show": literal(True), "fontSize": literal(8.0)}}],
                 "categoryAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                 "valueAxis": [{"properties": {"showAxisTitle": literal(False), "show": literal(False)}}]})
    vis.append(container(f"{p}_porte_gasto", (644, 308, 306, 332),
                         barras("Gasto das redes avaliadas (mediana)", "Gasto (mediana)"),
                         21, so_portes("porte_gasto"), titulo="Gasto por aluno (mediana), por porte"))
    vis.append(container(f"{p}_porte_prof", (958, 308, 306, 332),
                         barras("Proficiência mediana", "Proficiência (mediana)"),
                         22, so_portes("porte_prof"), titulo="Proficiência (mediana), por porte"))
    vis.append(container(f"{p}_nota", (16, 646, 1248, 40), texto([(
        "Clusters: k-médias com população, alfabetização, IDHM Renda e Longevidade da UF e infraestrutura das escolas, sem "
        "gasto nem nota. A separação entre os grupos é fraca (silhueta ≈ 0,23): são uma partição útil para formar pares, não "
        "tipos naturais, e saem ligados à região porque o IDHM só existe por UF. Porte = população do Censo 2022.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), 29, estilo="nenhum"))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_contexto", "Contexto e clusters"), vis


PAGINAS = [pagina_inicio, pagina_eficiencia, pagina_ficha, pagina_pares, pagina_mapa, pagina_defasagens, pagina_contexto]


# ───────────────────────── gravação e validação ─────────────────────────

PASTA_ESQUEMAS = BASE_DIR / "data" / "interim" / "esquemas_pbir"
RAW_ESQUEMAS = "https://raw.githubusercontent.com/microsoft/json-schemas/main/fabric/item/report/definition"


def baixar_esquemas(pasta: Path) -> None:
    """Baixa do repositório público da Microsoft os esquemas usados (visual, página, lista de páginas) e todos os
    que eles referenciam, espelhando os caminhos. Só roda quando a pasta ainda não tem esquemas."""
    import requests
    from urllib.parse import urljoin
    fila = [ESQ_VISUAL, ESQ_PAGINA, ESQ_PAGINAS]
    vistos = set()
    while fila:
        url = fila.pop()
        if url in vistos:
            continue
        vistos.add(url)
        resp = requests.get(url.replace(ESQ, RAW_ESQUEMAS), timeout=60)
        resp.raise_for_status()
        json.loads(resp.text)  # garante que é JSON antes de gravar
        destino = pasta / url.replace(ESQ + "/", "")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(resp.text, encoding="utf-8")
        fila += [urljoin(url, ref) for ref in re.findall(r'"\$ref"\s*:\s*"([^"#]+)', resp.text)]
    print(f"[INFO] {len(vistos)} esquemas baixados para {pasta}")


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
    ap.add_argument("--validar", type=Path, nargs="?", const=PASTA_ESQUEMAS,
                    help="confere os JSON contra os esquemas oficiais (baixados para data/interim/esquemas_pbir "
                         "na primeira vez, ou lidos da pasta indicada)")
    ap.add_argument("--pasta", type=Path, help="outra pasta .Report (para testes)")
    args = ap.parse_args()
    raiz = (args.pasta or RELATORIO).resolve()
    paginas_dir = raiz / "definition" / "pages"
    if not (paginas_dir / "pages.json").exists():
        sys.exit(f"[ERRO] Não achei {paginas_dir / 'pages.json'}: o projeto .pbip foi criado (roteiro, Fase 1)?")
    validar = None
    if args.validar:
        if not any(args.validar.rglob("*.json")):
            baixar_esquemas(args.validar)
        validar = validador(args.validar)

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

    RECURSO_MALHA = registrar_malha(raiz)  # malha do mapa como recurso do relatório, na versão atual do pipeline

    # toda medida usada nos visuais precisa existir em powerbi/medidas.dax (pega nome digitado errado)
    from Gerar_Modelo_PowerBI import ler_medidas
    existentes = {m["nome"] for m in ler_medidas()}
    usadas = {m.group(1) for montar in PAGINAS for v in montar()[1]
              for m in re.finditer(r'"Measure": \{"Expression": \{"SourceRef": \{"Entity": "_Medidas"\}\}, "Property": "([^"]+)"',
                                   json.dumps(v, ensure_ascii=False))}
    if usadas - existentes:
        sys.exit(f"[ERRO] Medidas usadas nos visuais e ausentes de medidas.dax: {', '.join(sorted(usadas - existentes))}")

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
