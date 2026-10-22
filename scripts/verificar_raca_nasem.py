"""Teste de verificação com o NASEM real, sem editar os arquivos do projeto.

Execute: python scripts/verificar_raca_nasem.py
Executa o mesmo cenário-demo com raça Holstein e Jersey, preservando os demais dados.
Não calcula uma dieta adequada nem prescreve alimentação.
"""
import nasem_dairy as nd
from services.breed import para_raca_nasem


def main():
    diet, animal_demo, equations, infusion = nd.demo('lactating_cow_test')
    for raca in ('Holandesa', 'Jersey'):
        breed = para_raca_nasem(raca)
        animal = dict(animal_demo)
        animal['An_Breed'] = breed
        saida = nd.nasem(user_diet=diet.copy(), animal_input=animal,
                         equation_selection=dict(equations), infusion_input=dict(infusion))
        ca_req = saida.get_value('An_Ca_req')
        prod_comp = saida.get_value('Mlk_Prod_comp')
        print(f'{raca} -> An_Breed={breed}; Ca requerido={ca_req:.4f} g/d; '
              f'leite previsto na equação={prod_comp:.4f} kg/d')
    print('OK — ambas as raças chegaram ao NASEM sem fallback para o exemplo.')


if __name__ == '__main__':
    main()
