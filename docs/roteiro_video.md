# Roteiro do vídeo de apresentação do TCC (Henrique)

*2026-11-18; revisado em 2026-11-25 contra o documento principal (Revisado5). Etapa 6 do plano final. Os números
conferem com o texto e com o painel publicado.*

## Regras do Manual (vídeo vale 20% da nota do TCC II)

- **Duração:** cerca de 5 minutos, no máximo 7.
- **Formato:** cada integrante grava o próprio vídeo, com os slides na janela grande e o rosto numa janela menor.
- **Entrega:**
  - o link do YouTube vai no **1º slide**;
  - o arquivo do PowerPoint, nomeado com os **nomes completos** dos autores, é postado no Moodle.
- **Este roteiro:** dá cerca de 5min40s em ritmo natural (cerca de 140 palavras por minuto). Se passar de 6 minutos no ensaio, encurte primeiro o slide 6, a demonstração do painel.
- **Combinar com o Guilherme:** cada vídeo precisa se sustentar sozinho e cobrir o trabalho todo. O dele pode dar mais tempo à revisão da literatura e a Ceará × Bahia; o seu, aos dados, ao método e ao painel.

---

## Slide 1 · Abertura (0:00–0:20)

**Na tela:**
- o título;
- os autores: Guilherme Menezes Araújo e Henrique Nogueira Pedro Lindoso;
- a orientadora: Profa. Adriana Backx Noronha Viana;
- FEA/USP, 2026;
- o **link do YouTube**.

**Fala:**
> Olá, eu sou o Henrique Lindoso e vou apresentar o TCC que fiz com o Guilherme Menezes, sob orientação da professora Adriana Backx: "Gasto público por aluno e desempenho no Saeb: uma análise das redes públicas brasileiras com apoio de Business Intelligence".

## Slide 2 · Problema e pergunta (0:20–1:00)

**Na tela:**
- "R$ 339 bilhões no Fundeb em 2025";
- a pergunta de pesquisa em destaque.

**Fala:**
> O Brasil gasta muito com educação básica: só o Fundeb teve receita estimada em 339 bilhões de reais em 2025. Mas os dados de gasto e os de aprendizagem estão em sistemas diferentes, e são raros os portais que permitem comparar, rede a rede, quanto se gasta com quanto se aprende. Então nossa pergunta foi: o gasto público por aluno se associa ao desempenho das redes no Saeb? E, considerando o gasto e o contexto de cada rede, quais entregam mais ou menos do que o esperado?

## Slide 3 · Dados e método (1:00–1:50)

**Na tela:** um esquema simples com quatro elementos:
- 8 bases públicas → painéis de dados → modelos → painel;
- "2017–2025", "cerca de 5.500 municípios", "27 UFs".

**Fala:**
> Juntamos oito bases públicas, entre elas o SIOPE e o Siconfi, para o gasto, o Saeb, para a nota, e o Censo Escolar, o IBGE e o IDHM, para o contexto. Cobrimos de 2017 a 2025, com os valores corrigidos pela inflação. O trabalho tem duas camadas: as redes municipais e as redes estaduais. Para medir a associação, usamos regressões que comparam municípios entre si e cada município com ele mesmo ao longo do tempo. E criamos um indicador, o desempenho em relação ao esperado: quanto a nota de uma rede fica acima ou abaixo da de redes com gasto e contexto parecidos. Os scripts foram desenvolvidos com o auxílio de IA, em acordo com a orientadora, e todas as decisões estão registradas no repositório público.

## Slide 4 · Resultado 1: o gasto, sozinho, explica pouco (1:50–2:40)

**Na tela:**
- "correlação de 0,46 (2017) → 0,16 (2025)";
- "+10% no gasto → +0,2 ponto no Saeb";
- gráfico de apoio: a Figura 6 do texto (associação por porte, região, cluster e faixa de gasto).

**Fala:**
> O primeiro resultado é que o gasto, sozinho, diz pouco. A correlação simples entre gasto e nota caiu de 0,46 em 2017 para 0,16 em 2025, e se explica, em grande parte, pelo contexto dos municípios. Quando comparamos cada município com ele mesmo, 10% a mais de gasto por aluno acompanham só 0,2 ponto a mais no Saeb. A associação existe, mas é pequena, e se concentra nos municípios menores e no Nordeste e no Norte. Nas redes estaduais, com só 27 unidades, não dá para detectá-la. E é importante dizer: são associações, não efeitos causais.

## Slide 5 · Resultado 2: mesmo gasto, resultados diferentes (2:40–3:20)

