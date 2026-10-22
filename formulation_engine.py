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
    min_ndf_pct_dm: float | None = None  # limite explícito do cenário, nunca default nutricional
    max_starch_pct_dm: float | None = None
    min_forage_ndf_pct_dm: float | None = None  # opcional, em % MS; classificação explícita
    require_absorbed_ca_p: bool = False  # restringe Ca/P na base absorvida calculada pelo NASEM


def _valid_real(value: Any, what: str, *, positive: bool = False) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{what}: deve ser número") from exc
    if not math.isfinite(n) or (n <= 0 if positive else n < 0):
        raise ValueError(f"{what}: valor inválido")
    return n


def validate_request(req: FormulationRequest) -> None:
    if type(req.require_absorbed_ca_p) is not bool:
        raise ValueError("require_absorbed_ca_p deve ser booleano")
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
    for value, label in ((req.min_ndf_pct_dm, "FDN mínima"), (req.max_starch_pct_dm, "Amido máximo"), (req.min_forage_ndf_pct_dm, "FDN de forragens mínima")):
        if value is not None:
            _valid_real(value, label)
            if float(value) > 100:
                raise ValueError(f"{label}: percentual deve estar entre 0 e 100")
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
    """Minimiza custo exploratório sujeito a ME/MP, total de MS e restrições opcionais.

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

    # FDN/amido no CSV NASEM são tratados como % da MS somente após validar os
    # dados selecionados. Sem valor não se substitui por zero.
    lib_nut = load_library() if catalog_names is None or request.min_ndf_pct_dm is not None or request.max_starch_pct_dm is not None or request.min_forage_ndf_pct_dm is not None else None
    # Para avaliações reais, carregar biblioteca também quando não há limites;
    # testes com catálogo sintético e evaluator injetado não precisam dela.
    if lib_nut is None and evaluate is None:
        lib_nut = load_library()
    elif lib_nut is None and evaluate is not None:
        # Avaliadores sintéticos podem usar nomes fictícios: não assumir catálogo real.
        try:
            candidate_lib = load_library()
        except (ImportError, ModuleNotFoundError):
            candidate_lib = None
        if candidate_lib is not None and "Fd_Name" in candidate_lib.columns and all(
            f.name in set(candidate_lib["Fd_Name"]) for f in request.feeds
        ):
            lib_nut = candidate_lib
    comp = {}
    if lib_nut is not None:
        for column in ('Fd_Name', 'Fd_NDF', 'Fd_St'):
            if column not in lib_nut.columns:
                raise ValueError(f"Biblioteca NASEM sem coluna exigida: {column}")
        sub = lib_nut.set_index('Fd_Name')
        for feed in request.feeds:
            if feed.name not in sub.index:
                raise ValueError(f"Ingrediente não encontrado para FDN/amido: {feed.name}")
            row = sub.loc[feed.name]
            if isinstance(row, pd.DataFrame):
                raise ValueError(f"Ingrediente com linhas ambíguas na biblioteca: {feed.name}")
            comp[feed.name] = {}
            for attr, column in (('ndf', 'Fd_NDF'), ('starch', 'Fd_St')):
                value = pd.to_numeric(row[column], errors='coerce')
                if pd.isna(value) or not math.isfinite(float(value)) or not 0 <= float(value) <= 100:
                    comp[feed.name][attr] = None
                else:
                    comp[feed.name][attr] = float(value)
    for attr, limit in (('ndf', request.min_ndf_pct_dm), ('starch', request.max_starch_pct_dm)):
        if limit is not None and (not comp or any(comp[f.name][attr] is None for f in request.feeds)):
            raise ValueError(f"Não há dados válidos e completos para impor restrição de {attr}; não serão usados zeros artificiais")

    # FDN de forragens requer classificação exata, nunca inferida por pedaços do nome.
    from services.forage_ndf import is_forage
    forage_flags = {f.name: is_forage(f.name) for f in request.feeds}
    def forage_ndf_pct(x: np.ndarray) -> float | None:
        if not comp or any(forage_flags[f.name] is None or comp[f.name]['ndf'] is None
                           for f in request.feeds):
            return None
        return float(sum(float(q) * comp[f.name]['ndf'] for f, q in zip(request.feeds, x)
                         if forage_flags[f.name]) / float(request.total_dm_kg))
    if request.min_forage_ndf_pct_dm is not None:
        if any(v is None for v in forage_flags.values()):
            unknown = [n for n,v in forage_flags.items() if v is None]
            raise ValueError(f"Classificação de forragem pendente para: {unknown}. Não é seguro aplicar limite de FDN de forragens.")
        if not comp or any(comp[f.name]['ndf'] is None for f in request.feeds):
            raise ValueError('FDN de forragens: dado NASEM indisponível; restrição não aplicada')

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
        if request.require_absorbed_ca_p:
            from services.nasem_requirements import exigir_calcio_fosforo
            return tuple(m[k] for k in METRICS) + exigir_calcio_fosforo(output)
        return tuple(m[k] for k in METRICS)

    def metrics(x: np.ndarray) -> tuple[float, float, float, float]:
        return eval_cached(tuple(float(t) for t in x))

    def constraints_energy(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[0] - v[1]) / max(1.0, v[1])

    def constraints_protein(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[2] - v[3]) / max(1.0, v[3])

    def constraints_ca(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[4] - v[5]) / max(v[5], 1.0)

    def constraints_p(x: np.ndarray) -> float:
        v = metrics(x)
        return (v[6] - v[7]) / max(v[7], 1.0)

    def percent_dm(x: np.ndarray, attr: str) -> float | None:
        if not comp or any(comp[f.name][attr] is None for f in feeds):
            return None
        return float(np.dot(x, [comp[f.name][attr] for f in feeds]) / total)

    constraints = [
        {"type": "eq", "fun": lambda x: float(x.sum() - total)},
        {"type": "ineq", "fun": constraints_energy},
        {"type": "ineq", "fun": constraints_protein},
    ]
    if request.require_absorbed_ca_p:
        constraints.extend([{"type": "ineq", "fun": constraints_ca},
                            {"type": "ineq", "fun": constraints_p}])
    if request.min_ndf_pct_dm is not None:
        constraints.append({"type": "ineq", "fun": lambda x: (percent_dm(x, 'ndf') - request.min_ndf_pct_dm) / 100})
    if request.min_forage_ndf_pct_dm is not None:
        constraints.append({"type": "ineq", "fun": lambda x: (forage_ndf_pct(x) - request.min_forage_ndf_pct_dm) / 100})
    if request.max_starch_pct_dm is not None:
        constraints.append({"type": "ineq", "fun": lambda x: (request.max_starch_pct_dm - percent_dm(x, 'starch')) / 100})
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
    solver_attempts = []
    for attempt_id, x0 in enumerate(starts, 1):
        try:
            initial_m = metrics(x0)
            if not all(math.isfinite(v) for v in initial_m):
                raise ValueError("Indicadores iniciais inválidos")
            res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                           options={"maxiter": request.max_iterations, "ftol": 1e-9})
            solver_attempts.append({
                "attempt": attempt_id, "converged": bool(res.success),
                "initial_cost_brl_cow_day": float(objective(x0)),
                "improvement_brl_cow_day": (float(objective(x0)) - float(objective(res.x))) if np.all(np.isfinite(res.x)) else None,
                "message": str(res.message), "iterations": int(getattr(res, "nit", 0)),
                "cost_brl_cow_day": float(objective(res.x)) if np.all(np.isfinite(res.x)) else None,
            })
            if not res.success:
                failures.append(f"SLSQP: {res.message}")
            if np.all(np.isfinite(res.x)):
                candidates.append(np.asarray(res.x, dtype=float))
            candidates.append(x0)
        except Exception as exc:
            solver_attempts.append({"attempt": attempt_id, "converged": False,
                                    "message": f"{type(exc).__name__}: {exc}", "iterations": 0,
                                    "initial_cost_brl_cow_day": float(objective(x0)), "improvement_brl_cow_day": None,
                                    "cost_brl_cow_day": None})
            failures.append(f"Falha no cenário inicial: {type(exc).__name__}: {exc}")

    # Avaliação independente do retorno `success` do solver — nenhuma folga nutricional.
    valid: list[tuple[float, np.ndarray, tuple[float, ...]]] = []
    near: list[tuple[float, float, np.ndarray, tuple[float, ...], dict[str, float]]] = []
    for x in candidates:
        try:
            m = metrics(x)
        except Exception as exc:
            failures.append(f"Candidata descartada: {exc}")
            continue
        gaps = {
            "total_dm_kg": abs(float(x.sum()) - total),
            "me_mcal_day": max(0.0, m[1] - m[0]),
            "mp_g_day": max(0.0, m[3] - m[2]),
        }
        if request.require_absorbed_ca_p:
            gaps["ca_abs_g_day"] = max(0.0, m[5] - m[4])
            gaps["p_abs_g_day"] = max(0.0, m[7] - m[6])
        if request.min_ndf_pct_dm is not None:
            gaps["ndf_pct_dm"] = max(0.0, request.min_ndf_pct_dm - percent_dm(x, 'ndf'))
        if request.min_forage_ndf_pct_dm is not None:
            gaps["forage_ndf_pct_dm"] = max(0.0, request.min_forage_ndf_pct_dm - forage_ndf_pct(x))
        if request.max_starch_pct_dm is not None:
            gaps["starch_pct_dm"] = max(0.0, percent_dm(x, 'starch') - request.max_starch_pct_dm)
        bounds_gap = max(float(np.max(np.maximum(lower - x, 0))), float(np.max(np.maximum(x - upper, 0))))
        gaps["bounds_dm_kg"] = bounds_gap
        score = (gaps["total_dm_kg"] / max(total, 1.0) + gaps["me_mcal_day"] / max(m[1], 1.0)
                 + gaps["mp_g_day"] / max(m[3], 1.0) + bounds_gap / max(total, 1.0)
                 + gaps.get("ndf_pct_dm", 0) / 100 + gaps.get("starch_pct_dm", 0) / 100
                 + gaps.get("forage_ndf_pct_dm", 0) / 100)
        if request.require_absorbed_ca_p:
            score += gaps["ca_abs_g_day"] / max(m[5], 1.0) + gaps["p_abs_g_day"] / max(m[7], 1.0)
        near.append((score, objective(x), x.copy(), m, gaps))
        if (abs(float(x.sum()) - total) <= 1e-5
                and np.all(x >= lower - 1e-6) and np.all(x <= upper + 1e-6)
                and m[0] >= m[1] and m[2] >= m[3]
                and (not request.require_absorbed_ca_p or (m[4] >= m[5] - 1e-7 and m[6] >= m[7] - 1e-7))
                and (request.min_forage_ndf_pct_dm is None or forage_ndf_pct(x) >= request.min_forage_ndf_pct_dm - 1e-7)
                and (request.min_ndf_pct_dm is None or percent_dm(x, 'ndf') >= request.min_ndf_pct_dm - 1e-7)
                and (request.max_starch_pct_dm is None or percent_dm(x, 'starch') <= request.max_starch_pct_dm + 1e-7)):
            valid.append((objective(x), x.copy(), m))
    checked_extra = (["calcio_absorvido", "fosforo_absorvido"] if request.require_absorbed_ca_p else []) + (["fdn_forragens"] if request.min_forage_ndf_pct_dm is not None else []) + (["fdn"] if request.min_ndf_pct_dm is not None else []) + (["amido"] if request.max_starch_pct_dm is not None else [])
    unverified = [v for v in ["fdn", "fibra_fisicamente_efetiva", "fdn_forragens", "amido", "minerais", "vitaminas", "limites_nutricionais_de_inclusao"] if v not in checked_extra]
    base = {
        "status": "experimental_sem_dieta_validada",
        "nutrition_completeness": "nao_avaliada",
        "model": "NASEM 2021 via nasem_dairy",
        "evaluation_count": eval_cached.cache_info().misses,
        "warnings": [
            "NÃO USAR para alimentar animais: modelo parcial.",
            ("Cálcio/fósforo ABSORVIDOS do NASEM são restrições ativas; minerais restantes, vitaminas, "
             "fibra fisicamente efetiva e outras exigências continuam sem verificação completa."
             if request.require_absorbed_ca_p else
             "Ca e P totais são composição bruta. Balanços absorvidos do NASEM serão exibidos, "
             "quando disponíveis, como diagnóstico SEM restrição automática. Outros nutrientes NÃO AVALIADOS."),
            "Otimização local SLSQP: não garante mínimo global.",
            "Consumo total de matéria seca foi fornecido como entrada, não previsto pelo sistema.",
            "Limites mínimo/máximo são apenas operacionais informados pelo usuário.",
        ],
        "solver_messages": failures[-10:],
        "solver_diagnostics": {
            "algorithm": "SLSQP (otimizacao local)",
            "attempts": solver_attempts,
            "attempts_count": len(solver_attempts),
            "converged_attempts": sum(1 for a in solver_attempts if a["converged"]),
            "validated_candidates": len(valid),
            "global_optimum_guaranteed": False,
        },
        "constraints_checked": ["total_ms", "me", "mp", "limites_operacionais"] + checked_extra,
        "constraints_not_checked": unverified,
    }
    if not valid:
        if near:
            _score, _cost, _x, _m, gaps = min(near, key=lambda t: (t[0], t[1]))
            base["solver_diagnostics"]["closest_candidate_gaps"] = gaps
            base["solver_diagnostics"]["diagnostic_note"] = (
                "Nenhuma candidata satisfez todas as restrições verificadas. "
                "As diferenças abaixo são de uma tentativa aproximada, não comprovam inviabilidade."
            )
        else:
            base["solver_diagnostics"]["diagnostic_note"] = (
                "Não foi possível avaliar candidatas; verifique dados e mensagens do avaliador NASEM."
            )
        return base
    cost, x, m = min(valid, key=lambda z: z[0])
    base["solver_diagnostics"]["best_cost_brl_cow_day"] = float(cost)
    base["solver_diagnostics"]["lowest_initial_cost_brl_cow_day"] = min(
        float(objective(start)) for start in starts)
    base["solver_diagnostics"]["best_improvement_vs_lowest_initial_brl"] = (
        base["solver_diagnostics"]["lowest_initial_cost_brl_cow_day"] - float(cost))
    base["solver_diagnostics"]["validated_costs_brl_cow_day"] = sorted(
        {round(float(z[0]), 6) for z in valid})
    # Alertas DESCRITIVOS: números de observação não são limites nutricionais.
    descriptive_alerts = []
    portions = x / total
    idx = int(np.argmax(portions))
    if portions[idx] >= 0.70:
        descriptive_alerts.append(
            f"Composição concentrada: {names[idx]} representa {portions[idx]*100:.1f}% da MS. "
            "O patamar de 70% é apenas um gatilho de revisão, não uma recomendação nutricional."
        )
    if m[0] / m[1] >= 1.20:
        descriptive_alerts.append(
            f"Energia calculada em {m[0]/m[1]*100:.1f}% da exigência. "
            "Gatilho descritivo de 120%, não limite nutricional; revisar composição e hipóteses."
        )
    base["descriptive_alerts"] = descriptive_alerts
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
    from services.mineral_composition import calcular_minerais
    from services.nutrient_profile import calcular_perfil
    # Composição bruta é distinta dos balanços absorvidos da saída NASEM.
    minerais = (calcular_minerais(lib_nut, dict(zip(names, map(float, x))))
                if lib_nut is not None else {k: None for k in
                    ('ca_pct_dm', 'ca_g_day', 'p_pct_dm', 'p_g_day')})
    perfil_adicional = (calcular_perfil(lib_nut, dict(zip(names, map(float, x))))
                        if lib_nut is not None else {})
    forage_ndf = forage_ndf_pct(x)
    ndf_pct = percent_dm(x, 'ndf')
    starch_pct = percent_dm(x, 'starch')
    # Balanços absorvidos: avaliar também quando NÃO são restrições do otimizador.
    from services.nasem_requirements import ler_balancos
    if request.require_absorbed_ca_p:
        from_cache = {
            "calcio_absorvido": {"label": "Cálcio absorvido", "unit": "g/dia", "intake": m[4],
                "requirement": m[5], "status": "atende", "source": "NASEM 2021 via nasem_dairy"},
            "fosforo_absorvido": {"label": "Fósforo absorvido", "unit": "g/dia", "intake": m[6],
                "requirement": m[7], "status": "atende", "source": "NASEM 2021 via nasem_dairy"},
        }
        absorbed = from_cache
    else:
        try:
            diet_final = pd.DataFrame({"Feedstuff": names, "kg_user": x})
            output_final = evaluator(diet_final, copy.deepcopy(animal), copy.deepcopy(equations), copy.deepcopy(infusion))
            absorbed = ler_balancos(output_final)
        except (ValueError, KeyError, TypeError, AttributeError):
            absorbed = {}
    for item in absorbed.values():
        if item["status"] == "viola":
            descriptive_alerts.append(
                f"{item['label']}: {item['intake']:.2f} g/d absorvidos < {item['requirement']:.2f} g/d exigidos. "
                "Este mineral não foi imposto como restrição da otimização."
            )
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
        "nutrient_composition": {
            "ndf_pct_dm": ndf_pct, "starch_pct_dm": starch_pct,
            "forage_ndf_pct_dm": forage_ndf, "forage_ndf_min_pct_dm": request.min_forage_ndf_pct_dm,
            **minerais,
            "additional_nutrients": perfil_adicional,
            "absorbed_mineral_checks": absorbed,
            "forage_classification": {f.name: ("forragem" if forage_flags[f.name] else "nao_forragem") if forage_flags[f.name] is not None else "desconhecida" for f in feeds},
            "ndf_min_pct_dm": request.min_ndf_pct_dm, "starch_max_pct_dm": request.max_starch_pct_dm,
            "source": "NASEM_feed_library.csv: Fd_NDF, Fd_St; ponderação pela MS",
            "is_nutritionally_validated": False,
        },
        "nutrition": {
            "me_intake_mcal_day": m[0], "me_requirement_mcal_day": m[1],
            "mp_intake_g_day": m[2], "mp_requirement_g_day": m[3],
        },
        "activated_rules": ([
            {"id": "R_CA_ABS", "status": "atendida", "explanation": "Cálcio absorvido >= exigência calculada no NASEM", "source": "NASEM 2021 via nasem_dairy"},
            {"id": "R_P_ABS", "status": "atendida", "explanation": "Fósforo absorvido >= exigência calculada no NASEM", "source": "NASEM 2021 via nasem_dairy"},
        ] if request.require_absorbed_ca_p else []) + [
            {"id": "R_ME", "status": "atendida", "explanation": "Energia metabolizável ingerida >= exigida no cenário avaliado"},
            {"id": "R_MP", "status": "atendida", "explanation": "Proteína metabolizável ingerida >= exigida no cenário avaliado"},
        ] + ([{"id": "R_FDN_FORRAGEM_MIN", "status": "atendida", "explanation": f"FDN de forragens {forage_ndf:.2f}% MS >= mínimo configurado {request.min_forage_ndf_pct_dm:.2f}% MS", "source": "Limite informado pelo usuário; composição NASEM, classificação explícita"}] if request.min_forage_ndf_pct_dm is not None else []) + ([{"id": "R_FDN_MIN", "status": "atendida", "explanation": f"FDN {ndf_pct:.2f}% MS >= mínimo configurado {request.min_ndf_pct_dm:.2f}% MS", "source": "Limite informado pelo usuário; composição NASEM"}] if request.min_ndf_pct_dm is not None else []) + ([{"id": "R_AMIDO_MAX", "status": "atendida", "explanation": f"Amido {starch_pct:.2f}% MS <= máximo configurado {request.max_starch_pct_dm:.2f}% MS", "source": "Limite informado pelo usuário; composição NASEM"}] if request.max_starch_pct_dm is not None else []),
    })
    return base
