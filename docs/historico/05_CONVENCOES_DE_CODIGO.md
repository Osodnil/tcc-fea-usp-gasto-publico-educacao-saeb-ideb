# 05 — Convenções de código, ambiente e lições aprendidas

## 1. Ambiente

- Windows, PowerShell, Anaconda. Python: `C:\Users\lindo\anaconda3\python.exe`.
- Rodar scripts com `& C:\Users\lindo\anaconda3\python.exe caminho\script.py`.
- **Instalar pacotes sempre com o mesmo Python que roda o script:** `C:\Users\lindo\anaconda3\python.exe -m pip install <pacote>`. Um `pip install` solto caiu em outro Python (o da Microsoft Store) e o script falhou com `ModuleNotFoundError`.
- Bibliotecas em uso: `polars` (versão recente: tem `unpivot`, `replace_strict`, `collect_schema`, `sink_parquet`), `requests`, `xlsxwriter` (para exportar Excel de conferência). Excel lido com `pl.read_excel`; `sheet_id=0` devolve um dicionário nome da aba → DataFrame nesta versão.
- Repositório: `C:\Users\lindo\OneDrive\Documentos\GitHub\ENEM_Microdata_Analysis`. O nome é da fase ENEM; o projeto agora é de gasto x Saeb.

```
ENEM_Microdata_Analysis/
├── .git/
├── data/
│   ├── raw/        # downloads manuais (ENEM, IDEB, Censo Escolar, IBGE, IDHM, ...)
│   ├── interim/    # parquets extraídos e transformados
│   │   └── diagnosticos/   # saídas grandes de diagnóstico (CSV)
│   └── processed/  # base final para o Power BI
├── src/
│   ├── Extract/
│   └── Transform/
└── docs/           # dossiê do projeto (fonte da verdade, cópia no Claude)
```

## 2. Padrões dos scripts

1. **Raiz do projeto:** todo script começa com a função que sobe a árvore de pastas até achar `.git`, em vez de cadeias de `.parent`. Isso evita quebra quando o script muda de pasta.

```python
def encontrar_raiz_projeto(marcador: str = ".git") -> Path:
    atual = Path(__file__).resolve().parent
    while atual != atual.parent:
        if (atual / marcador).exists():
            return atual
        atual = atual.parent
    raise FileNotFoundError(f"Não foi possível localizar a raiz do projeto (marcador '{marcador}').")
```

2. **Polars, não pandas.** CSVs grandes com `pl.scan_csv(..., separator=";", encoding="utf8-lossy", infer_schema_length=0)` e `sink_parquet`. Ler tudo como texto e converter depois, de forma explícita (`cast(pl.Float64, strict=False)`: '-' e 'ND' viram nulo).
3. **Dicionários de JSON em DataFrame:** `pl.DataFrame(registros, infer_schema_length=None)`. Sem isso, um texto como "Valores sujeito alterações" fora da amostra inicial derruba a leitura.
4. **Um arquivo por ano, nome previsível:** `enem_{ano}_extraido.parquet`, `siope_{ano}_extraido.parquet`, `siope_funcao_{ano}_extraido.parquet`, `censo_matriculas_{ano}.parquet`, `saeb_municipios_{etapa}.parquet`, `saeb_ufs_{etapa}.parquet`. Intermediários em Parquet em `data/interim/`.
5. **Nunca sobrescrever em silêncio.** Ao localizar arquivos por padrão de nome, travar se houver mais de um candidato por ano. Gravar em `.tmp` e renomear só ao terminar; ao reexecutar, validar o parquet existente (abre e tem linhas) antes de pular o ano.
6. **Busca tolerante de pastas e arquivos:** comparar nomes sem acento e sem diferenciar maiúsculas (`unicodedata.normalize("NFKD", ...)`), com `rglob`.
7. **Excel com cabeçalhos mesclados:** ler com `read_options={"header_row": None}`, achar a linha com mais nomes técnicos (como `VL_NOTA_MEDIA_2017`) e promovê-la a cabeçalho. A opção `header_row` do Polars não se comportou como esperado.
8. **Saídas pequenas no terminal.** O buffer do terminal trunca prints longos em silêncio. Diagnósticos grandes vão para CSV em `data/interim/diagnosticos/`; no console, só resumos.
9. **Mensagens padronizadas:** `[INFO]`, `[AVISO]`, `[OK]`, `[ERRO]`, `[FALTA]`, `[DIAGNÓSTICO]`.
10. **Descobrir antes de assumir:** para qualquer fonte nova, rodar primeiro um script de reconhecimento (lista de entidades, colunas, anos disponíveis, valores distintos). Não presumir nomes de coluna, códigos de categoria nem endpoints.
11. **Diagnóstico de nulos e rodapés** antes de dar um Transform como fechado (proporção de nulos por coluna e ano; linhas de nota de rodapé do Excel).
12. **APIs:** pausa curta entre chamadas, três tentativas com espera crescente, distinguir erro de API (`None`) de resposta vazia (`[]`), seguir a paginação (`@odata.nextLink` no SIOPE; `offset` e `hasMore` no SICONFI).
13. **Scripts entregues sempre completos**, com nome e pasta sugeridos, prontos para colar.

