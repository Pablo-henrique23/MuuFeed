import io
from dataclasses import replace
from datetime import date, datetime
import pytest
from pypdf import PdfReader
from services.formatting import brl, data_br, data_hora_br, num, pct
from services.pdf_report import TEXTO_EXPERIMENTAL, gerar_relatorio_pdf
from tests.factories import CUSTO_VACA, ingredientes_teste, resultado_teste
from tests.test_contracts import lote_ok

AGORA = datetime(2026, 10, 20, 21, 5)
EXP = "Candidata experimental - É necessária a revisão de um profissional"


def paginas(pdf: bytes) -> list[str]:
    return [" ".join(p.extract_text().split()) for p in PdfReader(io.BytesIO(pdf)).pages]


def texto(pdf: bytes) -> str:
    return " ".join(paginas(pdf))


def test_formatacao_brasileira():
    assert brl(1234.5) == "R$ 1.234,50" and brl(None) == "—"
    assert num(0.5, 1) == "0,5" and num(1234567.891, 2) == "1.234.567,89" and num(10, 1, "kg") == "10,0 kg"
    assert pct(12.34) == "12,3 %"
    assert data_br(date(2026, 10, 5)) == "05/10/2026" and data_br(None) == "não informada"
    assert data_hora_br("2026-10-20T20:15:00-03:00") == "20/10/2026 20:15"


def test_pdf_otimo_valido_com_todas_as_secoes():
    pdf = gerar_relatorio_pdf(resultado_teste(), lote_ok(), ingredientes_teste(), date(2026, 10, 20), AGORA)
    assert pdf[:5] == b"%PDF-" and len(pdf) > 4000
    t = texto(pdf)
    for trecho in ["MuuFeed", "MF-TESTE-123", "1. Identificação", "2. Dados do lote", "3. Dieta formulada",
                   "4. Consumo, custos estimados", "5. Ingestão", "6. Restrições", "7. Regras acionadas", "8. Fontes e limitações"]:
        assert trecho in t, trecho
    assert "20/10/2026 21:05" in t
    assert "Silagem de milho" in t and "Holandesa" in t and "Atendidas" in t and "Violadas" in t and "Não avaliadas" in t
    assert "Regra de teste" in t and "Amido máximo" in t and "Aviso de teste" in t
    assert "Preço ilustrativo" in t and "20/10/2026" in t
    assert "Esta formulação não substitui a avaliação" in t
    assert EXP not in t                                   # só a candidata leva o aviso experimental


def test_candidata_experimental_exporta_e_nao_vira_otimo():
    res = resultado_teste("candidata_experimental")
    pdf = gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste(), date(2026, 10, 20), AGORA)
    assert res.status == "candidata_experimental"        # o gerador não converte o status
    pgs = paginas(pdf)
    assert pdf[:5] == b"%PDF-"
    assert all(EXP not in p for p in pgs), "a faixa antiga deve desaparecer"
    t = " ".join(pgs)
    assert "Candidata experimental Resultado experimental:" not in pgs[0]
    assert "Requisitos sem limites verificados:" not in pgs[0]
    assert "Dieta candidata experimental" in t and "3. Dieta candidata experimental" in t
    assert "3. Dieta formulada" not in t
    assert "Dieta candidata experimental" in t and "não declara esta dieta como nutricionalmente completa" not in t


def test_pdf_traz_preco_unitario_consumo_e_custos_consistentes():
    t = texto(gerar_relatorio_pdf(resultado_teste("candidata_experimental"), lote_ok(n_vacas=40), ingredientes_teste(),
                                  date(2026, 10, 20), AGORA))
    assert "Preço (R$/kg MN)" in t and "R$ 0,30 *" in t and "R$ 2,45" in t
    assert "Consumo de MS (kg MS/vaca/dia)" in t and "12,00" in t
    assert "R$ 14,54" in t                                # por vaca/dia (9,0909 + 5,4444)
    assert "R$ 581,41" in t and "R$ 17.442,42" in t       # lote/dia e mês (30 dias)
    assert "R$ 9,09" in t and "R$ 5,44" in t              # custos individuais
    assert "inconsistência financeira" not in t.lower()


def test_pdf_sinaliza_inconsistencia_financeira():
    ruim = replace(resultado_teste("candidata_experimental"), custo_vaca_dia=CUSTO_VACA + 5)
    t = texto(gerar_relatorio_pdf(ruim, lote_ok(), ingredientes_teste(), None, AGORA))
    assert "inconsistência financeira" in t.lower()


def test_custos_de_lote_nao_se_aplicam_sem_lote():
    t = texto(gerar_relatorio_pdf(resultado_teste(), None, None, None, AGORA))
    assert "Dados do lote não disponíveis" in t and "Não se aplica" in t
    assert "Origem e data dos preços não disponíveis" in t
    assert "Não disponível" in t                          # indicador sem valor exigido


def test_dados_ausentes_sao_declarados_sem_inventar():
    t = texto(gerar_relatorio_pdf(resultado_teste(regras=False), None, None, None, AGORA))
    assert "Nenhuma regra acionada foi informada" in t


@pytest.mark.parametrize("status", ["nao_conectado", "erro", "inviavel", "escopo_nao_suportado"])
def test_recusa_exportar_sem_resultado_real(status):
    with pytest.raises(ValueError):
        gerar_relatorio_pdf(resultado_teste(status=status), lote_ok(), None, None, AGORA)


