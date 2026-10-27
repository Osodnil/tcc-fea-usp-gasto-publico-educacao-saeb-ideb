# Resumo para a reunião com a orientadora

*Versão curta de `decisoes_metodo.md` (os códigos entre colchetes remetem ao registro completo). Atualizado em 2026-10-26, depois da reunião de 23/10/2026.*

## 1. Onde estamos

- **Dados prontos.** Todas as bases foram extraídas, tratadas, validadas e cruzadas em dois painéis (municípios e estados, 2017–2025), com gasto por aluno em reais de 2025, notas do Saeb e controles. Há um dashboard de conferência que abre no navegador.
- **Decisões da reunião de 23/10 já aplicadas** (ver seção 2).
- **Próxima etapa:** análise exploratória, clusters e estimações, depois das definições da seção 3.

| | Municípios | Estados |
|---|---|---|
| Gasto por aluno | SIOPE: gasto com Ensino Fundamental ÷ matrículas do Fundamental na rede municipal | SICONFI: gasto em educação menos o Ensino Superior ÷ matrículas da educação básica na rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais | Saeb Anos Finais e Ensino Médio |
| Tamanho | ~5.500 municípios | 27 UFs |

## 2. O que foi decidido em 23/10 e como foi aplicado

| Ponto | Decisão | Situação |
|---|---|---|
| IDHM [C1] | Usar o IDHM do mesmo ano do Saeb, sem defasagem | **Aplicado.** A edição de 2025 fica sem IDHM, porque a série termina em 2024; isso está registrado como limitação |
| Outliers [A5] | Não remover | **Aplicado.** Todos os casos entram na análise; os implausíveis só ficam marcados |
| Gasto anual ou bianual [G12] | Entender a periodicidade | **Respondido:** o gasto é anual; o Saeb é que é bienal. Cada edição usa o gasto do mesmo ano, e os anos intermediários entram pelas defasagens |
| Clusters [A6] | Incluir análise de clusters | Desenho proposto abaixo (3.1) |
| IDHM e educação [C1b] | Entender a relação | Proposta abaixo (3.2) |
| Acesso ao projeto [A7] | QR Code ou similar, ao final | Fica para a etapa final; exige publicar o dashboard num endereço público |
| Registro [seção 10] | Anotar toda decisão e limitação | Lista consolidada de limitações criada no registro |

## 3. Pontos para a próxima reunião

### 3.1 Desenho da análise de clusters [A6]
- **Proposta:** agrupar os municípios só pelo **contexto** (porte da rede, população, alfabetização, IDHM Renda, infraestrutura) e, dentro de cada grupo, comparar gasto por aluno e nota. Assim se mostra quem entrega mais ou menos do que os pares comparáveis, que é o centro da pergunta do TCC.
- **Alternativa:** agrupar por tudo junto (gasto, nota e contexto), para descrever perfis como "alto gasto, baixo desempenho".
- **Pergunta:** qual das duas? Os clusters ficam só para os municípios (27 UFs é pouco para agrupar)?

### 3.2 IDHM: controle ou parte do resultado? [C1b]
- **Situação:** o IDHM tem uma dimensão de Educação (escolaridade adulta e fluxo escolar). Usá-lo como controle pode significar controlar, em parte, pelo próprio resultado. Nos estados, o IDHM Educação e o IDHM Renda têm correlação parecida com a nota (0,48 e 0,45) e muito alta entre si (0,77).
- **Proposta:** usar o **IDHM Renda** como controle principal e mostrar o IDHM total como comparação.
- **Pergunta:** de acordo?

### 3.3 Medida principal de desempenho [S9]
- **Proposta:** nota padronizada N (0 a 10, combina Matemática e Português) como principal; Matemática e Português como complementares; o IDEB como medida secundária, porque mistura aprendizado e aprovação.
- **Pergunta:** de acordo?

### 3.4 Municípios sem nota no Saeb [S8]
- **Situação:** ficam sem nota de 2% a 13% das redes em Anos Iniciais e de 15% a 33% em Anos Finais. São redes menores, que gastam mais por aluno.
- **Proposta:** não imputar notas, descrever a seleção no Método, controlar o porte nos modelos e testar com um painel balanceado.
- **Pergunta:** de acordo?

### 3.5 Gasto estadual sem a linha de Ensino Superior [G4]
- **Situação:** a linha não existe para RO (todos os anos), AC e SE (até 2024) e RS (2018–2023).
- **Proposta:** tratar como zero em AC, RO e SE; para o RS, conferir antes no relatório original. As duas versões já estão calculadas.
- **Pergunta:** de acordo?

### 3.6 Escopo [S4, E3]
- **Anos Finais na camada municipal:** proposta de manter como complementar, com Anos Iniciais como principal. De acordo?
- **Recorte geográfico:** Brasil (com SP em destaque) ou só SP?

### 3.7 Testes de sensibilidade [A4, P3]
- **Lista atual:**
  - sem 2021;
  - sem 2025 na camada estadual;
  - IDHM Renda × IDHM total;
  - tratamento alternativo do Ensino Superior;
  - painel balanceado;
  - gasto médio do biênio no lugar do gasto anual.
- **Pergunta:** a lista está suficiente? Vale estender as matrículas para 2015–2016 (cerca de meio dia) para ter defasagens nos estados?

### 3.8 Pontos de estrutura do TCC que ficaram para trás [D1–D4]
Vêm das conversas anteriores ao pivô e ainda não foram respondidos:
- **Formato do TCC:** método científico ou consultoria? A pergunta central é de descoberta (estudo quantitativo), com o dashboard como produto aplicado. A escolha muda a estrutura e os critérios de avaliação.
- **Pontos do e-mail de 02/10:** reescrever a pergunta de pesquisa, as perguntas analíticas (há 6 em rascunho) e os indicadores formais (nome, fórmula, unidade, interpretação) para o projeto atual. Podemos trazer uma proposta na próxima reunião?
- **Usuário-alvo:** secretaria estadual, municipal ou as duas (o produto já tem as duas camadas)?

## 4. Principais limitações (lista completa na seção 10 do registro)

- O nível do gasto depende da fonte, sobretudo nas capitais.
- Só entram redes com nota divulgada; redes pequenas ficam sub-representadas.
- O IDHM existe só por UF e só até 2024: a edição de 2025 fica sem esse controle.
- A edição de 2021 foi afetada pela pandemia.
- A camada estadual tem só 27 unidades.
- O gasto municipal usado (Ensino Fundamental) não separa Anos Iniciais de Finais e exclui a Educação Infantil.
- Os resultados são de associação, não de causalidade.

## 5. Uso de IA

O Manual exige informar e discutir previamente o uso de IA. Usamos assistente de IA no desenvolvimento do código de tratamento dos dados e na organização dos registros. Todas as decisões são nossas e verificáveis no código e nos diagnósticos. Precisamos saber como você prefere que isso seja documentado no Método.
