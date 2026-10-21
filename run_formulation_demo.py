"""Executar no venv com nasem_dairy instalado: python run_formulation_demo.py

Usa SOMENTE ingredientes já presentes no cenário demo oficial. Os preços abaixo
são hipotéticos: substitua por preços levantados para uma formulação real.
A saída é EXPERIMENTAL e não pode ser usada para alimentação de animais.
"""
import json
import math

import nasem_dairy as nd

from formulation_engine import FeedChoice, FormulationRequest, formulate_diet, load_library


# R$/kg de matéria natural — VALORES HIPOTÉTICOS para testar o software.
EXAMPLE_PRICES_AS_FED = {
    "Alfalfa meal": 1.40,
    "Canola meal": 2.30,
    "Corn silage, typical": 0.35,
}


def main():
    diet, animal, equations, infusion = nd.demo("lactating_cow_test")
    lib = load_library()
    lib_name_col = "Fd_Name" if "Fd_Name" in lib.columns else "Feedstuff"
    diet_name_col = "Fd_Name" if "Fd_Name" in diet.columns else "Feedstuff"
    if "Fd_DM" not in lib.columns:
        raise RuntimeError("Biblioteca NASEM sem coluna Fd_DM; inspecione a versão instalada")
    if lib[lib_name_col].duplicated().any():
        raise RuntimeError("Biblioteca NASEM com nomes duplicados; precisamos de ID inequívoco")
    ingredients = lib.set_index(lib_name_col)
    names = diet[diet_name_col].tolist()
    selected = []
    for _, row in diet.iterrows():
        name = row[diet_name_col]
        if name not in EXAMPLE_PRICES_AS_FED:
            continue
        dm_pct = float(ingredients.loc[name, "Fd_DM"])
        if not math.isfinite(dm_pct) or not 0 < dm_pct <= 100:
            raise RuntimeError(f"MS inválida no catálogo para {name}: {dm_pct}")
        selected.append(FeedChoice(
            name=name,
            price_as_fed_brl_kg=EXAMPLE_PRICES_AS_FED[name],
            dry_matter_pct=dm_pct,
            initial_dm_kg=float(row["kg_user"]),
        ))
    if len(selected) != 3:
        raise RuntimeError(f"Esperados 3 ingredientes demo, encontrados: {[f.name for f in selected]}")
    # Consumo de matéria seca é controlado na prova de conceito (não predito).
    total = float(sum(f.initial_dm_kg for f in selected))
    animal["Trg_Dt_DMIn"] = total
    equations["DMIn_eqn"] = 0
    req = FormulationRequest(
        feeds=tuple(selected), animal=animal, equations=equations,
        infusion=infusion, total_dm_kg=total, herd_size=30,
        max_iterations=80, restarts=2,
    )
    print("PREÇOS HIPOTÉTICOS — NÃO USAR EM FAZENDA")
    output = formulate_diet(req)
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    if output["status"] != "candidata_experimental":
        raise SystemExit("Nenhuma candidata que satisfaça os critérios parciais foi encontrada")


if __name__ == "__main__":
    main()
