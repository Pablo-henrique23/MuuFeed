"""Tradução explícita da raça da interface para An_Breed do nasem_dairy.

O código `Other` é um caminho genérico experimental do pacote externo,
não uma parametrização validada para uma raça específica. Não converter
nomes arbitrários em Holstein nem em Other sem escolha explícita.
"""
from __future__ import annotations

RACA_GENERICA = "Outra raça (genérica — experimental)"
BREEDS_NASEM = {
    "holandesa": "Holstein", "holstein": "Holstein",
    "jersey": "Jersey",
    RACA_GENERICA.casefold(): "Other",
}
AVISO_RACA_GENERICA = (
    "Raça sem parametrização específica: será usado An_Breed='Other' do "
    "nasem_dairy. Trata-se de uma aproximação experimental, não de uma "
    "validação nutricional para a raça informada. Confira os resultados "
    "com um médico-veterinário ou zootecnista."
)


def para_raca_nasem(raca: str) -> str:
    nome = str(raca).strip().casefold()
    if nome not in BREEDS_NASEM:
        raise ValueError(
            "Raça não parametrizada: escolha Holandesa, Jersey ou "
            f"'{RACA_GENERICA}' na interface."
        )
    return BREEDS_NASEM[nome]


def utiliza_raca_generica(raca: str) -> bool:
    return para_raca_nasem(raca) == "Other"


def rotulo_raca_lote(lote) -> str:
    """Rótulo de relatório; o NASEM continua recebendo apenas An_Breed."""
    if utiliza_raca_generica(lote.raca):
        detalhe = str(getattr(lote, "raca_descricao", "") or "").strip()
        return f"{detalhe} (modelo genérico Other)" if detalhe else "Outra raça (modelo genérico Other)"
    return lote.raca
