"""Ca/P: somente composição bruta, nunca uma exigência assumida."""
import pandas as pd
import pytest
from services.mineral_composition import calcular_minerais
from services import diet_analysis
from models import Ingrediente, Lote


def test_porcentagem_e_gramas_nao_confundidos():
    library = pd.DataFrame([
        {'Fd_Name':'A','Fd_Ca':1.0,'Fd_P':0.2},
        {'Fd_Name':'B','Fd_Ca':0.5,'Fd_P':0.4},
    ])
    r = calcular_minerais(library, {'A':8.,'B':2.})
    assert r['ca_g_day'] == pytest.approx(90.)
    assert r['ca_pct_dm'] == pytest.approx(.9)
    assert r['p_g_day'] == pytest.approx(24.)
    assert r['p_pct_dm'] == pytest.approx(.24)


def test_mineral_faltante_nao_vira_zero():
    lib = pd.DataFrame([{'Fd_Name':'A','Fd_Ca':1.,'Fd_P':None},
                        {'Fd_Name':'B','Fd_Ca':None,'Fd_P':.3}])
    r = calcular_minerais(lib, {'A':1,'B':1})
    assert r['ca_g_day'] is None and r['p_g_day'] is None
    r2 = calcular_minerais(lib, {'A':1,'B':0})
    assert r2['ca_g_day'] == pytest.approx(10)
    assert r2['p_g_day'] is None


def test_valor_fora_da_escala_rejeitado():
    lib = pd.DataFrame([{'Fd_Name':'A','Fd_Ca':-2,'Fd_P':120}])
    r = calcular_minerais(lib, {'A':1})
    assert all(v is None for v in r.values())


def test_analise_dieta_informa_minerais_sem_veredito(monkeypatch):
    feed = pd.DataFrame([{'Fd_Name':'Corn silage, typical','Fd_DM':35,
                          'Fd_NDF':40,'Fd_St':30,'Fd_Ca':.3,'Fd_P':.25}])
    monkeypatch.setattr(diet_analysis, 'load_library', lambda: feed)
    class Out:
        def get_value(self,key):
            return dict(An_MEIn=20,Trg_MEuse=30,An_MPIn_g=1000,An_MPuse_g_Trg=1500)[key]
    lote = Lote(nome='Teste',n_vacas=10,raca='Holandesa',idade_valor=821,
                idade_unidade='dias',peso_kg=600,ordem_lactacao=1,
                dias_lactacao=100,leite_kg_dia=25,gordura_pct=4.5,proteina_pct=3.6)
    ins = [Ingrediente('a','Corn silage, typical','Silagem',35,.3)]
    r = diet_analysis.analisar_dieta(lote,ins,{'a':20},scenario=(None,{}, {}, None),evaluate=lambda *args:Out())
    assert r['minerals']['ca_g_day'] == pytest.approx(21.)
    assert r['minerals']['p_g_day'] == pytest.approx(17.5)
    assert r['validated_complete'] is False
