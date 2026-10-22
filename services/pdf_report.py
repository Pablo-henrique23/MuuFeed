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
from services.financeiro import DIAS_MES, resumo_financeiro
from services.formatting import brl, data_br, data_hora_br, num
from services.rotulos import eh_chave_tecnica, nao_avaliadas_unicas, rotulo_legivel

VERDE, VERDE_ESC = colors.HexColor("#1F6B4F"), colors.HexColor("#17503B")
TINTA, CINZA, LINHA = colors.HexColor("#14211B"), colors.HexColor("#51625A"), colors.HexColor("#D5E0D8")
ZEBRA, VERMELHO, AMBAR = colors.HexColor("#F1F6F2"), colors.HexColor("#B42318"), colors.HexColor("#FBF1DC")
AVISO_PROFISSIONAL = "Esta formulação não substitui a avaliação de médico-veterinário ou zootecnista."
EXPORTAVEIS = {"otimo": "Dieta formulada", "candidata_experimental": "Dieta candidata experimental",
               "demonstracao": "Cenário demonstrativo"}
TEXTO_EXPERIMENTAL = "CANDIDATA EXPERIMENTAL — NÃO É DIETA NUTRICIONALMENTE VALIDADA"
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
        "big": ParagraphStyle("big", parent=b, fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=VERDE_ESC),
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


