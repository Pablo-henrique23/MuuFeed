"""Regressões de segurança/organização do pacote de entrega."""
from pathlib import Path
import math

from models import Ingrediente, validar_ingredientes

ROOT = Path(__file__).resolve().parents[1]


def test_limpeza_preserva_referencias_bibliograficas():
    script = (ROOT / "scripts" / "limpar_documentacao.sh").read_text(encoding="utf-8")
    assert "referencias.txt" not in script.split("legacy=(", 1)[1].split(")", 1)[0]
    assert (ROOT / "referencias.txt").exists()


def test_preco_nan_e_infinito_rejeitados():
    for preco in (float("nan"), float("inf"), -float("inf"), 0.0):
        x = Ingrediente("teste", "Corn", "Milho", 90, preco)
        assert validar_ingredientes([x]), f"deveria rejeitar preco={preco}"


def test_ms_e_limites_nao_finitos_rejeitados():
    x = Ingrediente("teste", "Corn", "Milho", float("nan"), 1.0)
    assert validar_ingredientes([x])
    for lim in (float("nan"), float("inf"), -1):
        x = Ingrediente("teste", "Corn", "Milho", 90, 1.0, max_kg_mn=lim)
        assert validar_ingredientes([x])


def test_preco_normal_valido():
    x = Ingrediente("teste", "Corn", "Milho", 90, 1.0, min_kg_mn=0, max_kg_mn=3)
    assert validar_ingredientes([x]) == []
