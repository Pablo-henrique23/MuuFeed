"""Relatório PDF separado para análise de dieta INFORMADA, sem otimização."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from services.formatting import num, brl
from services.breed import utiliza_raca_generica, rotulo_raca_lote, AVISO_RACA_GENERICA

GREEN = colors.HexColor('#1F6B4F')
GRAY = colors.HexColor('#52625A')
BORDER = colors.HexColor('#D5E0D8')
PALE = colors.HexColor('#F1F6F2')


def gerar_pdf_analise_dieta(res: dict, lote, *, agora: datetime | None = None) -> bytes:
    """Exporta os números efetivamente avaliados, nunca chama o otimizador."""
    if not res.get('items') or res.get('total_dm_kg', 0) <= 0:
        raise ValueError('Não existe uma dieta informada válida para exportar.')
    agora = agora or datetime.now()
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=21*mm, bottomMargin=21*mm, title='MuuFeed — Análise de dieta existente')
    text = ParagraphStyle('text', fontName='Helvetica', fontSize=9, leading=13, spaceAfter=6)
    subtitle = ParagraphStyle('subtitle', parent=text, fontName='Helvetica-Bold', fontSize=11,
                               leading=15, textColor=GREEN, spaceBefore=12)
    head = ParagraphStyle('head', parent=text, fontName='Helvetica-Bold', fontSize=19,
                          leading=23, textColor=GREEN, spaceAfter=12)
    tiny = ParagraphStyle('tiny', parent=text, fontSize=8, leading=11, textColor=GRAY)
    warning = ParagraphStyle('warning', parent=text, fontName='Helvetica-Bold', textColor=colors.HexColor('#9A3412'))
    cell = ParagraphStyle('cell', parent=text, fontSize=8, leading=10, spaceAfter=0)
    cellhead = ParagraphStyle('cellhead', parent=cell, fontName='Helvetica-Bold', textColor=colors.white)
    p = lambda value, style=cell: Paragraph(escape(str(value)), style)
    story = [Paragraph('MuuFeed | Análise de dieta existente', head),
             Paragraph('AVALIAÇÃO PARCIAL — NÃO É DIETA FORMULADA NEM NUTRICIONALMENTE VALIDADA', warning),
             Paragraph('Esta análise não substitui a avaliação de médico-veterinário ou zootecnista.', text),
             Paragraph(f'Lote: {escape(lote.nome)} | Vacas: {lote.n_vacas} | Data: {agora:%d/%m/%Y %H:%M}', text),
             Paragraph('Raça: ' + escape(rotulo_raca_lote(lote)), text),
             Paragraph(f'Matéria seca: {num(res["total_dm_kg"],2)} kg/vaca/dia | '
                       f'Custo: {brl(res["cost_cow_day"])} por vaca/dia | '
                       f'Custo do lote: {brl(res["cost_herd_day"])} por dia.', text),
             Paragraph('Composição da dieta informada', subtitle)]

    if utiliza_raca_generica(lote.raca):
        story.append(Paragraph(AVISO_RACA_GENERICA, warning))

    def tab(headers, rows, widths):
        data = [[p(h,cellhead) for h in headers]] + [[p(v) for v in row] for row in rows]
        table = Table(data, colWidths=[w*mm for w in widths], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), GREEN),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LINEBELOW',(0,0),(-1,-1),.25,BORDER),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ]))
        return table

    rows = [[r['name'], num(r['kg_mn'],2), num(r['kg_dm'],2),
             num(r['pct_dm'],1,'%'), brl(r['cost_brl'])] for r in res['items']]
    story.append(tab(['Ingrediente','kg MN','kg MS','% MS','Custo'],rows,[72,24,24,24,30]))
    story.append(Paragraph('Indicadores e exigências estimadas', subtitle))
    checks = [
        ['Energia metabolizável',num(res['me_in'],2),num(res['me_req'],2),'Mcal/dia',
         'Atende' if res['me_in'] >= res['me_req'] else 'Abaixo'],
        ['Proteína metabolizável',num(res['mp_in'],2),num(res['mp_req'],2),'g/dia',
         'Atende' if res['mp_in'] >= res['mp_req'] else 'Abaixo'],
    ]
    for key,title in [('ndf_pct_dm','FDN'),('starch_pct_dm','Amido'),('forage_ndf_pct_dm','FDN de forragens')]:
        if res.get(key) is not None:
            checks.append([title,num(res[key],2),'—','% MS','Informativo'])
    for key,title in [('ca_pct_dm','Cálcio total'),('p_pct_dm','Fósforo total')]:
        value=(res.get('minerals') or {}).get(key)
        if value is not None:
            checks.append([title,num(value,2),'—','% MS','Informativo'])
    for val in (res.get('additional_nutrients') or {}).values():
        if val.get('pct_dm') is not None:
            checks.append([val['label'],num(val['pct_dm'],2),'—','% MS','Informativo'])
    for bal in (res.get('absorbed_mineral_checks') or {}).values():
        if bal.get('status') != 'nao_avaliado':
            checks.append([bal['label'],num(bal['intake'],2),num(bal['requirement'],2),
                           'g/dia abs.', 'Atende' if bal['status']=='atende' else 'Abaixo'])
    story.append(tab(['Indicador','Ingestão','Exigência','Unidade','Situação'],checks,[64,25,25,27,33]))
    story.append(Paragraph('Limitações e observações', subtitle))
    for alert in res.get('alerts') or []:
        story.append(Paragraph('• ' + escape(str(alert)), tiny))
    story.append(Spacer(1,10))
    story.append(Paragraph('O resultado reflete quantidades inseridas pelo usuário; não houve otimização. '
                           'Nutrientes totais diferem de absorvidos. Os alimentos da biblioteca são valores '
                           'de referência; alimentos reais exigem análise bromatológica e avaliação profissional.',tiny))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(18*mm,16*mm,A4[0]-18*mm,16*mm)
        canvas.setFont('Helvetica',7)
        canvas.setFillColor(GRAY)
        canvas.drawString(18*mm,11*mm,'Análise experimental — não substitui médico-veterinário ou zootecnista')
        canvas.drawRightString(A4[0]-18*mm,11*mm,f'Página {document.page}')
        canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return stream.getvalue()
