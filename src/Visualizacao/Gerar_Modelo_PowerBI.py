"""Escreve o modelo semântico do dashboard oficial em TMDL, dentro do projeto Power BI (.pbip).

Fluxo (powerbi/roteiro_construcao.md, Fase 1):
1. No Power BI Desktop, criar um relatório em branco e salvar como projeto em powerbi/tcc_gasto_saeb.pbip.
   O Desktop escreve a pasta do relatório (formato PBIR) e um modelo vazio em tcc_gasto_saeb.SemanticModel.
2. Fechar o Power BI e rodar este script: ele grava as 12 tabelas, o parâmetro PastaDados, as relações,
   as ordenações e as medidas de powerbi/medidas.dax em tcc_gasto_saeb.SemanticModel/definition/.
3. Reabrir o .pbip e clicar em Atualizar.

O script é de partida: depois que o modelo existe, o Desktop passa a ser a fonte (os arquivos TMDL vão
para o Git). Por isso ele se recusa a sobrescrever um modelo que já tem tabelas, salvo com --forcar.

Antes de gravar, confere: tipos lidos dos Parquet, ordenações 1:1, nomes únicos e se toda coluna
tabela[COLUNA] e toda medida [Medida] citadas nas fórmulas existem.
"""
import argparse
import re
import shutil
import sys
import uuid
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
DADOS = BASE_DIR / "data" / "processed" / "powerbi"
PASTA_PBI = BASE_DIR / "powerbi"
MODELO = PASTA_PBI / "tcc_gasto_saeb.SemanticModel"
MEDIDAS = PASTA_PBI / "medidas.dax"
NS = uuid.UUID("6f1c2a52-7d0e-4d43-9a57-3c1f2b8e9a10")  # lineageTags estáveis entre execuções

TABELAS = ["dim_municipio", "dim_uf", "dim_cluster", "dim_ano", "dim_etapa", "dim_disciplina", "dim_defasagem",
           "dim_modelo", "fato_desempenho_municipal", "fato_gasto_municipal", "fato_desempenho_estadual",
           "fato_gasto_estadual", "fato_oferta_municipal"]

# (lado muitos, lado um)
RELACOES = [
    ("dim_municipio.SG_UF", "dim_uf.SG_UF"),
    ("fato_desempenho_estadual.SG_UF", "dim_uf.SG_UF"),
    ("fato_gasto_estadual.SG_UF", "dim_uf.SG_UF"),
    ("dim_municipio.CLUSTER", "dim_cluster.CLUSTER"),
    ("fato_desempenho_municipal.CO_MUNICIPIO", "dim_municipio.CO_MUNICIPIO"),
    ("fato_gasto_municipal.CO_MUNICIPIO", "dim_municipio.CO_MUNICIPIO"),
    *[(f"{f}.ANO", "dim_ano.ANO") for f in ("fato_desempenho_municipal", "fato_gasto_municipal",
                                            "fato_desempenho_estadual", "fato_gasto_estadual")],
    *[(f"{f}.{c}", f"dim_{c.lower()}.{c}") for f in ("fato_desempenho_municipal", "fato_desempenho_estadual")
      for c in ("ETAPA", "DISCIPLINA")],
    # oferta da rede municipal por etapa (motivo da falta de nota e parcela municipal; 2026-11-09)
    ("fato_oferta_municipal.CO_MUNICIPIO", "dim_municipio.CO_MUNICIPIO"),
    ("fato_oferta_municipal.ANO", "dim_ano.ANO"),
    ("fato_oferta_municipal.ETAPA", "dim_etapa.ETAPA"),
]

ORDENAR = {  # coluna de rótulo -> coluna que dá a ordem
    ("dim_etapa", "NOME_ETAPA"): "ORDEM",
    ("dim_disciplina", "NOME_DISCIPLINA"): "ORDEM",
    ("dim_defasagem", "ROTULO_DEFASAGEM"): "DEFASAGEM",
    ("dim_modelo", "ROTULO_MODELO"): "ORDEM",
    ("dim_municipio", "PORTE"): "PORTE_ORDEM",
    ("dim_municipio", "CLUSTER_ROTULO"): "CLUSTER",
    ("dim_municipio", "CLUSTER_CURTO"): "CLUSTER",
    ("dim_cluster", "CLUSTER_ROTULO"): "CLUSTER",
}

