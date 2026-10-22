"""Balanços de macrominerais do próprio motor NASEM, em base ABSORVIDA.

Não comparar minerais totais do catálogo com exigências absorvidas. A ingestão
absorvida e a exigência são ambas calculadas pelo NASEM na mesma execução.
Ausência de dados => sem veredito; não inventar valores de substituição.
"""
from __future__ import annotations

import math

# Exatidão dos nomes conforme nasem_dairy.model.nasem (saída ModelOutput).
MINERAIS_ABSORVIDOS = {
    "calcio_absorvido": ("Cálcio absorvido", "Abs_CaIn", "An_Ca_req"),
    "fosforo_absorvido": ("Fósforo absorvido", "Abs_PIn", "An_P_req"),
    "magnesio_absorvido": ("Magnésio absorvido", "Abs_MgIn", "An_Mg_req"),
    "sodio_absorvido": ("Sódio absorvido", "Abs_NaIn", "An_Na_req"),
    "cloro_absorvido": ("Cloro absorvido", "Abs_ClIn", "An_Cl_req"),
    "potassio_absorvido": ("Potássio absorvido", "Abs_KIn", "An_K_req"),
}


def ler_balancos(output, *, apenas: tuple[str, ...] | None = None) -> dict[str, dict]:
    """Retorna comparações g/d; uma variável ausente não invalida as demais."""
    saida: dict[str, dict] = {}
    selecionados = apenas or tuple(MINERAIS_ABSORVIDOS)
    for chave in selecionados:
        rotulo, ingerido_var, exigido_var = MINERAIS_ABSORVIDOS[chave]
        valor, exigencia = None, None
        try:
            valor = float(output.get_value(ingerido_var))
            exigencia = float(output.get_value(exigido_var))
            if not math.isfinite(valor) or not math.isfinite(exigencia) or valor < 0 or exigencia <= 0:
                valor, exigencia = None, None
        except (KeyError, AttributeError, TypeError, ValueError, OverflowError):
            valor, exigencia = None, None
        saida[chave] = {
            "label": rotulo, "unit": "g/dia", "intake": valor, "requirement": exigencia,
            "status": ("nao_avaliado" if valor is None else
                       "atende" if valor >= exigencia - 1e-7 else "viola"),
            "source": f"NASEM 2021 via nasem_dairy: {ingerido_var} versus {exigido_var}",
        }
    return saida


def exigir_calcio_fosforo(output) -> tuple[float, float, float, float]:
    """Retorna valores em g/d para a otimização; falha explicitamente se ausentes."""
    result = ler_balancos(output, apenas=("calcio_absorvido", "fosforo_absorvido"))
    if any(item["status"] == "nao_avaliado" for item in result.values()):
        raise ValueError("NASEM não retornou cálcio e fósforo absorvidos/exigidos válidos")
    ca, p = result["calcio_absorvido"], result["fosforo_absorvido"]
    return (ca["intake"], ca["requirement"], p["intake"], p["requirement"])


def exigir_sodio(output) -> tuple[float, float]:
    """Retorna Na absorvido/exigido (g/dia) para uma restrição explícita.

    Dados inválidos ou ausentes bloqueiam a restrição em vez de virar zero.
    """
    bal = ler_balancos(output, apenas=("sodio_absorvido",))["sodio_absorvido"]
    if bal["status"] == "nao_avaliado":
        raise ValueError("NASEM não retornou sódio absorvido/exigido válido")
    return float(bal["intake"]), float(bal["requirement"])
