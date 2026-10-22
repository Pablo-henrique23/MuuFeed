"""Casos de regressão v7: CMS opcional por equação e teto operacional."""
import math
import sys
import types
from unittest.mock import patch

import pytest

from services.dmi_estimator import estimar_consumo_nrc2001, estimar_do_lote
from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from services.nasem_adapter import NasemFormulador
from tests.test_contracts import lote_ok


def test_cms_estimativa_nrc2001_reprodutivel():
    cms = estimar_consumo_nrc2001(peso_kg=624.8, leite_kg_dia=25.062,
                                  gordura_pct=4.55, dias_lactacao=100)
    assert cms == pytest.approx(21.48313, rel=1e-5)
    lote = lote_ok()
    assert estimar_do_lote(lote) > 0


@pytest.mark.parametrize('peso,leite,gordura,dim', [(0,25,4,100),(600,-1,4,100),
                                                    (600,25,0,100),(600,25,4,-1)])
def test_estimador_rejeita_dados_invalidos(peso,leite,gordura,dim):
    with pytest.raises(ValueError):
        estimar_consumo_nrc2001(peso_kg=peso,leite_kg_dia=leite,
                                 gordura_pct=gordura,dias_lactacao=dim)


def _req(teto=None, origem='estimado_nrc2001'):
    ings=[Ingrediente('a','Alfalfa meal','Alfafa',90.0,2.0),
          Ingrediente('b','Corn silage, typical','Silagem',35.0,.5)]
    return RequisicaoFormulacao(lote_ok(),ings,OpcoesFormulacao(
        consumo_ms_kg_dia=20.0,consumo_ms_origem=origem,
        max_share_ingredient_pct_dm=teto))


def test_teto_operacional_inviavel_e_detectado_antes_de_chamar_nasem():
    ok,msg=NasemFormulador().verificar_escopo(_req(teto=40))
    assert not ok and 'teto' in msg.lower()


def test_teto_operacional_propagado_para_limites_dm_e_aviso():
    import services.nasem_adapter as adapter
    fake=types.ModuleType('nasem_dairy')
    fake.demo=lambda _:(None,{}, {},None)
    recorded=[]
    def formulate(req):
        recorded.append(req)
        return {'status':'experimental_sem_dieta_validada', 'constraints_not_checked':[],
                'warnings': ['Consumo total de matéria seca foi fornecido como entrada, não previsto pelo sistema.'],
                'solver_diagnostics': {}}
    with patch.dict(sys.modules, {'nasem_dairy':fake}),patch.object(adapter,'formulate_diet',side_effect=formulate):
        res=NasemFormulador().formular(_req(teto=60))
    assert len(recorded)==1
    assert all(f.maximum_dm_kg==pytest.approx(12) for f in recorded[0].feeds)
    assert any('60.0%' in s for s in res.avisos)
    assert any('NRC (2001)' in s for s in res.avisos)
    assert not any('foi fornecido como entrada' in s for s in res.avisos)


def test_nenhum_teto_nao_cria_bounds_artificiais():
    import services.nasem_adapter as adapter
    fake=types.ModuleType('nasem_dairy')
    fake.demo=lambda _:(None,{}, {},None)
    recorded=[]
    def formulate(req):
        recorded.append(req)
        return {'status':'experimental_sem_dieta_validada','constraints_not_checked':[],
                'warnings':[],'solver_diagnostics':{}}
    with patch.dict(sys.modules, {'nasem_dairy':fake}),patch.object(adapter,'formulate_diet',side_effect=formulate):
        NasemFormulador().formular(_req(teto=None,origem='informado'))
    assert all(f.maximum_dm_kg is None for f in recorded[0].feeds)


def test_cacop_obrigatorios_nao_escondem_outros_minerais():
    """Regressão A2: Ca/P ativos não podem ocultar déficit de sódio/cloro."""
    from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
    class Output:
        def __init__(self,vals): self.vals=vals
        def get_value(self,k): return self.vals[k]
    def evaluator(diet, animal, equations, infusion):
        a=float(diet.loc[diet.Feedstuff=='A','kg_user'].iloc[0])
        b=float(diet.loc[diet.Feedstuff=='B','kg_user'].iloc[0])
        return Output({'An_MEIn':50, 'Trg_MEuse':40,
                       'An_MPIn_g':2500,'An_MPuse_g_Trg':2000,
                       'Abs_CaIn':a+6*b,'An_Ca_req':30,
                       'Abs_PIn':a+6*b,'An_P_req':30,
                       'Abs_MgIn':20,'An_Mg_req':10,
                       'Abs_NaIn':2,'An_Na_req':15,
                       'Abs_ClIn':5,'An_Cl_req':10,
                       'Abs_KIn':200,'An_K_req':100})
    req=FormulationRequest(
        feeds=(FeedChoice('A',1,100),FeedChoice('B',2,100)),
        animal={'An_StatePhys':'Lactating Cow','An_AgeDay':821,
                'An_BW':625,'An_LactDay':100,'An_Parity_rl':1},
        equations={'DMIn_eqn':0},total_dm_kg=10,herd_size=30,
        require_absorbed_ca_p=True,restarts=3)
    result=formulate_diet(req,evaluate=evaluator,catalog_names={'A','B'})
    assert result['status']=='candidata_experimental'
    checks=result['nutrient_composition']['absorbed_mineral_checks']
    assert set(checks)=={'calcio_absorvido','fosforo_absorvido','magnesio_absorvido',
                         'sodio_absorvido','cloro_absorvido','potassio_absorvido'}
    assert checks['sodio_absorvido']['status']=='viola'
    assert checks['cloro_absorvido']['status']=='viola'
    assert checks['calcio_absorvido']['status']=='atende'
