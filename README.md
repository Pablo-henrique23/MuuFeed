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
