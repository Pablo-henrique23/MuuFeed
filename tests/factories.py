"""Dados FICTÍCIOS apenas para testes (não representam nenhuma dieta calculada).

Aritmética base (conferível à mão): silagem 10 kg MS a 33% MS = 30,303 kg MN × R$ 0,30 = R$ 9,0909;
farelo 2 kg MS a 90% MS = 2,2222 kg MN × R$ 2,45 = R$ 5,4444; total R$ 14,5354 por vaca/dia.
"""
from models import Indicador, Ingrediente, ItemDieta, RegraAcionada, Restricao, ResultadoFormulacao

CUSTO_VACA = 10 / 0.33 * 0.30 + 2 / 0.9 * 2.45  # ≈ 14,5354


def ingredientes_teste():
    return [Ingrediente("U1", "Corn silage, typical", "Silagem de milho, típica", 33.0, 0.30, "ilustrativo"),
            Ingrediente("U2", "Soybean meal", "Farelo de soja", 90.0, 2.45, "informado")]


def itens_teste(com_preco=True):
    a, b = 10 / 0.33, 2 / 0.9
    return [ItemDieta("U1", "Silagem de milho, típica", 10.0, a, a * 0.30, 0.30 if com_preco else None),
            ItemDieta("U2", "Farelo de soja", 2.0, b, b * 2.45, 2.45 if com_preco else None)]


def resultado_teste(status="otimo", regras=True):
    return ResultadoFormulacao(
        status=status, mensagem="Resultado de teste.", custo_vaca_dia=CUSTO_VACA, itens=itens_teste(),
        indicadores=[Indicador("energia", "Energia metabolizável", "Mcal/dia", 40.0, 38.0, "atende"),
                     Indicador("proteina", "Proteína metabolizável", "g/dia", 2000.0, None, "nao_avaliado")],
        regras=[RegraAcionada("R-01", "Regra de teste com ação e justificativa.", "Fonte de teste")] if regras else [],
        restricoes=[Restricao("C1", "Restrição atendida", "atendida", "ok"), Restricao("C2", "Restrição violada", "violada", "x"),
                    Restricao("C3", "Restrição pendente", "nao_avaliada")],
        nao_avaliadas=["Amido máximo"], avisos=["Aviso de teste."], modelo_referencia="Modelo de teste",
        id_formulacao="MF-TESTE-123", executada_em="2026-10-20T20:15:00-03:00")
