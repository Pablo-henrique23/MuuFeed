"""Normalização numérica da tabela de indicadores para Streamlit/Arrow."""
from __future__ import annotations

import pandas as pd


def preparar_tabela_indicadores_analise(indicadores: list[dict]) -> pd.DataFrame:
    """Impede coluna mista float/str ("—") na conversão pandas → PyArrow.

    Campos sem exigência numérica continuam ausentes, nunca são transformados
    em zero ou usados para calcular um suposto atendimento.
    """
    tabela = pd.DataFrame(indicadores)
    for coluna in ("Ingestão", "Exigência"):
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_numeric(tabela[coluna], errors="coerce").astype("float64")
    return tabela
