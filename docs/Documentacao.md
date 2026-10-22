# MuuFeed — Documentação completa do projeto

**Hackathon Rerum 2026.2 | Versão auditada a partir do ZIP do desenvolvedor | 22/10/2026**

## 1. Visão geral e motivação

O MuuFeed é um protótipo de sistema especialista para **apoiar a formulação de dietas de vacas leiteiras em lactação**. O desafio é combinar alimentos disponíveis e seus custos com exigências nutricionais calculadas a partir das características médias do lote. O usuário pode solicitar uma sugestão inicial de alimentos, formular com ingredientes escolhidos manualmente ou avaliar uma dieta existente.

**Valor do sistema:** centraliza lote, base alimentar, pré-triagem por composição, avaliação por modelo científico, otimização econômica e justificativas transparentes. A diferença em relação a uma planilha de soma de ingredientes está no uso de **exigências do NASEM 2021**, na otimização com restrições não lineares e na seleção preliminar dinâmica.

**O que ele não é:** um substituto de nutricionista/zootecnista, uma previsão garantida de produção de leite ou um algoritmo que ateste segurança completa de uma dieta. A formulação deve ser chamada de **candidata experimental** e avaliada por profissional habilitado para uso real.

## 2. Escopo e público

- **Público-alvo:** produtores, estudantes e técnicos que precisam examinar cenários de alimentação e custos; demonstração de hackathon.
- **Animal modelado:** vacas leiteiras **em lactação**; não existe formulação validada para vaca seca, novilha, bezerro ou bovino de corte no aplicativo atual.
- **Raças:** Holandesa (`Holstein`), Jersey (`Jersey`) e opção **Outra — genérica experimental** (`Other`). O nome digitado de uma raça genérica aparece no relatório, mas **não personaliza o ramo `Other`**.
- **Alimentos:** catálogo da biblioteca NASEM importado no ambiente (284 registros na instalação auditada), com rótulos PT-BR e busca pelo nome original inglês ou tradução.
- **Fonte de preços:** valores informados pelo usuário ou exemplos em `data/demo_prices.json`, explicitamente identificados como ilustrativos.
- **Execução:** aplicação Streamlit local; depende de instalação prévia de Python e bibliotecas, mas não consulta API online durante a formulação.

## 3. Fluxos de uso

### 3.1 Caracterização do lote

O usuário informa número de animais, peso vivo médio, idade, raça, ordem de lactação, dias em lactação, produção de leite (kg/vaca/dia), gordura e proteína do leite. Campos avançados permitem informar escore de condição corporal, lactose, peso à maturidade e dias de gestação. Os valores descrevem **o lote/cenário avaliado**, preferencialmente medidos; não são resultados desejados que a dieta automaticamente garante.

O `Lote` de `models/contracts.py` valida faixas de plausibilidade e converte idade para dias. `Lote.para_animal_nasem()` envia as chaves `An_StatePhys`, `An_Parity_rl`, `An_Breed`, `An_AgeDay`, `An_BW`, `An_BW_mature`, `An_BCS`, `An_LactDay`, `An_GestDay`, `Trg_MilkProd`, `Trg_MilkFatp`, `Trg_MilkTPp` e `Trg_MilkLacp`.

**Hipóteses complementares:** `services/nasem_adapter.py` obtém inicialmente `nd.demo('lactating_cow_test')`, substitui os campos conhecidos pelo lote e mantém valores de referência nos campos restantes. Na instalação testada, estes incluem `An_305RHA_MlkTP`, `An_AgeDryFdStart`, `An_GestLength`, `Env_DistParlor`, `Env_TempCurr`, `Env_Topo`, `Env_TripsParlor`, `Fet_BWbrth`, `Trg_FrmGain` e `Trg_RsrvGain`. São **hipóteses do cenário demonstrativo, não medições da fazenda**. Também são herdadas escolhas de equações e parâmetros de infusão. O diagnóstico pode ser consultado em `scripts/verificar_hipoteses_nasem_v19.py`.

