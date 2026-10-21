"""Tests without nasem_dairy installed: a fake evaluator only tests wiring and cost."""
from types import SimpleNamespace
import pytest
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet, validate_request


class FakeOutput:
    def __init__(self, values):
        self.values = values
    def get_value(self, name):
        return self.values[name]


def fake_evaluate(diet, animal, equations, infusion):
    q = dict(zip(diet["Feedstuff"], diet["kg_user"]))
    return FakeOutput({
        "An_MEIn": 2 * q["Forage A"] + 5 * q["Concentrate B"],
        "Trg_MEuse": 20.0,
        "An_MPIn_g": 130 * q["Forage A"] + 350 * q["Concentrate B"],
        "An_MPuse_g_Trg": 1400.0,
    })


def request(**kwargs):
    data = dict(
        feeds=(FeedChoice("Forage A", 0.5, 50), FeedChoice("Concentrate B", 2, 100)),
        animal={"An_StatePhys": "Lactating Cow", "An_AgeDay": 1000,
                "An_BW": 600, "An_LactDay": 150, "An_Parity_rl": 2},
        equations={"DMIn_eqn": 0}, total_dm_kg=10, herd_size=20,
        max_iterations=80, restarts=2,
    )
    data.update(kwargs)
    return FormulationRequest(**data)


def test_formulation_cost_units_and_constraints():
    out = formulate_diet(request(), evaluate=fake_evaluate,
                         catalog_names={"Forage A", "Concentrate B"})
    assert out["status"] == "candidata_experimental"
    assert out["nutrition_completeness"] == "nao_avaliada"
    assert out["nutrition"]["me_intake_mcal_day"] >= 20
    assert out["nutrition"]["mp_intake_g_day"] >= 1400
    assert abs(sum(r["kg_dm_cow_day"] for r in out["diet"]) - 10) < 1e-5
    assert abs(sum(r["cost_brl_cow_day"] for r in out["diet"]) - out["cost_brl_cow_day"]) < 1e-5
    assert out["cost_brl_herd_day"] == pytest.approx(out["cost_brl_cow_day"] * 20)
    assert out["constraints_not_checked"]


def test_reject_unknown_ingredient():
    with pytest.raises(ValueError, match="ausentes"):
        formulate_diet(request(), evaluate=fake_evaluate, catalog_names={"Forage A"})


def test_reject_wrong_dmi():
    req = request(animal={**request().animal, "Trg_Dt_DMIn": 15})
    with pytest.raises(ValueError, match="total_dm_kg"):
        validate_request(req)


def test_reject_impossible_bounds():
    req = request(feeds=(FeedChoice("Forage A", 0.5, 50, maximum_dm_kg=2),
                         FeedChoice("Concentrate B", 2, 100, maximum_dm_kg=3)))
    with pytest.raises(ValueError, match="limites operacionais"):
        validate_request(req)


def test_reject_invalid_dry_matter():
    req = request(feeds=(FeedChoice("Forage A", 0.5, 0), FeedChoice("Concentrate B", 2, 100)))
    with pytest.raises(ValueError, match="MS"):
        validate_request(req)
