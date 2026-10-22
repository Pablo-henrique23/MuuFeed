"""Teste de integração da triagem V18 com o NASEM REAL instalado.

Executar da raiz: python scripts/verificar_selecao_guiada_v18.py
Não calcula dieta, não altera CSV, não prescreve uso de ingredientes.
"""
from models import Lote
from services.feed_catalog import CatalogoIngredientes
from services.constraint_guided_suggestion import (
    LimitesTriagem, sugerir_por_restricoes, conferir_selecao_quimica)


def main():
    cat=CatalogoIngredientes()
    lote=Lote(nome='QA Seleção Guiada', n_vacas=30, raca='Holandesa',
              idade_valor=2.25, idade_unidade='anos', peso_kg=675,
              ordem_lactacao=1, dias_lactacao=100, leite_kg_dia=25,
              gordura_pct=3.55, proteina_pct=3.66)
    limites=LimitesTriagem(min_ndf_pct_dm=25, max_starch_pct_dm=30,
                          min_forage_ndf_pct_dm=19, max_share_ingredient_pct_dm=30,
                          require_ca_p=True, require_na=True)
    r=sugerir_por_restricoes(lote,cat,limites)
    print(f'NASEM real: {len(cat.tabela)} ingredientes; {r.candidatos_examinados} elegíveis à triagem com preço.')
    assert len(cat.tabela)==284, 'Instalação com contagem de ingredientes distinta da auditada'
    assert r.composicao_possivel, 'Pré-triagem com limites de demonstração não encontrou combinação química; consultar dados e conjunto de preços.'
    assert len(r.sugestoes) >= 4
    assinalados=[s.uid for s in r.sugestoes if not s.opcional]
    ok,mensagem=conferir_selecao_quimica(cat,limites,assinalados)
    assert ok, mensagem
    print('Pré-triagem 25% FDN, 30% amido, 19% fNDF, teto 30%: OK (química, não NASEM ME/MP/minerais).')
    for s in r.sugestoes:
        print(f'  {"[marcado]" if not s.opcional else "[opcional]"} {s.nome_pt}: {s.grupo} (R$ {s.preco_ilustrativo:.2f}/kg MN, ilustrativo)')
    for a in r.avisos:
        print('AVISO:',a)
    print('OK — Triagem experimental testada. Formule no Streamlit e valide ME/MP/minerais separadamente.')


if __name__ == '__main__':
    main()
