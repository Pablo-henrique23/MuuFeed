"""Regressões v19: gordura máxima opcional e simplificação do PDF."""
from dataclasses import replace
from io import BytesIO

import pandas as pd
from pypdf import PdfReader
import pytest

import formulation_engine as engine
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
from models import Indicador
from services.pdf_report import gerar_relatorio_pdf
from services.breed import RACA_GENERICA
from tests.factories import ingredientes_teste, resultado_teste
from tests.test_contracts import lote_ok


class Output:
    def get_value(self, k):
        return {"An_MEIn": 50., "Trg_MEuse": 40., "An_MPIn_g": 2500., "An_MPuse_g_Trg": 2000.}[k]


def mock_eval(*args):
    return Output()


def req(max_ee=None):
    return FormulationRequest(
        feeds=(FeedChoice("A", 1.0, 100), FeedChoice("B", 2.0, 100)),
        animal={"An_StatePhys": "Lactating Cow", "An_Breed": "Holstein", "An_AgeDay": 800,
                "An_BW": 620, "An_LactDay": 100, "An_Parity_rl": 1},
        equations={"DMIn_eqn": 0}, total_dm_kg=10, herd_size=20,
        max_ether_extract_pct_dm=max_ee, restarts=3,
    )


def library(fat_A=10.0, fat_B=2.0):
    return pd.DataFrame({"Fd_Name": ["A", "B"], "Fd_NDF": [20., 40.],
                         "Fd_St": [30., 5.], "Fd_CFat": [fat_A, fat_B],
                         "Fd_Ca": [.1, .1], "Fd_P": [.1, .1],
                         "Fd_Type": ["Concentrate", "Concentrate"],
                         "Fd_Category": ["Energy Source", "Energy Source"]})


def test_gordura_maxima_muda_dieta_e_validacao(monkeypatch):
    monkeypatch.setattr(engine, "load_library", library)
    unrestricted = formulate_diet(req(), evaluate=mock_eval, catalog_names={"A", "B"})
    restricted = formulate_diet(req(7), evaluate=mock_eval, catalog_names={"A", "B"})
    assert unrestricted["status"] == restricted["status"] == "candidata_experimental"
    assert unrestricted["cost_brl_cow_day"] == pytest.approx(10, abs=.01)
    assert restricted["cost_brl_cow_day"] == pytest.approx(13.75, abs=.01)
    comp = restricted["nutrient_composition"]
    assert comp["ee_pct_dm"] <= 7.0 + 1e-7
    assert comp["ee_max_pct_dm"] == 7
    assert "extrato_etereo" in restricted["constraints_checked"]
    assert any(r["id"] == "R_EXTRATO_ETEREO_MAX" for r in restricted["activated_rules"])


def test_limite_gordura_inviavel_nao_e_aceito(monkeypatch):
    monkeypatch.setattr(engine, "load_library", library)
    result = formulate_diet(req(1.0), evaluate=mock_eval, catalog_names={"A", "B"})
    assert result["status"] == "experimental_sem_dieta_validada"
    assert result["solver_diagnostics"]["closest_candidate_gaps"]["ee_pct_dm"] > 0


def test_gordura_nao_exigida_sem_dado_e_exigida_falha_fechada(monkeypatch):
    def lib_sem_gordura():
        return library().drop(columns=["Fd_CFat"])
    monkeypatch.setattr(engine, "load_library", lib_sem_gordura)
    assert formulate_diet(req(), evaluate=mock_eval, catalog_names={"A", "B"})["status"] == "candidata_experimental"
    with pytest.raises(ValueError, match="Fd_CFat"):
        formulate_diet(req(7), evaluate=mock_eval, catalog_names={"A", "B"})


def test_pdf_sem_faixa_caixa_e_ruido_tecnico():
    resultado = replace(resultado_teste("candidata_experimental"),
        avisos=["Diagnóstico SLSQP: 6/6 tentativas convergiram.",
                "Cenário NASEM utiliza parâmetros complementares do exemplo oficial; revisão.",
                "Energia calculada em 127.4% da exigência. Gatilho descritivo de 120%.",
                "NaCl declarado: 0.40% da MS.",
                "Exigências e ingestão referem-se a um animal médio do lote."],
        indicadores=[Indicador("extrato_etereo", "Extrato etéreo", "% da MS", 6.4, 7.0, "atende")],
    )
    pdf = gerar_relatorio_pdf(resultado, lote_ok(raca=RACA_GENERICA, raca_descricao="Girolando"), ingredientes_teste())
    paginas = [p.extract_text() for p in PdfReader(BytesIO(pdf)).pages]
    texto = " ".join(paginas)
    assert "Relatório de formulação" in texto
    assert "Faixa vermelha" not in texto
    assert "Candidata experimental - É necessária" not in texto
    assert "Resultado experimental: atende somente" not in texto
    assert "CANDIDATA EXPERIMENTAL: restrições" not in texto
    for termo in ("Diagnóstico SLSQP:", "NaCl declarado:", "Energia calculada em 127.4%",
                  "Cenário NASEM utiliza parâmetros complementares", "Preço por kg MN é unitário"):
        assert termo not in texto
    assert "Esta formulação não substitui" in texto
    assert "A composição dos alimentos é uma referência" in texto
    assert texto.count("Raça sem parametrização específica") == 1
    assert "Extrato etéreo" in texto


def test_pretriagem_quimica_respeita_gordura_e_exige_dados():
    from services.constraint_guided_suggestion import LimitesTriagem, conferir_selecao_quimica
    from tests.test_triagem_orientada_v18 import _cat
    cat = _cat()
    # Casos sintéticos legados não trazem essa coluna.
    ids = list(cat.precos_ilustrativos)
    ok, text = conferir_selecao_quimica(cat, LimitesTriagem(max_ether_extract_pct_dm=7), ids)
    assert not ok and "composição/preço" in text
    cat._bruta["Fd_CFat"] = [10., 8., 3., 4., 4., 2., 1., 1.]
    ok, text = conferir_selecao_quimica(cat, LimitesTriagem(max_ether_extract_pct_dm=7), ids)
    assert ok, text
    ok, text = conferir_selecao_quimica(cat, LimitesTriagem(max_ether_extract_pct_dm=.5), ids)
    assert not ok


def test_interface_transfere_gordura_e_remove_mensagem_antiga():
    from pathlib import Path
    ui = (Path(__file__).parents[1] / 'ui/pages.py').read_text()
    assert 'req.opcoes.max_ether_extract_pct_dm = limite_ee' in ui
    assert '("form_ee_max", "ee")' in ui
    assert 'max_ether_extract_pct_dm=ee_pre' in ui
    assert 'st.success("**Triagem dos ingredientes marcados:** " + diagnostico_quimica)' not in ui