# chaves dos fatos ficam ocultas: os filtros usam sempre as dimensões
OCULTAS = {"CO_MUNICIPIO", "SG_UF", "ETAPA", "DISCIPLINA", "ANO"}

CALCULADAS = {
    "ref_municipio": (
        "SELECTCOLUMNS ( dim_municipio, \"REF_CO_MUNICIPIO\", dim_municipio[CO_MUNICIPIO], "
        "\"REF_MUNICIPIO_UF\", dim_municipio[MUNICIPIO_UF], \"REF_CLUSTER\", dim_municipio[CLUSTER] )",
        {"REF_CO_MUNICIPIO": "string", "REF_MUNICIPIO_UF": "string", "REF_CLUSTER": "int64"},
    ),
    # segundo município da comparação 1 a 1 na página Pares (reunião de 2026-11-06), também sem relação
    "cmp_municipio": (
        "SELECTCOLUMNS ( dim_municipio, \"CMP_CO_MUNICIPIO\", dim_municipio[CO_MUNICIPIO], "
        "\"CMP_MUNICIPIO_UF\", dim_municipio[MUNICIPIO_UF], \"CMP_CLUSTER\", dim_municipio[CLUSTER] )",
        {"CMP_CO_MUNICIPIO": "string", "CMP_MUNICIPIO_UF": "string", "CMP_CLUSTER": "int64"},
    ),
    "_Medidas": ("ROW ( \"Coluna\", 0 )", {"Coluna": "int64"}),
}

FORMATOS = [  # (padrão no nome da medida, formatString); vale o primeiro que casar
    (r"^(Gasto (por aluno|das redes|estadual|do município)|Par: gasto)", "R$ #,0"),
    (r"^(Eficiência \(pontos\)|Eficiência do município|Nota menos|Par: (eficiência|diferença))", "+0.0;-0.0;0.0"),
    # eficiência em % do esperado (medida principal desde 2026-11-09); tem de vir antes das regras em pontos
    (r"^(Eficiência \(% do esperado\)|Eficiência % do|Par: eficiência \(%\)|Comparado: eficiência \(%\))", "+0.0%;-0.0%;0.0%"),
    (r"^Par: diferença \(p\.p\.\)", "+0.0;-0.0;0.0"),
    (r"^Mapa: eficiência \(%\)", "+0.0%;-0.0%;0.0%"),
    (r"^Mapa: eficiência \(pontos\)", "+0.0;-0.0;0.0"),
    (r"^Mapa: % acima", "0.0%"),
    (r"^Mapa: redes", "#,0"),
    (r"^UF: eficiência \(%\)", "+0.0%;-0.0%;0.0%"),
    (r"^UF: % acima", "0.0%"),
    (r"^UF: redes", "#,0"),
    (r"^Fator do IPCA", "0.00"),
    (r"^% de redes", "0%"),
    # comparação 1 a 1 da página Pares (2026-11-09)
    (r"^Comparado: gasto", "R$ #,0"),
    (r"^Comparado: eficiência", "+0.0;-0.0;0.0"),
    (r"^(Comparado: (proficiência|esperada)|Esperada)", "0.0"),
    (r"^Comparado: percentil", "0"),
    (r"^(Proficiência|Par: proficiência)", "0.0"),
    (r"^(Percentil|Par: percentil)", "0"),
    (r"^Parcela", "0%"),
    (r"^Pares (encontrados|que)", "#,0"),
    (r"^(% acima|Cobertura)", "0.0%"),
    (r"^Correlação", "0.00"),
    (r"^(IDEB|Nota padronizada|Gasto ÷)", "0.00"),
    (r"^(Redes|Municípios|UFs)", "#,0"),
    (r"^(Defasagem|É par)", "0"),
]

# formato das colunas exibidas direto nos visuais (perfil dos clusters, página Contexto e clusters, 2026-11-06)
FORMATOS_COLUNA = {
    ("dim_cluster", "MUNICIPIOS"): "#,0",
    ("dim_cluster", "POP_MEDIANA"): "#,0",
    ("dim_cluster", "ALFAB_MEDIA"): "0.0%",
    ("dim_cluster", "IDHM_RENDA_MEDIO"): "0.000",
    ("dim_cluster", "IDHM_LONGEVIDADE_MEDIO"): "0.000",
    ("dim_cluster", "INFRA_MEDIA"): "0.00",
    ("dim_cluster", "PARCELA_REGIAO_PREDOMINANTE"): "0%",
    ("dim_municipio", "POPULACAO_TOTAL_CENSO"): "#,0",
    ("dim_municipio", "TAXA_ALFABETIZACAO_15MAIS"): "0.0%",
    ("fato_oferta_municipal", "QT_MAT_MUN"): "#,0",
    ("fato_oferta_municipal", "QT_MAT_EST"): "#,0",
    ("fato_oferta_municipal", "PART_MUN"): "0.0%",
}