### 3.2 Sugestão automática de ingredientes

O modo guiado lê os dados do lote e solicita **antes da sugestão** os limites opcionais: FDN mínima, amido máximo, FDN de forragens mínima, extrato etéreo máximo e máxima participação individual. As caixas de minerais definem quais balanços serão exigidos na formulação final.

`services/constraint_guided_suggestion.py` percorre o catálogo disponível, descarta itens sem dados necessários de composição/preço e não seleciona automaticamente rações exclusivas para bezerros nem suplementos que precisam de inclusão individual supervisionada. A instalação verificada anteriormente possuía **23 candidatos elegíveis com preço conhecido**, embora o catálogo total tenha 284 itens; a cobertura dos preços pode mudar.

Uma **programação linear** procura uma composição **quimicamente compatível** com os limites de fibra/amido/gordura/participação. Sua solução preliminar é usada para definir candidatos. A interface também acrescenta opções de grupos distintos (volumosos, energéticos, proteicos, fibrosos) e pondera heurísticas simples conforme produção de leite e dias em lactação.

O produtor confirma disponibilidade e preço; a seleção marcada é reavaliada pela triagem química. Essa etapa **não calcula ainda ME, MP ou minerais absorvidos**, não sabe as análises bromatológicas reais e pode sugerir um conjunto para o qual o otimizador posterior não encontre candidata.

### 3.3 Formulação personalizada / final

Depois de selecionar ou aceitar os ingredientes, o usuário informa o CMS ou solicita uma estimativa NRC 2001. Pode ajustar os mesmos limites nutricionais opcionais, teto global e mínimos/máximos individuais por ingrediente. O adaptador `services/nasem_adapter.py` transforma preços e quantidades em contratos `FeedChoice` / `FormulationRequest`.

`formulation_engine.py` usa o **SciPy SLSQP** com seis pontos iniciais para minimizar custo enquanto satisfaz consumo total, energia metabolizável, proteína metabolizável e restrições ativas. O fornecimento e a exigência de ME/MP/minerais são obtidos do NASEM; o motor também calcula indicadores químicos a partir da composição de referência dos ingredientes. Cada solução é reavaliada antes de ser aceita.

A resposta contém quantidades em kg MS e kg MN, participações percentuais, custos, indicadores, restrições atendidas/não avaliadas, regras, avisos e eventual diagnóstico de falha. A interface e o relatório PDF leem o mesmo resultado estruturado; o PDF **não reotimiza** a dieta.

### 3.4 Análise de dieta existente

O usuário escolhe ingredientes, preços e as quantidades reais em **kg de matéria natural por vaca/dia**. `services/diet_analysis.py` converte as quantidades em matéria seca, fixa a dieta e chama NASEM para calcular ingestão/exigências. **Não altera quantidades nem minimiza custo**. O relatório independente é gerado por `services/analysis_pdf.py` e pode mostrar nutrientes abaixo das exigências mínimas.

## 4. Notação e unidades

| Símbolo | Significado | Unidade |
|---|---|---|
| `i` | Índice de ingrediente | — |
| `x_i` | Quantidade diária de matéria seca do ingrediente `i` | kg MS/vaca/dia |
| `d_i` | Fração de matéria seca do ingrediente (`Fd_DM/100`) | kg MS/kg MN |
| `m_i` | Quantidade em matéria natural | kg MN/vaca/dia |
| `p_i` | Preço unitário em matéria natural | R$/kg MN |
| `D` | Consumo total de matéria seca usado na formulação | kg MS/vaca/dia |
| `n_i`, `s_i`, `f_i`, `e_i` | Frações de FDN, amido, FDN de forragens e extrato etéreo | fração de MS |
| `N` | Número de vacas no lote | vacas |

**Conversão:**

