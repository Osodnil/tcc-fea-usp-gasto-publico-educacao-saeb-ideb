# Revisão geral do projeto

*2026-11-11. Revisão do que foi construído contra o que era esperado, feita com o painel e a fase de análise concluídos. Cada item traz a evidência e o que fazer. Nada foi alterado nesta revisão.*

## Situação depois da revisão (2026-11-11)

Corrigido no mesmo dia, por não depender da orientadora:
- **2.2:** a frase da correlação de 0,01 saiu do painel e da nota de método; no lugar, o achado do modelo (+10% no gasto acompanha +0,2 ponto dentro do município). O título da dispersão da página Eficiência ficou descritivo.
- **2.4:** o glossário de Defasagens perdeu a explicação "o aluno acumula anos de escola" e ganhou a linha "Gasto antigo".
- **3.1:** 12 medidas removidas (de 97 para 85). Ficaram 5 sem uso em visual, por serem indicadores formais à espera de D2: `IDEB médio`, `Nota padronizada N média`, `Nota menos a mediana do cluster`, `Gasto ÷ mediana do cluster` e `Redes com gasto extremo`.
- **3.5:** `run_pipeline.py --com-analise` roda os modelos e o material do texto; `matplotlib` entrou no `requirements.txt`.
- **3.7 e seção 4:** README, especificação do dashboard (versão 2), nota de método, lista de pendências e a página "Sobre os dados" atualizados; o roteiro de construção foi marcado como histórico. Sobre a nota de método, a revisão exagerou: ela já trazia o % do esperado (A10), e só a frase da correlação precisava sair.

Seguem abertos, para a orientadora: 2.1, 2.3, 2.5, 3.2 (regra dos saltos) e 3.3; e a seção 4.1 do resumo, que depende das respostas dela na reunião já feita.

## 1. O que está sólido

- **Dados:** as chaves dos painéis são únicas (município × etapa × edição; UF × etapa × edição; e a tabela de desempenho por disciplina). As contagens batem com a especificação: 93.630 linhas, 82.390 com proficiência, 65.084 com eficiência nacional, 82.260 com eficiência no mesmo estado, 633 saltos. Não há gasto zero ou negativo, e 2025 não tem IDHM, como decidido (C1).
- **Inflação:** `src/Testes/Conferir_Inflacao.py` passa: as 16 colunas de gasto e as 9 usadas nas medidas estão em R$ de 2025.
- **Painel:** as 10 páginas validam contra os esquemas oficiais, e nenhum texto é estimado como cortado. As 97 medidas de `medidas.dax` são as mesmas 97 do modelo.
- **Modelos:** o MQO agrupado do modelo principal reproduz exatamente o modelo da eficiência (coeficiente, N e R²), e a especificação de referência reproduz o teste da investigação de 2025.

## 2. Incoerências de ideia (as mais importantes)

### 2.1 O indicador chamado "eficiência" quase não depende do gasto
- **Evidência:** no modelo nacional que gera a nota esperada, o coeficiente do log do gasto é 0,92 (p = 0,20) em AI Matemática: dobrar o gasto muda a nota esperada em 0,6 ponto. A nota esperada é, na prática, a esperada **para o contexto**.
- **Consequência:** o painel diz "esperado para o gasto e o contexto", mas o que ele mede é o desempenho ajustado ao contexto. O nome "eficiência" sugere resultado por real gasto, e não é isso.
- **O que fazer:** decidir com a orientadora entre (a) manter o nome e explicar no Método que o gasto entra no modelo mas pesa pouco, ou (b) chamar o indicador de "desempenho em relação ao esperado" (o rótulo "vs. esperado" já vai nessa direção).

### 2.2 "Gastar mais não garante eficiência (correlação de 0,01)" é verdade por construção
- **Evidência:** o resíduo de uma regressão que inclui o log do gasto é, por construção, não correlacionado com o log do gasto. A frase está no glossário da página Eficiência, na nota de método e no registro (reunião de 06/11), apresentada como achado. O título da dispersão ("há redes acima e abaixo do esperado em todo nível de gasto") tem o mesmo problema.
- **O que fazer:** trocar a frase por um achado de verdade, que agora existe: "dentro do mesmo município, +10% no gasto acompanha +0,2 ponto" (A11).

