# Revisão de formatação e referências

> **Situação em 2026-11-18 (A26):** a versão final está em `exportacao/TCC_II_FEA_USP_Versao_Final.docx`, sem as notas amarelas.
> - **Já resolvidos:** chefe do departamento (A29) e agradecimentos do Henrique (2026-11-24); título único; página de opções e dedicatória removidas; sumário e listas automáticos; títulos das listas no corpo; lista de siglas; resumo e abstract; marcações da Introdução; citações institucionais na forma da APA; "(Inep, 2026b)".
> - **Restam:** o número do texto de Menezes-Filho e Amaral (2009), a autoria do Radar IDHM, a revisão ortográfica, o Turnitin e, da etapa 3, a reescrita com as próprias palavras e a revisão das paráfrases.
> - **Cuidado:** depois que vocês começarem a editar a versão final no Word, não gerar de novo pelo montador, para não sobrescrever as edições. Para refazer o sumário e as listas, usar no Word o botão direito > Atualizar campo, ou rodar `src/Exportacao/Atualizar_Campos.ps1`.

*2026-11-17 (registro A21). Revisão inicial do rascunho do TCC II (`TCC_II_FEA_USP_Rascunho.docx`) e da cópia com o conteúdo técnico (`exportacao/TCC_II_FEA_USP_Rascunho_com_conteudo.docx`).*

## 1. Qual norma vale para quê

| Item | Norma | Origem |
|---|---|---|
| Citações no texto e lista de referências | **APA 7** | Manual de TCC ADM 2025 da FEA/USP: APA obrigatória a partir de 2026. A nota do próprio rascunho diz que o modelo de 2026 aceita APA ou ABNT, e a APA já é a usada no texto. |
| Formatação do documento (papel, margens, fonte, espaçamento, paginação, títulos, ilustrações) | **ABNT NBR 14724** | O Manual remete às diretrizes da USP para teses e dissertações, que seguem a ABNT para a apresentação do trabalho. |
| Resumo e abstract | ABNT NBR 6028 | Mesma origem. |

**Resumo:** a formatação segue a ABNT, e as citações e as referências seguem a APA. Não se usa a referência no padrão ABNT ("SOBRENOME, Nome. **Título**...").

## 2. Já aplicado na cópia

- **Margens:** 3 cm na superior e na esquerda, 2 cm na inferior e na direita, em todas as seções. Nas páginas pré-textuais do rascunho, a margem inferior era de 0,5 cm, e a direita, de 1,75 cm.
- **Número da página:** campo automático no canto superior direito, a 2 cm da borda. No rascunho, o cabeçalho trazia um "10" digitado, que se repetia em todas as páginas.
- **Figuras:** título acima da imagem ("Figura N – Título"), e fonte e eventual nota abaixo. Na versão anterior da cópia, o título ficava embaixo.
- **Tabelas e quadros:** título acima e fonte abaixo; o texto das células em tamanho 9, e a fonte em tamanho 10. Desde a auditoria de 2026-11-17, as **tabelas** seguem a apresentação tabular do IBGE, a que a ABNT remete: abertas nas laterais, só com os traços de cima, de baixo e sob o cabeçalho, sem grade interna. Os **quadros** continuam fechados. Toda tabela tem "Fonte:" logo abaixo e, depois, a "Nota:" (nas Tabelas 3 a 7, a fonte faltava e só havia a nota).
- **Capa e folha de rosto:** com a margem inferior de 2 cm, "São Paulo 2026" tinha passado para uma página a mais nas duas. Saíram cinco linhas em branco antes de cada um, e cada uma voltou a caber numa página.
- **Corpo do texto:** Times New Roman 12, espaçamento de 1,5, justificado, com recuo de 1,25 cm na primeira linha. A auditoria não achou nenhum parágrafo do corpo fora desse padrão.
- **Idioma:** português do Brasil. O documento estava marcado como português de Portugal, o que atrapalha o corretor ortográfico.
- **Referências:** lista final única em APA 7, com recuo deslocado de 1,25 cm, espaço simples e uma linha em branco entre as referências (ver seção 4).
- **Capítulos:** títulos trocados para o formato de método científico (D1), com notas onde o texto ainda precisa mudar.
- **Enxugamento (A22):** as figuras que repetiam tabelas saíram; telas, clusters, duas tabelas e as fichas dos casos foram para o novo Apêndice B. Figuras e tabelas foram renumeradas.
- **Figuras:** o título fica no mesmo parágrafo da imagem, para os dois não se separarem entre páginas.

