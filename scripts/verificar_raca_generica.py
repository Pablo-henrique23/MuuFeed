"""Confere o caminho An_Breed='Other' no nasem_dairy REAL instalado localmente.

Não altera a aplicação nem fornece validação clínica de outras raças.
Saída != 0 significa que o modo genérico NÃO foi confirmado nesta instalação.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.breed import RACA_GENERICA, para_raca_nasem

OBRIGATORIAS = (
    "An_MEIn", "Trg_MEuse", "An_MPIn_g", "An_MPuse_g_Trg",
    "Abs_CaIn", "An_Ca_req", "Abs_PIn", "An_P_req",
    "Abs_MgIn", "An_Mg_req", "Abs_NaIn", "An_Na_req",
    "Abs_ClIn", "An_Cl_req", "Abs_KIn", "An_K_req",
)


def ler_finitos(output):
    dados = {}
    for name in OBRIGATORIAS:
        try:
            value = float(output.get_value(name))
            dados[name] = value if math.isfinite(value) else None
        except (AttributeError, TypeError, ValueError, KeyError, OverflowError):
            dados[name] = None
    return dados


def main():
    import nasem_dairy as nd
    try:
        dieta, animal_base, equacoes, infusao = nd.demo("lactating_cow_test")
    except Exception as exc:
        print(f"ERRO ao carregar exemplo: {type(exc).__name__}: {exc}")
        return 2
    resultados = {}
    for label in ("Holandesa", "Jersey", RACA_GENERICA):
        breed = para_raca_nasem(label)
        animal = dict(animal_base)
        animal["An_Breed"] = breed
        try:
            out = nd.nasem(user_diet=dieta.copy(), animal_input=animal,
                           equation_selection=dict(equacoes), infusion_input=dict(infusao))
            data = ler_finitos(out)
        except Exception as exc:
            print(f"FALHA: {label} (An_Breed={breed}) -> {type(exc).__name__}: {exc}")
            if breed == "Other":
                print("Modo genérico indisponível neste NASEM. Não o utilize para formular.")
            return 2
        missing = [n for n, v in data.items() if v is None]
        if missing:
            print(f"FALHA: {label} (An_Breed={breed}): sem resultados numéricos para: {missing}")
            return 2
        resultados[breed] = data
        print(f"OK: {label} -> An_Breed={breed}; ME={data['An_MEIn']:.2f} Mcal/dia; "
              f"Ca absorvido={data['Abs_CaIn']:.2f} g/dia; "
              f"exigência Ca={data['An_Ca_req']:.2f} g/dia")
    iguais_h = sum(resultados['Other'][k] == resultados['Holstein'][k] for k in OBRIGATORIAS)
    iguais_j = sum(resultados['Other'][k] == resultados['Jersey'][k] for k in OBRIGATORIAS)
    print(f"Diagnóstico: Other coincide em {iguais_h}/{len(OBRIGATORIAS)} métricas com Holstein "
          f"e {iguais_j}/{len(OBRIGATORIAS)} com Jersey neste exemplo.")
    print("OK — ramo Other calculou todos os indicadores essenciais na instalação atual.")
    print("ATENÇÃO: isto verifica execução técnica, NÃO adequação científica para uma raça específica.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
