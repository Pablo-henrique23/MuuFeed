# Backlog priorizado — MuuFeed (22/10/2026)

## P0 — Imprescindível para demonstração hoje, antes de 19h

- [x] Conferir caminho da raça Holandesa/Jersey em `An_Breed`, unificar função e testar via mocks.
- [x] Implementar restrição opcional de sódio ABSORVIDO, com exigência do próprio NASEM.
- [x] Incluir opção explícita de fonte de sódio na seleção assistida, **desmarcada por padrão**, com preço editável e máximo obrigatório informado pelo usuário.
- [x] Manter Ca/P e Na como restrições opcionais independentes; déficits restantes sinalizados.
- [ ] Rodar a **suíte completa** com Streamlit + NASEM instalado; preservar o número final de testes.
- [ ] Rodar `python scripts/verificar_raca_nasem.py` e confirmar Holandesa/Jersey no NASEM real.
- [ ] Testar v8: cenário controle versus inclusão de sal + Na exigido, mesmo CMS/preços/restantes limites.
- [ ] Revisar PDFs dos três fluxos, avisos, valores e consistência financeira; evitar páginas vazias.
- [ ] Confirmar que **nenhum suplemento é incluído sem máximo informado** e que cenário sem candidato informa falha, não dieta falsa.
- [ ] Fazer teste offline completo, `git commit`, registrar versão, ensaiar roteiro e congelar alterações.

## P1 — Essencial para futura alegação de adequação nutricional (não completar à força hoje)

- [ ] Verificar limites superiores e relações Na/K/Cl/DCAD, suplementação mineral e risco de excesso; definir tetos nutricionais com fonte e revisão profissional.
- [ ] Limites técnicos para inclusão por classe de alimento, considerando condições de uso e digestibilidade, e dados físicos da forragem.
- [ ] Fibra fisicamente efetiva, FDNf/amido contextuais, excesso de gordura e integridade da fibra.
- [ ] Microminerais, vitaminas e aminoácidos/eficiências conforme NASEM, quando saídas e exigências compatíveis estiverem disponíveis.
- [ ] Tornar explícitas as hipóteses do cenário NASEM que ainda não são preenchidas na interface; validar seus impactos.
- [ ] Avaliar estimativa CMS versus consumo medido, coerência energética e fisiologia do animal.
- [ ] Avaliar robustez e globalidade da otimização e validação por profissional + análises bromatológicas.

## P2 — Evolução do produto

- [ ] Sugestão contextualizada de alimentos e suplementos baseada no lote e na disponibilidade real.
- [ ] Comparar dieta existente versus nova dieta na mesma MS e sob restrições equivalentes.
- [ ] Histórico, estoque, fornecedores e cotações verificadas, importação de composição de amostras.
- [ ] Suporte a animais não lactantes após validação do modelo.
- [ ] Exportação de dados e relatórios comparativos completos.

## Critérios de entrega

- Os três fluxos devem funcionar sem internet na demonstração.
- Testes automatizados completos devem passar no ambiente da equipe.
- Avisos não devem declarar uma dieta nutricionalmente completa: o modelo permanece parcial/experimental.
- Preços ilustrativos e limites configurados não podem ser apresentados como recomendações técnicas reais.
