"""Regressão do erro com fNDF e alternativas da curadoria contextual.

Os testes com avaliador substituto checam apenas a montagem das restrições;
o resultado nutricional real permanece responsabilidade do nasem_dairy.
"""
from dataclasses import replace
from types import SimpleNamespace

import pandas as pd
import formulation_engine as eng
from formulation_engine import FeedChoice, FormulationRequest
from services.forage_ndf import is_forage
from services.ingredient_suggestion import CANDIDATOS_LACTACAO, _alternativas_do_lote


EXTRAS = (
    'Sorghum grain, dry, ground', 'DDGS, high protein', 'Soybean hulls',
    'Alfalfa meal', 'Wheat bran', 'Sunflower meal', 'Cottonseed meal',
)


class AvaliacaoFicticia:
    def get_value(self, key):
        return {'An_MEIn': 60., 'Trg_MEuse': 40.,
                'An_MPIn_g': 2400., 'An_MPuse_g_Trg': 2000.}[key]


def test_todas_alternativas_contextuais_tem_classificacao_explicita():
    for leite, dias in [(35, 60), (25, 120), (17, 260)]:
        lote = SimpleNamespace(leite_kg_dia=leite, dias_lactacao=dias)
        for nome, _, _ in _alternativas_do_lote(lote):
            assert is_forage(nome) is not None, nome
    assert is_forage('Alfalfa meal') is True
    for nome in EXTRAS:
        if nome != 'Alfalfa meal':
            assert is_forage(nome) is False, nome


def test_fdn_alternativas_fibrosas_nao_se_transforma_em_fdn_forragem():
    assert is_forage('Soybean hulls') is False
    assert is_forage('Wheat bran') is False
    assert is_forage('Cottonseed meal') is False


def test_todos_candidatos_sugeridos_possuem_classificacao():
    for nome, _, _ in CANDIDATOS_LACTACAO:
        assert is_forage(nome) is not None, nome
    for nome in EXTRAS:
        assert is_forage(nome) is not None, nome
    assert is_forage('Sodium chloride (salt)') is False
    assert is_forage('Ingredientes nunca classificados') is None


def test_motor_impõe_fdn_forragens_com_tres_subprodutos(monkeypatch):
    dados = pd.DataFrame([
        {'Fd_Name': 'Corn silage, typical', 'Fd_NDF': 40., 'Fd_St': 30.},
        {'Fd_Name': 'Soybean hulls', 'Fd_NDF': 60., 'Fd_St': 3.},
        {'Fd_Name': 'Wheat bran', 'Fd_NDF': 35., 'Fd_St': 22.},
        {'Fd_Name': 'Cottonseed meal', 'Fd_NDF': 30., 'Fd_St': 5.},
    ])
    monkeypatch.setattr(eng, 'load_library', lambda: dados)
    req = FormulationRequest(
        feeds=(FeedChoice('Corn silage, typical', 0.5, 35),
               FeedChoice('Soybean hulls', 0.8, 90),
               FeedChoice('Wheat bran', 0.9, 90),
               FeedChoice('Cottonseed meal', 1.0, 90)),
        animal={'An_StatePhys': 'Lactating Cow', 'An_AgeDay': 821,
                'An_Breed':'Holstein', 'An_BW': 625,
                'An_LactDay':100, 'An_Parity_rl':1},
        equations={'DMIn_eqn':0}, total_dm_kg=10,
        herd_size=10, restarts=2, min_forage_ndf_pct_dm=19.,
    )
    res = eng.formulate_diet(req, evaluate=lambda *args: AvaliacaoFicticia())
    assert res['status'] == 'candidata_experimental'
    assert 'fdn_forragens' in res['constraints_checked']
    nutr = res['nutrient_composition']
    assert nutr['forage_ndf_pct_dm'] >= 19 - 1e-7
    # Apesar da FDN elevada da casca de soja, sua contribuição à fNDF é ZERO.
    composicao = res['diet']
    assert composicao, 'A otimização deveria devolver quantidades por ingrediente'
    ms_silagem = next(item['kg_dm_cow_day'] for item in composicao
                      if item['ingredient'] == 'Corn silage, typical')
    assert abs(nutr['forage_ndf_pct_dm'] - ms_silagem / 10 * 40) < 1e-5
    # O teor TOTAL de FDN é maior pela contribuição não-forrageira.
    assert nutr['ndf_pct_dm'] > nutr['forage_ndf_pct_dm']


def test_ui_tem_exemplo_condicional_e_distingue_basicos_de_alternativas():
    from pathlib import Path
    ui = (Path(__file__).parents[1] / 'ui/pages.py').read_text(encoding='utf-8')
    assert 'mínima **19%**' in ui
    assert 'Os seis candidatos básicos continuam iguais' in ui


def test_fdn_de_concentrado_ausente_nao_bloqueia_fdn_de_forragens(monkeypatch):
    """Uma FDN desconhecida de subproduto não pode contar como forragem,
    mas tampouco precisa impedir a fNDF se sua classificação é conhecida.
    """
    dados = pd.DataFrame([
        {'Fd_Name':'Corn silage, typical', 'Fd_NDF':40., 'Fd_St':30.},
        {'Fd_Name':'Soybean hulls', 'Fd_NDF':float('nan'), 'Fd_St':3.},
    ])
    monkeypatch.setattr(eng, 'load_library', lambda: dados)
    request = FormulationRequest(
        feeds=(FeedChoice('Corn silage, typical',1.,35),
               FeedChoice('Soybean hulls',2.,90)),
        animal={'An_StatePhys':'Lactating Cow','An_Breed':'Holstein',
                'An_AgeDay':821,'An_BW':620,'An_LactDay':100,'An_Parity_rl':1},
        equations={'DMIn_eqn':0}, total_dm_kg=10, herd_size=10,
        restarts=2, min_forage_ndf_pct_dm=19.,
    )
    res = eng.formulate_diet(request, evaluate=lambda *args: AvaliacaoFicticia())
    assert res['status']=='candidata_experimental'
    assert res['nutrient_composition']['forage_ndf_pct_dm'] is not None
    assert res['nutrient_composition']['ndf_pct_dm'] is None
    # Para FDN total, a falta de dado para qualquer alimento deve bloquear.
    from dataclasses import replace
    import pytest
    with pytest.raises(ValueError, match='dados válidos e completos'):
        eng.formulate_diet(replace(request,min_ndf_pct_dm=25.),
                            evaluate=lambda *args: AvaliacaoFicticia())
