# MuuFeed — Casos de teste finais (v10)

Todos os insumos e preços a seguir são **dados ilustrativos de validação de software**, não recomendações zootécnicas nem cotações de mercado. Nunca fornecer as formulações a animais sem avaliação profissional.

## 0. Dados-base do lote (reutilizar nos testes 1 a 8)

| Campo | Valor a informar |
| --- | --- |
| Nome | `Lote QA Hackathon` |
| Número de vacas | `30` |
| Raça | `Holandesa` |
| Estado fisiológico | `Vaca em lactação` |
| Idade média | `820,8` **dias** |
| Peso médio | `624,8` kg |
| Ordem de lactação | `1` |
| Dias em lactação | `100` |
| Leite | `25,062` kg/vaca/dia |
| Gordura do leite | `4,55` % |
| Proteína do leite | `3,66` % |
| ECC/BCS avançado | `3` |
| Lactose avançada | `4,85` % |
| Peso adulto avançado | `700` kg |
| Dias de gestação avançado | `46` |

A idade do PDF deverá ser próxima de `820,80 dias (821 dias)`; raça `Holandesa`; ordem de lactação `1ª`. Use separador decimal aceito pelo widget Streamlit.

## 1. Ingredientes/preços do fluxo assistido

Confirmar a disponibilidade dos seguintes **seis alimentos**, com preços em R$/kg de matéria natural (MN):

| Ingrediente | R$/kg MN |
| --- | ---: |
| Silagem de milho, típica | `0,30` |
| Feno de capim-bermuda | `1,00` |
| Milho grão seco, moagem média | `1,15` |
| Polpa cítrica seca | `1,35` |
| Farelo de soja, solvente (48 PB) | `2,45` |
| Farelo de canola | `2,30` |

Se usar uma fonte mineral no **teste de software**, adicionar separadamente `Sal comum (cloreto de sódio)` (original `Sodium chloride (salt)`), disponibilidade confirmada, preço ilustrativo `R$ 1,00/kg MN`, **máximo operacional `0,12 kg MN/vaca/dia`** para reproduzir o ensaio anterior. Esse teto de ensaio não é um máximo universal seguro nem prescrição.

## 2. Casos por fluxo

### A — Sugestão automática: controle simples

1. Carregue o lote-base.
2. Abra **Sugestão automática**, confirme os seis ingredientes e preços acima.
3. Abra **Formular dieta**: consumo MS **manual `24,521` kg/vaca/dia**; teto por ingrediente `60%` da MS; FDN, amido e FDNf **em branco**.
4. Desmarque Ca/P, Na e Mg/Cl/K.
5. Formule e exporte PDF.

**Conferir:** status `candidata_experimental` ou diagnóstico de falha (nunca aprovação total); MS ~24,52 kg; nenhum ingrediente >60%; custos por item e resumo coerentes; seis minerais informados quando NASEM tiver dados; avisos de déficits não impostos. Cenário anterior, sem mudanças, resultou próximo a **R$ 28,03/vaca/dia** e silagem 60%.

### B — Sugestão automática: Ca/P/Na e sal (teste de restrição)

Repita A com as mesmas entradas e teto de 60%, **com sal disponível** e máximo `0,12 kg MN/vaca/dia`. Marque **Ca/P absorvidos** e **Na absorvido**; deixe Mg/Cl/K desmarcado para comparação. Exporte PDF.

**Conferir:** regras `R_CA_ABS`, `R_P_ABS`, `R_NA_ABS`; todos esses balanços devem atender se houver candidata; sal pode ser 0 ou positivo dependendo da solução; não exceder máximo definido; preço e custo preservados. No ensaio anterior, candidato ~**R$ 29,16/vaca/dia**, sal ~0,08 kg MN/dia. O resultado exato pode variar (mínimo local).

### C — Sugestão automática: seis macrominerais exigidos

Repita B, **agora marcando Mg/Cl/K absorvidos** também. Marque Ca/P, Na, Mg/Cl/K; sal e demais entradas iguais. Exporte PDF ou capture diagnóstico.

**Conferir:** se houver candidata, todas as seis restrições absorvidas impostas devem atender e as regras aparecer. Se **não houver candidata**, a tela deve mostrar falha/diagnóstico e **não** disponibilizar dieta como se fosse aprovada. Não force saltos em doses para fabricar solução.

### D — Formulação manual: quatro ingredientes + FDN/amido

Na página **Ingredientes e preços**, selecione **somente**:

| Ingrediente/NASEM | R$/kg MN |
| --- | ---: |
| Farelo de alfafa (`Alfalfa meal`) | `1,50` |
| Farelo de canola (`Canola meal`) | `2,00` |
| Silagem de milho, típica (`Corn silage, typical`) | `0,45` |
| Milho grão úmido, moagem grossa (`Corn grain HM, coarse grind`) | `1,20` |

Lote-base, consumo manual **24,521 kg MS/dia**, **FDN mínima = 25%**, **amido máximo = 30%**, FDN de forragens em branco, teto operacional em branco, Ca/P, Na e Mg/Cl/K **desmarcados**.

**Conferir:** FDN ≥25% MS; amido ≤30% MS; MS ~24,521 kg; energia e MP verificados; custo na coluna *Custo* somado, preços unitários não somados. Em ensaios anteriores o custo foi ~**R$ 36,13/vaca/dia** com 38,46% FDN e 26,40% amido, sem promessa de resultado idêntico.

### E — Analisar dieta existente (quantidades fixas)