## 3. A fazer à mão no documento oficial

### 3.1 Elementos pré-textuais
1. [ ] **Título do trabalho:** escolher entre as opções da capa, tirar a página com as três opções e as marcas "[REVISAR]". Hoje, a capa diz "Eficiência do Gasto Público...: Proposição de um Modelo Analítico de BI", e a folha de rosto traz outro título ("Business Intelligence para a gestão do financiamento..."): os dois precisam ser iguais. O título não deve falar em "eficiência" (D2) nem em proposição de modelo para a gestão, já que o formato é científico (D1).
2. [ ] **Sumário automático:** hoje ele está digitado, com números de página fixos, que já não batem com o texto. No Word, usar Referências > Sumário, depois de aplicar os estilos de título.
3. [ ] **Listas de figuras, tabelas e quadros automáticas:** também estão digitadas. Para gerá-las, os títulos das ilustrações precisam do estilo Legenda (Referências > Inserir Legenda).
4. [ ] **Títulos "SUMÁRIO", "LISTA DE FIGURAS", "LISTA DE TABELAS" e "LISTA DE QUADROS":** estão dentro do cabeçalho da página, um resto da conversão do modelo. Devem ir para o corpo, centralizados, em negrito e em maiúsculas, sem numeração.
5. [ ] **Paginação:** pela ABNT, as folhas são contadas a partir da folha de rosto, e o número só aparece a partir da Introdução. Na cópia, a Introdução sai como página 13. Conferir se essa contagem bate com o número de folhas desde a folha de rosto, sem contar a capa.
6. [ ] **Resumo e abstract (hoje vazios, só com instruções):** de 150 a 500 palavras, em parágrafo único, com 3 a 5 palavras-chave separadas por ponto. Precisam refletir o formato científico, o indicador "desempenho em relação ao esperado" e os resultados principais. Retirar a simulação de cenários e o VAAR.

7b. [ ] **Lista de abreviaturas e siglas:** é opcional na ABNT, mas o texto usa muitas (SIOPE, SICONFI, Saeb, Ideb, IDHM, MDE, VAAF, VAAT, VAAR, Inep, FNDE, IBGE, IPCA, MQO, EF, UF). Recomendado incluir, depois das listas de ilustrações.
7c. [ ] **Palavras-chave:** tirar "Eficiência do gasto" e pôr, por exemplo, "Desempenho educacional" (D2).

7d. [ ] **Sumário digitado:** ainda lista o antigo Capítulo 3 (Diagnóstico) e o item 2.2; some ao gerar o sumário automático.

