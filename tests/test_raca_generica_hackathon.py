"""Regressões do ramo 'Other' genérico: sem fingir correspondência racial.

A execução com NASEM REAL depende de scripts/verificar_fallback_raca_nasem.py
na máquina do usuário; aqui validamos os contratos, encaminhamento e relatórios.
"""
from io import BytesIO
from types import ModuleType
from unittest.mock import patch
import sys

import pytest
from pypdf import PdfReader

from models import Lote, Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from services.breed import (
    AVISO_RACA_GENERICA, RACA_GENERICA, para_raca_nasem,
    rotulo_raca_lote, utiliza_raca_generica,
)
from services.nasem_adapter import NasemFormulador
from services.pdf_report import gerar_relatorio_pdf
from services.analysis_pdf import gerar_pdf_analise_dieta
from tests.test_contracts import lote_ok
from tests.factories import resultado_teste, ingredientes_teste
from tests.test_analysis_pdf_v6 import resultado as resultado_analise
from tests.test_raca_sodio_v8 import make_request


def txt(pdf):
    return " ".join(" ".join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages).split())


def test_selecao_generica_envia_other_e_preserva_duas_racas():
    assert para_raca_nasem('Holandesa') == 'Holstein'
    assert para_raca_nasem(' Jersey ') == 'Jersey'
    assert para_raca_nasem(RACA_GENERICA) == 'Other'
    assert para_raca_nasem(RACA_GENERICA.upper()) == 'Other'
    assert utiliza_raca_generica(RACA_GENERICA)
    with pytest.raises(ValueError):
        para_raca_nasem('Angus')  # sem escolha explícita do modelo genérico


def test_lote_generico_nao_bloqueia_validacao_e_registra_ressalva():
    l = lote_ok(raca=RACA_GENERICA, raca_descricao='Girolando')
    errors, notices = l.validar()
    assert not errors
    assert any('parâmetros genéricos' in item for item in notices)
    assert l.para_animal_nasem()['An_Breed'] == 'Other'
    assert 'Girolando' in rotulo_raca_lote(l)
    assert 'genérico' in rotulo_raca_lote(l)


def test_formulador_envia_other_para_o_motor_sem_perder_raca_informada():
    import services.nasem_adapter as adapter
    nd = ModuleType('nasem_dairy')
    nd.demo = lambda _: (None, {'An_Breed': 'Holstein'}, {'DMIn_eqn': 0}, None)
    lote = lote_ok(raca=RACA_GENERICA, raca_descricao='Gir Leiteiro')
    req = RequisicaoFormulacao(lote, [
        Ingrediente('a', 'Alfalfa meal', 'Farelo de alfafa', 90, 2),
        Ingrediente('b', 'Corn silage, typical', 'Silagem', 35, .5),
    ], OpcoesFormulacao(consumo_ms_kg_dia=20))
    captured = []
    def fake_formulate(request):
        captured.append(request)
        return {'status': 'experimental_sem_dieta_validada', 'warnings': [],
                'constraints_not_checked': [], 'solver_diagnostics': {}}
    with patch.dict(sys.modules, {'nasem_dairy': nd}), patch.object(adapter,'formulate_diet',side_effect=fake_formulate):
        allowed, reason = NasemFormulador().verificar_escopo(req)
        assert allowed, reason
        r = NasemFormulador().formular(req)
    assert captured and captured[0].animal['An_Breed'] == 'Other'
    assert any('parâmetros genéricos' in a for a in r.avisos)


def test_pdf_formulacao_identifica_parametros_genericos():
    l = lote_ok(raca=RACA_GENERICA, raca_descricao='Girolando')
    pdf = gerar_relatorio_pdf(resultado_teste('candidata_experimental'),l,ingredientes_teste())
    t=txt(pdf)
    assert 'Girolando' in t and 'Other' in t
    assert 'Trata-se de uma aproximação' in t


def test_pdf_analise_identifica_parametros_genericos():
    l = lote_ok(raca=RACA_GENERICA, raca_descricao='Gir Leiteiro')
    pdf = gerar_pdf_analise_dieta(resultado_analise(), l)
    t=txt(pdf)
    assert 'Gir Leiteiro' in t and 'Other' in t
    assert 'Trata-se de uma aproximação' in t


def test_ui_disponibiliza_generico_sem_remover_holstein_jersey():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    ui=(root/'ui/pages.py').read_text(encoding='utf-8')
    assert '["Holandesa", "Jersey", RACA_GENERICA]' in ui
    assert 'Nome da outra raça (opcional)' in ui
    assert 'raca_descricao=raca_descricao if raca == RACA_GENERICA else ""' in ui
