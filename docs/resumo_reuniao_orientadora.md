# Resumo para a reunião com a orientadora

*Versão curta de `decisoes_metodo.md` (os códigos entre colchetes remetem ao registro completo). Atualizado em 2026-10-22.*

## 1. Onde estamos

- **Extração concluída.** Todas as bases necessárias para a pergunta já estão extraídas e validadas: gasto (SIOPE e SICONFI), matrículas (Censo Escolar), desempenho (Saeb/IDEB), controles (IDHM, alfabetização e infraestrutura) e o deflator (IPCA).
- **Tratamento e cruzamento concluídos.** Os dois painéis estão montados, com gasto por aluno em reais de 2025 (no mesmo ano e com defasagens de 1, 2 e 4 anos), notas do Saeb e controles. O painel municipal tem ~5.300 municípios com nota em Anos Iniciais por edição; o estadual, as 27 UFs. Em seguida vem a análise.
- **O desenho continua o mesmo:** duas camadas analisadas separadamente, no período de 2017 a 2025 (cinco edições do Saeb).

| | Municípios | Estados |
|---|---|---|
| Gasto por aluno | SIOPE: gasto com Ensino Fundamental ÷ matrículas do Fundamental na rede municipal | SICONFI: gasto em educação menos o Ensino Superior ÷ matrículas da educação básica na rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais | Saeb Anos Finais e Ensino Médio |
| Tamanho | ~5.500 municípios | 27 UFs |

## 2. Principais problemas encontrados e como foram contornados

1. **SIOPE e SICONFI não batem [G1–G3].** Para o mesmo município, a diferença é de até 20% em ~3 de cada 4 casos, e nas capitais pode ser muito maior (Rio e Porto Alegre ficam 30% a 50% abaixo no SICONFI).
   → **Cada camada usa uma única fonte, sem misturar.** O SIOPE é usado nos municípios, porque é o sistema específico da educação e cobre ~5.550 municípios por ano. O SICONFI é usado nos estados, porque no SIOPE faltam MG em quase todos os anos e RS em 2018–2019.
2. **O gasto é comparável no tempo [G5].** O formato do rótulo mudou em 2024, mas a parcela do Ensino Fundamental no gasto total em educação fica estável, entre 59% e 63%, em todos os anos. Não há quebra de série.
3. **O desempenho veio das planilhas oficiais do IDEB [S1].** Elas já trazem as notas do Saeb por município e por rede, e os totais batem exatamente com os divulgados pelo Inep. Os microdados por aluno ficaram como extensão possível.
4. **2021, ano da pandemia, tem menos dados [S5].** Há de 11% a 37% menos resultados com nota, conforme a etapa.
   → O ano fica na análise, com um teste de sensibilidade sem ele.
5. **O IDHM de 2025 ainda não foi publicado [C1].** A série do PNUD termina em 2024.
   → Uso do IDHM do ano anterior em todas as edições (ver item 3.1).
6. **Códigos de município fora do padrão [G9].** Nove municípios têm código oficial do IBGE que não segue a regra de cálculo usada para converter o código do SIOPE, e teriam sumido do cruzamento sem aviso.
   → A conversão agora consulta a tabela oficial de códigos, e todos os municípios casam.

## 3. Decisões que precisam do seu aval

### 3.1 IDHM do ano anterior como controle [C1]
- **Proposta:** usar, para cada edição do Saeb, o IDHM do ano anterior (Saeb 2025 ← IDHM 2024, e assim por diante).
- **Por quê:** é a mesma regra para todas as edições e não inventa nenhum valor. O teste de sensibilidade seria usar o IDHM do mesmo ano, repetindo 2024 em 2025.
- **Pergunta:** a defasagem de um ano é aceitável como controle de contexto?

### 3.2 Gasto estadual sem o Ensino Superior: o que fazer quando a linha não existe [G4]
- **Situação:** o SICONFI não traz a linha do Ensino Superior em quatro estados: RO em todos os anos, AC e SE até 2024 e RS de 2018 a 2023. Onde a linha existe, o Ensino Superior costuma pesar pouco (mediana de 2% do gasto em educação), mas chega a 15%–19% em SC e PR.
- **Opção (a):** tratar como "sem gasto com Ensino Superior" e não descontar nada. Mantém as 27 UFs.
- **Opção (b):** tratar como dado faltante. Perde observações em uma amostra que já é pequena.
- **Recomendação:** (a) para AC, RO e SE, onde a ausência parece real (hipótese ainda não verificada). Para o RS, conferir antes no relatório original, porque a linha existe antes e depois da lacuna. As duas versões já estão calculadas, então a escolha não exige refazer nada.
- **Ponto relacionado [G4b]:** o total do gasto estadual em educação inclui despesas que não aparecem nas subfunções detalhadas (provavelmente inativos), com peso diferente entre os estados. A proposta é registrar como limitação e testar como sensibilidade o gasto calculado só pelas subfunções da educação básica.
- **Pergunta:** de acordo?

