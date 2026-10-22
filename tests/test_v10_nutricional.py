"""v10: cobertura Mg/Cl/K e remoção do campo de destinação econômica.

Simula saídas NASEM para exercitar o otimizador sem instalação externa.
"""
from dataclasses import replace, fields

import pandas as pd
import pytest

from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
from models import Lote, OpcoesFormulacao
from services.nasem_requirements import exigir_magnesio_cloro_potassio
from services.rotulos import rotulo_legivel


class Output:
    def __init__(self, vals):
        self.vals = vals
    def get_value(self, key):
        return self.vals[key]


def avaliar(dieta, animal, equacoes, infusao):
    a = float(dieta.loc[dieta['Feedstuff'] == 'A', 'kg_user'].iloc[0])
    b = float(dieta.loc[dieta['Feedstuff'] == 'B', 'kg_user'].iloc[0])
    supply = a + 6 * b
    return Output({
        'An_MEIn': 40, 'Trg_MEuse': 30,
        'An_MPIn_g': 3000, 'An_MPuse_g_Trg': 2000,
        'Abs_CaIn': supply, 'An_Ca_req': 30,
        'Abs_PIn': supply, 'An_P_req': 30,
        'Abs_NaIn': supply, 'An_Na_req': 30,
        'Abs_MgIn': supply, 'An_Mg_req': 30,
        'Abs_ClIn': supply, 'An_Cl_req': 30,
        'Abs_KIn': supply, 'An_K_req': 30,
    })


def req(**opts):
    return FormulationRequest(
        feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100)),
        animal={'An_StatePhys': 'Lactating Cow', 'An_Breed': 'Holstein',
                'An_AgeDay': 821, 'An_BW': 625, 'An_LactDay': 100, 'An_Parity_rl': 1},
        equations={'DMIn_eqn': 0}, total_dm_kg=10, herd_size=30,
        restarts=4, **opts)


def test_mg_cl_k_exigidos_alteram_efetivamente_dieta():
    opts = {'evaluate': avaliar, 'catalog_names': {'A', 'B'}}
    without = formulate_diet(req(), **opts)
    with_minerals = formulate_diet(req(require_absorbed_mg_cl_k=True), **opts)
    assert without['status'] == with_minerals['status'] == 'candidata_experimental'
    assert without['cost_brl_cow_day'] == pytest.approx(10, abs=.01)
    assert with_minerals['cost_brl_cow_day'] == pytest.approx(14, abs=.01)
    for key in ('magnesio_absorvido', 'cloro_absorvido', 'potassio_absorvido'):
        assert key in with_minerals['constraints_checked']
        assert key not in without['constraints_checked']
        assert with_minerals['nutrient_composition']['absorbed_mineral_checks'][key]['status'] == 'atende'
    assert {r['id'] for r in with_minerals['activated_rules']} >= {'R_MG_ABS', 'R_CL_ABS', 'R_K_ABS'}


def test_todos_os_seis_macrominerais_podem_ser_exigidos_juntos():
    r = formulate_diet(req(require_absorbed_ca_p=True, require_absorbed_na=True,
                           require_absorbed_mg_cl_k=True),
                       evaluate=avaliar, catalog_names={'A', 'B'})
    assert r['status'] == 'candidata_experimental'
    assert r['cost_brl_cow_day'] == pytest.approx(14, abs=.01)
    assert len(set(r['constraints_checked']) & {
        'calcio_absorvido', 'fosforo_absorvido', 'sodio_absorvido',
        'magnesio_absorvido', 'cloro_absorvido', 'potassio_absorvido'}) == 6


def test_deficit_com_limite_operacional_nao_e_aceito():
    r = req(require_absorbed_mg_cl_k=True)
    r = replace(r, feeds=(FeedChoice('A', 1, 100), FeedChoice('B', 2, 100, maximum_dm_kg=2)))
    result = formulate_diet(r, evaluate=avaliar, catalog_names={'A', 'B'})
    assert result['status'] == 'experimental_sem_dieta_validada'
    gaps = result['solver_diagnostics']['closest_candidate_gaps']
    assert all(gaps[key] > 0 for key in ('mg_abs_g_day', 'cl_abs_g_day', 'k_abs_g_day'))


def test_ausencia_dados_bloqueia_restricao_ao_inves_de_inventar_nutriente():
    invalido = Output({'Abs_MgIn': 20, 'An_Mg_req': 30, 'Abs_ClIn': 20, 'An_Cl_req': 30})
    with pytest.raises(ValueError, match='Mg, Cl e K'):
        exigir_magnesio_cloro_potassio(invalido)
    with pytest.raises(ValueError, match='booleano'):
        formulate_diet(req(require_absorbed_mg_cl_k=1), evaluate=avaliar, catalog_names={'A', 'B'})


def test_destinacao_removida_de_contrato_e_pdf():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert 'destinacao_economica' not in {f.name for f in fields(Lote)}
    assert 'Destinação econômica' not in (root / 'ui/pages.py').read_text(encoding='utf-8')
    assert 'Destinação econômica' not in (root / 'services/pdf_report.py').read_text(encoding='utf-8')
    assert 'Destinação econômica' not in (root / 'services/analysis_pdf.py').read_text(encoding='utf-8')
    assert 'An_Breed' in Lote(raca='Holandesa').para_animal_nasem()


def test_labels_legiveis_e_opcao_na_interface():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert rotulo_legivel('MAGNESIO_ABSORVIDO') == 'Magnésio absorvido (NASEM)'
    assert rotulo_legivel('CLORO_ABSORVIDO') == 'Cloro absorvido (NASEM)'
    assert rotulo_legivel('POTASSIO_ABSORVIDO') == 'Potássio absorvido (NASEM)'
    assert 'req.opcoes.require_absorbed_mg_cl_k = exigir_mg_cl_k' in (root / 'ui/pages.py').read_text(encoding='utf-8')


def test_adaptador_envia_flag_mg_cl_k_para_motor(monkeypatch):
    import sys
    from types import ModuleType
    from unittest.mock import patch
    from models import Ingrediente, RequisicaoFormulacao
    import services.nasem_adapter as adapter

    fake_nd = ModuleType('nasem_dairy')
    fake_nd.demo = lambda _: (None, {'An_Breed': 'Holstein'}, {'DMIn_eqn': 0}, None)
    lote = Lote(nome='Teste', n_vacas=30, raca='Jersey', idade_valor=821,
                idade_unidade='dias', peso_kg=625, ordem_lactacao=1,
                dias_lactacao=100, leite_kg_dia=25, gordura_pct=4.55,
                proteina_pct=3.66)
    pedido = RequisicaoFormulacao(lote, [
        Ingrediente('a', 'Alfalfa meal', 'Alfafa', 90, 2),
        Ingrediente('b', 'Corn silage, typical', 'Silagem de milho', 35, .5)
    ], OpcoesFormulacao(consumo_ms_kg_dia=20, require_absorbed_mg_cl_k=True))
    calls = []
    def fake_engine(request):
        calls.append(request)
        return {'status': 'experimental_sem_dieta_validada',
                'constraints_not_checked': ['vitaminas'], 'warnings': [],
                'solver_diagnostics': {}}
    with patch.dict(sys.modules, {'nasem_dairy': fake_nd}), \
         patch.object(adapter, 'formulate_diet', side_effect=fake_engine):
        result = adapter.NasemFormulador().formular(pedido)
    assert calls and calls[0].require_absorbed_mg_cl_k is True
    assert calls[0].animal['An_Breed'] == 'Jersey'
    assert result.status == 'inviavel'
