"""Regressão: raça NASEM sem fallback e Na absorvido como restrição REAL."""
from dataclasses import replace
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
import sys

import pandas as pd
import pytest

from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from services.breed import para_raca_nasem
from services.nasem_adapter import NasemFormulador
from services.nasem_requirements import exigir_sodio
from services.ingredient_suggestion import sugerir_ingredientes, CANDIDATOS_LACTACAO
from tests.test_contracts import lote_ok


class Output:
    def __init__(self, values):
        self.values = values
    def get_value(self, name):
        return self.values[name]


def evaluate(diet, animal, equations, infusion):
    a = float(diet.loc[diet['Feedstuff'] == 'A', 'kg_user'].iloc[0])
    b = float(diet.loc[diet['Feedstuff'] == 'B', 'kg_user'].iloc[0])
    return Output({
        'An_MEIn': 40.0, 'Trg_MEuse': 30.0,
        'An_MPIn_g': 3000.0, 'An_MPuse_g_Trg': 2000.0,
        'Abs_CaIn': a + 6 * b, 'An_Ca_req': 30.0,
        'Abs_PIn': a + 6 * b, 'An_P_req': 30.0,
        'Abs_NaIn': a + 6 * b, 'An_Na_req': 30.0,
    })


def make_request(**kwargs):
    return FormulationRequest(
        feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100)),
        animal={'An_Breed': 'Holstein', 'An_StatePhys': 'Lactating Cow',
                'An_AgeDay': 821, 'An_BW': 625, 'An_LactDay': 100,
                'An_Parity_rl': 1}, equations={'DMIn_eqn': 0},
        total_dm_kg=10, herd_size=30, restarts=3, **kwargs,
    )


def test_raça_convertida_estritamente_e_entrando_no_input():
    assert para_raca_nasem('Holandesa') == 'Holstein'
    assert para_raca_nasem(' jersey ') == 'Jersey'
    assert lote_ok(raca='Holandesa').para_animal_nasem()['An_Breed'] == 'Holstein'
    assert lote_ok(raca='Jersey').para_animal_nasem()['An_Breed'] == 'Jersey'
    with pytest.raises(ValueError, match='Raça não parametrizada'):
        lote_ok(raca='Outra / não parametrizada').para_animal_nasem()


@pytest.mark.parametrize('raca,esperada', [('Holandesa', 'Holstein'), ('Jersey', 'Jersey')])
def test_adaptador_substitui_raca_do_cenario_demo(raca, esperada):
    import services.nasem_adapter as adapter
    fake_nd = ModuleType('nasem_dairy')
    fake_nd.demo = lambda _: (None, {'An_Breed':'Holstein'}, {'DMIn_eqn':0}, None)
    req = RequisicaoFormulacao(lote_ok(raca=raca), [
        Ingrediente('a', 'Alfalfa meal', 'Alfafa', 90, 2),
        Ingrediente('b', 'Corn silage, typical', 'Silagem', 35, .5),
    ], OpcoesFormulacao(consumo_ms_kg_dia=20))
    gravados = []
    def fake_formulation(request):
        gravados.append(request)
        return {'status': 'experimental_sem_dieta_validada',
                'constraints_not_checked': ['minerais'], 'warnings': [],
                'solver_diagnostics': {}}
    with patch.dict(sys.modules, {'nasem_dairy': fake_nd}), \
         patch.object(adapter, 'formulate_diet', side_effect=fake_formulation):
        assert NasemFormulador().verificar_escopo(req)[0]
        NasemFormulador().formular(req)
    assert gravados[0].animal['An_Breed'] == esperada


def test_sodio_restringe_mesmo_sem_ca_p():
    inputs = {'evaluate': evaluate, 'catalog_names': {'A', 'B'}}
    sem = formulate_diet(make_request(), **inputs)
    com = formulate_diet(make_request(require_absorbed_na=True), **inputs)
    assert sem['status'] == 'candidata_experimental'
    assert com['status'] == 'candidata_experimental'
    assert sem['cost_brl_cow_day'] == pytest.approx(10, abs=.01)
    assert com['cost_brl_cow_day'] == pytest.approx(14, abs=.01)
    assert 'sodio_absorvido' in com['constraints_checked']
    assert any(r['id'] == 'R_NA_ABS' for r in com['activated_rules'])
    assert com['nutrient_composition']['absorbed_mineral_checks']['sodio_absorvido']['status'] == 'atende'


def test_sodio_e_ca_p_simultaneos():
    res = formulate_diet(make_request(require_absorbed_na=True, require_absorbed_ca_p=True),
                         evaluate=evaluate, catalog_names={'A','B'})
    assert res['status'] == 'candidata_experimental'
    assert res['cost_brl_cow_day'] == pytest.approx(14, abs=.01)
    for key in ('sodio_absorvido','calcio_absorvido','fosforo_absorvido'):
        assert key in res['constraints_checked']


def test_deficit_sodio_impede_aceitar_dieta():
    r = make_request(require_absorbed_na=True)
    r = replace(r, feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100, maximum_dm_kg=2)))
    res = formulate_diet(r, evaluate=evaluate, catalog_names={'A','B'})
    assert res['status'] == 'experimental_sem_dieta_validada'
    assert res['solver_diagnostics']['closest_candidate_gaps']['na_abs_g_day'] > 0


def test_dados_de_sodio_ausentes_bloqueiam_restricao():
    with pytest.raises(ValueError, match='sódio absorvido'):
        exigir_sodio(Output({}))


def test_suplemento_sem_limite_operacional_recusado():
    req = RequisicaoFormulacao(lote_ok(), [
        Ingrediente('a', 'Corn silage, typical', 'Silagem', 35, .3),
        Ingrediente('b', 'Sodium chloride (salt)', 'Sal comum', 100, 1.2),
    ], OpcoesFormulacao(consumo_ms_kg_dia=20, require_absorbed_na=True))
    valido, erro = NasemFormulador().verificar_escopo(req)
    assert not valido and 'máximo' in erro.lower()
    req.ingredientes[1].max_kg_mn = 0.1
    valido, erro = NasemFormulador().verificar_escopo(req)
    assert valido, erro


def test_suplemento_é_opcional_na_sugestao_e_desmarcado_na_tela():
    nomes = [n for n, _, _ in CANDIDATOS_LACTACAO] + ['Sodium chloride (salt)']
    cat = SimpleNamespace(tabela=pd.DataFrame([
        {'uid': str(i), 'nome_original': n, 'nome_pt': n, 'ms_pct': 100.0}
        for i, n in enumerate(nomes)]), precos_ilustrativos={})
    class Lote:
        estado = 'Lactating Cow'
        def validar(self): return [], []
    sem, _ = sugerir_ingredientes(Lote(), cat)
    com, _ = sugerir_ingredientes(Lote(), cat, incluir_fonte_sodio=True)
    assert len(sem) == 6 and len(com) == 7
    assert com[-1].nome_original == 'Sodium chloride (salt)'
    assert com[-1].grupo == 'Mineral'


def test_rotulo_sodio_legivel():
    from services.rotulos import rotulo_legivel
    assert rotulo_legivel('SODIO_ABSORVIDO') == 'Sódio absorvido (NASEM)'