def adicionar_tabelas(definicao: Path, schemas: dict) -> list[str]:
    """Acrescenta a um modelo existente as tabelas de TABELAS que ainda não têm arquivo, com as relações delas,
    a referência em model.tmdl e a ordem de consulta. Não mexe nas tabelas, relações e medidas existentes."""
    novas = [t for t in [*TABELAS, *CALCULADAS] if not (definicao / "tables" / f"{t}.tmdl").exists()]
    if not novas:
        return []
    for t in novas:
        texto_t = tabela_importada(t, schemas[t]) if t in TABELAS else tabela_calculada(t, *CALCULADAS[t], [])
        (definicao / "tables" / f"{t}.tmdl").write_text(texto_t, encoding="utf-8")
    rel = definicao / "relationships.tmdl"
    texto_rel = rel.read_text(encoding="utf-8").rstrip("\n")
    for a, b in RELACOES:
        if a.split(".")[0] in novas or b.split(".")[0] in novas:
            texto_rel += f"\n\nrelationship {tag('r', a, b)}\n\tfromColumn: {a}\n\ttoColumn: {b}"
    rel.write_text(texto_rel + "\n", encoding="utf-8")
    mod = definicao / "model.tmdl"
    linhas = mod.read_text(encoding="utf-8").split("\n")
    ultima_ref = max(i for i, l in enumerate(linhas) if l.startswith("ref table "))
    linhas[ultima_ref + 1:ultima_ref + 1] = [f"ref table {nome(t)}" for t in novas]
    texto = "\n".join(linhas)
    ordem = ["PastaDados", *TABELAS]
    texto = re.sub(r"annotation PBI_QueryOrder = \[.*\]",
                   "annotation PBI_QueryOrder = [" + ",".join(f'"{q}"' for q in ordem) + "]", texto)
    mod.write_text(texto, encoding="utf-8")
    return novas


def formatar_colunas(definicao: Path) -> list[str]:
    """Acrescenta formatString às colunas de FORMATOS_COLUNA num modelo existente (sem mexer no resto do arquivo)."""
    feitas = []
    for (t, c), f in FORMATOS_COLUNA.items():
        arq = definicao / "tables" / f"{t}.tmdl"
        texto = arq.read_text(encoding="utf-8")
        bloco = re.search(rf"(\tcolumn {re.escape(nome(c))}\n)(.*?)(?=\n\t\S|\n\n\t\S|\Z)", texto, re.S)
        if not bloco:
            sys.exit(f"[ERRO] coluna {t}[{c}] não encontrada em {arq.name}")
        corpo = bloco.group(2)
        if "formatString:" in corpo:
            novo = re.sub(r"formatString: .*", f"formatString: {f}", corpo)
        else:
            novo = re.sub(r"(\t\tdataType: \w+\n)", rf"\g<1>\t\tformatString: {f}\n", corpo, count=1)
        if novo != corpo:
            texto = texto[:bloco.start(2)] + novo + texto[bloco.end(2):]
            arq.write_text(texto, encoding="utf-8")
            feitas.append(f"{t}[{c}] = {f}")
    return feitas


def tipo_tmdl(dtype: pl.DataType) -> tuple[str, str]:
    """Tipo da coluna no TMDL e o tipo correspondente do Power Query."""
    if dtype == pl.Utf8 or dtype == pl.String:
        return "string", "type text"
    if dtype == pl.Boolean:
        return "boolean", "type logical"
    if dtype.is_integer():
        return "int64", "Int64.Type"
    if dtype.is_float():
        return "double", "type number"
    raise TypeError(f"tipo sem correspondência no TMDL: {dtype}")


def nome(n: str) -> str:
    """Nome de objeto TMDL: entre aspas simples se tiver espaço ou . = : '"""
    return "'" + n.replace("'", "''") + "'" if re.search(r"[\s.=:']", n) else n


def tag(*partes: str) -> str:
    return str(uuid.uuid5(NS, "/".join(partes)))


