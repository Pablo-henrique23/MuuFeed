from types import SimpleNamespace
import pandas as pd

from services.ingredient_suggestion import CANDIDATOS_LACTACAO, sugerir_ingredientes


class LoteTeste:
    estado = 'Lactating Cow'
    def validar(self):
        return [], []


def catalogo_teste():
    nomes = [nome for nome, _, _ in CANDIDATOS_LACTACAO]
    return SimpleNamespace(
        tabela=pd.DataFrame([{'uid':str(i), 'nome_original':n, 'nome_pt':n, 'ms_pct':45.0}
                             for i,n in enumerate(nomes)]),
        precos_ilustrativos={'0':0.5, '1':1.0}
    )


def test_sugestao_nao_cria_preco_para_alimento_sem_preco():
    s, avisos = sugerir_ingredientes(LoteTeste(), catalogo_teste())
    assert len(s) == len(CANDIDATOS_LACTACAO)
    assert s[0].preco_ilustrativo == 0.5
    assert s[2].preco_ilustrativo is None
    assert not avisos


def test_sugestao_sem_lote_nao_prossegue():
    s, avisos = sugerir_ingredientes(None, catalogo_teste())
    assert not s and avisos


def test_sugestao_recusa_vaca_seca():
    lote = LoteTeste()
    lote.estado = 'Dry Cow'
    s, avisos = sugerir_ingredientes(lote, catalogo_teste())
    assert not s and 'lactação' in avisos[0]


def test_sugestao_ignora_alimento_ausente_sem_fabricar_dados():
    cat = catalogo_teste()
    cat.tabela = cat.tabela.iloc[:1]
    s, avisos = sugerir_ingredientes(LoteTeste(), cat)
    assert len(s) == 1 and len(avisos) == len(CANDIDATOS_LACTACAO)-1


def test_sugestao_nao_modifica_catalogo():
    cat = catalogo_teste()
    antes = cat.tabela.copy(deep=True)
    sugerir_ingredientes(LoteTeste(), cat)
    pd.testing.assert_frame_equal(cat.tabela, antes)
