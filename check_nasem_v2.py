"""Conferência local do catálogo NASEM e cálculo real do motor experimental v2."""
import nasem_dairy as nd
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet, load_library

prices = {'Alfalfa meal':1.40, 'Canola meal':2.30, 'Corn silage, typical':0.35, 'Corn grain HM, coarse grind':1.20}
diet, animal, equations, infusion = nd.demo('lactating_cow_test')
lib = load_library().set_index('Fd_Name')
print('Valores do catálogo NASEM (porcentagens de MS):')
for name in prices:
    row=lib.loc[name]
    print(f'{name}: MS={row["Fd_DM"]:.3f}%, FDN={row["Fd_NDF"]:.3f}%, amido={row["Fd_St"]:.3f}%')

seeds = dict(zip(diet['Feedstuff'],diet['kg_user']))
feeds = tuple(FeedChoice(name, price, float(lib.loc[name,'Fd_DM']),initial_dm_kg=float(seeds[name])) for name,price in prices.items())
total=float(diet['kg_user'].sum()); animal['Trg_Dt_DMIn']=total; equations['DMIn_eqn']=0
req=FormulationRequest(feeds=feeds,animal=animal,equations=equations,infusion=infusion,total_dm_kg=total,herd_size=30)
for title, case in [('SEM LIMITES (informativo)',req),('COM LIMITES ILUSTRATIVOS, NÃO RECOMENDAÇÕES',FormulationRequest(**{**vars(req),'min_ndf_pct_dm':25.,'max_starch_pct_dm':30.}))]:
    print('\n'+title)
    out=formulate_diet(case)
    print('Status:',out['status'],'Avaliações:',out['evaluation_count'])
    print('Restrições verificadas:',out['constraints_checked'])
    print('Restrições não verificadas:',out['constraints_not_checked'])
    print('Composição:',out.get('nutrient_composition'))
    print('Custo R$/vaca/dia:',out.get('cost_brl_cow_day'))
    print('Mensagens:',out['solver_messages'])
    if out['status']!='candidata_experimental':
        print('Não foi encontrada candidata neste caso: não concluir inviabilidade nutricional.')
