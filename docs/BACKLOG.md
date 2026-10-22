# Backlog do MuuFeed — estado de entrega do Hackathon Rerum 2026.2

Este backlog descreve **o protótipo efetivamente implementado**, sem confundir funcionalidades prontas com prioridades de um produto futuro. A documentação principal está em [`DOCUMENTACAO_COMPLETA.md`](DOCUMENTACAO_COMPLETA.md) e a auditoria em [`AUDITORIA_FINAL_HACKATHON.md`](AUDITORIA_FINAL_HACKATHON.md).

## Implementado

- [x] Cadastro de lote para **vacas em lactação**, raças Holandesa, Jersey e ramo genérico experimental `Other`.
- [x] Catálogo NASEM com 284 ingredientes auditados, rótulos em português e busca PT/EN; preços de exemplo editáveis.
- [x] Sugestão **dinâmica** de ingredientes por programação linear química, restrições e contexto do lote; confirmação de disponibilidade e preço.
- [x] Formulação personalizada por menor custo com NASEM 2021 e SLSQP de seis pontos iniciais.
- [x] CMS informado ou estimado pela equação NRC 2001, explicitando a origem.
- [x] Limites opcionais de FDN, FDN de forragens, amido, extrato etéreo e participação individual.
- [x] Exigências de ME/MP e mínimos opcionais absorvidos de Ca/P, Na, Mg/Cl/K, com indicadores explicativos.
- [x] Análise de dieta existente com quantidades **fixas**, sem otimização.
- [x] Relatórios PDF para formulação e análise, cálculo financeiro por vaca/lote/mês.
- [x] Testes automatizados (246 passaram no ambiente completo informado pelo autor antes da auditoria; revisão adicional testada parcialmente).
- [x] Documentação integrada: README, fluxo, fórmulas, referências, auditoria, limpeza segura.

## P0 — antes de enviar (testar, não programar outro módulo)

- [ ] `python -m pytest -q` no ambiente final com NASEM, Streamlit e PyArrow.
- [ ] `python scripts/verificar_entrega_final.py` e `python scripts/auditar_catalogo_nutricional.py`.
- [ ] Demonstrar os três fluxos e a geração dos dois PDFs.
- [ ] Testar restrição de gordura ≤ 7% com resultado válido ou diagnóstico de falha.
- [ ] Testar rejeição de ingrediente/preço inválido e da situação sem candidata.
- [ ] Confirmar que `referencias.txt` está presente no pacote final.
- [ ] Registrar commit e ZIP de submissão; não alterar o núcleo após testes finais.

## Limitações do protótipo (devem ser declaradas)

- O estado fisiológico implementado é somente **vaca em lactação**; `Other` é ramo genérico sem calibração por raça específica.
- As exigências ME/MP e minerais não equivalem a validação nutricional completa: faltam vitaminas, micronutrientes, DCAD, peNDF, limites superiores, análise real de água/forragens e perfil lipídico.
- Limites operacionais do usuário não são limites de segurança universalmente válidos para cada alimento.
- A pré-triagem LP não avalia ME/MP/minerais; o NASEM faz a verificação posterior.
- O consumo estimado pela equação NRC 2001 não é medição; valores complementares do exemplo `nasem_dairy` são hipóteses.
- SLSQP encontra soluções locais e pode falhar; preços ilustrativos não são cotações reais.

## P1 — evolução pós-hackathon

- [ ] Permitir análise bromatológica específica da fazenda e dados minerais da água.
- [ ] Tornar parâmetros complementares do NASEM explicitamente configuráveis e validar sua influência.
- [ ] Adicionar limites nutricionais individuais embasados por ingrediente, processamento e tipo de dieta.
- [ ] Completar microminerais, vitaminas, peNDF, balanço lipídico/DCAD e limites superiores com profissional da área.
- [ ] Suporte específico a vacas secas/novilhas/bovinos de corte, com modelos e validações correspondentes.
- [ ] Comparar múltiplas candidatas/algoritmos e investigar motivos de falha numérica.
- [ ] Integrar atualização de preços/estoque, históricos e cenários de sensibilidade.
