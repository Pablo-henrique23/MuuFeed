"""Exigências minerais NASEM: diferente de composição bruta; testável offline."""
from dataclasses import replace

import pandas as pd
import pytest

from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
from services.nasem_requirements import exigir_calcio_fosforo, ler_balancos


class Output:
    def __init__(self, d):
        self.d = d
    def get_value(self, key):
        return self.d[key]


def evaluator(diet, animal, equations, infusion):
    a = float(diet.loc[diet['Feedstuff']=='A', 'kg_user'].iloc[0])
    b = float(diet.loc[diet['Feedstuff']=='B', 'kg_user'].iloc[0])
    return Output({
        'An_MEIn': 40, 'Trg_MEuse': 30,
        'An_MPIn_g': 3000, 'An_MPuse_g_Trg': 2000,
        'Abs_CaIn': 1*a + 6*b, 'An_Ca_req': 30,
        'Abs_PIn': 1*a + 6*b, 'An_P_req': 30,
    })


def request(**overrides):
    return FormulationRequest(
        feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100)),
        animal={'An_StatePhys':'Lactating Cow', 'An_AgeDay':821, 'An_BW':625,
                'An_LactDay':100, 'An_Parity_rl':1},
        equations={'DMIn_eqn': 0}, total_dm_kg=10, herd_size=30,
        restarts=3, **overrides)


def test_balanco_nasem_so_compara_absorvido_a_absorvido():
    b = ler_balancos(evaluator(pd.DataFrame({'Feedstuff':['A','B'],'kg_user':[9,1]}), {}, {}, None))
    assert b['calcio_absorvido']['status'] == 'viola'
    assert b['fosforo_absorvido']['status'] == 'viola'
    assert b['calcio_absorvido']['unit'] == 'g/dia'
    assert b['magnesio_absorvido']['status'] == 'nao_avaliado'


def test_opcao_mineral_muda_realmente_otimizacao():
    kw = {'evaluate': evaluator, 'catalog_names': {'A', 'B'}}
    base = formulate_diet(request(), **kw)
    with_minerals = formulate_diet(request(require_absorbed_ca_p=True), **kw)
    assert base['status'] == with_minerals['status'] == 'candidata_experimental'
    assert base['cost_brl_cow_day'] == pytest.approx(10, abs=.01)
    assert with_minerals['cost_brl_cow_day'] >= 13.99
    assert with_minerals['cost_brl_cow_day'] <= 14.01
    assert 'calcio_absorvido' not in base['constraints_checked']
    assert 'calcio_absorvido' in with_minerals['constraints_checked']
    assert 'fosforo_absorvido' in with_minerals['constraints_checked']
    assert base['nutrient_composition']['absorbed_mineral_checks']['calcio_absorvido']['status'] == 'viola'
    assert with_minerals['nutrient_composition']['absorbed_mineral_checks']['calcio_absorvido']['status'] == 'atende'


def test_sem_solucao_mineral_nao_retorna_dieta_falsa():
    req = request(require_absorbed_ca_p=True)
    req = replace(req, feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100, maximum_dm_kg=2)))
    r = formulate_diet(req, evaluate=evaluator, catalog_names={'A','B'})
    assert r['status'] == 'experimental_sem_dieta_validada'
    assert r['solver_diagnostics']['closest_candidate_gaps']['ca_abs_g_day'] > 0


def test_chaves_minerais_faltantes_nao_sao_inventadas():
    out = Output({'Abs_CaIn':10, 'An_Ca_req':30})
    b = ler_balancos(out)
    assert b['calcio_absorvido']['status'] == 'viola'
    assert b['fosforo_absorvido']['status'] == 'nao_avaliado'
    with pytest.raises(ValueError, match='NASEM não retornou'):
        exigir_calcio_fosforo(out)


def test_adaptador_propaga_opcao_ao_motor(monkeypatch):
    import sys, types
    from unittest.mock import patch
    from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
    from services.nasem_adapter import NasemFormulador
    from tests.test_contracts import lote_ok
    import services.nasem_adapter as adapter
    fake_module = types.ModuleType('nasem_dairy')
    fake_module.demo = lambda _: (None, {}, {}, None)
    req = RequisicaoFormulacao(lote_ok(), [
        Ingrediente('a','Alfalfa meal','Alfafa',90,2),
        Ingrediente('b','Corn silage, typical','Silagem',35,.5)
    ], OpcoesFormulacao(consumo_ms_kg_dia=20,require_absorbed_ca_p=True))
    recorded=[]
    def formulate(request):
        recorded.append(request)
        return {'status':'experimental_sem_dieta_validada',
                'constraints_not_checked':['minerais'], 'warnings':[], 'solver_diagnostics':{}}
    with patch.dict(sys.modules,{'nasem_dairy': fake_module}), patch.object(adapter,'formulate_diet',side_effect=formulate):
        res=NasemFormulador().formular(req)
    assert recorded[0].require_absorbed_ca_p is True
    assert res.status == 'inviavel'
