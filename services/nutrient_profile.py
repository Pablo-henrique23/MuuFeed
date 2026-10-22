"""Perfil informativo dos nutrientes com unidade comprovada (% da MS).

Calcula concentração ponderada em MS, não absorção/exigência nem segurança da dieta.
Uma composição ausente em ingrediente utilizado invalida somente aquele nutriente.
Não inferir unidades de microminerais (mg/kg), vitaminas ou aminoácidos.
"""
from __future__ import annotations

import math
import pandas as pd
from services.feed_science import proteina_bruta_valida

# Apenas colunas do catálogo NASEM expressas em % da matéria seca.
# FDN, amido, Ca e P já são calculados separadamente no motor.
PERFIL_PERCENTUAL = {
    "proteina_bruta": ("Proteína bruta equivalente", "Fd_CP"),
    "fda": ("Fibra em detergente ácido (FDA)", "Fd_ADF"),
    "lignina": ("Lignina", "Fd_Lg"),
    "acucares_soluveis": ("Carboidratos solúveis em água", "Fd_WSC"),
    "gordura_bruta": ("Extrato etéreo", "Fd_CFat"),
    "cinzas": ("Cinzas", "Fd_Ash"),
    "magnesio": ("Magnésio total", "Fd_Mg"),
    "potassio": ("Potássio total", "Fd_K"),
    "sodio": ("Sódio total", "Fd_Na"),
    "cloro": ("Cloro total", "Fd_Cl"),
    "enxofre": ("Enxofre total", "Fd_S"),
}


def calcular_perfil(catalogo: pd.DataFrame, quantidades_ms: dict[str, float]) -> dict[str, dict]:
    """Retorna {chave: {label, pct_dm, g_day, source}} ou None para nutrientes sem dados.

    Percentuais do feed library são tratados como percentuais de matéria seca.
    Uma dieta sem MS positiva é inválida para esta finalidade.
    """
    if "Fd_Name" not in catalogo:
        raise ValueError("Catálogo sem Fd_Name")
    if catalogo["Fd_Name"].duplicated().any():
        raise ValueError("Ingredientes com nomes ambíguos no catálogo")
    dados = catalogo.set_index("Fd_Name")
    total = 0.0
    for nome, quantidade in quantidades_ms.items():
        kg = float(quantidade)
        if not math.isfinite(kg) or kg < 0:
            raise ValueError(f"Quantidade MS inválida para {nome}")
        if kg > 0 and nome not in dados.index:
            raise ValueError(f"Ingrediente ausente: {nome}")
        total += kg
    saida = {}
    for key, (label, coluna) in PERFIL_PERCENTUAL.items():
        massa_g = 0.0
        completo = total > 0 and coluna in dados.columns
        if completo:
            for nome, quantidade in quantidades_ms.items():
                kg = float(quantidade)
                if kg == 0:
                    continue
                valor = pd.to_numeric(dados.at[nome, coluna], errors="coerce")
                # Equivalente proteico >100% é legítimo APENAS em fontes NNP
                # reconhecidas, não em ingredientes normais desconhecidos.
                valido = (proteina_bruta_valida(nome, float(valor))
                          if key == "proteina_bruta" and pd.notna(valor)
                          else pd.notna(valor) and 0 <= float(valor) <= 100)
                if pd.isna(valor) or not math.isfinite(float(valor)) or not valido:
                    completo = False
                    break
                massa_g += kg * float(valor) * 10.0
        saida[key] = {
            "label": label,
            "pct_dm": massa_g / (10 * total) if completo else None,
            "g_day": massa_g if completo else None,
            "source": f"NASEM_feed_library.csv: {coluna}; média ponderada por MS",
        }
    return saida
