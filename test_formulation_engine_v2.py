import sys
from dataclasses import replace
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parent))
import formulation_engine_v2 as eng

class FakeOutput:
    def __init__(self, vals): self.vals = vals
    def get_value(self, key): return self.vals[key]

def evaluate(diet, animal, equations, infusion):
    a, b = diet['kg_user'].tolist()
    return FakeOutput({'An_MEIn': 2*a + 5*b, 'Trg_MEuse':20,
                       'An_MPIn_g':130*a+350*b, 'An_MPuse_g_Trg':1400})

@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(eng, 'load_library', lambda: pd.DataFrame({
        'Fd_Name':['Forage A','Concentrate B'], 'Fd_NDF':[50,10], 'Fd_St':[5,70]}))
    return eng.FormulationRequest(feeds=(eng.FeedChoice('Forage A',.5,50),eng.FeedChoice('Concentrate B',2,100)),
      animal={'An_StatePhys':'Lactating Cow','An_AgeDay':1000,'An_BW':600,'An_LactDay':150,'An_Parity_rl':2},
      equations={'DMIn_eqn':0},total_dm_kg=10,herd_size=20)

def test_informativos_sem_limites(setup):
    out=eng.formulate_diet(setup,evaluate=evaluate,catalog_names={'Forage A','Concentrate B'})
    assert out['status']=='candidata_experimental'
    assert out['nutrient_composition']['ndf_pct_dm'] is None  # with synthetic external evaluator no catalog read
    assert 'fdn' in out['constraints_not_checked']

def test_limites_explicitamente_configurados(setup):
    req=replace(setup,min_ndf_pct_dm=30,max_starch_pct_dm=40)
    out=eng.formulate_diet(req,evaluate=evaluate,catalog_names={'Forage A','Concentrate B'})
    assert out['status']=='candidata_experimental'
    assert out['nutrient_composition']['ndf_pct_dm'] >= 30-1e-6
    assert out['nutrient_composition']['starch_pct_dm'] <= 40+1e-6
    assert 'fdn' in out['constraints_checked'] and 'amido' in out['constraints_checked']
    assert {'R_FDN_MIN','R_AMIDO_MAX'}.issubset({r['id'] for r in out['activated_rules']})

def test_dados_faltantes_rejeitam_restricao(setup,monkeypatch):
    monkeypatch.setattr(eng,'load_library',lambda:pd.DataFrame({'Fd_Name':['Forage A','Concentrate B'],
        'Fd_NDF':[None,10],'Fd_St':[5,70]}))
    with pytest.raises(ValueError,match='dados válidos'):
        eng.formulate_diet(replace(setup,min_ndf_pct_dm=25),evaluate=evaluate,catalog_names={'Forage A','Concentrate B'})

def test_limites_invalidos(setup):
    with pytest.raises(ValueError,match='percentual'):
        eng.validate_request(replace(setup,max_starch_pct_dm=101))
