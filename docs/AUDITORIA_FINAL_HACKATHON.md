# MuuFeed — Auditoria de código e prontidão de entrega

**Base auditada:** `MuuFeed.zip` enviado pelo desenvolvedor em 22/10/2026. **Objetivo:** fechar protótipo de hackathon, **não** certificar dieta para produção/uso zootécnico. A versão do ZIP prevalece sobre possíveis alterações posteriores no GitHub.

## Resultado executivo

**Recomendação:** o projeto possui os componentes essenciais para entrega como **protótipo experimental de formulação de dietas para vacas leiteiras em lactação**. Evitar adicionar módulos nutricionais novos de última hora. Preservar o termo "candidata experimental" e demonstrar uma execução com sal/ingredientes confirmados, restrições acionadas e relatório PDF. É necessária validação final no `.venv` local e empacotamento final.

### Funcionalidades verificadas no código

- Cadastro/validação de lote, incluindo raça genérica identificada.
- Catálogo NASEM, rótulos PT-BR, busca bilíngue e preços ilustrativos/editáveis.
- Sugestão dinâmica de ingredientes por LP química e heurísticas de perfil do lote.
- Escolha manual de ingredientes/preços e limites individuais.
- CMS informado ou estimado por NRC 2001; custo por vaca, lote e mês (30 dias).
- Otimização SLSQP multistart (6 pontos), avaliação NASEM e verificação posterior dos limites ativos.
- Restrições ME/MP obrigatórias; FDN, fNDF, amido, EE e minerais absorvidos opcionais.
- Análise de uma dieta existente sem alterar suas quantidades; PDF independente.
- Avisos de ingredientes restritos, lacunas de catálogo, déficits minerais e contexto experimental.

## Correções efetivamente feitas nesta revisão

| Prioridade | Achado | Medida |
|---|---|---|
| **Alta** | `scripts/limpar_documentacao.sh` listava **`referencias.txt`** para exclusão. | **Corrigido:** arquivo bibliográfico permanece e o novo script opera em prévia por padrão. |
| **Média** | Validação de preço/MS e limites em `validar_ingredientes()` aceitava valores `NaN`/infinito em chamadas externas ao formulário. | **Corrigido:** valida números finitos, positivos/não negativos e intervalos. `services/nasem_adapter.py` usa a mesma validação. |
| **Alta para entrega** | `README.md` misturava histórico de versões antigas com afirmações obsoletas sobre a seleção inicial. | **Substituído** por um README conciso, coerente com o fluxo v19 e ligado a documentação completa. |
| **Média** | Documentação científica, arquitetura e fórmulas estavam dispersas entre arquivos de patch. | **Consolidado** em `docs/DOCUMENTACAO_COMPLETA.md`, com referências e explicação dos dois algoritmos. |
| **Média** | Acúmulo de arquivos de patch/instrução e CSV de auditoria gerado. | **Listados para limpeza**; fornecido ZIP de entrega enxuto; nenhum arquivo de referência bibliográfica foi excluído. |

## Execução dos testes

- **Máquina do usuário antes da revisão:** 246 testes passaram, conforme log informado pelo desenvolvedor, com integração NASEM real.
- **Ambiente de revisão:** Python 3.13, NumPy/SciPy/pandas/ReportLab presentes; `nasem_dairy`, Streamlit e PyArrow **não instalados**. Por isso não é possível reproduzir aqui a suíte de integração completa.
- **Suíte executável no ambiente de revisão:** **217 passaram e 1 foi ignorado**, após as correções, excluindo explicitamente quatro módulos que exigem dependências não presentes (`test_service_and_app.py`, `test_catalog.py`, `test_integracao_nasem.py`, `test_environment.py`).
- **Compilação:** `python -m compileall -q .` deve terminar sem exceções.
- **Ainda obrigatório na máquina de entrega:** `python -m pytest -q`, teste do Streamlit (três fluxos), auditoria de catálogo, verificador de seleção, exportação de PDFs e execução offline.

Os testes sintéticos exercitam lógica e contratos, mas não equivalem a experimentos zootécnicos nem substituem a conferência de um lote real com profissional.

## Riscos e lacunas pendentes — classificados por relevância ao hackathon

### P0 — conferência de entrega, não desenvolvimento adicional

1. **Rodar a suíte completa no `.venv` real** após substituir os arquivos revisados. Qualquer regressão detectada deve ser resolvida antes do envio.
2. **Percorrer uma demonstração completa**: lote → sugestões → confirmação de preços → formular → resultados → PDF; repetir manual e análise de dieta existente.
3. **Verificar ao menos um cenário sem candidata** com alerta compreensível (não confundir falha numérica com inviabilidade absoluta).
4. **Conferir ZIP de entrega:** presença de `referencias.txt`, `data/`, `models/`, `services/`, `ui/`, `tests/`, `requirements.txt`, `README.md`, `init.sh` e `docs/DOCUMENTACAO_COMPLETA.md`.
5. **Arquivar cópia segura e fazer commit/tag** do estado efetivamente testado; não misturar documentação enviada com alterações posteriores não testadas.

### P1 — limitações documentadas, não bloqueiam entregar um protótipo experimental

