# Folha de defesa: perguntas prováveis da banca

*2026-11-24. Para Henrique e Guilherme estudarem antes da banca. Cada resposta cabe em uma ou duas frases; os números
vêm do documento principal (`exportacao/TCC_II_FEA_USP_Versao_Final-Revisado5.docx`). Regra de ouro: sempre falar em
**associação**, nunca em **efeito** ou **causa**.*

---

## 1. A ideia do trabalho

**Qual é a pergunta do trabalho?**
Se o gasto público por aluno se associa ao desempenho das redes no Saeb e, considerando o gasto e o contexto de cada
rede, quais redes entregam mais ou menos do que o esperado.

**Por que isso é um tema de Administração, e não de Economia?**
Porque o foco é a decisão do gestor: os dados existem, mas estão espalhados, e o trabalho os reúne num painel que
permite comparar a rede com redes parecidas e investigar o que as melhores fazem. A estatística é o respaldo; o
produto é a ferramenta de gestão.

**Qual é a contribuição prática?**
Um painel que junta, numa só tela, gasto, nota e contexto, e que mostra quem entrega mais do que o esperado e quem são
os pares de cada rede.

**E a contribuição teórica?**
Evidência recente (2017–2025, já com o Novo Fundeb) de que o volume de gasto, sozinho, explica pouco do desempenho; a
pergunta relevante é como o recurso é usado.

---

## 2. Dados

**De onde vêm os dados?**
Gasto: SIOPE (municípios) e Siconfi (estados). Nota: Saeb. Matrículas e infraestrutura: Censo Escolar. Contexto: IBGE
(população e alfabetização) e IDHM. Tudo público, de 2017 a 2025, corrigido pela inflação (IPCA).

**Como o gasto por aluno é calculado?**
Na rede municipal, a despesa paga no Ensino Fundamental dividida pelas matrículas do Ensino Fundamental da rede.

**Por que só a rede municipal no Ensino Fundamental?**
Porque o gasto e a nota precisam ser da mesma rede. O município cuida sobretudo do Fundamental; o estado, dos Anos
Finais e do Ensino Médio, analisados à parte (camada estadual).

**E os municípios sem nota?**
Ficam de fora: o Inep não divulga nota de redes muito pequenas. É uma limitação declarada.

**Vocês tiraram os valores estranhos de gasto?**
Não, por decisão da orientadora: eles foram marcados (0,7% das observações) e mantidos.

---

## 3. Resultados (seção 4.2)

**Quem gasta mais tira nota maior?**
Comparando municípios diferentes, quase não: o gasto não se distingue de zero quando se controla o contexto.
Comparando o mesmo município ao longo do tempo, sim, mas pouco.

**Quanto é "pouco"?**
10% a mais de gasto por aluno acompanham cerca de 0,2 ponto no Saeb; dobrar o gasto, cerca de 1,6 ponto, menos de 7%
da diferença típica entre as redes (24,2 pontos).

**Por que o resultado entre municípios é diferente do resultado dentro do município?**
Porque municípios diferentes diferem em tudo, não só no gasto (renda, gestão, história). Comparar o município com ele
mesmo tira da conta o que é fixo nele.

**O que é "efeito fixo de município"?**
É a forma de comparar cada município com ele mesmo ao longo do tempo: a pergunta passa a ser "nos anos em que gastou
mais do que costuma, a nota foi maior do que costuma?".

**E por que comparar só com municípios do mesmo estado e do mesmo ano?**
Porque, de 2023 a 2025, o Norte e o Nordeste ganharam ao mesmo tempo mais dinheiro e mais nota. Sem esse cuidado, uma
melhora regional pareceria efeito do gasto. Com ele, o resultado fica estável.

**O que quer dizer o asterisco nas tabelas?**
Que o número se distingue de zero: três asteriscos indicam menos de 1% de chance de um valor assim aparecer se a
associação real fosse nula.

**O gasto de anos anteriores importa?**
O que acompanha a nota é o gasto dos dois anos do ciclo da prova (o Saeb é a cada dois anos). O de antes do ciclo não
se associa de forma significativa.

**Como sabem que o resultado não depende de uma escolha de vocês?**
Pelos testes de sensibilidade: a conta foi refeita mudando uma escolha por vez (sem 2021, sem redes parciais, sem
saltos de nota etc.), e a associação continuou positiva e significativa em todos, entre 1,4 e 5,5 pontos por log do
gasto (Tabela 4).

