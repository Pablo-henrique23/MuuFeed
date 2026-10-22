import math
from models import Ingrediente, Lote, RequisicaoFormulacao, ResultadoFormulacao, validar_ingredientes


def lote_ok(**kw):
    base = dict(nome="L1", n_vacas=40, raca="Holandesa", idade_valor=4, idade_unidade="anos", peso_kg=620,
                ordem_lactacao=2, dias_lactacao=120, leite_kg_dia=28, gordura_pct=3.7, proteina_pct=3.2)
    base.update(kw)
    return Lote(**base)


def test_lote_valido():
    erros, _ = lote_ok().validar()
    assert erros == []


def test_conversao_idade_para_dias():
    assert math.isclose(lote_ok(idade_valor=2, idade_unidade="anos").idade_dias, 730.5)
    assert math.isclose(lote_ok(idade_valor=24, idade_unidade="meses").idade_dias, 24 * 30.4375)
    assert lote_ok(idade_valor=821, idade_unidade="dias").idade_dias == 821


def test_idade_chega_ao_motor():
    assert lote_ok(idade_valor=3).para_animal_nasem()["An_AgeDay"] == 3 * 365.25
    assert lote_ok(idade_valor=821, idade_unidade="dias").para_animal_nasem()["An_AgeDay"] == 821


def test_entradas_invalidas():
    assert lote_ok(nome=" ").validar()[0]
    assert lote_ok(peso_kg=0).validar()[0]
    assert lote_ok(leite_kg_dia=-1).validar()[0]
    assert lote_ok(gordura_pct=25).validar()[0]
    assert lote_ok(n_vacas=0).validar()[0]
    assert lote_ok(estado="Heifer").validar()[0]
    assert lote_ok(idade_valor=0.1).validar()[0]


def test_hipoteses_padrao_sao_sinalizadas():
    erros, avisos = lote_ok().validar()
    assert any("padrão" in a for a in avisos)
    assert set(lote_ok().campos_padrao) == {"bcs", "lactose_pct", "peso_maduro_kg", "dias_gestacao"}
    assert "bcs" not in lote_ok(bcs=3.5).campos_padrao


def test_conversao_ms_mn():
    ing = Ingrediente("U", "Corn", "Milho", 90.0, 1.80)
    assert math.isclose(ing.preco_ms_brl_kg, 2.0)
    ing2 = Ingrediente("U", "Corn", "Milho", 90.0, 1.0, min_kg_mn=1.0, max_kg_mn=2.0)
    assert ing2.limites_ms() == (0.9, 1.8)


def test_validacao_ingredientes():
    assert validar_ingredientes([])
    assert validar_ingredientes([Ingrediente("U", "C", "Milho", 90, None)])
    assert validar_ingredientes([Ingrediente("U", "C", "Milho", 90, 1.0, min_kg_mn=3, max_kg_mn=1)])
    assert validar_ingredientes([Ingrediente("U", "C", "Milho", 90, 1.0)]) == []


def test_requisicao_serializavel_e_resultado_sem_campo_de_completude():
    req = RequisicaoFormulacao(lote_ok(), [Ingrediente("U", "C", "Milho", 90, 1.0)])
    d = req.to_dict()
    assert d["lote"]["nome"] == "L1" and d["ingredientes"][0]["uid"] == "U"
    assert not any("complet" in k for k in ResultadoFormulacao(status="erro").__dict__)


def test_idade_em_dias_validacao():
    assert lote_ok(idade_valor=821, idade_unidade="dias").validar()[0] == []
    assert lote_ok(idade_valor=200, idade_unidade="dias").validar()[0]
    assert lote_ok(idade_valor=2, idade_unidade="semanas").validar()[0]
