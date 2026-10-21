"""Dados FICTÍCIOS apenas para testes (não representam nenhuma dieta calculada)."""
from models import Indicador, Ingrediente, ItemDieta, RegraAcionada, Restricao, ResultadoFormulacao


def ingredientes_teste():
    return [Ingrediente("U1", "Corn silage, typical", "Silagem de milho, típica", 33.0, 0.30, "ilustrativo"),
            Ingrediente("U2", "Soybean meal", "Farelo de soja", 90.0, 2.45, "informado")]


def resultado_teste(status="otimo", regras=True):
    return ResultadoFormulacao(
        status=status, mensagem="Resultado de teste.", custo_vaca_dia=12.34,
        itens=[ItemDieta("U1", "Silagem de milho, típica", 10.0, 30.30, 9.09), ItemDieta("U2", "Farelo de soja", 2.0, 2.22, 5.44)],
        indicadores=[Indicador("energia", "Energia metabolizável", "Mcal/dia", 40.0, 38.0, "atende"),
                     Indicador("proteina", "Proteína metabolizável", "g/dia", 2000.0, None, "nao_avaliado")],
        regras=[RegraAcionada("R-01", "Regra de teste com ação e justificativa.", "Fonte de teste")] if regras else [],
        restricoes=[Restricao("C1", "Restrição atendida", "atendida", "ok"), Restricao("C2", "Restrição violada", "violada", "x"),
                    Restricao("C3", "Restrição pendente", "nao_avaliada")],
        nao_avaliadas=["Amido máximo"], avisos=["Aviso de teste."], modelo_referencia="Modelo de teste",
        id_formulacao="MF-TESTE-123", executada_em="2026-10-20T20:15:00-03:00")
