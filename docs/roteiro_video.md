# Roteiro do vídeo de apresentação do TCC

*2026-11-18; reescrito em 2026-11-25 contra o documento principal (Revisado5). Uma só apresentação, usada pelo Henrique
e pelo Guilherme, com o trabalho e a ferramenta em peso parecido: problema, legislação, literatura, método,
resultados, painel e conclusões. Etapa 6 do plano final. Os números conferem com o texto e com o painel publicado.*

## Regras do Manual (vídeo vale 20% da nota do TCC II)

- **Duração:** cerca de 5 minutos, no máximo 7.
- **Formato:** cada integrante grava o próprio vídeo, com os slides na janela grande e o rosto numa janela menor.
- **Entrega:**
  - o link do YouTube vai no **1º slide**;
  - o arquivo do PowerPoint, nomeado com os **nomes completos** dos autores, é postado no Moodle.
- **Este roteiro:** tem 12 slides e cerca de 920 palavras faladas, o que dá cerca de 6min35s em ritmo natural (140 palavras por minuto). Se o ensaio passar de 6min50s, encurte, nesta ordem, o slide 10 (alertas), a última frase do slide 4 e os exemplos do slide 9.
- **Slides com pouco texto:** o slide mostra só o número ou a palavra-chave; a explicação está na fala. Não leia o slide.
- **Uma apresentação para os dois:** as falas estão na primeira pessoa do plural e cobrem o trabalho todo, então o Henrique e o Guilherme podem usá-las do mesmo jeito. Só a primeira frase do slide 1 muda: cada um diz o próprio nome.

| Bloco | Slides | Tempo |
|---|---|---|
| Por que estudar (problema, legislação, literatura) | 1 a 4 | cerca de 2min |
| Como foi feito (dados, método, indicador) | 5 | cerca de 0:50 |
| O que encontramos | 6 e 7 | cerca de 1min20s |
| A ferramenta (painel) | 8 a 10 | cerca de 1min40s |
| Conclusões e fechamento | 11 e 12 | cerca de 1min |

---

## Slide 1 · Abertura (0:00–0:15)

**Na tela:** o título, os autores, a orientadora e FEA/USP, 2026. A gravação é feita sem o link do YouTube, que ainda não existe; o link entra no slide 1 só na versão postada no Moodle.

**Fala:**
> Olá, eu sou o Henrique Lindoso e vou apresentar o TCC que fiz com o Guilherme Menezes, sob orientação da professora Adriana Backx: "Gasto público por aluno e desempenho no Saeb: uma análise das redes públicas brasileiras com apoio de Business Intelligence".

*(O Guilherme troca a primeira frase por: "Olá, eu sou o Guilherme Menezes e vou apresentar o TCC que fiz com o Henrique Lindoso, …".)*

## Slide 2 · Problema e pergunta (0:15–0:50)

**Na tela:** "R$ 339 bi", "gasto e aprendizagem em sistemas separados" e a pergunta de pesquisa.

**Fala:**
> O Brasil gasta muito com educação básica: só o Fundeb teve receita estimada em 339 bilhões de reais em 2025. Mas o gestor público presta contas de quanto aplica e não tem um jeito simples de saber se esse dinheiro virou aprendizagem, porque os dados de gasto e os de aprendizagem estão em sistemas diferentes. Daí a nossa pergunta: o gasto público por aluno se associa ao desempenho das redes no Saeb? E, considerando o gasto e o contexto de cada rede, quais entregam mais ou menos do que o esperado?

## Slide 3 · Como a educação é financiada (0:50–1:35)

**Na tela:** uma rosca dupla sobre cada R$ 100 dos impostos da cesta. O anel interno mostra R$ 75 livres e R$ 25 para a educação. O anel externo abre os 25 em R$ 5 aplicados direto e R$ 20 do Fundeb: pelo menos R$ 14 para os profissionais (70%) e R$ 6 para outras despesas. Ao lado ficam a legenda, nessa mesma ordem, a nota "+23%: a União acrescenta ao Fundeb" e a faixa da cota do ICMS por resultados (no mínimo 10 pontos; no Ceará, 18%).

**Fala:**
> Primeiro, como a educação é financiada. A Constituição obriga estados e municípios a aplicar pelo menos 25% da receita de impostos na educação. Desses 25 pontos, 20 passam pelo Fundeb: em cada estado, 20% de uma cesta de impostos formam um fundo, que é repartido entre o estado e os municípios pelo número de matrículas, e a União complementa com pelo menos 23%. Pelo menos 70% do fundo paga os profissionais da educação. Além disso, desde a Emenda 108, de 2020, cada estado distribui parte do ICMS dos municípios segundo resultados educacionais, um modelo inspirado no Ceará.

