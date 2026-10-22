"""Regressões dos ajustes finais de UX, PDF e diagnóstico SLSQP."""
from pathlib import Path
from services.pdf_report import TEXTO_EXPERIMENTAL, TITULO_CAIXA_EXPERIMENTAL

RAIZ = Path(__file__).parents[1]


def test_tela_resultados_nao_repete_explica_preco_unitario():
    codigo = (RAIZ / "ui/pages.py").read_text(encoding="utf-8")
    assert "é unitário e não deve ser somado" not in codigo
    assert "O total da dieta é a soma da coluna" not in codigo


def test_textos_do_pdf_sao_breves_e_humanos():
    codigo = (RAIZ / "services/pdf_report.py").read_text(encoding="utf-8")
    assert TEXTO_EXPERIMENTAL == "Candidata experimental - É necessária a revisão de um profissional"
    assert TITULO_CAIXA_EXPERIMENTAL == "Candidata experimental"
    assert '"Requisitos sem limites verificados: "' not in codigo
    assert "Resultado experimental: atende somente às restrições efetivamente verificadas." in codigo
    assert "Não use para alimentar animais sem revisão de um profissional." in codigo


def test_mais_pontos_iniciais_e_diagnostico_distinto():
    adapter = (RAIZ / "services/nasem_adapter.py").read_text(encoding="utf-8")
    engine = (RAIZ / "formulation_engine.py").read_text(encoding="utf-8")
    assert "max_iterations=100, restarts=6" in adapter
    assert '"distinct_valid_candidates": len(composicoes_distintas)' in engine
