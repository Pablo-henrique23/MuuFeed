# MuuFeed — Checklist de entrega do hackathon

**Escopo do artefato:** protótipo offline de sistema especialista para bovinos leiteiros, com modelo NASEM 2021, otimização local de custo e análises nutricionais *parciais*. **Não é prescrição de alimentação animal.**

## A. Já implementado e demonstrado até a versão v10

- [x] Cadastro de lote em português, incluindo raça Holandesa/Jersey, idade em dias/meses/anos, peso, lactação, produção e composição do leite.
- [x] Dados de lote convertidos para entradas NASEM, com `An_Breed=Holstein` ou `Jersey`; `An_Parity_rl` recebe a ordem de lactação.
- [x] Catálogo com 284 itens NASEM: rótulos traduzidos, busca PT/EN e preservação do identificador original no cálculo.
- [x] Preço editável por kg de matéria natural (MN), ingredientes disponíveis escolhidos pelo usuário e conversão consistente para matéria seca (MS).
- [x] Fluxo 1 — sugestões assistidas de ingredientes com confirmação pelo usuário (curadoria fixa; não é seleção contextualizada).
- [x] Fluxo 2 — formulação personalizada, escolhendo ingredientes e preços.
- [x] Fluxo 3 — análise de dieta existente com quantidades fixas e PDF próprio, sem otimização.
- [x] Consumo de MS digitado ou estimado pela equação NRC 2001; origem deve ficar visível ao usuário.
- [x] Formulação com SciPy/SLSQP multistart: minimizar custo e exigir MS, energia metabolizável e proteína metabolizável.
- [x] Restrições opcionais de FDN mínima, amido máximo e FDN de forragens mínima; todas com limites explícitos do usuário.
- [x] Teto operacional opcional de participação por ingrediente; não representa segurança nutricional.
- [x] Balanços NASEM de Ca/P/Na absorvidos, com restrições opcionais, além de Mg/Cl/K na versão v10.
- [x] Triagem descritiva de concentração de ingrediente e NaCl; sem alegar limite superior validado de todos os minerais.
- [x] Cálculos de custo por vaca/dia, lote/dia e 30 dias, distinguidos de preços unitários.
- [x] Relatórios em PDF com regras acionadas, fontes, avisos, limites realmente verificados e diagnósticos.
- [x] Falhas de formulação retornam estado/diagnóstico sem publicar dieta como validada.
- [x] `python scripts/verificar_release_v10.py` executado com sucesso no computador do desenvolvedor: ambas as raças mapeadas; seis macrominerais expostos pela biblioteca.
- [x] Testes `pytest` passaram na instalação do desenvolvedor (número da suíte ainda não registrado nesta rodada).

## B. Obrigatório verificar antes de enviar (P0)

- [ ] Confirmar commit Git limpo e guardar backup ZIP; salvar uma **tag de release** (ex.: `hackathon-final`).
- [ ] Reiniciar Streamlit e testar acesso offline a todas as páginas, com `./init.sh`.
- [ ] Fazer o teste A: sugestão assistida; conferir disponibilidade, preços, PDF e aviso experimental.
- [ ] Fazer o teste B: formulação manual com limites FDN/amido; conferir unidades e restrições.
- [ ] Fazer o teste C: análise da dieta informada; quantidades devem permanecer fixas; PDF próprio.
- [ ] Testar minerais no modo controle e com Ca/P/Na/Mg/Cl/K ativos, incluindo caso sem candidata.
- [ ] Testar uma alteração de preço e verificar atualização de custo, preservando unidades MN/MS.
- [ ] Testar busca por nome português, original inglês e português sem acentos.
- [ ] Testar erro amigável: sem ingredientes, preço ausente, quantidade zero na análise, limites contraditórios, sal sem máximo.
- [ ] Conferir no PDF o lote, idade, raça, origem do CMS, ingredientes, preço, custo, minerais e **restrições ativas**.
- [ ] Conferir que **nenhum** resultado afirma dieta nutricionalmente validada ou mínimo global garantido.
- [ ] Conferir que exemplos e preços ilustrativos estão identificados como tal; não usar resultados como prescrições.
- [ ] Conferir `README.md`: requisitos, instalação, execução, três fluxos, testes, dependências, aviso e fontes.
- [ ] Excluir credenciais/secrets/dados privados do ZIP; manter `requirements.txt`, `init.sh`, código, dados e testes.
- [ ] Fazer teste de instalação em diretório limpo se houver tempo.
- [ ] Fazer captura de 3 telas e guardar 3 PDFs exemplares para demonstrar funcionalidade caso Streamlit tenha problema.

## C. Qualidade desejável se houver tempo (P1)

- [ ] Melhorar clareza dos avisos de inviabilidade e distinguir falha do algoritmo de impossibilidade matemática comprovada.
- [ ] Mostrar claramente quais macrominerais foram *impostos como restrição* versus apenas comparados no diagnóstico.
- [ ] Tornar parâmetros complementares NASEM (hipóteses avançadas e ambiente) mais completos/visíveis.
- [ ] Identificar efeitos de alterações de CMS e preços no custo, sem comparações econômicas enganosas entre dietas de volumes diferentes.
- [ ] Validar, **antes de habilitar**, uma terceira opção de raça com fallback genérico do `nasem_dairy`; rotular limitações no PDF.
- [ ] Examinar visualmente PDFs para órfãos/quebras de tabela e legibilidade.

## D. Fora do necessário para a entrega do hackathon (backlog futuro)

- [ ] Validar dieta nutricionalmente de modo abrangente com especialistas e dados de campo.
- [ ] Fibra fisicamente efetiva, análises de partícula, estabilidade ruminal.
- [ ] Limites de inclusão seguros, específicos por ingrediente, com fontes e condições.
- [ ] Limites superiores de minerais, água, DCAD, interações minerais; vitaminas e microminerais.
- [ ] Suporte genuíno a mais raças/estados fisiológicos, bovinos de corte e dupla aptidão.
- [ ] Curadoria automática contextualizada conforme lote/preços/estoque; importação de análises laboratoriais.
- [ ] Histórico, fornecedores, controle de estoque, autenticação, hospedagem, dashboards extensos.
- [ ] Provar ótimo global: SLSQP não oferece essa garantia.

**Critério de fechamento para hackathon:** três fluxos reproduzíveis, testes passando, PDFs coerentes, disponibilidade offline e limitações nutricionais explícitas. O protótipo é demonstrável sem ser uma dieta autorizada para uso real.