**Na tela:** a Figura 7 do texto (Ceará e Bahia), com três números:
- R$ 11.391 × R$ 11.231;
- 242 × 200 pontos;
- 90% × 38% acima do esperado.

**Fala:**
> O segundo resultado aparece quando comparamos redes com o mesmo gasto. Em 2023, as redes municipais do Ceará e da Bahia gastaram praticamente o mesmo por aluno, cerca de 11 mil reais. Mas a nota média em Matemática foi de 242 pontos no Ceará e de 200 na Bahia, e 90% das redes cearenses ficaram acima do esperado, contra 38% das baianas. A diferença se mantém entre municípios de contexto parecido. A literatura liga o caso do Ceará a incentivos e à assistência técnica aos municípios. Ou seja: o que faz diferença parece ser como o recurso é usado, e não só quanto se gasta.

## Slide 6 · O painel (3:20–4:30)

**Na tela:** o painel publicado, ao vivo, ou capturas de tela, nesta ordem:
1. **Boas-vindas:** as três perguntas.
2. **Desempenho:** o ranking e a dispersão.
3. **Ficha:** Timon (MA).
4. **Pares:** Timon comparado com Pacajus (CE).
5. Um alerta: Coruripe (AL), com salto atípico.

**Fala:**
> Para levar isso ao gestor, construímos um painel em Power BI, organizado em três perguntas. Primeiro: gastar mais se associa a aprender mais? Segundo: a minha rede entrega o esperado? Aqui, por exemplo, Timon, no Maranhão, ficou 24% acima do esperado em 2023, melhor que 98% das redes. Terceiro: com quem conversar? A página de Pares mostra redes do mesmo grupo de contexto e com gasto parecido que obtêm resultados melhores. O painel também traz alertas. Coruripe, em Alagoas, aparece muito acima do esperado, mas com um salto de nota fora do padrão, e o alerta avisa para conferir antes de usar a rede como exemplo.

## Slide 7 · Conclusões e limitações (4:30–5:20)

**Na tela:**
- três conclusões curtas;
- três limitações curtas.

**Fala:**
> Concluímos três coisas. Primeiro, o volume de gasto, sozinho, explica pouco das diferenças de desempenho. Segundo, redes com o mesmo gasto podem ter resultados muito diferentes. E terceiro, comparar cada rede com redes parecidas, com os alertas certos, ajuda o gestor a encontrar referências e a investigar o uso dos recursos. As principais limitações são que os resultados são de associação, que o controle socioeconômico só existe por estado e termina em 2024, e que o painel ainda não foi testado com gestores, o que fica como sugestão para trabalhos futuros.

## Slide 8 · Fechamento (5:20–5:40)

**Na tela:**
- o QR Code (Figura 5);
- o endereço do repositório;
- "Obrigado".

**Fala:**
> O painel e todo o código estão abertos: é só ler este QR Code ou acessar o repositório no GitHub. Obrigado pela atenção!

---

## Como gravar no formato pedido

> **Slides prontos:** `exportacao/Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx`, com 8 slides. As falas deste roteiro estão nas **notas do apresentador** de cada slide, visíveis no modo de gravação. Gerador: `src/Exportacao/Gerar_Slides.ps1`, que exige o PowerPoint fechado. Antes de gravar, troque no slide 1 o texto "[colar aqui o link do YouTube]" pelo link.

1. **PowerPoint > Gravar > Gravar do início.** O próprio PowerPoint grava os slides com a sua câmera numa janela no canto, que é exatamente o formato pedido. Ensaie uma vez sem gravar.
2. **Demonstração do painel (slide 6):**
   - **opção mais simples:** use capturas de tela nos slides; as telas de `docs/resultados/telas/` já estão prontas;
   - **ao vivo:** grave com o Teams, o Zoom ou o OBS, compartilhando a tela e com a câmera ligada.
3. **Exportar:** Arquivo > Exportar > Criar um vídeo, em Full HD.
4. **YouTube:** envie o vídeo como **Não listado**, que só abre com o link. Cole o link no slide 1 e salve o PowerPoint de novo.
5. **Moodle:** poste o PowerPoint com o nome completo dos autores, por exemplo `Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx`. Confirme o padrão exato no Moodle.

## Antes de gravar

- **Painel:** abra o link do painel e deixe na página certa, se for mostrar ao vivo.
- **Duração:** cronometre um ensaio; o alvo é de 5 a 6 minutos.
- **Perguntas da banca:** se perguntarem sobre o método, os detalhes estão no Capítulo 3, Procedimentos metodológicos (seções 3.1 a 3.5, com a matriz de amarração no Quadro 5), e em `docs/decisoes_metodo.md`. Para estudar, use `docs/folha_defesa.md`.
