# MuuFeed — motor experimental v2: FDN e amido

Este pacote é **substituição incremental** do motor existente. Não muda as assinaturas já utilizadas pelo adaptador: dois parâmetros novos em `FormulationRequest` são opcionais, com `None` por padrão.

## Instalação

No diretório `~/MuuFeed`, faça checkpoint com Git. Copie `formulation_engine_v2.py` para `formulation_engine.py`, preservando o arquivo anterior no Git. Execute `python -m pytest -q` e `python check_nasem_v2.py` com a venv ativada.

## O que passa a funcionar

- Consulta `Fd_NDF` e `Fd_St` nos registros correspondentes aos ingredientes selecionados na biblioteca original `NASEM_feed_library.csv`.
- Calcula FDN e amido da mistura em **% da MS**, ponderados pelos kg de MS de cada ingrediente. Dados ausentes nunca viram zero artificial.
- Sem limites: mostra os valores como **informativos** em `nutrient_composition`, sem declará-los restrições verificadas.
- Limites explícitos, quando presentes: `min_ndf_pct_dm` e `max_starch_pct_dm` em `FormulationRequest`; entram como desigualdades no SLSQP, são conferidos independentemente no resultado final e aparecem nas regras `R_FDN_MIN` e `R_AMIDO_MAX` e em `constraints_checked`. Não são recomendação nutricional automática.
- Retém `candidata_experimental`; fibra fisicamente efetiva, minerais, vitaminas e limites de inclusão continuam não avaliados.

## Integrar à interface (Claude)

1. No adaptador `services/nasem_adapter.py`, após `result = formulate_diet(...)`, converter `result['nutrient_composition']` em dois `Indicador` com unidade `% da MS`. Quando limite for `None`, usar status `informativo`; quando configurado e atingido, status `atende` (conferir nomes admitidos por `models/contracts.py`).
2. Se os limites passarem a ser oferecidos em formulário, adicionar campos opcionais no contrato `OpcoesFormulacao` e repassá-los para `FormulationRequest(min_ndf_pct_dm=..., max_starch_pct_dm=...)`. Deixar os dois vazios por padrão; **não** assumir valores como recomendação NASEM.
3. Para regras, ler `activated_rules` e preservar `source` quando disponível. As listas `constraints_checked` e `constraints_not_checked` já determinam a tabela de restrições e o PDF.
4. Atualizar a mensagem fixa “satisfaz apenas MS, ME e MP” do adaptador para gerar a descrição dinamicamente a partir de `constraints_checked`.
5. Não alterar `services/financeiro.py` nem a rotina PDF de custos.

## Testes

`python -m pytest test_formulation_engine_v2.py -q` testa o algoritmo com avaliador fictício e catálogo sintético. Isso **não substitui** o teste real em `check_nasem_v2.py` com `nasem_dairy`.

**Importante:** o script de teste usa `25% de FDN mínima` e `30% de amido máximo` apenas como **números demonstrativos escolhidos para exercitar o software**; não constituem requisitos NASEM validados nem orientação de alimentação. Limites reais dependeriam de cenário e fonte técnica documentada.
