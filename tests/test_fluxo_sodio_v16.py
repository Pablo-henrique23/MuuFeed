"""Regressão: exigência de sódio sem fonte disponível recebe diagnóstico útil."""
import ast
from pathlib import Path
from types import ModuleType
import sys
from unittest.mock import patch

from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from services.nasem_adapter import NasemFormulador
from services.sodium_guidance import aviso_fonte_sodio, fontes_concentradas_sodio
from services.pdf_report import _fonte_legivel
from tests.test_contracts import lote_ok


def test_aviso_conjunto_sem_fonte_concentrada_na():
    feed = [Ingrediente('1', 'Corn silage, typical', 'Silagem', 35, 0.3)]
    text = aviso_fonte_sodio(feed, exigir_sodio=True)
    assert text and 'fonte concentrada de sódio' in text
    assert 'não prova de inviabilidade' in text
    assert aviso_fonte_sodio(feed, exigir_sodio=False) is None


def test_sal_reconhecido_mas_nao_imposto_automaticamente():
    ingredientes = ['Corn silage, typical', 'Sodium chloride (salt)']
    assert fontes_concentradas_sodio(ingredientes) == ('Sodium chloride (salt)',)
    assert aviso_fonte_sodio(ingredientes, exigir_sodio=True) is None
    assert fontes_concentradas_sodio(['Soybean hulls', 'Canola meal']) == ()


def _req(com_sal=False):
    alimentos = [
        Ingrediente('a', 'Corn silage, typical', 'Silagem', 35, .3),
        Ingrediente('b', 'Soybean meal, solvent 48CP', 'Farelo de soja', 90, 2.4),
    ]
    if com_sal:
        alimentos.append(Ingrediente('c', 'Sodium chloride (salt)', 'Sal', 100, 1.0,
                                    max_kg_mn=0.1))
    return RequisicaoFormulacao(lote_ok(), alimentos,
                                OpcoesFormulacao(consumo_ms_kg_dia=20, require_absorbed_na=True))


def test_inviabilidade_com_sodio_sem_suplemento_explica_causa_suspeita():
    mock_nd = ModuleType('nasem_dairy')
    mock_nd.demo = lambda _: (None, {}, {'DMIn_eqn': 0}, None)
    result_fake = {
        'status': 'experimental_sem_dieta_validada',
        'constraints_not_checked': ['vitaminas', 'fibra_fisicamente_efetiva'],
        'warnings': [],
        'solver_diagnostics': {'closest_candidate_gaps': {'na_abs_g_day': 25.2}},
    }
    with patch.dict(sys.modules, {'nasem_dairy': mock_nd}), \
         patch('services.nasem_adapter.formulate_diet', return_value=result_fake):
        resultado = NasemFormulador().formular(_req())
    assert resultado.status == 'inviavel'
    assert 'sódio absorvido foi exigido' in resultado.mensagem
    assert 'fonte concentrada' in resultado.mensagem
    assert any('25.200' in aviso for aviso in resultado.avisos)
    assert resultado.nao_avaliadas == ['vitaminas', 'fibra_fisicamente_efetiva']


def test_inviabilidade_com_fonte_nao_afirma_falta_de_sodio():
    mock_nd = ModuleType('nasem_dairy')
    mock_nd.demo = lambda _: (None, {}, {'DMIn_eqn': 0}, None)
    result_fake = {
        'status': 'experimental_sem_dieta_validada',
        'constraints_not_checked': ['vitaminas'],
        'warnings': [],
        'solver_diagnostics': {},
    }
    with patch.dict(sys.modules, {'nasem_dairy': mock_nd}), \
         patch('services.nasem_adapter.formulate_diet', return_value=result_fake):
        resultado = NasemFormulador().formular(_req(com_sal=True))
    assert resultado.status == 'inviavel'
    assert 'não há fonte concentrada' not in resultado.mensagem


def test_texto_fonte_nasem_e_limite_usuario():
    assert _fonte_legivel('Limite informado pelo usuário; composição NASEM') == 'NASEM 2021; limite do usuário'
    assert _fonte_legivel('Limite informado pelo usuário; composição NASEM, classificação explícita') == 'NASEM 2021; limite do usuário'
    assert _fonte_legivel('NASEM 2021 via nasem_dairy') == 'NASEM 2021'


def test_interface_exibe_aviso_previo_retorno_para_sugestao_e_distingue_pendencias():
    root = Path(__file__).resolve().parents[1]
    s = (root / 'ui/pages.py').read_text(encoding='utf-8')
    ast.parse(s)
    assert 'sodium_warning = aviso_fonte_sodio(' in s
    assert 'Revisar ingredientes e avaliar fonte de sódio' in s
    assert 'ss["assistido_sodio"] = True' in s
    assert 'Eles NÃO são, por si, a causa da ausência de candidata' in s
