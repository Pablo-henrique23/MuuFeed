"""Composição BRUTA de Ca/P via Fd_Ca/Fd_P, sem alegar exigência absorvível.

Validação de dados: percentual de MS [0, 100]. Ingredientes com quantidade zero
não invalidam o cálculo se não possuírem composição. Não usar como validação
mineral da dieta ou como exigência nutricional NASEM.
"""
from __future__ import annotations
import math
import pandas as pd

MINERAIS = {"ca": "Fd_Ca", "p": "Fd_P"}


def calcular_minerais(catalogo: pd.DataFrame, quantidades_ms: dict[str, float]) -> dict:
    """Retorna {ca_pct_dm, ca_g_day, p_pct_dm, p_g_day}; valor None se incompleto."""
    if 'Fd_Name' not in catalogo.columns:
        raise ValueError('Biblioteca sem Fd_Name')
    if catalogo['Fd_Name'].duplicated().any():
        raise ValueError('Nomes duplicados no catálogo NASEM')
    by_name = catalogo.set_index('Fd_Name')
    total = 0.0
    for nome, kg in quantidades_ms.items():
        x = float(kg)
        if not math.isfinite(x) or x < 0:
            raise ValueError('Quantidade MS inválida')
        if x > 0 and nome not in by_name.index:
            raise ValueError(f'Ingrediente ausente da biblioteca: {nome}')
        total += x
    if total <= 0:
        return {f'{m}_{u}': None for m in MINERAIS for u in ('pct_dm', 'g_day')}
    result = {}
    for mineral, column in MINERAIS.items():
        grams = 0.0
        complete = column in by_name.columns
        if complete:
            for nome, kg in quantidades_ms.items():
                if float(kg) == 0:
                    continue
                value = pd.to_numeric(by_name.at[nome, column], errors='coerce')
                if pd.isna(value) or not math.isfinite(float(value)) or not 0 <= float(value) <= 100:
                    complete = False
                    break
                grams += float(kg) * float(value) * 10.0 # kg MS × (% / 100) × 1000 g
        result[f'{mineral}_pct_dm'] = grams / (10 * total) if complete else None
        result[f'{mineral}_g_day'] = grams if complete else None
    return result
