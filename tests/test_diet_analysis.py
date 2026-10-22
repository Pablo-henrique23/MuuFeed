"""Análise de dieta informada: não usar o otimizador nem declarar validação total."""
import pandas as pd
import pytest

from models import Ingrediente, Lote
from services import diet_analysis


class FakeResult:
    def get_value(self, key):
        return {'An_MEIn': 55, 'Trg_MEuse': 50, 'An_MPIn_g': 1800,
                'An_MPuse_g_Trg': 2000}[key]


def evaluator(diet, animal, equations, infusion):
    assert equations['DMIn_eqn'] == 0
    assert animal['Trg_Dt_DMIn'] == pytest.approx(diet['kg_user'].sum())
    assert animal['An_Breed'] == 'Holstein'
    return FakeResult()


@pytest.fixture
def scenario(monkeypatch):
    feeds = pd.DataFrame([
        {'Fd_Name': 'Corn silage, typical', 'Fd_DM': 35, 'Fd_NDF': 40, 'Fd_St': 30},
        {'Fd_Name': 'Canola meal', 'Fd_DM': 90, 'Fd_NDF': 25, 'Fd_St': 2},
    ])
    monkeypatch.setattr(diet_analysis, 'load_library', lambda: feeds)
    return (None, {}, {}, None)


def lote():
    return Lote(nome='Teste', n_vacas=10, raca='Holandesa', idade_valor=821,
                idade_unidade='dias', peso_kg=600, ordem_lactacao=1,
                dias_lactacao=100, leite_kg_dia=25, gordura_pct=4.5,
                proteina_pct=3.6)


def ingredientes():
    return [Ingrediente('a', 'Corn silage, typical', 'Silagem', 35, 0.3),
            Ingrediente('b', 'Canola meal', 'Canola', 90, 2.0)]


def test_quantidades_fixas_e_nutrientes(scenario):
    result = diet_analysis.analisar_dieta(lote(), ingredientes(), {'a': 20, 'b': 3},
                                         scenario=scenario, evaluate=evaluator)
    assert result['total_dm_kg'] == pytest.approx(9.7)
    assert result['total_mn_kg'] == pytest.approx(23)
    assert result['cost_cow_day'] == pytest.approx(12)
    assert result['cost_herd_day'] == pytest.approx(120)
    assert result['ndf_pct_dm'] == pytest.approx(100*(7*.4+2.7*.25)/9.7)
    assert result['starch_pct_dm'] == pytest.approx(100*(7*.3+2.7*.02)/9.7)
    assert result['forage_ndf_pct_dm'] == pytest.approx(100*(7*.4)/9.7)
    assert result['mp_in'] < result['mp_req']
    assert result['validated_complete'] is False


def test_quantidade_zero_ignoradas(scenario):
    res = diet_analysis.analisar_dieta(lote(), ingredientes(), {'a': 20, 'b': 0},
                                      scenario=scenario, evaluate=evaluator)
    assert len(res['items']) == 1


def test_dieta_vazia_recusada(scenario):
    with pytest.raises(ValueError, match='quantidade positiva'):
        diet_analysis.analisar_dieta(lote(), ingredientes(), {'a': 0, 'b': 0},
                                    scenario=scenario, evaluate=evaluator)


def test_preco_invalidado(scenario):
    ing = ingredientes()
    ing[0].preco_mn_brl_kg = None
    with pytest.raises(ValueError, match='preço positivo'):
        diet_analysis.analisar_dieta(lote(), ing, {'a': 5, 'b': 0}, scenario=scenario,
                                    evaluate=evaluator)
