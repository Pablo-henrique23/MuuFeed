
    
  
"""Teste exploratorio da integracao NASEM 2021; nao formula dietas."""
import copy
import time
import math
import nasem_dairy as nd


def extract(output, key):
    value = output.get_value(key)
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise AssertionError(f"Saida nao numerica/finita: {key}={value!r}")
    return float(value)


def evaluate(diet, animal, equations, infusion):
    start = time.perf_counter()
    result = nd.nasem(
        user_diet=diet,
        animal_input=animal,
        equation_selection=equations,
        infusion_input=infusion,
    )
    return result, time.perf_counter() - start


def main():
    diet, animal, equations, infusion = nd.demo("lactating_cow_test")
    print("TIPOS DOS DADOS:", type(diet).__name__, type(animal).__name__)
    print("COLUNAS DA DIETA:", list(diet.columns))
    print("INGREDIENTES (AMOSTRA):")
    print(diet.head(3).to_string(index=False))
    print("CHAVES ANIMAL:", sorted(animal.keys()))
    print("EQUACOES:", equations)

    output, elapsed = evaluate(diet, animal, equations, infusion)
    print(f"\nAVALIACAO 1: {elapsed:.3f}s")
    keys = [
        "An_MEIn", "Trg_MEuse", "An_MPIn_g", "An_MPuse_g_Trg",
        "Mlk_Prod_NEalow", "Mlk_Prod_MPalow",
    ]
    values = {key: extract(output, key) for key in keys}
    for key, value in values.items():
        print(f"{key} = {value:.6f}")

    output2, elapsed2 = evaluate(diet.copy(deep=True), copy.deepcopy(animal), copy.deepcopy(equations), copy.deepcopy(infusion))
    print(f"\nAVALIACAO 2: {elapsed2:.3f}s")
    for key, value in values.items():
        other = extract(output2, key)
        assert math.isclose(value, other, rel_tol=1e-10, abs_tol=1e-8), (key, value, other)
    print("PASSOU: resultados reproduziveis e finitos no cenario demo")
    print("ATENCAO: isto NAO valida requisitos, otimizacao, seguranca ou licenciamento.")


if __name__ == "__main__":
    main()


