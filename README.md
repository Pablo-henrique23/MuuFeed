# MuuFeed 🐄

**Sistema especialista experimental de apoio à formulação e análise econômica de dietas para vacas leiteiras em lactação.** Desenvolvido para o Hackathon Rerum 2026.2.

O MuuFeed combina uma biblioteca de ingredientes baseada no **NASEM (2021)**, uma etapa de **pré-seleção dinâmica por programação linear**, avaliação nutricional pelo pacote Python `nasem_dairy` e **otimização de menor custo com SciPy/SLSQP**. Apresenta resultados em português, tabelas e relatórios PDF. Funciona **localmente/offline após a instalação das dependências**.

> **Escopo:** protótipo experimental de apoio à decisão. Uma formulação que atende às restrições ativas **não é uma prescrição nutricional completa**. O modelo não verifica automaticamente todas as vitaminas, microminerais, limites superiores, fibra fisicamente efetiva ou a composição real de cada lote de alimento. A revisão de médico-veterinário ou zootecnista é necessária antes de utilizar uma dieta em animais.

Confira a **[Documentação completa](docs/DOCUMENTACAO_COMPLETA.md)**.

## Instalação (Python 3.12)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
chmod +x init.sh
./init.sh
```

Alternativamente, com o ambiente ativo:

```bash
export MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
streamlit run app.py
```

A aplicação abre no navegador, geralmente em `http://localhost:8501`. O pacote `nasem_dairy` fornece a biblioteca original de alimentos; o MuuFeed **não baixa cotações de preços** nem requer conexão na execução.

## O que o sistema faz

| Fluxo | O que o usuário informa | O que o MuuFeed entrega |
|---|---|---|
| **Sugestão automática** | Lote, limites iniciais, disponibilidade e preços | Pré-seleção dinâmica de ingredientes por composição/limites, seguida de confirmação e formulação |
| **Formulação personalizada** | Lote, ingredientes próprios, preços, CMS, restrições opcionais | Candidata experimental de menor custo local que respeita as verificações ativadas, com PDF |
| **Análise de dieta existente** | Uma dieta já utilizada, em kg de matéria natural por vaca/dia | Custo, consumo de MS, indicadores e possíveis déficits; **não altera** ingredientes nem quantidades |

### Sequência sugerida para demonstração

1. Em **Lote**, informe peso, dias em lactação, produção e composição do leite e escolha Holandesa, Jersey ou a opção genérica explicitamente identificada.
2. Vá a **Sugestão automática** e configure primeiro FDN mínima, amido máximo, FDN de forragens mínima, extrato etéreo máximo, teto de participação e as restrições minerais desejadas.
3. Confira as alternativas calculadas. **Confirme disponibilidade e preços:** os preços iniciais são ilustrativos, não cotações.
4. Se decidir usar um suplemento como sal, informe um teto individual fundamentado com orientação técnica; o sistema não calcula uma dose segura.
5. Acesse **Formular dieta**, confira o consumo de MS estimado pelo NRC (2001) ou informe um CMS externo/medido e revise os parâmetros.
6. Execute a otimização, examine o painel de indicadores e exporte o **PDF de formulação**.
7. Para comparação independente, use **Analisar dieta** com quantidades já conhecidas e exporte seu PDF próprio.

## Como o cálculo funciona, resumidamente

- Seja `x_i` a quantidade de **matéria seca** do ingrediente `i` (kg MS/vaca/dia), `d_i` sua fração de MS e `p_i` seu preço (R$/kg **matéria natural**):

  `custo por vaca/dia = Σ [x_i × p_i / d_i]`

- O MuuFeed fixa o consumo total: `Σ x_i = CMS` e aplica limites inferior/superior por ingrediente. Opcionalmente: `x_i ≤ CMS × teto%/100`.
- FDN, FDN de forragens, amido e extrato etéreo são ponderados por MS. Exemplos:

  `FDN (% MS) = Σ[x_i × FDN_i (% MS)] / CMS`

  `FDNf (% MS) = Σ[x_i × FDN_i × indicador_de_forragem_i] / CMS`

- O modelo NASEM avalia **energia metabolizável (ME)**, **proteína metabolizável (MP)** e, se marcados, mínimos de **Ca, P, Na, Mg, Cl e K absorvidos**. Cada fornecimento precisa alcançar a exigência do modelo (nas mesmas unidades).
- A otimização usa **SLSQP com seis pontos iniciais determinísticos**; valida separadamente a candidata final, mas **não garante ótimo global**.
- Na sugestão automática, uma **programação linear** examina os ingredientes de preço e composição conhecidos, verificando somente limites químicos e custo para escolher candidatos. A formulação NASEM vem depois; a pré-triagem não garante viabilidade final.

A derivação, as equações completas, as fontes e um exemplo de cálculo estão em **[Documentação completa](docs/DOCUMENTACAO_COMPLETA.md)**.

## Testar

```bash
python -m pytest -q
python scripts/verificar_selecao_guiada_v18.py
python scripts/verificar_hipoteses_nasem_v19.py
python scripts/auditar_catalogo_nutricional.py
```

O teste no ambiente do autor alcançou **246 testes aprovados antes desta auditoria final**. A revisão acrescenta testes defensivos para preços, MS e limpeza; o resultado final deve ser reexecutado na máquina de entrega, pois o ambiente de revisão não contém todas as dependências NASEM/Streamlit.

## Tecnologias e arquivos principais

- **Interface:** `app.py`, `ui/pages.py`, `ui/state.py`, `ui/theme.py` — Streamlit.
- **Domínio e contratos:** `models/contracts.py` — lote, ingredientes, opções, indicadores, resultados.
- **Catálogo e nomes:** `services/feed_catalog.py`, `services/feed_translation.py`, `data/feed_names_pt.json`, `data/demo_prices.json`.
- **Sugestão dinâmica:** `services/constraint_guided_suggestion.py` — programação linear (HiGHS).
- **NASEM:** `services/nasem_adapter.py`, `services/nasem_requirements.py`, `services/breed.py`.
- **Otimização:** `formulation_engine.py` — SciPy SLSQP e verificação independente.
- **Avaliação de dieta informada:** `services/diet_analysis.py`.
- **Relatórios:** `services/pdf_report.py`, `services/analysis_pdf.py`, `services/financeiro.py`.
- **Testes:** `tests/` e verificadores em `scripts/`.

## Documentos de entrega

- [**Documentação completa — fluxo, fórmulas, arquitetura e fontes**](docs/DOCUMENTACAO_COMPLETA.md)
- [**Fontes originais reunidas durante o desenvolvimento**](referencias.txt)

## Limitações principais

O protótipo atende **apenas vacas em lactação**. Outras raças utilizam o ramo genérico `An_Breed='Other'`, que **não possui validação específica por raça**. Campos ambientais e de crescimento não preenchidos podem usar parâmetros remanescentes do cenário demonstrativo NASEM. O consumo estimado pela equação NRC (2001) não é uma medição. A composição de referência do catálogo não substitui análise bromatológica. Os valores de referência orientativos para limites de inclusão variam segundo o ingrediente e o sistema de alimentação. **Atender aos mínimos exibidos não demonstra equilíbrio nutricional integral.**

Consulte a documentação científica e o relatório de auditoria antes de interpretar resultados.
