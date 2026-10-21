"""Adaptador entre os contratos Streamlit do MuuFeed e o motor experimental.

Ativação: MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
Requer `req.opcoes.consumo_ms_kg_dia` informado pelo usuário, em kg MS/vaca/dia.
Enquanto fibras, amido e minerais não forem incorporados, o resultado é
explicitamente uma CANDIDATA EXPERIMENTAL.
"""
from __future__ import annotations

import math

from models import (Indicador, ItemDieta, RegraAcionada, Restricao,
                    ResultadoFormulacao)
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet


class NasemFormulador:
    nome = "NASEM 2021 — experimental"

    def verificar_escopo(self, req):
        errors, _warnings = req.lote.validar()
        if errors:
            return False, "; ".join(errors)
        if req.lote.estado != "Lactating Cow":
            return False, "O formulador experimental suporta apenas vacas em lactação."
        if len(req.ingredientes) < 2:
            return False, "Selecione pelo menos dois ingredientes disponíveis."
        dmi = getattr(req.opcoes, "consumo_ms_kg_dia", None)
        if dmi is None:
            return False, ("Informe o consumo diário estimado de matéria seca "
                           "(kg MS/vaca/dia). Este motor ainda não estima automaticamente o consumo.")
        try:
            value = float(dmi)
        except (TypeError, ValueError):
            return False, "O consumo de matéria seca deve ser numérico."
        if not math.isfinite(value) or value <= 0:
            return False, "O consumo de matéria seca deve ser maior que zero."
        if any(i.preco_mn_brl_kg is None or i.preco_mn_brl_kg <= 0 or
               not 0 < i.ms_pct <= 100 for i in req.ingredientes):
            return False, "Todos os ingredientes devem ter preço positivo e MS válida."
        return True, ""

    def formular(self, req):
        import nasem_dairy as nd
        _, animal, equations, infusion = nd.demo("lactating_cow_test")
        # O exemplo é SOMENTE um template para os parâmetros que o lote ainda
        # não coleta; a interface deve mostrar todas as hipóteses remanescentes.
        overrides = req.lote.para_animal_nasem()
        animal.update(overrides)
        breed_names = {"holandesa": "Holstein", "holstein": "Holstein",
                       "jersey": "Jersey"}
        breed = breed_names.get(req.lote.raca.strip().lower())
        if breed:
            animal["An_Breed"] = breed
        elif req.lote.raca.strip():
            # Não assumir breed default do cenário original como raça real.
            animal["An_Breed"] = "Other"
        total_dm = float(req.opcoes.consumo_ms_kg_dia)
        animal["Trg_Dt_DMIn"] = total_dm
        equations["DMIn_eqn"] = 0
        choices = []
        for i in req.ingredientes:
            low, high = i.limites_ms()
            choices.append(FeedChoice(
                name=i.nome_original, price_as_fed_brl_kg=float(i.preco_mn_brl_kg),
                dry_matter_pct=float(i.ms_pct),
                minimum_dm_kg=0.0 if low is None else low,
                maximum_dm_kg=high,
            ))
        result = formulate_diet(FormulationRequest(
            feeds=tuple(choices), animal=animal, equations=equations,
            infusion=infusion, total_dm_kg=total_dm, herd_size=req.lote.n_vacas,
            max_iterations=80, restarts=2,
        ))
        warnings = list(result.get("warnings", []))
        warnings += ["Cenário NASEM utiliza parâmetros complementares do exemplo oficial; "
                     "ainda é necessário explicitar/validar esses parâmetros na interface."]
        if any(i.origem_preco == "ilustrativo" for i in req.ingredientes):
            warnings += ["Há preços ilustrativos na composição; custos não representam cotação atual."]
        warnings += result.get("solver_messages", [])
        unseen = list(result.get("constraints_not_checked", []))
        if result["status"] != "candidata_experimental":
            return ResultadoFormulacao(
                status="inviavel", mensagem=("Nenhuma dieta candidata atendeu às restrições "
                     "experimentais. Isso não comprova inviabilidade nutricional."),
                nao_avaliadas=unseen, avisos=warnings,
                modelo_referencia=result.get("model", "NASEM 2021"),
            )
        by_name = {i.nome_original: i for i in req.ingredientes}
        items = []
        for row in result["diet"]:
            ing = by_name[row["ingredient"]]
            items.append(ItemDieta(ing.uid, ing.nome_pt, row["kg_dm_cow_day"],
                                   row["kg_as_fed_cow_day"], row["cost_brl_cow_day"],
                                   row.get("price_brl_kg_as_fed")))
        nutrition = result["nutrition"]
        indicators = [
            Indicador("me", "Energia metabolizável", "Mcal/dia",
                      nutrition["me_intake_mcal_day"], nutrition["me_requirement_mcal_day"], "atende"),
            Indicador("mp", "Proteína metabolizável", "g/dia",
                      nutrition["mp_intake_g_day"], nutrition["mp_requirement_g_day"], "atende"),
        ]
        checked = list(result.get("constraints_checked", []))
        return ResultadoFormulacao(
            status="candidata_experimental",
            mensagem="CANDIDATA EXPERIMENTAL: satisfaz apenas MS, ME e MP verificadas; não é dieta completa.",
            itens=items, custo_vaca_dia=result["cost_brl_cow_day"],
            indicadores=indicators,
            regras=[RegraAcionada(r["id"], r["explanation"], "NASEM 2021 via nasem_dairy")
                    for r in result.get("activated_rules", [])],
            restricoes=([Restricao(k, k.upper(), "atendida") for k in checked] +
                        [Restricao(k, k.upper(), "nao_avaliada") for k in unseen]),
            nao_avaliadas=unseen,
            avisos=warnings,
            modelo_referencia=result.get("model", "NASEM 2021"),
        )
