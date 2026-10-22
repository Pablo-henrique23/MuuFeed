"""Testes rápidos sem Streamlit e sem NASEM: regressão da entrega."""
from pathlib import Path
from services.ingredient_suggestion import CANDIDATOS_LACTACAO, sugerir_ingredientes
from tests.test_ingredient_suggestion import catalogo_teste


class OutroLote:
    estado = "Lactating Cow"
    def validar(self):
        return [], []
    peso_kg = 450
    leite_kg_dia = 18


def test_sugestao_assistida_nao_alega_personalizacao():
    cat = catalogo_teste()
    a, _ = sugerir_ingredientes(OutroLote(), cat)
    b, _ = sugerir_ingredientes(type("Lote", (), {"estado":"Lactating Cow", "validar": lambda self: ([], []),
        "peso_kg": 720, "leite_kg_dia": 40})(), cat)
    assert [s.nome_original for s in a] == [s.nome_original for s in b]
    assert len(a) == len(CANDIDATOS_LACTACAO) == 6


def test_fdn_forragens_so_em_avancado_e_indicador_preservado():
    ui = (Path(__file__).parents[1] / "ui/pages.py").read_text()
    assert 'with st.expander("Avançado: FDN proveniente de forragens (opcional)")' in ui
    assert 'key="form_fdn_forragem_min"' in ui
    assert "limite_fdn_forragem" in ui


def test_help_campos_avancados_presentes():
    ui = (Path(__file__).parents[1] / "ui/pages.py").read_text()
    for fragment in ("muito magra", "lactose medido", "Peso vivo esperado", "não confundir com dias em lactação"):
        assert fragment in ui


def test_frase_redundante_excluida_mas_aviso_essencial_conservado():
    raiz = Path(__file__).parents[1]
    motor = (raiz / "formulation_engine.py").read_text()
    pdf = (raiz / "services/pdf_report.py").read_text()
    assert "NÃO USAR para alimentar animais: modelo parcial." not in motor
    assert "Esta formulação não substitui a avaliação de médico-veterinário ou zootecnista." in pdf