1. **Parâmetros do exemplo NASEM:** vários campos do cenário `nd.demo('lactating_cow_test')` seguem por padrão, apesar dos 13 campos substituídos pelo lote. Essa abordagem permite executar o protótipo, mas é uma hipótese científica relevante. O roteiro de diagnóstico está em `scripts/verificar_hipoteses_nasem_v19.py`.
2. **Não há cobertura nutricional completa:** vitaminas A/D/E, microminerais, água, perfil de ácidos graxos, peNDF, balanço eletrolítico, limites superiores de minerais e concentrações seguras individuais não foram integralmente validados.
3. **A dieta pode ser economicamente extrema:** o SLSQP minimiza custo e pode concentrar um alimento até o teto informado; respeitar um teto genérico não demonstra inclusão segura para aquela matéria-prima. Referências de literatura são condicionais.
4. **Pré-triagem não é NASEM completo:** a LP inicial trata FDN/amido/fNDF/EE e teto, mas não ME, MP ou seis minerais absorvidos. Conjunto inicialmente sugerido pode se mostrar insuficiente depois.
5. **Cobertura de preços:** nem todos os 284 alimentos têm preços de demonstração; a sugestão dinâmica limita-se aos elegíveis com dados e preço.
6. **Faltam dados de composição em parte do catálogo:** na auditoria do usuário, 68/284 apresentavam lacunas entre 15 nutrientes monitorados. Não devem ser completadas com zero artificial.
7. **Raça Other:** funciona tecnicamente no NASEM real informado pelo usuário, mas não é uma parametrização validada especificamente para a raça digitada.
8. **Estado fisiológico:** o protótipo não formula vacas secas/novilhas/bovinos de corte.
9. **Consumo estimado:** previsão NRC 2001 não substitui ingestão medida; dados médios do lote podem não representar indivíduos.
10. **Numérico:** SLSQP é local, com inicializações determinísticas; ausência de solução encontrada não prova inviabilidade global nem que o menor custo é global.
11. **Dependências não rigidamente congeladas:** `requirements.txt` contém intervalos; para replicação perfeita registrar `python -m pip freeze` **no ambiente de entrega**, sem substituir automaticamente o requirements principal de última hora.

### P2 — melhorias não necessárias para apresentação

- Cadastro de análise bromatológica própria por ingrediente, estoque, fornecedores e preços de mercado.
- Formulação para outros estados fisiológicos e validação de raça genérica com dados experimentais.
- Formulação robusta com incerteza de composição e consumo, comparação entre múltiplos ótimos/candidatas.
- Cobertura veterinária completa de vitaminas, microminerais, limites superiores, DCAD, peNDF e ingestão de água.
- Ampliação do mecanismo de diagnóstico de inviabilidade, análise de sensibilidade e benchmarks de desempenho.

## Pontos de interpretação que podem aparecer na banca

- **Por que tudo aparece "Atende" no PDF otimizado?** Porque as candidatas aceitas passaram nas restrições *ativadas*. "Atende" a um mínimo não significa "ideal" nem ausência de excesso.
- **A sugestão é personalizada?** É dinâmica quanto à composição, restrições, disponibilidade/preço e usa heurísticas do lote; a **avaliação nutricional completa do conjunto é posterior**, no NASEM. Não afirmar que a sugestão inicial já valida minerais/energia/proteína.
- **Por que o custo mudou ao ativar 7% de EE?** O otimizador foi obrigado a procurar outra mistura ou falharia se nenhuma passasse. Uma regra nutricional adicional pode aumentar custo.
- **Por que não preencher todas as vitaminas e minerais?** Falta de dados seguros e limites científicos específicos para as matérias-primas reais; inventar valores é pior que registrar lacunas.
- **Por que há teto global?** Para permitir simulações de participação; não equivale a um máximo nutricional universal.
- **Por que o sistema não garante ótimo global?** Busca não linear com algoritmo SLSQP local e múltiplos pontos iniciais, seguida de validação de viabilidade.

## Auditoria da estrutura do projeto

- Não foram encontrados arquivos `.env`, credenciais ou `.venv` dentro do ZIP fornecido.
- Existe um `referencias.txt` na raiz que deve ser preservado. **Suas anotações de porcentagens não foram validadas individualmente como limites universais** e não viraram regras fixas do motor.
- Há numerosos `LEIA-ME-PATCH-*.md`, scripts diagnósticos e um CSV de auditoria gerado na raiz. São material histórico de desenvolvimento; não são dependências da execução. Veja `docs/LIMPEZA_ENTREGA.md`.
- `formulation_engine_v2.py` é um motor histórico independente, e `test_formulation_engine_v2.py` importa esse arquivo. **Não remover um sem o outro**; preferi preservar ambos na versão revisada para não reduzir a suíte de testes na última hora.
- `install_integration.py` é um utilitário de migração histórica que **altera arquivos-fonte quando executado**; não executar numa instalação já pronta. Não é usado pelo `init.sh`.
- A pasta `docs/` inclui CSV/XLSX de auditoria científica e outras validações que são evidências úteis, não arquivos exigidos para execução.

## Veredito

**Tecnicamente suficiente para submissão como protótipo experimental, condicionado à suíte e aos três fluxos passarem na máquina de entrega.** Não há base científica para declarar que todas as candidatas estejam "nutricionalmente adequadas" no sentido profissional. O melhor investimento antes do prazo é testar, documentar e congelar; não acrescentar outra categoria animal ou novos micronutrientes sem validação.
