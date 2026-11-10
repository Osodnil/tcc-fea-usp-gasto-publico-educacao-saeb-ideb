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
    if re.fullmatch(r"(dim|fato|ref|cmp)_\w+\.\w+", ref):
        return coluna(*ref.split(".", 1))
    return medida(ref)


def query_ref(ref: str) -> str:
    return ref if re.fullmatch(r"(dim|fato|ref|cmp)_\w+\.\w+", ref) else f"{MEDIDAS}.{ref}"


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


def texto_misto(paragrafos: list[list[tuple[str, dict]]]) -> dict:
    """Caixa de texto em que cada parágrafo tem vários trechos de estilos diferentes (número, título, corpo)."""
    return {"visualType": "textbox", "drillFilterOtherVisuals": True, "objects": {"general": [{"properties": {
        "paragraphs": [{"textRuns": [{"value": t, "textStyle": est} for t, est in trechos]} for trechos in paragrafos]}}]}}


def glossario(termos: list[tuple[str, str]], nota: str | None = None, titulo: str | None = "Como ler",
              vertical: float = 10.0) -> dict:
    """Quadro "Como ler" em forma de glossário: termo em negrito + definição, um por linha (todas as colunas da tabela).
    Padrão visual escolhido por Henrique em 2026-11-09 a partir da Ficha; titulo=None para quadros pequenos."""
    tit = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    termo = {"fontWeight": "bold", "fontSize": "9pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    pars = ([[(titulo, tit)]] if titulo else []) + [[(f"{t}: ", termo), (d, corpo)] for t, d in termos]
    if nota:
        pars.append([(nota, {"fontSize": "9pt", "color": COR_TEXTO_2, "fontStyle": "italic"})])
    return com_padding(texto_misto(pars), vertical=vertical, horizontal=14.0)


def segmentacao(ref: str, rotulo: str, padrao: list | None = None, unica: bool = True,
                grupo: str | None = None, busca: bool = False, sobre_cartao: bool = False,
                permite_vazio: bool = False) -> dict:
    """Lista suspensa; o rótulo vai no cabeçalho da própria segmentação (sem título de contêiner).
    grupo: nome do grupo de sincronização (a mesma escolha vale em todas as páginas do grupo).
    busca: caixa de pesquisa na lista (para listas longas, como a de municípios).
    permite_vazio: sem seleção única obrigatória (que sempre marca o primeiro item) e sem "Selecionar tudo";
    a medida lê SELECTEDVALUE, e o vazio tem significado (2026-11-09, "Comparar com" da página Pares)."""
    tabela, col = ref.split(".", 1)
    estrita, marcar_tudo = (False, False) if permite_vazio else (unica, not unica)
    objetos = {"data": [{"properties": {"mode": literal("Dropdown")}}],
               "selection": [{"properties": {"strictSingleSelect": literal(estrita), "selectAllCheckboxEnabled": literal(marcar_tudo)}}],
               # sobre a faixa azul: cabeçalho azul-claro e caixa de seleção branca
               # sobre_cartao: segmentação fora da faixa, em fundo branco (cabeçalho azul-escuro)
               "header": [{"properties": {"show": literal(True), "fontColor": cor(AZUL_FAIXA if sobre_cartao else AZUL_CLARO),
                                          "textSize": literal(9.0)}}],
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
    # o id de cada área passa a ser "Nome (UF)" (dim_municipio.MUNICIPIO_UF): o Mapa de formas mostra o campo de local
    # na dica do mouse, e com o código ela exibia "CO_MUNICIPIO 2304400" (pedido de 2026-11-09). Nomes são únicos.
    import polars as pl
    nomes = dict(pl.read_parquet(BASE_DIR / "data" / "processed" / "powerbi" / "dim_municipio.parquet",
                                 columns=["CO_MUNICIPIO", "MUNICIPIO_UF"]).iter_rows())
    malha = json.loads(MALHA.read_text(encoding="utf-8"))
    geometrias = next(iter(malha["objects"].values()))["geometries"]
    sem_nome = [g["id"] for g in geometrias if g["id"] not in nomes]
    if sem_nome:
        sys.exit(f"[ERRO] Áreas da malha sem município em dim_municipio: {sem_nome[:5]}")
    for g in geometrias:
        g["properties"]["CD_MUN"] = g["id"]
        g["id"] = nomes[g["id"]]
    destino.write_text(json.dumps(malha, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return item["name"]


LIMITE_COR_MAPA = 0.12  # % do esperado, comparação no mesmo estado: ±12% cobre 88% a 96% das redes em 2023 (2026-11-09)


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
        "uf": ("dim_uf.SG_UF", "UF (vazio = Brasil)", None, False, None, "uf", False, 136),
        "municipio": ("dim_municipio.MUNICIPIO_UF", "Município (digite para buscar)", None, True, None, None, True, 252),
        # tabela sem relação com o modelo: escolher a referência não filtra a lista de pares
        "referencia": ("ref_municipio.REF_MUNICIPIO_UF", "Município de referência (busque)", None, True, None, None, True, 252),
        "etapa": ("dim_etapa.NOME_ETAPA", "Etapa", ["Anos Iniciais (5º ano)"], True,
                  [filtro_visual(f"{prefixo}_f_etapa", "dim_etapa", "ETAPA", ["AI", "AF"])], "etapa", False, 192),
        "disciplina": ("dim_disciplina.NOME_DISCIPLINA", "Disciplina", ["Matemática"], True, None, "disciplina", False, 156),
        "edicao": ("dim_ano.ANO", "Edição do Saeb", [2023], True,
                   [filtro_visual(f"{prefixo}_f_edicao", "dim_ano", "EDICAO_SAEB", [True])], "edicao", False, 156),
        # rótulos revistos na reunião de 2026-11-06 ("dentro da UF" parecia filtrar a UF); mais largo para caber
        "modelo": ("dim_modelo.ROTULO_MODELO", "Comparação da eficiência", ["Nacional (até 2023)"], True, None,
                   "modelo", False, 196),
        # comparação própria do Mapa (sem sincronização), com padrão no mesmo estado (2026-11-09)
        "modelo_mapa": ("dim_modelo.ROTULO_MODELO", "Comparação do mapa", ["Mesmo estado (até 2025)"], True, None,
                        None, False, 196),
        # parâmetro sem relação com o modelo e sem sincronização: vale só na página Defasagens
        "defasagem": ("dim_defasagem.ROTULO_DEFASAGEM", "Gasto de quando", ["Mesmo ano"], True, None, None, False, 140),
        # camada estadual: só AF e EM; sem sincronização, porque nas páginas municipais EM não existe
        "etapa_est": ("dim_etapa.NOME_ETAPA", "Etapa (rede estadual)", ["Anos Finais (9º ano)"], True,
                      [filtro_visual(f"{prefixo}_f_etapa_est", "dim_etapa", "ETAPA", ["AF", "EM"])], None, False, 196),
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


def pagina(nome: str, titulo: str, sem_filtro: list[tuple[str, str]] | None = None, filtros: list | None = None) -> dict:
    """page.json com o fundo cinza-claro da identidade (também na área fora da tela).
    sem_filtro: pares (visual de origem, visual de destino) em que a origem NÃO filtra o destino.
    filtros: filtros da página inteira (ocultos), por exemplo a comparação fixa do Mapa."""
    p = {"$schema": ESQ_PAGINA, "name": nome, "displayName": titulo, "displayOption": "FitToPage",
         "height": ALTURA, "width": LARGURA,
         "objects": {"background": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}],
                     "outspace": [{"properties": {"color": cor(FUNDO_PAGINA), "transparency": literal(0.0)}}]}}
    if sem_filtro:
        p["visualInteractions"] = [{"source": a, "target": b, "type": "NoFilter"} for a, b in sem_filtro]
    if filtros:
        p["filterConfig"] = {"filters": filtros}
    return p


def cartao_destaque(medida_nome: str, tamanho: float = 14.0) -> dict:
    """Cartão de texto em destaque (nome do município), sem rótulo."""
    return com_padding(grafico("card", {"Values": [medida_nome]}, objetos={
        "labels": [{"properties": {"fontSize": literal(tamanho), "color": cor(AZUL_FAIXA)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}]}))


def rodape_fontes(prefixo: str, z: int) -> dict:
    # uma linha só: a versão longa quebrava em duas e a segunda ficava cortada (2026-11-09)
    return container(f"{prefixo}_rodape", (16, 690, 1248, 24), texto([(
        "Fontes: SIOPE, Censo Escolar, Saeb/Inep, IBGE e PNUD. Valores em R$ de 2025 (IPCA). "
        "Resultados de associação, não de causalidade. Detalhes na página Sobre os dados.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), z, estilo="nenhum")


# grade da página (1280 × 720): faixa 0–72, cartões 80–164, gráficos 172–404, tabela 412–684, rodapé 690–714
def pagina_eficiencia() -> tuple[dict, list[dict]]:
    p = "efic"
    vis = cabecalho(p, "Quem entrega acima do esperado?",
                    "Em % do esperado: acima (+) ou abaixo (−)")
    # "Eficiência média" em texto: "≈ 0" no Brasil inteiro, onde é zero por construção (2026-11-09); o aviso diz o porquê
    cartoes = [("redes", "Redes com eficiência calculada", "Redes comparadas"),
               ("acima", "% acima do esperado", "Acima do esperado"),
               ("media", "Eficiência média (cartão)", "Média vs. esperado"),
               ("saltos", "Redes com salto atípico", "Saltos atípicos")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_aviso", (672, 80, 592, 84), cartao_texto("Aviso da eficiência"), 14))
    vis.append(container(
        f"{p}_dispersao", (16, 172, 760, 232),
        grafico("scatterChart",
                {"Category": [("dim_municipio.MUNICIPIO_UF", "Município")], "Series": [("dim_municipio.CLUSTER_CURTO", "Cluster")],
                 "X": [("Gasto das redes avaliadas (mediana)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Eficiência (% do esperado)", "vs. esperado (%)")]},
                # propriedade copiada do que o Desktop grava ao ligar a escala logarítmica
                objetos={"categoryAxis": [{"properties": {"logAxisScale": literal(True)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Right"), "fontSize": literal(8.0)}}],  # rótulo curto do cluster (o completo era cortado)
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
        f"{p}_ranking", (16, 412, 792, 272),
        grafico("tableEx", {"Values": [("dim_municipio.MUNICIPIO_UF", "Município"), ("dim_municipio.CLUSTER_CURTO", "Cluster"),
                                       ("Gasto das redes avaliadas (mediana)", "Gasto por aluno"),
                                       ("Proficiência média", "Proficiência"), ("Proficiência esperada", "Esperada"),
                                       ("Eficiência (% do esperado)", "vs. esperado"), ("Eficiência (pontos)", "Pontos"),
                                       ("Percentil de eficiência", "Percentil"), ("Marca de salto", "Salto"),
                                       # decisão A9: parcela dos alunos públicos da etapa na rede municipal (⚠ < 50%)
                                       ("Marca de rede parcial", "Rede atende")]},
                ordenar="Eficiência (% do esperado)",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        22, titulo="Ranking de eficiência (clique no cabeçalho para reordenar)"))
    # glossário de todas as colunas do ranking (pedido de 2026-11-09: faltavam colunas no "Como ler")
    vis.append(container(f"{p}_como_ler", (816, 412, 448, 272), glossario([
        ("Cluster", "grupo de contexto parecido (cores do gráfico)."),
        ("Gasto por aluno", "Fundamental da rede municipal, em R$ de 2025."),
        ("Proficiência", "nota média da rede no Saeb, em pontos."),
        ("Esperada", "média de redes com gasto e contexto parecidos (regressão)."),
        ("vs. esperado", "nota acima (+) ou abaixo (−) da esperada, em %; 0% = igual a ela."),
        ("Pontos", "a mesma diferença, em pontos do Saeb."),
        ("Percentil", "posição entre as redes: 80 = melhor que 80% delas."),
        ("Salto", "⚠ = o resultado mudou demais desde a edição anterior: conferir."),
        ("Rede atende", "% dos alunos públicos da etapa na rede municipal (⚠ abaixo de 50%)."),
    ], "Gastar mais não garante eficiência (correlação de 0,01)."), 23))
    vis.append(container(f"{p}_rodape", (16, 690, 1248, 24), texto([(
        "Eficiência: associação, não efeito do gasto. A comparação nacional cobre 2017 a 2023; 2025 só na comparação "
        "com o mesmo estado.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), 30, estilo="nenhum"))
    return pagina("tcc_eficiencia", "Eficiência"), vis


def pagina_ficha() -> tuple[dict, list[dict]]:
    """Ficha de um município: série por edição contra cluster, UF e Brasil; gasto anual; eficiência por edição.
    O filtro de Edição vale só para os cartões (as séries mostram todas as edições)."""
    p = "fic"
    vis = cabecalho(p, "Ficha do município", "Um município ao longo das edições do Saeb",
                    segs=("municipio", "etapa", "disciplina", "edicao", "modelo"))
    vis.append(container(f"{p}_card_nome", (16, 80, 344, 34), cartao_destaque("Município selecionado", 13.0), 10))
    vis.append(container(f"{p}_card_perfil", (16, 114, 344, 50), cartao_texto("Perfil do município"), 11))  # duas linhas: o cluster era cortado
    cartoes = [("gasto", "Gasto por aluno (mediana anual)", "Gasto por aluno"),
               ("prof", "Proficiência média", "Proficiência"),
               ("efic", "Eficiência (% do esperado)", "vs. esperado"),
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
    # por que há ou não nota e eficiência (reunião de 2026-11-06)
    vis.append(container(f"{p}_situacao", (16, 412, 760, 56), cartao_texto("Situação da rede"), 24))
    vis.append(container(
        f"{p}_tabela", (16, 476, 760, 208),
        grafico("tableEx", {"Values": [("dim_ano.ANO", "Edição"), ("Proficiência média", "Proficiência"),
                                       ("Proficiência esperada", "Esperada"), ("Eficiência (% do esperado)", "vs. esperado"),
                                       ("Eficiência (pontos)", "Pontos"),
                                       ("Percentil de eficiência", "Percentil"), ("Faixa de eficiência", "Faixa"),
                                       ("Marca de salto", "Salto")]},
                ordenar="dim_ano.ANO", decrescente=False,
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        22, so_edicoes("tabela"), titulo="Eficiência por edição"))
    # glossário de todas as colunas da tabela e das linhas (pedido de 2026-11-09)
    vis.append(container(f"{p}_como_ler", (788, 412, 476, 272), glossario([
        ("Linhas", "o município por edição, contra as medianas do cluster, da UF e do Brasil."),
        ("Proficiência", "nota média da rede no Saeb, em pontos."),
        ("Esperada", "média de redes com gasto e contexto parecidos (modelo de regressão)."),
        ("vs. esperado", "acima (+) ou abaixo (−) da esperada, em %; 0% = igual a ela."),
        ("Pontos", "a mesma diferença, em pontos do Saeb."),
        ("Percentil", "80 = melhor que 80% das redes da mesma etapa, disciplina e edição."),
        ("Faixa", "o percentil em cinco grupos, de bem abaixo a bem acima."),
        ("Salto", "⚠ = mudou demais desde a edição anterior; não = sem salto."),
        ("2025", "eficiência só na comparação com o mesmo estado (sem IDHM de 2025)."),
    ], "O filtro de edição muda só os cartões. Associação, não efeito do gasto.", "Como ler esta ficha"), 23))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_edicao", f"{p}_{alvo}") for alvo in ("linhas", "gasto", "tabela")]
    return pagina("tcc_ficha", "Ficha do município", sem_filtro), vis


def pagina_pares() -> tuple[dict, list[dict]]:
    """Pares: redes do mesmo cluster do município de referência, com gasto entre 0,8 e 1,25 vez o dele,
    ordenadas pela eficiência. As colunas são medidas 'Par: ...', vazias fora dos pares (a linha some sozinha)."""
    p = "par"
    vis = cabecalho(p, "Com quem conversar", "Redes parecidas, ordenadas pela eficiência",
                    segs=("referencia", "etapa", "disciplina", "edicao", "modelo"))
    vis.append(container(f"{p}_card_nome", (16, 80, 344, 44), cartao_destaque("Município de referência"), 10))
    vis.append(container(f"{p}_card_regra", (16, 124, 344, 40), cartao_texto("Regra dos pares"), 11))
    cartoes = [("gasto", "Gasto do município de referência", "Gasto por aluno"),
               ("prof", "Proficiência do município de referência", "Proficiência"),
               ("efic", "Eficiência % do município de referência", "vs. esperado"),
               ("pares", "Pares encontrados", "Pares encontrados"),
               ("acima", "Pares que entregam mais", "Pares que entregam mais")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (368 + i * 180, 80, 172, 84), cartao(m, rot), 12 + i))
    vis.append(container(
        f"{p}_tabela", (16, 172, 744, 512),
        grafico("tableEx", {"Values": [("dim_municipio.MUNICIPIO_UF", "Município"),
                                       ("Par: gasto por aluno", "Gasto por aluno"), ("Par: proficiência", "Proficiência"),
                                       ("Par: eficiência (%)", "vs. esperado"),
                                       ("Par: diferença (p.p.)", "Diferença (p.p.)"),
                                       ("Par: percentil", "Percentil"), ("Par: salto", "Salto")]},
                ordenar="Par: eficiência (%)",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        20, titulo="Pares, do mais ao menos eficiente (clique num par para compará-lo ao lado)"))
    # comparação 1 a 1 (reunião de 2026-11-06): referência × município clicado na tabela ou escolhido em "Comparar com"
    vis.append(container(f"{p}_seg_comparar", (768, 172, 496, 56),
                         segmentacao("cmp_municipio.CMP_MUNICIPIO_UF", "Comparar com (opcional; vazio = par clicado)",
                                     busca=True, sobre_cartao=True, permite_vazio=True), 30))
    vis.append(container(f"{p}_cmp_ref", (768, 236, 244, 44), cartao_texto("Município de referência"), 31))
    vis.append(container(f"{p}_cmp_nome", (1020, 236, 244, 44), cartao_texto("Município comparado"), 32))
    linhas = [("gasto", "Gasto do município de referência", "Comparado: gasto por aluno", "Gasto por aluno"),
              ("prof", "Proficiência do município de referência", "Comparado: proficiência", "Proficiência"),
              ("esp", "Esperada do município de referência", "Comparado: esperada", "Proficiência esperada"),
              ("efic", "Eficiência % do município de referência", "Comparado: eficiência (%)", "vs. esperado"),
              ("pct", "Percentil do município de referência", "Comparado: percentil", "Percentil")]
    for i, (nome, m_ref, m_cmp, rot) in enumerate(linhas):
        y = 284 + i * 60
        vis.append(container(f"{p}_cmp_{nome}_r", (768, y, 244, 56), cartao(m_ref, rot, 14.0), 33 + 2 * i))
        vis.append(container(f"{p}_cmp_{nome}_c", (1020, y, 244, 56), cartao(m_cmp, rot, 14.0), 34 + 2 * i))
    vis.append(container(f"{p}_cmp_resumo", (768, 584, 496, 100), cartao_texto("Comparação 1 a 1"), 45))
    vis.append(container(f"{p}_rodape", (16, 690, 1248, 24), texto([(
        "Pares = mesmo cluster (e mesma UF, na comparação no mesmo estado) e gasto entre 0,8 e 1,25 vez o da referência. "
        "⚠ salto: conferir antes de usar como exemplo. Associação, não efeito do gasto.", {"fontSize": "9pt", "color": COR_TEXTO_2})]), 50, estilo="nenhum"))
    return pagina("tcc_pares", "Pares"), vis


def botao_pagina(rotulo: str, destino: str, tamanho: float = 11.0, fundo: str = AZUL_FAIXA,
                 cor_texto: str = "#ffffff", dica: str | None = None) -> dict:
    """Botão que leva a outra página (no Desktop, Ctrl + clique). A navegação fica em visualContainerObjects.visualLink
    (propriedades conferidas no esquema oficial); o estilo do botão segue o formato de botões do Power BI.
    dica: texto que aparece ao passar o mouse (propriedade tooltip do visualLink)."""
    padrao = {"id": "default"}
    link = {"show": literal(True), "type": literal("PageNavigation"), "navigationSection": literal(destino)}
    if dica:
        link["tooltip"] = literal(dica)
    return {
        "visualType": "actionButton", "drillFilterOtherVisuals": True,
        "objects": {
            "icon": [{"properties": {"show": literal(False)}, "selector": padrao}],
            # o Desktop grava duas entradas: o texto no estado "default" e um "show" sem estado, que é o que liga a
            # exibição; sem a segunda, o texto fica oculto (aprendido do Desktop em 2026-11-09)
            "text": [{"properties": {"show": literal(True), "text": literal(rotulo), "fontColor": cor(cor_texto),
                                     "fontSize": literal(tamanho), "bold": literal(True)}, "selector": padrao},
                     {"properties": {"show": literal(True)}}],
            "fill": [{"properties": {"show": literal(True), "fillColor": cor(fundo), "transparency": literal(0.0)},
                      "selector": padrao}],
            "outline": [{"properties": {"show": literal(False)}, "selector": padrao}],
        },
        "visualContainerObjects": {"visualLink": [{"properties": link}]},
    }


# páginas de destino da Boas-vindas: (nome interno, rótulo do botão, o que a página responde)
DESTINOS = [
    ("tcc_inicio", "Visão geral", "Números do recorte escolhido e séries de nota e gasto contra o Brasil."),
    ("tcc_eficiencia", "Eficiência", "Quem entrega mais ou menos do que o esperado para o seu gasto e contexto."),
    ("tcc_ficha", "Ficha do município", "Um município ao longo das edições, e o motivo quando falta nota."),
    ("tcc_pares", "Pares", "Redes parecidas com gasto semelhante; comparação de dois municípios, 1 a 1."),
    ("tcc_mapa", "Mapa", "A eficiência de cada município, numa UF escolhida."),
    ("tcc_defasagens", "Defasagens", "Gastar mais se associa a notas maiores? Com o gasto do ano ou de anos antes."),
    ("tcc_contexto", "Contexto e clusters", "Os 7 grupos de municípios de contexto parecido usados nas comparações."),
    ("tcc_estados", "Estados", "Redes estaduais (Anos Finais e Ensino Médio), em leitura descritiva."),
    ("tcc_sobre", "Sobre os dados", "Fontes, indicadores, limitações e autoria."),
]


# Boas-vindas: as três perguntas do painel, cada uma com a página que a responde (redesenho de 2026-11-09)
PERGUNTAS = [
    ("1", "Gastar mais se associa a aprender mais?",
     "Correlação entre gasto por aluno e nota, com o gasto do mesmo ano ou de até 4 anos antes, no Brasil e em cada UF.",
     "tcc_defasagens", "Defasagens"),
    ("2", "Minha rede entrega o esperado?",
     "Nota da rede contra a de redes com gasto e contexto parecidos. Também na Eficiência (ranking) e no Mapa.",
     "tcc_ficha", "Ficha do município"),
    ("3", "Com quem conversar?",
     "Redes do mesmo grupo de contexto, com gasto semelhante, que entregam mais. Compare duas redes, 1 a 1.",
     "tcc_pares", "Pares"),
]

# Como usar, em passos curtos: (número, título, texto)
PASSOS = [
    ("1", "Filtros", "Ficam na faixa azul, só os que mudam a página. UF vazia = Brasil. A mesma escolha vale em "
                     "todas as páginas que têm o filtro."),
    ("2", "Uma etapa por vez", "Escolha uma etapa e uma disciplina: notas de etapas ou disciplinas diferentes não se "
                               "comparam."),
    ("3", "Explore", "Passe o mouse para ver detalhes. Clique num ponto ou barra para filtrar; clique de novo para limpar."),
    ("4", "Comparação", "Nacional (padrão, edições de 2017 a 2023) ou com as redes do mesmo estado (inclui 2025)."),
    ("5", "Dados ausentes", "Vazio ou “–” = dado ausente, nunca zero. ⚠ salto = resultado que mudou demais: conferir."),
    ("6", "Botões", "No Power BI Desktop, Ctrl + clique. No relatório publicado, um clique basta."),
]


def pagina_boas_vindas() -> tuple[dict, list[dict]]:
    """Primeira página (reunião de 2026-11-06). Terceira versão (2026-11-09), escolhida por Henrique entre três arranjos:
    duas colunas, com pouca coisa na tela. À esquerda, para que serve e como usar; à direita, as três perguntas como
    botões grandes e as outras seis páginas como botões pequenos. A frase sobre cada página aparece ao passar o mouse."""
    p = "bv"
    vis = cabecalho(p, "Boas-vindas", "Como usar o painel e por onde começar", segs=())
    tit = {"fontWeight": "bold", "fontSize": "13pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "10pt", "color": COR_TEXTO_2}
    num = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_MEDIO}
    negrito = {"fontWeight": "bold", "fontSize": "10pt", "color": AZUL_FAIXA}
    vazio = [(" ", {"fontSize": "6pt"})]
    # coluna da esquerda: um único quadro, com respiro entre os passos
    paragrafos = [[("Para que serve", tit)],
                  [("Mostra quanto cada rede municipal gasta por aluno no Ensino Fundamental e quanto os alunos aprendem "
                    "no Saeb, e se a rede entrega mais ou menos do que redes parecidas, com gasto semelhante, alcançaram. "
                    "Feito para gestores e analistas da educação pública. Descreve associações, não efeitos do gasto.", corpo)],
                  vazio, [("Como usar", tit)]]
    for n, titulo_passo, texto_passo in PASSOS:
        paragrafos += [vazio, [(f"{n}   ", num), (f"{titulo_passo}. ", negrito), (texto_passo, corpo)]]
    vis.append(container(f"{p}_guia", (16, 88, 608, 596),
                         com_padding(texto_misto(paragrafos), vertical=20.0, horizontal=24.0), 10))
    # coluna da direita: as três perguntas (botão grande) e as outras páginas (botões pequenos, azul-claro)
    vis.append(container(f"{p}_perg_tit", (648, 88, 616, 36), texto([("Comece por uma pergunta", tit)]), 20,
                         estilo="nenhum"))
    for i, (n, pergunta, explica, destino, rotulo) in enumerate(PERGUNTAS):
        vis.append(container(f"{p}_q{n}", (648, 128 + i * 88, 616, 76),
                             botao_pagina(f"{pergunta}   →", destino, 14.0, dica=f"{explica} Abre a página {rotulo}."),
                             21 + i, estilo="nenhum"))
    vis.append(container(f"{p}_outras_tit", (648, 404, 616, 36), texto([("Outras páginas", tit)]), 30, estilo="nenhum"))
    outras = [d for d in DESTINOS if d[0] not in {q[3] for q in PERGUNTAS}]
    for i, (destino, rotulo, descricao) in enumerate(outras):
        x, y = 648 + (i % 2) * 316, 444 + (i // 2) * 56
        vis.append(container(f"{p}_bt_{i}", (x, y, 300, 44),
                             botao_pagina(rotulo, destino, 11.0, AZUL_CLARO, AZUL_FAIXA, dica=descricao), 31 + i, estilo="nenhum"))
    vis.append(container(f"{p}_dica", (648, 616, 616, 40), texto([(
        "Passe o mouse sobre um botão para ver o que a página mostra.", {"fontSize": "9pt", "color": COR_TEXTO_2})]),
        40, estilo="nenhum"))
    return pagina("tcc_boas_vindas", "Boas-vindas"), vis


def pagina_inicio() -> tuple[dict, list[dict]]:
    """Visão geral (antiga Início, renomeada em 2026-11-09): números do recorte, séries de proficiência e gasto
    (recorte × Brasil) e guia de leitura. O filtro de Edição vale só para os cartões. A navegação foi para a Boas-vindas."""
    p = "ini"
    # sem o filtro de comparação: só o cartão de % acima dependia dele (revisão de filtros, 2026-11-09)
    vis = cabecalho(p, "Visão geral", "Números e séries do recorte escolhido nos filtros",
                    segs=("uf", "etapa", "disciplina", "edicao"))
    cartoes = [("gasto", "Gasto por aluno (mediana anual)", "Gasto por aluno (mediana)"),
               ("prof", "Proficiência média", "Proficiência média"),
               ("acima", "% acima do esperado (padrão)", "Redes acima do esperado"),
               ("redes", "Redes avaliadas", "Redes com nota no Saeb"),
               ("cobertura", "Cobertura do Saeb", "Cobertura do Saeb")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 251, 80, 242, 84), cartao(m, rot), 10 + i))
    # glossário no padrão da Ficha (2026-11-09); a navegação está na Boas-vindas
    vis.append(container(f"{p}_guia", (16, 172, 400, 512), glossario([
        ("Cartões", "os números do recorte escolhido na faixa (UF, etapa, disciplina e edição)."),
        ("Linhas", "a proficiência por edição e o gasto por ano do recorte, contra o Brasil."),
        ("Gasto por aluno", "Ensino Fundamental da rede municipal, mediana entre as redes, em R$ de 2025 (IPCA)."),
        ("Proficiência", "nota média das redes no Saeb, em pontos. Não compare etapas nem disciplinas."),
        ("Acima do esperado", "% das redes acima de redes parecidas (comparação nacional; 2025: no mesmo estado)."),
        ("Redes com nota", "redes municipais com nota divulgada pelo Inep na etapa e edição."),
        ("Cobertura", "redes com nota ÷ municípios do recorte."),
        ("Melhoraram", "% das redes com nota mais alta que na edição anterior (2021: pandemia)."),
        ("R$ de 2025", "todo valor em reais do painel está corrigido pelo IPCA (detalhes em Sobre os dados)."),
        ("Edição", "o filtro vale só para os cartões; os gráficos mostram todas as edições."),
        ("Próximos passos", "minha rede entrega o esperado? Ficha do município. Com quem conversar? Pares. "
                            "Gastar mais se associa a aprender mais? Defasagens."),
    ], "Valores de associação: melhorar não prova bom uso do gasto.", "Como ler esta página"), 20))
    so_edicoes = lambda nome: [filtro_visual(f"{p}_f_{nome}", "dim_ano", "EDICAO_SAEB", [True])]
    eixo_ano = {"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}],
                "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                "legend": [{"properties": {"show": literal(True), "position": literal("Top")}}]}
    vis.append(container(
        f"{p}_linhas_prof", (424, 172, 416, 252),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Edição")],
                              "Y": [("Proficiência média", "Recorte escolhido"), ("Proficiência média do Brasil", "Brasil")]},
                objetos=eixo_ano),
        22, so_edicoes("linhas_prof"), titulo="Proficiência média: recorte × Brasil"))
    # tendência (reunião de 2026-11-06: "o desempenho está melhorando a cada edição?")
    vis.append(container(
        f"{p}_melhora", (848, 172, 416, 252),
        grafico("clusteredColumnChart", {"Category": [("dim_ano.ANO", "Edição")],
                                         "Y": [("% de redes que melhoraram", "Redes que melhoraram")]},
                objetos={**eixo_ano, "labels": [{"properties": {"show": literal(True)}}],
                         **linha_constante("y1AxisReferenceLine", 0.5)}),
        24, so_edicoes("melhora"), titulo="Redes que melhoraram desde a edição anterior"))
    # a inflação é explicada uma vez, em Sobre os dados (2026-11-09): aqui, só valores em R$ de 2025
    vis.append(container(
        f"{p}_linhas_gasto", (424, 432, 840, 252),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Ano")],
                              "Y": [("Gasto por aluno (mediana anual)", "Recorte escolhido"),
                                    ("Gasto por aluno do Brasil (mediana anual)", "Brasil")]},
                objetos=eixo_ano),
        23, titulo="Gasto por aluno por ano (mediana, R$ de 2025): recorte × Brasil"))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_edicao", f"{p}_{alvo}") for alvo in ("linhas_prof", "linhas_gasto", "melhora")]
    # nome interno mantido (tcc_inicio) para não quebrar os botões e o histórico; o nome exibido mudou
    return pagina("tcc_inicio", "Visão geral", sem_filtro), vis


def pagina_mapa() -> tuple[dict, list[dict]]:
    """Mapa da eficiência por município, com resumo por UF ao lado.
    O Mapa de formas desenha no máximo ~1.500 áreas: o mapa municipal completo pede uma UF escolhida
    (decisão de 2026-11-05); a visão nacional fica no Resumo por UF."""
    p = "map"
    # mesma régua no mapa (reunião de 2026-11-06), em % do esperado. O mapa e os cartões seguem um filtro de
    # comparação próprio da página ("modelo_mapa", sem sincronização), com padrão "Mesmo estado"; Henrique pediu
    # de volta a opção nacional (2026-11-09). As medidas "Mapa: ..." leem esse filtro e caem em "mesmo estado" sem ele.
    # O resumo por UF fica sempre na comparação nacional (medidas "UF: ..."): no mesmo estado, a média de cada UF
    # é zero no período (efeito fixo de UF) e não mostraria diferenças entre estados.
    vis = cabecalho(p, "Mapa da eficiência", "Onde as redes entregam mais ou menos do que o esperado",
                    segs=("uf", "etapa", "disciplina", "edicao", "modelo_mapa"))
    cartoes = [("redes", "Mapa: redes comparadas", "Redes comparadas"),
               ("acima", "Mapa: % acima do esperado", "Acima do esperado"),
               ("media", "Mapa: eficiência média (cartão)", "Média vs. esperado"),
               ("saltos", "Redes com salto atípico", "Saltos atípicos")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    vis.append(container(f"{p}_card_aviso", (672, 80, 592, 84), cartao_texto("Mapa: aviso da comparação"), 14))
    # mapa mais largo (924 px) e tabela mais estreita: os municípios ficavam pequenos demais
    # o aviso ganhou a contagem dos municípios sem nota (2026-11-09): duas linhas
    vis.append(container(f"{p}_aviso_mapa", (16, 172, 924, 48), cartao_texto("Aviso do mapa"), 19))
    vis.append(container(
        f"{p}_mapa", (16, 228, 924, 456),
        # local = nome do município (a malha usa "Nome (UF)" como id): a dica do mouse mostra o nome, e não o código
        mapa_formas(RECURSO_MALHA, "dim_municipio.MUNICIPIO_UF", ("Mapa: eficiência (%)", "vs. esperado (%)"),
                    [("Proficiência média", "Proficiência"),
                     ("Mapa: eficiência (pontos)", "vs. esperado (pontos)"),
                     ("Gasto das redes avaliadas (mediana)", "Gasto por aluno"),
                     ("Marca de rede parcial", "Rede municipal atende")]),
        20, titulo="% acima (+) ou abaixo (−) do esperado, na comparação escolhida no filtro"))
    vis.append(container(
        f"{p}_tabela_uf", (948, 172, 316, 512),
        grafico("tableEx", {"Values": [("dim_uf.SG_UF", "UF"), ("UF: % acima do esperado", "Acima"),
                                       ("UF: eficiência (%)", "vs. esperado"),
                                       ("UF: redes comparadas", "Redes")]},
                ordenar="UF: % acima do esperado",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        21, titulo="Resumo por UF (nacional)"))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_mapa", "Mapa"), vis


def pagina_defasagens() -> tuple[dict, list[dict]]:
    """Associação gasto × proficiência (ρ de Spearman) por edição e defasagem do gasto.
    As segmentações de edição e de defasagem valem para os cartões e a dispersão; o gráfico de colunas e a matriz
    mostram todas as edições e defasagens (a defasagem é a própria série/coluna, sem relação com o modelo)."""
    p = "def"
    vis = cabecalho(p, "Gastar mais se associa a notas maiores?",
                    "ρ de Spearman entre gasto por aluno e proficiência",
                    segs=("uf", "etapa", "disciplina", "edicao", "defasagem"))
    cartoes = [("rho", "Correlação gasto × proficiência (Spearman)", "ρ de Spearman"),
               ("redes", "Redes na correlação", "Redes na correlação"),
               ("gasto", "Gasto das redes avaliadas (mediana)", "Gasto mediano"),
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
    # glossário no padrão da Ficha (2026-11-09)
    vis.append(container(f"{p}_como_ler", (788, 412, 476, 272), glossario([
        ("ρ de Spearman", "de −1 a 1; compara a ordem das redes no gasto com a ordem na nota. 0 = sem relação. "
                          "Só com 30 redes ou mais."),
        ("Gasto de quando", "gasto do mesmo ano da prova ou de 1, 2 ou 4 anos antes (o aluno acumula anos de escola)."),
        ("Vazio", "sem gasto daquele ano: a série começa em 2017, e 4 anos antes só existe a partir de 2021."),
        ("Redes", "redes com gasto e nota que entram no cálculo."),
        ("Brasil × UF", "no Brasil, parte da associação vem das diferenças entre estados; dentro de uma UF, "
                        "costuma cair muito."),
        ("Dispersão", "cada ponto é uma rede, na edição e na defasagem escolhidas."),
    ], "Associação, não efeito do gasto: contexto, gestão e registro também entram."), 23))
    vis.append(rodape_fontes(p, 30))
    sem_filtro = [(f"{p}_seg_{seg}", f"{p}_{alvo}") for seg in ("edicao", "defasagem") for alvo in ("colunas", "matriz")]
    return pagina("tcc_defasagens", "Defasagens", sem_filtro), vis


PORTES = ["Até 5 mil", "5 a 10 mil", "10 a 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Mais de 500 mil"]


def pagina_contexto() -> tuple[dict, list[dict]]:
    """Perfil dos 7 clusters de contexto (A6) com gasto, nota e eficiência de cada um; gasto e nota por porte;
    dispersão gasto × proficiência colorida por cluster. O perfil (colunas de dim_cluster) é nacional e fixo;
    as medidas seguem os filtros da faixa."""
    p = "ctx"
    # sem o filtro de comparação: só a coluna de % acima dependia dele (revisão de filtros, 2026-11-09)
    vis = cabecalho(p, "Contexto e clusters", "Grupos de municípios com contexto parecido",
                    segs=("uf", "etapa", "disciplina", "edicao"))
    vis.append(container(
        f"{p}_perfil", (16, 80, 1248, 220),
        grafico("tableEx", {"Values": [
            ("dim_cluster.CLUSTER_ROTULO", "Cluster"), ("dim_cluster.MUNICIPIOS", "Municípios"),
            ("dim_cluster.POP_MEDIANA", "População mediana"), ("dim_cluster.ALFAB_MEDIA", "Alfabetização"),
            ("dim_cluster.IDHM_RENDA_MEDIO", "IDHM Renda"), ("dim_cluster.IDHM_LONGEVIDADE_MEDIO", "IDHM Longev."),
            ("dim_cluster.INFRA_MEDIA", "Infraestrutura"), ("dim_cluster.REGIAO_PREDOMINANTE", "Região principal"),
            ("dim_cluster.PARCELA_REGIAO_PREDOMINANTE", "% na região"),
            ("Redes avaliadas", "Redes com nota"), ("Gasto das redes avaliadas (mediana)", "Gasto (mediana)"),
            ("Proficiência mediana", "Proficiência (mediana)"), ("% acima do esperado (padrão)", "Acima do esperado")]},
            ordenar="dim_cluster.CLUSTER_ROTULO", decrescente=False,
            objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        10, titulo="Perfil dos 7 clusters (contexto nacional e fixo) e resultados no recorte escolhido"))
    vis.append(container(
        f"{p}_dispersao", (16, 308, 620, 332),
        grafico("scatterChart",
                {"Category": [("dim_municipio.MUNICIPIO_UF", "Município")], "Series": [("dim_municipio.CLUSTER_CURTO", "Cluster")],
                 "X": [("Gasto das redes avaliadas (mediana)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Proficiência média", "Proficiência")]},
                objetos={"categoryAxis": [{"properties": {"logAxisScale": literal(True)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Right"), "fontSize": literal(8.0)}}]}),
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
                         21, so_portes("porte_gasto"), titulo="Gasto mediano, por porte"))
    vis.append(container(f"{p}_porte_prof", (958, 308, 306, 332),
                         barras("Proficiência mediana", "Proficiência (mediana)"),
                         22, so_portes("porte_prof"), titulo="Proficiência mediana, por porte"))
    vis.append(container(f"{p}_nota", (16, 646, 1248, 40), texto([(
        "Clusters: k-médias com população, alfabetização, IDHM Renda e Longevidade da UF e infraestrutura das escolas, sem "
        "gasto nem nota. A separação entre os grupos é fraca (silhueta ≈ 0,23): são uma partição útil para formar pares, não "
        "tipos naturais, e saem ligados à região porque o IDHM só existe por UF. Acima do esperado: comparação nacional "
        "(2025: no mesmo estado).",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), 29, estilo="nenhum"))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_contexto", "Contexto e clusters"), vis


def pagina_estados() -> tuple[dict, list[dict]]:
    """Camada estadual (27 UFs, AF e EM), leitura descritiva: sem correlação nem eficiência, por serem poucas unidades.
    Gasto na versão A (G4). A versão B saiu do painel em 2026-11-09: onde a linha do Ensino Superior existe, A = B,
    e a mediana muda no máximo ~1%. Fica a marca ⚠ na tabela; a comparação A × B vai para o texto, como robustez."""
    p = "est"
    vis = cabecalho(p, "Redes estaduais", "Anos Finais e Ensino Médio nas 27 UFs: leitura descritiva",
                    segs=("etapa_est", "disciplina", "edicao"))
    cartoes = [("ufs", "UFs avaliadas", "UFs com nota"),
               ("prof", "Proficiência média estadual", "Proficiência média"),
               # rótulos curtos: "Gasto por aluno (mediana)" não cabia em 156 px (2026-11-09)
               ("gasto_a", "Gasto estadual por aluno (mediana, versão A)", "Gasto mediano"),
               ("sem_linha", "UFs sem a linha do Ensino Superior", "UFs sem a linha ⚠")]
    for i, (nome, m, rot) in enumerate(cartoes):
        vis.append(container(f"{p}_card_{nome}", (16 + i * 164, 80, 156, 84), cartao(m, rot), 10 + i))
    # glossário curto, sem título, no padrão da Ficha (2026-11-09)
    vis.append(container(f"{p}_aviso", (672, 80, 592, 84), glossario([
        ("27 UFs", "leitura descritiva, sem correlação nem eficiência."),
        ("Gasto", "função Educação menos o Ensino Superior, em R$ de 2025."),
        ("⚠", "UF sem a linha do Ensino Superior no ano: nada é descontado."),
    ], titulo=None, vertical=6.0), 15))
    so_edicoes = lambda nome: [filtro_visual(f"{p}_f_{nome}", "dim_ano", "EDICAO_SAEB", [True])]
    vis.append(container(
        f"{p}_dispersao", (16, 172, 620, 300),
        grafico("scatterChart",
                {"Category": [("dim_uf.SG_UF", "UF")], "Series": [("dim_uf.NM_REGIAO", "Região")],
                 "X": [("Gasto estadual por aluno (mediana, versão A)", "Gasto por aluno (R$ de 2025)")],
                 "Y": [("Proficiência média estadual", "Proficiência")]},
                objetos={"categoryLabels": [{"properties": {"show": literal(True), "fontSize": literal(8.0)}}],
                         "legend": [{"properties": {"show": literal(True), "position": literal("Top"), "fontSize": literal(8.0)}}]}),
        # um clique num ponto filtra a página toda para aquela UF (na conferência de 2026-11-09, parecia erro)
        20, titulo="Gasto × proficiência por UF (clique num ponto filtra a página)"))
    eixo_ano = {"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}],
                "valueAxis": [{"properties": {"showAxisTitle": literal(False)}}],
                "legend": [{"properties": {"show": literal(True), "position": literal("Top"), "fontSize": literal(8.0)}}]}
    vis.append(container(
        f"{p}_linhas_prof", (644, 172, 620, 300),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Edição")], "Series": [("dim_uf.NM_REGIAO", "Região")],
                              "Y": [("Proficiência média estadual", "Proficiência")]},
                objetos=eixo_ano),
        21, so_edicoes("linhas_prof"), titulo="Proficiência média das redes estaduais por edição, por região"))
    vis.append(container(
        f"{p}_tabela", (16, 480, 760, 204),
        grafico("tableEx", {"Values": [("dim_uf.NM_UF", "UF"), ("dim_uf.NM_REGIAO", "Região"),
                                       ("Gasto estadual por aluno (mediana, versão A)", "Gasto por aluno"),
                                       ("Proficiência média estadual", "Proficiência"),
                                       ("Marca do Ensino Superior", "Ensino Superior")]},
                ordenar="Proficiência média estadual",
                objetos={"total": [{"properties": {"totals": literal(False)}}]}),
        22, titulo="UFs na edição escolhida (clique no cabeçalho para reordenar)"))
    vis.append(container(
        f"{p}_linhas_gasto", (788, 480, 476, 204),
        grafico("lineChart", {"Category": [("dim_ano.ANO", "Ano")],
                              "Y": [("Gasto estadual por aluno (mediana, versão A)", "Gasto por aluno")]},
                objetos=eixo_ano),
        23, titulo="Gasto por aluno estadual (mediana das UFs)"))
    vis.append(container(f"{p}_rodape", (16, 690, 1248, 24), texto([(
        "Fontes: SICONFI/DCA (gasto estadual), Censo Escolar (matrículas), Saeb/Inep (proficiência). "
        "R$ de 2025 (IPCA). Leitura descritiva, não causal.",
        {"fontSize": "9pt", "color": COR_TEXTO_2})]), 30, estilo="nenhum"))
    sem_filtro = [(f"{p}_seg_edicao", f"{p}_{alvo}") for alvo in ("linhas_prof", "linhas_gasto")]
    return pagina("tcc_estados", "Estados", sem_filtro), vis


def data_dos_dados() -> str:
    """Data da última preparação das tabelas do Power BI (arquivo .parquet mais recente), em dd/mm/aaaa."""
    from datetime import datetime
    arquivos = list((BASE_DIR / "data" / "processed" / "powerbi").glob("*.parquet"))
    if not arquivos:
        return "data não encontrada"
    return datetime.fromtimestamp(max(a.stat().st_mtime for a in arquivos)).strftime("%d/%m/%Y")


def pagina_sobre() -> tuple[dict, list[dict]]:
    """Fontes, indicadores (seção 4 da especificação), limitações principais (seção 10 do registro), autores,
    data dos dados e acesso ao projeto. O QR Code (A7) fica como espaço reservado até haver endereço público."""
    p = "sob"
    vis = cabecalho(p, "Sobre os dados", "Fontes, indicadores, limitações e autoria do painel", segs=())
    tit = {"fontWeight": "bold", "fontSize": "11pt", "color": AZUL_FAIXA}
    sub = {"fontWeight": "bold", "fontSize": "9pt", "color": AZUL_FAIXA}
    corpo = {"fontSize": "9pt", "color": COR_TEXTO_2}
    vis.append(container(f"{p}_fontes", (16, 80, 404, 364), quadro_texto([
        ("Fontes", tit),
        ("• Gasto municipal: SIOPE/FNDE, despesa paga na subfunção 361 (Ensino Fundamental), 2017–2025.", corpo),
        ("• Gasto estadual: SICONFI/Tesouro (DCA), função 12 (Educação) menos a subfunção 364 (Ensino Superior).", corpo),
        ("• Matrículas e infraestrutura das escolas: Censo Escolar/Inep.", corpo),
        ("• Proficiência e IDEB: Saeb/Inep, edições de 2017 a 2025 (bienais).", corpo),
        ("• População e alfabetização: Censo Demográfico 2022/IBGE.", corpo),
        ("• IDHM Renda e Longevidade da UF: Atlas do Desenvolvimento Humano (PNUD, Ipea, FJP).", corpo),
        ("• Correção monetária: IPCA/IBGE. Todo valor em reais está em R$ de 2025: R$ 1 pago em 2017 vale R$ 1,51 de 2025 (gráfico ao lado).", corpo),
        ("Recorte", tit),
        ("Redes municipais (Anos Iniciais e Finais) de todo o Brasil e redes estaduais (Anos Finais e Ensino "
         "Médio). Entram só as redes com nota divulgada pelo Inep.", corpo),
    ]), 10))
    vis.append(container(f"{p}_indicadores", (428, 80, 420, 604), quadro_texto([
        ("Indicadores", tit),
        ("Gasto por aluno", sub),
        ("Despesa da rede ÷ matrículas da rede, em R$ de 2025 por aluno/ano. Nas redes municipais, só o Ensino "
         "Fundamental (sem Educação Infantil). Agregado pela mediana entre as redes.", corpo),
        ("Proficiência", sub),
        ("Pontos do Saeb, média simples entre as redes, por etapa e disciplina. Não compare etapas nem disciplinas.", corpo),
        ("Eficiência (vs. esperado)", sub),
        ("Quanto a nota ficou acima (+) ou abaixo (−) da esperada, em % da esperada: 0% = nota igual à esperada; +5% = 5% "
         "acima. A esperada é a de redes com o mesmo gasto e contexto (população, alfabetização, infraestrutura, tamanho "
         "da rede, IDHM Renda e Longevidade da UF). Modelo nacional de 2017 a 2023; o do mesmo estado cobre 2025.", corpo),
        ("Percentil e faixa de eficiência", sub),
        ("Posição entre as redes da mesma etapa, disciplina e edição: 80 = melhor que 80% delas.", corpo),
        ("Clusters e pares", sub),
        ("7 grupos de municípios com contexto parecido, sem gasto nem nota. Pares = mesmo cluster (e mesma UF, na "
         "comparação no mesmo estado) e gasto entre 0,8 e 1,25 vez o do município de referência.", corpo),
        ("ρ de Spearman", sub),
        ("Associação entre a ordem das redes no gasto e na nota (−1 a 1), só com 30 redes ou mais.", corpo),
        ("⚠ Salto atípico", sub),
        ("Variação desde a edição anterior a mais de 3 desvios-padrão da média: conferir antes de interpretar.", corpo),
        ("Cobertura do Saeb", sub),
        ("Redes com nota ÷ municípios do recorte.", corpo),
    ]), 11))
    vis.append(container(f"{p}_limitacoes", (856, 80, 408, 404), quadro_texto([
        ("Limitações principais", tit),
        ("• Associação, não causalidade: o painel não mostra efeito do gasto sobre a nota.", corpo),
        ("• A eficiência é um resíduo: também capta gestão, contexto familiar e qualidade do registro.", corpo),
        ("• Só entram redes com nota divulgada; as pequenas, que gastam mais por aluno, ficam sub-representadas.", corpo),
        ("• O IDHM só existe por UF e termina em 2024: a edição de 2025 não tem o modelo oficial.", corpo),
        ("• O gasto municipal cobre todo o Fundamental: Anos Iniciais e Finais usam o mesmo valor.", corpo),
        ("• Gasto da série começa em 2017: defasagens de 2 e 4 anos só a partir de 2019 e 2021.", corpo),
        ("• 2021 foi aplicado na pandemia, com menos redes e condições atípicas.", corpo),
        ("• Camada estadual: só 27 unidades, leitura descritiva.", corpo),
        ("• Clusters com separação fraca (silhueta ≈ 0,23) e ligados à região.", corpo),
    ]), 12))
    vis.append(container(f"{p}_autoria", (16, 452, 404, 232), quadro_texto([
        ("Autoria e atualização", tit),
        ("Trabalho de Conclusão de Curso em Administração, FEA/USP. Autores: Henrique Lindoso (dados e painel) e "
         "Guilherme (texto).", corpo),
        (f"Dados preparados em {data_dos_dados()}. Registro completo das decisões de método no repositório do "
         "projeto (docs/decisoes_metodo.md).", corpo),
        ("Parte do código e da documentação foi desenvolvida com apoio de um assistente de IA (Claude, da Anthropic). "
         "As decisões de método são dos autores.", corpo),
        # A7: o QR Code precisa de um endereço público (o repositório é privado); até lá, só o aviso
        ("Acesso: o QR Code entra aqui quando o endereço público do painel for definido.", corpo),
    ]), 13))
    # inflação explicada uma vez, aqui (2026-11-09): quanto vale R$ 1 de cada ano em R$ de 2025
    vis.append(container(
        f"{p}_ipca", (856, 492, 408, 192),
        grafico("clusteredColumnChart", {"Category": [("dim_ano.ANO", "Ano")], "Y": [("Fator do IPCA", "R$ de 2025")]},
                objetos={"categoryAxis": [{"properties": {"axisType": literal("Categorical"), "showAxisTitle": literal(False)}}],
                         "valueAxis": [{"properties": {"showAxisTitle": literal(False), "show": literal(False)}}],
                         "labels": [{"properties": {"show": literal(True), "fontSize": literal(8.0)}}]}),
        14, titulo="Inflação: R$ 1 de cada ano em R$ de 2025"))
    vis.append(rodape_fontes(p, 30))
    return pagina("tcc_sobre", "Sobre os dados"), vis


PAGINAS = [pagina_boas_vindas, pagina_inicio, pagina_eficiencia, pagina_ficha, pagina_pares, pagina_mapa, pagina_defasagens, pagina_contexto,
           pagina_estados, pagina_sobre]


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


# ───────────────────────── conferência de textos cortados (2026-11-09) ─────────────────────────
# Estimativa, não medição: largura média da letra ~0,48 da altura (negrito, ~0,50), calibrada com prints do Desktop em 2026-11-09; linha de ~1,45.
# Serve para achar os blocos que com certeza estouram; o Power BI corta sem avisar (quadros, títulos, rótulos).

def _num(v) -> float:
    return float(str(v["expr"]["Literal"]["Value"]).rstrip("DL"))


def _linhas(texto_: str, largura: float, px: float, negrito: bool) -> int:
    largura_letra = px * (0.50 if negrito else 0.48)
    linhas, atual = 1, 0.0
    for palavra in texto_.split():
        w = (len(palavra) + 1) * largura_letra
        if atual + w > largura and atual > 0:
            linhas, atual = linhas + 1, w
        else:
            atual += w
    return linhas


def conferir_textos() -> list[str]:
    avisos = []
    for montar in PAGINAS:
        pag, visuais = montar()
        # faixa: título e subtítulo têm de caber antes da primeira segmentação (o subtítulo de Defasagens passava por baixo)
        segs_faixa = [c["position"]["x"] for c in visuais if "_seg_" in c["name"] and c["position"]["y"] < 72]
        faixa = next((c for c in visuais if c["name"].endswith("_titulo")), None)
        if faixa and segs_faixa:
            livre = min(segs_faixa) - 16 - 8
            for par in faixa["visual"]["objects"]["general"][0]["properties"]["paragraphs"]:
                run = par["textRuns"][0]
                px = float(run["textStyle"].get("fontSize", "10pt").rstrip("pt")) * 4 / 3
                largura = len(run["value"]) * px * (0.50 if run["textStyle"].get("fontWeight") == "bold" else 0.48)
                if largura > livre:
                    avisos.append(f"{pag['displayName']} · faixa: {run['value'][:40]!r} passa por baixo dos filtros "
                                  f"(~{largura:.0f} px em {livre:.0f} px)")
        for c in visuais:
            v, pos = c["visual"], c["position"]
            vco = v.get("visualContainerObjects", {})
            pad = vco.get("padding", [{}])[0].get("properties", {})
            ph = _num(pad["left"]) if pad else 0.0
            pv = _num(pad["top"]) if pad else 0.0
            titulo = vco.get("title", [{}])[0].get("properties", {}).get("text")
            if titulo:
                largura_tit = len(titulo["expr"]["Literal"]["Value"].strip("'")) * 11 * 4 / 3 * 0.57
                if largura_tit > pos["width"] - 24:
                    avisos.append(f"{pag['displayName']} · {c['name']}: título cortado "
                                  f"(~{largura_tit:.0f} px em {pos['width'] - 24:.0f} px)")
            if v["visualType"] == "textbox":
                pars = v["objects"]["general"][0]["properties"]["paragraphs"]
                altura = 0.0
                for par in pars:
                    # parágrafo com vários trechos: mede o texto inteiro com a maior letra e negrito se houver
                    runs = par["textRuns"]
                    px = max(float(r["textStyle"].get("fontSize", "10pt").rstrip("pt")) for r in runs) * 4 / 3
                    negrito = any(r["textStyle"].get("fontWeight") == "bold" for r in runs) and len(runs) == 1
                    valor = "".join(r["value"] for r in runs)
                    altura += _linhas(valor, pos["width"] - 2 * ph - 8, px, negrito) * px * 1.45
                disponivel = pos["height"] - 2 * pv - 4
                if altura > disponivel:
                    avisos.append(f"{pag['displayName']} · {c['name']}: texto não cabe "
                                  f"(~{altura:.0f} px em {disponivel:.0f} px)")
            if v["visualType"] == "slicer":
                # lista suspensa: o maior valor da coluna tem de caber ao lado da seta (~44 px de seta e margens)
                campo_ = v["query"]["queryState"]["Values"]["projections"][0]["field"]["Column"]
                tabela_, coluna_ = campo_["Expression"]["SourceRef"]["Entity"], campo_["Property"]
                arq = BASE_DIR / "data" / "processed" / "powerbi" / f"{tabela_}.parquet"
                if arq.exists():
                    import polars as pl
                    valores = pl.read_parquet(arq, columns=[coluna_])[coluna_].cast(pl.Utf8).drop_nulls().unique()
                    if valores.len() <= 100:
                        maior = max(valores.to_list(), key=len)
                        if len(maior) * 10 * 4 / 3 * 0.48 + 44 > pos["width"]:
                            avisos.append(f"{pag['displayName']} · {c['name']}: valor {maior!r} cortado no filtro "
                                          f"(~{len(maior) * 10 * 4 / 3 * 0.48 + 44:.0f} px em {pos['width']} px)")
            if v["visualType"] == "card":
                for proj in v["query"]["queryState"].get("Values", {}).get("projections", []):
                    rot = proj.get("displayName")
                    if rot and len(rot) * 9 * 4 / 3 * 0.52 > pos["width"] - 2 * ph - 8:
                        avisos.append(f"{pag['displayName']} · {c['name']}: rótulo do cartão cortado ({rot!r})")
    return avisos


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
    ap.add_argument("--conferir-textos", action="store_true",
                    help="só lista os blocos cujo texto provavelmente não cabe (estimativa) e sai")
    args = ap.parse_args()
    if args.conferir_textos:
        avisos = conferir_textos()
        print("\n".join(avisos) if avisos else "[OK] Nenhum texto estimado como cortado")
        sys.exit(0)
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