### 3.3 Anos Finais na camada municipal [S4]
- **Situação:** só ~3.900 municípios têm rede própria de Anos Finais, e ~3.000 deles têm nota. Esses municípios não são uma amostra aleatória.
- **Opção (a):** Anos Iniciais como resultado principal e Anos Finais como complementar, registrando a limitação.
- **Opção (b):** analisar Anos Finais só na camada estadual.
- **Recomendação:** (a).
- **Pergunta:** de acordo?

### 3.4 Recorte geográfico [E3]
- **Situação:** a sugestão de focar em SP ficou sem decisão registrada. O tratamento dos dados já cobre o Brasil inteiro, então o recorte pode ser aplicado só na análise.
- **Pergunta:** a análise principal fica no Brasil (com SP em destaque) ou só em SP?

### 3.5 Gastos por aluno implausíveis [A5]
- **Situação:** cerca de 0,7% dos municípios com nota têm gasto por aluno muito fora do padrão. Há casos de R$ 210 por aluno (Cáceres-MT, 2021) e de mais de R$ 60 mil em redes com menos de 100 alunos. A mediana é de R$ 11 mil. São erros de registro ou redes muito pequenas.
- **Proposta:** manter todos os casos no painel, só marcados. Usar o logaritmo do gasto por aluno, que reduz o peso das pontas, e rodar a análise com e sem os casos marcados.
- **Pergunta:** de acordo, ou prefere excluir os casos marcados desde o início?

### 3.6 Municípios sem nota no Saeb [S8]
- **Situação:** o Inep só divulga a nota das redes que atingem participação mínima. Ficam sem nota de 2% a 13% das redes municipais em Anos Iniciais e de 15% a 33% em Anos Finais (o pior ano é 2021). Essas redes não são aleatórias: em Anos Iniciais 2023, têm em média um quarto das matrículas (182 contra 721) e gastam mais por aluno (R$ 16,6 mil contra R$ 13,5 mil).
- **Consequência:** os resultados valem para as redes com nota divulgada, e os municípios pequenos ficam sub-representados.
- **Proposta:** não imputar notas; descrever a seleção no Método (cobertura e comparação entre incluídos e excluídos); controlar o porte da rede nos modelos; testar com um painel balanceado (só municípios com nota nas cinco edições).
- **Pergunta:** de acordo?

### 3.7 Medida principal de desempenho [S2, S9]
- **Situação:** temos Matemática e Português (em pontos), a nota padronizada N (0 a 10, que combina as duas) e o IDEB (N × aprovação). Entre municípios, Matemática e Português se correlacionam em 0,96, então a escolha muda pouco a ordenação.
- **Proposta:** usar a nota padronizada N como medida principal e Matemática e Português separadas como complementares. O IDEB fica como medida secundária, porque mistura aprendizado e fluxo escolar.
- **Pergunta:** de acordo?

### 3.8 Testes de sensibilidade previstos [A4]
- **Lista:**
  - sem 2021;
  - sem 2025 na camada estadual (as matrículas estaduais caem ~5% nesse ano, e ainda não se sabe se é real ou efeito da mudança no Censo);
  - IDHM do mesmo ano;
  - tratamento alternativo do Ensino Superior;
  - com e sem os gastos extremos;
  - painel balanceado (só municípios com nota em todas as edições).
- **Defasagens na camada estadual [P3]:** hoje elas têm a mesma limitação das municipais, porque as matrículas começam em 2017. Dá para estendê-las extraindo as matrículas de 2015–2016 (cerca de meio dia de trabalho).
- **Pergunta:** a lista está suficiente? Vale a extensão para os estados?

## 4. Limitações que vão para o Método

- O nível do gasto depende da fonte escolhida, sobretudo nas capitais.
- A camada estadual tem só 27 unidades.
- A amostra é selecionada pela divulgação do Saeb: redes pequenas ficam sem nota, sobretudo em Anos Finais e em 2021.
- O controle socioeconômico (IDHM) só existe por UF e com defasagem.
- Os resultados são de associação, não de causalidade.

## 5. Uso de IA

O Manual exige informar e discutir previamente o uso de IA. Esta é a comunicação: usamos assistente de IA no desenvolvimento do código de tratamento dos dados e na organização deste registro. Todas as decisões foram tomadas por nós e são verificáveis no código e nos diagnósticos. Precisamos saber como você prefere que isso seja documentado no Método.
