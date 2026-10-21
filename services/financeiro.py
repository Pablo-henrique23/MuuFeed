"""Resumo financeiro ÚNICO da dieta: a tela e o PDF usam exatamente os mesmos números.

Fonte dos dados: `ResultadoFormulacao` (kg MS, kg MN, preço e custo por item, custo por vaca/dia) e,
opcionalmente, os ingredientes da requisição (preço, teor de MS, origem do preço).
Derivados, sempre a partir do MESMO custo por vaca/dia informado pelo formulador:
    custo do lote/dia = custo por vaca/dia × nº de vacas
    custo mensal      = custo do lote/dia × dias do mês (convenção: 30)
Sem Streamlit; não recalcula nem altera a dieta, apenas apresenta e confere.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from models import Ingrediente, ResultadoFormulacao
from services.formatting import brl, num

DIAS_MES = 30
TOL_BRL = 0.005  # meio centavo: erro máximo de arredondar um valor em R$ a 2 casas
TOL_KG = 0.005   # erro máximo de arredondar uma massa em kg a 2 casas


@dataclass(frozen=True)
class LinhaDieta:
    uid: str
    nome: str
    kg_ms: float
    kg_mn: float
    preco_mn_brl_kg: Optional[float]
    custo_brl: Optional[float]
    pct_ms: Optional[float]
    origem_preco: str = ""


@dataclass(frozen=True)
class ResumoFinanceiro:
    linhas: tuple[LinhaDieta, ...]
    consumo_ms_kg: float
    consumo_mn_kg: float
    custo_vaca_dia: Optional[float]
    n_vacas: Optional[int]
    custo_lote_dia: Optional[float]
    custo_mes: Optional[float]
    dias_mes: int
    inconsistencias: tuple[str, ...]


def resumo_financeiro(res: ResultadoFormulacao, n_vacas: Optional[int] = None,
                      ingredientes: Optional[Sequence[Ingrediente]] = None,
                      dias_mes: int = DIAS_MES) -> ResumoFinanceiro:
    por_uid = {i.uid: i for i in (ingredientes or [])}
    tot_ms = sum(i.kg_ms for i in res.itens)
    linhas: list[LinhaDieta] = []
    inc: list[str] = []
    for it in res.itens:
        ing = por_uid.get(it.uid)
        preco = it.preco_mn_brl_kg if it.preco_mn_brl_kg is not None else (ing.preco_mn_brl_kg if ing else None)
        linhas.append(LinhaDieta(it.uid, it.nome, it.kg_ms, it.kg_mn, preco, it.custo_brl,
                                 it.kg_ms / tot_ms * 100 if tot_ms else None, ing.origem_preco if ing else ""))
        if preco is not None and it.custo_brl is not None and abs(it.kg_mn * preco - it.custo_brl) > TOL_BRL + TOL_KG * preco:  # custo e massa podem estar arredondados
            inc.append(f"{it.nome}: custo informado ({brl(it.custo_brl)}) difere de kg MN × preço ({brl(it.kg_mn * preco)}).")
        if it.preco_mn_brl_kg is not None and ing and ing.preco_mn_brl_kg is not None \
                and abs(it.preco_mn_brl_kg - ing.preco_mn_brl_kg) > TOL_BRL:
            inc.append(f"{it.nome}: preço do formulador ({brl(it.preco_mn_brl_kg)}) difere do preço informado ({brl(ing.preco_mn_brl_kg)}).")
        if ing and ing.ms_pct > 0 and abs(it.kg_ms / (ing.ms_pct / 100) - it.kg_mn) > 2 * TOL_KG:
            inc.append(f"{it.nome}: kg MN ({num(it.kg_mn, 2)}) difere de kg MS ÷ teor de MS ({num(it.kg_ms / (ing.ms_pct / 100), 2)}).")
    custos = [l.custo_brl for l in linhas]
    completo = bool(custos) and all(c is not None for c in custos)
    vaca = res.custo_vaca_dia
    if vaca is None and completo:
        vaca = sum(custos)
    elif vaca is not None and completo and abs(sum(custos) - vaca) > TOL_BRL * (len(custos) + 1):  # cada parcela e o total podem estar arredondados
        inc.append(f"A soma dos custos individuais ({brl(sum(custos))}) difere do custo por vaca/dia ({brl(vaca)}).")
    lote = vaca * n_vacas if (vaca is not None and n_vacas) else None
    mes = lote * dias_mes if lote is not None else None
    return ResumoFinanceiro(tuple(linhas), tot_ms, sum(i.kg_mn for i in res.itens), vaca,
                            n_vacas or None, lote, mes, dias_mes, tuple(inc))
