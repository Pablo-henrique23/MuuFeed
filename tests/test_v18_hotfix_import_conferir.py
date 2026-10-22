"""Garante que a função usada pela página assistida esteja importada.

Este erro passou despercebido em testes da pré-triagem diretamente no serviço;
a regressão confere a integração da página sem depender de Streamlit.
"""
import ast
from pathlib import Path


def test_pagina_sugestao_importa_conferir_selecao_quimica():
    pages = Path(__file__).resolve().parents[1] / "ui" / "pages.py"
    arvore = ast.parse(pages.read_text(encoding="utf-8"), filename=str(pages))
    importados = {
        alias.asname or alias.name
        for node in arvore.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "services.constraint_guided_suggestion"
        for alias in node.names
    }
    assert "conferir_selecao_quimica" in importados, (
        "ui/pages.py chama conferir_selecao_quimica mas não a importa"
    )
    paginas = [node for node in arvore.body if isinstance(node, ast.FunctionDef)
               and node.name == "pagina_sugestao_automatica"]
    assert len(paginas) == 1
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "conferir_selecao_quimica"
               for n in ast.walk(paginas[0]))


def test_modulo_triangulacao_exporta_funcao():
    from services.constraint_guided_suggestion import conferir_selecao_quimica
    assert callable(conferir_selecao_quimica)
