# Nota de método: proficiência, nota esperada, eficiência e clusters

*Para o Henrique e o Guilherme, em resposta às dúvidas da reunião de 2026-11-06. Escrita em 2026-11-09. Os códigos entre colchetes remetem a `docs/decisoes_metodo.md`. Os números são de Anos Iniciais (5º ano), Matemática, edição de 2023, salvo indicação.*

## 1. Proficiência: o que o painel chama de "nota"

- **O que é:** a nota média dos alunos da **rede municipal** no Saeb, em pontos, numa escala do Inep comparável entre edições [S1, S9]. Ela vem pronta nas planilhas de divulgação do IDEB; o projeto não recalcula nada.
- **Uma disciplina por vez:** Matemática e Língua Portuguesa ficam separadas. Notas de etapas diferentes (5º e 9º ano) também não devem ser comparadas, porque são alunos e testes diferentes.
- **Ordem de grandeza em 2023:**
  - **mediana:** 220,7 pontos;
  - **intervalo:** 10% das redes ficam abaixo de 188,1, e 10% ficam acima de 250,8.
- **Nota padronizada N e IDEB:** existem no painel só como medidas secundárias [S10].

## 2. Nota esperada: de onde vem

A nota esperada responde à pergunta: **"quanto redes com o mesmo gasto e o mesmo contexto tiraram, em média?"**. Ela vem de uma regressão linear (MQO), estimada sobre todas as redes do país, separadamente para cada etapa e disciplina [A8]:

> proficiência = constante + b₁·log(gasto por aluno) + b₂·log(população) + b₃·alfabetização + b₄·infraestrutura + b₅·log(matrículas) + b₆·IDHM Renda da UF + b₇·IDHM Longevidade da UF + efeito da edição

**Coeficientes do modelo nacional (Anos Iniciais, Matemática, 2017–2023, 20.315 observações, R² = 0,39):**

| Variável | Coeficiente | Erro-padrão | Leitura |
|---|---|---|---|
| log do gasto por aluno | +0,92 | 0,72 (p = 0,20) | 10% a mais de gasto → +0,09 ponto; **não significativo** |
| log10 da população | +7,49 | 1,46 | municípios maiores, nota um pouco maior |
| alfabetização (pontos percentuais) | +0,27 | 0,06 | +10 p.p. de alfabetização → +2,7 pontos |
| infraestrutura (0 a 1) | +30,1 | 1,7 | escolas mais equipadas, nota maior |
| log10 das matrículas | −9,44 | 1,46 | redes maiores, mantido o resto, nota menor |
| IDHM Renda da UF | +146,4 | 7,4 | estados mais ricos, nota maior |
| IDHM Longevidade da UF | +213,5 | 16,4 | idem |

Todos os coeficientes estão em `data/interim/diagnosticos/eficiencia_coeficientes.csv`.

**Duas versões do modelo:**

| | Comparação nacional (oficial) | Comparação no próprio estado (robustez) |
|---|---|---|
| Diferença | usa o IDHM Renda e Longevidade da UF | troca o IDHM por um efeito fixo de cada UF |
| Com quem cada rede é comparada | redes de todo o país | redes do mesmo estado |
| Edições | 2017–2023 (não existe IDHM de 2025 [C1]) | 2017–2025 |
| Coeficiente do gasto (AI, MT) | +0,92 (não significativo) | +4,33 (p < 0,001) |

**O seletor não filtra a UF.** O que muda é a régua da comparação: a comparação no próprio estado tira da eficiência a diferença média entre os estados. Nenhuma rede sai do cálculo; em 2023, as duas versões têm as mesmas 5.240 redes. Exemplos de 2023:

| UF | Eficiência média, comparação nacional | Eficiência média, no próprio estado | Acima do esperado, nacional → estado |
|---|---|---|---|
| CE | +33,6 | +4,0 | 90% → 45% |
| AL | +27,2 | +6,5 | 87% → 41% |
| TO | −22,5 | −4,4 | 7% → 36% |

As duas versões ordenam as redes de forma parecida (correlação de 0,89 entre os resíduos).

## 3. Eficiência

- **Definição:** eficiência = proficiência observada − proficiência esperada (o resíduo da regressão). +10 significa 10 pontos acima do que redes com gasto e contexto parecidos alcançaram.
- **Percentil:** a posição da rede entre as da mesma etapa, disciplina e edição. 80 = melhor que 80% das redes.
- **Faixas:** "bem abaixo", "abaixo", "próximo", "acima" e "bem acima do esperado", por quintil do percentil. A proposta ainda está a confirmar [D2].
- **Escala:** em 2023, 80% das redes ficam entre −23,7 e +24,7 pontos.