def _metricas(S, itens, largura_mm=174) -> Table:
    k = len(itens)
    t = Table([[_p(r, S["lbl"]) for r, _ in itens], [_p(v, S["big"]) for _, v in itens]],
              colWidths=[largura_mm / k * mm] * k)
    est = [("BACKGROUND", (0, 0), (-1, -1), ZEBRA), ("LEFTPADDING", (0, 0), (-1, -1), 7),
           ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, 1), (-1, 1), 8)]
    est += [("BOX", (j, 0), (j, -1), 0.6, LINHA) for j in range(k)]
    t.setStyle(TableStyle(est))
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
    if res.status == "candidata_experimental":
        c.setFillColor(VERMELHO)
        c.rect(0, alt - 32 * mm, larg, 6 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(larg / 2, alt - 30 * mm, TEXTO_EXPERIMENTAL)
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
        raise ValueError("Só é possível exportar dieta formulada (otimo), candidata experimental ou o cenário demonstrativo.")
    if not resultado.itens:
        raise ValueError("O formulador não retornou uma dieta: não há o que exportar.")
    demo = resultado.status == "demonstracao"
    exp = resultado.status == "candidata_experimental"
    agora = agora or datetime.now()
    S = _estilos()
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=(40 if resultado.status == "candidata_experimental" else 33) * mm,
                          bottomMargin=20 * mm, title="Relatório MuuFeed", author="MuuFeed")
    doc.addPageTemplates([PageTemplate("p", [Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")],
                                       onPage=lambda c, d: _moldura(c, d, resultado, demo, agora))])
    por_uid = {i.uid: i for i in (ingredientes or [])}
    n = lote.n_vacas if (lote and not demo) else None
    resumo = resumo_financeiro(resultado, n, None if demo else ingredientes)
    st_ = [_p(EXPORTAVEIS[resultado.status], S["h1"])]
    if demo:
        st_ += [Table([[_p("EXEMPLO DE LAYOUT. Este documento NÃO é uma dieta formulada pelo MuuFeed e não corresponde "
                           "a nenhum lote. " + resultado.mensagem, S["demo"])]], colWidths=[doc.width],
                      style=[("BOX", (0, 0), (-1, -1), 1, VERMELHO), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEA")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)])]
    if exp:
        # Derivado do resultado (não de uma lista fixa): FDN e amido podem estar verificados
        # quando seus limites opcionais foram informados pelo usuário.
        pendentes = [nome for nome, _ in nao_avaliadas_unicas(resultado)]
        descricao_pendencias = ("Requisitos sem limites verificados: " + ", ".join(pendentes) + ". ") if pendentes else ""
        aviso = ("Resultado experimental: atende somente às restrições efetivamente verificadas. "
                 + descricao_pendencias
                 + "Não use para alimentar animais sem revisão de um profissional.")
        st_ += [Table([[_p(TEXTO_EXPERIMENTAL, S["demo"])], [_p(
            aviso, S["aviso"])]], colWidths=[doc.width],
            style=[("BOX", (0, 0), (-1, -1), 1.2, VERMELHO), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDECEA")),
                   ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]), Spacer(1, 4)]
    if resultado.mensagem and not demo:
        st_.append(_p(resultado.mensagem, S["b"]))
    if not demo:
        st_.append(_p(AVISO_PROFISSIONAL, S["peq"]))

    # 1. Identificação
    st_ += [_p("1. Identificação", S["h2"]), _pares(S, [
        ("Formulação", resultado.id_formulacao or "Não identificada"),
        ("Executada em", data_hora_br(resultado.executada_em) if resultado.executada_em else "Não informada"),
        ("Relatório gerado em", data_hora_br(agora)), ("Modelo de referência", resultado.modelo_referencia or "Não informado"),
        ("Situação", EXPORTAVEIS[resultado.status])])]

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
    st_.append(_p("3. Dieta candidata experimental (por vaca/dia)" if exp else "3. Dieta formulada (por vaca/dia)", S["h2"]))
    linhas = [[l.nome, num(l.kg_ms, 2), num(l.kg_mn, 2), num(l.pct_ms, 1, "%"),
               brl(l.preco_mn_brl_kg) + (" *" if l.origem_preco == "ilustrativo" else ""), brl(l.custo_brl)]
              for l in resumo.linhas]
    linhas.append(["Total", num(resumo.consumo_ms_kg, 2), num(resumo.consumo_mn_kg, 2), "100,0 %", "", brl(resumo.custo_vaca_dia)])
    st_.append(_tabela(S, ["Ingrediente", "MS (kg)", "MN (kg)", "% da MS", "Preço (R$/kg MN)", "Custo (R$)"],
                       linhas, [58, 20, 20, 20, 30, 26], direita=(1, 2, 3, 4, 5), total=True))
    notas = ["MS = matéria seca; MN = matéria natural (como fornecida). Proporções calculadas sobre a MS total."]
    if demo or any(l.origem_preco == "ilustrativo" for l in resumo.linhas):
        notas.append("* Preço ilustrativo, não é preço de mercado confirmado.")
    if any(l.preco_mn_brl_kg is None or l.custo_brl is None for l in resumo.linhas):
        notas.append("Preço ou custo individual não informado para ao menos um ingrediente.")
    st_ += [Spacer(1, 3)] + [_p(t, S["peq"]) for t in notas]

    # 4. Custos
    st_.append(_p("4. Consumo, custos estimados e hipóteses", S["h2"]))
    nao = "Não se aplica"
    st_.append(_metricas(S, [("Consumo de MS (kg MS/vaca/dia)", num(resumo.consumo_ms_kg, 2)),
                             ("Custo por vaca/dia", brl(resumo.custo_vaca_dia)),
                             ("Custo por lote/dia", brl(resumo.custo_lote_dia) if resumo.custo_lote_dia is not None else nao),
                             (f"Custo por mês ({resumo.dias_mes} dias)", brl(resumo.custo_mes) if resumo.custo_mes is not None else nao)]))
    hip = []
    if n:
        hip += [f"Todas as {num(n, 0)} vacas do lote recebem a mesma dieta, na mesma quantidade por vaca.",
                f"Mês de {resumo.dias_mes} dias (convenção do MuuFeed). Custo do lote = custo por vaca/dia × número de vacas; "
                "custo mensal = custo do lote/dia × dias do mês."]
    if ingredientes and not demo:
        o = [x.origem_preco for x in ingredientes if x.uid in {i.uid for i in resultado.itens}]
        sem = len(o) - o.count("ilustrativo") - o.count("informado")
        hip.append(f"Origem dos preços: {o.count('ilustrativo')} ilustrativo(s), {o.count('informado')} informado(s)"
                   + (f", {sem} sem origem." if sem else "."))
        hip.append("Data de referência dos preços: " + data_br(data_ref_precos) + ".")
    elif not demo:
        hip.append("Origem e data dos preços não disponíveis neste relatório; só os valores informados pelo formulador são exibidos.")
    st_ += [Spacer(1, 5)] + _lista(S, hip)
    for msg in resumo.inconsistencias:
        st_ += [Spacer(1, 3), _p("Atenção, inconsistência financeira: " + msg, S["aviso"])]

    # 5. Ingestão e indicadores nutricionais — limites de composição têm direção própria.
    st_.append(_p("5. Ingestão e indicadores nutricionais", S["h2"]))
    if resultado.indicadores:
        linhas = []
        for i in resultado.indicadores:
            direcao = ("Mínimo" if i.chave in ("fdn", "fdn_forragens") else
                       "Máximo" if i.chave == "amido" else "Exigência")
            limite = (f"{direcao}: {num(i.exigido, 2)}" if i.exigido is not None
                      else "Não configurado" if i.chave in ("fdn", "fdn_forragens", "amido") else "—" if i.status == "informativo" else "Não disponível")
            razao = (num(i.ingerido / i.exigido * 100, 1, "%")
                     if i.chave in ("me", "mp", "calcio_absorvido", "fosforo_absorvido", "magnesio_absorvido", "sodio_absorvido", "cloro_absorvido", "potassio_absorvido") and i.ingerido is not None
                     and i.exigido is not None and i.exigido > 0 else "—")
            linhas.append([i.rotulo, i.unidade,
                           num(i.ingerido, 2) if i.ingerido is not None else "Não disponível",
                           limite, razao, SITUACAO.get(i.status, i.status)])
        st_.append(_tabela(S, ["Indicador", "Unidade", "Valor", "Limite", "Valor / exigência", "Situação"],
                           linhas, [42, 20, 24, 35, 26, 27], direita=(2, 4)))
        st_.append(_p("Indicadores de composição em % da matéria seca são informativos quando não há exigência validada; "
                       "o traço (—) indica que nenhum limite foi aplicado. "
                       "Limites opcionais são definidos pelo usuário, não são recomendações automáticas do NASEM.", S["peq"]))
    else:
        st_.append(_p("O formulador não informou indicadores nutricionais.", S["b"]))

    # 6. Restrições
    st_.append(_p("6. Restrições", S["h2"]))
    sub = ParagraphStyle("sub", parent=S["b"], fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=3)
    tem = False
    for rot, chave in (("Atendidas", "atendida"), ("Violadas", "violada")):
        its = [r for r in resultado.restricoes if r.status == chave]
        if its:
            tem = True
            tecnicas = all(eh_chave_tecnica(r.id) for r in its)  # ids de máquina não vão para o relatório
            if tecnicas:
                tab = _tabela(S, ["Restrição", "Detalhe"], [[rotulo_legivel(r.descricao or r.id), r.detalhe or "—"] for r in its], [100, 74])
            else:
                tab = _tabela(S, ["ID", "Restrição", "Detalhe"], [[("—" if eh_chave_tecnica(r.id) else r.id),
                              rotulo_legivel(r.descricao or r.id), r.detalhe or "—"] for r in its], [22, 90, 62])
            st_.append(KeepTogether([_p(rot, sub), tab]))
    nao = nao_avaliadas_unicas(resultado)  # restrições + lista de não avaliados, sem repetição
    if nao:
        tem = True
        bloco = [_p("Não avaliadas", sub), _p("Requisitos que o sistema ainda não verifica.", S["peq"]), Spacer(1, 2)]
        if any(d for _, d in nao):
            bloco.append(_tabela(S, ["Requisito", "Detalhe"], [[r, d or "—"] for r, d in nao], [100, 74]))
        else:
            bloco += _lista(S, [r for r, _ in nao])
        st_.append(KeepTogether(bloco))
    if not tem:
        st_.append(_p("O formulador não informou restrições verificadas nem requisitos não avaliados.", S["b"]))

    # 7. Regras
    st_.append(_p("7. Regras acionadas pelo motor de inferência", S["h2"]))
    if resultado.regras:
        st_.append(_tabela(S, ["Regra", "Explicação", "Fonte"], [[r.id, r.descricao, r.fonte or "Não informada"] for r in resultado.regras], [35, 82, 57]))
    else:
        st_.append(_p("Nenhuma regra acionada foi informada pelo formulador.", S["b"]))

    # 8. Fontes e limitações
    st_.append(_p("8. Fontes e limitações", S["h2"]))
    fontes = [resultado.modelo_referencia or "Modelo de referência não informado pelo formulador.",
              "Composição dos ingredientes: biblioteca de alimentos NASEM (NASEM_feed_library.csv, distribuída com o pacote Python nasem_dairy), sem alteração de valores."]
    fontes += sorted({r.fonte for r in resultado.regras if r.fonte})
    fontes = list(dict.fromkeys(fontes))  # sem fontes repetidas
    lim = ([TEXTO_EXPERIMENTAL.capitalize() + "."] if exp else []) + [AVISO_PROFISSIONAL, "O MuuFeed não declara esta dieta como nutricionalmente completa: só foram verificados os itens listados como atendidos ou violados.",
           "A composição dos alimentos é a de referência da biblioteca; alimentos reais variam, e recomenda-se análise bromatológica.",
           "Exigências e ingestão referem-se a um animal médio do lote; variações individuais não são consideradas.",
           "Preços marcados como ilustrativos não são preços de mercado confirmados."] + list(resultado.avisos)
    st_ += [_p("Fontes", ParagraphStyle("f", parent=S["b"], fontName="Helvetica-Bold", spaceAfter=3))] + _lista(S, fontes)
    st_ += [Spacer(1, 6), _p("Limitações", ParagraphStyle("l", parent=S["b"], fontName="Helvetica-Bold", spaceAfter=3))] + _lista(S, lim)
    doc.build(st_)
    return buf.getvalue()
