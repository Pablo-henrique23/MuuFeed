# Hotfix v18 — PyArrow e texto da sugestão

Aplicar **sobre a v18 com o hotfix de importação** já instalado.

- Normaliza as colunas `Ingestão` e `Exigência` da tabela **Analisar dieta existente** para números. Indicadores informativos sem exigência ficam vazios (NaN), nunca zero. Evita `ArrowInvalid: Could not convert '—' ... to double`.
- Simplifica a introdução da página **Sugestão automática**.
- Preserva `conferir_selecao_quimica` importada no hotfix anterior.
- Não altera cálculos NASEM, seleção guiada, custos nem PDFs.

```bash
cd ~/MuuFeed
unzip -o ~/Downloads/muufeed_v18_hotfix_arrow_ui.zip
python -m pytest -q
./init.sh
```

Confirme a ausência de erros na página **Analisar dieta existente** com indicadores nutricionais informativos e exigências numéricas. Para uma auditoria explícita com PyArrow, rode `python -m pytest -q tests/test_v18_arrow_tabela_ui.py`.
