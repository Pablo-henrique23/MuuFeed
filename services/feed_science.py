"""Políticas de *apresentação e cautela* por identificador NASEM.

Não altera os valores da biblioteca. Referências de inclusão NÃO são limites
universais, nem são ativadas automaticamente pelo otimizador.
"""
from __future__ import annotations

FONTE_NASEM = "https://www.ncbi.nlm.nih.gov/books/NBK600601/"
FONTE_BIBLIOTECA = "https://www.cnmnasemdairy.com/library"
FONTE_NNP = "https://www.ncbi.nlm.nih.gov/books/NBK600603/"
FONTE_PSU = "https://extension.psu.edu/concentrates-for-dairy-cattle"
FONTE_UGA = "https://fieldreport.caes.uga.edu/publications/B862/considerations-for-using-by-product-feeds/"
FONTE_AGUA_S = "https://www.ncbi.nlm.nih.gov/books/NBK600589/"

# Composto de nitrogênio não proteico: Fd_CP representa equivalente de N x 6,25,
# não massa de proteína verdadeira. Alguns equivalentes ultrapassam 100%.
FONTES_NNP = frozenset({
    "Urea", "Ammonium chloride", "Ammonium phosphate (dibasic)",
    "Ammonium phosphate (monobasic)", "Ammonium sulfate",
})

# Nenhuma dessas referências representa a dose automaticamente segura.
# Números de Penn State (TMR, % MS), apenas para CONSULTA HUMANA, sem impor no motor.
REFERENCIAS_INCLUSAO_TMR = {
    "Urea": (1.0, "Ureia adicionada em dieta total misturada (TMR); NNP exige adaptação e supervisão."),
    "Soybean hulls": (10.0, "Casca de soja, referência orientativa de máximo de Penn State; UGA apresenta outros valores."),
    "Wheat bran": (12.0, "Farelo de trigo, referência orientativa de Penn State; condições de formulação importam."),
    "Cottonseed meal": (8.0, "Farelo de algodão, referência orientativa de Penn State; considerar gossipol."),
    "Citrus pulp, dry": (10.0, "Polpa cítrica, referência orientativa de Penn State; outras condições na mesma tabela."),
    "Cottonseed, whole": (10.0, "Algodão integral, referência orientativa de Penn State; considerar gordura e gossipol."),
}


def eh_so_bezerro(nome: str) -> bool:
    return "(fed to calves only)" in str(nome).casefold()


def limite_explicito_obrigatorio(nome: str, categoria: object = None) -> bool:
    """Minimiza risco de suplementos concentrados sem teto operacional.

    O teto é escolha explícita do usuário; NÃO converte em recomendação segura.
    """
    return (str(nome) in FONTES_NNP or
            str(nome) in {"Sodium chloride (salt)", "Sodium bicarbonate"} or
            str(categoria).strip().casefold() in {"vitamin/mineral", "fat supplement", "fatty acid supplement", "additive"})


def referencia_inclusao(nome: str) -> tuple[float | None, str, str]:
    dado = REFERENCIAS_INCLUSAO_TMR.get(nome)
    if dado is None:
        return None, "Sem limite individual generalizável neste catálogo", ""
    return dado[0], dado[1], FONTE_PSU


def classificar_uso(nome: str, categoria: object = None) -> tuple[str, str, str]:
    """Status de triagem, não aprovação zootécnica individual."""
    cat = str(categoria).strip().casefold()
    if eh_so_bezerro(nome):
        return ("NAO_ELEGIVEL_LACTACAO", "Ração identificada na fonte como destinada somente a bezerros.", FONTE_BIBLIOTECA)
    if nome in FONTES_NNP:
        return ("NNP_REQUER_TETO_E_REVISAO", "Nitrogênio não proteico; proteína bruta equivalente pode superar 100%; risco de dose incorreta.", FONTE_NNP)
    if cat == "vitamin/mineral":
        return ("SUPLEMENTO_REQUER_TETO", "Fonte mineral/vitamínica concentrada; composição e dose exigem revisão.", FONTE_NASEM)
    if cat in {"fat supplement", "fatty acid supplement"}:
        return ("GORDURA_REQUER_TETO", "Ingrediente concentrado em gordura; avaliar gordura total, forma e efeitos ruminais.", FONTE_UGA)
    if cat == "additive":
        return ("ADITIVO_REQUER_REVISAO", "Aditivo: verificar uso, dose e regulamentação específica antes da formulação.", FONTE_NASEM)
    if cat in {"by-product/other", "byproduct/other"}:
        return ("SUBPRODUTO_VARIAVEL", "Composição de subproduto pode variar com processamento e origem; conferir análise real.", FONTE_UGA)
    return ("NUTRICIONAL_A_VALIDAR", "Composição de referência NASEM; inclusão depende da dieta completa e características reais.", FONTE_NASEM)


def proteina_bruta_valida(nome: str, pct_ms: float) -> bool:
    """0-100% para alimento usual; equivalente NPN pode ser >100% até teto químico cauteloso.

    O teto 300% evita aceitar números arbitrariamente altos; não aprova
    a segurança do ingrediente e não é um máximo dietético.
    """
    teto = 300.0 if nome in FONTES_NNP else 100.0
    return 0 <= pct_ms <= teto