\[m_i = \frac{x_i}{d_i} = \frac{x_i}{\mathrm{MS}_i/100}\]

Por exemplo, 6 kg MS de uma silagem a 35% de MS equivalem a `6/0,35 ≈ 17,14 kg MN`. O custo usa os 17,14 kg MN, não os 6 kg MS. Todos os limites da composição são calculados sobre a **MS**.

## 5. Estimativa opcional do CMS: NRC (2001)

O sistema aceita CMS informado ou calcula uma **estimativa**, utilizando peso vivo, produção, gordura do leite e semanas em lactação:

\[\mathrm{FCM}_{4\%} = 0{,}4 \cdot M + 15\cdot M\cdot(g/100)\]

\[\widehat{\mathrm{CMS}} = \big[0{,}372\,\mathrm{FCM}_{4\%} + 0{,}0968\,PV^{0{,}75}\big]\cdot\left[1-\exp\left(-0{,}192\left(\frac{DEL}{7}+3{,}67\right)\right)\right]\]

Em que `M` é leite (kg/dia), `g` é gordura do leite em %, `PV` é peso vivo em kg e `DEL` são dias em lactação. O código está em `services/dmi_estimator.py`, implementando a equação reportada no NRC (2001), citada em referências de nutrição leiteira [R2].

**Importante:** o consumo é fornecido ao NASEM como **dado fixo** `Trg_Dt_DMIn = D` com `DMIn_eqn = 0`. O NASEM **não está estimando espontaneamente o consumo nesse fluxo**; a estimativa pode diferir do consumo real do lote. No fluxo de análise existente, `D` é calculado a partir das quantidades informadas.

## 6. Formulação econômica e matemática

### 6.1 Objetivo de menor custo

\[\min_{x}\;C(x) = \sum_{i=1}^{k}\frac{p_i}{d_i}\,x_i\]

O preço efetivo por kg de MS do ingrediente é `p_i/d_i`. O custo final é:

\[C_{\mathrm{vaca/dia}}=\sum_i p_i\,m_i;\qquad C_{\mathrm{lote/dia}}=N\,C_{\mathrm{vaca/dia}};\qquad C_{\mathrm{lote/30d}}=30N\,C_{\mathrm{vaca/dia}}.\]

O mês é uma **convenção financeira de 30 dias**. Preços ilustrativos não são cotações atuais.

### 6.2 Restrições de massa e inclusão

\[\sum_{i=1}^{k}x_i=D,\quad l_i\leq x_i\leq u_i,\quad x_i\geq0.\]

Se o usuário marca teto global de participação `t%`:

\[x_i\leq D\cdot t/100.\]

Mínimos/máximos específicos por ingrediente são dados em **kg MN** e convertidos pelo teor de MS. O teto global é apenas **operacional**, não uma declaração de segurança nutricional individual.

### 6.3 Composição química da dieta

Com `q_{ji}` o teor do nutriente `j` no ingrediente `i`, em **% da MS**:

\[Q_j(x)\;(\%\mathrm{MS}) = \frac{\sum_i x_i\,q_{ji}}{D}.\]

Para FDN de forragens, somente os ingredientes classificados como **forragem** pela biblioteca entram no numerador:

\[\mathrm{FDNf}(x)=\frac{\sum_{i\in\mathcal F}x_i\,\mathrm{FDN}_i}{D}.\]

A classificação usa `Fd_Type` e `Fd_Category`; **FDNf química não equivale a fibra fisicamente efetiva (peNDF)**, pois a segunda também requer propriedades físicas, como distribuição de tamanho de partículas.

Restrições opcionais:

\[\mathrm{FDN}(x)\geq L_{\mathrm{FDN}},\quad \mathrm{FDNf}(x)\geq L_{\mathrm{FDNf}},\quad \mathrm{Amido}(x)\leq U_{\mathrm{amido}},\quad \mathrm{EE}(x)\leq U_{\mathrm{EE}}.\]

