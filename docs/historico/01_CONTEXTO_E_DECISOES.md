# 01 — Contexto e decisões

## 1. Quem e o quê

- **Autores:** Henrique (cuida da ferramenta: extração, tratamento e integração dos dados em Python, e o dashboard em Power BI) e Guilherme, em dupla. Curso de Administração, FEA/USP.
- **Disciplinas:** TCC I e TCC II (EAD 600 e EAD 601), regidas pelo Manual de TCC 2025 do Departamento de Administração (ver arquivo 04).
- **Orientadora:** professora do Departamento de Administração. Acompanha por e-mail e reuniões no Zoom.
- **Perfil técnico do Henrique:** experiência em Python e análise de dados; já usou Power BI, sem aprofundamento. Preferiu Polars a pandas para a extração.
- **Usuário-alvo do produto:** gestor de secretaria de educação (a orientadora pediu que se definisse se estadual ou municipal; a proposta foi estadual, com leitura por município dentro do estado).

## 2. Cronologia das fases

**Fase 1 — Proposta original (setembro de 2026).** Um dashboard de indicadores do ENEM para a Secretaria de Educação do Estado, com pipeline ETL em Python, microdados do ENEM 2011–2025, Censo Escolar e IBGE. Os artigos de Leonardo Sales no Medium ("ENEM, parte 1 e parte 2": desempenho x perfil socioeconômico, ICP, gap racial controlado, só ENEM 2022) serviram de inspiração e devem ser citados como literatura cinzenta. Já existiam ferramentas parecidas no mercado, então o projeto se reposicionou para um híbrido de análise rigorosa e produto. Arquitetura escolhida: Python para ETL e estatística, Power BI como camada de apresentação.

**Fase 2 — Extract e Transform sobre ENEM e bases de contexto (setembro a outubro).** ENEM 2013–2023, IDHM, IDEB do Ensino Médio, Censo Escolar (infraestrutura) e IBGE (alfabetização). Achados principais:
- O código da escola (`CO_ESCOLA`) não existe nos microdados públicos do ENEM, por decisão do INEP baseada na LGPD.
- Em 2024 e 2025 o INEP separou o ENEM em arquivos sem chave em comum entre perfil do candidato e nota; 2024 saiu do escopo.
- Só 15,6% a 27,4% dos inscritos do ENEM têm escola (e município) vinculados, em todos os anos.
- Nas edições de 2013 a 2015, a nota de redação de quem faltou vem como zero, não como vazio.
- O IDEB é bienal e o IDHM anual só existe por UF.

**Fase 3 — E-mail da orientadora e reunião (02/10).** Ela pediu delimitar melhor a pesquisa para o TCC não ficar concentrado só no desenvolvimento da ferramenta (detalhes no arquivo 04). Preparamos um documento de 4 páginas (`Delimitacao_TCC_Reuniao.docx`). Segundo o Henrique, a reunião levou a um pivô, mas o resultado sobre o recorte geográfico não foi registrado.

**Fase 4 — Pivô: gasto público x desempenho (outubro).** O projeto passou a ser um trabalho de consultoria com uma pergunta central: o gasto público em educação se associa ao desempenho em prova nacional? Passos:
- O ENEM foi descartado como desfecho: é voluntário, tende a reunir os alunos mais preparados, inclui escola privada (que não recebe esse investimento) e só tem município para 15% a 27% dos inscritos. O PISA foi descartado porque é amostral e só dá resultado nacional e por grandes regiões.
- O Saeb/IDEB foi escolhido: nas escolas públicas é censitário, sai por município, rede e UF, e é bienal (2017–2025), o que coincide com a janela do SIOPE.
- A prévia do cruzamento mostrou que prefeituras quase não oferecem Ensino Médio. Por isso nasceu a **Opção D**, proposta pelo usuário: duas camadas, municipal e estadual, ambas com gasto do SIOPE/SICONFI e desfecho do Saeb.
- Fonte de gasto: SIOPE (API do FNDE) para o município e SICONFI (Tesouro Nacional) para os estados, porque o SIOPE não tem Minas Gerais (só 2024) e tem lacunas no RS.
- Extract das fontes novas: SIOPE, SICONFI, matrículas, IPCA e Saeb. Falta baixar o IDEB municipal de Anos Iniciais e Finais.

