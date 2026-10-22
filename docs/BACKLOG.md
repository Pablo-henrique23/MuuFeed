# Backlog do MuuFeed — v10 (22/10/2026)

## P0 — Entrega do código hoje

- [x] Três fluxos: sugestão assistida, formulação manual e análise de dieta existente, com PDFs separados.
- [x] Consumo de MS informado ou estimado via NRC 2001; origem registrada.
- [x] Motor NASEM 2021 e otimização local multistart SLSQP com diagnóstico de busca.
- [x] FDN total, FDN de forragens, amido e teto operacional opcionais, sem limites universais inventados.
- [x] Cálculo de composição mineral/proteica adicional como informação.
- [x] Balanços absorvidos de Ca/P/Na como restrições opcionais, com diagnósticos de Mg/Cl/K.
- [x] **v10:** possibilidade de exigir Mg, Cl e K ABSORVIDOS como restrições adicionais, em conjunto ou isoladamente dos demais.
- [x] **v10:** remover Destinação econômica e oferecer apenas estados e raças realmente suportados na interface.
- [x] Raça Holandesa/Jersey mapeada explicitamente para `An_Breed`, sem fallback silencioso.
- [x] Complemento experimental: opção **Outra raça** envia `An_Breed='Other'` (com ressalva/descrição no PDF).
- [ ] **Obrigatório antes de usar a opção genérica:** executar `python scripts/verificar_raca_generica.py` com o NASEM real e conferir resultados finitos.
- [x] Catálogo 284 ingredientes traduzidos e buscáveis em PT/EN, preservando nomes NASEM.
- [x] Sal opcional somente após disponibilidade/preço/máximo informados; triagem descritiva de NaCl.
- [ ] Reexecutar `python -m pytest -q` na máquina com Streamlit, PyArrow e NASEM reais após o patch.
- [ ] Executar `python scripts/verificar_release_v10.py` e validar os seis minerais com Holandesa/Jersey reais.
- [ ] Testar novo grupo Mg/Cl/K em três cenários: desativado, ativado, todos minerais ativos.
- [ ] Testar todas as páginas e PDFs offline, inclusive caso sem candidata, sem preços e sem itens.
- [ ] Verificar que `git diff` contém somente arquivos esperados; fazer commit/tag e arquivar ZIP final.

## P1 — Nutrição / regras para além da entrega experimental

- [ ] Revisão de **limites superiores** de Na, Cl, K, Mg e outros minerais, interações e DCAD com água e fontes minerais declaradas. Não confundir % da exigência mínima com máximo seguro.
- [ ] Limites específicos de inclusão por ingrediente e categoria, com referências e condições verificáveis.
- [ ] Fibra fisicamente efetiva, comprimento das partículas, estabilidade ruminal e contextos FDNf/amido.
- [ ] Vitaminas, microminerais, aminoácidos essenciais e necessidades NASEM compatíveis.
- [ ] Tornar configuráveis/medidos todos os parâmetros complementares herdados da demonstração NASEM.
- [ ] Estudar consumo esperado segundo condições de fazenda e sensibilidade ao CMS estimado/medido.
- [ ] Fazer análise de risco, validação com especialista e comparação com dietas reais/análises bromatológicas.
- [ ] Diagnósticos de inviabilidade mais específicos e comparação entre otimizadores/inicializações.

## P2 — Produto pós-entrega

- [ ] Seleção automática contextualizada conforme lote, preço e ingredientes realmente disponíveis.
- [ ] Comparar dieta existente a uma proposta otimizada sob MS e exigências equivalentes.
- [ ] Histórico de dietas, estoque, fornecedores e atualização de preços.
- [ ] Importar análises bromatológicas reais, exportar CSV/Excel, comparar lotes.
- [ ] Suporte zootécnico especificamente validado para mais raças e vacas secas, carne/dupla aptidão **somente com modelo adequado**; o ramo `Other` é apenas aproximação experimental.
- [ ] Apresentação: roteiro e demonstração, fora do escopo do código para o prazo atual.

## Critérios obrigatórios de honestidade científica

O status deve continuar **candidata experimental**. O projeto calcula apenas as restrições que efetivamente verificou e não pode ser utilizado como prescrição nutricional independente de médico-veterinário ou zootecnista.

## Revisão após testes funcionais A–G

- [x] Testes de entrada negativa G1–G6 aprovados pelo usuário.
- [x] PDFs A–F gerados; conferidas composições, custos e diagnósticos principais.
- [x] Transparência: candidatos do modo assistido são fixos, preços iniciais ilustrativos; lote entra na formulação.
- [x] HELP nos quatro campos avançados do lote.
- [x] Campo FDN proveniente de forragens recolhido a seção avançada sem perda do indicador ou regra.
- [x] Remover frase repetida "NÃO USAR para alimentar animais: modelo parcial." do fim do PDF, mantendo alertas profissionais e experimentais.
- [ ] Extensão para vacas secas: entradas e hipóteses específicas, ramo NASEM testado com dieta exemplo e testes nutricionais próprios (não expor sem validação).
- [ ] Sugestão REALMENTE personalizada de ingredientes: selecionar por lote, disponibilidade, classes nutricionais e restrições cientificamente referenciadas; atualmente NÃO implementada.
- [ ] Limites nutricionais de inclusão por ingrediente/categoria, com referência veterinária/zootécnica; teto operacional atual não substitui isso.
