"""Relatório PDF do MuuFeed (ReportLab, 100% offline).

Independe do Streamlit e NÃO recalcula a dieta: apresenta apenas os dados estruturados do
`ResultadoFormulacao` (mais lote e ingredientes da requisição, para contexto e preços).
Dados ausentes são declarados como ausentes; nada é inventado.
"""
from __future__ import annotations

import io
from datetime import date, datetime
from typing import Optional, Sequence
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle

from models import ESTADOS, PADROES_AVANCADOS, ROTULOS, Ingrediente, Lote, ResultadoFormulacao
from services.formatting import brl, data_br, data_hora_br, num

VERDE, VERDE_ESC = colors.HexColor("#1F6B4F"), colors.HexColor("#17503B")
TINTA, CINZA, LINHA = colors.HexColor("#14211B"), colors.HexColor("#51625A"), colors.HexColor("#D5E0D8")
ZEBRA, VERMELHO, AMBAR = colors.HexColor("#F1F6F2"), colors.HexColor("#B42318"), colors.HexColor("#FBF1DC")
EXPORTAVEIS = {"otimo": "Dieta formulada", "demonstracao": "Cenário demonstrativo"}
DIAS_MES = 30  # convenção do MuuFeed para o custo mensal
SITUACAO = {"atende": "Atende", "viola": "Não atende", "nao_avaliado": "Não avaliado",
            "informativo": "Informativo (sem veredito)"}


def _estilos() -> dict[str, ParagraphStyle]:
    b = ParagraphStyle("b", fontName="Helvetica", fontSize=9, leading=12.5, textColor=TINTA)
    return {
        "b": b, "peq": ParagraphStyle("peq", parent=b, fontSize=7.5, leading=10, textColor=CINZA),
        "h1": ParagraphStyle("h1", parent=b, fontName="Helvetica-Bold", fontSize=19, leading=23, spaceAfter=2),
        "h2": ParagraphStyle("h2", parent=b, fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=VERDE,
                             spaceBefore=13, spaceAfter=5, keepWithNext=1),
        "c": ParagraphStyle("c", parent=b, fontSize=8.5, leading=11),
        "cd": ParagraphStyle("cd", parent=b, fontSize=8.5, leading=11, alignment=TA_RIGHT),
        "h": ParagraphStyle("h", parent=b, fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white),
        "hd": ParagraphStyle("hd", parent=b, fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white,
                             alignment=TA_RIGHT),
        "lbl": ParagraphStyle("lbl", parent=b, fontSize=7.5, leading=10, textColor=CINZA),
        "big": ParagraphStyle("big", parent=b, fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=VERDE_ESC),
        "aviso": ParagraphStyle("aviso", parent=b, fontSize=8.5, leading=11.5, textColor=colors.HexColor("#7A4B00")),
        "demo": ParagraphStyle("demo", parent=b, fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=VERMELHO),
    }


def _p(txt, estilo) -> Paragraph:
    return Paragraph(escape(str(txt)), estilo)


def _tabela(S, cab, linhas, larguras_mm, direita=(), total=False) -> Table:
    dados = [[_p(c, S["hd"] if i in direita else S["h"]) for i, c in enumerate(cab)]]
    for n, l in enumerate(linhas):
        ult = total and n == len(linhas) - 1
        dados.append([Paragraph(("<b>%s</b>" if ult else "%s") % escape(str(c)), S["cd"] if i in direita else S["c"])
                      for i, c in enumerate(l)])
    t = Table(dados, colWidths=[w * mm for w in larguras_mm], repeatRows=1)
    est = [("BACKGROUND", (0, 0), (-1, 0), VERDE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
           ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINHA), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
           ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if total:
        est.append(("LINEABOVE", (0, -1), (-1, -1), 0.8, VERDE))
    t.setStyle(TableStyle(est))
    return t


def _pares(S, pares, larg=(30, 57, 30, 57)) -> Table:
    linhas = []
    for i in range(0, len(pares), 2):
        a = pares[i]
        b = pares[i + 1] if i + 1 < len(pares) else ("", "")
        linhas.append([_p(a[0], S["lbl"]), _p(a[1], S["c"]), _p(b[0], S["lbl"]), _p(b[1], S["c"])])
    t = Table(linhas, colWidths=[w * mm for w in larg])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, LINHA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    return t


def _metricas(S, itens) -> Table:
    cel = [[_p(r, S["lbl"]), _p(v, S["big"])] for r, v in itens]
    t = Table([[c[0] for c in cel], [c[1] for c in cel]], colWidths=[58 * mm] * len(itens))
    t.setStyle(TableStyle([("BOX", (0, 0), (0, -1), 0.6, LINHA), ("BOX", (1, 0), (1, -1), 0.6, LINHA),
                           ("BOX", (2, 0), (2, -1), 0.6, LINHA), ("BACKGROUND", (0, 0), (-1, -1), ZEBRA),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, 0), 7),
                           ("BOTTOMPADDING", (0, 1), (-1, 1), 8)]))
    return t


