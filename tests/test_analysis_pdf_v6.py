import io
import pytest
from pypdf import PdfReader
from services.analysis_pdf import gerar_pdf_analise_dieta
from tests.test_contracts import lote_ok


def resultado():
    return {'items':[{'name':'Silagem','kg_mn':20,'kg_dm':7.0,'pct_dm':70.,'cost_brl':6},
                     {'name':'Farelo','kg_mn':3,'kg_dm':3.0,'pct_dm':30.,'cost_brl':7.35}],
            'total_dm_kg':10,'cost_cow_day':13.35,'cost_herd_day':400.50,
            'me_in':25,'me_req':50,'mp_in':1000,'mp_req':1800,
            'ndf_pct_dm':34,'starch_pct_dm':24,'forage_ndf_pct_dm':30,
            'minerals':{'ca_pct_dm':.25,'p_pct_dm':.3},
            'additional_nutrients':{},
            'absorbed_mineral_checks':{'calcio_absorvido':{'label':'Cálcio absorvido',
            'intake':20,'requirement':40,'status':'viola'}},
            'alerts':['Sem otimização']}

def test_pdf_analise_distingue_quantidades_e_adequacao():
    pdf=gerar_pdf_analise_dieta(resultado(),lote_ok())
    assert pdf.startswith(b'%PDF')
    pages=PdfReader(io.BytesIO(pdf)).pages
    text=' '.join(p.extract_text() for p in pages)
    for term in ('Análise de dieta existente','NÃO É DIETA FORMULADA','Cálcio absorvido',
                 'Abaixo','Silagem','13,35','zootecnista'):
        assert term in text

def test_pdf_rejeita_dieta_sem_itens():
    with pytest.raises(ValueError):
        gerar_pdf_analise_dieta({'items':[],'total_dm_kg':0},lote_ok())