## 3. Lições aprendidas (bugs já vistos)

| Problema | Causa | Solução |
|---|---|---|
| Disco cheio na extração do ENEM | Dados brutos dentro do OneDrive | Liberar espaço; gravar com `.tmp` |
| Saída de 2023–2025 do Censo Escolar corrompida sem erro | Mais de um CSV por ano gerava o mesmo nome de saída | Lista de padrões permitidos e travada se houver mais de um arquivo |
| Linhas de rodapé do Excel como dados (IDHM) | Notas de fonte na planilha | Lista positiva de territórios válidos |
| `IDHM_EDUCACAO` como texto | Herdado da extração | Converter todas as métricas para `Float64` |
| `header_row` do Polars lia a linha errada | Cabeçalho multilinha e mesclado | Promover a linha manualmente |
| SIOPE falhou na leitura de 2018 | Texto "Valores sujeito alterações" fora da amostra de inferência de tipo | `infer_schema_length=None` |
| 2015 vazio no SIOPE | A API só tem dado desde 2017 | Sondar anos antes de extrair |
| Divisão por zero no resumo do SIOPE | Despesa total igual a zero em 41 linhas | `pl.when(den > 0)`; contar e documentar |
| UFs abreviadas no Saeb ("M. G. do Sul" etc.) | Rótulos do arquivo do Inep | Mapa `ALIAS_UF` antes de classificar |
| `ModuleNotFoundError: xlsxwriter` | `pip` instalou em outro Python | `python.exe -m pip install ...` |
| Prévia de cruzamento SIOPE x IDEB quase vazia | SIOPE mede gasto da prefeitura; IDEB do Médio é da rede estadual | Pareamento por camada (Opção D) |
| Script de diagnóstico sobrescreveu o de extração | Mesmo nome de arquivo | Nomear diagnósticos como `Teste*` ou `Diagnostico_*` e extrações como `Extract_*` |

## 4. Mapa dos scripts (nomes sugeridos)

| Script | Função |
|---|---|
| `src/Extract/Extract_ENEM.py` | ENEM 2013–2023 → parquet por ano (herdado) |
| `src/Extract/Extract_IDHM.py` | IDHM por UF (herdado) |
| `src/Extract/Extract_IDEB.py` | IDEB do Médio, só `VL_OBSERVADO` (herdado) |
| `src/Extract/Extract_Censo_Escolar.py` | Infraestrutura por escola (herdado) |
| `src/Extract/Extract_IBGE.py` | Alfabetização municipal, Censo 2022 (herdado) |
| `src/Extract/Extract_SIOPE.py` | SIOPE `Dados_Gerais_Siope`, camada municipal, 2017–2025 |
| `src/Extract/Extract_SIOPE_Funcao.py` | SIOPE por subfunção, camadas municipal e estadual |
| `src/Extract/Extract_SICONFI_Estados.py` | DCA Anexo I-E dos estados, função 12, 2014–2025 |
| `src/Extract/Extract_Censo_Matriculas.py` | Matrículas por município × rede (inclui `QT_MAT_BAS`) |
| `src/Extract/Extract_IPCA.py` | Deflator anual (base 2025) |
| `src/Extract/Extract_Saeb.py` | Saeb/IDEB municipal (EM, AI, AF) e por UF |
| `src/Transform/Transform_*.py` | IDHM, IDEB, Censo Escolar e IBGE (herdados, já rodados) |
| `Teste*.py`, `Sondagem_SIOPE.py`, `Visualização_SIOPE.py` | Diagnósticos e conferências; `Teste9` importa de `Teste8_Reconciliacao` |

O inventário gerado por `Gerar_Pacote_Migracao.py` (`CODIGO_PIPELINE.md`) mostra os nomes reais, com a data de modificação de cada arquivo.

## 5. Estilo de trabalho combinado

- Português do Brasil, tom direto. Explicar em poucas linhas por que cada teste é necessário.
- Ao receber uma saída de terminal: separar o que funcionou, o que é erro de código e o que é achado sobre os dados; só então propor o próximo passo.
- Corrigir os próprios erros às claras.
- Decisões de escopo: opções com prós e contras, uma recomendação e o que depende da orientadora.
- Dizer o que foi verificado e o que não foi; citar a fonte ao afirmar fatos sobre bases externas.
- Falar em associação e eficiência, nunca em causalidade.