def ler_medidas() -> list[dict]:
    """Lê powerbi/medidas.dax: blocos separados por linha em branco; '// ... Pasta: X ...' define a pasta;
    comentários colados acima da medida viram a descrição."""
    medidas, pasta = [], ""
    for bloco in re.split(r"\n\s*\n", MEDIDAS.read_text(encoding="utf-8")):
        linhas = bloco.strip("\n").split("\n")
        m = re.search(r"Pasta:\s*(.+?)\s*─", bloco)
        if m:
            pasta = m.group(1)
            continue
        comentarios = [l[2:].strip() for l in linhas if l.startswith("//")]
        codigo = [l for l in linhas if not l.startswith("//")]
        if not codigo:
            continue
        cab = re.match(r"^(\S.*?) =\s*(.*)$", codigo[0])
        if not cab:
            raise ValueError(f"bloco sem cabeçalho de medida: {codigo[0]!r}")
        corpo = ([cab.group(2)] if cab.group(2) else []) + codigo[1:]
        medidas.append({"nome": cab.group(1).strip(), "corpo": corpo, "pasta": pasta, "descricao": comentarios})
    return medidas


def formato(n: str) -> str | None:
    return next((f for padrao, f in FORMATOS if re.search(padrao, n)), None)


def tabela_importada(t: str, schema: dict) -> str:
    tipos = ", ".join(f'{{"{c}", {tipo_tmdl(d)[1]}}}' for c, d in schema.items())
    linhas = [f"table {nome(t)}", f"\tlineageTag: {tag('t', t)}", ""]
    for c, d in schema.items():
        linhas += [f"\tcolumn {nome(c)}", f"\t\tdataType: {tipo_tmdl(d)[0]}"]
        if (t, c) in FORMATOS_COLUNA:
            linhas.append(f"\t\tformatString: {FORMATOS_COLUNA[(t, c)]}")
        if t.startswith("fato_") and c in OCULTAS:
            linhas.append("\t\tisHidden")
        linhas += [f"\t\tlineageTag: {tag('c', t, c)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}"]
        if (t, c) in ORDENAR:
            linhas.append(f"\t\tsortByColumn: {nome(ORDENAR[(t, c)])}")
        linhas.append("")
    linhas += [
        f"\tpartition {nome(t)} = m", "\t\tmode: import", "\t\tsource =",
        "\t\t\tlet",
        f'\t\t\t    Fonte = Parquet.Document(File.Contents(PastaDados & "\\{t}.parquet")),',
        f"\t\t\t    Tipos = Table.TransformColumnTypes(Fonte, {{{tipos}}})",
        "\t\t\tin",
        "\t\t\t    Tipos", "",
    ]
    return "\n".join(linhas)


def medida_tmdl(m: dict) -> list[str]:
    linhas = [f"\t/// {d}" for d in m["descricao"]]
    if len(m["corpo"]) == 1:
        linhas.append(f"\tmeasure {nome(m['nome'])} = {m['corpo'][0].strip()}")
    else:
        linhas.append(f"\tmeasure {nome(m['nome'])} =")
        linhas += [f"\t\t\t{l}" if l.strip() else "" for l in m["corpo"]]
    if formato(m["nome"]):
        linhas.append(f"\t\tformatString: {formato(m['nome'])}")
    return linhas + [f"\t\tdisplayFolder: {m['pasta']}", f"\t\tlineageTag: {tag('m', m['nome'])}", ""]


def adicionar_medidas(arquivo: Path, medidas: list[dict]) -> list[str]:
    """Acrescenta ao _Medidas.tmdl do projeto só as medidas de medidas.dax que ainda não existem.
    Não altera nem remove nenhuma medida existente (o Desktop é a fonte delas)."""
    texto = arquivo.read_text(encoding="utf-8")
    existentes = {n.strip("'").replace("''", "'") for n in re.findall(r"^\tmeasure (.+?) =", texto, flags=re.M)}
    novas = [m for m in medidas if m["nome"] not in existentes]
    if novas:
        bloco = "\n".join(l for m in novas for l in medida_tmdl(m))
        arquivo.write_text(texto.rstrip("\n") + "\n\n" + bloco + "\n", encoding="utf-8")
    return [m["nome"] for m in novas]