### 2.3 Duas réguas convivem, e a "oficial" não é a mais usada
- **Evidência:** a decisão A8 define a comparação nacional com IDHM como oficial e a do mesmo estado como robustez. Mas: o mapa abre no mesmo estado; 2025 só existe no mesmo estado; os pares no mesmo estado ficam na mesma UF; e o modelo principal (A11) adotou como referência a comparação dentro do estado e da edição. No modelo do mesmo estado, o gasto pesa mais (4,3, p < 0,001) e o ajuste é melhor (R² de 0,52 contra 0,39).
- **O que fazer:** levar à orientadora a pergunta "qual é a régua principal do trabalho?". Se for a do mesmo estado, A8 muda, o padrão dos filtros muda, e 2025 deixa de ser exceção.

### 2.4 A página Defasagens conta uma história que o modelo não confirma
- **Evidência:** a página mostra o ρ simples crescendo com a defasagem, e o glossário explica: "o aluno acumula anos de escola". O modelo com efeito fixo mostra o contrário: dentro do município, contam o gasto do ano da prova e o do anterior; o de 2 e 4 anos antes não se associa (A11).
- **O que fazer:** no painel, tirar a explicação causal do glossário e dizer que o ρ com gasto antigo reflete diferenças persistentes entre municípios. No texto, apresentar os dois resultados lado a lado.

### 2.5 Os resultados dos modelos não estão no painel
- **Evidência:** a primeira pergunta da Boas-vindas é "Gastar mais se associa a aprender mais?", e leva à página Defasagens, que só tem a correlação simples. O efeito fixo, a heterogeneidade e a sensibilidade estão só em `docs/`.
- **O que fazer:** decidir se o painel é só descritivo (e dizer isso) ou se ganha um quadro com o resultado principal.

## 3. Incoerências de dados e de construção

| # | Achado | Evidência | O que fazer |
|---|---|---|---|
| 3.1 | **17 medidas sem uso** no modelo | não aparecem em nenhum visual nem em medida usada: `Marca de salto`, `Par: salto`, `Par: percentil`, `Par: diferença (p.p.)`, `Par: diferença para a referência`, `Par: eficiência`, `Comparado: eficiência`, `Eficiência do município de referência`, `Gasto por aluno da época (mediana anual)`, `Gasto estadual por aluno (mediana, versão B)`, `Aviso de salto atípico`, `Aviso de seleção`, `Gasto ÷ mediana do cluster`, `Nota menos a mediana do cluster`, `IDEB médio`, `Nota padronizada N média`, `Redes com gasto extremo` | remover as que sobraram das revisões; manter as de indicadores formais (IDEB, N) só se D2 as confirmar |
| 3.2 | **Nota implausível** | Santana do Mundaú (AL), AF, 2023: 404,9 em Matemática, acima de qualquer rede do país; está marcada como salto (S11), mas entra nos modelos | confirmar a regra S11 e citar o caso; o teste "sem saltos atípicos" já mostra que não muda a conclusão |
| 3.3 | **Eficiência usa só o gasto do ano** | A11 e A4 mostram que o gasto médio do biênio mede melhor o ciclo (coeficiente 60% maior) | avaliar se a nota esperada do painel passa a usar o gasto do biênio; hoje há uma pequena incoerência entre indicador e modelo |
| 3.4 | **Clusters presos à região** | o IDHM é da UF, e os clusters saem regionais (gráfico novo de Contexto); pares "nacionais" são, na prática, regionais | já registrado; reforçar no Método |
| 3.5 | **Scripts de análise fora do pipeline** | `run_pipeline.py` para em `Eficiencia.py`; os cinco scripts novos e `Material_Texto.py` rodam à mão; `matplotlib` não está em `requirements.txt` | incluir no pipeline (ou numa opção `--analise`) e no `requirements.txt` |
| 3.6 | **Caminho pessoal no modelo** | `PastaDados` em `expressions.tmdl` aponta para a pasta do usuário de Henrique | previsto (troca-se o parâmetro), mas vale citar no roteiro de publicação |
| 3.7 | **Arredondamento** | o registro A11 traz 2,48 para o EF de 2017–2023; a Tabela 3 mostra 2,47 (valor 2,475) | alinhar o registro à tabela |

## 4. Documentos desatualizados

