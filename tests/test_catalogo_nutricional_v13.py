"""Cobertura de metadados NASEM e comportamento conservador com nutrientes."""
import pandas as pd
from services.forage_ndf import classificar_forragem, is_forage
from scripts.auditar_catalogo_nutricional import auditar


def test_classificacao_metadados_nasem_tipo_foragem():
    assert classificar_forragem('Silagem hipotetica', feed_type='Forage') == (True, 'Fd_Type')
    assert is_forage('Subproduto novo', feed_type='Concentrate') is False
    assert is_forage('Nutriente novo', feed_category='Vitamin/Mineral') is False
    assert is_forage('Pasto novo', feed_category='Pasture') is True
    assert is_forage('Desconhecido') is None


def test_metadados_inconsistentes_nao_chutam():
    assert classificar_forragem('Alimento', feed_type='Forage',
                                feed_category='Plant Protein') == (None, 'conflito_tipo_categoria_nasem')


def test_auditoria_nao_inventa_valores_ausentes():
    a = pd.DataFrame([
        {'UID':'1', 'Fd_Name':'Forragem nova', 'Fd_Type':'Forage',
         'Fd_Category':'Grass/Legume Forage', 'Fd_DM':34.0, 'Fd_NDF':40.0,
         'Fd_St':float('nan'), 'Fd_Ca':0.4},
        {'UID':'2', 'Fd_Name':'Concentrado novo', 'Fd_Type':'Concentrate',
         'Fd_Category':'Plant Protein', 'Fd_DM':90.0, 'Fd_NDF':30.0,
         'Fd_St':20.0, 'Fd_Ca':0.1},
    ])
    res = auditar(a)
    assert len(res) == 2
    assert set(res['fdn_forragem_classificacao']) == {'FORRAGEM','NAO_FORRAGEM'}
    assert res.loc[0, 'amido_disponivel'] == False
    assert 'Fd_St' in res.loc[0, 'nutrientes_ausentes']
    assert (res['situacao'] == 'OK_COM_LACUNAS').all()
    assert a.loc[0,'Fd_NDF'] == 40.0  # Fonte preservada.


def test_auditoria_aponta_dm_invalida_e_inconsistencia():
    a = pd.DataFrame([{
        'UID':'a', 'Fd_Name':'Inconsistente', 'Fd_Type':'Forage',
        'Fd_Category':'Plant Protein', 'Fd_DM':0.0, 'Fd_NDF':120.0,
    }])
    linha = auditar(a).iloc[0]
    assert linha['fdn_forragem_classificacao'] == 'PENDENTE'
    assert linha['situacao'] == 'REVISAO_NECESSARIA'
    assert 'Fd_NDF' in linha['nutrientes_invalidos']


def test_auditoria_cobre_tambem_campos_nasem_adicionais_e_duplicacoes():
    df = pd.DataFrame([
        {'UID':'A','Fd_Name':'A','Fd_Type':'Forage',
         'Fd_Category':'Pasture','Fd_DM':40,'Fd_NDF':45,
         'Fd_Marcador_Novo':1.25},
        {'UID':'A','Fd_Name':'B','Fd_Type':'Concentrate',
         'Fd_Category':'Plant Protein','Fd_DM':90,'Fd_NDF':30,
         'Fd_Marcador_Novo':float('nan')},
    ])
    res = auditar(df)
    assert 'Fd_Marcador_Novo' in res.loc[1,'campos_nasem_ausentes']
    assert res.loc[0,'uid_ou_nome_duplicado']
    assert (res['situacao'] == 'REVISAO_NECESSARIA').all()