As propriedades vêm das colunas `Fd_NDF`, `Fd_St` e `Fd_CFat`. Valor ausente **não é assumido como zero** quando a restrição depende dele. O limite sugerido inicialmente de EE = 7% é **condicional e ajustável**, não um máximo universal de segurança. A Tabela 5-1 do NASEM 2021 [R1] relaciona, em condições específicas de dieta total misturada, **mínimo 19% de FDN de forragens, mínimo 25% de FDN total e máximo 30% de amido**; não são prescrições universais.

### 6.4 Exigências NASEM 2021

O pacote `nasem_dairy` calcula requisitos e oferta em função do lote, da dieta, da seleção de equações e das hipóteses disponíveis. O MuuFeed impõe por padrão:

\[\mathrm{An\_MEIn}(x)\geq\mathrm{Trg\_MEuse}(x),\quad \mathrm{An\_MPIn\_g}(x)\geq\mathrm{An\_MPuse\_g\_Trg}(x).\]

Os valores são respectivamente **Mcal/dia** e **g/dia**. Outros nutrientes que podem ser ativados **independentemente** são Ca, P, Na, Mg, Cl e K **absorvidos**:

\[A_j(x)\geq R_j(x)\qquad (j\in\{\mathrm{Ca,P,Na,Mg,Cl,K}\}).\]

Aqui `A_j` é a ingestão **absorvida** do mineral em **g/dia** e `R_j` a exigência estimada também em **g/dia**. Não confundir fornecimento total com absorvido, nem **atendimento ao mínimo** com ausência de excesso ou toxicidade.

As equações fisiológicas detalhadas do NASEM não são reinventadas dentro do projeto: são executadas pela biblioteca `nasem_dairy`, conforme a publicação NASEM (2021) e o código oficial [R1, R3]. `services/nasem_requirements.py` interpreta os seis balanços e seus estados.

### 6.5 Solução numérica

O problema é não linear porque ME, MP e minerais podem variar com a dieta segundo o NASEM. O motor usa **Sequential Least Squares Programming (SLSQP)** via `scipy.optimize.minimize`, com **seis inicializações** (distribuição inicial, custo e pontos pseudoaleatórios de semente fixa). São impostas restrições de igualdade para MS e desigualdades para nutrientes e inclusões.

Mesmo quando o SLSQP retorna `success`, a solução é **verificada novamente** quanto à soma MS, limites de cada ingrediente, ME, MP, minerais marcados e limites químicos. Se a candidata falhar na verificação, ela não é aceita. O sistema pode não encontrar candidata com um conjunto de ingredientes e limites mesmo quando existiria uma opção em outro conjunto; **não é prova matemática de inviabilidade global**. O algoritmo encontra **mínimos locais**, sem garantia do menor custo global.

## 7. Pré-triagem linear da sugestão dinâmica

A seleção inicial é diferente da formulação NASEM. A pré-triagem define `y_i = x_i/D` (frações de MS):

\[\min_y\sum_i (p_i/d_i)\,y_i,\qquad \sum_i y_i=1,\quad 0\leq y_i\leq t/100.\]

Ela verifica, quando informados:

\[\sum_i y_i\,n_i\geq L_{\mathrm{FDN}}/100,\quad \sum_i y_i\,s_i\leq U_{\mathrm{amido}}/100,\]

\[\sum_{i\in\mathcal F}y_i\,n_i\geq L_{\mathrm{FDNf}}/100,\quad\sum_i y_i\,e_i\leq U_{\mathrm{EE}}/100.\]

A biblioteca SciPy/HiGHS (`scipy.optimize.linprog`) resolve essa combinação **apenas química**. O MuuFeed exibe os ingredientes ativos e reservas de grupos diferentes, com ranqueamento heurístico pelo estágio de lactação/produção. O resultado da LP não é uma dieta final: ele deve passar por confirmação e pela etapa NASEM/SLSQP. A triagem não inclui ME, MP nem seis minerais absorvidos.