**Fase 5 — Migração para um projeto no Claude da conta empresarial (outubro de 2026).** Este dossiê foi gerado para dar continuidade sem perder contexto.

## 3. Decisões explícitas do usuário

1. Usar Python e Polars (não pandas) para extração e tratamento; Power BI para o dashboard.
2. Extrair todas as bases antes de transformar qualquer uma (reafirmado em outubro).
3. Tratar o projeto como MVP: documentar limitações em vez de resolver tudo.
4. Desagregar por rede (Estadual, Municipal, Federal) em vez de usar o agregado "Pública".
5. Não perseguir o ENEM 2024 nem 2025 (estrutura sem chave).
6. Opção D: camadas municipal e estadual com a mesma fonte de gasto, cada uma com o desfecho do ente que presta o serviço.
7. Critério de recorte: usar apenas provas em que o viés de seleção seja ausente ou pequeno.
8. Entregável preferido: dashboard com dados estaduais e municipais, quanto mais informação melhor.
9. Aceitou o Saeb/IDEB como a melhor base de desempenho.
10. Ordem de trabalho: concluir a base financeira, depois o Saeb (usando nota Saeb e não só IDEB).
11. Migrar o projeto para uma conta empresarial do Claude.

## 4. Propostas do assistente seguidas sem objeção (não confirmadas por escrito)

- Janela 2017–2025 (imposta pela disponibilidade do SIOPE e do Saeb).
- Municipal: SIOPE subfunção 361 paga ÷ matrículas do Fundamental da rede municipal. Estadual: SICONFI função 12 menos 12.364 ÷ matrículas da educação básica da rede estadual.
- Nota Saeb como medida principal de desempenho; IDEB e rendimento como secundárias.
- Valores em reais de 2025 (IPCA, média anual).
- Nunca misturar fontes de gasto dentro da mesma camada.
- Desfecho municipal principal: Anos Iniciais; camada estadual: Anos Finais e Médio.

## 5. Literatura e diferenciação

- "Gasto público municipal x desempenho no IDEB" é uma linha de pesquisa estabelecida no Brasil (artigos em SciELO, ANPEC, ENAP). Os achados costumam mostrar efeito defasado (cerca de quatro anos) e relação heterogênea entre estados. A maioria usa IDEB, não ENEM, e cobre um ano ou uma região.
- Diferenciação proposta: (1) painel multianual nacional com defasagens; (2) enquadramento de consultoria, com produto para o gestor; (3) ângulo de eficiência (quem entrega mais resultado por real investido) e não só correlação.
- Limite: a série do SIOPE começa em 2017, então defasagem de 4 anos só vale para IDEB de 2021 em diante. O SICONFI estadual começa em 2014.

## 6. Perguntas analíticas (rascunho do assistente, a validar com a orientadora)

1. O gasto por aluno (real) do município no Fundamental se associa à nota Saeb dos Anos Iniciais e Finais da rede municipal, com defasagens de 0 a 2 anos?
2. Dentro do mesmo município, aumentos de gasto por aluno precedem melhora da nota (efeito fixo)?
3. Quais municípios estão acima ou abaixo da nota esperada dado gasto e contexto (eficiência)?
4. Na camada estadual, o gasto estadual por aluno da rede se associa à nota de Anos Finais e Médio da rede estadual, por UF?
5. A relação muda por porte do município ou região?
6. A associação é robusta à troca da fonte de gasto e à exclusão de 2021?

## 7. Documento original do TCC e referências

O PDF "TCC — Análise de dados voltados ao desenvolvimento de insights e indicadores de desempenho no ENEM" é a proposta original (de antes do pivô). Seções: introdução, problema, objetivos, justificativa, referencial (avaliações em larga escala, determinantes socioeconômicos, TRI, dashboards e BI), metodologia, resultados esperados, bibliografia.

**Atenção:** várias referências dessa bibliografia não foram verificadas por nós (por exemplo, Benjamin e Kim 2018, Dehghan et al. 2020 e a versão de Franco et al. 2015 em "Cadernos de Pesquisa"). Confirmar a existência de cada uma antes de citar no TCC.
