"""Classificação de ingredientes para FDN **proveniente de forragens** (fNDF).

Fonte primária: Fd_Type/Fd_Category da biblioteca NASEM instalada. Nomes
curados são fallback apenas quando a biblioteca não fornece metadados claros.
Nenhuma classe é inferida de nomes não reconhecidos; retornamos None.

Importante: fNDF não é fibra fisicamente efetiva (peNDF). A classificação não
atribui limites máximos nutricionais de inclusão ou dados químicos ausentes.
"""
from __future__ import annotations

FORAGE_NASEM_NAMES = frozenset({
    "Corn silage, typical", "Bermudagrass hay", "Alfalfa meal",
})
NONFORAGE_NASEM_NAMES = frozenset({
    "Canola meal", "Corn grain HM, coarse grind", "Corn grain dry, medium grind",
    "Soybean meal, solvent 48CP", "Citrus pulp, dry",
    "Sodium chloride (salt)", "Sodium bicarbonate",
    "Sorghum grain, dry, ground", "DDGS, high protein",
    "Soybean hulls", "Wheat bran", "Sunflower meal", "Cottonseed meal",
})

# Metadados do próprio catálogo. Forrageiras (silagens, fenos, pastagens)
# contam como forragem; concentrados, suplementos e subprodutos NÃO.
_FORAGE_TYPES = frozenset({"forage"})
_NONFORAGE_TYPES = frozenset({"concentrate", "supplement", "additive"})
_FORAGE_CATEGORIES = frozenset({
    "grain crop forage", "grass/legume forage", "pasture",
})
_NONFORAGE_CATEGORIES = frozenset({
    "vitamin/mineral", "by-product/other", "byproduct/other", "energy source",
    "plant protein", "calf liquid feed", "additive", "fat supplement",
    "animal protein", "fatty acid supplement", "sugar/sugar alcohol",
})


def _norm(value: object) -> str:
    """Trata apenas metadados textuais válidos; não transforma NaN em categoria."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().casefold().split())


def classificar_forragem(
    name: str, *, feed_type: object = None, feed_category: object = None
) -> tuple[bool | None, str]:
    """Retorna (é_forragem, origem), sem inventar a classificação.

    Os campos Fd_Type/Fd_Category da biblioteca têm preferência sobre nomes
    curados. Se houver conflito entre tipo e categoria, não presume resposta.
    """
    tipo, categoria = _norm(feed_type), _norm(feed_category)
    por_tipo = (True if tipo in _FORAGE_TYPES else
                False if tipo in _NONFORAGE_TYPES else None)
    por_categoria = (True if categoria in _FORAGE_CATEGORIES else
                     False if categoria in _NONFORAGE_CATEGORIES else None)
    if por_tipo is not None and por_categoria is not None and por_tipo != por_categoria:
        # Caso documentado no catálogo NASEM 2021: "Alfalfa meal" é
        # "Forage" em Fd_Type, mas "Plant Protein" em Fd_Category.
        # A categoria indica papel proteico e não revoga a origem vegetal
        # da FDN. Isso NÃO avalia fibra fisicamente efetiva (moagem).
        if name == "Alfalfa meal" and por_tipo is True and tipo == "forage" and categoria == "plant protein":
            return True, "curadoria_nasem_alfalfa_tipo_prevalece"
        return None, "conflito_tipo_categoria_nasem"
    if por_tipo is not None:
        return por_tipo, "Fd_Type"
    if por_categoria is not None:
        return por_categoria, "Fd_Category"
    if name in FORAGE_NASEM_NAMES:
        return True, "curadoria_explicita"
    if name in NONFORAGE_NASEM_NAMES:
        return False, "curadoria_explicita"
    return None, "nao_classificado"


def is_forage(name: str, *, feed_type: object = None,
              feed_category: object = None) -> bool | None:
    return classificar_forragem(name, feed_type=feed_type,
                               feed_category=feed_category)[0]
