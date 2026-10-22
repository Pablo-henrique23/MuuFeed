#!/usr/bin/env bash
# Limpeza apenas dos arquivos históricos listados, sem tocar em fontes, testes ou catálogos.
set -euo pipefail
cd "$(dirname "$0")/.."
legacy=(
  LEIA-ME-ANALISE-DIETA.md
  LEIA-ME-FLUXO-ASSISTIDO.md
  LEIA-ME-V3.md LEIA-ME-V4.md LEIA-ME-V5.md
  README_INTEGRACAO.md README_MOTOR_V2.md
  EXEC_FIRST.txt LEIA-ME.txt initialPrompt
  referencias.txt inconsistencias_embrapa.txt
  formulador_poc.py
)
echo 'Arquivos históricos candidatos à remoção:'
for file in "${legacy[@]}"; do
  if [[ -f "$file" ]]; then echo "  $file"; fi
done
if [[ "${1:-}" == '--apply' ]]; then
  echo 'Removendo apenas itens da lista acima (faça commit antes).'
  for file in "${legacy[@]}"; do if [[ -f "$file" ]]; then rm -- "$file"; fi; done
else
  echo 'Prévia apenas. Use: bash scripts/limpar_documentacao.sh --apply'
fi
