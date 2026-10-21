"""Ponta a ponta com o motor NASEM REAL (≈6 s): adaptador -> resumo financeiro -> PDF.
Não altera o algoritmo nutricional; apenas confere o que ele devolve."""
import io
import pytest
from pypdf import PdfReader
from models import OpcoesFormulacao, RequisicaoFormulacao
from services.feed_catalog import CatalogoIngredientes
from services.financeiro import resumo_financeiro
from services.nasem_adapter import NasemFormulador
from services.pdf_report import gerar_relatorio_pdf
from models import Ingrediente
from tests.test_contracts import lote_ok

CONSUMO_MS = 22.0


@pytest.fixture(scope="module")
def req():
    cat = CatalogoIngredientes()

    def ing(nome, preco):
        r = cat.tabela[cat.tabela.nome_original == nome].iloc[0]
        return Ingrediente(r.uid, r.nome_original, r.nome_pt, float(r.ms_pct), preco, "ilustrativo")

    ings = [ing("Corn silage, typical", 0.30), ing("Soybean meal, solvent 48CP", 2.45),
            ing("Corn grain dry, medium grind", 1.15), ing("Alfalfa meal", 2.20)]
    return RequisicaoFormulacao(lote_ok(n_vacas=50), ings, OpcoesFormulacao(consumo_ms_kg_dia=CONSUMO_MS))


@pytest.fixture(scope="module")
def res(req):
    f = NasemFormulador()
    assert f.verificar_escopo(req) == (True, "")
    return f.formular(req)


def test_adaptador_devolve_candidata_experimental_com_preco_unitario(res, req):
    assert res.status == "candidata_experimental"                  # nunca vira "otimo"
    preco_req = {i.uid: i.preco_mn_brl_kg for i in req.ingredientes}
    assert res.itens and all(i.preco_mn_brl_kg == pytest.approx(preco_req[i.uid]) for i in res.itens)


def test_financas_consistentes_com_motor_real(res, req):
    r = resumo_financeiro(res, req.lote.n_vacas, req.ingredientes)
    assert r.inconsistencias == ()
    assert r.consumo_ms_kg == pytest.approx(CONSUMO_MS, abs=1e-3)
    assert sum(l.custo_brl for l in r.linhas) == pytest.approx(res.custo_vaca_dia, abs=1e-6)
    assert r.custo_lote_dia == pytest.approx(res.custo_vaca_dia * 50, rel=1e-12)
    assert r.custo_mes == pytest.approx(res.custo_vaca_dia * 50 * 30, rel=1e-12)
    for l in r.linhas:                                             # recálculo independente: kg MN x preço
        assert l.custo_brl == pytest.approx(l.kg_mn * l.preco_mn_brl_kg, rel=1e-9, abs=1e-9)


def test_pdf_da_candidata_real(res, req):
    pdf = gerar_relatorio_pdf(res, req.lote, req.ingredientes, None)
    pgs = [" ".join(p.extract_text().split()) for p in PdfReader(io.BytesIO(pdf)).pages]
    assert all("CANDIDATA EXPERIMENTAL — NÃO É DIETA NUTRICIONALMENTE VALIDADA" in p for p in pgs)
    assert res.status == "candidata_experimental"


def test_pdf_real_sem_identificadores_tecnicos_nem_duplicacao(res, req):
    import re
    t = " ".join(" ".join(p.extract_text().split()) for p in PdfReader(io.BytesIO(gerar_relatorio_pdf(res, req.lote, req.ingredientes, None))).pages)
    permitidos = {"nasem_dairy", "NASEM_feed_library.csv", "R_ME", "R_MP"}  # pacote, arquivo e ids de regra (rastreabilidade)
    achados = {m for m in re.findall(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9.]+)+\b", t)} - permitidos
    assert not achados, achados
    secao6 = t[t.index("6. Restrições"):t.index("7. Regras acionadas")]
    assert secao6.count("Fibra fisicamente efetiva") == 1 and secao6.count("Amido") == 1
