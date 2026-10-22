# MuuFeed — hotfix v18: NameError na sugestão automática

Corrige o `NameError: name 'conferir_selecao_quimica' is not defined` na página "Sugestão automática".

## Como instalar sobre a v18

```bash
cd ~/MuuFeed
unzip -o ~/Downloads/muufeed_v18_hotfix_import.zip
python -m pytest -q
./init.sh
```

**Mudanças:** importa a função existente de `services.constraint_guided_suggestion` em `ui/pages.py` e adiciona teste de regressão em `tests/test_v18_hotfix_import_conferir.py`.

**Não modifica:** seleção dinâmica, cálculos NASEM, SLSQP, limites, preços ou PDFs.

**Teste manual:** cadastrar lote; abrir Sugestão automática; deixar modo guiado ligado, marcar ingredientes e verificar se a mensagem de pré-triagem da seleção é exibida sem erro. Depois continuar para Ingredientes e preços.
