"""MuuFeed — formulador experimental independente da interface.

NÃO produz uma dieta validada para alimentação animal. Atualmente impõe apenas:
consumo total de MS definido pelo usuário, energia metabolizável e proteína
metabolizável retornadas por NASEM. Limites individuais SOMENTE se informados
explicitamente pelo usuário, sem interpretá-los como limites nutricionais seguros.

Todas as quantidades internas são kg de MATÉRIA SECA por vaca/dia. Preço é
R$/kg de MATÉRIA NATURAL e convertido por fração de MS de cada ingrediente.

A função formula_diet aceita uma função `evaluate` injetável (para testes). Se
omitida, executa o pacote nasem_dairy offline. Não depende de Streamlit.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from functools import lru_cache
import math
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize


METRICS = ("An_MEIn", "Trg_MEuse", "An_MPIn_g", "An_MPuse_g_Trg")


@dataclass(frozen=True)
class FeedChoice:
    name: str  # identificação EXATA da biblioteca NASEM
    price_as_fed_brl_kg: float
    dry_matter_pct: float  # MS em %, da biblioteca ou medição documentada
    minimum_dm_kg: float = 0.0
    maximum_dm_kg: float | None = None  # máximo operacional informado, NÃO recomendação nutricional
    initial_dm_kg: float | None = None


@dataclass(frozen=True)
class FormulationRequest:
    feeds: tuple[FeedChoice, ...]
    animal: Mapping[str, Any]
    equations: Mapping[str, Any]
    total_dm_kg: float
    herd_size: int
    infusion: Mapping[str, Any] | None = None
    max_iterations: int = 100
    restarts: int = 2


def _valid_real(value: Any, what: str, *, positive: bool = False) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{what}: deve ser número") from exc
    if not math.isfinite(n) or (n <= 0 if positive else n < 0):
        raise ValueError(f"{what}: valor inválido")
    return n


def validate_request(req: FormulationRequest) -> None:
    if len(req.feeds) < 2:
        raise ValueError("Selecione pelo menos dois ingredientes")
    names = [f.name for f in req.feeds]
    if any(not isinstance(n, str) or not n.strip() for n in names) or len(set(names)) != len(names):
        raise ValueError("Ingredientes devem ter nomes únicos e não vazios")
    total = _valid_real(req.total_dm_kg, "Consumo total de MS", positive=True)
    if type(req.herd_size) is not int or req.herd_size <= 0:
        raise ValueError("Tamanho do lote deve ser inteiro positivo")
    if type(req.max_iterations) is not int or req.max_iterations < 1:
        raise ValueError("max_iterations inválido")
    if type(req.restarts) is not int or not 1 <= req.restarts <= 10:
        raise ValueError("restarts deve estar entre 1 e 10")
    min_total = 0.0
    max_total = 0.0
    for f in req.feeds:
        _valid_real(f.price_as_fed_brl_kg, f"Preço de {f.name}")
        dm = _valid_real(f.dry_matter_pct, f"MS de {f.name}", positive=True)
        if dm > 100:
            raise ValueError(f"MS de {f.name} não pode superar 100%")
        low = _valid_real(f.minimum_dm_kg, f"Mínimo de {f.name}")
        high = total if f.maximum_dm_kg is None else _valid_real(f.maximum_dm_kg, f"Máximo de {f.name}")
        if high < low:
            raise ValueError(f"Máximo inferior ao mínimo: {f.name}")
        if f.initial_dm_kg is not None:
            _valid_real(f.initial_dm_kg, f"Quantidade inicial de {f.name}")
        min_total += low
        max_total += high
    if min_total > total + 1e-8 or max_total < total - 1e-8:
        raise ValueError("Os limites operacionais não permitem atingir o consumo total de MS")
    if req.animal.get("An_StatePhys") != "Lactating Cow":
        raise ValueError("O protótipo suporta apenas vacas em lactação")
    age = _valid_real(req.animal.get("An_AgeDay"), "Idade em dias", positive=True)
    _valid_real(req.animal.get("An_BW"), "Peso vivo", positive=True)
    _valid_real(req.animal.get("An_LactDay"), "Dias em lactação")
    _valid_real(req.animal.get("An_Parity_rl"), "Paridade", positive=True)
    if "Trg_Dt_DMIn" in req.animal:
        dmi = _valid_real(req.animal["Trg_Dt_DMIn"], "Consumo MS do NASEM", positive=True)
        if abs(dmi - total) > 1e-6:
            raise ValueError("Trg_Dt_DMIn deve corresponder ao total_dm_kg")
    if req.equations.get("DMIn_eqn") != 0:
        raise ValueError("Este protótipo exige DMIn_eqn=0 (consumo de MS fixado)")


def load_library() -> pd.DataFrame:
    """Carrega catálogo original completo, sem alterar nem traduzir identificadores."""
    from importlib.resources import files
    path = files("nasem_dairy.data.feed_library").joinpath("NASEM_feed_library.csv")
    return pd.read_csv(path)


def _make_start(low: np.ndarray, high: np.ndarray, total: float, weights: np.ndarray) -> np.ndarray:
    """Distribui massa adicional até total respeitando bounds; ponto factível linear."""
    x = low.copy()
    remaining = total - float(x.sum())
    capacity = high - x
    weights = np.maximum(weights, 0.0)
    for _ in range(len(x) + 1):
        if remaining < 1e-9:
            break
        viable = capacity > 1e-10
        if not viable.any():
            break
        scores = np.where(viable, weights, 0.0)
        if scores.sum() <= 0:
            scores = viable.astype(float)
        allocation = np.minimum(capacity, remaining * scores / scores.sum())
        x += allocation
        capacity -= allocation
        remaining = total - float(x.sum())
    if abs(total - float(x.sum())) > 1e-6:
        raise ValueError("Não foi possível construir um ponto inicial dentro dos limites")
    return x


def _get_metrics(output: Any) -> dict[str, float]:
    vals = {key: float(output.get_value(key)) for key in METRICS}
    if not all(math.isfinite(v) for v in vals.values()):
        raise ValueError("NASEM retornou indicadores não finitos")
    if vals["Trg_MEuse"] <= 0 or vals["An_MPuse_g_Trg"] <= 0:
        raise ValueError("Exigências NASEM inválidas")
    return vals


def _default_evaluator(diet: pd.DataFrame, animal: dict, equations: dict, infusion: dict | None):
    import nasem_dairy as nd
    kwargs = {"user_diet": diet, "animal_input": animal, "equation_selection": equations}
    if infusion is not None:
        kwargs["infusion_input"] = infusion
    return nd.nasem(**kwargs)


def formulate_diet(
    request: FormulationRequest,
    *,
    evaluate: Callable[[pd.DataFrame, dict, dict, dict | None], Any] | None = None,
    catalog_names: set[str] | None = None,
) -> dict[str, Any]:
    """Minimiza custo exploratório sujeito APENAS a ME/MP e total de MS.

    catalog_names: IDs NASEM aceitos (para testes/injeção); omitido = CSV original.
    Não garante ótimo global: SLSQP é um método local.
    """
    validate_request(request)
    if catalog_names is None:
        lib = load_library()
        name_col = "Fd_Name" if "Fd_Name" in lib.columns else "Feedstuff"
        catalog_names = set(lib[name_col].dropna().astype(str))
    missing = [f.name for f in request.feeds if f.name not in catalog_names]
    if missing:
        raise ValueError(f"Ingredientes ausentes na biblioteca NASEM: {missing}")

    feeds = request.feeds
    n = len(feeds)
    names = [f.name for f in feeds]
    total = float(request.total_dm_kg)
    lower = np.array([f.minimum_dm_kg for f in feeds], dtype=float)
    upper = np.array([total if f.maximum_dm_kg is None else f.maximum_dm_kg for f in feeds], dtype=float)
    dm_frac = np.array([f.dry_matter_pct / 100 for f in feeds], dtype=float)
    prices = np.array([f.price_as_fed_brl_kg for f in feeds], dtype=float) / dm_frac
    bounds = list(zip(lower, upper))
    evaluator = evaluate or _default_evaluator
    animal = copy.deepcopy(dict(request.animal))
    animal["Trg_Dt_DMIn"] = total
    equations = copy.deepcopy(dict(request.equations))
    infusion = copy.deepcopy(dict(request.infusion)) if request.infusion is not None else None
    failures: list[str] = []

    @lru_cache(maxsize=20000)
    def eval_cached(key: tuple[float, ...]) -> tuple[float, float, float, float]:
        x = np.asarray(key, dtype=float)
        if not np.all(np.isfinite(x)) or np.any(x < -1e-6):
            raise ValueError("Quantidades não finitas/negativas")
        diet = pd.DataFrame({"Feedstuff": names, "kg_user": x})
        output = evaluator(diet, copy.deepcopy(animal), copy.deepcopy(equations), copy.deepcopy(infusion))
        m = _get_metrics(output)
        return tuple(m[k] for k in METRICS)

    def metrics(x: np.ndarray) -> tuple[float, float, float, float]:
        return eval_cached(tuple(float(t) for t in x))

    def constraints_energy(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[0] - v[1]) / max(1.0, v[1])

    def constraints_protein(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[2] - v[3]) / max(1.0, v[3])

    constraints = [
        {"type": "eq", "fun": lambda x: float(x.sum() - total)},
        {"type": "ineq", "fun": constraints_energy},
        {"type": "ineq", "fun": constraints_protein},
    ]
    starting = np.array([
        0.0 if f.initial_dm_kg is None else f.initial_dm_kg for f in feeds
    ], dtype=float)
    starts = [_make_start(lower, upper, total, starting)]
    if request.restarts > 1:
        # viés para ingredientes mais baratos; determinístico e reproduzível
        starts.append(_make_start(lower, upper, total, 1.0 / np.maximum(prices, 1e-7)))
    if request.restarts > 2:
        rng = np.random.default_rng(2026)
        for _ in range(request.restarts - 2):
            starts.append(_make_start(lower, upper, total, rng.uniform(0.01, 1.0, n)))

    def objective(x: np.ndarray) -> float:
        return float(np.dot(prices, x))

    candidates = []
    for x0 in starts:
        try:
            initial_m = metrics(x0)
            if not all(math.isfinite(v) for v in initial_m):
                raise ValueError("Indicadores iniciais inválidos")
            res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                           options={"maxiter": request.max_iterations, "ftol": 1e-9})
            if not res.success:
                failures.append(f"SLSQP: {res.message}")
            if np.all(np.isfinite(res.x)):
                candidates.append(np.asarray(res.x, dtype=float))
            candidates.append(x0)
        except Exception as exc:
            failures.append(f"Falha no cenário inicial: {type(exc).__name__}: {exc}")

    # Avaliação independente do retorno `success` do solver — nenhuma folga nutricional.
    valid: list[tuple[float, np.ndarray, tuple[float, ...]]] = []
    for x in candidates:
        try:
            m = metrics(x)
        except Exception as exc:
            failures.append(f"Candidata descartada: {exc}")
            continue
        if (abs(float(x.sum()) - total) <= 1e-5
                and np.all(x >= lower - 1e-6) and np.all(x <= upper + 1e-6)
                and m[0] >= m[1] and m[2] >= m[3]):
            valid.append((objective(x), x.copy(), m))
    base = {
        "status": "experimental_sem_dieta_validada",
        "nutrition_completeness": "nao_avaliada",
        "model": "NASEM 2021 via nasem_dairy",
        "evaluation_count": eval_cached.cache_info().misses,
        "warnings": [
            "NÃO USAR para alimentar animais: modelo parcial.",
            "Fibra, amido, minerais, limites nutricionais de inclusão e outras necessidades NÃO AVALIADOS.",
            "Otimização local SLSQP: não garante mínimo global.",
            "Consumo total de matéria seca foi fornecido como entrada, não previsto pelo sistema.",
            "Limites mínimo/máximo são apenas operacionais informados pelo usuário.",
        ],
        "solver_messages": failures[-10:],
        "constraints_checked": ["total_ms", "me", "mp", "limites_operacionais"],
        "constraints_not_checked": ["fdn", "fibra_fisicamente_efetiva", "amido", "minerais", "vitaminas", "limites_nutricionais_de_inclusao"],
    }
    if not valid:
        return base
    cost, x, m = min(valid, key=lambda z: z[0])
    rows = []
    for f, dm, qty in zip(feeds, dm_frac, x):
        as_fed = float(qty / dm)
        rows.append({
            "ingredient": f.name,
            "kg_dm_cow_day": float(qty),
            "kg_as_fed_cow_day": as_fed,
            "dry_matter_pct": float(f.dry_matter_pct),
            "price_brl_kg_as_fed": float(f.price_as_fed_brl_kg),
            "cost_brl_cow_day": as_fed * f.price_as_fed_brl_kg,
        })
    base.update({
        "status": "candidata_experimental",
        "diet": rows,
        "animal_inputs": {k: animal.get(k) for k in
                          ("An_AgeDay", "An_Parity_rl", "An_LactDay", "An_BW", "Trg_MilkProd")},
        "total_dm_kg_cow_day": float(x.sum()),
        "total_as_fed_kg_cow_day": float(sum(r["kg_as_fed_cow_day"] for r in rows)),
        "cost_brl_cow_day": cost,
        "cost_brl_herd_day": cost * request.herd_size,
        "cost_brl_herd_30_days": cost * request.herd_size * 30,
        "nutrition": {
            "me_intake_mcal_day": m[0], "me_requirement_mcal_day": m[1],
            "mp_intake_g_day": m[2], "mp_requirement_g_day": m[3],
        },
        "activated_rules": [
            {"id": "R_ME", "status": "atendida", "explanation": "Energia metabolizável ingerida >= exigida no cenário avaliado"},
            {"id": "R_MP", "status": "atendida", "explanation": "Proteína metabolizável ingerida >= exigida no cenário avaliado"},
        ],
    })
    return base
