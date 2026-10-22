# MuuFeed — Limpeza segura antes da entrega

**Regra obrigatória:** preservar `referencias.txt` e não apagar bibliografia, códigos essenciais, testes ou dados do catálogo.

O ZIP revisado inclui um **script de limpeza corrigido**:

```bash
# Na raiz do repositório: somente prévia
bash scripts/limpar_documentacao.sh

# OPCIONAL, após commit e revisão da lista
bash scripts/limpar_documentacao.sh --apply
```

## Podem ser retirados da raiz, sem afetar execução nem os testes atuais

São **instruções históricas de patches já aplicados** e relatório gerado, não arquivos usados pelo aplicativo:

```text
INSTRUCOES_TRADUCAO.md
LEIA-ME-PATCH-v12.md
LEIA-ME-PATCH-V14.md
LEIA-ME-PATCH-V15.md
LEIA-ME-PATCH-V16.md
LEIA-ME-PATCH-V17.md
LEIA-ME-PATCH-V18.md
LEIA-ME-HOTFIX-V18.md
LEIA-ME-HOTFIX-ARROW-UI.md
LEIA-ME-CORRECAO-TESTE-V19.md
LEIA-ME-REVISAO-FINAL.md
LEIA-ME-V13-CATALOGO.md
LEIA-ME-PATCH-RACA-GENERICA.md
BACKLOG_MUUFEED_COMPLETO.md   # histórico substituído pelo docs/BACKLOG.md e auditoria final
auditoria_catalogo_nasem.csv    # resultado gerado novamente pelo auditor
```

O arquivo `auditoria_catalogo_nasem.csv` pode ser **gerado novamente** por `python scripts/auditar_catalogo_nutricional.py`. Não confundir com `data/demo_prices.json` ou `data/feed_names_pt.json`, que são dados essenciais.

## Remoções OPCIONAIS após a entrega, com mais cautela

- `formulation_engine_v2.py` e `test_formulation_engine_v2.py` — um módulo histórico e seu teste **devem ser removidos em conjunto**; deixei ambos na versão revisada para preservar a contagem de testes e facilitar regressões.
- `install_integration.py` — patcher antigo que altera arquivos; não faz parte do fluxo atual e não deve ser executado.
- `check_nasem_v2.py`, `diagnosticar_formulacao.py`, `run_formulation_demo.py`, `nasem_smoke.py` — scripts de investigação/demonstração, não chamados pelo aplicativo; podem ficar fora do ZIP final se houver um backup Git, mas preservá-los é útil para auditoria.
- Arquivos de auditoria antigos em `docs/auditoria_catalogo_revisada_v14.csv` e `docs/auditoria_catalogo_cientifica_v14.xlsx` — históricos, não exigidos pela execução; deixá-los mostra trabalho de validação realizado.

## NÃO remover

```text
referencias.txt
README.md
requirements.txt
init.sh
app.py
formulation_engine.py
models/
services/
ui/
data/
.streamlit/config.toml
tests/
docs/DOCUMENTACAO_COMPLETA.md
docs/AUDITORIA_FINAL_HACKATHON.md
```

A documentação de referência em `docs/` (como `SELECAO_ORIENTADA_V18.md` e `VALIDACAO_V19.md`) pode ser preservada como histórico científico, mas o leitor principal deve começar por `README.md` e `docs/DOCUMENTACAO_COMPLETA.md`.

## Não empacotar arquivos locais desnecessários ou sigilosos

- `.venv/`, `.git/`, `.pytest_cache/`, `__pycache__/`, arquivos `.pyc`, `.env`, arquivos com senhas, tokens ou `.streamlit/secrets.toml`.
- Em caso de dúvida, verifique o ZIP final com `unzip -l arquivo.zip | less` antes de enviar.

## Checklist de congelamento

```bash
# 1. Fazer checkpoint do código testado
git add .
git commit -m "versao final hackathon muufeed"

# 2. Revisar documentação e rodar suíte completa
python -m pytest -q
python scripts/auditar_catalogo_nutricional.py

# 3. Confirmar presença da bibliografia
test -s referencias.txt && echo "referencias.txt preservado"

# 4. Gerar arquivo sem .git, .venv e segredos
zip -r ~/MuuFeed_entrega.zip . \
  -x '.git/*' '.venv/*' '*/__pycache__/*' '__pycache__/*' \
     '.pytest_cache/*' '*.pyc' '.streamlit/secrets.toml' '.env' '.env*'
```

**Nota:** se quiser usar o script com `--apply`, execute-o ANTES de gerar o ZIP e somente depois de conferir sua prévia. O ZIP limpo entregue nesta revisão já omite os arquivos históricos de patch, sem removê-los do diretório original do usuário.
