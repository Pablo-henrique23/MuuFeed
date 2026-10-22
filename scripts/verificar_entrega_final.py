"""Verifica a integridade mínima da árvore de entrega; não formula dietas.

Uso: python scripts/verificar_entrega_final.py
Para testar nutrição/fluxos: python -m pytest -q no .venv real.
"""
from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "referencias.txt", "README.md", "requirements.txt", "init.sh", "app.py",
    "formulation_engine.py", "services/nasem_adapter.py",
    "services/constraint_guided_suggestion.py", "services/diet_analysis.py",
    "services/pdf_report.py", "services/analysis_pdf.py", "models/contracts.py",
    "data/demo_prices.json", "data/feed_names_pt.json", ".streamlit/config.toml",
    "docs/DOCUMENTACAO_COMPLETA.md", "docs/AUDITORIA_FINAL_HACKATHON.md",
    "docs/LIMPEZA_ENTREGA.md",
)

def main() -> int:
    faltando = [p for p in REQUIRED if not (ROOT / p).is_file()]
    print("MuuFeed — verificação de integridade da entrega")
    print(f"Arquivos obrigatórios: {len(REQUIRED) - len(faltando)}/{len(REQUIRED)}")
    for f in faltando:
        print(f"ERRO: arquivo ausente: {f}")
    if not (ROOT / "referencias.txt").is_file() or not (ROOT / "referencias.txt").read_text(encoding="utf-8").strip():
        print("ERRO: referencias.txt deve existir e conter bibliografia.")
        faltando.append("referencias.txt vazio")
    if not list((ROOT / "tests").glob("test_*.py")):
        print("ERRO: suíte de testes não foi incluída.")
        faltando.append("tests/")
    if sys.version_info[:2] != (3, 12):
        print(f"AVISO: ambiente Python {sys.version_info.major}.{sys.version_info.minor}; instalação de referência usa Python 3.12.")
    for modulo in ("nasem_dairy", "streamlit", "pyarrow", "scipy", "pandas", "reportlab", "pytest"):
        instalado = find_spec(modulo) is not None
        print(f"{'OK' if instalado else 'PENDENTE'}: dependência {modulo}")
    if faltando:
        print("FALHA: faltam arquivos necessários à entrega.")
        return 1
    print("OK: estrutura e bibliografia preservadas.")
    print("Próximo: python -m pytest -q ; teste manual dos 3 fluxos e PDFs.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
