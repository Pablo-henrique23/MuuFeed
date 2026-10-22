"""Análise de dieta FIXA, sem otimização. Não declara adequação nutricional total.

Recebe quantidades de matéria natural em kg/vaca/dia; utiliza as mesmas equações
NASEM da formulação e retorna dados para visualização independente.
"""
from __future__ import annotations

import math
from typing import Callable

import pandas as pd

from formulation_engine import _default_evaluator, _get_metrics, load_library
from services.forage_ndf import is_forage
from services.mineral_composition import calcular_minerais
from services.nutrient_profile import calcular_perfil


def analisar_dieta(lote, ingredientes, quantidades_mn: dict[str, float], *,
                   evaluate: Callable | None = None, scenario: tuple | None = None) -> dict:
    if not ingredientes:
        raise ValueError("Selecione pelo menos um ingrediente.")
    if scenario is None:
        import nasem_dairy as nd
        scenario = nd.demo("lactating_cow_test")
    _old_diet, animal, equations, infusion = scenario
    animal, equations = dict(animal), dict(equations)
    animal.update(lote.para_animal_nasem())
    # Mesmo mapeamento validado usado pelo formulador.
    from services.breed import AVISO_RACA_GENERICA, utiliza_raca_generica
    generic_breed = utiliza_raca_generica(lote.raca)
    catalog = load_library().set_index("Fd_Name")
    rows, total_dm, cost = [], 0.0, 0.0
    ndf_mass, starch_mass, forage_ndf_mass = 0.0, 0.0, 0.0
    ndf_ok, starch_ok, forage_ok = True, True, True
    for ing in ingredientes:
        if ing.nome_original not in catalog.index:
            raise ValueError(f"Ingrediente fora da biblioteca NASEM: {ing.nome_original}")
        qty = float(quantidades_mn.get(ing.uid, 0.0))
        if not math.isfinite(qty) or qty < 0:
            raise ValueError(f"Quantidade inválida para {ing.nome_pt}.")
        if qty == 0:
            continue
        dm_pct = float(catalog.loc[ing.nome_original, "Fd_DM"])
        if not 0 < dm_pct <= 100:
            raise ValueError(f"Matéria seca inválida: {ing.nome_pt}.")
        kg_dm = qty * dm_pct / 100
        price = ing.preco_mn_brl_kg
        if price is None or not math.isfinite(float(price)) or float(price) <= 0:
            raise ValueError(f"Informe preço positivo para {ing.nome_pt}.")
        item_cost = qty * float(price)
        rows.append({"ingredient": ing.nome_original, "name": ing.nome_pt, "uid": ing.uid,
                     "kg_dm": kg_dm, "kg_mn": qty, "cost_brl": item_cost, "price_brl_kg_mn": float(price)})
        total_dm += kg_dm
        cost += item_cost
        for col, name in (("Fd_NDF", "ndf"), ("Fd_St", "starch")):
            val = catalog.loc[ing.nome_original, col]
            valid = pd.notna(val) and math.isfinite(float(val))
            if name == "ndf":
                ndf_ok &= bool(valid)
                if valid:
                    ndf_mass += kg_dm * float(val) / 100
            else:
                starch_ok &= bool(valid)
                if valid:
                    starch_mass += kg_dm * float(val) / 100
        feed_row = catalog.loc[ing.nome_original]
        forage = is_forage(ing.nome_original,
                           feed_type=feed_row.get("Fd_Type"),
                           feed_category=feed_row.get("Fd_Category"))
        if forage is None:
            forage_ok = False
        elif forage:
            val = pd.to_numeric(feed_row["Fd_NDF"], errors="coerce")
            if pd.isna(val) or not math.isfinite(float(val)) or not 0 <= float(val) <= 100:
                forage_ok = False
            else:
                forage_ndf_mass += kg_dm * float(val) / 100
        # Concentrados/subprodutos classificados não contribuem à fNDF.
        # A ausência de Fd_NDF deles pode impedir FDN total, mas não fNDF.
    if total_dm <= 0:
        raise ValueError("A dieta deve ter quantidade positiva de pelo menos um ingrediente.")
    diet = pd.DataFrame({"Feedstuff": [r["ingredient"] for r in rows],
                         "kg_user": [r["kg_dm"] for r in rows]})
    animal["Trg_Dt_DMIn"] = total_dm
    equations["DMIn_eqn"] = 0
    output = (evaluate or _default_evaluator)(diet, animal, equations, infusion)
    metrics = _get_metrics(output)
    from services.nasem_requirements import ler_balancos
    balancos = ler_balancos(output)
    for r in rows:
        r["pct_dm"] = 100 * r["kg_dm"] / total_dm
    minerais = calcular_minerais(catalog.reset_index(), {r['ingredient']: r['kg_dm'] for r in rows})
    perfil_adicional = calcular_perfil(catalog.reset_index(), {r["ingredient"]: r["kg_dm"] for r in rows})
    alerts = ([AVISO_RACA_GENERICA] if generic_breed else []) + ["Dieta informada pelo usuário: nenhuma quantidade foi otimizada.",
              "MS total derivada das quantidades; não foi estimada como ingestão espontânea.",
              "Fibra fisicamente efetiva, vitaminas e limites nutricionais de inclusão não foram verificados. "
              "Balanços minerais absorvidos (quando disponíveis) são verificações parciais."]
    for mineral in balancos.values():
        if mineral["status"] == "viola":
            alerts.append(f"{mineral['label']}: ingerido {mineral['intake']:.2f} g/dia, "
                          f"exigido {mineral['requirement']:.2f} g/dia. Abaixo da exigência NASEM.")
    from services.mineral_upper_review import revisar_superiores_minerais
    alerts.extend(revisar_superiores_minerais(
        dieta_ms=((r["ingredient"], r["kg_dm"]) for r in rows),
        total_ms_kg=total_dm, balancos=balancos,
    ))
    max_row = max(rows, key=lambda r: r["pct_dm"])
    if max_row["pct_dm"] >= 70:
        alerts.append(f"Ingrediente dominante: {max_row['name']} ({max_row['pct_dm']:.1f}% da MS). Gatilho informativo de 70%, não limite nutricional.")
    if metrics["An_MEIn"] / metrics["Trg_MEuse"] >= 1.20:
        alerts.append("Energia calculada acima de 120% da exigência: alerta descritivo, não diagnóstico de excesso prejudicial.")
    return {"items": rows, "total_dm_kg": total_dm, "total_mn_kg": sum(r["kg_mn"] for r in rows),
            "cost_cow_day": cost, "cost_herd_day": cost * lote.n_vacas,
            "me_in": metrics["An_MEIn"], "me_req": metrics["Trg_MEuse"],
            "mp_in": metrics["An_MPIn_g"], "mp_req": metrics["An_MPuse_g_Trg"],
            "ndf_pct_dm": 100 * ndf_mass / total_dm if ndf_ok else None,
            "starch_pct_dm": 100 * starch_mass / total_dm if starch_ok else None,
            "forage_ndf_pct_dm": 100 * forage_ndf_mass / total_dm if forage_ok else None,
            "minerals": minerais, "additional_nutrients": perfil_adicional, "absorbed_mineral_checks": balancos, "alerts": alerts, "source": "NASEM 2021 via nasem_dairy; composição do catálogo NASEM",
            "validated_complete": False}