| Documento | O que está velho |
|---|---|
| `README.md` | "formato de consultoria" (D1 aponta para método científico); "9 páginas (Início, …)"; "12 tabelas" (são 13, com `fato_oferta_municipal`); malha com chave `CD_MUN` (hoje "Nome (UF)"); estrutura de pastas sem `src/Analise`; "⏳ Testes de sensibilidade" (feitos); abertos sem os itens novos |
| `powerbi/especificacao_dashboard.md` | toda a seção 5: 9 páginas, eficiência em pontos, mapa em ±30 pontos, versão B em Estados, filtros; indicadores I7 e I8 sem o % do esperado (A10); "o `.pbip` (a criar)" |
| `powerbi/roteiro_construcao.md` | escrito antes dos geradores de páginas; conferir se ainda serve ou vira histórico |
| `docs/nota_metodo_eficiencia.md` | define a eficiência em pontos como principal; traz a frase da correlação de 0,01 (item 2.2) |
| `docs/decisoes_metodo.md` | lista de pendências da seção 9 (A4 ainda aparece como aberto); linha solta sobre o QR Code na seção 7b; A11 a A14 estão dentro da seção "Regras de análise", antes de S11; com 1.160 linhas, pede um índice |
| `docs/resumo_reuniao_orientadora.md` | a seção 4.1 está escrita como pauta de uma reunião futura; Henrique informou que a reunião já aconteceu, mas as respostas não estão registradas |
| Página "Sobre os dados" do painel | fala em "modelo oficial"; o resto do painel diz "comparação nacional" |

## 5. Formato esperado (Manual de TCC ADM 2025)

- **Formato (D1):** ainda não decidido com a orientadora. O conteúdo produzido é de **método científico, estudo quantitativo** (pergunta de descoberta, painel longitudinal, modelos). O README ainda diz consultoria. Essa decisão define a estrutura do texto e a rubrica de avaliação.
- **O que o Manual pede e o estado de cada parte:**

  | Parte | Estado |
  |---|---|
  | Introdução (questão, objetivos, contexto) | não há texto no repositório; pergunta central definida; as 6 perguntas analíticas seguem como rascunho não validado |
  | Revisão bibliográfica | **lacuna principal.** Não há revisão; as referências do documento original nunca foram verificadas (D4); a rubrica pesa autores relevantes e atuais, nacionais e internacionais |
  | Método | bem coberto pelo registro de decisões e pela nota de método; falta virar texto, com citação de autores para cada escolha (efeito fixo, clusters, deflação) |
  | Resultados e análise | material pronto (`docs/resultados/`, `docs/nota_resultados.md`); falta a discussão conectada à teoria |
  | Conclusões, limitações, pesquisa futura | limitações consolidadas (seção 10, L1 a L19); conclusões por escrever |
  | Referências em APA | por fazer (obrigatório a partir de 2026) |
  | Uso de IA (item 2.3) | rascunho pronto; **falta a aprovação da orientadora**, que o Manual exige antes do uso |
  | Avaliação com usuários (está no fluxo do README) | não feita; se envolver pessoas, pede TCLE e possivelmente comitê de ética |
  | Vídeo de até 7 minutos, por integrante | por fazer |
  | Turnitin | por fazer, com o texto |

- **Pontos do e-mail de 02/10 da orientadora (D2):** pergunta de pesquisa, perguntas analíticas, indicadores formais e unidade de análise ainda não foram respondidos nos termos do projeto atual. Hoje dá para responder todos.

## 6. Como prosseguir

1. **Reunião com a orientadora**, com esta ordem de assuntos: uso de IA (aprovação); formato (D1); régua principal e nome do indicador (itens 2.1 e 2.3); regra dos saltos (S11) e indicadores (D2); avaliação com usuários; QR Code.
2. **Arrumar a casa** (não depende da orientadora): atualizar README, especificação e nota de método; limpar as 17 medidas; pôr a análise no pipeline; corrigir os itens 2.2 e 2.4 no painel.
3. **Revisão bibliográfica**: é a maior lacuna para a nota. Verificar as referências já listadas e buscar a literatura de gasto × desempenho no Brasil (IDEB, Fundeb, eficiência municipal).
4. **Redação**: Método e Resultados a partir do registro e da nota de resultados; depois Introdução, Discussão e Conclusões.
5. **Fechamento**: publicação do painel e QR Code, vídeo, Turnitin.