def atualizar_medidas(arquivo: Path, medidas: list[dict], nomes: list[str]) -> list[str]:
    """Troca no _Medidas.tmdl do projeto só as medidas nomeadas pela versão de medidas.dax, mantendo o lineageTag.
    O resto do arquivo (outras medidas, colunas, partição) fica como o Desktop gravou."""
    por_nome = {m["nome"]: m for m in medidas}
    faltando = [n for n in nomes if n not in por_nome]
    if faltando:
        sys.exit(f"[ERRO] Medidas que não estão em medidas.dax: {', '.join(faltando)}")
    linhas = arquivo.read_text(encoding="utf-8").split("\n")
    saida, trocadas, i = [], [], 0
    while i < len(linhas):
        j = i
        while j < len(linhas) and linhas[j].startswith("\t///"):  # descrição colada acima da medida
            j += 1
        cab = re.match(r"^\tmeasure (.+?) =", linhas[j]) if j < len(linhas) else None
        if not cab:
            saida += linhas[i:j + 1]
            i = j + 1
            continue
        k = j + 1  # o bloco vai até a próxima linha de nível 1 (medida, coluna, partição ou descrição)
        while k < len(linhas) and not re.match(r"^\t[^\t]", linhas[k]):
            k += 1
        nome_m = cab.group(1).strip("'").replace("''", "'")
        if nome_m in nomes:
            antiga = next((m.group(1) for l in linhas[j:k] if (m := re.search(r"lineageTag: (\S+)", l))), None)
            novo = medida_tmdl(por_nome[nome_m])
            saida += [re.sub(r"lineageTag: \S+", f"lineageTag: {antiga}", l) if antiga else l for l in novo]
            trocadas.append(nome_m)
        else:
            saida += linhas[i:k]
        i = k
    nao_achadas = [n for n in nomes if n not in trocadas]
    if nao_achadas:
        sys.exit(f"[ERRO] Medidas que não estão no modelo (use --adicionar-medidas): {', '.join(nao_achadas)}")
    arquivo.write_text("\n".join(saida), encoding="utf-8")
    return trocadas


def tabela_calculada(t: str, dax: str, colunas: dict, medidas: list[dict]) -> str:
    linhas = [f"table {nome(t)}", f"\tlineageTag: {tag('t', t)}", ""]
    for m in medidas:
        linhas += medida_tmdl(m)
    for c, tipo in colunas.items():
        linhas += [f"\tcolumn {nome(c)}", f"\t\tdataType: {tipo}"]
        if t == "_Medidas":
            linhas.append("\t\tisHidden")
        linhas += ["\t\tisNameInferred", f"\t\tlineageTag: {tag('c', t, c)}", "\t\tsummarizeBy: none",
                   f"\t\tsourceColumn: [{c}]", ""]
    linhas += [f"\tpartition {nome(t)} = calculated", "\t\tmode: import", f"\t\tsource = {dax}", ""]
    return "\n".join(linhas)


def conferir(schemas: dict, medidas: list[dict]) -> None:
    colunas = {t: set(s) for t, s in schemas.items()} | {t: set(c) for t, (_, c) in CALCULADAS.items()}
    nomes = [m["nome"] for m in medidas]
    assert len(nomes) == len(set(nomes)), "medida com nome repetido"
    for (t, rot), ordem in ORDENAR.items():
        df = pl.read_parquet(DADOS / f"{t}.parquet", columns=[rot, ordem]).unique()
        assert df.height == df[rot].n_unique(), f"{t}.{rot} não tem uma única ordem em {ordem}"
    for a, b in RELACOES:
        for lado in (a, b):
            t, c = lado.split(".")
            assert c in colunas[t], f"relação usa coluna inexistente: {lado}"
        t, c = b.split(".")
        chave = pl.read_parquet(DADOS / f"{t}.parquet", columns=[c])[c]
        assert chave.n_unique() == chave.len(), f"lado 'um' com chave repetida: {b}"
    problemas = []
    for m in medidas:
        texto = "\n".join(m["corpo"])
        # em DAX, aspas dentro de texto se escrevem dobradas (""); \" invalida a medida inteira (2026-11-09)
        if re.search(r'\\"', re.sub(r"//.*", "", texto)):
            problemas.append(f'{m["nome"]}: use "" (e não \\") para aspas dentro de texto')
        for t, c in re.findall(r"\b([A-Za-z_]\w*)\[([^\]]+)\]", texto):
            if t not in colunas or c not in colunas[t]:
                problemas.append(f"{m['nome']}: coluna {t}[{c}] não existe")
        for ref in re.findall(r"(?<![\w\]])\[([^\]@]+)\]", texto):
            if ref not in nomes:
                problemas.append(f"{m['nome']}: medida [{ref}] não existe")
    if problemas:
        sys.exit("[ERRO] Fórmulas com referências inválidas:\n  " + "\n  ".join(problemas))


