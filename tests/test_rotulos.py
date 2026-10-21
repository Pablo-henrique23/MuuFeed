import pytest
from models import Restricao
from services.rotulos import eh_chave_tecnica, nao_avaliadas_unicas, rotulo_legivel
from tests.factories import resultado_teste
from dataclasses import replace

CHAVES_DO_MOTOR = ["total_ms", "me", "mp", "limites_operacionais", "fdn", "fibra_fisicamente_efetiva",
                   "amido", "minerais", "vitaminas", "limites_nutricionais_de_inclusao"]


@pytest.mark.parametrize("chave", CHAVES_DO_MOTOR)
def test_toda_chave_do_motor_tem_rotulo_legivel(chave):
    for forma in (chave, chave.upper()):              # o adaptador emite as duas formas
        r = rotulo_legivel(forma)
        assert "_" not in r and r != forma and r[0].isupper()
    assert rotulo_legivel("fibra_fisicamente_efetiva") == "Fibra fisicamente efetiva"
    assert rotulo_legivel("FDN") == "Fibra em detergente neutro (FDN)"


def test_chave_desconhecida_usa_regra_de_reserva_e_textos_normais_passam():
    assert rotulo_legivel("limite_de_gordura") == "Limite de gordura"
    assert rotulo_legivel("Amido máximo") == "Amido máximo"          # frase: intacta
    assert rotulo_legivel("Restrição pendente") == "Restrição pendente"
    assert eh_chave_tecnica("total_ms") and eh_chave_tecnica("ME") and not eh_chave_tecnica("C1")
    assert not eh_chave_tecnica("R-01") and not eh_chave_tecnica("Amido máximo")


def test_nao_avaliadas_sao_unificadas_sem_repeticao():
    # formato real do adaptador: o mesmo requisito como restrição (UPPER) e na lista (snake_case)
    res = replace(resultado_teste("candidata_experimental"),
                  restricoes=[Restricao(k, k.upper(), "nao_avaliada") for k in ("fdn", "fibra_fisicamente_efetiva", "amido")],
                  nao_avaliadas=["fdn", "fibra_fisicamente_efetiva", "amido", "minerais"])
    assert nao_avaliadas_unicas(res) == [("Fibra em detergente neutro (FDN)", ""), ("Fibra fisicamente efetiva", ""),
                                         ("Amido", ""), ("Minerais", "")]


def test_detalhe_da_restricao_e_preservado_na_unificacao():
    res = replace(resultado_teste(), restricoes=[Restricao("amido", "AMIDO", "nao_avaliada", "sem dado de amido")],
                  nao_avaliadas=["amido"])
    assert nao_avaliadas_unicas(res) == [("Amido", "sem dado de amido")]
