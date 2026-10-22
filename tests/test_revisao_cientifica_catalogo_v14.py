"""Regressão: classificação do NASEM, equivalente proteico e suplementação segura."""
import pandas as pd
import pytest
from services.feed_science import (
    FONTES_NNP, classificar_uso, eh_so_bezerro, limite_explicito_obrigatorio,
    proteina_bruta_valida, referencia_inclusao,
)
from services.forage_ndf import classificar_forragem
from scripts.auditar_catalogo_nutricional import auditar
from services.nasem_adapter import NasemFormulador
from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from tests.test_contracts import lote_ok


def test_alfalfa_tipo_nasem_forage_preenche_fndf_sem_ignorar_conflito():
    assert classificar_forragem('Alfalfa meal', feed_type='Forage', feed_category='Plant Protein') == (
        True, 'curadoria_nasem_alfalfa_tipo_prevalece')
    assert classificar_forragem('Produto desconhecido', feed_type='Forage', feed_category='Plant Protein')[0] is None


@pytest.mark.parametrize('nome', sorted(FONTES_NNP))
def test_nnp_pode_ultrapassar_100_por_cent_de_cp_equivalente(nome):
    assert proteina_bruta_valida(nome, 125)
    assert not proteina_bruta_valida(nome, 500)
    assert limite_explicito_obrigatorio(nome)


def test_proteina_120_nao_nnp_continua_erro():
    assert not proteina_bruta_valida('Corn silage, typical', 120)


def test_bezerro_nao_elegivel_em_lactacao():
    nome = 'Calf starter 18CP high starch (Fed to calves only)'
    assert eh_so_bezerro(nome)
    assert classificar_uso(nome, 'Energy Source')[0] == 'NAO_ELEGIVEL_LACTACAO'


def test_literatura_de_inclusao_nao_aplica_teto_por_padrao():
    val, obs, fonte = referencia_inclusao('Urea')
    assert val == 1.0 and 'TMR' in obs and 'extension.psu.edu' in fonte
    assert referencia_inclusao('Corn silage, typical')[0] is None


def test_auditoria_recupera_alertas_de_falso_positivo_sem_alterar_biblioteca():
    df = pd.DataFrame([
        {'UID':'1','Fd_Name':'Alfalfa meal','Fd_Type':'Forage', 'Fd_Category':'Plant Protein',
         'Fd_DM':90, 'Fd_CP':18, 'Fd_NDF':40, 'Fd_St':3},
        {'UID':'2','Fd_Name':'Ammonium chloride','Fd_Type':'Concentrate', 'Fd_Category':'Vitamin/Mineral',
         'Fd_DM':100, 'Fd_CP':163.6, 'Fd_NDF':0, 'Fd_St':0},
        {'UID':'3','Fd_Name':'Urea','Fd_Type':'Concentrate', 'Fd_Category':'Additive',
         'Fd_DM':100, 'Fd_CP':281, 'Fd_NDF':0, 'Fd_St':0},
        {'UID':'4','Fd_Name':'Vit D premix','Fd_Type':'Concentrate', 'Fd_Category':'Vitamin/Mineral',
         'Fd_DM':99, 'Fd_CP':0, 'Fd_NDF':None, 'Fd_St':None},
    ])
    out = auditar(df)
    assert (out['situacao'] != 'REVISAO_NECESSARIA').all()
    assert (out.loc[0, 'fdn_forragem_classificacao'] == 'FORRAGEM')
    assert out.loc[1, 'proteina_bruta_equivalente_nnp']
    assert out.loc[2, 'exige_maximo_explicito']
    assert out.loc[3, 'situacao'] == 'OK_COM_LACUNAS'
    assert not out.loc[3, 'fdn_total_disponivel']
    assert pd.isna(df.loc[3, 'Fd_NDF'])


def _req(feed1, feed2):
    return RequisicaoFormulacao(lote_ok(), [
        Ingrediente('a','Corn silage, typical','Silagem',35.0,0.30),
        Ingrediente('b', feed1, feed2, 100.0, 1.00),
    ], OpcoesFormulacao(consumo_ms_kg_dia=20))


def test_adapter_bloqueia_ureia_sem_teto_e_aceita_com_teto():
    req=_req('Urea','Ureia')
    ok,msg=NasemFormulador().verificar_escopo(req)
    assert not ok and 'máximo' in msg
    req.ingredientes[1].max_kg_mn=0.05
    ok,msg=NasemFormulador().verificar_escopo(req)
    assert ok, msg


def test_adapter_bloqueia_racao_so_bezerro():
    req=_req('Calf grower 14CP (Fed to calves only)','Ração bezerro')
    ok,msg=NasemFormulador().verificar_escopo(req)
    assert not ok and 'bezerros' in msg
