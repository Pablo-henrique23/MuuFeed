"""Testes de diagnóstico sem exigir a instalação do NASEM real."""
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet


class Output:
    def __init__(self, metrics):
        self.metrics = metrics
    def get_value(self, key):
        return self.metrics[key]


def request():
    return FormulationRequest(
        feeds=(FeedChoice('Forage X', 1, 50), FeedChoice('Protein Y', 2, 90)),
        animal={'An_StatePhys': 'Lactating Cow', 'An_AgeDay': 833, 'An_BW': 625,
                'An_LactDay': 100, 'An_Parity_rl': 1},
        equations={'DMIn_eqn': 0}, total_dm_kg=10, herd_size=30, restarts=3,
    )


def test_diagnostico_solucao_e_alertas():
    def evaluator(diet, animal, equations, infusion):
        return Output({'An_MEIn': 30, 'Trg_MEuse': 20,
                       'An_MPIn_g': 2200, 'An_MPuse_g_Trg': 2000})
    r = formulate_diet(request(), evaluate=evaluator,
                       catalog_names={'Forage X', 'Protein Y'})
    assert r['status'] == 'candidata_experimental'
    d = r['solver_diagnostics']
    assert d['attempts_count'] == 3 and d['validated_candidates'] >= 1
    assert not d['global_optimum_guaranteed']
    assert any('Composição concentrada' in w for w in r['descriptive_alerts'])
    assert any('Energia calculada' in w for w in r['descriptive_alerts'])


def test_diagnostico_sem_solucao_nao_confunde_com_inviabilidade():
    def evaluator(diet, animal, equations, infusion):
        return Output({'An_MEIn': 10, 'Trg_MEuse': 20,
                       'An_MPIn_g': 1000, 'An_MPuse_g_Trg': 2000})
    r = formulate_diet(request(), evaluate=evaluator,
                       catalog_names={'Forage X', 'Protein Y'})
    assert r['status'] == 'experimental_sem_dieta_validada'
    gaps = r['solver_diagnostics']['closest_candidate_gaps']
    assert gaps['me_mcal_day'] == 10
    assert gaps['mp_g_day'] == 1000
    assert 'não comprovam inviabilidade' in r['solver_diagnostics']['diagnostic_note']