def model_tmdl(original: str | None) -> str:
    """Mantém as propriedades que o Desktop gravou no modelo vazio e acrescenta a ordem das tabelas."""
    if original:
        manter = [l for l in original.rstrip().split("\n")
                  if not re.match(r"^(ref table|annotation (PBI_QueryOrder|__PBI_TimeIntelligenceEnabled))", l)]
    else:
        manter = ["model Model", "\tculture: pt-BR", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
                  "\tsourceQueryCulture: pt-BR"]
    if not any(l.strip() == "discourageImplicitMeasures" for l in manter):
        manter.insert(1, "\tdiscourageImplicitMeasures")
    ordem = ["PastaDados", *TABELAS]
    return "\n".join([
        *manter, "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        "annotation PBI_QueryOrder = [" + ",".join(f'"{q}"' for q in ordem) + "]", "",
        *[f"ref table {nome(t)}" for t in [*TABELAS, *CALCULADAS]], "",
    ])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--forcar", action="store_true", help="sobrescreve um modelo que já tem tabelas")
    ap.add_argument("--pasta", type=Path, help="outra pasta .SemanticModel (para testes)")
    ap.add_argument("--adicionar-medidas", action="store_true",
                    help="só acrescenta ao modelo existente as medidas novas de medidas.dax (feche o Power BI antes)")
    ap.add_argument("--atualizar-medidas", nargs="+", metavar="MEDIDA",
                    help="troca no modelo existente só estas medidas pela versão de medidas.dax (feche o Power BI antes)")
    ap.add_argument("--formatar-colunas", action="store_true",
                    help="só aplica FORMATOS_COLUNA às colunas do modelo existente (feche o Power BI antes)")
    ap.add_argument("--adicionar-tabelas", action="store_true",
                    help="só acrescenta ao modelo existente as tabelas novas de TABELAS, com as relações (feche o Power BI antes)")
    ap.add_argument("--recriar-tabelas", nargs="+", metavar="TABELA",
                    help="regrava só estas tabelas importadas a partir do Parquet atual (colunas novas; feche o Power BI antes)")
    args = ap.parse_args()
    if args.pasta:
        MODELO = args.pasta.resolve()

    if args.recriar_tabelas:
        # mesmas lineageTags (determinísticas): relações, medidas e visuais continuam apontando para as colunas
        fora = [t for t in args.recriar_tabelas if t not in TABELAS]
        if fora:
            sys.exit(f"[ERRO] Não são tabelas importadas: {', '.join(fora)}")
        schemas = {t: dict(pl.read_parquet_schema(DADOS / f"{t}.parquet")) for t in TABELAS}
        conferir(schemas, ler_medidas())
        for t in args.recriar_tabelas:
            (MODELO / "definition" / "tables" / f"{t}.tmdl").write_text(tabela_importada(t, schemas[t]), encoding="utf-8")
        print(f"[OK] Tabelas regravadas: {', '.join(args.recriar_tabelas)}")
        if not (args.adicionar_medidas or args.atualizar_medidas or args.adicionar_tabelas or args.formatar_colunas):
            sys.exit(0)

    if args.adicionar_tabelas:
        schemas = {t: dict(pl.read_parquet_schema(DADOS / f"{t}.parquet")) for t in TABELAS}
        novas = adicionar_tabelas(MODELO / "definition", schemas)
        print(f"[OK] Tabelas acrescentadas: {', '.join(novas) if novas else 'nenhuma (todas já existem)'}")
        if not (args.adicionar_medidas or args.atualizar_medidas or args.formatar_colunas):
            sys.exit(0)

    if args.formatar_colunas:
        feitas = formatar_colunas(MODELO / "definition")
        print(f"[OK] Formatos de coluna: {', '.join(feitas) if feitas else 'nenhum (já aplicados)'}")
        if not (args.adicionar_medidas or args.atualizar_medidas):
            sys.exit(0)

    if args.adicionar_medidas or args.atualizar_medidas:
        schemas = {t: dict(pl.read_parquet_schema(DADOS / f"{t}.parquet")) for t in TABELAS}
        medidas = ler_medidas()
        conferir(schemas, medidas)
        arquivo = MODELO / "definition" / "tables" / "_Medidas.tmdl"
        if args.adicionar_medidas:
            novas = adicionar_medidas(arquivo, medidas)
            print(f"[OK] Medidas acrescentadas: {', '.join(novas) if novas else 'nenhuma (todas já existem)'}")
        if args.atualizar_medidas:
            print(f"[OK] Medidas atualizadas: {', '.join(atualizar_medidas(arquivo, medidas, args.atualizar_medidas))}")
        sys.exit(0)

    if not (MODELO / "definition.pbism").exists():
        if not args.pasta and (PASTA_PBI / "tcc_gasto_saeb.pbix").exists():
            sys.exit("[ERRO] O relatório em branco foi salvo como .pbix (arquivo único), e o gerador precisa do projeto "
                     ".pbip (pastas). Abra o .pbix no Power BI e use Arquivo > Salvar como, com o Tipo 'Arquivos de "
                     "projeto do Power BI (*.pbip)', na mesma pasta powerbi\\, com o nome tcc_gasto_saeb. Feche o Power "
                     "BI e rode o gerador de novo.")
        sys.exit(f"[ERRO] Não achei {MODELO / 'definition.pbism'}. Salve antes um relatório em branco como "
                 "powerbi/tcc_gasto_saeb.pbip no Power BI Desktop (roteiro, Fase 1) e feche o Power BI.")
    definicao = MODELO / "definition"
    if (definicao / "tables").exists() and any((definicao / "tables").iterdir()) and not args.forcar:
        sys.exit("[ERRO] O modelo já tem tabelas: depois da criação, o Desktop é a fonte. Use --forcar para recriar "
                 "(as mudanças feitas no Desktop seriam perdidas).")

    schemas = {t: dict(pl.read_parquet_schema(DADOS / f"{t}.parquet")) for t in TABELAS}
    medidas = ler_medidas()
    conferir(schemas, medidas)

    original_model = (definicao / "model.tmdl").read_text(encoding="utf-8") if (definicao / "model.tmdl").exists() else None
    original_db = (definicao / "database.tmdl").read_text(encoding="utf-8") if (definicao / "database.tmdl").exists() else None
    if definicao.exists():
        shutil.rmtree(definicao / "tables", ignore_errors=True)
    (definicao / "tables").mkdir(parents=True, exist_ok=True)
    # projeto salvo em TMSL (model.bim): passa para TMDL
    if (MODELO / "model.bim").exists():
        (MODELO / "model.bim").unlink()
    pbism = (MODELO / "definition.pbism").read_text(encoding="utf-8")
    pbism = re.sub(r'"version":\s*"[0-3]\.\d+"', '"version": "4.0"', pbism)
    (MODELO / "definition.pbism").write_text(pbism, encoding="utf-8")

    (definicao / "database.tmdl").write_text(original_db or "database\n\tcompatibilityLevel: 1567\n", encoding="utf-8")
    (definicao / "model.tmdl").write_text(model_tmdl(original_model), encoding="utf-8")
    caminho = str(DADOS)
    (definicao / "expressions.tmdl").write_text(
        f'expression PastaDados = "{caminho}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"\tlineageTag: {tag('e', 'PastaDados')}\n\n\tannotation PBI_ResultType = Text\n", encoding="utf-8")
    (definicao / "relationships.tmdl").write_text("\n".join(
        f"relationship {tag('r', a, b)}\n\tfromColumn: {a}\n\ttoColumn: {b}\n" for a, b in RELACOES), encoding="utf-8")
    for t in TABELAS:
        (definicao / "tables" / f"{t}.tmdl").write_text(tabela_importada(t, schemas[t]), encoding="utf-8")
    for t, (dax, cols) in CALCULADAS.items():
        (definicao / "tables" / f"{t}.tmdl").write_text(
            tabela_calculada(t, dax, cols, medidas if t == "_Medidas" else []), encoding="utf-8")

    print(f"[OK] Modelo gravado em {definicao}")
    print(f"     {len(TABELAS)} tabelas importadas + {len(CALCULADAS)} calculadas, {len(RELACOES)} relações, "
          f"{len(medidas)} medidas, {len(ORDENAR)} ordenações")
    print(f"     PastaDados = {caminho}")
    print("[PRÓXIMO] Abra powerbi/tcc_gasto_saeb.pbip no Power BI Desktop e clique em Página Inicial > Atualizar.")