## 8. Regras implementadas e interpretação

| Regra/indicador | Origem | Estado |
|---|---|---|
| Matéria seca total | CMS escolhido ou calculado | Obrigatório |
| ME e MP | NASEM 2021 | Mínimos obrigatórios |
| FDN total mínima | Biblioteca NASEM + mínimo do usuário | Opcional |
| FDN de forragens mínima | Biblioteca NASEM + mínimo do usuário | Opcional |
| Amido máximo | Biblioteca NASEM + máximo do usuário | Opcional |
| Extrato etéreo máximo | Biblioteca NASEM + teto do usuário | Opcional |
| Ca e P absorvidos | NASEM 2021 | Mínimos opcionais, em conjunto |
| Na absorvido | NASEM 2021 | Mínimo opcional |
| Mg, Cl e K absorvidos | NASEM 2021 | Mínimos opcionais, em conjunto |
| Teto global / limites individuais | Usuário | Operacionais, opcionais; casos especiais exigem teto individual |
| Vitaminas/microminerais/peNDF/limites superiores | Dados e regras ainda insuficientes | **Não verificados integralmente** |

**“Atende”** significa somente que o indicador respeitou o limite da **regra ativada**, não que o valor seja ideal. Por exemplo, ME em 130% da exigência mínima continua aparecendo como `Atende` por ser comparação contra um **mínimo**. Algumas grandezas são exibidas só como `Informativo` quando nenhum limite foi configurado.

## 9. Catálogo e proteção dos dados

`services/feed_catalog.py` carrega a biblioteca NASEM original do pacote externo sem alterar seus identificadores; `services/feed_translation.py` e `data/feed_names_pt.json` fornecem nomes em português e a busca aceita também o inglês. Traduções não modificam composição nutricional. `data/demo_prices.json` armazena preços de **demonstração**.

Auditoria anterior no ambiente do autor: **284 ingredientes, 284 com MS válida e classificação química de forragem, 281 com FDN e 281 com amido informados; 68 com pelo menos uma lacuna entre 15 nutrientes monitorados**. Ausência nutricional deve permanecer ausente até haver análise confiável; nunca preencher automaticamente com zero. Ingredientes exclusivos de bezerros são rejeitados no fluxo atual; certos sais, NNP, premixes e gorduras concentradas exigem teto operacional explícito informado pelo usuário e responsável técnico.

A lista `referencias.txt` contém também **anotações de estudo e percentuais orientativos sem análise individual de aplicabilidade**. É preservada como referência histórica, mas essas anotações **não são regras automáticas nem limites universais do software**.

## 10. Arquitetura e dependências

```text
app.py [Streamlit]
  ├── ui/pages.py + ui/state.py [telas e estado da sessão]
  ├── models/contracts.py [Lote, Ingrediente, opções, resultados]
  ├── services/feed_catalog.py + feed_translation.py [catálogo e busca PT/EN]
  ├── services/constraint_guided_suggestion.py [LP/HiGHS preliminar]
  ├── services/formulation_service.py [serviço e tratamento de exceções]
  │     └── services/nasem_adapter.py [tradução contratos → NASEM]
  │           └── formulation_engine.py [SciPy/SLSQP; NASEM; validação]
  ├── services/diet_analysis.py [dieta existente, quantidades fixas]
  ├── services/financeiro.py [custos e consistência]
  └── services/pdf_report.py + analysis_pdf.py [PDF, sem novos cálculos]
```

**Tecnologias:** Python 3.12, pandas, NumPy 1.x, SciPy, Streamlit, Plotly, PyArrow, ReportLab, pypdf (testes), `nasem_dairy` e pytest. As restrições de versão estão em `requirements.txt`; o ambiente virtual `.venv` é local e não integra a entrega.

