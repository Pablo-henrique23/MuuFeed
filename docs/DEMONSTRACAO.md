# Roteiro de demonstração — 6 a 8 minutos

1. **Abrir `./init.sh`**, mostrar que funciona localmente e sem API externa.
2. **Cadastrar lote Holandesa**: 30 vacas; 821 dias; peso 624,8 kg; paridade 1; 100 dias de lactação; leite 25,062 kg/dia, gordura 4,55%, proteína 3,66%; MS estimada 24,521 kg/dia na formulação.
3. **Sugestão assistida**: apresentar 6 ingredientes candidatos; avisar que disponibilidade e preços devem ser confirmados e que preços são ilustrativos. Demonstrar edição de preço.
4. **Formulação básica**: não configurar os limites opcionais; mostrar quantidades, custos, indicadores ME e MP, regras, ressalvas e PDF. **Não** caracterizar a dieta como adequada para uso real.
5. **Experimento Ca/P**: voltar à formulação e marcar “Exigir cálcio e fósforo ABSORVIDOS”. Mostrar aumento de custo ou ausência de candidata como consequência da exigência adicionada. Se não houver solução, explicar a recomendação de revisão dos ingredientes; não é crash.
6. **Analisar dieta existente**: inserir 20 kg MN de silagem de milho e 3 kg MN de farelo de soja; mostrar que o sistema não altera quantidades, calcula MS, custos, energia, proteína, minerais brutos e absorvidos quando NASEM oferece dados; exportar seu PDF próprio.
7. **Encerrar com a trilha de auditoria**: NASEM 2021; regras determinísticas, biblioteca original, dados do lote, limites opcionais, diagnósticos, PDF e testes. Explicar limitações científicas.

## Antes de apresentar

```bash
python -m pytest -q
python scripts/verificar_nasem_minerais.py
./init.sh
```

A execução com o NASEM real deve ser verificada no computador usado na apresentação; os testes simulados não provam compatibilidade científica.
