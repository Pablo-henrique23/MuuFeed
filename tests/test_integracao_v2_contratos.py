"""Teste de integração do adaptador v2 sem depender de instalação local do NASEM."""
import sys
import types
from dataclasses import replace
from unittest.mock import patch

import pytest

from models import Ingrediente, OpcoesFormulacao, RequisicaoFormulacao
from services.nasem_adapter import NasemFormulador
from tests.test_contracts import lote_ok


def _req(ndf=None, starch=None):
    lote = lote_ok()
    return RequisicaoFormulacao(lote, [
        Ingrediente("a", "Alfalfa meal", "Alfafa", 90, 2),
        Ingrediente("b", "Corn silage, typical", "Silagem de milho", 35, .5),
    ], OpcoesFormulacao(consumo_ms_kg_dia=22, min_ndf_pct_dm=ndf,
                        max_starch_pct_dm=starch))


def _fake_result(ndf, starch, limited):
    checked = ["total_ms", "me", "mp", "limites_operacionais"]
    unchecked = ["fibra_fisicamente_efetiva", "minerais", "vitaminas", "limites_nutricionais_de_inclusao"]
    for key, enabled in (("fdn", limited), ("amido", limited)):
        (checked if enabled else unchecked).append(key)
    return {
        "status": "candidata_experimental", "diet": [
            {"ingredient": "Alfalfa meal", "kg_dm_cow_day": 10., "kg_as_fed_cow_day": 11.111,
             "cost_brl_cow_day": 22.222, "price_brl_kg_as_fed": 2.},
            {"ingredient": "Corn silage, typical", "kg_dm_cow_day": 12., "kg_as_fed_cow_day": 34.285,
             "cost_brl_cow_day": 17.1425, "price_brl_kg_as_fed": .5}],
        "nutrition": {"me_intake_mcal_day": 60., "me_requirement_mcal_day": 52.,
                      "mp_intake_g_day": 2200., "mp_requirement_g_day": 2000.},
        "nutrient_composition": {"ndf_pct_dm": ndf, "starch_pct_dm": starch,
                                 "ndf_min_pct_dm": 25. if limited else None,
                                 "starch_max_pct_dm": 30. if limited else None},
        "constraints_checked": checked, "constraints_not_checked": unchecked,
        "activated_rules": [{"id": "R_FDN_MIN", "explanation": "Mínimo definido pelo usuário",
                             "source": "Limite informado pelo usuário"}] if limited else [],
        "cost_brl_cow_day": 39.3645,
    }


@pytest.mark.parametrize("limited", [False, True])
def test_contrato_motor_adaptador_v2(limited):
    fake_nasem = types.ModuleType("nasem_dairy")
    fake_nasem.demo = lambda _: (None, {}, {}, None)
    request = _req(25, 30) if limited else _req()
    captured = []

    def fake_formulate(req):
        captured.append(req)
        return _fake_result(32.5, 29.3, limited)

    with patch.dict(sys.modules, {"nasem_dairy": fake_nasem}), patch(
        "services.nasem_adapter.formulate_diet", side_effect=fake_formulate
    ):
        adapter = NasemFormulador()
        assert adapter.verificar_escopo(request) == (True, "")
        res = adapter.formular(request)

    assert res.status == "candidata_experimental"
    assert captured[0].min_ndf_pct_dm == (25 if limited else None)
    assert captured[0].max_starch_pct_dm == (30 if limited else None)
    indic = {i.chave: i for i in res.indicadores}
    assert indic["fdn"].ingerido == pytest.approx(32.5)
    assert indic["amido"].ingerido == pytest.approx(29.3)
    assert indic["fdn"].status == indic["amido"].status == ("atende" if limited else "informativo")
    assert indic["fdn"].exigido == (25 if limited else None)
    assert indic["amido"].exigido == (30 if limited else None)
    if limited:
        assert "FDN" in res.mensagem and "amido" in res.mensagem
        assert res.regras[0].fonte == "Limite informado pelo usuário"
    else:
        assert "FDN" not in res.mensagem and "amido" not in res.mensagem


@pytest.mark.parametrize("value", [-1, 101, float("nan"), float("inf"), "foo"])
def test_limites_invalidos_sao_rejeitados(value):
    req = _req(ndf=value)
    assert NasemFormulador().verificar_escopo(req)[0] is False