def _lista(S, textos) -> list:
    return [Paragraph("&bull; " + escape(str(t)), ParagraphStyle("li", parent=S["b"], leftIndent=10, firstLineIndent=-8))
            for t in textos]


def _moldura(c, doc, res, demo, agora) -> None:
    larg, alt = A4
    c.saveState()
    c.setFillColor(VERDE)
    c.rect(0, alt - 26 * mm, larg, 26 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(18 * mm, alt - 14 * mm, "MuuFeed")
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, alt - 20 * mm, "Relatório de formulação de dieta para bovinos leiteiros")
    c.setFont("Helvetica", 8)
    c.drawRightString(larg - 18 * mm, alt - 12 * mm, "Gerado em " + data_hora_br(agora))
    c.drawRightString(larg - 18 * mm, alt - 17 * mm, "Formulação: " + (res.id_formulacao or "não identificada"))
    c.setStrokeColor(LINHA)
    c.line(18 * mm, 14 * mm, larg - 18 * mm, 14 * mm)
    c.setFillColor(CINZA)
    c.setFont("Helvetica", 7)
    c.drawString(18 * mm, 10 * mm, "Documento de apoio à decisão; não substitui a avaliação de médico-veterinário ou zootecnista.")
    c.drawRightString(larg - 18 * mm, 10 * mm, f"Página {doc.page}")
    if demo:
        c.translate(larg / 2, alt / 2)
        c.rotate(45)
        c.setFillColor(VERMELHO)
        c.setFillAlpha(0.13)
        c.setFont("Helvetica-Bold", 38)
        c.drawCentredString(0, 10, "EXEMPLO DE LAYOUT")
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(0, -28, "NÃO É DIETA FORMULADA")
    c.restoreState()