**Responsabilidades:** a interface não implementa equações nutricionais; os modelos guardam dados e limites; o adaptador alimenta o pacote NASEM; a otimização busca composições; os relatórios apresentam o resultado estruturado. Os identificadores NASEM originais são mantidos para que os cálculos funcionem; traduções são uma camada visual.

## 11. Instalação, execução e verificação

1. Instale **Python 3.12**.
2. Crie ambiente virtual e instale dependências conforme `README.md`.
3. Inicie `./init.sh` na raiz.
4. Execute `python -m pytest -q`.
5. Rode verificadores de catálogo, seleção guiada, minerais, raça e hipóteses (em `scripts/`).
6. Faça testes manuais dos três fluxos e de uma situação sem candidata.
7. Confira preços, números do lote, composição, alertas e PDFs e mantenha `referencias.txt`.

**Testes reproduzíveis:** `tests/` possui testes do motor com avaliadores artificiais, da interface, das regras, catálogos, mineralização e PDFs. Alguns testes exigem o `nasem_dairy`, Streamlit e PyArrow instalados. Os scripts `scripts/auditar_catalogo_nutricional.py`, `scripts/verificar_selecao_guiada_v18.py` e `scripts/verificar_hipoteses_nasem_v19.py` verificam a instalação real.

## 12. Limitações científicas e técnicas

1. **Parâmetros demonstrativos:** as 10 entradas animais remanescentes do exemplo NASEM e escolhas de equações/infusões são hipóteses até serem coletadas ou validadas.
2. **CMS fixo:** mesmo quando estimado por NRC, não é medição de consumo espontâneo e afeta fortemente custo e composição.
3. **Composição de referência:** matéria seca e nutrientes reais variam por manejo, clima e processamento. A análise bromatológica do lote real é recomendável.
4. **Raças:** `Other` usa generalizações do pacote; não há validação específica para uma raça informada.
5. **Estados fisiológicos:** apenas vacas em lactação; modelos para vacas secas, novilhas e corte não integrados.
6. **Insumos especiais:** máximos individuais informados pelo usuário não são garantia de dose segura nem de ausência de interação.
7. **Nutrientes incompletos:** vitaminas, microminerais, limites superiores, água, DCAD, perfil lipídico, balanço eletrolítico e peNDF permanecem parciais ou não implementados.
8. **Interpretação de excesso:** cumprir um mínimo de mineral não certifica ausência de excesso; o cloro absorvido em porcentagem da exigência mínima não é comparação com limite tóxico.
9. **Modelo matemático:** SLSQP é local; o algoritmo pode falhar na busca mesmo com soluções matematicamente possíveis.
10. **Preços:** exemplos são ilustrativos, não cotações; resultados econômicos dependem dos preços informados.
11. **Cenário médio:** o cálculo utiliza um animal representativo do lote; não modela a variação individual entre animais.
12. **Validação profissional:** o sistema não deve ser apresentado como uma prescrição nutricional completa para alimentação real.

## 13. Fórmulas de verificação financeira

Para cada alimento, `kg MN × R$/kg MN = custo individual (R$/vaca/dia)`. A soma dos custos individuais deve coincidir com o total por vaca, salvo diferenças de arredondamento; o lote/dia multiplica pelo número de animais, e mês utiliza 30 dias. `services/financeiro.py` compara preço/quantidade/custo e sinaliza inconsistências sem alterar a solução.

## 14. Exemplo didático (não prescrição)

Considere dois alimentos fictícios A e B, com D = 10 kg MS/vaca/dia. O alimento A possui MS de 40% e preço R$ 0,50/kg MN; B possui MS de 90% e preço R$ 2,00/kg MN. Suponha que a otimização encontre `x_A=6` e `x_B=4` kg MS.