### 3.2 Texto
7. [x] **Capítulo 3 (Diagnóstico):** remanejado na cópia em 2026-11-17 (A23), com as remissões já ajustadas. Falta o Guilherme revisar a redação.
8. [ ] **Objetivos e item 2.1.4:** alinhar ao que foi feito. Não há simulação de cenários nem monitoramento do VAAR, e o indicador é o desempenho em relação ao esperado.
9. [ ] **Citações longas:** a APA usa citação em bloco a partir de 40 palavras, e a ABNT, a partir de três linhas. Como a citação segue a APA, usar 40 palavras, com o leiaute da ABNT: recuo de 4 cm, fonte 10, espaço simples e sem aspas.
10. [ ] **Notas amarelas e marcas:** retirar todas as notas, "[INSERIR]", "[CONFERIR]" e "RASCUNHO TÉCNICO" antes da entrega.
11. [x] **Telas do painel:** capturadas de novo em 2026-11-17, já com o nome "Desempenho". Depois do enxugamento (A22), três estão no texto (Figuras 2 a 4), uma é a de Pares de Timon (Figura 7), e as outras estão no Apêndice B (Figuras B.1 a B.7 e B.10 a B.12).
11b. [ ] **Lista automática de figuras:** na cópia, o título de cada figura está no mesmo parágrafo da imagem, separado por uma quebra de linha, para não ficar sozinho no pé da página. Ao gerar a lista automática de figuras no Word, aplicar o estilo Legenda só ao título, ou manter a lista digitada.
12. [ ] **Revisão ortográfica:** passar o corretor, que agora está em português do Brasil.

### 3.3 Citações no texto (APA)
13. [ ] **Ideb:** trocar "(Inep, 2026)" por "(Inep, 2026b)". A lista final tem dois itens do Inep: 2026a, o Censo Escolar, e 2026b, o Ideb.
14. [ ] **Três ou mais autores:** usar "et al." desde a primeira citação, como em "(Jackson et al., 2016)" e "(Lautharte et al., 2021)".
15. [ ] **"&" ou "e":** dentro dos parênteses, usar "&", como em "(Davenport & Harris, 2007)"; na frase, usar "e", como em "Davenport e Harris (2007)".
16. [ ] **Autores institucionais:** na primeira citação, escrever o nome por extenso e a sigla entre colchetes, como em "(Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira [Inep], 2026b)"; depois, só "(Inep, 2026b)". Vale também para FNDE, IBGE e PNUD. Hoje, a fonte do Quadro 3 usa as siglas direto.
17. [ ] **Toda citação na lista, e toda referência citada:** conferir nos dois sentidos antes da entrega.

### 3.4 Entrega
18. [ ] **Turnitin:** submeter pela Biblioteca da FEA e enviar o relatório à orientadora, como recomenda o Manual.
19. [ ] **Declaração de uso de IA:** decidir onde entra (Método, nota ou apêndice), conforme a orientadora.

## 4. Lista de referências

- **Composição:** a lista final da cópia tem 44 obras: as do rascunho, as dos capítulos 3 e 4, a ferramenta de IA (Anthropic, 2026) e as 12 do levantamento citadas na revisão bibliográfica (A24). A ordem alfabética é aplicada pelo script. São as 19 do rascunho (com o Ideb do Inep fundido ao item já existente) e as citadas nos capítulos 4 e 5: as bases de dados, o pacote educabR, Lautharte et al. (2021), MacQueen (1967) e Rousseeuw (1987).
- **DOIs acrescentados:** Cairney (2016), Hanushek (1997), Jackson et al. (2016), Janssen et al. (2012) e Sackett et al. (1996).
- **Ainda a conferir:**
  - a ementa da Lei nº 14.276/2021;
  - a autoria da edição usada do Radar IDHM;
  - as datas de acesso das bases de dados, se a orientadora pedir. A APA 7 só pede data de acesso para conteúdo que muda sem versão;
  - qual Hanushek usar: o rascunho cita o de 1997, e o levantamento localizou o de 2003.
- **Candidatas do levantamento bibliográfico** (`docs/levantamento_bibliografico.md`): entram na lista só quando forem citadas, e depois de lido o texto completo, e não só o resumo. Para a revisão bibliográfica (Guilherme), as mais ligadas aos resultados são:
  - Menezes-Filho e Amaral (2009);
  - Oliveira, Menezes Filho e Komatsu (2022);
  - Alves e Frio (2022);
  - Hirata, Melo e Oliveira (2022);
  - Jackson e Mackevicius (2024);
  - Alves e Soares (2013);
  - Soares e Xavier (2013).