**Exemplos (2023, comparação nacional):**

| Município | Gasto por aluno | Proficiência | Esperada | Eficiência | Percentil | Observação |
|---|---|---|---|---|---|---|
| Ibateguara (AL) | R$ 12.000 | 331,2 | 193,6 | +137,6 | 100 | salto atípico em 2021 [S11]; no próprio estado, +120,1 |
| Sobral (CE) | R$ 11.197 | 333,4 | 212,6 | +120,8 | 100 | salto atípico em 2023 |
| São Paulo (SP) | R$ 18.374 | 210,6 | 232,2 | −21,6 | 12 | a rede municipal atende 42% dos alunos públicos de AI |
| Campinas (SP) | R$ 26.036 | 212,3 | 237,2 | −25,0 | 9 | a rede municipal atende só 22% dos alunos públicos de AI |

**Gastar mais não garante eficiência.**
- No modelo nacional, o gasto quase não muda a nota esperada (coeficiente de +0,92, não significativo).
- A eficiência é praticamente independente do gasto: a correlação entre as duas é de 0,01.
- Campinas é o exemplo extremo: um dos maiores gastos por aluno do país, com eficiência no 9º percentil.

Tudo isso é associação, não efeito causal [A1].

**Por que 2025 não tem eficiência na comparação nacional:** o modelo usa o IDHM da UF do mesmo ano, e a série do IDHM termina em 2024. Essa foi uma decisão combinada com a orientadora [C1]. Em 2025, só a comparação no próprio estado tem eficiência; o painel avisa isso quando a edição de 2025 é escolhida.

## 4. Clusters

- **O que são:** 7 grupos de municípios com **contexto** parecido, formados **sem gasto nem nota** [A6].
- **Variáveis:** log da população, alfabetização, IDHM Renda e Longevidade da UF e infraestrutura das escolas municipais, todas padronizadas.
- **Método:** k-médias, com k = 7 escolhido pela silhueta e pela utilidade para formar pares.
- **Para que servem:** dar cor à dispersão da página Eficiência, comparar a rede com as medianas do grupo na Ficha e definir os pares (mesmo cluster e gasto entre 0,8 e 1,25 vez o da referência).
- **Cuidado:** a separação entre os grupos é fraca (silhueta ≈ 0,23), e eles saem ligados à região, porque o IDHM só existe por UF [L16]. A eficiência não entra na formação dos clusters; os clusters também não entram no modelo da nota esperada.

## 5. Por que tantos municípios aparecem sem dados

O painel agora mostra o motivo, usando as matrículas por rede do Censo Escolar (tabela `fato_oferta_municipal`; cartão "Situação da rede" na Ficha e aviso no Mapa).

**Situação dos 5.571 municípios em 2023:**

| Etapa | Com nota | Sem nota divulgada pelo Inep (há alunos na rede municipal) | Sem rede municipal na etapa |
|---|---|---|---|
| Anos Iniciais | 5.243 | 319 | 9 |
| Anos Finais | 3.196 | 723 | 1.652 |

- **Anos Finais:** a maior parte da ausência é estrutural, porque a etapa fica com a rede estadual em 1.652 municípios.
- **Sem nota divulgada:** o Inep só publica a nota de redes com participação e número de alunos avaliados acima de um mínimo [S8]; os números exatos ainda precisam ser conferidos na nota técnica.
- **Nota sem gasto:** é raro, de 3 a 15 casos por edição.

## 6. Rede municipal × rede estadual (limitação levantada na reunião)

- **A regra geral:** os Anos Iniciais são responsabilidade das prefeituras, mas em muitos municípios a rede estadual ainda atende parte desses alunos.
- **Quanto pesa (2023):**
  - em 923 municípios, a rede municipal atende menos de 80% dos alunos de Anos Iniciais das escolas públicas;
  - em 266, atende menos da metade;
  - os estados com mais Anos Iniciais na rede estadual são AC (42%), RS (33%), AP (32%), SP (25%), SC (25%) e MG (23%).
- **O indicador continua coerente:** o gasto e a nota são da mesma rede municipal.
- **O que muda é a leitura:** nesses municípios, a rede municipal não representa todas as crianças da cidade; Campinas é o exemplo acima.
- **Encaminhamento (etapa 2 do plano de ação):** a parcela municipal já está calculada (`PART_MUN`). Falta:
  - criar a marca e o teste de sensibilidade;
  - medir a mesma limitação nos Anos Finais;
  - registrar a nova limitação.
