
    
  
"""MuuFeed: experimento de FORMULACAO (nao dieta completa para uso em fazenda).

Usa o cenario de demonstracao do nasem_dairy, otimiza quantidades de ate 3
ingredientes e avalia cada dieta candidata no NASEM 2021. O experimento
verifica apenas energia metabolizavel e proteina metabolizavel; limites
de fibra, amido, minerais e inclusao ainda precisam ser implementados.

Precos sao INDICES FICTICIOS por unidade de kg_user (nao R$/kg reais).
Nao usar as dietas para alimentar animais.
"""
import argparse
import copy
import math
from functools import lru_cache

import nasem_dairy as nd
import numpy as np
from scipy.optimize import minimize

METRICS = ("An_MEIn", "Trg_MEuse", "An_MPIn_g", "An_MPuse_g_Trg")


def read_metrics(result):
    values = tuple(float(result.get_value(k)) for k in METRICS)
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"NASEM retornou valor nao-finito: {values}")
    return values


def run(age_days=None, maxiter=30):
    diet, animal, equations, infusion = nd.demo("lactating_cow_test")
    if age_days is not None:
        animal["An_AgeDay"] = age_days
    # Usa consumo fornecido como cenario de controle; nao deixa a ingestao
    # estimada variar no decorrer desta prova de conceito.
    equations["DMIn_eqn"] = 0
    diet = diet.copy(deep=True)
    if "kg_user" not in diet.columns:
        raise RuntimeError(f"Coluna kg_user nao encontrada: {list(diet.columns)}")
    name_column = "Fd_Name" if "Fd_Name" in diet.columns else "Feedstuff" if "Feedstuff" in diet.columns else None
    if name_column is None:
        raise RuntimeError(f"Coluna de nome de ingrediente nao encontrada: {list(diet.columns)}")
    baseline = diet["kg_user"].to_numpy(dtype=float)
    if not np.all(np.isfinite(baseline)) or np.any(baseline < 0):
        raise ValueError("Dieta de referencia invalida")
    selected = np.argsort(baseline)[::-1][:3]
    selected = np.array([int(i) for i in selected if baseline[i] > 0], dtype=int)
    if len(selected) < 2:
        raise RuntimeError("A dieta demo precisa conter >=2 ingredientes positivos")

    # Somente para provar que a formulacao consegue encontrar outra mistura.
    # NAO sao precos de mercado nem recomendacoes.
    pseudo_prices = np.array([1.00, 1.40, 2.20][:len(selected)])
    x0 = baseline[selected].copy()
    # Faixa relativa +/- 20% e apenas exploratoria; nao um limite nutricional.
    bounds = [(max(0, float(v * .8)), float(v * 1.2)) for v in x0]

    @lru_cache(maxsize=2048)
    def evaluate_cached(key):
        quantities = np.array(key, dtype=float)
        candidate = diet.copy(deep=True)
        candidate.loc[candidate.index[selected], "kg_user"] = quantities
        result = nd.nasem(candidate, copy.deepcopy(animal), copy.deepcopy(equations), infusion_input=copy.deepcopy(infusion))
        return read_metrics(result)

    def evaluate(x):
        try:
            return evaluate_cached(tuple(float(v) for v in x))
        except (ValueError, ArithmeticError, OverflowError, ZeroDivisionError) as exc:
            raise RuntimeError(f"Falha avaliando candidata: {exc}") from exc

    initial = evaluate(x0)
    total_initial = float(x0.sum())
    def objective(x):
        return float(np.dot(pseudo_prices, x))

    def energy_slack(x):
        me_in, me_req, _, _ = evaluate(x)
        return me_in - me_req

    def protein_slack(x):
        _, _, mp_in, mp_req = evaluate(x)
        return (mp_in - mp_req) / 1000.0  # g/d -> kg/d (escalonamento)

    constraints = [
        {"type": "eq", "fun": lambda x: float(np.sum(x) - total_initial)},
        {"type": "ineq", "fun": energy_slack},
        {"type": "ineq", "fun": protein_slack},
    ]
    print("AVISO: FORMULADOR EXPERIMENTAL. Nao verifica fibra, amido, minerais nem todos os limites de inclusao.")
    print(f"Idade dias: {animal['An_AgeDay']}; ordem de lactacao (paridade): {animal['An_Parity_rl']}")
    print("Ingredientes modificaveis:")
    for idx, price in zip(selected, pseudo_prices):
        print(f"  {diet.iloc[idx][name_column]}: inicial={baseline[idx]:.4f} kg_user, indice de custo ficticio={price:.2f}")
    print("NASEM original ME / exigencia; MP / exigencia:", initial)
    if initial[0] < initial[1] or initial[2] < initial[3]:
        print("AVISO: dieta demo inicial nao satisfaz pelo menos uma das duas restricoes selecionadas.")

    solution = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                        options={"maxiter": maxiter, "ftol": 1e-7, "disp": False})
    print("\nOTIMIZADOR:", solution.message)
    print("Iteracoes:", solution.nit, "avaliacoes distintas do NASEM:", evaluate_cached.cache_info().misses)
    if not np.all(np.isfinite(solution.x)):
        print("SEM SOLUCAO: otimizador retornou quantidades invalidas")
        return
    final = evaluate(solution.x)
    sum_error = abs(float(solution.x.sum()) - total_initial)
    feasible = (sum_error < 1e-5 and final[0] + 1e-6 >= final[1] and final[2] + 1e-3 >= final[3]
                and all(lo - 1e-6 <= v <= hi + 1e-6 for v, (lo, hi) in zip(solution.x, bounds)))
    print("Custo inicial (indice, nao R$):", round(objective(x0), 5))
    print("Custo candidato (indice, nao R$):", round(objective(solution.x), 5))
    for idx, x in zip(selected, solution.x):
        print(f"  {diet.iloc[idx][name_column]}: {x:.4f} kg_user")
    print("ME ingerida/exigida (Mcal/d):", round(final[0], 4), "/", round(final[1], 4))
    print("MP ingerida/exigida (g/d):", round(final[2], 4), "/", round(final[3], 4))
    print("PASSOU nas DUAS restricoes experimentais?", feasible)
    print("Dieta nutricionalmente completa? NAO AVALIADA")
    if not solution.success or not feasible:
        print("NENHUMA FORMULACAO APROVADA: nao usar o candidato. Restricoes ou otimizacao nao satisfeitas.")
    else:
        print("CANDIDATA EXPERIMENTAL FORMULADA: nao usar em animais; outras restricoes nao verificadas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--idade-dias", type=int, default=None)
    parser.add_argument("--maxiter", type=int, default=30)
    args = parser.parse_args()
    if args.idade_dias is not None and args.idade_dias <= 0:
        parser.error("--idade-dias deve ser positivo")
    run(args.idade_dias, args.maxiter)


