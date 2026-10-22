"""Smoke test REAL do NASEM para as chaves minerais usadas no Motor v6.
Execute no ambiente com nasem_dairy antes de ativar restrições minerais.
"""
import nasem_dairy as nd
from services.nasem_requirements import ler_balancos

def main():
    dieta, animal, equacoes, infusao = nd.demo('lactating_cow_test')
    resultado = nd.nasem(user_diet=dieta, animal_input=animal,
                         equation_selection=equacoes, infusion_input=infusao)
    balancos = ler_balancos(resultado)
    for chave, item in balancos.items():
        print(f"{item['label']}: {item['intake']} / {item['requirement']} g/dia - {item['status']}")
    assert all(balancos[k]['status'] != 'nao_avaliado'
               for k in ('calcio_absorvido', 'fosforo_absorvido')), \
        'A API instalada não retornou todas as variáveis necessárias: reporte versão de nasem_dairy.'
    print('OK — Ca/P absorvidos e exigências encontrados no NASEM instalado.')

if __name__ == '__main__':
    main()
