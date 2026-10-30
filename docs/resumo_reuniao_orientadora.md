# Resumo para a reunião com a orientadora

*Versão curta de `decisoes_metodo.md` (os códigos entre colchetes remetem ao registro completo). Atualizado em 2026-10-30, depois da leitura do Manual de TCC.*

## 1. Onde estamos

- **Dados prontos.** Todas as bases foram extraídas, tratadas, validadas e cruzadas em dois painéis (municípios e estados, 2017–2025), com gasto por aluno em reais de 2025, notas do Saeb e controles.
- **Ferramenta de análise pronta.** Dashboard HTML com seis abas (visão geral, defasagens, porte e contexto, mapa, ficha e pares), usado para explorar os dados.
- **Desenho fechado.** As decisões de método estão tomadas (seção 2).
- **Próxima etapa:** clusters e indicador de eficiência, e o dashboard oficial em Power BI.

| | Municípios | Estados |
|---|---|---|
| Gasto por aluno | SIOPE: gasto com Ensino Fundamental ÷ matrículas do Fundamental na rede municipal | SICONFI: gasto em educação menos o Ensino Superior ÷ matrículas da educação básica na rede estadual |
| Desempenho | Saeb Anos Iniciais (principal) e Anos Finais | Saeb Anos Finais e Ensino Médio |
| Tamanho | ~5.500 municípios | 27 UFs |

## 2. Decisões tomadas

| Ponto | Decisão |
|---|---|
| IDHM no tempo [C1] | IDHM do mesmo ano do Saeb; a edição de 2025 fica sem IDHM, o que vai como limitação |
| IDHM e educação [C1b] | Excluir os índices de escolaridade (IDHM Educação e IDHM total), para evitar circularidade; usar IDHM Renda e Longevidade |
| Outliers [A5] | Não remover; os casos implausíveis só ficam marcados |
| Gasto anual ou bianual [G12] | O gasto é anual; o Saeb é bienal. Cada edição usa o gasto do mesmo ano, e os anos intermediários entram pelas defasagens |
| Clusters [A6] | Desenvolver: agrupar os municípios por contexto e comparar gasto e nota dentro de cada grupo |
| Medida principal [S9, S10] | Proficiência do Saeb em pontos, Matemática e Português separadas. A nota padronizada N do Inep fica como secundária, porque satura nos limites de 1997 (43 redes de Anos Iniciais presas no teto) e não é comparável entre etapas. O cálculo da N foi conferido na Nota Técnica do Inep e reproduzido nos dados |
| Ensino Superior no gasto estadual [G4] | Versão A: quando a linha não existe, nada é descontado, para não perder UF/anos |
| Recorte [E3] | Brasil inteiro: ferramenta nacional, mesma perspectiva para todos os estados |
| Usuário-alvo [E4] | Agente de secretaria de educação ou analista da educação pública |
| Acesso [A7] | QR Code ao final, apontando para o dashboard publicado |
| Registro [seção 10] | Toda decisão e limitação anotada |

## 3. Pontos ainda abertos (não bloqueiam o desenvolvimento)

- **Formato do TCC [D1]:** pelo Manual de 2025, o enquadramento mais natural é **método científico (estudo quantitativo)**: a pergunta é de descoberta, e não há uma organização-cliente para um plano de consultoria. Confirmar. Muda a estrutura do texto, não o dashboard.
- **Avaliação com usuários:** o Manual prevê TCLE (e possivelmente comitê de ética) para pesquisa com pessoas. Como fazer a avaliação com gestores?
- **Indicadores formais [D2]:** nome, fórmula, unidade e interpretação de cada indicador. Serão propostos junto com a especificação do dashboard.
- **Testes de sensibilidade [A4]:**
  - sem 2021;
  - sem 2025 na camada estadual;
  - IDHM Renda × IDHM total;
  - versão B do gasto estadual;
  - painel balanceado;
  - gasto médio do biênio.

  A lista está suficiente?
- **Uso de IA [D5]:** como você prefere que seja documentado no Método?

## 4. Principais limitações (lista completa na seção 10 do registro)

- O nível do gasto depende da fonte, sobretudo nas capitais.
- Só entram redes com nota divulgada; redes pequenas ficam sub-representadas.
- O IDHM existe só por UF e só até 2024: a edição de 2025 fica sem esse controle.
- O desempenho é a proficiência média da rede, não a de cada aluno.
- A edição de 2021 foi afetada pela pandemia.
- A camada estadual tem só 27 unidades.
- O gasto municipal usado (Ensino Fundamental) não separa Anos Iniciais de Finais e exclui a Educação Infantil.
- Os resultados são de associação, não de causalidade.

## 5. Uso de IA

O Manual exige informar e discutir previamente o uso de IA. Usamos assistente de IA no desenvolvimento do código de tratamento dos dados e na organização dos registros. Todas as decisões são nossas e verificáveis no código e nos diagnósticos.
