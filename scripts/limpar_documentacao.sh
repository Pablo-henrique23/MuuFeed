#!/usr/bin/env bash
# Limpeza SEGURA de documentação histórica: prévia por padrão.
# NUNCA remove referencias.txt, código-fonte, testes ou dados NASEM.
set -euo pipefail
cd "$(dirname "$0")/.."
legacy=(
  INSTRUCOES_TRADUCAO.md
  LEIA-ME-PATCH-v12.md
  LEIA-ME-PATCH-V14.md LEIA-ME-PATCH-V15.md LEIA-ME-PATCH-V16.md
  LEIA-ME-PATCH-V17.md LEIA-ME-PATCH-V18.md
  LEIA-ME-HOTFIX-V18.md LEIA-ME-HOTFIX-ARROW-UI.md
  LEIA-ME-CORRECAO-TESTE-V19.md LEIA-ME-REVISAO-FINAL.md
  LEIA-ME-V13-CATALOGO.md LEIA-ME-PATCH-RACA-GENERICA.md
  auditoria_catalogo_nasem.csv
  BACKLOG_MUUFEED_COMPLETO.md
)
printf 'Arquivos históricos/removíveis encontrados:\n'
for f in "${legacy[@]}"; do
  if [[ -f "$f" ]]; then printf '  %s\n' "$f"; fi
done
if [[ "${1:-}" == "--apply" ]]; then
  echo 'Aplicando limpeza somente à lista acima. referencias.txt será preservado.'
  for f in "${legacy[@]}"; do
    if [[ -f "$f" ]]; then rm -- "$f"; fi
  done
else
  echo 'PRÉVIA: nenhum arquivo apagado. Após fazer commit: bash scripts/limpar_documentacao.sh --apply'
fi
