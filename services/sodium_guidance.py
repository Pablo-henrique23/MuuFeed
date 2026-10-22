"""Orientação pré-formulação sobre sódio; NÃO indica doses nem conclui inviabilidade.

O diagnóstico é informativo: alimentos comuns também fornecem sódio. Apenas o
NASEM pode comparar a oferta ABSORVIDA com a exigência para a dieta avaliada.
"""
from __future__ import annotations

# Nomes originais da biblioteca que representam fontes concentradas de Na.
# Lista conservadora: NÃO tratar ausência destes nomes como prova de inviabilidade.
FONTES_CONCENTRADAS_NA = frozenset({
    "Sodium chloride (salt)",
    "Sodium bicarbonate",
    "Sodium carbonate",
    "Sodium sulfate",
})


def fontes_concentradas_sodio(ingredientes) -> tuple[str, ...]:
    """Aceita Ingrediente, FeedChoice ou nome NASEM puro sem NASEM instalado."""
    nomes = (
        str(ing) if isinstance(ing, str) else
        str(getattr(ing, "nome_original", getattr(ing, "name", "")))
        for ing in ingredientes
    )
    return tuple(nome for nome in nomes if nome in FONTES_CONCENTRADAS_NA)


def aviso_fonte_sodio(ingredientes, *, exigir_sodio: bool) -> str | None:
    if not exigir_sodio or fontes_concentradas_sodio(ingredientes):
        return None
    return (
        "A restrição de sódio absorvido está ativa, mas os ingredientes selecionados "
        "não incluem uma fonte concentrada de sódio reconhecida pelo MuuFeed. "
        "Com os alimentos atuais, pode não haver candidata que atenda à exigência. "
        "Revise a disponibilidade de sal comum ou de outra fonte de sódio, "
        "com preço informado e máximo de inclusão definido por responsável técnico. "
        "Isso é um aviso, não prova de inviabilidade; os alimentos atuais podem conter sódio."
    )
