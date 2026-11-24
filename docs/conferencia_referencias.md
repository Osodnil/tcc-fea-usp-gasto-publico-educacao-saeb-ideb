# Conferência das referências no Crossref

*2026-11-24. A lista de referências do documento principal (`exportacao/TCC_II_FEA_USP_Versao_Final-Revisado5.docx`) foi
comparada, item a item, com os dados oficiais do Crossref (e do DataCite, para o pacote de software). Esta conferência
verifica se a obra existe e se os dados bibliográficos estão certos. Ela não verifica se o texto do TCC descreve bem o
que cada obra diz: isso é a pendência (b) da etapa 3.*

## Resumo

| Situação | Quantas |
|---|---|
| Confere (Crossref, DataCite ou, no caso de Lourenço et al., o site da revista) | 21 |
| Precisa de correção ou complemento | 6 |
| Livro sem registro no Crossref, com dados coerentes com a edição conhecida | 5 |
| Leis, dados oficiais, modelos de IA e documentos institucionais (fora do escopo do Crossref) | 27 |
| **Total** | **59** |

**Conferência nos dois sentidos:** toda referência da lista é citada no texto, e toda citação do texto está na lista.

## O que corrigir (✅ aplicado em 2026-11-24 por `src/Exportacao/Corrigir_Referencias.py`, A33)

1. **Crozatti et al. (2022)**
   - O quinto autor está registrado como **Rinaldi, Aryane Manfron Serpa**, e não "Serpa, A. M.". Na lista, fica "Rinaldi, A. M. S.". Confira no PDF do artigo.
   - Faltam as páginas: **143–171**.
2. **Alves e Frio (2022):** faltam as páginas: **285–312**.
3. **Mazzon (2018):** falta o DOI: https://doi.org/10.5585/bjm.v17i5.4175.
4. **Sasso et al. (2021):** falta o DOI: https://doi.org/10.1590/S1413-24782021260071.
5. **Soares e Xavier (2013):** trocar o link do PDF no SciELO pelo DOI: https://doi.org/10.1590/S0101-73302013000300013.
6. **Menezes-Filho e Amaral (2009)**, resolve a marca [CONFERIR]:
   - o trabalho saiu na série de working papers do Insper;
   - o arquivo oficial se chama `2009_wpe164.pdf`, o que indica **Insper Working Paper WPE 164**;
   - os catálogos divergem: há registros como wpe_156 e como 064 (Business and Economics Working Papers);
   - sugestão: "(Insper Working Paper No. WPE 164)", conferindo o número na capa do PDF.

## Complementos opcionais

- **Heald (2006):** o capítulo tem DOI (https://doi.org/10.5871/bacad/9780197263839.003.0002), e pode ser acrescentado.
- **Silva Júnior et al. (2025):** páginas 1–21.
- **Lourenço et al. (2017):** não está no Crossref, mas o artigo existe (Contabilidade Vista & Revista, 28(1), 89–116, UFMG), e os dados batem.

## Sem registro no Crossref (normal para livros)

Banco Mundial (2017), Davenport e Harris (2007), Few (2006), Moore (1995) e MacQueen (1967). São obras conhecidas, e
os dados da lista (editora, ano e, no caso de MacQueen, as páginas 281–297 dos anais de Berkeley) correspondem às
edições usuais.

## Fora do escopo

As leis (Brasil, Ceará, Minas Gerais), as bases de dados (Inep, IBGE, FNDE, Tesouro, Radar IDHM), os modelos de IA
(Anthropic, Google), o manual do departamento e os documentos institucionais (Ipea, Iede, TCE-SP, Edunomics) não são
indexados pelo Crossref. Continuam pendentes as ementas das leis estaduais (A31) e a autoria do Radar IDHM, ambas
marcadas no documento.
