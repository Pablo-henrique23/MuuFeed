import io
from datetime import date, datetime
import pytest
from pypdf import PdfReader
from services.formatting import brl, data_br, data_hora_br, num, pct
from services.pdf_report import gerar_relatorio_pdf
from tests.factories import ingredientes_teste, resultado_teste
from tests.test_contracts import lote_ok

AGORA = datetime(2026, 10, 20, 21, 5)


def texto(pdf: bytes) -> str:
    r = PdfReader(io.BytesIO(pdf))
    return " ".join(p.extract_text() for p in r.pages)


def test_formatacao_brasileira():
    assert brl(1234.5) == "R$ 1.234,50" and brl(None) == "—"
    assert num(0.5, 1) == "0,5" and num(1234567.891, 2) == "1.234.567,89" and num(10, 1, "kg") == "10,0 kg"
    assert pct(12.34) == "12,3 %"
    assert data_br(date(2026, 10, 5)) == "05/10/2026" and data_br(None) == "não informada"
    assert data_hora_br("2026-10-20T20:15:00-03:00") == "20/10/2026 20:15"


def test_pdf_valido_com_todas_as_secoes():
    pdf = gerar_relatorio_pdf(resultado_teste(), lote_ok(), ingredientes_teste(), date(2026, 10, 20), AGORA)
    assert pdf[:5] == b"%PDF-" and len(pdf) > 4000
    t = texto(pdf)
    for trecho in ["MuuFeed", "MF-TESTE-123", "1. Identificação", "2. Dados do lote", "3. Dieta formulada",
                   "4. Custos estimados", "5. Ingestão", "6. Restrições", "7. Regras acionadas", "8. Fontes e limitações"]:
        assert trecho in t, trecho
    assert "20/10/2026 21:05" in t                       # data de geração no formato brasileiro
    assert "R$ 12,34" in t and "R$ 493,60" in t.replace("\n", " ")
    assert "Silagem de milho" in t and "Holandesa" in t and "Atendidas" in t and "Violadas" in t and "Não avaliadas" in t
    assert "Regra de teste" in t and "Amido máximo" in t and "Aviso de teste" in t
    assert "Preço ilustrativo" in t and "20/10/2026" in t
    assert "não declara esta dieta como nutricionalmente completa" in t.replace("\n", " ")


def test_custos_de_lote_e_mes_usam_os_dados_do_resultado():
    t = texto(gerar_relatorio_pdf(resultado_teste(), lote_ok(n_vacas=40), ingredientes_teste(), None, AGORA)).replace("\n", " ")
    assert "R$ 493,60" in t          # 12,34 x 40
    assert "R$ 14.808,00" in t       # x 30 dias
    assert "não informada" in t       # data de referência dos preços ausente


def test_dados_ausentes_sao_declarados_sem_inventar():
    t = texto(gerar_relatorio_pdf(resultado_teste(regras=False), None, None, None, AGORA)).replace("\n", " ")
    assert "Dados do lote não disponíveis" in t
    assert "Nenhuma regra acionada foi informada" in t
    assert "Preços por ingrediente não disponíveis" in t
    assert "Não disponível" in t      # indicador sem valor exigido


@pytest.mark.parametrize("status", ["nao_conectado", "erro", "inviavel", "escopo_nao_suportado"])
def test_recusa_exportar_sem_resultado_real(status):
    with pytest.raises(ValueError):
        gerar_relatorio_pdf(resultado_teste(status=status), lote_ok(), None, None, AGORA)


def test_cenario_demonstrativo_e_marcado():
    t = texto(gerar_relatorio_pdf(resultado_teste(status="demonstracao"), lote_ok(), ingredientes_teste(), None, AGORA)).replace("\n", " ")
    assert "NÃO é uma dieta formulada" in t
    assert "Não se aplica" in t and "Cenário demonstrativo" in t