Na página **Ingredientes e preços**, selecione `Silagem de milho, típica` e `Farelo de soja, solvente (48 PB)`; abra **Analisar dieta existente** e insira:

| Ingrediente | kg MN/vaca/dia | R$/kg MN |
| --- | ---: | ---: |
| Silagem de milho, típica | `20,00` | `0,30` |
| Farelo de soja, solvente (48 PB) | `3,00` | `2,45` |

**Conferir:** 23 kg MN, cerca de **9,75 kg MS**, **R$ 13,35/vaca/dia** e **R$ 400,50 por lote/dia** (30 vacas); quantidades **não são alteradas**; energia, proteína e minerais mostram déficits quando aplicável; PDF é de **análise**, não formulação.

### F — CMS estimado (equação NRC 2001)

Repita o **A**, mas escolha **consumo estimado NRC 2001** em vez de manual. Com lote-base espere consumo em torno de **21,48 kg MS/vaca/dia**. A composição e o custo poderão mudar; o CMS estimado deve ser explicitamente identificado como predição.

**Conferir:** não comparar R$ 25 da dieta menor diretamente com R$ 28 da dieta de 24,521 kg de MS como se fossem o mesmo volume nutritivo.

### G — Jersey: raça enviada ao modelo

Cadastre **novo lote de teste**, sem comparar diretamente com A:

| Campo | Valor |
| --- | --- |
| Nome | `Lote QA Jersey` |
| Vacas | `12` |
| Raça | `Jersey` |
| Idade | `1461` dias |
| Peso | `430` kg |
| Ordem de lactação | `2` |
| Dias em lactação | `120` |
| Leite | `18` kg/dia |
| Gordura | `5,00%` |
| Proteína | `3,80%` |
| ECC/BCS | `3` |
| Lactose | `4,85%` |
| Peso à maturidade | `500` kg |
| Gestação | `0` dias |

Execute análise E ou formulação D com CMS NRC estimado. **Conferir:** NASEM recebe `An_Breed=Jersey`; relatórios registram Jersey; resultado/erro precisa ser explicável. O cenário pode não ter candidata. Não espere obrigatoriamente exigências minerais diferentes do caso Holstein para toda dieta.

## 3. Testes negativos e de interface

| ID | Ação | Resultado esperado |
| --- | --- | --- |
| N1 | Buscar `soro de leite fresco` e `whey fresh` | Ambos localizam o mesmo nome original do alimento. |
| N2 | Buscar `selenito de sodio` e `selenite sodium` | Busca PT/EN e remoção de acento funcionam. |
| N3 | Buscar `sal comum` e `sodium chloride` | Mesmo alimento NASEM, sem troca do identificador interno. |
| N4 | No analisador, deixar **todas** as quantidades zero | Mensagem para informar quantidade positiva; sem PDF enganoso. |
| N5 | Retirar todos os ingredientes | Validação clara; sem crash. |
| N6 | Remover preço ou inserir preço zero | Validação clara em R$/kg MN; não executar com custo inválido. |
| N7 | Selecionar sal sem informar máximo por ingrediente | Bloqueio com mensagem; não usar suplemento mineral sem limite. |
| N8 | Informar idade `821` **dias** | Campo aceita sem erro de faixa de anos; relatório usa ~821 dias. |
| N9 | Informar um teto e mínimos incompatíveis | Retornar falha de formulação com diagnóstico, não dieta aprovada. |
| N10 | Alterar preço de apenas um ingrediente e recalcular | Custo atualizado; origem do preço preservada; verificar mudança possível na solução. |
| N11 | Abrir PDFs de sucesso e falha | Sem páginas vazias, tabelas cortadas ou status contraditórios. |
| N12 | Desconectar internet e rodar `./init.sh` | Fluxos e PDFs funcionam offline com dependências previamente instaladas. |
| N13 | Alterar dados do lote após formular | Resultado antigo invalidado; nova formulação usa lote novo. |
| N14 | Alterar quantidade da análise sem clicar em analisar novamente | Resultado anterior fica sinalizado/desatualizado, não exibido como atual. |

## 4. Critérios de consistência e evidências

- Ingredientes: ∑kg MS ≈ CMS configurado/estimado; ∑ participação em MS ≈ 100% (aplicar tolerância de arredondamento).
- Preço unitário não se soma; `custo item = kg MN × R$/kg MN`; `custo vaca = soma dos itens`.
- Lote/dia ≈ custo vaca/dia × número de vacas; custo mensal 30 dias ≈ lote/dia × 30. Compare com precisão interna, pois valores apresentados são arredondados.
- As regras aparecem **somente** se estiverem ativas e satisfeitas para a candidata.
- Nutrientes informativos não devem ser descritos como atendidos sem limites/exigências válidos.
- Sem candidata, **não** permitir exportar PDF de dieta como se ela estivesse validada.
- Em todo PDF: raça, idade, lote, CMS/origem, regras, preços ilustrativos, limitações e aviso profissional.

## 5. O que enviar para revisão final

1. Captura ou PDF de **A** (assistido controle).
2. PDF de **B** (Ca/P/Na com sal) e captura se falhar.
3. PDF/captura de **C** (todos seis minerais).
4. PDF de **D** (manual FDN/amido).
5. PDF de **E** (analisar dieta existente).
6. Captura **F** (CMS estimado ~21,48 kg).
7. Saídas `python -m pytest -q`, `python scripts/verificar_release_v10.py`.
8. Confirmação de `./init.sh` offline e `git status --short`.

> Regra de ouro: o resultado é **candidata experimental** ou **análise parcial**, não uma dieta clinicamente validada para alimentar animais.
