# MuuFeed 🐄

**Sistema especialista experimental e offline para formulação e análise de dietas de vacas leiteiras.** Python 3.12, Streamlit, `nasem_dairy` (modelo NASEM 2021), SciPy SLSQP, catálogo original de alimentos e relatórios PDF.

## Instalação e execução

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./init.sh
```

O launcher `init.sh` configura automaticamente o motor NASEM. Executar testes:

```bash
python -m pytest -q
python scripts/verificar_nasem_minerais.py
```

## Os três fluxos

| Fluxo | Entrada | Resultado |
|---|---|---|
| **Sugestão automática** | Dados do lote; confirmação de ingredientes, disponibilidade e preço | Ingredientes candidatos → formulação pelo motor |
| **Formulação personalizada** | Lote, alimentos disponíveis, preços, MS estimada e limites opcionais | Candidata local de menor custo, regras acionadas e PDF |
| **Analisar dieta existente** | Quantidades fixas em kg de matéria natural | Avaliação da dieta existente, sem otimizar quantidades, e PDF específico |

## Transparência do modo assistido (revisão da entrega)

A **Sugestão automática de ingredientes** começa com **seis candidatos fixos**
para lotes em lactação, identificados em `services/ingredient_suggestion.py`. Opcionalmente,
a tela apresenta **três alternativas contextuais**, escolhidas por critérios operacionais
transparentes de **produção de leite e dias de lactação**. Isso é uma curadoria
experimental, **não uma recomendação nutricional personalizada nem uma fórmula de dosagem**.
As alternativas extras começam desmarcadas. Os preços iniciais são **ilustrativos**, não
cotações reais. O usuário confirma disponibilidade, limites e preços. **Só então** o
motor NASEM e SLSQP usa os dados do lote para formular as quantidades e verificar
as restrições selecionadas. O uso das alternativas não garante que a dieta seja
nutricionalmente completa, diversa ou economicamente ótima em sentido global.

**Produção média, gordura, proteína e lactose do leite** são entradas de cenário
(preferir dados medidos do lote; valores estimados devem ser identificados como
hipóteses). Não são saídas garantidas pelo modelo nem metas cuja realização a dieta
possa prometer. A opção de raça sempre envia `An_Breed` preenchido; detalhes da
limitação externa observada em `docs/NOTAS_VALIDACAO_FINAL.md`.

A FDN **proveniente de forragens** fica em *Restrições avançadas*, mas permanece calculada
como indicador e opcionalmente limitada quando o usuário informa um mínimo técnico.
Ela **não equivale à fibra fisicamente efetiva**. O teto em % MS por ingrediente é
operacional e não garante segurança nutricional ou diversidade suficiente.

O estado fisiológico **Vaca seca** exige regras, entradas e estimativa de consumo
apropriadas; ainda não foi integrado nem testado neste protótipo. O aplicativo só
permite formulação de **vacas em lactação**, embora a biblioteca NASEM tenha outros ramos.

## Por que os nutrientes novos nem sempre mudam a dieta?

Um **valor de composição** não é uma exigência nutricional. Por exemplo, saber que a dieta contém 0,26% de cálcio total não prova sua adequação: a comparação precisa levar em conta **cálcio absorvido** e a exigência calculada pelo NASEM.

O MuuFeed passou a ler Ca e P absorvidos e suas exigências **na mesma base (g/dia)**, além de tentar ler os balanços absorvidos de Mg, Na, Cl e K. Quando o avaliador fornece os dados, o balanço aparece no resultado. Na opção **“Exigir cálcio e fósforo ABSORVIDOS”**, esses dois nutrientes também passam a restringir o otimizador, podendo elevar custos ou impedir uma solução. O recurso fica desativado inicialmente para manter os cenários antigos comparáveis.

**ME e MP** são verificadas por padrão. **FDN, FDN de forragens e amido** só restringem a busca se o usuário informar limites tecnicamente fundamentados. Outros componentes do catálogo permanecem indicadores informativos.

## Limites e honestidade científica

**CANDIDATA EXPERIMENTAL — NÃO É DIETA NUTRICIONALMENTE VALIDADA.** Nem todos os nutrientes, níveis máximos de inclusão, vitaminas, fibra fisicamente efetiva, consumo espontâneo e variação real dos ingredientes são avaliados. O SLSQP é local e não assegura ótimo global. Preços demonstrativos não representam o mercado. **Não utilizar dietas geradas para alimentar animais sem revisão de profissional especializado.**

## Documentação (organizada)

- [`docs/DEMONSTRACAO.md`](docs/DEMONSTRACAO.md) — roteiro e validações antes do hackathon.
- [`docs/CIENCIA_E_LIMITACOES.md`](docs/CIENCIA_E_LIMITACOES.md) — fundamentos, variáveis usadas e o que falta validar.
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — entregáveis restantes, ordenados por prioridade.
- [`docs/INTERFACE.md`](docs/INTERFACE.md) — arquitetura e contratos existentes.

Os antigos `LEIA-ME-V3.md`, `LEIA-ME-V4.md`, `LEIA-ME-V5.md` e demais tutoriais de patches são históricos e não são necessários para executar. Veja `scripts/limpar_documentacao.sh` (prévia por padrão).

## Arquivos principais

`app.py` e `ui/pages.py` (interface); `models/contracts.py` (dados); `services/nasem_adapter.py` (integração NASEM); `formulation_engine.py` (SLSQP e regras); `services/nasem_requirements.py` (balanços minerais absorvidos); `services/diet_analysis.py` (dieta fixa); `services/pdf_report.py` (PDF); `tests/` (testes).

## Novidades de uso (v7)

**Consumo de MS:** na página *Formular dieta*, escolha entre (a) estimar automaticamente pela equação **NRC 2001** usando peso, leite, gordura e dias em lactação, ou (b) informar um consumo medido/estimado externamente. O motor NASEM recebe esse consumo como **entrada fixa**, não calcula o consumo espontâneo; a estimativa NRC não é uma medição nem uma validação de ingestão. A origem adotada fica nos avisos e no PDF. Fonte: https://pmc.ncbi.nlm.nih.gov/articles/PMC7825592/

**Controle de concentração:** opcionalmente informe uma máxima participação por ingrediente em **% da MS**, como limite operacional da simulação. Por exemplo, 60% impede qualquer ingrediente de superar 60% da MS, mas **não é recomendação nutricional**. Pode aumentar o custo e eliminar candidatas se os ingredientes disponíveis forem insuficientes. O teto não substitui regras de inclusão individuais embasadas nem a avaliação de micronutrientes e minerais.

**Indicadores:** o painel principal e o PDF mostram exigências/limites comparáveis; a composição bruta adicional aparece em seção informativa, sem repetição de “sem veredito”. Os déficits calculados de minerais absorvidos ganham aviso explícito mesmo quando não foram impostos como restrição.

**Preços:** valor em R$/kg MN é preço **unitário**, não somável. O total financeiro é a soma dos custos de ingrediente na coluna R$/vaca/dia.

**Correção no diagnóstico mineral:** os seis macrominerais absorvidos (Ca, P, Mg, Na, Cl, K) passam a ser consultados também com Ca/P ativados; na versão anterior a leitura final mostrava somente Ca/P nesse modo. Isso não impõe automaticamente os demais minerais como restrições.

## Alterações v8 (22/10/2026)

- Raça enviada ao NASEM por mapeamento único: Holandesa → `Holstein`; Jersey → `Jersey`.
- Nova restrição opcional **Na absorvido >= exigência NASEM**, separada do controle opcional Ca/P.
- Sugestão assistida pode incluir cloreto de sódio apenas por escolha explícita, com confirmação de preço, disponibilidade e **máximo informado pelo usuário**.
- Regras de Ca/P/Na e diagnósticos restantes são independentes; nenhuma dieta é declarada nutricionalmente completa.
- Veja [validação do v8](docs/VALIDACAO_V8.md) e [backlog](docs/BACKLOG.md).

## Atualização v10 — escopo reduzido e avaliação de macrominerais

- O cadastro **não tem Destinação econômica**: a aplicação é exclusivamente para **vacas leiteiras em lactação**. O campo oferece Holandesa (`An_Breed='Holstein'`), Jersey (`An_Breed='Jersey'`) e **Outra raça — genérica experimental** (`An_Breed='Other'`). O nome específico pode ser registrado, mas NÃO altera as equações usadas pelo ramo `Other`. Esta opção exige cautela e não constitui validação para Gir, Girolando ou qualquer outra raça; estados fisiológicos além de lactação continuam não suportados.
- Nova opção **Exigir magnésio, cloro e potássio absorvidos**: cada um passa a restringir a busca pela comparação entre oferta absorvida e exigência NASEM em g/dia; pode ser combinada com Ca/P e Na. Se não encontrar candidata, o resultado deve indicar ausência de candidata que satisfaça os requisitos verificados, nunca um ótimo nutricionalmente validado.
- Mesmo se os seis macrominerais estiverem em conformidade, limites superiores, minerais traço, vitaminas, água, DCAD, aminoácidos e fibra fisicamente efetiva **não estão automaticamente validados**. O alerta experimental continua obrigatório.
- Execute `python scripts/verificar_release_v10.py` no ambiente que contém `nasem_dairy`, e consulte [docs/VALIDACAO_V10.md](docs/VALIDACAO_V10.md).

## Complemento de entrega — opção de raça genérica (experimental)

A seleção **Outra raça (genérica — experimental)** ativa `An_Breed='Other'` do `nasem_dairy`, sem disfarçar a raça como Holandesa. O nome opcional da raça é apenas metadado para os relatórios. A aplicação emite aviso no cadastro, resultado e PDFs; **não garante parâmetros nutricionais adequados à raça informada**.

Teste no NASEM instalado antes de demonstrar este modo:

```bash
python scripts/verificar_raca_generica.py
```

Se retornar erro, utilize Holandesa/Jersey no cenário principal e registre a limitação. Mesmo passando, mantenha a indicação experimental.

[Checklist final](docs/CHECKLIST_ENTREGA.md) • [Casos de teste](docs/CASOS_DE_TESTE.md)

### Sódio e ausência de candidata — atualização v16

Ativar a restrição de **sódio absorvido** pode impedir a obtenção de candidata
quando o conjunto escolhido não contém uma fonte capaz de fornecer o mineral.
Nesse caso, o MuuFeed alerta a ausência de fonte concentrada reconhecida e
permite rever os ingredientes. O sal é **opcional**, requer confirmação de
preço, disponibilidade e teto por responsável técnico e não é prescrito.
Os aspectos não avaliados exibidos no resultado são **limitações de escopo**;
não devem ser lidos como causa automática da ausência de candidata.

### Seleção guiada por lote e restrições (v18 — hackathon)

Na página **Sugestão automática**, o modo guiado (padrão) pede **teto de participação, FDN mínima, amido máximo, FDN de forragens mínima e opções de minerais antes da lista**. Ele consulta o catálogo e preços disponíveis, exclui ingredientes especiais que exigem teto individual e usa programação linear para **pré-triagem de composição química**; seleciona opções e alternativas, considerando produção e dias de lactação. O produtor confirma disponibilidade e preços, e os mesmos limites são encaminhados à página **Formular dieta**, onde o modelo NASEM e o SLSQP realizam a verificação nutricional experimental. O modo antigo permanece disponível.

**Não confundir pré-triagem com formulação final.** A etapa linear não verifica exigências de energia, proteína metabolizável ou minerais absorvidos; o NASEM final pode legitimamente não encontrar candidata. Não há preços coletados automaticamente, nem inclusão automática de suplementos, nem dados bromatológicos medidos pelo programa. Referências de inclusão de literatura são orientativas e condicionais, não máximos seguros.

Veja `docs/SELECAO_ORIENTADA_V18.md`; rode `python scripts/verificar_selecao_guiada_v18.py` no ambiente com `nasem_dairy` instalado antes de demonstrar a funcionalidade.

### Triagem de gordura / extrato etéreo (v19)

O formulador inclui um teto opcional para extrato etéreo (EE, coluna `Fd_CFat` do NASEM), aplicado na pré-triagem química e na otimização. O valor inicial de **7% da matéria seca** é uma referência condicional de alimentação de vacas leiteiras de maior produção (Penn State Extension), **não um limite universal de segurança**. O usuário pode ajustá-lo ou deixá-lo vazio, e a composição de gordura continua informativa quando desativada.

O MuuFeed ainda **não certifica adequação nutricional completa**. Consulte `docs/VALIDACAO_V19.md` para limitações, dados de origem e procedimentos de teste. A aparência simplificada do PDF não altera essas limitações.