- A: `m_A = 6/0,40 = 15 kg MN`; `c_A = 15×0,50 = R$ 7,50`.
- B: `m_B = 4/0,90 = 4,444... kg MN`; `c_B ≈ 4,444×2 = R$ 8,89`.
- CMS = `6+4 = 10 kg MS`; custo por vaca/dia ≈ **R$ 16,39**.
- Se FDN de A for 45% e de B 10%, FDN total = `(6×45 + 4×10)/10 = 31% da MS`.

Esse exemplo apenas demonstra **conversão de unidades e ponderação**. Para uma dieta verdadeira no MuuFeed, as funções ME/MP/minerais são avaliadas pela biblioteca NASEM e o conjunto de restrições configuradas.

## 15. Bibliografia e rastreabilidade

**Fontes acadêmicas/modelos diretamente utilizados:**

- **[R1]** National Academies of Sciences, Engineering, and Medicine (NASEM). *Nutrient Requirements of Dairy Cattle: Eighth Revised Edition*. National Academies Press, 2021. DOI: **10.17226/25806**. https://doi.org/10.17226/25806 . Capítulo 5 (carboidratos e Tabela 5-1): https://www.ncbi.nlm.nih.gov/books/NBK600592/ . Fundamenta o modelo de exigências e referências condicionais de fibra/amido.
- **[R2]** National Research Council (NRC). *Nutrient Requirements of Dairy Cattle*, 7ª edição, 2001. Equação de CMS/FCM reproduzida em material técnico da University of Minnesota: https://www.foragelab.com/Media/NRC2001.pdf . A fórmula está implementada em `services/dmi_estimator.py`; a publicação anotada em `referencias.txt` é https://pmc.ncbi.nlm.nih.gov/articles/PMC7825592/ .
- **[R3]** CNM — University of Guelph. *NASEM-Model-Python*, código aberto da implementação Python do NASEM. https://github.com/CNM-University-of-Guelph/NASEM-Model-Python/ e https://nasem-model-python.readthedocs.io/ . Biblioteca `nasem_dairy` utilizada pelo software.

**Referências técnicas para interpretação e referências condicionais (não regras universais):**

- **[R4]** Penn State Extension. *Concentrates for Dairy Cattle*. https://extension.psu.edu/concentrates-for-dairy-cattle . Tabela de inclusões sugeridas condicionais (por exemplo, farelo de trigo 12% ou 15%, conforme processamento), sem interpretação automática como limite seguro geral.
- **[R5]** Penn State Extension. *From Feed to Milk: Understanding Rumen Function*. https://extension.psu.edu/from-feed-to-milk-understanding-rumen-function . Conceitos de fibra, ruminação e gordura da dieta. A referência de 6–7% de gordura corresponde a condições específicas e **não a um máximo universal**.
- **[R6]** University of Georgia Extension. *Considerations for Using By-product Feeds*. https://fieldreport.caes.uga.edu/publications/B862/considerations-for-using-by-product-feeds/ . Variabilidade de composição e processamento de coprodutos.
- **[R7]** Embrapa. Material técnico de alimentação de vacas leiteiras, listado em `referencias.txt`: https://www.embrapa.br/en/web/agencia-de-informacao-tecnologica/criacoes/gado_de_leite/producao/sistemas-de-producao/alimentacao/vacas-leiteiras/alimentacao . Fonte de contexto para alimentação animal, não origem direta de uma equação específica do programa.
- **[R8]** Embrapa, documentos técnicos adicionais listados em `referencias.txt` (PDFs ali identificados). Mantidos para consulta; nenhuma regra do código deve ser atribuída a eles sem checagem da condição e do trecho específico.

**Nota de origem:** a presente documentação distingue (a) equações realmente implementadas no código, (b) cálculos internos do pacote NASEM, (c) referências técnicas externas e (d) anotações não verificadas mantidas em `referencias.txt`. Não foi realizada uma revisão por pares das equações do pacote externo nem validação clínica/zootécnica de dietas individuais.