**Por que o teste com o gasto médio do biênio dá um número maior?**
O coeficiente é cerca de 60% maior. Uma explicação provável, não testada, é que o gasto de um ano isolado oscila (uma
obra, um atraso de pagamento), e essa oscilação puxa o número para perto de zero; a média dos dois anos do ciclo
reduz a oscilação. O ponto central é que o sinal e a significância não mudam.

**Onde a associação é maior?**
Nos municípios pequenos (até 50 mil habitantes) e no Nordeste e no Norte. Nas cidades de 50 a 100 mil habitantes, ela
não se distingue de zero, e nas de mais de 100 mil, fica negativa, sem explicação testada; no Sudeste e no Sul, não se
distingue de zero.

**E nas redes estaduais?**
Com só 27 unidades, a estimativa é imprecisa: não dá para detectar a associação, o que não quer dizer que ela não
exista.

---

## 4. O indicador e os grupos

**O que é o "desempenho em relação ao esperado"?**
A diferença entre a nota da rede e a nota esperada para redes com o mesmo gasto e o mesmo contexto, em percentual.
+5% quer dizer 5% acima do esperado.

**De onde vem a nota esperada?**
De uma regressão da nota contra o gasto e o contexto (população, alfabetização, infraestrutura, tamanho da rede e IDHM
Renda e Longevidade da UF).

**Por que não chamar de eficiência?**
Porque o gasto quase não muda a nota esperada, e porque "eficiência" tem um sentido técnico próprio (métodos de
fronteira, em que 100% é o máximo possível), que não se aplica aqui.

**O indicador mede a qualidade da gestão?**
Não só: como é a parte da nota que o modelo não explica, ele capta gestão, mas também contexto familiar e qualidade do
registro. Por isso é ponto de partida para investigar, não veredito.

**Como os municípios foram agrupados?**
Pelo k-médias, com cinco variáveis de contexto (população, alfabetização, IDHM Renda, IDHM Longevidade e
infraestrutura), nunca pelo gasto nem pela nota. Foram formados sete grupos.

**Por que sete grupos?**
Comparando de 3 a 10 grupos, a qualidade da separação fica parecida a partir de cinco; com sete, os municípios grandes
do Norte e do Nordeste ganham grupo próprio. Três grupos seriam largos demais para formar pares.

**Os grupos são bem separados?**
Não muito (silhueta de 0,23): servem para formar pares de comparação, não para definir tipos de município.

---

## 5. Ceará × Bahia e casos

**O que mostra a comparação entre Ceará e Bahia?**
Gasto praticamente igual (R$ 11.391 e R$ 11.231 por aluno, em 2023), mas 90% das redes do Ceará acima do esperado,
contra 38% das da Bahia. O gasto, sozinho, não explica a diferença.

**Então a política do Ceará causou isso?**
O trabalho não testa. O resultado é compatível com os estudos sobre a cota do ICMS e a assistência técnica do Ceará
(Lautharte et al., 2021), mas a explicação não foi testada aqui.

**Como os três casos foram escolhidos?**
Por regras objetivas, aplicadas ao recorte padrão do painel: uma rede acima do esperado sem alerta (Timon), uma abaixo
com rede parcial (São Paulo) e uma acima com salto atípico (Coruripe).

---

## 6. Método, IA e limites

**Por que não um estudo causal?**
Porque exigiria uma variação do gasto externa às decisões das redes, o que os dados públicos não oferecem de forma
direta. O trabalho é honesto sobre isso e fala sempre em associação.

**Como vocês usaram inteligência artificial?**
Em acordo com a orientadora, para desenvolver os scripts, levantar referências e redigir versões iniciais. As decisões
de pesquisa foram dos autores, os números vêm das bases públicas e podem ser refeitos pelos scripts, e tudo está
registrado no repositório.

**O painel foi testado com gestores?**
Não: foi validado por cenários de uso e pela conferência dos números. Testar com gestores exigiria consentimento e,
possivelmente, comitê de ética; fica como sugestão de pesquisa futura.

**Quais as principais limitações?**
Associação, e não causa; IDHM só por UF (e até 2024); gasto declarado pelos próprios entes; redes pequenas sem nota;
gasto do Fundamental sem separar Anos Iniciais e Finais; camada estadual com só 27 unidades.

**Por que não há simulador de gasto no painel?**
Porque a associação é pequena e não causal: um simulador sugeriria um efeito que o trabalho não mede.

---

## Se não souber responder

Diga o que o trabalho mostra e o que ele não mostra. Por exemplo: "O trabalho não testou isso; o que os dados mostram
é...". Admitir um limite com clareza vale mais do que improvisar uma resposta.
