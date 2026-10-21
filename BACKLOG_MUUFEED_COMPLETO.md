# MuuFeed — Backlog consolidado (21/10/2026)

## P0 — Segurança, correção e confiança (antes de considerar dieta utilizável)
- [ ] Verificação abrangente de exigências nutricionais e revisão por zootecnista/veterinário; até lá, sempre **candidata experimental**.
- [ ] Fibra de forragem: identificar `Fd_Category`/`Fd_Type`, revisar classificações de volumosos, calcular FDN de forragens; não confundir com fibra fisicamente efetiva (peNDF).
- [ ] Implementar peNDF apenas com dados físicos/partículas adequados; não inferir a partir de FDN isoladamente.
- [ ] Regras fundamentadas para FDN e amido por estado/produção, explicitando bibliografia, aplicabilidade e exceções; conservar limites opcionais do usuário.
- [ ] Minerais: Ca, P, Na, K, Mg, S e, depois, microminerais, biodisponibilidade e razões relevantes; comparar fornecimento com necessidades reais calculadas.
- [ ] Vitaminas e demais nutrientes essenciais de acordo com cobertura de dados NASEM.
- [ ] Restrições nutricionais de inclusão por ingrediente, com justificativas e exceções, distintas de limites operacionais do produtor.
- [ ] Validar rigorosamente unidades (kg MN × kg MS, %MS, Mcal/d, g/d), nomes de alimentos, dados ausentes e variações reais por análise bromatológica.
- [ ] Evitar dietas extremas e sobrealimentação: sinalizar, formular regras somente com base técnica; considerar excesso e limites superiores quando relevantes.
- [ ] Revisar pressupostos do `nd.demo('lactating_cow_test')`: expor ou estimar de modo validado cada parâmetro adicional (BCS, gestação, ganho, peso maduro, etc.); nunca extrapolar silenciosamente.
- [ ] Estimar/validar consumo de MS (DMI), hoje informado pelo usuário; permitir sobrescrita, registrar método e incerteza.
- [ ] Testar diferentes categorias fisiológicas — hoje somente vacas em lactação; não prometer atendimento de bezerras/vacas secas sem motor específico.
- [ ] Manter bloqueio/aviso de uso real até cobertura e validação profissional.

## P1 — Otimizador e explicabilidade
- [x] Multistart determinístico com quatro partidas (v3); registrar diagnóstico por tentativa.
- [x] Mensagens de falha com melhor candidata aproximada e déficits observados, sem declarar inviabilidade comprovada (v3).
- [x] Alertas descritivos de composição concentrada e excedente de energia (v3; gatilhos heurísticos, não recomendações).
- [ ] Teste real integrado NASEM e medição de tempo das quatro partidas.
- [ ] Diagnosticar causas de falhas: falta de alimentos, incompatibilidade entre limites, exigências inalcançáveis, falha numérica, dados faltantes, excesso de iterações.
- [ ] Separar explicitamente convergência numérica, factibilidade e otimalidade; melhorar tolerâncias escaladas, gradientes/derivadas, cache e logs.
- [ ] Reexecutar com diversas sementes e comparar custo/valores; benchmark de robustez em vários lotes e catálogos.
- [ ] Estudo de solver alternativo/método global ou relaxações para comparação (SLSQP não garante mínimo global).
- [ ] Sensibilidade de custos, preços sombra quando apropriado, análise de impacto de restrições e de alterações de preços.
- [ ] Política para ingredientes com quantidade zero: ocultar ou destacar 'considerado e não utilizado' sem mascarar seleção do usuário.
- [ ] Apresentar diagnósticos detalhados estruturados em UI/PDF, não apenas alertas textuais.
- [ ] Alertar preço zero/irrealista, alimento indisponível, limite operacional conflitante e ingredientes sem dados completos.

## P1 — Dois fluxos e UX de produção
- [x] Fluxo de escolha manual dos ingredientes, com preços editáveis.
- [x] Fluxo assistido v1: lote → seis candidatos → disponibilidade/preços → formulação.
- [ ] Evoluir seletor de seis alimentos fixos para regras contextualizadas por lote, exigências e região/estação se fornecidas; explicação para cada sugestão.
- [ ] Selecionar automaticamente de todo catálogo por categoria e dados disponíveis com saneamento e filtros; não presumir estoque.
- [ ] Confirmar disponibilidade, preços e dados de qualidade antes de otimizar; permitir excluir/trocar alimento sem apagar escolhas.
- [ ] Estoque, preço por unidade, data de cotação, frete, sazonalidade e custos reais editáveis.
- [ ] Comparar manual × assistido lado a lado, inclusive custo e cobertura nutricional.
- [ ] Ação de 'tentar novamente' após falha, sugestões concretas de alterações sustentadas no diagnóstico.
- [ ] Persistir lotes, cenário, históricos e formulações; editar/copiar/reformular.
- [ ] Exibir parâmetros avançados do NASEM, hipóteses e influência da idade; conferir idade exibida (2,28 anos gera ~833 dias; 820,8 dias seriam ~2,247 anos) e precisão de entrada.
- [ ] Melhorar campos de entrada: unidades, validação, acessibilidade, navegação e feedback ao usuário.
- [ ] Inicializar motor automaticamente (hoje usa `MUUFEED_FORMULADOR`), com falha explicativa quando ausente.

## P1 — Relatórios, qualidade e hackathon
- [x] PDF de candidata experimental, não avaliadas sem duplicações e rótulos legíveis.
- [x] PDF com aviso dinâmico e ID `R_AMIDO_MAX` sem quebra indevida.
- [ ] Integrar diagnóstico v3 de maneira tabular no PDF, com critérios de verificação e folgas.
- [ ] Revisar consistência do arredondamento da página financeira e tabelas dos nutrientes, custos e preços ilustrativos.
- [ ] Revisar quebra de páginas, evitar página 3 quase vazia e texto longo nas tabelas.
- [ ] Estender testes reais NASEM, teste de ponta a ponta Streamlit/PDF e regressão dos dois modos.
- [ ] Documentar origem dos dados da biblioteca e versões Python/NASEM; scripts reprodutíveis e execução totalmente offline.
- [ ] Criar cenários de demonstração: viável, não encontrado, limite FDN/amido ativo, ingredientes/preços trocados.
- [ ] Preparar apresentação do hackathon: problema, diferenciais do sistema especialista (regras auditáveis), demonstração real e limitações honestas.
- [ ] Manual rápido/instalação, capturas de tela, README definitivo, git tag e plano de fallback para demo.
- [ ] Auditar mensagens na interface, inclusive 'preços ilustrativos' e a distinção seleção vs formulação vs validação.

## P2 — Pós-hackathon / expansão
- [ ] Modelo de múltiplos lotes, cenários econômicos e previsão de demanda de estoque por período.
- [ ] Cadastro de fornecedor, importação de laudos bromatológicos e comparação com biblioteca de referência.
- [ ] Recomendações de substituição de insumos com comparação de custos e justificativa técnica.
- [ ] Exportar CSV/XLSX, histórico de decisões e relatórios comparativos.
- [ ] Melhorar energia/proteína/aminoácidos e demais exigências por fases da lactação com validação científica.
- [ ] Avaliação formal com profissional e casos reais/benchmark contra formulações especializadas.

## Critério de encerramento
Passar testes automatizados não equivale a validação zootécnica. O software só poderá deixar de chamar o resultado de 'experimental' depois que a cobertura dos nutrientes, qualidade dos insumos, critérios de segurança e validação externa estiverem demonstrados.
