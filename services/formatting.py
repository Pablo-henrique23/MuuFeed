"""Formatação brasileira (números, moeda, datas). Sem dependência de Streamlit."""
from __future__ import annotations

from datetime import date, datetime


def num(v, casas: int = 2, un: str = "") -> str:
    if v is None:
        return "—"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} {un}".strip() if un else s


def brl(v) -> str:
    return "—" if v is None else "R$ " + num(v, 2)


def pct(v, casas: int = 1) -> str:
    return "—" if v is None else num(v, casas) + " %"


def data_br(d) -> str:
    if d is None or d == "":
        return "não informada"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except ValueError:
            return d
    return d.strftime("%d/%m/%Y")


def data_hora_br(d) -> str:
    if d is None or d == "":
        return "não informada"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d)
        except ValueError:
            return d
    return d.strftime("%d/%m/%Y %H:%M") if isinstance(d, datetime) else data_br(d)