## Slide 4 · O que a literatura diz (1:35–2:10)

**Na tela:** três ideias com os autores ("gasto sozinho explica pouco", "efeito maior para os mais pobres", "sem o contexto, redes vulneráveis parecem piores") e uma faixa com a lacuna.

**Fala:**
> Na literatura, os estudos clássicos, como os de Hanushek, e os brasileiros, como o de Menezes-Filho e Amaral, encontram uma associação pequena entre gasto e desempenho. Estudos recentes, como o de Jackson e coautores, mostram efeitos maiores sobretudo para os alunos de baixa renda. E Alves e Soares mostram que, sem considerar o contexto, as redes que atendem alunos mais vulneráveis parecem piores do que são. A lacuna é que são raras as ferramentas que permitem comparar, rede a rede, o gasto com o desempenho, levando em conta o contexto.

## Slide 5 · Dados, método e indicador (2:10–3:00)

**Na tela:** quatro etapas com palavras-chave (8 bases públicas, listadas em letra pequena: SIOPE, Siconfi, Saeb, Censo Escolar, Censo Demográfico, IDHM, IPCA e malha municipal → 2 comparações → indicador → painel em Power BI) e três números: "2017–2025", "~5.500 redes municipais", "27 redes estaduais".

**Fala:**
> Juntamos oito bases públicas: o SIOPE e o Siconfi, para o gasto; o Saeb, para a nota; e o Censo Escolar, o IBGE e o IDHM, para o contexto, de 2017 a 2025, com os valores corrigidos pela inflação. Comparamos os municípios entre si e cada município com ele mesmo ao longo do tempo. E criamos um indicador, o desempenho em relação ao esperado: a nota de cada rede comparada com a nota esperada para redes com o mesmo gasto e o mesmo contexto. Assim, uma cidade pequena do interior não é medida pela régua de uma capital. Os scripts foram desenvolvidos com o auxílio de IA, em acordo com a orientadora.

## Slide 6 · Resultado 1: o gasto, sozinho, explica pouco (3:00–3:40)

**Na tela:** o gráfico da correlação, de 0,46 (2017) a 0,16 (2025); "+0,2 ponto a cada 10% a mais de gasto"; "maior em: municípios pequenos, Nordeste e Norte".

**Fala:**
> O primeiro resultado confirma a literatura: o gasto, sozinho, diz pouco. A correlação simples entre gasto e nota caiu de 0,46 em 2017 para 0,16 em 2025, e se explica, em grande parte, pelo contexto. Quando comparamos cada município com ele mesmo, 10% a mais de gasto por aluno acompanham só 0,2 ponto a mais no Saeb, sobretudo nos municípios menores e no Nordeste e no Norte. São associações, não efeitos causais.

## Slide 7 · Resultado 2: mesmo gasto, resultados diferentes (3:40–4:20)

**Na tela:** Ceará × Bahia (90% × 38% acima do esperado; R$ 11.391 × R$ 11.231; 242,4 × 200,1 pontos) e "gestão e incentivos pesam mais que o volume".

**Fala:**
> O segundo resultado aparece entre redes com o mesmo gasto. Em 2023, as redes municipais do Ceará e da Bahia gastaram praticamente o mesmo por aluno, cerca de 11 mil reais. Mas a nota média em Matemática foi de 242 pontos no Ceará e de 200 na Bahia, e 90% das redes cearenses ficaram acima do esperado, contra 38% das baianas. Aqui a legislação volta: o Ceará deu escala à cota do ICMS por resultados, junto com assistência técnica aos municípios. A literatura liga a diferença a essas políticas, uma explicação que não testamos aqui.

## Slide 8 · O painel e as três perguntas (4:20–4:55)

**Na tela:** a página Desempenho (captura), com "3 perguntas" e "46% acima do esperado em 2023".

**Fala:**
> Para levar isso ao gestor, construímos um painel em Power BI, com dez páginas organizadas em três perguntas: gastar mais se associa a aprender mais, a minha rede entrega o esperado, e com quem conversar. Esta é a página Desempenho, que mostra, para cada rede, o gasto por aluno e o resultado em relação ao esperado. Em 2023, 46% das redes ficaram acima do esperado, e tudo pode ser filtrado por estado, etapa, disciplina e edição.

