from dataclasses import replace
import pandas as pd
import pytest
import formulation_engine as eng
from services.forage_ndf import is_forage
from formulation_engine import FeedChoice, FormulationRequest

class Output:
    def get_value(self, key):
        return {'An_MEIn': 60., 'Trg_MEuse': 40., 'An_MPIn_g': 2400., 'An_MPuse_g_Trg': 2000.}[key]

def req(minimum=None):
    return FormulationRequest(
        feeds=(FeedChoice('Corn silage, typical', .5, 35), FeedChoice('Canola meal', 2., 89)),
        animal={'An_StatePhys':'Lactating Cow', 'An_AgeDay': 821, 'An_BW': 620,
                'An_LactDay': 100, 'An_Parity_rl': 1},
        equations={'DMIn_eqn':0}, total_dm_kg=10, herd_size=10, restarts=2,
        min_forage_ndf_pct_dm=minimum,
    )

def fake_lib():
    return pd.DataFrame([
        {'Fd_Name':'Corn silage, typical','Fd_NDF':40.,'Fd_St':32.},
        {'Fd_Name':'Canola meal','Fd_NDF':30.,'Fd_St':2.},
    ])

def run(monkeypatch, minval):
    monkeypatch.setattr(eng, 'load_library', fake_lib)
    return eng.formulate_diet(req(minval), evaluate=lambda *args: Output())

def test_classificacao_curadoria_e_desconhecido():
    assert is_forage('Corn silage, typical') is True
    assert is_forage('Bermudagrass hay') is True
    assert is_forage('Canola meal') is False
    assert is_forage('Citrus pulp, dry') is False
    assert is_forage('Produto desconhecido') is None

def test_fdn_de_forragem_informativa(monkeypatch):
    result=run(monkeypatch,None)
    assert result['status']=='candidata_experimental'
    comp=result['nutrient_composition']
    assert comp['forage_ndf_pct_dm'] is not None
    assert comp['forage_ndf_min_pct_dm'] is None
    assert 'fdn_forragens' in result['constraints_not_checked']

def test_fdn_de_forragem_com_limite(monkeypatch):
    result=run(monkeypatch,15.)
    assert result['status']=='candidata_experimental'
    assert result['nutrient_composition']['forage_ndf_pct_dm']>=15.-1e-7
    assert 'fdn_forragens' in result['constraints_checked']
    assert any(rule['id']=='R_FDN_FORRAGEM_MIN' for rule in result['activated_rules'])

def test_classificacao_incompleta_falha_fechado(monkeypatch):
    monkeypatch.setattr(eng,'load_library',lambda: pd.concat([fake_lib(), pd.DataFrame([
        {'Fd_Name':'Unknown feed', 'Fd_NDF':40., 'Fd_St':10.}
    ])],ignore_index=True))
    request=replace(req(15.),feeds=(FeedChoice('Unknown feed',1.,80),FeedChoice('Canola meal',2.,89)))
    with pytest.raises(ValueError,match='Classificação de forragem pendente'):
        eng.formulate_diet(request,evaluate=lambda *args:Output(),catalog_names={'Unknown feed','Canola meal'})
