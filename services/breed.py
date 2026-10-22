"""Mapeamento ÚNICO e estrito de raça da interface para o NASEM.

Nunca retorna silenciosamente a raça do cenário de demonstração.
"""
from __future__ import annotations

BREEDS_NASEM = {"holandesa": "Holstein", "holstein": "Holstein", "jersey": "Jersey"}


def para_raca_nasem(raca: str) -> str:
    nome = str(raca).strip().casefold()
    if nome not in BREEDS_NASEM:
        raise ValueError("Raça não parametrizada: selecione Holandesa ou Jersey.")
    return BREEDS_NASEM[nome]