def gerar_relatorio_pdf(resultado: ResultadoFormulacao, lote: Optional[Lote] = None,
                        ingredientes: Optional[Sequence[Ingrediente]] = None,
                        data_ref_precos: Optional[date | str] = None,
                        agora: Optional[datetime] = None) -> bytes:
    """Gera o PDF. Aceita apenas resultado real (`otimo`) ou o cenário `demonstracao` (com marca d'água)."""
    if resultado.status not in EXPORTAVEIS:
        raise ValueError("Só é possível exportar uma dieta formulada (status 'otimo') ou o cenário demonstrativo.")
    demo = resultado.status == "demonstracao"
    agora = agora or datetime.now()
    S = _estilos()
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=33 * mm,
                          bottomMargin=20 * mm, title="Relatório MuuFeed", author="MuuFeed")
    doc.addPageTemplates([PageTemplate("p", [Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")],
                                       onPage=lambda c, d: _moldura(c, d, resultado, demo, agora))])
    por_uid = {i.uid: i for i in (ingredientes or [])}
    n = lote.n_vacas if (lote and not demo) else None
    st_ = [_p(EXPORTAVEIS[resultado.status], S["h1"])]
    if demo:
        st_ += [Table([[_p("EXEMPLO DE LAYOUT. Este documento NÃO é uma dieta formulada pelo MuuFeed e não corresponde "
                           "a nenhum lote. " + resultado.mensagem, S["demo"])]], colWidths=[doc.width],
                      style=[("BOX", (0, 0), (-1, -1), 1, VERMELHO), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEA")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])]
    elif resultado.mensagem:
        st_.append(_p(resultado.mensagem, S["b"]))

    # 1. Identificação
    st_ += [_p("1. Identificação", S["h2"]), _pares(S, [
        ("Formulação", resultado.id_formulacao or "Não identificada"),
        ("Executada em", data_hora_br(resultado.executada_em) if resultado.executada_em else "Não informada"),
        ("Relatório gerado em", data_hora_br(agora)), ("Modelo de referência", resultado.modelo_referencia or "Não informado")])]

    # 2. Lote
    st_.append(_p("2. Dados do lote", S["h2"]))
    if demo:
        st_.append(_p("Não se aplica: o cenário demonstrativo não corresponde a nenhum lote.", S["b"]))
    elif lote is None:
        st_.append(_p("Dados do lote não disponíveis neste resultado.", S["b"]))
    else:
        pares = [("Lote", lote.nome), ("Número de animais", num(lote.n_vacas, 0)),
                 ("Raça", lote.raca or "Não informada"), ("Estado fisiológico", ESTADOS.get(lote.estado, lote.estado)),
                 ("Idade média", f"{num(lote.idade_valor, 2)} {lote.idade_unidade} ({num(lote.idade_dias, 0)} dias)"),
                 ("Peso médio", num(lote.peso_kg, 1, "kg")), ("Ordem de lactação", f"{lote.ordem_lactacao}ª"),
                 ("Dias em lactação", num(lote.dias_lactacao, 0, "dias")),
                 ("Produção de leite", num(lote.leite_kg_dia, 1, "kg/vaca/dia")), ("Gordura do leite", num(lote.gordura_pct, 2, "%")),
                 ("Proteína do leite", num(lote.proteina_pct, 2, "%"))]
        st_.append(_pares(S, pares))
        padrao = lote.campos_padrao
        if padrao:
            fmt = {"bcs": lote.bcs, "lactose_pct": lote.lactose_pct, "peso_maduro_kg": lote.peso_maduro_kg,
                   "dias_gestacao": lote.dias_gestacao}
            st_ += [Spacer(1, 4), _p("Hipóteses padrão (valores não medidos): " + "; ".join(
                f"{ROTULOS[k].lower()} = {num(fmt[k], 2)}" for k in padrao) + ".", S["peq"])]

    # 3. Dieta
    st_.append(_p("3. Dieta formulada (por vaca/dia)", S["h2"]))
    tot_ms, tot_mn = sum(i.kg_ms for i in resultado.itens), sum(i.kg_mn for i in resultado.itens)
    linhas, ilustr = [], False
    for i in resultado.itens:
        ing = por_uid.get(i.uid)
        preco = "—"
        if ing and ing.preco_mn_brl_kg is not None:
            ilu = ing.origem_preco == "ilustrativo"
            ilustr = ilustr or ilu
            preco = brl(ing.preco_mn_brl_kg) + (" *" if ilu else "")
        linhas.append([i.nome, num(i.kg_ms, 2), num(i.kg_mn, 2), num(i.kg_ms / tot_ms * 100, 1, "%") if tot_ms else "—",
                       preco, brl(i.custo_brl)])
    linhas.append(["Total", num(tot_ms, 2), num(tot_mn, 2), "100,0 %" if tot_ms else "—", "", brl(resultado.custo_vaca_dia)])
    st_.append(_tabela(S, ["Ingrediente", "MS (kg)", "MN (kg)", "% da MS", "Preço (R$/kg MN)", "Custo (R$)"],
                       linhas, [58, 20, 20, 20, 30, 26], direita=(1, 2, 3, 4, 5), total=True))
    notas = ["MS = matéria seca; MN = matéria natural (como fornecida). Proporções calculadas sobre a MS total."]
    if ilustr or demo:
        notas.append("* Preço ilustrativo, não é preço de mercado confirmado.")
    if any(i.custo_brl is None for i in resultado.itens):
        notas.append("Custo individual não informado para ao menos um ingrediente.")
    st_ += [Spacer(1, 3)] + [_p(t, S["peq"]) for t in notas]

    # 4. Custos
    st_.append(_p("4. Custos estimados e hipóteses", S["h2"]))
    c = resultado.custo_vaca_dia
    st_.append(_metricas(S, [("Por vaca/dia", brl(c)), ("Por lote/dia", brl(c * n) if (c is not None and n) else "Não se aplica"),
                             ("Por mês (30 dias)", brl(c * n * DIAS_MES) if (c is not None and n) else "Não se aplica")]))
    hip = []
    if n:
        hip += [f"Todas as {num(n, 0)} vacas do lote recebem a mesma dieta, na mesma quantidade por vaca.",
                f"Mês de {DIAS_MES} dias (convenção do MuuFeed)."]
    if ingredientes:
        o = [x.origem_preco for x in ingredientes if x.uid in {i.uid for i in resultado.itens}]
        hip.append(f"Origem dos preços: {o.count('ilustrativo')} ilustrativo(s), {o.count('informado')} informado(s)"
                   f"{', ' + str(len(o) - o.count('ilustrativo') - o.count('informado')) + ' sem origem' if len(o) > o.count('ilustrativo') + o.count('informado') else ''}.")
        hip.append("Data de referência dos preços: " + data_br(data_ref_precos) + ".")
    else:
        hip.append("Preços por ingrediente não disponíveis neste relatório; só o custo informado pelo formulador é exibido.")
    st_ += [Spacer(1, 5)] + _lista(S, hip)

    # 5. Ingestão x exigências
    st_.append(_p("5. Ingestão × exigências nutricionais", S["h2"]))
    if resultado.indicadores:
        lin = []
        for i in resultado.indicadores:
            ok = i.ingerido is not None and i.exigido
            lin.append([i.rotulo, i.unidade, num(i.ingerido, 2) if i.ingerido is not None else "Não disponível",
                        num(i.exigido, 2) if i.exigido is not None else "Não disponível",
                        num(i.ingerido / i.exigido * 100, 1, "%") if ok else "—", SITUACAO.get(i.status, i.status)])
        st_.append(_tabela(S, ["Indicador", "Unidade", "Ingerido", "Exigido", "Ingerido ÷ exigido", "Situação"], lin,
                           [42, 20, 24, 24, 30, 34], direita=(2, 3, 4)))
        st_.append(_p("Somente indicadores efetivamente calculados pelo formulador são exibidos. 'Informativo' não é veredito de adequação.", S["peq"]))
    else:
        st_.append(_p("O formulador não informou indicadores de ingestão e exigência.", S["b"]))

    # 6. Restrições
    st_.append(_p("6. Restrições", S["h2"]))
    tem = False
    for rot, chave in (("Atendidas", "atendida"), ("Violadas", "violada"), ("Não avaliadas", "nao_avaliada")):
        its = [r for r in resultado.restricoes if r.status == chave]
        if its:
            tem = True
            st_.append(KeepTogether([_p(rot, ParagraphStyle("sub", parent=S["b"], fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=3)),
                                     _tabela(S, ["ID", "Restrição", "Detalhe"], [[r.id, r.descricao, r.detalhe or "—"] for r in its], [22, 90, 62])]))
    if resultado.nao_avaliadas:
        tem = True
        st_ += [_p("Requisitos não avaliados pelo sistema", ParagraphStyle("sub2", parent=S["b"], fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=3))]
        st_ += _lista(S, resultado.nao_avaliadas)
    if not tem:
        st_.append(_p("O formulador não informou restrições verificadas nem requisitos não avaliados.", S["b"]))

    # 7. Regras
    st_.append(_p("7. Regras acionadas pelo motor de inferência", S["h2"]))
    if resultado.regras:
        st_.append(_tabela(S, ["Regra", "Explicação", "Fonte"], [[r.id, r.descricao, r.fonte or "Não informada"] for r in resultado.regras], [24, 88, 62]))
    else:
        st_.append(_p("Nenhuma regra acionada foi informada pelo formulador.", S["b"]))

    # 8. Fontes e limitações
    st_.append(_p("8. Fontes e limitações", S["h2"]))
    fontes = [resultado.modelo_referencia or "Modelo de referência não informado pelo formulador.",
              "Composição dos ingredientes: biblioteca de alimentos NASEM (NASEM_feed_library.csv, distribuída com o pacote Python nasem_dairy), sem alteração de valores."]
    fontes += sorted({r.fonte for r in resultado.regras if r.fonte})
    lim = ["O MuuFeed não declara esta dieta como nutricionalmente completa: só foram verificados os itens listados como atendidos ou violados.",
           "A composição dos alimentos é a de referência da biblioteca; alimentos reais variam, e recomenda-se análise bromatológica.",
           "Exigências e ingestão referem-se a um animal médio do lote; variações individuais não são consideradas.",
           "Preços marcados como ilustrativos não são preços de mercado confirmados."] + list(resultado.avisos)
    st_ += [_p("Fontes", ParagraphStyle("f", parent=S["b"], fontName="Helvetica-Bold", spaceAfter=3))] + _lista(S, fontes)
    st_ += [Spacer(1, 6), _p("Limitações", ParagraphStyle("l", parent=S["b"], fontName="Helvetica-Bold", spaceAfter=3))] + _lista(S, lim)
    doc.build(st_)
    return buf.getvalue()
