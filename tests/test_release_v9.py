"""Testes de contrato, nomes bilíngues e triagem mineral sem extrapolação."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from models import Lote
from services.breed import para_raca_nasem
from services.feed_translation import traduzir_nome
from services.mineral_upper_review import revisar_superiores_minerais


def test_holandesa_jersy_normalizam_sem_alterar_valor_nasem():
    assert para_raca_nasem('Holandesa') == 'Holstein'
    assert para_raca_nasem(' HOLANDESA ') == 'Holstein'
    assert para_raca_nasem('hOlAnDeSa') == 'Holstein'
    assert para_raca_nasem('Jersey') == 'Jersey'
    with pytest.raises(ValueError):
        para_raca_nasem('Outra')


def test_lote_nao_expoe_destinacao_economica_irrelevante():
    import dataclasses
    assert 'destinacao_economica' not in {f.name for f in dataclasses.fields(Lote)}
    assert 'An_Breed' in Lote(raca='Holandesa').para_animal_nasem()


def test_destinacao_nao_muda_chave_breed():
    lote = Lote(raca='Holandesa')
    assert lote.para_animal_nasem()['An_Breed'] == 'Holstein'
    lote.raca = 'Jersey'
    assert lote.para_animal_nasem()['An_Breed'] == 'Jersey'


def test_todas_traducoes_pendentes_exatas_escaneaveis():
    raiz = Path(__file__).resolve().parents[1]
    mapa = json.loads((raiz/'data/feed_names_pt.json').read_text(encoding='utf-8'))
    valores = list(mapa.values())
    assert all(v and v.strip() for v in valores)
    assert len(set(mapa)) == len(mapa)
    auditoria = (raiz/'tests/data_traducoes_v9.csv')
    rows = list(csv.DictReader(auditoria.open(encoding='utf-8',newline='')))
    assert len(rows) == 90
    for r in rows:
        original = r['Nome original NASEM']
        esperado = r['Sugestao de nome PT']
        assert mapa[original] == esperado
        assert traduzir_nome(original,mapa) == (esperado,True)


def test_busca_ambos_idiomas_depois_das_novas_traducoes(monkeypatch):
    from services import feed_catalog
    dados = pd.DataFrame({
        'UID':['u1','u2','u3'],
        'Fd_Name':['Whey, fresh','Selenite, sodium','Sunflower silage'],
        'Fd_Category':['By-Product/Other','Vitamin/Mineral','Grain Crop Forage'],
        'Fd_Type':['Concentrate','Concentrate','Forage'],
        'Fd_DM':[6.0,99.0,32.0],
    })
    monkeypatch.setattr(feed_catalog,'carregar_biblioteca_bruta', lambda: dados.copy())
    cat=feed_catalog.CatalogoIngredientes()
    assert len(cat.buscar('soro de leite fresco'))==1
    assert len(cat.buscar('Whey fresh'))==1
    assert len(cat.buscar('selenito de sodio'))==1
    assert len(cat.buscar('Selenite sodium'))==1
    assert len(cat.buscar('silagem girassol'))==1
    assert len(cat.buscar('sunflower silage'))==1
    assert cat.tabela['nome_original'].tolist()==dados['Fd_Name'].tolist()


def test_maximo_cloro_nao_e_inventado():
    a=revisar_superiores_minerais(
        dieta_ms=[('Sodium chloride (salt)',.08),('Corn silage, typical',24.44)],
        total_ms_kg=24.52,
        balancos={'cloro_absorvido':{'intake':117.5,'requirement':52.47}},
    )
    assert any('NaCl declarado' in s and 'NÃO recomendação' in s for s in a)
    assert any('EXIGÊNCIA MÍNIMA' in s and 'não estabelece' in s for s in a)
    assert not any('tóxico' in s.lower() for s in a)


def test_maximo_de_nacl_mais_que_tres_porcento_gera_alerta_sem_validacao():
    a=revisar_superiores_minerais(dieta_ms=[('Sodium chloride (salt)',0.8)],total_ms_kg=20)
    assert any('ATENÇÃO' in s and '3%' in s for s in a)


def test_sem_sodio_e_sem_cloro_nao_acrescenta_alerta():
    assert revisar_superiores_minerais(dieta_ms=[('Canola meal',5)],total_ms_kg=5)==[]
