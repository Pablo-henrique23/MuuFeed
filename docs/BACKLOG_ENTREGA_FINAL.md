# Checklist objetivo — entrega do hackathon

## Antes de enviar

- [ ] Executar `python -m pytest -q` na `.venv` do projeto.
- [ ] Abrir Sugestão automática → confirmar ingredientes/preços → formular → baixar PDF.
- [ ] Formular manualmente um caso com limites de FDN, amido, FDNf e extrato etéreo.
- [ ] Abrir Analisar dieta e conferir que as quantidades informadas NÃO são alteradas.
- [ ] Testar cenário com restrições incompatíveis e verificar diagnóstico sem travamento.
- [ ] Executar `python scripts/auditar_catalogo_nutricional.py` no catálogo real.
- [ ] Conferir que `referencias.txt` está no ZIP.
- [ ] Gerar arquivo de entrega, guardar commit/tag e uma cópia de segurança.

## O que NÃO precisa ser implementado para entregar protótipo

- Microminerais, vitaminas e limites máximos completos.
- Vacas secas, novilhas, bovinos de corte.
- Integração com fornecedores, preços atualizados em tempo real, estoque ou login.
- Interface em nuvem / escalabilidade de produção.

## Comunicação da banca

"O MuuFeed considera o lote e as restrições informadas para selecionar opções de alimentos; utiliza o NASEM 2021 para avaliar exigências de energia, proteína e minerais e um otimizador de menor custo para encontrar uma **candidata experimental**. Os números são uma ferramenta de apoio à decisão, não prescrição nutricional pronta para fornecimento sem profissional especializado."
