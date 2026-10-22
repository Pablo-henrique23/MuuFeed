"""Estimativa explícita de consumo de matéria seca (CMS) em vacas lactantes.

Equação NRC 2001 (não NASEM 2021):
CMS (kg/d) = [0.372 * LCG4% + 0.0968 * BW^0.75] *
             [1 - exp(-0.192 * (dias_em_lactacao/7 + 3.67))]
LCG4% (kg/d) = 0.4 * leite_kg_dia + 15 * leite_kg_dia * gordura_pct / 100.
Fonte: NRC (2001), relatada em J. Dairy Sci. 2021,
https://pmc.ncbi.nlm.nih.gov/articles/PMC7825592/

É predição aproximada; não é consumo observado nem regra de adequação.
O motor ainda trabalha com CMS fixo: essa estimativa fornece o valor de entrada.
"""
from __future__ import annotations

import math


def estimar_consumo_nrc2001(*, peso_kg: float, leite_kg_dia: float,
                           gordura_pct: float, dias_lactacao: int) -> float:
    valores = (peso_kg, leite_kg_dia, gordura_pct, dias_lactacao)
    if not all(math.isfinite(float(v)) for v in valores):
        raise ValueError("Não é possível estimar consumo com dados não finitos.")
    if peso_kg <= 0 or leite_kg_dia <= 0 or not 0 < gordura_pct <= 12 or dias_lactacao < 0:
        raise ValueError("Informe peso, leite, gordura e dias em lactação válidos para estimar CMS.")
    leite_corrigido_gordura = 0.4 * leite_kg_dia + 15 * leite_kg_dia * (gordura_pct / 100)
    semanas = dias_lactacao / 7
    atraso = 1 - math.exp(-0.192 * (semanas + 3.67))
    estimado = (0.372 * leite_corrigido_gordura + 0.0968 * peso_kg ** 0.75) * atraso
    if not math.isfinite(estimado) or estimado <= 0:
        raise ValueError("Não foi possível gerar estimativa válida de consumo de MS.")
    return float(estimado)


def estimar_do_lote(lote) -> float:
    if lote.estado != "Lactating Cow":
        raise ValueError("A estimativa NRC (2001) implementada é para vacas em lactação.")
    return estimar_consumo_nrc2001(peso_kg=lote.peso_kg, leite_kg_dia=lote.leite_kg_dia,
                                   gordura_pct=lote.gordura_pct, dias_lactacao=lote.dias_lactacao)
