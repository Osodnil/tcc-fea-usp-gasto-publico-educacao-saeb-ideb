# Registro de decisões de método

Decisões tomadas durante o pipeline que afetam o resultado final. Cada uma indica o status de validação com a orientadora e onde está implementada, para poder ser revertida.

## D1. IDHM por UF com defasagem de um ano (t−1)

- **Data:** 2026-10-21
- **Status:** provisória — **pendente de validação com a orientadora**
- **Decisão:** o controle socioeconômico de cada edição do Saeb é o IDHM da UF do ano anterior (Saeb 2017 ← IDHM 2016, …, Saeb 2025 ← IDHM 2024).
- **Motivo:** a série anual do IDHM por UF (Radar IDHM, PNUD/FJP/IBGE, base PNAD Contínua, divulgada em 26/05/2026) termina em 2024; não há IDHM 2025. Usar t−1 em todas as edições evita imputar valores e trata as cinco edições da mesma forma.
- **Alternativas consideradas:**
  - Repetir o IDHM 2024 em 2025, marcado como imputado: mexe só em 2025, mas trata uma edição de forma diferente das outras. **Sugerida como teste de sensibilidade.**
  - Projetar 2025 pela tendência: descartada (valor inventado).
  - Excluir 2025 das estimações com IDHM: descartada (perde a edição de maior cobertura).
- **Implementação:** `src/Transform/Transform_IDHM.py`, coluna `ANO_REF_SAEB = ANO + 1` (Int32). O merge casa `saeb_*_transformado.ANO` com `idhm_transformado.ANO_REF_SAEB`.
- **Como reverter:** no merge, casar com `ANO` em vez de `ANO_REF_SAEB` (e decidir o tratamento de 2025). Nada mais precisa mudar.
- **Para o Método:** "O controle socioeconômico é o IDHM da UF no ano anterior à aplicação do Saeb (t−1), pois a série do PNUD termina em 2024."