@pytest.mark.parametrize("status", ["otimo", "candidata_experimental"])
def test_recusa_exportar_sem_dieta_retornada(status):
    with pytest.raises(ValueError, match="não retornou uma dieta"):
        gerar_relatorio_pdf(replace(resultado_teste(status), itens=[]), lote_ok(), None, None, AGORA)


def test_cenario_demonstrativo_e_marcado():
    t = texto(gerar_relatorio_pdf(resultado_teste(status="demonstracao"), lote_ok(), ingredientes_teste(), None, AGORA))
    assert "NÃO é uma dieta formulada" in t and "Não se aplica" in t and "Cenário demonstrativo" in t
    assert EXP not in t


def _res_formato_do_motor():
    """Mesmo formato que o NasemFormulador devolve (ids técnicos + lista duplicada de não avaliados)."""
    from models import Restricao
    chk, nao = ["total_ms", "me", "mp", "limites_operacionais"], ["fdn", "fibra_fisicamente_efetiva", "amido", "minerais",
                                                                  "vitaminas", "limites_nutricionais_de_inclusao"]
    return replace(resultado_teste("candidata_experimental"),
                   restricoes=[Restricao(k, k.upper(), "atendida") for k in chk] + [Restricao(k, k.upper(), "nao_avaliada") for k in nao],
                   nao_avaliadas=nao)


def test_pdf_usa_nomes_legiveis_e_nao_repete_nao_avaliadas():
    t = texto(gerar_relatorio_pdf(_res_formato_do_motor(), lote_ok(), ingredientes_teste(), None, AGORA))
    for tecnico in ["fibra_fisicamente_efetiva", "FIBRA_FISICAMENTE_EFETIVA", "total_ms", "TOTAL_MS",
                    "limites_operacionais", "LIMITES_NUTRICIONAIS_DE_INCLUSAO", "limites_nutricionais_de_inclusao"]:
        assert tecnico not in t, tecnico
    for legivel in ["Fibra fisicamente efetiva", "Fibra em detergente neutro (FDN)", "Consumo total de matéria seca (MS)",
                    "Energia metabolizável (ME)", "Limites nutricionais de inclusão de ingredientes", "Vitaminas", "Minerais"]:
        assert legivel in t, legivel
    # cada requisito não avaliado aparece uma única vez na seção 6 (sem lista duplicada)
    secao6 = t[t.index("6. Restrições"):t.index("7. Regras acionadas")]
    for req in ["Fibra fisicamente efetiva", "Fibra em detergente neutro (FDN)", "Amido", "Minerais", "Vitaminas",
                "Limites nutricionais de inclusão de ingredientes"]:
        assert secao6.count(req) == 1, (req, secao6.count(req))
    assert "Requisitos não avaliados pelo sistema" not in t
    assert secao6.count("Não avaliadas") == 1


def test_ids_de_restricao_tipo_codigo_continuam_visiveis():
    t = texto(gerar_relatorio_pdf(resultado_teste(), lote_ok(), ingredientes_teste(), None, AGORA))
    assert "C1" in t and "C2" in t and "Restrição atendida" in t


def test_fontes_nao_se_repetem():
    res = replace(resultado_teste(), modelo_referencia="Modelo X",
                  regras=[__import__("models").RegraAcionada("R-1", "a", "Modelo X"), __import__("models").RegraAcionada("R-2", "b", "Modelo X")])
    t = texto(gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste(), None, AGORA))
    assert t[t.index("8. Fontes e limitações"):].count("Modelo X") == 1


def test_aviso_experimental_reflete_limites_nutricionais_ativados():
    from models import Restricao, RegraAcionada
    res = replace(resultado_teste("candidata_experimental"),
        restricoes=[Restricao(k, k.upper(), "atendida") for k in ("total_ms", "me", "mp", "fdn", "amido")] +
                   [Restricao(k, k.upper(), "nao_avaliada") for k in ("fibra_fisicamente_efetiva", "minerais", "vitaminas")],
        nao_avaliadas=["fibra_fisicamente_efetiva", "minerais", "vitaminas"],
        regras=[RegraAcionada("R_AMIDO_MAX", "Amido abaixo do teto", "Limite informado pelo usuário")],
    )
    pdf = gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste(), None, AGORA)
    t = texto(pdf)
    cabecalho = t[:t.index("1. Identificação")]
    assert "Fibra, amido, minerais, vitaminas e limites de inclusão não foram avaliados" not in t
    assert "Requisitos sem limites verificados:" not in cabecalho
    assert "Fibra fisicamente efetiva" not in cabecalho and "Minerais" not in cabecalho
    assert "Resultado experimental: atende somente às restrições efetivamente verificadas." not in cabecalho
    assert "R_AMIDO_MAX" in t
    assert all(TEXTO_EXPERIMENTAL not in pagina for pagina in paginas(pdf))

def test_aviso_sem_limites_exibe_pendencias_apenas_na_secao_de_restricoes():
    res = _res_formato_do_motor()
    pdf = gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste(), None, AGORA)
    completo = texto(pdf)
    cabecalho = completo.split("1. Identificação")[0]
    secao_restricoes = completo[completo.index("6. Restrições"):completo.index("7. Regras acionadas")]
    assert "Fibra em detergente neutro (FDN)" not in cabecalho
    assert "Amido" not in cabecalho
    assert "Requisitos sem limites verificados:" not in cabecalho
    assert "Fibra em detergente neutro (FDN)" in secao_restricoes
    assert "Amido" in secao_restricoes
