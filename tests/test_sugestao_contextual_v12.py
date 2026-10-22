"""Regressões sem pacote NASEM: sugestões são curadoria, não dieta prescrita."""
from types import SimpleNamespace
import pandas as pd
from services.ingredient_suggestion import sugerir_ingredientes, CANDIDATOS_LACTACAO


def lote(leite, dias):
    return SimpleNamespace(estado="Lactating Cow", leite_kg_dia=leite,
                           dias_lactacao=dias, validar=lambda: ([], []))


def catalogo():
    nomes = [n for n, _, _ in CANDIDATOS_LACTACAO]
    nomes += ["Sorghum grain, dry, ground", "DDGS, high protein", "Soybean hulls",
              "Alfalfa meal", "Wheat bran", "Sunflower meal", "Cottonseed meal",
              "Sodium chloride (salt)"]
    return SimpleNamespace(tabela=pd.DataFrame([
        {"uid": str(i), "nome_original": nome, "nome_pt": nome, "ms_pct": 90.0}
        for i, nome in enumerate(nomes)]), precos_ilustrativos={"0": 0.30})


def test_lista_basica_preservada_por_compatibilidade():
    a, av = sugerir_ingredientes(lote(35, 60), catalogo())
    assert [v.nome_original for v in a] == [n for n, _, _ in CANDIDATOS_LACTACAO]
    assert not av


def test_opcoes_contextuais_mudam_com_lote_mas_sao_desmarcadas():
    a, _ = sugerir_ingredientes(lote(35, 60), catalogo(), ampliar_pelo_lote=True)
    b, _ = sugerir_ingredientes(lote(17, 260), catalogo(), ampliar_pelo_lote=True)
    assert len(a) == len(b) == 9
    assert [x.nome_original for x in a[:6]] == [x.nome_original for x in b[:6]]
    assert [x.nome_original for x in a[6:]] != [x.nome_original for x in b[6:]]
    assert all(x.opcional for x in a[6:] + b[6:])
    assert all(not x.opcional for x in a[:6] + b[:6])
    assert all(x.preco_ilustrativo is None for x in a[6:])


def test_sal_e_independente_da_lista_contextual():
    a, _ = sugerir_ingredientes(lote(25, 120), catalogo(), ampliar_pelo_lote=True,
                                incluir_fonte_sodio=True)
    assert a[-1].nome_original == "Sodium chloride (salt)"
    assert a[-1].opcional


def test_ui_declara_criacao_contextual_e_nao_altera_lote():
    from pathlib import Path
    ui = (Path(__file__).parents[1] / 'ui/pages.py').read_text()
    assert 'key="assistido_contextual"' in ui
    assert 'ampliar_pelo_lote=ampliar_pelo_lote' in ui
    assert 'and not sug.opcional' in ui
    assert 'É uma ENTRADA para calcular exigências' in ui