## Slide 9 · Minha rede e meus pares (4:55–5:35)

**Na tela:** a Ficha e a página Pares de Timon (MA), lado a lado, com "+24% · melhor que 98%" e "161 pares · só 1 entrega mais".

**Fala:**
> A Ficha mostra cada rede ao longo do tempo. Timon, no Maranhão, gastou cerca de 10 mil reais por aluno em 2023 e ficou 24% acima do esperado, melhor que 98% das redes do país. A página de Pares lista as redes do mesmo grupo de contexto e com gasto parecido: Timon tem 161 pares, e só um entrega mais, Sobral, no Ceará, que tem um alerta. Para Timon, a pergunta passa a ser o que explica o resultado.

## Slide 10 · Os alertas (5:35–5:55)

**Na tela:** a Ficha de Coruripe (AL) (captura), com "+70%" e "salto atípico".

**Fala:**
> O painel também ajuda a evitar conclusões apressadas. Coruripe, em Alagoas, aparece quase 70% acima do esperado, mas a nota mudou demais em relação à edição anterior, e o painel mostra um alerta. Antes de usar uma rede como exemplo, o gestor deve conferir o que está por trás desse salto.

## Slide 11 · Conclusões, contribuições e limitações (5:55–6:40)

**Na tela:** três colunas em palavras-chave: conclusões ("gasto sozinho explica pouco", "mesmo gasto, resultados diferentes"), contribuições ("prática: o painel", "teórica: evidência de 2017 a 2025") e limitações ("associação, não causa", "contexto só por UF, até 2024", "sem teste com gestores").

**Fala:**
> Concluímos que o volume de gasto, sozinho, explica pouco das diferenças de desempenho, e que redes com o mesmo gasto podem ter resultados muito diferentes. A contribuição prática é o painel: com ele, o gestor pode achar redes parecidas que entregam mais e investigar o que elas fazem. A contribuição teórica é evidência recente, de 2017 a 2025, já sob o Novo Fundeb, de que a pergunta relevante é menos quanto se gasta e mais como o recurso é usado. As limitações são que os resultados são de associação, que o contexto socioeconômico só existe por estado e até 2024, e que o painel ainda não foi testado com gestores.

## Slide 12 · Fechamento (6:40–6:50)

**Na tela:** o QR Code (Figura 5), o endereço do repositório e "Obrigado".

**Fala:**
> O painel e todo o código estão abertos: é só ler este QR Code ou acessar o repositório no GitHub. Obrigado pela atenção!

---

## Como gravar no formato pedido

> **Slides prontos:** `exportacao/Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx`, com 12 slides. As falas deste roteiro estão nas **notas do apresentador** de cada slide, visíveis no modo de gravação; o gerador as lê direto deste arquivo, então basta editar a fala aqui e gerar de novo. Gerador: `src/Exportacao/Gerar_Slides.ps1`, que exige o PowerPoint fechado. O slide 1 vem sem o link do YouTube, para a gravação. Depois de publicar o vídeo, gere a versão para o Moodle com `-Link "<endereço do vídeo>"`, que acrescenta a linha "▶ Vídeo: …" ao slide 1.

1. **PowerPoint > Gravar > Gravar do início.** O próprio PowerPoint grava os slides com a sua câmera numa janela no canto, que é exatamente o formato pedido. Ensaie uma vez sem gravar.
2. **Painel:** não há demonstração ao vivo. Os slides 8, 9 e 10 mostram capturas das páginas do painel (de `docs/resultados/telas/`), e basta falar sobre elas.
3. **Exportar:** Arquivo > Exportar > Criar um vídeo, em Full HD.
4. **YouTube:** envie o vídeo como **Não listado**, que só abre com o link. Depois, gere o PowerPoint com o link no slide 1: rode `src/Exportacao/Gerar_Slides.ps1 -Link "<endereço do vídeo>"`, ou cole o link à mão no slide 1.
5. **Moodle:** poste o PowerPoint com o nome completo dos autores, por exemplo `Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx`. Confirme o padrão exato no Moodle.

## Antes de gravar

- **Duração:** cronometre um ensaio; o alvo é de 6min30s a 6min50s, abaixo do limite de 7 minutos.
- **Perguntas da banca:** se perguntarem sobre o método, os detalhes estão no Capítulo 3, Procedimentos metodológicos (seções 3.1 a 3.5, com a matriz de amarração no Quadro 5), e em `docs/decisoes_metodo.md`. Para estudar, use `docs/folha_defesa.md`.
