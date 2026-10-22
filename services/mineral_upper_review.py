"""Triagem de excesso mineral com rastreabilidade, sem declarar dieta segura.

NASEM 2021, capítulo Minerals: tolerância máxima de Cl isolado NÃO
estabelecida. O livro cita MTL histórico de 3% de NaCl TOTAL na MS para
vacas lactantes (NRC 2005). Não é valor recomendado de inclusão.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

FONTE = "NASEM 2021, Minerals: https://www.ncbi.nlm.nih.gov/books/NBK600600/"
MTL_NACL_TOTAL_PCT_DM = 3.0  # máximo tolerável de NaCl total, NÃO dose recomendada


def revisar_superiores_minerais(
    *,
    dieta_ms: Iterable[tuple[str, float]],
    total_ms_kg: float,
    balancos: Mapping[str, dict] | None = None,
) -> list[str]:
    """Sinaliza limites conhecidos e incertezas; não confirma ausência de toxicidade.

    Os nomes da dieta permanecem os nomes EXATOS da biblioteca NASEM.
    """
    if not math.isfinite(float(total_ms_kg)) or total_ms_kg <= 0:
        raise ValueError("MS total inválida para triagem de minerais")
    linhas = list(dieta_ms)
    nacl_ms = sum(float(kg) for name, kg in linhas if name == "Sodium chloride (salt)")
    if nacl_ms < 0:
        raise ValueError("Quantidade negativa de NaCl")
    avisos: list[str] = []
    if nacl_ms > 0:
        parcela_pct = 100.0 * nacl_ms / total_ms_kg
        if parcela_pct > MTL_NACL_TOTAL_PCT_DM + 1e-8:
            avisos.append(
                f"ATENÇÃO: NaCl declarado corresponde a {parcela_pct:.2f}% da MS, acima da referência "
                "de 3% de NaCl TOTAL na MS como máximo tolerável para vacas lactantes "
                f"({FONTE}). Não interpretar como formulação segura."
            )
        else:
            avisos.append(
                f"NaCl declarado: {parcela_pct:.2f}% da MS. O valor de 3% de NaCl TOTAL "
                "citado pelo NASEM é máximo tolerável histórico, NÃO recomendação; "
                "esta verificação parcial não avalia outras fontes (incluindo água), DCAD ou segurança completa."
            )
    cl = (balancos or {}).get("cloro_absorvido") or {}
    entrada, exigido = cl.get("intake"), cl.get("requirement")
    if entrada is not None and exigido is not None:
        a, r = float(entrada), float(exigido)
        if math.isfinite(a) and math.isfinite(r) and r > 0 and a / r > 2.0:
            avisos.append(
                f"Cloro absorvido equivale a {a/r*100:.1f}% da EXIGÊNCIA MÍNIMA, "
                "não de um limite máximo. O NASEM 2021 não estabelece "
                "limite máximo tolerável para cloro isolado. "
                "Avaliar fontes minerais, água e balanço eletrolítico com profissional."
            )
    return avisos
