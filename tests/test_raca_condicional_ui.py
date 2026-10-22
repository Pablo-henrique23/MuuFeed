"""Regras de exibição da raça genérica: sem campos extras para Holandesa/Jersey."""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "ui" / "pages.py"


def test_nome_de_outra_raca_renderizado_so_para_outra():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "pagina_lote")
    condicionais = [n for n in ast.walk(func) if isinstance(n, ast.If)
                    and isinstance(n.test, ast.Compare)
                    and isinstance(n.test.left, ast.Name)
                    and n.test.left.id == "raca"
                    and len(n.test.ops) == 1 and isinstance(n.test.ops[0], ast.Eq)
                    and isinstance(n.test.comparators[0], ast.Name)
                    and n.test.comparators[0].id == "RACA_GENERICA"]
    assert condicionais, "Campo da raça genérica precisa ser condicional."
    assert any(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "text_input"
        and call.args and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == "Nome da outra raça (opcional)"
        for cond in condicionais for call in ast.walk(cond)
    )


def test_cadastro_reativo_e_salvar_explicito():
    s = SOURCE.read_text(encoding="utf-8")
    assert 'with st.container(border=True):' in s
    assert 'with st.form("form_lote"):' not in s
    assert 'st.button("Salvar lote", type="primary", key="salvar_lote")' in s
    assert 'raca_descricao=raca_descricao if raca == RACA_GENERICA else ""' in s
