import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from models import Ingrediente, ResultadoFormulacao, RequisicaoFormulacao
from services import formulation_service as fs
from tests.test_contracts import lote_ok


@pytest.fixture(autouse=True)
def limpa():
    fs.registrar_formulador(None)
    yield
    fs.registrar_formulador(None)


def req():
    return RequisicaoFormulacao(lote_ok(), [Ingrediente("U", "C", "Milho", 90, 1.0)])


def test_padrao_nao_conectado_nao_inventa_dieta():
    r = fs.executar_formulacao(req())
    assert r.status == "nao_conectado" and r.itens == [] and r.custo_vaca_dia is None
    assert not fs.formulador_conectado()


class Falso:
    def verificar_escopo(self, r):
        return False, "fora do escopo de teste"

    def formular(self, r):
        raise AssertionError("não deve ser chamado")


class Quebrado:
    def verificar_escopo(self, r):
        return True, ""

    def formular(self, r):
        raise RuntimeError("boom")


class StatusInvalido(Quebrado):
    def formular(self, r):
        return ResultadoFormulacao(status="otimo-ish")


def test_escopo_recusado_nao_chama_formulador():
    fs.registrar_formulador(Falso())
    assert fs.executar_formulacao(req()).status == "escopo_nao_suportado"


def test_excecao_e_status_invalido_viram_erro():
    fs.registrar_formulador(Quebrado())
    assert fs.executar_formulacao(req()).status == "erro"
    fs.registrar_formulador(StatusInvalido())
    assert fs.executar_formulacao(req()).status == "erro"


def test_formulador_via_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("MUUFEED_FORMULADOR", "tests.test_service_and_app:Falso")
    assert fs.executar_formulacao(req()).status == "escopo_nao_suportado"
    assert fs.formulador_conectado()


APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGINAS = ["Painel", "Lote", "Ingredientes e preços", "Formular dieta", "Resultados"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_todas_as_paginas_renderizam(pagina):
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = pagina
    at.run()
    assert not at.exception


def test_painel_mostra_nao_calculado_sem_formulacao():
    at = AppTest.from_file(APP, default_timeout=60).run()
    html = " ".join(m.value for m in at.markdown)
    assert "Não calculado" in html


def _clicar(at, rotulo):
    alvo = [b for b in at.button if b.label == rotulo]
    assert alvo, f"botão {rotulo!r} não encontrado"
    alvo[0].click().run()


def test_fluxo_completo_sem_formulador():
    from services.feed_catalog import CatalogoIngredientes
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = "Lote"
    at.run()
    _clicar(at, "Carregar lote de exemplo (valores ilustrativos)")
    _clicar(at, "Salvar lote")
    assert not at.exception and at.session_state["lote"] is not None
    assert at.session_state["lote"].idade_dias == pytest.approx(2.25 * 365.25)

    cat = CatalogoIngredientes()
    uid = cat.tabela.loc[cat.tabela["nome_original"] == "Corn silage, typical", "uid"].iloc[0]
    at.session_state["selecionados"] = {uid: {"preco": 0.30, "origem": "ilustrativo", "disponivel": True,
                                              "min_mn": None, "max_mn": None}}
    at.session_state["nav"] = "Formular dieta"
    at.run()
    _clicar(at, "FORMULAR DIETA")
    assert not at.exception
    assert at.session_state["resultado"].status == "nao_conectado"
    assert at.session_state["nav"] == "Resultados"


def test_botao_formular_desabilitado_sem_lote_e_ingredientes():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = "Formular dieta"
    at.run()
    assert [b for b in at.button if b.label == "FORMULAR DIETA"][0].disabled


def test_cenario_demonstrativo_e_identificado():
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["nav"] = "Resultados"
    at.run()
    _clicar(at, "Ver cenário demonstrativo (layout)")
    assert not at.exception
    assert at.session_state["resultado"].status == "demonstracao"
    assert "NÃO É UMA DIETA CALCULADA" in " ".join(m.value for m in at.markdown)


def _com_resultado(res, req=None):
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = "Resultados"
    at.session_state["resultado"] = res
    at.session_state["requisicao_resultado"] = req
    at.run()
    return at


def test_botao_pdf_habilitado_apenas_com_resultado_real():
    from tests.factories import resultado_teste, ingredientes_teste
    req = RequisicaoFormulacao(lote_ok(), ingredientes_teste())
    at = _com_resultado(resultado_teste("otimo"), req)
    assert not at.exception and len(at.get("download_button")) == 1
    for status in ("nao_conectado", "erro", "inviavel"):
        at = _com_resultado(resultado_teste(status))
        assert not at.exception and len(at.get("download_button")) == 0
        assert [b for b in at.button if b.label == "Exportar relatório PDF"][0].disabled
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = "Resultados"
    at.run()
    assert [b for b in at.button if b.label == "Exportar relatório PDF"][0].disabled


def test_servico_identifica_a_formulacao():
    r = fs.executar_formulacao(req())
    assert r.id_formulacao.startswith("MF-") and r.executada_em


def test_ui_candidata_experimental_exporta_e_mostra_preco_consumo_e_custos():
    from tests.factories import resultado_teste, ingredientes_teste
    req = RequisicaoFormulacao(lote_ok(n_vacas=40), ingredientes_teste())
    at = _com_resultado(resultado_teste("candidata_experimental"), req)
    assert not at.exception
    assert len(at.get("download_button")) == 1                       # exportação habilitada
    assert at.session_state["resultado"].status == "candidata_experimental"  # status preservado
    m = {x.label: x.value for x in at.metric}
    assert m["Consumo de MS (kg MS/vaca/dia)"] == "12,00"
    assert m["Custo por vaca/dia"] == "R$ 14,54"
    assert m["Custo do lote/dia"] == "R$ 581,41" and m["Custo mensal estimado (30 dias)"] == "R$ 17.442,42"
    df = at.dataframe[0].value
    assert "Preço (R$/kg MN)" in df.columns
    assert list(df["Preço (R$/kg MN)"].iloc[:2]) == [0.30, 2.45]
    assert df.iloc[-1]["Ingrediente"] == "Total" and df.iloc[-1]["kg MS/vaca/dia"] == pytest.approx(12.0)
    assert not [w for w in at.warning if "Inconsistência financeira" in w.value]


def test_ui_candidata_sem_dieta_real_nao_exporta():
    from dataclasses import replace
    from tests.factories import resultado_teste
    at = _com_resultado(replace(resultado_teste("candidata_experimental"), itens=[]))
    assert not at.exception and len(at.get("download_button")) == 0
    assert [b for b in at.button if b.label == "Exportar relatório PDF"][0].disabled


def test_ui_alerta_inconsistencia_financeira():
    from dataclasses import replace
    from tests.factories import resultado_teste, ingredientes_teste, CUSTO_VACA
    req = RequisicaoFormulacao(lote_ok(), ingredientes_teste())
    at = _com_resultado(replace(resultado_teste("candidata_experimental"), custo_vaca_dia=CUSTO_VACA + 5), req)
    assert any("Inconsistência financeira" in w.value for w in at.warning)


def test_campo_nome_outra_raca_aparece_imediatamente_so_no_modo_generico():
    """Regressão Streamlit: a seleção de raça deve ser reativa, sem clicar Salvar."""
    from services.breed import RACA_GENERICA

    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["nav"] = "Lote"
    at.run()
    assert not at.exception
    assert not [w for w in at.text_input if w.label == "Nome da outra raça (opcional)"]

    seletor = next(w for w in at.selectbox if w.label == "Raça")
    seletor.select(RACA_GENERICA).run()
    assert not at.exception
    assert len([w for w in at.text_input if w.label == "Nome da outra raça (opcional)"]) == 1

    seletor = next(w for w in at.selectbox if w.label == "Raça")
    seletor.select("Jersey").run()
    assert not at.exception
    assert not [w for w in at.text_input if w.label == "Nome da outra raça (opcional)"]
