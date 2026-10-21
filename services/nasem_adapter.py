"""Adaptador entre os contratos Streamlit do MuuFeed e o motor experimental.

Ativação: MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
Requer `req.opcoes.consumo_ms_kg_dia` informado pelo usuário, em kg MS/vaca/dia.
FDN e amido podem ser limitados pelo usuário, mas a candidata permanece experimental.
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
        for campo, rotulo in (("min_ndf_pct_dm", "FDN mínima"), ("max_starch_pct_dm", "Amido máximo")):
            valor = getattr(req.opcoes, campo, None)
            if valor is not None:
                try:
                    n = float(valor)
                except (TypeError, ValueError):
                    return False, f"{rotulo} deve ser numérico."
                if not math.isfinite(n) or not 0 <= n <= 100:
                    return False, f"{rotulo} deve estar entre 0 e 100% da MS."
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
            min_ndf_pct_dm=req.opcoes.min_ndf_pct_dm,
            max_starch_pct_dm=req.opcoes.max_starch_pct_dm,
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
        comp = result.get("nutrient_composition") or {}
        for key, label, amount_key, limit_key in (
            ("fdn", "Fibra em detergente neutro (FDN)", "ndf_pct_dm", "ndf_min_pct_dm"),
            ("amido", "Amido", "starch_pct_dm", "starch_max_pct_dm"),
        ):
            value, limit = comp.get(amount_key), comp.get(limit_key)
            if value is not None and math.isfinite(float(value)):
                # Nenhum limite: valor apenas informativo, nunca "atende".
                status = "informativo" if limit is None else (
                    "atende" if (float(value) >= float(limit) - 1e-6 if key == "fdn"
                                else float(value) <= float(limit) + 1e-6) else "viola")
                indicators.append(Indicador(key, label, "% da MS", float(value),
                                            None if limit is None else float(limit), status))
        checked = list(result.get("constraints_checked", []))
        checked_labels = {"total_ms": "MS", "me": "ME", "mp": "MP", "fdn": "FDN", "amido": "amido"}
        verified = ", ".join(checked_labels[k] for k in checked if k in checked_labels)
        rules = [RegraAcionada(r["id"], r["explanation"], r.get("source") or
                               "NASEM 2021 via nasem_dairy") for r in result.get("activated_rules", [])]
        return ResultadoFormulacao(
            status="candidata_experimental",
            mensagem=f"CANDIDATA EXPERIMENTAL: restrições verificadas: {verified or 'nenhuma'}; não é dieta nutricionalmente completa.",
            itens=items, custo_vaca_dia=result["cost_brl_cow_day"],
            indicadores=indicators,
            regras=rules,
            restricoes=([Restricao(k, k.upper(), "atendida") for k in checked] +
                        [Restricao(k, k.upper(), "nao_avaliada") for k in unseen]),
            nao_avaliadas=unseen,
            avisos=warnings,
            modelo_referencia=result.get("model", "NASEM 2021"),
        )
