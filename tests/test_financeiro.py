import math
from dataclasses import replace
import pytest
from services.financeiro import TOL_BRL, resumo_financeiro
from tests.factories import CUSTO_VACA, ingredientes_teste, itens_teste, resultado_teste


def resumo(res=None, n=40, ings="padrao"):
    return resumo_financeiro(res or resultado_teste(), n, ingredientes_teste() if ings == "padrao" else ings)


def test_valores_independentes_conferidos_a_mao():
    r = resumo()
    assert round(r.custo_vaca_dia, 4) == 14.5354          # 9,0909 + 5,4444
    assert round(r.custo_lote_dia, 2) == 581.41           # x 40 vacas
    assert round(r.custo_mes, 2) == 17442.42              # x 30 dias
    assert r.consumo_ms_kg == pytest.approx(12.0)
    assert r.consumo_mn_kg == pytest.approx(10 / 0.33 + 2 / 0.9)


def test_lote_e_mes_derivam_do_mesmo_custo_por_vaca():
    r = resumo()
    assert r.custo_lote_dia == pytest.approx(r.custo_vaca_dia * 40, rel=1e-12)
    assert r.custo_mes == pytest.approx(r.custo_lote_dia * 30, rel=1e-12)


def test_custos_individuais_somam_o_total_e_igualam_massa_x_preco():
    r = resumo()
    assert r.inconsistencias == ()
    assert sum(l.custo_brl for l in r.linhas) == pytest.approx(r.custo_vaca_dia, abs=1e-9)
    for l in r.linhas:
        assert l.custo_brl == pytest.approx(l.kg_mn * l.preco_mn_brl_kg, abs=1e-9)
    assert sum(l.pct_ms for l in r.linhas) == pytest.approx(100.0)


def test_preco_vem_do_item_ou_da_requisicao():
    com = resumo()
    sem = resumo_financeiro(replace(resultado_teste(), itens=itens_teste(com_preco=False)), 40, ingredientes_teste())
    assert [l.preco_mn_brl_kg for l in com.linhas] == [l.preco_mn_brl_kg for l in sem.linhas] == [0.30, 2.45]
    assert [l.origem_preco for l in com.linhas] == ["ilustrativo", "informado"]
    nada = resumo_financeiro(replace(resultado_teste(), itens=itens_teste(com_preco=False)), 40, None)
    assert [l.preco_mn_brl_kg for l in nada.linhas] == [None, None] and nada.inconsistencias == ()


def test_sem_numero_de_vacas_nao_inventa_custo_de_lote():
    r = resumo(n=None)
    assert r.custo_lote_dia is None and r.custo_mes is None and r.custo_vaca_dia is not None


def test_total_ausente_usa_soma_dos_itens():
    r = resumo(replace(resultado_teste(), custo_vaca_dia=None))
    assert r.custo_vaca_dia == pytest.approx(CUSTO_VACA)


def test_diferencas_de_arredondamento_sao_toleradas():
    # itens e total arredondados a centavos, massas a 2 casas: 14,53 + 14,54 etc. não são inconsistência
    its = [replace(i, kg_mn=round(i.kg_mn, 2), custo_brl=round(i.custo_brl, 2)) for i in itens_teste()]
    r = resumo(replace(resultado_teste(), itens=its, custo_vaca_dia=round(CUSTO_VACA, 2)))
    assert r.inconsistencias == ()


@pytest.mark.parametrize("alteracao, trecho", [
    (lambda r: replace(r, custo_vaca_dia=r.custo_vaca_dia + 1.0), "soma dos custos"),
    (lambda r: replace(r, itens=[replace(r.itens[0], custo_brl=r.itens[0].custo_brl + 1.0), r.itens[1]]), "difere de kg MN"),
    (lambda r: replace(r, itens=[replace(r.itens[0], kg_mn=r.itens[0].kg_mn * 1.1), r.itens[1]]), "teor de MS"),
    (lambda r: replace(r, itens=[replace(r.itens[0], preco_mn_brl_kg=0.50), r.itens[1]]), "preço do formulador"),
])
def test_detecta_divergencias_alem_do_arredondamento(alteracao, trecho):
    r = resumo(alteracao(resultado_teste()))
    assert any(trecho in m for m in r.inconsistencias), r.inconsistencias
