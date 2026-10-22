"""Garante que o usuário vê nomes PT sem alterar chaves NASEM."""
from services.feed_translation import traduzir_nome


def test_exemplos_da_tela_ficam_em_portugues():
    casos = {
        'Zinc, organic generic': 'Zinco orgânico (genérico)',
        'Calf grower 14CP (Fed to calves only)': 'Ração de crescimento para bezerros (14% PB; somente bezerros)',
        'Calf grower 16CP (Fed to calves only)': 'Ração de crescimento para bezerros (16% PB; somente bezerros)',
        'Calf starter 18CP high starch (Fed to calves only)': 'Ração inicial para bezerros (18% PB, alto amido; somente bezerros)',
        'Calf starter 18CP low starch (Fed to calves only)': 'Ração inicial para bezerros (18% PB, baixo amido; somente bezerros)',
        'Calf starter 22CP high starch (Fed to calves only)': 'Ração inicial para bezerros (22% PB, alto amido; somente bezerros)',
        'Calf starter 22CP med starch (Fed to calves only)': 'Ração inicial para bezerros (22% PB, amido médio; somente bezerros)',
        'Casein': 'Caseína',
    }
    for en, pt in casos.items():
        assert traduzir_nome(en) == (pt, True)


def test_nome_tecnico_nao_reconhecido_nao_e_adivinhado():
    assert traduzir_nome('Unlisted feedstuff ZYX') == ('Unlisted feedstuff ZYX', False)


def test_formas_minerais_previsiveis():
    assert traduzir_nome('Manganese sulfate (H2O)') == ('Sulfato de manganês (H2O)', True)
    assert traduzir_nome('Sodium chloride (salt)', {'Sodium chloride (salt)': 'Sal comum'}) == ('Sal comum', True)


def test_mapeamento_de_usuario_prevalece():
    assert traduzir_nome('Casein', {'Casein': 'Caseína técnica'}) == ('Caseína técnica', True)


def test_catalogo_busca_nos_dois_idiomas_sem_alterar_nome_original(monkeypatch):
    import pandas as pd
    from services import feed_catalog
    dados = pd.DataFrame({
        'UID': ['i1','i2'], 'Fd_Name': ['Zinc, organic generic','Calf starter 18CP high starch (Fed to calves only)'],
        'Fd_Category': ['Vitamin/Mineral','Energy Source'], 'Fd_Type': ['Concentrate','Concentrate'],
        'Fd_DM': [98.,88.],
    })
    monkeypatch.setattr(feed_catalog, 'carregar_biblioteca_bruta', lambda: dados.copy())
    cat = feed_catalog.CatalogoIngredientes()
    assert cat.tabela['nome_original'].tolist() == dados['Fd_Name'].tolist()
    assert cat.tabela['nome_pt'].tolist()[0] == 'Zinco orgânico (genérico)'
    assert cat.tabela['traduzido'].tolist() == [True, True]
    assert len(cat.buscar('zinco organico')) == 1
    assert len(cat.buscar('zinc organic')) == 1
    assert len(cat.buscar('bezerros')) == 1
    assert len(cat.buscar('calf starter')) == 1
