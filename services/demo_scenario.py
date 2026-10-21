"""Cenário demonstrativo SOMENTE para validar o layout da tela de resultados.

Usa a dieta de exemplo do pacote nasem_dairy (`lactating_cow_test`) avaliada pelo próprio pacote.
Não foi formulada nem otimizada pelo MuuFeed e não representa o lote informado.
"""
from __future__ import annotations

from models import Indicador, ItemDieta, ResultadoFormulacao
from services.feed_catalog import CatalogoIngredientes


def cenario_demonstrativo(catalogo: CatalogoIngredientes) -> ResultadoFormulacao:
    import nasem_dairy as nd

    dieta, animal, eqs, infusao = nd.demo("lactating_cow_test")
    saida = nd.nasem(user_diet=dieta, animal_input=animal, equation_selection=eqs, infusion_input=infusao)
    por_nome = {r.nome_original: r for r in catalogo.tabela.itertuples()}
    itens, total = [], 0.0
    for r in dieta.itertuples():
        info = por_nome[r.Feedstuff]
        kg_ms = float(r.kg_user)  # kg de MS/dia, conforme o pacote
        kg_mn = kg_ms / (info.ms_pct / 100)
        preco = catalogo.precos_ilustrativos.get(info.uid)
        custo = None if preco is None else kg_mn * preco
        total += custo or 0.0
        itens.append(ItemDieta(info.uid, info.nome_pt, kg_ms, kg_mn, custo))
    v = saida.get_value
    return ResultadoFormulacao(
        status="demonstracao",
        mensagem=("Exemplo de layout: dieta de demonstração do pacote nasem_dairy, avaliada pelo pacote. "
                  "Não foi formulada pelo MuuFeed e não corresponde ao lote informado."),
        itens=itens, custo_vaca_dia=total,
        indicadores=[
            Indicador("energia", "Energia metabolizável", "Mcal/dia", float(v("An_MEIn")), float(v("Trg_MEuse"))),
            Indicador("proteina", "Proteína metabolizável", "g/dia", float(v("An_MPIn_g")), float(v("An_MPuse_g_Trg"))),
        ],
        nao_avaliadas=["Restrições do sistema especialista (fibra, minerais, limites de inclusão)",
                       "Otimização de custo"],
        avisos=["Preços ilustrativos. Os indicadores são informativos, sem veredito de adequação."],
        modelo_referencia="NASEM 2021 via nasem_dairy (dieta de exemplo do pacote)",
        id_formulacao="DEMONSTRACAO",
    )
