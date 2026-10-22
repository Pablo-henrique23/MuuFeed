"""Regressão: a unidade continua ao lado da idade, dentro do formulário.

A validação por unidade ocorre no contrato Lote, não nos limites do widget,
pois st.form só atualiza os widgets quando é enviado.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "ui" / "pages.py"


def test_idade_e_unidade_no_mesmo_formulario():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "pagina_lote")
    form = next(n for n in ast.walk(func) if isinstance(n, ast.With) and any(
        isinstance(item.context_expr, ast.Call)
        and isinstance(item.context_expr.func, ast.Attribute)
        and item.context_expr.func.attr == "form" for item in n.items))
    calls = [n for n in ast.walk(form) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert any(n.func.attr == "selectbox" and n.args and isinstance(n.args[0], ast.Constant)
               and n.args[0].value == "Unidade" for n in calls)
    assert any(n.func.attr == "number_input" and n.args and isinstance(n.args[0], ast.Constant)
               and n.args[0].value == "Idade média" for n in calls)


def test_limite_do_widget_independente_da_unidade():
    s = SOURCE.read_text(encoding="utf-8")
    assert 'max_value=12000.0' in s
    assert 'key="f_idade"' in s
    assert 'key="f_idade_dias"' not in s
    assert 'key="f_idade_meses"' not in s
    assert 'Lote(nome, int(n), raca, float(idade), un,' in s
