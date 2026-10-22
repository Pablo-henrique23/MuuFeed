# Backlog priorizado — MuuFeed (revisão v7)

## P0 — Obrigatório antes de apresentar (22/10/2026, 19h)

- [ ] Executar `python -m pytest -q` na máquina com Streamlit, `nasem_dairy` e biblioteca NASEM; registrar contagem de testes.
- [ ] Testar escolha **NRC 2001 estimado** e **consumo informado**. A estimativa muda a MS fixada; não comparar dietas sem igualar a MS.
- [ ] Confirmar com o NASEM real que o **teto de participação por ingrediente** (p.ex., 60% MS, apenas ilustrativo) é respeitado; testar caso de inviabilidade e alternativa sem teto.
- [ ] Repetir teste A1 e A2 com o **mesmo CMS**, mesma lista e mesmos preços, mantendo controle de Ca/P igual ao da comparação.
- [ ] Conferir Na, Ca, Cl e outros balanços absorvidos. Mesmo quando Ca/P passa, outros minerais podem apresentar déficits; preservar o aviso experimental.
- [ ] Exportar os PDFs de formulação e análise de dieta; checar paginação, tabelas, avisos e origem do CMS.
- [ ] Validar entradas inválidas, ingredientes insuficientes, custo total e mensagens sem candidato.
- [ ] Ensaiar demonstração offline e fazer commit/tag da versão congelada. Não aplicar patches extras sem reexecutar os testes.

## P1 — Nutrição e qualidade do formulador (fundamental para uso real, escopo científico ainda incompleto)

- [ ] Regras justificadas por tipo de ingrediente e condições da dieta para limites de inclusão (não confundir o teto operacional com limite nutricional).
- [ ] Verificar adequação absorvida de Na, Cl, Mg e K como restrições opcionais, com diagnóstico explícito de inexistência de soluções; incluir fontes de suplementos quando disponíveis/confirmadas.
- [ ] Avaliar excessos máximos e relações minerais, além de mínimos; incluir risco de toxicidade.
- [ ] Fibra fisicamente efetiva (exige tamanho de partícula e classificação da forragem); limites contextuais de FDN, FDNf, amido, gordura etc.
- [ ] Vitaminas, microminerais, aminoácidos e outros nutrientes efetivamente modeláveis pela biblioteca NASEM.
- [ ] Substituir hipóteses herdadas do `nd.demo` por dados explícitos e cientificamente verificados do lote.
- [ ] Avaliar estimativa de CMS NRC 2001 contra alternativas NASEM 2021; testar sensibilidade e plausibilidade em vários lotes.
- [ ] Validar resultados com especialista (zootecnista/veterinário), referências e composição real dos alimentos por análise bromatológica.
- [ ] Investigar convergência global, desempenho da busca, alternativas de otimização e certificado de inviabilidade quando possível.

## P2 — Experiência e evolução do produto

- [ ] Seleção assistida contextualizada com classificação de todas as opções da biblioteca NASEM.
- [ ] Comparar dieta existente x nova alternativa **sob mesmo CMS e restrições**, custos totais e diferenças nutricionais.
- [ ] Importação de análises de alimentos, preços reais, estoque e fornecedores.
- [ ] Salvar lotes/cenários e histórico; exportar em CSV/Excel e relatórios comparativos.
- [ ] Suporte a outros estágios (vacas secas, novilhas) após parametrização e validação dos modelos.
- [ ] Melhorar relatórios de recomendações e referência explícita de cada regra.

## Implementado na v7

- [x] Estimativa **opcional** de CMS pela equação NRC 2001, com modo manual preservado e aviso de origem.
- [x] Teto **operacional configurável** de participação máxima por ingrediente (% MS), aplicado ao SLSQP via bounds.
- [x] PDF: situação “Informativo” concisa, composição adicional separada, tabelas em blocos e sem página quase vazia no teste de regressão.
- [x] Tela Resultados: detalhes de composição recolhidos; déficits de nutrientes verificados destacados.
- [x] Preço unitário x custo total explicado na interface e no PDF.

### Corrigido no diagnóstico v7 (regressão A2)

- [x] Quando **Ca/P estão ligados**, o motor também reavalia **Mg, Na, Cl e K** na dieta final. Antes o caminho Ca/P exibia apenas Ca e P, ocultando os outros balanços. Os déficits continuam diagnósticos (não restrições), salvo Ca/P ativados.
