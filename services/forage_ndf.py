"""Classificação explícita e conservadora para FDN de forragens.

NÃO representa FDN fisicamente efetiva. Ingredientes não cadastrados retornam
None e não podem ser tratados como concentrado silenciosamente.
"""
from __future__ import annotations

FORAGE_NASEM_NAMES = frozenset({
    "Corn silage, typical", "Bermudagrass hay", "Alfalfa meal",
})
NONFORAGE_NASEM_NAMES = frozenset({
    "Canola meal", "Corn grain HM, coarse grind", "Corn grain dry, medium grind",
    "Soybean meal, solvent 48CP", "Citrus pulp, dry",
})

def is_forage(name: str) -> bool | None:
    if name in FORAGE_NASEM_NAMES:
        return True
    if name in NONFORAGE_NASEM_NAMES:
        return False
    return None
