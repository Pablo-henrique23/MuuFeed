"""Mostra quais campos do cenário NASEM são substituídos pelo MuuFeed.

Executar na raiz: python scripts/verificar_hipoteses_nasem_v19.py
Exige nasem_dairy instalado e não altera dados ou fórmulas.
"""
from models import Lote
from services.breed import RACA_GENERICA


def main():
    import nasem_dairy as nd
    _, animal, eqs, infusion = nd.demo("lactating_cow_test")
    lote = Lote(nome="Auditoria", n_vacas=20, raca=RACA_GENERICA, raca_descricao="Exemplo",
                idade_valor=821, idade_unidade="dias", peso_kg=625, ordem_lactacao=1,
                dias_lactacao=100, leite_kg_dia=25, gordura_pct=4.0, proteina_pct=3.5)
    substituidos = lote.para_animal_nasem()
    assert "An_Breed" in substituidos and substituidos["An_Breed"] == "Other"
    remanescentes = sorted(set(animal) - set(substituidos) - {"Trg_Dt_DMIn"})
    print(f"Animal do exemplo NASEM: {len(animal)} campos")
    print(f"Substituídos pelo lote: {len(substituidos)} campos: {', '.join(sorted(substituidos))}")
    print("Consumo fixado pela formulação: Trg_Dt_DMIn; escolha de equação: DMIn_eqn=0")
    print(f"Restantes do cenário demonstrativo: {len(remanescentes)} campos")
    for campo in remanescentes:
        print(f"  {campo}: {animal[campo]!r}")
    print(f"Equações importadas do cenário: {len(eqs)}; infusões: {len(infusion or {})}")
    print("ATENÇÃO: campos remanescentes são hipóteses, não medições do lote.")


if __name__ == "__main__":
    main()
