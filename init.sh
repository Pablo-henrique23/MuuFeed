#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
exec python -m streamlit run app.py
