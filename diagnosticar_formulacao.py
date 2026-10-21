"""Diagnostico do exemplo NASEM: python diagnosticar_formulacao.py
Nao fornece recomendacao alimentar; somente verifica configuracao do motor.
"""
import copy
import math

import nasem_dairy as nd
from formulation_engine import FormulationRequest, FeedChoice, _make_start, formulate_diet, _get_metrics, load_library
import numpy as np
import pandas as pd

PRECO_EXEMPLO = {"Alfalfa meal": 1.40, "Canola meal": 2.30, "Corn silage, typical": 0.35, "Corn grain HM, coarse grind": 1.20,}

def resumo(label, resultado):
    print('\n' + label)
    v = _get_metrics(resultado)
    for k, value in v.items():
        print(f'  {k}: {value:.8f}')
    print('  Saldo ME:', v['An_MEIn'] - v['Trg_MEuse'])
    print('  Saldo MP:', v['An_MPIn_g'] - v['An_MPuse_g_Trg'])
    return v


def main():
    diet, animal, equations, infusion = nd.demo('lactating_cow_test')
    print('Colunas da dieta:', diet.columns.tolist())
    print('Dieta original:\n', diet.to_string(index=False))
    print('DMI original em animal:', animal.get('Trg_Dt_DMIn'))
    print('Equacao DMI:', equations.get('DMIn_eqn'))
    print('Idade:', animal.get('An_AgeDay'), 'Paridade:', animal.get('An_Parity_rl'))
    resumo('1) NASEM do exemplo SEM alteracoes', nd.nasem(user_diet=diet.copy(), animal_input=copy.deepcopy(animal), equation_selection=copy.deepcopy(equations), infusion_input=copy.deepcopy(infusion)))

    total = float(diet['kg_user'].sum())
    animal_fixed = copy.deepcopy(animal)
    equations_fixed = copy.deepcopy(equations)
    animal_fixed['Trg_Dt_DMIn'] = total
    equations_fixed['DMIn_eqn'] = 0
    resumo('2) Mesma dieta com Trg_Dt_DMIn = soma kg_user', nd.nasem(user_diet=diet.copy(), animal_input=copy.deepcopy(animal_fixed), equation_selection=copy.deepcopy(equations_fixed), infusion_input=copy.deepcopy(infusion)))

    lib = load_library()
    name_col = 'Fd_Name' if 'Fd_Name' in lib.columns else 'Feedstuff'
    ingredients = lib.set_index(name_col)
    feeds = tuple(FeedChoice(
        name=str(r['Feedstuff']),
        price_as_fed_brl_kg=PRECO_EXEMPLO[str(r['Feedstuff'])],
        dry_matter_pct=float(ingredients.loc[str(r['Feedstuff']), 'Fd_DM']),
        initial_dm_kg=float(r['kg_user']),
    ) for _, r in diet.iterrows())
    initial = np.array([f.initial_dm_kg for f in feeds], dtype=float)
    low = np.array([f.minimum_dm_kg for f in feeds], dtype=float)
    high = np.array([total if f.maximum_dm_kg is None else f.maximum_dm_kg for f in feeds], dtype=float)
    start = _make_start(low, high, total, initial)
    print('\n3) Ponto inicial:')
    print('  consumo total:', total)
    print('  quantidade original:', initial)
    print('  quantidade reconstruida:', start)
    print('  diferenca maxima:', float(np.max(np.abs(initial-start))))
    recreated_diet = pd.DataFrame({'Feedstuff':[f.name for f in feeds], 'kg_user':start})
    resumo('4) Dieta reconstruida pelo motor', nd.nasem(user_diet=recreated_diet, animal_input=copy.deepcopy(animal_fixed), equation_selection=copy.deepcopy(equations_fixed), infusion_input=copy.deepcopy(infusion)))

    req = FormulationRequest(feeds=feeds, animal=animal_fixed, equations=equations_fixed, infusion=infusion, total_dm_kg=total, herd_size=30, max_iterations=80, restarts=2)
    out = formulate_diet(req)
    print('\n5) Resultado do motor:')
    print('  status:', out['status'])
    print('  avaliacoes:', out['evaluation_count'])
    print('  mensagens:', out.get('solver_messages'))
    if 'nutrition' in out:
        print('  nutricao:', out['nutrition'])
        print('  custo:', out['cost_brl_cow_day'])
    print('\nOBS: mesmo se encontrar candidata, nao e dieta nutricionalmente validada.')

if __name__ == '__main__':
    main()
