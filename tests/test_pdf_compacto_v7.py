"""PDF compacto deve preservar avisos e eliminar textos verbosos repetidos."""
from dataclasses import replace
import io
from pypdf import PdfReader
from models import Indicador
from services.pdf_report import gerar_relatorio_pdf
from tests.factories import resultado_teste, ingredientes_teste
from tests.test_contracts import lote_ok


def test_pdf_v7_compacto_alerta_e_preco_unitario():
    principais=[
      Indicador('me','Energia metabolizável','Mcal/dia',60,50,'atende'),
      Indicador('calcio_absorvido','Cálcio absorvido','g/dia',25,53,'viola'),
      Indicador('sodio_absorvido','Sódio absorvido','g/dia',3,45,'viola'),
      Indicador('fdn','FDN','% da MS',35,None,'informativo'),
    ]
    informativos=[Indicador('p'+str(j), 'Nutriente '+str(j),'% da MS', j+0.1,None,'informativo')
                  for j in range(17)]
    res=replace(resultado_teste('candidata_experimental'), indicadores=principais+informativos)
    pdf=gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste())
    pgs=PdfReader(io.BytesIO(pdf)).pages
    txt=' '.join(p.extract_text() for p in pgs)
    assert len(pgs)<=4
    assert all(len(p.extract_text())>550 for p in pgs)  # sem página quase vazia
    assert 'Cálcio absorvido' in txt and 'Sódio absorvido' in txt
    assert 'ATENÇÃO: exigências/limites não atendidos' in txt
    assert 'Composição adicional' in txt
    assert 'Informativo (sem veredito)' not in txt
    assert 'Preço por kg MN é unitário' in txt
    assert 'não há exigência validada' in txt
