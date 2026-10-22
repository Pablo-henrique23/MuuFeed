"""Auditoria opcional das traduções do catálogo instalado. Executar na raiz do MuuFeed."""
from __future__ import annotations

import csv
from pathlib import Path
from services.feed_catalog import CatalogoIngredientes


def main() -> None:
    cat = CatalogoIngredientes()
    dados = cat.tabela
    faltantes = dados[~dados['traduzido']]
    print(f"Catálogo NASEM: {len(dados)} ingredientes")
    print(f"Com rótulo em português: {int(dados['traduzido'].sum())}")
    print(f"A conferir/traduzir: {len(faltantes)}")
    arquivo = Path('traducoes_pendentes.csv')
    with arquivo.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['UID', 'Nome original NASEM', 'Sugestao de nome PT'])
        writer.writerows((r.uid, r.nome_original, '') for r in faltantes.itertuples(index=False))
    print(f"Relação para revisão: {arquivo.resolve()}")
    print('Observação: traduções alteram SOMENTE rótulos; os cálculos mantêm nomes originais.')

if __name__ == '__main__':
    main()
