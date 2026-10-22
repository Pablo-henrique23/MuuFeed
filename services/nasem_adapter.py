"""Adaptador entre os contratos Streamlit do MuuFeed e o motor experimental.

Ativação: MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
Recebe `req.opcoes.consumo_ms_kg_dia` informado ou estimado explicitamente na interface, em kg MS/vaca/dia.
FDN e amido podem ser limitados pelo usuário, mas a candidata permanece experimental.
"""
from __future__ import annotations

import math

from models import (Indicador, ItemDieta, RegraAcionada, Restricao,
                    ResultadoFormulacao)
from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
from services.breed import para_raca_nasem, utiliza_raca_generica, AVISO_RACA_GENERICA
from services.feed_science import eh_so_bezerro, limite_explicito_obrigatorio


class NasemFormulador:
    nome = "NASEM 2021 — experimental"

    def verificar_escopo(self, req):
        errors, _warnings = req.lote.validar()
        if errors:
            return False, "; ".join(errors)
        if req.lote.estado != "Lactating Cow":
            return False, "O formulador experimental suporta apenas vacas em lactação."
        try:
            para_raca_nasem(req.lote.raca)
        except ValueError as exc:
            return False, str(exc)
        if len(req.ingredientes) < 2:
            return False, "Selecione pelo menos dois ingredientes disponíveis."
        dmi = getattr(req.opcoes, "consumo_ms_kg_dia", None)
        if dmi is None:
            return False, ("Informe o consumo de MS ou escolha a opção de estimativa NRC (2001) "
                           "na página Formular dieta.")
        try:
            value = float(dmi)
        except (TypeError, ValueError):
            return False, "O consumo de matéria seca deve ser numérico."
        if not math.isfinite(value) or value <= 0:
            return False, "O consumo de matéria seca deve ser maior que zero."
        if any(i.preco_mn_brl_kg is None or i.preco_mn_brl_kg <= 0 or
               not 0 < i.ms_pct <= 100 for i in req.ingredientes):
            return False, "Todos os ingredientes devem ter preço positivo e MS válida."
        for campo, rotulo in (("min_ndf_pct_dm", "FDN mínima"), ("max_starch_pct_dm", "Amido máximo"), ("min_forage_ndf_pct_dm", "FDN de forragens mínima")):
            valor = getattr(req.opcoes, campo, None)
            if valor is not None:
                try:
                    n = float(valor)
                except (TypeError, ValueError):
                    return False, f"{rotulo} deve ser numérico."
                if not math.isfinite(n) or not 0 <= n <= 100:
                    return False, f"{rotulo} deve estar entre 0 e 100% da MS."
        if type(getattr(req.opcoes, "require_absorbed_ca_p", False)) is not bool:
            return False, "A verificação de cálcio/fósforo deve ser ativada ou desativada."
        if type(getattr(req.opcoes, "require_absorbed_na", False)) is not bool:
            return False, "A restrição de sódio deve ser ativada ou desativada."
        if type(getattr(req.opcoes, "require_absorbed_mg_cl_k", False)) is not bool:
            return False, "A restrição de Mg/Cl/K deve ser ativada ou desativada."
        # O catálogo NASEM inclui premixes, gorduras concentradas, aditivos e
        # NNP; eles não podem entrar ilimitadamente na otimização. O teto
        # operacional continua sendo do usuário / especialista, não recomendado
        # automaticamente pelo MuuFeed.
        try:
            from services.feed_catalog import carregar_biblioteca_bruta
            bruta = carregar_biblioteca_bruta()
            categorias = dict(zip(bruta["Fd_Name"], bruta["Fd_Category"]))
        except (ImportError, ModuleNotFoundError):
            # Testes unitários sem nasem_dairy: ainda exigir teto para NNP/sais
            # conhecidos pelo identificador; integração real tem catálogo.
            categorias = {}
        for ing in req.ingredientes:
            if eh_so_bezerro(ing.nome_original):
                return False, (f"{ing.nome_pt} é identificado na biblioteca como ração "
                               "exclusiva para bezerros, não elegível para vacas em lactação.")
            cat = categorias.get(ing.nome_original)
            if limite_explicito_obrigatorio(ing.nome_original, cat) and ing.max_kg_mn is None:
                return False, (f"Defina o máximo (kg MN/vaca/dia) para {ing.nome_pt} "
                               "na tela Ingredientes e preços. Trata-se de ingrediente "
                               "concentrado/aditivo que requer limite operacional "
                               "definido por profissional; o MuuFeed não define dose segura.")
        origem = getattr(req.opcoes, "consumo_ms_origem", "informado")
        if origem not in ("informado", "estimado_nrc2001"):
            return False, "Origem do consumo MS inválida."
        teto = getattr(req.opcoes, "max_share_ingredient_pct_dm", None)
        if teto is not None:
            try:
                teto = float(teto)
            except (TypeError, ValueError):
                return False, "O teto de participação deve ser numérico."
            if not math.isfinite(teto) or not 0 < teto <= 100:
                return False, "O teto operacional de participação deve estar entre 0 e 100% da MS."
            if teto * len(req.ingredientes) < 100 - 1e-6:
                return False, ("O teto informado não permite distribuir 100% da MS entre os "
                               "ingredientes disponíveis. Aumente o teto ou adicione alimentos.")
        return True, ""

    def formular(self, req):
        import nasem_dairy as nd
        _, animal, equations, infusion = nd.demo("lactating_cow_test")
        # O exemplo é SOMENTE um template para os parâmetros que o lote ainda
        # não coleta; a interface deve mostrar todas as hipóteses remanescentes.
        overrides = req.lote.para_animal_nasem()
        animal.update(overrides)
        # Lote.para_animal_nasem() já fornece An_Breed com mapeamento validado.
        assert animal["An_Breed"] == para_raca_nasem(req.lote.raca)
        total_dm = float(req.opcoes.consumo_ms_kg_dia)
        animal["Trg_Dt_DMIn"] = total_dm
        equations["DMIn_eqn"] = 0
        choices = []
        teto = getattr(req.opcoes, "max_share_ingredient_pct_dm", None)
        for i in req.ingredientes:
            low, high = i.limites_ms()
            if teto is not None:
                limite_ms = total_dm * float(teto) / 100.0
                high = limite_ms if high is None else min(high, limite_ms)
            choices.append(FeedChoice(
                name=i.nome_original, price_as_fed_brl_kg=float(i.preco_mn_brl_kg),
                dry_matter_pct=float(i.ms_pct),
                minimum_dm_kg=0.0 if low is None else low,
                maximum_dm_kg=high,
            ))
        result = formulate_diet(FormulationRequest(
            feeds=tuple(choices), animal=animal, equations=equations,
            infusion=infusion, total_dm_kg=total_dm, herd_size=req.lote.n_vacas,
            max_iterations=100, restarts=4,
            min_ndf_pct_dm=req.opcoes.min_ndf_pct_dm,
            max_starch_pct_dm=req.opcoes.max_starch_pct_dm,
            min_forage_ndf_pct_dm=req.opcoes.min_forage_ndf_pct_dm,
            require_absorbed_ca_p=getattr(req.opcoes, "require_absorbed_ca_p", False),
            require_absorbed_na=getattr(req.opcoes, "require_absorbed_na", False),
            require_absorbed_mg_cl_k=getattr(req.opcoes, "require_absorbed_mg_cl_k", False),
        ))
        warnings = list(result.get("warnings", []))
        if utiliza_raca_generica(req.lote.raca):
            warnings.insert(0, AVISO_RACA_GENERICA)
        # O motor recebe CMS fixo; quem o estimou foi a etapa anterior, não o NASEM.
        if getattr(req.opcoes, "consumo_ms_origem", "informado") == "estimado_nrc2001":
            warnings = [w for w in warnings if "Consumo total de matéria seca foi fornecido" not in w]
            warnings.append(
                f"Consumo de MS adotado: {total_dm:.2f} kg/vaca/dia, estimado pela equação NRC (2001) "
                "a partir dos dados do lote, não medido nem previsto pelo NASEM. "
                "A estimativa afeta quantidades e custo da formulação."
            )
        if teto is not None:
            warnings.append(
                f"Teto operacional informado: nenhum ingrediente pode exceder {float(teto):.1f}% da matéria seca. "
                "Controle de participação, não limite nutricional seguro nem garantia de dieta equilibrada."
            )
        warnings += ["Cenário NASEM utiliza parâmetros complementares do exemplo oficial; "
                     "ainda é necessário explicitar/validar esses parâmetros na interface."]
        if any(i.origem_preco == "ilustrativo" for i in req.ingredientes):
            warnings += ["Há preços ilustrativos na composição; custos não representam cotação atual."]
        warnings += result.get("solver_messages", [])
        warnings += result.get("descriptive_alerts", [])
        diagnostics = result.get("solver_diagnostics", {})
        if diagnostics:
            warnings.append(
                f"Diagnóstico SLSQP: {diagnostics.get('converged_attempts', 0)}/"
                f"{diagnostics.get('attempts_count', 0)} tentativas convergiram; "
                f"{diagnostics.get('validated_candidates', 0)} candidatas passaram na verificação. "
                "O ótimo global não é garantido."
            )
            if diagnostics.get("best_improvement_vs_lowest_initial_brl") is not None:
                warnings.append(
                    f"Comparação de custos: melhor ponto inicial R$ "
                    f"{diagnostics['lowest_initial_cost_brl_cow_day']:.2f}; "
                    f"melhor candidata R$ {diagnostics['best_cost_brl_cow_day']:.2f} por vaca/dia. "
                    "Isso não prova ótimo global nem qualidade nutricional completa."
                )
        unseen = list(result.get("constraints_not_checked", []))
        if result["status"] != "candidata_experimental":
            if diagnostics.get("diagnostic_note"):
                warnings.append(diagnostics["diagnostic_note"])
            gaps = diagnostics.get("closest_candidate_gaps") or {}
            names_gap = {"total_dm_kg": "diferença MS (kg)", "me_mcal_day": "déficit ME (Mcal/dia)",
                         "mp_g_day": "déficit MP (g/dia)", "na_abs_g_day": "déficit sódio absorvido (g/dia)", "ndf_pct_dm": "déficit FDN (p.p.)",
                         "starch_pct_dm": "excesso amido (p.p.)", "ca_abs_g_day": "déficit cálcio absorvido (g/dia)", "p_abs_g_day": "déficit fósforo absorvido (g/dia)", "forage_ndf_pct_dm": "déficit FDN de forragens (p.p.)", "mg_abs_g_day": "déficit magnésio absorvido (g/dia)", "cl_abs_g_day": "déficit cloro absorvido (g/dia)", "k_abs_g_day": "déficit potássio absorvido (g/dia)", "bounds_dm_kg": "violação de limite (kg MS)"}
            for key, value in gaps.items():
                if float(value) > 1e-5:
                    warnings.append(f"Melhor tentativa avaliada — {names_gap.get(key, key)}: {value:.3f}.")
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
        # Triagem conservadora: não chamar razão Cl/exigência de limite de toxicidade.
        from services.mineral_upper_review import revisar_superiores_minerais
        comp_triagem = result.get("nutrient_composition") or {}
        warnings.extend(revisar_superiores_minerais(
            dieta_ms=((item["ingredient"], float(item["kg_dm_cow_day"])) for item in result["diet"]),
            total_ms_kg=total_dm,
            balancos=comp_triagem.get("absorbed_mineral_checks"),
        ))
        nutrition = result["nutrition"]
        indicators = [
            Indicador("me", "Energia metabolizável", "Mcal/dia",
                      nutrition["me_intake_mcal_day"], nutrition["me_requirement_mcal_day"], "atende"),
            Indicador("mp", "Proteína metabolizável", "g/dia",
                      nutrition["mp_intake_g_day"], nutrition["mp_requirement_g_day"], "atende"),
        ]
        comp = result.get("nutrient_composition") or {}
        deficits_minerais = [
            f"{bal['label']}: {bal['intake']:.2f} de {bal['requirement']:.2f} g/dia"
            for bal in (comp.get("absorbed_mineral_checks") or {}).values()
            if bal.get("status") == "viola"
            and bal.get("intake") is not None and bal.get("requirement") is not None
        ]
        if deficits_minerais:
            warnings.append("Atenção: déficits minerais observados pelo NASEM (alguns podem não "
                            "ser restrições da otimização): " + "; ".join(deficits_minerais) + ". "
                            "Não interpretar a dieta como nutricionalmente adequada.")
        for key, label, amount_key, limit_key in (
            ("fdn", "Fibra em detergente neutro (FDN)", "ndf_pct_dm", "ndf_min_pct_dm"),
            ("amido", "Amido", "starch_pct_dm", "starch_max_pct_dm"),
            ("fdn_forragens", "FDN proveniente de forragens", "forage_ndf_pct_dm", "forage_ndf_min_pct_dm"),
        ):
            value, limit = comp.get(amount_key), comp.get(limit_key)
            if value is not None and math.isfinite(float(value)):
                # Nenhum limite: valor apenas informativo, nunca "atende".
                status = "informativo" if limit is None else (
                    "atende" if (float(value) >= float(limit) - 1e-6 if key in ("fdn", "fdn_forragens")
                                else float(value) <= float(limit) + 1e-6) else "viola")
                indicators.append(Indicador(key, label, "% da MS", float(value),
                                            None if limit is None else float(limit), status))
        for chave, rotulo, pct_key, g_key in (
            ("calcio", "Cálcio total", "ca_pct_dm", "ca_g_day"),
            ("fosforo", "Fósforo total", "p_pct_dm", "p_g_day"),
        ):
            # Composição bruta: não presumir biodisponibilidade nem exigência.
            valor_pct, valor_g = comp.get(pct_key), comp.get(g_key)
            if valor_pct is not None and math.isfinite(float(valor_pct)):
                indicators.append(Indicador(chave, rotulo, "% da MS", float(valor_pct), None, "informativo"))
            if valor_g is not None and math.isfinite(float(valor_g)):
                indicators.append(Indicador(chave + "_g", rotulo + " ingerido", "g/dia", float(valor_g), None, "informativo"))
        # Balanços absorvidos calculados pelo próprio NASEM. Podem ser exibidos sem
        # serem impostos na otimização; nesse caso uma violação é um ALERTA real.
        for chave, bal in (comp.get("absorbed_mineral_checks") or {}).items():
            if bal.get("status") != "nao_avaliado" and bal.get("intake") is not None:
                indicators.append(Indicador(chave, bal["label"], "g/dia",
                                             bal["intake"], bal["requirement"], bal["status"]))
        # Composição adicional calculada sobre a MS, sem exigência/limite nutricional.
        for chave, perfil in (comp.get("additional_nutrients") or {}).items():
            valor = perfil.get("pct_dm") if isinstance(perfil, dict) else None
            if valor is not None and math.isfinite(float(valor)):
                indicators.append(Indicador("perfil_" + chave, perfil["label"],
                                             "% da MS", float(valor), None, "informativo"))
        checked = list(result.get("constraints_checked", []))
        checked_labels = {"total_ms": "MS", "me": "ME", "mp": "MP", "fdn": "FDN", "amido": "amido", "fdn_forragens": "FDN de forragens", "calcio_absorvido": "Ca absorvido", "fosforo_absorvido": "P absorvido", "sodio_absorvido": "Na absorvido"}
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
