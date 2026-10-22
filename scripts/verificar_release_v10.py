"""Smoke test com nasem_dairy REAL: raças e seis macrominerais absorvidos.

Executar: python scripts/verificar_release_v10.py
Não valida dieta para uso prático. Não modifica o catálogo.
"""
from services.breed import para_raca_nasem
from services.nasem_requirements import ler_balancos, exigir_magnesio_cloro_potassio


def main():
    import nasem_dairy as nd
    dieta, animal_demo, eqns, infusion = nd.demo('lactating_cow_test')
    for raca in ('Holandesa', 'Jersey'):
        an = dict(animal_demo)
        an['An_Breed'] = para_raca_nasem(raca)
        out = nd.nasem(user_diet=dieta.copy(), animal_input=an,
                       equation_selection=dict(eqns), infusion_input=dict(infusion))
        if raca == 'Holandesa':
            assert an['An_Breed'] == 'Holstein'
        else:
            assert an['An_Breed'] == 'Jersey'
        bal = ler_balancos(out)
        for chave in ('calcio_absorvido', 'fosforo_absorvido', 'magnesio_absorvido',
                      'sodio_absorvido', 'cloro_absorvido', 'potassio_absorvido'):
            item = bal[chave]
            assert item['status'] in ('atende', 'viola'), f'{chave}: dados ausentes'
        pares = exigir_magnesio_cloro_potassio(out)
        assert len(pares) == 6
        print(f'{raca} → An_Breed={an["An_Breed"]}:')
        for chave, item in bal.items():
            print(f'  {item["label"]}: {item["intake"]:.2f} / {item["requirement"]:.2f} g/dia; {item["status"]}')
    print('OK — NASEM real fornece todos os balanços e ambas as raças foram enviadas explicitamente.')


if __name__ == '__main__':
    main()
