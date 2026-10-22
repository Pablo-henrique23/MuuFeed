"""Regressão v15: metadados bibliográficos NASEM e regras numéricas no PDF."""
from dataclasses import replace
from datetime import datetime
import io

import pandas as pd
from pypdf import PdfReader

from models import Indicador, RegraAcionada
from scripts.auditar_catalogo_nutricional import auditar
from services.pdf_report import gerar_relatorio_pdf
from tests.factories import ingredientes_teste, resultado_teste
from tests.test_contracts import lote_ok


def test_fd_libr_bibliografia_textual_nao_e_erro_numerico():
    df = pd.DataFrame([{
        'UID': 1, 'Fd_Name': 'Corn silage, typical', 'Fd_Type': 'Forage',
        'Fd_Category': 'Grass/Legume Forage', 'Fd_Libr': 'NASEM Dairy (2021)',
        'Fd_DM': 35.0, 'Fd_NDF': 42.0, 'Fd_St': 30.0,
    }])
    original = df.copy(deep=True)
    result = auditar(df).iloc[0]
    assert result['situacao'] == 'OK_COM_LACUNAS'
    assert result['campos_adicionais_nao_numericos'] == ''
    assert result['total_campos_nasem'] == 4  # Fd_Libr, DM, NDF, St
    pd.testing.assert_frame_equal(df, original)


def test_campo_adicional_numericamente_invalido_ainda_e_detectado():
    df = pd.DataFrame([{
        'UID': 1, 'Fd_Name': 'Corn silage, typical', 'Fd_Type': 'Forage',
        'Fd_Category': 'Grass/Legume Forage', 'Fd_Libr': 'NASEM (2021)',
        'Fd_DM': 35.0, 'Fd_NDF': 42.0, 'Fd_St': 30.0,
        'Fd_EnergyHypothetical': 'nao numerico',
    }])
    row = auditar(df).iloc[0]
    assert row['situacao'] == 'REVISAO_NECESSARIA'
    assert row['campos_adicionais_nao_numericos'] == 'Fd_EnergyHypothetical'


def _pdf_texto(resultado):
    pdf = gerar_relatorio_pdf(resultado, lote_ok(), ingredientes_teste(),
                              None, datetime(2026, 10, 22, 13, 50))
    text = ' '.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    return ' '.join(text.split())


def test_regras_ativas_numeros_reais_e_fontes_simplificadas_no_pdf():
    orig = resultado_teste('candidata_experimental')
    ind = [
        Indicador('me', 'Energia metabolizável', 'Mcal/dia', 62.85, 52.12, 'atende'),
        Indicador('mp', 'Proteína metabolizável', 'g/dia', 2012.82, 2012.82, 'atende'),
        Indicador('calcio_absorvido', 'Cálcio absorvido', 'g/dia', 53.24, 53.24, 'atende'),
        Indicador('fosforo_absorvido', 'Fósforo absorvido', 'g/dia', 67.40, 49.93, 'atende'),
        Indicador('sodio_absorvido', 'Sódio absorvido', 'g/dia', 45.82, 45.82, 'atende'),
        Indicador('magnesio_absorvido', 'Magnésio absorvido', 'g/dia', 18.27, 10.63, 'atende'),
        Indicador('cloro_absorvido', 'Cloro absorvido', 'g/dia', 108.64, 52.41, 'atende'),
        Indicador('potassio_absorvido', 'Potássio absorvido', 'g/dia', 297.35, 224.28, 'atende'),
        Indicador('fdn', 'FDN', '% da MS', 41.41, 25.00, 'atende'),
        Indicador('fdn_forragens', 'FDN proveniente de forragens', '% da MS', 35.23, 19.0, 'atende'),
        Indicador('amido', 'Amido', '% da MS', 20.79, 30.0, 'atende'),
    ]
    source_nasem = 'NASEM 2021 via nasem_dairy'
    comp = 'Limite informado pelo usuário; composição NASEM'
    rules = [
        RegraAcionada('R_CA_ABS','Cálcio absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_P_ABS','Fósforo absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_NA_ABS','Sódio absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_MG_ABS','Magnésio absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_CL_ABS','Cloro absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_K_ABS','Potássio absorvido >= exigência calculada no NASEM',source_nasem),
        RegraAcionada('R_ME','Energia metabolizável ingerida >= exigida no cenário avaliado',source_nasem),
        RegraAcionada('R_MP','Proteína metabolizável ingerida >= exigida no cenário avaliado',source_nasem),
        RegraAcionada('R_FDN_FORRAGEM_MIN','FDN de forragens 35.23% MS >= mínimo configurado 19%',comp + ', classificação explícita'),
        RegraAcionada('R_FDN_MIN','FDN 41.41% MS >= mínimo configurado 25%',comp),
        RegraAcionada('R_AMIDO_MAX','Amido 20.79% MS <= máximo configurado 30%',comp),
    ]
    res = replace(orig, indicadores=ind, regras=rules, modelo_referencia=source_nasem)
    t = _pdf_texto(res)
    rules_text = t[t.index('7. Regras acionadas'):t.index('8. Fontes e limitações')]
    for chunk in [
        'Cálcio absorvido: 53,24 >= 53,24 g/dia',
        'Fósforo absorvido: 67,40 >= 49,93 g/dia',
        'Sódio absorvido: 45,82 >= 45,82 g/dia',
        'Energia metabolizável: 62,85 >= 52,12 Mcal/dia',
        'Proteína metabolizável: 2.012,82 >= 2.012,82 g/dia',
        'FDN de forragens: 35,23% MS >= 19,00% MS',
        'FDN: 41,41% MS >= 25,00% MS',
        'Amido: 20,79% MS <= 30,00% MS',
        'NASEM 2021 + usuário',
    ]:
        assert chunk in rules_text, chunk
    assert 'calculada no NASEM' not in rules_text
    assert 'mínimo configurado' not in rules_text
    assert 'máximo configurado' not in rules_text
    assert 'exigida no cenário avaliado' not in rules_text
    assert 'via nasem_dairy' not in t
    assert 'Composição dos ingredientes: biblioteca NASEM 2021' in t
    assert 'valores definidos pelo usuário' in t


def test_pdf_regra_sem_valor_nao_inventa_numero():
    res = replace(resultado_teste('candidata_experimental'),
                  regras=[RegraAcionada('R_CA_ABS', 'Dados de cálcio não disponíveis', 'NASEM 2021')])
    t = _pdf_texto(res)
    assert 'Dados de cálcio não disponíveis' in t
