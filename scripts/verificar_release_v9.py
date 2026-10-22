"""Auditoria de regressão: executar no .venv que contém o NASEM real."""
from __future__ import annotations

from services.feed_catalog import CatalogoIngredientes
from services.breed import para_raca_nasem
from models import Lote


def main() -> None:
    cat = CatalogoIngredientes()
    t = cat.tabela
    total, traduzidos = len(t), int(t['traduzido'].sum())
    print(f'Catálogo NASEM: {total} itens; rótulos PT: {traduzidos}; pendentes: {total - traduzidos}')
    assert total == 284, 'Versão de catálogo diferente da auditada (284 ingredientes).'
    assert traduzidos == total, 'Há ingredientes sem rótulo PT.'
    for pt, en in (
        ('soro de leite fresco', 'whey fresh'),
        ('selenito de sodio', 'selenite sodium'),
        ('silagem de girassol', 'sunflower silage'),
        ('sal comum', 'sodium chloride'),
    ):
        a = set(cat.buscar(pt)['uid'])
        b = set(cat.buscar(en)['uid'])
        assert a and b and a == b, f'Busca bilíngue divergente: {pt} / {en}: {a} != {b}'
        print(f'Busca PT/EN OK: {pt} / {en}')
    for display, expected in [('Holandesa','Holstein'), (' HOLANDESA ', 'Holstein'), ('Jersey','Jersey')]:
        assert para_raca_nasem(display) == expected
        assert Lote(raca=display).para_animal_nasem()['An_Breed'] == expected
    print('Raça → An_Breed OK: Holandesa/HOLANDESA → Holstein; Jersey → Jersey')
    for dest in ('Produção de carne', 'Dupla aptidão (leite e carne)'):
        l = Lote(destinacao_economica=dest)
        try:
            l.para_animal_nasem()
        except ValueError:
            pass
        else:
            raise AssertionError(f'Destinação sem suporte aceita: {dest}')
    print('Destinação econômica OK: produção de leite é a única suportada')
    print('OK — revisão v9 aprovada nesta instalação do catálogo NASEM.')


if __name__ == '__main__':
    main()
