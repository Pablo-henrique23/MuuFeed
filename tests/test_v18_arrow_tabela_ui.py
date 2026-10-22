"""Regressão: relatório UI de análise não mistura float e travessão em Arrow."""
import ast
from pathlib import Path

import pandas as pd

from services.table_format import preparar_tabela_indicadores_analise


ROOT = Path(__file__).resolve().parents[1]


def test_requisitos_sem_limite_sao_nan_e_coluna_numerica():
    dados = [
        {"Indicador": "Energia", "Ingestão": 55.92, "Exigência": 49.81, "Situação": "Atende"},
        {"Indicador": "FDN", "Ingestão": 40.43, "Exigência": "—", "Situação": "Informativo"},
        {"Indicador": "Amido", "Ingestão": 20.24, "Exigência": None, "Situação": "Informativo"},
    ]
    tabela = preparar_tabela_indicadores_analise(dados)
    assert pd.api.types.is_float_dtype(tabela["Ingestão"])
    assert pd.api.types.is_float_dtype(tabela["Exigência"])
    assert tabela["Exigência"].iloc[0] == 49.81
    assert pd.isna(tabela["Exigência"].iloc[1])
    assert pd.isna(tabela["Exigência"].iloc[2])
    assert tabela["Situação"].tolist() == ["Atende", "Informativo", "Informativo"]


def test_tabela_arrow_se_disponivel():
    import importlib.util
    if importlib.util.find_spec("pyarrow") is None:
        import pytest
        pytest.skip("PyArrow não está instalado neste ambiente; executar na .venv do usuário")
    import pyarrow as pa
    tabela = preparar_tabela_indicadores_analise([
        {"Indicador": "ME", "Ingestão": 55.92, "Exigência": 49.81},
        {"Indicador": "FDN", "Ingestão": 40.43, "Exigência": "—"},
    ])
    arrow = pa.Table.from_pandas(tabela, preserve_index=False)
    assert arrow.column("Exigência").to_pylist() == [49.81, None]


def test_interface_chama_normalizador_e_mensagem_antiga_ausente():
    src = (ROOT / "ui/pages.py").read_text(encoding="utf-8")
    ast.parse(src)
    assert "preparar_tabela_indicadores_analise(indicadores)" in src
    assert "Novo fluxo orientado por restrições:" not in src
    assert "Defina os limites para receber sugestões" in src
    assert "conferir_selecao_quimica" in src
