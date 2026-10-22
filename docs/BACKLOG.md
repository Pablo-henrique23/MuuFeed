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
- [x] Transparência: seis candidatos fixos, três alternativas contextuais opcionais por produção/dias de lactação; sem seleção nutricional validada. Preços iniciais ilustrativos; lote entra no motor NASEM durante a formulação.
- [x] HELP nos quatro campos avançados do lote.
- [x] Campo FDN proveniente de forragens recolhido a seção avançada sem perda do indicador ou regra.
- [x] Remover frase repetida "NÃO USAR para alimentar animais: modelo parcial." do fim do PDF, mantendo alertas profissionais e experimentais.
- [ ] Extensão para vacas secas: entradas e hipóteses específicas, ramo NASEM testado com dieta exemplo e testes nutricionais próprios (não expor sem validação).
- [x] Alternativas contextuais experimentais no modo assistido (heurística declarada; extras desmarcados).
- [ ] Sugestão nutricionalmente personalizada e validada: considerar disponibilidade, composição, restrições técnicas e custo real; ainda NÃO implementada.
- [ ] Limites nutricionais de inclusão por ingrediente/categoria, com referência veterinária/zootécnica; teto operacional atual não substitui isso.

### V14 — Revisão científica do catálogo

- [x] Tratar equivalente de proteína bruta em fontes NNP sem falso positivo de 100%.
- [x] Curadoria explícita de `Alfalfa meal`: `Fd_Type=Forage`, `Fd_Category=Plant Protein`; fNDF química ≠ peNDF.
- [x] Auditar 84 campos NASEM por alimento quanto à presença/tipo numérico, MS e 15 nutrientes monitorados.
- [x] Distinguir ingredientes exclusivos de bezerros e exigir teto operacional explícito para aditivos, premixes minerais/vitamínicos, fontes NNP e suplementos de gordura.
- [x] Associar fontes científicas rastreáveis e limites **indicativos, condicionais** somente para exemplos com estudos disponíveis.
- [ ] Completar teores ausentes com resultados laboratoriais específicos ou fontes com equivalência de unidade, processamento e lote demonstrada; **não inventar zeros**.
- [ ] Implantar análise de limites superiores de todos os nutrientes, água, micotoxinas, DCAD e peNDF antes de uso animal; não concluído para o hackathon.

### V15 — Legibilidade das regras no PDF e correção da auditoria

- [x] Resolver falso positivo global da auditoria: `Fd_Libr` é referência **textual**, não coluna nutricional numérica; permanece entre os 84 campos contabilizados, mas não deve ser validada por conversão para `float`.
- [x] Preservar as 68 lacunas nutricionais reportadas e a classificação 284/284 sem editar o CSV original NASEM.
- [x] Na seção 7 do PDF, mostrar valores efetivos e limiares em formato PT-BR para ME, MP, minerais, FDN, fNDF e amido, a partir de `ResultadoFormulacao.indicadores`; sem novos cálculos.
- [x] Na seção 7, simplificar fontes para `NASEM 2021` e `NASEM 2021 + usuário`.
- [x] Na seção 8, distinguir teores de referência da biblioteca de alimentos das restrições operacionais informadas pelo usuário.
- [ ] Rodar a auditoria e a suíte completa na instalação local, gerar novo PDF e conferir a seção 7 visualmente.

## Revisão v16 — entrega do hackathon

- [x] Mostrar aviso contextual quando exigência de sódio absorvido estiver ativa sem fonte concentrada reconhecida.
- [x] Atalho da formulação para rever a sugestão, sem inclusão automática de suplemento e sem inventar dose.
- [x] Distinguir aspectos nutricionais não avaliados de causas prováveis de não encontrar candidata.
- [x] Especificar na coluna Fonte do PDF: “NASEM 2021; limite do usuário”.
- [ ] Executar suíte completa no ambiente do usuário com `nasem_dairy`, `streamlit` e `pyarrow`.
- [ ] Validar com dados reais o efeito da fonte de sódio e restrição máxima na candidata.
- [ ] **Destinação econômica adicional**: modelar e validar categoria animal diferente (ex.: novilhas de reposição ou vacas secas). Não confundir destinação comercial com estado fisiológico e não declarar suporte fictício na entrega.

## V18 — Seleção guiada por restrições (hackathon)

- [x] Inserir teto global, FDN, amido e fNDF ANTES da sugestão; permitir informar quais restrições de minerais serão exigidas na etapa final.
- [x] Pré-triagem linear de composição com fontes realmente presentes no catálogo NASEM, valores de MS/FDN/amido e preços conhecidos; descartar candidatos sem dados em vez de assumir zero.
- [x] Apresentar conjunto de candidatos dinâmico, com variantes por perfil do lote e alternativas para confirmação do usuário.
- [x] Verificar a pré-triagem com os ingredientes MARCADOS, não apenas com conjunto total; informar incompatibilidade antes do NASEM.
- [x] Transferir os mesmos limites para a página Formular dieta; manter o NASEM final como verificador de ME/MP/minerais.
- [x] Sinalizar referências de inclusão condicionais quando teto geral for mais permissivo, sem inventar dose segura.
- [ ] Executar `python scripts/verificar_selecao_guiada_v18.py` e suíte completa no ambiente do usuário com NASEM/Streamlit reais.
- [ ] Testar cenário com teto 30%, FDN 25%, amido 30%, FDNf 19%, com e sem suplementos confirmados.
- [ ] Demonstração de inviabilidade de NASEM com aviso explicativo; a pré-triagem não faz verificação completa e não deve mentir.
- [ ] Futuro: pré-seleção com ME/MP e minerais via NASEM real em rotina de busca iterativa, com custo computacional medido e limites de execução; **não implementado nesta versão**.
- [ ] Futuro: vitaminas A/D/E com suprimento declarado e dados de suplementos reais; microminerais e limites superiores, exigem validação.
