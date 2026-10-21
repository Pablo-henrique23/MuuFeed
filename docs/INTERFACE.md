# Interface do MuuFeed

## Arquitetura
```
app.py ─► ui/pages.py ─► ui/state.py ─► services/formulation_service.py ─► [Formulador real]
              │                 │                 ▲
              │                 └► services/feed_catalog.py (biblioteca NASEM, somente leitura)
              └► models/contracts.py (contratos; sem Streamlit)
```
- `models/`: contratos de entrada e saída. Independentes do Streamlit, testáveis sem interface.
- `services/feed_catalog.py`: lê `NASEM_feed_library.csv` (284 alimentos) sem modificar valores; UIDs originais preservados; nomes em português via `data/feed_names_pt.json` (sem tradução, mantém o original); busca sem acento em PT e EN.
- `services/formulation_service.py`: único ponto de integração. Padrão: `FormuladorNaoConectado`, que não calcula nada.
- `ui/`: só apresentação. Nenhuma regra nutricional.
- `data/demo_prices.json`: preços ILUSTRATIVOS (R$/kg de MN), sem fonte de mercado. Origem exibida na tela (“ilustrativo” ou “informado”).

## Contrato (`models/contracts.py`)
**Entrada** `RequisicaoFormulacao`: `lote` (nome, n_vacas, raça, idade em dias via `idade_dias`, peso, ordem de lactação, dias em lactação, estado fisiológico, leite, gordura, proteína, e avançados com hipóteses padrão), `ingredientes` (uid original NASEM, nome original, `ms_pct`, `preco_mn_brl_kg`, `origem_preco`, mín./máx. opcionais do usuário em kg MN), `opcoes.objetivo`, `data_ref_precos`.
`Lote.para_animal_nasem()` entrega os campos do lote nas chaves de `animal_input` do nasem_dairy; o formulador completa o restante.
Unidade-base: kg de MS por vaca/dia. `Ingrediente.limites_ms()` e `preco_ms_brl_kg` convertem MN ↔ MS.

**Saída** `ResultadoFormulacao`: `status` ∈ {otimo, inviavel, escopo_nao_suportado, erro, nao_conectado, demonstracao}, `itens` (kg MS, kg MN, custo), `custo_vaca_dia`, `indicadores` (ingerido × exigido), `regras` acionadas, `restricoes` (atendida/violada/nao_avaliada), `nao_avaliadas`, `avisos`, `modelo_referencia`. **Não existe campo “dieta completa”**: só aparece o que foi verificado.

## Relatório PDF (`services/pdf_report.py`)
`gerar_relatorio_pdf(resultado, lote, ingredientes, data_ref_precos)` usa ReportLab, offline e sem Streamlit. Apresenta só os dados do contrato (não recalcula a dieta); dados ausentes são declarados como ausentes.
- `status="otimo"`: botão **Exportar relatório PDF**. `status="demonstracao"`: PDF com marca d'água “EXEMPLO DE LAYOUT”. Qualquer outro status: botão desabilitado e o gerador levanta `ValueError`.
- O serviço carimba `id_formulacao` e `executada_em` em todo resultado; o PDF mostra também a data de geração.
- Custo do lote e do mês dependem de `lote.n_vacas` (mesma dieta para todas) e de 30 dias/mês; ambos aparecem como hipóteses no documento.

## Ambiente
`nasem_dairy` exige `numpy<2`. Use **Python 3.12** com `pip install -r requirements.txt` (`pyarrow<18`). O app avisa na tela se o `pyarrow` não carregar. O botão Deploy do Streamlit está oculto (`toolbarMode = "minimal"` + CSS).

## Como conectar o formulador
1. Crie uma classe com `verificar_escopo(req) -> (bool, motivo)` e `formular(req) -> ResultadoFormulacao`.
2. Aponte para ela: `set MUUFEED_FORMULADOR=meu_modulo:MinhaClasse` (Windows) / `export ...` (Linux) antes de `streamlit run app.py`, ou chame `registrar_formulador(obj)`.
3. A interface passa a mostrar “Formulador: conectado”. Exceções e status inválidos viram `status="erro"` sem derrubar a tela.

## Escolhas de interface
- **Formular dieta** é a página central: destaque no menu e botão único; só habilita com lote e preços válidos.
- O botão nunca produz números. Sem formulador: “nenhuma dieta foi calculada”. O **cenário demonstrativo** (Resultados) usa a dieta de exemplo do nasem_dairy avaliada pelo pacote, com faixa vermelha permanente “NÃO É UMA DIETA CALCULADA PELO MUUFEED”.
- Valores padrão dos campos avançados são **hipóteses** (origem: exemplo `lactating_cow_test` do pacote) e aparecem como aviso ao salvar o lote.
- Limites de validação de entrada são de **plausibilidade** (evitam erro de digitação), não regras nutricionais.
- Fontes do sistema, sem Google Fonts: funciona offline.
- Custo mensal = custo do lote/dia × 30 (convenção da interface).

## Limitações conhecidas
- Estados fisiológicos oferecidos: vaca em lactação e vaca seca. Se o formulador não suportar algum, deve recusar em `verificar_escopo`.
- “Raça” é informativa; não altera cálculos.
- Nomes em português cobrem parte da biblioteca; o restante mantém o nome original em inglês.
- Relatório exportável ainda não implementado (o contrato já carrega os dados necessários).
